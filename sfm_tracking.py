import json
import os
import shutil
import tempfile
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    import pycolmap
except ImportError:
    pycolmap = None

from alignment import average_rotations, robust_umeyama_alignment
from pose import Pose
from tracking import Tracker
from trajectory import Trajectory

CHARUCO_WINDOW_FRAMES = 150


class SfmTracker:
    """
    Tracking caméra par Structure-from-Motion (COLMAP), pour les prises où
    la cible Charuco n'est visible que quelques secondes au début du plan
    puis la caméra est libre de bouger dans la scène.

    Principe : COLMAP reconstruit la trajectoire de la GoPro dans un repère
    et une échelle qui lui sont propres. Sur la fenêtre initiale où le
    Charuco est encore visible, on compare cette trajectoire COLMAP à la
    pose Charuco (en mètres) pour calculer une transformation de similarité,
    qu'on applique ensuite à toute la trajectoire pour la ramener dans le
    repère métrique du Charuco.
    """

    def __init__(self, video, calibration_file, charuco_window_frames=CHARUCO_WINDOW_FRAMES):
        if pycolmap is None:
            raise ImportError("pycolmap est requis pour le tracking SfM : pip install pycolmap")
        if cv2 is None or np is None:
            raise ImportError(
                "OpenCV contrib est requis pour le tracking : pip install opencv-contrib-python"
            )
        self.video = video
        self.charuco_window_frames = charuco_window_frames
        # Réutilise le chargement de calibration, le Rig et la détection
        # Charuco déjà implémentés par Tracker, sans dupliquer ce code.
        self._helper = Tracker(video, calibration_file)

    def _check_disk_space(self, sample_frame_path, total_frames, image_dir):
        """
        Chaque frame de la vidéo est extraite en PNG plein format sur le disque avant
        d'être passée à COLMAP : pour une prise longue en haute résolution, ça peut
        représenter des dizaines de Go. On estime la taille totale à partir d'une
        vraie frame déjà extraite, et on arrête proprement avant de saturer le disque
        (ce qui peut lui aussi geler la machine) plutôt que de le découvrir en cours
        de route.
        """
        if total_frames <= 0:
            return
        sample_size = sample_frame_path.stat().st_size
        estimated_bytes = sample_size * total_frames
        free_bytes = shutil.disk_usage(image_dir).free
        safety_margin = 1.15
        if estimated_bytes * safety_margin > free_bytes:
            estimated_gb = estimated_bytes / (1024 ** 3)
            free_gb = free_bytes / (1024 ** 3)
            raise RuntimeError(
                f"Espace disque insuffisant pour extraire les {total_frames} frames de "
                f"cette vidéo : ~{estimated_gb:.1f} Go nécessaires, {free_gb:.1f} Go "
                "disponibles. Libérez de l'espace disque avant de relancer le tracking."
            )

    def _extract_frames(self, image_dir, progress_callback):
        capture = cv2.VideoCapture(str(self.video))
        if not capture.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la vidéo : {self.video}")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self._helper._frame_rate(capture)

        frame_paths = {}
        index = 0
        disk_space_checked = False
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            path = image_dir / f"frame_{index:06d}.png"
            cv2.imwrite(str(path), frame)
            frame_paths[index] = path

            if not disk_space_checked:
                disk_space_checked = True
                self._check_disk_space(path, total_frames, image_dir)

            if progress_callback:
                if total_frames > 0:
                    pct = int(15 * (index + 1) / total_frames)
                    progress_callback(pct, f"Extraction frame {index + 1}/{total_frames}")
                else:
                    progress_callback(-1, f"Extraction frame {index + 1}")

            index += 1

        capture.release()
        if not frame_paths:
            raise RuntimeError("Aucune frame n'a pu être extraite de la vidéo.")
        return frame_paths, fps

    def _colmap_thread_count(self):
        """
        COLMAP prend tous les cœurs disponibles par défaut (num_threads=-1), ce qui peut
        saturer entièrement la machine et la rendre totalement inréactive le temps du
        calcul (perçu comme un plantage) sur une machine grand public. On laisse
        volontairement 2 cœurs de libre pour le système — ça ne change rien à la
        précision du calcul, juste à sa durée.
        """
        cpu_count = os.cpu_count() or 4
        return max(1, cpu_count - 2)

    def _run_colmap(self, image_dir, frame_paths, progress_callback):
        num_threads = self._colmap_thread_count()

        with tempfile.TemporaryDirectory(prefix="colmap_db_") as db_dir:
            database_path = Path(db_dir) / "database.db"
            sparse_path = Path(db_dir) / "sparse"
            sparse_path.mkdir()

            if progress_callback:
                progress_callback(15, "Extraction des features (COLMAP)...")
            pycolmap.extract_features(
                database_path, image_dir,
                extraction_options=pycolmap.FeatureExtractionOptions(num_threads=num_threads),
            )

            if progress_callback:
                progress_callback(30, "Appariement des frames (COLMAP)...")
            pycolmap.match_sequential(
                database_path,
                matching_options=pycolmap.FeatureMatchingOptions(num_threads=num_threads),
                pairing_options=pycolmap.SequentialPairingOptions(num_threads=num_threads),
            )

            if progress_callback:
                progress_callback(45, "Reconstruction SfM (COLMAP)...")

            total_frames = len(frame_paths)
            registered = {"count": 0}

            def on_next_image():
                registered["count"] += 1
                if progress_callback and total_frames > 0:
                    pct = min(89, 45 + int(45 * registered["count"] / total_frames))
                    progress_callback(pct, f"Reconstruction SfM ({registered['count']} images enregistrées)")

            reconstructions = pycolmap.incremental_mapping(
                database_path, image_dir, sparse_path,
                options=pycolmap.IncrementalPipelineOptions(num_threads=num_threads),
                next_image_callback=on_next_image,
            )

        if not reconstructions:
            raise RuntimeError(
                "COLMAP n'a pas réussi à reconstruire de trajectoire à partir de cette vidéo "
                "(scène trop peu texturée, mouvement trop rapide, ou flou de mouvement excessif)."
            )

        reconstruction = max(reconstructions.values(), key=lambda r: r.num_reg_images())
        if reconstruction.num_reg_images() == 0:
            raise RuntimeError("COLMAP n'a enregistré aucune image dans la reconstruction.")

        return reconstruction

    def _colmap_poses_by_index(self, reconstruction, frame_paths):
        name_to_index = {path.name: index for index, path in frame_paths.items()}
        poses_by_index = {}
        for image in reconstruction.images.values():
            if not image.has_pose:
                continue
            index = name_to_index.get(image.name)
            if index is None:
                continue
            cam_from_world = image.cam_from_world()
            rotation = cam_from_world.rotation.matrix()
            translation = np.asarray(cam_from_world.translation, dtype=np.float64)
            poses_by_index[index] = Pose(rotation=rotation, translation=translation)
        return poses_by_index

    def _collect_alignment_pairs(self, colmap_poses_by_index, frame_paths):
        colmap_centers = []
        charuco_centers = []
        colmap_rotations = []
        charuco_rotations = []
        for index in sorted(colmap_poses_by_index):
            if index >= self.charuco_window_frames:
                break
            frame = cv2.imread(str(frame_paths[index]))
            if frame is None:
                continue
            charuco_pose = self._helper._detect_pose_for_frame(frame)
            if charuco_pose is None:
                continue
            colmap_cam_to_world = colmap_poses_by_index[index].inverse()
            charuco_cam_to_world = charuco_pose.inverse()
            colmap_centers.append(colmap_cam_to_world.translation)
            charuco_centers.append(charuco_cam_to_world.translation)
            colmap_rotations.append(colmap_cam_to_world.rotation)
            charuco_rotations.append(charuco_cam_to_world.rotation)
        return np.array(colmap_centers), np.array(charuco_centers), colmap_rotations, charuco_rotations

    def _refine_rotation_alignment(self, colmap_rotations, charuco_rotations, inlier_mask):
        """
        Un recalage basé uniquement sur les positions des centres caméra peut
        laisser la rotation mal contrainte lorsque la trajectoire de la
        fenêtre Charuco est plutôt plate/peu courbée (cas fréquent : la
        caméra bouge peu pendant les quelques secondes où la cible est
        visible). On affine donc la rotation en utilisant directement les
        orientations de chaque paire de poses (moyenne de rotations par SVD),
        indépendamment de la géométrie des positions.
        """
        candidates = [
            charuco_rotations[i] @ colmap_rotations[i].T
            for i in range(len(colmap_rotations))
            if inlier_mask[i]
        ]
        return average_rotations(candidates)

    def _align_pose(self, colmap_pose, scale, rotation_align, translation_align):
        cam_to_world = colmap_pose.inverse()
        new_rotation = rotation_align @ cam_to_world.rotation
        new_center = scale * (rotation_align @ cam_to_world.translation) + translation_align
        new_cam_to_world = Pose(rotation=new_rotation, translation=new_center)
        return new_cam_to_world.inverse()

    def run(self, progress_callback=None, output_path="data/tracking.json"):
        def report(pct, message):
            if progress_callback:
                progress_callback(pct, message)

        if not Path(self.video).exists():
            raise FileNotFoundError(self.video)

        with tempfile.TemporaryDirectory(prefix="gopro_sfm_") as tmp_dir:
            image_dir = Path(tmp_dir) / "frames"
            image_dir.mkdir()

            report(0, "Extraction des frames...")
            frame_paths, fps = self._extract_frames(image_dir, progress_callback)

            reconstruction = self._run_colmap(image_dir, frame_paths, progress_callback)

            report(90, "Détection du Charuco de référence...")
            colmap_poses_by_index = self._colmap_poses_by_index(reconstruction, frame_paths)
            colmap_centers, charuco_centers, colmap_rotations, charuco_rotations = (
                self._collect_alignment_pairs(colmap_poses_by_index, frame_paths)
            )

            if len(colmap_centers) < 3:
                raise RuntimeError(
                    "Pas assez d'images communes entre la reconstruction SfM et la fenêtre "
                    "Charuco pour recaler la trajectoire dans le repère monde. Vérifiez que "
                    "le Charuco est bien visible et net en tout début de prise."
                )

            report(92, "Recalage dans le repère Charuco...")
            scale, rotation_align, translation_align, inlier_mask = robust_umeyama_alignment(
                colmap_centers, charuco_centers
            )
            # La rotation issue du recalage sur les seules positions peut être mal
            # contrainte si la trajectoire de la fenêtre Charuco est peu courbée ;
            # on l'affine avec les orientations réelles des poses appariées.
            rotation_align = self._refine_rotation_alignment(colmap_rotations, charuco_rotations, inlier_mask)
            inlier_colmap_centers = colmap_centers[inlier_mask]
            inlier_charuco_centers = charuco_centers[inlier_mask]
            translation_align = inlier_charuco_centers.mean(axis=0) - scale * (
                rotation_align @ inlier_colmap_centers.mean(axis=0)
            )
            report(
                93,
                f"Recalage : {int(inlier_mask.sum())}/{len(inlier_mask)} correspondances retenues",
            )

            report(95, "Conversion vers la caméra cinéma...")
            trajectory = Trajectory()
            trajectory.fps = fps
            for index in sorted(colmap_poses_by_index):
                gopro_world_pose = self._align_pose(
                    colmap_poses_by_index[index], scale, rotation_align, translation_align
                )
                cinema_pose = self._helper.rig.transform_tracker_to_cinema(gopro_world_pose)
                trajectory.add_pose(cinema_pose, index)

        if len(trajectory) == 0:
            raise RuntimeError("Aucune pose n'a pu être calculée pour cette vidéo.")

        report(98, "Écriture du fichier de tracking...")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "fps": trajectory.fps,
            "frames": [
                {"index": idx, "matrix": pose.matrix.tolist()}
                for idx, pose in zip(trajectory.frame_indices, trajectory.poses)
            ],
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        report(100, "Tracking terminé")
        return str(output)

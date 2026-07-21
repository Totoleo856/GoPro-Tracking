import json
import tempfile
from pathlib import Path

import numpy as np

from alignment import average_rotations
from app_paths import default_tracking_output_path
from audio_sync import estimate_offset_frames
from pose import Pose
from retime import resample_trajectory
from tracking import Tracker
from sfm_tracking import SfmTracker


class DualTracker:
    """
    Tracking à deux GoPro rigidement montées sur le même rig : chaque flux
    est reconstruit indépendamment (Charuco ou SfM, chacun avec sa propre
    calibration), les deux trajectoires caméra cinéma qui en résultent sont
    synchronisées via un clap sonore puis fusionnées image par image pour
    réduire le bruit, avant un rééchantillonnage final sur le fps réel de la
    caméra cinéma.
    """

    def __init__(
        self, video1, calibration1, video2, calibration2, mode="sfm",
        num_threads=None, max_num_features=None, max_position_discrepancy_mm=30.0,
    ):
        self.video1 = video1
        self.calibration1 = calibration1
        self.video2 = video2
        self.calibration2 = calibration2
        self.max_position_discrepancy_mm = max_position_discrepancy_mm
        if mode == "sfm":
            self.tracker1 = SfmTracker(video1, calibration1, num_threads=num_threads, max_num_features=max_num_features)
            self.tracker2 = SfmTracker(video2, calibration2, num_threads=num_threads, max_num_features=max_num_features)
        else:
            self.tracker1 = Tracker(video1, calibration1)
            self.tracker2 = Tracker(video2, calibration2)

    def _cinema_fps(self):
        with open(self.calibration1, "r", encoding="utf-8") as file:
            data = json.load(file)
        fps = float(data["camera"]["cinema_camera"].get("fps", 0.0))
        if fps <= 0.0:
            raise ValueError(
                "Le fps de la caméra cinéma n'est pas renseigné dans le fichier de "
                "calibration : il est nécessaire pour recaler la trajectoire fusionnée "
                "sur la timeline réelle de la caméra cinéma."
            )
        return fps

    def _load_result(self, output_path):
        with open(output_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        fps = float(data["fps"])
        poses_by_index = {
            int(frame["index"]): Pose.from_matrix(np.array(frame["matrix"], dtype=np.float64))
            for frame in data["frames"]
        }
        return poses_by_index, fps

    def _check_consistency(self, poses1_by_index, shifted_poses2_by_index, common_indices, report):
        """
        Les deux reconstructions sont indépendantes (calibration et éventuellement mode
        de tracking propres à chaque GoPro) : avant de les fusionner, on vérifie qu'elles
        s'accordent réellement sur les frames communes (après synchronisation audio),
        plutôt que de moyenner aveuglément deux résultats incohérents (mauvais rig,
        mauvaise synchronisation, échec de reconstruction d'un des deux flux).
        """
        if not common_indices:
            raise RuntimeError(
                "Aucune frame commune entre les deux reconstructions GoPro après la "
                "synchronisation audio : vérifiez que le clap est bien audible et "
                "identique sur les deux vidéos."
            )

        discrepancies_mm = [
            float(np.linalg.norm(
                poses1_by_index[index].inverse().translation
                - shifted_poses2_by_index[index].inverse().translation
            )) * 1000.0
            for index in common_indices
        ]
        mean_discrepancy = float(np.mean(discrepancies_mm))
        max_discrepancy = float(np.max(discrepancies_mm))
        report(
            87,
            f"Cohérence entre les deux reconstructions ({len(common_indices)} frames "
            f"communes) : écart moyen {mean_discrepancy:.1f} mm, max {max_discrepancy:.1f} mm",
        )
        if max_discrepancy > self.max_position_discrepancy_mm:
            raise RuntimeError(
                f"Écart de position trop important entre les deux reconstructions GoPro "
                f"({max_discrepancy:.1f} mm sur les frames communes, tolérance réglée à "
                f"{self.max_position_discrepancy_mm:.1f} mm) : vérifiez la calibration de "
                "chaque rig, la synchronisation audio (clap), ou relancez le tracking avec "
                "une seule des deux GoPro plutôt que de fusionner un résultat incohérent."
            )

    def _fuse_pose(self, pose_a, pose_b):
        cam_to_world_a = pose_a.inverse()
        cam_to_world_b = pose_b.inverse()
        center = (cam_to_world_a.translation + cam_to_world_b.translation) / 2.0
        rotation = average_rotations([cam_to_world_a.rotation, cam_to_world_b.rotation])
        return Pose(rotation=rotation, translation=center).inverse()

    def run(self, progress_callback=None, output_path=None):
        output_path = output_path or default_tracking_output_path()

        def report(pct, message):
            if progress_callback:
                progress_callback(pct, message)

        with tempfile.TemporaryDirectory(prefix="dual_tracking_") as tmp_dir:
            output1 = Path(tmp_dir) / "gopro1.json"
            output2 = Path(tmp_dir) / "gopro2.json"

            report(0, "Reconstruction GoPro 1...")
            self.tracker1.run(
                progress_callback=lambda pct, msg: report(int(pct * 0.4) if pct >= 0 else -1, f"GoPro 1 : {msg}"),
                output_path=str(output1),
            )

            report(40, "Reconstruction GoPro 2...")
            self.tracker2.run(
                progress_callback=lambda pct, msg: report(40 + int(pct * 0.4) if pct >= 0 else -1, f"GoPro 2 : {msg}"),
                output_path=str(output2),
            )

            poses1_by_index, fps1 = self._load_result(output1)
            poses2_by_index, fps2 = self._load_result(output2)

        report(82, "Synchronisation audio (clap)...")
        source_fps = fps1 if fps1 > 0 else fps2
        offset = estimate_offset_frames(self.video1, self.video2, source_fps)

        shifted_poses2_by_index = {index + offset: pose for index, pose in poses2_by_index.items()}

        report(86, "Fusion des deux reconstructions...")
        common_indices = sorted(set(poses1_by_index) & set(shifted_poses2_by_index))
        only_in_1 = sorted(set(poses1_by_index) - set(shifted_poses2_by_index))
        only_in_2 = sorted(set(shifted_poses2_by_index) - set(poses1_by_index))

        self._check_consistency(poses1_by_index, shifted_poses2_by_index, common_indices, report)

        fused_by_index = {}
        for index in common_indices:
            fused_by_index[index] = self._fuse_pose(poses1_by_index[index], shifted_poses2_by_index[index])
        for index in only_in_1:
            fused_by_index[index] = poses1_by_index[index]
        for index in only_in_2:
            fused_by_index[index] = shifted_poses2_by_index[index]

        report(
            88,
            f"Fusion : {len(common_indices)} frames combinées, "
            f"{len(only_in_1) + len(only_in_2)} en source unique",
        )

        if len(fused_by_index) < 2:
            raise RuntimeError(
                "Pas assez de poses reconstruites (à elles deux) pour produire une trajectoire."
            )

        report(90, "Recalage sur le fps de la caméra cinéma...")
        cinema_fps = self._cinema_fps()
        sorted_indices = sorted(fused_by_index)
        sorted_poses = [fused_by_index[index] for index in sorted_indices]
        output_indices, output_poses = resample_trajectory(
            sorted_indices, sorted_poses, source_fps, cinema_fps
        )

        report(98, "Écriture du fichier de tracking...")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "fps": cinema_fps,
            "frames": [
                {"index": idx, "matrix": pose.matrix.tolist()}
                for idx, pose in zip(output_indices, output_poses)
            ],
        }
        with open(output, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

        report(100, "Tracking terminé")
        return str(output)

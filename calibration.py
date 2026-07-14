import json
import math
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from camera import Camera
from pose import Pose


class Calibration:
    def __init__(self, gopro_model, cinema_video, gopro_video, offset, camera, charuco_board=None):
        self.gopro_model = gopro_model
        self.cinema_video = cinema_video
        self.gopro_video = gopro_video
        self.offset = offset
        self.camera = camera
        self.charuco_board = charuco_board or {
            "dictionary": "DICT_6X6_250",
            "squares_x": 5,
            "squares_y": 7,
            "square_length": 0.04,
            "marker_length": 0.03,
        }

    def _camera_matrix(self):
        width, height = self.camera["resolution"]
        focal_mm = self.camera["focal"]
        sensor_width_mm = self.camera["sensor"]
        if sensor_width_mm == 0:
            raise ValueError("La taille du capteur ne peut pas être zéro.")

        sensor_height_mm = sensor_width_mm * height / width
        fx = focal_mm * width / sensor_width_mm
        fy = focal_mm * height / sensor_height_mm
        cx = width / 2.0
        cy = height / 2.0
        return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64)

    def _create_camera(self, name: str) -> Camera:
        width, height = self.camera["resolution"]
        focal_mm = self.camera["focal"]
        sensor_width_mm = self.camera["sensor"]
        if sensor_width_mm == 0:
            raise ValueError("La taille du capteur ne peut pas être zéro.")

        sensor_height_mm = sensor_width_mm * height / width
        fx = focal_mm * width / sensor_width_mm
        fy = focal_mm * height / sensor_height_mm
        cx = width / 2.0
        cy = height / 2.0

        return Camera(
            name=name,
            model=self.gopro_model,
            width=width,
            height=height,
            fx=fx,
            fy=fy,
            cx=cx,
            cy=cy,
            sensor_width=sensor_width_mm,
            sensor_height=sensor_height_mm,
            focal_length=focal_mm,
        )

    def _camera_to_dict(self, camera: Camera) -> dict:
        return {
            "name": camera.name,
            "model": camera.model,
            "width": camera.width,
            "height": camera.height,
            "fx": camera.fx,
            "fy": camera.fy,
            "cx": camera.cx,
            "cy": camera.cy,
            "distortion": camera.distortion.tolist(),
            "sensor_width": camera.sensor_width,
            "sensor_height": camera.sensor_height,
            "focal_length": camera.focal_length,
            "fps": camera.fps,
        }

    def _create_charuco_board(self):
        if cv2 is None:
            raise ImportError("OpenCV est requis pour Charuco")
        dictionary_name = self.charuco_board["dictionary"]
        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"ArUco dictionary inconnu : {dictionary_name}")
        aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dictionary_name))
        return cv2.aruco.CharucoBoard(
            (int(self.charuco_board["squares_x"]), int(self.charuco_board["squares_y"])),
            float(self.charuco_board["square_length"]),
            float(self.charuco_board["marker_length"]),
            aruco_dict,
        )

    def _rotation_matrix_to_euler(self, r):
        sy = math.sqrt(r[0, 0] * r[0, 0] + r[1, 0] * r[1, 0])
        singular = sy < 1e-6
        if not singular:
            x = math.atan2(r[2, 1], r[2, 2])
            y = math.atan2(-r[2, 0], sy)
            z = math.atan2(r[1, 0], r[0, 0])
        else:
            x = math.atan2(-r[1, 2], r[1, 1])
            y = math.atan2(-r[2, 0], sy)
            z = 0.0
        return {"x": float(math.degrees(x)), "y": float(math.degrees(y)), "z": float(math.degrees(z))}

    def _detect_charuco_pose(self, video_path, progress_callback=None, progress_range=(0, 100)):
        if cv2 is None or np is None or not hasattr(cv2, "aruco"):
            raise ImportError(
                "OpenCV contrib est requis pour Charuco : pip install opencv-contrib-python"
            )

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Impossible d'ouvrir la vidéo : {video_path}")

        board = self._create_charuco_board()
        detector = cv2.aruco.CharucoDetector(board)
        camera_matrix = self._camera_matrix()
        dist_coeffs = np.zeros((5, 1), dtype=np.float64)

        max_frames = 60
        start, end = progress_range
        for frame_index in range(max_frames):
            ok, frame = capture.read()
            if not ok:
                break
            if progress_callback:
                pct = start + (end - start) * (frame_index + 1) / max_frames
                progress_callback(int(pct), f"Analyse de la vidéo ({frame_index + 1}/{max_frames})")

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)
            if charuco_ids is None or len(charuco_ids) < 4:
                continue

            rvec = np.zeros((3, 1), dtype=np.float64)
            tvec = np.zeros((3, 1), dtype=np.float64)
            retval, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
                charuco_corners, charuco_ids, board, camera_matrix, dist_coeffs, rvec, tvec
            )
            if retval:
                rotation_matrix, _ = cv2.Rodrigues(rvec)
                translation = tvec.reshape(3)
                capture.release()
                if progress_callback:
                    progress_callback(int(end), "Pose Charuco détectée")
                return Pose(rotation=rotation_matrix, translation=translation)

        capture.release()
        return None

    def compute(self, output_path: str, progress_callback=None):
        if cv2 is None or np is None or not hasattr(cv2, "aruco"):
            raise ImportError(
                "OpenCV contrib est requis pour Charuco : pip install opencv-contrib-python"
            )

        if not Path(self.gopro_video).exists():
            raise FileNotFoundError(f"Vidéo GoPro introuvable : {self.gopro_video}")
        if not Path(self.cinema_video).exists():
            raise FileNotFoundError(f"Vidéo caméra cinéma introuvable : {self.cinema_video}")

        if progress_callback:
            progress_callback(0, "Préparation des caméras...")
        gopro_camera = self._create_camera("GoPro")
        cinema_camera = self._create_camera("Cinema")

        gopro_pose = self._detect_charuco_pose(self.gopro_video, progress_callback, (5, 50))
        cinema_pose = self._detect_charuco_pose(self.cinema_video, progress_callback, (50, 95))

        if gopro_pose is None or cinema_pose is None:
            raise RuntimeError("Impossible d'extraire la pose Charuco sur l'une des vidéos.")

        if progress_callback:
            progress_callback(95, "Calcul de la transformation du rig...")
        rig_pose = Pose.from_matrix(cinema_pose.matrix @ gopro_pose.inverse().matrix)

        result = {
            "camera": {
                "gopro_camera": self._camera_to_dict(gopro_camera),
                "cinema_camera": self._camera_to_dict(cinema_camera),
            },
            "charuco_board": self.charuco_board,
            "rig_transform": {
                "translation": {
                    "x": float(rig_pose.translation[0]),
                    "y": float(rig_pose.translation[1]),
                    "z": float(rig_pose.translation[2]),
                },
                "rotation_euler": self._rotation_matrix_to_euler(rig_pose.rotation),
                "rotation_matrix": rig_pose.rotation.tolist(),
                "matrix": rig_pose.matrix.tolist(),
            },
            "metadata": {
                "gopro_model": self.gopro_model,
                "cinema_video": self.cinema_video,
                "gopro_video": self.gopro_video,
                "offset": self.offset,
            },
        }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

        if progress_callback:
            progress_callback(100, "Calibration terminée")

        return str(output)

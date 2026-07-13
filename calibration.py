import json
import math
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError as exc:
    cv2 = None
    np = None
    _cv2_import_error = exc

from camera import Camera
from pose import Pose


class Calibration:
    def __init__(self, gopro_model, cinema_video, gopro_video, offset, camera):
        self.gopro_model = gopro_model
        self.cinema_video = cinema_video
        self.gopro_video = gopro_video
        self.offset = offset
        self.camera = camera

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

    def _detect_aruco_pose(self, video_path, marker_length=0.2):
        if cv2 is None or np is None or not hasattr(cv2, "aruco"):
            raise ImportError(
                "OpenCV contrib est requis pour ArUco : pip install opencv-contrib-python"
            )

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Impossible d'ouvrir la vidéo : {video_path}")

        detector_params = cv2.aruco.DetectorParameters_create()
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
        camera = self._create_camera("GoPro")
        camera_matrix = camera.intrinsic_matrix
        dist_coeffs = camera.distortion.reshape(-1, 1)

        for _ in range(30):
            ok, frame = capture.read()
            if not ok:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, aruco_dict, parameters=detector_params
            )

            if ids is not None and len(ids) > 0:
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                    corners, marker_length, camera_matrix, dist_coeffs
                )
                if rvecs is not None and len(rvecs) > 0 and len(tvecs) > 0:
                    rotation_matrix, _ = cv2.Rodrigues(rvecs[0].reshape(3))
                    translation = tvecs[0].reshape(3)
                    return Pose(rotation=rotation_matrix, translation=translation)

        return None

    def compute(self):
        if cv2 is None or np is None or not hasattr(cv2, "aruco"):
            raise ImportError(
                "OpenCV contrib est requis pour ArUco : pip install opencv-contrib-python"
            )

        if not Path(self.gopro_video).exists():
            raise FileNotFoundError(f"Vidéo GoPro introuvable : {self.gopro_video}")
        if not Path(self.cinema_video).exists():
            raise FileNotFoundError(f"Vidéo caméra cinéma introuvable : {self.cinema_video}")

        gopro_camera = self._create_camera("GoPro")
        cinema_camera = self._create_camera("Cinema")

        gopro_pose = self._detect_aruco_pose(self.gopro_video)
        cinema_pose = self._detect_aruco_pose(self.cinema_video)

        rig_pose = Pose()
        if gopro_pose is not None and cinema_pose is not None:
            rig_matrix = cinema_pose.matrix @ gopro_pose.inverse().matrix
            rig_pose = Pose.from_matrix(rig_matrix)

        result = {
            "camera": {
                "gopro_camera": self._camera_to_dict(gopro_camera),
                "cinema_camera": self._camera_to_dict(cinema_camera),
            },
            "rig_transform": {
                "translation": {
                    "x": float(rig_pose.translation[0] if gopro_pose is not None and cinema_pose is not None else self.offset["forward"]),
                    "y": float(rig_pose.translation[1] if gopro_pose is not None and cinema_pose is not None else self.offset["up"]),
                    "z": float(rig_pose.translation[2] if gopro_pose is not None and cinema_pose is not None else self.offset["left"]),
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

        output = Path("data/calibration.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

        return str(output)

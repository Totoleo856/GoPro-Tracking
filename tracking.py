import json
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
from rig import Rig
from trajectory import Trajectory


class Tracker:
    def __init__(self, video, calibration_file):
        self.video = video
        self.calibration = self._load_calibration(calibration_file)
        self.rig = self._build_rig(self.calibration)
        self.charuco_board = self._build_charuco_board(self.calibration["charuco_board"])

    def _load_calibration(self, path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _camera_from_dict(self, data):
        distortion = data.get("distortion", [])
        return Camera(
            name=data.get("name", ""),
            model=data.get("model", ""),
            width=int(data["width"]),
            height=int(data["height"]),
            fx=float(data["fx"]),
            fy=float(data["fy"]),
            cx=float(data["cx"]),
            cy=float(data["cy"]),
            distortion=np.asarray(distortion, dtype=np.float64),
            sensor_width=float(data.get("sensor_width", 0.0)),
            sensor_height=float(data.get("sensor_height", 0.0)),
            focal_length=float(data.get("focal_length", 0.0)),
            fps=float(data.get("fps", 0.0)),
        )

    def _build_rig(self, calibration):
        cinema_camera = self._camera_from_dict(calibration["camera"]["cinema_camera"])
        tracker_camera = self._camera_from_dict(calibration["camera"]["gopro_camera"])
        rotation = np.array(calibration["rig_transform"]["rotation_matrix"], dtype=np.float64)
        translation_data = calibration["rig_transform"]["translation"]
        translation = np.array(
            [
                float(translation_data["x"]),
                float(translation_data["y"]),
                float(translation_data["z"]),
            ],
            dtype=np.float64,
        )
        gopro_to_cinema = Pose(rotation=rotation, translation=translation)
        return Rig(cinema_camera=cinema_camera, tracker_camera=tracker_camera, gopro_to_cinema=gopro_to_cinema)

    def _build_charuco_board(self, board_data):
        if cv2 is None:
            raise ImportError("OpenCV est requis pour Charuco")
        dictionary_name = board_data["dictionary"]
        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"ArUco dictionary inconnu : {dictionary_name}")
        aruco_dict = cv2.aruco.Dictionary_get(getattr(cv2.aruco, dictionary_name))
        return cv2.aruco.CharucoBoard_create(
            int(board_data["squares_x"]),
            int(board_data["squares_y"]),
            float(board_data["square_length"]),
            float(board_data["marker_length"]),
            aruco_dict,
        )

    def _camera_matrix_from_camera(self, camera: Camera):
        return np.array(
            [
                [camera.fx, 0.0, camera.cx],
                [0.0, camera.fy, camera.cy],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

    def _detect_pose_for_frame(self, frame):
        if cv2 is None or np is None or not hasattr(cv2, "aruco"):
            raise ImportError(
                "OpenCV contrib est requis pour Charuco : pip install opencv-contrib-python"
            )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        params = cv2.aruco.DetectorParameters_create()
        corners, ids, _ = cv2.aruco.detectMarkers(
            gray, self.charuco_board.dictionary, parameters=params
        )
        if ids is None or len(ids) == 0:
            return None

        _, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            corners, ids, gray, self.charuco_board
        )
        if charuco_ids is None or len(charuco_ids) < 4:
            return None

        camera_matrix = self._camera_matrix_from_camera(self.rig.tracker_camera)
        dist_coeffs = np.asarray(self.rig.tracker_camera.distortion, dtype=np.float64).reshape(-1, 1)

        retval, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
            charuco_corners,
            charuco_ids,
            self.charuco_board,
            camera_matrix,
            dist_coeffs,
        )
        if not retval:
            return None

        rotation_matrix, _ = cv2.Rodrigues(rvec)
        translation = tvec.reshape(3)
        return Pose(rotation=rotation_matrix, translation=translation)

    def _frame_rate(self, capture):
        fps = capture.get(cv2.CAP_PROP_FPS)
        return float(fps if fps > 0.0 else 25.0)

    def run(self):
        if not Path(self.video).exists():
            raise FileNotFoundError(self.video)
        if cv2 is None or np is None:
            raise ImportError(
                "OpenCV est requis pour le tracking : pip install opencv-contrib-python"
            )

        capture = cv2.VideoCapture(str(self.video))
        if not capture.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la vidéo : {self.video}")

        trajectory = Trajectory()
        trajectory.fps = self._frame_rate(capture)

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            pose = self._detect_pose_for_frame(frame)
            if pose is not None:
                cinema_pose = self.rig.transform_tracker_to_cinema(pose)
                trajectory.add_pose(cinema_pose)

        capture.release()

        if len(trajectory) == 0:
            raise RuntimeError("Aucune pose Charuco détectée pendant le tracking.")

        output = Path("data/tracking.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "fps": trajectory.fps,
            "frames": [
                {"index": idx, "matrix": pose.matrix.tolist()}
                for idx, pose in enumerate(trajectory.poses)
            ],
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        return str(output)

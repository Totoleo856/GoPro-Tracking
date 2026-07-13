from __future__ import annotations

from dataclasses import dataclass

from camera import Camera
from pose import Pose


@dataclass
class Rig:
    """
    Représente le rig physique constitué de la caméra cinéma
    et de la (ou des) GoPro de tracking.

    La pose `gopro_to_cinema` est une transformation rigide
    déterminée lors de la calibration.
    """

    cinema_camera: Camera
    tracker_camera: Camera

    gopro_to_cinema: Pose = Pose()

    def transform_tracker_to_cinema(self, tracker_pose: Pose) -> Pose:
        rotation = self.gopro_to_cinema.rotation @ tracker_pose.rotation
        translation = (
            self.gopro_to_cinema.rotation @ tracker_pose.translation
            + self.gopro_to_cinema.translation
        )
        return Pose(rotation=rotation, translation=translation)

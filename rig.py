from __future__ import annotations

from dataclasses import dataclass

from .camera import Camera
from .pose import Pose


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

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Camera:
    """
    Représentation d'une caméra.

    Les paramètres intrinsèques correspondent au modèle pinhole.
    Les coefficients de distorsion sont conservés pour les moteurs
    qui savent les exploiter (OpenCV, COLMAP, etc.).
    """

    name: str = ""
    model: str = ""

    width: int = 0
    height: int = 0

    fx: float = 0.0
    fy: float = 0.0
    cx: float = 0.0
    cy: float = 0.0

    distortion: np.ndarray = field(
        default_factory=lambda: np.zeros(5, dtype=np.float64)
    )

    sensor_width: float = 0.0
    sensor_height: float = 0.0

    focal_length: float = 0.0

    fps: float = 0.0

    @property
    def intrinsic_matrix(self) -> np.ndarray:
        """
        Retourne la matrice intrinsèque.
        """

        return np.array(
            [
                [self.fx, 0.0, self.cx],
                [0.0, self.fy, self.cy],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

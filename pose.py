from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Pose:
    """
    Représente une pose 3D.

    La rotation est stockée sous forme de matrice 3x3.
    La translation est stockée sous forme d'un vecteur (x, y, z).
    """

    rotation: np.ndarray = field(
        default_factory=lambda: np.eye(3, dtype=np.float64)
    )

    translation: np.ndarray = field(
        default_factory=lambda: np.zeros(3, dtype=np.float64)
    )

    @property
    def matrix(self) -> np.ndarray:
        """
        Retourne la matrice homogène 4x4.
        """
        T = np.eye(4, dtype=np.float64)
        T[:3, :3] = self.rotation
        T[:3, 3] = self.translation
        return T

    @classmethod
    def from_matrix(cls, matrix: np.ndarray) -> "Pose":
        """
        Construit une pose à partir d'une matrice homogène 4x4.
        """
        return cls(
            rotation=matrix[:3, :3].copy(),
            translation=matrix[:3, 3].copy(),
        )

    def inverse(self) -> "Pose":
        """
        Retourne l'inverse de la pose.
        """
        inv_rotation = self.rotation.T
        inv_translation = -inv_rotation @ self.translation
        return Pose(rotation=inv_rotation, translation=inv_translation)

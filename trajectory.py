from __future__ import annotations

from dataclasses import dataclass, field

from .pose import Pose


@dataclass
class Trajectory:
    """
    Représente une trajectoire caméra.

    Une pose est associée à chaque image de la vidéo.
    L'indice de la liste correspond au numéro de frame.
    """

    poses: list[Pose] = field(default_factory=list)
    fps: float = 0.0

    def __len__(self) -> int:
        return len(self.poses)

    def __getitem__(self, index: int) -> Pose:
        return self.poses[index]

    def add_pose(self, pose: Pose) -> None:
        """Ajoute une pose à la trajectoire."""
        self.poses.append(pose)

    @property
    def frame_count(self) -> int:
        """Nombre de frames de la trajectoire."""
        return len(self.poses)

    @property
    def duration(self) -> float:
        """Durée de la trajectoire en secondes."""
        if self.fps <= 0:
            return 0.0
        return len(self.poses) / self.fps

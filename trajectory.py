from __future__ import annotations

from dataclasses import dataclass, field

from pose import Pose


@dataclass
class Trajectory:
    poses: list[Pose] = field(default_factory=list)
    fps: float = 0.0

    def __len__(self) -> int:
        return len(self.poses)

    def __getitem__(self, index: int) -> Pose:
        return self.poses[index]

    def add_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    @property
    def frame_count(self) -> int:
        return len(self.poses)

    @property
    def duration(self) -> float:
        if self.fps <= 0:
            return 0.0
        return len(self.poses) / self.fps

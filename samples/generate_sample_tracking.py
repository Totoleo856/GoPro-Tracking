"""Génère un fichier tracking.json d'exemple (mouvement de travelling en arc)
pour tester la visionneuse 3D de l'onglet Vérification sans avoir à faire
tourner une vraie calibration/tracking sur des vidéos GoPro.

Usage : python samples/generate_sample_tracking.py
"""

import json
from pathlib import Path

import numpy as np

FPS = 24.0
FRAME_COUNT = 150
RADIUS = 4.0
HEIGHT_BASE = 1.7
HEIGHT_AMPLITUDE = 0.15
ARC_DEGREES = 80.0
LOOK_AT = np.array([0.0, 0.0, 1.2])
WORLD_UP = np.array([0.0, 0.0, 1.0])


def build_rotation(position, look_at, world_up):
    forward = look_at - position
    forward = forward / np.linalg.norm(forward)
    right = np.cross(world_up, forward)
    right = right / np.linalg.norm(right)
    true_up = np.cross(forward, right)

    rotation = np.eye(3)
    rotation[:, 0] = right
    rotation[:, 1] = true_up
    rotation[:, 2] = forward
    return rotation


def main():
    frames = []
    half_arc = np.radians(ARC_DEGREES) / 2.0

    for i in range(FRAME_COUNT):
        t = i / (FRAME_COUNT - 1)
        angle = -half_arc + t * 2 * half_arc

        x = RADIUS * np.sin(angle)
        y = -RADIUS * np.cos(angle)
        z = HEIGHT_BASE + HEIGHT_AMPLITUDE * np.sin(t * 3 * np.pi)

        position = np.array([x, y, z])
        rotation = build_rotation(position, LOOK_AT, WORLD_UP)

        matrix = np.eye(4)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = position

        frames.append({"index": i, "matrix": matrix.tolist()})

    result = {"fps": FPS, "frames": frames}

    output_path = Path(__file__).parent / "sample_tracking.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(f"Écrit : {output_path} ({FRAME_COUNT} poses, {FPS} fps)")


if __name__ == "__main__":
    main()

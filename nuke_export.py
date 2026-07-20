import math

import numpy as np

# Nuke (comme Maya/Blender) utilise localement X-droite, Y-haut, Z-arrière pour sa
# caméra (elle regarde selon -Z) ; OpenCV/le reste du projet utilise X-droite, Y-bas,
# Z-avant. Même correctif d'axes que pour Blender (rotation propre à 180° des axes
# locaux Y et Z, pas un miroir) : cf. blender_export.py pour le détail.
_OPENCV_TO_YUP_CAMERA_AXES = np.diag([1.0, -1.0, -1.0])


def _rotation_matrix_to_xyz_euler_degrees(rotation):
    """
    Angles d'Euler XYZ (en degrés) tels que rotation = Rz(z) @ Ry(y) @ Rx(x) — même
    convention que Calibration._rotation_matrix_to_euler (calibration.py), pour rester
    cohérent avec le reste du projet, et c'est la convention attendue par l'import .chan
    standard (Maya/Nuke/PFTrack/SynthEyes).
    """
    sy = math.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        x = math.atan2(rotation[2, 1], rotation[2, 2])
        y = math.atan2(-rotation[2, 0], sy)
        z = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        x = math.atan2(-rotation[1, 2], rotation[1, 1])
        y = math.atan2(-rotation[2, 0], sy)
        z = 0.0
    return math.degrees(x), math.degrees(y), math.degrees(z)


def generate_chan_file(positions, rotations, frame_indices):
    """
    Génère le contenu d'un fichier .chan (frame tx ty tz rx ry rz), le format standard
    d'échange d'animation caméra Maya/Nuke/PFTrack/SynthEyes. Dans Nuke : créer un nœud
    Camera, clic droit sur le champ "translate" ou "rotate" > Import chan file...

    positions : (N, 3) centres caméra dans le monde, mètres (repère déjà corrigé, cf.
                MainWindow._load_tracking_positions : Z = vers le haut).
    rotations : (N, 3, 3) matrices monde->caméra, même repère/convention que positions.
    frame_indices : index de frame réel (utilisé tel quel comme numéro de frame).
    """
    if len(positions) == 0:
        raise ValueError("Aucune pose à exporter.")

    lines = []
    for i in range(len(positions)):
        cam_to_world = rotations[i].T
        yup_axes = cam_to_world @ _OPENCV_TO_YUP_CAMERA_AXES
        rx, ry, rz = _rotation_matrix_to_xyz_euler_degrees(yup_axes)
        px, py, pz = positions[i]
        frame = int(frame_indices[i])
        lines.append(
            f"{frame}\t{px:.6f}\t{py:.6f}\t{pz:.6f}\t{rx:.6f}\t{ry:.6f}\t{rz:.6f}"
        )

    return "\n".join(lines)

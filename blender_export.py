import numpy as np

# OpenCV/le reste du projet : axes caméra locaux X-droite, Y-bas, Z-avant (la caméra
# regarde selon +Z). Blender : X-droite, Y-haut, Z-arrière (la caméra regarde selon -Z).
# Passer de l'un à l'autre revient à inverser les axes locaux Y et Z de la caméra
# (rotation propre, cf. investigation sur l'axe Z de la visionneuse : inverser deux axes
# ensemble reste une rotation, pas un miroir).
_OPENCV_TO_BLENDER_CAMERA_AXES = np.diag([1.0, -1.0, -1.0])


def _rotation_matrix_to_quaternion(rotation):
    """
    Convertit une matrice de rotation 3x3 propre en quaternion (w, x, y, z). Utilisé
    plutôt que des angles d'Euler pour l'animation Blender générée : pas de discontinuité
    ni de gimbal lock possible entre deux frames consécutives.
    """
    trace = np.trace(rotation)
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (rotation[2, 1] - rotation[1, 2]) * s
        y = (rotation[0, 2] - rotation[2, 0]) * s
        z = (rotation[1, 0] - rotation[0, 1]) * s
    elif rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2])
        w = (rotation[2, 1] - rotation[1, 2]) / s
        x = 0.25 * s
        y = (rotation[0, 1] + rotation[1, 0]) / s
        z = (rotation[0, 2] + rotation[2, 0]) / s
    elif rotation[1, 1] > rotation[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2])
        w = (rotation[0, 2] - rotation[2, 0]) / s
        x = (rotation[0, 1] + rotation[1, 0]) / s
        y = 0.25 * s
        z = (rotation[1, 2] + rotation[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1])
        w = (rotation[1, 0] - rotation[0, 1]) / s
        x = (rotation[0, 2] + rotation[2, 0]) / s
        y = (rotation[1, 2] + rotation[2, 1]) / s
        z = 0.25 * s
    return float(w), float(x), float(y), float(z)


def generate_blender_script(positions, rotations, frame_indices, fps, focal_length=None, sensor_width=None):
    """
    Génère un script Python à exécuter dans Blender (onglet Scripting > Run Script) qui
    crée une caméra et l'anime avec la trajectoire suivie (position + orientation par
    keyframe, quaternions pour éviter tout gimbal lock).

    positions : (N, 3) centres caméra dans le monde, mètres (repère déjà corrigé, cf.
                MainWindow._load_tracking_positions : Z = vers le haut).
    rotations : (N, 3, 3) matrices monde->caméra, même repère/convention que positions.
    frame_indices : index de frame réel (utilisé tel quel comme numéro de frame Blender).
    fps : fps de la caméra cinéma (0 ou None si inconnu).
    focal_length, sensor_width : en mm, optionnels (depuis le fichier de calibration) ;
                si absents, la caméra Blender créée garde ses réglages optiques par défaut.
    """
    if len(positions) == 0:
        raise ValueError("Aucune pose à exporter.")

    lines = [
        "import bpy",
        "",
        "scene = bpy.context.scene",
    ]
    if fps:
        lines.append(f"scene.render.fps = {int(round(fps))}")
    lines += [
        "",
        "cam_data = bpy.data.cameras.new('TrackedCamera')",
    ]
    if focal_length is not None and sensor_width is not None:
        lines += [
            f"cam_data.lens = {float(focal_length)}",
            f"cam_data.sensor_width = {float(sensor_width)}",
            "cam_data.sensor_fit = 'HORIZONTAL'",
        ]
    lines += [
        "cam_obj = bpy.data.objects.new('TrackedCamera', cam_data)",
        "scene.collection.objects.link(cam_obj)",
        "cam_obj.rotation_mode = 'QUATERNION'",
        "",
    ]

    for i in range(len(positions)):
        cam_to_world = rotations[i].T
        blender_axes = cam_to_world @ _OPENCV_TO_BLENDER_CAMERA_AXES
        w, x, y, z = _rotation_matrix_to_quaternion(blender_axes)
        px, py, pz = positions[i]
        frame = int(frame_indices[i])
        lines += [
            f"cam_obj.location = ({px:.6f}, {py:.6f}, {pz:.6f})",
            f"cam_obj.rotation_quaternion = ({w:.6f}, {x:.6f}, {y:.6f}, {z:.6f})",
            f"cam_obj.keyframe_insert(data_path='location', frame={frame})",
            f"cam_obj.keyframe_insert(data_path='rotation_quaternion', frame={frame})",
            "",
        ]

    return "\n".join(lines)

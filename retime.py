import math

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from pose import Pose


def resample_trajectory(frame_indices, poses, source_fps, target_fps):
    """
    Rééchantillonne une trajectoire (poses monde->caméra, échantillonnées à
    des indices de frame entiers à `source_fps`) sur une nouvelle grille
    temporelle uniforme à `target_fps` (typiquement le fps de la caméra
    cinéma, différent de celui de la GoPro).

    L'interpolation se fait en espace caméra->monde (centre caméra +
    orientation), l'espace physiquement pertinent pour un mouvement de
    caméra continu — la convention de sortie monde->caméra est restaurée
    en fin de fonction pour rester compatible avec le schéma existant.

    Ne produit des échantillons que dans la plage de temps couverte par la
    trajectoire source (pas d'extrapolation).
    """
    if len(frame_indices) < 2:
        raise ValueError("Il faut au moins 2 poses pour rééchantillonner une trajectoire.")
    if target_fps <= 0:
        raise ValueError("Le fps cible (caméra cinéma) doit être strictement positif.")

    order = np.argsort(frame_indices)
    sorted_indices = np.asarray(frame_indices)[order]
    sorted_poses = [poses[i] for i in order]

    times = sorted_indices / source_fps
    cam_to_world = [p.inverse() for p in sorted_poses]
    centers = np.array([p.translation for p in cam_to_world])
    rotations = Rotation.from_matrix(np.array([p.rotation for p in cam_to_world]))
    slerp = Slerp(times, rotations)

    start_time, end_time = float(times[0]), float(times[-1])
    first_output_frame = math.ceil(start_time * target_fps)
    last_output_frame = math.floor(end_time * target_fps)
    if first_output_frame > last_output_frame:
        raise RuntimeError(
            "La plage temporelle de la trajectoire est trop courte pour le fps cible demandé."
        )

    output_indices = list(range(first_output_frame, last_output_frame + 1))
    output_times = np.array(output_indices, dtype=np.float64) / target_fps

    interp_centers = np.column_stack(
        [np.interp(output_times, times, centers[:, axis]) for axis in range(3)]
    )
    interp_rotations = slerp(output_times)

    output_poses = []
    for center, rotation in zip(interp_centers, interp_rotations):
        cam_to_world_pose = Pose(rotation=rotation.as_matrix(), translation=center)
        output_poses.append(cam_to_world_pose.inverse())

    return output_indices, output_poses

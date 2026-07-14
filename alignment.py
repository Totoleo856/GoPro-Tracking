import numpy as np


def umeyama_alignment(source_points, target_points):
    """
    Calcule la transformation de similarité (échelle, rotation, translation)
    qui fait passer au mieux (au sens des moindres carrés) de `source_points`
    vers `target_points` :

        target ≈ scale * (rotation @ source) + translation

    Algorithme de Umeyama (1991), solution fermée par SVD.

    Paramètres
    ----------
    source_points, target_points : np.ndarray de forme (N, 3), N >= 3.

    Retourne
    --------
    (scale: float, rotation: np.ndarray (3, 3), translation: np.ndarray (3,))
    """
    source_points = np.asarray(source_points, dtype=np.float64)
    target_points = np.asarray(target_points, dtype=np.float64)

    if source_points.shape != target_points.shape:
        raise ValueError("source_points et target_points doivent avoir la même forme.")
    if source_points.shape[0] < 3:
        raise ValueError("Il faut au moins 3 points pour calculer un recalage fiable.")

    n, dim = source_points.shape

    source_mean = source_points.mean(axis=0)
    target_mean = target_points.mean(axis=0)
    source_centered = source_points - source_mean
    target_centered = target_points - target_mean

    covariance = (target_centered.T @ source_centered) / n
    u, singular_values, vt = np.linalg.svd(covariance)

    s = np.eye(dim)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        s[-1, -1] = -1.0

    rotation = u @ s @ vt

    source_variance = (source_centered ** 2).sum(axis=1).mean()
    scale = float(np.trace(np.diag(singular_values) @ s) / source_variance)

    translation = target_mean - scale * (rotation @ source_mean)

    return scale, rotation, translation


def robust_umeyama_alignment(source_points, target_points, max_iterations=5, outlier_threshold=3.0):
    """
    Comme `umeyama_alignment`, mais rejette itérativement les correspondances
    dont le résidu après recalage est aberrant (> outlier_threshold fois la
    médiane des résidus), avant de recalculer un recalage final sur les
    points restants.

    Utile ici car les détections Charuco en bord de fenêtre (planche petite
    ou légèrement floue) peuvent être ponctuellement très bruitées et
    fausser un simple ajustement aux moindres carrés.

    Retourne
    --------
    (scale, rotation, translation, inlier_mask: np.ndarray[bool] de forme (N,))
    """
    source_points = np.asarray(source_points, dtype=np.float64)
    target_points = np.asarray(target_points, dtype=np.float64)

    mask = np.ones(len(source_points), dtype=bool)
    scale, rotation, translation = umeyama_alignment(source_points, target_points)

    for _ in range(max_iterations):
        scale, rotation, translation = umeyama_alignment(source_points[mask], target_points[mask])
        residuals = np.linalg.norm(
            scale * (source_points @ rotation.T) + translation - target_points, axis=1
        )
        median_residual = max(float(np.median(residuals[mask])), 1e-9)
        threshold = outlier_threshold * median_residual
        new_mask = residuals < threshold

        if new_mask.sum() < 3 or np.array_equal(new_mask, mask):
            mask = new_mask if new_mask.sum() >= 3 else mask
            break
        mask = new_mask

    return scale, rotation, translation, mask

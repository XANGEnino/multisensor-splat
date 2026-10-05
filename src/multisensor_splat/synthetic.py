import numpy as np
import itertools

def make_cube(center, size, points_per_edge):
    half_size = size / 2
    center = np.asarray(center, dtype=float)
    signs = np.array(list(itertools.product([-1, 1], repeat=3)))
    corners = center + half_size * signs

    edges = [(i, j) for i, j in itertools.combinations(range(8), 2) if np.sum(signs[i] != signs[j]) == 1]

    t = np.linspace(0, 1, points_per_edge)[:, None]
    pts = np.vstack([corners[i] + t * (corners[j] - corners[i]) for i, j in edges])
    return np.unique(pts, axis=0)


def make_ground_grid(extent, spacing, z=0.0):
    first_corner = np.array([-extent * spacing, -extent * spacing, z])

    t = np.linspace(0, 1, 2 * extent + 1)[:, None]
    ground_line = first_corner + t * np.array([2 * extent * spacing, 0., 0.])
    pts = np.vstack([ground_line[i] + t * np.array([0., 2 * extent * spacing, 0.]) for i in range(ground_line.shape[0])])
    return np.unique(pts, axis=0)

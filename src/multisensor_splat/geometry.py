'''
Visualization for multisensor splat data.
Conventions:
- Camera frame:
    - x: right
    - y: down
    - z: forward
- Point Arrays:
    - always shape (N, 2) for 2D points (in meters)
    - always shape (N, 3) for 3D points (in meters)
- Poses:
    - (4, 4) homogeneous matrices named by direction
    - e.g., T_cam_world for world -> camera
'''

import numpy as np

# Homogeneous coords
def to_homogeneous(points):
    return np.hstack([points, np.ones((points.shape[0], 1), dtype=points.dtype)])

def from_homogeneous(points_h):
    return points_h[:, :-1] / points_h[:, -1:]

# Transforms
def make_transform(R, t):
    return np.vstack([np.hstack([R, t[:, None]]), np.array([0, 0, 0, 1])])

def invert_transform(T):
    R = T[:-1, :-1]
    t = T[:-1, -1]
    return make_transform(R.T, -R.T @ t)

def transform_points(T, points):
    points_h = to_homogeneous(points)
    points_transformed = points_h @ T.T
    return from_homogeneous(points_transformed)

# Intrinsics
def make_intrinsics(fx, fy, cx, cy):
    return np.array([[fx,  0, cx],
                     [ 0, fy, cy],
                     [ 0,  0,  1]])

# Projection
def project(points_cam, K):
    K_padded = np.hstack([K, np.zeros((K.shape[0], 1), dtype=points_cam.dtype)])
    return from_homogeneous(to_homogeneous(points_cam) @ K_padded.T), points_cam[:, -1:]

def unproject(uv, depth, K):
    K_inv = np.linalg.inv(K)
    return (to_homogeneous(uv) @ K_inv.T) * depth[:, None]

def in_image_mask(uv, depth, width, height):
    uv = np.asarray(uv).reshape(-1, 2)
    depth = np.asarray(depth).reshape(-1)
    mask = (depth > 0) & ((uv >= 0) & (uv < np.array([width, height]))).all(axis=-1)
    return mask

def look_at(eye, target, up=(0, 0, 1)):
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    return make_transform(np.column_stack([right, down, forward]), eye)

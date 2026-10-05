import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
from multisensor_splat.geometry import *

# Colored by depth
def plot_projection(image, uv, depth, ax=None, max_depth=50):
    ax = ax or plt.gca()
    ax.imshow(image)
    h, w = image.shape[:2]
    m = (uv[:, 0] >= 0) & (uv[:, 0] < w) & (uv[:, 1] >= 0) & (uv[:, 1] < h)
    sc = ax.scatter(uv[m, 0], uv[m, 1], c=depth[m], s=1, cmap="turbo", vmin=0, vmax=max_depth)
    
    cax = make_axes_locatable(ax).append_axes("right", size="2%", pad = 0)
    plt.colorbar(sc, cax=cax, label="depth [m]")
    
    ax.set_axis_off()
    return ax 

def plot_reflectance(image, uv, depth, reflectance, ax=None, max_depth=50, point_size=1):
    ax = ax or plt.gca()
    ax.imshow(image)
    h, w = image.shape[:2]

    uv = np.asarray(uv).reshape(-1, 2)
    depth = np.asarray(depth).reshape(-1)
    reflectance = np.asarray(reflectance).reshape(-1)
    
    mask = in_image_mask(uv, depth, w, h) & (depth < max_depth)
    r = reflectance[mask]
    sc = ax.scatter(uv[mask, 0], uv[mask, 1], c=r, cmap="gray", s=point_size,
                    vmin=np.percentile(r, 1), vmax=np.percentile(r, 99))

    cax = make_axes_locatable(ax).append_axes("right", size="2%", pad = 0)
    plt.colorbar(sc, cax=cax, fraction=0.03, label="reflectance")
    ax.set_axis_off()
    return ax 

def draw_camera_frustum(ax3d, T_world_cam, K, width, height, scale=1.0, color="tab:blue"):
    corners_cam = np.array([[0, 0],
                        [width, 0],
                        [width, height],
                        [0, height]])
    corners_cam = transform_points(np.linalg.inv(K), corners_cam)
    corners_cam = to_homogeneous(corners_cam)
    corners_cam *= scale
    corners_cam = np.vstack([np.zeros((1, 3)), corners_cam])
    pts_world = transform_points(T_world_cam, corners_cam)

    # Build frustum
    apex, corners = pts_world[0], pts_world[1:]
    base = np.vstack([corners, corners[:1]])
    ax3d.plot(base[:, 0], base[:, 1], base[:, 2], color=color)
    for c in corners:
        ax3d.plot([apex[0], c[0]], [apex[1], c[1]], [apex[2], c[2]], color=color)

    # Build small "Up" triangle
    tri_px = np.array([[width, 0.3 * height],
                       [width, 0.7 * height],
                       [1.2 * width, 0.5 * height]], dtype=float)

    tri_cam = to_homogeneous(transform_points(np.linalg.inv(K), tri_px)) * scale
    tri = transform_points(T_world_cam, tri_cam)

    tri = np.vstack([tri, tri[:1]])
    ax3d.plot(tri[:, 0], tri[:, 1], tri[:, 2], color="tab:red")

    return ax3d
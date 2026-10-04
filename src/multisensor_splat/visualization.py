import matplotlib.pyplot as plt

# Colored by depth
def plot_projection(image, uv, depth, ax=None, max_depth=50):
    ax = ax or plt.gca()
    ax.imshow(image)
    h, w = image.shape[:2]
    m = (uv[:, 0] >= 0) & (uv[:, 0] < w) & (uv[:, 1] >= 0) & (uv[:, 1] < h)
    sc = ax.scatter(uv[m, 0], uv[m, 1], c=depth[m], s=1, cmap="turbo", vmin=0, vmax=max_depth)
    plt.colorbar(sc, ax=ax, label="depth [m]")
    ax.set_axis_off()
    return ax

def draw_camera_frustum(ax3d, T_world_cam, K, width, height, scale=1.0):
    pass
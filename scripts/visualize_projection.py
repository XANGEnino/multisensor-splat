#!/usr/bin/env python3
"""
Regenerate the README example images in docs/images from the notebooks' code.

    synthetic_projection.png        notebook 01: cube + ground grid in 3D and projected
    kitti_camera_frame.png          notebook 02: raw camera image
    kitti_lidar_depth.png           notebook 02: LiDAR projected, coloured by depth
    kitti_lidar_reflectance.png     notebook 02: LiDAR projected, coloured by reflectance

The KITTI images need the sample data (scripts/download_kitti.py).

Usage (from the repository root):
    uv run python scripts/generate_images.py
    uv run python scripts/generate_images.py --frame 3 --out docs/images
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from multisensor_splat.data.kitti import load_dataset, project_lidar
from multisensor_splat.geometry import (
    invert_transform, look_at, make_intrinsics, project, transform_points,
)
from multisensor_splat.synthetic import make_cube, make_ground_grid
from multisensor_splat.visualization import (
    draw_camera_frustum, plot_projection, plot_reflectance,
)

ROOT = Path(__file__).resolve().parents[1]


def save(fig, out_dir, name):
    path = out_dir / name
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def synthetic_projection(out_dir):
    width, height = 640, 480
    K = make_intrinsics(500, 500, 320, 240)
    image = np.ones((height, width, 3), dtype=float)

    pts_world = np.vstack([make_cube(np.array([0., 0., 1.]), 2, 50),
                           make_ground_grid(40, 0.1, 0)])
    T_world_cam = look_at(np.array([2., 1., 2.5]), np.array([0., 0., 1.]))
    pts_cam = transform_points(invert_transform(T_world_cam), pts_world)
    uv, depth = project(pts_cam, K)

    fig = plt.figure(figsize=(12, 5))
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    ax2d = fig.add_subplot(1, 2, 2)

    ax3d.scatter(pts_world[:, 0], pts_world[:, 1], pts_world[:, 2],
                 c=depth[:, 0], s=1, cmap="turbo", vmin=0, vmax=50)
    draw_camera_frustum(ax3d, T_world_cam, K, width, height)
    ax3d.set_aspect("equal")

    plot_projection(image, uv, depth, ax2d)
    save(fig, out_dir, "synthetic_projection.png")


def kitti_images(out_dir, base_dir, date, drive, frame, cam):
    data = load_dataset(base_dir, date, drive, frames=range(frame, frame + 1))
    img, uv, depth, reflectance = project_lidar(data, idx=0, cam=cam)

    # Lossless copy of the camera image, at its native resolution.
    path = out_dir / "kitti_camera_frame.png"
    plt.imsave(path, img)
    print(f"  {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")

    fig, ax = plt.subplots()
    plot_projection(img, uv, depth, ax)
    save(fig, out_dir, "kitti_lidar_depth.png")

    fig, ax = plt.subplots()
    plot_reflectance(img, uv, depth, reflectance, ax, max_depth=500)
    save(fig, out_dir, "kitti_lidar_reflectance.png")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=ROOT / "docs" / "images", help="output directory")
    p.add_argument("--kitti-dir", type=Path, default=ROOT / "data" / "kitti", help="pykitti basedir")
    p.add_argument("--date", default="2011_09_26")
    p.add_argument("--drive", default="0001")
    p.add_argument("--frame", type=int, default=0, help="KITTI frame index")
    p.add_argument("--cam", type=int, default=2, help="camera index (2 = left colour)")
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Writing images to {args.out}")
    synthetic_projection(args.out)
    kitti_images(args.out, str(args.kitti_dir), args.date, args.drive, args.frame, args.cam)


if __name__ == "__main__":
    main()

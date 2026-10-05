import pykitti as kitti
from multisensor_splat.geometry import *

'''
Default values for the download script
BASE_DIR = Path(os.environ.get("KITTI_DIR", Path(__file__).resolve().parents[3] / "data" / "kitti"))
DATE = "2011_09_26"
DRIVE = "0001"
'''

def load_dataset(basedir, date, drive, frames=range(0, 10)):
    return kitti.raw(basedir, date, drive, frames=frames)

def load_scan(data, idx):
    velo = data.get_velo(idx)
    pts, reflectance = velo[:, :3], velo[:, 3]
    return pts, reflectance

def get_lidar_to_camera(calib, cam):
    return getattr(calib, f"T_cam{cam}_velo"), getattr(calib, f"K_cam{cam}")

def lidar_to_camera(pts, T_cam_velo):
    return transform_points(T_cam_velo, pts)

def project_to_image(pts_cam, K):
    return project(pts_cam, K)

def filter_visible(img_shape, uv, depth, *arrays):
    width, height = img_shape
    mask = in_image_mask(uv, depth, width, height)
    return (uv[mask], depth[mask]) + tuple([a[mask] for a in arrays])

def project_lidar(data, idx, cam):
    pts, reflectance = load_scan(data, idx)
    T_cam_velo, K_cam = get_lidar_to_camera(data.calib, cam)
    pts_cam = lidar_to_camera(pts, T_cam_velo)
    uv, depth = project_to_image(pts_cam, K_cam)

    img = getattr(data, f"get_cam{cam}")(idx)
    width, height = img.size
    uv, depth, reflectance = filter_visible((width, height), uv, depth, reflectance)
    return img, uv, depth, reflectance
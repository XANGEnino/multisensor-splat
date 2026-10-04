import numpy as np
 
from multisensor_splat.geometry import *
 
POINTS = np.array([[0.0, 0.0, 1.0], [1.0, -2.0, 4.0], [-1.5, 0.5, 3.0]])
K = make_intrinsics(500.0, 400.0, 320.0, 240.0)
 
 
def test_homogeneous():
    np.testing.assert_allclose(from_homogeneous(to_homogeneous(POINTS)), POINTS, atol=1e-9)
 
 
def test_transform():
    R = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    T = make_transform(R, np.array([1.0, 2.0, 3.0]))
    result = transform_points(invert_transform(T), transform_points(T, POINTS))
    np.testing.assert_allclose(result, POINTS, atol=1e-5)
 
 
def test_projection():
    pixels = project(POINTS, K)
    np.testing.assert_allclose(unproject(pixels, POINTS[:, 2], K), POINTS, atol=1e-9)
 
 
def test_look_at():
    eye, target = np.array([1.0, -5.0, 2.0]), np.array([0.0, 0.0, 0.0])
    target_cam = transform_points(invert_transform(look_at(eye, target)), target[None])
    np.testing.assert_allclose(target_cam, [[0.0, 0.0, np.linalg.norm(target - eye)]], atol=1e-9)
 
 
if __name__ == "__main__":
    for test in [test_homogeneous, test_transform, test_projection, test_look_at]:
        test()
        print(f"{test.__name__} passed")
 
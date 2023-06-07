import cv2
import numpy as np


def projection_on_sensor():
    real_coord = np.array([[[2,3,0], [1,2,3]]], np.float32)
    print("real_coord", real_coord)
    print(real_coord.shape)

    # Convert real coord system to homogeneous coordinates
    real_coord_column = np.column_stack(real_coord)
    print("real_coord_column\n", real_coord_column)
    print(real_coord_column.shape)

    N = real_coord_column.shape[0]
    real_coord_hom = np.hstack((real_coord_column, np.ones((N,1))))
    print('N', N)
    print("real_coord_hom\n", real_coord_hom)


    # # Compute the camera coordinates
    rvecs = [np.array([[ 0.61428556],
        [-1.47077786],
        [-0.64098175]])]

    tvecs = [np.array([[ 44.78812006],
        [-18.2397174 ],
        [136.88302954]])]
    
    mtx = np.array([[ 3.62916898e+03,    0., 1.58513866e+03],
                                 [    0., 3.77369633e+03, 2.10494246e+03],
                                 [    0.,    0.,           1.]])

    R = cv2.Rodrigues(rvecs[0])[0]
    Extrinsic_matrix = np.append(R, tvecs[0], 1)
    print("R\n", R)
    print("Extrinsic_matrix\n", Extrinsic_matrix)

    camera_coord = np.dot(real_coord_hom, Extrinsic_matrix.T)
    print("camera_coord\n", camera_coord)

    # Convert camera coord in normalised image plane
    camera_coord /= camera_coord[:,-1][:, np.newaxis]
    print("camera_coord\n", camera_coord)
    norm_proj = camera_coord[:,:-1]
    print("norm_proj\n", norm_proj)

    # distortion_coefficients = np.ones(20)
    distortion_coefficients = np.array([1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14., 15., 16., 17., 18., 19., 20.])
    
    distorted_proj = distorsion_warp_function(norm_proj=norm_proj, distortion_coefficients=distortion_coefficients)
    print(distorted_proj)

    distorted_proj_hom = np.hstack((distorted_proj, np.ones((distorted_proj.shape[0],1))))
    print("distorted_proj_hom\n", distorted_proj_hom)

    sensor_project = np.dot(distorted_proj_hom, mtx[:-1].T)
    print("sensor_project\n", sensor_project)

    return sensor_project


def distorsion_warp_function(norm_proj, distortion_coefficients):
    x, y = norm_proj[:, 0], norm_proj[:, 1]

    non_linear_vector = np.column_stack([
        np.ones_like(x),
        x,
        y,
        x**2,
        y**2,
        x**3,
        y**3,
        x*y,
        x*y**2,
        x**2*y
    ])

    param = np.zeros((2, 10))
    param[:2, :10] = distortion_coefficients.reshape(2, 10)
    print("distortion_coefficients\n", distortion_coefficients)
    print("param\n", param)

    distorted_points = np.dot(non_linear_vector, param.T)

    return distorted_points

# projection_on_sensor()

def reprojection_error(): #param, real_coord, image_coord, rvecs, tvecs):

    # distortion_coefficients = param

    img_coord_reprojected = projection_on_sensor()

    image_coord = np.array([[[7000, 55000], [6800, 55200]]], np.float32)
    print(image_coord)
    image_coord = image_coord[0]
    print(image_coord)

    tot_err = np.linalg.norm(image_coord-img_coord_reprojected) / len(img_coord_reprojected)

    print(image_coord - img_coord_reprojected)

    print(tot_err)

def optimise_calibration(real_coord, image_coord, mtx, rvecs, tvecs):

    fx = 0 # mtx[0,0]
    fy = 0 # mtx[1,1]
    cx = 0 # mtx[0,2]
    cy = 0 # mtx [1,2]
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    param = np.array([fx, fy, cx, cy, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t])
    # k1, k2, p1, p2, k3 = 0, 0, 0, 0, 0
    # param = np.array([fx, fy, cx, cy, k1, k2, p1, p2, k3])
    result = minimize(minimize_function, param, args = (real_coord, image_coord, rvecs, tvecs), method="Powell")

    return result

reprojection_error()



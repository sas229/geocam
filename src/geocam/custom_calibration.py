import cv2
import numpy as np
import matplotlib.pyplot as plt
import glob 

from cv2 import aruco  
from pathlib import Path 
from scipy.stats import norm
from scipy.optimize import minimize


def get_cloud_of_3d_points(charuco_num_of_columns:int = 44, 
                           charuco_num_of_rows:int = 28,
                           sample_height_mm:float = 140,
                           sample_diameter_mm:float = 70,
                           flag1:bool = False, 
                           flag2:bool = False) -> dict:
    """
    Generate a cloud of 3D points based on the given parameters.

    Parameters
    ----------
    charuco_num_of_columns : int, optional
        Number of columns in the charuco board, by default 44.
    charuco_num_of_rows : int, optional
        Number of rows in the charuco board, by default 28.
    sample_height_mm : float, optional
        Height of the sample in millimeters, by default 140.
    sample_diameter_mm : float, optional
        Diameter of the sample in millimeters, by default 70.
    flag1 : bool, optional
        Whether to plot the generated points or not, by default False.
    flag2 : bool, optional
        Whether to plot the corners ids or not, by default False.

    Returns
    -------
    dict
        Dictionary containing the 3D coordinates of each corner.
    """

    horz_num_of_squares = charuco_num_of_columns - 1
    sample_radius_mm = 0.5 * sample_diameter_mm
    charuco_square_length_mm = round((np.pi*sample_diameter_mm)/charuco_num_of_columns)
    elementary_angle_rad = charuco_square_length_mm / sample_radius_mm


    num_of_corners = (charuco_num_of_rows - 1) * (charuco_num_of_columns - 1)
    x_coordinates = np.zeros(num_of_corners)
    y_coordinates = np.zeros(num_of_corners)
    z_coordinates = np.zeros(num_of_corners)

    for ver_corner_index in range(charuco_num_of_rows - 1):
        for horz_corner_index in range(charuco_num_of_columns - 1):
            corner_id = horz_corner_index + ver_corner_index * horz_num_of_squares
            theta = horz_corner_index * elementary_angle_rad
            x_coordinates[corner_id] = sample_radius_mm * np.cos(theta) 
            y_coordinates[corner_id] = sample_radius_mm * np.sin(theta)
            # z_coordinates[corner_id] = sample_height_mm - (ver_corner_index * charuco_square_length_mm + charuco_square_length_mm)
            z_coordinates[corner_id] = (ver_corner_index * charuco_square_length_mm + charuco_square_length_mm)

    coords_3d_points = {
        corner_id: np.array([x, y, z])
        for corner_id, x, y, z in zip(range(num_of_corners), x_coordinates, y_coordinates, z_coordinates)
    }

    if flag1:
        # plot the points
        plot_3d_points(coords_3d_points, flag=flag2)
    
    return coords_3d_points

def plot_3d_points(coords_3d_points: dict, flag: bool = False):
    """
    Plot the 3D points in a scatter plot.

    Parameters
    ----------
    coords_3d_points : dict
        Dictionary containing the 3D coordinates of each corner.
    flag : bool, optional
        Whether to plot the corners ids or not, by default False.
    
    Returns
    -------
    None
        The function plots the 3D points.

    """
    x_coordinates = np.array([])
    y_coordinates = np.array([])
    z_coordinates = np.array([])
    corner_ids = np.array([])

    for corner_id, coords in coords_3d_points.items():
        corner_ids = np.append(corner_ids, corner_id)
        x_coordinates = np.append(x_coordinates, coords[0])
        y_coordinates = np.append(y_coordinates, coords[1])
        z_coordinates = np.append(z_coordinates, coords[2])

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(x_coordinates, y_coordinates, z_coordinates, marker=".")

    if flag:
        # show the ids of the corners
        for i, corner_id in enumerate(corner_ids):
            label = int(corner_id) if isinstance(corner_id, float) else corner_id
            ax.text(x_coordinates[i], y_coordinates[i], z_coordinates[i], str(label), fontsize=4)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Cloud of 3D points')
    plt.axis('equal')
    plt.show()

def filter_cloud_of_3d_points(cloud_of_3d_points, coords_2d_projections):
    return {key: value for key, value in cloud_of_3d_points.items() if key in coords_2d_projections}

#############################################################################################################################################
## HANDLE 2D image coordinates ##############################################################################################################
#############################################################################################################################################

def get_charuco_corners_image_coords(image_in_gray, charuco_dictionary, charuco_board):
    """
    Detects charuco corners on a grayscale image.

    Parameters
    ----------
    image_in_gray : numpy.ndarray
        Grayscale input image.
    charuco_dictionary : cv2.aruco_Dictionary
        Aruco dictionary to use for corner detection.
    charuco_board : cv2.aruco_CharucoBoard
        Charuco board object.

    Returns
    -------
    bool
        Whether the corner interpolation was successful.
    numpy.ndarray
        Detected charuco corners.
    numpy.ndarray
        Charuco IDs.
    """
    params = aruco.DetectorParameters_create()
    corners, ids, _ = aruco.detectMarkers(image_in_gray, charuco_dictionary, parameters=params)
    if corners: 
        retval, charuco_corners_image_coords, charuco_corners_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, image_in_gray, charuco_board)
        return retval, charuco_corners_image_coords, charuco_corners_ids

def get_scatter_of_2D_points_projection(input_image_dir: str,
                                        charuco_num_of_columns: int = 44,
                                        charuco_num_of_rows: int = 28,
                                        charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000),
                                        sample_diameter_mm: float = 70,
                                        flag1: bool = False,
                                        flag2: bool = False) -> tuple:
    
    # TODO: change the return. have dict instead of pair of list 

    # Validate input parameters
    if not isinstance(charuco_dictionary, cv2.aruco_Dictionary):
        raise TypeError("charuco_dictionary should be an instance of cv2.aruco_Dictionary.")

    # Create the charuco board
    charuco_square_length_mm = round((np.pi * sample_diameter_mm) / charuco_num_of_columns)
    factor_between_square_and_marker = 3 / 5 
    charuco_marker_length_mm = round(factor_between_square_and_marker * charuco_square_length_mm)
    charuco_board = aruco.CharucoBoard_create(charuco_num_of_columns,
                                              charuco_num_of_rows,
                                              charuco_square_length_mm * 1e-3,
                                              charuco_marker_length_mm * 1e-3,
                                              charuco_dictionary)

    # Read the input image
    input_image = cv2.imread(input_image_dir)
    # rotated_image = cv2.rotate(input_image, cv2.ROTATE_90_CLOCKWISE)
    image_in_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    image_size = image_in_gray.shape #[::-1]    

    # Process: Detect charuco corners
    retval, charuco_corners_image_coords, charuco_corners_ids = get_charuco_corners_image_coords(image_in_gray, charuco_dictionary, charuco_board)
    
    if retval:
        # post process for saves 
        aruco.drawDetectedCornersCharuco(image_in_gray, charuco_corners_image_coords, charuco_corners_ids)

        # initiate image coordinates arrays - retval is the number of charuco corners found 
        u_coordinates = np.zeros(retval)
        v_coordinates = np.zeros(retval)

        for _ in range(retval): 
            u_coordinates[_] = charuco_corners_image_coords[_][0][0]
            v_coordinates[_] = charuco_corners_image_coords[_][0][1]

    coords_2d_projections = {
    corner_id[0]: np.array([u, v])
    for corner_id, u, v in zip(charuco_corners_ids, u_coordinates, v_coordinates)
    }

    if flag1:
        # Save the charuco board image
        directory = Path(__file__).absolute()
        image = np.ones((2100, 3300), dtype=np.uint8) * 255
        imgboard = charuco_board.draw((3300, 2100), image)
        cv2.imwrite(str(directory.parent / "charuco_board.jpg"), imgboard)

    if flag2:
        # Save the image with detected corners
        directory_path = Path(input_image_dir).absolute()
        parent_folder = directory_path.parent
        file_name = directory_path.name
        new_name = file_name.rsplit(".", 1)[0] + "_with_detected_charuco_corners.jpg"
        cv2.imwrite(str(parent_folder / new_name), image_in_gray)
    
    return retval, coords_2d_projections, image_size

def calibrate_camera(input_images_dir:str = r"C:\Users\hilar\Documents\project\geocam\src\images\cylindrical_calibration_rig\*.jpg"):

    # store the directories of each calibration image in a directory
    calibration_images_directories = glob.glob(input_images_dir)
    
    # initialize vectors to store coords for each image
    all_object_points = []
    all_image_points = []

    # compute the 3d coordinates - they are fixed
    cloud_of_3d_points_dict = get_cloud_of_3d_points()

    for calibration_image_dir in calibration_images_directories:

        # detected the charuco corners on the image of the cylindrical rig 
        retval, coords_2d_projections_dict, image_size = get_scatter_of_2D_points_projection(input_image_dir = calibration_image_dir)

        # filter the cloud of 3d points to only keep the one detected on the image
        cloud_of_3d_points_dict_filtered = filter_cloud_of_3d_points(cloud_of_3d_points_dict, coords_2d_projections_dict)

        # format the coordinates before calibration 
        object_points = np.zeros((1, retval, 3), dtype=np.float32)
        image_points = np.zeros((1, retval, 2), dtype=np.float32)

        for index, key in enumerate(cloud_of_3d_points_dict_filtered):
            object_points[0][index] = cloud_of_3d_points_dict_filtered[key]
            image_points[0][index] = coords_2d_projections_dict[key]

        # updated the vectors used for calibration 
        all_object_points.append(object_points)
        all_image_points.append(image_points)
        # print(all_object_points)
        # print(all_image_points)

    # Carry out opencv calibration of the camera to find the camera matrix and extenric matrix 
    initial_camera_matrix = np.array([[ 1000.,    0., image_size[0]/2.],
                                    [    0., 1000., image_size[1]/2.],
                                    [    0.,    0.,           1.]])
    distCoeffsInit = np.zeros((5,1))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.001)
    flags = cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL
    retval, cameraMatrix, distCoeffs, rvecs, tvecs, stdDeviationsIntrinsics, stdDeviationsExtrinsics, perViewErrors = cv2.calibrateCameraExtended(objectPoints = object_points, 
                                                                        imagePoints = image_points, 
                                                                        imageSize = image_size,
                                                                        cameraMatrix = initial_camera_matrix,
                                                                        distCoeffs = distCoeffsInit,
                                                                        flags=flags,
                                                                        criteria=criteria)
    
    # Carry out optimisation of the distortion parameters for each picture
    for index, (object_points, image_points) in enumerate(zip(all_object_points, all_image_points)):
        
        # rotation matrix 
        rotation_matrix, _ = cv2.Rodrigues(rvecs[index])
        extrinsic_matrix = np.hstack((rotation_matrix, tvecs[index]))
        
        # optimization process 
        # distortion_coefficients = np.zeros(20)
        distortion_coefficients = [1.45598487e-04, 9.90567117e-01, 9.47409801e-04, -8.00497563e-03,
                                   -6.40577414e-03, -3.39783002e-01, -1.65442306e-02,  6.65389864e-03,
                                    -2.18857410e-01, -4.73834414e-03, -1.04825610e-04,  4.58516917e-04,
                                    1.00447982e+00, 4.99436767e-03,  2.44399043e-02, -2.49364963e-03,
                                    -6.69130328e-01, -2.01844464e-03, -6.10910165e-03, -3.59383038e-01]
        optimized_distortion_coefficients = custom_calibration(object_points=object_points, 
                                  extrinsic_matrix=extrinsic_matrix, 
                                  cameraMatrix=cameraMatrix, 
                                  image_points=image_points, 
                                  distortion_coefficients = distortion_coefficients)
        

def custom_calibration(object_points, 
                        extrinsic_matrix, 
                        cameraMatrix, 
                        image_points, 
                        distortion_coefficients):
    
    # arguments for the reprojection_error_minization function 
    args = object_points, extrinsic_matrix, cameraMatrix, image_points

    # Define options
    options = {
        'maxiter': 1000,            # Maximum number of iterations
        'disp': True               # Display optimization information
    }

    # # Define the minimum value constraint
    # minimum_value_constraint = {
    #     'type': 'ineq',
    #     'fun': lambda x: x - 100  # Set the minimum value as 0.2 (adjust as needed)
    # }

    # # Set up the constraints
    # constraints = [minimum_value_constraint]

    # optimize calling the minimize function
    result = minimize(fun = reprojection_error_minization, x0 = distortion_coefficients, args = args, method='Powell', options=options)#, constraints=constraints)
    if result.success:
        print(result.x)
        print(reprojection_error(result.x, object_points, extrinsic_matrix, cameraMatrix, image_points))
        return result.x

def reprojection_error_minization(distortion_coefficients, *args):

    object_points, extrinsic_matrix, cameraMatrix, image_points = args 

    # get the image points resulting from the mapping to the scaled and skewed sensor coordinates by the affine transformation
    computed_image_points = projection_on_sensor(object_points = object_points, 
                                                 extrinsic_matrix = extrinsic_matrix, 
                                                 cameraMatrix = cameraMatrix,
                                                 distortion_coefficients = distortion_coefficients)

    # compute the overall RMS 
    error_for_each_point = image_points - computed_image_points
    custom_retval = np.linalg.norm(image_points - computed_image_points) / len(computed_image_points)

    return custom_retval

def reprojection_error(optimized_distortion_coefficients, *args):

    object_points, extrinsic_matrix, cameraMatrix, image_points = args 

    # get the image points resulting from the mapping to the scaled and skewed sensor coordinates by the affine transformation
    computed_image_points = projection_on_sensor(object_points = object_points, 
                                                 extrinsic_matrix = extrinsic_matrix, 
                                                 cameraMatrix = cameraMatrix,
                                                 distortion_coefficients = optimized_distortion_coefficients)

    # compute the overall RMS 
    error_for_each_point = image_points - computed_image_points
    print(error_for_each_point)
    custom_retval = np.linalg.norm(image_points - computed_image_points) / len(computed_image_points)

    return custom_retval

def projection_on_sensor(object_points, 
                        extrinsic_matrix, 
                        cameraMatrix,
                        distortion_coefficients):

    # format the object_points
    object_points_column = np.column_stack(object_points)
    object_points_column_hom = np.hstack((object_points_column, np.ones((object_points_column.shape[0],1))))

    # transform the object_points from world system to camera system 
    object_points_in_camera_system = np.dot(object_points_column_hom, extrinsic_matrix.T)

    # transform the object_points in camera system in normalised image plane
    object_points_in_camera_system /= object_points_in_camera_system[:,-1][:, np.newaxis]
    projection_on_normalized_img_plane = object_points_in_camera_system[:,:-1]

    # apply distortion 
    lens_distorted_2d_coords = warp_function(projection_on_normalized_img_plane,
                                             distortion_coefficients)

    # format the result 
    lens_distorted_2d_coords_hom = np.hstack((lens_distorted_2d_coords, np.ones((lens_distorted_2d_coords.shape[0],1))))

    # mapping to the scaled and skewed sensor coordinates by the affine transformation
    computed_image_points = np.dot(lens_distorted_2d_coords_hom, cameraMatrix[:-1].T)

    return computed_image_points

def warp_function(projection_on_normalized_img_plane, distortion_coefficients):
    
    x = projection_on_normalized_img_plane[:, 0]
    y = projection_on_normalized_img_plane[:, 1]

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

    param = distortion_coefficients.reshape(2, 10)
    lens_distorted_2d_coords = np.dot(non_linear_vector, param.T)

    return lens_distorted_2d_coords


if __name__ == "__main__":
    calibrate_camera()
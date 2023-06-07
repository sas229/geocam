import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import glob

from cv2 import aruco  
from pathlib import Path 
from scipy.stats import norm


#############################################################################################################################################
## HANDLE 3D world coordinates ##############################################################################################################
#############################################################################################################################################

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

def stack_points(model_coord_filterd, px_coord):

    model_Coord = np.ones((0,3))
    for val in model_coord_filterd.values():

        model_Coord = np.vstack((model_Coord, val))

    model_coord = []
    model_coord.append(model_Coord)
    model_coord = np.float32(model_coord)

    px_Coord = []
    px_Coord.append(px_coord)

    return model_coord, px_Coord


def calibrate_camera(input_image_dir: str, flag1: bool = False, flag2: bool = False, flag3: bool = False):

    # Sample input for objectPoints (3D points in the real world) and imagePoints (2D points captured by the camera)

    # match 3D points and 2D projection of these points 
    cloud_of_3d_points_dict = get_cloud_of_3d_points()
    retval, coords_2d_projections_dict, image_size = get_scatter_of_2D_points_projection(input_image_dir = input_image_dir)
    cloud_of_3d_points_dict_filtered = filter_cloud_of_3d_points(cloud_of_3d_points_dict, coords_2d_projections_dict)

    print(image_size)

    # format the inputs 
    all_object_points = []
    all_image_points = []

    # should be done for all images of calibration but only using one here 
    # for image in images_list: 

    object_points = np.zeros((1, retval, 3), dtype=np.float32)
    image_points = np.zeros((1, retval, 2), dtype=np.float32)

    for index, key in enumerate(cloud_of_3d_points_dict_filtered):
        object_points[0][index] = cloud_of_3d_points_dict_filtered[key]
        image_points[0][index] = coords_2d_projections_dict[key]

    all_object_points.append(object_points)
    all_image_points.append(image_points)

    # Carry out calibration of the camera
    # initial_camera_matrix = np.array([[ 1000.,    0., image_size[0]/2.],
    #                              [    0., 1000., image_size[1]/2.],
    #                              [    0.,    0.,           1.]])
    distCoeffsInit = np.zeros((5,1))

    initial_camera_matrix = np.array([[ 3.62916898e+03,    0., 1.58513866e+03],
                                 [    0., 3.77369633e+03, 2.10494246e+03],
                                 [    0.,    0.,           1.]])
    # distCoeffsInit = np.array([[-9.26873347e+00], [ 4.06241122e+01],  
    #                            [-2.26419530e-03],  [-4.22193723e-03], 
    #                            [ 3.57866539e+01], [-8.76263182e+00], 
    #                             [ 3.53185405e+01], [ 6.07663413e+01], 
    #                             [ 0.00000000e+00], [ 0.00000000e+00], 
    #                             [ 0.00000000e+00],  [ 0.00000000e+00], 
    #                             [ 0.00000000e+00], [ 0.00000000e+00]])

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.001)

    # Call the calibrateCamera function with the initial camera matrix flag
    calibrate_camera_results = {}
    # cv2.CALIB_ZERO_TANGENT_DIST
    # cv2.CALIB_RATIONAL_MODEL 
    # cv2.CALIB_THIN_PRISM_MODEL
    # cv2.CALIB_TILTED_MODEL
    flags = cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL
    retval, cameraMatrix, distCoeffs, rvecs, tvecs, stdDeviationsIntrinsics, stdDeviationsExtrinsics, perViewErrors = cv2.calibrateCameraExtended(objectPoints = object_points, 
                                                                         imagePoints = image_points, 
                                                                         imageSize = image_size,
                                                                         cameraMatrix = initial_camera_matrix,
                                                                         distCoeffs = distCoeffsInit,
                                                                         flags=flags,
                                                                         criteria=criteria)
    
    calibrate_camera_results.update({"retval":retval, "cameraMatrix":cameraMatrix,
                    "distCoeffs":distCoeffs, "rvecs":rvecs, "tvecs":tvecs,
                    "stdDeviationsIntrinsics":stdDeviationsIntrinsics,
                    "stdDeviationsExtrinsics":stdDeviationsExtrinsics,
                    "perViewErrors":perViewErrors})


    # plotting the camera position
    rotation_matrix, _ = cv2.Rodrigues(rvecs[0])
    # invert the rotation matrix to obtain the rotation from the camera coordinate system to the world coordinate system
    rotation_matrix_inv = np.linalg.inv(rotation_matrix)
    # multiply the inverted rotation matrix (rotation_matrix_inv) with the translation vector (tvec) to obtain the camera position in world coordinates
    camera_position_world = -np.dot(rotation_matrix_inv, tvecs[0])

    if flag1:
        camera_position_world_as_a_list = [item for sublist in camera_position_world for item in sublist]
        camera_position_world_formatted = np.array(camera_position_world_as_a_list)
        cloud_of_3d_points_dict_filtered.update({'camera': camera_position_world_formatted})

        if flag2: 
            axis_length = 10

            # Define the camera axes
            axes = np.array([[axis_length, 0, 0, 1],
                            [0, axis_length, 0, 1],
                            [0, 0, axis_length, 1]])

            # Transform the axes from camera coordinates to world coordinates
            axes_world = -np.dot(rotation_matrix_inv, axes) + camera_position_world

            # Extract the X, Y, Z coordinates of the camera axes
            x_coords = axes_world[:, 0]
            y_coords = axes_world[:, 1]
            z_coords = axes_world[:, 2]

            # Extract the X, Y, Z coordinates of the camera axes
            cloud_of_3d_points_dict_filtered.update({'X_c': x_coords})
            cloud_of_3d_points_dict_filtered.update({'Y_c': y_coords})
            cloud_of_3d_points_dict_filtered.update({'Z_c': z_coords})


        # plot
        plot_3d_points(cloud_of_3d_points_dict_filtered, flag=True)
    
    if flag3:
        # TODO: a dict 
        names = ["fx","fy","cx","cy","k1","k2","p1","p2","k3","k4","k5","k6","s1","s2","s3","s4","τx","τy"]
        
        # focal lengths 
        mean_fx = cameraMatrix[0,0]
        std_dev_fx = stdDeviationsIntrinsics[0]
        cov_fx_percentage = abs(std_dev_fx[0]/mean_fx*100)
        mean_fy = cameraMatrix[1,1]
        std_dev_fy = stdDeviationsIntrinsics[1]
        cov_fy_percentage = abs(std_dev_fy[0]/mean_fy*100)

        # position of the principal point 
        mean_cx = cameraMatrix[0,2]
        std_dev_cx = stdDeviationsIntrinsics[2]
        cov_cx_percentage = abs(std_dev_cx[0]/mean_cx*100)
        mean_cy = cameraMatrix[1,2]
        std_dev_cy = stdDeviationsIntrinsics[3]
        cov_cy_percentage = abs(std_dev_cy[0]/mean_cy*100)

        # distortion coefficints 
        # k1
        mean_k1 = distCoeffs[0][0]
        std_dev_k1 = stdDeviationsIntrinsics[4]
        cov_k1_percentage = abs(std_dev_k1[0]/mean_k1*100)
       
        # k2
        mean_k2 = distCoeffs[1][0]
        std_dev_k2 = stdDeviationsIntrinsics[5]
        cov_k2_percentage = abs(std_dev_k2[0]/mean_k2*100)
        
        # p1
        mean_p1 = distCoeffs[2][0]
        print("DDDD", mean_p1)
        std_dev_p1 = stdDeviationsIntrinsics[6]
        cov_p1_percentage = abs(std_dev_p1[0]/mean_p1*100)
        
        # p2
        mean_p2 = distCoeffs[3][0]
        print("DDDD", mean_p2)
        std_dev_p2 = stdDeviationsIntrinsics[7]
        cov_p2_percentage = abs(std_dev_p2[0]/mean_p2*100)
        
        # k3
        mean_k3 = distCoeffs[4][0]
        std_dev_k3 = stdDeviationsIntrinsics[8]
        cov_k3_percentage = abs(std_dev_k3[0]/mean_k3*100)
        
        # k4
        # mean_k4 = distCoeffs[5][0]
        # std_dev_k4 = stdDeviationsIntrinsics[9]
        # cov_k4_percentage = abs(std_dev_k4[0]/mean_k4*100)
        
        # # k5
        # mean_k5 = distCoeffs[6][0]
        # std_dev_k5 = stdDeviationsIntrinsics[10]
        # cov_k5_percentage = abs(std_dev_k5[0]/mean_k5*100)
        
        # # k6
        # mean_k6 = distCoeffs[7][0]
        # std_dev_k6 = stdDeviationsIntrinsics[11]
        # cov_k6_percentage = abs(std_dev_k6[0]/mean_k6*100)
        
        
        fig1 = plt.figure("Focal lengths")
        plot_probality_density_function(mean_fx, std_dev_fx, f'{names[0]}, {round(mean_fx)}, {round(std_dev_fx[0])}, {round(cov_fx_percentage, 2)}%')
        plot_probality_density_function(mean_fy, std_dev_fy, f'{names[1]}, {round(mean_fy)}, {round(std_dev_fy[0])}, {round(cov_fy_percentage, 2)}%')
        plt.show()

        fig2 = plt.figure("Principal point")
        plot_probality_density_function(mean_cx, std_dev_cx, f'{names[2]}, {round(mean_cx)}, {round(std_dev_cx[0])}, {round(cov_cx_percentage, 2)}%')
        plot_probality_density_function(mean_cy, std_dev_cy, f'{names[3]}, {round(mean_cy)}, {round(std_dev_cy[0])}, {round(cov_cy_percentage, 2)}%')
        plt.show()

        fig3 = plt.figure("Distorsion coefficients")
        plot_probality_density_function(mean_k1, std_dev_k1, f'{names[4]}, {round(mean_k1)}, {round(std_dev_k1[0])}, {round(cov_k1_percentage, 2)}%')
        plt.show()

        fig4 = plt.figure("Distorsion coefficients")
        plot_probality_density_function(mean_k2, std_dev_k2, f'{names[5]}, {round(mean_k2)}, {round(std_dev_k2[0])}, {round(cov_k2_percentage, 2)}%')
        plt.show()

        fig5 = plt.figure("Distorsion coefficients")
        plot_probality_density_function(mean_p1, std_dev_p1, f'{names[6]}, {round(mean_p1)}, {round(std_dev_p1[0])}, {round(cov_p1_percentage, 2)}%')
        plt.show()

        fig6 = plt.figure("Distorsion coefficients")
        plot_probality_density_function(mean_p2, std_dev_p2, f'{names[7]}, {round(mean_p2)}, {round(std_dev_p2[0])}, {round(cov_p2_percentage, 2)}%')
        plt.show()

        fig7= plt.figure("Distorsion coefficients")
        plot_probality_density_function(mean_k3, std_dev_k3, f'{names[8]}, {round(mean_k3)}, {round(std_dev_k3[0])}, {round(cov_k3_percentage, 2)}%')
        # plot_probality_density_function(mean_k4, std_dev_k4, f'{names[9]}, {round(mean_k4)}, {round(std_dev_k4[0])}, {round(cov_k4_percentage, 2)}%')
        # plot_probality_density_function(mean_k5, std_dev_k5, f'{names[10]}, {round(mean_k5)}, {round(std_dev_k5[0])}, {round(cov_k5_percentage, 2)}%')
        # plot_probality_density_function(mean_k6, std_dev_k6, f'{names[3]}, {round(mean_k6)}, {round(std_dev_cy[0])}, {round(cov_k6_percentage, 2)}%')
        plt.show()

    return retval, cameraMatrix, distCoeffs, rvecs, tvecs, stdDeviationsIntrinsics, stdDeviationsExtrinsics, perViewErrors

def plot_3d_points_and_camera(results_calibrate_camera: dict, flag1:bool = False, flag2:bool = False, flag3:bool = False):
    # TODO: make some plots 
    retval = results_calibrate_camera["retval"]
    cameraMatrix = results_calibrate_camera["cameraMatrix"]
    distCoeffs = results_calibrate_camera["distCoeffs"] 
    rvecs = results_calibrate_camera["rvecs"] 
    tvecs = results_calibrate_camera["tvecs"] 
    stdDeviationsIntrinsics = results_calibrate_camera["stdDeviationsIntrinsics"] 
    stdDeviationsExtrinsics = results_calibrate_camera["stdDeviationsExtrinsics"] 
    perViewErrors = results_calibrate_camera["perViewErrors"]

        

def plot_probality_density_function(mean:float, std_dev:float, param:str):

    # Generate x values spanning a range around the mean
    x = np.linspace(mean - 4 * std_dev, mean + 4 * std_dev, 100)

    # Compute corresponding y values using the probability density function (pdf) of the normal distribution
    y = norm.pdf(x, mean, std_dev)

    # Plot the normal distribution
    plt.plot(x, y, label = f'{param}')
    plt.xlabel('data')
    plt.ylabel('Probability density')
    plt.title('Normal Distributions')
    plt.legend()
    plt.grid(True)
    

#############################################################################################################################################
## Main #####################################################################################################################################
#############################################################################################################################################


if __name__ == "__main__":
    coord_3D_points = get_cloud_of_3d_points()
    directory = r"C:\Users\hilar\Documents\project\geocam\src\images\calibration_img_example.jpg"
    retval, coords_2d_projections, image_size = get_scatter_of_2D_points_projection(input_image_dir = directory, flag2=True)

    coord_3D_points_filtered = filter_cloud_of_3d_points(coord_3D_points, coords_2d_projections)

    # print("coords_2d_projections", coords_2d_projections)
    # print()
    # print("coord_3D_points_filtered", coord_3D_points_filtered)

    names = ["retval", "cameraMatrix", "distCoeffs", "rvecs", "tvecs", "stdDeviationsIntrinsics", "stdDeviationsExtrinsics", "perViewErrors"]
    results = calibrate_camera(input_image_dir=directory, flag1=True, flag3=True)
    
    for index, name in enumerate(names):
        print(name, results[index])

    # plot_probality_density_function()
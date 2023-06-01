"""
:Name: communicator
:Description: This module is used for the various communication operations
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

import logging
import numpy as np
import matplotlib.pyplot as plt
import cv2

from pathlib import Path
from cv2 import aruco

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################
# see https://docs.python.org/3/library/logging.html for documentation on logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler that logs the debug messages
file_handler = logging.FileHandler(f'{__file__[:-3]}.log', mode='w')
file_handler.setLevel(logging.DEBUG)

# create a stream handler to print the errors in console
stream_handler = logging.StreamHandler()

# format the handlers 
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

#############################################################################################################################################
## COULD BE IN UTILS ########################################################################################################################
#############################################################################################################################################

## get_cloud_of_3D_points ###################################################################################################################
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
        corner_id: np.array([x, y, z], np.float32)
        for corner_id, x, y, z in zip(range(num_of_corners), x_coordinates, y_coordinates, z_coordinates)
    }

    if flag1:
        # plot the points
        plot_3d_points(coords_3d_points, flag=flag2)
    
    return coords_3d_points

## plot_3d_points ###########################################################################################################################
#############################################################################################################################################

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
            ax.text(x_coordinates[i], y_coordinates[i], z_coordinates[i], str(int(corner_id)), fontsize=6)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Cloud of 3D points')
    plt.axis('equal')
    plt.show()

## detect_charuco_corners ###################################################################################################################
#############################################################################################################################################

def detect_charuco_corners(image_in_gray, charuco_dictionary, charuco_board):
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
        retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, image_in_gray, charuco_board)
        return retval, charuco_corners, charuco_ids

## get_scatter_of_2D_points_projection ######################################################################################################
#############################################################################################################################################

def get_scatter_of_2D_points_projection(input_image_dir: str,
                                        charuco_num_of_columns: int = 44,
                                        charuco_num_of_rows: int = 28,
                                        charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000),
                                        sample_diameter_mm: float = 70,
                                        flag1: bool = False,
                                        flag2: bool = False) -> tuple:
    """
    Detects charuco corners on an input image.

    Parameters
    ----------
    input_image_dir : str
        Directory path of the input image.
    charuco_num_of_columns : int, optional
        Number of columns in the charuco board, by default 44.
    charuco_num_of_rows : int, optional
        Number of rows in the charuco board, by default 28.
    charuco_dictionary : cv2.aruco_Dictionary, optional
        Aruco dictionary to use for corner detection, by default cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000).
    sample_diameter_mm : float, optional
        Diameter of the sample in millimeters, by default 70.
    flag1 : bool, optional
        Whether to save the charuco board image, by default False.
    flag2 : bool, optional
        Whether to save the input image with detected charuco corners, by default False.

    Returns
    -------
    tuple
        A tuple containing the status of corner interpolation, charuco corners, and charuco IDs.
    """

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
    image_in_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    

    # Process: Detect charuco corners
    retval, charuco_corners, charuco_ids = detect_charuco_corners(image_in_gray, charuco_dictionary, charuco_board)
    
    if retval:
        aruco.drawDetectedCornersCharuco(image_in_gray, charuco_corners, charuco_ids)

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

    return retval, charuco_corners, charuco_ids

if __name__ == "__main__":
    func1 = False
    func2 = True
    if func1:
        get_cloud_of_3d_points(charuco_num_of_columns = 10, charuco_num_of_rows = 5, flag1=True, flag2=True)
    if func2:
        get_scatter_of_2D_points_projection()
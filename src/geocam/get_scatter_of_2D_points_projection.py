import logging
import cv2
import numpy as np
import matplotlib.pyplot as plt

from cv2 import aruco  
from pathlib import Path 


from pathlib import Path
import cv2
from cv2 import aruco
import numpy as np

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
    image_size = image_in_gray.shape
    print("image_size", image_size)
    # add a logger here shape is (height, width, 3) for color images and (height, width) for gray images
    

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

    return retval, charuco_corners, charuco_ids, charuco_board, image_size


if __name__ == "__main__":
    directory = r"C:\Users\hilar\Documents\project\geocam\src\images\calibration_img_example.jpg"
    retval, charuco_corners, charuco_ids, charuco_board, image_size = get_scatter_of_2D_points_projection(input_image_dir = directory, flag2=True)
    print(type(retval))
    print(type(charuco_corners))
    print(type(charuco_ids))
    print(type(charuco_board))
    print(charuco_board)
    print(type(image_size))
    print(image_size)
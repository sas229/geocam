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

import getmac
import json
import logging
import os
import platform
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import cv2

from geocam.communicator import *
from typing import Union, List, Dict
from cv2 import aruco
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
## COMMUNICATION FUNCTIONS ##################################################################################################################
#############################################################################################################################################

## Get informations on machine ##############################################################################################################
############################################################################################################################################# 

# test up to date
def get_host_name() -> str: 
    """
    Returns the hostname of the current machine.

    Returns
    -------
    str
        The hostname of the current machine.
    """
    host_name = socket.gethostname()

    # Logging the host_name before returning
    logger.info("Current hostname: %s", host_name)

    return host_name

# test up to date be careful with the test from mac os  
def get_host_ip() -> str:
    """
    Returns the IP address of the current machine.

    Returns
    -------
    str
        The hostname of the current machine.

    Raises
    ------
    OSError
        If the IP address could not be retreived.
    """  
    host_ip = None

    if platform.system().lower() == 'windows':
        host_ip = socket.gethostbyname(socket.gethostname())
    elif platform.system().lower() == 'linux': 
        routes = json.loads(os.popen("ip -j -4 route").read())
        for r in routes:
            if r.get("dev") == "wlan0" and r.get("prefsrc"):
                host_ip = r['prefsrc']
                break 
    elif platform.system().lower() == 'darwin': 
        host_ip = os.popen("ipconfig getifaddr en0").read()

    if host_ip is None:
        raise OSError("Failed to retrieve the IP address.")
    logger.info("Current IP address: %s", host_ip)
    return host_ip 


def get_mac_address() -> str:
    """
    Returns the MAC address of the current machine.

    Returns
    -------
    str
        The MAC address of the current machine.
    """
    mac_addr = getmac.get_mac_address()
    logger.info("Current mac_addr: %s", mac_addr)
    return mac_addr

## Checks on IP address  ####################################################################################################################
############################################################################################################################################# 

def is_local_ip_address(host_ip:str) -> bool: 
    """
    Checks if the given IP address is a local address.

    Parameters
    ----------
    host_ip : str
        The IP address to check.

    Returns
    -------
    bool
        True if the IP address is a local address, False otherwise.
    """         
    if host_ip == host_ip.startswith('127.') or host_ip == socket.gethostbyname('localhost'):
        logger.info("IP address %s is a local address.", host_ip)
        return True
    else: 
        logger.info("IP address %s is not a local address.", host_ip)
        return False 

def is_valid_ipv4(ip: str) -> bool:
    """
    Checks if the given IPv4 address is valid.

    Parameters
    ----------
    ip : str
        The IPv4 address to check.

    Returns
    -------
    bool
        True if the IPv4 address is valid, False otherwise.

    """
    parts = ip.split('.')
    if len(parts) != 4:
        logger.info("Invalid IPv4 address: %s", ip)
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            logger.info("Invalid IPv4 address: %s", ip)
            return False
    logger.info("Valid IPv4 address: %s", ip)
    return True

def is_valid_ipv6(ip: str) -> bool:
    """
    Checks if the given IPv6 address is valid.

    Parameters
    ----------
    ip : str
        The IPv6 address to check.

    Returns
    -------
    bool
        True if the IPv6 address is valid, False otherwise.

    """
    parts = ip.split(':')
    if len(parts) > 8:
        logger.info("Invalid IPv6 address: %s", ip)
        return False
    for part in parts:
        if not (1 <= len(part) <= 4) or not all(c in '0123456789abcdefABCDEF' for c in part):
            logger.info("Invalid IPv6 address: %s", ip)
            return False
    logger.info("Valid IPv6 address: %s", ip)
    return True

def is_valid_ip(ip: str) -> bool:
    """
    Checks if the given IP address is valid (IPv4 or IPv6).

    Parameters
    ----------
    ip : str
        The IP address to check.

    Returns
    -------
    bool
        True if the IP address is valid (IPv4 or IPv6), False otherwise.

    """
    if is_valid_ipv4(ip) or is_valid_ipv6(ip):
        logger.info("Valid IP address: %s", ip)
        return True
    else:
        logger.info("Invalid IP address: %s", ip)
        return False
    
## Check if a port is occupied ##############################################################################################################
#############################################################################################################################################

def is_port_free(port: int) -> bool:
    """
    Checks if the given port is free.

    Parameters
    ----------
    port : int
        The port number to check.

    Returns
    -------
    bool
        True if the port is free, False otherwise.

    """
    if platform.system() == "Windows":
        command = f"netstat -ano | findstr :{port}"
    else:
        command = f"lsof -i :{port}"

    try:
        subprocess.check_output(command, shell=True)
        logger.info("Port %d is not free.", port)
        return False
    except subprocess.CalledProcessError:
        logger.info("Port %d is free.", port)
        return True

def get_free_port(candidates):
    """
    Finds and returns a list of free ports from the given candidates.

    Parameters
    ----------
    candidates : list
        A list of port numbers to check.

    Returns
    -------
    list
        A list of free port numbers.

    """
    result = []
    for port in candidates:
        if is_port_free(port):
            result.append(port)
    logger.info("Free ports: %s", result)
    return result

## Network diagnostic #######################################################################################################################
############################################################################################################################################# 
    
def ping(target:str) -> bool:
    """
    Pings the specified target and returns whether it is reachable or not.

    Parameters
    ----------
    target : str
        The target to ping.

    Returns
    -------
    bool
        True if the target is reachable, False otherwise.
    """          
    param = '-n' if platform.system().lower()=='windows' else '-c'
    try:
        subprocess.check_output(["ping", param, "1", target], stderr=subprocess.STDOUT)
        logger.info("Target %s is reachable.", target)
        return True
    except subprocess.CalledProcessError:
        logger.info("Target %s is not reachable.", target)
        return False
               
def network_status(remote_server:str = "google.com") -> int:
    """
    Checks the network status of the device.

    Parameters
    ----------
    remote_server : str, optional
        The remote server to ping for checking internet connectivity. Default is "google.com".

    Returns
    -------
    str
        The network status:
        - 0 if the device is not connected to a network.
        - -1 if the device is connected to a WLAN but has no internet access.
        - 1 if the device is connected to a WLAN and has internet access.

    Raises
    ------
    NotImplementedError
        If the IP address is local but there is access to the internet.

    """
    is_the_ip_local = is_local_ip_address(get_host_ip())
    is_internet_connected = ping(remote_server)

    if not is_internet_connected and is_the_ip_local:
        logger.warning("This device isn't connected to a network")
        return 0
    elif not is_internet_connected and not is_the_ip_local:
        logger.warning("On local network with no access to internet")
        return -1
    elif is_internet_connected and not is_the_ip_local:
        logger.warning("Access to internet")
        return 1
    else:
        raise NotImplementedError("Undefined - the IP is the local one but there is access to the internet")

## Create JSON ##############################################################################################################################
############################################################################################################################################# 

def create_json(source:str, content:dict) -> str:
    """
    Creates a JSON string from the given source and content.

    Parameters
    ----------
    source : str
        The source of the JSON data.
    content : dict
        The content of the JSON data.

    Returns
    -------
    str
        The JSON string representation of the source and content.

    """    
    _dict = {"source":source ,"content":content}
    json_string = json.dumps(_dict, indent=2)
    logger.info("Created JSON string: %s", json_string)
    return json_string

def read_json(json_string:str) -> dict: 
    """
    Reads a JSON string and returns a dictionary.

    Parameters
    ----------
    json_string : str
        The JSON string to read.

    Returns
    -------
    dict
        The dictionary representation of the JSON data.

    """
    data = json.loads(json_string)
    logger.info("Read JSON data: %s", data)
    return data 

#############################################################################################################################################
## CALIBRATION FUNCTIONS ####################################################################################################################
#############################################################################################################################################

## related to 3d world ######################################################################################################################
#############################################################################################################################################

def get_cloud_of_3d_points(num_of_charuco_squares_horizontally: int = 44, 
                           num_of_charuco_squares_vertically: int = 28,
                           sample_height_mm: float = 140,
                           sample_diameter_mm: float = 70,
                           plot_the_cloud_of_3d_points: bool = False, 
                           plot_corners_ids: bool = False) -> Dict[str, np.ndarray]:
        """
        Generate a cloud of 3D points based on the given parameters.

        Parameters
        ----------
        num_of_charuco_squares_horizontally : int, optional
            Number of squares in the horizontal direction of the charuco board, by default 44.
        num_of_charuco_squares_vertically : int, optional
            Number of squares in the vertical direction of the charuco board, by default 28.
        sample_height_mm : float, optional
            Height of the sample in millimeters, by default 140.
        sample_diameter_mm : float, optional
            Diameter of the sample in millimeters, by default 70.
        plot_the_cloud_of_3d_points : bool, optional
            Whether to plot the generated points or not, by default False.
        plot_corners_ids : bool, optional
            Whether to plot the corners IDs or not, by default False.

        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary containing the 3D coordinates of each corner.

        NOTE: Possible limit not very flexible with with the charuco grids 
        """

        logger.info(f"Generating cloud of 3D points with {num_of_charuco_squares_horizontally} squares horizontally, "
                    f"{num_of_charuco_squares_vertically} squares vertically, a sample height of {sample_height_mm} mm, "
                    f"and a sample diameter of {sample_diameter_mm} mm.")

        # Calculate the radius of the sample
        sample_radius_mm = 0.5 * sample_diameter_mm

        # Calculate the length of a charuco square
        charuco_square_length_mm = round((np.pi * sample_diameter_mm) / num_of_charuco_squares_horizontally)

        # Calculate the elementary angle
        elementary_angle_rad = charuco_square_length_mm / sample_radius_mm

        # Calculate useful informations in cylendric system
        theta = np.array([index * elementary_angle_rad for index in range(num_of_charuco_squares_horizontally - 1)])
        levels = np.arange(charuco_square_length_mm, sample_height_mm, charuco_square_length_mm)

        # Calculate the coordinates of each corner in cartesian system
        x_coordinates = np.tile(np.cos(theta) * sample_radius_mm, len(levels))
        y_coordinates = np.tile(np.sin(theta) * sample_radius_mm, len(levels))
        z_coordinates = np.repeat(levels, len(theta))

        # Create a dictionary of the 3D coordinates of each corner
        num_of_corners = (num_of_charuco_squares_vertically - 1) * (num_of_charuco_squares_horizontally - 1)
        coords_3d_points = {
            str(corner_id): np.array([x, y, z])
            for corner_id, x, y, z in zip(range(num_of_corners), x_coordinates, y_coordinates, z_coordinates)
        }

        # Verify that the lengths of x, y, z, and the dictionary are equal
        assert len(x_coordinates) == len(y_coordinates) == len(z_coordinates) == num_of_corners

        # Log the lengths of x, y, z, and the dictionary
        logger.debug(f"Length of x_coordinates: {len(x_coordinates)}")
        logger.debug(f"Length of y_coordinates: {len(y_coordinates)}")
        logger.debug(f"Length of z_coordinates: {len(z_coordinates)}")
        logger.debug(f"Length of coords_3d_points: {len(coords_3d_points)}")

        # Plot the points if plot_the_cloud_of_3d_points is True
        if plot_the_cloud_of_3d_points:
            plot_3d_points(coords_3d_points, plot_corners_ids = plot_corners_ids)

        # Return the dictionary of 3D coordinates
        return coords_3d_points

def plot_3d_points(dict_s_coords_3d_points: Union[List[Dict], List], plot_corners_ids: bool = False) -> None:
    """
    Plot the 3D points in a scatter plot.

    Parameters
    ----------
    dict_s_coords_3d_points : List[Dict] or Dict
        List of dictionaries or a single dictionary containing the 3D coordinates of each 3D point.
    length_arrows_mm : float, optional
        Length of arrows of the 3D coordinate system in millimeters, by default 15.
    plot_corners_ids : bool, optional
        Whether to plot the corner IDs or not, by default False.

    Returns
    -------
    None
        The function plots the 3D points.

    Raises
    ------
    ValueError
        If the `dict_s_coords_3d_points` argument is empty.
    """
    FONT_SIZE = 6

    if not dict_s_coords_3d_points:
        raise ValueError("'dict_s_coords_3d_points' is empty.")
    
    # create the figure  
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # draw a 3d coordinates system
    _plot_3d_coordinate_system(ax=ax, add_planes=True)

    # if list of dict than plot the different sets of data 
    if isinstance(dict_s_coords_3d_points, list):
        logger.info("Plotting multiple sets of data")
        for coords_3d_points in dict_s_coords_3d_points:
            _plot_3d_scatter_and_handle_legends(ax=ax, coords_3d_points=coords_3d_points, font_size=FONT_SIZE, plot_corners_ids=plot_corners_ids)
    # elif dict than plot the only set given  
    elif isinstance(dict_s_coords_3d_points, dict):
        logger.info("Plotting singular set of data")
        _plot_3d_scatter_and_handle_legends(ax=ax, coords_3d_points=dict_s_coords_3d_points, font_size=FONT_SIZE, plot_corners_ids=plot_corners_ids)

    # additional settings 
    ax.axis('equal')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Cloud of 3D points')
    # plt.axis('equal')
    plt.show()

def _plot_3d_coordinate_system(ax: plt.Axes, length_arrows_mm:float = 40, origin:np.array = np.zeros(3), add_planes:bool = False):
    """
    Plots a 3D coordinate system with arrows representing the x, y, and z axes.

    Parameters
    ----------
    ax : plt.Axes
        The matplotlib axis object to plot the coordinate system on.
    length_arrows_mm : float, optional
        The length of the arrows in millimeters. Default is 40.
    origin : np.array, optional
        The origin of the coordinate system. Default is np.zeros(3).
    add_planes : bool, optional
        Whether to add planes normal to the coordinate system. Default is False.

    Returns
    -------
    None

    The function draws a 3D coordinate system with arrows representing the x, y, and z axes. The origin of the system can be specified, and the length of the arrows can be adjusted. If add_planes is set to True, the function also adds planes normal to the coordinate system. The planes are represented by polygons and are colored orange with an alpha value of 0.4. The function returns nothing.
    """
    # Constants
    X_ARROW_COLOR = "r"
    Y_ARROW_COLOR = "g"
    Z_ARROW_COLOR = "b"
    PLANES_COLOR = "orange"
    PLANES_ALPHA = 0.4

    # Draw the arrows 
    ax.quiver(origin[0], origin[1], origin[2], 1, 0, 0, color=X_ARROW_COLOR, length = length_arrows_mm, normalize=True)
    ax.quiver(origin[0], origin[1], origin[2], 0, 1, 0, color=Y_ARROW_COLOR, length = length_arrows_mm, normalize=True)
    ax.quiver(origin[0], origin[1], origin[2], 0, 0, 1, color=Z_ARROW_COLOR, length = length_arrows_mm, normalize=True)
    ax.text(length_arrows_mm * 0.1, length_arrows_mm * 0.0, -length_arrows_mm * 0.2, r'$0$')
    ax.text( length_arrows_mm * 1.3, length_arrows_mm * 0, length_arrows_mm * 0, r'$x$')
    ax.text(length_arrows_mm * 0, length_arrows_mm * 1.3, length_arrows_mm * 0, r'$y$')
    ax.text(length_arrows_mm * 0, length_arrows_mm * 0, length_arrows_mm * 1.3, r'$z$')

    # Draw plans normal to axis 
    if add_planes:
        elem_length_1 = 0.1 * length_arrows_mm
        elem_length_2 = 0.6 * length_arrows_mm

        # Plane normal to the x axis 
        x_plan_normal_to_x = [origin[0], origin[0], origin[0], origin[0]]
        y_plan_normal_to_x = [origin[1] + elem_length_1, origin[1] + elem_length_2, origin[1] + elem_length_2, origin[1] + elem_length_1]
        z_plan_normal_to_x = [origin[2] + elem_length_1, origin[2] + elem_length_1, origin[2] + elem_length_2, origin[2] + elem_length_2]

        # Plane normal to the y axis 
        x_plan_normal_to_y = [elem_length_1, elem_length_2, elem_length_2, elem_length_1]
        y_plan_normal_to_y = [origin[1], origin[1], origin[1], origin[1]]
        z_plan_normal_to_y = [origin[2] + elem_length_1, origin[2] + elem_length_1, origin[2] + elem_length_2, origin[2] + elem_length_2]

        # Plane normal to the z axis 
        x_plan_normal_to_z = [elem_length_1, elem_length_2, elem_length_2, elem_length_1]
        y_plan_normal_to_z = [origin[1] + elem_length_1, origin[1] + elem_length_1, origin[1] + elem_length_2, origin[1] + elem_length_2]
        z_plan_normal_to_z = [origin[2], origin[2], origin[2], origin[2]]

        # Format coordinates of corners 
        vertice_1 = [list(zip(x_plan_normal_to_x, y_plan_normal_to_x, z_plan_normal_to_x))]
        vertice_2 = [list(zip(x_plan_normal_to_y, y_plan_normal_to_y, z_plan_normal_to_y))]
        vertice_3 = [list(zip(x_plan_normal_to_z, y_plan_normal_to_z, z_plan_normal_to_z))]

        # Create polygone objects 
        poly_1 = Poly3DCollection(vertice_1, alpha=PLANES_ALPHA, facecolors=PLANES_COLOR)
        poly_2 = Poly3DCollection(vertice_2, alpha=PLANES_ALPHA, facecolors=PLANES_COLOR)
        poly_3 = Poly3DCollection(vertice_3, alpha=PLANES_ALPHA, facecolors=PLANES_COLOR)

        # Add the planes to the axis
        ax.add_collection3d(poly_1)
        ax.add_collection3d(poly_2)
        ax.add_collection3d(poly_3)

def _plot_3d_scatter_and_handle_legends(ax: plt.Axes, coords_3d_points: dict, font_size: int, plot_corners_ids: bool) -> None:
    """
    Plot the 3D scatter points and handle legends for each point.

    Parameters
    ----------
    ax : plt.Axes
        The 3D axes object to plot on.
    coords_3d_points : dict
        Dictionary containing the 3D coordinates of each corner.
    font_size : int
        Font size for the legends.
    plot_corners_ids : bool
        Whether to plot the corner IDs or not.

    Returns
    -------
    None
        The function plots the 3D scatter points and handles legends.

    """

    MARKER = "." 
    SIZE_MARKER = 1.1
    COLER_MARKER = "tab:blue"

    x_coordinates, y_coordinates, z_coordinates, ids = [], [], [], []

    # parse the dict 
    for id, coords in coords_3d_points.items():
        ids.append(id)
        x_coordinates.append(coords[0])
        y_coordinates.append(coords[1])
        z_coordinates.append(coords[2])

    # plot the 3d points
    ax.scatter(x_coordinates, y_coordinates, z_coordinates, marker=MARKER, s=SIZE_MARKER, c=COLER_MARKER)

    # handle the legends next to each scatter point
    for id, x, y, z in zip(ids, x_coordinates, y_coordinates, z_coordinates):
        try: 
            int(id)
            if plot_corners_ids:
                ax.text(x, y, z, id, fontsize=font_size)
        except ValueError:
            ax.text(x, y, z, id, fontsize=font_size)

def filter_cloud_of_3d_points(cloud_of_3d_points : dict, coords_2d_projections : dict) -> dict:
    """
    Filter the cloud of 3D points based on the specified 2D projections.

    Parameters
    ----------
    cloud_of_3d_points : dict
        Dictionary containing the 3D coordinates of each point.
    coords_2d_projections : dict
        Dictionary containing the 2D projections and their associated information.

    Returns
    -------
    dict
        Dictionary containing the filtered 3D points.

    """
    return {key: value for key, value in cloud_of_3d_points.items() if key in coords_2d_projections}

## related to 2d image ######################################################################################################################
#############################################################################################################################################

def get_scatter_of_2D_points_projection(input_image_dir: str,
                                        charuco_num_of_columns: int = 44,
                                        charuco_num_of_rows: int = 28,
                                        charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000),
                                        sample_diameter_mm: float = 70,
                                        show_result: bool = False,
                                        save_result: bool = False) -> tuple:
    """
    Generates a scatter plot of the Charuco corners detected in the input image.

    Parameters
    ----------
    input_image_dir : str
        The directory of the input image.
    charuco_num_of_columns : int, optional
        The number of columns in the Charuco board, by default 44
    charuco_num_of_rows : int, optional
        The number of rows in the Charuco board, by default 28
    charuco_dictionary : cv2.aruco_Dictionary, optional
        The dictionary used to generate the Charuco board, by default aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
    sample_diameter_mm : float, optional
        The diameter of the sample in millimeters, by default 70
    show_result : bool, optional
        Whether to show the result of the Charuco corner detection, by default False
    save_result : bool, optional
        Whether to save the result of the Charuco corner detection, by default False

    Returns
    -------
    tuple
        A tuple containing the number of Charuco corners found, the Charuco corners detected, and the size of the input image.

    Notes
    -----
    This function first creates a Charuco board using the provided parameters. It then reads the input image and processes it to detect 
    the Charuco corners. The function then post-processes the image to draw the detected corners and optionally saves the result. Finally, 
    the function returns the number of Charuco corners found, the Charuco corners detected, and the size of the input image.

    If `show_result` is set to True, the function displays the input image with the detected Charuco corners drawn on it. If `save_result` 
    is set to True, the function prompts the user to select a directory and saves the input image with the detected Charuco corners drawn on it.
    """
    # Create the charuco board
    charuco_board = create_charuco_board(charuco_num_of_columns = charuco_num_of_columns,
                                         charuco_num_of_rows = charuco_num_of_rows, 
                                         charuco_dictionary = charuco_dictionary,
                                         sample_diameter_mm = sample_diameter_mm)

    # Read the input image
    input_image = cv2.imread(input_image_dir)
    image_in_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    image_size = image_in_gray.shape    

    # Process: Detect Charuco corners
    retval, charuco_corners_image_coords, charuco_corners_ids = _get_charuco_corners_image_coords(image_in_gray, charuco_dictionary, charuco_board)

    if retval:
        # Post-process: Draw detected corners on the input image
        aruco.drawDetectedCornersCharuco(image_in_gray, charuco_corners_image_coords, charuco_corners_ids)

        # Post-process: Extract u and v coordinates of the detected corners
        u_coordinates = np.zeros(retval)
        v_coordinates = np.zeros(retval)
        for index in range(retval): 
            u_coordinates[index] = charuco_corners_image_coords[index][0][0]
            v_coordinates[index] = charuco_corners_image_coords[index][0][1]

        # Post-process: Store the found Charuco corners in a dict
        coords_2d_projections = {
        corner_id[0]: np.array([u, v])
        for corner_id, u, v in zip(charuco_corners_ids, u_coordinates, v_coordinates)
        }
    
    # Display the image with the detected Charuco corners drawn on it
    if show_result:
        # Create a named window with a fixed size
        name_window = 'Image_with_detected_corners'
        resized_im = resize_with_aspect_ratio(image_in_gray, width=1050)

        # Display the image
        cv2.imshow(name_window, resized_im)
        cv2.waitKey(0)  # Wait until a key is pressed
        cv2.destroyAllWindows()

        # Save the image with the detected Charuco corners drawn on it
        if save_result: 
            output_directory = ask_for_directory()
            if output_directory:
                file_name = Path(input_image_dir).absolute().name
                new_name = file_name.rsplit(".", 1)[0] + "_with_detected_charuco_corners.jpg"
                output_path = Path(output_directory) / new_name
                cv2.imwrite(str(output_path), image_in_gray)
            else: 
                logger.info('No directory given')
    
    return retval, coords_2d_projections, image_size

def create_charuco_board(charuco_num_of_columns: int = 44,
                         charuco_num_of_rows: int = 28,
                         charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000),
                         sample_diameter_mm: float = 70,
                         factor_between_square_and_marker = 3 / 5,
                         show_the_charuco_board: bool = False,
                         save_the_charuco_board: bool = False) -> cv2.aruco_CharucoBoard:
    """
    Creates a charuco board object with the specified number of columns, rows, dictionary, sample diameter, and marker length.

    Parameters
    ----------
    charuco_num_of_columns : int, optional
        The number of columns in the charuco board, by default 44
    charuco_num_of_rows : int, optional
        The number of rows in the charuco board, by default 28
    charuco_dictionary : cv2.aruco_Dictionary, optional
        The aruco dictionary to use for corner detection, by default aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
    sample_diameter_mm : float, optional
        The diameter of the sample in millimeters, by default 70
    factor_between_square_and_marker : float, optional
        The factor between the square size and the marker size, by default 3/5
    show_the_charuco_board : bool, optional
        Whether to show the charuco board in a window, by default False
    save_the_charuco_board : bool, optional
        Whether to save the charuco board as an image file, by default False

    Returns
    -------
    cv2.aruco_CharucoBoard
        The created charuco board object.

    Notes
    -----
    The function calculates the square size and marker size based on the sample diameter and factor between square and marker. 
    It then creates a charuco board object with the specified number of columns, rows, dictionary, square size, and marker size. 
    If `show_the_charuco_board` is set to True, the function displays the charuco board in a window with a fixed size. 
    If `save_the_charuco_board` is set to True, the function prompts the user to select an output directory and saves 
    the charuco board as an image file with the specified name.
    """  
    # Show the charuco board in a window if specified
    charuco_square_length_mm = round((np.pi * sample_diameter_mm) / charuco_num_of_columns)
    charuco_marker_length_mm = round(factor_between_square_and_marker * charuco_square_length_mm)
    
    # Create a charuco board object with the specified number of columns, rows, dictionary, square size, and marker size
    charuco_board = aruco.CharucoBoard_create(charuco_num_of_columns,
                                    charuco_num_of_rows,
                                    charuco_square_length_mm * 1e-3,
                                    charuco_marker_length_mm * 1e-3,
                                    charuco_dictionary)  
    
    # Show the charuco board in a window if specified
    if show_the_charuco_board:
        image = np.ones((2100, 3300), dtype=np.uint8) * 255
        imgboard = charuco_board.draw((3300, 2100), image)
        
        # Create a named window with a fixed size
        name_window = f'Charuco_board_{charuco_num_of_rows}_rows_{charuco_num_of_columns}_columns'
        resized_im = resize_with_aspect_ratio(imgboard, width=1650)

        cv2.namedWindow(name_window, cv2.WINDOW_NORMAL)
        cv2.imshow(name_window, resized_im)
        cv2.waitKey(0)  # Wait until a key is pressed
        cv2.destroyAllWindows()
        
        if save_the_charuco_board: 
            output_directory = ask_for_directory()
            if output_directory:
                output_path = Path(output_directory) / "charuco_board.jpg"
                cv2.imwrite(str(output_path), imgboard)
            else: 
                logger.info('No directory given')

    return charuco_board

def resize_with_aspect_ratio(image, width=None, height=None, inter=cv2.INTER_AREA):
    """
    Resizes an image while maintaining its aspect ratio.

    Parameters
    ----------
    image : numpy.ndarray
        The image to be resized.
    width : int, optional
        The desired width of the resized image. The default is None.
    height : int, optional
        The desired height of the resized image. The default is None.
    inter : int, optional
        The interpolation method to use during resizing. The default is cv2.INTER_AREA.

    Returns
    -------
    numpy.ndarray
        The resized image.

    Notes
    -----
    This function is based on the code provided in the following Stack Overflow post:
    https://stackoverflow.com/questions/35180764/opencv-python-image-too-big
    """
   
    # Get the original dimensions of the image
    h, w = image.shape[:2]

    # If both width and height are None, return the original image
    if width is None and height is None:
        return image

    # Calculate the aspect ratio of the original image
    aspect_ratio = w / h

    # If the width is None, set the width based on the height and aspect ratio
    if width is None:
        width = int(height * aspect_ratio)

    # If the height is None, set the height based on the width and aspect ratio
    if height is None:
        height = int(width / aspect_ratio)

    # Resize the image
    resized_image = cv2.resize(image, (width, height), interpolation=inter)

    return resized_image

def ask_for_directory():
    """
    Prompts the user to select a directory using a Tkinter file dialog.

    Parameters
    ----------
    None

    Returns
    -------
    str
        The path of the selected directory if a directory is selected, None otherwise.
    """

    # Create the Tkinter root window
    root = Tk()
    root.withdraw()  # Hide the root window

    # Prompt the user to select a directory
    directory_path = askdirectory(title='Select Directory')

    # Check if a directory was selected
    if directory_path:
        return directory_path
    else:
        pass

def _get_charuco_corners_image_coords(image_in_gray, charuco_dictionary, charuco_board):
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


if __name__ == "__main__":
    get_cloud_of_3d_points(plot_the_cloud_of_3d_points=True)

    # dictionnary = {'3': np.array([100 ,   100,  100], dtype=np.float32), 'rp1_config_0': np.array([-107.93629 ,   74.088196,  123.84841 ], dtype=np.float32), 'rp1_config_1': np.array([-107.93629 ,   74.088196,  123.84841 ], dtype=np.float32), 'rp1_config_2': np.array([-76.71401, 106.13757, 124.18906], dtype=np.float32), 'rp1_config_3': np.array([-45.03127, 138.42816, 124.48046], dtype=np.float32), 'rp1_config_4': np.array([-74.48471, 112.1615 , 126.59885], dtype=np.float32)}
    # dictionnary_2 = {5: np.array([20 ,   80,  100], dtype=np.float32)}
    # plot_3d_points(dict_s_coords_3d_points=[dictionnary, dictionnary_2], length_arrows_mm=20, flag=True)

    # directory = r"C:\Users\hilar\Documents\project\geocam\src\images\calibration_img_example.jpg"
    # retval, coords_2d_projections, image_size = get_scatter_of_2D_points_projection(input_image_dir = directory, flag2=True)

    get_scatter_of_2D_points_projection(input_image_dir=r"C:\Users\hilar\Documents\project\geocam\src\images\calibration_img_example.jpg",
                                        show_result=True)
    pass
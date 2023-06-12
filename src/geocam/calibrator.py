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
import glob

from geocam.utils import ask_for_directory, resize_with_aspect_ratio
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import Union, List, Dict, Tuple 
from pathlib import Path
from cv2 import aruco
from scipy.stats import norm
from scipy.optimize import minimize

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

#############################################################################################################################################
## CLASSES ##################################################################################################################################
#############################################################################################################################################
# TODO: get the im_size in check 
class Calibrator():
    def __init__(self) -> None:
        # Initialize info related to charuco board 
        self.num_of_charuco_squares_horizontally: int = 44
        self.num_of_charuco_squares_vertically: int = 28 
        self.charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
        self.sample_height_mm: float = 140 
        self.sample_diameter_mm: float = 70

        # Prepare storage for results 
        self.calibration_data = self._prepare_storage_of_results()
            
        logger.info(f"{self}")
        logger.info(f"Calibration initialization:\n {self.calibration_data}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        return f"Instanciated a {self.__class__.__name__} class instance"
    
    def _prepare_storage_of_results(self):
        # Data about images - Ask for the directory where the images are stored 
        directory = ask_for_directory()
        if directory:
            calibration_images_path = Path(directory) / "*.jpg"
            calibration_images_directories = glob.glob(str(calibration_images_path))
        else:
            # raise an error 
            logger.exception("Can't carry calibration without calibration images")
        
        # Data about images - Initiate dicts for storage
        calibration_data = {"overall_analysis_data":{}, "image_specific_data":{}}
        
        # Data about images - Initiate dicts for overall data 
        calibration_data["overall_analysis_data"].update({"image_size":None})
        calibration_data["overall_analysis_data"].update({"num_images":len(calibration_images_directories)})
        calibration_data["overall_analysis_data"].update({"opencv_result_retval":None})
        calibration_data["overall_analysis_data"].update({"custom_optimisation_retval":None})
        calibration_data["overall_analysis_data"].update({"opencv_result_camera_matrix":None})
        calibration_data["overall_analysis_data"].update({"opencv_result_dist_coeff":None})
        calibration_data["overall_analysis_data"].update({"opencv_result_stdDeviationsIntrinsic":None})
        calibration_data["overall_analysis_data"].update({"opencv_result_stdDeviationsExtrinsic":None})
        calibration_data["overall_analysis_data"].update({"custom_optimisation_glob_result_dist_coeff":None})
        calibration_data["overall_analysis_data"].update({"custom_optimisation_glob_result_stdDeviations_dist_coeff":None})
        calibration_data["overall_analysis_data"].update({"calibration_images_directories":calibration_images_directories})
        calibration_data["overall_analysis_data"].update({"all_object_points":None})
        calibration_data["overall_analysis_data"].update({"all_image_points":None})
    
        # Data about images - Initiate dicts for image specific data
        result_per_image_dict = {
                                "calibration_image_directory":None,
                                "coords_2d_projections_dict":None, 
                                "cloud_of_3d_points_dict_filtered":None,
                                "opencv_result_rvec":None,
                                "opencv_result_tvec":None,
                                "opencv_result_perViewError":None,
                                "custom_optimisation_perViewError":None,
                                "custom_optimisation_per_image_dist_coeff":None    
                                }
        for calibration_image_dir in calibration_images_directories:
            # Get the image size
            if not calibration_data["overall_analysis_data"]["image_size"]:
                input_image = cv2.imread(calibration_image_dir)
                calibration_data["overall_analysis_data"]["image_size"] = input_image.shape[:2]
            # Update the calibration_image directory
            result_per_image_dict["calibration_image_directory"] = calibration_image_dir
            # Get image name and prepare dicts speficic to image
            img_name = Path(calibration_image_dir).absolute().name
            calibration_data["image_specific_data"].update({img_name:result_per_image_dict})

        return calibration_data


    def get_cloud_of_3d_points(self, plot_the_cloud_of_3d_points: bool = False, plot_corners_ids: bool = False) -> Dict[str, np.ndarray]:
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

        logger.info(f"Generating cloud of 3D points with {self.num_of_charuco_squares_horizontally} squares horizontally, "
                    f"{self.num_of_charuco_squares_vertically} squares vertically, a sample height of {self.sample_height_mm} mm, "
                    f"and a sample diameter of {self.sample_diameter_mm} mm.")

        # Calculate the radius of the sample
        sample_radius_mm = 0.5 * self.sample_diameter_mm

        # Calculate the length of a charuco square
        charuco_square_length_mm = round((np.pi * self.sample_diameter_mm) / self.num_of_charuco_squares_horizontally)

        # Calculate the elementary angle
        elementary_angle_rad = charuco_square_length_mm / sample_radius_mm

        # Calculate useful informations in cylendric system
        theta = np.array([index * elementary_angle_rad for index in range(self.num_of_charuco_squares_horizontally - 1)])
        levels = np.arange(charuco_square_length_mm, self.sample_height_mm, charuco_square_length_mm)

        # Calculate the coordinates of each corner in cartesian system
        x_coordinates = np.tile(np.cos(theta) * sample_radius_mm, len(levels))
        y_coordinates = np.tile(np.sin(theta) * sample_radius_mm, len(levels))
        z_coordinates = np.repeat(levels, len(theta))

        # Create a dictionary of the 3D coordinates of each corner
        num_of_corners = (self.num_of_charuco_squares_vertically - 1) * (self.num_of_charuco_squares_horizontally - 1)
        coords_3d_points = {
            corner_id: np.array([x, y, z])
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
            self.plot_3d_points(coords_3d_points, plot_corners_ids = plot_corners_ids)

        # Return the dictionary of 3D coordinates
        return coords_3d_points
    
    def plot_3d_points(self, dict_s_coords_3d_points: Union[List[Dict], List], plot_corners_ids: bool = False) -> None:
        """
        Plot the 3D points in a scatter plot.

        Parameters
        ----------
        dict_s_coords_3d_points : List[Dict] or Dict
            List of dictionaries or a single dictionary containing the 3D coordinates of each 3D point.
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

        if not dict_s_coords_3d_points:
            raise ValueError("'dict_s_coords_3d_points' is empty.")
        
        # create the figure  
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        # draw a 3d coordinates system
        self._plot_3d_coordinate_system(ax=ax, add_planes=True)

        # if list of dict than plot the different sets of data 
        if isinstance(dict_s_coords_3d_points, list):
            logger.info("Plotting multiple sets of data")
            for coords_3d_points in dict_s_coords_3d_points:
                self._plot_3d_scatter_and_handle_legends(ax=ax, coords_3d_points=coords_3d_points, plot_corners_ids=plot_corners_ids)
        # elif dict than plot the only set given  
        elif isinstance(dict_s_coords_3d_points, dict):
            logger.info("Plotting singular set of data")
            self._plot_3d_scatter_and_handle_legends(ax=ax, coords_3d_points=dict_s_coords_3d_points, plot_corners_ids=plot_corners_ids)

        # additional settings 
        ax.axis('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Cloud of 3D points')
        # plt.axis('equal')
        plt.show()

    def _plot_3d_coordinate_system(self, ax: plt.Axes, origin:np.array = np.zeros(3), add_planes:bool = False):
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
        LENGTH_ARROW_MM = 40
        PLANES_COLOR = "orange"
        PLANES_ALPHA = 0.4

        # Draw the arrows 
        ax.quiver(origin[0], origin[1], origin[2], 1, 0, 0, color=X_ARROW_COLOR, length = LENGTH_ARROW_MM, normalize=True)
        ax.quiver(origin[0], origin[1], origin[2], 0, 1, 0, color=Y_ARROW_COLOR, length = LENGTH_ARROW_MM, normalize=True)
        ax.quiver(origin[0], origin[1], origin[2], 0, 0, 1, color=Z_ARROW_COLOR, length = LENGTH_ARROW_MM, normalize=True)
        ax.text(LENGTH_ARROW_MM * 0.1, LENGTH_ARROW_MM * 0.0, - LENGTH_ARROW_MM * 0.2, r'$0$')
        ax.text(LENGTH_ARROW_MM * 1.3, LENGTH_ARROW_MM * 0, LENGTH_ARROW_MM * 0, r'$x$')
        ax.text(LENGTH_ARROW_MM * 0, LENGTH_ARROW_MM * 1.3, LENGTH_ARROW_MM * 0, r'$y$')
        ax.text(LENGTH_ARROW_MM * 0, LENGTH_ARROW_MM * 0, LENGTH_ARROW_MM * 1.3, r'$z$')

        # Draw plans normal to axis 
        if add_planes:
            elem_length_1 = 0.1 * LENGTH_ARROW_MM
            elem_length_2 = 0.6 * LENGTH_ARROW_MM

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

    def _plot_3d_scatter_and_handle_legends(self, ax: plt.Axes, coords_3d_points: dict, plot_corners_ids: bool) -> None:
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
        FONT_SIZE = 6

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
                    ax.text(x, y, z, str(id), fontsize=FONT_SIZE)
            except ValueError:
                ax.text(x, y, z, id, fontsize=FONT_SIZE)

    def filter_cloud_of_3d_points(self, cloud_of_3d_points: dict, coords_2d_projections: dict) -> dict:
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
    
    def get_scatter_of_2D_points_projection(self, input_image_dir: str, show_result: bool = False, save_result: bool = False) -> Tuple[int, Dict[str,np.array]]:
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
            A tuple containing the number of Charuco corners found and the Charuco corners detected.

        Notes
        -----
        This function first creates a Charuco board using the provided parameters. It then reads the input image and processes it to detect 
        the Charuco corners. The function then post-processes the image to draw the detected corners and optionally saves the result. Finally, 
        the function returns the number of Charuco corners found and the Charuco corners detected.

        If `show_result` is set to True, the function displays the input image with the detected Charuco corners drawn on it. If `save_result` 
        is set to True, the function prompts the user to select a directory and saves the input image with the detected Charuco corners drawn on it.
        """

        # Create the charuco board
        charuco_board = self.create_charuco_board()

        # Read the input image - Store the image size: needed for camera_calibration
        input_image = cv2.imread(input_image_dir)
        image_in_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        # if not self.image_size == image_in_gray.shape:    
        #     self.image_size = image_in_gray.shape    

        # Process: Detect Charuco corners
        retval, charuco_corners_image_coords, charuco_corners_ids = self._get_charuco_corners_image_coords(image_in_gray, self.charuco_dictionary, charuco_board)

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
        
        return retval, coords_2d_projections
    
    def create_charuco_board(self, show_the_charuco_board: bool = False, save_the_charuco_board: bool = False) -> cv2.aruco_CharucoBoard:
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
        # Constant 
        FACTOR_BETWEEN_SQUARE_AND_MARKER = 3/5

        # Show the charuco board in a window if specified
        charuco_square_length_mm = round((np.pi * self.sample_diameter_mm) / self.num_of_charuco_squares_horizontally)
        charuco_marker_length_mm = round(FACTOR_BETWEEN_SQUARE_AND_MARKER * charuco_square_length_mm)
        
        # Create a charuco board object with the specified number of columns, rows, dictionary, square size, and marker size
        charuco_board = aruco.CharucoBoard_create(self.num_of_charuco_squares_horizontally,
                                        self.num_of_charuco_squares_vertically,
                                        charuco_square_length_mm * 1e-3,
                                        charuco_marker_length_mm * 1e-3,
                                        self.charuco_dictionary)  
        
        # Show the charuco board in a window if specified
        if show_the_charuco_board:
            image = np.ones((2100, 3300), dtype=np.uint8) * 255
            imgboard = charuco_board.draw((3300, 2100), image)
            
            # Create a named window with a fixed size
            name_window = f'Charuco_board_{self.num_of_charuco_squares_vertically}_rows_{self.num_of_charuco_squares_horizontally}_columns'
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
    
    def _get_charuco_corners_image_coords(self, image_in_gray, charuco_dictionary, charuco_board):
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
        
    def calibrate_camera(self) -> None:

        # Get opencv's calibration results 
        self._camera_calibration_opencv()

        # Work on the distorsion coefficients 
        # self._enhance_distorsion_handling_and_stat_analysis_of_results()

        # Log results
        # logger.debug(f"Calibration results:\n{self.calibration_data}")

    def _pair_2d_and_3d_points_and_format_for_calibration(self) -> Tuple[List[np.array], List[np.array]]:
        """
        This function looks in the self.calibration_data for the directory containing the calibration images. 
        It then looks for Charuco corners in each image and pairs them with the corresponding 3D points from a calibration rig. 
        Finally it formats and returns the object points and image points as lists of numpy arrays.

        Returns:
            Tuple[List[np.ndarray], List[np.ndarray]]: A tuple containing two lists of numpy arrays: the object points and image points.
        """

        # Initialize lists to store fromated data 
        all_object_points = [] # This will be a list of the lists of found 3D points for each calibration image
        all_image_points = [] # This will be a list of the lists of found 2D points for each calibration image
        all_found_3d_points_dict = {} # This dictionnary will contain a single copy of every found corner during the analysis 

        # Get the cloud of 3D points present on the calibration rig 
        cloud_of_3d_points_dict = self.get_cloud_of_3d_points()

        # Process each of the calibration images 
        for calibration_image_dir in self.calibration_data["overall_analysis_data"]["calibration_images_directories"]:
            # Get image name
            img_name = Path(calibration_image_dir).absolute().name

            # Match found 2D points on image and 3D points from the calibration rig 
            retval, coords_2d_projections_dict = self.get_scatter_of_2D_points_projection(input_image_dir = calibration_image_dir)
            cloud_of_3d_points_dict_filtered = self.filter_cloud_of_3d_points(cloud_of_3d_points_dict, coords_2d_projections_dict)

            # Format data for calibration 
            object_points = np.zeros((retval, 3), dtype=np.float32)
            image_points = np.zeros((retval, 2), dtype=np.float32)
            for index, key in enumerate(cloud_of_3d_points_dict_filtered):
                object_points[index] = cloud_of_3d_points_dict_filtered[key]
                image_points[index] = coords_2d_projections_dict[key]
            all_object_points.append(object_points)
            all_image_points.append(image_points)

            # Post-process: store the found 2D and 3D points
            self.calibration_data["image_specific_data"][img_name]["coords_2d_projections_dict"] = coords_2d_projections_dict
            self.calibration_data["image_specific_data"][img_name]["cloud_of_3d_points_dict_filtered"] = cloud_of_3d_points_dict_filtered
            
            # Post-process: refine the sorting - in found_3d_points_dict every corner is only present once 
            common_keys = set(coords_2d_projections_dict.keys()).intersection(cloud_of_3d_points_dict.keys())
            newly_found_key_counter = 0
            for key in common_keys:
                if key not in all_found_3d_points_dict:
                    newly_found_key_counter += 1
                    all_found_3d_points_dict[key] = cloud_of_3d_points_dict[key]

            # Log infos 
            logger.debug(f"Found {len(cloud_of_3d_points_dict_filtered)} corners in the image")
            logger.debug(f"Here is the list of ids :\n {cloud_of_3d_points_dict_filtered.keys()}")
            logger.debug(f"{len(cloud_of_3d_points_dict_filtered.keys())} were found this time.") 
            logger.debug(f"Of which, {newly_found_key_counter} were found for the first time.") 
            logger.debug(f"So far, {len(all_found_3d_points_dict.keys())} were found")       
            logger.debug(f"Here is the updated found_3d_points_dict:\n {all_found_3d_points_dict.keys()}")

        # Store all_found_3d_points_dict
        self.calibration_data["overall_analysis_data"]["all_found_3d_points_dict"] = all_found_3d_points_dict
        # Store all_image_points - list
        self.calibration_data["overall_analysis_data"]["all_image_points"] = all_image_points
        # Store all_object_points - list 
        self.calibration_data["overall_analysis_data"]["all_object_points"] = all_object_points
    
    def _camera_calibration_opencv(self) -> None:

        # Constants 
        CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.001)
        FLAGS = cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL
        DIST_COEFFS_INIT = np.zeros((5,1))

        # print(self._initialize_camera_matrix_with_opencv())
        IMAGE_SIZE = self.calibration_data["overall_analysis_data"]["image_size"]
        
        INITIAL_CAMERA_MATRIX = np.array([[ 3.62916898e+03,    0., 1.58513866e+03],
                                    [    0., 3.77369633e+03, 2.10494246e+03],
                                    [    0.,    0.,           1.]])
        
        # INITIAL_CAMERA_MATRIX = self._initialize_camera_matrix_with_opencv()
        

        # Prepare data for calibration 
        self._pair_2d_and_3d_points_and_format_for_calibration()
        
        # Carry the calibration 
        (retval, cameraMatrix, distCoeffs, rvecs, tvecs, 
         stdDeviationsIntrinsics, stdDeviationsExtrinsics, 
         perViewErrors) = cv2.calibrateCameraExtended(objectPoints = self.calibration_data["overall_analysis_data"]["all_object_points"], 
                                                    imagePoints = self.calibration_data["overall_analysis_data"]["all_image_points"], 
                                                    imageSize = IMAGE_SIZE,
                                                    cameraMatrix = INITIAL_CAMERA_MATRIX,
                                                    distCoeffs = DIST_COEFFS_INIT,
                                                    flags=FLAGS,
                                                    criteria=CRITERIA)
        
        # Store image specific results 
        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]):
            # Get image name
            img_name = Path(calibration_image_dir).absolute().name
            # Store image specific results - rotatation vector
            self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"] = rvecs[index]
            # Store image specific results - translation vector
            self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"] = tvecs[index]
            # Store image specific results - per view errors
            self.calibration_data["image_specific_data"][img_name]["opencv_result_perViewError"] = perViewErrors[index]

        # Store overall results - overall error of 3D corners reprojection in 2D image 
        self.calibration_data["overall_analysis_data"]["opencv_result_retval"] = retval
        # Store overall results - camera matrix
        self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"] = cameraMatrix
        # Store overall results - distortion coefficients  
        self.calibration_data["overall_analysis_data"]["opencv_result_dist_coeff"] = distCoeffs
        # Store overall results - standard deviations intrinsics - (fx,fy,cx,cy,k1,k2,p1,p2,k3,k4,k5,k6,s1,s2,s3,s4,τx,τy)
        self.calibration_data["overall_analysis_data"]["opencv_result_stdDeviationsIntrinsic"] = stdDeviationsIntrinsics
        # Store overall results - standard deviations extrinsics - (R0,T0,…,RM−1,TM−1) where M is the number of images, Ri,Ti are concatenated 1x3 vectors. 
        self.calibration_data["overall_analysis_data"]["opencv_result_stdDeviationsExtrinsic"] = stdDeviationsExtrinsics

    def _initialize_camera_matrix_with_opencv(self) -> None:

        # Constants 
        CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.001)
        FLAGS = cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL
        DIST_COEFFS_INIT = np.zeros((5,1))
        IMAGE_SIZE = self.calibration_data["overall_analysis_data"]["image_size"]
        INITIAL_CAMERA_MATRIX = np.array([[ 1000.,    0., IMAGE_SIZE[0]/2.],
                                [    0., 1000., IMAGE_SIZE[1]/2.],
                                [    0.,    0.,           1.]])
        
        # Prepare data for calibration 
        self._pair_2d_and_3d_points_and_format_for_calibration()
        
        # Carry the calibration 
        (retval, cameraMatrix, distCoeffs, rvecs, tvecs, 
        stdDeviationsIntrinsics, stdDeviationsExtrinsics, 
        perViewErrors) = cv2.calibrateCameraExtended(objectPoints = self.calibration_data["overall_analysis_data"]["all_object_points"], 
                                                    imagePoints = self.calibration_data["overall_analysis_data"]["all_image_points"], 
                                                    imageSize = IMAGE_SIZE,
                                                    cameraMatrix = INITIAL_CAMERA_MATRIX,
                                                    distCoeffs = DIST_COEFFS_INIT,
                                                    flags=FLAGS,
                                                    criteria=CRITERIA)

        return cameraMatrix

    ## TODO comment these functions and fix the format of object and image points  #############################################################
    def _enhance_distorsion_handling_and_stat_analysis_of_results(self):

        # Initiate temporary array for stat analysis 
        num_images = self.calibration_data["overall_analysis_data"]["num_images"]
        temp_array_dist_coeffs = np.zeros((num_images, 20), dtype=np.float32)
        temp_array_errors = np.zeros(num_images, dtype=np.float32)
  
        # Optimize the estimation of the distorsion parameters  
        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]): 

            # Get image name and require data 
            img_name = Path(calibration_image_dir).absolute().name
            image_points = self.calibration_data["overall_analysis_data"]["all_image_points"][index]
            object_points = self.calibration_data["overall_analysis_data"]["all_object_points"][index]
            rvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"]
            tvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"]
            rotation_matrix, _ = cv2.Rodrigues(rvec)
            extrinsic_matrix = np.hstack((rotation_matrix, tvec))

            # Carry custom calibration 
            DISTORTION_COEFFS = np.zeros(20)
            OPENCV_CAMERA_MATRIX = self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"]
            optimized_distortion_coefficients, error = self.custom_calibration(object_points=[object_points], 
                                                extrinsic_matrix=extrinsic_matrix, 
                                                cameraMatrix=OPENCV_CAMERA_MATRIX, 
                                                image_points=[image_points], 
                                                distortion_coefficients = DISTORTION_COEFFS)
            
            # Store results - dist coefficiants per image 
            self.calibration_data["image_specific_data"][img_name]["custom_optimisation_per_image_dist_coeff"] = optimized_distortion_coefficients
            # Store results - error per image 
            self.calibration_data["image_specific_data"][img_name]["custom_optimisation_perViewError"] = error
            # Store results - dist coefficiants and errors for stat analysis 
            temp_array_dist_coeffs[index,:] = optimized_distortion_coefficients
            temp_array_errors[index] = error

        # Store results - stat analysis
        self.calibration_data["overall_analysis_data"]["custom_optimisation_glob_result_dist_coeff"] = np.mean(a=temp_array_dist_coeffs, axis=0, dtype=np.float32)
        self.calibration_data["overall_analysis_data"]["custom_optimisation_retval"] = np.mean(a=temp_array_errors, axis=0, dtype=np.float32)
        self.calibration_data["overall_analysis_data"]["custom_optimisation_glob_result_stdDeviations_dist_coeff"] = np.std(a=temp_array_dist_coeffs, axis=0, dtype=np.float32)
        
    def custom_calibration(self, object_points, 
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

        # optimize calling the minimize function
        result = minimize(fun = self.reprojection_error_minization, x0 = distortion_coefficients, args = args, method='Powell', options=options)#, constraints=constraints)
        if result.success:
            error = self.reprojection_error(result.x, object_points, extrinsic_matrix, cameraMatrix, image_points)
            return result.x, error

    def reprojection_error_minization(self, distortion_coefficients, *args):

        object_points, extrinsic_matrix, cameraMatrix, image_points = args 

        # get the image points resulting from the mapping to the scaled and skewed sensor coordinates by the affine transformation
        computed_image_points = self.projection_on_sensor(object_points = object_points, 
                                                    extrinsic_matrix = extrinsic_matrix, 
                                                    cameraMatrix = cameraMatrix,
                                                    distortion_coefficients = distortion_coefficients)

        # compute the overall RMS 
        custom_retval = np.linalg.norm(image_points - computed_image_points) / len(computed_image_points)

        return custom_retval
    
    def reprojection_error(self, optimized_distortion_coefficients, *args):

        object_points, extrinsic_matrix, cameraMatrix, image_points = args 

        # get the image points resulting from the mapping to the scaled and skewed sensor coordinates by the affine transformation
        computed_image_points = self.projection_on_sensor(object_points = object_points, 
                                                    extrinsic_matrix = extrinsic_matrix, 
                                                    cameraMatrix = cameraMatrix,
                                                    distortion_coefficients = optimized_distortion_coefficients)

        # compute the overall RMS 
        error_for_each_point = image_points - computed_image_points
        # print(error_for_each_point)
        custom_retval = np.linalg.norm(image_points - computed_image_points) / len(computed_image_points)

        return custom_retval

    def projection_on_sensor(self, object_points, 
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
        lens_distorted_2d_coords = self.warp_function(projection_on_normalized_img_plane,
                                                distortion_coefficients)

        # format the result 
        lens_distorted_2d_coords_hom = np.hstack((lens_distorted_2d_coords, np.ones((lens_distorted_2d_coords.shape[0],1))))

        # mapping to the scaled and skewed sensor coordinates by the affine transformation
        computed_image_points = np.dot(lens_distorted_2d_coords_hom, cameraMatrix[:-1].T)

        return computed_image_points

    def warp_function(self, projection_on_normalized_img_plane, distortion_coefficients):
    
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

    ## TODO write these functions ################################################################################################
    def locate_camera_in_world_coordinates(self, num_calibration_rig_configs:int = 5, num_calibration_image_per_config:int = 3):
        pass

    def get_stats():
        pass 
    ##############################################################################################################################


    

    
    


if __name__ == "__main__":
    calibrator = Calibrator()
    calibrator.calibrate_camera()
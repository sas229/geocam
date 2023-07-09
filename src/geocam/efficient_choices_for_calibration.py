"""
:Name: calibrator
:Description: This module is used for the various calibration operations
:Date: 2023-07-06
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
import geocam.calibrator_utils as calibrator_utils 

from matplotlib import cm
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
## CLASSES ##################################################################################################################################
#############################################################################################################################################

# TODO: get the im_size in check 
class Calibrator():

    ## INITIALISATION FUNCTIONS #################################################################################################################
    #############################################################################################################################################
    
    def __init__(self) -> None:
        # Initialise info related to charuco board 
        self.num_of_charuco_squares_horizontally: int = 44
        self.num_of_charuco_squares_vertically: int = 28 
        self.charuco_dictionary: cv2.aruco_Dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
        self.sample_height_mm: float = 140 
        self.sample_diameter_mm: float = 70

        # Prepare storage for results 
        self.calibration_data = calibrator_utils.prepare_storage_of_results(self)
        
        logger.info(f"{self}")
        logger.info(f"Calibration initialisation:\n {self.calibration_data}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        return f"Instanciated a {self.__class__.__name__} class instance"
    
    ## PRE AND POST CALIBRATION PROCESS FUNCTIONS ###############################################################################################
    #############################################################################################################################################

    ## Working with coordinates - 3D world corrss of every corners ##############################################################################
    #############################################################################################################################################
    # NOTE: There's only one calibration rig so this function is only called once
    def get_cloud_of_3d_points(self) -> Dict[str, np.ndarray]:
        return calibrator_utils.get_cloud_of_3d_points(self)

    ## Working with coordinates - 2D world coords of detected corners ###########################################################################
    #############################################################################################################################################
    # NOTE: There can be multiple images; therefore, this function is called as many times as there are images. 
    def get_scatter_of_2D_points_projection(self) -> Tuple[int, Dict[str,np.array]]:
        return calibrator_utils.get_scatter_of_2D_points_projection(self)

    ## Working with coordinates - identify the points with both info in 2D and 3D ###############################################################
    #############################################################################################################################################
    # NOTE: Since this function filters 3D points based on found 2D points, this function is called as many times as there are images.
    def filter_cloud_of_3d_points(self) -> dict: 
        return calibrator_utils.filter_cloud_of_3d_points(self)
    
    ## Format data for analysis - iterate on images #############################################################################################
    #############################################################################################################################################
    def prepare_data_for_calibration_with_opencv(self):
        calibrator_utils.pair_2d_and_3d_points_and_format_for_calibration(self)

    ## CALIBRATION PROCESS FUNCTIONS ############################################################################################################
    #############################################################################################################################################

    ## Calibrate camera with opencv - yields info on intrinsic and extrinsic matrices ###########################################################
    #############################################################################################################################################
    def calibrate_with_opencv(self) -> None:
        # Constants 
        CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.001)
        FLAGS = cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL
        DIST_COEFFS_INIT = np.zeros((5,1))
        IMAGE_SIZE = self.calibration_data["overall_analysis_data"]["image_size"]
        INITIAL_CAMERA_MATRIX = np.array([[ 3.62916898e+03,    0., 1.58513866e+03],
                                    [    0., 3.77369633e+03, 2.10494246e+03],
                                    [    0.,    0.,           1.]])
        
        # INITIAL_CAMERA_MATRIX = np.array([[ 3000,    0., 1500],
        #                             [    0., 2000, 2100],
        #                             [    0.,    0.,           1.]])
        
        # Prepare data for calibration 
        self.prepare_data_for_calibration_with_opencv()

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
        
        print("retval:\n", retval)
        print("cameraMatrix:\n", cameraMatrix)
        print("distCoeffs:\n", distCoeffs)
        print("rvecs:\n", rvecs)
        print("tvecs:\n", tvecs)
        print("stdDeviationsIntrinsics:\n", stdDeviationsIntrinsics)
        print("stdDeviationsExtrinsics:\n", stdDeviationsExtrinsics)
        print("perViewErrors:\n", perViewErrors)
        
        # Store image specific results 
        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]):
            # Get image name
            img_name = Path(calibration_image_dir).absolute().name
            # Store image specific results - rotatation vector
            self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"] = rvecs[index]

            ### Playing arroud still ################################################################################################################
            file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\rvec.npy"
            np.save(file_path, rvecs[index])
            #########################################################################################################################################

            # Store image specific results - translation vector
            self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"] = tvecs[index]

            ### Playing arroud still ################################################################################################################
            file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\tvec.npy"
            np.save(file_path, tvecs[index])
            #########################################################################################################################################

            # Store image specific results - per view errors
            self.calibration_data["image_specific_data"][img_name]["opencv_result_perViewError"] = perViewErrors[index]

        # Store overall results - overall error of 3D corners reprojection in 2D image 
        self.calibration_data["overall_analysis_data"]["opencv_result_retval"] = retval
        # Store overall results - camera matrix
        self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"] = cameraMatrix

        # ### Playing arroud still ################################################################################################################
        # file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\cameraMatrix.txt"
        # np.savetxt(file_path, cameraMatrix)
        # #########################################################################################################################################

        ### Playing arroud still ################################################################################################################
        file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\cameraMatrix.npy"
        np.save(file_path, cameraMatrix)
        #########################################################################################################################################
        
        # Store overall results - distortion coefficients  
        self.calibration_data["overall_analysis_data"]["opencv_result_dist_coeff"] = distCoeffs

        ### Playing arroud still ################################################################################################################
        file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\distCoeffs.npy"
        np.save(file_path, distCoeffs)
        #########################################################################################################################################

        # Store overall results - standard deviations intrinsics - (fx,fy,cx,cy,k1,k2,p1,p2,k3,k4,k5,k6,s1,s2,s3,s4,τx,τy)
        self.calibration_data["overall_analysis_data"]["opencv_result_stdDeviationsIntrinsic"] = stdDeviationsIntrinsics
        # Store overall results - standard deviations extrinsics - (R0,T0,…,RM−1,TM−1) where M is the number of images, Ri,Ti are concatenated 1x3 vectors. 
        self.calibration_data["overall_analysis_data"]["opencv_result_stdDeviationsExtrinsic"] = stdDeviationsExtrinsics

    ## Calibrate camera with alternative distortion model - yields the parameters of the distortion model  ######################################
    #############################################################################################################################################
    def calibrate_with_alternative_distortion_model(self) -> None:
        if not self.calibration_data["overall_analysis_data"]["opencv_result_retval"]:
            self.calibrate_with_opencv()

        # Initiate temporary array for stat analysis 
        num_images = self.calibration_data["overall_analysis_data"]["num_images"]
        temp_array_dist_coeffs = np.zeros((num_images, 20), dtype=np.float32)
        temp_array_errors = np.zeros(num_images, dtype=np.float32)
  
        # Optimize the estimation of the distortion parameters  
        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]): 

            # Get image name and require data 
            img_name = Path(calibration_image_dir).absolute().name
            image_points = self.calibration_data["overall_analysis_data"]["all_image_points"][index]
            object_points = self.calibration_data["overall_analysis_data"]["all_object_points"][index]
            rvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"]
            tvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"]
            rotation_matrix, _ = cv2.Rodrigues(rvec)
            extrinsic_matrix = np.hstack((rotation_matrix, tvec))

            ### Playing arroud still ################################################################################################################
            file_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\extrinsic_matrix_config1_img0.txt" ## TODO: add customisation to the path of the file - having name of the image corresponding to the rotation 
            np.savetxt(file_path, extrinsic_matrix)
            #########################################################################################################################################

            # Carry custom calibration 
            DISTORTION_COEFFS = np.zeros(20)
            OPENCV_CAMERA_MATRIX = self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"]
            optimised_distortion_coefficients, error_map, over_all_error = calibrator_utils.custom_calibration(object_points=[object_points], 
                                                extrinsic_matrix=extrinsic_matrix, 
                                                cameraMatrix=OPENCV_CAMERA_MATRIX, 
                                                image_points=[image_points], 
                                                distortion_coefficients = DISTORTION_COEFFS)
            
            print(over_all_error)
            
            # Store results - dist coefficiants per image 
            self.calibration_data["image_specific_data"][img_name]["custom_optimisation_per_image_dist_coeff"] = optimised_distortion_coefficients
            # Store results - error per image 
            self.calibration_data["image_specific_data"][img_name]["custom_optimisation_perViewError"] = over_all_error
            # Store results - dist coefficiants and errors for stat analysis 
            temp_array_dist_coeffs[index,:] = optimised_distortion_coefficients
            temp_array_errors[index] = over_all_error

        # Store results - stat analysis
        self.calibration_data["overall_analysis_data"]["custom_optimisation_glob_result_dist_coeff"] = np.mean(a=temp_array_dist_coeffs, axis=0, dtype=np.float32)
        self.calibration_data["overall_analysis_data"]["custom_optimisation_retval"] = np.mean(a=temp_array_errors, axis=0, dtype=np.float32)
        self.calibration_data["overall_analysis_data"]["custom_optimisation_glob_result_stdDeviations_dist_coeff"] = np.std(a=temp_array_dist_coeffs, axis=0, dtype=np.float32)

#############################################################################################################################################
## RUNTIME ##################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__":
    # few tests of the process 
    calibrator = Calibrator()

    # test of calibration 
    calibrator.calibrate_with_opencv()

    # test of alternative model
    calibrator.calibrate_with_alternative_distortion_model()

    # # test on the distorsion function

    # # get the objects and image points 
    # object_points_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\cloud_of_3d_points_dict_filtered.json" 
    # image_points_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\coords_2d_projections_dict.json"
    # object_points = calibrator_utils.load_data_from_jsons(object_points_path)
    # image_points = calibrator_utils.load_data_from_jsons(image_points_path)
    # # # # print("object_points:\n", object_points)
    # # # # print("image_points:\n", image_points)
    # object_points_formatted, image_points_formatted = calibrator_utils.temporary_format_obj_and_img_points(object_points, image_points)
    # # # # print("object_points_formatted:\n", object_points_formatted)
    # # # # print("image_points_formatted:\n", image_points_formatted)
    
    # # # # get the matrixes 
    # # # # camera matrix
    # # cameraMatrix = np.loadtxt(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\cameraMatrix.txt")
    # # # # print(cameraMatrix) 
    # # # # excentric matrixes 
    # # extrinsic_matrix = np.loadtxt(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\extrinsic_matrix_config1_img0.txt")
    # # # # print(extrinsic_matrix) 

    # # # # actual test 
    # # error_map, custom_retval = calibrator_utils.small_test_on_distorsion_function(object_points_formatted, extrinsic_matrix, cameraMatrix, image_points_formatted)
    # # print(error_map)


    # # # results_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\results_with_img1_and_mean_value_for_dist_coeff.npy"
    # # # np.save(results_path, error_map)

    # # results_path = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\results_with_img1_and_img_1_value_for_dist_coeff.npy"
    # # np.save(results_path, error_map)

    # # calibrator_utils.plot_error_maps(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4")

    # rvec = np.load(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\rvec.npy", allow_pickle=True)
    # tvec = np.load(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\tvec.npy", allow_pickle=True)
    # distCoeffs =  np.load(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\distCoeffs.npy", allow_pickle=True)
    # cameraMatrix = np.load(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\tests_with_opencv\cameraMatrix.npy", allow_pickle=True)

    # computed_image_points_opencv, _ = cv2.projectPoints(objectPoints=np.array(object_points_formatted), rvec=rvec, tvec=tvec, cameraMatrix=cameraMatrix, distCoeffs=distCoeffs)
    # print("computed_image_points_opencv:\n", computed_image_points_opencv)
    # print("type computed_image_points_opencv:\n", type(computed_image_points_opencv))
    # print("image_points_formatted:\n", np.array(image_points_formatted))

    # print(np.array(image_points_formatted).shape)
    # print(computed_image_points_opencv.shape)

    # print(np.array(image_points_formatted))
    # print(computed_image_points_opencv)

    # reshaped_computed_image_points_opencv = computed_image_points_opencv.reshape(np.array(image_points_formatted).shape)
    # # print(reshaped_computed_image_points_opencv)

    # error_opencv = np.array(image_points_formatted) - reshaped_computed_image_points_opencv
    # # print(error_opencv)

    # results_path_opencv = r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\results_opencv.npy"
    # np.save(results_path_opencv, error_opencv)

    # data =  np.load(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4\results_opencv.npy", allow_pickle=True)
    # print(data)

    calibrator_utils.plot_error_maps(r"C:\Users\hilar\Documents\2023_06_06_Calibration_tests\results_analysis\rp4")
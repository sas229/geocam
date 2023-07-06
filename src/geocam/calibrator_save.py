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
            optimized_distortion_coefficients, error = self.custom_calibration(object_points=object_points, 
                                                extrinsic_matrix=extrinsic_matrix, 
                                                cameraMatrix=OPENCV_CAMERA_MATRIX, 
                                                image_points=image_points, 
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
    
        # arguments for the reprojection_error_minization_per_img function 
        args = object_points, extrinsic_matrix, cameraMatrix, image_points

        # Define options
        options = {
            'maxiter': 1000,            # Maximum number of iterations
            'disp': True               # Display optimization information
        }

        # optimize calling the minimize function
        result = minimize(fun = self.reprojection_error_minization_per_img, x0 = distortion_coefficients, args = args, method='Powell', options=options)#, constraints=constraints)
        if result.success:
            error = self.reprojection_error(result.x, object_points, extrinsic_matrix, cameraMatrix, image_points)
            return result.x, error
        
    def reprojection_error_minization_per_img(self, distortion_coefficients, *args):

        object_points, extrinsic_matrix, cameraMatrix, image_points = args 

        # get the image points resulting from the mapping to the scaled and skewed sensor coordinates by the affine transformation
        computed_image_points = self.projection_on_sensor(object_points = object_points, 
                                                    extrinsic_matrix = extrinsic_matrix, 
                                                    cameraMatrix = cameraMatrix,
                                                    distortion_coefficients = distortion_coefficients)

        # compute the overall RMS 
        custom_retval_per_image = np.linalg.norm(image_points - computed_image_points) / len(computed_image_points)

        return custom_retval_per_image
    
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
        
        # object_points_column = np.column_stack(object_points)
        object_points_column_hom = np.hstack((object_points, np.ones((object_points.shape[0],1))))

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

## Trying something new 2 ################################################################################################

    def _enhance_distorsion_handling_and_stat_analysis_of_results2(self):

        # Initiate temporary array for stat analysis 
        num_images = self.calibration_data["overall_analysis_data"]["num_images"]
  
        # Optimize the estimation of the distorsion parameters  
        optimized_distortion_coefficients, custom_overall_retval, per_image_error = self.custom_calibration2()
        print("optimized_distortion_coefficients\n", optimized_distortion_coefficients)
        print("custom_overall_retval\n", custom_overall_retval)
        print("per_image_error\n", per_image_error)
    
    def custom_calibration2(self):
        
        # Constants
        DISTORTION_COEFFS = np.zeros(20)

        # Define options
        options = {
            'maxiter': 1000,            # Maximum number of iterations
            'disp': True               # Display optimization information
        }

        # optimize calling the minimize function
        result = minimize(fun = self.overall_error, x0 = DISTORTION_COEFFS, method='Powell', options=options)
        if result.success:
            custom_overall_retval, per_image_error = self.call_back_overall_error(result.x)
            return result.x, custom_overall_retval, per_image_error
 
    def overall_error(self, distortion_coefficients):

        # Initiate array to store per image errors
        num_images = self.calibration_data["overall_analysis_data"]["num_images"]
        per_image_error = np.zeros(num_images) 

        # Constants for optimisation 
        OPENCV_CAMERA_MATRIX = self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"]

        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]):
            
            # Get image name and require data 
            img_name = Path(calibration_image_dir).absolute().name
            image_points = self.calibration_data["overall_analysis_data"]["all_image_points"][index]
            object_points = self.calibration_data["overall_analysis_data"]["all_object_points"][index]
            rvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"]
            tvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"]
            rotation_matrix, _ = cv2.Rodrigues(rvec)
            extrinsic_matrix = np.hstack((rotation_matrix, tvec))

            # get error for this image 
            custom_retval_per_image = self.reprojection_error_minization_per_img(distortion_coefficients, object_points, extrinsic_matrix, OPENCV_CAMERA_MATRIX, image_points)

            # store it 
            per_image_error[index] = custom_retval_per_image

        custom_overall_retval = np.sum(per_image_error) / num_images

        return custom_overall_retval
    
    def call_back_overall_error(self, distortion_coefficients):

        # Initiate array to store per image errors
        num_images = self.calibration_data["overall_analysis_data"]["num_images"]
        per_image_error = np.zeros(num_images)

        # Constants for optimisation 
        OPENCV_CAMERA_MATRIX = self.calibration_data["overall_analysis_data"]["opencv_result_camera_matrix"]

        for index, calibration_image_dir in enumerate(self.calibration_data["overall_analysis_data"]["calibration_images_directories"]):
            
            # Get image name and require data 
            img_name = Path(calibration_image_dir).absolute().name
            image_points = self.calibration_data["overall_analysis_data"]["all_image_points"][index]
            object_points = self.calibration_data["overall_analysis_data"]["all_object_points"][index]
            rvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_rvec"]
            tvec = self.calibration_data["image_specific_data"][img_name]["opencv_result_tvec"]
            rotation_matrix, _ = cv2.Rodrigues(rvec)
            extrinsic_matrix = np.hstack((rotation_matrix, tvec))

            # get error for this image 
            custom_retval_per_image = self.reprojection_error_minization_per_img(distortion_coefficients, object_points, extrinsic_matrix, OPENCV_CAMERA_MATRIX, image_points)

            # store it 
            per_image_error[index] = custom_retval_per_image

        custom_overall_retval = np.sum(per_image_error) / num_images

        return custom_overall_retval, per_image_error
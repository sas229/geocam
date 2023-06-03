import cv2 
import time

def get_first_guess_of_camera_matrix_and_dist(images_directories):

    all_charuco_corners = []
    all_charuco_ids = []

    for image_dir in images_directories:
        retval, charuco_corners, charuco_ids, charuco_board, image_size = get_scatter_of_2D_points_projection(image_dir)
        print("retval in the init function", retval)
        all_charuco_corners.append(charuco_corners)
        all_charuco_ids.append(charuco_ids)

    cameraMatrixInit = np.array([[ 1000.,    0., image_size[0]/2.],
                                 [    0., 1000., image_size[1]/2.],
                                 [    0.,    0.,           1.]])

    distCoeffsInit = np.zeros((5,1))
    flags = (cv2.CALIB_USE_INTRINSIC_GUESS + cv2.CALIB_RATIONAL_MODEL + cv2.CALIB_FIX_ASPECT_RATIO)
    #flags = (cv2.CALIB_RATIONAL_MODEL)
    (ret, camera_matrix, distortion_coefficients0,
     rotation_vectors, translation_vectors,
     stdDeviationsIntrinsics, stdDeviationsExtrinsics,
     perViewErrors) = cv2.aruco.calibrateCameraCharucoExtended(
                      charucoCorners=all_charuco_corners,
                      charucoIds=all_charuco_ids,
                      board=charuco_board,
                      imageSize=image_size,
                      cameraMatrix=cameraMatrixInit,
                      distCoeffs=distCoeffsInit,
                      flags=flags,
                      criteria=(cv2.TERM_CRITERIA_EPS & cv2.TERM_CRITERIA_COUNT, 10000, 1e-9))

    return camera_matrix, distortion_coefficients0

if __name__ == "__main__":
    directory = r"C:\Users\hilar\Documents\project\geocam\src\images\calibration_img_example.jpg"
    start_time = time.time()
    retval, charuco_corners, charuco_ids, charuco_board, image_size = get_scatter_of_2D_points_projection(input_image_dir = directory, flag2=True)
    ret, camera_matrix, distortion_coefficients0, rotation_vectors, translation_vectors = calibrate_camera(charuco_corners, charuco_ids, charuco_board, image_size)
    end_time = time.time()
    delta_t = end_time - start_time
    print("ret", ret)
    print("camera_matrix_finale", camera_matrix)
    print("Time to calibrate:", delta_t)
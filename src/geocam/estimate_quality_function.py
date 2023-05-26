# import glob
import cv2
import numpy as np
import matplotlib.pyplot as plt

from cv2 import aruco  
from pathlib import Path  

#############################################################################################################################################
## BUILDING THE FUNCTIONS ###################################################################################################################
#############################################################################################################################################

def add_quality_index_text(input_image, index_text, flag1:bool = True) -> np.ndarray:

    _, image_width = input_image.shape[:2]

    rectangle_width = int(image_width * 0.3)
    rectangle_height = int(3/6*rectangle_width)

    x = image_width - rectangle_width  # Calculate the x-coordinate of the top-left corner of the rectangle
    y = 0                              # Set the y-coordinate of the top-left corner of the rectangle

    cv2.rectangle(input_image, (x, y), (x + rectangle_width, y + rectangle_height), (0, 0, 0), -1)

    fontScale = 1.5
    thickness = 7

    # dealing with the text
    lines = index_text.split('\n')
    # print(lines)
    set_line_height = int(rectangle_height/3) # Set the line height to the text height plus some additional spacing
    # print(set_line_height)
    y_offset = int(set_line_height*0.7) # Set the initial y-coordinate for the first line

    for line in lines:
        # print(line)
        # print("y_offset before updated", y_offset)
        # Calculate the size of the current line
        (line_width, _) = cv2.getTextSize(line, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=thickness)[0]
        # print(line_width, _)
        # Calculate the x-coordinate for centering the current line
        x_offset = x + (rectangle_width - line_width) // 2
        # print(x_offset)
        # Draw the current line
        cv2.putText(img=input_image, text=line, org=(x_offset, y_offset), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, color=(255, 0, 0), thickness=thickness)
        # Update the y-coordinate for the next line
        y_offset += set_line_height
        # print("y_offset after updated", y_offset)


    # - display option 2 with plt 
    if flag1:
        figure = plt.figure('Detected Charuco Corners')
        plt.imshow(input_image)
        plt.title('Charuco Corners')
        plt.xticks([])
        plt.yticks([])
        plt.show()

    return input_image

def estimate_image_quality(input_image_dir, flag1:bool = False, flag2:bool = True) -> np.ndarray:

    # create the board, aruco_dict could become a paramter if a different dictionnary is used
    
    aruco_dict = aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
    horizontal_number_of_squares = 44
    vertical_number_of_squares = 28
    charuco_board = aruco.CharucoBoard_create(horizontal_number_of_squares, vertical_number_of_squares, 5/3, 1, aruco_dict)

    # save the charuco board (optional)
    if flag1:
        directory = Path(__file__).absolute()
        image = np.ones((2100, 3300), dtype=np.uint8) * 255
        imgboard = charuco_board.draw((3300, 2100), image)
        cv2.imwrite(str(directory.parent / "charuco_board.jpg"), imgboard)

    # compute the ma number of detectable charuco corners 
    max_num_of_detectable_charuco_corners = (horizontal_number_of_squares - 1) * (vertical_number_of_squares - 1) 

    # image to be processed 
    input_image = cv2.imread(input_image_dir)

    # process: detect aruco and charuco corners 
    image_in_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    params = aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(image_in_gray, aruco_dict, parameters = params)
    if len(corners) > 0:
        retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, image_in_gray, charuco_board)
    num_detected_corners = len(charuco_corners)
    quality_index = round(num_detected_corners / max_num_of_detectable_charuco_corners, 3)
    index_text = f"DETECTED CORNERS :: {num_detected_corners} \nMAX NUM OF CORNERS :: {max_num_of_detectable_charuco_corners} \nQUALITY INDEX :: {quality_index}"
    
    # post process: draw croners and ass the quality index text
    if retval:
        aruco.drawDetectedCornersCharuco(input_image, charuco_corners, charuco_ids)
    input_image = add_quality_index_text(input_image, index_text)
    
    # optionnal save
    if flag2:
        directory_path = Path(input_image_dir).absolute()
        parent_folder = directory_path.parent
        file_name = directory_path.name
        new_name = file_name.rsplit(".", 1)[0] + "_processed.jpg"
        cv2.imwrite(str(parent_folder / new_name), input_image)

    return input_image

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__":

    image1 = r"..\images\charuco_board.jpg"
    image2 = r"..\images\curved.jpg"
    image3 = r"..\images\relatively_flat.jpg"
    
    estimate_image_quality(image1)


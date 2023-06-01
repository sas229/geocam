# Mostly copied from https://picamera.readthedocs.io/en/release-1.13/recipes2.html
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

import io
import logging
import socketserver
import threading
import time 
import cv2
import queue
import numpy as np

from cv2 import aruco 
from http import server
from threading import Condition
from geocam.utils import get_host_ip

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

logging.basicConfig(level=logging.DEBUG)
logging.debug("done with imports")
## Streaming  ###############################################################################################################################
############################################################################################################################################# 

# PAGE = """\
# <html>
# <head>
# <title>picamera2 MJPEG streaming for focus</title>
# </head>
# <body>
# <center><h1>Picamera2 MJPEG Streaming for focus</h1></center>
# <center><img src="stream.mjpg" width="640" height="480" /></center>
# </body>
# </html>
# """

PAGE = """\
<html>
<head>
    <title>picamera2 MJPEG streaming for focus</title>
</head>
<body>
    <center>
        <h1>Picamera2 MJPEG Streaming for focus</h1>
    </center>
    <div style="display: flex;">
        <div style="flex: 1;">
            <h2>Original Frames</h2>
            <img src="stream_original.mjpg" width="640" height="480" />
        </div>
        <div style="flex: 1;">
            <h2>Processed Frames</h2>
            <img src="stream_processed.mjpg" width="640" height="480" />
        </div>
    </div>
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Create two separate queues for original and processed frames
original_queue = queue.Queue()
processed_queue = queue.Queue()


# Function to process the frame
def process_frame():
    relative_time = 0
    logging.debug("3. in process frame")
    frequency = 0.2
    last_process_time = time.time()
    max_num_of_detected_charuco_corners = 1
    while True:
        if not original_queue.empty():
            frame = original_queue.get()  # Retrieve a frame from the original queue
            current_time = time.time()
            delta_t = current_time - last_process_time
            relative_time += delta_t
            if delta_t >= frequency:
                last_process_time = current_time
                logging.debug("RELATIVE TIME IS: %s", relative_time)
                logging.debug("5. in process frame")
                frame = original_queue.get()  # Retrieve a frame from the original queue
                logging.debug("6. original frame will be processed")
                # Perform frame processing (e.g., convert to grayscale)
                decoded_frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR) # Decode the frame
                # processed_frame = cv2.cvtColor(decoded_frame, cv2.COLOR_BGR2GRAY)
                processed_frame, new_num_of_detected_charuco_corners = estimate_image_quality(decoded_frame, round(relative_time, 2), max_num_of_detected_charuco_corners)
                max_num_of_detected_charuco_corners = new_num_of_detected_charuco_corners
                _, processed_frame_encoded = cv2.imencode('.jpg', processed_frame) # Encode the processed frame
                processed_queue.put(processed_frame_encoded.tobytes())  # Put the processed frame into the processed queue
                logging.debug("7. original was processed")

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream_original.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                    # logging.debug("1. original frame received")
                original_queue.put(frame)
                # logging.debug("2. original frame received queued")
                self.wfile.write(b'--FRAME\r\n')
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(frame))
                self.end_headers()
                self.wfile.write(frame)
                self.wfile.write(b'\r\n')      
        elif self.path == '/stream_processed.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            while True:
                if not processed_queue.empty():
                    processed_frame = processed_queue.get()  # Retrieve the processed frame from the processed queue
                    logging.debug("3. processed frame was be retreived")
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(processed_frame))
                    self.end_headers()
                    self.wfile.write(processed_frame)
                    self.wfile.write(b'\r\n')
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

#############################################################################################################################################
## PROCESS DATA FUNCTIONS ###################################################################################################################
#############################################################################################################################################


def add_quality_index_text(frame, index_text) -> np.ndarray:

    _, image_width = frame.shape[:2]

    rectangle_width = int(image_width * 0.6)
    rectangle_height = int(3/12 *rectangle_width)

    x = image_width - rectangle_width  # Calculate the x-coordinate of the top-left corner of the rectangle
    y = 0                              # Set the y-coordinate of the top-left corner of the rectangle

    cv2.rectangle(frame, (x, y), (x + rectangle_width, y + rectangle_height), (0, 0, 0), -1)

    thickness = int(10/3000 * image_width)
    fontScale = 3/14 * thickness

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
        cv2.putText(img=frame, text=line, org=(x_offset, y_offset), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, color=(255, 0, 0), thickness=thickness)
        # Update the y-coordinate for the next line
        y_offset += set_line_height
        # print("y_offset after updated", y_offset)

    return frame

def estimate_image_quality(frame, current_time, previous_max_num_of_detected_charuco_corners:int = 1) -> np.ndarray:
    # initiated to false
    index_text = f"PLEASE CHANGE THE FOCUS \nNO CORNER WERE FOUND \nPLEASE CHANGE THE FOCUS"

    # initiated to the previous one
    updated_max_num_of_detected_charuco_corners = previous_max_num_of_detected_charuco_corners

    # create the board, aruco_dict could become a paramter if a different dictionnary is used
    aruco_dict = aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
    horizontal_number_of_squares = 44
    vertical_number_of_squares = 28
    charuco_board = aruco.CharucoBoard_create(horizontal_number_of_squares, vertical_number_of_squares, 5/3, 1, aruco_dict)

    # # compute the ma number of detectable charuco corners 
    # max_num_of_detectable_charuco_corners = (horizontal_number_of_squares - 1) * (vertical_number_of_squares - 1) 

    # process: detect aruco and charuco corners 
    image_in_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    params = aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(image_in_gray, aruco_dict, parameters = params)

    if corners:
        logging.info("ARUCOS FOUND")

        # look for charuco corners 
        retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, image_in_gray, charuco_board)

        if retval:
            logging.info("CORNER INTERPOLATION SUCCESSFUL")
            num_detected_corners = len(charuco_corners)
            
            if num_detected_corners > previous_max_num_of_detected_charuco_corners:
                updated_max_num_of_detected_charuco_corners = num_detected_corners
            
            quality_index = round(num_detected_corners / updated_max_num_of_detected_charuco_corners, 2)
            index_text = f"TIME :: {current_time} \nDETECTED\HISTORICAL_MAX :: {num_detected_corners}\\{updated_max_num_of_detected_charuco_corners} \nQUALITY INDEX :: {quality_index}"
            
            # post process: draw corners 
            aruco.drawDetectedCornersCharuco(image_in_gray, charuco_corners, charuco_ids)

    
    # add the quality index text
    processed_gray_image = add_quality_index_text(image_in_gray, index_text)

    return processed_gray_image, updated_max_num_of_detected_charuco_corners

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__":

    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    logging.debug("1. just after starting")

    try:
        # Start the frame processing thread
        logging.debug("2. just before processing_thread")
        processing_thread = threading.Thread(target=process_frame)
        processing_thread.daemon = True
        processing_thread.start()
        logging.debug("4. processing_thread should have started")

        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)

        # Start the server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print(f"streaming at http://{get_host_ip()}:8000/")

        # Wait for a keyboard interrupt to stop the server
        print("Press Ctrl+C to stop the server.")
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    except Exception as e:
        logging.warning('Server error: %s', str(e))

    finally:
        logging.debug("just before closing")
        picam2.stop_recording()
        # Stop the frame processing thread and gracefully shutdown the server
        processing_thread.join()
        server.shutdown()
        server.server_close()


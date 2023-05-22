import io
import logging
import time 
import queue
import struct
import threading
from geocam.communicator import Communicator
from PIL import Image
from picamera2 import Picamera2

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler(f'{__file__[:-3]}.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

# Create a queue to store the image buffers
image_queue = queue.Queue()
max_queue_size = 10

# Step 1: Define the stop flag
stop_thread = False

leader_ip_addr = '172.20.10.2'
def send_images():
    collaborator = Communicator(Communicator.COLLABORATOR)
    time.sleep(5)
    logger.info("sleeping*****")
    while True: 
        with collaborator.set_socket() as sock_tcp:
            if not image_queue.empty():
                data = image_queue.get()  # Retrieve buffer from image_queue
                image_size = data.getbuffer().nbytes
                collaborator.send(struct.pack('!I', image_size), sock_tcp=sock_tcp, target_ip=leader_ip_addr)
                collaborator.send(data.getvalue())
            if stop_thread:
                break

class GeoPicamera(Picamera2):

    def __init__(self):
        super().__init__()
        logger.debug(self.__str__())

    def start_capture_and_send_images(self, name: str = "image{:03d}.jpg", initial_delay=1, num_files=1, delay=1, show_preview=False):
        data = io.BytesIO()

        # the two following will be useful for more detailed configuration 
        preview_config = self.create_preview_configuration()
        capture_config = self.create_still_configuration()

        if self.started:
            self.stop()

        if delay:
            # Show a preview between captures, so we will switch mode and back for each capture.
            self.configure(preview_config)
            self.start(show_preview=show_preview)
            
            for i in range(num_files):
                time.sleep(initial_delay if i == 0 else delay)
                # self.switch_mode_and_capture_file(capture_mode, name.format(i))
                self.switch_mode_and_capture_file(capture_config, data, format='jpeg')
                image_queue.put(data)
                if image_queue.qsize() >= max_queue_size:
                    break

        else:
            # No preview between captures, it's more efficient just to stay in capture mode.
            if initial_delay:
                self.configure(preview_config)
                self.start(show_preview=show_preview)
                time.sleep(initial_delay)
                self.switch_mode(capture_config)
                
            else:
                self.configure(capture_config)
                self.start(show_preview=show_preview)

            for i in range(num_files):
                self.capture_file(data, format='jpeg')
                image_queue.put(data)
                if i == num_files - 1 or image_queue.qsize >= max_queue_size:
                    break
                time.sleep(delay)
        self.stop()


if __name__ == '__main__':

    sending_thread = threading.Thread(target=send_images)
    sending_thread.daemon = True
    sending_thread.start()

    camera = GeoPicamera()
    camera.start_capture_and_send_images(initial_delay=0, delay=1, num_files=2)

    stop_thread = True
    sending_thread.join()

    
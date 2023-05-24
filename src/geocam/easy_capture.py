import io
import logging
import time 
import queue
import struct
import threading
import socket 

from PIL import Image
from picamera2 import Picamera2

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(thread)d:%(message)s')

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
data_queue = queue.Queue()
max_queue_size = 10

# Create a lock for data 
data_lock = threading.Lock()

# Step 1: Define the stop flag
stop_thread = False

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('172.20.10.2', 1645)
sock.connect(server_address)

def send_images():
    global data_queue
    global stop_thread
    global sock
    
    logger.info("THIS IS THE VALUE OF STOP THREAD %s", stop_thread)
    while True: 
        if not data_queue.empty():
            logger.info("QUEUE")
            logger.info("%s ELEMENTS ARE QUEUED IN THE QUEUE", data_queue.qsize())
            data = data_queue.get()  # Retrieve buffer from data_queue
            logger.info("%s ELEMENTS ARE QUEUED IN THE QUEUE AFTER GET", data_queue.qsize())
            logger.info("CHECK1")
            image_size = data.getbuffer().nbytes
            logger.info("image_size %s", image_size)
            logger.info("CHECK2")
            logger.info("THIS IS THE SIZE OF THE DATA %s", len(struct.pack('!I', image_size)))
            logger.info("SENDALL RETURNS %s", sock.sendall(struct.pack('!I', image_size)))
            logger.info("CHECK3")
            sock.sendall(data.getvalue())
            logger.info("CHECK4")
            # Close the data_copy object to release resources
            data.close()
            logger.info("THIS IS THE VALUE OF STOP THREAD NOW %s", stop_thread)
        if stop_thread:
            logger.info("BREAK")
            break

class GeoPicamera(Picamera2):

    def __init__(self):
        super().__init__()
        logger.debug(self.__str__())

    def start_capture_and_send_images(self, initial_delay=1, num_files=2, delay=5, show_preview=False):
        global data_queue
        global data_lock

        # the two following will be useful for more detailed configuration 
        preview_config = self.create_preview_configuration()
        capture_config = self.create_still_configuration()

        if self.started:
            self.stop()

        data_buffer = io.BytesIO()
        
        logger.info("initial_delay %s", initial_delay)
        logger.info("num_files %s", num_files)
        logger.info("delay %s", delay)


        if delay:
            # Show a preview between captures, so we will switch mode and back for each capture.
            self.configure(preview_config)
            self.start(show_preview=show_preview)
            target_delay = delay
            
            for i in range(num_files):
                time.sleep(initial_delay if i == 0 else delay)
                # Reset data_buffer
                data_buffer.seek(0)
                data_buffer.truncate()
                
                with data_lock:
                    current_time = time.time()
                    self.switch_mode_and_capture_file(capture_config, data_buffer, format='jpeg')
                    data_copy = io.BytesIO(data_buffer.getvalue())
                    data_queue.put(data_copy)
                
                delay_elapsed = time.time() - current_time
                delay = max(0, target_delay - delay_elapsed)
                logger.info("Time delay due to the lock %s", delay_elapsed)
                logger.info("Updated delay that takes it in account %s", delay)
                effective_delay = delay + delay_elapsed
                logger.info("Effective delay after correction %s", effective_delay)

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
                # Reset data_buffer
                data_buffer.seek(0)
                data_buffer.truncate()

                with data_lock:
                    self.capture_file(data_buffer, format='jpeg')
                    data_copy = io.BytesIO(data_buffer.getvalue())
                    data_queue.put(data_copy)
                
                if i == num_files - 1:
                    break
                time.sleep(delay)

                logger.info("Time between captures %s", dela_t)

            # Release the data buffer
            data_buffer.close()

            logger.info("the queue is not empty %s", not data_queue.empty())
            logger.info("OUT OF LOCK")

        self.stop()


if __name__ == '__main__':

    sending_thread = threading.Thread(target=send_images)
    sending_thread.daemon = True
    sending_thread.start()

    camera = GeoPicamera()
    camera_thread = threading.Thread(target=camera.start_capture_and_send_images, kwargs={'initial_delay': 5, 'delay': 10, 'num_files': 3})
    camera_thread.daemon = True
    camera_thread.start()

    camera_thread.join()
    stop_thread = True
    sending_thread.join()
    sock.close()

    
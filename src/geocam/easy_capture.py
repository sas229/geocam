import io
import logging
import time 
from PIL import Image
from picamera2 import Picamera2

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler(f'{__file__[:-3]}.log', mode='w')
# file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

# picam2 = Picamera2()
# capture_config = picam2.create_still_configuration()
# picam2.configure(picam2.create_preview_configuration())
# picam2.start()

# time.sleep(1)
# data = io.BytesIO()
# picam2.switch_mode_and_capture_file(capture_config, data, format='jpeg')
# print(data.getbuffer().nbytes)

# image = Image.open(data)
# image.save("./image.jpg")
# image.close()

class GeoPicamera(Picamera2):

    def __init__(self):
        super().__init__()
        logger.debug(self.__str__())

    def start_capture_and_send_images(self, name: str = "image{:03d}.jpg", initial_delay=1, preview_mode="preview", capture_mode="still", num_files=1, delay=1, show_preview=False):
        
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
                with Image.open(data) as image:
                    image.save(name.format(i))

        else:
            # No preview between captures, it's more efficient just to stay in capture mode.
            if initial_delay:
                self.configure(preview_config)
                self.start(show_preview=show_preview)
                time.sleep(initial_delay)
                # self.switch_mode(capture_config['usage_mode'])
                self.switch_mode(capture_config)

                # self.configure(self.create_preview_configuration())
                # self.start()
                # time.sleep(initial_delay)
                # self.switch_mode(capture_mode)

            else:
                self.configure(capture_config)
                self.start(show_preview=show_preview)

                # self.configure(self.create_preview_configuration())
                # self.start()

            for i in range(num_files):
                # self.capture_file(name.format(i))
                self.capture_file(data, format='jpeg')
                with Image.open(data) as image:
                    image.save(name.format(i))
                if i == num_files - 1:
                    break
                time.sleep(delay)
        self.stop()


if __name__ == '__main__':
    camera = GeoPicamera()
    camera.start_capture_and_send_images(initial_delay=0, delay=0, num_files=1)
    
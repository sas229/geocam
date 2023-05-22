#!/usr/bin/python3

import io
import time
from PIL import Image
import matplotlib.pyplot as plt

from picamera2 import Picamera2

picam2 = Picamera2()
capture_config = picam2.create_still_configuration()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

# # time.sleep(1)
# # data = io.BytesIO()
# # picam2.capture_file(data, format='jpeg')
# # print(data.getbuffer().nbytes)

time.sleep(1)
data = io.BytesIO()
picam2.switch_mode_and_capture_file(capture_config, data, format='jpeg')
print(data.getbuffer().nbytes)

image = Image.open(data)
image.save("./image.jpg")
plt.imshow(image)
plt.show()
image.close()
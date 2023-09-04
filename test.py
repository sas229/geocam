import geocam as gc

network = "192.168.0.0/24"
id = "rp"
controller = gc.controller.Controller(configuration='rp.json', password="rp")
# controller = gc.controller.Controller()
# controller.reboot_cameras()
# controller.restart_cameras()
# controller.find_cameras(id=id, password="rp")
# controller.save_configuration()
# controller.capture_images()
controller.preview_status = True
controller.preview_camera = "rp3"
controller._get_preview_image()
del controller

# from PIL import Image
# import io

# image = Image.open("test.jpg")
# byte_stream = io.BytesIO()
# image.save(byte_stream, format="JPEG")
# new_image = Image.open(byte_stream)
# new_image.save("test2.jpg")
# byte_stream.close()

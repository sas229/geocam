import geocam as gc

network = "192.168.0.0/24"
id = "rp"
# controller = gc.controller.Controller(configuration='rp.json', yes)
controller = gc.controller.Controller()
# controller.reboot_cameras()
# controller.restart_cameras()
controller.find_cameras(id=id, password="rp")
controller.save_configuration()
controller.capture_images()
del controller
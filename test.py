import geocam as gc

network = "192.168.0.0/24"
id = "rp"
controller = gc.controller.Controller()
# controller.restart_cameras()
controller.find_cameras(id=id, password="rp")
controller.save_configuration()
del controller
import geocam as gc

network = "192.168.0.0/24"
id = "rp"
controller = gc.controller.Controller()
controller.find_cameras(id=id, network=network)
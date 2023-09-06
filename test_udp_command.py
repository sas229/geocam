import socket
import json

sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
command = {"command": "previewOff"}
sendsock.sendto(bytes(json.dumps(command), "utf-8"), ("localhost", 3179))
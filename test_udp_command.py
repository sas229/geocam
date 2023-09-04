import socket
import json

command = {"command": "get_preview"}
sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sendsock.sendto(bytes(json.dumps(command), "utf-8"), ("192.168.0.121", 3179))

import socket
import json

sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
command = {"command": "captureFrame"}
sendsock.sendto(bytes(json.dumps(command), "utf-8"), ("192.168.161.232", 3179))
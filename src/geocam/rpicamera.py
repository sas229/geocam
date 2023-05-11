"""
:Name: rpicamera
:Description: This module is used on the RPis 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## TODO's ###################################################################################################################################
#############################################################################################################################################
""" 
1. Add some asserts 
2. Code the loggings 
"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

import json
import os 
import platform
import socket
import time 
from picamera2 import Picamera2

from geocam.communicator import *
from geocam.utils import *


#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

class RPicamera(): 

    def __init__(self) -> None: 
        print("Created a RPicamera instance.")
        # instanciate an Agent and a Collaborator
        self.agent = Communicator(Communicator.AGENT)
        self.collaborator = Communicator(Communicator.COLLABORATOR)
        self.id_info = {"host_name":get_host_name(), "ip_addr":get_host_ip(), "mac_addr":get_mac_address()}

    def stand_by_for_request(self, timeout:int = 10) -> None: # long run no timeout - used for dev 

        ## first: set a socket listening for broadcast
        with self.agent.set_socket(timeout, info_set = True) as sock_udp: 
            print("in the block")
            while True:
                try:
                    start_time = time.time()
                    print("trying to listen")
                    data, addr = self.agent.listen(sock_udp = sock_udp, info_listen = True)
                    if data: # this condition is true is data is received 
                        request = read_json(data)
                        with self.collaborator.set_socket(timeout=5) as sock_tcp:
                            self.excecute(request, sock_tcp, addr) # in this case the socket is needed to send a response
                
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                break
    
    def excecute(self, request:dict, socket_tcp:CustomSocket = None, addr:str = None, print_info:bool = True) -> None:
        
        ## first: parse the request
        command = request['command']
        arguments = request['arguments']

        ## second: given the command/arguments, do the correct job 
        # REGISTRATION 
        if command == "registration":
            print(f"{command} job")
            # when receiving this command, a response should only be sent if the machine is a member 
            # this is checked given the argents of the request 
            # check1 os name 
            check1 = os.name == arguments["os_name"]
            # check 2 plateform name 
            check2 = platform.system() == arguments["plateform"]
            # check 3 prefix of hostname 
            check3 = get_host_name().startswith(arguments["prefix"])
            # bundle the checks in a list
            checks = [check1, check2, check3] 
            if all(checks):
                print("I'm a member !")
                type_of_info = command
                content = self.id_info
                message = create_json(type_of_info, content)
                self.collaborator.send(message, sock_tcp=socket_tcp, target_ip=addr[0], info_sent = False)
            else:
                print("I'm not a member !")

        # AQUIRE IMAGES 
        # NOTE: think of the storage of the images  
        if command == "capture_images":
            print(f"{command} job")
            picam2 = Picamera2()
            # picam2.sensor_mode = 2
            host_name = self.id_info["host_name"]
            picam2.start_and_capture_files(f"{host_name}"+"_img{:03d}.jpg", initial_delay = 1, delay = arguments["delay"], num_files = arguments["number_of_images"], show_preview = False) 

        # CALIBRATE
        if command == "calibrate":
            print(f"{command} job")
            pass 

        # CONFIGURE CAMERAS 
        if command == "configure_cameras":
            print(f"{command} job")
            pass 
        
        # REBOOT 
        if command == "reboot":
            print(f"{command} job")
            pass 

        # SHUTDOWN 
        if command == "shutdown":
            print(f"{command} job")
            pass 

        # INITIAL SCANNING 
        if command == "initial_scanning":
            print(f"{command} job")


#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    # TODO: change the network_status function - so it returns info usable to start or not the process
    rpicamera = RPicamera()
    # rpicamera.stand_by_for_request(timeout=10)
    request = read_json(create_json("capture_images", {"delay":1 , "number_of_images":2}))
    rpicamera.excecute(request)

    


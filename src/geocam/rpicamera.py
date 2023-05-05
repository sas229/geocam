"""
:Name: rpicamera
:Description: This module is used on the RPis 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

from geocam import communicator
import json
import os 
import platform
import socket
import time 

#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

class RPicamera(): 

    def __init__(self): 
        print("Created a RPicamera instance.")
        # instanciate a Communicator
        self.communicator = communicator.Communicator(device = "member")
        print("behavior :", self.communicator.behavior)

        # machine infos
        self.name = communicator.get_host_name()
        self.ipaddr = communicator.get_host_ip()
        self.macaddr = communicator.get_mac_address()

        # print("name", self.name)
        # print("ipaddr", self.ipaddr)
        # print("macaddr", self.macaddr)

    def stand_by_for_request(self, timeout:int = 10) -> None: # long run no timeout - used for dev 

        ## first: set a socket listening for broadcast
        with self.communicator.set_socket(timeout, info_set = True) as s: 
            print("in the block")
            while True:
                try:
                    start_time = time.time()
                    print("trying to listen")
                    data, addr = self.communicator.listen(s, info_listen = True)
                    if data: # this condition is true is data is received 
                        request = communicator.read_json(data)
                        self.excecute(request, addr, socket_udp = s) # in this case the socket is needed to send a response
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                break
    
    def excecute(self, request:dict, addr:str, socket_udp:communicator.CustomSocket, print_info:bool = True) -> None:
        #TODO: add some asserts to check if the sockets sockets to send info 
        #TODO: write print_info to ask for info when running
        
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
            check3 = communicator.get_host_name().startswith(arguments["prefix"])
            # bundle the checks in a list
            checks = [check1, check2, check3] 
            if all(checks):
                message = "I'm a member !"
                print(message)
                self.communicator.send(message, socket_udp, info_sent = True)
            else:
                print("I'm not a member !")

        # IDENTIFICATION
        if command == "identification":
            print(f"{command} job")
            pass 

        # AQUIRE IMAGES 
        # NOTE: think of the storage of the images  
        if command == "aquire_images":
            print(f"{command} job")
            pass 

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
    rpicamera.stand_by_for_request(timeout=10)

    


"""
:Name: rpicamera
:Description: This module is used on the RPis 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""
from geocam import communicator
import json
import os 
import platform
import socket

class RPicamera(): 

    def __init__(self): 
        print("Created a RPicamera instance.")

        print("[INITIALISATION]")
        # initialisation: setup 
        self.sender = communicator.Sender()
        self.receiver = communicator.Receiver()

        # initialisation: Controller information
        self.ipaddr = self.sender.get_host_ip()
        self.macaddr = self.sender.get_mac_address()

        print('ips', self.ipaddr)
        print('mac', self.macaddr)

#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
############################################################################################################################################# 
    
    def excecute(self, request:dict, addr:str) -> None:
        # get the command and arguments 
        
        command = request['command']
        arguments = request['arguments']

        if command == "registration":
            print("[START REGISTRATION")
            # we must check that the device what it's suppose to be: in thise first version of the system: a RPi with a specific hostname runnning on Linux
            # check 1 os name must be the same as the ones sent by the controller 
            os_name = os.name
            check1 = os_name == arguments["os_name"]
            # check 2 plateform name must be the same as the ones sent by the controller 
            plateform_system = platform.system()
            check2 = plateform_system == arguments["plateform"]
            # check 3 prefix of hostname must be the same as the ones sent by the controller 
            hostname = self.receiver.get_host_name()
            check3 = hostname == arguments["prefix"].startswith("rp")
            # bundle the checks in a list
            checks = [check1, check2, check3] 
            # if all checks then only then respond 

#############################################################################################################################################
## IN PROGRESS NOW ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##########
###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########

            if all(checks):
                self.sender.sendto(b"pong", addr)
                print('response sent')

###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########
## IN PROGRESS NOW ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##########
#############################################################################################################################################


        if command == "id":
            print("[START] id command")
            self.controler_ip = arguments["id_address"]
            type_of_info = "pi_id"
            content = {"hostname":self.hostname, "ip_addr":self.ip_addr, "mac_addr":self.mac_addr}
            response = self.create_json(type_of_info, content)
            self.computer_ipaddr = arguments["id_address"]
            self.tcp_protocol_send(self.computer_ipaddr, response) 
            print('response sent') 

if __name__ == "__main__": 
    # instanciate a RPicamera class 
    rpicamera = RPicamera()
    # set a socket for listening to the MCAST_GRP
    udp_socket_waiting_for_requests = rpicamera.receiver.socket_for_broadcast_listenning()
    # infinitly wait for requests and execute them 
    while True:
        # get the requests in bytes 
        data, addr = rpicamera.receiver.get_requests(udp_socket_waiting_for_requests)
        # parse the request to a python dict
        request = rpicamera.receiver._read_json(data)
        # execute the request
        rpicamera.excecute(request, addr)

#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
############################################################################################################################################# 

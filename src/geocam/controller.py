"""
:Name: controller
:Description: This module is used for control of the rigs 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## TODO's ###################################################################################################################################
#############################################################################################################################################
""" 
1. Move the timeout from set_socket to listen 
"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

from geocam.communicator import *
from geocam.utils import *
import socket 
import traceback
import time

#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

class Controller:

    RPI_INFOS:dict = {"os_name":"posix", "plateform":"Linux", "prefix":"rp"}
    PC_PERSO_INFOS:dict = {"os_name":"nt", "plateform":"Windows", "prefix":"L"}

    def __init__(self) -> None:
        print("Created a Controller instance.")
        # instanciate a Leader and a Collaborator
        self.leader = Communicator(Communicator.LEADER) 
        self.collaborator = Communicator(Communicator.COLLABORATOR)
        # initiate the number of members 
        self.number_of_members = 0

    def choose_the_rig(self):
        """
        - Should allow the user to choose one of the rigs in the lab - which triaxial 
        - Ideally, since the number of rigs and there number of pis/cameras will be known, it could ba a good idea to set these infos here 
        """
        return 

    def registration(self, timeout:int = 10) -> None: 

        print("before registration: self.number_of_members = ", self.number_of_members)
        print(get_host_ip())
        ## first: create the request that will be sent to the members. 
        command = "registration" 
        arguments = self.PC_PERSO_INFOS
        request = create_json(command, arguments)

        ## second: assert the communicator 
        assert isinstance(self.leader.behavior, Leader)

        ## third: set the socket for broadcast, send the request and wait for answers from members. 
        # TODO: the timeout should be given to listen and not the set_socket function 
        print("[send/listen]")

        with self.collaborator.set_socket(timeout, info_set= False) as sock_tcp:
            # send request
            with self.leader.set_socket(timeout, info_set = False) as sock_udp: #timeout in seconds - info_set = True to print info  
                print("in the block")
                self.leader.send(request, sock_udp = sock_udp, info_sent = False)

            # wait for answers
            # TODO: use yield instead of return. this will allow to move the while and error handling in listen 
            while True:
                try:
                    start_time = time.time()
                    data, addr = self.collaborator.listen(sock_tcp = sock_tcp, info_listen = True)
                    if data: # this line basically tests if something was received 
                        print("something received")
                        print(data)
                        self.number_of_members += 1
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                    break
                else:
                    break # in the current sate only one registration is possible TODO: change that 

        print("after registration: self.number_of_members = ", self.number_of_members)

    def aquire_images(self, delay:int = 1, number_of_images:int = 2, timeout:int = 30) -> None:

        self.registration()

        print("[START CAPTURE]")

        ## first: create the request that will be sent to the members. 
        command = "capture_images" 
        arguments = {"delay":delay , "number_of_images":number_of_images}
        request = create_json(command, arguments)

        ## second: assert the communicator 
        assert isinstance(self.leader.behavior, Leader)

        ## third: set the socket for broadcast, send the request and wait for answers from members. 
        # TODO: the timeout should be given to listen and not the set_socket function 
        print("[send/listen]")

        with self.collaborator.set_socket(timeout, info_set= False) as sock_tcp:
            # send request
            with self.leader.set_socket(timeout, info_set = False) as sock_udp: #timeout in seconds - info_set = True to print info  
                print("in the block")
                self.leader.send(request, sock_udp = sock_udp, info_sent = False)

            # wait for answers
            # TODO: use yield instead of return. this will allow to move the while and error handling in listen 
            confirmations = 0
            while True:
                print(confirmations)
                try:
                    start_time = time.time()
                    data, addr = self.collaborator.listen(sock_tcp = sock_tcp, info_listen = True)
                    if data and confirmations < self.number_of_members: # this line basically tests if something was received 
                        print("something received")
                        print(data)
                        print("confirmations")
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                    break
                else:
                    break # in the current sate only one registration is possible TODO: change that 

        print("[All have confirmed]")

    def get_video_stream(self, timeout:int = 10):

        self.registration()

        command = "stream" 
        arguments = {}
        request = create_json(command, arguments)

        with self.collaborator.set_socket(timeout, info_set= False) as sock_tcp:
            # send request
            with self.leader.set_socket(timeout, info_set = False) as sock_udp: #timeout in seconds - info_set = True to print info  
                print("in the block")
                self.leader.send(request, sock_udp = sock_udp, info_sent = False)

            # wait for answers
            # TODO: use yield instead of return. this will allow to move the while and error handling in listen 
            while True:
                try:
                    start_time = time.time()
                    data, addr = self.collaborator.listen(sock_tcp = sock_tcp, info_listen = True)
                    if data: # this line basically tests if something was received 
                        print("something received")
                        print(data.decode('utf-8'))
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                    break
                else:
                    break # in the current sate only one registration is possible TODO: change that 

### Functions to be written 

    def configure_cameras(self): 
        """
        - Configuration and contols of the camera, must dive in the picamera2-mannual for the pi cameras 
        - Would be different rules for other cameras - we could make a child class to control each type of cameras that'll be used. Configure would then be specific to each camera
        - will communicate with the module used for a given type of camera 
        - To be reflected on 
        """
        return
    
    def focus(self):
        """
        - Start the focus process
        - Calls functions from the calibration module 
        """ 
        return

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    # check the network
    network_status()
    controller = Controller()
    controller.registration()
    # controller.aquire_images(delay = 1, number_of_images = 2)
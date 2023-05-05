"""
:Name: controller
:Description: This module is used for control of the rigs 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

from geocam import communicator 
import socket 
import traceback
import time

#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

class Controller:

    def __init__(self):
        print("Created a Controller instance.")
        # instanciate a Communicator
        self.communicator = communicator.Communicator(device = "controller") 
        # initiate the number of members 
        self.number_of_members = 0

    def choose_the_rig(self):
        """
        - Should allow the user to choose one of the rigs in the lab - which triaxial 
        - Ideally, since the number of rigs and there number of pis/cameras will be known, it could ba a good idea to set these infos here 
        """
        return 

    def list_the_registrants(self, timeout:int = 3) -> int: 

        ## first: create the request that will be sent to the members.

        # these informations are used to confirm that the targets are members.
        members_os_name = "nt" #"posix" # TODO: should modify to be an input of the user. 
        members_plateform = "Windows" #"Linux" # TODO: should modify to be an input of the user too. 
        prefix_of_host_name = "L" #"rp" # example: rp1 - NOTE: same for all mambers.

        # create the request using the communicator.create_json function. 
        command = "registration" 
        arguments = {"os_name":members_os_name, "plateform":members_plateform, "prefix":prefix_of_host_name}
        request = communicator.create_json(command, arguments)

        ## second: since this module is used on controller no need to change its behavior, 
        # default behavior of controllers being broadcaster. However, it's good practice 
        # to check anyway.

        assert isinstance(self.communicator.behavior, communicator.Broadcaster)
        # NOTE: self.communicator.behavior: Communicator current behavior
        # NOTE: communicator.Broadcaster: behavior of the controller when asking registrations

        ## third: set the socket for broadcast, send the request and wait for answers from 
        # members. 
        # TODO: the timeout should be given to listen and not the set_socket function 
        print("[send/listen]")
        with self.communicator.set_socket(timeout, info_set = True) as s: #timeout in seconds - info_set = True to print info  
            print("in the block")
            self.communicator.send(request, sock_udp = s, info_sent = True)
            while True:
                try:
                    start_time = time.time()
                    print("trying to listen")
                    data, addr = self.communicator.listen(s, info_listen = True)
                    if data: # this line basically tests if something was received 
                        print("something received")
                        self.number_of_members += 1
                except TimeoutError:
                    event_time = time.time()
                    time_past = event_time - start_time
                    print(f"exited after {time_past} seconds. timeout was set to {timeout} seconds")
                    break

        print("self.number_of_members = ", self.number_of_members)

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
    
    def aquire_images(self):
        """
        - Start taking the pictures 
        - The way to retrieve them should be discussed
        """
        return

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    # check the network
    communicator.network_status()
    controller = Controller()
    controller.list_the_registrants()
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
import inspect
import os 
import platform
import socket
import time 
# if platform.system() == "Linux":
    # from picamera2 import Picamera2
    # import cv2
    # import  pyshine as ps

from geocam.communicator import *
from geocam.utils import *

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler(f'{__file__[:-3]}.log', mode='w')
# file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


#############################################################################################################################################
## CLASS ####################################################################################################################################
#############################################################################################################################################

if platform.system() != "Linux" and not get_host_name().startswith("rp"):
    logger.critical("This module is intended to be used on the Raspberry Pi OS")

class RPicamera(): 

    HTML="""
    <html>
    <head>
    <title>PyShine Live Streaming</title>
    </head>

    <body>
    <center><h1> PyShine Live Streaming using OpenCV </h1></center>
    <center><img src="stream.mjpg" width='640' height='480' autoplay playsinline></center>
    </body>
    </html>
    """

    def __init__(self) -> None: 
        self.agent = Communicator(Communicator.AGENT)
        self.collaborator = Communicator(Communicator.COLLABORATOR)
        self.connection_info = {"host_name":get_host_name(), "ip_addr":get_host_ip(), "mac_addr":get_mac_address()}
        self.requests_history = []

        logger.info(f"{self}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        return f"Instanciated a {self.__class__.__name__} class instance"

    def stand_by_for_request(self, timeout:int = 10) -> None: 

        name_of_this_function = inspect.currentframe().f_code.co_name
        logger.info(f"Starting {name_of_this_function}")

        logger.debug(f"before {name_of_this_function}: self.requests_history = {self.requests_history}")
        logger.debug(f"host_ip is {get_host_ip()}")

        ## 1: assert the communicator 
        try: 
            assert isinstance(self.agent.behavior, Agent)
        except AssertionError:
            self.agent.change_behavior(Communicator.AGENT)
            logger.exception("AssertionError occured")
            # TODO: test this

        ## 2: set a socket that will listen for requests
        with self.agent.set_socket() as sock_udp: 
            ## 2.1: catch the requests
            for data, addr in self.agent.listen(sock_udp=sock_udp):
                request = read_json(data)
                self.requests_history.append(request)
                ## 2.2: execute the request 
                with self.collaborator() as sock_tcp:
                    self.excecute(request=request, socket_tcp=sock_tcp)

        logger.debug(f"after {name_of_this_function}: self.requests_history = {self.requests_history}") 

        logger.info(f"{name_of_this_function.capitalize()} completed")

    def excecute(self, request:dict, socket_tcp:socket.socket = None) -> None:
        
        ## 1: parse the request
        source = request["source"]
        content = request["content"]

        ## 2: do the requested job 
        if content["command"] == "registration":
            self._registration_job(source=source, arguments=content["arguments_or_response"], sock_tcp=socket_tcp)   

    def _registration_job(self, source:dict, arguments:dict, sock_tcp:socket.socket):
        
        name_of_this_function = inspect.currentframe().f_code.co_name
        logger.debug(f"Starting {name_of_this_function[1:]}")

        ## 0: parsing source 
        leader_ip_addr = source["ip_addr"]
        leader_name = source["host_name"]

        ## 1: check before sending answer
        checks = []
        checks.extend([os.name == arguments["os_name"], 
                       platform.system() == arguments["plateform"],
                       get_host_name().startswith(arguments["prefix"])])
        if all(checks):
            logger.debug(f"{get_host_name()} is a member and will send response to {leader_name} at ip addr {leader_ip_addr}")
            ## 1.1: creating a reponse
            content = {"command":"registration", "arguments_or_response":f"{name_of_this_function[1:]} completed"}
            message = create_json(self.connection_info, content)
            self.collaborator.send(message, sock_tcp=sock_tcp, target_ip=leader_ip_addr)

        logger.debug(f"Starting {name_of_this_function[1:]}")

# # AQUIRE IMAGES 
        # # NOTE: think of the storage of the images  
        # if command == "capture_images":
        #     print(f"{command} job")
        #     picam2 = Picamera2()
        #     # picam2.sensor_mode = 2
        #     host_name = self.id_info["host_name"]
        #     picam2.start_and_capture_files(f"{host_name}"+"_img{:03d}.jpg", initial_delay = 1, delay = arguments["delay"], num_files = arguments["number_of_images"], show_preview = False) 
        #     type_of_info = command
        #     content = f"{command} job done"
        #     message = create_json(type_of_info, content)
        #     self.collaborator.send(message, sock_tcp=socket_tcp, target_ip=addr[0], info_sent = False)

        # # CALIBRATE
        # if command == "stream":
        #     print(f"{command} job")
        #     type_of_info = command
        #     content = self.stream()
        #     message = create_json(type_of_info, content)
        #     self.collaborator.send(message, sock_tcp=socket_tcp, target_ip=addr[0], info_sent = False)

        # # CONFIGURE CAMERAS 
        # if command == "configure_cameras":
        #     print(f"{command} job")
        #     pass 
        
        # # REBOOT 
        # if command == "reboot":
        #     print(f"{command} job")
        #     pass 

        # # SHUTDOWN 
        # if command == "shutdown":
        #     print(f"{command} job")
        #     pass 

        # # INITIAL SCANNING 
        # if command == "initial_scanning":
        #     print(f"{command} job")

    # def stream(self) -> str:
    #     StreamProps = ps.StreamProps
    #     StreamProps.set_Page(StreamProps,self.HTML)
    #     host_ip = self.id_info["ip_addr"]
    #     address = (host_ip,9000) # Enter your IP address for host_ip
    #     try:
    #         StreamProps.set_Mode(StreamProps,'cv2')
    #         capture = cv2.VideoCapture(0)
    #         capture.set(cv2.CAP_PROP_BUFFERSIZE,4)
    #         capture.set(cv2.CAP_PROP_FRAME_WIDTH,320)
    #         capture.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
    #         capture.set(cv2.CAP_PROP_FPS,30)
    #         StreamProps.set_Capture(StreamProps,capture)
    #         StreamProps.set_Quality(StreamProps,90)
    #         server = ps.Streamer(address,StreamProps)
    #         print('Server started at','http://'+address[0]+':'+str(address[1]))
    #         yield 'Server started at','http://'+address[0]+':'+str(address[1])
    #         server.serve_forever()
            
    #     except KeyboardInterrupt:
    #         capture.release()
    #         server.socket.close()

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    # TODO: change the network_status function - so it returns info usable to start or not the process
    rpicamera = RPicamera()
    rpicamera.stand_by_for_request(timeout=10)
    # request = read_json(create_json("capture_images", {"delay":1 , "number_of_images":2}))
    # rpicamera.excecute(request)

    


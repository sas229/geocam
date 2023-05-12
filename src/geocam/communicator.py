"""
:Name: communicator
:Description: This module is used for the various communication operations
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

#############################################################################################################################################
## TODO's ###################################################################################################################################
#############################################################################################################################################
""" 
1. Write a flag that will switch on/off the printing of informtations/write some loggings -> it actually does just that 
2. Write the asserts functions 
3. Re-write the tests for this module
"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

import socket
import struct
import json 
import platform
import subprocess
import os
import warnings
import time
import traceback
import getmac

from geocam.utils import get_host_ip
from geocam.utils import network_status

#############################################################################################################################################
## CLASSES ##################################################################################################################################
#############################################################################################################################################

class CustomSocket(socket.socket): #TODO: replace by @context manager from contextlib 
    """Allow the use of context managers
    Its a class no parameters 

    Parameters
    ----------
    socket : _type_
        _description_
    """
    # TODO: add a flag to print or not print the exit statement
        
    def __enter__(self):
        print("in customsocket")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("in customsocket")
        print("socket closed")
        self.close()

class Behavior():

    MCAST_GRP:str = "224.1.1.1"
    MCAST_PORT:int = 1965
    TCP_PORT:int = 1645

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        return f"Instance of the {self.__class__.__name__} class"

class Leader(Behavior):

    def set_socket(self, timeout:int, info_set:bool) -> CustomSocket: 
        sock_udp = CustomSocket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock_udp.settimeout(timeout)
        if info_set: 
            print("in broadcaster_set_socket from broadcaster")
            print('socket set')
            print('timeout =', timeout, 's')
        return sock_udp
        
    def send(self, message:str, sock_udp:CustomSocket, info_sent:bool) -> None:
        print("in broadcast_request from broadcaster class") 
        sock_udp.sendto(bytes(message, encoding="utf-8"), (self.MCAST_GRP, self.MCAST_PORT))
        if info_sent:
            print(f"{message} sent to {(self.MCAST_GRP, self.MCAST_PORT)}")
            
    # def set_socket(self, timeout:int, info_set:bool) -> None:
    #     return self.broadcaster_set_socket(timeout, info_set)

    # def send(self, message:str, sock_udp:CustomSocket, info_sent:bool) -> None:
    #     return self.broadcast_request(message, sock_udp, info_sent)

    def listen(self) -> None: 
        raise NotImplementedError("Listen method not available for Broadcaster") 

class Agent(Behavior):

    def set_socket(self, timeout:int, info_set:bool) -> CustomSocket:
        sock_udp = CustomSocket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock_udp.settimeout(timeout)
        if info_set:
            print("in crowdmember_set_socket from crowdmember")
            print('socket set')
            print('timeout =', timeout, 's')
        return sock_udp
    
    def send(self) -> None:
        raise NotImplementedError("Send method not available for Broadcaster") 

    def listen(self, sock_udp:CustomSocket, info_listen:bool) -> tuple: 
        print("in wait_for_broadcast from crowdmember class")  
        print("before blocking")
        data, addr = sock_udp.recvfrom(1024)
        print("after blocking")
        if data: 
            if info_listen:
                print(f"{data} received from {addr}")
            return data, addr   

    # def set_socket(self, timeout:int, info_set:bool) -> None:
    #     return self.crowdmember_set_socket(timeout, info_set)

    # def listen(self, sock_udp:CustomSocket, info_listen:bool) -> None: 
    #     return self.wait_for_broadcast(sock_udp, info_listen)

class Collaborator(Behavior):

    def set_socket(self, timeout:int, info_set:bool) -> CustomSocket:
        sock_tcp = CustomSocket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(timeout)
        if info_set:
            print('socket set')
            print('timeout =', timeout, 's')
        return sock_tcp
    
    # TODO: modify this, the socket should be set in set socket !!!
    def send(self, message:str, sock_tcp:CustomSocket, target_ip:str, info_sent:bool) -> None:

        # to handle the case of no wlan or lan  
        # NOTE: this is a quick fix but maybe it will be enough 
        print() 
        if network_status() == "no_network":
            target_ip = "127.0.0.1"

        target_address = (target_ip, self.TCP_PORT)
        # TODO: check out create_connection 
        while True:
            try: 
                print(target_address)
                sock_tcp.connect(target_address)
            except ConnectionRefusedError:
                if info_sent:
                    print("Connection refused, retrying in 2 seconds...")
                time.sleep(2)
                continue
            except TimeoutError:
                if info_sent:
                    print(f"exited after timeout")
                break
            sock_tcp.sendall(bytes(message, 'utf-8'))
            print("Finally !!!")
            break

    def listen(self, sock_tcp:CustomSocket) -> tuple:
        # TODO: check out create_server 
        ipaddr = get_host_ip()
        sock_tcp.bind((ipaddr, self.TCP_PORT))
        sock_tcp.listen()
        while True:
            conn, addr = sock_tcp.accept()
            if conn: 
                data = conn.recv(1024)
                conn.close()
                break 
        return data, addr

    # def set_socket(self, timeout:int) -> None:
    #     return self.collaborator_set_socket(timeout)

    # def send(self, message:str, target_ip:str) -> None:
    #     return self.send_message(message, target_ip)

    # def listen(self, sock_tcp:CustomSocket) -> None: 
        return self.receive_message(sock_tcp)

    ## think about closing the sock when finished !!!

class Communicator: 

    LEADER = "Leader"
    AGENT = "Agent"
    COLLABORATOR = "Collaborator"

    def __init__(self, kind:str) -> None:
        self.kind = kind
        if self.kind == self.LEADER:
            self.behavior = Leader()
        elif self.kind == self.AGENT:
            self.behavior = Agent()
        elif self.kind == self.COLLABORATOR:
            self.behavior = Collaborator()
        else: 
            raise NotImplementedError("No other kind of Communicator is implemented at the moment") 
        print("Instantiated a", self)

    def __str__(self) -> str:
        return f"Communicator class instance behaving like a {self.kind}"
    
    def __repr__(self) -> str:
        return f"Communicator(Communicator.{self.kind.upper()})"
    
    def change_behavior(self, new_kind:str) -> None: 
        if new_kind == self.kind:
            print(f"Communicator already behaves like a {self.behavior}")
        else: 
            self.kind = new_kind
            if new_kind == Communicator.LEADER: 
                self.behavior = Leader()
                print(f"Communicator behavior changed to: {self.behavior}")
            elif new_kind == Communicator.AGENT:  
                self.behavior = Agent()
                print(f"Communicator behavior changed to: {self.behavior}")
            elif new_kind == Communicator.COLLABORATOR: 
                self.behavior = Collaborator()
                print(f"Communicator behavior changed to: {self.behavior}")

    def set_socket(self, timeout:int, info_set:bool = False) -> CustomSocket:
        return self.behavior.set_socket(timeout, info_set)
         
    def send(self,  message:str, sock_udp:CustomSocket = None, sock_tcp:CustomSocket = None, target_ip:str = None, info_sent:bool = False) -> None:
        print("in the send function of communicator")
        if isinstance(self.behavior, Collaborator): 
            print("tcp sender")
            # assert is_valid_ip(target_ip)
            print(target_ip)
            return self.behavior.send(message, sock_tcp, target_ip, info_sent)
        elif isinstance(self.behavior, Leader):
            print("udp sender")
            return self.behavior.send(message, sock_udp, info_sent)
        else: 
            return self.behavior.send()

    def listen(self, sock_udp:CustomSocket = None, sock_tcp:CustomSocket = None, info_listen:bool = False):
        print("in the listen function of communicator") 
        if isinstance(self.behavior, Collaborator):
            print("tcp listener")
            # assert isinstance(sock_tcp, CustomSocket) 
            return self.behavior.listen(sock_tcp)
        elif isinstance(self.behavior, Agent):
            print("udp listener")
            # assert isinstance(sock_udp, CustomSocket)  
            return self.behavior.listen(sock_udp, info_listen)
        else: 
            return self.behavior.listen()

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    leader = Communicator(Communicator.LEADER)
    print(leader.behavior.__repr__())
    print(leader.behavior)
    # print(leader.behavior.mcast_grp)
    # leader._change_mcast_grp("224.1.1.2")
    # print(leader.behavior.mcast_grp)
    # print(leader.behavior.MCAST_GRP)


    # in the future write some tests
    # functions 
    # print(get_host_name())
    # print(get_host_ip())
    # print(get_mac_address())
    # print(ping("google.com")) # works with conn to internet
    # print(ping(get_host_ip()))
    # print(is_local_ip_address("127.0.0.1"))
    # print(is_local_ip_address(get_host_ip()))
    # network_status()
    # print(type(create_json("ping", {"ipaddr":"127.0.0.1"})))
    # print(type(read_json(create_json("ping", {"ipaddr":"127.0.0.1"}))))

    # # classes 
    # customsock = CustomSocket()
    # print(isinstance(customsock, CustomSocket))
    
    # com = Communicator(Communicator.BROADCASTER)
    # print(com)
    # # try: 
    # #     com.listen()
    # # except NotImplementedError:
    # #     print("OK")
    # # print(isinstance(com, Communicator))
    # # print(isinstance(com.behavior, Broadcaster)) #when on controller 
    # com.change_type("crowdmember")
    # print(com)
    # print(isinstance(com.behavior, CrowdMember),'why', print(com.behavior)) #when on member 
    # try: 
    #     com.send()
    # except NotImplementedError:
    #     print("OK")
    # com.change_type("collaborator")
    # print(isinstance(com.behavior, Collaborator)) # specially for tcp
    
    

# TODO: debbug change behavior 



                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    # more tests of the methods


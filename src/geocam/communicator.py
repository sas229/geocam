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
1. Write the asserts functions 
2. Re-write the tests for this module
"""

#############################################################################################################################################
## IMPORTS ##################################################################################################################################
#############################################################################################################################################

import logging
import socket
import struct
import time
import datetime

from typing import Union

from geocam.utils import get_host_ip
from geocam.utils import network_status

#############################################################################################################################################
## CLASSES ##################################################################################################################################
#############################################################################################################################################
class Behavior():
    """_summary_

    Returns
    -------
    _type_
        _description_
    """    

    MCAST_GRP:str = "232.18.125.68"
    MCAST_PORT:int = 1965
    TCP_PORT:int = 1645

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        return f"Instance of the {self.__class__.__name__} class"

class Leader(Behavior):
    """_summary_

    Parameters
    ----------
    Behavior : _type_
        _description_
    """    

    def _set_socket(self, timeout:int = 10) -> socket.socket: 
        """_summary_

        Parameters
        ----------
        timeout : int, optional
            _description_, by default 10

        Returns
        -------
        socket.socket
            _description_
        """
        ttl = 2
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock_udp.settimeout(timeout)
        print("Socket set for UDP multicast transfer - set to send")
        return sock_udp
        
    def _send(self, message:str = None, sock_udp:socket.socket = None) -> None:
        """_summary_

        Parameters
        ----------
        message : str, optional
            _description_, by default None
        sock_udp : socket.socket, optional
            _description_, by default None
        info_prints : bool, optional
            _description_, by default False
        """
        sock_udp.sendto(bytes(message, encoding="utf-8"), (self.MCAST_GRP, self.MCAST_PORT))
        print(f"{message} sent to {(self.MCAST_GRP, self.MCAST_PORT)}")

    def _listen(self) -> None: 
        raise NotImplementedError("Listen method not available for Leader. This class is only supposed to send requests") 

class Agent(Behavior):
    """_summary_

    Parameters
    ----------
    Behavior : _type_
        _description_
    """    

    def _set_socket(self, timeout:int = 10) -> socket.socket:
        """_summary_

        Parameters
        ----------
        timeout : int, optional
            _description_, by default 10

        Returns
        -------
        socket.socket
            _description_
        """
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock_udp.settimeout(timeout)
        print("Socket set for UDP multicast transfer - set to receive")
        return sock_udp
    
    def _send(self) -> None:
        raise NotImplementedError("Send method not available for Broadcaster. This class is only supposed to receive requests") 

    def _listen(self, sock_udp:socket.socket = None) -> tuple:
        """_summary_

        Parameters
        ----------
        sock_udp : socket.socket, optional
            _description_, by default None
        info_prints : bool, optional
            _description_, by default False

        Returns
        -------
        tuple
            _description_
        """
        data, addr = sock_udp.recvfrom(1024)
        print(f"This data: \n {data} \nwas received from {addr}")
        return data, addr   

class Collaborator(Behavior):
    """_summary_

    Parameters
    ----------
    Behavior : _type_
        _description_
    """    

    def _set_socket(self, timeout:int = 10) -> socket.socket:
        """_summary_

        Parameters
        ----------
        timeout : int, optional
            _description_, by default 10
        info_set : bool, optional
            _description_, by default False

        Returns
        -------
        socket.socket
            _description_
        """
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(timeout)
        print("Socket set for TCP unicast transfer")
        return sock_tcp
    
    def _send(self, message:str, sock_tcp:socket.socket, target_ip:str) -> None:
        """_summary_

        Parameters
        ----------
        message : str
            _description_
        sock_tcp : socket.socket
            _description_
        target_ip : str
            _description_
        info_sent : bool
            _description_
        """
        
        target_address = (target_ip, self.TCP_PORT)
        
        # to handle the case of no wlan or lan NOTE: this is a quick fix but maybe it will be enough
        if network_status() == "no_network":
            target_ip = "127.0.0.1"

        while True:
            try: 
                sock_tcp.connect(target_address)
            except ConnectionRefusedError:
                print("Connection refused, retrying in 2 seconds...")
                time.sleep(2)
                continue
            except TimeoutError:
                print(f"exited after timeout")
                break
            sock_tcp.sendall(bytes(message, 'utf-8'))
            print("Finally !!!")
            break

    def _listen(self, sock_tcp:socket.socket) -> tuple: 
        """_summary_

        Parameters
        ----------
        sock_tcp : socket.socket
            _description_

        Returns
        -------
        tuple
            _description_
        """
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
    
class Communicator:
    """_summary_

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    NotImplementedError
        _description_
    """     

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

    def set_socket(self, timeout:int = 10) -> None:
        """_summary_

        Parameters
        ----------
        timeout : int, optional
            _description_, by default 10
        info_prints : bool, optional
            _description_, by default False

        Returns
        -------
        _type_
            _description_
        """               
        return self.behavior._set_socket(timeout) 
         
    def send(self,  message:str, sock_udp:socket.socket = None, sock_tcp:socket.socket = None, target_ip:str = None) -> None:
        """_summary_

        Parameters
        ----------
        message : str
            _description_
        sock_udp : socket.socket, optional
            _description_, by default None
        sock_tcp : socket.socket, optional
            _description_, by default None
        target_ip : str, optional
            _description_, by default None
        info_prints : bool, optional
            _description_, by default False
        """        
        if isinstance(self.behavior, Collaborator): 
            self.behavior._send(message, sock_tcp, target_ip)
        if isinstance(self.behavior, Leader):
            self.behavior._send(message, sock_udp)
        else: 
            self.behavior._send()

    def listen(self, sock_udp:socket.socket = None, sock_tcp:socket.socket = None) -> None:
        """_summary_

        Parameters
        ----------
        sock_udp : socket.socket, optional
            _description_, by default None
        sock_tcp : socket.socket, optional
            _description_, by default None

        Returns
        -------
        _type_
            _description_
        """
        if isinstance(self.behavior, Collaborator):
            return self.behavior._listen(sock_tcp)
        if isinstance(self.behavior, Agent): 
            return self.behavior._listen(sock_udp)
        else: 
            return self.behavior._listen()

# #############################################################################################################################################
# ## MAIN #####################################################################################################################################
# #############################################################################################################################################

def main():

    logging.basicConfig(filename='communicator.log', encoding='utf-8', level=logging.DEBUG)
    logging.info(f'<{datetime.datetime.now().strftime("%H:%M:%S")}>'+'Started')
    # could be changed 

    # leader = Communicator(Communicator.LEADER)
    # with leader.set_socket() as s: 
    #     leader.send("test", sock_udp=s)

    collaborator = Communicator(Communicator.COLLABORATOR)
    with collaborator.set_socket() as s:
        print(collaborator.listen(sock_tcp=s))

    logging.info(f'<{datetime.datetime.now().strftime("%H:%M:%S")}>'+'Finished')

if __name__ == "__main__": 
    main()


    # agent = Communicator(Communicator.AGENT)
    # agent_socket = agent.set_socket(info_prints=True) 
    # with agent_socket as s:
    #     agent.listen(sock_udp=s, info_prints=True)

    # collaborator = Communicator(Communicator.COLLABORATOR)
    # collaborator_server_socket = collaborator.set_socket()
    # with collaborator_server_socket as s: 
    #     collaborator.listen(sock_tcp=s)














#     print(leader.behavior.__repr__())
#     print(leader.behavior)
#     # print(leader.behavior.mcast_grp)
#     # leader._change_mcast_grp("224.1.1.2")
#     # print(leader.behavior.mcast_grp)
#     # print(leader.behavior.MCAST_GRP)


#     # in the future write some tests
#     # functions 
#     # print(get_host_name())
#     # print(get_host_ip())
#     # print(get_mac_address())
#     # print(ping("google.com")) # works with conn to internet
#     # print(ping(get_host_ip()))
#     # print(is_local_ip_address("127.0.0.1"))
#     # print(is_local_ip_address(get_host_ip()))
#     # network_status()
#     # print(type(create_json("ping", {"ipaddr":"127.0.0.1"})))
#     # print(type(read_json(create_json("ping", {"ipaddr":"127.0.0.1"}))))

#     # # classes 
#     # customsock = CustomSocket()
#     # print(isinstance(customsock, CustomSocket))
    
#     # com = Communicator(Communicator.BROADCASTER)
#     # print(com)
#     # # try: 
#     # #     com.listen()
#     # # except NotImplementedError:
#     # #     print("OK")
#     # # print(isinstance(com, Communicator))
#     # # print(isinstance(com.behavior, Broadcaster)) #when on controller 
#     # com.change_type("crowdmember")
#     # print(com)
#     # print(isinstance(com.behavior, CrowdMember),'why', print(com.behavior)) #when on member 
#     # try: 
#     #     com.send()
#     # except NotImplementedError:
#     #     print("OK")
#     # com.change_type("collaborator")
#     # print(isinstance(com.behavior, Collaborator)) # specially for tcp
    
    

# TODO: debbug change behavior 



                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    # more tests of the methods


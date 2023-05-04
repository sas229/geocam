"""
:Name: communicator
:Description: This module is used for the various communication operations
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""

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

#############################################################################################################################################
## MAIN CLASS ###############################################################################################################################
#############################################################################################################################################


class Communicator(): 

    def __init__(self, device:str = 'controller', rig:str = 'txc1',  mcast_grp:str = '224.1.1.1', mcast_port:int = 9998, tcp_port:int = 47822) -> None: 
        print("Created a Communicator instance.")
        
        # constants - given byt he user 
        self.rig:str = rig
        self.mcast_grp:str = mcast_grp
        self.mcast_port:int = mcast_port
        self.tcp_port:int = tcp_port

        # constants - generated
        self.ipaddr:str = self.get_host_ip()
        self.hostname:str = self.get_host_name()
        self.macaddr:str = self.get_mac_address()
        # could be interesting to get the name of the router ..

#############################################################################################################################################
## Get informations on machine ##############################################################################################################
############################################################################################################################################# 
 
    def get_host_name(self) -> str: 
        """No very useful but might become useful, if not discard it

        Returns
        -------
        str
            _description_
        """
        return socket.gethostname()
        
    def get_host_ip(self) -> str:
        """Gets the host IP address

        Returns
        -------
        str
            IP address
        """        
        if platform.system().lower() == 'windows':
            return socket.gethostbyname(socket.gethostname())
        else: 
            routes = json.loads(os.popen("ip -j -4 route").read())
            for r in routes:
                if r.get("dev") == "wlan0" and r.get("prefsrc"):
                    host_ip = r['prefsrc']
                    continue
            return host_ip 
        
    def get_mac_address(self) -> str:
        return getmac.get_mac_address()
    
#############################################################################################################################################
## Network diagnostic #######################################################################################################################
############################################################################################################################################# 
    
    def ping(self, host:str) -> bool:
        """This method is used to ping the network

        Parameters
        ----------
        host : str
            Host to ping 

        Returns
        -------
        bool
            True if we have an answer or False if no answer
        """        
        param = '-n' if platform.system().lower()=='windows' else '-c'
        try:
            subprocess.check_output(["ping", param, "1", host], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False
        
    def is_local_ip_address(self, host_ip:str) -> bool: 
        """_summary_

        Parameters
        ----------
        host_ip : str
            _description_

        Returns
        -------
        bool
            _description_
        """        
        if host_ip == host_ip.startswith('127.') or host_ip == socket.gethostbyname('localhost'):
            return True
        else: 
            return False 
        
    def network_status(self, remote_server:str = "google.com"):
        """_summary_
        3 status possible: 
        - status_1: the device is not on a network
        - status_2: the device is on a network with no access to internet 
        - status_3: the device is on a network with access to internet 

        Parameters
        ----------
        remote_server : str, optional
            Sexternal server that the device will try to reach to test the internet connection, 
            by default "google.com"

        """

        is_local_ip_address = self.is_local_ip_address(self.get_host_ip())
        is_internet_connected = self.ping(remote_server)

        # status_1 : Warning : Not on a network
        if not is_internet_connected and is_local_ip_address :
            warnings.warn("This device isn't connected to a network", stacklevel=2)

        # status_2 : Warning : No access to internet
        elif not is_internet_connected and not is_local_ip_address: 
            warnings.warn("No access to internet", stacklevel=2)

        # status_3 : Warning : Access to internet
        elif is_internet_connected and not is_local_ip_address:
            warnings.warn("Access to internet", stacklevel=2)
        
        # undifined configuration
        else:
            print("Undifined - the ip is the local one but access to internet")

## Messages bundle ##########################################################################################################################
############################################################################################################################################# 
            
    def _create_json(self, command:str, arguments:str) -> str:
        """_summary_

        Parameters
        ----------
        command : str
            _description_
        arguments : str
            _description_

        Returns
        -------
        str
            string representing a JSON object
        """      
        _dict = {"command":command ,"arguments":arguments}
        return json.dumps(_dict, indent=2)

    def _read_json(self, json_string:str) -> dict: 
        """Don't do much for now but might become usefull later

        Parameters
        ----------
        json_string : str
            _description_

        Returns
        -------
        dict
            _description_
        """
        return json.loads(json_string)
        

#############################################################################################################################################
## CHILD CLASSES ############################################################################################################################
#############################################################################################################################################


class Sender(Communicator):
    """_summary_

    Parameters
    ----------
    Communicator : _type_
        _description_
    """
    def __init__(self, device:str = 'controller', rig: str = 'txc1', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822) -> None:
        """_summary_

        Parameters
        ----------
        device : str, optional
            _description_, by default 'controller'
        rig : str, optional
            _description_, by default 'txc1'
        mcast_grp : str, optional
            _description_, by default '224.1.1.1'
        mcast_port : int, optional
            _description_, by default 9998
        tcp_port : int, optional
            _description_, by default 47822
        """
        super().__init__(device, rig, mcast_grp, mcast_port, tcp_port)
        print("--> Child Class: Sender instance")

#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
############################################################################################################################################# 

    # VERSION 1 FUNC TO SEND INFO TO ALL MEMBERS OF THE MCCASTGRP - used by the controller

    def send_to_all(self, message:str) -> None:
        print("[send_to_all]")
        """_summary_

        Parameters
        ----------
        message : _type_
            _description_
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            ttl = struct.pack('b', 1)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            s.sendto(bytes(message, encoding="utf-8"), (self.mcast_grp, self.mcast_port))

        print(f"{message} sent on broadcast channel")

    # VERSION 1 FUNC TO SEND INFO TO ONE MEMBER VIA TCP/IP

    def send_to_one(self, target_ip:str, message:str) -> None:
        """_summary_

        Parameters
        ----------
        target_ip : str
            _description_
        message : str
            _description_
        """
        target_address = (target_ip, self.tcp_port)
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try: 
                    s.connect(target_address)
                except ConnectionRefusedError:
                    print("Connection refused, retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                s.sendall(bytes(message, 'utf-8'))
            break 
        print(f"{message} sent to {target_address}")

    # VERSION 2 FUNC TO SEND INFO TO ALL MEMBERS OF THE MCCASTGRP : new name send_on_mcastgrp old name send_to_all

    def send_on_mcastgrp(self, message:str) -> None:
        print("[send_to_all]")
        """_summary_

        Parameters
        ----------
        message : _type_
            _description_
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            ttl = struct.pack('b', 1)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            s.sendto(bytes(message, encoding="utf-8"), (self.mcast_grp, self.mcast_port))

        print(f"{message} sent on broadcast channel")

class Receiver(Communicator):
    """_summary_

    Parameters
    ----------
    Communicator : _type_
        _description_
    """
    def __init__(self, device: str = 'controller', rig: str = 'txc1', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822) -> None:
        super().__init__(device, rig, mcast_grp, mcast_port, tcp_port)
        print("--> Child Class: Receiver instance")

    # VERSION 1 FUNC TO LISTEN TO ALL MEMBERS OF THE MCCASTGRP

    def listen_for_broadcast(self, timeout = 3) -> str: # WILL DISAPPEAR
        """_summary_

        Returns
        -------
        _type_
            _description_
        """
        print("[listen_for_broadcast]")
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"Standing by on mcast_grp:{self.mcast_grp}, mcast_port:{self.mcast_port}")
        sock_udp.settimeout(timeout)
        
        counter = 0
        try: 
            while True:
                data, addr = sock_udp.recvfrom(1024)
                counter += 1
                print(f"Received data {data}")
                return data 
        
        except TimeoutError:
            print(f"Waited {timeout} s and no responce")

        except Exception:
            traceback.print_exc()
        
        finally: 
            sock_udp.close()
            if counter == 0:
                print(f"No rpis found")
            else:
                print(f"Found {counter} rpis")
            return counter
        
    # VERSION 2 FUNC TO LISTEN TO ALL MEMBERS OF THE MCCASTGRP: NOW TWO FUNCS 

    # FIRST TO CREATE THE SOCKET 
        
    def socket_for_broadcast_listenning(self, timeout:float = 3) -> socket.socket:
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"Standing by on mcast_grp:{self.mcast_grp}, mcast_port:{self.mcast_port}")
        
        return sock_udp 
    
    # SECOND TO COUNT THE MEMBERS 

    def count_member_of_mcastgrp(self, sock_udp:socket.socket, timeout:int = 3) -> int: # WILL DISAPPEAR
        # what will happen with the returns ? 
        number_of_members = 0
        with sock_udp as s:
            s.settimeout(timeout) 
            try: 
                while True:
                    data, addr = s.recvfrom(1024)
                    number_of_members += 1
                    print(f"Received data {data}")
                    return data 
            
            except TimeoutError:
                print(f"Waited {timeout} s and no responce")

            except Exception:
                traceback.print_exc()
            
            finally: 
                print(f"No rpis found") if number_of_members == 0 else print(f"Found {number_of_members} rpis")
                return number_of_members

    # VERSION 3 FUNC TO LISTEN TO ALL MEMBERS OF THE MCASTGRP: THREE FUNCTIONS WITH ONE IN CONTROLLER: SEE count_member_of_mcastgrp

    # FIRST ONE REMAINS: socket_for_broadcast_listenning

    # SECOND ONE IN CONTROLLER: count_member_of_mcastgrp2 : MODIFIED 

    # THIRD ONE HERE: see here : listen_to_all

    # it's the one that allows the most flexibility when using the communications functions. count_member_of_mcastgrp2 is only a example of how these functions can be used 

    def listen_to_all(self, sock_tcp:socket.socket, timeout:float) -> int:
        number_of_members = 0
        while True:
            data, addr = sock_tcp.recvfrom(1024)
            number_of_members += 1
            print(f"Received data {data}")
            return number_of_members 
        
    # VERSION 4 FUNC TO LISTEN TO ALL MEMBERS OF THE MCASTGRP: THREE FUNCTIONS WITH ONE IN CONTROLLER: SEE count_member_of_mcastgrp

    # FIRST ONE REMAINS: socket_for_broadcast_listenning

    # SECOND ONE IN CONTROLLER: count_member_of_mcastgrp2 : MODIFIED 

    # THIRD ONE HERE: see here : listen_to_all_members

    # I realised something: 
    # - issue one: the current code will get out of the while loop after the first member answers. this can be solved by relying on a timeout error to stop the process 
    # - issue two: this fucntions as to be used for the registration process and the identification of the pis - it's not flexible enough as it is -> will have to write two  

#############################################################################################################################################
## NEEDS MODIFICATIONS ###%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%######
###%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%########

    def listen_to_all_members_for_registration(self, sock_udp:socket.socket, timeout:float) -> int:
        # timeout shouldn't be too high
        number_of_members = 0
        addr = None
        while True:
            try:    
                data, addr = sock_udp.recvfrom(1024)
                if data:
                    number_of_members += 1 
            except TimeoutError:
                break
        return number_of_members 
        
    def get_requests(self, sock_udp:socket.socket, timeout:float = 20) -> bytes: # should have no timetout for later - keeping the timeout for dev
        print(f"don't forget the timeout of {timeout}s, get rid of it")
        while True:
            data, addr = sock_udp.recvfrom(1024)
            return data, addr

###%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%########
## IN PROGRESS NOW ###%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%##########
#############################################################################################################################################


    # VERSION 1 FUNC TO LISTEN TO ALL MEMBERS FOR INCOMING TCP/IP REQUESTS   
    
    def listen_to_one(self) -> str: # WILL DISAPPEAR
        """_summary_

        Returns
        -------
        str
            _description_
        """
        print("[listen_to_one]")
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ipaddr, self.tcp_port))
        sock_tcp.listen()

        try:
            while True:
                conn, addr = sock_tcp.accept()
                if conn: 
                    data = conn.recv(1024)
                
        except Exception:
            traceback.print_exc()
            sock_tcp.close()

        return data
    
    # VERSION 2 FUNC TO LISTEN TO ALL MEMBERS FOR INCOMING TCP/IP REQUESTS: NOW TWO FUNCS
    
    # FIRST TO CREATE THE SOCKET 

    def socket_for_one_to_one_listening(self) -> socket.socket:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ipaddr, self.tcp_port))
        sock_tcp.listen()
        return sock_tcp 
    
    # SECOND TO ACCEPT INCOMING REQUESTS FOR CONNECTION
    
    def accept_response(self, sock_tcp:socket.socket, timeout:float = 10) -> None: # WILL DISAPPEAR
        found_members = 0
        with sock_tcp as s: 
            try: 
                while True:
                    conn, addr = sock_tcp.accept()
                    if conn: 
                        data = conn.recv(1024)
                        print(f"Received data {data}")
                        found_members += 1
                        return data 

            except TimeoutError:
                print(f"Waited {timeout} s and no responce")

            except Exception:
                traceback.print_exc()

    # VERSION 3 FUNC TO LISTEN TO ALL MEMBERS FOR INCOMING TCP/IP REQUESTS: NOW THREE FUNCTIONS WITH ONE IN CONTROLLER: SEE get_ip_and_mac_addrr_of_the_members2

    # FIRST ONE REMAINS: socket_for_one_to_one_listening

    # SECOND ONE IN CONTROLLER: get_ip_and_mac_addrr_of_the_members2 : MODIFIED 

    # THIRD ONE HERE: see here : listen_to_one2

    # FINAL VERSION: it's the one that allows the most flexibility when using the communications functions. get_ip_and_mac_addrr_of_the_members2 is only a example of how these functions can be used 

    def listen_to_one2(self, sock_tcp:socket.socket, timeout:float) -> bytes:
        while True:
            conn, addr = sock_tcp.accept()
            if conn: 
                data = conn.recv(1024)
                print(f"Received data {data}")
                return data 

#############################################################################################################################################
####################################################"""IN PROGRESS NOW"""####################################################################
#############################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!###########################################################
#############################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#################################
############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!###################
###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########

class UDP_multicast(Communicator):

    def __init__(self, device: str = 'controller', rig: str = 'txc1', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822) -> None:
        super().__init__(device, rig, mcast_grp, mcast_port, tcp_port)

    ### used by the sender
    # setup the udp socket 
    def sender(self, timeout:int = 10) -> socket.socket: # check if the timeout is required or not  
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        return sock_udp  

    # send data 
    # use the preexsiting sendto method of socket

    ### used by the receiver
    # setup the udp socket
    def receiver(self) -> socket.socket: # check if the timeout is required or not  
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"Standing by on mcast_grp:{self.mcast_grp}, mcast_port:{self.mcast_port}")
        return sock_udp 
    
    # receive data 
    # this function is not join to the previous to allow us to write different function that uses the receive function 
    def receive(self, sock_udp:socket.socket, timeout:int = 10) -> tuple: 
        sock_udp.settimeout(timeout)
        while True:
            data, addr = sock_udp.recvfrom(1024)
            return data, addr

class TCP_ip(Communicator):

    def __init__(self, device: str = 'controller', rig: str = 'txc1', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822) -> None:
        super().__init__(device, rig, mcast_grp, mcast_port, tcp_port)

    # used by the sender
    def send(self, target_ip:str, message) -> socket.socket: 
        server_address = (target_ip, self.tcp_port)
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try: 
                    s.connect(server_address)
                except ConnectionRefusedError:
                    print("Connection refused, retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                s.sendall(bytes(message, 'utf-8'))
            break 

    # used by the receiver 
    def receiver(self, timeout:int = 10) -> socket.socket: # check if the timeout is required or not 
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ipaddr, self.tcp_port))
        sock_tcp.listen()
        return sock_tcp
    
    def receive(self, sock_tcp:socket.socket, timeout:int = 10) -> tuple:
        sock_tcp.settimeout(timeout)
        while True:
            conn, addr = sock_tcp.accept()
            if conn: 
                data = conn.recv(1024)
                return data, addr


###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########
############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!####################
#############################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#################################
#############################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!###########################################################
####################################################"""IN PROGRESS NOW"""####################################################################
#############################################################################################################################################
  
      



#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
#############################################################################################################################################
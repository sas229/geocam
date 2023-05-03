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
        self.ip_address:str = self.get_host_ip()

    def tcp_ip_socket(self) -> socket.socket: 
        """This method creates a socket for TCP/IP communication

        Returns
        -------
        socket.socket
            TCP socket
        """
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ip_address, self.tcp_port))
        return sock_tcp

    def ping(self, host: str) -> bool:
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
            print("host_ip", host_ip)
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
        print(is_local_ip_address)
        print(is_internet_connected)

        # status_1 : Warning : Not on a network
        if not is_internet_connected and is_local_ip_address :
            warnings.warn("This device isn't connected to a network", stacklevel=2)

        # status_2 : Warning : No access to internet
        elif not is_internet_connected and not is_local_ip_address: 
            warnings.warn("No access to internet", stacklevel=2)

        # status_3 
        elif is_internet_connected and not is_local_ip_address:
            warnings.warn("Access to internet", stacklevel=2)
        
        # undifined configuration
        else:
            print("Undifined - the ip is the local one but access to internet")
            
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

    def send_to_all(self, message:str) -> None:
        """_summary_

        Parameters
        ----------
        message : _type_
            _description_
        """
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ttl = struct.pack('b', 1)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
        sock_udp.sendto(bytes(message, encoding="utf-8"), (self.mcast_grp, self.mcast_port))
        print(f"{message} sent on broadcast channel")

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

class Receiver(Communicator):
    """_summary_

    Parameters
    ----------
    Communicator : _type_
        _description_
    """
    def __init__(self, device: str = 'controller', rig: str = 'txc1', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822) -> None:
        super().__init__(device, rig, mcast_grp, mcast_port, tcp_port)

    def listen_for_brodcast_on(self) -> str:
        """_summary_

        Returns
        -------
        _type_
            _description_
        """
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"Standing by on mcast_grp:{self.mcast_grp} | mcast_port:{self.mcast_port}")
        
        try: 
            while True:
                data, addr = sock_udp.recvfrom(1024)
                print(f"Received data {data}")
        
        except Exception:
            traceback.print_exc()
            sock_udp.close()
        
        return data

    def listen_to_one(self) -> str:
        """_summary_

        Returns
        -------
        str
            _description_
        """
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
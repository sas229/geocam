"""
:Name: communicator
:Description: This module is used for the various communication operations
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

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

#############################################################################################################################################
## CLASSES ##################################################################################################################################
#############################################################################################################################################

class CustomSocket(socket.socket):
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

# TODO: change the classes 
class Behavior():

    def __init__(self, **kwargs) -> None:
        # si ça bug essaie avec pop au lieu de get 
        # ids and connections "numbers" - papers of the communicator
        self.mcast_grp:str = kwargs.get("mcast_grp", "224.1.1.1")
        self.mcast_port:int = kwargs.get("mcast_port", 1965)
        self.tcp_port:int = kwargs.get("tcp_port", 1645)

    def set_socket(self) -> None:
        pass

    def send(self) -> None:
        pass 

    def listen(self) -> None: 
        pass 

    # having set, send, listen would be great 

class Broadcaster(Behavior):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return "broadcaster"

    def broadcaster_set_socket(self, timeout:int, info_set:bool) -> CustomSocket: 
        sock_udp = CustomSocket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock_udp.settimeout(timeout)
        if info_set: 
            print("in broadcaster_set_socket from broadcaster")
            print('socket set')
            print('timeout =', timeout, 's')
        return sock_udp
        
    def broadcast_request(self, message:str, sock_udp:CustomSocket, info_sent:bool) -> None:
        print("in broadcast_request from broadcaster class") 
        sock_udp.sendto(bytes(message, encoding="utf-8"), (self.mcast_grp, self.mcast_port))
        if info_sent:
            print(f"{message} sent to {(self.mcast_grp, self.mcast_port)}")

    def listen_to_members(self, sock_udp:CustomSocket, info_listen:bool) -> tuple:
        print("in listen_to_members from broadcaster class")  
        print("before blocking")
        data, addr = sock_udp.recvfrom(1024)
        print("after blocking")
        if data: 
            if info_listen:
                print(f"{data} received from {addr}")
            return data, addr
            
    def set_socket(self, timeout:int, info_set:bool) -> None:
        return self.broadcaster_set_socket(timeout, info_set)

    def send(self, message:str, sock_udp:CustomSocket, info_sent:bool) -> None:
        return self.broadcast_request(message, sock_udp, info_sent)

    def listen(self, sock_udp:CustomSocket, info_listen:bool) -> None: 
        return self.listen_to_members(sock_udp, info_listen) 
    
    ## think about closing the sock when finished !!!

class CrowdMember(Behavior):
    # TODO: write about the asserts 

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return "crowdmember"

    def crowdmember_set_socket(self, timeout:int, info_set:bool) -> CustomSocket:
        sock_udp = CustomSocket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock_udp.settimeout(timeout)
        if info_set:
            print("in crowdmember_set_socket from crowdmember")
            print('socket set')
            print('timeout =', timeout, 's')
        return sock_udp

    def respond_to_broadcaster(self, message:str, sock_udp:CustomSocket, info_sent:str) -> None:
        print("in respond_to_broadcaster from crowdmember class")
        sock_udp.sendto(bytes(message, encoding="utf-8"), (self.mcast_grp, self.mcast_port)) 
        if info_sent:
                print(f"{message} sent to {(self.mcast_grp, self.mcast_port)}")

    def wait_for_broadcast(self, sock_udp:CustomSocket, info_listen:bool) -> tuple: 
        print("in wait_for_broadcast from crowdmember class")  
        print("before blocking")
        data, addr = sock_udp.recvfrom(1024)
        print("after blocking")
        if data: 
            if info_listen:
                print(f"{data} received from {addr}")
            return data, addr   

    def set_socket(self, timeout:int, info_set:bool) -> None:
        return self.crowdmember_set_socket(timeout, info_set)

    def send(self, message:str, sock_udp:CustomSocket, info_sent:str) -> None:
        # TODO: inverse message and sock_udp -> copy the template from braodcaster
        return self.respond_to_broadcaster(message, sock_udp, info_sent)

    def listen(self, sock_udp:CustomSocket, info_listen:bool) -> None: 
        return self.wait_for_broadcast(sock_udp, info_listen)

    ## think about closing the sock when finished !!!

class Confidant(Behavior):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return "confidant"
    
    def confidant_set_socket(self, timeout:int) -> CustomSocket:
        sock_tcp = CustomSocket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(timeout)
        print('socket set')
        print('timeout =', timeout, 's')
        return sock_tcp
    
    def send_message(self, message:str, target_ip:str) -> None:
        server_address = (target_ip, self.tcp_port)
        while True:
            with CustomSocket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try: 
                    s.connect(server_address)
                except ConnectionRefusedError:
                    print("Connection refused, retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                s.sendall(bytes(message, 'utf-8'))
            break

    def receive_message(self, sock_tcp:CustomSocket) -> None:
        ipaddr = get_host_ip()
        sock_tcp.bind((ipaddr, self.tcp_port))
        sock_tcp.listen()
        while True:
            conn, addr = sock_tcp.accept()
            if conn: 
                data = conn.recv(1024)
                conn.close()
                break 
        return data, addr
    
    ## trouver comment s'arranger ici là, c'est un peu relou comme situation 

    def set_socket(self, timeout:int) -> None:
        return self.confidant_set_socket(timeout)

    def send(self, message:str, target_ip:str) -> None:
        return self.send_message(message, target_ip)

    def listen(self, sock_tcp:CustomSocket) -> None: 
        return self.receive_message(sock_tcp)

    ## think about closing the sock when finished !!!

class Communicator(): 

##### SUPER IMPORTANT THINK OF CLOSING THE SOCKETS AFTER - maybe write a context manager version ?? will see
    def __init__(self, **kwargs) -> None:
        self.device:str = kwargs.get("device", "controller")
        self.rig:str = kwargs.get("rig", "triaxial_1")
        print(f"Created a Communicator instance on {self.device} for rig:{self.rig}") 

        # initial default behaviors - can be changes
        if self.device == "controller": 
            self.behavior = Broadcaster()
        elif self.device == "member":
            self.behavior = CrowdMember()
        else: 
            print("Undifined type of device")
            # later raise an error and/or ask to input the type of device and give choices 

    def change_behavior(self, behavior:str) -> None: 
        if behavior == self.behavior.__str__():
            print("self.behavior")
        elif behavior == "broadcaster": 
            self.behavior = Broadcaster()
            print(self.behavior)
        elif behavior == "crowdmember":  
            self.behavior = CrowdMember()
            print(self.behavior)
        elif behavior == "confidant": 
            self.behavior = Confidant()
            print(self.behavior)

    def set_socket(self, timeout:int = 10, info_set:bool = False) -> None:
        # TODO: write alternative info_set -> print_info flags to pring entry and closing info of the socket
        return self.behavior.set_socket(timeout, info_set)
         
    def send(self,  message:str, sock_udp:CustomSocket = None, target_ip:str = None, info_sent:bool = False) -> None:
        print("in the send function of communicator")
        # TODO: put some asserts in here to make sure that the sockets are given same for ip
        if isinstance(self.behavior, Confidant): 
            print("tcp sender")
            # assert is_valid_ip(target_ip)
            return self.behavior.send(message, target_ip)
        else:
            print("udp sender") 
            # assert isinstance(sock_udp, CustomSocket)
            return self.behavior.send(message, sock_udp, info_sent)

    def listen(self, sock_udp:CustomSocket = None, sock_tcp:CustomSocket = None, info_listen:bool = False) -> None:
        print("in the listen function of communicator")
        # TODO: put some asserts in here to make sure that the sockets 
        if isinstance(self.behavior, Confidant):
            print("tcp listener")
            # assert isinstance(sock_tcp, CustomSocket) 
            return self.behavior.listen(sock_tcp)
        else:
            print("udp listener")
            # assert isinstance(sock_udp, CustomSocket)  
            return self.behavior.listen(sock_udp, info_listen)

#############################################################################################################################################
## FUNCTIONS ################################################################################################################################
#############################################################################################################################################

## Get informations on machine ##############################################################################################################
############################################################################################################################################# 
 
def get_host_name() -> str: 
    """No very useful but might become useful, if not discard it

    Returns
    -------
    str
        _description_
    """
    return socket.gethostname()
    
def get_host_ip() -> str:
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
    
def get_mac_address() -> str:
    return getmac.get_mac_address()
    
## Network diagnostic #######################################################################################################################
############################################################################################################################################# 
    
def ping(target:str) -> bool:
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
        subprocess.check_output(["ping", param, "1", target], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False
        
def is_local_ip_address(host_ip:str) -> bool: 
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
        
def network_status(remote_server:str = "google.com") -> None:
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

    is_the_ip_local = is_local_ip_address(get_host_ip())
    is_internet_connected = ping(remote_server)

    # status_1 : Warning : Not on a network
    if not is_internet_connected and is_the_ip_local :
        warnings.warn("This device isn't connected to a network", stacklevel=2)
        
    # status_2 : Warning : No access to internet
    elif not is_internet_connected and not is_the_ip_local: 
        warnings.warn("No access to internet", stacklevel=2)

    # status_3 : Warning : Access to internet
    elif is_internet_connected and not is_the_ip_local:
        warnings.warn("Access to internet", stacklevel=2)
    
    # undifined configuration
    else:
        print("Undifined - the ip is the local one but access to internet")

## Create JSON ##############################################################################################################################
############################################################################################################################################# 

def create_json(command:str, arguments:dict) -> str:
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

def read_json(json_string:str) -> dict: 
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

## Check if the ip is valid #################################################################################################################
############################################################################################################################################# 

# TODO: check if these work fine 

def is_valid_ipv4(ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

def is_valid_ipv6(ip: str) -> bool:
    parts = ip.split(':')
    if len(parts) > 8:
        return False
    for part in parts:
        if not (1 <= len(part) <= 4) or not all(c in '0123456789abcdefABCDEF' for c in part):
            return False
    return True

def is_valid_ip(ip: str) -> bool:
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)

## Check if a port is occupied #################################################################################################################
############################################################################################################################################# 

def is_port_free(port: int) -> bool:
    if platform.system() == "Windows":
        command = f"netstat -ano | findstr :{port}"
    else:
        command = f"lsof -i :{port}"

    try:
        result = subprocess.check_output(command, shell=True)
        return False
    except subprocess.CalledProcessError:
        return True
    
## List of available ports that can be used see: https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
ports_candidates_for_TCP_protocol = [1645, 1646, 4944, 5000, 5500, 9600, 10000, 20000, 11100, 19788]
ports_candidates_for_UDP_protocol = [1965, 3001, 3128, 5070, 5678, 8006, 8008, 8010, 8089, 8448]

def get_free_port(candidates):
    result = []
    for port in candidates:
        if is_port_free(port):
            result.append(port)
    return result

#############################################################################################################################################
## MAIN #####################################################################################################################################
#############################################################################################################################################

if __name__ == "__main__": 
    # in the future write some tests
    # functions 
    print(get_host_name())
    print(get_host_ip())
    print(get_mac_address())
    print(ping("google.com")) # works with conn to internet
    print(ping(get_host_ip()))
    print(is_local_ip_address("127.0.0.1"))
    print(is_local_ip_address(get_host_ip()))
    network_status()
    print(type(create_json("ping", {"ipaddr":"127.0.0.1"})))
    print(type(read_json(create_json("ping", {"ipaddr":"127.0.0.1"}))))

    # classes 
    customsock = CustomSocket()
    print(isinstance(customsock, CustomSocket))
    
    com = Communicator()
    print(isinstance(com, Communicator))
    print(isinstance(com.behavior, Broadcaster)) #when on controller 
    com.change_behavior("crowdmember")
    print(isinstance(com.behavior, CrowdMember)) #when on member 
    com.change_behavior("confidant")
    print(isinstance(com.behavior, Confidant)) # specially for tcp

    # more tests of the methods


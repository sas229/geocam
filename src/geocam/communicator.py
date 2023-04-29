import socket 
import struct
import json 
import platform
import subprocess
import os
import warnings

# Needs to be changed: tcp_link, 

class Communicator(): 

    def __init__(self, device:str = 'controller', rig:str = 'txc1',  mcast_grp:str = '224.1.1.1', mcast_port:int = 9998, tcp_port:int = 47822): 
        print("Created a Communicator instance.")
        
        # constants - given byt he user 
        self.rig = rig
        self.mcast_grp = mcast_grp
        self.mcast_port = mcast_port
        self.tcp_port = tcp_port

        # constants - generated
        self.ip_address:str = self.get_host_ip()

    def tcp_link(self): 
        """
        - Create a tcp link for communication
        - This will then either run as a client or server 
        """
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ip_address, self.tcp_port))
        return sock_tcp
    
    def udp_multicast_link(self): # no sure if it works 
        """
        - Create a tcp link for communication
        - This will then either run as a client or server 
        """
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
        return sock_udp
    
    def get_router_name(self):
        # Get the hostname of the machine
        hostname = socket.gethostname()
        # Get the IP address associated with the hostname
        ip_address = socket.gethostbyname(hostname)
        # Get the router's IP address by removing the last digit of the IP address
        router_ip_address = ".".join(ip_address.split(".")[:-1]) + ".1"
        # Get the hostname associated with the router's IP address
        router_hostname = socket.gethostbyaddr(router_ip_address)[0]
        # Return the router's hostname
        return router_hostname

    def ping(self, host: str) -> bool:
        """

        Classical ping function - modified to not print the results in terminal

        Parameters
        ----------
        host : str
            ip address to ping - can be a website name

        Returns
        -------
        bool
            True if the ip is reached - False if not
        """
        param = '-n' if platform.system().lower()=='windows' else '-c'
        try:
            subprocess.check_output(["ping", param, "1", host], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False
        
    def get_host_ip(self) -> str:
        """_summary_
        Function to get the IP address of a device

        Returns
        -------
        str
            IP address of the device
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

        Remark
        -------
        Having a virtualization software on the machine might simulate a LAN as these sofwares emulate a GegE 
        """

        is_local_ip_address = self.is_local_ip_address(self.get_host_ip())
        is_internet_connected = self.ping(remote_server)

        # status_1 : Warning : Not on a network
        if not is_internet_connected and is_local_ip_address :
            warnings.warn("This device isn't connected to a network", stacklevel=2)

        # status_2 : Warning : No access to internet
        elif not is_internet_connected and not is_local_ip_address: 
            warnings.warn("No access to internet", stacklevel=2)
            print(f"Connected to to a router with no access to internet")

        # status_3 
        elif is_internet_connected and not is_local_ip_address:
            print(f"Connected to a router with access to internet")
        
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
    


## !! need to update the child classes    
#############################################################################################################################################
    
class Sender(Communicator):
    """
    - They should only be one type of sender: computers. 

    Args:
        Communicator (_type_): _description_
    """
    # def __init__(self, device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822):
    #     super().__init__(device, mcast_grp, mcast_port, tcp_port)
    #     self.receivers = {}
    #     self.sock_tcp = self.tcp_link()

    # def wait_for_answer_tcp(self): 
    #     self.sock_tcp.listen()
    #     number_of_found_receivers = len(self.receivers)

    #     try: 
    #         while number_of_found_receivers != self.number_of_receivers:        
    #             # event loop waiting for connection 
    #             while True:
    #                 conn, addr = self.sock_tcp.accept()
    #                 if conn: 
    #                     data = conn.recv(1024)
    #                     parsed_data = json.loads(data)
    #                     # print(f"received data:\n {json.dumps(parsed_data, indent=2)}")

    #                     dict_of_ip_addr_and_macaddr = parsed_data["content"]
    #                     name_of_the_raspberrypi = parsed_data["content"]["hostname"]
    #                     print(f'{name_of_the_raspberrypi} found at {addr}')

    #                     # updates
    #                     number_of_found_rpi += 1
    #                     rpi_dict = {name_of_the_raspberrypi:dict((key, dict_of_ip_addr_and_macaddr[key]) for key in ('ip_addr', 'mac_addr'))}
    #                     self.rpis_ids.update(rpi_dict)

    #                     # finishing up 
    #                     conn.close()
    #                     break

    #         # closing the tcp socket         
    #         sock_tcp.close() 
 
        # except Exception: 
        #     print("still to be coded")



class Receiver(Communicator): 
    """_summary_

    Args:
        Communicator (_type_): _description_
    """
    def __init__(self, device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822):
        super().__init__(device, mcast_grp, mcast_port, tcp_port)

##############################################################################################################################################
    
class ListeningRPi(Receiver): 
    def __init__(self, device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822):
        super().__init__(device, mcast_grp, mcast_port, tcp_port)

    def stream(self): 
        """
        - Stream video to a ip address
        """
        return

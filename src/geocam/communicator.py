import socket 
import struct
import json 
import platform
import subprocess
import os

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
        self.hostname = socket.gethostname()
        self.ipaddr = socket.gethostbyname(self.hostname)

    def tcp_link(self): 
        """
        - Create a tcp link for communication
        - This will then either run as a client or server 
        """
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.ipaddr, self.tcp_port))
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
        param += '-n' if platform.system().lower()=='windows' else '-c'
        try:
            subprocess.check_output(["ping", param, "1", host], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False
        
    def get_host_ip(self) -> str:
        """
        
        Function to get the IPv4 address of a device

        Returns
        -------
        str
            host ip address
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
        
    def network_status(self) -> str:
        """
        
        3 status possible: 
        - status_1: the device is connected to internet 
        - status_2: the device is not connected to any kind of network 
        - status_3: the device is connected either to a LAN or WLAN 

        Returns
        -------
        str
            status 1, 2 or 3 - see above 

        Remark
        ------
        Note that having a virtualization software on the machine might simulate a LAN

        """

        host_ip = self.get_host_ip()
        is_internet_connected = self.ping('google.com')

        if is_internet_connected: 
            return "status_1"
        
        elif host_ip.startswith('127.') or host_ip == socket.gethostbyname('localhost'):
            return "status_2"
        
        else: 
            return "status_3" 
            
    def _create_json(self): 
        """
        - Will be used to create JSON files
        """
        return 

## !! need to update the child classes    
#############################################################################################################################################
    
class Sender(Communicator):
    """
    - They should only be one type of sender: computers. 

    Args:
        Communicator (_type_): _description_
    """
    def __init__(self, device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822):
        super().__init__(device, mcast_grp, mcast_port, tcp_port)
        self.receivers = {}
        self.sock_tcp = self.tcp_link()

    def wait_for_answer_tcp(self): 
        self.sock_tcp.listen()
        number_of_found_receivers = len(self.receivers)

        try: 
            while number_of_found_receivers != self.number_of_receivers:        
                # event loop waiting for connection 
                while True:
                    conn, addr = self.sock_tcp.accept()
                    if conn: 
                        data = conn.recv(1024)
                        parsed_data = json.loads(data)
                        # print(f"received data:\n {json.dumps(parsed_data, indent=2)}")

                        dict_of_ip_addr_and_macaddr = parsed_data["content"]
                        name_of_the_raspberrypi = parsed_data["content"]["hostname"]
                        print(f'{name_of_the_raspberrypi} found at {addr}')

                        # updates
                        number_of_found_rpi += 1
                        rpi_dict = {name_of_the_raspberrypi:dict((key, dict_of_ip_addr_and_macaddr[key]) for key in ('ip_addr', 'mac_addr'))}
                        self.rpis_ids.update(rpi_dict)

                        # finishing up 
                        conn.close()
                        break

            # closing the tcp socket         
            sock_tcp.close() 
 
        except Exception: 
            print("still to be coded")



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

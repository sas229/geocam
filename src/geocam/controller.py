import logging
import networkscan
import fabric
from getpass4 import getpass
import ipaddress
import socket

log = logging.getLogger(__name__)

class Controller:

    def __init__(self):
        log.info("Created a Controller instance.")
        self._set_ssh_credentials()

    def find_cameras(self, id: str, network: str=None) -> None:
        # Scan network for valid IP addresses with devices.
        if network == None:
            ip = self._get_ip()
            mask = '255.255.255.0'
            address = ip + '/' + mask
            itf = ipaddress.ip_interface(address)
            network = itf.network
        log.info("Searching network: {network}".format(network=network))
        scan = networkscan.Networkscan(network)
        scan.run()

        # Check hostname of device.
        self.cameras_found = 0
        self.camera_ip = []
        for ip_addr in scan.list_of_hosts_found:
            found, name = self._check_hostname(ip_addr, id)
            if found:
                log.info("RPi camera found called {name} found at {ip_addr}".format(name=name, ip_addr=ip_addr))
                self.cameras_found += 1
                self.camera_ip.append(ip_addr)
        
        # If cameras are found, check control script.
        if self.cameras_found > 0:
            log.info("Checking control script is installed.")
        else:
            log.warning("No RPi cameras found on the network.")

    def _set_ssh_credentials(self):
        log.info("Input SSH credentials to use to connect to RPi cameras.")
        self.username = input('Username: ')
        self.password = getpass('Password: ')
        
    def _check_hostname(self, ip_addr: str, id: str) -> bool:
        # Try to connect to the device via SSH. If successful, get the hostname.
        try:
            result = fabric.Connection(host=ip_addr, connect_kwargs={"password": self.password}).run('hostname -s', hide=True)
            hostname = result.stdout
            if id in hostname:
                return True, hostname
            else:
                return False, "none"
        except Exception:
            return False, "none"
        
    def _get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Doesn't even have to be reachable.
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
        
if __name__ == "__main__": 
    test = Controller()
import getmac
import json
import logging
import os
import socket
import struct
import json
from time import sleep

# Initialise log at default settings.
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.debug("Initialised geocam log.")

# Create console handler and set level to debug.
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch.
ch.setFormatter(formatter)

# Add ch to logger.
log.addHandler(ch)

def get_hostname() -> str: 
    """
    Returns the hostname of the current machine.

    Returns
    -------
    str
        The hostname of the current machine.
    """
    host_name = socket.gethostname()

    # Logging the host_name before returning
    log.info("Current hostname: %s", host_name)

    return host_name

def get_ip_address() -> str:
    """
    Returns the IP address of the current machine.

    Returns
    -------
    str
        The hostname of the current machine.

    Raises
    ------
    OSError
        If the IP address could not be retreived.
    """  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Doesn't even have to be reachable.
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "none"
    finally:
        s.close()
    return ip

def get_mac_address() -> str:
    """
    Returns the MAC address of the current machine.

    Returns
    -------
    str
        The MAC address of the current machine.
    """
    mac_addr = getmac.get_mac_address()
    log.info("Current mac_addr: %s", mac_addr)
    return mac_addr

def stand_by_for_commands() -> None:
    # Wait until an Ip address is assigned, then update IP and MAC addresses.
    while get_ip_address() == "none":
        sleep(1)

    # Open a UDP socket and listen on the multicast group and port.
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind(('', MCAST_PORT)) 
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Listen for incoming commands.
    while True:
        try: 
            log.debug("Standing by for commands.")
            data, ip_addr = udp.recvfrom(1024)
            command = json.loads(data)
            execute(command, ip_addr)
        except Exception: 
            udp.close()
            log.info("UDP socket closed.")
    
def execute(command: str, ip_addr: str):
    print("Command recieved from {ip_addr}: {command}".format(command=command, ip_addr=ip_addr[0]))
    timeout = 3
    if command["command"] == "get_hostname_ip_mac":
        RPI_ADDR_AND_MAC = {"hostname":get_hostname(), "ip":get_ip_address(), "mac":get_mac_address()}
        json_message = json.dumps(RPI_ADDR_AND_MAC)
        try: 
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            sock_tcp.settimeout(timeout)
            sock_tcp.connect((ip_addr[0], TCP_PORT))
            log.debug("Successfully connected to {ip}:{port}".format(ip=ip_addr[0], port=TCP_PORT))
            sock_tcp.sendall(json_message.encode('utf-8'))
            log.debug("Message sent successfully.")
        except socket.timeout:
            log.debug("TCP socket timed out.")
        except Exception as e:
            log.error("Unknown error: {e}".format(e=e))

if __name__ == "__main__": 
    MCAST_GRP = '225.1.1.1'
    MCAST_PORT = 3179
    TCP_PORT = 1645 
    stand_by_for_commands()
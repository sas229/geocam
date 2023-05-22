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

import getmac
import json
import logging
import os
import platform
import subprocess

from geocam.communicator import *

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################
# see https://docs.python.org/3/library/logging.html for documentation on logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# create a file handler that logs the debug messages
file_handler = logging.FileHandler(f'{__file__[:-3]}.log', mode='w')
file_handler.setLevel(logging.DEBUG)

# create a stream handler to print the errors in console
stream_handler = logging.StreamHandler()

# format the handlers 
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

#############################################################################################################################################
## FUNCTIONS ################################################################################################################################
#############################################################################################################################################

## Get informations on machine ##############################################################################################################
############################################################################################################################################# 

# test up to date
def get_host_name() -> str: 
    """
    Returns the hostname of the current machine.

    Returns
    -------
    str
        The hostname of the current machine.
    """
    host_name = socket.gethostname()

    # Logging the host_name before returning
    logging.info("Current hostname: %s", host_name)

    return host_name

# test up to date be careful with the test from mac os  
def get_host_ip() -> str:
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
    host_ip = None

    if platform.system().lower() == 'windows':
        host_ip = socket.gethostbyname(socket.gethostname())
    elif platform.system().lower() == 'linux': 
        routes = json.loads(os.popen("ip -j -4 route").read())
        for r in routes:
            if r.get("dev") == "wlan0" and r.get("prefsrc"):
                host_ip = r['prefsrc']
                break 
    elif platform.system().lower() == 'darwin': 
        host_ip = os.popen("ipconfig getifaddr en0").read()

    if host_ip is None:
        raise OSError("Failed to retrieve the IP address.")
    logging.info("Current IP address: %s", host_ip)
    return host_ip 


def get_mac_address() -> str:
    """
    Returns the MAC address of the current machine.

    Returns
    -------
    str
        The MAC address of the current machine.
    """
    mac_addr = getmac.get_mac_address()
    logging.info("Current mac_addr: %s", mac_addr)
    return mac_addr

## Checks on IP address  ####################################################################################################################
############################################################################################################################################# 

def is_local_ip_address(host_ip:str) -> bool: 
    """
    Checks if the given IP address is a local address.

    Parameters
    ----------
    host_ip : str
        The IP address to check.

    Returns
    -------
    bool
        True if the IP address is a local address, False otherwise.
    """         
    if host_ip == host_ip.startswith('127.') or host_ip == socket.gethostbyname('localhost'):
        logging.info("IP address %s is a local address.", host_ip)
        return True
    else: 
        logging.info("IP address %s is not a local address.", host_ip)
        return False 

def is_valid_ipv4(ip: str) -> bool:
    """
    Checks if the given IPv4 address is valid.

    Parameters
    ----------
    ip : str
        The IPv4 address to check.

    Returns
    -------
    bool
        True if the IPv4 address is valid, False otherwise.

    """
    parts = ip.split('.')
    if len(parts) != 4:
        logging.info("Invalid IPv4 address: %s", ip)
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            logging.info("Invalid IPv4 address: %s", ip)
            return False
    logging.info("Valid IPv4 address: %s", ip)
    return True

def is_valid_ipv6(ip: str) -> bool:
    """
    Checks if the given IPv6 address is valid.

    Parameters
    ----------
    ip : str
        The IPv6 address to check.

    Returns
    -------
    bool
        True if the IPv6 address is valid, False otherwise.

    """
    parts = ip.split(':')
    if len(parts) > 8:
        logging.info("Invalid IPv6 address: %s", ip)
        return False
    for part in parts:
        if not (1 <= len(part) <= 4) or not all(c in '0123456789abcdefABCDEF' for c in part):
            logging.info("Invalid IPv6 address: %s", ip)
            return False
    logging.info("Valid IPv6 address: %s", ip)
    return True

def is_valid_ip(ip: str) -> bool:
    """
    Checks if the given IP address is valid (IPv4 or IPv6).

    Parameters
    ----------
    ip : str
        The IP address to check.

    Returns
    -------
    bool
        True if the IP address is valid (IPv4 or IPv6), False otherwise.

    """
    if is_valid_ipv4(ip) or is_valid_ipv6(ip):
        logging.info("Valid IP address: %s", ip)
        return True
    else:
        logging.info("Invalid IP address: %s", ip)
        return False
    
## Check if a port is occupied ##############################################################################################################
#############################################################################################################################################

def is_port_free(port: int) -> bool:
    """
    Checks if the given port is free.

    Parameters
    ----------
    port : int
        The port number to check.

    Returns
    -------
    bool
        True if the port is free, False otherwise.

    """
    if platform.system() == "Windows":
        command = f"netstat -ano | findstr :{port}"
    else:
        command = f"lsof -i :{port}"

    try:
        subprocess.check_output(command, shell=True)
        logging.info("Port %d is not free.", port)
        return False
    except subprocess.CalledProcessError:
        logging.info("Port %d is free.", port)
        return True

def get_free_port(candidates):
    """
    Finds and returns a list of free ports from the given candidates.

    Parameters
    ----------
    candidates : list
        A list of port numbers to check.

    Returns
    -------
    list
        A list of free port numbers.

    """
    result = []
    for port in candidates:
        if is_port_free(port):
            result.append(port)
    logging.info("Free ports: %s", result)
    return result

## Network diagnostic #######################################################################################################################
############################################################################################################################################# 
    
def ping(target:str) -> bool:
    """
    Pings the specified target and returns whether it is reachable or not.

    Parameters
    ----------
    target : str
        The target to ping.

    Returns
    -------
    bool
        True if the target is reachable, False otherwise.
    """          
    param = '-n' if platform.system().lower()=='windows' else '-c'
    try:
        subprocess.check_output(["ping", param, "1", target], stderr=subprocess.STDOUT)
        logging.info("Target %s is reachable.", target)
        return True
    except subprocess.CalledProcessError:
        logging.info("Target %s is not reachable.", target)
        return False
               
def network_status(remote_server:str = "google.com") -> int:
    """
    Checks the network status of the device.

    Parameters
    ----------
    remote_server : str, optional
        The remote server to ping for checking internet connectivity. Default is "google.com".

    Returns
    -------
    str
        The network status:
        - 0 if the device is not connected to a network.
        - -1 if the device is connected to a WLAN but has no internet access.
        - 1 if the device is connected to a WLAN and has internet access.

    Raises
    ------
    NotImplementedError
        If the IP address is local but there is access to the internet.

    """
    is_the_ip_local = is_local_ip_address(get_host_ip())
    is_internet_connected = ping(remote_server)

    if not is_internet_connected and is_the_ip_local:
        logging.warning("This device isn't connected to a network")
        return 0
    elif not is_internet_connected and not is_the_ip_local:
        logging.warning("On local network with no access to internet")
        return -1
    elif is_internet_connected and not is_the_ip_local:
        logging.warning("Access to internet")
        return 1
    else:
        raise NotImplementedError("Undefined - the IP is the local one but there is access to the internet")

## Create JSON ##############################################################################################################################
############################################################################################################################################# 

def create_json(source:str, content:dict) -> str:
    """
    Creates a JSON string from the given source and content.

    Parameters
    ----------
    source : str
        The source of the JSON data.
    content : dict
        The content of the JSON data.

    Returns
    -------
    str
        The JSON string representation of the source and content.

    """    
    _dict = {"source":source ,"content":content}
    json_string = json.dumps(_dict, indent=2)
    logging.info("Created JSON string: %s", json_string)
    return json_string

def read_json(json_string:str) -> dict: 
    """
    Reads a JSON string and returns a dictionary.

    Parameters
    ----------
    json_string : str
        The JSON string to read.

    Returns
    -------
    dict
        The dictionary representation of the JSON data.

    """
    data = json.loads(json_string)
    logging.info("Read JSON data: %s", data)
    return data 

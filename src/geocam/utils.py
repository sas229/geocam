from geocam.communicator import *

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
        
def network_status(remote_server:str = "google.com") -> str:
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
        return "no_network"
        
    # status_2 : Warning : No access to internet
    elif not is_internet_connected and not is_the_ip_local: 
        warnings.warn("No access to internet", stacklevel=2)
        return "wlan_and_no_internet"

    # status_3 : Warning : Access to internet
    elif is_internet_connected and not is_the_ip_local:
        warnings.warn("Access to internet", stacklevel=2)
        return "wlan_and_internet"
    
    # undifined configuration
    else:
        raise NotImplementedError("Undifined - the ip is the local one but access to internet")

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

## Check if a port is occupied ##############################################################################################################
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

## Connection variables #####################################################################################################################
############################################################################################################################################# 

def _change_mcast_grp(self, mcast_grp:str) -> None:
        warnings.warn("This will permanently change the mcast_grp address used by this instance of communicator.", stacklevel=2)
        answer = input("Do you want to continue? (y/n) ")
        if answer.lower() in ["y", "yes"]:
            self.behavior.MCAST_GRP = mcast_grp
        elif answer.lower() in ["n", "no"]:
            pass
        else:
            print("Invalid input.")

def _change_all_mcast_grps(self, mcast_grp:str) -> None:
    warnings.warn("This will permanently change the mcast_grp address used by all instances of communicators on this machine. Please make sure that this change is also made on all members of the mcast_grp.", stacklevel=2)
    answer = input("Do you want to continue? (y/n) ")
    if answer.lower() in ["y", "yes"]:
        Behavior.MCAST_GRP = mcast_grp
    elif answer.lower() in ["n", "no"]:
        pass
    else:
        print("Invalid input.")

def _change_all_mcast_ports(self, mcast_port:int) -> None:
    warnings.warn("This will permanently change the mcast_port used by all instances of communicators on this machine.", stacklevel=2)
    answer = input("Do you want to continue? (y/n) ")
    if answer.lower() in ["y", "yes"]:
        Behavior.MCAST_PORT = mcast_port
    elif answer.lower() in ["n", "no"]:
        pass
    else:
        print("Invalid input.")

def _change_all_tcp_ports(self, tcp_port:int) -> None:
    warnings.warn("This will permanently change the tcp_port used by all instances of communicators on this machine.", stacklevel=2)
    answer = input("Do you want to continue? (y/n) ")
    if answer.lower() in ["y", "yes"]:
        Behavior.TCP_PORT = tcp_port
    elif answer.lower() in ["n", "no"]:
        pass
    else:
        print("Invalid input.")
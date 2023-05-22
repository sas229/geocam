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

import logging
import socket
import struct
import time

from geocam.utils import get_host_ip
from geocam.utils import network_status
from typing import Optional, Tuple

#############################################################################################################################################
## SETTING UP THE LOGGER ####################################################################################################################
#############################################################################################################################################
# see https://docs.python.org/3/library/logging.html for documentation on logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
## CLASSES ##################################################################################################################################
#############################################################################################################################################

class Behavior():
    """
    Class representing behavior settings.

    Attributes
    ----------
    MCAST_GRP : str
        Multicast group IP address.
    MCAST_PORT : int
        Multicast group port number.
    TCP_PORT : int
        TCP port number.
        
    Methods
    -------
    __init__() -> None
        Initialize the Behavior object.
    __repr__() -> str
        Return a string representation of the object.
    __str__() -> str
        Return a human-readable string representation of the object.

    Returns
    -------
    str
        A string representation of the `Behavior` object.

    Notes
    -----
    - The string representation includes the class name.
    - Use the `__repr__()` method for a concise representation.
    - Use the `__str__()` method for a more descriptive representation.
    """
    MCAST_GRP:str = "232.18.125.68"
    
    MCAST_PORT:int = 1965
    
    TCP_PORT:int = 1645
    
    def __init__(self) -> None:
        """
        Initialize the Behavior object.

        Notes
        -----
        - This method logs the multicast group IP address, multicast group port number,
          and TCP port number at the DEBUG level.
        """
        logger.debug("Multicast group IPv4 address: %s", self.MCAST_GRP)
        logger.debug("Multicast group port number: %s", self.MCAST_PORT)
        logger.debug("TCP port number: %s", self.TCP_PORT)

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Returns
        -------
        str
            String representation of the object.
        """
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        """
        Return a human-readable string representation of the object.

        Returns
        -------
        str
            Human-readable string representation of the object.
        """
        return f"Instance of the {self.__class__.__name__} class"

class Leader(Behavior):
    """
    Class representing a leader with specific behavior settings.

    Methods
    -------
    __init__() -> None
        Initialize the Leader object.

    _set_socket(timeout: int = 10) -> socket.socket
        Set up and return a UDP socket for multicast transfer.

    _send(message: str = None, sock_udp: socket.socket = None) -> None
        Send a message via the UDP socket to the multicast group.

    _listen() -> None
        Raise NotImplementedError as this class is only meant to send requests.

    Inherits
    --------
    Behavior: A base class defining behavior settings.

    Attributes (inherited)
    ----------------------
    MCAST_GRP : str
        Multicast group IP address.
    MCAST_PORT : int
        Multicast group port number.
    TCP_PORT : int
        TCP port number.

    Raises
    ------
    NotImplementedError
        If _listen() method is called.

    Notes
    -----
    - The `Leader` class inherits behavior settings from the `Behavior` class.
    - It provides methods for setting up a UDP socket, sending messages, and raises an error when attempting to listen.
    - Specific log messages related to the behavior settings and operations are available in the implementation.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.debug(self.__str__())

    # test up to date
    def _set_socket(self, timeout:int = 10) -> socket.socket: 
        """
        Set up and return a UDP socket for multicast transfer.

        Parameters
        ----------
        timeout : int, optional
            Socket timeout value in seconds (default is 10).

        Returns
        -------
        socket.socket
            A UDP socket configured for multicast transfer.

        Notes
        -----
        - The method sets the IP_MULTICAST_TTL socket option to 2 and applies the timeout.
        """
        ttl = 2
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock_udp.settimeout(timeout)
        logger.info("UDP socket set up for multicast transfer to %s-%d", self.MCAST_GRP, self.MCAST_PORT)
        return sock_udp

    # no test written yet. TODO: have a better handling of the error when provided with wrong arguments 
    def _send(self, message:str = None, sock_udp:socket.socket = None) -> None:
        """
        Send a message via the UDP socket to the multicast group.

        Parameters
        ----------
        message : str, optional
            Message to be sent (default is None).
        sock_udp : socket.socket, optional
            UDP socket for sending the message (default is None).

        Returns
        -------
        None

        Notes
        -----
        - The method sends the provided message as bytes to the multicast group defined by MCAST_GRP and MCAST_PORT.
        - Still need to add error handling for when a message is not given
        """
        try:
            sock_udp.sendto(bytes(message, encoding="utf-8"), (self.MCAST_GRP, self.MCAST_PORT))
            logger.info('Leader sent "%s" to the multicast group', message)
        except Exception:
            logger.exception("An error occured")

    # test up to date
    def _listen(self) -> None: 
        """
        Raise NotImplementedError as this class is only meant to send requests.

        Returns
        -------
        None

        Raises
        ------
        NotImplementedError
            If the method is called, as listening is not available in the Leader class.

        Notes
        -----
        - This method should not be called for the Leader class, as it does not support listening.
        - Instead, the Leader class is designed for sending requests.
        """
        raise NotImplementedError(f"Listen method not available for {self.__class__.__name__}. This class is only supposed to send requests") 

class Agent(Behavior): 
    """
    A class representing an agent behavior.

    This class extends the Behavior class and provides additional methods for an agent's functionality.

    Methods
    -------
    __init__() -> None
        Initialize the Agent object.

    _set_socket(timeout=10)
        Set up and return a UDP socket for receiving multicast requests.

    _send()
        Not available for Agent. Raises NotImplementedError.

    _listen(sock_udp=None)
        Listen for incoming requests on the UDP socket and yield the received data and address.
        
    Inherits
    --------
    Behavior: A base class defining behavior settings.

    Attributes (inherited)
    ----------------------
    MCAST_GRP : str
        Multicast group IP address.
    MCAST_PORT : int
        Multicast group port number.
    TCP_PORT : int
        TCP port number.

    Raises
    ------
    NotImplementedError
        If _send() method is called.

    Notes
    -----
    - The _listen() method is a generator function that yields the received data and address indefinitely.
    - If a socket timeout occurs while listening, an exception is logged and the listenning is stopped.
    """
    
    def __init__(self) -> None:
        super().__init__()
        logger.debug(self.__str__())

    # test up to date
    def _set_socket(self, timeout:int = 10) -> socket.socket:
        """
        Set up and return a UDP socket for receiving multicast requests.

        Parameters
        ----------
        timeout : int, optional
            Socket timeout value in seconds (default is 10).

        Returns
        -------
        socket.socket
            A UDP socket configured for receiving multicast requests.

        Notes
        -----
        - The method binds the socket to the MCAST_PORT and sets IP_ADD_MEMBERSHIP socket option to receive multicast messages.
        """
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock_udp.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock_udp.settimeout(timeout)
        logger.info("UDP socket set up for multicast transfer on %s-%d", self.MCAST_GRP, self.MCAST_PORT)
        return sock_udp
    
    # test up to date 
    def _send(self) -> None:
        """
        Not available for Agent.

        Raises
        ------
        NotImplementedError
            This method is not available for Agent behavior.
        
        Notes
        -----
        - This method should not be called for the Agent class, as it does not support sending.
        - Instead, the Agent class is designed for receiving requests.
        """
        raise NotImplementedError(f"Send method not available for {self.__class__.__name__}. This class is only supposed to receive requests") 

    # test up to date: however still need to make some chanegs to the method 
    def _listen(self, sock_udp:socket.socket = None) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        """
        Listen for incoming requests on the UDP socket and yield the received data and address.

        Parameters
        ----------
        sock_udp : socket.socket, optional
            UDP socket for receiving requests (default is None).

        Yields
        ------
        Tuple[bytes, Tuple[str, int]]
            The received data and address as a tuple.

        Returns
        -------
        None
            If a socket timeout occurs while listening.

        Notes
        -----
        - This method is a generator function that yields the received data and address indefinitely.
        - If a socket timeout occurs while listening, an exception is logged.
        - must investigate what is up with the return (TODO) 
        """
        try:
            while True:
                try:
                    data, addr = sock_udp.recvfrom(1024)
                    yield data, addr
                    logger.info("Data received from %s: %r", addr, data)
                except socket.timeout:
                    logger.exception("Timeout occured")
                    """This return is suppose to be used in the listen function. However I don't understand why it does not beahve as expected. 
                    Could be because return and yield are not suppose to be used together: TODO: investigate"""
                    # TODO replace this return by a break 
                    return None
        except Exception: 
            logger.exception("An error occured")

class Collaborator(Behavior):
    """
    A class representing a collaborator behavior.

    This class extends the Behavior class and provides additional methods for a collaborator's functionality.

    Methods
    -------
    __init__() -> None
        Initialize the Collaborator object.

    _set_socket(timeout: int = 10) -> socket.socket:
        Set up and return a TCP socket for unicast transfer.

    _send(message: str, sock_tcp: socket.socket, target_ip: str) -> None:
        Send a message over a TCP socket to a specified target IP address.

    _listen(sock_tcp: socket.socket) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        Listen for incoming TCP connections and yield received data and address.
        
    Inherits
    --------
    Behavior: A base class defining behavior settings.

    Attributes (inherited)
    ----------------------
    MCAST_GRP : str
        Multicast group IP address.
    MCAST_PORT : int
        Multicast group port number.
    TCP_PORT : int
        TCP port number.

    Raises
    ------
    NotImplementedError
        If _send() method is called.

    Notes
    -----
    - The _listen() method is a generator function that yields the received data and address indefinitely.
    - If a socket timeout occurs while listening, an exception is logged and the listenning is stopped.
    """
    def __init__(self) -> None:
        super().__init__()
        logger.debug(self.__str__())

    # test up to date
    def _set_socket(self, timeout:int = 10) -> socket.socket:
        """
        Set up and return a TCP socket for unicast transfer.

        Parameters
        ----------
        timeout : int, optional
            Socket timeout value in seconds (default is 10).

        Returns
        -------
        socket.socket
            A TCP socket configured for unicast transfer.

        Notes
        -----
        - The method binds the socket to the local IP address and the TCP_PORT attribute.
        - It applies the specified timeout to the socket.
        """
        host_ip = get_host_ip()
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((host_ip, self.TCP_PORT))
        sock_tcp.settimeout(timeout)
        logger.info("UDP socket set up for unicast transfer on %s-%d", host_ip, self.TCP_PORT)
        return sock_tcp
    
    # test up to date. TODO: rethink the layout to make it that client can also listen and that servers can send info 
    # TODO this test can be better with more cases: test the network, test the error handlings
    def _send(self, message:str = None, sock_tcp:socket.socket = None, target_ip:str = None) -> None:
        """
        Send a message over a TCP socket to a specified target IP address.

        Parameters
        ----------
        message : str, optional
            The message to be sent (default is None).
        sock_tcp : socket.socket, optional 
            The TCP socket used for sending (default is None).
        target_ip : str, optional
            The IP address of the target recipient (default is None).

        Returns
        -------
        None

        Notes
        -----
        - If the device is not connected to a network, a critical error is logged.
        - The method attempts to establish a connection with the target IP address.
        - If the connection is refused, it retries after a 2-second delay.
        - If a timeout occurs, the exception is logged and the method exits.
        - The message is sent over the socket and the target address is logged.
        """
        target_address = (target_ip, self.TCP_PORT)

        if network_status() == 0:
            logger.critical("this device is not on a network")
            target_ip = "127.0.0.1"

        while True:
            try: 
                sock_tcp.connect(target_address)
            except ConnectionRefusedError:
                logger.exception("Connection refused, retrying in 2 seconds...")
                time.sleep(2)
                continue
            except TimeoutError:
                logger.exception("Timeout occured")
                break
            sock_tcp.sendall(bytes(message, 'utf-8'))
            logger.info("The message was sent to %s", target_address)
            break

    # test not up to date TODO: rethink the layout to make it that client can also listen and that servers can send info 
    def _listen(self, sock_tcp:socket.socket) -> Optional[Tuple[bytes, Tuple[str, int]]]: 
        """
        Listen for incoming TCP connections and yield received data and address.

        Parameters
        ----------
        sock_tcp : socket.socket
            The TCP socket used for listening.

        Yields
        ------
        Tuple[bytes, Tuple[str, int]]
            The received data and address as a tuple.

        Returns
        -------
        None
            If a socket timeout occurs while listening.

        Notes
        -----
        - This method sets the socket to listen for incoming connections.
        - It continuously accepts connections and receives data from the connected client.
        - If a socket timeout occurs while listening, an exception is logged.
        """
        sock_tcp.listen()
        while True:
            try: 
                conn, addr = sock_tcp.accept()
                data = conn.recv(1024)
                yield data, addr
            except socket.timeout:
                logger.exception("Timeout occured")
                """This return is suppose to be used in the listen function. However I don't understand why it does not beahve as expected. 
                Could be because return and yield are not suppose to be used together: TODO: investigate"""
                return None

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
        
        logger.info(f"Instantiated a {self}")

    def __str__(self) -> str:
        return f"Communicator class instance behaving like a {self.kind}"
    
    def __repr__(self) -> str:
        return f"Communicator(Communicator.{self.kind.upper()})"
    
    def change_behavior(self, new_kind:str) -> None: 
        if new_kind == self.kind:
            logger.info(f"Communicator already behaves like a {self.behavior}")
        else: 
            self.kind = new_kind
            if new_kind == Communicator.LEADER: 
                self.behavior = Leader()
                logger.info(f"Communicator behavior changed to: {self.behavior}")
            elif new_kind == Communicator.AGENT:  
                self.behavior = Agent()
                logger.info(f"Communicator behavior changed to: {self.behavior}")
            elif new_kind == Communicator.COLLABORATOR: 
                self.behavior = Collaborator()
                logger.info(f"Communicator behavior changed to: {self.behavior}")

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
        """         
        args = []
        if isinstance(self.behavior, Collaborator):
            args.extend([message, sock_tcp, target_ip])
        elif isinstance(self.behavior, Leader):
            args.extend([message, sock_udp])

        try: 
            self.behavior._send(*args)
        except NotImplementedError:
            logger.exception("NotImplementedError error occured")   

        # if isinstance(self.behavior, Collaborator): 
        #     self.behavior._send(message, sock_tcp, target_ip)
        # if isinstance(self.behavior, Leader):
        #     self.behavior._send(message, sock_udp)
        # else: 
        #     self.behavior._send()

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

        args = []
        if isinstance(self.behavior, Collaborator):
            args.extend([sock_tcp])
            sock_name = sock_tcp.getsockname()
        elif isinstance(self.behavior, Agent):
            args.extend([sock_udp])
            assert isinstance(sock_udp, socket.socket)
            sock_name = sock_udp.getsockname()

        logger.debug(f"Start listening at {sock_name}")
        logger.info("Start listening... ")
        for data, addr in self.behavior._listen(*args):
            if data is None:
                """This is suppose to use the return from _listen. However it does not it does not beahve as expected. 
                Could be because return and yield are not suppose to be used together: TODO: investigate"""
                print("Timeout occurred")
            else:
                logger.debug(f"Received data: {data} from {addr}")
                logger.info(f"Received data: \n{data}")
                yield data, addr


        # if isinstance(self.behavior, Collaborator):
        #     return self.behavior._listen(sock_tcp)
        # if isinstance(self.behavior, Agent): 
        #     return self.behavior._listen(sock_udp)
        # else: 
        #     return self.behavior._listen()

# #############################################################################################################################################
# ## MAIN #####################################################################################################################################
# #############################################################################################################################################

def main():
    pass

if __name__ == "__main__": 
    main()















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


class Communicator(): 

    def __init__(self, device:str = 'controller',  mcast_grp:str = '224.1.1.1', mcast_port:int = 9998, tcp_port:int = 47822): 
        print("Created a Communicator instance.")

    def tcp_link(self): 
        """
        - Create a tcp link for communication
        - This will then either run as a client or server 
        """
        return
    
    def udp_multicast_link(self): 
        """
        - Create a tcp link for communication
        - This will then either run as a client or server 
        """
        return
    
    def ping(self): 
        """
        - Send a ping on the lan
        """
        return
        
    def _create_json(self): 
        """
        - Will be used to create JSON files
        """
        return 
    
#############################################################################################################################################
    
class Sender(Communicator):
    """
    - They should only be one type of sender: computers. 

    Args:
        Communicator (_type_): _description_
    """
    def __init__(self, device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822):
        super().__init__(device, mcast_grp, mcast_port, tcp_port)

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

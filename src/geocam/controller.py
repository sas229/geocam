"""

This module is used for control of the rigs 


"""

from geocam import communicator 

class Controller:

    def __init__(self):
        print("Created a Controller instance.")
        com = communicator.Communicator()
        com.network_status()

    def check_available_network_interfaces(self):
        """
        - Should check the type of network - and if a connection to internet is available or not
        - Raise the necessary error if need be
        """

        return
    
    def choose_the_rig(self):
        """
        - Should allow the user to choose one of the rigs in the lab - which triaxial 
        - Ideally, since the number of rigs and there number of pis/cameras will be known, it could ba a good idea to set these infos here 
        """
        return 

    def identify_the_pis(self):
        """
        - Create a connection with all the pis allocated to a rig
        - Check the number of pis known for the rig 
        - Raise the necessary error if need be  
        """
        return
    
    def configure_cameras(self): 
        """
        - Configuration and contols of the camera, must dive in the picamera2-mannual for the pi cameras 
        - Would be different rules for other cameras - we could make a child class to control each type of cameras that'll be used. Configure would then be specific to each camera
        - will communicate with the module used for a given type of camera 
        - To be reflected on 
        """
        return
    
    def focus(self):
        """
        - Start the focus process
        - Calls functions from the calibration module 
        """ 
        return
    
    def aquire_images(self):
        """
        - Start taking the pictures 
        - The way to retrieve them should be discussed
        """
        return

if __name__ == "__main__": 
    controller = Controller()
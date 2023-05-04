"""
:Name: controller
:Description: This module is used for control of the rigs 
:Date: 2023-05-03
:Version: 0.0.1
:Author(s): Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane

"""


from geocam import communicator 
import socket 
import traceback

class Controller:

    def __init__(self):
        print("Created a Controller instance.")

        print("[INITIALISATION]")
        # initialisation: setup 
        self.sender = communicator.Sender()
        self.receiver = communicator.Receiver()

        # initialisation: RPis informations
        self.number_of_members = 0

        # initialisation: Controller information
        self.ipaddr = self.sender.get_host_ip()

        print("[CHECKS]")
        # checks : network 
        self.sender.network_status()
        self.receiver.network_status()

    def choose_the_rig(self):
        """
        - Should allow the user to choose one of the rigs in the lab - which triaxial 
        - Ideally, since the number of rigs and there number of pis/cameras will be known, it could ba a good idea to set these infos here 
        """
        return 
    
#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
#############################################################################################################################################

    # VERSION 1 FUNCTION TO INITIALIZE CONTACT 

    def count_member_of_mcastgrp(self, timeout:int = 3) -> None:
        # creating and sending the request to the mcastgrp - see send_to_all for more details about the mcastgrp
        request = self.sender._create_json("ping", "None")
        self.sender.send_to_all(request)
        # set a listening udp socket for responses 
        sock_udp = self.receiver.socket_for_broadcast_listenning()
        
        with sock_udp as s:
            s.settimeout(timeout) 
            try: 
                while True:
                    data, addr = s.recvfrom(1024)
                    self.number_of_members += 1
                    print(f"Received data {data}")
                    return data 
            
            except TimeoutError:
                print(f"Waited {timeout} s and no responce")

            except Exception:
                traceback.print_exc()
            
            finally: 
                print(f"No rpis found") if self.number_of_members == 0 else print(f"Found {self.number_of_members} rpis")

    def get_ip_and_mac_addrr_of_the_members(self, timeout:float = 10) -> None:
        # creating and sending the request to the mcastgrp - see send_to_all for more details about the mcastgrp
        request = self.sender._create_json("id", {"id_address":self.ipaddr})
        self.sender.send_to_all(request)
        # set a listening tcp socket for "private" responses 
        sock_tcp = self.receiver.socket_for_one_to_one_listening()

        found_members = 0
        with sock_tcp as s: 
            try: 
                while found_members != self.number_of_members:
                    while True:
                        conn, addr = sock_tcp.accept()
                        if conn: 
                            data = conn.recv(1024)
                            print(f"Received data {data}")
                            found_members += 1
                            return data 

            except TimeoutError:
                print(f"Waited {timeout} s and no responce")

            except Exception:
                traceback.print_exc()

            finally:
                if found_members == self.number_of_members:
                    print(f"All members identified") 
                else:
                    print(f"{self.number_of_members - found_members} missing")

    # VERSION 2 TO INITIALIZE THE CONTACT WITH THE PIS

    def count_member_of_mcastgrp2(self, timeout:int = 3) -> None:
        # creating and sending the request to the mcastgrp - see send_to_all for more details about the mcastgrp
        request = self.sender._create_json("ping", "None")
        self.sender.send_to_all(request) #OHTER NAME send_to_all_members
        # set a listening udp socket for responses 
        registration_socket_udp = self.receiver.socket_for_broadcast_listenning() #OTHER NAME socket_listenning_to_group / socket_listenning_to_all_members_at_once 
        
        with registration_socket_udp as s:
            try: 
                number_of_registrants = self.receiver.listen_to_all(s, timeout) #OTHER NAME listen_to_all_members 
                self.number_of_members = number_of_registrants
            
            except TimeoutError:
                print(f"We waited {timeout}s and no responce came")

            except Exception:
                traceback.print_exc()
            
            finally: 
                print(f"No new members") if self.number_of_members == 0 else print(f"We have {self.number_of_members} new members")

    def get_ip_and_mac_addrr_of_the_members2(self, timeout:float = 10) -> None: # variation - proposition 
        # creating and sending the request to the mcastgrp - see send_to_all for more details about the mcastgrp
        request = self.sender._create_json("id", {"id_address":self.ipaddr})
        self.sender.send_to_all(request)
        # set a listening tcp socket for "private" responses 
        sock_tcp = self.receiver.socket_for_one_to_one_listening()

        found_members = 0
        with sock_tcp as s: 
            try: 
                while found_members != self.number_of_members:
                    data = self.receiver.listen_to_one2(s, timeout)

            except TimeoutError:
                print(f"Waited {timeout} s and no responce")

            except Exception:
                traceback.print_exc()

            finally:
                if found_members == self.number_of_members:
                    print(f"All members identified") 
                else:
                    print(f"{self.number_of_members - found_members} missing")

#############################################################################################################################################
## IN PROGRESS NOW ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##########
###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########

    # VERSION 3 TO INITIALIZE THE CONTACT WITH THE PIS

    def count_member_of_mcastgrp3(self, timeout:int = 3) -> None:
        ## [SENDING]
        # creating and sending the request to the mcastgrp - see send_to_all for more details about the mcastgrp

        # informations about the members 
        members_os_name = "posix" # should modify to be an input of the user 
        members_plateform = "Linux" # should modify to be an input of the user too 
        prefix_of_host_name = "rp" # rp1 for example 

        # request 
        command = "registration" 
        arguments = {"os_name":members_os_name, 
                     "plateform":members_plateform, 
                     "prefix":prefix_of_host_name}
        request = self.sender._create_json(command, arguments)

        # sending the request to the mcast group members 
        self.sender.send_to_all(request) #OHTER NAME send_to_all_members

        ## [RECEIVING]
        # set a listening udp socket for responses 
        registration_socket_udp = self.receiver.socket_for_broadcast_listenning() #OTHER NAME socket_listenning_to_group / socket_listenning_to_all_members_at_once 
        
        with registration_socket_udp as s:
            try: 
                number_of_registrants = self.receiver.listen_to_all_members_for_registration(s, timeout) #titemout should be small  
                self.number_of_members = number_of_registrants
            
            except TimeoutError:
                print(f"We waited {timeout}s and no responce came")

            except Exception:
                traceback.print_exc()
            
            finally: 
                print(f"No new members") if self.number_of_members == 0 else print(f"We have {self.number_of_members} new members")

###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########
## IN PROGRESS NOW ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##########
#############################################################################################################################################


    # BUNDLE THE CONTACT FUNCTION IN ONE 

    def find_the_raspberry_pis(self) -> str:
        print("[find_the_raspberry_pis]")
        self.count_member_of_mcastgrp()
        self.get_ip_and_mac_addrr_of_the_members2()
        return "Success"
    
#############################################################################################################################################
## IN PROGRESS ###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!##############
#############################################################################################################################################


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
    print(controller.find_the_raspberry_pis())
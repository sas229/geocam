# import subprocess
# import platform

# def is_port_free(port: int) -> bool:
#     if platform.system() == "Windows":
#         command = f"netstat -ano | findstr :{port}"
#     else:
#         command = f"lsof -i :{port}"

#     try:
#         result = subprocess.check_output(command, shell=True)
#         return False
#     except subprocess.CalledProcessError:
#         return True
    
# ## List of available ports that can be used see: https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
# ports_candidates_for_TCP_protocol = [1645, 1646, 4944, 5000, 5500, 9600, 10000, 20000, 11100, 19788]
# ports_candidates_for_UDP_protocol = [1965, 3001, 3128, 5070, 5678, 8006, 8008, 8010, 8089, 8448]

# def get_free_port(candidates):
#     result = []
#     for port in candidates:
#         if is_port_free(port):
#             result.append(port)
#     return result

# free_ports_for_TCP_protocol = get_free_port(ports_candidates_for_TCP_protocol)
# print(free_ports_for_TCP_protocol)

# free_ports_for_UDP_protocol = get_free_port(ports_candidates_for_UDP_protocol)
# print(free_ports_for_UDP_protocol)


# ## NEW CLASSES

# class Collaborator():
#     def listen(self):
#         pass

#     def send(self):
#         pass

# class Broadcaster(Collaborator):
#     def listen(self):
#         raise NotImplementedError("Subclasses of CollaboratorBehavior must implement listen method")

#     def send(self):
#         # implementation for broadcast behavior
#         pass

# class ListenBehavior(Collaborator):
#     def listen(self):
#         # implementation for listen behavior
#         pass

# class Communicator():
#     def __init__(self, behavior: Collaborator):
#         self.behavior = behavior

#     def listen(self):
#         self.behavior.listen()

#     def send(self):
#         self.behavior.send()

from utils import *

ports_candidates_for_TCP_protocol = [1645, 1646, 4944, 5000, 5500, 9600, 10000, 20000, 11100, 19788]


print(get_free_port(ports_candidates_for_TCP_protocol))
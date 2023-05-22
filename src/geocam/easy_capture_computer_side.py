from geocam.communicator import Communicator

communicator = Communicator(Communicator.COLLABORATOR)
with communicator.set_socket(timeout=30) as sock_tcp:
    for data, addr in communicator.listen(sock_tcp=sock_tcp):
        print(data, addr)
    
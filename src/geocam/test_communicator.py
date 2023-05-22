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

import pytest 
import platform
import socket

import geocam.communicator as communicator
from unittest.mock import patch, MagicMock


## fixtures #################################################################################################################################
#############################################################################################################################################

@pytest.fixture
def leader():
    # Create a Collaborator instance for testing
    return communicator.Leader()

@pytest.fixture
def agent():
    # Create a Collaborator instance for testing
    return communicator.Agent()

@pytest.fixture
def collaborator():
    # Create a Collaborator instance for testing
    return communicator.Collaborator()

## set_socket tests  ########################################################################################################################
#############################################################################################################################################

def _is_bound_udp_socket(sock: object) -> bool:
    """
    Check if a socket is a UDP socket with the correct settings and is bound.

    Parameters
    ----------
    sock : object
        The object to check.

    Returns
    -------
    bool
        True if the socket has the correct settings and is bound, False otherwise.
    """
    if not isinstance(sock, socket.socket):
        return False
    if sock.type != socket.SOCK_DGRAM:
        return False
    if sock.proto != socket.IPPROTO_UDP:
        return False
    try:
        sockname = sock.getsockname()
    except OSError:
        return False
    return True

def _is_bound_tcp_socket(sock: object) -> bool:
    """
    Check if a socket is a TCP socket with the correct settings and is bound.

    Parameters
    ----------
    sock : object
        The object to check.

    Returns
    -------
    bool
        True if the socket has the correct settings and is bound, False otherwise.
    """
    if not isinstance(sock, socket.socket):
        return False
    if sock.type != socket.SOCK_STREAM:
        return False
    try:
        sockname = sock.getsockname()
    except OSError:
        return False
    return True

def test_leader_set_socket(leader):
    # Test sending socket
    sock_udp_send = leader._set_socket(timeout=10)
    assert _is_bound_udp_socket(sock_udp_send) is False
    assert sock_udp_send.gettimeout() == 10
    # assert sock_udp_send.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL) == 2

def test_agent_set_socket(agent):    
    # Test listening socket
    sock_udp_listen = agent._set_socket(timeout=5)
    assert _is_bound_udp_socket(sock_udp_listen) is True
    assert sock_udp_listen.gettimeout() == 5
    # assert sock_udp_listen.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL) == 2

def test_collaborator_set_socket(collaborator):
    sock = collaborator._set_socket(timeout=5)
    assert _is_bound_tcp_socket(sock)
    assert sock.gettimeout() == 5

## send tests  ##############################################################################################################################
#############################################################################################################################################

def test_leader_send(leader):
    # No test to write for now as it only uses the sendto method of the socket already set
    pass 

def test_agent_send(agent):
    with pytest.raises(NotImplementedError):
        agent._send()

def test_collaborator_send(collaborator):
    # TODO this test can be better with more cases: test the network, test the error handlings
    sock = MagicMock(spec=socket.socket)
    message = "Hello, multicast!"
    target_ip = "192.168.0.1"
    collaborator._send(message, sock, target_ip)
    sock.connect.assert_called_once_with((target_ip, collaborator.TCP_PORT))
    sock.sendall.assert_called_once_with(bytes(message, 'utf-8'))

## listen tests  ############################################################################################################################
#############################################################################################################################################

def test_leader_listen(leader):
    with pytest.raises(NotImplementedError):
        leader._listen()

def test_agent_listen(agent):
    # test if the function yields as expected 
    sock = MagicMock(spec=socket.socket)
    data = b"Hello, multicast!"
    addr = ("127.0.0.1", 12345)
    sock.recvfrom.return_value = (data, addr)
    gen = agent._listen(sock_udp=sock)
    assert next(gen) == (data, addr)

def test_agent_listen_timeout(agent):
    # test if the yielding stops when a timout occurs
    sock = MagicMock(spec=socket.socket)
    sock.recvfrom.side_effect = socket.timeout("Timeout occurred")
    gen = agent._listen(sock_udp=sock)
    with pytest.raises(StopIteration):
        next(gen)

def test_agent_listen_error(agent):
    # test if the yielding stops when any other errors occurs 
    sock = MagicMock(spec=socket.socket)
    sock.recvfrom.side_effect = Exception("An error occurred")
    gen = agent._listen(sock_udp=sock)
    with pytest.raises(StopIteration):
        next(gen)

def test_collaborator_listen(collaborator):
    # Test to be written after having gotten more experience with test 
    pass

def test_collaborator_listen_timeout(collaborator):
    # Test to be written after having gotten more experience with test
    pass

## Communicator tests  ######################################################################################################################
#############################################################################################################################################


def test_create_communicator():
    # test if the behavior is set to what is expected
    pass

def test_change_behavior():
    # test a change of the behavior 
    pass 

def test_set_soket():
    # test that the call function is the right one 
    # make sure that everything happen as expected 
    # also the expection, the one i wrote but more importantly the ones raised by the sockets 
    pass

def test_send():
    # test that the call function is the right one 
    # make sure that everything happen as expected 
    # also the expection, the one i wrote but more importantly the ones raised by the sockets 
    pass

def test_listen():
    # test that the called function is the right one 
    # mock the behavior af receive 
    # also work with the execptions 
    pass 


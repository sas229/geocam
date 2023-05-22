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
import os
import json

from unittest.mock import patch, MagicMock
from geocam.utils import *

## get_host_name tests  #####################################################################################################################
############################################################################################################################################# 

@pytest.mark.parametrize("hostname", ["test-machine"])
def test_get_host_name(hostname):
    with patch('socket.gethostname', return_value=hostname):
        result = get_host_name()
        assert result == hostname

## get_host_ip tests  #######################################################################################################################
############################################################################################################################################# 

@pytest.mark.parametrize("expected_ip", ["192.168.0.1", "172.20.10.2"])
def test_get_host_ip_windows(monkeypatch, expected_ip):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(socket, "gethostbyname", lambda _: expected_ip)

    actual_ip = get_host_ip()
    
    assert actual_ip == expected_ip, f"Expected IP: {expected_ip}, Actual IP: {actual_ip}"

@pytest.mark.parametrize("routes, expected_ip", [([{"dev": "wlan0", "prefsrc": "192.168.0.1"}], "192.168.0.1")])
def test_get_host_ip_linux(monkeypatch, routes, expected_ip):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(os, "popen", lambda _: type('DummyProcess', (object,), {'read': lambda self: json.dumps(routes)})()) # reproduces the behavior of os.popen("ip -j -4 route").read()

    actual_ip = get_host_ip()
    
    assert actual_ip == expected_ip, f"Expected IP: {expected_ip}, Actual IP: {actual_ip}"

# this test should be tested on a macos machine
@pytest.mark.parametrize("expected_ip", ["192.168.0.1", "172.20.10.2"])
def test_get_host_ip_macos(monkeypatch, expected_ip):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(os, "popen", lambda _: type('DummyProcess', (object,), {'read': lambda self: expected_ip})()) # reproduces the behavior of os.popen("ip -j -4 route").read()

    actual_ip = get_host_ip()

    assert actual_ip == expected_ip, f"Expected IP: {expected_ip}, Actual IP: {actual_ip}"

def test_get_host_ip_ip_unavailable(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(socket, "gethostbyname", lambda _: None)

    with pytest.raises(OSError):
        get_host_ip()

def test_get_host_ip_unsupported_platform(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Solaris")

    with pytest.raises(OSError):
        get_host_ip()

## get_mac_address tests  ###################################################################################################################
############################################################################################################################################# 

def test_get_mac_address():
    mock_get_mac_address = MagicMock(return_value="00:11:22:33:44:55")
    with patch('getmac.get_mac_address', mock_get_mac_address):
        result = get_mac_address()
        assert result == "00:11:22:33:44:55"

## ip checks functions tests ################################################################################################################
############################################################################################################################################# 

def test_is_local_ip_address():
    # Test for a local IP address (loopback)
    local_ip_address = '127.0.0.1'
    assert is_local_ip_address(local_ip_address) is True

    # Test for a local IP address (localhost)
    localhost_ip_address = socket.gethostbyname('localhost')
    assert is_local_ip_address(localhost_ip_address) is True

    # Test for a non-local IP address
    non_local_ip_address = '192.168.0.1'
    assert is_local_ip_address(non_local_ip_address) is False

def test_is_valid_ipv4():
    # Test for a valid IPv4 address
    valid_ipv4 = "192.168.0.1"
    assert is_valid_ipv4(valid_ipv4) is True

    # Test for an invalid IPv4 address
    invalid_ipv4 = "256.0.0.1"
    assert is_valid_ipv4(invalid_ipv4) is False

def test_is_valid_ipv6():
    # Test for a valid IPv6 address
    valid_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    assert is_valid_ipv6(valid_ipv6) is True

    # Test for an invalid IPv6 address
    invalid_ipv6 = "2001:0db8:85a3::8a2e:0370:7334:abcd:1234"
    assert is_valid_ipv6(invalid_ipv6) is False

def test_is_valid_ip():
    # Test for a valid IP address (IPv4)
    valid_ip = "192.168.0.1"
    assert is_valid_ip(valid_ip) is True

    # Test for a valid IP address (IPv6)
    valid_ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    assert is_valid_ip(valid_ip) is True

    # Test for an invalid IP address
    invalid_ip = "256.0.0.1"
    assert is_valid_ip(invalid_ip) is False

## port availability tests ##################################################################################################################
############################################################################################################################################# 

def test_is_port_free():
    # Find an available port dynamically
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    assert is_port_free(port) is True

    # Test for a used port (assuming port 80 is in use)
    used_port = 80
    assert is_port_free(used_port) is False

def test_get_free_port():
    # careful: there is a small chance for this test to stop working randomly as the ports appened to candidates might get used just before the assertion 

    # Test for finding free ports from candidates
    candidates = []
    for _ in range(2):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        candidates.append(port)
    expected_free_ports = candidates
    assert get_free_port(candidates) == expected_free_ports

    # Test for empty candidates list
    empty_candidates = []
    assert get_free_port(empty_candidates) == []

## network function #########################################################################################################################
############################################################################################################################################# 

def test_ping():
    reachable_target = "google.com"
    try:
        # Check if the computer has internet connectivity by resolving a domain name
        socket.gethostbyname("google.com")
        # If internet: test for a reachable target
        assert ping(reachable_target) is True
        # If internet: test for an unreachable target
        unreachable_target = "nonexistenthost"
        assert ping(unreachable_target) is False
    except socket.gaierror:
        # If no internet: the previously reachable target, should not be anymore
        assert ping(reachable_target) is False

def test_network_status():
    try:
        # Check if the computer has internet connectivity by resolving a domain name
        socket.gethostbyname("google.com")
        # If internet: test for WLAN connection with internet access
        assert network_status(remote_server="google.com") == 1

        # check for the last case -> there is internet but the ip is local 
        if socket.gethostbyname(socket.gethostname()).startswith("127."):
            with pytest.raises(NotImplementedError):
                network_status()

    except socket.gaierror:
        # If no internet
        try: 
            # Test if the ip is the local one 
            assert socket.gethostbyname('localhost').startswith("127.")
            # then the machine is not on a network
            assert network_status(remote_server="google.com") == 0
        except AssertionError:
            # If the ip is not the local one the machine is on a local network 
            assert network_status(remote_server="google.com") == -1

## Create JSON tests ########################################################################################################################
############################################################################################################################################# 


def test_create_json():
    # Test for creating a JSON string
    source = "example"
    content = {"name": "John", "age": 30}
    _dict = {"source":source ,"content":content}
    expected_json = json.dumps(_dict, indent=2)
    assert create_json(source, content) == expected_json

def test_read_json():
    # Test for reading a JSON string
    source = "example"
    content = {"name": "John", "age": 30}
    _dict = {"source":source ,"content":content}
    json_string = json.dumps(_dict, indent=2)
    expected_data = {"source": "example", "content": {"name": "John", "age": 30}}
    assert read_json(json_string) == expected_data



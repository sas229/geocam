# RECEIVER

import socket
import struct

group = '224.1.1.1'
port = 1695

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', port))
          
mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.settimeout(10)

while True:
    try: 
        data, addr = sock.recvfrom(1024)
        print(f"Received message from {addr}: {data.decode()}")
    except TimeoutError:
        print(TimeoutError)
        break
    except Exception:
        break
    finally:
        sock.close()
    
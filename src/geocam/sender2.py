
import socket 
import time

sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_tcp.settimeout(10)

while True:
    try: 
        sock_tcp.connect(("172.20.10.2", 1645))
    except ConnectionRefusedError:
        print("Connection refused, retrying in 2 seconds...")
        time.sleep(2)
        continue
    except TimeoutError:
        print(f"exited after timeout")
        break
    sock_tcp.sendall(bytes('test', 'utf-8'))
    sock_tcp.close()
    print("Finally !!!")
    break


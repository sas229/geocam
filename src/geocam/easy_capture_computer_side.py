import socket 
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(20)

server_address = ('', 1645)
sock.bind(server_address)

sock.listen(1)

while True:
    # Wait for a connection
    print('Waiting for a connection...')
    connection, client_address = sock.accept()

    try:
        # Receive the image size
        image_size_data = connection.recv(4)
        image_size = struct.unpack('!I', image_size_data)[0]

        # Receive the image data
        image_data = b''
        while len(image_data) < image_size:
            data = connection.recv(image_size - len(image_data))
            print("data", data)
            if not data:
                break
            image_data += data
        print("image_data", image_data)
    except TimeoutError:
        connection.close()
    # finally:
    #     # Clean up the connection
    #     connection.close()
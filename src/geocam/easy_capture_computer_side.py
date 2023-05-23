import socket 
import struct
import traceback

from PIL import Image

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(20)

server_address = ('', 1645)
sock.bind(server_address)

sock.listen(1)

name = "image{:03d}.jpg"
image_num = 0
while True:
    # Wait for a connection
    print('Waiting for a connection...')
    connection, client_address = sock.accept()
    print('Connection established !')
    try:
        # Receive the image size
        image_size_data = connection.recv(4)
        if len(image_size_data) != 4:
            print("Error: Incomplete or incorrect data received.")
        else:
            image_size = struct.unpack('!I', image_size_data)[0]
        # image_size = struct.unpack('!I', image_size_data)[0]

        # Receive the image data
        image_data = b''
        
        while len(image_data) < image_size:
            data = connection.recv(image_size - len(image_data))
            print("data", data)
            if not data:
                break
            image_data += data
            
        with Image.open(data) as image:
            image.save(name.format(image_num))

        image_num += 1

        # print("image_data", image_data)
    
    except KeyboardInterrupt:
        print('Key board Interrupted')

    except TimeoutError:
        print('Timeout')

    except Exception as e:
        traceback.print_exc()
        
    finally:
        connection.close()


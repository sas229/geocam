import socket 
import struct
import traceback
import time
import io

from PIL import Image

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(20)

server_address = ('172.20.10.2', 1645)
sock.bind(server_address)

sock.listen()

name = "image{:03d}.jpg"
image_num = 0

print('Waiting for a connection...')
connection, client_address = sock.accept()
print('Connection established !')

while True:
    try:
        # Receive the image size
        print('Waiting for data')
        current_time = time.time()
        image_size_data = connection.recv(4)
        current_time2 = time.time()
        waited_time = current_time2 - current_time
        print("Waited %s seconds", waited_time)
        print(type(image_size_data))
        if len(image_size_data) != 4:
            print(len(image_size_data))
            print("Error: Incomplete or incorrect data received.")
        else:
            image_size = struct.unpack('!I', image_size_data)[0]
            print("horay!!")
            print()
        # image_size = struct.unpack('!I', image_size_data)[0]

        # Receive the image data
        image_data = b''
        
        while len(image_data) < image_size:
            data = connection.recv(image_size - len(image_data))
            # print("data", data)
            if not data:
                break
            image_data += data
        
        print(len(image_data))
        byte_stream = io.BytesIO(image_data)

        with Image.open(byte_stream) as image:
            image.save(name.format(image_num))

        image_num += 1
        byte_stream.close()

        # print("image_data", image_data)
        if not data:
            break
    
    except KeyboardInterrupt:
        print('Key board Interrupted')
        connection.close()

    except TimeoutError:
        print('Timeout')
        connection.close()

    except Exception as e:
        traceback.print_exc()
        break
        


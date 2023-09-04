import getmac
import json
import logging
import socket
import struct
import json
from time import sleep
import threading
from queue import Queue
from picamera2 import Picamera2
import base64

# Initialise log at default settings.
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.debug("Initialised geocam log.")

# Create console handler and set level to debug.
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch.
ch.setFormatter(formatter)

# Add ch to logger.
log.addHandler(ch)

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/stream.mjpg')
            self.end_headers()
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Camera: 
    # Network settings.
    MCAST_GRP = '225.1.1.1'
    MCAST_PORT = 3179
    TCP_PORT = 1645

    def __init__(self):
        log.debug("Created a Camera instance.")        

        # TCP connection.
        self.TCP_connected = False
        self.thread_running = threading.Event()
        self.thread_running.set()
        self.buffer = Queue()

        # Camera configuration.
        self.camera = Picamera2()

        self.camera.configure(self.camera.create_video_configuration(main={"size": (1280, 960)}))
        output = StreamingOutput()
        self.camera.start_recording(JpegEncoder(), FileOutput(output))
        
        # self.camera_config = self.camera.create_still_configuration()
        # self.camera.configure(self.camera_config)
        # self.camera.start()

        # Standby for commands.
        self._stand_by_for_commands()

    def __del__(self):
        self._close_TCP_thread()
        log.debug("Deleted a Camera instance.")

    def _get_hostname(self) -> str: 
        """
        Returns the hostname of the current machine.

        Returns
        -------
        str
            The hostname of the current machine.
        """
        host_name = socket.gethostname()

        # Logging the host_name before returning
        log.info("Current hostname: %s", host_name)

        return host_name

    def _get_ip_address(self) -> str:
        """
        Returns the IP address of the current machine.

        Returns
        -------
        str
            The hostname of the current machine.

        Raises
        ------
        OSError
            If the IP address could not be retreived.
        """  
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Doesn't even have to be reachable.
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "none"
        finally:
            s.close()
        return ip

    def _get_mac_address(self) -> str:
        """
        Returns the MAC address of the current machine.

        Returns
        -------
        str
            The MAC address of the current machine.
        """
        mac_addr = getmac.get_mac_address()
        log.info("Current mac_addr: %s", mac_addr)
        return mac_addr

    def _open_TCP_thread(self, thread_running: threading.Event, buffer: Queue):
        log.debug("Opening TCP socket and listening on IP address {ip} port {port}.".format(ip=self.ip, port=self.TCP_PORT))
        TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCP_socket.bind((self.ip, self.TCP_PORT))
        TCP_socket.listen()
        while thread_running.is_set():
            log.debug("Waiting for geocam client to connect.")
            connection, client_address = TCP_socket.accept()
            log.debug("Connected to geocam client at {client_address}.".format(client_address=client_address))
            self.TCP_connected = True
            while self.TCP_connected:
                message = self.buffer.get()
                self.buffer.task_done()
                try:
                    connection.sendall(message.encode('utf-8'))
                    log.debug("Sent message.")
                except Exception:
                    self.TCP_connected = False
                    connection.close()
                    log.error("Failed to send message.")
        TCP_socket.close()

    def _close_TCP_thread(self):
        log.debug("Closing TCP thread.")
        self.thread_running.clear()
        self.TCP_thread.join()

    def _preview_server(self):
        print("Starting preview server.")
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()

    def _stand_by_for_commands(self) -> None:
        # Wait until an IP address is assigned, then update IP and MAC addresses.
        log.debug("Waiting for network connection.")
        while self._get_ip_address() == "none":
            sleep(1)
        self.ip = self._get_ip_address()

        # Open a UDP socket and listen on the multicast group and port.
        log.debug("Opening UDP socket on IP address {ip} port {port}.".format(ip=self.ip, port=self.MCAST_PORT))
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', self.MCAST_PORT)) 
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Open a TCP socket for sending images.
        self.TCP_thread = threading.Thread(target=self._open_TCP_thread, args=(self.thread_running, self.buffer,))
        self.TCP_thread.start()

        # Open the preview thread and start server.
        self.preview_thread = threading.Thread(target=self._preview_server)
        self.preview_thread.start()

        # Listen for incoming commands on UDP.
        while True:
            try: 
                log.debug("Standing by for commands.")
                data, ip_addr = self.udp_socket.recvfrom(1024)
                command = json.loads(data)
                self._execute(command, ip_addr)
            except Exception: 
                pass
    
    def _capture_image(self, filename: str) -> None:
        filepath = "images/" + filename + ".jpg"
        self.camera.capture_file(filepath, format="jpeg")

    def _execute(self, command: dict, ip_addr: str):
        log.debug("Command recieved from {ip_addr}: {command}".format(command=command, ip_addr=ip_addr[0]))
        if command["command"] == "get_hostname_ip_mac":
            self.RPI_ADDR_AND_MAC = {"hostname":self._get_hostname(), "ip":self._get_ip_address(), "mac":self._get_mac_address()}
            message = {"response": self.RPI_ADDR_AND_MAC}
            json_message = json.dumps(message)
            if self.TCP_connected:
                self.buffer.put(json_message)
        elif command["command"] == "start_preview":
            if command["camera"] == self._get_hostname():
                print("Starting preview server...")
        elif command["command"] == "start_preview":
            if command["camera"] == self._get_hostname():
                print("Stopping preview server...")
                # self._capture_image("preview")
                # log.debug("Opening preview image in binary...")
                # preview = open("images/preview.jpg", "rb").read()
                # message = {"preview": base64.b64encode(preview)}
                # log.debug("Dumping to json...")
                # json_message = json.dumps(message)
                # log.debug("Captured preview image.")
                # if self.TCP_connected:
                #     self.buffer.put(json_message)
                #     log.debug("Sent preview image via TCP.")

if __name__ == "__main__": 
    camera = Camera()
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import logging
import socket
import struct
import json
import time
import threading
import os
from picamera2 import Picamera2
import io
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # This is a new client.
            # Add an entry for it in the self.events dict.
            # Each entry has two elements, a threading.Event() and a timestamp.
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].is_set():
                # If this client's event is not set, then set it
                # also updates the last set timestamp to now.
                event[0].set()
                event[1] = now
            else:
                # If the client's event is already set, it means the client
                # did not process a previous frame.
                # If the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it.
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # Background thread that reads frames from camera.
    frame = None  # Current frame is stored here by background thread.
    last_access = 0  # Time of last client access to the camera.
    event = CameraEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # Start background frame thread.
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # Wait until first frame is available.
            BaseCamera.event.wait()

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # Wait for a signal from the camera thread.
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()  # Send signal to clients.
            time.sleep(0)

class Camera(BaseCamera):

    def __init__(self):
        super(Camera, self).__init__()
        self.camera = Picamera2()
        self.config = self.camera.create_still_configuration()
        self.camera.cofigure(self.config)
        self.camera.start()
        time.sleep(2)

    @staticmethod
    def frames(self):   
        frame = io.BytesIO()
        while True:
            frame.seek(0)
            self.camera.capture_file(frame, format='jpeg')
            frame.seek(0)
            yield frame.getvalue()

    # @staticmethod
    # def frames():
    #     with Picamera2() as camera:
    #         config = camera.create_still_configuration()
    #         camera.configure(config)
    #         camera.start()
    #         time.sleep(2)
    #         frame = io.BytesIO()
    #         while True:
    #             frame.seek(0)
    #             camera.capture_file(frame, format='jpeg')
    #             frame.seek(0)
    #             yield frame.getvalue()

    def update_controls(self, setting):
        print(setting)

# Disable werkzeug logging.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app and serve static Vue SPA.
app = Flask(__name__)
CORS(app)
host = "0.0.0.0"
port = 8002
debug = False
options = None

# Network settings.
MCAST_GRP = '225.1.1.1'
MCAST_PORT = 3179
TCP_PORT = 1645

# Create camera instance.
camera = Camera()

def gen():
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/preview')
def preview():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/updateControls', methods=['POST'])
def update_controls():
    if request.method == 'POST':
        data = request.json
        try:
            for key, value in data.items():
                camera.update_controls({key: value})
        except Exception:
            log.error("Unsuccessfully attempted to update camera settings.")
        return jsonify({"success": True})

def capture_frame():
    with open("test.jpg", "wb") as image_file:
        # Write bytes image to file.
        image_file.write(camera.frame)

def listen_on_UDP():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', MCAST_PORT)) 
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Listen for incoming commands on UDP.
    while True:
        try: 
            log.debug("Standing by for commands.")
            data, ip_addr = udp_socket.recvfrom(1024)
            command = json.loads(data)
            log.debug("Command {command} received from {ip_addr} on UDP.".format(command=command, ip_addr=ip_addr))
            if command["command"] == "captureFrame":
                capture_frame()
        except Exception: 
            pass

if __name__ == "__main__":
    UDP_thread = threading.Thread(target=listen_on_UDP)
    UDP_thread.start()
    app.run(host, port, debug, options)
    
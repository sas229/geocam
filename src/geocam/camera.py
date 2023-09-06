from flask import Flask, Response
from flask_cors import CORS
import logging
import socket
import struct
import json
import time
import threading
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
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until first frame is available
            BaseCamera.event.wait()

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # wait for a signal from the camera thread
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
            BaseCamera.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        BaseCamera.thread = None

class Camera(BaseCamera):
    """An emulated camera implementation that streams a repeated sequence of
    files 1.jpg, 2.jpg and 3.jpg at a rate of one frame per second."""
    imgs = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]
    previewOn = False

    @staticmethod
    def frames():
        while True:
            yield Camera.imgs[int(time.time()) % 3]
            time.sleep(1)

# Disable werkzeug logging.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app and serve static Vue SPA.
app = Flask(__name__)
CORS(app)
host = "0.0.0.0"
port = 8000
debug = False
options = None

# Network settings.
MCAST_GRP = '225.1.1.1'
MCAST_PORT = 3179
TCP_PORT = 1645

previewOn = False
frame = None

# Create camera instance.
camera = Camera()

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/previewOff")
def preview_off():
    camera.previewOn = False
    print("Stream turned off!")
    return "Stream turned off!"

def gen():
    yield b'--frame\r\n'
    camera.previewOn = True
    while True and camera.previewOn:
        frame = camera.get_frame()
        print("Yielding frame.")
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/preview')
def preview():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_UDP():
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
            print("Command {command} received from {ip_addr} on UDP.".format(command=command, ip_addr=ip_addr))
            if command["command"] == "previewOff":
                preview_off()
        except Exception: 
            pass

if __name__ == "__main__":
    UDP_thread = threading.Thread(target=run_UDP)
    UDP_thread.start()
    app.run(host, port, debug, options)
    
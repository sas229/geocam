from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import webbrowser
from threading import Timer
import geocam as gc
from PIL import Image
import logging

# Disable werkzeug logging.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app and serve static Vue SPA.
app = Flask(__name__, static_folder = "./../frontend/dist/assets", template_folder = "./../frontend/dist")
CORS(app)
host = "0.0.0.0"
port = 8001
debug = False
options = None

# Camera controller.
controller = gc.controller.Controller()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image')
def image():
    image = Image.open(r'test.jpg')
    yield Response(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(image) + b'\r\n', mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/findCameras', methods=['POST'])
def findCameras():
    if request.method == 'POST':
        data = request.json
        id = data['username']
        password = data['password']
        cameras = controller.find_cameras(id=id, password=password)
        return jsonify(cameras)

def open_browser():
      webbrowser.open_new_tab("http://{host}:{port}".format(host=host, port=port))

def run():
    # Run Flask server.
    Timer(1, open_browser).start()
    app.run(host, port, debug, options)

if __name__ == '__main__':
    run()
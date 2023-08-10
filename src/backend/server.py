from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_cors import CORS
import webbrowser
import geocam as gc
import logging
from time import time, sleep

# Disable werkzeug logging.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app and serve static Vue SPA.
# app = Flask(__name__, static_folder = "./../frontend/dist/assets", template_folder = "./../frontend/dist")
app = Flask(__name__)
CORS(app)
host = "0.0.0.0"
port = 8001
debug = False
options = None

frames = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

# Camera controller.
controller = gc.controller.Controller()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview')
def preview():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/setPreviewCamera', methods=['POST'])
def setPreviewCamera():
    if request.method == 'POST':
        data = request.json
        if data['previewCamera'] != "":
            controller._set_preview_camera(data['previewCamera'])
            controller._set_preview_status(True)
        elif data['previewCamera'] == "":
            controller._set_preview_camera("")
            controller._set_preview_status(False)
        return jsonify({"success": True})

def generate():
    i = 0
    while True:
        img = frames[i]
        i = (i + 1) % 3
        sleep(0.1)
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(img) + b'\r\n'

@app.route('/image')
def image():
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/findCameras', methods=['POST'])
def findCameras():
    if request.method == 'POST':
        data = request.json
        id = data['username']
        password = data['password']
        cameras = controller.find_cameras(id=id, password=password)
        return jsonify(cameras)

@app.route('/logMessage', methods=['GET'])
def logMessage():
    if request.method == 'GET':
        if len(controller.frontend_log_messages) > 0:
            message = controller.frontend_log_messages.pop()
        else:
            message = ""
        response = {"logMessage": message}
        return jsonify(response)

def open_browser():
      webbrowser.open_new_tab("http://{host}:{port}".format(host=host, port=port))

def run():
    # Run Flask server.
    # Timer(1, open_browser).start()
    app.run(host, port, debug, options)

if __name__ == '__main__':
    run()
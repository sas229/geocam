from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import webbrowser
import geocam as gc
import logging
from threading import Timer

# Disable werkzeug logging.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app and serve static Vue SPA.
app = Flask(__name__, static_folder = "./../frontend/dist/assets", template_folder = "./../frontend/dist")
# app = Flask(__name__)
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

@app.route('/preview')
def preview():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/image')
def image():
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

def generate():
    while True:
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + controller._get_preview_image() + b'\r\n'

@app.route('/setPreviewCamera', methods=['POST'])
def setPreviewCamera():
    if request.method == 'POST':
        data = request.json
        camera = data["previewCamera"]
        if camera != "":
            success = controller._set_preview_camera(camera, True)
        elif camera == "":
            success = controller._set_preview_camera(controller.preview_camera, False)
        return jsonify({"success": success})

@app.route('/findCameras', methods=['POST'])
def findCameras():
    if request.method == 'POST':
        data = request.json
        id = data['id']
        password = data['password']
        cameras = controller.find_cameras(id=id, password=password)
        return jsonify(cameras)

@app.route('/loadConfiguration', methods=['POST'])
def loadConfiguration():
    if request.method == 'POST':
        data = request.json
        configuration = data["configuration"]
        id = data["id"]
        password = data["password"]
        cameras = controller.load_configuration(configuration=configuration, id=id, password=password)
        return jsonify(cameras)

@app.route('/clearConfiguration', methods=['POST'])
def clearConfiguration():
    if request.method == 'POST':
        data = request.json
        configuration = data["configuration"]
        id = data["id"]
        password = data["password"]
        cameras = controller.clear_configuration(configuration=configuration, id=id, password=password)
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
    # Run Flask server and open app in browser.
    Timer(1, open_browser).start()
    app.run(host, port, debug, options)

if __name__ == '__main__':
    run()
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
app = Flask(__name__, static_folder = "./../frontend/app/assets", template_folder = "./../frontend/app")
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

@app.route('/getConfiguration', methods=['GET'])
def getConfiguration():
    if request.method == 'GET':
        configuration = controller.cameras
        print(configuration)
        return jsonify(configuration)

@app.route('/captureImages', methods=['POST'])
def captureImages():
    data = request.json
    name = data['name']
    number = data['number']
    interval = data['interval']
    recover = data['recover']
    success = controller.capture_images(name, number, interval, recover)
    response = {"success": success}
    return jsonify(response)

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
    
@app.route('/cameraResponse', methods=['POST'])
def cameraResponse():
    if request.method == 'POST':
        message = request.json
        controller.message_buffer.put(message)
        response = {"success": True}
        return jsonify(response)

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
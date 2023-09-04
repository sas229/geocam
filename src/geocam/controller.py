import concurrent.futures
from fabric import Connection
import geocam as gc
import geocam.dependencies as deps
# import backend.server as server
import getmac
from getpass4 import getpass
from importlib import resources as impresources
import ipaddress
import json
import logging
import networkscan
import socket
import threading
import time
from queue import Queue
import sys
import os
from time import sleep
import copy
import base64

# Initialise log at default settings.
level = logging.INFO
gc.log.initialise(level)
logging.getLogger('paramiko').setLevel(logging.FATAL)
log = logging.getLogger(__name__)
log.debug("Initialised geocam log.")

MCAST_GRP = '225.1.1.1'
MCAST_PORT = 3179
TCP_PORT = 1645

frames = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

class Controller:

    def __init__(self, configuration: str=None, password: str=None):
        self.log_message = "Initialising Controller instance."
        self.frontend_log_messages = []
        log.debug(self.log_message)
        self.ip = self._get_ip()
        self.cameras = {}
        self.preview_camera = ""
        self.waiting_for_preview = True
        self.i = 0
        self.log_message = ""
        if configuration is not None:
            c = open(configuration, 'r')
            self.cameras = json.load(c)
            self.id = configuration.rsplit( ".", 1 )[ 0 ]
            self.username = self.id
        if password is not None:
            self.password = password
            
        # Dependencies.
        self.camera_control_script = (impresources.files(gc) / 'camera.py')
        self.launch_script = (impresources.files(gc) / 'launch.py')
        self.lib2to3_name = 'python3-lib2to3_3.9.2-1_all.deb'
        self.lib2to3_file = (impresources.files(deps) / 'python3-lib2to3_3.9.2-1_all.deb')
        self.distutils_name = 'python3-distutils_3.9.2-1_all.deb'
        self.distutils_file = (impresources.files(deps) / 'python3-distutils_3.9.2-1_all.deb')
        self.pip_pyz = (impresources.files(deps) / 'pip.pyz')
        self.getmac_wheel_name = 'getmac-0.9.4-py2.py3-none-any.whl'
        self.getmac_wheel = (impresources.files(deps) / 'getmac-0.9.4-py2.py3-none-any.whl')

        # Required packages.
        self.required_packages = [
            'getmac',
            'picamera2',
        ]
        
        # Create UDP multicast socket for sending messages.
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        # Camera control thread storage.
        self.threads = []
        self.threads_running = threading.Event()
        self.threads_running.set()
        self.message_buffer = Queue()

        # If a configuration file is provided, check the cameras are ready.
        if configuration is not None:
            found_all_cameras = self._check_status()
            # If any camera is not found, perform a network scan to update the configuration.
            if not found_all_cameras:
                self.find_cameras(id=self.id, password=self.password)

    def __del__(self):
        self.log_message = "Stopping camera threads."
        log.debug(self.log_message)
        self._close_TCP_connections()
        self.log_message = "Deleted Controller instance."
        log.debug(self.log_message)

    def load_configuration(self, configuration: dict, id: str, password: str) -> dict:
        self.log_message = "Loading configuration."
        log.debug(self.log_message)
        self.cameras = configuration
        self.id = id
        self.username = password
        self._check_status()
        return self.cameras
    
    def clear_configuration(self, configuration: dict, id: str, password: str) -> dict:
        self.log_message = "Clearing configuration."
        self.cameras = configuration
        self.id = id
        self.username = password
        return self.cameras

    def capture_images(self, number: int=1, interval: float=0.0, recover: bool=True):
        # Send the command. Do this in a loop here with timing controlled by the controller.
        # command = {"command": "capture", "args": {"number": number, "interval": interval, "recover": recover}}
        # self._send_command(command)
        self.log_message = "Capturing images."
        log.info(self.log_message)

    def reboot_cameras(self):
        for camera in self.cameras:
            ip_addr = self.cameras[camera]['ip']
            self._reboot_camera(ip_addr)

    def find_cameras(self, id: str, network: str=None, password: str=None) -> dict:
        # Frontend log messages.
        self.frontend_log_messages = []

        # SSH credentials.
        self.id = id
        self.username = self.id
        self.password = password
        if  self.password == None:
            self._set_ssh_credentials()

        # Close any open TCP connections.
        self._close_TCP_connections()

        # Scan network for valid IP addresses with devices.
        if network == None:
            mask = '255.255.255.0'
            address = self.ip + '/' + mask
            itf = ipaddress.ip_interface(address)
            network = itf.network
        self.log_message = "Searching network: {network}".format(network=network)
        self.frontend_log_messages.append(self.log_message)
        log.info(self.log_message)
        scan = networkscan.Networkscan(network)
        scan.run()

        # Check hostname of devices using ThreadPool.
        self.cameras = {}
        results = []
        hostname = ""
        ip = ""
        mac = ""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for ip_addr in scan.list_of_hosts_found:
                self.log_message = "Checking IP address: {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.debug(self.log_message)
                results.append(executor.submit(self._check_hostname, ip_addr, id))
            for future in concurrent.futures.as_completed(results):
                found = future.result()[0]
                hostname = future.result()[1]
                ip = future.result()[2]
                if found:
                    mac = getmac.get_mac_address(ip=ip)
                    self.cameras.update({hostname: {"ip": ip, "mac": mac, "ready": False, "tcp": False}})
                    self.log_message = "RPi camera called {name} found at {ip} with MAC address: {mac}".format(name=hostname, ip=ip, mac=mac)
                    self.frontend_log_messages.append(self.log_message)
                    log.info(self.log_message)
    
        # If cameras are found, check control script and packages using ThreadPool.
        if len(self.cameras) > 0:
            log.debug("Checking control script is installed.")
            results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for camera in self.cameras:
                    ip_addr = self.cameras[camera]["ip"]
                    results.append(executor.submit(self._check_RPi, ip_addr))
                for future in concurrent.futures.as_completed(results):
                    ready = future.result()[0]
                    ip = future.result()[1]
                    if ready:
                        ready = True
                        self.log_message ="Camera ready for acquisiton at {ip}".format(ip=ip)
                        self.frontend_log_messages.append(self.log_message)
                        log.info(self.log_message)
                    else:
                        ready = False
                        self.log_message = "Camera not ready for acquisition at {ip}".format(ip=ip)
                        log.warning(self.log_message)
                    self.cameras[camera]["ready"] = ready

            #Check status of cameras communications.
            self._check_status()
            self._close_TCP_connections()
            return self.cameras
        else:
            self.log_message = "No RPi cameras found on the network."
            self.frontend_log_messages.append(self.log_message)
            log.warning(self.log_message)
            return self.cameras

    def save_configuration(self) -> None:
        filename = self.id + ".json"
        if len(self.cameras) == 0:
            self.log_message = "No cameras found. No configuration to save."
            log.warning(self.log_message)
            return
        self.log_message = "Saving configuration to {filename}".format(filename=filename)
        log.debug(self.log_message)
        with open(filename, 'w') as outfile:
            json.dump(self.cameras, outfile, indent=4, sort_keys=True)
        self.log_message = "Saved configuration to {filename}".format(filename=filename)
        log.info(self.log_message)

    def restart_cameras(self):
        self.log_message = "Restarting all cameras."
        log.info(self.log_message)
        if len(self.cameras) == 0:
            self.log_message = "No cameras found. Run find_cameras() or pass in a configuration."
            log.warning(self.log_message)
            return
        for camera in self.cameras:
            ip = self.cameras[camera]["ip"]
            self._run_launch_script(ip)
            self.log_message = "Restarted camera at {ip}".format(ip=ip)
            log.info(self.log_message)
        time.sleep(1)

    def _set_preview_camera(self, camera: str, status: bool) -> bool:
        try:
            self.preview_camera = camera
            if status:
                cmd = {"command": "start_preview", "camera": self.preview_camera}
                self.log_message = "Started preview on {camera}".format(camera=self.preview_camera)
            else:
                cmd = {"command": "stop_preview", "camera": self.preview_camera}
                self.log_message = "Stopped preview on {camera}".format(camera=self.preview_camera)
            log.debug(self.log_message)
            self._send_command(cmd)
            return True
        except Exception:
            log.error("Failed to set preview camera status.")
            return False

    def _get_preview_image(self) -> bytearray():
        if self.preview_status:
            cmd = {"command": "get_preview", "camera": self.preview_camera}
            self._send_command(cmd)
            sleep(0.1)
            preview_location = "images/preview.jpg"
            preview_destination = "images/" + self.preview_camera + "/preview.jpg"
            self._recover_image(self.cameras[self.preview_camera]["ip"], preview_location, preview_destination)
            self.preview_image = open(preview_destination, "rb").read()
            return bytearray(self.preview_image)
        else:
            sleep(0.1)
            return bytearray()

    def _check_status(self) -> bool:
        # Open TCP connection for each camera in a separate thread.
        found_all_cameras = False
        self.log_message = "Opening TCP connection to cameras."
        self.frontend_log_messages.append(self.log_message)
        log.info(self.log_message)
        self.threads_running.set()
        for camera in self.cameras:
            self.cameras[camera]["tcp"] = False     # Set the TCP flag to False so that we check the TCP connection.
            thread = threading.Thread(target=self._open_TCP_connection, args=(self.threads_running, self.cameras[camera],))
            thread.setDaemon(True)
            thread.start()
            self.threads.append(thread)

        # Send command via UDP to get MAC address of found devices and await response on TCP.
        self.log_message = "Sending UDP command to get MAC addresses."
        log.debug(self.log_message)
        cmd = {"command": "get_hostname_ip_mac"}
        self.tcp_connections = 0
        timeout = 30.0
        start_time = time.time()
        elapsed_time = 0.0
        while elapsed_time < timeout and self.tcp_connections < len(self.cameras):
            elapsed_time = time.time() - start_time
            self._send_command(cmd)
            time.sleep(1)
            while not self.message_buffer.empty():
                message = self.message_buffer.get()
                hostname = message["response"]["hostname"]
                if self.cameras[hostname]["tcp"] == False:
                    ip_addr = self.cameras[hostname]["ip"]
                    self.cameras[hostname]["tcp"] = True    # TCP connection working so set flag True.
                    self.cameras[hostname]["ready"] = self._check_camera_running(ip_addr) # Check camera.
                    self.tcp_connections += 1
                    self.log_message = "Camera at {ip} is ready for acquisition via TCP".format(ip=ip_addr)
                    self.frontend_log_messages.append(self.log_message)
                    log.info(self.log_message) 

        # Check all cameras have been found.
        found_all_cameras = True
        for camera in self.cameras:
            if self.cameras[camera]["tcp"] == False:
                found_all_cameras = False
                break
        
        return found_all_cameras

    def _open_TCP_connection(self, thread_running, camera: dict) -> None:
        # Open TCP client connection to camera.
        ip = camera["ip"]
        self.log_message = "Opening TCP connection to camera at {ip}".format(ip=ip)
        self.frontend_log_messages.append(self.log_message)
        log.debug(self.log_message)
        TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        self.log_message = "Trying to connect to camera at {ip}".format(ip=ip)
        self.frontend_log_messages.append(self.log_message)
        log.info(self.log_message)
        start_time = time.time()
        elapsed_time = 0.0
        timeout = 20.0
        while elapsed_time < timeout and not connected and thread_running.is_set():
            try:
                TCP_socket.connect((ip, TCP_PORT))
                self.log_message = "Connected to camera via TCP on {ip}:{port}".format(ip=ip, port = TCP_PORT)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
                connected = True
                start_time = time.time()
            except Exception:
                time.sleep(1)

            if connected:
                self.log_message = "Waiting for response via TCP from camera at {ip}".format(ip=ip)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
            while connected and thread_running.is_set():
                data = TCP_socket.recv(1024)
                message = data.decode('utf-8')
                if message == "":
                    connected = False
                    self.log_message = "TCP connection closed by camera at {ip}".format(ip=ip)
                    self.frontend_log_messages.append(self.log_message)
                    log.warning(self.log_message)
                else:
                    try:
                        message = json.loads(message)
                        if "response" in message:
                            self.message_buffer.put(message)
                            connected = False
                        if "image" in message:
                            self.log_message = "Saving image..."
                            log.debug(self.log_message)
                            # Save image to file.
                        if "preview" in message:
                            self.log_message = "Receiving preview image..."
                            log.debug(self.log_message)
                            self.preview_image = copy.deepcopy(base64.b64decode(message["preview"]))
                            self.waiting_for_preview = False
                    except Exception:
                        print(Exception)
                        pass
            elapsed_time = time.time() - start_time
        TCP_socket.close()

    def _close_TCP_connections(self) -> None:
        # Close TCP connections to cameras.
        self.threads_running.clear()

    def _send_command(self, command: str) -> None:
        try: 
            json_command = json.dumps(command, indent=2)
            self.udp_socket.sendto(bytes(json_command, 'utf-8'), (MCAST_GRP, MCAST_PORT))
        except Exception as e: 
            log.error(e.with_traceback())

    def _check_RPi(self, ip_addr: str) -> bool | str:
        installed = self._check_camera_control_script(ip_addr)
        if not installed:
            # Raspberry Pi hasn't been used as a camera before.
            log.warning("Checking RPi OS on {ip_addr}".format(ip_addr=ip_addr))
            self.frontend_log_messages.append(self.log_message)
            self._check_python_packages(ip_addr)
            self._install_control_script(ip_addr)
            self._install_launch_script(ip_addr)
            self._run_launch_script(ip_addr)
        return True, ip_addr

    def _set_ssh_credentials(self):
        print("Input SSH password to use to connect to RPi cameras:")
        self.password = getpass('Password: ')

    def _recover_image(self, ip_addr: str, filename: str, destination: str) -> None:
        # Recover image from RPi camera.
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            c.get(remote=filename, local=destination)
            log.debug("Image recovered from {ip_addr}".format(ip_addr=ip_addr))
            c.close()
        except Exception:
            c.close()
            log.error("Failed to recover image from {ip_addr}".format(ip_addr=ip_addr))
            pass
        
    def _check_hostname(self, ip_addr: str, id: str) -> bool | str | str:
        # Try to connect to the device via SSH. If successful, get the hostname.
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            result = c.run('hostname -s', hide=True)
            c.close()
            hostname = result.stdout.rstrip()
            if id in hostname:
                return True, hostname, ip_addr
            else:
                return False, "none", "none"
        except Exception:
            c.close()
            return False, "none", "none"

    def _check_camera_control_script(self, ip_addr: str) -> bool:
        # Check if the camera control script is installed.
        file_exists_cmd = "test -f /home/{username}/camera.py && echo 'exists' || echo 'does not exist'".format(username=self.username)
        with open(self.camera_control_script, 'r') as f:
            camera_control_script_contents = f.read()
        current_camera_control_script_contents = ""
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            result = c.run(file_exists_cmd, hide=True)
            if "exists" in result.stdout:
                result = c.run('cat /home/{username}/camera.py'.format(username=self.username), hide=True)
                current_camera_control_script_contents = result.stdout
        except Exception:
            self.log_message = "Failed to check if control script is installed on {ip_addr}".format(ip_addr=ip_addr)
            log.warning(self.log_message)
        
        # Check if existing camera control script is current.
        if camera_control_script_contents == current_camera_control_script_contents:
            return True
        else:
            return False
            
    def _install_control_script(self, ip_addr: str):
        # Install the control script on the RPi.
        destination = '/home/{username}/camera.py'.format(username=self.username)
        self.log_message = "Installing control script on {ip_addr}".format(ip_addr=ip_addr)
        self.frontend_log_messages.append(self.log_message)
        log.debug(self.log_message)
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            c.put(self.camera_control_script, destination)
            self.log_message = "Control script installed on {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to install control script on {ip_addr}".format(ip_addr=ip_addr)
            log.warning(self.log_message)
        c.close()
        self._add_camera_control_script_to_crontab(ip_addr)
    
    def _install_launch_script(self, ip_addr: str):
        # Install the launch script on the RPi.
        destination = '/home/{username}/launch.py'.format(username=self.username)
        self.log_message = "Installing launch script on {ip_addr}".format(ip_addr=ip_addr)
        self.frontend_log_messages.append(self.log_message)
        log.debug(self.log_message)
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            c.put(self.launch_script, destination)
            self.log_message = "Launch script installed on {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to install launch script on {ip_addr}".format(ip_addr=ip_addr)
            log.warning(self.log_message)
        c.close()

    def _run_launch_script(self, ip_addr: str):
        # Run the launch script on the RPi.
        self.log_message = "Running launch script on {ip_addr}".format(ip_addr=ip_addr)
        self.frontend_log_messages.append(self.log_message)
        log.debug(self.log_message)
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        
        # Kill any existing camera.py processes.
        try:
            c.run('pkill -f camera.py -9', hide=True, warn=True)
            self.log_message = "Killed existing camera.py processes on {ip_addr}".format(ip_addr=ip_addr)
            log.debug(self.log_message)
        except Exception as e:
            log.warning("Exception: {e}".format(e=e))
            self.log_message = "Failed to kill existing camera.py processes on {ip_addr}".format(ip_addr=ip_addr)
            log.warning(self.log_message)
            log.warning(e)
        
        # Run the launch script (ignoring any exceptions raised by Fabric).
        try:
            c.run('python3 /home/{username}/launch.py &'.format(username=self.username), hide=True, timeout=2, warn=True)
            self.log_message = "Launch script run on {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            pass
        c.close()

    def _check_camera_running(self, ip_addr: str) -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            result = c.run('ps aux | grep "[c]amera.py"', hide=True)
            if "camera.py" in result.stdout:
                self.log_message = "Camera is running on {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
                return True
        except Exception:
            self.log_message = "Camera is not running on {ip_addr}".format(ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.warning(self.log_message)
            return False

    def _check_python_packages(self, ip_addr: str):
        # Get list of installed Python packages.
        self.log_message = "Checking Python packages on {ip_addr}".format(ip_addr=ip_addr)
        self.frontend_log_messages.append(self.log_message)
        log.info(self.log_message)
        pip_list = self._get_python_package_list(ip_addr)
        for package in self.required_packages:
            if package not in pip_list:
                if package == 'picamera2':
                    self.log_message = "The picamera2 package ought to be installed on the RPi by default. This package only works with the RPi."
                    self.frontend_log_messages.append(self.log_message)
                    log.error(self.log_message)
                else:
                    self.log_message = "Python package {package} not installed on {ip_addr}".format(package=package, ip_addr=ip_addr)
                    self.frontend_log_messages.append(self.log_message)
                    log.warning(self.log_message)
                    self._install_python_package(ip_addr, package)

    def _get_python_package_list(self, ip_addr: str) -> str:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        # Check if pip.pyz is installed on the RPi.
        pip_exists_cmd = "test -f /home/{username}/pip.pyz && echo 'exists' || echo 'does not exist'".format(username=self.username)
        try: 
            result = c.run(pip_exists_cmd, hide=True)
            if "exists" not in result.stdout:
                self._install_python_dependencies(ip_addr)
                self._install_python_package_manager(ip_addr)
        except Exception:
            self.log_message = "Failed to check if pip.pyz installed on {ip_addr}".format(ip_addr=ip_addr)
            log.error(self.log_message)
            sys.exit(1)

        pip_list = ""
        try:
            result = c.run('python3 pip.pyz list', hide=True)
            c.close()
            pip_list = result.stdout
            return pip_list
        except Exception:
            self.log_message = "Could not get list of installed packages."
            log.error(self.log_message)
            sys.exit(1)

    def _install_python_dependencies(self, ip_addr: str)  -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        # Upload package to RPi.
        try:
            c.put(self.lib2to3_file, '/home/{username}/{lib2to3}'.format(username=self.username, lib2to3=self.lib2to3_name))
            c.put(self.distutils_file, '/home/{username}/{distutils}'.format(username=self.username, distutils=self.distutils_name))
            self.log_message = "Uploaded Python dependencies to {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to upload Python dependencies to {ip_addr}".format(ip_addr=ip_addr)
            log.error(self.log_message)
            sys.exit(1)

        # Install package on RPi.
        try:
            self.log_message = "Installing Python dependencies on {ip_addr}".format(ip_addr=ip_addr)
            log.debug(self.log_message)
            c.sudo('dpkg -i {lib2to3}'.format(lib2to3=self.lib2to3_name), hide=True)
            c.sudo('dpkg -i {distutils}'.format(distutils=self.distutils_name), hide=True)
            c.sudo('rm *.deb', hide=True)
            self.log_message = "Python dependencies installed on {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to install Python dependencies on {ip_addr}".format(ip_addr=ip_addr)
            log.error(self.log_message)
            sys.exit(1)

        # Close connection and remove downloaded package.
        c.close()
        return True

    def _install_python_package_manager(self, ip_addr: str)  -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        self.log_message = "Installing Python package manager on {ip_addr}".format(ip_addr=ip_addr)
        log.info(self.log_message)
        success = False
        try:
            c.put(self.pip_pyz, '/home/{username}/pip.pyz'.format(username=self.username))
            success = True
            self.log_message = "Installed pip.pyz on {ip_addr}".format(ip_addr=ip_addr)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to install pip.pyz on {ip_addr}".format(ip_addr=ip_addr)
            log.error(self.log_message)
            sys.exit(1)
        return success
        
    def _install_python_package(self, ip_addr: str, package: str) -> bool:
        # Select package.
        if package == "getmac":
            wheel = self.getmac_wheel
            wheel_name = self.getmac_wheel_name

        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        # Upload package to RPi.
        try:
            c.put(wheel, '/home/{username}/{wheel}'.format(username=self.username, wheel=wheel_name))
            self.log_message = "Uploaded {package} to {ip_addr}".format(package=package, ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to upload {package} to {ip_addr}".format(package=package, ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.error(self.log_message)
            sys.exit(1)

        # Install package on RPi.
        try:
            self.log_message = "Installing Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.debug(self.log_message)
            c.sudo('python3 pip.pyz install {wheel}'.format(wheel=wheel_name), hide=True)
            c.sudo('rm {wheel}'.format(wheel=wheel_name), hide=True)
            self.log_message = "Python package {package} installed on {ip_addr}".format(package=package, ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.info(self.log_message)
        except Exception:
            self.log_message = "Failed to install Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr)
            self.frontend_log_messages.append(self.log_message)
            log.error(self.log_message)
            sys.exit(1)

        # Close connection and remove downloaded package.
        c.close()
        return True

    def _add_camera_control_script_to_crontab(self, ip_addr: str):
        # Add the control script to the crontab if not already added.
        crontab_cmd = "@reboot python3 /home/{username}/camera.py\n".format(username=self.username)
        crontab = open("crontab", "a")
        crontab.write(crontab_cmd)
        crontab.close()
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            result = c.run("crontab -l", hide=True, warn=True)
            if crontab_cmd in result.stdout:
                self.log_message = "Control script already set to autostart on {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
            else:
                self.log_message = "Adding control script to the crontab on {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
                c.put('crontab', '/home/{username}/crontab'.format(username=self.username))
                self.log_message = "Uploaded crontab script to {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
                c.run('crontab /home/{username}/crontab'.format(username=self.username), hide=True)
                c.sudo('rm crontab', hide=True)
                self.log_message = "Control script added to the crontab on {ip_addr}".format(ip_addr=ip_addr)
                self.frontend_log_messages.append(self.log_message)
                log.info(self.log_message)
        except Exception as e:   
            log.error(e)
            self.log_message = "Failed to add control script to the crontab on {ip_addr}".format(ip_addr=ip_addr)
            log.error(self.log_message)
            sys.exit(1)
        os.system("rm crontab")

    def _reboot_camera(self, ip_addr: str):
        log.info("Rebooting {ip_addr}".format(ip_addr=ip_addr))
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            c.sudo('reboot', hide=True)
            c.close()
        except Exception:
            self.log_message = "Failed to reboot {ip_addr}".format(ip_addr=ip_addr)
            log.warning(self.log_message)

    def _get_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Doesn't even have to be reachable.
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
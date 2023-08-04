import concurrent.futures
from fabric import Connection
import geocam as gc
import geocam.dependencies as deps
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

# Initialise log at default settings.
level = logging.INFO
gc.log.initialise(level)
logging.getLogger('paramiko').setLevel(logging.FATAL)
log = logging.getLogger(__name__)
log.debug("Initialised geocam log.")

MCAST_GRP = '225.1.1.1'
MCAST_PORT = 3179
TCP_PORT = 1645

class Controller:

    def __init__(self, configuration: str=None):
        log.debug("Created a Controller instance.")
        self.ip = self._get_ip()
        self.cameras = {}
        if configuration is not None:
            c = open(configuration, 'r')
            self.cameras = json.load(c)
            self.id = configuration.rsplit( ".", 1 )[ 0 ]
            self.username = self.id
            self._set_ssh_credentials()

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
        log.debug("Stopping camera threads.")
        self._close_TCP_connections()
        log.debug("Deleted a Controller instance.")
        
    def find_cameras(self, id: str, network: str=None, password: str=None) -> dict:
        # SSH credentials.
        self.username = id
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
        log.info("Searching network: {network}".format(network=network))
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
                log.debug("Checking IP address: {ip_addr}".format(ip_addr=ip_addr))
                results.append(executor.submit(self._check_hostname, ip_addr, id))
            for future in concurrent.futures.as_completed(results):
                found = future.result()[0]
                hostname = future.result()[1]
                ip = future.result()[2]
                if found:
                    mac = getmac.get_mac_address(ip=ip)
                    self.cameras.update({hostname: {"ip": ip, "mac": mac, "ready": False, "tcp": False}})
                    log.info("RPi camera called {name} found at {ip} with MAC address: {mac}".format(name=hostname, ip=ip, mac=mac))
    
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
                        log.info("Camera ready for acquisiton at {ip}".format(ip=ip))
                    else:
                        ready = False
                        log.warning("Camera not ready for acquisition at {ip}".format(ip=ip))
                    self.cameras[camera]["ready"] = ready

            #Check status of cameras communications.
            self._check_status()
            return self.cameras
        else:
            log.warning("No RPi cameras found on the network.")
            return self.cameras

    def save_configuration(self) -> None:
        filename = self.id + ".json"
        if len(self.cameras) == 0:
            log.warning("No cameras found. No configuration to save...")
            return
        log.debug("Saving configuration to {filename}".format(filename=filename))
        with open(filename, 'w') as outfile:
            json.dump(self.cameras, outfile, indent=4, sort_keys=True)
        log.info("Saved configuration to {filename}".format(filename=filename))

    def restart_cameras(self):
        log.info("Restarting all cameras...")
        if len(self.cameras) == 0:
            log.warning("No cameras found. Run find_cameras() or pass in a configuration...")
            return
        for camera in self.cameras:
            ip = self.cameras[camera]["ip"]
            self._run_launch_script(ip)
            log.info("Restarted camera at {ip}".format(ip=ip))
        time.sleep(1)

    def _check_status(self) -> bool:
        # Open TCP connection for each camera in a separate thread.
        found_all_cameras = False
        log.info("Opening TCP connection to cameras.")
        self.threads_running.set()
        for camera in self.cameras:
            self.cameras[camera]["tcp"] = False
            thread = threading.Thread(target=self._open_TCP_connection, args=(self.threads_running, self.cameras[camera],))
            thread.setDaemon(True)
            thread.start()
            self.threads.append(thread)

        # Send command via UDP to get MAC address of found devices and await response on TCP.
        log.debug("Sending UDP command to get MAC addresses.")
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
                    self.cameras[hostname]["tcp"] = True
                    self.tcp_connections += 1
                    log.info("Camera at {ip} is ready for acquisition via TCP".format(ip=self.cameras[hostname]["ip"])) 
        self._close_TCP_connections()

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
        log.debug("Opening TCP connection to camera at {ip}".format(ip=ip))
        TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        log.info("Trying to connect to camera at {ip}".format(ip=ip))
        start_time = time.time()
        elapsed_time = 0.0
        timeout = 20.0
        while elapsed_time < timeout and not connected:
            try:
                TCP_socket.connect((ip, TCP_PORT))
                log.info("Connected to camera via TCP on {ip}:{port}".format(ip=ip, port = TCP_PORT))
                connected = True
            except Exception:
                time.sleep(5)

            if connected:
                log.info("Waiting for response via TCP from camera at {ip}".format(ip=ip))
            while connected and thread_running.is_set():
                data = TCP_socket.recv(1024)
                message = data.decode('utf-8')
                if message == "":
                    connected = False
                    log.warning("TCP connection closed by camera at {ip}".format(ip=ip))
                else:
                    try:
                        message = json.loads(message)
                        if "response" in message:
                            self.message_buffer.put(message)
                            connected = False
                    except Exception:
                        pass
            elapsed_time = time.time() - start_time
        TCP_socket.close()
        log.warning("Failed to open TCP connection to camera at {ip}".format(ip=ip))

    def _close_TCP_connections(self) -> None:
        # Close TCP connections to cameras.
        self.threads_running.clear()

    def _send_command(self, command: str) -> None:
        try: 
            json_command = json.dumps(command, indent=2)
            self.udp_socket.sendto(bytes(json_command, 'utf-8'), (MCAST_GRP, MCAST_PORT))
            log.debug("Sent command: {command}".format(command=command))
        except Exception as e: 
            log.error(e.with_traceback())

    def _check_RPi(self, ip_addr: str) -> bool | str:
        installed = self._check_camera_control_script(ip_addr)
        if not installed:
            # Raspberry Pi hasn't been used as a camera before.
            log.warning("Checking RPi OS on {ip_addr}".format(ip_addr=ip_addr))
            self._check_python_packages(ip_addr)
            self._install_control_script(ip_addr)
            self._install_launch_script(ip_addr)
            self._run_launch_script(ip_addr)
        return True, ip_addr

    def _set_ssh_credentials(self):
        print("Input SSH password to use to connect to RPi cameras:")
        self.password = getpass('Password: ')
        
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
            log.warning("Failed to check if control script is installed on {ip_addr}".format(ip_addr=ip_addr))
        
        # Check if existing camera control script is current.
        if camera_control_script_contents == current_camera_control_script_contents:
            return True
        else:
            return False
            
    def _install_control_script(self, ip_addr: str):
        # Install the control script on the RPi.
        destination = '/home/{username}/camera.py'.format(username=self.username)
        log.debug("Installing control script on {ip_addr}".format(ip_addr=ip_addr))
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            c.put(self.camera_control_script, destination)
            log.info("Control script installed on {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            log.warning("Failed to install control script on {ip_addr}".format(ip_addr=ip_addr))
        c.close()
        self._add_camera_control_script_to_crontab(ip_addr)
    
    def _install_launch_script(self, ip_addr: str):
        # Install the launch script on the RPi.
        destination = '/home/{username}/launch.py'.format(username=self.username)
        log.debug("Installing launch script on {ip_addr}".format(ip_addr=ip_addr))
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        try:
            c.put(self.launch_script, destination)
            log.info("Launch script installed on {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            log.warning("Failed to install launch script on {ip_addr}".format(ip_addr=ip_addr))
        c.close()

    def _run_launch_script(self, ip_addr: str):
        # Run the launch script on the RPi.
        log.debug("Running launch script on {ip_addr}".format(ip_addr=ip_addr))
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        
        # Kill any existing camera.py processes.
        try:
            c.run('pkill -f camera.py -9', hide=True, warn=True)
            log.debug("Killed existing camera.py processes on {ip_addr}".format(ip_addr=ip_addr))
        except Exception as e:
            log.warning("Exception: {e}".format(e=e))
            log.warning("Failed to kill existing camera.py processes on {ip_addr}".format(ip_addr=ip_addr))
            log.warning(e)
        
        # Run the launch script (ignoring any exceptions raised by Fabric).
        try:
            c.run('python3 /home/{username}/launch.py &'.format(username=self.username), hide=True, timeout=2, warn=True)
            log.info("Launch script run on {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            pass
        c.close()

    def _check_python_packages(self, ip_addr: str):
        # Get list of installed Python packages.
        log.info("Checking Python packages on {ip_addr}".format(ip_addr=ip_addr))
        pip_list = self._get_python_package_list(ip_addr)
        for package in self.required_packages:
            if package not in pip_list:
                if package == 'picamera2':
                    log.fatal("The picamera2 package ought to be installed on the RPi by default. This package only works with the RPi.")
                else:
                    log.warning("Python package {package} not installed on {ip_addr}".format(package=package, ip_addr=ip_addr))
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
            log.error("Failed to check if pip.pyz installed on {ip_addr}".format(ip_addr=ip_addr))
            sys.exit(1)

        pip_list = ""
        try:
            result = c.run('python3 pip.pyz list', hide=True)
            c.close()
            pip_list = result.stdout
            return pip_list
        except Exception:
            log.error("Could not get list of installed packages.")
            sys.exit(1)

    def _install_python_dependencies(self, ip_addr: str)  -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        # Upload package to RPi.
        try:
            c.put(self.lib2to3_file, '/home/{username}/{lib2to3}'.format(username=self.username, lib2to3=self.lib2to3_name))
            c.put(self.distutils_file, '/home/{username}/{distutils}'.format(username=self.username, distutils=self.distutils_name))
            log.info("Uploaded Python dependencies to {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            log.error("Failed to upload Python dependencies to {ip_addr}".format(ip_addr=ip_addr))
            sys.exit(1)

        # Install package on RPi.
        try:
            log.debug("Installing Python dependencies on {ip_addr}".format(ip_addr=ip_addr))
            c.sudo('dpkg -i {lib2to3}'.format(lib2to3=self.lib2to3_name), hide=True)
            c.sudo('dpkg -i {distutils}'.format(distutils=self.distutils_name), hide=True)
            c.sudo('rm *.deb', hide=True)
            log.info("Python dependencies installed on {ip_addr}".format(ip_addr=ip_addr))
            
        except Exception:
            log.error("Failed to install Python dependencies on {ip_addr}".format(ip_addr=ip_addr))
            sys.exit(1)

        # Close connection and remove downloaded package.
        c.close()
        return True

    def _install_python_package_manager(self, ip_addr: str)  -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        log.info("Installing Python package manager on {ip_addr}".format(ip_addr=ip_addr))
        success = False
        try:
            c.put(self.pip_pyz, '/home/{username}/pip.pyz'.format(username=self.username))
            success = True
            log.info("Installed pip.pyz on {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            log.error("Failed to upload pip.pyz to {ip_addr}".format(ip_addr=ip_addr))
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
            log.info("Uploaded {package} to {ip_addr}".format(package=package, ip_addr=ip_addr))
        except Exception:
            log.error("Failed to upload {package} to {ip_addr}".format(package=package, ip_addr=ip_addr))
            sys.exit(1)

        # Install package on RPi.
        try:
            log.debug("Installing Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr))
            c.sudo('python3 pip.pyz install {wheel}'.format(wheel=wheel_name), hide=True)
            c.sudo('rm {wheel}'.format(wheel=wheel_name), hide=True)
            log.info("Python package {package} installed on {ip_addr}".format(package=package, ip_addr=ip_addr))
        except Exception:
            log.error("Failed to install Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr))
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
                log.info("Control script already set to autostart on {ip_addr}".format(ip_addr=ip_addr))
            else:
                log.info("Adding control script to the crontab on {ip_addr}".format(ip_addr=ip_addr))
                c.put('crontab', '/home/{username}/crontab'.format(username=self.username))
                log.info("Uploaded crontab script to {ip_addr}".format(ip_addr=ip_addr))
                c.run('crontab /home/{username}/crontab'.format(username=self.username), hide=True)
                c.sudo('rm crontab', hide=True)
                log.info("Control script added to the crontab on {ip_addr}".format(ip_addr=ip_addr))
        except Exception as e:   
            log.error(e)
            log.error("Failed to add control script to the crontab on {ip_addr}".format(ip_addr=ip_addr))
            sys.exit(1)
        os.system("rm crontab")

    def _reboot_camera(self, ip_addr: str):
        log.info("Rebooting {ip_addr}".format(ip_addr=ip_addr))
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            c.sudo('reboot', hide=True)
            c.close()
        except Exception:
            log.warning("Failed to reboot {ip_addr}".format(ip_addr=ip_addr))

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
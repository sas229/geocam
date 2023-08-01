import concurrent.futures
from fabric import Connection
import geocam as gc
import getmac
from getpass4 import getpass
from glob import glob
from importlib import resources as impresources
import ipaddress
import json
import logging
import networkscan
import os
import requests
import shutil
import socket

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

    required_packages = [
        'getmac',
        'picamera2',
    ]

    def __init__(self):
        log.debug("Created a Controller instance.")
        self._set_ssh_credentials()
        self.cameras = []
        self.ip = self._get_ip()

        # Camera control script.
        self.camera_control_script = (impresources.files(gc) / 'camera.py')

        # Create UDP multicast socket.
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        # Create TCP socket.
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.ip, TCP_PORT))
        self.tcp_socket.listen()

    def find_cameras(self, id: str, network: str=None) -> None:
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
        self.cameras = []
        results = []
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
                    self.cameras.append({"hostname":hostname, "ip":ip, "mac":mac})
                    log.info("RPi camera called {name} found at {ip} with MAC address: {mac}".format(name=hostname, ip=ip, mac=mac))
    
        # If cameras are found, check control script and packages using ThreadPool.
        if len(self.cameras) > 0:
            log.debug("Checking control script is installed.")
            results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for camera in self.cameras:
                    ip_addr = camera["ip"]
                    results.append(executor.submit(self._check_RPi, ip_addr))
                for future in concurrent.futures.as_completed(results):
                    ready = future.result()[0]
                    ip = future.result()[1]
                    if ready:
                        status = {"ready": True}
                        log.info("Camera ready for acquisiton at {ip}".format(ip=ip))
                    else:
                        status = {"ready": False}
                        log.warning("Camera not ready for acquisition at {ip}".format(ip=ip))
                    camera.update(status)
            # Remove locally downloaded dependencies if necessary.
            if os.path.exists("./dependencies/"):
                shutil.rmtree("./dependencies/")
        
            # Send command via UDP to get MAC address of found devices and await response on TCP.
            log.debug("Sending UDP command to get MAC addresses.")
            cmd = {"command": "get_hostname_ip_mac"}
            self._send_command(cmd)
            self._await_TCP_responses_with_timeout(30)
        
        else:
            log.warning("No RPi cameras found on the network.")

    def _send_command(self, command: str) -> None:
        try: 
            json_command = json.dumps(command, indent=2)
            self.udp_socket.sendto(bytes(json_command, 'utf-8'), (MCAST_GRP, MCAST_PORT))
            log.debug("Sent command: {command}".format(command=command))
        except Exception as e: 
            log.error(e.with_traceback())
        
    def _await_TCP_responses_with_timeout(self, timeout: int) -> None:
        # Wait for TCP responses from RPi cameras.
        log.debug("Waiting for TCP responses with {timeout} second timeout.".format(timeout=timeout))
        self.tcp_socket.settimeout(timeout)
        try:
            client_socket, client_address = self.tcp_socket.accept()
            log.debug("Received TCP response from {client_address}".format(client_address=client_address))
            data = client_socket.recv(1024)
            message = data.decode('utf-8')
            response = json.loads(message)
            print("Hostname: {hostname}; IP: {ip}; MAC: {mac}".format(hostname=response['hostname'], ip=response['ip'], mac=response['mac']))
        except socket.timeout:
            log.debug("TCP socket timed out.")

    def _check_RPi(self, ip_addr: str) -> bool | str:
        installed = self._check_camera_control_script(ip_addr)
        if not installed:
            # Raspberry Pi hasn't been used as a camera before.
            log.warning("Preparing RPi on {ip_addr}".format(ip_addr=ip_addr))
            self._check_python_packages(ip_addr)
            self._install_control_script(ip_addr)
        return True, ip_addr

    def _set_ssh_credentials(self):
        print("Input SSH credentials to use to connect to RPi cameras:")
        self.username = input('Username: ')
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
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            c.put(self.camera_control_script, destination)
            log.info("Control script installed on {ip_addr}".format(ip_addr=ip_addr))
        except Exception:
            log.warning("Failed to install control script on {ip_addr}".format(ip_addr=ip_addr))
        c.close()
        self._add_camera_control_script_to_crontab(ip_addr)

    def _check_python_packages(self, ip_addr: str):
        # Get list of installed Python packages.
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
                self._install_python_package_manager(ip_addr)
        except Exception:
            log.warning("Failed to check if pip.pyz installed on {ip_addr}".format(ip_addr=ip_addr))
                        
        pip_list = ""
        try:
            result = c.run('python3 pip.pyz list', hide=True)
            c.close()
            pip_list = result.stdout
            return result.stdout
        except Exception:
            log.fatal("Could not get list of installed packages.")
            return pip_list

    def _install_python_package_manager(self, ip_addr: str)  -> bool:
        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        log.info("Installing Python package manager on {ip_addr}".format(ip_addr=ip_addr))
        pip_url = "https://bootstrap.pypa.io/pip/pip.pyz"
        pip_app = requests.get(pip_url)
        open('pip.pyz', 'wb').write(pip_app.content)
        success = False
        try:
            c.put('pip.pyz', '/home/{username}/pip.pyz'.format(username=self.username))
            success = True
            log.info("Installed pip.pyz on {ip_addr}".format(ip_addr=ip_addr))
            return True
        except Exception:
            log.warning("Failed to upload pip.pyz to {ip_addr}".format(ip_addr=ip_addr))
        os.remove('pip.pyz')
        return success
        
    def _install_python_package(self, ip_addr: str, package: str) -> bool:
        # Download package from PyPI.
        if not os.path.exists("dependencies"): 
            os.mkdir("dependencies")
        os.system('pip download {package} -d dependencies'.format(package=package))
        os.chdir("dependencies")
        wheel = glob('{package}-*.whl'.format(package=package))[0]

        c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
        # Upload package to RPi.
        try:
            c.put(wheel, '/home/{username}/{wheel}'.format(username=self.username, wheel=wheel))
            log.info("Uploaded {package} to {ip_addr}".format(package=package, ip_addr=ip_addr))
        except Exception:
            log.warning("Failed to upload {package} to {ip_addr}".format(package=package, ip_addr=ip_addr))

        # Install package on RPi.
        try:
            log.debug("Installing Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr))
            c.sudo('python3 pip.pyz install {wheel}'.format(wheel=wheel), hide=True)
            log.info("Python package {package} installed on {ip_addr}".format(package=package, ip_addr=ip_addr))
        except Exception:
            log.warning("Failed to install Python package {package} on {ip_addr}".format(package=package, ip_addr=ip_addr))
        
        # Close connection and remove downloaded package.
        c.close()
        os.chdir("..")
        return True

    def _add_camera_control_script_to_crontab(self, ip_addr: str):
        # Add the control script to the crontab if not already added.
        crontab_cmd = "@reboot python3 /home/{username}/camera.py".format(username=self.username)
        autostart_cmd = '(crontab -l ; echo "' + crontab_cmd + '") | crontab -'
        try:
            c = Connection(host=ip_addr, user=self.username, connect_kwargs={"password": self.password})
            result = c.run("crontab -l", hide=True)
            if crontab_cmd in result.stdout:
                log.info("Control script already set to autostart on {ip_addr}".format(ip_addr=ip_addr))
            else:
                log.info("Adding control script to the crontab on {ip_addr}".format(ip_addr=ip_addr))
                c.run(autostart_cmd, hide=True)
                log.info("Control script added to the crontab on {ip_addr}".format(ip_addr=ip_addr))
            c.close()
        except Exception:
            log.warning("Failed to add control script to the crontab on {ip_addr}".format(ip_addr=ip_addr))
        self._reboot_camera(ip_addr)

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
        
if __name__ == "__main__": 
    test = Controller()
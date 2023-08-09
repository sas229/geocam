<template>
    <div>
        <details open>
            <summary>Overview</summary>
            <p>
                geocam is a simple package written in Python and Vue.js that can be used to find, 
                control and acquire for Raspberry Pi single board computers (SBCs) equipped with cameras 
                that can be controlled via the Picamera2 Python library.
            </p>
            <p>
                The software is designed to be run with Raspberry Pi SBCs running the Raspbian operating
                system. The required packages will automatically install on finding cameras with user 
                supplied SSH login ID and password.
            </p>
        </details>
        <details>
            <summary>Preparation</summary>
            <p>To use geocam on your RPi, the following steps should be taken:</p>
            <ol type="1">
                <li>Install the latest version of Raspbian on your RPi using <a href="https://www.raspberrypi.com/software/">Raspberry Pi Imager</a></li>
                <li>Setup the installation by pressing the cog symbol in the lower right corner:</li>
                <div class="container">
                    <img src="@/assets/Imager.png" alt="Raspberry Pi Imager">
                </div>
                <li>Using a hostname, username and password (and WiFi SSID and password, if WiFi is required) of your choice, fill out the settings. <strong><u>Note: the hostname must contain the username, which should be the same across all devices to be used in a single given system.</u></strong></li>
                <div class="container">
                    <img src="@/assets/ImagerSettings.png" alt="Raspberry Pi Imager Settings">
                </div>
                <li>Burn the customised RPi image to an SD card and insert it into your RPi.</li>
                <li>Boot the RPi and it will automatically connect to your WiFi network, or use an Ethernet cable to connect it to your network if you want a hard-wired connection.</li>
            </ol>
        </details>
        <details>
            <summary>Configuration</summary>
            <p>
                Give the RPi a few minutes to boot up and connect to the network. 
                If the RPi are running headless (i.e. no monitor) then you can use a tool such as 
                <a href="https://angryip.org/">Angry IP Scanner</a> to check they are on the network. 
                Input your username and password on the "Configuration" page and click "Find Cameras".
                The network will be searched for RPi with the supplied username and password.
            </p>
        </details>
        <details>
            <summary>Preview</summary>
            <p>Text to go here...</p>
        </details>
        <details>
            <summary>Capture</summary>
            <p>Text to go here...</p>
        </details>
    </div>
</template>

<style scoped>
.container {
    max-width: 80%;
    width: auto;
    text-align: center;
}
</style>
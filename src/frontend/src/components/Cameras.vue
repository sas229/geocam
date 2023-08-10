<template>
  <div class="grid">
    <button @click="loadConfiguration" data-tooltip="Load a configuration...">Load</button>
    <button v-if="configured" @click="saveConfiguration" data-tooltip="Save the configuration...">Save</button>
    <button v-if="configured" @click="clearConfiguration" data-tooltip="Clear the configuration...">Clear</button>
    <input v-if="!configured" @change="checkLogin" type="text" v-model="username" placeholder="username" :aria-invalid="!usernameValid" data-tooltip="Input the RPi username to search for...">
    <input v-if="!configured" @change="checkLogin" type="text" v-model="password" placeholder="password" :aria-invalid="!passwordValid" data-tooltip="Input the RPi password to search for...">
    <button v-if="!configured" @click="findCameras" class="contrast" :disabled="!loginValid" data-tooltip="Find cameras with current ID and password...">Find Cameras</button>
  </div>
  <br>
  <table v-if="configured">
    <tr>
      <th>Hostname</th>
      <th>IP</th>
      <th>MAC</th>
      <th>TCP</th>
      <th>Camera</th>
    </tr>
    <tr v-for="camera in Object.keys(store.cameras)">
      <td>{{ camera }}</td>
      <td>{{ store.cameras[camera].ip }}</td>
      <td>{{ store.cameras[camera].mac }}</td>
      <td v-if="store.cameras[camera].tcp"><i class="fa fa-check" aria-hidden="true"></i></td>
      <td v-else><i class="fa fa-times" aria-hidden="true"></i></td>
      <td v-if="store.cameras[camera].ready"><i class="fa fa-check" aria-hidden="true"></i></td>
      <td v-else><i class="fa fa-times" aria-hidden="true"></i></td>
    </tr>
  </table> 
  <div v-if="findingCameras">
    <dialog open>
      <article class="fixedWidth">
        <h3>Finding cameras...</h3>
        <progress></progress>
        <footer class="leftAligned">
          <small >{{ logMessage }}</small>
        </footer>
      </article>
    </dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useGeocamStore } from '@/stores/geocam'
import axios from 'axios'
axios.defaults.baseURL = "http://0.0.0.0:8001/";

// Reactive state.
const store = useGeocamStore()
const username = ref('')
const password = ref('')
const usernameValid = ref(false)
const passwordValid = ref(false)
const findingCameras = ref(false)
const logMessage = ref('')
const configured = ref(false)
const loginValid = ref(true)

// Functions.
function toggleFindingCameras() {
  findingCameras.value = !findingCameras.value
}

function checkLogin() {
  console.log("Checking login details...")
  usernameValid.value = username.value != '' ? true :  false
  console.log("usernameValid: " + usernameValid.value)
  console.log("username: " + username.value)
  passwordValid.value = password.value != '' ? true :  false
  console.log("passwordValid: " + passwordValid.value)
  console.log("password: " + password.value)
  loginValid.value = (username.value != '' && password.value != '') ? true : false
}

function loadConfiguration() {
  console.log('Loading configuration...')  
}

function saveConfiguration() {
  console.log('Saving configuration...')
}

function clearConfiguration() {
  console.log('Clearing configuration...')
  configured.value = false
  username.value = ''
  password.value = ''
  checkLogin()
}

async function findCameras() {
  logMessage.value = 'Connecting to server';
  toggleFindingCameras();
  try {
    let data = {
      username: username.value,
      password: password.value
    }
    let messageUpdated = false;
    const logMessageInterval = setInterval(async () => {
      if (!messageUpdated) {
        await getLogMessage();
        messageUpdated = true;
      } else {
        messageUpdated = false;
      }
    }, 50);
    let response = await axios({
      method: 'post',
      url: '/findCameras',
      data: data
    });
    clearInterval(logMessageInterval);
    store.cameras = response.data;
    if (Object.keys(store.cameras).length > 0) {
      configured.value = true;
    }
    toggleFindingCameras();
  } catch (error) {
    console.error(error);
  }
}

async function getLogMessage() {
  try {
    let response = await axios({
      method: 'get',
      url: '/logMessage'
    });
    if (response.data.logMessage != '') {
      logMessage.value = response.data.logMessage;
    }
    return Promise.resolve(response);
  } catch (error) {
    console.error(error);
  }
}

</script>

<style scoped>
.fixedWidth {
  width: 1000px;
}

.leftAligned {
  text-align: left;
}
</style>
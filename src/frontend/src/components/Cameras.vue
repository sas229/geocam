<template>
  <div class="grid">
    <input v-if="!configured" @change="checkLogin" type="text" v-model="id" placeholder="id" :aria-invalid="!idValid" data-tooltip="Input the RPi id to search for...">
    <input v-if="!configured" @change="checkLogin" type="text" v-model="password" placeholder="password" :aria-invalid="!passwordValid" data-tooltip="Input the RPi password to search for...">
    <button @click="selectConfiguration" :disabled="!loginValid" data-tooltip="Load a configuration...">Load</button>
    <button v-if="configured" @click="saveConfiguration" data-tooltip="Save the configuration...">Save</button>
    <button v-if="configured" @click="clearConfiguration" data-tooltip="Clear the configuration...">Clear</button>
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
  <div v-if="loadingConfiguration">
    <dialog open>
      <article class="fixedWidth">
        <h3>Loading configuration...</h3>
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
const id = ref('')
const password = ref('')
const idValid = ref(false)
const passwordValid = ref(false)
const findingCameras = ref(false)
const loadingConfiguration = ref(false)
const logMessage = ref('')
const configured = ref(false)
const loginValid = ref(false)

// Functions.
function toggleFindingCameras() {
  findingCameras.value = !findingCameras.value
}

function toggleLoadingConfiguration() {
  loadingConfiguration.value = !loadingConfiguration.value
}

function checkLogin() {
  console.log("Checking login details...")
  idValid.value = id.value != '' ? true :  false
  console.log("idValid: " + idValid.value)
  console.log("id: " + id.value)
  passwordValid.value = password.value != '' ? true :  false
  console.log("passwordValid: " + passwordValid.value)
  console.log("password: " + password.value)
  loginValid.value = (id.value != '' && password.value != '') ? true : false
}

function selectConfiguration() {
  console.log('Selecting configuration...')  
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = e => {
    toggleLoadingConfiguration();
    console.log("Configuration selected") 
    // Get the file reference.
    let file = e.target.files[0]; 

    // Set up the reader.
    let reader = new FileReader();
    reader.readAsText(file,'UTF-8');

    // Read the configuration file.
    let configuration;
    reader.onload = readerEvent => {
      configuration = JSON.parse(readerEvent.target.result);

      // Load the configuration in the backend.
      let data = {
        configuration: configuration,
        id: id.value,
        password: password.value,
      }
      loadConfiguration(data);
    }
  }
  input.click();
}

async function loadConfiguration(data) {
  console.log('Loading configuration')
  try {
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
      url: '/loadConfiguration',
      data: data
    });
    clearInterval(logMessageInterval);
    store.cameras = response.data;
    if (Object.keys(store.cameras).length > 0) {
      configured.value = true;
    }
  } catch (error) {
    console.error(error);
  }
  toggleLoadingConfiguration();
}

function saveConfiguration() {
  console.log('Saving configuration...')
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(store.cameras, null, 4)], {
    type: "text/plain"
  }));
  let filename = id.value + ".json"
  a.setAttribute("download", filename);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function clearConfiguration() {
  console.log('Clearing configuration...')
  configured.value = false
  id.value = ''
  password.value = ''
  store.cameras = {}
  checkLogin()
  let data = {
    configuration: {},
    id: id.value,
    password: password.value,
  }
  console.log('Clearing configuration')
  try {
    let response = await axios({
      method: 'post',
      url: '/clearConfiguration',
      data: data
    });
    store.cameras = response.data;
    if (Object.keys(store.cameras).length > 0) {
      configured.value = true;
    } else {
      configured.value = false;
    }
  } catch (error) {
    console.error(error);
  }
}

async function findCameras() {
  logMessage.value = 'Connecting to server';
  toggleFindingCameras();
  try {
    let data = {
      id: id.value,
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

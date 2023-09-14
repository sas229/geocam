<template>
  <main>
    <div v-if="Object.keys(store.cameras).length > 0">
      <label for="previewSelect">Camera selected</label>
      <select id="previewSelect" @change="setPreviewCamera" v-model="previewCamera" required>
        <option disabled value="" selected>Select a camera...</option>
        <option v-for="camera in Object.keys(store.cameras)">{{ camera }}</option>
      </select>
      <VueMagnifier v-if="previewCamera != ''" :src="preview" alt="Preview placeholder" class="container" zoomFactor="3.0" v-bind:mgShowOverflow="false" mgWidth="300" mgHeight="300"/>
    </div>
    <h6 v-if="Object.keys(store.cameras).length === 0">No cameras currently available...</h6>
    <br>
    <details v-if="previewCamera != ''" :open="controlsOpen.value">
      <br>
      <summary>Controls</summary>
      <select @change="setCameraControl" v-model="currentControl">
        <option value="" disabled selected>Select</option>
        <option value="AeEnable">Auto Exposure Enable</option>
        <option value="ExposureTime">Exposure Time (μs)</option>
        <option value="ExposureValue">Exposure Value (-)</option>
        <option value="Saturation">Saturation (-)</option>
        <option value="Sharpness">Sharpness (-)</option>
        <option value="Brightness">Brightness (-)</option>
        <option value="NoiseReductionMode">Noise Reduction Mode</option>
        <option value="AwbEnable">Auto White Balance Enable</option>
        <option value="AwbMode">Auto White Balance Mode</option>
      </select>

      <div v-if="currentControl === 'AeEnable'" class="container text-center">
        <select @change="controlChanged" id="AeEnable" v-model="AeEnable">
          <option>True</option>
          <option>False</option>
        </select>
      </div>

      <div v-if="currentControl === 'ExposureTime'" class="container text-center">
        <div class="row centered">
          <div class="col-8 spaced">
            <input @change="controlChanged" id="ExposureTime" class="slider" type="range" min="1" max="10000" v-model="ExposureTime">
          </div>
          <div class="col spaced">
            <input @change="controlChanged" type="number" id="ExposureTime" min="1" max="10000" v-model="ExposureTime">
          </div>
        </div>
      </div>

      <div v-if="currentControl === 'ExposureValue'" class="container text-center">
        <div class="row centered">
          <div class="col-8 spaced">
            <input @change="controlChanged" id="ExposureValue" class="slider" type="range" min="-8.0" max="8.0" step="0.01" v-model="ExposureValue">
          </div>
          <div class="col spaced">
            <input @change="controlChanged" type="number" id="ExposureValue" min="-8.0" max="8.0" step="0.01" v-model="ExposureValue">
          </div>
        </div>
      </div>

      <div v-if="currentControl === 'Saturation'" class="container text-center">
        <div class="row centered">
          <div class="col-8 spaced">
            <input @change="controlChanged" id="Saturation" class="slider" type="range" min="0.0" max="32.0" step="0.01" v-model="Saturation">
          </div>
          <div class="col spaced">
            <input @change="controlChanged" type="number" id="Saturation" min="0.0" max="32.0" step="0.01" v-model="Saturation">
          </div>
        </div>
      </div>

      <div v-if="currentControl === 'Sharpness'" class="container text-center">
        <div class="row centered">
          <div class="col-8 spaced">
            <input @change="controlChanged" id="Sharpness" class="slider" type="range" min="1.0" max="16.0" step="0.01" v-model="Sharpness">
          </div>
          <div class="col spaced">
            <input @change="controlChanged" type="number" id="Sharpness" min="1.0" max="16.0" step="0.01" v-model="Sharpness">
          </div>
        </div>
      </div>

      <div v-if="currentControl === 'Brightness'" class="container text-center">
        <div class="row centered">
          <div class="col-8 spaced">
            <input @change="controlChanged" id="Brightness" class="slider" type="range" min="-1.0" max="1.0" step="0.01" v-model="Brightness">
          </div>
          <div class="col spaced">
            <input @change="controlChanged" type="number" id="Brightness" min="-1.0" max="1.0" step="0.01" v-model="Brightness">
          </div>
        </div>
      </div>

      <div v-if="currentControl === 'NoiseReductionMode'" class="container text-center">
        <select @change="controlChanged" id="NoiseReductionMode">
          <option value="0">Off</option>
          <option value="1">Fast</option>
          <option value="2">HighQuality</option>
        </select>
      </div>
      
      <div v-if="currentControl === 'AwbEnable'" class="container text-center">
        <select @change="controlChanged" id="AwbEnable" v-model="AwbEnable">
          <option>False</option>
          <option>True</option>
        </select>
      </div>
      
      <div v-if="currentControl === 'AwbMode'" class="container text-center">
        <select @change="controlChanged" id="AwbMode" v-model="AwbMode" :disabled="AwbEnable === 'False'">
          <option value="0">Auto</option>
          <option value="1">Incandescant</option>
          <option value="2">Tungsten</option>
          <option value="3">Fluorescent</option>
          <option value="4">Indoor</option>
          <option value="5">Daylight</option>
          <option value="6">Cloudy</option>
          <option value="7">Custom</option>
        </select>
      </div>

      <div class="container">
        <label>
          <input type="checkbox" id="sendToAll" name="sendToAll">
          Send setting updates to all cameras?
        </label>
      </div>
      
    </details>
  </main>
</template>

<script setup>
import { ref, onActivated, onDeactivated } from 'vue'
import { useGeocamStore } from '@/stores/geocam'
import axios from 'axios'
import VueMagnifier from '@websitebeaver/vue-magnifier'
import '@websitebeaver/vue-magnifier/styles.css'

axios.defaults.baseURL = "http://0.0.0.0:8001/";

const store = useGeocamStore()

let previewCamera = ref('')
let controlsOpen = ref(false)
let currentControl = ref('')
let preview = ref('')
let ExposureTime = ref(500)
let ExposureValue = ref(0.00)
let Saturation = ref(1.00)
let Sharpness = ref(1.00)
let Brightness = ref(0.00)
let AwbEnable = ref('False')
let AwbMode = ref('Auto')
let AeEnable = ref(true)

async function controlChanged(event) {
  console.log(event.target.id + " changed to " + event.target.value)
  let control = event.target.id;
  let value;
  if (control === "AwbEnable") {
    value = (String(event.target.value).toLowerCase() == "true");
    console.log("Type: " + typeof value)
  } else if (control === "AwbMode" || control === "NoiseReductionMode") {
    value = parseInt(event.target.value)
  } else {
    value  = parseFloat(event.target.value);
  }
  let data = {}
  data[control] = value
  try {
    let response = await axios({
      method: 'post',
      url: 'http://' + store.cameras[previewCamera.value].ip + ':8002/updateControls',
      data: data
    });
    let success = response.data["success"]
    console.log("Successfully applied control: " + success)
  } catch (error) {
    console.error(error);
  }
}

function setCameraControl(event) {
  console.log(currentControl.value + " selected")
  console.log(currentControl.value)
}

function setPreviewCamera() {
  if (previewCamera.value === '') {
    preview = ''
  } else {
    console.log('Preview camera changed to ' + previewCamera.value)
    preview = 'http://' + store.cameras[previewCamera.value].ip + ':8002/preview';
  }
}

onActivated(() => {
  previewCamera.value = ''
  controlsOpen.value = false
})

onDeactivated(() => {
  previewCamera.value = '';
  setPreviewCamera();
  console.log("Preview deactivated");
})
</script>

<style scoped>
.scrollable{
  overflow-y: auto;
  max-height: 300px;
}

.spaced {
  padding: 15px 15px 15px 15px;
}

.centered {
  align-items: center;
}

</style>
<template>
  <main>
    <div>
      <label for="previewSelect">Camera selected</label>
      <select id="previewSelect" @change="setPreviewCamera" v-model="previewCamera" required>
        <option disabled value="" selected>Select a camera...</option>
        <option v-for="camera in Object.keys(store.cameras)">{{ camera }}</option>
      </select>
      <img v-if="previewCamera != ''" :src="preview" alt="Preview placeholder" class="container"> 
    </div>
    <br>
    <details :open="settingsOpen.value">
      <br>
      <summary>Settings</summary>
      <div class="scrollable container">
        <label for="exposureTime">Exposure Time (ms)</label>
        <input @change="settingChanged" id="exposureTime" class="slider" type="range" min="1" max="10000" value="500">
        <label for="exposureValue">Exposure Value (-)</label>
        <input @change="settingChanged" id="exposureValue" class="slider" type="range" min="-8.0" max="8" value="0.0" step="0.01">
        <label for="saturationValue">Saturation (-)</label>
        <input @change="settingChanged" id="saturationValue" class="slider" type="range" min="0.0" max="32.0" value="1.0" step="0.01">
        <label for="sharpnessValue">Sharpness (-)</label>
        <input @change="settingChanged" id="sharpnessValue" class="slider" type="range" min="1.0" max="16.0" value="1.0" step="0.01">
        <label for="brightnessValue">Brightness (-)</label>
        <input @change="settingChanged" id="brightnessValue" class="slider" type="range" min="-1.0" max="1.0" value="0.0" step="0.01"> 

        <label for="noiseReductionMode">Noise Reduction Mode</label>
        <select id="noiseReductionMode">
            <option>Off</option>
            <option>Fast</option>
            <option>HighQuality</option>
        </select>

        <label for="awbEnable">Auto White Balance Enable</label>
        <select id="awbEnable" v-model="awbEnabled">
            <option>False</option>
            <option>True</option>
        </select>

        <label for="awbMode">Auto White Balance Mode</label>
        <select id="awbMode" :disabled="awbEnabled === 'False'">
            <option>Auto</option>
            <option>Tungsten</option>
            <option>Fluorescent</option>
            <option>Indoor</option>
            <option>Daylight</option>
            <option>Cloudy</option>
            <option>Custom</option>
        </select>
      </div>
    </details>
  </main>
</template>

<script setup>
import { ref, onActivated, onDeactivated } from 'vue'
import { useGeocamStore } from '@/stores/geocam'
import axios from 'axios'
axios.defaults.baseURL = "http://0.0.0.0:8001/";

const store = useGeocamStore()
const awbEnabled = ref('False')
const previewCamera = ref('')
const settingsOpen = ref(false)
let preview = ref("")

function settingChanged(event) {
    console.log(event.target.id + " changed to " + event.target.value)
}

async function setPreviewCamera() {
  if (previewCamera.value === '') {
    preview = ''
  } else {
    console.log('Preview camera changed to ' + previewCamera.value)
    preview = 'http://' + store.cameras[previewCamera.value].ip + ':8000/stream.mjpg';
  }
  try {
    let data = {
      previewCamera: previewCamera.value
    }
    let response = await axios({
      method: 'post',
      url: '/setPreviewCamera',
      data: data
    })
    console.assert(response.data.success === true)
    return Promise.resolve(response);
  } catch (error) {
    console.error(error);
  }
}

onActivated(() => {
  previewCamera.value = ''
  settingsOpen.value = false
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

</style>
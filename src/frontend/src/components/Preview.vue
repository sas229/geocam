<template>
  <main>
    <div>
      <label for="preview">Camera selected</label>
      <select id="preview" @change="previewSelected" v-model="previewCamera" required>
        <option disabled value="" selected>Select a camera...</option>
        <option v-for="camera in Object.keys(store.cameras)">{{ camera }}</option>
      </select>
      <img v-if="previewCamera != ''" :src="preview" alt="Preview placeholder" class="container"> 
    </div>
    <br>
    <details>
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
import { ref } from 'vue'
import { useGeocamStore } from '@/stores/geocam'

// Reactive state.
const store = useGeocamStore()
const awbEnabled = ref('False')
const previewCamera = ref('')
const preview = ref("https://picsum.photos/800/600")

function settingChanged(event) {
    console.log(event.target.id + " changed to " + event.target.value)
}

</script>

<style scoped>
.scrollable{
    overflow-y: auto;
    max-height: 300px;
}

</style>
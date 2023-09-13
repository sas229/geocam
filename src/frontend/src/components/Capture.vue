<template>
    <main>
        <div class="grid">
            <input @change="isNameValid" type="text" placeholder="Name" :aria-invalid="!nameValid" v-model="name" data-tooltip="Image series name...">
            <input @change="isNumberValid" type="number" placeholder="Number" min="1" step="1" :aria-invalid="!numberValid" v-model="number" data-tooltip="Number of images to capture...">
            <input @change="isIntervalValid" type="number" placeholder="Interval" min="0" step="0.1" :aria-invalid="!intervalValid" v-model="interval" data-tooltip="Interval between images...">
            <button @click="captureImages" :disabled="!captureSettingsValid" data-tooltip="Capture images...">Capture</button>
            <button @click="recoverImages" class="secondary" :disabled="!captureSettingsValid" data-tooltip="Recover images...">Recover</button>
        </div>
        <label>
            <input type="checkbox" id="recover" name="recover" v-model="recover">
            Recover images on-the-fly?
        </label>
    </main>
    <div v-if="capturingImages">
    <dialog open>
      <article class="fixedWidth">
        <h3>Capturing images...</h3>
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

const name = ref('')
const number = ref(0)
const interval = ref(0)
const nameValid = ref(false)
const numberValid = ref(false)
const intervalValid = ref(false)
const captureSettingsValid = ref(false)
const capturingImages = ref(false)
const logMessage = ref('')
const recover = ref(false)

function isNameValid() {
  console.log("Checking image name is valid...")
  nameValid.value = name.value != '' ? true :  false
  checkCameraSettings();
}

function isNumberValid() {
  console.log("Checking image number is valid...")
  numberValid.value = number.value > 0 ? true :  false
  checkCameraSettings();
}

function isIntervalValid() {
  console.log("Checking image capture interval is valid...")
  intervalValid.value = interval.value != '' ? true :  false
  checkCameraSettings();
}

function checkCameraSettings() {
    if (nameValid.value && numberValid.value && intervalValid.value) {
        captureSettingsValid.value = true;
    } else {
        captureSettingsValid.value = false;
    }
}

function toggleCapturingImages() {
    capturingImages.value = !capturingImages.value;
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

async function captureImages() {
  logMessage.value = 'Connecting to server';
  toggleCapturingImages();
  try {
    let data = {
      name: name.value,
      number: number.value,
      interval: interval.value,
      recover: recover.value,
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
    await axios({
      method: 'post',
      url: '/captureImages',
      data: data
    });
    clearInterval(logMessageInterval);
    toggleCapturingImages();
  } catch (error) {
    console.error(error);
  }
}

function recoverImages() {
    console.log("Recovering images...");
}

</script>
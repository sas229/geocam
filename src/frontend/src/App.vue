<template>
  <main class="container">
    <br>
    <header>
      <hgroup>
        <h1>geocam</h1>
        <h2>Network based camera control software for the RPi</h2>
      </hgroup>
    </header>
    <nav aria-label="breadcrumb">
      <ul>
          <li @click="clickedNav"><a>About</a></li>
          <li @click="clickedNav"><a>Cameras</a></li>
          <li @click="clickedNav" v-if="Object.keys(store.cameras).length > 0"><a>Preview</a></li>
          <li @click="clickedNav" v-if="Object.keys(store.cameras).length > 0"><a>Capture</a></li>
      </ul>
      <br>
    </nav>
    <KeepAlive>
      <Cameras v-if="currentComponent === 'Cameras'"/>
    </KeepAlive>
    <KeepAlive>
      <Preview v-if="currentComponent === 'Preview'"/>
    </KeepAlive>
    <KeepAlive>
      <Capture v-if="currentComponent === 'Capture'"/>
    </KeepAlive>
    <KeepAlive>
      <About v-if="currentComponent === 'About'"/>
    </KeepAlive>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import Cameras from './components/Cameras.vue'
import Preview from './components/Preview.vue'
import Capture from './components/Capture.vue'
import About from './components/About.vue'
import { useGeocamStore } from '@/stores/geocam'

const store = useGeocamStore()

const currentComponent = ref('About')

function clickedNav(event) {
  console.log(event.target.innerText)
  currentComponent.value = event.target.innerText
}
</script>
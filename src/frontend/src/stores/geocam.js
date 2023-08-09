import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useGeocamStore = defineStore('geocam', () => {
  const cameras = ref({})
  const settings = ref({})

  return {cameras, settings }
})
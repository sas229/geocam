import { defineStore } from 'pinia'

export const useGeocamStore = defineStore('geocam', {
  state: () => {
    return { 
      cameras: {},
   }
  },
})
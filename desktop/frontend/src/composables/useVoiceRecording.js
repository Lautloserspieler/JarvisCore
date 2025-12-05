/**
 * Voice Recording Composable
 * Verwaltet Audio-Aufnahme mit Wails Backend
 */

import { ref, computed } from 'vue'
import { useWails } from './useWails'

export function useVoiceRecording() {
  const { api, wailsReady } = useWails()
  
  const isRecording = ref(false)
  const recordingDuration = ref(0)
  const isProcessing = ref(false)
  const error = ref(null)
  
  let durationInterval = null
  
  // Start Recording
  const startRecording = async () => {
    error.value = null
    
    try {
      if (!wailsReady.value) {
        throw new Error('Wails nicht bereit')
      }
      
      // Backend API-Call
      await window.go.app.App.StartRecording()
      
      isRecording.value = true
      recordingDuration.value = 0
      
      // Duration-Timer starten
      durationInterval = setInterval(async () => {
        if (wailsReady.value) {
          const duration = await window.go.app.App.GetRecordingDuration()
          recordingDuration.value = duration
        } else {
          recordingDuration.value += 0.1
        }
      }, 100)
      
    } catch (err) {
      error.value = err.message
      console.error('Recording Start Error:', err)
      throw err
    }
  }
  
  // Stop Recording
  const stopRecording = async () => {
    isProcessing.value = true
    
    // Duration-Timer stoppen
    if (durationInterval) {
      clearInterval(durationInterval)
      durationInterval = null
    }
    
    try {
      if (!wailsReady.value) {
        throw new Error('Wails nicht bereit')
      }
      
      // Backend API-Call
      const transcription = await window.go.app.App.StopRecording()
      
      isRecording.value = false
      recordingDuration.value = 0
      isProcessing.value = false
      
      return transcription
      
    } catch (err) {
      error.value = err.message
      console.error('Recording Stop Error:', err)
      isRecording.value = false
      isProcessing.value = false
      throw err
    }
  }
  
  // Cancel Recording
  const cancelRecording = async () => {
    if (durationInterval) {
      clearInterval(durationInterval)
      durationInterval = null
    }
    
    try {
      if (wailsReady.value && isRecording.value) {
        await window.go.app.App.StopRecording()
      }
    } catch (err) {
      console.error('Cancel Error:', err)
    }
    
    isRecording.value = false
    recordingDuration.value = 0
    isProcessing.value = false
    error.value = null
  }
  
  // Formatted Duration
  const formattedDuration = computed(() => {
    const seconds = Math.floor(recordingDuration.value)
    const ms = Math.floor((recordingDuration.value % 1) * 10)
    return `${seconds}.${ms}s`
  })
  
  return {
    isRecording,
    isProcessing,
    recordingDuration,
    formattedDuration,
    error,
    startRecording,
    stopRecording,
    cancelRecording
  }
}

<template>
  <div class="chat-container">
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="msg in messages" 
        :key="msg.id"
        :class="['message', msg.role]"
      >
        <div class="message-header">
          <span class="role">{{ msg.role === 'user' ? 'Du' : 'J.A.R.V.I.S.' }}</span>
          <span class="timestamp">{{ formatTime(msg.timestamp) }}</span>
        </div>
        <div class="message-text">{{ msg.text }}</div>
      </div>
      
      <div v-if="isProcessing" class="message assistant typing">
        <div class="message-header">
          <span class="role">J.A.R.V.I.S.</span>
        </div>
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
    
    <div class="input-area">
      <button 
        class="voice-btn"
        :class="{ active: isListening }"
        @click="toggleListening"
        title="Spracherkennung"
      >
        🎤
      </button>
      
      <input 
        type="text"
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="Nachricht an J.A.R.V.I.S..."
        :disabled="isProcessing"
      />
      
      <button 
        class="send-btn"
        @click="sendMessage"
        :disabled="!userInput.trim() || isProcessing"
      >
        Senden
      </button>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted } from 'vue'

export default {
  name: 'Chat',
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const isProcessing = ref(false)
    const isListening = ref(false)
    const messagesContainer = ref(null)
    
    const sendMessage = async () => {
      const text = userInput.value.trim()
      if (!text || isProcessing.value) return
      
      messages.value.push({
        id: Date.now(),
        role: 'user',
        text: text,
        timestamp: Date.now()
      })
      
      userInput.value = ''
      isProcessing.value = true
      scrollToBottom()
      
      try {
        // TODO: Wails Backend-Call aktivieren
        // const response = await window.go.app.App.ProcessCommand(text)
        
        await new Promise(resolve => setTimeout(resolve, 1000))
        const response = `Du hast gesagt: "${text}"`
        
        messages.value.push({
          id: Date.now() + 1,
          role: 'assistant',
          text: response,
          timestamp: Date.now()
        })
      } catch (error) {
        console.error('Fehler:', error)
        messages.value.push({
          id: Date.now() + 1,
          role: 'assistant',
          text: `Fehler: ${error.message}`,
          timestamp: Date.now()
        })
      } finally {
        isProcessing.value = false
        scrollToBottom()
      }
    }
    
    const toggleListening = () => {
      isListening.value = !isListening.value
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
      })
    }
    
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('de-DE', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
    
    onMounted(() => {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        text: 'Hallo! Ich bin J.A.R.V.I.S. Wie kann ich dir helfen?',
        timestamp: Date.now()
      })
    })
    
    return {
      messages,
      userInput,
      isProcessing,
      isListening,
      messagesContainer,
      sendMessage,
      toggleListening,
      formatTime
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  padding: 16px;
  border-radius: 12px;
  max-width: 70%;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
  background: var(--accent);
  color: white;
}

.message.assistant {
  align-self: flex-start;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.85em;
  opacity: 0.7;
}

.message-text {
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 20px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.voice-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--accent);
  background: transparent;
  color: var(--accent);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.voice-btn:hover {
  background: var(--accent);
  color: white;
}

.voice-btn.active {
  background: var(--accent);
  color: white;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--accent);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(0, 180, 216, 0);
  }
}

input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 24px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: var(--accent);
}

.send-btn {
  padding: 12px 24px;
  border-radius: 24px;
  border: none;
  background: var(--accent);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

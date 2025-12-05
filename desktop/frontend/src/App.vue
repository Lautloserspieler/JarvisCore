<template>
  <div id="app" class="dark-theme">
    <!-- Security Challenge Overlay (Global) -->
    <SecurityChallenge />
    
    <Sidebar 
      :currentView="currentView"
      @change-view="changeView"
    />
    
    <main class="main-content">
      <StatusBar />
      
      <div class="view-container">
        <Chat v-if="currentView === 'chat'" />
        <SystemMonitor v-else-if="currentView === 'system'" />
        <ModelManager v-else-if="currentView === 'models'" />
        <PluginManager v-else-if="currentView === 'plugins'" />
        <Knowledge v-else-if="currentView === 'knowledge'" />
        <Memory v-else-if="currentView === 'memory'" />
        <Logs v-else-if="currentView === 'logs'" />
        <Training v-else-if="currentView === 'training'" />
        <CustomCommands v-else-if="currentView === 'commands'" />
        <Settings v-else-if="currentView === 'settings'" />
      </div>
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import StatusBar from './components/StatusBar.vue'
import SecurityChallenge from './components/SecurityChallenge.vue'
import Chat from './components/Chat.vue'
import SystemMonitor from './components/SystemMonitor.vue'
import ModelManager from './components/ModelManager.vue'
import PluginManager from './components/PluginManager.vue'
import Knowledge from './components/Knowledge.vue'
import Memory from './components/Memory.vue'
import Logs from './components/Logs.vue'
import Training from './components/Training.vue'
import CustomCommands from './components/CustomCommands.vue'
import Settings from './components/Settings.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    StatusBar,
    SecurityChallenge,
    Chat,
    SystemMonitor,
    ModelManager,
    PluginManager,
    Knowledge,
    Memory,
    Logs,
    Training,
    CustomCommands,
    Settings
  },
  setup() {
    const currentView = ref('chat')
    
    const changeView = (view) => {
      currentView.value = view
      console.log(`📦 Switched to view: ${view}`)
    }
    
    return {
      currentView,
      changeView
    }
  }
}
</script>

<style>
@import './assets/main.css';

#app {
  display: flex;
  height: 100vh;
  overflow: hidden;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  position: relative;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.view-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Scrollbar Styling */
.view-container::-webkit-scrollbar {
  width: 8px;
}

.view-container::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

.view-container::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.view-container::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
}
</style>

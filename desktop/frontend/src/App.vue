<template>
  <div id="app" class="dark-theme">
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
        <Settings v-else-if="currentView === 'settings'" />
      </div>
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import StatusBar from './components/StatusBar.vue'
import Chat from './components/Chat.vue'
import SystemMonitor from './components/SystemMonitor.vue'
import ModelManager from './components/ModelManager.vue'
import PluginManager from './components/PluginManager.vue'
import Settings from './components/Settings.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    StatusBar,
    Chat,
    SystemMonitor,
    ModelManager,
    PluginManager,
    Settings
  },
  setup() {
    const currentView = ref('chat')
    
    const changeView = (view) => {
      currentView.value = view
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
</style>

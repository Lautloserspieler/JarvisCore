<template>
  <div class="sidebar">
    <div class="logo">
      <h1>J.A.R.V.I.S.</h1>
      <p>Desktop</p>
    </div>
    
    <nav class="nav-menu">
      <button 
        v-for="item in menuItems"
        :key="item.id"
        :class="['nav-item', { active: currentView === item.id }]"
        @click="$emit('change-view', item.id)"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="label">{{ item.label }}</span>
      </button>
    </nav>
    
    <div class="sidebar-footer">
      <button class="settings-btn" @click="$emit('change-view', 'settings')">
        ⚙️ Einstellungen
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    currentView: String
  },
  emits: ['change-view'],
  setup() {
    const menuItems = [
      { id: 'chat', icon: '💬', label: 'Chat' },
      { id: 'system', icon: '📊', label: 'System' },
      { id: 'models', icon: '🧠', label: 'Modelle' },
      { id: 'plugins', icon: '🔌', label: 'Plugins' }
    ]
    
    return {
      menuItems
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
}

.logo {
  padding: 32px 24px;
  border-bottom: 1px solid var(--border-color);
}

.logo h1 {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, var(--accent), var(--accent-hover));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo p {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.nav-menu {
  flex: 1;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
  font-size: 14px;
}

.nav-item:hover {
  background: var(--bg-hover);
}

.nav-item.active {
  background: var(--accent);
  color: white;
}

.icon {
  font-size: 20px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.settings-btn {
  width: 100%;
  padding: 12px;
  border: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.settings-btn:hover {
  background: var(--bg-hover);
}
</style>

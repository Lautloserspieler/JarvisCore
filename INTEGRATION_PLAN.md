# 🔗 JARVIS Core - UI Integration Plan

## 📊 Projekt-Analyse

### Aktueller Status

#### ✅ Fertiggestellt (100%)

**Frontend Struktur:**
```
frontend/src/
├── components/
│   ├── ui/                 # 45+ shadcn/ui Komponenten ✅
│   ├── tabs/               # 7 Tab-Komponenten ✅
│   │   ├── ChatTab.tsx
│   │   ├── DashboardTab.tsx
│   │   ├── LogsTab.tsx
│   │   ├── MemoryTab.tsx
│   │   ├── ModelsTab.tsx
│   │   ├── PluginsTab.tsx
│   │   └── SettingsTab.tsx
│   ├── ChatInput.tsx       ✅
│   ├── ChatMessage.tsx     ✅
│   ├── JarvisCore.tsx      ✅
│   ├── QuickActions.tsx    ✅
│   ├── StatusPanel.tsx     ✅
│   └── VoiceVisualizer.tsx ✅
├── services/
│   ├── api.ts              # Base API Client ✅
│   ├── websocket.ts        # WebSocket Manager ✅
│   ├── chatService.ts      # Chat API ✅
│   ├── modelService.ts     # Model API ✅
│   ├── pluginService.ts    # Plugin API ✅
│   ├── memoryService.ts    # Memory API ✅
│   ├── logService.ts       # Log API ✅
│   └── index.ts            # Central Export ✅
├── hooks/
│   ├── useWebSocket.ts     # WebSocket Hook ✅
│   ├── useChat.ts          # Chat Hook ✅
│   └── use-toast.ts        # Toast Hook ✅
├── pages/
│   ├── Index.tsx           # Main Page ✅
│   └── NotFound.tsx        # 404 Page ✅
└── lib/
    └── utils.ts            # Utilities ✅
```

**Backend API:**
- FastAPI Server ✅
- WebSocket Endpoint ✅
- REST API Endpoints ✅
- Mock Data Responses ✅

---

## 🎯 Integrations-Strategie

### Phase 1: Chat Integration (Priorität: HOCH) 🔴

**Ziel:** Live-Chat mit Backend verbinden

**Aktueller Zustand:**
- ❌ ChatTab.tsx verwendet Mock-Daten
- ❌ Keine WebSocket-Verbindung
- ❌ Keine persistente Chat-Historie

**Integration Steps:**

#### Step 1.1: ChatTab mit useChat Hook verbinden
```typescript
// ChatTab.tsx - VORHER
const [messages, setMessages] = useState(mockMessages);
const handleSend = (message: string) => {
  // Mock implementation
};

// ChatTab.tsx - NACHHER
import { useChat } from '@/hooks/useChat';

const ChatTab = ({ onStateChange }) => {
  const { messages, sendMessage, isTyping, isConnected } = useChat();
  
  const handleSend = (message: string) => {
    sendMessage(message);
    onStateChange?.('processing');
  };
  
  // Auto-update Core state based on typing
  useEffect(() => {
    if (isTyping) onStateChange?.('processing');
    else if (messages.length > 0) onStateChange?.('speaking');
    else onStateChange?.('idle');
  }, [isTyping, messages]);
};
```

#### Step 1.2: ChatMessage mit echten Timestamps
```typescript
// ChatMessage.tsx Enhancement
const ChatMessage = ({ message }) => {
  const formattedTime = useMemo(() => {
    return new Date(message.timestamp).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, [message.timestamp]);
  
  return (
    <div>
      {/* ... */}
      <span className="text-xs text-muted-foreground">{formattedTime}</span>
    </div>
  );
};
```

#### Step 1.3: WebSocket Connection Status
```typescript
// Add to Index.tsx
import { useWebSocket } from '@/hooks/useWebSocket';

const Index = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  useWebSocket({
    onConnect: () => setConnectionStatus('connected'),
    onDisconnect: () => setConnectionStatus('disconnected'),
    onError: () => setConnectionStatus('error'),
  });
  
  return (
    <header>
      {/* ... */}
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${
          connectionStatus === 'connected' ? 'bg-green-500' :
          connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500'
        } animate-pulse`} />
        <span className="text-xs">{connectionStatus.toUpperCase()}</span>
      </div>
    </header>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/ChatTab.tsx`
- [ ] `frontend/src/components/ChatMessage.tsx`
- [ ] `frontend/src/pages/Index.tsx`

---

### Phase 2: Model Management (Priorität: MITTEL) 🟡

**Ziel:** AI-Model Switching & Testing

**Integration Steps:**

#### Step 2.1: ModelsTab API Integration
```typescript
// ModelsTab.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelService } from '@/services';

const ModelsTab = () => {
  const queryClient = useQueryClient();
  
  // Get all models
  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => modelService.getModels(),
  });
  
  // Set active model
  const activateModelMutation = useMutation({
    mutationFn: (modelId: string) => modelService.setActiveModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      toast({ title: 'Model activated successfully' });
    },
  });
  
  // Test model
  const testModelMutation = useMutation({
    mutationFn: ({ modelId, prompt }: { modelId: string; prompt: string }) => 
      modelService.testModel(modelId, prompt),
    onSuccess: (data) => {
      toast({ 
        title: 'Model test completed',
        description: `Response time: ${data.responseTime}ms`
      });
    },
  });
  
  return (
    <div>
      {models?.map(model => (
        <ModelCard
          key={model.id}
          model={model}
          onActivate={() => activateModelMutation.mutate(model.id)}
          onTest={(prompt) => testModelMutation.mutate({ modelId: model.id, prompt })}
        />
      ))}
    </div>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/ModelsTab.tsx`
- [ ] Create: `frontend/src/components/ModelCard.tsx`

---

### Phase 3: Plugin System (Priorität: MITTEL) 🟡

**Integration Steps:**

#### Step 3.1: PluginsTab mit Real-Time Updates
```typescript
// PluginsTab.tsx
import { pluginService } from '@/services';
import { useQuery, useMutation } from '@tanstack/react-query';

const PluginsTab = () => {
  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => pluginService.getPlugins(),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });
  
  const togglePluginMutation = useMutation({
    mutationFn: ({ pluginId, enable }: { pluginId: string; enable: boolean }) => 
      enable ? pluginService.enablePlugin(pluginId) : pluginService.disablePlugin(pluginId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
    },
  });
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {plugins?.map(plugin => (
        <PluginCard
          key={plugin.id}
          plugin={plugin}
          onToggle={(enable) => togglePluginMutation.mutate({ pluginId: plugin.id, enable })}
        />
      ))}
    </div>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/PluginsTab.tsx`
- [ ] Create: `frontend/src/components/PluginCard.tsx`

---

### Phase 4: Memory System (Priorität: MITTEL) 🟡

**Integration Steps:**

#### Step 4.1: Memory Search & Management
```typescript
// MemoryTab.tsx
import { memoryService } from '@/services';
import { useState } from 'react';

const MemoryTab = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string | undefined>();
  
  const { data: memories } = useQuery({
    queryKey: ['memories', selectedType],
    queryFn: () => memoryService.getMemories(selectedType),
  });
  
  const { data: stats } = useQuery({
    queryKey: ['memory-stats'],
    queryFn: () => memoryService.getStats(),
  });
  
  const searchMutation = useMutation({
    mutationFn: (query: string) => memoryService.searchMemories({ query, limit: 50 }),
  });
  
  const deleteMemoryMutation = useMutation({
    mutationFn: (memoryId: string) => memoryService.deleteMemory(memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    },
  });
  
  return (
    <div>
      <MemoryStats stats={stats} />
      <MemorySearch onSearch={(q) => searchMutation.mutate(q)} />
      <MemoryList 
        memories={searchMutation.data || memories}
        onDelete={(id) => deleteMemoryMutation.mutate(id)}
      />
    </div>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/MemoryTab.tsx`
- [ ] Create: `frontend/src/components/MemoryCard.tsx`
- [ ] Create: `frontend/src/components/MemorySearch.tsx`

---

### Phase 5: Logs & Monitoring (Priorität: NIEDRIG) 🟢

**Integration Steps:**

#### Step 5.1: Real-Time Log Streaming
```typescript
// LogsTab.tsx
import { logService } from '@/services';
import { useWebSocket } from '@/hooks/useWebSocket';

const LogsTab = () => {
  const [filters, setFilters] = useState<LogFilter>({ level: [], category: [] });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  // Fetch historical logs
  const { data: historicalLogs } = useQuery({
    queryKey: ['logs', filters],
    queryFn: () => logService.getLogs(filters),
  });
  
  // Real-time log streaming via WebSocket
  useWebSocket({
    onMessage: (data) => {
      if (data.type === 'log_entry') {
        setLogs(prev => [data.log, ...prev].slice(0, 100)); // Keep last 100
      }
    },
  });
  
  const exportLogsMutation = useMutation({
    mutationFn: () => logService.exportLogs(filters),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jarvis-logs-${new Date().toISOString()}.csv`;
      a.click();
    },
  });
  
  return (
    <div>
      <LogFilters filters={filters} onChange={setFilters} />
      <Button onClick={() => exportLogsMutation.mutate()}>Export Logs</Button>
      <LogList logs={[...logs, ...(historicalLogs || [])]} />
    </div>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/LogsTab.tsx`
- [ ] Create: `frontend/src/components/LogFilters.tsx`

---

### Phase 6: Dashboard Integration (Priorität: NIEDRIG) 🟢

**Integration Steps:**

#### Step 6.1: Real-Time Statistics
```typescript
// DashboardTab.tsx
import { useQuery } from '@tanstack/react-query';
import { modelService, pluginService, memoryService, logService } from '@/services';

const DashboardTab = () => {
  // Aggregate all stats
  const { data: modelStats } = useQuery({
    queryKey: ['model-stats'],
    queryFn: async () => {
      const models = await modelService.getModels();
      const active = models.find(m => m.isActive);
      return active ? await modelService.getModelStats(active.id) : null;
    },
    refetchInterval: 10000,
  });
  
  const { data: memoryStats } = useQuery({
    queryKey: ['memory-stats'],
    queryFn: () => memoryService.getStats(),
    refetchInterval: 10000,
  });
  
  const { data: logStats } = useQuery({
    queryKey: ['log-stats'],
    queryFn: () => logService.getStats(),
    refetchInterval: 10000,
  });
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatCard title="Model Performance" data={modelStats} />
      <StatCard title="Memory Usage" data={memoryStats} />
      <StatCard title="System Logs" data={logStats} />
    </div>
  );
};
```

**Dateien zu ändern:**
- [ ] `frontend/src/components/tabs/DashboardTab.tsx`
- [ ] Create: `frontend/src/components/StatCard.tsx`

---

## 🔧 Technische Implementierung

### Custom Hooks zu erstellen

#### 1. `useModels` Hook
```typescript
// frontend/src/hooks/useModels.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelService } from '@/services';

export const useModels = () => {
  const queryClient = useQueryClient();
  
  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => modelService.getModels(),
  });
  
  const activateModel = useMutation({
    mutationFn: (modelId: string) => modelService.setActiveModel(modelId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  });
  
  const testModel = useMutation({
    mutationFn: ({ modelId, prompt }: { modelId: string; prompt: string }) =>
      modelService.testModel(modelId, prompt),
  });
  
  return {
    models,
    isLoading,
    activateModel: activateModel.mutate,
    testModel: testModel.mutate,
    activeModel: models?.find(m => m.isActive),
  };
};
```

#### 2. `usePlugins` Hook
```typescript
// frontend/src/hooks/usePlugins.ts
export const usePlugins = () => {
  // Similar structure as useModels
};
```

#### 3. `useMemory` Hook
```typescript
// frontend/src/hooks/useMemory.ts
export const useMemory = () => {
  // Similar structure as useModels
};
```

#### 4. `useLogs` Hook
```typescript
// frontend/src/hooks/useLogs.ts
export const useLogs = () => {
  // Similar structure as useModels
};
```

---

## 📋 Checkliste: Integration Steps

### Phase 1: Chat (Woche 1)
- [ ] ChatTab mit useChat verbinden
- [ ] WebSocket Status-Anzeige
- [ ] Typing Indicator implementieren
- [ ] Chat-Historie persistieren
- [ ] Error Handling für Nachricht-Fehler

### Phase 2: Models (Woche 1-2)
- [ ] ModelsTab API-Integration
- [ ] Model-Switching Funktionalität
- [ ] Model-Testing Interface
- [ ] useModels Hook erstellen
- [ ] Model Statistics Display

### Phase 3: Plugins (Woche 2)
- [ ] PluginsTab API-Integration
- [ ] Plugin Enable/Disable
- [ ] Plugin Configuration UI
- [ ] usePlugins Hook erstellen
- [ ] Plugin Statistics

### Phase 4: Memory (Woche 2-3)
- [ ] MemoryTab API-Integration
- [ ] Memory Search funktional
- [ ] Memory CRUD Operations
- [ ] useMemory Hook erstellen
- [ ] Memory Visualization

### Phase 5: Logs (Woche 3)
- [ ] LogsTab API-Integration
- [ ] Real-Time Log Streaming
- [ ] Log Filtering
- [ ] useLogs Hook erstellen
- [ ] Log Export Funktion

### Phase 6: Dashboard (Woche 3)
- [ ] Dashboard API-Integration
- [ ] Real-Time Stats
- [ ] Chart Komponenten
- [ ] Performance Metrics

---

## 🚀 Deployment Strategie

### Development
```bash
# Start Development Environment
python main.py
```

### Testing
```bash
# Frontend Tests
cd frontend && npm run test

# Backend Tests
cd backend && pytest
```

### Production Build
```bash
# Frontend Production Build
cd frontend && npm run build

# Backend Production
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Prioritäten-Matrix

| Feature | Priorität | Aufwand | Impact | Status |
|---------|-----------|---------|--------|--------|
| Chat Integration | 🔴 HOCH | 2d | HOCH | ⏳ TODO |
| Model Management | 🟡 MITTEL | 3d | HOCH | ⏳ TODO |
| Plugin System | 🟡 MITTEL | 3d | MITTEL | ⏳ TODO |
| Memory System | 🟡 MITTEL | 2d | MITTEL | ⏳ TODO |
| Logs & Monitoring | 🟢 NIEDRIG | 2d | NIEDRIG | ⏳ TODO |
| Dashboard | 🟢 NIEDRIG | 2d | NIEDRIG | ⏳ TODO |

---

## 🎯 Success Criteria

### Chat
- ✅ Messages send & receive in real-time
- ✅ WebSocket connection stable
- ✅ Typing indicators work
- ✅ Message history persists

### Models
- ✅ Can switch between models
- ✅ Model testing works
- ✅ Statistics display correctly

### Plugins
- ✅ Can enable/disable plugins
- ✅ Plugin config updates work
- ✅ Plugin stats visible

### Memory
- ✅ Search returns relevant results
- ✅ CRUD operations work
- ✅ Stats accurate

### Logs
- ✅ Real-time logs stream
- ✅ Filtering works
- ✅ Export successful

---

## 📝 Nächste Schritte

1. **START:** Phase 1 - Chat Integration
2. Erstelle `useModels`, `usePlugins`, `useMemory`, `useLogs` Hooks
3. Update alle Tab-Komponenten mit echten API-Calls
4. Teste jede Integration einzeln
5. Ende-zu-Ende Testing
6. Performance Optimierung
7. Production Deployment

---

**Geschätzte Gesamtdauer:** 3-4 Wochen
**Entwickler:** 1 Full-Stack Developer

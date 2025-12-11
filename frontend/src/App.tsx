import React, { useEffect, useState, useRef } from 'react'
import './App.css'
import VoiceVisualizer from './components/VoiceVisualizer'

interface Message {
  id: string
  type: 'user' | 'assistant'
  text: string
  timestamp: Date
}

interface SystemMetrics {
  cpu: number
  memory: number
  gpu?: number
  temperature?: number
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
  })
  const [activeTab, setActiveTab] = useState<'chat' | 'dashboard' | 'settings'>('chat')
  const [llmStatus, setLlmStatus] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    const socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log('WebSocket connected')
      setWs(socket)
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WS message:', data)

      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'assistant',
          text: data.response || data.text,
          timestamp: new Date(),
        }])
        setIsProcessing(false)
      } else if (data.type === 'state_change') {
        if (data.state === 'listening') setIsListening(true)
        else if (data.state === 'idle') setIsListening(false)
        else if (data.state === 'processing') setIsProcessing(true)
      } else if (data.type === 'metrics_update') {
        setSystemMetrics(data.data)
      }
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    socket.onclose = () => {
      console.log('WebSocket disconnected')
      setWs(null)
    }

    // Fetch LLM status
    fetchLlmStatus()

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchLlmStatus = async () => {
    try {
      const response = await fetch('/api/llm/status')
      const data = await response.json()
      setLlmStatus(data)
    } catch (error) {
      console.error('Failed to fetch LLM status:', error)
    }
  }

  const sendMessage = () => {
    if (!inputValue.trim() || !ws) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      text: inputValue,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)

    ws.send(JSON.stringify({
      type: 'chat',
      text: inputValue,
    }))

    setInputValue('')
  }

  const handleVoiceStart = () => {
    if (ws) {
      setIsListening(true)
      ws.send(JSON.stringify({ type: 'voice_start' }))
    }
  }

  const handleVoiceEnd = () => {
    if (ws) {
      setIsListening(false)
      ws.send(JSON.stringify({ type: 'voice_end' }))
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <h1>🤖 J.A.R.V.I.S.</h1>
            <p className="tagline">Just A Rather Very Intelligent System</p>
          </div>
          <div className="header-status">
            <div className={`status-indicator ${isListening ? 'listening' : isProcessing ? 'processing' : 'idle'}`}>
              <span className="pulse"></span>
              {isListening ? 'Listening' : isProcessing ? 'Processing' : 'Ready'}
            </div>
          </div>
        </div>
      </header>

      <div className="app-content">
        {/* Sidebar */}
        <aside className="sidebar">
          <nav className="nav-tabs">
            <button
              className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 Chat
            </button>
            <button
              className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 Dashboard
            </button>
            <button
              className={`nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              ⚙️ Settings
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {activeTab === 'chat' && (
            <div className="chat-panel">
              {/* Messages */}
              <div className="messages-container">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">🤖</div>
                    <p>Start a conversation with JARVIS</p>
                    <p className="empty-subtitle">Use voice or text to communicate</p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <div key={msg.id} className={`message ${msg.type}`}>
                        <div className="message-content">
                          <p>{msg.text}</p>
                          <span className="message-time">{msg.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Voice Visualizer */}
              {isListening && (
                <div className="voice-viz">
                  <VoiceVisualizer isActive={isListening} barCount={20} />
                </div>
              )}

              {/* Input Area */}
              <div className="input-section">
                <div className="input-group">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type a message or use voice..."
                    disabled={!ws}
                    className="text-input"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!ws || !inputValue.trim() || isProcessing}
                    className="send-btn"
                  >
                    ↑ Send
                  </button>
                </div>
                <div className="voice-controls">
                  <button
                    onMouseDown={handleVoiceStart}
                    onMouseUp={handleVoiceEnd}
                    onTouchStart={handleVoiceStart}
                    onTouchEnd={handleVoiceEnd}
                    disabled={!ws}
                    className={`voice-btn ${isListening ? 'active' : ''}`}
                  >
                    🎙️ Voice
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'dashboard' && (
            <div className="dashboard-panel">
              <h2>System Dashboard</h2>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">CPU Usage</div>
                  <div className="metric-value">{systemMetrics.cpu.toFixed(1)}%</div>
                  <div className="metric-bar">
                    <div className="metric-fill" style={{ width: `${systemMetrics.cpu}%` }}></div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Memory Usage</div>
                  <div className="metric-value">{systemMetrics.memory.toFixed(1)}%</div>
                  <div className="metric-bar">
                    <div className="metric-fill" style={{ width: `${systemMetrics.memory}%` }}></div>
                  </div>
                </div>
              </div>
              {llmStatus && (
                <div className="llm-status">
                  <h3>LLM Status</h3>
                  <p><strong>Current Model:</strong> {llmStatus.current || 'None'}</p>
                  <p><strong>Status:</strong> {llmStatus.active ? 'Active' : 'Inactive'}</p>
                  <p><strong>Loaded Models:</strong> {llmStatus.loaded?.join(', ') || 'None'}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-panel">
              <h2>Settings</h2>
              <div className="settings-content">
                <p>Settings coming soon...</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App

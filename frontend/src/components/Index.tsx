import React, { useEffect, useState, useRef } from 'react'
import '../styles/Index.css'
import VoiceVisualizer from './VoiceVisualizer'

interface Message {
  id: string
  type: 'user' | 'assistant'
  text: string
  timestamp: Date
}

interface SystemStatus {
  cpu: number
  memory: number
  temperature: number
}

const Index: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [coreState, setCoreState] = useState<'idle' | 'listening' | 'processing' | 'speaking' | 'error'>('idle')
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({ cpu: 0, memory: 0, temperature: 0 })
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'system' | 'settings'>('chat')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    
    const socket = new WebSocket(wsUrl)
    
    socket.onopen = () => {
      console.log('WebSocket connected')
      setCoreState('idle')
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
        setCoreState('idle')
      } else if (data.type === 'state_change') {
        setCoreState(data.state || 'idle')
      } else if (data.type === 'system_status') {
        setSystemStatus(data.data)
      }
    }
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setCoreState('error')
    }
    
    socket.onclose = () => {
      console.log('WebSocket disconnected')
      setWs(null)
      setCoreState('error')
    }
    
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!inputValue.trim() || !ws || coreState === 'processing' || coreState === 'speaking') return
    
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      text: inputValue,
      timestamp: new Date(),
    }
    
    setMessages(prev => [...prev, userMessage])
    setCoreState('processing')
    
    ws.send(JSON.stringify({
      type: 'chat',
      text: inputValue,
    }))
    
    setInputValue('')
  }

  const handleVoiceStart = () => {
    if (ws && coreState === 'idle') {
      setCoreState('listening')
      ws.send(JSON.stringify({ type: 'voice_start' }))
    }
  }

  const handleVoiceEnd = () => {
    if (ws) {
      setCoreState('processing')
      ws.send(JSON.stringify({ type: 'voice_end' }))
    }
  }

  return (
    <div className="jarvis-container">
      {/* Header */}
      <header className="jarvis-header glow-primary">
        <div className="header-content">
          <h1 className="jarvis-title glow-text">🤖 J.A.R.V.I.S.</h1>
          <div className="core-status">
            <div className={`status-ring ${coreState}`}>
              <div className="status-ring-inner"></div>
              <span className="status-text">
                {coreState === 'idle' && 'Awaiting Input'}
                {coreState === 'listening' && 'Listening...'}
                {coreState === 'processing' && 'Processing Request'}
                {coreState === 'speaking' && 'Generating Response'}
                {coreState === 'error' && 'Error Occurred'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="jarvis-main">
        {/* Sidebar */}
        <aside className="jarvis-sidebar">
          <nav className="tab-navigation">
            <button
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 Chat
            </button>
            <button
              className={`tab-btn ${activeTab === 'system' ? 'active' : ''}`}
              onClick={() => setActiveTab('system')}
            >
              📊 System
            </button>
            <button
              className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              ⚙️ Settings
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="jarvis-content">
          {activeTab === 'chat' && (
            <div className="chat-section">
              {/* Messages */}
              <div className="messages-area">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">🤖</div>
                    <h2>Welcome to J.A.R.V.I.S.</h2>
                    <p>Start a conversation using voice or text</p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <div key={msg.id} className={`message message-${msg.type}`}>
                        <div className="message-bubble">
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
              {coreState === 'listening' && (
                <div className="voice-visualizer-container">
                  <VoiceVisualizer isActive={true} />
                </div>
              )}

              {/* Input Controls */}
              <div className="input-controls">
                <div className="input-group">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your message..."
                    disabled={coreState === 'processing' || coreState === 'speaking' || !ws}
                    className="message-input"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || coreState === 'processing' || coreState === 'speaking' || !ws}
                    className="send-btn glow-primary"
                  >
                    ↑ Send
                  </button>
                </div>

                {/* Voice Control */}
                <button
                  onMouseDown={handleVoiceStart}
                  onMouseUp={handleVoiceEnd}
                  onTouchStart={handleVoiceStart}
                  onTouchEnd={handleVoiceEnd}
                  disabled={coreState === 'processing' || coreState === 'speaking' || !ws}
                  className={`voice-btn ${coreState === 'listening' ? 'active' : ''}`}
                >
                  🎙️ Voice
                </button>
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="system-section">
              <h2>System Status</h2>
              <div className="status-grid">
                <div className="status-card">
                  <h3>CPU Usage</h3>
                  <div className="status-bar">
                    <div className="status-fill" style={{ width: `${systemStatus.cpu}%` }}></div>
                  </div>
                  <p className="status-value">{systemStatus.cpu.toFixed(1)}%</p>
                </div>
                <div className="status-card">
                  <h3>Memory Usage</h3>
                  <div className="status-bar">
                    <div className="status-fill" style={{ width: `${systemStatus.memory}%` }}></div>
                  </div>
                  <p className="status-value">{systemStatus.memory.toFixed(1)}%</p>
                </div>
                <div className="status-card">
                  <h3>Temperature</h3>
                  <div className="status-bar">
                    <div className="status-fill" style={{ width: `${Math.min(systemStatus.temperature / 100, 1) * 100}%` }}></div>
                  </div>
                  <p className="status-value">{systemStatus.temperature.toFixed(1)}°C</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-section">
              <h2>Settings</h2>
              <p>Settings panel coming soon...</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default Index

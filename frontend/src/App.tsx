import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState<string>('Connecting...')
  const [messages, setMessages] = useState<Array<{type: string, text: string}>>([]
  const [inputValue, setInputValue] = useState('')
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    
    const socket = new WebSocket(wsUrl)
    
    socket.onopen = () => {
      console.log('WebSocket connected')
      setStatus('Connected')
      setWs(socket)
    }
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WS message:', data)
      
      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, { type: 'assistant', text: data.response || data.text }])
      } else if (data.type === 'state_change') {
        setStatus(data.state || 'Ready')
      }
    }
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setStatus('Error')
    }
    
    socket.onclose = () => {
      console.log('WebSocket disconnected')
      setStatus('Disconnected')
      setWs(null)
    }
    
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [])

  const sendMessage = () => {
    if (!inputValue.trim() || !ws) return
    
    setMessages(prev => [...prev, { type: 'user', text: inputValue }])
    
    ws.send(JSON.stringify({
      type: 'chat',
      text: inputValue
    }))
    
    setInputValue('')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 J.A.R.V.I.S.</h1>
        <p>Status: <span className={`status ${status.toLowerCase()}`}>{status}</span></p>
      </header>
      
      <main className="chat-container">
        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <p>Start a conversation with JARVIS</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`message ${msg.type}`}>
                <p>{msg.text}</p>
              </div>
            ))
          )}
        </div>
        
        <div className="input-area">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message..."
            disabled={!ws}
          />
          <button onClick={sendMessage} disabled={!ws || !inputValue.trim()}>
            Send
          </button>
        </div>
      </main>
    </div>
  )
}

export default App

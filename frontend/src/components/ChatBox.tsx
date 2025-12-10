import { useState, useEffect, useRef } from 'react'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import { sendChatMessage, JarvisWebSocket } from '../lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Willkommen! Wie kann ich Ihnen helfen?',
      timestamp: Date.now(),
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<JarvisWebSocket | null>(null)

  useEffect(() => {
    // WebSocket Connection
    wsRef.current = new JarvisWebSocket(
      'ws://localhost:8000/ws',
      (data) => {
        if (data.type === 'chat_response') {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: data.text,
              timestamp: Date.now(),
            },
          ])
        }
      },
      () => console.log('WebSocket connected'),
      () => console.log('WebSocket disconnected')
    )

    wsRef.current.connect()

    return () => {
      wsRef.current?.disconnect()
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || sending) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: Date.now(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setSending(true)

    try {
      // Send via WebSocket if connected
      if (wsRef.current) {
        wsRef.current.send({
          type: 'chat',
          text: input,
        })
      } else {
        // Fallback to REST API
        const response = await sendChatMessage(input)
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: response.response,
            timestamp: Date.now(),
          },
        ])
      }
    } catch (error: any) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Fehler: ${error.message}`,
          timestamp: Date.now(),
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="jarvis-card jarvis-glow p-6 flex flex-col h-full">
      <div className="flex items-center gap-3 mb-4">
        <MessageSquare className="w-6 h-6 text-jarvis-cyan" />
        <h3 className="text-lg font-bold">Chat</h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-3 min-h-0">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-jarvis-cyan/20 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold">J</span>
              </div>
            )}
            
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-jarvis-cyan/20 border border-jarvis-cyan/50'
                  : 'bg-jarvis-dark/50 border border-jarvis-cyan/20'
              }`}
            >
              <p className="text-sm text-gray-300 whitespace-pre-wrap">
                {msg.content}
              </p>
              <span className="text-xs text-gray-500 mt-1 block">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-jarvis-blue/20 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold">U</span>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Nachricht eingeben..."
          disabled={sending}
          className="jarvis-input"
        />
        <button
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="jarvis-button min-w-[100px]"
        >
          {sending ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto" />
          ) : (
            <div className="flex items-center gap-2">
              <Send className="w-5 h-5" />
              <span>Senden</span>
            </div>
          )}
        </button>
      </div>
    </div>
  )
}

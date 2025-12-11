# JARVIS Core Backend

## Overview
FastAPI backend for JARVIS Core system with WebSocket support and REST API endpoints.

## Features
- ✅ WebSocket for real-time communication
- ✅ REST API endpoints for all services
- ✅ CORS enabled for frontend connection
- ✅ Type-safe with Pydantic models

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health
- `GET /` - Root endpoint
- `GET /api/health` - Health check

### WebSocket
- `WS /ws` - WebSocket connection for real-time communication

### Chat
- `GET /api/chat/sessions` - Get all chat sessions
- `POST /api/chat/sessions` - Create new chat session
- `POST /api/chat/messages` - Send message

### Models
- `GET /api/models` - Get all models
- `GET /api/models/active` - Get active model
- `POST /api/models/{id}/activate` - Set active model

### Plugins
- `GET /api/plugins` - Get all plugins
- `POST /api/plugins/{id}/enable` - Enable plugin
- `POST /api/plugins/{id}/disable` - Disable plugin

### Memory
- `GET /api/memory` - Get memories
- `GET /api/memory/stats` - Get memory statistics
- `POST /api/memory/search` - Search memories

### Logs
- `GET /api/logs` - Get logs
- `GET /api/logs/stats` - Get log statistics

## WebSocket Message Format

### Client to Server
```json
{
  "type": "chat_message",
  "message": "Hello JARVIS",
  "sessionId": "session-id"
}
```

### Server to Client
```json
{
  "type": "chat_response",
  "messageId": "uuid",
  "response": "Hello! How can I help?",
  "sessionId": "session-id",
  "timestamp": "2025-12-11T10:00:00Z"
}
```

## Environment Variables

Create a `.env` file:

```
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

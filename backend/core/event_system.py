"""Centralized event system for JARVIS - handles all UI ↔ Backend communication"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Set, Any, Optional, Callable
from enum import Enum
from fastapi import WebSocket
import logging

logger = logging.getLogger('jarvis.events')

class EventType(str, Enum):
    """All possible event types"""
    # System
    HEARTBEAT = "heartbeat"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"
    
    # Chat
    CHAT_MESSAGE = "chat_message"
    CHAT_RESPONSE = "chat_response"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    
    # Models
    MODEL_LOAD_START = "model_load_start"
    MODEL_LOAD_COMPLETE = "model_load_complete"
    MODEL_LOAD_ERROR = "model_load_error"
    MODEL_UNLOAD = "model_unload"
    MODEL_DOWNLOAD_START = "model_download_start"
    MODEL_DOWNLOAD_PROGRESS = "model_download_progress"
    MODEL_DOWNLOAD_COMPLETE = "model_download_complete"
    MODEL_DOWNLOAD_ERROR = "model_download_error"
    
    # Memory
    MEMORY_UPDATE = "memory_update"
    MEMORY_CLEAR = "memory_clear"
    MEMORY_STATS = "memory_stats"
    
    # Plugins
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_ERROR = "plugin_error"
    PLUGIN_TOGGLE = "plugin_toggle"
    
    # Commands
    COMMAND_START = "command_start"
    COMMAND_COMPLETE = "command_complete"
    COMMAND_ERROR = "command_error"
    
    # Speech
    STT_START = "stt_start"
    STT_RESULT = "stt_result"
    STT_ERROR = "stt_error"
    TTS_START = "tts_start"
    TTS_COMPLETE = "tts_complete"
    TTS_ERROR = "tts_error"

class Event:
    """Standardized event object"""
    
    def __init__(self, 
                 event_type: EventType,
                 data: Dict[str, Any],
                 source: str = "backend",
                 target: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.type = event_type.value
        self.data = data
        self.source = source
        self.target = target
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class EventBus:
    """Central event bus for pub/sub pattern"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, Set[Callable]] = {}
        self.event_history: list = []
        self.max_history = 100
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(callback)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        # Store in history
        self.event_history.append(event.to_dict())
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Log the event
        logger.info(f"Event published: {event.type} from {event.source}")
        logger.debug(f"Event data: {event.data}")
        
        # Notify subscribers
        event_enum = EventType(event.type)
        if event_enum in self.subscribers:
            for callback in self.subscribers[event_enum]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50):
        """Get event history"""
        if event_type:
            filtered = [e for e in self.event_history if e['type'] == event_type.value]
            return filtered[-limit:]
        return self.event_history[-limit:]

class WebSocketManager:
    """Manages WebSocket connections with heartbeat and event broadcasting"""
    
    def __init__(self, event_bus: EventBus):
        self.connections: Set[WebSocket] = set()
        self.event_bus = event_bus
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task = None
        logger.info("WebSocketManager initialized")
    
    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")
        
        # Send initial connection event
        await self.send_to_client(websocket, Event(
            EventType.INFO,
            {"message": "Connected to JARVIS Core", "version": "1.0.0"},
            source="websocket_manager"
        ))
        
        # Start heartbeat if not already running
        if self.heartbeat_task is None:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")
        
        # Stop heartbeat if no connections
        if len(self.connections) == 0 and self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
    
    async def send_to_client(self, websocket: WebSocket, event: Event):
        """Send event to specific client"""
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, event: Event):
        """Broadcast event to all connected clients"""
        logger.debug(f"Broadcasting {event.type} to {len(self.connections)} clients")
        
        disconnected = set()
        for websocket in self.connections:
            try:
                await websocket.send_text(event.to_json())
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all clients"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                heartbeat_event = Event(
                    EventType.HEARTBEAT,
                    {
                        "timestamp": datetime.now().isoformat(),
                        "connections": len(self.connections)
                    },
                    source="websocket_manager"
                )
                
                await self.broadcast(heartbeat_event)
                logger.debug(f"Heartbeat sent to {len(self.connections)} clients")
                
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

# Global instances
event_bus = EventBus()
ws_manager = None  # Will be initialized with event_bus

def get_ws_manager() -> WebSocketManager:
    """Get or create WebSocket manager"""
    global ws_manager
    if ws_manager is None:
        ws_manager = WebSocketManager(event_bus)
    return ws_manager

"""
WebSocket endpoint for real-time event streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import logging

from app.core.events import event_bus, Event, EventType

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for projects"""
    
    def __init__(self):
        # project_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Global connections (receive all events)
        self.global_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, project_id: int = None):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        if project_id is None:
            self.global_connections.add(websocket)
            logger.info(f"Global WebSocket connection established")
        else:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)
            logger.info(f"WebSocket connection established for project {project_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: int = None):
        """Disconnect a WebSocket client"""
        if project_id is None:
            self.global_connections.discard(websocket)
            logger.info(f"Global WebSocket connection closed")
        else:
            if project_id in self.active_connections:
                self.active_connections[project_id].discard(websocket)
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]
            logger.info(f"WebSocket connection closed for project {project_id}")
    
    async def send_to_project(self, project_id: int, message: str):
        """Send message to all connections for a specific project"""
        if project_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[project_id].discard(conn)
    
    async def send_to_global(self, message: str):
        """Send message to all global connections"""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to global WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.global_connections.discard(conn)
    
    async def broadcast_event(self, event: Event):
        """Broadcast event to relevant connections"""
        message = event.to_json()
        
        # Send to project-specific connections
        if event.project_id is not None:
            await self.send_to_project(event.project_id, message)
        
        # Send to global connections
        await self.send_to_global(message)


# Global connection manager
manager = ConnectionManager()


# Subscribe to all events and broadcast them
async def event_handler(event: Event):
    """Handler to broadcast events via WebSocket"""
    await manager.broadcast_event(event)


# Register the handler
event_bus.subscribe_all_async(event_handler)


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Global WebSocket endpoint - receives all events"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/projects/{project_id}")
async def websocket_project(websocket: WebSocket, project_id: int):
    """Project-specific WebSocket endpoint"""
    await manager.connect(websocket, project_id)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
        manager.disconnect(websocket, project_id)

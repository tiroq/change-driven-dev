"""
Event bus system for publishing and subscribing to system events.
Supports real-time notifications and audit trail.
"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """System event types"""
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    
    CHANGE_REQUEST_CREATED = "change_request_created"
    CHANGE_REQUEST_SUBMITTED = "change_request_submitted"
    CHANGE_REQUEST_APPROVED = "change_request_approved"
    CHANGE_REQUEST_REJECTED = "change_request_rejected"
    
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_DELETED = "artifact_deleted"
    
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_LOG = "run_log"
    
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_type": self.event_type.value,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    Supports both synchronous and asynchronous subscribers.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._async_subscribers: Dict[EventType, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._async_wildcard_subscribers: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to a specific event type with a synchronous callback.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")
    
    def subscribe_async(self, event_type: EventType, callback: Callable[[Event], Any]) -> None:
        """
        Subscribe to a specific event type with an asynchronous callback.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Async function to call when event is published
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(callback)
        logger.debug(f"Async subscribed to {event_type.value}")
    
    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to all events (wildcard subscription).
        
        Args:
            callback: Function to call for any event
        """
        self._wildcard_subscribers.append(callback)
        logger.debug("Subscribed to all events")
    
    def subscribe_all_async(self, callback: Callable[[Event], Any]) -> None:
        """
        Subscribe to all events with async callback (wildcard subscription).
        
        Args:
            callback: Async function to call for any event
        """
        self._async_wildcard_subscribers.append(callback)
        logger.debug("Async subscribed to all events")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from a specific event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback to remove
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from {event_type.value}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        logger.info(f"Publishing event: {event.event_type.value} (project_id={event.project_id}, task_id={event.task_id})")
        
        # Notify wildcard subscribers
        for callback in self._wildcard_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in wildcard subscriber: {e}", exc_info=True)
        
        # Notify specific subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in subscriber for {event.event_type.value}: {e}", exc_info=True)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event to all subscribers (async version).
        
        Args:
            event: The event to publish
        """
        # Publish synchronously first
        self.publish(event)
        
        # Notify async wildcard subscribers
        for callback in self._async_wildcard_subscribers:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in async wildcard subscriber: {e}", exc_info=True)
        
        # Notify async specific subscribers
        if event.event_type in self._async_subscribers:
            for callback in self._async_subscribers[event.event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in async subscriber for {event.event_type.value}: {e}", exc_info=True)
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history with optional filters.
        
        Args:
            event_type: Filter by event type
            project_id: Filter by project ID
            task_id: Filter by task ID
            limit: Maximum number of events to return
        
        Returns:
            List of matching events
        """
        filtered = self._event_history
        
        if event_type is not None:
            filtered = [e for e in filtered if e.event_type == event_type]
        if project_id is not None:
            filtered = [e for e in filtered if e.project_id == project_id]
        if task_id is not None:
            filtered = [e for e in filtered if e.task_id == task_id]
        
        if limit is not None:
            filtered = filtered[-limit:]
        
        return filtered
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
        logger.debug("Event history cleared")


# Global event bus instance
event_bus = EventBus()


# Convenience functions for common events

def emit_project_event(event_type: EventType, project_id: int, data: Optional[Dict[str, Any]] = None) -> None:
    """Emit a project-related event"""
    event = Event(
        event_type=event_type,
        project_id=project_id,
        data=data or {}
    )
    event_bus.publish(event)


def emit_task_event(event_type: EventType, project_id: int, task_id: int, data: Optional[Dict[str, Any]] = None) -> None:
    """Emit a task-related event"""
    event = Event(
        event_type=event_type,
        project_id=project_id,
        task_id=task_id,
        data=data or {}
    )
    event_bus.publish(event)


async def emit_run_log(project_id: int, task_id: int, log_message: str, level: str = "info") -> None:
    """Emit a run log event"""
    event = Event(
        event_type=EventType.RUN_LOG,
        project_id=project_id,
        task_id=task_id,
        data={"message": log_message, "level": level}
    )
    await event_bus.publish_async(event)

"""
Event Base Classes - Observer Pattern Implementation.

This module provides the foundation for event-driven architecture:
- Event: Base class for all events
- EventDispatcher: Singleton that manages event handlers and dispatching
"""
import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='Event')


class Event:
    """Base class for all events (not a dataclass to avoid inheritance issues)."""
    pass


class EventDispatcher:
    """
    Singleton event dispatcher that manages event handlers.
    
    Usage:
        # Register a handler
        EventDispatcher.register(CardMovedEvent, handle_card_moved)
        
        # Dispatch an event
        EventDispatcher.dispatch(CardMovedEvent(...))
    """
    _handlers: dict[type[Event], list[Callable[[Event], None]]] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, event_type: type[T], handler: Callable[[T], None]) -> None:
        """Register a handler for an event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
        logger.debug(f"Registered handler {handler.__name__} for {event_type.__name__}")

    @classmethod
    def dispatch(cls, event: Event) -> None:
        """Dispatch an event to all registered handlers."""
        event_type = type(event)
        handlers = cls._handlers.get(event_type, [])

        logger.info(f"Dispatching {event_type.__name__} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in handler {handler.__name__}: {e}")

    @classmethod
    def clear(cls) -> None:
        """Clear all handlers (useful for testing)."""
        cls._handlers = {}
        cls._initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize event handlers. Called once at app startup."""
        if cls._initialized:
            return

        from app.events.handlers import (
            handle_email,
            handle_notification,
        )
        from app.events.types import (
            CardMovedEvent,
            ChecklistToggledEvent,
            CommentAddedEvent,
            InvitationRespondedEvent,
            InvitationSentEvent,
            WelcomeEmailSentEvent,
        )

        cls.register(CardMovedEvent, handle_notification)
        cls.register(CommentAddedEvent, handle_notification)
        cls.register(ChecklistToggledEvent, handle_notification)
        cls.register(InvitationSentEvent, handle_notification)
        cls.register(InvitationRespondedEvent, handle_notification)

        cls.register(CardMovedEvent, handle_email)
        cls.register(CommentAddedEvent, handle_email)
        cls.register(ChecklistToggledEvent, handle_email)
        cls.register(WelcomeEmailSentEvent, handle_email)

        cls._initialized = True
        logger.info("EventDispatcher initialized with handlers")

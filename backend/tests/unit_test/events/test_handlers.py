"""
Unit tests for Events module.
Tests EventDispatcher and event handlers.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4


class TestEventDispatcher:
    """Tests for EventDispatcher class."""

    def test_register_handler(self):
        """Test registering an event handler."""
        from app.events.base import EventDispatcher, Event

        # Clear any existing handlers
        EventDispatcher.clear()

        class TestEvent(Event):
            pass

        def handler(event):
            pass

        EventDispatcher.register(TestEvent, handler)

        assert TestEvent in EventDispatcher._handlers
        assert handler in EventDispatcher._handlers[TestEvent]

        # Cleanup
        EventDispatcher.clear()

    def test_dispatch_event(self):
        """Test dispatching an event to handlers."""
        from app.events.base import EventDispatcher, Event

        EventDispatcher.clear()

        class TestEvent(Event):
            def __init__(self, value):
                self.value = value

        results = []
        
        def handler(event):
            results.append(event.value)

        EventDispatcher.register(TestEvent, handler)

        event = TestEvent(value="test")
        EventDispatcher.dispatch(event)

        assert "test" in results
        EventDispatcher.clear()

    def test_dispatch_to_multiple_handlers(self):
        """Test dispatching to multiple handlers."""
        from app.events.base import EventDispatcher, Event

        EventDispatcher.clear()

        class TestEvent(Event):
            pass

        results = []
        
        def handler1(event):
            results.append(1)
        
        def handler2(event):
            results.append(2)

        EventDispatcher.register(TestEvent, handler1)
        EventDispatcher.register(TestEvent, handler2)

        event = TestEvent()
        EventDispatcher.dispatch(event)

        assert 1 in results
        assert 2 in results
        EventDispatcher.clear()

    def test_dispatch_no_handlers(self):
        """Test dispatching event with no handlers."""
        from app.events.base import EventDispatcher, Event

        EventDispatcher.clear()

        class UnhandledEvent(Event):
            pass

        # Should not raise error
        event = UnhandledEvent()
        EventDispatcher.dispatch(event)
        EventDispatcher.clear()

    def test_handler_error_does_not_stop_others(self):
        """Test that handler error doesn't prevent other handlers from running."""
        from app.events.base import EventDispatcher, Event

        EventDispatcher.clear()

        class TestEvent(Event):
            pass

        results = []

        def failing_handler(event):
            raise Exception("Handler error")

        def handler2(event):
            results.append("success")

        EventDispatcher.register(TestEvent, failing_handler)
        EventDispatcher.register(TestEvent, handler2)

        event = TestEvent()
        EventDispatcher.dispatch(event)

        # Second handler should still be called
        assert "success" in results
        EventDispatcher.clear()

    def test_clear_handlers(self):
        """Test clearing all handlers."""
        from app.events.base import EventDispatcher, Event

        EventDispatcher.clear()

        class TestEvent(Event):
            pass

        def handler(e):
            pass

        EventDispatcher.register(TestEvent, handler)
        EventDispatcher.clear()

        assert EventDispatcher._handlers == {}

    def test_initialize_registers_handlers(self):
        """Test that initialize registers default handlers."""
        from app.events.base import EventDispatcher

        EventDispatcher.clear()
        EventDispatcher.initialize()

        # Should have handlers registered
        assert len(EventDispatcher._handlers) > 0
        EventDispatcher.clear()


class TestEventTypes:
    """Tests for event type definitions."""

    def test_card_moved_event(self):
        """Test CardMovedEvent creation."""
        from app.events.types import CardMovedEvent

        event = CardMovedEvent(
            card_id=uuid4(),
            card_title="Test Card",
            old_list_name="Todo",
            new_list_name="Done",
            moved_by_id=uuid4(),
            moved_by_name="Test User",
            card_owner_id=uuid4(),
            card_owner_email="owner@test.com"
        )

        assert event.card_title == "Test Card"
        assert event.old_list_name == "Todo"
        assert event.new_list_name == "Done"

    def test_comment_added_event(self):
        """Test CommentAddedEvent creation."""
        from app.events.types import CommentAddedEvent

        event = CommentAddedEvent(
            card_id=uuid4(),
            card_title="Test Card",
            comment_content="Test comment",
            commenter_id=uuid4(),
            commenter_name="Commenter",
            card_owner_id=uuid4(),
            card_owner_email="owner@test.com"
        )

        assert event.comment_content == "Test comment"

    def test_checklist_toggled_event(self):
        """Test ChecklistToggledEvent creation."""
        from app.events.types import ChecklistToggledEvent

        event = ChecklistToggledEvent(
            card_id=uuid4(),
            card_title="Test Card",
            item_title="Task 1",
            is_completed=True,
            toggled_by_id=uuid4(),
            toggled_by_name="User",
            card_owner_id=uuid4(),
            card_owner_email="owner@test.com"
        )

        assert event.is_completed is True

    def test_invitation_sent_event(self):
        """Test InvitationSentEvent creation."""
        from app.events.types import InvitationSentEvent

        event = InvitationSentEvent(
            invitation_id=uuid4(),
            workspace_id=uuid4(),
            workspace_name="Test Workspace",
            inviter_id=uuid4(),
            inviter_name="Inviter",
            invitee_id=uuid4(),
            invitee_email="invitee@test.com"
        )

        assert event.workspace_name == "Test Workspace"

    def test_welcome_email_event(self):
        """Test WelcomeEmailSentEvent creation."""
        from app.events.types import WelcomeEmailSentEvent

        event = WelcomeEmailSentEvent(
            user_id=uuid4(),
            user_email="user@test.com"
        )

        assert event.user_email == "user@test.com"


class TestEventHandlers:
    """Tests for event handler functions."""

    def test_handle_notification_card_moved(self):
        """Test notification handler for card moved event."""
        from app.events.types import CardMovedEvent
        from app.events.handlers import handle_notification

        event = CardMovedEvent(
            card_id=uuid4(),
            card_title="Test Card",
            old_list_name="Todo",
            new_list_name="Done",
            moved_by_id=uuid4(),
            moved_by_name="Mover",
            card_owner_id=uuid4(),
            card_owner_email="owner@test.com"
        )

        # Mock the session and repository using correct import paths
        with patch('sqlmodel.Session') as mock_session_class:
            with patch('app.repository.notifications.create_notification') as mock_create:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
                mock_session_class.return_value.__exit__ = Mock(return_value=False)

                handle_notification(event)

                # Notification should be created
                mock_create.assert_called_once()

    def test_handle_notification_same_user_no_notify(self):
        """Test that no notification is created when user moves their own card."""
        from app.events.types import CardMovedEvent
        from app.events.handlers import handle_notification

        user_id = uuid4()
        event = CardMovedEvent(
            card_id=uuid4(),
            card_title="Test Card",
            old_list_name="Todo",
            new_list_name="Done",
            moved_by_id=user_id,
            moved_by_name="User",
            card_owner_id=user_id,  # Same user
            card_owner_email="owner@test.com"
        )

        with patch('sqlmodel.Session') as mock_session_class:
            with patch('app.repository.notifications.create_notification') as mock_create:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
                mock_session_class.return_value.__exit__ = Mock(return_value=False)

                handle_notification(event)

                # No notification should be created
                mock_create.assert_not_called()

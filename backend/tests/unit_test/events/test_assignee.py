"""
Unit tests for Card Assignee Feature.

Tests cover:
- _get_notification_target() function prioritizing assignee over owner
- CardAssignedEvent handling
- Notification/email routing to correct recipient
"""

import uuid
from unittest.mock import MagicMock, patch
import pytest

from app.events.handlers import _get_notification_target


class MockEvent:
    """Mock event for testing _get_notification_target."""
    def __init__(self, owner_id=None, owner_email=None, assignee_id=None, assignee_email=None):
        self.card_owner_id = owner_id
        self.card_owner_email = owner_email
        self.card_assignee_id = assignee_id
        self.card_assignee_email = assignee_email


class TestGetNotificationTarget:
    """Tests for _get_notification_target helper function."""

    def test_returns_assignee_when_both_set(self):
        """Should return assignee when both owner and assignee are set."""
        owner_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        event = MockEvent(
            owner_id=owner_id,
            owner_email="owner@example.com",
            assignee_id=assignee_id,
            assignee_email="assignee@example.com"
        )

        target_id, target_email = _get_notification_target(event)

        assert target_id == assignee_id
        assert target_email == "assignee@example.com"

    def test_returns_owner_when_no_assignee(self):
        """Should return owner when assignee is not set."""
        owner_id = uuid.uuid4()
        event = MockEvent(
            owner_id=owner_id,
            owner_email="owner@example.com",
            assignee_id=None,
            assignee_email=None
        )

        target_id, target_email = _get_notification_target(event)

        assert target_id == owner_id
        assert target_email == "owner@example.com"

    def test_returns_none_when_neither_set(self):
        """Should return (None, None) when neither is set."""
        event = MockEvent()

        target_id, target_email = _get_notification_target(event)

        assert target_id is None
        assert target_email is None

    def test_returns_assignee_id_only_when_email_missing(self):
        """Should return assignee ID even if email is missing."""
        assignee_id = uuid.uuid4()
        event = MockEvent(
            assignee_id=assignee_id,
            assignee_email=None
        )

        target_id, target_email = _get_notification_target(event)

        assert target_id == assignee_id
        assert target_email is None

    def test_works_with_event_without_assignee_attrs(self):
        """Should handle events that don't have assignee attributes."""
        class NoAssigneeEvent:
            card_owner_id = uuid.uuid4()
            card_owner_email = "owner@example.com"

        event = NoAssigneeEvent()
        target_id, target_email = _get_notification_target(event)

        assert target_id == event.card_owner_id
        assert target_email == "owner@example.com"


class TestCardAssignedEventHandling:
    """Tests for CardAssignedEvent notification and email handlers."""

    def test_card_assigned_event_has_correct_fields(self):
        """Verify CardAssignedEvent contains all required fields."""
        from app.events.types import CardAssignedEvent

        assignee_id = uuid.uuid4()
        card_id = uuid.uuid4()
        assigner_id = uuid.uuid4()

        event = CardAssignedEvent(
            card_id=card_id,
            card_title="Test Card",
            assigned_by_id=assigner_id,
            assigned_by_name="John Doe",
            assignee_id=assignee_id,
            assignee_email="assignee@example.com"
        )

        assert event.card_id == card_id
        assert event.card_title == "Test Card"
        assert event.assigned_by_id == assigner_id
        assert event.assigned_by_name == "John Doe"
        assert event.assignee_id == assignee_id
        assert event.assignee_email == "assignee@example.com"


class TestCommentAddedWithAssignee:
    """Tests for comment notifications going to assignee."""

    def test_comment_notification_goes_to_assignee_not_owner(self):
        """When card has assignee, comment notification should go to assignee."""
        from app.events.types import CommentAddedEvent

        owner_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        commenter_id = uuid.uuid4()

        event = CommentAddedEvent(
            card_id=uuid.uuid4(),
            card_title="Test Card",
            comment_content="Test comment",
            commenter_id=commenter_id,
            commenter_name="Commenter",
            card_owner_id=owner_id,
            card_owner_email="owner@example.com",
            card_assignee_id=assignee_id,
            card_assignee_email="assignee@example.com"
        )

        target_id, target_email = _get_notification_target(event)

        # Should target assignee, not owner
        assert target_id == assignee_id
        assert target_email == "assignee@example.com"
        assert target_id != owner_id


class TestCardMovedWithAssignee:
    """Tests for card moved notifications going to assignee."""

    def test_card_moved_notification_goes_to_assignee(self):
        """When card has assignee, move notification should go to assignee."""
        from app.events.types import CardMovedEvent

        owner_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        mover_id = uuid.uuid4()

        event = CardMovedEvent(
            card_id=uuid.uuid4(),
            card_title="Test Card",
            old_list_name="To Do",
            new_list_name="Done",
            moved_by_id=mover_id,
            moved_by_name="Mover",
            card_owner_id=owner_id,
            card_owner_email="owner@example.com",
            card_assignee_id=assignee_id,
            card_assignee_email="assignee@example.com"
        )

        target_id, target_email = _get_notification_target(event)

        assert target_id == assignee_id
        assert target_email == "assignee@example.com"


class TestChecklistToggledWithAssignee:
    """Tests for checklist toggle notifications going to assignee."""

    def test_checklist_notification_goes_to_assignee(self):
        """When card has assignee, checklist notification should go to assignee."""
        from app.events.types import ChecklistToggledEvent

        owner_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        toggler_id = uuid.uuid4()

        event = ChecklistToggledEvent(
            card_id=uuid.uuid4(),
            card_title="Test Card",
            item_title="Task 1",
            is_completed=True,
            toggled_by_id=toggler_id,
            toggled_by_name="Toggler",
            card_owner_id=owner_id,
            card_owner_email="owner@example.com",
            card_assignee_id=assignee_id,
            card_assignee_email="assignee@example.com"
        )

        target_id, target_email = _get_notification_target(event)

        assert target_id == assignee_id
        assert target_email == "assignee@example.com"

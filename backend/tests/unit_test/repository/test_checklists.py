"""
Unit tests for Checklists Repository.
Tests all database operations for ChecklistItem model.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4


class TestChecklistItemCRUD:
    """Tests for checklist item CRUD operations."""

    def test_create_checklist_item(self, mock_session):
        """Test creating checklist item."""
        from app.models.checklists import ChecklistItemCreate
        from app.repository import checklists as checklists_repo

        item_in = ChecklistItemCreate(
            title="Test Item",
            card_id=uuid4(),
            position=1.0
        )

        result = checklists_repo.create_checklist_item(
            session=mock_session,
            item_in=item_in
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_checklist_item_by_id(self, mock_session):
        """Test getting checklist item by ID."""
        from app.repository import checklists as checklists_repo

        mock_item = Mock()
        mock_item.id = uuid4()
        mock_session.get.return_value = mock_item

        result = checklists_repo.get_checklist_item_by_id(
            session=mock_session,
            item_id=mock_item.id
        )

        assert result == mock_item

    def test_update_checklist_item(self, mock_session):
        """Test updating checklist item."""
        from app.models.checklists import ChecklistItemUpdate
        from app.repository import checklists as checklists_repo

        mock_item = Mock()
        mock_item.sqlmodel_update = Mock()
        item_in = ChecklistItemUpdate(title="Updated Item")

        result = checklists_repo.update_checklist_item(
            session=mock_session,
            item=mock_item,
            item_in=item_in
        )

        mock_item.sqlmodel_update.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_toggle_checklist_item_complete(self, mock_session):
        """Test toggling checklist item to completed."""
        from app.repository import checklists as checklists_repo

        mock_item = Mock()
        mock_item.is_completed = False

        result = checklists_repo.toggle_checklist_item(
            session=mock_session,
            item=mock_item
        )

        assert mock_item.is_completed is True
        mock_session.commit.assert_called_once()

    def test_toggle_checklist_item_incomplete(self, mock_session):
        """Test toggling checklist item to incomplete."""
        from app.repository import checklists as checklists_repo

        mock_item = Mock()
        mock_item.is_completed = True

        result = checklists_repo.toggle_checklist_item(
            session=mock_session,
            item=mock_item
        )

        assert mock_item.is_completed is False

    def test_soft_delete_checklist_item(self, mock_session):
        """Test soft deleting checklist item."""
        from app.repository import checklists as checklists_repo

        mock_item = Mock()
        mock_item.is_deleted = False
        deleted_by = uuid4()

        result = checklists_repo.soft_delete_checklist_item(
            session=mock_session,
            item=mock_item,
            deleted_by=deleted_by
        )

        assert mock_item.is_deleted is True
        assert mock_item.deleted_by == str(deleted_by)


class TestGetChecklistItems:
    """Tests for checklist item retrieval."""

    def test_get_checklist_items_by_card(self, mock_session):
        """Test getting checklist items for a card."""
        from app.repository import checklists as checklists_repo

        mock_items = [Mock(), Mock()]
        mock_session.exec.return_value.all.return_value = mock_items

        items, count = checklists_repo.get_checklist_items_by_card(
            session=mock_session,
            card_id=uuid4()
        )

        assert len(items) == 2

    def test_get_checklist_items_all(self, mock_session):
        """Test getting all checklist items without filter."""
        from app.repository import checklists as checklists_repo

        mock_items = [Mock()]
        mock_session.exec.return_value.all.return_value = mock_items

        items, count = checklists_repo.get_checklist_items_by_card(
            session=mock_session,
            card_id=None
        )

        assert len(items) == 1

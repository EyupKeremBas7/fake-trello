"""
Unit tests for Cards Repository.
Tests all database operations for Card model.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from app.models.enums import MemberRole


class TestCardCRUD:
    """Tests for card CRUD operations."""

    def test_create_card_success(self, mock_session):
        """Test successful card creation."""
        from app.models.cards import CardCreate
        from app.repository import cards as cards_repo

        card_in = CardCreate(
            title="Test Card",
            description="Description",
            list_id=uuid4()
        )
        created_by = uuid4()

        result = cards_repo.create_card(
            session=mock_session,
            card_in=card_in,
            created_by=created_by
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_card_by_id(self, mock_session, mock_card):
        """Test getting card by ID."""
        from app.repository import cards as cards_repo

        mock_session.get.return_value = mock_card

        result = cards_repo.get_card_by_id(
            session=mock_session,
            card_id=mock_card.id
        )

        assert result == mock_card

    def test_update_card(self, mock_session, mock_card):
        """Test updating card."""
        from app.models.cards import CardUpdate
        from app.repository import cards as cards_repo

        card_in = CardUpdate(title="Updated Card")
        mock_card.sqlmodel_update = Mock()

        result = cards_repo.update_card(
            session=mock_session,
            card=mock_card,
            card_in=card_in
        )

        mock_card.sqlmodel_update.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_move_card(self, mock_session, mock_card):
        """Test moving card to different list."""
        from app.repository import cards as cards_repo

        new_list_id = uuid4()
        new_position = 2.0

        result = cards_repo.move_card(
            session=mock_session,
            card=mock_card,
            list_id=new_list_id,
            position=new_position
        )

        assert mock_card.list_id == new_list_id
        assert mock_card.position == new_position
        mock_session.commit.assert_called_once()

    def test_soft_delete_card(self, mock_session, mock_card):
        """Test soft deleting card."""
        from app.repository import cards as cards_repo

        deleted_by = uuid4()
        mock_card.is_deleted = False

        result = cards_repo.soft_delete_card(
            session=mock_session,
            card=mock_card,
            deleted_by=deleted_by
        )

        assert mock_card.is_deleted is True
        assert mock_card.deleted_by == str(deleted_by)


class TestCardAccess:
    """Tests for card access permissions."""

    def test_can_access_card_owner(self, mock_session, mock_card, mock_list, mock_board, mock_workspace):
        """Test workspace owner can access card."""
        from app.repository import cards as cards_repo

        user_id = mock_workspace.owner_id

        # Setup chain: card -> list -> board -> workspace
        mock_session.get.side_effect = [mock_list, mock_board, mock_workspace]

        result = cards_repo.can_access_card(
            session=mock_session,
            user_id=user_id,
            card=mock_card
        )

        assert result is True

    def test_can_access_card_member(self, mock_session, mock_card, mock_list, mock_board, mock_workspace):
        """Test workspace member can access card."""
        from app.repository import cards as cards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()

        mock_session.get.side_effect = [mock_list, mock_board, mock_workspace]
        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = cards_repo.can_access_card(
            session=mock_session,
            user_id=user_id,
            card=mock_card
        )

        assert result is True

    def test_can_access_card_denied(self, mock_session, mock_card, mock_list, mock_board, mock_workspace):
        """Test non-member cannot access card."""
        from app.repository import cards as cards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()

        mock_session.get.side_effect = [mock_list, mock_board, mock_workspace]
        mock_session.exec.return_value.first.return_value = None

        result = cards_repo.can_access_card(
            session=mock_session,
            user_id=user_id,
            card=mock_card
        )

        assert result is False

    def test_can_access_card_no_list(self, mock_session, mock_card):
        """Test access denied when list not found."""
        from app.repository import cards as cards_repo

        mock_session.get.return_value = None

        result = cards_repo.can_access_card(
            session=mock_session,
            user_id=uuid4(),
            card=mock_card
        )

        assert result is False

    def test_can_edit_card_member(self, mock_session, mock_card, mock_list, mock_board, mock_workspace):
        """Test member can edit card."""
        from app.repository import cards as cards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()

        mock_session.get.side_effect = [mock_list, mock_board, mock_workspace]
        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = cards_repo.can_edit_card(
            session=mock_session,
            user_id=user_id,
            card=mock_card
        )

        assert result is True

    def test_can_edit_card_observer_denied(self, mock_session, mock_card, mock_list, mock_board, mock_workspace):
        """Test observer cannot edit card."""
        from app.repository import cards as cards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()

        mock_session.get.side_effect = [mock_list, mock_board, mock_workspace]
        mock_member = Mock()
        mock_member.role = MemberRole.observer
        mock_session.exec.return_value.first.return_value = mock_member

        result = cards_repo.can_edit_card(
            session=mock_session,
            user_id=user_id,
            card=mock_card
        )

        assert result is False


class TestEnrichCard:
    """Tests for card enrichment functions."""

    def test_enrich_card_with_owner(self, mock_session, mock_user):
        """Test enriching card with owner info."""
        from app.repository import cards as cards_repo
        from unittest.mock import Mock

        # Create a fresh mock card with all required attributes explicitly set
        mock_card = Mock()
        mock_card.id = uuid4()
        mock_card.title = "Test Card"
        mock_card.description = "Description"
        mock_card.position = 1.0
        mock_card.due_date = None
        mock_card.is_archived = False
        mock_card.cover_image = None
        mock_card.list_id = uuid4()
        mock_card.created_by = mock_user.id
        mock_card.assigned_to = None  # No assignee
        mock_card.created_at = datetime.utcnow()
        mock_card.updated_at = datetime.utcnow()
        mock_card.is_deleted = False

        # Mock session.get to return owner for created_by
        mock_session.get.return_value = mock_user

        result = cards_repo.enrich_card_with_owner(mock_session, mock_card)

        assert result.owner_full_name == mock_user.full_name
        assert result.owner_email == mock_user.email
        assert result.assignee_full_name is None
        assert result.assignee_email is None

    def test_enrich_card_no_owner(self, mock_session):
        """Test enriching card without owner."""
        from app.repository import cards as cards_repo
        from unittest.mock import Mock

        # Create a fresh mock card with all required attributes explicitly set
        mock_card = Mock()
        mock_card.id = uuid4()
        mock_card.title = "Test Card"
        mock_card.description = "Description"
        mock_card.position = 1.0
        mock_card.due_date = None
        mock_card.is_archived = False
        mock_card.cover_image = None
        mock_card.list_id = uuid4()
        mock_card.created_by = None  # No owner
        mock_card.assigned_to = None  # No assignee
        mock_card.created_at = datetime.utcnow()
        mock_card.updated_at = datetime.utcnow()
        mock_card.is_deleted = False

        result = cards_repo.enrich_card_with_owner(mock_session, mock_card)

        assert result.owner_full_name is None
        assert result.owner_email is None
        assert result.assignee_full_name is None
        assert result.assignee_email is None


class TestGetCards:
    """Tests for card retrieval functions."""

    def test_get_cards_for_user(self, mock_session, mock_card):
        """Test getting cards for user."""
        from app.repository import cards as cards_repo

        mock_session.exec.return_value.all.return_value = [mock_card]

        cards, count = cards_repo.get_cards_for_user(
            session=mock_session,
            user_id=uuid4()
        )

        assert len(cards) == 1

    def test_get_cards_superuser(self, mock_session, mock_card):
        """Test getting all cards as superuser."""
        from app.repository import cards as cards_repo

        mock_session.exec.return_value.one.return_value = 1
        mock_session.exec.return_value.all.return_value = [mock_card]

        cards, count = cards_repo.get_cards_superuser(session=mock_session)

        assert len(cards) == 1

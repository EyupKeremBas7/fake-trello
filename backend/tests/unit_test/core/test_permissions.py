"""
Unit tests for Core Permissions module.
Tests permission checking and role-based access control.
"""
import pytest
from app.models.enums import MemberRole
from app.core.permissions import Action, has_permission, get_allowed_roles, PERMISSIONS


class TestHasPermission:
    """Tests for has_permission function."""

    def test_owner_always_has_permission(self):
        """Test that owner always has permission regardless of role."""
        for action in Action:
            result = has_permission(
                role=None,
                action=action,
                is_owner=True
            )
            assert result is True, f"Owner should have permission for {action}"

    def test_admin_has_most_permissions(self):
        """Test admin role has most permissions."""
        admin_actions = [
            Action.INVITE_MEMBER,
            Action.REMOVE_MEMBER,
            Action.CREATE_BOARD,
            Action.EDIT_BOARD,
            Action.DELETE_BOARD,
            Action.VIEW_BOARD,
            Action.CREATE_LIST,
            Action.CREATE_CARD,
            Action.CREATE_COMMENT,
        ]

        for action in admin_actions:
            result = has_permission(
                role=MemberRole.admin,
                action=action,
                is_owner=False
            )
            assert result is True, f"Admin should have permission for {action}"

    def test_member_permissions(self):
        """Test member role permissions."""
        member_can = [
            Action.CREATE_BOARD,
            Action.EDIT_BOARD,
            Action.VIEW_BOARD,
            Action.CREATE_LIST,
            Action.CREATE_CARD,
            Action.EDIT_CARD,
            Action.MOVE_CARD,
            Action.CREATE_COMMENT,
        ]

        member_cannot = [
            Action.INVITE_MEMBER,
            Action.REMOVE_MEMBER,
            Action.DELETE_BOARD,
            Action.DELETE_ANY_COMMENT,
        ]

        for action in member_can:
            result = has_permission(role=MemberRole.member, action=action)
            assert result is True, f"Member should have permission for {action}"

        for action in member_cannot:
            result = has_permission(role=MemberRole.member, action=action)
            assert result is False, f"Member should NOT have permission for {action}"

    def test_observer_view_only(self):
        """Test observer role has view-only permissions."""
        # Observer CAN view
        result = has_permission(role=MemberRole.observer, action=Action.VIEW_BOARD)
        assert result is True, "Observer should be able to view board"

    def test_observer_cannot_edit(self):
        """Test observer cannot edit."""
        observer_cannot = [
            Action.INVITE_MEMBER,
            Action.CREATE_BOARD,
            Action.EDIT_BOARD,
            Action.DELETE_BOARD,
            Action.CREATE_LIST,
            Action.CREATE_CARD,
            Action.EDIT_CARD,
        ]

        for action in observer_cannot:
            result = has_permission(role=MemberRole.observer, action=action)
            assert result is False, f"Observer should NOT have permission for {action}"

    def test_no_role_no_permission(self):
        """Test that None role has no permissions."""
        for action in Action:
            result = has_permission(
                role=None,
                action=action,
                is_owner=False
            )
            assert result is False, f"None role should not have permission for {action}"


class TestGetAllowedRoles:
    """Tests for get_allowed_roles function."""

    def test_get_allowed_roles_invite_member(self):
        """Test getting allowed roles for invite_member."""
        roles = get_allowed_roles(Action.INVITE_MEMBER)
        
        assert MemberRole.admin in roles
        assert MemberRole.member not in roles
        assert MemberRole.observer not in roles

    def test_get_allowed_roles_view_board(self):
        """Test getting allowed roles for view_board."""
        roles = get_allowed_roles(Action.VIEW_BOARD)
        
        assert MemberRole.admin in roles
        assert MemberRole.member in roles
        assert MemberRole.observer in roles

    def test_get_allowed_roles_create_card(self):
        """Test getting allowed roles for create_card."""
        roles = get_allowed_roles(Action.CREATE_CARD)
        
        assert MemberRole.admin in roles
        assert MemberRole.member in roles
        assert MemberRole.observer not in roles


class TestPermissionsMatrix:
    """Tests for PERMISSIONS dictionary completeness."""

    def test_all_actions_have_permissions(self):
        """Test that all actions are defined in PERMISSIONS."""
        for action in Action:
            assert action in PERMISSIONS, f"Action {action} not in PERMISSIONS"

    def test_permissions_have_valid_roles(self):
        """Test that all permission values are valid MemberRole lists."""
        for action, roles in PERMISSIONS.items():
            assert isinstance(roles, list), f"{action} permissions should be a list"
            for role in roles:
                assert isinstance(role, MemberRole), f"Invalid role {role} for {action}"

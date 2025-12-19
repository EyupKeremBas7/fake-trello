"""
Permissions Module - Centralized permission definitions (Strategy Pattern).

This module defines all permissions in one place, making it easy to:
1. Add new roles without modifying routes
2. Change permission requirements in one place
3. Understand the full permission matrix at a glance
"""
from enum import Enum

from app.models.enums import MemberRole


class Action(str, Enum):
    INVITE_MEMBER = "invite_member"
    REMOVE_MEMBER = "remove_member"

    CREATE_BOARD = "create_board"
    EDIT_BOARD = "edit_board"
    DELETE_BOARD = "delete_board"
    VIEW_BOARD = "view_board"

    CREATE_LIST = "create_list"
    EDIT_LIST = "edit_list"
    DELETE_LIST = "delete_list"

    CREATE_CARD = "create_card"
    EDIT_CARD = "edit_card"
    DELETE_CARD = "delete_card"
    MOVE_CARD = "move_card"

    CREATE_COMMENT = "create_comment"
    DELETE_ANY_COMMENT = "delete_any_comment"

    CREATE_CHECKLIST = "create_checklist"
    TOGGLE_CHECKLIST = "toggle_checklist"


PERMISSIONS: dict[Action, list[MemberRole]] = {
    Action.INVITE_MEMBER: [MemberRole.admin],
    Action.REMOVE_MEMBER: [MemberRole.admin],

    Action.CREATE_BOARD: [MemberRole.admin, MemberRole.member],
    Action.EDIT_BOARD: [MemberRole.admin, MemberRole.member],
    Action.DELETE_BOARD: [MemberRole.admin],
    Action.VIEW_BOARD: [MemberRole.admin, MemberRole.member, MemberRole.observer],


    Action.CREATE_LIST: [MemberRole.admin, MemberRole.member],
    Action.EDIT_LIST: [MemberRole.admin, MemberRole.member],
    Action.DELETE_LIST: [MemberRole.admin, MemberRole.member],


    Action.CREATE_CARD: [MemberRole.admin, MemberRole.member],
    Action.EDIT_CARD: [MemberRole.admin, MemberRole.member],
    Action.DELETE_CARD: [MemberRole.admin, MemberRole.member],
    Action.MOVE_CARD: [MemberRole.admin, MemberRole.member],

    Action.CREATE_COMMENT: [MemberRole.admin, MemberRole.member, MemberRole.observer],
    Action.DELETE_ANY_COMMENT: [MemberRole.admin],

    Action.CREATE_CHECKLIST: [MemberRole.admin, MemberRole.member],
    Action.TOGGLE_CHECKLIST: [MemberRole.admin, MemberRole.member, MemberRole.observer],
}


def has_permission(
    role: MemberRole | None,
    action: Action,
    is_owner: bool = False
) -> bool:
    """
    Check if a role has permission to perform an action.
    
    Args:
        role: The user's role in the workspace (None if not a member)
        action: The action to check permission for
        is_owner: Whether the user is the workspace owner
    
    Returns:
        True if the user has permission, False otherwise
    """

    if is_owner:
        return True

    if role is None:
        return False

    allowed_roles = PERMISSIONS.get(action, [])
    return role in allowed_roles


def get_allowed_roles(action: Action) -> list[MemberRole]:
    """Get list of roles that can perform an action."""
    return PERMISSIONS.get(action, [])

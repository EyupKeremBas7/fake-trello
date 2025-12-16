"""Add card_moved and checklist_toggled notification types

Revision ID: c3b7d8e9f012
Revises: 05cf83a9a367
Create Date: 2025-12-16 22:48:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3b7d8e9f012"
down_revision = "05cf83a9a367"
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to NotificationType
    # PostgreSQL requires ALTER TYPE for adding enum values
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'card_moved'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'checklist_toggled'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly.
    # This would require recreating the enum type and all dependent columns.
    # For simplicity, we leave this as a no-op.
    pass

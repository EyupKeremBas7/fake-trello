"""Initial comprehensive schema - All tables

Revision ID: 0001_initial
Revises: None
Create Date: 2025-12-21

This is the SINGLE migration that creates the entire database schema.
All tables, enums, indexes, and foreign keys are defined here.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.execute("CREATE TYPE visibility AS ENUM ('private', 'workspace', 'public')")
    
    # Notification type enum
    op.execute("""
        CREATE TYPE notificationtype AS ENUM (
            'card_moved', 'comment_added', 'checklist_completed',
            'card_assigned', 'card_due_soon', 'card_overdue',
            'mention', 'board_shared', 'workspace_invitation',
            'card_created', 'checklist_toggled'
        )
    """)
    
    # Invitation status enum
    op.execute("CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'rejected', 'expired')")
    
    # Workspace role enum
    op.execute("CREATE TYPE workspacerole AS ENUM ('owner', 'admin', 'member', 'viewer')")
    
    # Activity action type enum
    op.execute("""
        CREATE TYPE actiontype AS ENUM (
            'created', 'updated', 'deleted', 'moved', 'archived',
            'restored', 'completed', 'assigned', 'commented', 'invited',
            'joined', 'left'
        )
    """)
    
    # Activity entity type enum
    op.execute("""
        CREATE TYPE entitytype AS ENUM (
            'card', 'list', 'board', 'workspace', 'comment',
            'checklist_item', 'member'
        )
    """)

    # ========================================
    # USER TABLE
    # ========================================
    op.create_table(
        'user',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)

    # ========================================
    # WORKSPACE TABLE
    # ========================================
    op.create_table(
        'workspace',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # WORKSPACE MEMBER TABLE
    # ========================================
    op.create_table(
        'workspacemember',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'admin', 'member', 'viewer', name='workspacerole', create_type=False), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member')
    )

    # ========================================
    # BOARD TABLE
    # ========================================
    op.create_table(
        'board',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('visibility', postgresql.ENUM('private', 'workspace', 'public', name='visibility', create_type=False), nullable=False, server_default='workspace'),
        sa.Column('background_image', sa.String(length=500), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # BOARD LIST TABLE
    # ========================================
    op.create_table(
        'board_list',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Float(), nullable=False, server_default='65535'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('board_id', sa.UUID(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # CARD TABLE
    # ========================================
    op.create_table(
        'card',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Float(), nullable=False, server_default='65535'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cover_image', sa.String(length=500), nullable=True),
        sa.Column('list_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('assigned_to', sa.UUID(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['user.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.ForeignKeyConstraint(['list_id'], ['board_list.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # CARD COMMENT TABLE
    # ========================================
    op.create_table(
        'card_comment',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('card_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['card.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # CHECKLIST ITEM TABLE
    # ========================================
    op.create_table(
        'checklist_item',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('position', sa.Float(), nullable=False, server_default='65535'),
        sa.Column('card_id', sa.UUID(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['card.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # NOTIFICATION TABLE
    # ========================================
    op.create_table(
        'notification',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type', postgresql.ENUM(
            'card_moved', 'comment_added', 'checklist_completed',
            'card_assigned', 'card_due_soon', 'card_overdue',
            'mention', 'board_shared', 'workspace_invitation',
            'card_created', 'checklist_toggled',
            name='notificationtype', create_type=False
        ), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reference_id', sa.UUID(), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notification_user_id', 'notification', ['user_id'])
    op.create_index('ix_notification_is_read', 'notification', ['is_read'])

    # ========================================
    # WORKSPACE INVITATION TABLE
    # ========================================
    op.create_table(
        'workspace_invitation',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('inviter_id', sa.UUID(), nullable=False),
        sa.Column('invitee_email', sa.String(length=255), nullable=False),
        sa.Column('invitee_id', sa.UUID(), nullable=True),
        sa.Column('role', postgresql.ENUM('owner', 'admin', 'member', 'viewer', name='workspacerole', create_type=False), nullable=False, server_default='member'),
        sa.Column('status', postgresql.ENUM('pending', 'accepted', 'rejected', 'expired', name='invitationstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invitee_id'], ['user.id']),
        sa.ForeignKeyConstraint(['inviter_id'], ['user.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================
    # ACTIVITY LOG TABLE
    # ========================================
    op.create_table(
        'activity_log',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('action', postgresql.ENUM(
            'created', 'updated', 'deleted', 'moved', 'archived',
            'restored', 'completed', 'assigned', 'commented', 'invited',
            'joined', 'left',
            name='actiontype', create_type=False
        ), nullable=False),
        sa.Column('entity_type', postgresql.ENUM(
            'card', 'list', 'board', 'workspace', 'comment',
            'checklist_item', 'member',
            name='entitytype', create_type=False
        ), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('entity_name', sa.String(length=255), nullable=True),
        sa.Column('board_id', sa.UUID(), nullable=True),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('details', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_log_user_id', 'activity_log', ['user_id'])
    op.create_index('ix_activity_log_entity_id', 'activity_log', ['entity_id'])
    op.create_index('ix_activity_log_board_id', 'activity_log', ['board_id'])
    op.create_index('ix_activity_log_workspace_id', 'activity_log', ['workspace_id'])
    op.create_index('ix_activity_log_created_at', 'activity_log', ['created_at'])


def downgrade():
    op.drop_table('activity_log')
    op.drop_table('workspace_invitation')
    op.drop_table('notification')
    op.drop_table('checklist_item')
    op.drop_table('card_comment')
    op.drop_table('card')
    op.drop_table('board_list')
    op.drop_table('board')
    op.drop_table('workspacemember')
    op.drop_table('workspace')
    op.drop_table('user')
    
    # Drop enums
    op.execute("DROP TYPE entitytype")
    op.execute("DROP TYPE actiontype")
    op.execute("DROP TYPE invitationstatus")
    op.execute("DROP TYPE notificationtype")
    op.execute("DROP TYPE workspacerole")
    op.execute("DROP TYPE visibility")

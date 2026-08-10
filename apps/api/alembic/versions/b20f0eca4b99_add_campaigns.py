"""add campaigns

Revision ID: b20f0eca4b99
Revises: c3235190486a
Create Date: 2026-08-09 22:08:01.176687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b20f0eca4b99'
down_revision: Union[str, Sequence[str], None] = 'c3235190486a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'campaigns',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('whatsapp_connection_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('language_code', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=False),
        sa.Column('sent_count', sa.Integer(), nullable=False),
        sa.Column('delivered_count', sa.Integer(), nullable=False),
        sa.Column('read_count', sa.Integer(), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['whatsapp_connection_id'], ['whatsapp_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaigns_organization_id'), 'campaigns', ['organization_id'], unique=False)
    op.create_index(op.f('ix_campaigns_whatsapp_connection_id'), 'campaigns', ['whatsapp_connection_id'], unique=False)

    op.create_table(
        'campaign_recipients',
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('contact_id', sa.UUID(), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rendered_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('whatsapp_message_id', sa.String(length=255), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('whatsapp_message_id'),
    )
    op.create_index(op.f('ix_campaign_recipients_campaign_id'), 'campaign_recipients', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_contact_id'), 'campaign_recipients', ['contact_id'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_whatsapp_message_id'), 'campaign_recipients', ['whatsapp_message_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_campaign_recipients_whatsapp_message_id'), table_name='campaign_recipients')
    op.drop_index(op.f('ix_campaign_recipients_contact_id'), table_name='campaign_recipients')
    op.drop_index(op.f('ix_campaign_recipients_campaign_id'), table_name='campaign_recipients')
    op.drop_table('campaign_recipients')

    op.drop_index(op.f('ix_campaigns_whatsapp_connection_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_organization_id'), table_name='campaigns')
    op.drop_table('campaigns')

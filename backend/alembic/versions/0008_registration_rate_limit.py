"""registration rate-limit log

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-26

"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registration_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ip_address", sa.String(45), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("registration_log")

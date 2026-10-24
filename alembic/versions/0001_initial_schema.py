"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-22

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "search_filters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("min_price", sa.Integer, nullable=True),
        sa.Column("max_price", sa.Integer, nullable=True),
        sa.Column("rooms", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("scan_interval_minutes", sa.Integer, server_default="60"),
        sa.Column("last_scanned_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_url", sa.String(500), unique=True, nullable=False),
        sa.Column("source", sa.String(20), server_default="olx"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("rooms", sa.Integer, nullable=True),
        sa.Column("photos", sa.JSON, server_default="[]"),
        sa.Column("seller_type", sa.String(20), server_default="unknown"),
        sa.Column("is_agency", sa.Boolean, server_default=sa.false()),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("ai_pros", sa.JSON, server_default="[]"),
        sa.Column("ai_cons", sa.JSON, server_default="[]"),
        sa.Column("price_vs_market_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "user_listing_status",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_user_listing"),
    )


def downgrade() -> None:
    op.drop_table("user_listing_status")
    op.drop_table("listings")
    op.drop_table("search_filters")
    op.drop_table("users")

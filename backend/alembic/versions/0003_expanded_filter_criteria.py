"""expanded filter criteria

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-24

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NEW_BOOL_COLUMNS = [
    "is_new_building", "furnished_only", "has_elevator", "has_parking",
    "has_balcony", "internet_included", "utilities_included", "near_metro_only",
]


def upgrade() -> None:
    op.add_column("search_filters", sa.Column("property_type", sa.String(20), nullable=True))
    op.add_column("search_filters", sa.Column("renovation_type", sa.String(20), nullable=True))
    op.add_column("search_filters", sa.Column("heating_type", sa.String(20), nullable=True))
    op.add_column("search_filters", sa.Column("min_lease_months", sa.Integer, nullable=True))
    op.add_column("search_filters", sa.Column("deposit_required", sa.Boolean, nullable=True))
    for col in NEW_BOOL_COLUMNS:
        op.add_column("search_filters", sa.Column(col, sa.Boolean, server_default=sa.false()))


def downgrade() -> None:
    for col in NEW_BOOL_COLUMNS:
        op.drop_column("search_filters", col)
    op.drop_column("search_filters", "deposit_required")
    op.drop_column("search_filters", "min_lease_months")
    op.drop_column("search_filters", "heating_type")
    op.drop_column("search_filters", "renovation_type")
    op.drop_column("search_filters", "property_type")

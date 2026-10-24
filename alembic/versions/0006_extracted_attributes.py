"""extracted listing attributes, drop near_metro_only

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("search_filters", "near_metro_only")

    op.add_column("listings", sa.Column("property_type", sa.String(20), nullable=True))
    op.add_column("listings", sa.Column("is_new_building", sa.Boolean, server_default=sa.false()))
    op.add_column("listings", sa.Column("furnished", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("heating_type", sa.String(20), nullable=True))
    op.add_column("listings", sa.Column("has_elevator", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("has_parking", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("has_balcony", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("internet_included", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("utilities_included", sa.Boolean, nullable=True))
    op.add_column("listings", sa.Column("min_lease_months", sa.Integer, nullable=True))
    op.add_column("listings", sa.Column("deposit_required", sa.Boolean, nullable=True))


def downgrade() -> None:
    for col in [
        "property_type", "is_new_building", "furnished", "heating_type", "has_elevator",
        "has_parking", "has_balcony", "internet_included", "utilities_included",
        "min_lease_months", "deposit_required",
    ]:
        op.drop_column("listings", col)

    op.add_column("search_filters", sa.Column("near_metro_only", sa.Boolean, server_default=sa.false()))

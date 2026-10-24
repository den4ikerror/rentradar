"""multi-select property type

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-24

"""
import json
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search_filters", sa.Column("property_types", sa.JSON, server_default="[]"))

    # Переносимо існуючі одиничні значення в новий список без Postgres-специфічних
    # функцій (json_build_array тощо), щоб міграція однаково працювала і на SQLite
    # (типовий локальний DATABASE_URL) і на Postgres (Railway).
    connection = op.get_bind()
    filters_table = sa.table(
        "search_filters",
        sa.column("id", sa.Integer),
        sa.column("property_type", sa.String),
        sa.column("property_types", sa.JSON),
    )
    rows = connection.execute(sa.select(filters_table.c.id, filters_table.c.property_type)).fetchall()
    for row in rows:
        if row.property_type:
            connection.execute(
                filters_table.update()
                .where(filters_table.c.id == row.id)
                .values(property_types=json.dumps([row.property_type]))
            )

    op.drop_column("search_filters", "property_type")


def downgrade() -> None:
    op.add_column("search_filters", sa.Column("property_type", sa.String(20), nullable=True))
    op.drop_column("search_filters", "property_types")

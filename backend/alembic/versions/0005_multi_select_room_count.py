"""multi-select room count

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-24

"""
import json
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search_filters", sa.Column("room_options", sa.JSON, server_default="[]"))

    connection = op.get_bind()
    filters_table = sa.table(
        "search_filters",
        sa.column("id", sa.Integer),
        sa.column("rooms", sa.Integer),
        sa.column("room_options", sa.JSON),
    )
    rows = connection.execute(sa.select(filters_table.c.id, filters_table.c.rooms)).fetchall()
    for row in rows:
        if row.rooms:
            connection.execute(
                filters_table.update()
                .where(filters_table.c.id == row.id)
                .values(room_options=json.dumps([row.rooms]))
            )

    op.drop_column("search_filters", "rooms")


def downgrade() -> None:
    op.add_column("search_filters", sa.Column("rooms", sa.Integer, nullable=True))
    op.drop_column("search_filters", "room_options")

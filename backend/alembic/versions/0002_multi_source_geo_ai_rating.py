"""multi-source geo and ai rating

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- search_filters: гео-деталізація ---
    op.add_column("search_filters", sa.Column("region", sa.String(100), nullable=True))
    op.add_column("search_filters", sa.Column("district", sa.String(100), nullable=True))
    op.add_column("search_filters", sa.Column("street", sa.String(200), nullable=True))
    op.add_column("search_filters", sa.Column("street_radius_km", sa.Float, nullable=True))
    op.add_column("search_filters", sa.Column("street_lat", sa.Float, nullable=True))
    op.add_column("search_filters", sa.Column("street_lon", sa.Float, nullable=True))
    op.add_column("search_filters", sa.Column("min_area", sa.Float, nullable=True))
    op.add_column("search_filters", sa.Column("floor_not_first", sa.Boolean, server_default=sa.false()))
    op.add_column("search_filters", sa.Column("floor_not_last", sa.Boolean, server_default=sa.false()))
    op.add_column("search_filters", sa.Column("pets_allowed_only", sa.Boolean, server_default=sa.false()))
    op.add_column("search_filters", sa.Column("created_at", sa.DateTime, server_default=sa.func.now()))

    # --- listings: гео + мультиджерела + AI-рейтинг ---
    op.add_column("listings", sa.Column("region", sa.String(100), nullable=True))
    op.add_column("listings", sa.Column("district", sa.String(100), nullable=True))
    op.add_column("listings", sa.Column("street", sa.String(200), nullable=True))
    op.add_column("listings", sa.Column("latitude", sa.Float, nullable=True))
    op.add_column("listings", sa.Column("longitude", sa.Float, nullable=True))
    op.add_column("listings", sa.Column("area", sa.Float, nullable=True))
    op.add_column("listings", sa.Column("floor", sa.Integer, nullable=True))
    op.add_column("listings", sa.Column("total_floors", sa.Integer, nullable=True))
    op.add_column("listings", sa.Column("ai_rating", sa.Integer, nullable=True))
    op.add_column("listings", sa.Column("ai_verdict", sa.Text, nullable=True))

    # Check if columns exist before dropping (in case of re-runs) or use batch alter
    with op.batch_alter_table("listings") as batch_op:
        try:
            batch_op.drop_column("ai_summary")
            batch_op.drop_column("ai_pros")
            batch_op.drop_column("ai_cons")
        except Exception:
            pass
        batch_op.alter_column("source", type_=sa.String(30))

    op.add_column("user_listing_status", sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()))

    # Check if geocode_cache table exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "geocode_cache" not in inspector.get_table_names():
        op.create_table(
            "geocode_cache",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("query", sa.String(300), unique=True, index=True, nullable=False),
            sa.Column("latitude", sa.Float, nullable=True),
            sa.Column("longitude", sa.Float, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("geocode_cache")
    op.drop_column("user_listing_status", "updated_at")

    op.add_column("listings", sa.Column("ai_summary", sa.Text, nullable=True))
    op.add_column("listings", sa.Column("ai_pros", sa.JSON, server_default="[]"))
    op.add_column("listings", sa.Column("ai_cons", sa.JSON, server_default="[]"))
    for col in ["region", "district", "street", "latitude", "longitude", "area", "floor", "total_floors", "ai_rating", "ai_verdict"]:
        op.drop_column("listings", col)

    for col in ["region", "district", "street", "street_radius_km", "street_lat", "street_lon",
                "min_area", "floor_not_first", "floor_not_last", "pets_allowed_only", "created_at"]:
        op.drop_column("search_filters", col)

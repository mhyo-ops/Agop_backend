"""Initial schema creation

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "crops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("crop_name", sa.String(length=100), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("soil_type", sa.String(length=50), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("growth_stage", sa.String(length=50), nullable=True),
        sa.Column("planting_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_watered_date", sa.DateTime(), nullable=True),
        sa.Column("last_fertilized_date", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id"), nullable=False, index=True),
        sa.Column("water_quantity", sa.Float(), nullable=False),
        sa.Column("fertilizer_qty", sa.Float(), nullable=True),
        sa.Column("logged_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id"), nullable=False, index=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("recommendation_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id"), nullable=False, index=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("is_done", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("recommendations")
    op.drop_table("daily_logs")
    op.drop_table("crops")
    op.drop_table("users")

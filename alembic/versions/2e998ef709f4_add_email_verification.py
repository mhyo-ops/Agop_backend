"""Add email verification

Revision ID: 2e998ef709f4
Revises: 0001_initial
Create Date: 2026-04-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2e998ef709f4"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_verified column to users table
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=True, default=False))

    # Create verification_codes table
    op.create_table(
        "verification_codes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("verification_codes")
    op.drop_column("users", "is_verified")
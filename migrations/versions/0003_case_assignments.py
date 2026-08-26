"""Add case assignments for authorized stakeholders.

Revision ID: 0003_case_assignments
Revises: 0002_rbac_and_sharing
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_case_assignments"
down_revision = "0002_rbac_and_sharing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["user.id"]),
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_assignment"),
    )
    op.create_index("ix_case_assignments_case_id", "case_assignments", ["case_id"])
    op.create_index("ix_case_assignments_user_id", "case_assignments", ["user_id"])
    op.create_index("ix_case_assignments_assigned_by", "case_assignments", ["assigned_by"])


def downgrade():
    op.drop_index("ix_case_assignments_assigned_by", table_name="case_assignments")
    op.drop_index("ix_case_assignments_user_id", table_name="case_assignments")
    op.drop_index("ix_case_assignments_case_id", table_name="case_assignments")
    op.drop_table("case_assignments")

"""add unit columns to meals and supplements

Revision ID: a4b1e8c9add9
Revises: dc0b459bbefb
Create Date: 2025-09-16 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a4b1e8c9add9"
down_revision = "dc0b459bbefb"
branch_labels = None
depends_on = None


def upgrade():
    # Meals unit columns
    with op.batch_alter_table("meals") as batch_op:
        batch_op.add_column(sa.Column("calories_unit", sa.Text, nullable=False, server_default="kcal"))
        batch_op.add_column(sa.Column("protein_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("carbohydrates_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("fat_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("fiber_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("vitamin_a_unit", sa.Text, nullable=False, server_default="ug"))
        batch_op.add_column(sa.Column("vitamin_c_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("vitamin_d_unit", sa.Text, nullable=False, server_default="ug"))
        batch_op.add_column(sa.Column("calcium_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("iron_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("potassium_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("sodium_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("creatine_unit", sa.Text, nullable=False, server_default="g"))

    # Supplements unit columns (no creatine in supplements table)
    with op.batch_alter_table("supplements") as batch_op:
        batch_op.add_column(sa.Column("calories_unit", sa.Text, nullable=False, server_default="kcal"))
        batch_op.add_column(sa.Column("protein_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("carbohydrates_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("fat_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("fiber_unit", sa.Text, nullable=False, server_default="g"))
        batch_op.add_column(sa.Column("vitamin_a_unit", sa.Text, nullable=False, server_default="ug"))
        batch_op.add_column(sa.Column("vitamin_c_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("vitamin_d_unit", sa.Text, nullable=False, server_default="ug"))
        batch_op.add_column(sa.Column("calcium_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("iron_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("potassium_unit", sa.Text, nullable=False, server_default="mg"))
        batch_op.add_column(sa.Column("sodium_unit", sa.Text, nullable=False, server_default="mg"))


def downgrade():
    # Drop unit columns in reverse order
    with op.batch_alter_table("supplements") as batch_op:
        batch_op.drop_column("sodium_unit")
        batch_op.drop_column("potassium_unit")
        batch_op.drop_column("iron_unit")
        batch_op.drop_column("calcium_unit")
        batch_op.drop_column("vitamin_d_unit")
        batch_op.drop_column("vitamin_c_unit")
        batch_op.drop_column("vitamin_a_unit")
        batch_op.drop_column("fiber_unit")
        batch_op.drop_column("fat_unit")
        batch_op.drop_column("carbohydrates_unit")
        batch_op.drop_column("protein_unit")
        batch_op.drop_column("calories_unit")

    with op.batch_alter_table("meals") as batch_op:
        batch_op.drop_column("creatine_unit")
        batch_op.drop_column("sodium_unit")
        batch_op.drop_column("potassium_unit")
        batch_op.drop_column("iron_unit")
        batch_op.drop_column("calcium_unit")
        batch_op.drop_column("vitamin_d_unit")
        batch_op.drop_column("vitamin_c_unit")
        batch_op.drop_column("vitamin_a_unit")
        batch_op.drop_column("fiber_unit")
        batch_op.drop_column("fat_unit")
        batch_op.drop_column("carbohydrates_unit")
        batch_op.drop_column("protein_unit")
        batch_op.drop_column("calories_unit")



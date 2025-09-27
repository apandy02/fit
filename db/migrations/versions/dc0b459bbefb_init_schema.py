"""init schema

Revision ID: dc0b459bbefb
Revises:
Create Date: 2025-09-07 16:44:18.020850

"""

import sqlalchemy as sa
from alembic import op

revision = "dc0b459bbefb"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # If you want citext for email (optional):
    # op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "email", sa.Text, nullable=True, unique=False
        ),  # use CITEXT for case-insensitive if desired
        sa.Column("provider", sa.Text, nullable=True),
        sa.Column("provider_user_id", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "provider", "provider_user_id", name="uq_users_provider_uid"
        ),
    )

    op.create_table(
        "profile",
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("name", sa.Text),
        sa.Column("email", sa.Text),  # current code reads email from profile
        sa.Column("gender", sa.Text),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("units", sa.Text),
        sa.Column("dietary_restrictions", sa.Text),
        sa.Column("activity_level", sa.Text),
        sa.Column("weight_goal", sa.Numeric(6, 2)),
        sa.Column("fitness_goal", sa.Text),
        sa.Column("onboarding_stage", sa.Integer),
    )

    op.create_table(
        "meals",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date_entered", sa.Date, nullable=False),
        sa.Column("meal_time", sa.Time, nullable=False),
        sa.Column("user_description", sa.Text),
        sa.Column("llm_summary", sa.Text),
        sa.Column("ingredients", sa.Text),
        sa.Column(
            "is_supplement", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column("calories", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("protein", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column(
            "carbohydrates", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column("fat", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fiber", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_a", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_c", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_d", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("calcium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("iron", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("potassium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sodium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("creatine", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_meals_user_date_time", "meals", ["user_id", "date_entered", "meal_time"]
    )

    op.create_table(
        "supplements",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("calories", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("protein", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column(
            "carbohydrates", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column("fat", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fiber", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_a", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_c", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("vitamin_d", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("calcium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("iron", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("potassium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sodium", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "name", name="uq_supplements_user_name"),
    )

    op.create_table(
        "supplement_entries",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplement_id",
            sa.BigInteger,
            sa.ForeignKey("supplements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date_consumed", sa.Date, nullable=False),
        sa.Column("time_consumed", sa.Time, nullable=False),
        sa.Column("servings", sa.Numeric(10, 2), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_supp_entries_user_date_time",
        "supplement_entries",
        ["user_id", "date_consumed", "time_consumed"],
    )

    op.create_table(
        "measurements",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("datetime", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("weight", sa.Numeric(7, 3)),
        sa.Column("height", sa.Numeric(5, 2)),
    )
    op.create_index(
        "ix_measurements_user_datetime", "measurements", ["user_id", "datetime"]
    )

    op.create_table(
        "water",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time", sa.Time, nullable=False),
        sa.Column("water_consumed_ml", sa.Numeric(10, 2), nullable=False),
    )
    op.create_index("ix_water_user_date", "water", ["user_id", "date"])

    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("unit", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
    )
    op.create_index("ix_inventory_user_category", "inventory", ["user_id", "category"])

    op.create_table(
        "tracker_accounts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("provider_user_id", sa.Text, nullable=False),
        sa.Column("access_token", sa.Text, nullable=False),
        sa.Column("refresh_token", sa.Text),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("scopes", sa.Text),
        sa.Column(
            "primary", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "linked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "provider_user_id",
            name="uq_tracker_user_provider_uid",
        ),
    )
    op.create_index(
        "ix_tracker_user_primary", "tracker_accounts", ["user_id", "primary"]
    )

    op.create_table(
        "oauth_state",
        sa.Column("state", sa.Text, primary_key=True),
        sa.Column("code_verifier", sa.Text, nullable=False),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column(
            "user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("redirect_to", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )


def downgrade():
    for t in [
        "oauth_state",
        "tracker_accounts",
        "inventory",
        "water",
        "measurements",
        "supplement_entries",
        "supplements",
        "meals",
        "profile",
        "users",
    ]:
        op.drop_table(t)

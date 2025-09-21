from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class AccountsRepository:
    def __init__(self, engine):
        self._engine = engine

    # Users
    def ensure_local_user(self, user_id: int) -> None:
        sql = text(
            """
            INSERT INTO users (id, email, provider, provider_user_id)
            VALUES (:id, NULL, 'local', :puid)
            ON CONFLICT (id) DO NOTHING
            """
        )
        with self._engine.begin() as conn:
            conn.execute(sql, {"id": user_id, "puid": str(user_id)})

    def get_user_id(self, provider_user_id: str, provider: str) -> int | None:
        sql = text(
            """
            SELECT id FROM users
            WHERE provider_user_id = :puid AND provider = :prov
            LIMIT 1
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(
                sql, {"puid": provider_user_id, "prov": provider}
            ).fetchone()
            return row[0] if row else None

    def insert_new_user(self, user_dict: dict) -> int:
        cols = ", ".join(user_dict.keys())
        params = {f"p_{k}": v for k, v in user_dict.items()}
        values = ", ".join(f":p_{k}" for k in user_dict.keys())
        sql = text(f"INSERT INTO users ({cols}) VALUES ({values}) RETURNING id")
        with self._engine.begin() as conn:
            return conn.execute(sql, params).scalar_one()

    def create_oauth_state(
        self,
        state: str,
        code_verifier: str,
        provider: str,
        user_id: int | None,
        redirect_to: str | None,
        created_at: str,
        expires_at: str,
    ):
        sql = text(
            """
            INSERT INTO oauth_state (state, code_verifier, provider, user_id, redirect_to, created_at, expires_at)
            VALUES (:s, :cv, :p, :u, :r, :c, :e)
            """
        )
        with self._engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "s": state,
                    "cv": code_verifier,
                    "p": provider,
                    "u": user_id,
                    "r": redirect_to,
                    "c": created_at,
                    "e": expires_at,
                },
            )

    def consume_oauth_state(self, state: str) -> dict | None:
        with self._engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM oauth_state WHERE state = :s"), {"s": state}
            ).fetchone()
            if not row:
                return None
            conn.execute(text("DELETE FROM oauth_state WHERE state = :s"), {"s": state})
            return dict(row._mapping)

    # Tracker accounts
    def upsert_tracker_account(
        self,
        user_id: int,
        provider: str,
        provider_user_id: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: str | None,
        scopes: str | None,
        primary: bool = False,
    ):
        with self._engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT id FROM tracker_accounts WHERE user_id = :u AND provider = :p AND provider_user_id = :puid"
                ),
                {"u": user_id, "p": provider, "puid": provider_user_id},
            ).fetchone()
            if existing:
                conn.execute(
                    text(
                        "UPDATE tracker_accounts SET access_token = :a, refresh_token = :r, expires_at = :e, scopes = :s WHERE id = :id"
                    ),
                    {
                        "a": access_token,
                        "r": refresh_token,
                        "e": expires_at,
                        "s": scopes,
                        "id": existing[0],
                    },
                )
            else:
                conn.execute(
                    text(
                        """
                    INSERT INTO tracker_accounts (user_id, provider, provider_user_id, access_token, refresh_token, expires_at, scopes, is_primary_tracker, linked_at)
                    VALUES (:u, :p, :puid, :a, :r, :e, :s, :pri, :lnk)
                """
                    ),
                    {
                        "u": user_id,
                        "p": provider,
                        "puid": provider_user_id,
                        "a": access_token,
                        "r": refresh_token,
                        "e": expires_at,
                        "s": scopes,
                        "pri": primary,
                        "lnk": datetime.now().isoformat(),
                    },
                )
            if primary:
                conn.execute(
                    text(
                        "UPDATE tracker_accounts SET is_primary_tracker = false WHERE user_id = :u AND provider != :p"
                    ),
                    {"u": user_id, "p": provider},
                )

    def get_tracker_account(
        self, user_id: int, provider: str | None = None, primary_only: bool = True
    ) -> dict | None:
        with self._engine.connect() as conn:
            if provider:
                row = conn.execute(
                    text(
                        "SELECT * FROM tracker_accounts WHERE user_id = :u AND provider = :p ORDER BY is_primary_tracker DESC LIMIT 1"
                    ),
                    {"u": user_id, "p": provider},
                ).fetchone()
            elif primary_only:
                row = conn.execute(
                    text(
                        "SELECT * FROM tracker_accounts WHERE user_id = :u AND is_primary_tracker = true LIMIT 1"
                    ),
                    {"u": user_id},
                ).fetchone()
            else:
                row = conn.execute(
                    text(
                        "SELECT * FROM tracker_accounts WHERE user_id = :u ORDER BY linked_at DESC LIMIT 1"
                    ),
                    {"u": user_id},
                ).fetchone()
            return None if not row else dict(row._mapping)

    def list_tracker_accounts(self, user_id: int) -> list[dict]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT provider, provider_user_id, expires_at, scopes, is_primary_tracker, linked_at FROM tracker_accounts WHERE user_id = :u"
                ),
                {"u": user_id},
            ).fetchall()
            return [dict(r._mapping) for r in rows]

    def set_primary_tracker(self, user_id: int, provider: str):
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE tracker_accounts SET is_primary_tracker = false WHERE user_id = :u"
                ),
                {"u": user_id},
            )
            conn.execute(
                text(
                    "UPDATE tracker_accounts SET is_primary_tracker = true WHERE user_id = :u AND provider = :p"
                ),
                {"u": user_id, "p": provider},
            )

    def update_tracker_tokens(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: str | None,
    ):
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE tracker_accounts SET access_token = :a, refresh_token = :r, expires_at = :e WHERE user_id = :u AND provider = :p"
                ),
                {
                    "a": access_token,
                    "r": refresh_token,
                    "e": expires_at,
                    "u": user_id,
                    "p": provider,
                },
            )

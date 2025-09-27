import os

from sqlalchemy import create_engine


def get_engine():
    database_url = os.environ.get("FIT_DATABASE_URL")
    if not database_url:
        raise RuntimeError("FIT_DATABASE_URL is not set")
    # future=True enables 2.0 style, pool_size for basic pooling
    return create_engine(database_url, pool_size=10, max_overflow=5, future=True)

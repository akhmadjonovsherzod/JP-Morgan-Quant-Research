"""
Small wrapper around psycopg2 so the rest of the app never has to think
about connection setup/teardown, and every query gets the same
error-handling behaviour.
"""

from contextlib import contextmanager

import psycopg2

from app.config import DB_CONFIG


@contextmanager
def get_connection():
    """
    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    Connection is always closed, even if the query raises.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def is_database_available() -> bool:
    try:
        with get_connection():
            return True
    except psycopg2.OperationalError:
        return False

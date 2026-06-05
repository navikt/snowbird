# Snowflake-config
import io
import os
import sys
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Optional

import snowflake.connector
from alive_progress import alive_bar, alive_it
from snowflake.connector import DictCursor


def _snow_config():
    return {
        "user": os.environ["DBT_USR"],
        "authenticator": "externalbrowser",
        "account": "wx23413.europe-west4.gcp",
        "role": "securityadmin",
        "warehouse": "dev__xs",
    }


def spinner(title: str):
    return alive_bar(
        title=title,
        elapsed=False,
        stats=False,
        monitor=False,
    )


def progressbar(*args, **kwargs):
    return alive_it(*args, **kwargs)


def snowflake_cursor(config: Optional[dict] = None):
    if config is None:
        config = _snow_config()
    sys.stdout = io.StringIO()
    cursor = snowflake.connector.connect(**config).cursor(DictCursor)
    sys.stdout = sys.__stdout__
    return cursor


class ConnectionPool:
    """Thread-safe pool of Snowflake connections."""

    def __init__(self, size: int = 10, config: Optional[dict] = None):
        if config is None:
            config = _snow_config()
        self._pool: Queue = Queue(maxsize=size)
        self._all_connections: list = []

        sys.stdout = io.StringIO()
        try:
            for _ in range(size):
                conn = snowflake.connector.connect(**config)
                self._all_connections.append(conn)
                self._pool.put(conn)
        except Exception:
            self.close()
            raise
        finally:
            sys.stdout = sys.__stdout__

    @contextmanager
    def get_cursor(self):
        conn = self._pool.get()
        cursor = conn.cursor(DictCursor)
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            finally:
                self._pool.put(conn)

    def close(self):
        for conn in self._all_connections:
            try:
                conn.close()
            except Exception:
                pass
        self._all_connections.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

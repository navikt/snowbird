# Snowflake-config
import io
import os
import sys

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
        refresh_secs=0.05,
    )


def progressbar(*args, **kwargs):
    return alive_it(*args, **kwargs)


def snowflake_cursor(config: dict = _snow_config()):
    sys.stdout = io.StringIO()
    cursor = snowflake.connector.connect(**config).cursor(DictCursor)
    sys.stdout = sys.__stdout__
    return cursor

import os

import snowflake.connector
from snowflake.connector.cursor import DictCursor

from snowbird.utils import _snow_config


def current_state() -> dict:
    with snowflake.connector.connect(**_snow_config()) as connection:
        with connection.cursor(DictCursor) as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            cursor.execute("SHOW WAREHOUSES")
            warehouses = cursor.fetchall()
            cursor.execute("SHOW SCHEMAS")
            schemas = cursor.fetchall()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            cursor.execute("SHOW VIEWS")
            views = cursor.fetchall()
            cursor.execute("SHOW USERS")
            users = cursor.fetchall()
            cursor.execute("SHOW ROLES")
            roles = cursor.fetchall()
            cursor.execute("SHOW GRANTS")
            grants = cursor.fetchall()
    return {
        "databases": databases,
        "warehouses": warehouses,
        "schemas": schemas,
        "tables": tables,
        "views": views,
        "users": users,
        "roles": roles,
        "grants": grants,
    }

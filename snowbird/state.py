from snowflake.connector.cursor import SnowflakeCursor

from snowbird.utils import snowflake_cursor


def _get_schemas(databases: list[dict]) -> list[str]:
    schemas = []
    for database in databases:
        db_schemas = database.get("schemas", [])
        for schema in db_schemas:
            full_schema_name = f"{database.get('name')}.{schema.get('name')}"
            schemas.append(full_schema_name)
    return schemas


def _get_db_grants(databases: list[dict], cursor: SnowflakeCursor) -> list[dict]:
    grants: list[dict] = []
    for database in databases:
        db_name = database.get("name")
        cursor.execute(f"show grants on database {db_name}")
        grants.extend(cursor.fetchall())
    return grants


def _get_schema_grants(schemas: list[str], cursor: SnowflakeCursor) -> list[dict]:
    grants: list[dict] = []
    for schema in schemas:
        cursor.execute(f"show grants on schema {schema}")
        grants.extend(cursor.fetchall())
    return grants


def _get_schema_future_grants(
    schemas: list[str], cursor: SnowflakeCursor
) -> list[dict]:
    grants: list[dict] = []
    for schema in schemas:
        cursor.execute(f"show future grants in schema {schema}")
        grants.extend(cursor.fetchall())
    return grants


def _get_role_grants(roles: list[dict], cursor: SnowflakeCursor) -> list[dict]:
    grants: list[dict] = []
    for role in roles:
        cursor.execute(f"show grants to role {role['name']}")
        grants.extend(cursor.fetchall())
    return grants


def current_state(config: dict) -> dict:
    assert config is not None, "Config must be provided"

    db_config = config.get("databases", [])
    db_schemas = _get_schemas(db_config)
    roles_config = config.get("roles", [])

    with snowflake_cursor() as cursor:
        cursor.execute("show databases")
        databases = cursor.fetchall()
        cursor.execute("show warehouses")
        warehouses = cursor.fetchall()
        cursor.execute("show schemas")
        schemas = cursor.fetchall()
        cursor.execute("show users")
        users = cursor.fetchall()
        cursor.execute("show roles")
        roles = cursor.fetchall()
    return {
        "databases": databases,
        "warehouses": warehouses,
        "schemas": schemas,
        "users": users,
        "roles": roles,
    }

import snowflake
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


def _get_of_role_grants(roles: list[dict], cursor: SnowflakeCursor) -> dict:
    grants: dict = {}
    for role in roles:
        try:
            cursor.execute(f"show grants of role {role['name']}")
            grants[role["name"]] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError as e:
            # This error is expected if the role does not exist
            pass
    return grants


def current_state(config: dict) -> dict:
    assert config is not None, "Config must be provided"

    db_config = config.get("databases", [])
    db_schemas = _get_schemas(db_config)
    roles_config = config.get("roles", [])

    with snowflake_cursor() as cursor:
        databases = cursor.execute("show databases").fetchall()
        warehouses = cursor.execute("show warehouses").fetchall()
        schemas = cursor.execute("show schemas").fetchall()
        users = cursor.execute("show users").fetchall()
        roles = cursor.execute("show roles").fetchall()
        grants_of_roles = _get_of_role_grants(roles_config, cursor)
    return {
        "databases": databases,
        "warehouses": warehouses,
        "schemas": schemas,
        "users": users,
        "roles": roles,
        "grants": {"of_roles": grants_of_roles},
    }

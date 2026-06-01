import json

import snowflake
from snowflake.connector.cursor import SnowflakeCursor

from snowbird.utils import snowflake_cursor


def _get_role_grants(roles: list[dict], cursor: SnowflakeCursor) -> dict:
    grants: dict = {}
    for role in roles:
        try:
            cursor.execute(f"show grants of role {role['name']}")
            grants[role["name"]] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError as e:
            # This error is expected if the role does not exist
            pass
    return grants


def _get_warehouse_grants(
    grants_config: list[dict], cursor: SnowflakeCursor
) -> dict:
    managed_warehouses: set[str] = set()
    for grant in grants_config:
        for wh in grant.get("warehouses", []):
            managed_warehouses.add(wh.lower())

    warehouse_grants: dict = {}
    for warehouse in managed_warehouses:
        try:
            cursor.execute(f"show grants on warehouse {warehouse}")
            warehouse_grants[warehouse] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return warehouse_grants


def _get_database_grants(
    grants_config: list[dict], cursor: SnowflakeCursor
) -> dict:
    managed_databases: set[str] = set()
    for grant in grants_config:
        for schema_path in grant.get("read_on_schemas", []) + grant.get(
            "write_on_schemas", []
        ):
            managed_databases.add(schema_path.split(".")[0].lower())
        for obj in grant.get("read_on_objects", []):
            _, obj_path = obj.split(":", 1)
            managed_databases.add(obj_path.split(".")[0].lower())

    database_grants: dict = {}
    for database in managed_databases:
        try:
            cursor.execute(f"show grants on database {database}")
            database_grants[database] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return database_grants


def _get_schema_grants(
    grants_config: list[dict], cursor: SnowflakeCursor
) -> dict:
    managed_schemas: set[str] = set()
    for grant in grants_config:
        for schema_path in grant.get("read_on_schemas", []) + grant.get(
            "write_on_schemas", []
        ):
            managed_schemas.add(schema_path.lower())
        for obj in grant.get("read_on_objects", []):
            _, obj_path = obj.split(":", 1)
            parts = obj_path.split(".")
            if len(parts) >= 3:
                managed_schemas.add(f"{parts[0]}.{parts[1]}".lower())

    schema_grants: dict = {}
    for schema_path in managed_schemas:
        try:
            cursor.execute(f"show grants on schema {schema_path}")
            schema_grants[schema_path] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return schema_grants


def _get_future_schema_grants(
    grants_config: list[dict], cursor: SnowflakeCursor
) -> dict:
    managed_schemas: set[str] = set()
    for grant in grants_config:
        for schema_path in grant.get("read_on_schemas", []):
            managed_schemas.add(schema_path.lower())

    future_grants: dict = {}
    for schema_path in managed_schemas:
        try:
            cursor.execute(f"show future grants in schema {schema_path}")
            future_grants[schema_path] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return future_grants


_OBJECT_TYPE_MAP = {
    "table": "table",
    "view": "view",
    "dynamic_table": "dynamic table",
    "semantic_view": "semantic view",
}


def _get_object_grants(
    grants_config: list[dict], cursor: SnowflakeCursor
) -> dict:
    managed_objects: list[tuple[str, str, str]] = []
    for grant in grants_config:
        for obj in grant.get("read_on_objects", []):
            prefix, obj_path = obj.split(":", 1)
            sf_type = _OBJECT_TYPE_MAP.get(prefix, prefix)
            managed_objects.append((prefix, sf_type, obj_path.lower()))

    object_grants: dict = {}
    seen: set[str] = set()
    for prefix, sf_type, obj_path in managed_objects:
        key = f"{prefix}:{obj_path}"
        if key in seen:
            continue
        seen.add(key)
        try:
            cursor.execute(f"show grants on {sf_type} {obj_path}")
            object_grants[key] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return object_grants


def _get_users_state(users: list[dict], cursor: SnowflakeCursor) -> list[dict]:

    state = []
    for user in users:
        try:
            # Fetch user details
            cursor.execute(f"show users like '{user['name']}'")
            user_details = cursor.fetchone()
            # Fetch network policy for each user
            cursor.execute(
                f"show parameters like 'NETWORK_POLICY' for user {user['name']}"
            )
            network_policy = cursor.fetchone()
            state.append(
                {
                    "name": user_details["name"],
                    "type": user_details["type"],
                    "network_policy": network_policy["value"],
                }
            )
        except snowflake.connector.errors.ProgrammingError:
            pass

    return state


def _get_network_policies(
    network_policies: list[dict], cursor: SnowflakeCursor
) -> dict:
    state = {}
    for policy in network_policies:
        try:
            cursor.execute(f"show network policies like '{policy['name']}'")
            policy_details = cursor.fetchone()
            if not policy_details:
                continue
            np = {
                "comment": policy_details["comment"],
            }
            cursor.execute(f"describe network policy {policy['name']}")
            res = cursor.fetchall()
            for row in res:
                if row["name"] == "ALLOWED_NETWORK_RULE_LIST":
                    np["allowed_network_rule_list"] = json.loads(row["value"])
                elif row["name"] == "BLOCKED_NETWORK_RULE_LIST":
                    np["blocked_network_rule_list"] = json.loads(row["value"])
            state[policy["name"]] = np
        except snowflake.connector.errors.ProgrammingError:
            pass

    return state


def current_state(config: dict) -> dict:
    assert config is not None, "Config must be provided"

    roles_config = config.get("roles", [])
    users_config = config.get("users", [])
    network_policies_config = config.get("network_policies", [])
    grants_config = config.get("grants", [])

    with snowflake_cursor() as cursor:
        databases = cursor.execute("show databases").fetchall()
        warehouses = cursor.execute("show warehouses").fetchall()
        schemas = cursor.execute("show schemas").fetchall()
        users = _get_users_state(users_config, cursor)
        roles = cursor.execute("show roles").fetchall()
        grants_of_roles = _get_role_grants(roles_config, cursor)
        warehouse_grants = _get_warehouse_grants(grants_config, cursor)
        database_grants = _get_database_grants(grants_config, cursor)
        schema_grants = _get_schema_grants(grants_config, cursor)
        future_schema_grants = _get_future_schema_grants(grants_config, cursor)
        object_grants = _get_object_grants(grants_config, cursor)
        network_policies = _get_network_policies(network_policies_config, cursor)
    return {
        "databases": databases,
        "warehouses": warehouses,
        "schemas": schemas,
        "users": users,
        "roles": roles,
        "grants": {
            "of_roles": grants_of_roles,
            "on_warehouses": warehouse_grants,
            "on_databases": database_grants,
            "on_schemas": schema_grants,
            "future_in_schemas": future_schema_grants,
            "on_objects": object_grants,
        },
        "network_policies": network_policies,
    }

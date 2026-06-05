import json
from concurrent.futures import ThreadPoolExecutor

import snowflake
from snowflake.connector.cursor import SnowflakeCursor

from snowbird.utils import ConnectionPool


def _execute_query(pool: ConnectionPool, sql: str) -> list[dict]:
    """Execute a single query using a connection from the pool."""
    with pool.get_cursor() as cursor:
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            return []


def _async_fetch_all(
    cursor: SnowflakeCursor, items: list[tuple[str, str]]
) -> dict[str, list[dict]]:
    """Submit queries async, collect results. Items: [(key, sql), ...]."""
    query_ids: dict[str, str] = {}
    for key, sql in items:
        try:
            cursor.execute_async(sql)
            query_ids[key] = cursor.sfqid
        except snowflake.connector.errors.ProgrammingError:
            pass

    results: dict[str, list[dict]] = {}
    for key, qid in query_ids.items():
        try:
            cursor.get_results_from_sfqid(qid)
            results[key] = cursor.fetchall()
        except snowflake.connector.errors.ProgrammingError:
            pass
    return results


def _get_role_grants(roles: list[dict], pool: ConnectionPool) -> dict:
    if not roles:
        return {}
    items = [(role["name"], f"show grants of role {role['name']}") for role in roles]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_warehouse_grants(warehouses_config: list[dict], pool: ConnectionPool) -> dict:
    managed_warehouses = [wh["name"].lower() for wh in warehouses_config]
    if not managed_warehouses:
        return {}
    items = [(wh, f"show grants on warehouse {wh}") for wh in managed_warehouses]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_database_grants(databases_config: list[dict], pool: ConnectionPool) -> dict:
    managed_databases = [db["name"].lower() for db in databases_config]
    if not managed_databases:
        return {}
    items = [(db, f"show grants on database {db}") for db in managed_databases]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_schema_grants(databases_config: list[dict], pool: ConnectionPool) -> dict:
    managed_schemas: list[str] = []
    for db in databases_config:
        db_name = db["name"].lower()
        for schema in db.get("schemas", []):
            managed_schemas.append(f"{db_name}.{schema['name'].lower()}")
    if not managed_schemas:
        return {}
    items = [(s, f"show grants on schema {s}") for s in managed_schemas]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_future_schema_grants(
    databases_config: list[dict], pool: ConnectionPool
) -> dict:
    managed_schemas: list[str] = []
    for db in databases_config:
        db_name = db["name"].lower()
        for schema in db.get("schemas", []):
            managed_schemas.append(f"{db_name}.{schema['name'].lower()}")
    if not managed_schemas:
        return {}
    items = [(s, f"show future grants in schema {s}") for s in managed_schemas]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


_OBJECT_TYPE_MAP = {
    "table": "table",
    "view": "view",
    "dynamic_table": "dynamic table",
    "semantic_view": "semantic view",
}


def _get_object_privileges(databases_config: list[dict], pool: ConnectionPool) -> dict:
    managed_databases = [db["name"].lower() for db in databases_config]
    if not managed_databases:
        return {}
    items = [
        (
            db,
            f"SELECT GRANTEE, PRIVILEGE_TYPE, OBJECT_TYPE, OBJECT_NAME, OBJECT_SCHEMA"
            f" FROM {db}.information_schema.object_privileges"
            f" WHERE PRIVILEGE_TYPE != 'OWNERSHIP'"
            f" AND OBJECT_TYPE NOT IN ('DATABASE', 'SCHEMA')",
        )
        for db in managed_databases
    ]
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_object_grants(grants_config: list[dict], pool: ConnectionPool) -> dict:
    managed_objects: list[tuple[str, str, str]] = []
    for grant in grants_config:
        for obj in grant.get("read_on_objects", []):
            prefix, obj_path = obj.split(":", 1)
            sf_type = _OBJECT_TYPE_MAP.get(prefix, prefix)
            managed_objects.append((prefix, sf_type, obj_path.lower()))

    seen: set[str] = set()
    items: list[tuple[str, str]] = []
    for prefix, sf_type, obj_path in managed_objects:
        key = f"{prefix}:{obj_path}"
        if key in seen:
            continue
        seen.add(key)
        items.append((key, f"show grants on {sf_type} {obj_path}"))

    if not items:
        return {}
    with pool.get_cursor() as cursor:
        return _async_fetch_all(cursor, items)


def _get_users_state(users: list[dict], pool: ConnectionPool) -> list[dict]:
    if not users:
        return []

    state = []
    for user in users:
        name = user["name"]
        details = _execute_query(pool, f"show users like '{name}'")
        policies = _execute_query(
            pool, f"show parameters like 'NETWORK_POLICY' for user {name}"
        )
        if details and policies:
            state.append(
                {
                    "name": details[0]["name"],
                    "type": details[0]["type"],
                    "network_policy": policies[0]["value"],
                }
            )
    return state


def _get_network_policies(network_policies: list[dict], pool: ConnectionPool) -> dict:
    if not network_policies:
        return {}

    state = {}
    for policy in network_policies:
        name = policy["name"]
        details = _execute_query(pool, f"show network policies like '{name}'")
        if not details:
            continue
        np: dict = {"comment": details[0]["comment"]}
        rows = _execute_query(pool, f"describe network policy {name}")
        for row in rows:
            if row["name"] == "ALLOWED_NETWORK_RULE_LIST":
                np["allowed_network_rule_list"] = json.loads(row["value"])
            elif row["name"] == "BLOCKED_NETWORK_RULE_LIST":
                np["blocked_network_rule_list"] = json.loads(row["value"])
        state[name] = np
    return state


def current_state(config: dict, pool_size: int = 10) -> dict:
    assert config is not None, "Config must be provided"

    roles_config = config.get("roles", [])
    users_config = config.get("users", [])
    network_policies_config = config.get("network_policies", [])
    databases_config = config.get("databases", [])
    warehouses_config = config.get("warehouses", [])
    grants_config = config.get("grants", [])

    with ConnectionPool(size=pool_size) as pool:
        with ThreadPoolExecutor(max_workers=pool_size) as executor:
            f_databases = executor.submit(_execute_query, pool, "show databases")
            f_warehouses = executor.submit(_execute_query, pool, "show warehouses")
            f_schemas = executor.submit(_execute_query, pool, "show schemas")
            f_roles = executor.submit(_execute_query, pool, "show roles")
            f_users = executor.submit(_get_users_state, users_config, pool)
            f_role_grants = executor.submit(_get_role_grants, roles_config, pool)
            f_wh_grants = executor.submit(
                _get_warehouse_grants, warehouses_config, pool
            )
            f_db_grants = executor.submit(_get_database_grants, databases_config, pool)
            f_schema_grants = executor.submit(
                _get_schema_grants, databases_config, pool
            )
            f_future_grants = executor.submit(
                _get_future_schema_grants, databases_config, pool
            )
            f_obj_grants = executor.submit(_get_object_grants, grants_config, pool)
            f_obj_privs = executor.submit(
                _get_object_privileges, databases_config, pool
            )
            f_net_policies = executor.submit(
                _get_network_policies, network_policies_config, pool
            )

        return {
            "databases": f_databases.result(),
            "warehouses": f_warehouses.result(),
            "schemas": f_schemas.result(),
            "users": f_users.result(),
            "roles": f_roles.result(),
            "grants": {
                "of_roles": f_role_grants.result(),
                "on_warehouses": f_wh_grants.result(),
                "on_databases": f_db_grants.result(),
                "on_schemas": f_schema_grants.result(),
                "future_in_schemas": f_future_grants.result(),
                "on_objects": f_obj_grants.result(),
                "object_privileges": f_obj_privs.result(),
            },
            "network_policies": f_net_policies.result(),
        }

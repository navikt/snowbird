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

    with snowflake_cursor() as cursor:
        databases = cursor.execute("show databases").fetchall()
        warehouses = cursor.execute("show warehouses").fetchall()
        schemas = cursor.execute("show schemas").fetchall()
        users = _get_users_state(users_config, cursor)
        roles = cursor.execute("show roles").fetchall()
        grants_of_roles = _get_role_grants(roles_config, cursor)
        network_policies = _get_network_policies(network_policies_config, cursor)
    return {
        "databases": databases,
        "warehouses": warehouses,
        "schemas": schemas,
        "users": users,
        "roles": roles,
        "grants": {"of_roles": grants_of_roles},
        "network_policies": network_policies,
    }

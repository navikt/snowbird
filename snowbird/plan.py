import jinja2
import yaml

use_sysadmin = "use role sysadmin"
use_useradmin = "use role useradmin"
use_securityadmin = "use role securityadmin"

create_database = "create {%- if transient %} transient {%- endif %} database if not exists {{ database }}"
create_schema = "create {%- if transient %} transient {%- endif %} schema if not exists {{ database }}.{{ schema }}"

alter_database_data_retention = "alter database {{ database }} set data_retention_time_in_days = {{ retention_days }}"
alter_schema_data_retention = "alter schema {{ database }}.{{ schema }} set data_retention_time_in_days = {{ retention_days }}"

create_warehouse = """
    create warehouse if not exists {{ warehouse }} with
        warehouse_size = '{{ size }}'
        auto_suspend = 30
        initially_suspended = true
"""
alter_warehouse = """
    alter warehouse {{ warehouse }} set
        warehouse_size = '{{ size }}'
"""

create_user = """
    create user if not exists {{ user }}
        type = {{ type }}
        network_policy = {{ network_policy }}
"""
alter_user = """
    alter user {{ user }} set type = {{ type }} network_policy = {{ network_policy }}
"""

create_role = """
    create role if not exists {{ role }}
"""

create_network_policy = """
    create network policy if not exists {{ name }}
        allowed_network_rule_list = (
            {% for rule in allowed_network_rule_list %}
                '{{ rule }}'{% if not loop.last %}, {% endif %}
            {% endfor %}
        )
        blocked_network_rule_list = (
            {% for rule in blocked_network_rule_list %}
                '{{ rule }}'{% if not loop.last %}, {% endif %}
            {% endfor %}
        )
        comment = '{{ comment }}'
"""

alter_network_policy = """
    alter network policy {{ name }} set
        allowed_network_rule_list = (
            {% for rule in allowed_network_rule_list %}
                '{{ rule }}'{% if not loop.last %}, {% endif %}
            {% endfor %}
        )
        blocked_network_rule_list = (
            {% for rule in blocked_network_rule_list %}
                '{{ rule }}'{% if not loop.last %}, {% endif %}
            {% endfor %}
        )
        comment = '{{ comment }}'
"""

grant_role_usage_on_warehouse = """
    grant usage on warehouse {{ warehouse }} to role {{ role }}
"""
grant_role_usage_on_database = """
    grant usage on database {{ database }} to role {{ role }}
"""
grant_role_usage_on_schema = """
    grant usage on schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_create_on_schema = """
    grant create {{ type }} on schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_read_on_tables_in_schema = """
    grant select on all tables in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_future_read_on_tables_in_schema = """
    grant select on future tables in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_read_on_views_in_schema = """
    grant select on all views in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_future_read_on_views_in_schema = """
    grant select on future views in schema {{ database }}.{{ schema }} to role {{ role }}
"""

grant_role_to_user = """
    grant role {{ role }} to user "{{ to_user.upper() }}"
"""
grant_role_to_role = """
    grant role {{ role }} to role "{{ to_role.upper() }}"
"""

revoke_grant_role_from_user = """
    revoke role {{ role }} from user "{{ to_user.upper() }}"
"""
revoke_grant_role_from_role = """
    revoke role {{ role }} from role "{{ to_role.upper() }}"
"""

DEFAULT_RETENTION_TIME = "7"
DEFAULT_TRANSIENT_RETENTION_TIME = "1"
DEFAULT_TRANSIENT = False
DEFAULT_WAREHOUSE_SIZE = "x-small"

jinja_env = jinja2.Environment()


class UnmodifiableStateError(Exception):
    pass


def load_config(path: str) -> dict:
    with open(path) as file:
        file_content = file.read().lower()
        return yaml.safe_load(file_content)


def _create_databases_execution_plan(databases: list[dict], state: dict) -> list[str]:
    if len(databases) == 0:
        return []
    execution_plan = []
    for database in databases:
        db_name = database["name"]
        db_transient = database.get("transient", DEFAULT_TRANSIENT)
        db_data_retention_time_in_days = str(
            database.get("data_retention_time_in_days", DEFAULT_RETENTION_TIME)
        )
        db_state = state.get(db_name)

        if db_transient:
            db_data_retention_time_in_days = DEFAULT_TRANSIENT_RETENTION_TIME

        if db_state is None:
            create_database_statement = jinja_env.from_string(create_database).render(
                database=db_name, transient=db_transient
            )
            execution_plan.append(create_database_statement)

            if db_transient == False:
                alter_database_data_retention_statement = jinja_env.from_string(
                    alter_database_data_retention
                ).render(
                    database=db_name, retention_days=db_data_retention_time_in_days
                )
                execution_plan.append(alter_database_data_retention_statement)
            continue

        if db_transient != db_state["transient"]:
            raise UnmodifiableStateError(
                f"Cannot change transient state of database {db_name}. It is currently {db_state['transient']}. Please modify the database manually."
            )

        if db_data_retention_time_in_days != db_state["data_retention_time_in_days"]:
            alter_database_data_retention_statement = jinja_env.from_string(
                alter_database_data_retention
            ).render(database=db_name, retention_days=db_data_retention_time_in_days)
            execution_plan.append(alter_database_data_retention_statement)

    return execution_plan


def _create_schema_execution_plan(databases: list[dict], state: dict) -> list[str]:
    if len(databases) == 0:
        return []
    execution_plan = []
    for database in databases:
        db_name = database["name"]
        db_transient = database.get("transient", DEFAULT_TRANSIENT)
        db_data_retention_time_in_days = str(
            database.get("data_retention_time_in_days", DEFAULT_RETENTION_TIME)
        )
        schemas = database["schemas"]
        for schema in schemas:
            schema_name = schema["name"]
            full_schema_name = f"{db_name.lower()}.{schema_name.lower()}"
            schema_transient = schema.get("transient", db_transient)
            schema_data_retention_time_in_days = str(
                schema.get(
                    "data_retention_time_in_days", db_data_retention_time_in_days
                )
            )
            schema_state = state.get(full_schema_name)

            if schema_transient:
                schema_data_retention_time_in_days = DEFAULT_TRANSIENT_RETENTION_TIME

            if schema_state is None:
                create_schema_statement = jinja_env.from_string(create_schema).render(
                    database=db_name, schema=schema_name, transient=schema_transient
                )
                execution_plan.append(create_schema_statement)

                if schema_transient == False:
                    alter_schema_data_retention_statement = jinja_env.from_string(
                        alter_schema_data_retention
                    ).render(
                        database=db_name,
                        schema=schema_name,
                        retention_days=schema_data_retention_time_in_days,
                    )
                    execution_plan.append(alter_schema_data_retention_statement)
                continue

            if schema_transient != schema_state["transient"]:
                raise UnmodifiableStateError(
                    f"Cannot change transient state of schema {full_schema_name}. It is currently {schema_state['transient']}. Please modify the schema manually."
                )
            if (
                schema_data_retention_time_in_days
                != schema_state["data_retention_time_in_days"]
            ):
                alter_schema_data_retention_statement = jinja_env.from_string(
                    alter_schema_data_retention
                ).render(
                    database=db_name,
                    schema=schema_name,
                    retention_days=schema_data_retention_time_in_days,
                )
                execution_plan.append(alter_schema_data_retention_statement)
    return execution_plan


def _create_warehouses_execution_plan(warehouses: list[dict], state: dict) -> list[str]:
    if len(warehouses) == 0:
        return []
    execution_plan = []
    for warehouse in warehouses:
        warehouse_name = warehouse["name"]
        warehouse_size = warehouse.get("size", DEFAULT_WAREHOUSE_SIZE)
        warehouse_state = state.get(warehouse_name)

        if warehouse_state is None:
            create_warehouse_statement = jinja_env.from_string(create_warehouse).render(
                warehouse=warehouse_name, size=warehouse_size
            )
            execution_plan.append(create_warehouse_statement)

            alter_warehouse_statement = jinja_env.from_string(alter_warehouse).render(
                warehouse=warehouse_name, size=warehouse_size
            )
            execution_plan.append(alter_warehouse_statement)
            continue
        if warehouse_size != warehouse_state["size"]:
            alter_warehouse_statement = jinja_env.from_string(alter_warehouse).render(
                warehouse=warehouse_name, size=warehouse_size
            )
            execution_plan.append(alter_warehouse_statement)
    return execution_plan


def _create_users_execution_plan(users: list[dict], state: dict) -> list[str]:
    if len(users) == 0:
        return []
    execution_plan = []
    for user in users:
        user_name = user["name"]
        user_type = user["type"]
        user_network_policy = user["network_policy"]
        user_state = state.get(user_name)

        if user_state is None:
            create_user_statement = jinja_env.from_string(create_user).render(
                user=user_name, type=user_type, network_policy=user_network_policy
            )
            execution_plan.append(create_user_statement)
            alter_user_statement = jinja_env.from_string(alter_user).render(
                user=user_name, type=user_type, network_policy=user_network_policy
            )
            execution_plan.append(alter_user_statement)
            continue
        if (
            user_type != user_state["type"]
            or user_network_policy != user_state["network_policy"]
        ):
            alter_user_statement = jinja_env.from_string(alter_user).render(
                user=user_name, type=user_type, network_policy=user_network_policy
            )
            execution_plan.append(alter_user_statement)
    return execution_plan


def _create_roles_execution_plan(roles: list[dict], state: dict) -> list[str]:
    if len(roles) == 0:
        return []
    execution_plan = []
    for role in roles:
        role_name = role["name"]
        role_state = state.get(role_name)

        if role_state is None:
            create_role_statement = jinja_env.from_string(create_role).render(
                role=role_name
            )
            execution_plan.append(create_role_statement)
    return execution_plan


def _grant_role_execution_plan(grants: list[dict], state: dict) -> list[str]:
    if len(grants) == 0:
        return []
    execution_plan = []
    for grant in grants:
        role = grant["role"]
        warehouses = grant.get("warehouses", [])
        read_on_schemas = grant.get("read_on_schemas", [])
        write_on_schemas = grant.get("write_on_schemas", [])
        to_roles = grant.get("to_roles", [])
        to_users = grant.get("to_users", [])

        for warehouse in warehouses:
            grant_role_usage_on_warehouse_statement = jinja_env.from_string(
                grant_role_usage_on_warehouse
            ).render(role=role, warehouse=warehouse)
            execution_plan.append(grant_role_usage_on_warehouse_statement)

        for full_schema_path in read_on_schemas:
            database, schema = full_schema_path.split(".")
            grant_role_usage_on_database_statement = jinja_env.from_string(
                grant_role_usage_on_database
            ).render(role=role, database=database)
            execution_plan.append(grant_role_usage_on_database_statement)

            grant_role_usage_on_schema_statement = jinja_env.from_string(
                grant_role_usage_on_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_usage_on_schema_statement)

            grant_role_read_on_schema_statement = jinja_env.from_string(
                grant_role_read_on_tables_in_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_read_on_schema_statement)

            grant_role_future_read_on_schema_statement = jinja_env.from_string(
                grant_role_future_read_on_tables_in_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_future_read_on_schema_statement)

            grant_role_read_on_views_in_schema_statement = jinja_env.from_string(
                grant_role_read_on_views_in_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_read_on_views_in_schema_statement)

            grant_role_future_read_on_views_in_schema_statement = jinja_env.from_string(
                grant_role_future_read_on_views_in_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_future_read_on_views_in_schema_statement)

        for full_schema_path in write_on_schemas:
            database, schema = full_schema_path.split(".")
            grant_role_usage_on_database_statement = jinja_env.from_string(
                grant_role_usage_on_database
            ).render(role=role, database=database)
            execution_plan.append(grant_role_usage_on_database_statement)

            grant_role_usage_on_schema_statement = jinja_env.from_string(
                grant_role_usage_on_schema
            ).render(role=role, database=database, schema=schema)
            execution_plan.append(grant_role_usage_on_schema_statement)

            create_types = ["table", "view", "dynamic table", "task", "alert"]
            for type in create_types:
                grant_role_create_on_schema_statement = jinja_env.from_string(
                    grant_role_create_on_schema
                ).render(type=type, role=role, database=database, schema=schema)
                execution_plan.append(grant_role_create_on_schema_statement)

        # Grant and revoke roles to users and roles
        grant_of_role_state = state.get("of_roles", {}).get(role)
        if grant_of_role_state is None:
            for to_role in to_roles:
                grant_role_to_role_statement = jinja_env.from_string(
                    grant_role_to_role
                ).render(role=role, to_role=to_role)
                execution_plan.append(grant_role_to_role_statement)

            for to_user in to_users:
                grant_role_to_user_statement = jinja_env.from_string(
                    grant_role_to_user
                ).render(role=role, to_user=to_user)
                execution_plan.append(grant_role_to_user_statement)
            continue

        to_roles_exists_in_database = [
            grant["grantee_name"].lower()
            for grant in grant_of_role_state
            if grant["granted_to"].lower() == "role"
        ]
        to_users_exists_in_database = [
            grant["grantee_name"].lower()
            for grant in grant_of_role_state
            if grant["granted_to"].lower() == "user"
        ]
        # grant user
        for to_user in to_users:
            if to_user in to_users_exists_in_database:
                continue
            grant_role_to_user_statement = jinja_env.from_string(
                grant_role_to_user
            ).render(role=role, to_user=to_user)
            execution_plan.append(grant_role_to_user_statement)
        # revoke user
        for to_user in to_users_exists_in_database:
            if to_user in to_users:
                continue
            revoke_grant_role_from_user_statement = jinja_env.from_string(
                revoke_grant_role_from_user
            ).render(role=role, to_user=to_user.upper())
            execution_plan.append(revoke_grant_role_from_user_statement)
        # grant role
        for to_role in to_roles:
            if to_role in to_roles_exists_in_database:
                continue
            grant_role_to_role_statement = jinja_env.from_string(
                grant_role_to_role
            ).render(role=role, to_role=to_role)
            execution_plan.append(grant_role_to_role_statement)
        # revoke role
        for to_role in to_roles_exists_in_database:
            if to_role in to_roles:
                continue
            revoke_grant_role_to_role_statement = jinja_env.from_string(
                revoke_grant_role_from_role
            ).render(role=role, to_role=to_role)
            execution_plan.append(revoke_grant_role_to_role_statement)

    return execution_plan


def _trim_sql_statements(execution_plan: list[str]) -> list[str]:
    result_trimmed = []
    for line in execution_plan:
        line_trimmed_list = []
        for l in line.split("\n"):
            line_trimmed_list.append(l.strip()) if l.strip() else None
        line_trimmed = " ".join(line_trimmed_list)
        result_trimmed.append(line_trimmed)
    return result_trimmed


def _database_state(databases: list[dict], state: dict) -> dict:
    if len(databases) == 0:
        return {}
    if state.get("databases") is None:
        return {}
    database_names = [database["name"].lower() for database in databases]
    return {
        database["name"].lower(): {
            "data_retention_time_in_days": database["retention_time"],
            "transient": True if "transient" in database["options"].lower() else False,
        }
        for database in state["databases"]
        if database["name"].lower() in database_names
    }


def _schema_state(databases: list[dict], state: dict) -> dict:
    if len(databases) == 0:
        return {}
    if state.get("schemas") is None:
        return {}
    existing_state = {}
    for database in databases:
        db_name = database["name"]
        schemas = database["schemas"]
        for schema_state in state["schemas"]:
            schema_state_name = schema_state["name"].lower()
            schema_state_db_name = schema_state["database_name"].lower()
            if schema_state_db_name != db_name:
                continue
            for schema in schemas:
                schema_name = schema["name"].lower()
                if schema_name == schema_state_name:
                    existing_state[f"{schema_state_db_name}.{schema_name}"] = {
                        "data_retention_time_in_days": schema_state["retention_time"],
                        "transient": (
                            True
                            if "transient" in schema_state["options"].lower()
                            else False
                        ),
                        "schema": schema_state,
                    }
    return existing_state


def _warehouse_state(warehouses: list[dict], state: dict) -> dict:
    if len(warehouses) == 0:
        return {}
    if state.get("warehouses") is None:
        return {}
    existing_state = {}
    for warehouse in warehouses:
        warehouse_name = warehouse["name"].lower()
        for warehouse_state in state["warehouses"]:
            if warehouse_name == warehouse_state["name"].lower():
                existing_state[warehouse_name] = {
                    "size": warehouse_state["size"].lower(),
                }
    return existing_state


def _user_state(users: list[dict], state: dict) -> dict:
    if len(users) == 0:
        return {}
    if state.get("users") is None:
        return {}
    existing_state = {}
    for user in users:
        user_name = user["name"].lower()
        for user_state in state["users"]:
            if user_name == user_state["name"].lower():
                existing_state[user_name] = {
                    "type": user_state["type"].lower(),
                    "network_policy": user_state.get("network_policy", "").lower(),
                }
    return existing_state


def _role_state(roles: list[dict], state: dict) -> dict:
    if len(roles) == 0:
        return {}
    if state.get("roles") is None:
        return {}
    existing_state: dict = {}
    for role in roles:
        role_name = role["name"].lower()
        for role_state in state["roles"]:
            if role_name == role_state["name"].lower():
                existing_state[role_name] = {}
    return existing_state


def _append_grant_roles_to_sysadmin(grants: list[dict]):
    for grant in grants:
        if "to_roles" not in grant:
            grant["to_roles"] = ["sysadmin"]
            continue
        if "sysadmin" not in grant["to_roles"]:
            grant["to_roles"].append("sysadmin")


def _create_network_policies_execution_plan(
    network_policies: list[dict], state: dict
) -> list[str]:
    if len(network_policies) == 0:
        return []
    execution_plan = []
    for network_policy in network_policies:
        policy_name = network_policy["name"]
        policy_description = network_policy.get("description", "")
        network_rules = network_policy["network_rules"]
        allowed_network_rules = network_rules.get("allowed", [])
        blocked_network_rules = network_rules.get("blocked", [])
        if len(allowed_network_rules) == 0 and len(blocked_network_rules) == 0:
            raise ValueError(
                f"Network policy {policy_name} must have at least one allowed or blocked network rule."
            )

        policy_state = state.get(policy_name)

        if policy_state is None:
            create_network_policy_statement = jinja_env.from_string(
                create_network_policy
            ).render(
                name=policy_name,
                allowed_network_rule_list=allowed_network_rules,
                blocked_network_rule_list=blocked_network_rules,
                comment=policy_description,
            )
            execution_plan.append(create_network_policy_statement)
            alter_network_policy_statement = jinja_env.from_string(
                alter_network_policy
            ).render(
                name=policy_name,
                allowed_network_rule_list=allowed_network_rules,
                blocked_network_rule_list=blocked_network_rules,
                comment=policy_description,
            )
            execution_plan.append(alter_network_policy_statement)
            continue

        policy_state_comment = policy_state.get("comment", "")
        policy_state_allowed_network_rule_list = [
            r["fullyQualifiedRuleName"].lower()
            for r in policy_state.get("allowed_network_rule_list", [])
        ]
        policy_state_blocked_network_rule_list = [
            r["fullyQualifiedRuleName"].lower()
            for r in policy_state.get("blocked_network_rule_list", [])
        ]

        if (
            policy_state_comment != policy_description
            or policy_state_allowed_network_rule_list != allowed_network_rules
            or policy_state_blocked_network_rule_list != blocked_network_rules
        ):
            alter_network_policy_statement = jinja_env.from_string(
                alter_network_policy
            ).render(
                name=policy_name,
                allowed_network_rule_list=allowed_network_rules,
                blocked_network_rule_list=blocked_network_rules,
                comment=policy_description,
            )
            execution_plan.append(alter_network_policy_statement)
            continue

    return execution_plan


def execution_plan(config: dict, state={}) -> list[str]:
    databases = config.get("databases", [])
    warehouses = config.get("warehouses", [])
    users = config.get("users", [])
    roles = config.get("roles", [])
    grants = config.get("grants", [])
    network_policies = config.get("network_policies", [])
    _append_grant_roles_to_sysadmin(grants=grants)

    databases_state = _database_state(databases, state)
    schema_state = _schema_state(databases, state)
    warehouses_state = _warehouse_state(warehouses, state)
    users_state = _user_state(users, state)
    roles_state = _role_state(roles, state)
    grants_state = state.get("grants", {})
    network_policies_state = state.get("network_policies", {})

    plan = []
    plan.extend(
        _create_databases_execution_plan(databases=databases, state=databases_state)
    )
    plan.extend(_create_schema_execution_plan(databases=databases, state=schema_state))
    plan.extend(
        _create_warehouses_execution_plan(warehouses=warehouses, state=warehouses_state)
    )
    if len(plan) > 0:
        plan.insert(0, use_sysadmin)
    plan_len = len(plan)

    plan.extend(
        _create_network_policies_execution_plan(
            network_policies=network_policies, state=network_policies_state
        )
    )
    if len(plan) > plan_len:
        plan.insert(plan_len, use_securityadmin)
    plan_len = len(plan)

    plan.extend(_create_users_execution_plan(users=users, state=users_state))
    plan.extend(_create_roles_execution_plan(roles=roles, state=roles_state))

    plan.extend(_grant_role_execution_plan(grants=grants, state=grants_state))
    if len(plan) > plan_len:
        plan.insert(plan_len, use_useradmin)

    plan = _trim_sql_statements(plan)
    return plan


def overview(execution_plan: dict) -> dict:
    create_databases = [s.split()[5] for s in execution_plan if "create database" in s]
    create_transient_databases = [
        s.split()[6] for s in execution_plan if "create transient database" in s
    ]
    create_databases.extend(create_transient_databases)
    alter_databases = [s.split()[2] for s in execution_plan if "alter database" in s]
    modify_databases = [d for d in alter_databases if d not in create_databases]

    create_schemas = [s.split()[5] for s in execution_plan if "create schema" in s]
    create_transient_schemas = [
        s.split()[6] for s in execution_plan if "create transient schema" in s
    ]
    create_schemas.extend(create_transient_schemas)
    alter_schemas = [s for s in execution_plan if "alter schema" in s]
    modify_schemas = [
        s.split()[2] for s in alter_schemas if s.split()[2] not in create_schemas
    ]

    create_roles = [s.split()[5] for s in execution_plan if "create role" in s]
    alter_roles = [s.split()[2] for s in execution_plan if "alter role" in s]
    modify_roles = [r for r in alter_roles if r not in create_roles]

    create_users = [s.split()[5] for s in execution_plan if "create user" in s]
    alter_users = [s.split()[2] for s in execution_plan if "alter user" in s]
    modify_users = [u for u in alter_users if u not in create_users]

    create_warehouses = [
        s.split()[5] for s in execution_plan if "create warehouse" in s
    ]
    alter_warehouses = [s.split()[2] for s in execution_plan if "alter warehouse" in s]
    modify_warehouses = [w for w in alter_warehouses if w not in create_warehouses]

    create_network_policies = [
        s.split()[6] for s in execution_plan if "create network policy" in s
    ]
    alter_network_policies = [
        s.split()[3] for s in execution_plan if "alter network policy" in s
    ]
    modify_network_policies = [
        s for s in alter_network_policies if s not in create_network_policies
    ]

    grant_selects = [s for s in execution_plan if "grant select on" in s]
    grant_create = [s for s in execution_plan if "grant create table" in s]
    grant_roles = [s for s in execution_plan if "grant role" in s and "to role" in s]
    grant_users = [s for s in execution_plan if "grant role" in s and "to user" in s]

    revoke_roles = [
        s for s in execution_plan if "revoke role" in s and "from role" in s
    ]
    revoke_users = [
        s for s in execution_plan if "revoke role" in s and "from user" in s
    ]
    return {
        "create_databases": create_databases,
        "modify_databases": modify_databases,
        "create_schemas": create_schemas,
        "modify_schemas": modify_schemas,
        "create_roles": create_roles,
        "modify_roles": modify_roles,
        "create_users": create_users,
        "modify_users": modify_users,
        "create_warehouses": create_warehouses,
        "modify_warehouses": modify_warehouses,
        "create_network_policies": create_network_policies,
        "modify_network_policies": modify_network_policies,
        "grant_selects": grant_selects,
        "grant_create": grant_create,
        "grant_roles": grant_roles,
        "grant_users": grant_users,
        "revoke_roles": revoke_roles,
        "revoke_users": revoke_users,
    }

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

transfer_ownership = """
    grant ownership on {{ resource_type }} {{ name }} to role {{ role }} copy current grants
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
grant_role_read_on_dynamic_tables_in_schema = """
    grant select on all dynamic tables in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_future_read_on_dynamic_tables_in_schema = """
    grant select on future dynamic tables in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_read_on_semantic_views_in_schema = """
    grant select on all semantic views in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_future_read_on_semantic_views_in_schema = """
    grant select on future semantic views in schema {{ database }}.{{ schema }} to role {{ role }}
"""
grant_role_select_on_object = """
    grant select on {{ object_type }} {{ database }}.{{ schema }}.{{ object_name }} to role {{ role }}
"""
revoke_privilege = """
    revoke {{ privilege_clause }} from {{ grantee_type }} "{{ grantee_name.upper() }}"
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

SNOWFLAKE_OBJECT_TYPES = {
    "table": "table",
    "view": "view",
    "dynamic_table": "dynamic table",
    "semantic_view": "semantic view",
}

jinja_env = jinja2.Environment()


class UnmodifiableStateError(Exception):
    pass


class UnmanagedReferenceError(Exception):
    pass


def load_config(path: str) -> dict:
    with open(path) as file:
        file_content = file.read().lower()
        return yaml.safe_load(file_content)


def _parse_object_type(type_input: str) -> tuple[str, str]:
    if type_input.count(":") != 1:
        raise ValueError(
            f"Invalid type_input, must contain exactly one colon between object type and name"
        )
    prefix, name = type_input.split(":")
    if prefix in SNOWFLAKE_OBJECT_TYPES.keys():
        object_type, object_name = prefix, name
        return SNOWFLAKE_OBJECT_TYPES[object_type], object_name
    else:
        valid_types = ", ".join(SNOWFLAKE_OBJECT_TYPES.keys())
        raise ValueError(
            f"Invalid input for object type, type must be one of {valid_types}, followed by a colon and a fully qualified object name (for example: table:my_database.my_schema.my_table)"
        )


def _validate_grant_references(
    grants: list[dict],
    managed_warehouses: set[str],
    managed_databases: set[str],
    managed_schemas: set[str],
    managed_roles: set[str],
):
    for grant in grants:
        role = grant["role"].lower()
        if role not in managed_roles:
            raise UnmanagedReferenceError(
                f"Grant references role '{grant['role']}' which is not declared in the 'roles' section"
            )
        for wh in grant.get("warehouses", []):
            if wh.lower() not in managed_warehouses:
                raise UnmanagedReferenceError(
                    f"Grant references warehouse '{wh}' which is not declared in the 'warehouses' section"
                )
        for schema_path in grant.get("read_on_schemas", []) + grant.get(
            "write_on_schemas", []
        ):
            if schema_path.lower() not in managed_schemas:
                raise UnmanagedReferenceError(
                    f"Grant references schema '{schema_path}' which is not declared in the 'databases' section"
                )
        for obj in grant.get("read_on_objects", []):
            if ":" not in obj:
                continue
            _, obj_path = obj.split(":", 1)
            parts = obj_path.split(".")
            if len(parts) >= 2:
                schema_key = f"{parts[0]}.{parts[1]}".lower()
                if schema_key not in managed_schemas:
                    raise UnmanagedReferenceError(
                        f"Grant references object in schema '{schema_key}' which is not declared in the 'databases' section"
                    )


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

        if db_state.get("owner") and db_state["owner"] != "sysadmin":
            execution_plan.append(
                jinja_env.from_string(transfer_ownership).render(
                    resource_type="database", name=db_name, role="sysadmin"
                )
            )

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

            if schema_state.get("owner") and schema_state["owner"] != "sysadmin":
                execution_plan.append(
                    jinja_env.from_string(transfer_ownership).render(
                        resource_type="schema",
                        name=full_schema_name,
                        role="sysadmin",
                    )
                )
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

        if warehouse_state.get("owner") and warehouse_state["owner"] != "sysadmin":
            execution_plan.append(
                jinja_env.from_string(transfer_ownership).render(
                    resource_type="warehouse",
                    name=warehouse_name,
                    role="sysadmin",
                )
            )
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
        elif role_state.get("owner") and role_state["owner"] != "useradmin":
            execution_plan.append(
                jinja_env.from_string(transfer_ownership).render(
                    resource_type="role", name=role_name, role="useradmin"
                )
            )
    return execution_plan


def _actual_grants(grant_state: list[dict]) -> set[tuple[str, str, str]]:
    """Build set of (privilege, grantee_type, grantee_name) from state, excluding OWNERSHIP."""
    return {
        (
            g["privilege"].lower(),
            g.get("granted_to", "ROLE").lower(),
            g["grantee_name"].lower(),
        )
        for g in grant_state
        if g["privilege"].lower() != "ownership"
        and g.get("granted_to", "ROLE").lower() in ("role", "user")
    }


def _grant_role_execution_plan(
    grants: list[dict],
    state: dict,
    managed_warehouses: set[str],
    managed_databases: set[str],
    managed_schemas: set[str],
) -> list[str]:
    if (
        len(grants) == 0
        and not managed_warehouses
        and not managed_databases
        and not managed_schemas
    ):
        return []
    execution_plan = set()

    # === Phase 1: Aggregate desired grants across all config entries ===

    desired_warehouse_roles: dict[str, set[str]] = {}
    desired_database_roles: dict[str, set[str]] = {}
    desired_schema_roles: dict[str, set[str]] = {}
    desired_future_read: dict[str, set[str]] = {}
    desired_create: dict[str, set[str]] = {}
    # {config_key: {"roles": set, "sf_type": str, "db": str, "schema": str, "name": str}}
    desired_object_read: dict[str, dict] = {}

    for grant in grants:
        role = grant["role"]

        for warehouse in grant.get("warehouses", []):
            desired_warehouse_roles.setdefault(warehouse, set()).add(role)

        for schema_path in grant.get("read_on_schemas", []):
            database = schema_path.split(".")[0]
            desired_database_roles.setdefault(database, set()).add(role)
            desired_schema_roles.setdefault(schema_path, set()).add(role)
            desired_future_read.setdefault(schema_path, set()).add(role)

        for schema_path in grant.get("write_on_schemas", []):
            database = schema_path.split(".")[0]
            desired_database_roles.setdefault(database, set()).add(role)
            desired_schema_roles.setdefault(schema_path, set()).add(role)
            desired_create.setdefault(schema_path, set()).add(role)

        for object_entry in grant.get("read_on_objects", []):
            object_type, object_name = _parse_object_type(object_entry)
            parts = object_name.split(".")
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid object path {object_name}, must be in the format database.schema.object"
                )
            database, schema, name = parts
            config_key = object_entry
            desired_database_roles.setdefault(database, set()).add(role)
            desired_schema_roles.setdefault(f"{database}.{schema}", set()).add(role)
            if config_key not in desired_object_read:
                desired_object_read[config_key] = {
                    "roles": set(),
                    "sf_type": object_type,
                    "db": database,
                    "schema": schema,
                    "name": name,
                }
            desired_object_read[config_key]["roles"].add(role)

    # === Phase 2: Stateful diffing ===

    # --- Warehouse USAGE ---
    on_warehouses_state = state.get("on_warehouses", {})
    all_warehouses_to_diff = managed_warehouses | set(desired_warehouse_roles.keys())
    for warehouse in all_warehouses_to_diff:
        desired_roles = desired_warehouse_roles.get(warehouse, set())
        warehouse_grant_state = on_warehouses_state.get(warehouse)
        desired = {("usage", "role", r) for r in desired_roles}
        if warehouse_grant_state is None:
            for priv, gtype, name in desired:
                execution_plan.add(
                    jinja_env.from_string(grant_role_usage_on_warehouse).render(
                        role=name, warehouse=warehouse
                    )
                )
        else:
            actual = _actual_grants(warehouse_grant_state)
            for priv, gtype, name in desired - actual:
                execution_plan.add(
                    jinja_env.from_string(grant_role_usage_on_warehouse).render(
                        role=name, warehouse=warehouse
                    )
                )
            for priv, gtype, name in actual - desired:
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on warehouse {warehouse}",
                        grantee_type=gtype,
                        grantee_name=name,
                    )
                )

    # --- Database USAGE ---
    on_databases_state = state.get("on_databases", {})
    all_databases_to_diff = managed_databases | set(desired_database_roles.keys())
    for database in all_databases_to_diff:
        desired_roles = desired_database_roles.get(database, set())
        db_grant_state = on_databases_state.get(database)
        desired = {("usage", "role", r) for r in desired_roles}
        if db_grant_state is None:
            for priv, gtype, name in desired:
                execution_plan.add(
                    jinja_env.from_string(grant_role_usage_on_database).render(
                        role=name, database=database
                    )
                )
        else:
            actual = _actual_grants(db_grant_state)
            for priv, gtype, name in desired - actual:
                execution_plan.add(
                    jinja_env.from_string(grant_role_usage_on_database).render(
                        role=name, database=database
                    )
                )
            for priv, gtype, name in actual - desired:
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on database {database}",
                        grantee_type=gtype,
                        grantee_name=name,
                    )
                )

    # --- Schema grants (USAGE + CREATE) ---
    on_schemas_state = state.get("on_schemas", {})
    create_types = [
        "table",
        "view",
        "dynamic table",
        "semantic view",
        "task",
        "alert",
        "masking policy",
        "row access policy",
        "procedure",
    ]
    all_managed_schemas = (
        set(desired_schema_roles.keys()) | set(desired_create.keys()) | managed_schemas
    )
    for schema_path in all_managed_schemas:
        database, schema = schema_path.split(".")
        schema_grant_state = on_schemas_state.get(schema_path)

        desired = set()
        for role in desired_schema_roles.get(schema_path, set()):
            desired.add(("usage", "role", role))
        for role in desired_create.get(schema_path, set()):
            for ct in create_types:
                desired.add((f"create {ct}", "role", role))

        if schema_grant_state is None:
            for priv, gtype, name in desired:
                if priv == "usage":
                    execution_plan.add(
                        jinja_env.from_string(grant_role_usage_on_schema).render(
                            role=name, database=database, schema=schema
                        )
                    )
                elif priv.startswith("create "):
                    execution_plan.add(
                        jinja_env.from_string(grant_role_create_on_schema).render(
                            type=priv[7:],
                            role=name,
                            database=database,
                            schema=schema,
                        )
                    )
        else:
            actual = _actual_grants(schema_grant_state)
            for priv, gtype, name in desired - actual:
                if priv == "usage":
                    execution_plan.add(
                        jinja_env.from_string(grant_role_usage_on_schema).render(
                            role=name, database=database, schema=schema
                        )
                    )
                elif priv.startswith("create "):
                    execution_plan.add(
                        jinja_env.from_string(grant_role_create_on_schema).render(
                            type=priv[7:],
                            role=name,
                            database=database,
                            schema=schema,
                        )
                    )
            for priv, gtype, name in actual - desired:
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on schema {schema_path}",
                        grantee_type=gtype,
                        grantee_name=name,
                    )
                )

    # --- Future read grants ---
    future_in_schemas_state = state.get("future_in_schemas", {})
    future_grant_map = {
        "table": (grant_role_future_read_on_tables_in_schema, "tables"),
        "view": (grant_role_future_read_on_views_in_schema, "views"),
        "dynamic table": (
            grant_role_future_read_on_dynamic_tables_in_schema,
            "dynamic tables",
        ),
        "semantic view": (
            grant_role_future_read_on_semantic_views_in_schema,
            "semantic views",
        ),
    }
    # Track (schema_path, role) pairs that need new future grants — these also
    # need ALL grants to bootstrap existing objects in that schema.
    schemas_needing_bootstrap: set[tuple[str, str]] = set()
    # Check all managed schemas that either have desired future reads or
    # existing future grant state — ensures stale future grants are revoked
    # even when a schema is only referenced via write_on_schemas or read_on_objects.
    managed_future_schemas = set(desired_future_read.keys()) | (
        set(future_in_schemas_state.keys()) & all_managed_schemas
    )
    for schema_path in managed_future_schemas:
        desired_roles = desired_future_read.get(schema_path, set())
        database, schema = schema_path.split(".")
        future_schema_state = future_in_schemas_state.get(schema_path)

        desired = {
            ("select", grant_on_type, role)
            for grant_on_type in future_grant_map
            for role in desired_roles
        }

        if future_schema_state is None:
            for priv, grant_on_type, role in desired:
                schemas_needing_bootstrap.add((schema_path, role))
                grant_tmpl = future_grant_map[grant_on_type][0]
                execution_plan.add(
                    jinja_env.from_string(grant_tmpl).render(
                        role=role, database=database, schema=schema
                    )
                )
        else:
            actual = {
                (
                    g["privilege"].lower(),
                    g["grant_on"].lower().replace("_", " "),
                    g["grantee_name"].lower(),
                )
                for g in future_schema_state
                if g["privilege"].lower() != "ownership"
            }
            for priv, grant_on_type, role in desired - actual:
                schemas_needing_bootstrap.add((schema_path, role))
                grant_tmpl = future_grant_map[grant_on_type][0]
                execution_plan.add(
                    jinja_env.from_string(grant_tmpl).render(
                        role=role, database=database, schema=schema
                    )
                )
            for priv, grant_on_type, grantee in actual - desired:
                type_plural = future_grant_map.get(
                    grant_on_type, (None, f"{grant_on_type}s")
                )[1]
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on future {type_plural} in schema {database}.{schema}",
                        grantee_type="role",
                        grantee_name=grantee,
                    )
                )
                # Also revoke on existing objects to clean up
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on all {type_plural} in schema {database}.{schema}",
                        grantee_type="role",
                        grantee_name=grantee,
                    )
                )

    # --- Object SELECT grants (read_on_objects) ---
    on_objects_state = state.get("on_objects", {})
    for config_key, info in desired_object_read.items():
        obj_state = on_objects_state.get(config_key)
        explicitly_desired = info["roles"]
        # Include roles from read_on_schemas for the containing schema
        # to avoid revoking schema-level access
        containing_schema = f"{info['db']}.{info['schema']}"
        expanded_desired = explicitly_desired | desired_future_read.get(
            containing_schema, set()
        )
        obj_fqn = f"{info['sf_type']} {info['db']}.{info['schema']}.{info['name']}"

        desired_to_grant = {("select", "role", r) for r in explicitly_desired}
        desired_to_keep = {("select", "role", r) for r in expanded_desired}

        if obj_state is None:
            for priv, gtype, name in desired_to_grant:
                execution_plan.add(
                    jinja_env.from_string(grant_role_select_on_object).render(
                        role=name,
                        object_type=info["sf_type"],
                        database=info["db"],
                        schema=info["schema"],
                        object_name=info["name"],
                    )
                )
        else:
            actual = _actual_grants(obj_state)
            for priv, gtype, name in desired_to_grant - actual:
                execution_plan.add(
                    jinja_env.from_string(grant_role_select_on_object).render(
                        role=name,
                        object_type=info["sf_type"],
                        database=info["db"],
                        schema=info["schema"],
                        object_name=info["name"],
                    )
                )
            for priv, gtype, name in actual - desired_to_keep:
                execution_plan.add(
                    jinja_env.from_string(revoke_privilege).render(
                        privilege_clause=f"{priv} on {obj_fqn}",
                        grantee_type=gtype,
                        grantee_name=name,
                    )
                )

    # === Phase 3: Per-grant loop (ALL grants + to_roles/to_users) ===
    for grant in grants:
        role = grant["role"]
        read_on_schemas = grant.get("read_on_schemas", [])
        to_roles = grant.get("to_roles", [])
        to_users = grant.get("to_users", [])

        # Emit ALL grants only when bootstrapping (future grants are being newly added)
        for full_schema_path in read_on_schemas:
            if (full_schema_path, role) not in schemas_needing_bootstrap:
                continue
            database, schema = full_schema_path.split(".")
            execution_plan.add(
                jinja_env.from_string(grant_role_read_on_tables_in_schema).render(
                    role=role, database=database, schema=schema
                )
            )
            execution_plan.add(
                jinja_env.from_string(grant_role_read_on_views_in_schema).render(
                    role=role, database=database, schema=schema
                )
            )
            execution_plan.add(
                jinja_env.from_string(
                    grant_role_read_on_dynamic_tables_in_schema
                ).render(role=role, database=database, schema=schema)
            )
            execution_plan.add(
                jinja_env.from_string(
                    grant_role_read_on_semantic_views_in_schema
                ).render(role=role, database=database, schema=schema)
            )

        # Grant and revoke roles to users and roles
        grant_of_role_state = state.get("of_roles", {}).get(role)
        if grant_of_role_state is None:
            for to_role in to_roles:
                grant_role_to_role_statement = jinja_env.from_string(
                    grant_role_to_role
                ).render(role=role, to_role=to_role)
                execution_plan.add(grant_role_to_role_statement)

            for to_user in to_users:
                grant_role_to_user_statement = jinja_env.from_string(
                    grant_role_to_user
                ).render(role=role, to_user=to_user)
                execution_plan.add(grant_role_to_user_statement)
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
            execution_plan.add(grant_role_to_user_statement)
        # revoke user
        for to_user in to_users_exists_in_database:
            if to_user in to_users:
                continue
            revoke_grant_role_from_user_statement = jinja_env.from_string(
                revoke_grant_role_from_user
            ).render(role=role, to_user=to_user.upper())
            execution_plan.add(revoke_grant_role_from_user_statement)
        # grant role
        for to_role in to_roles:
            if to_role in to_roles_exists_in_database:
                continue
            grant_role_to_role_statement = jinja_env.from_string(
                grant_role_to_role
            ).render(role=role, to_role=to_role)
            execution_plan.add(grant_role_to_role_statement)
        # revoke role
        for to_role in to_roles_exists_in_database:
            if to_role in to_roles:
                continue
            revoke_grant_role_to_role_statement = jinja_env.from_string(
                revoke_grant_role_from_role
            ).render(role=role, to_role=to_role)
            execution_plan.add(revoke_grant_role_to_role_statement)

    return list(execution_plan)


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
            "owner": database.get("owner", "").lower(),
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
                        "owner": schema_state.get("owner", "").lower(),
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
                    "owner": warehouse_state.get("owner", "").lower(),
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
                existing_state[role_name] = {
                    "owner": role_state.get("owner", "").lower(),
                }
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

    managed_warehouse_names = {wh["name"].lower() for wh in warehouses}
    managed_database_names = {db["name"].lower() for db in databases}
    managed_schema_names: set[str] = set()
    for db in databases:
        for schema in db.get("schemas", []):
            managed_schema_names.add(f"{db['name'].lower()}.{schema['name'].lower()}")
    managed_role_names = {r["name"].lower() for r in roles}

    _validate_grant_references(
        grants,
        managed_warehouse_names,
        managed_database_names,
        managed_schema_names,
        managed_role_names,
    )

    # Add synthetic grant entries for managed roles without explicit grants
    grant_role_names = {g["role"].lower() for g in grants}
    for role in roles:
        if role["name"].lower() not in grant_role_names:
            grants.append({"role": role["name"]})

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

    plan.extend(
        _grant_role_execution_plan(
            grants=grants,
            state=grants_state,
            managed_warehouses=managed_warehouse_names,
            managed_databases=managed_database_names,
            managed_schemas=managed_schema_names,
        )
    )
    if len(plan) > plan_len:
        plan.insert(plan_len, use_useradmin)

    plan = _trim_sql_statements(plan)
    return plan


def overview(execution_plan: dict) -> dict:
    create_databases = [
        s.split()[5] for s in execution_plan if s.startswith("create database")
    ]
    create_transient_databases = [
        s.split()[6]
        for s in execution_plan
        if s.startswith("create transient database")
    ]
    create_databases.extend(create_transient_databases)
    alter_databases = [
        s.split()[2] for s in execution_plan if s.startswith("alter database")
    ]
    modify_databases = [d for d in alter_databases if d not in create_databases]

    create_schemas = [
        s.split()[5] for s in execution_plan if s.startswith("create schema")
    ]
    create_transient_schemas = [
        s.split()[6] for s in execution_plan if s.startswith("create transient schema")
    ]
    create_schemas.extend(create_transient_schemas)
    alter_schemas = [s for s in execution_plan if s.startswith("alter schema")]
    modify_schemas = [
        s.split()[2] for s in alter_schemas if s.split()[2] not in create_schemas
    ]

    create_roles = [s.split()[5] for s in execution_plan if s.startswith("create role")]
    alter_roles = [s.split()[2] for s in execution_plan if s.startswith("alter role")]
    modify_roles = [r for r in alter_roles if r not in create_roles]

    create_users = [s.split()[5] for s in execution_plan if s.startswith("create user")]
    alter_users = [s.split()[2] for s in execution_plan if s.startswith("alter user")]
    modify_users = [u for u in alter_users if u not in create_users]

    create_warehouses = [
        s.split()[5] for s in execution_plan if s.startswith("create warehouse")
    ]
    alter_warehouses = [
        s.split()[2] for s in execution_plan if s.startswith("alter warehouse")
    ]
    modify_warehouses = [w for w in alter_warehouses if w not in create_warehouses]

    create_network_policies = [
        s.split()[6] for s in execution_plan if s.startswith("create network policy")
    ]
    alter_network_policies = [
        s.split()[3] for s in execution_plan if s.startswith("alter network policy")
    ]
    modify_network_policies = [
        s for s in alter_network_policies if s not in create_network_policies
    ]

    grant_selects = [
        s for s in execution_plan if "grant select on" in s and "in schema" in s
    ]
    grant_select_on_objects = [
        s for s in execution_plan if "grant select on" in s and "in schema" not in s
    ]
    grant_create = [s for s in execution_plan if "grant create" in s]
    grant_roles = [s for s in execution_plan if "grant role" in s and "to role" in s]
    grant_users = [s for s in execution_plan if "grant role" in s and "to user" in s]
    grant_warehouses = [s for s in execution_plan if "grant usage on warehouse" in s]
    grant_databases = [s for s in execution_plan if "grant usage on database" in s]
    grant_schemas = [s for s in execution_plan if "grant usage on schema" in s]
    revoke_warehouses = [s for s in execution_plan if "revoke usage on warehouse" in s]
    revoke_databases = [s for s in execution_plan if "revoke usage on database" in s]
    revoke_schemas = [s for s in execution_plan if "revoke usage on schema" in s]
    revoke_selects = [
        s for s in execution_plan if "revoke select on" in s and "in schema" in s
    ]
    revoke_select_on_objects = [
        s for s in execution_plan if "revoke select on" in s and "in schema" not in s
    ]
    revoke_create = [s for s in execution_plan if "revoke create" in s]

    revoke_roles = [
        s for s in execution_plan if "revoke role" in s and "from role" in s
    ]
    revoke_users = [
        s for s in execution_plan if "revoke role" in s and "from user" in s
    ]
    categorized_revokes = set(
        revoke_warehouses
        + revoke_databases
        + revoke_schemas
        + revoke_selects
        + revoke_select_on_objects
        + revoke_create
        + revoke_roles
        + revoke_users
    )
    revoke_other = [
        s for s in execution_plan if "revoke " in s and s not in categorized_revokes
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
        "grant_select_on_objects": grant_select_on_objects,
        "grant_create": grant_create,
        "grant_roles": grant_roles,
        "grant_users": grant_users,
        "grant_warehouses": grant_warehouses,
        "grant_databases": grant_databases,
        "grant_schemas": grant_schemas,
        "revoke_warehouses": revoke_warehouses,
        "revoke_databases": revoke_databases,
        "revoke_schemas": revoke_schemas,
        "revoke_selects": revoke_selects,
        "revoke_select_on_objects": revoke_select_on_objects,
        "revoke_create": revoke_create,
        "revoke_roles": revoke_roles,
        "revoke_users": revoke_users,
        "revoke_other": revoke_other,
    }

import logging
import secrets
from pathlib import Path
from typing import List

from permifrost.snowflake_connector import SnowflakeConnector

from snowbird.loader import get_spec_file_paths, load_snowbird_spec
from snowbird.models import (
    Database,
    Databases,
    Roles,
    SnowbirdModel,
    SnowbirdRole,
    SnowbirdRoles,
    SnowbirdShare,
    SnowbirdShares,
    Users,
    Warehouse,
    Warehouses,
)
from snowbird.utils import execute_statement, load_specs, print_command

LOGGER = logging.getLogger()


def create_databases(conn: SnowflakeConnector, spec: List[Databases]) -> None:
    print("create databases")
    execute_statement(conn, "USE ROLE SYSADMIN")
    for item in spec:
        for database in item.keys():
            statement = f"CREATE DATABASE IF NOT EXISTS {database}"
            execute_statement(conn, statement)

            db: Database = item[database]
            if db.schemas:
                for schema in db.schemas:
                    statement = f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}"
                    execute_statement(conn, statement)


def create_warehouses(conn: SnowflakeConnector, spec: List[Warehouses]) -> None:
    print("create warehouses")
    execute_statement(conn, "USE ROLE SYSADMIN")
    for item in spec:
        for name in item.keys():
            wh: Warehouse = item[name]
            statement = f"""
                    CREATE WAREHOUSE IF NOT EXISTS {name}
                        WITH WAREHOUSE_SIZE='{wh.size}'
                        INITIALLY_SUSPENDED={wh.initially_suspended}
                        AUTO_SUSPEND={wh.auto_suspend}
                    """
            execute_statement(conn, statement)


def create_roles(conn: SnowflakeConnector, spec: List[Roles]) -> None:
    print("create roles")
    execute_statement(conn, "USE ROLE USERADMIN")
    for item in spec:
        for role in item.keys():
            statement = f"CREATE ROLE IF NOT EXISTS {role}"
            execute_statement(conn, statement)
            statement = f"GRANT ROLE {role} TO ROLE SYSADMIN"
            execute_statement(conn, statement)


def create_users(conn: SnowflakeConnector, spec: List[Users]) -> None:
    print("create users")
    execute_statement(conn, "USE ROLE USERADMIN")
    for item in spec:
        for user in item.keys():
            password_length = 13
            # TODO: add user / password to Google Secret Manager secrets
            password = secrets.token_urlsafe(password_length)
            default_role = "PUBLIC"
            statement = f"CREATE USER IF NOT EXISTS {user} PASSWORD='{password}' DEFAULT_ROLE='{default_role}'"
            # avoid logging password
            try:
                conn.engine.execute(statement)
                status = True
            except:
                status = False
            finally:
                command = {
                    "run_status": status,
                    "sql": f"CREATE USER IF NOT EXISTS {user}",
                }
                print_command(command)


def _validate_shares_spec(spec: List[SnowbirdShares]) -> bool:
    for item in spec:
        for share in item.keys():
            props: SnowbirdShare = item[share]
            if props.privileges.tables != None:
                raise NotImplementedError("Sharing tables is not implemented.")
            for key, values in props.privileges.databases:
                if key == "write" and values is not None:
                    raise ValueError("A share cannot write to an database.")
            for key, values in props.privileges.schemas:
                if key == "write" and values is not None:
                    raise ValueError("A share cannot write to a schema.")
    return True


def _create_shares_execution_plan(spec: List[SnowbirdShares]) -> List[str]:
    execution_plan = []
    for item in spec:
        for share in item.keys():
            props: SnowbirdShare = item[share]
            execution_plan.append("USE ROLE ACCOUNTADMIN")
            execution_plan.append(
                f"GRANT CREATE SHARE ON ACCOUNT TO ROLE {props.owner}"
            )
            execution_plan.append(f"USE ROLE {props.owner}")
            execution_plan.append(f"CREATE SHARE IF NOT EXISTS {share}")
            execution_plan.append(
                f"REVOKE CREATE SHARE ON ACCOUNT FROM ROLE {props.owner}"
            )
            execution_plan.append(f"USE ROLE SYSADMIN")
            for key, values in props.privileges.databases:
                if key == "read":
                    for db in values:
                        execution_plan.append(
                            f"GRANT USAGE ON DATABASE {db} TO SHARE {share}"
                        )
            for key, values in props.privileges.schemas:
                if key == "read":
                    for schema in values:
                        execution_plan.append(
                            f"GRANT USAGE ON SCHEMA {schema} TO SHARE {share}"
                        )
            consumers = str.join(",", props.consumers)
            execution_plan.append(f"USE ROLE {props.owner}")
            execution_plan.append(f"ALTER SHARE {share} SET ACCOUNTS = {consumers}")
            return execution_plan


def create_shares(conn: SnowflakeConnector, spec: List[SnowbirdShares]) -> None:
    print("create shares")
    # execute_statement(conn, "USE ROLE USERADMIN")
    if _validate_shares_spec(spec=spec) != True:
        raise Exception("Something went wrong validating Shares specification.")
    execution_plan = _create_shares_execution_plan(spec=spec)
    for statement in execution_plan:
        execute_statement(conn, statement)


def _grant_extra_writes_to_roles_execution_plan(spec: List[Roles]) -> List[str]:
    execution_plan = []
    execution_plan.append("use role securityadmin")
    for item in spec:
        for role in item.keys():
            props: SnowbirdRole = item[role]
            print(props)
            if props.privileges.schemas.write:
                for schema in props.privileges.schemas.write:
                    print(f"write schemas: {schema}")
                    execution_plan.extend(
                        [
                            f"grant create dynamic table on schema {schema} to role {role}",
                            f"grant create masking policy on schema {schema} to role {role}",
                            f"grant create row access policy on schema {schema} to role {role}",
                        ]
                    )
    return execution_plan


def grant_extra_writes_to_roles(conn: SnowflakeConnector, spec: List[Roles]) -> None:
    print("grant extra writes to roles")
    execution_plan = _grant_extra_writes_to_roles_execution_plan(spec)
    for statement in execution_plan:
        execute_statement(conn=conn, statement=statement)


# resource creation not part of permifrost. We therefore generate our own resource creation queries
def create_snowflake_resources(
    conn: SnowflakeConnector, path: str = None, file: str = None
) -> SnowbirdModel:
    model = None

    try:
        file_name = file if file else "snowflake.yml"
        model = load_snowbird_spec(file_name, root_dir=Path(path))
    except Exception as e:
        LOGGER.error(f"Error parsing file {path}/{file}: {e}")

    try:
        if model.databases is not None:
            create_databases(conn, model.databases)
    except Exception as e:
        raise Exception(f"Error creating databases: {str(e)}")

    try:
        if model.warehouses is not None:
            create_warehouses(conn, model.warehouses)
    except Exception as e:
        raise Exception(f"Error creating warehouses: {str(e)}")

    try:
        if model.roles is not None:
            create_roles(conn, model.roles)
            grant_extra_writes_to_roles(conn=conn, spec=model.roles)
    except Exception as e:
        raise Exception(f"Error creating roles: {str(e)}")

    try:
        if model.users is not None:
            create_users(conn, model.users)
    except Exception as e:
        raise Exception(f"Error creating users: {str(e)}")

    try:
        if model.shares is not None:
            create_shares(conn, model.shares)
    except Exception as e:
        raise Exception(f"Error creating shares: {str(e)}")

    return model


# adapted from permifrost cli
def run_permifrost(
    conn: SnowflakeConnector, spec_file: str = None, root_dir: str = None
):
    LOGGER.info(f"Run permifrost with spec file {spec_file}")

    if not Path(spec_file).is_file:
        spec_file = get_spec_file_paths(spec_file, root_dir)

    try:
        execute_statement(conn, "USE ROLE SECURITYADMIN")
    except Exception as e:
        LOGGER.error(f"Could not set role SECURITYADMIN. {e}")
        return

    try:
        spec_loader = load_specs(spec_file, conn)

        # TODO: submit pull request to allow reuse of SnowflakeConnection and configuration?
        sql_grant_queries = spec_loader.generate_permission_queries()
        for query in sql_grant_queries:
            status = None
            if not query.get("already_granted"):
                try:
                    conn.run_query(query.get("sql", ""))
                    status = True
                except Exception:
                    status = False

                ran_query = query
                ran_query["run_status"] = status
                print_command(ran_query)
            else:
                print_command(query)

    except Exception as e:
        LOGGER.info(f"Error running permifrost with spec file {spec_file}. {e}")

import logging
import secrets
from typing import List

from permifrost import SpecLoadingError
from permifrost.snowflake_connector import SnowflakeConnector
from permifrost.snowflake_spec_loader import SnowflakeSpecLoader

from snowbird.loader import get_snowbird_model, get_spec_file_paths
from snowbird.models import (
    Database,
    Databases,
    Roles,
    SnowbirdModel,
    Users,
    Warehouse,
    Warehouses,
)

LOGGER = logging.getLogger()

# adapted from permifrost cli
def print_command(command):
    if command.get("run_status"):
        run_prefix = "[SUCCESS] "
    elif command.get("run_status") is None:
        run_prefix = "[SKIPPED] "
    else:
        run_prefix = "[ERROR] "

    print(f"{run_prefix}{command['sql']};")


def load_specs(spec, conn: SnowflakeConnector = None):
    try:
        spec_loader = SnowflakeSpecLoader(spec_path=spec, conn=conn)
        return spec_loader
    except SpecLoadingError as exc:
        for line in str(exc).splitlines():
            print(line)


def execute_statement(
    conn: SnowflakeConnector, statement: str, alias: str = None
) -> None:
    result = None
    try:
        LOGGER.info(statement)
        result = conn.run_query(statement)
        status = True
    except Exception as e:
        status = False
        LOGGER.error(f"Error executing {statement}. {e}")
    finally:
        command = {"run_status": status, "sql": alias or statement}
        print_command(command)
        return result


def create_databases(conn: SnowflakeConnector, spec: List[Databases]) -> None:
    print("create databases")
    execute_statement(conn, "USE ROLE SYSADMIN")
    for item in spec:
        for database in item.keys():
            statement = f"CREATE DATABASE IF NOT EXISTS {database}"
            execute_statement(conn, statement)

            db: Database = item[database]
            for schema in db.schemas:
                statement = f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}"


def create_warehouses(conn: SnowflakeConnector, spec: List[Warehouses]) -> None:
    print("create warehouses")
    execute_statement(conn, "USE ROLE SYSADMIN")
    for item in spec:
        for name in item.keys():
            wh: Warehouse = item[name]
            # TODO: consider allowing these permifrost attributes??
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


# resource creation not part of permifrost. We therefore generate our own resource creation queries
def create_resources() -> SnowbirdModel:
    print("create resources")

    try:
        conn = SnowflakeConnector()
    except Exception as e:
        print(f"Error creating Snowflake connection: {str(e)}")
        return

    print("creating resources defined in snowflake.yml")
    try:
        model = get_snowbird_model("snowflake.yml")

        if model.databases is not None:
            create_databases(conn, model.databases)

        if model.warehouses is not None:
            create_warehouses(conn, model.warehouses)

        if model.roles is not None:
            create_roles(conn, model.roles)

        if model.users is not None:
            create_users(conn, model.users)

        return model

    except Exception as e:
        print(f"Error creating resources: {str(e)}")


# adapted from permifrost cli
def run_permifrost(spec_file: str = "snowflake.yml"):

    try:
        conn = SnowflakeConnector()
    except Exception as e:
        print(e)
        return

    for spec_file in get_spec_file_paths(spec_file):

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
            print(e)

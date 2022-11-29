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
            for schema in db.schemas:
                statement = f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}"


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
def create_snowflake_resources(
    conn: SnowflakeConnector, path: str = None, file: str = None
) -> SnowbirdModel:

    model = None

    try:
        file_name = file if file else "snowflake.yml"
        model = load_snowbird_spec(file_name, root_dir=Path(path))
    except Exception as e:
        print(f"Error parsing file {path}/{file}: {str(e)}")

    try:
        if model.databases is not None:
            create_databases(conn, model.databases)

        if model.warehouses is not None:
            create_warehouses(conn, model.warehouses)

        if model.roles is not None:
            create_roles(conn, model.roles)

        if model.users is not None:
            create_users(conn, model.users)

    except Exception as e:
        print(f"Error creating resources: {str(e)}")

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

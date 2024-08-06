import logging

from permifrost.snowflake_connector import SnowflakeConnector

LOGGER = logging.getLogger(__file__)


def create_db_clone(src: str, dst: str, usage: tuple[str]):
    prod_db = src
    clone_db = dst

    use_role = "use role sysadmin"
    create_sql = f"create or replace database {clone_db} clone {prod_db}"
    show_dynamic_tables = f"show dynamic tables in database {clone_db}"

    try:
        conn = SnowflakeConnector()
    except Exception as e:
        LOGGER.error(f"Error creating Snowflake connection. {e}")
        return

    conn.run_query(use_role)
    conn.run_query(create_sql)
    dynamic_tables = conn.run_query(show_dynamic_tables)
    for suspend_dynamic_table in _suspend_dynamic_tables(
        db=clone_db, dynamic_tables=dynamic_tables
    ):
        conn.run_query(suspend_dynamic_table)
    for grant_usage_to_role in _grant_usage(db=clone_db, roles=usage):
        conn.run_query(grant_usage_to_role)


def _suspend_dynamic_tables(db, dynamic_tables: list[dict]) -> list[str]:
    sql = []
    for dynamic_table in dynamic_tables:
        if dynamic_table["scheduling_state"] != "SUSPENDED":
            schema = dynamic_table["schema_name"]
            table = dynamic_table["name"]
            sql.append(f"alter dynamic table {db}.{schema}.{table} suspend")
    return sql


def _grant_usage(db, roles: list[str]):
    return [f"grant usage on database {db} to role {role}" for role in roles]

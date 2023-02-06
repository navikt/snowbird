import logging

from permifrost import SpecLoadingError
from permifrost.snowflake_connector import SnowflakeConnector
from permifrost.snowflake_spec_loader import SnowflakeSpecLoader

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
    print(spec)
    try:
        spec_loader = SnowflakeSpecLoader(spec_path=spec, conn=conn)
        return spec_loader
    except SpecLoadingError as exc:
        for line in str(exc).splitlines():
            LOGGER.error(f"Error loading spec. {line}")


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

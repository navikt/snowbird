import logging
import tempfile

from permifrost.snowflake_connector import SnowflakeConnector

LOGGER = logging.getLogger(__file__)

from snowbird.loader import write_snowbird_model_to_permifrost_file
from snowbird.resources import create_snowflake_resources, run_permifrost


def run(path: str = None, file: str = None):

    try:
        conn = SnowflakeConnector()
    except Exception as e:
        LOGGER.error(f"Error creating Snowflake connection. {e}")
        return

    # create snowflake resources based on snowbird formatted spec file: snowflake.yml
    model = create_snowflake_resources(conn, path, file)

    # dump snowbird spec to file in permifrost compatible schema
    # and run permifrost to update permissions in snowflake
    with tempfile.NamedTemporaryFile(mode="w+") as tf:

        write_snowbird_model_to_permifrost_file(model, tf)

        run_permifrost(conn, tf.name, path)

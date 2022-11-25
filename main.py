import tempfile

from snowbird.dataproducts import create_snowflake_resources, run_permifrost
from snowbird.loader import write_snowbird_model_to_permifrost_file


def configure_infrastructure():

    # create snowflake resources based on snowbird formatted spec file: snowflake.yml
    model = create_snowflake_resources()

    # dump snowbird spec to file in permifrost compatible schema
    # and run permifrost to update permissions in snowflake
    with tempfile.NamedTemporaryFile(mode="w+") as tf:
        write_snowbird_model_to_permifrost_file(model, tf)
        run_permifrost(tf.name)


if __name__ == "__main__":
    configure_infrastructure()

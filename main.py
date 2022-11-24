import tempfile

from snowbird.dataproducts import create_resources, run_permifrost
from snowbird.loader import dump_permifrost_model_to_file


def configure_infrastructure():

    # create resources based on snowbird formatted spec file
    model = create_resources()

    # dump snowbird spec to file in permifrost compatible schema
    with tempfile.NamedTemporaryFile(mode="w+") as tf:
        dump_permifrost_model_to_file(model, tf)
        run_permifrost(tf.name)


if __name__ == "__main__":
    configure_infrastructure()

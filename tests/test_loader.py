import json
import tempfile
from pathlib import Path

import yaml
from permifrost.spec_file_loader import load_spec

from snowbird.loader import get_snowbird_model, write_permifrost_model_to_file
from snowbird.models import Database, PermifrostModel, SnowbirdModel


def test_updating_snowflake():

    model = get_snowbird_model("snowflake.yml", Path(__file__).parent)
    assert type(model) == SnowbirdModel


def test_to_permifrost():

    model = get_snowbird_model("snowflake.yml", Path(__file__).parent)

    pm = PermifrostModel(**model.dict())

    with tempfile.NamedTemporaryFile(mode="w+") as tf:
        js = json.loads(pm.json())
        yaml.dump(js, tf)
        spec = load_spec(tf.name)
        assert type(spec) == dict


def test_schemas():

    model = get_snowbird_model("snowflake.yml", Path(__file__).parent)

    for item in model.databases:
        for name in item.keys():
            db: Database = item[name]
            for schema in db.schemas:
                assert type(schema) == str


def test_get_permifrost_model():

    with tempfile.NamedTemporaryFile(mode="w+") as tf:
        write_permifrost_model_to_file(tf, "snowflake.yml", Path(__file__).parent)
        spec = load_spec(tf.name)
        assert type(spec) == dict


test_get_permifrost_model()

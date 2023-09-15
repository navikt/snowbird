import json
import tempfile
from pathlib import Path

import yaml
from permifrost.spec_file_loader import ensure_valid_schema, load_spec
from permifrost.types import PermifrostSpecSchema

from snowbird.loader import load_snowbird_spec
from snowbird.models import Database, PermifrostModel, SnowbirdModel

path = Path(__file__).parent / "infrastructure"


def test_updating_snowflake():
    model = load_snowbird_spec("read_only_role.y,", path)
    assert type(model) == SnowbirdModel


def test_to_permifrost():
    # get snowbird model
    model = load_snowbird_spec("read_only_role.yml", path)

    # convert to permifrost model
    pm = PermifrostModel(**model.dict())

    spec = json.loads(pm.model_dump_json())
    res = ensure_valid_schema(spec)

    for error in res:
        print(error)

    with tempfile.NamedTemporaryFile(mode="w+") as tf:
        yaml.dump(spec, tf)
        spec_from_file = load_spec(tf.name)
        assert type(spec_from_file) == dict


def test_schemas():
    model = load_snowbird_spec("read_only_role.yml", path)

    for item in model.databases:
        for name in item.keys():
            db: Database = item[name]
            for schema in db.schemas:
                assert type(schema) == str


test_to_permifrost()

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Iterator

LOGGER = logging.getLogger()


import yaml

from snowbird.models import PermifrostModel, SnowbirdModel


def read_json(source: str) -> Dict:
    with open(source, "r") as f:
        try:
            jobs_spec = yaml.safe_load(f)
            return jobs_spec
        except Exception as e:
            LOGGER.error(f"Error loading yaml file {source}. {e} ")


def get_spec_file_paths(
    spec_file: str = "snowflake.yml", root_dir: Path = None
) -> Iterator[Path]:

    root_dir = root_dir or Path.cwd()

    infra_dir = root_dir
    if infra_dir.is_dir():
        for spec_file in infra_dir.glob(spec_file):
            if spec_file.is_file():
                return spec_file

    LOGGER.error(f"Could not find spec file. Path: {root_dir}. File: {spec_file}")
    return None


def load_snowbird_spec(spec_file: str, root_dir: Path = None) -> SnowbirdModel:

    spec_file = get_spec_file_paths(spec_file, root_dir)
    try:
        js = read_json(str(spec_file))
        model = SnowbirdModel(**js)
        return model
    except Exception as e:
        LOGGER.error(f"Error parsing spec file {spec_file}. {e}")


def write_snowbird_model_to_permifrost_file(
    model: SnowbirdModel, tf: tempfile.NamedTemporaryFile
) -> str:

    if model is None:
        LOGGER.error(f"Could not write model to permifrost. No model supplied")

    try:
        pm = PermifrostModel(**model.dict())
    except Exception as e:
        LOGGER.error(f"Error parsing json as permifrost formatspec file. {e}")

    try:
        js = json.loads(pm.json())
        yaml.dump(js, tf)
    except Exception as e:
        LOGGER.error(f"Error writing permifrost model to file. {e}")

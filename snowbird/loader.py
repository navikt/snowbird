import logging
from pathlib import Path
from typing import Dict, Iterator

LOGGER = logging.getLogger()


import yaml

from snowbird.models import SnowbirdModel


def read_json(source: str) -> Dict:
    with open(source, "r") as f:
        try:
            jobs_spec = yaml.safe_load(f)
            return jobs_spec
        except Exception as e:
            print(e)


def get_spec_file_paths(spec_file: str, root_dir: Path = None) -> Iterator[Path]:

    root_dir = root_dir or Path.cwd()

    infra_dir = root_dir / "infrastructure"
    # TODO: only process new/updated files
    if infra_dir.is_dir():
        for spec_file in infra_dir.glob("snowflake.yml"):
            if spec_file.is_file():
                yield spec_file


def get_snowbird_model(spec_file: str, root_dir: Path = None) -> SnowbirdModel:

    for spec_file in get_spec_file_paths(spec_file, root_dir):
        try:
            js = read_json(str(spec_file))
            model = SnowbirdModel(**js)
            return model
        except Exception as e:
            LOGGER.error(f"Error parsing spec file {spec_file}. {e}")

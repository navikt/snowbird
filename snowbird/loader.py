import logging
from pathlib import Path
from typing import Dict, Iterator

LOGGER = logging.getLogger()


import yaml

from snowbird.models import Model


def read_json(source: str) -> Dict:
    with open(source, "r") as f:
        try:
            jobs_spec = yaml.safe_load(f)
            return jobs_spec
        except Exception as e:
            print(e)


def get_spec_file_paths(spec_file: str, root_dir: Path = None) -> Iterator[Path]:

    root_dir = root_dir or Path.cwd()

    config_dir = root_dir / "infrastructure"
    # TODO: only process new/updated files
    if config_dir.is_dir():
        for team_dir in config_dir.glob("*"):
            path = team_dir.absolute()
            if path.is_dir():
                for dataproducts_dir in team_dir.glob("*"):
                    path = dataproducts_dir.absolute()
                    if path.is_dir():
                        resource_file = path / spec_file
                        if resource_file.is_file():
                            yield resource_file


def get_models(spec_file: str, root_dir: Path = None) -> Iterator[Model]:

    for spec_file in get_spec_file_paths(spec_file, root_dir):
        try:
            js = read_json(str(spec_file))
            model = Model(**js)
            yield model
        except Exception as e:
            LOGGER.error(f"Error parsing spec file {spec_file}. {e}")

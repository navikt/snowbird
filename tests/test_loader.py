import os
from pathlib import Path

from snowbird.loader import get_models
from snowbird.models import Model


def test_updating_snowflake():

    try:
        models = get_models("snowflake.yml", Path(__file__).parent)
        for model in models:
            assert type(model) == Model
    except:
        assert False

test_updating_snowflake()
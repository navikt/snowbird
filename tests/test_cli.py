import logging
from os import environ
from pathlib import Path

from click.testing import CliRunner

from snowbird.command import cli
from snowbird.loader import LOGGER


def test_info():
    runner = CliRunner()
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0


def test_invoke_nonexisting_specfile_results_in_loadsnowbirdspecerror():
    runner = CliRunner()
    path = Path.cwd()
    file = "nothing.yml"
    result = runner.invoke(cli, ["run", "--path", path, "--file", file])
    assert result.exit_code == 1
    assert result.exception.__class__.__name__ == "LoadSnowbirdSpecError"


def test_invoke_witouth_env_variables_exits_with_error():
    environ.clear()
    runner = CliRunner()
    path = Path.cwd()
    file = "tests/infrastructure/snowflake.yml"
    result = runner.invoke(cli, ["run", "--path", path, "--file", file])
    logging.info(result.output)
    assert result.exit_code == 1
    assert result.exception.__class__.__name__ == "SnowflakeConnectionError"

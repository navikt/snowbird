from pathlib import Path

from click.testing import CliRunner

from snowbird.command import cli


def test_info():
    runner = CliRunner()
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0


def test_run():
    runner = CliRunner()
    path = Path.cwd()
    file = "nothing.yml"
    result = runner.invoke(cli, ["run", "--path", path, "--file", file])
    assert result.exit_code == 0

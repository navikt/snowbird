from pathlib import Path

from click.testing import CliRunner

from snowbird.command import snowbird


def test_info():
    runner = CliRunner()
    result = runner.invoke(snowbird, ["info"])
    assert result.exit_code == 0


def test_run():
    runner = CliRunner()
    path = Path.cwd()
    file = "nothing.yml"
    result = runner.invoke(snowbird, ["run", "--path", path, "--file", file])
    assert result.exit_code == 0

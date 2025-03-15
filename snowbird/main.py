import json
from pathlib import Path

import click

from snowbird.plan import execution_plan, load_config
from snowbird.state import current_state
from snowbird.utils import progressbar, snowflake_cursor, spinner

DEFAULT_CONFIG = "snowflake.yml"
DEFAULT_STATE = "state.json"


def _setup_execution_plan(config, silent, state, stateless):
    if state and stateless == True:
        click.echo("Cannot use --state and --stateless together")
        exit(1)

    config = load_config(path=config)
    if stateless:
        return execution_plan(config=config)
    if state:
        snowflake_state = Path(state).read_text(encoding="utf-8")
        return execution_plan(config=config, state=json.loads(snowflake_state))
    if silent:
        snowflake_state = current_state(config=config)
        return execution_plan(config=config, state=snowflake_state)
    with spinner("Fetching state"):
        snowflake_state = current_state(config=config)
        return execution_plan(config=config, state=snowflake_state)


@click.group(name="cli")
@click.version_option()
def cli():
    pass


@cli.command()
@click.option("--config", default=DEFAULT_CONFIG, help="Path to the configuration file")
@click.option(
    "--silent",
    is_flag=True,
    help="Silent mode. Can be used if you want to write the output to a file",
)
@click.option(
    "--state",
    help="Path snowflake state file to compare against",
)
@click.option("--stateless", is_flag=True, help="Run without state comparison")
def plan(config, silent, state, stateless):
    execution_plan = _setup_execution_plan(
        config=config, silent=silent, state=state, stateless=stateless
    )
    if silent == False:
        click.echo("Execution plan")
    for statement in execution_plan:
        click.echo(f"{statement};")


@cli.command()
@click.option("--config", default=DEFAULT_CONFIG, help="Path to the configuration file")
@click.option(
    "--silent",
    is_flag=True,
    help="Silent mode. Won't print the statements to the console",
)
@click.option(
    "--state",
    help="Path snowflake state file to compare against",
)
@click.option("--stateless", is_flag=True, help="Run without state comparison")
def apply(config, silent, state, stateless):
    execution_plan = _setup_execution_plan(
        config=config, silent=silent, state=state, stateless=stateless
    )
    with snowflake_cursor() as cursor:
        if silent == False:
            for statement in progressbar(execution_plan, title="Executing plan"):
                cursor.execute(statement)
        else:
            for statement in execution_plan:
                cursor.execute(statement)


@cli.group(name="save")
def save():
    pass


@save.command()
@click.option(
    "--file", default=DEFAULT_STATE, help="Path to the file to write the state to"
)
@click.option("--config", default=DEFAULT_CONFIG, help="Path to the configuration file")
def state(file, config):
    config = load_config(config)
    with spinner("Fetching state"):
        state = current_state(config)
    with open(file, "w") as f:
        f.write(json.dumps(state, indent=4, sort_keys=True, default=str))


if __name__ == "__main__":
    cli()

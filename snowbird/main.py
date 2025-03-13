import json

import click
import snowflake.connector

from snowbird.plan import execution_plan, load_config
from snowbird.state import current_state
from snowbird.utils import _snow_config

DEFAULT_CONFIG = "snowflake.yml"


def _setup_execution_plan(config, silent, state, stateless):
    if state and stateless == True:
        click.echo("Cannot use --state and --stateless together")
        return

    path = config if config else DEFAULT_CONFIG
    config = load_config(path=path)
    if silent == False and not stateless:
        click.echo("Fetching state")
    if stateless:
        return execution_plan(config=config)
    if state:
        with open(state, "r") as f:
            state = json.load(f)
    return execution_plan(config=config, state=state)


@click.group(name="cli")
@click.version_option()
def cli():
    pass


@cli.command()
@click.option("--config", help="Path to the configuration file")
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
@click.option("--config", help="Path to the configuration file")
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
    if silent == False:
        click.echo("Applying execution plan")
    with snowflake.connector.connect(**_snow_config()).cursor() as cursor:
        for statement in execution_plan:
            if silent == False:
                click.echo("Executing statement")
                click.echo(f"{statement};")
            cursor.execute(statement)


@cli.group(name="save")
def save():
    pass


@save.command()
@click.option(
    "--file", default="state.json", help="Path to the file to write the state to"
)
def state(file):
    click.echo("Fetching state")
    with open(file, "w") as f:
        f.write(json.dumps(current_state(), indent=4, sort_keys=True, default=str))


if __name__ == "__main__":
    cli()

import json
import sys
from pathlib import Path

import click

from snowbird.plan import execution_plan, load_config, overview
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
    plan_overview = overview(execution_plan=execution_plan)
    create_databases = plan_overview.get("create_databases", [])
    create_schemas = plan_overview.get("create_schemas", [])
    create_roles = plan_overview.get("create_roles", [])
    create_users = plan_overview.get("create_users", [])
    create_warehouses = plan_overview.get("create_warehouses", [])
    modify_databases = plan_overview.get("modify_databases", [])
    modify_schemas = plan_overview.get("modify_schemas", [])
    modify_roles = plan_overview.get("modify_roles", [])
    modify_users = plan_overview.get("modify_users", [])
    modify_warehouses = plan_overview.get("modify_warehouses", [])
    grant_selects = plan_overview.get("grant_selects", [])
    grant_create = plan_overview.get("grant_create", [])
    grant_roles = plan_overview.get("grant_roles", [])
    grant_users = plan_overview.get("grant_users", [])

    if silent == False:
        click.echo("\nCreate or modify:")
        click.echo("-----------------")

        total_create_objects = len(
            create_databases + create_schemas + create_roles + create_users
        )
        total_modify_objects = len(
            modify_databases + modify_schemas + modify_roles + modify_users
        )
        click.echo(
            "Total:".ljust(20)
            + f"{str(total_create_objects).rjust(2)} create, {str(total_modify_objects).rjust(2)} modify\n"
        )
        click.echo(
            "Databases:".ljust(20)
            + f"{str(len(create_databases)).rjust(2)} create, {str(len(modify_databases)).rjust(2)} modify"
        )
        click.echo(
            "Schemas:".ljust(20)
            + f"{str(len(create_schemas)).rjust(2)} create, {str(len(modify_schemas)).rjust(2)} modify"
        )
        click.echo(
            "Roles:".ljust(20)
            + f"{str(len(create_roles)).rjust(2)} create, {str(len(modify_roles)).rjust(2)} modify"
        )
        click.echo(
            "Users:".ljust(20)
            + f"{str(len(create_users)).rjust(2)} create, {str(len(modify_users)).rjust(2)} modify"
        )
        click.echo(
            "Warehouses:".ljust(20)
            + f"{str(len(create_warehouses)).rjust(2)} create, {str(len(modify_warehouses)).rjust(2)} modify\n"
        )

        click.echo(f"Grant:")
        click.echo("------")
        click.echo(
            "Total:".ljust(20)
            + f"{str(len(grant_selects) + len(grant_create) + len(grant_roles) + len(grant_users)).rjust(2)} apply,   0 revoke\n"
        )
        click.echo(
            "Read on schema:".ljust(20)
            + f"{str(len(grant_selects)).rjust(2)} apply,   0 revoke"
        )
        click.echo(
            "Write on schema:".ljust(20)
            + f"{str(len(grant_create)).rjust(2)} apply,   0 revoke"
        )
        click.echo(
            "Role to role:".ljust(20)
            + f"{str(len(grant_roles)).rjust(2)} apply,   0 revoke"
        )
        click.echo(
            "Role to user:".ljust(20)
            + f"{str(len(grant_users)).rjust(2)} apply,   0 revoke"
        )
        click.echo("")


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
        if silent:
            for statement in execution_plan:
                try:
                    cursor.execute(statement)
                except Exception:
                    sys.exit(1)
            return
        for statement in progressbar(execution_plan, title="Executing plan"):
            try:
                cursor.execute(statement)
            except Exception as e:
                msg = f"Error executing statement: {statement}\n{str(e)}"
                print(msg)
                sys.exit(1)


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

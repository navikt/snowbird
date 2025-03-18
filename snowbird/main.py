import json
import re
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
    create_databases = [s.split()[5] for s in execution_plan if "create database" in s]
    alter_databases = [s.split()[2] for s in execution_plan if "alter database" in s]
    modify_databases = [d for d in alter_databases if d not in create_databases]

    create_schemas = [s.split()[5] for s in execution_plan if "create schema" in s]
    alter_schemas = [s for s in execution_plan if "alter schema" in s]
    modify_schemas = [
        s.split()[2] for s in alter_schemas if s.split()[2] not in create_schemas
    ]

    create_roles = [s.split()[5] for s in execution_plan if "create role" in s]
    alter_roles = [s.split()[2] for s in execution_plan if "alter role" in s]
    modify_roles = [r for r in alter_roles if r not in create_roles]

    create_users = [s.split()[5] for s in execution_plan if "create user" in s]
    alter_users = [s.split()[2] for s in execution_plan if "alter user" in s]
    modify_users = [u for u in alter_users if u not in create_users]

    create_warehouses = [
        s.split()[5] for s in execution_plan if "create warehouse" in s
    ]
    alter_warehouses = [s.split()[2] for s in execution_plan if "alter warehouse" in s]
    print(alter_warehouses)
    modify_warehouses = [w for w in alter_warehouses if w not in create_warehouses]

    alter_warehouses = [s for s in execution_plan if "alter warehouse" in s]

    grant_selects = [s for s in execution_plan if "grant select on" in s]
    grant_create = [s for s in execution_plan if "grant create table" in s]
    grant_roles = [s for s in execution_plan if "grant role" in s and "to role" in s]
    grant_users = [s for s in execution_plan if "grant role" in s and "to user" in s]

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
                cursor.execute(statement)
            return
        for statement in progressbar(execution_plan, title="Executing plan"):
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

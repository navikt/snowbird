import importlib
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
@click.option(
    "--execution-plan",
    "print_execution_plan",
    is_flag=True,
    default=False,
    help="Print the execution plan",
)
def plan(config, silent, state, stateless, print_execution_plan):
    execution_plan = _setup_execution_plan(
        config=config, silent=silent, state=state, stateless=stateless
    )
    plan_overview = overview(execution_plan=execution_plan)
    create_databases = plan_overview.get("create_databases", [])
    create_schemas = plan_overview.get("create_schemas", [])
    create_roles = plan_overview.get("create_roles", [])
    create_users = plan_overview.get("create_users", [])
    create_warehouses = plan_overview.get("create_warehouses", [])
    create_network_policies = plan_overview.get("create_network_policies", [])
    modify_databases = plan_overview.get("modify_databases", [])
    modify_schemas = plan_overview.get("modify_schemas", [])
    modify_roles = plan_overview.get("modify_roles", [])
    modify_users = plan_overview.get("modify_users", [])
    modify_warehouses = plan_overview.get("modify_warehouses", [])
    modify_network_policies = plan_overview.get("modify_network_policies", [])
    grant_selects = plan_overview.get("grant_selects", [])
    grant_select_on_objects = plan_overview.get("grant_select_on_objects", [])
    grant_create = plan_overview.get("grant_create", [])
    grant_roles = plan_overview.get("grant_roles", [])
    grant_users = plan_overview.get("grant_users", [])
    grant_warehouses = plan_overview.get("grant_warehouses", [])
    grant_databases = plan_overview.get("grant_databases", [])
    grant_schemas = plan_overview.get("grant_schemas", [])
    revoke_roles = plan_overview.get("revoke_roles", [])
    revoke_users = plan_overview.get("revoke_users", [])
    revoke_warehouses = plan_overview.get("revoke_warehouses", [])
    revoke_databases = plan_overview.get("revoke_databases", [])
    revoke_schemas = plan_overview.get("revoke_schemas", [])
    revoke_selects = plan_overview.get("revoke_selects", [])
    revoke_select_on_objects = plan_overview.get("revoke_select_on_objects", [])
    revoke_create = plan_overview.get("revoke_create", [])

    if silent == False:
        click.echo("\nCreate or modify:")
        click.echo("-----------------")

        total_create_objects = len(
            create_databases
            + create_schemas
            + create_roles
            + create_users
            + create_warehouses
            + create_network_policies
        )
        total_modify_objects = len(
            modify_databases
            + modify_schemas
            + modify_roles
            + modify_users
            + modify_warehouses
            + modify_network_policies
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
            + f"{str(len(create_warehouses)).rjust(2)} create, {str(len(modify_warehouses)).rjust(2)} modify"
        )
        click.echo(
            "Network policies:".ljust(20)
            + f"{str(len(create_network_policies)).rjust(2)} create, {str(len(modify_network_policies)).rjust(2)} modify"
        )
        click.echo("")

        click.echo(f"Grant or revoke:")
        click.echo("----------------")
        total_grants = sum(
            map(
                len,
                [
                    grant_selects,
                    grant_select_on_objects,
                    grant_create,
                    grant_roles,
                    grant_users,
                    grant_warehouses,
                    grant_databases,
                    grant_schemas,
                ],
            )
        )
        total_revokes = sum(
            map(
                len,
                [
                    revoke_roles,
                    revoke_users,
                    revoke_warehouses,
                    revoke_databases,
                    revoke_schemas,
                    revoke_selects,
                    revoke_select_on_objects,
                    revoke_create,
                ],
            )
        )
        click.echo(
            "Total:".ljust(20)
            + f"{str(total_grants).rjust(2)} grant, {str(total_revokes).rjust(3)} revoke\n"
        )
        click.echo(
            "Warehouses:".ljust(20)
            + f"{str(len(grant_warehouses)).rjust(2)} grant, {str(len(revoke_warehouses)).rjust(3)} revoke"
        )
        click.echo(
            "Databases:".ljust(20)
            + f"{str(len(grant_databases)).rjust(2)} grant, {str(len(revoke_databases)).rjust(3)} revoke"
        )
        click.echo(
            "Schemas:".ljust(20)
            + f"{str(len(grant_schemas)).rjust(2)} grant, {str(len(revoke_schemas)).rjust(3)} revoke"
        )
        click.echo(
            "Read on schema:".ljust(20)
            + f"{str(len(grant_selects)).rjust(2)} grant, {str(len(revoke_selects)).rjust(3)} revoke"
        )
        click.echo(
            "Read on object:".ljust(20)
            + f"{str(len(grant_select_on_objects)).rjust(2)} grant, {str(len(revoke_select_on_objects)).rjust(3)} revoke"
        )
        click.echo(
            "Write on schema:".ljust(20)
            + f"{str(len(grant_create)).rjust(2)} grant, {str(len(revoke_create)).rjust(3)} revoke"
        )
        click.echo(
            "Role to role:".ljust(20)
            + f"{str(len(grant_roles)).rjust(2)} grant, {str(len(revoke_roles)).rjust(3)} revoke"
        )
        click.echo(
            "Role to user:".ljust(20)
            + f"{str(len(grant_users)).rjust(2)} grant, {str(len(revoke_users)).rjust(3)} revoke"
        )
        click.echo("")
    if print_execution_plan == True:
        if not silent:
            click.echo("\nExecution plan:")
            click.echo("----------------")
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
        if silent:
            for statement in execution_plan:
                try:
                    cursor.execute(statement)
                except Exception:
                    sys.exit(1)
        else:
            for statement in progressbar(execution_plan, title="Executing plan"):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    msg = f"Error executing statement: {statement}\n{str(e)}"
                    print(msg)
                    sys.exit(1)

        new_config = load_config(path=config)
        id = new_config["id"]
        config_str = json.dumps(new_config, indent=4, sort_keys=True, default=str)
        snowbird_version = importlib.metadata.version("snowbird")
        query = f"""
            merge into snowbird.config.latest target using (select '{id}' as id) as source
            on target.id = source.id
            when matched then
                update set target.config = parse_json('{config_str}'),
                target.snowbird_version = '{snowbird_version}',
                target.updated_at = current_timestamp()
            when not matched then
                insert (id, config, snowbird_version, updated_at)
                values (source.id, parse_json('{config_str}'), '{snowbird_version}', current_timestamp())
            ;
        """
        cursor.execute(query)


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

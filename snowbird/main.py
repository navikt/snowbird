import click

from snowbird.plan import execution_plan, load_config


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
def plan(config, silent):
    if silent == False:
        click.echo("Planning")
        click.echo("Execution plan")
    path = config if config else "snowflake.yml"
    config = load_config(path=path)
    execution_statements = execution_plan(config=config)
    for statement in execution_statements:
        click.echo(f"{statement};")

if __name__ == "__main__":
    cli()

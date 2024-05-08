import click

from snowbird import __version__ as version
from snowbird import app
from snowbird.create_dev_db import create_db_clone

LOGO = rf"""
Snowbird. version: {version}
"""


@click.group(name="cli")
@click.version_option(version, "--version", "-V", help="Show version and exit")
def cli():
    pass


@cli.command()
def info():
    """Get more information about snowbird."""
    click.secho(LOGO, fg="green")
    click.secho(
        "Snowbird configures Snowflake ressources based on declarations in yml. Builds on Permifrost"
    )


@cli.command()
@click.option(
    "--path", default="./infrastructure", help="Path to infrastructure yml files."
)
@click.option("--file", default="snowflake.yml", help="yml file.")
def run(path, file):
    app.run(path, file)


@cli.command()
@click.argument("db", nargs=1, required=True)
@click.argument("to", nargs=1, required=True)
@click.option("--usage", "-u", multiple=True, help="Grant usage to role")
def clone(db, to, usage):
    create_db_clone(src=db, dst=to, usage=usage)


if __name__ == "__main__":
    cli()

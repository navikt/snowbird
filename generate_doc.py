import click

from snowbird.main import cli as snowbird


def generate_doc():
    with open("COMMANDS.md", "w") as f:
        f.write("# Commands\n\n")
        f.write("```text\n")
        recursive_help(snowbird, f, None)
        f.write("```\n")


def recursive_help(cmd, writer, parent=None):
    if parent is None:
        info_name = "snowbird"
    else:
        info_name = cmd.name
    ctx = click.core.Context(cmd, info_name=info_name, parent=parent)
    writer.write(cmd.get_help(ctx))
    writer.write("\n\n")
    commands = getattr(cmd, "commands", {})
    for sub in commands.values():
        recursive_help(cmd=sub, writer=writer, parent=ctx)


generate_doc()

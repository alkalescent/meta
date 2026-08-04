"""Command-line interface for silicon hello world template."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Annotated

import typer

from silicon.tools import Greeter

PACKAGE_NAME = Path(__file__).parent.name

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
version_help = "Show the installed version."


@app.callback()
def main(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help=version_help,
            callback=lambda value: version() if value else None,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """A Python CLI hello world template."""
    pass


@app.command(help="Say hello to someone.")
def hello(
    name: Annotated[str, typer.Option("--name", "-n", help="Name to greet")] = "World",
) -> None:
    """Say hello to someone."""
    greeter = Greeter(name)
    typer.echo(greeter.greet())
    raise typer.Exit(code=0)


@app.command(help="Say goodbye to someone.")
def goodbye(
    name: Annotated[
        str, typer.Option("--name", "-n", help="Name to bid farewell")
    ] = "World",
) -> None:
    """Say goodbye to someone."""
    greeter = Greeter(name)
    typer.echo(greeter.farewell())
    raise typer.Exit(code=0)


@app.command(help=version_help)
def version() -> None:
    """Display the installed package version."""
    prefix = "v"
    try:
        typer.echo(f"{prefix}{get_version(PACKAGE_NAME)}")
    except PackageNotFoundError:
        typer.echo(f"{prefix}0.0.0")
    # Exit is needed for the --version flag callback to terminate execution.
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()

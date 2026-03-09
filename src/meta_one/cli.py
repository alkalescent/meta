"""Main CLI application for meta.one."""

from __future__ import annotations

import subprocess
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer

from meta_one.contributors import analyze_contributors
from meta_one.deps import analyze_deps
from meta_one.detect import detect_project_type
from meta_one.env import analyze_env
from meta_one.health import run_health_checks
from meta_one.output import (
    SYMBOL_FAIL,
    SYMBOL_OK,
    SYMBOL_WARN,
    Context,
    json_out,
)
from meta_one.scripts import discover_scripts
from meta_one.size import analyze_size

app = typer.Typer(invoke_without_command=True)


def get_version() -> str:
    """Get package version.

    Returns:
        str: Package version.
    """
    try:
        return metadata.version("meta.one")
    except metadata.PackageNotFoundError:
        return "0.0.0-dev"


def version_callback(value: bool) -> None:
    """Print version and exit.

    Args:
        value (bool): Whether version flag was passed.
    """
    if value:
        typer.echo(f"v{get_version()}")
        raise typer.Exit(code=0)


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version.",
        ),
    ] = None,
    json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable colors.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet output.")] = False,
    path: Annotated[
        str, typer.Option("--path", help="Path to project directory.")
    ] = ".",
) -> None:
    """Meta CLI application."""
    ctx.obj = Context(
        path=str(Path(path).resolve()),
        json_output=json,
        no_color=no_color,
        quiet=quiet,
    )
    if ctx.invoked_subcommand is None:
        _overview(ctx.obj)


def _overview(ctx: Context) -> None:
    """Run overview of the project.

    Args:
        ctx (Context): The application context.
    """
    if ctx.json_output:
        typer.echo(json_out({"overview": "Not fully implemented in JSON for overview"}))
        return

    # Basic overview data gathering
    target_path = Path(ctx.path)
    project_name = target_path.name
    proj_type = detect_project_type(target_path).project_type

    # Gather data from modules
    size_data = analyze_size(target_path)
    files = size_data.total_files if size_data else 0
    lines = size_data.total_lines if size_data else 0

    deps_data = analyze_deps(target_path)
    deps_count = len(deps_data.production) if deps_data else 0
    dev_count = len(deps_data.dev) if deps_data else 0

    scripts = discover_scripts(target_path)
    scripts_count = sum(len(s.scripts) for s in scripts)

    env_data = analyze_env(target_path)
    env_vars = env_data.expected_vars if env_data else []
    expected = len(env_vars)
    missing = sum(1 for v in env_vars if v.status == "MISSING")

    # Git stats
    branch = "unknown"
    uncommitted = 0
    last_commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=target_path, text=True
        ).strip()
        porcelain = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=target_path, text=True
        )
        uncommitted = len([line for line in porcelain.splitlines() if line.strip()])
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%ar by %an"], cwd=target_path, text=True
        ).strip()
    except subprocess.SubprocessError:
        pass

    health_data = run_health_checks(target_path)
    issues = sum(1 for h in health_data if h.status != "pass")

    typer.echo(f"Project:     {project_name}")
    typer.echo(f"Type:        {proj_type}")
    typer.echo("Language:    Unknown (0%)")  # Needs real language breakdown
    typer.echo(f"Size:        {files} files, {lines} lines")
    typer.echo(f"Deps:        {deps_count} dependencies, {dev_count} dev")
    typer.echo(f"Scripts:     {scripts_count} runnable")
    typer.echo(f"Env:         {expected} expected, {missing} missing")
    typer.echo(f"Git:         {branch} branch, {uncommitted} uncommitted changes")
    typer.echo(f"Last commit: {last_commit}")
    typer.echo(
        f"Health:      {SYMBOL_WARN if issues else SYMBOL_OK} {issues} issues found"
    )


@app.command()
def deps(
    ctx: typer.Context,
    dev: Annotated[
        bool, typer.Option("--dev", help="Show only dev dependencies.")
    ] = False,
    outdated: Annotated[
        bool, typer.Option("--outdated", help="Check for outdated dependencies.")
    ] = False,
) -> None:
    """Analyze project dependencies."""
    if outdated:
        typer.echo("Note: Outdated check not yet fully implemented.")

    data = analyze_deps(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(
            json_out(
                {
                    "production": [d.__dict__ for d in data.production],
                    "dev": [d.__dict__ for d in data.dev],
                }
            )
        )
        return

    typer.echo("Production Dependencies:")
    for d in data.production:
        typer.echo(f"  {d.name}@{d.version}")

    if dev or not data.production:
        typer.echo("Development Dependencies:")
        for d in data.dev:
            typer.echo(f"  {d.name}@{d.version}")


@app.command()
def scripts(
    ctx: typer.Context,
    run: Annotated[str | None, typer.Option("--run", help="Run a script.")] = None,
) -> None:
    """Discover project scripts."""
    if run:
        typer.echo(f"Running script {run} (not fully implemented)")
        return

    data = discover_scripts(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(
            json_out(
                [
                    {
                        "source": s.source_file,
                        "scripts": [sc.__dict__ for sc in s.scripts],
                    }
                    for s in data
                ]
            )
        )
        return

    for source in data:
        for script in source.scripts:
            typer.echo(f"{script.name}: {script.command}")


@app.command()
def env(ctx: typer.Context) -> None:
    """Analyze environment variables."""
    data = analyze_env(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(json_out({"variables": [v.__dict__ for v in data.expected_vars]}))
        return

    for var in data.expected_vars:
        status = var.status
        typer.echo(f"{var.name}: {status}")


@app.command()
def size(
    ctx: typer.Context,
    sort: Annotated[str, typer.Option("--sort", help="Sort order.")] = "lines",
    depth: Annotated[int, typer.Option("--depth", help="Directory depth.")] = 3,
    code_only: Annotated[
        bool, typer.Option("--code-only", help="Include code only.")
    ] = False,
) -> None:
    """Analyze project size."""
    data = analyze_size(
        Path(ctx.obj.path), sort_by=sort, depth=depth, code_only=code_only
    )
    if ctx.obj.json_output:
        typer.echo(
            json_out({"total_lines": data.total_lines, "total_files": data.total_files})
        )
        return

    typer.echo(f"Total lines: {data.total_lines}")


@app.command()
def contributors(
    ctx: typer.Context,
    since: Annotated[str | None, typer.Option("--since", help="Since date.")] = None,
    author: Annotated[str | None, typer.Option("--author", help="Author name.")] = None,
) -> None:
    """Analyze Git contributors."""
    since_arg = since if since is not None else ""
    author_arg = author if author is not None else ""
    data = analyze_contributors(Path(ctx.obj.path), since=since_arg, author=author_arg)
    if ctx.obj.json_output:
        typer.echo(json_out({"contributors": [c.__dict__ for c in data.contributors]}))
        return

    for c in data.contributors:
        typer.echo(f"{c.name}: {c.commits} commits")


@app.command()
def health(ctx: typer.Context) -> None:
    """Run project health checks."""
    data = run_health_checks(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(json_out([c.__dict__ for c in data]))
        return

    for check in data:
        status_sym = SYMBOL_OK if check.status == "pass" else SYMBOL_FAIL
        typer.echo(f"{status_sym} {check.message}")


@app.command()
def version(ctx: typer.Context) -> None:
    """Show version."""
    ver = get_version()
    if ctx.obj.json_output:
        typer.echo(json_out({"version": ver}))
    else:
        typer.echo(f"v{ver}")


if __name__ == "__main__":
    app()

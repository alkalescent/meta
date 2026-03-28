"""Main CLI application for meta.one."""

from __future__ import annotations

import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer

from meta_one.contributors import analyze_contributors
from meta_one.deps import analyze_deps, check_outdated
from meta_one.detect import detect_project_type
from meta_one.env import analyze_env
from meta_one.health import run_health_checks
from meta_one.output import (
    SYMBOL_FAIL,
    SYMBOL_OK,
    SYMBOL_WARN,
    Context,
    format_table,
    json_out,
)
from meta_one.scripts import discover_scripts
from meta_one.size import analyze_size

# Windows consoles often default to a non-UTF-8 codepage (e.g. cp1252),
# which can't encode the ✓/⚠/✗ status symbols and raises UnicodeEncodeError.
# Force UTF-8 with a safe fallback so output never crashes the process.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except AttributeError:
        pass

app = typer.Typer(invoke_without_command=True)

# health.py's HealthCheck.status is one of "ok"/"warn"/"fail"/"optional" —
# never "pass". Both symbol rendering and issue counting must branch on
# these actual values.
_STATUS_SYMBOLS = {
    "ok": SYMBOL_OK,
    "warn": SYMBOL_WARN,
    "optional": SYMBOL_WARN,
    "fail": SYMBOL_FAIL,
}


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
    target_path = Path(ctx.path)
    project_name = target_path.name
    proj_type = detect_project_type(target_path).project_type

    size_data = analyze_size(target_path)
    files = size_data.total_files if size_data else 0
    lines = size_data.total_lines if size_data else 0
    top_lang = size_data.languages[0] if size_data and size_data.languages else None

    deps_data = analyze_deps(target_path)
    deps_count = len(deps_data.production) if deps_data else 0
    dev_count = len(deps_data.dev) if deps_data else 0

    scripts_data = discover_scripts(target_path)
    scripts_count = sum(len(s.scripts) for s in scripts_data)

    env_data = analyze_env(target_path)
    env_vars = env_data.expected_vars if env_data else []
    expected = len(env_vars)
    missing = sum(1 for v in env_vars if v.status == "missing")

    # Git stats
    branch = "unknown"
    uncommitted = 0
    last_commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=target_path,
            text=True,
            encoding="utf-8",
        ).strip()
        porcelain = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=target_path,
            text=True,
            encoding="utf-8",
        )
        uncommitted = len([line for line in porcelain.splitlines() if line.strip()])
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%ar by %an"],
            cwd=target_path,
            text=True,
            encoding="utf-8",
        ).strip()
    except subprocess.SubprocessError:
        pass

    health_data = run_health_checks(target_path)
    issues = sum(1 for h in health_data if h.status in ("fail", "warn"))

    if ctx.json_output:
        typer.echo(
            json_out(
                {
                    "project": project_name,
                    "type": proj_type,
                    "language": top_lang.name if top_lang else "Unknown",
                    "language_percentage": round(top_lang.percentage, 1)
                    if top_lang
                    else 0.0,
                    "files": files,
                    "lines": lines,
                    "dependencies": deps_count,
                    "dev_dependencies": dev_count,
                    "scripts": scripts_count,
                    "env_expected": expected,
                    "env_missing": missing,
                    "git_branch": branch,
                    "git_uncommitted": uncommitted,
                    "last_commit": last_commit,
                    "health_issues": issues,
                }
            )
        )
        return

    language_line = (
        f"{top_lang.name} ({top_lang.percentage:.0f}%)" if top_lang else "Unknown"
    )

    typer.echo(f"Project:     {project_name}")
    typer.echo(f"Type:        {proj_type}")
    typer.echo(f"Language:    {language_line}")
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
    root = Path(ctx.obj.path)
    data = analyze_deps(root)

    outdated_deps = []
    outdated_note = None
    if outdated:
        outdated_deps, outdated_note = check_outdated(root, data)

    if ctx.obj.json_output:
        payload = (
            {"dev": [d.__dict__ for d in data.dev]}
            if dev
            else {
                "production": [d.__dict__ for d in data.production],
                "dev": [d.__dict__ for d in data.dev],
            }
        )
        if outdated:
            payload["outdated"] = [d.__dict__ for d in outdated_deps]
            if outdated_note:
                payload["outdated_note"] = outdated_note
        typer.echo(json_out(payload))
        return

    if ctx.obj.quiet:
        if dev:
            typer.echo(f"{len(data.dev)} dev dependencies")
        else:
            typer.echo(f"{len(data.production)} dependencies, {len(data.dev)} dev")
    elif dev:
        typer.echo("Development Dependencies:")
        typer.echo(format_table([[d.name, d.version] for d in data.dev]))
    else:
        typer.echo("Production Dependencies:")
        typer.echo(format_table([[d.name, d.version] for d in data.production]))
        if data.dev:
            typer.echo("Development Dependencies:")
            typer.echo(format_table([[d.name, d.version] for d in data.dev]))

    if outdated and not ctx.obj.quiet:
        if outdated_note:
            typer.echo(outdated_note)
        elif outdated_deps:
            typer.echo("Outdated:")
            typer.echo(
                format_table([[o.name, o.current, o.latest] for o in outdated_deps])
            )
        else:
            typer.echo("All dependencies up to date.")


@app.command()
def scripts(
    ctx: typer.Context,
    run: Annotated[str | None, typer.Option("--run", help="Run a script.")] = None,
) -> None:
    """Discover project scripts."""
    root = Path(ctx.obj.path)
    data = discover_scripts(root)

    if run:
        script = next(
            (sc for source in data for sc in source.scripts if sc.name == run), None
        )
        if script is None:
            typer.echo(f"No script named '{run}' found.", err=True)
            raise typer.Exit(code=1)
        result = subprocess.run(script.command, shell=True, cwd=root)
        raise typer.Exit(code=result.returncode)

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

    if ctx.obj.quiet:
        total = sum(len(s.scripts) for s in data)
        typer.echo(f"{total} scripts discovered")
        return

    rows = [
        [script.name, script.command, script.description]
        for source in data
        for script in source.scripts
    ]
    typer.echo(format_table(rows))


@app.command()
def env(ctx: typer.Context) -> None:
    """Analyze environment variables."""
    data = analyze_env(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(json_out({"variables": [v.__dict__ for v in data.expected_vars]}))
        return

    if ctx.obj.quiet:
        missing = sum(1 for v in data.expected_vars if v.status == "missing")
        typer.echo(f"{len(data.expected_vars)} expected, {missing} missing")
        return

    typer.echo(format_table([[var.name, var.status] for var in data.expected_vars]))


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
            json_out(
                {
                    "total_lines": data.total_lines,
                    "total_files": data.total_files,
                    "total_bytes": data.total_bytes,
                    "languages": [lang.__dict__ for lang in data.languages],
                    "directories": [d.__dict__ for d in data.directories],
                    "largest_files": [f.__dict__ for f in data.largest_files],
                }
            )
        )
        return

    typer.echo(
        f"Total: {data.total_files} files, {data.total_lines} lines, "
        f"{data.total_bytes} bytes"
    )

    if ctx.obj.quiet:
        return

    if data.languages:
        typer.echo("\nLanguages:")
        typer.echo(
            format_table(
                [
                    [
                        lang.name,
                        str(lang.files),
                        str(lang.lines),
                        f"{lang.percentage:.1f}%",
                    ]
                    for lang in data.languages
                ]
            )
        )

    if data.directories:
        typer.echo("\nDirectories:")
        typer.echo(
            format_table(
                [[d.path, str(d.files), str(d.lines)] for d in data.directories]
            )
        )

    if data.largest_files:
        typer.echo("\nLargest Files:")
        typer.echo(format_table([[f.path, str(f.lines)] for f in data.largest_files]))


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

    if ctx.obj.quiet:
        typer.echo(f"{len(data.contributors)} contributors")
        return

    typer.echo(
        format_table([[c.name, f"{c.commits} commits"] for c in data.contributors])
    )


@app.command()
def health(ctx: typer.Context) -> None:
    """Run project health checks."""
    data = run_health_checks(Path(ctx.obj.path))
    if ctx.obj.json_output:
        typer.echo(json_out([c.__dict__ for c in data]))
        return

    checks = (
        [c for c in data if c.status in ("fail", "warn")] if ctx.obj.quiet else data
    )
    typer.echo(
        format_table(
            [[_STATUS_SYMBOLS.get(c.status, SYMBOL_FAIL), c.message] for c in checks]
        )
    )


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

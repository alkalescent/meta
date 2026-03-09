"""Script discovery for the meta CLI tool.

Discover runnable commands across ecosystems.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Script:
    """Represents a runnable script."""

    name: str
    command: str
    description: str


@dataclass
class ScriptSource:
    """Represents a source file containing runnable scripts."""

    source_file: str
    scripts: list[Script]


DESCRIPTION_MAP: dict[str, str] = {
    "jest": "run tests",
    "vitest": "run tests",
    "pytest": "run tests",
    "mocha": "run tests",
    "next dev": "start dev server",
    "next build": "production build",
    "next start": "start production server",
    "vite": "start dev server",
    "vite build": "production build",
    "nuxt dev": "start dev server",
    "eslint": "lint codebase",
    "ruff": "lint codebase",
    "prettier": "format codebase",
    "tsc": "type check",
    "prisma migrate": "run DB migrations",
    "prisma generate": "generate Prisma client",
    "prisma studio": "open Prisma Studio",
    "docker-compose up": "start containers",
    "docker-compose down": "stop containers",
    "docker compose up": "start containers",
    "docker compose down": "stop containers",
    "npm start": "start application",
    "node": "run script",
    "tsx": "run TypeScript script",
    "ts-node": "run TypeScript script",
    "webpack": "bundle assets",
    "esbuild": "bundle assets",
    "rollup": "bundle assets",
    "storybook": "start Storybook",
    "cypress": "run E2E tests",
    "playwright": "run E2E tests",
}


def _infer_description(command: str) -> str:
    """Infer a human-readable description for a command."""
    for key, desc in DESCRIPTION_MAP.items():
        if key in command:
            return desc
    return "run script"


def discover_scripts(root: Path) -> list[ScriptSource]:
    """Discover runnable scripts in the given root directory.

    Args:
        root: The root directory to scan.

    Returns:
        A list of ScriptSource objects containing discovered scripts.
    """
    sources: list[ScriptSource] = []

    package_json = root / "package.json"
    if package_json.exists():
        try:
            with package_json.open(encoding="utf-8") as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                if scripts:
                    script_list = [
                        Script(name, cmd, _infer_description(cmd))
                        for name, cmd in scripts.items()
                    ]
                    sources.append(ScriptSource("package.json", script_list))
        except Exception:
            pass

    makefile = root / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text(encoding="utf-8")
            matches = re.finditer(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE)
            scripts_list: list[Script] = []
            for match in matches:
                name = match.group(1)
                if not name.startswith("_") and not name.startswith("."):
                    scripts_list.append(Script(name, f"make {name}", "run make target"))
            if scripts_list:
                sources.append(ScriptSource("Makefile", scripts_list))
        except Exception:
            pass

    justfile = root / "justfile"
    if justfile.exists():
        try:
            content = justfile.read_text(encoding="utf-8")
            matches = re.finditer(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE)
            scripts_list = []
            for match in matches:
                name = match.group(1)
                if not name.startswith("_"):
                    scripts_list.append(Script(name, f"just {name}", "run just recipe"))
            if scripts_list:
                sources.append(ScriptSource("justfile", scripts_list))
        except Exception:
            pass

    taskfile = root / "Taskfile.yml"
    if taskfile.exists():
        try:
            content = taskfile.read_text(encoding="utf-8")
            # Simple regex parser for YAML tasks
            in_tasks = False
            scripts_list = []
            for line in content.splitlines():
                if line.startswith("tasks:"):
                    in_tasks = True
                    continue
                if in_tasks:
                    match = re.match(r"^  ([a-zA-Z0-9_-]+):", line)
                    if match:
                        name = match.group(1)
                        scripts_list.append(Script(name, f"task {name}", "run task"))
                    elif line and not line.startswith(" "):
                        in_tasks = False
            if scripts_list:
                sources.append(ScriptSource("Taskfile.yml", scripts_list))
        except Exception:
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            scripts_list = []

            taskipy_tasks = data.get("tool", {}).get("taskipy", {}).get("tasks", {})
            for name, cmd in taskipy_tasks.items():
                scripts_list.append(Script(name, cmd, _infer_description(cmd)))

            project_scripts = data.get("project", {}).get("scripts", {})
            for name, cmd in project_scripts.items():
                scripts_list.append(Script(name, cmd, _infer_description(cmd)))

            if scripts_list:
                sources.append(ScriptSource("pyproject.toml", scripts_list))
        except Exception:
            pass

    return sources

# scripts

Discover runnable scripts across `package.json`, `Makefile`, `justfile`, `Taskfile.yml`, and `pyproject.toml` (`[tool.taskipy.tasks]` or `[project.scripts]`).

```bash
meta scripts
```

```text
build     next build            production build
lint      eslint .              lint codebase
test      jest                  run tests
```

Descriptions are inferred from the command itself (e.g. `jest` → "run tests", `next dev` → "start dev server") so scripts are recognizable even without documentation.

## Flags

| Flag | Description |
|---|---|
| `--run <name>` | Execute the named script directly, streaming its output. Exits with the script's own exit code. |

```bash
meta scripts --run lint
```

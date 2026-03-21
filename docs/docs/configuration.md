---
sidebar_position: 3
---

# Configuration

meta needs no configuration file — every option is a flag on the command line, applied globally before the subcommand.

```bash
meta [GLOBAL FLAGS] [COMMAND] [COMMAND FLAGS]
```

## Global Flags

| Flag | Description |
|---|---|
| `--json` | Output results as JSON instead of formatted text. |
| `--no-color` | Disable ANSI color output. meta also respects the `NO_COLOR` environment variable and disables color automatically when output isn't a TTY. |
| `--quiet` | Print a condensed summary instead of full detail — a count for `deps`/`scripts`/`env`/`contributors`, and only failing/warning checks for `health`. |
| `--path` | Run against a different directory instead of the current working directory. |
| `--version`, `-v` | Print the installed version and exit. |
| `--help`, `-h` | Show usage help. |

## Examples

```bash
# JSON output for scripting
meta --json health

# Point at another project
meta --path ../other-project

# Condensed summary, no color, for CI logs
meta --quiet --no-color health
```

`--json` output is unaffected by `--quiet` — JSON is already machine-consumable, so `--quiet` only changes human-readable text output.

# Overview

Running `meta` with no subcommand prints a one-screen summary of the current project.

```bash
meta
```

```text
Project:     meta
Type:        Python
Language:    Python (82%)
Size:        43 files, 23800 lines
Deps:        14 dependencies, 8 dev
Scripts:     13 runnable
Env:         0 expected, 0 missing
Git:         master branch, 0 uncommitted changes
Last commit: 2 hours ago by Krish Suchak
Health:      ✓ 0 issues found
```

## Flags

Overview accepts only the [global flags](../configuration.md) — there's nothing subcommand-specific to configure.

```bash
meta --json
```

```json
{
  "project": "meta",
  "type": "Python",
  "language": "Python",
  "language_percentage": 82.1,
  "files": 43,
  "lines": 23800,
  "dependencies": 14,
  "dev_dependencies": 8,
  "scripts": 13,
  "env_expected": 0,
  "env_missing": 0,
  "git_branch": "master",
  "git_uncommitted": 0,
  "last_commit": "2 hours ago by Krish Suchak",
  "health_issues": 0
}
```

# contributors

Summarize git contributor activity: commits, insertions, deletions, and last-active date per author, sourced from `git log`/`git shortlog`.

```bash
meta contributors
```

```text
Krish Suchak   42 commits
Alice          8 commits
```

## Flags

| Flag | Description |
|---|---|
| `--since <date>` | Only count commits since the given date (any format `git log --since` accepts, e.g. `"30 days ago"`). |
| `--author <name>` | Filter to a single author. |

```bash
meta contributors --since "30 days ago"
meta contributors --author "Krish Suchak"
```

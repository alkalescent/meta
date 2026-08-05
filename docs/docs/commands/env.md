---
title: 🔐 env
---

# 🔐 env

Parse `.env.example` / `.env.sample` / `.env.template` for expected environment variables, then check whether each is set in `.env` or the shell environment, and scan source files for where each variable is actually used.

```bash
meta env
```

```text
DATABASE_URL         missing
NEXTAUTH_SECRET      set
NEXT_PUBLIC_URL      set
DEBUG                optional
```

Detects usage patterns across Node.js (`process.env.VAR`), Python (`os.environ[...]`, `os.getenv(...)`), Rust (`std::env::var(...)`), Ruby (`ENV[...]`), and Go (`os.Getenv(...)`).

## Flags

`env` accepts only the [global flags](../configuration.md).

```bash
meta --quiet env
```

```text
4 expected, 1 missing
```

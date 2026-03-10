#!/bin/bash

set -eu

# Derive the binary name and source module from [project.scripts] in
# pyproject.toml, e.g. `meta = "meta_one.cli:app"` -> NAME=meta,
# MODULE=meta_one. The binary name and the package directory are not
# guaranteed to match (PyPI names may contain dots that aren't valid in
# directory names), so both must come from the same source of truth.
SCRIPT_LINE="$(grep -m1 -E '^[a-zA-Z0-9_.-]+ = "[a-zA-Z0-9_.]+:[a-zA-Z0-9_]+"' pyproject.toml)"
NAME="$(echo "$SCRIPT_LINE" | sed -E 's/^([a-zA-Z0-9_.-]+) = .*/\1/')"
MODULE="$(echo "$SCRIPT_LINE" | sed -E 's/.* = "([a-zA-Z0-9_.]+)\..*/\1/')"

MODE="${MODE:-standalone}"

uv run python -m nuitka \
  --mode="${MODE}" \
  --output-filename="${NAME}" \
  --remove-output \
  --assume-yes-for-downloads \
  "src/${MODULE//./\/}/cli.py"

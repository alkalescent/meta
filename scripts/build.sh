#!/bin/bash

set -eu

# Extract project name from README.md
NAME="$(grep '^#' README.md | head -n 1 | sed -e 's/^# *//' -e 's/ *$//')"

# If CI is true, then use basename of $GITHUB_REPOSITORY as name
if [ "${CI:-false}" = "true" ]; then
  NAME=$(basename "$GITHUB_REPOSITORY")
fi

MODE="${MODE:-standalone}"

uv run python -m nuitka \
  --mode="${MODE}" \
  --output-filename="${NAME}" \
  --remove-output \
  --assume-yes-for-downloads \
  src/${NAME}/cli.py
#!/usr/bin/env bash
# Generate CHANGELOG.md from git history. Stdlib Python only.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")/skills/generate-changelog/scripts" && pwd)"
python3 "$SCRIPT_DIR/changelog.py" "$@"

# generate-changelog

Automatically generate a structured `CHANGELOG.md` from git history. Pure Python stdlib, no deps.

## Quick start (3 steps)
1. `bash changelog.sh --stdout` — preview
2. `bash changelog.sh -o CHANGELOG.md` — write file
3. `pytest -q` — run 16 tests

## Acceptance mapping
- [x] Works via `/generate-changelog` (`SKILL.md`) and `bash changelog.sh`
- [x] Fetches commits since last git tag
- [x] Auto-categorizes `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs formatted `CHANGELOG.md`
- [x] Tested on real repo (see `examples/sample-CHANGELOG.md`)
- [x] Conventional-commit prefix + keyword fallback + `⚠️ **BREAKING**`

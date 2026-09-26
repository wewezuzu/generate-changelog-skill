# Generate Changelog Skill

Claude Code skill that generates a structured CHANGELOG.md from git history.

## What it does
- Finds commits since the last git tag (`git describe --tags --abbrev=0`)
- Auto-categorizes into `Added` / `Fixed` / `Changed` / `Removed`
- Supports Conventional Commits (`feat:`, `fix:`, `refactor:`, ...) with keyword fallback
- Marks `feat!:` and `BREAKING CHANGE:` bodies with `⚠️ **BREAKING**`
- Outputs Keep-a-Changelog style markdown

## Usage
Slash command:
- `/generate-changelog` -> runs `bash changelog.sh`

Manual:
- `bash changelog.sh --stdout`
- `bash changelog.sh -o CHANGELOG.md --version v1.2.0`
- `python3 skills/generate-changelog/scripts/changelog.py --repo . --stdout`

## Files
- `scripts/changelog.py` - pure-Python core, stdlib only
- `changelog.sh` - bash wrapper (repo root)

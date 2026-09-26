#!/usr/bin/env python3
"""Generate structured CHANGELOG.md from git history. Stdlib only."""
import argparse
import re
import subprocess
import sys
from collections import OrderedDict

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]

TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "revert": "Changed",
    "remove": "Removed",
    "removal": "Removed",
    "deprecate": "Removed",
    "delete": "Removed",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<msg>.*)$"
)


def run_git(args, cwd):
    r = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


def get_last_tag(cwd):
    try:
        out = run_git(["describe", "--tags", "--abbrev=0"], cwd).strip()
        return out if out else None
    except RuntimeError:
        return None


def get_commits(from_ref, to_ref, cwd):
    rev = "%s..%s" % (from_ref, to_ref) if from_ref else to_ref
    fmt = "%H%x1f%s%x1f%b%x1e"
    out = run_git(["log", rev, "--pretty=format:%s" % fmt], cwd)
    commits = []
    for record in out.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 2:
            continue
        sha = parts[0].strip()
        subject = parts[1].strip() if len(parts) > 1 else ""
        body = parts[2].strip() if len(parts) > 2 else ""
        if sha:
            commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def classify(subject, body):
    text = ("%s\n%s" % (subject, body)).strip()
    breaking = False
    if "BREAKING CHANGE" in body or "BREAKING-CHANGE" in body:
        breaking = True
    m = CONVENTIONAL_RE.match(subject.strip())
    if m:
        if m.group("breaking"):
            breaking = True
        typ = m.group("type").lower()
        msg = m.group("msg").strip() or subject.strip()
        cat = TYPE_MAP.get(typ, None)
        if cat is None:
            cat = keyword_fallback(text)
        return cat, breaking, msg
    return keyword_fallback(text), breaking, subject.strip()


def keyword_fallback(text):
    low = text.lower()
    if any(k in low for k in ("remove", "delete", "drop ", "deprecat", "uninstall")):
        # avoid "drop " missing end-of-string case
        if any(k.strip() in low for k in ("remove", "delete", "drop", "deprecat", "uninstall")):
            return "Removed"
    if any(k in low for k in ("fix", "bug", "patch", "hotfix", "repair", "resolve")):
        return "Fixed"
    if any(k in low for k in ("add", "feat", "support", "implement", "introduce", "create", "new")):
        return "Added"
    return "Changed"


def build_groups(commits):
    groups = OrderedDict((c, []) for c in CATEGORIES)
    for c in commits:
        cat, breaking, msg = classify(c["subject"], c["body"])
        short = c["sha"][:7]
        entry = {"msg": msg, "sha": short, "breaking": breaking}
        groups[cat].append(entry)
    return groups


def render_markdown(groups, from_ref, to_ref, version="Unreleased"):
    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    rng = "%s...%s" % (from_ref, to_ref) if from_ref else to_ref
    lines.append("## [%s] - %s" % (version, rng))
    lines.append("")
    empty = True
    for cat in CATEGORIES:
        items = groups.get(cat, [])
        if not items:
            continue
        empty = False
        lines.append("### %s" % cat)
        lines.append("")
        for e in items:
            prefix = "- "
            if e["breaking"]:
                prefix += "\u26a0\ufe0f **BREAKING** "
            lines.append("%s%s (%s)" % (prefix, e["msg"], e["sha"]))
        lines.append("")
    if empty:
        lines.append("No notable changes.")
        lines.append("")
    return "\n".join(lines)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("--repo", default=".", help="path to git repo")
    p.add_argument("--from", dest="from_ref", default=None, help="start tag (default: last tag)")
    p.add_argument("--to", dest="to_ref", default="HEAD", help="end ref (default: HEAD)")
    p.add_argument("--version", default="Unreleased", help="version label")
    p.add_argument("-o", "--output", default="CHANGELOG.md", help="output file")
    p.add_argument("--stdout", action="store_true", help="print to stdout instead of file")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    cwd = args.repo
    from_ref = args.from_ref
    if from_ref is None:
        from_ref = get_last_tag(cwd)
    commits = get_commits(from_ref, args.to_ref, cwd)
    groups = build_groups(commits)
    md = render_markdown(groups, from_ref, args.to_ref, args.version)
    if args.stdout:
        sys.stdout.write(md + "\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md + "\n")
        print("wrote %s (%d commits since %s)" % (args.output, len(commits), from_ref or "root"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

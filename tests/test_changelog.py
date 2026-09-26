import os
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "generate-changelog", "scripts"))
from changelog import build_groups, classify, get_commits, get_last_tag, render_markdown


def test_feat_goes_added():
    cat, br, msg = classify("feat: add login", "")
    assert cat == "Added" and not br and msg == "add login"


def test_fix_goes_fixed():
    cat, br, _ = classify("fix: crash on empty input", "")
    assert cat == "Fixed" and not br


def test_refactor_goes_changed():
    cat, _, _ = classify("refactor: split parser", "")
    assert cat == "Changed"


def test_remove_goes_removed():
    cat, _, _ = classify("remove: drop legacy api", "")
    assert cat == "Removed"


def test_breaking_exclamation():
    cat, br, _ = classify("feat!: new config format", "")
    assert cat == "Added" and br


def test_breaking_body():
    cat, br, _ = classify("fix: adjust api", "BREAKING CHANGE: drops v1")
    assert br


def test_scoped_type():
    cat, _, msg = classify("feat(auth): oauth login", "")
    assert cat == "Added" and msg == "oauth login"


def test_keyword_fallback_fixed():
    cat, _, _ = classify("repair null pointer on start", "")
    assert cat == "Fixed"


def test_keyword_fallback_added():
    cat, _, _ = classify("implement csv exporter", "")
    assert cat == "Added"


def test_keyword_fallback_removed():
    cat, _, _ = classify("delete temp files", "")
    assert cat == "Removed"


def test_keyword_fallback_changed():
    cat, _, _ = classify("update readme typo", "")
    assert cat == "Changed"


def test_unknown_type_falls_back():
    cat, _, _ = classify("weird: something happened", "")
    assert cat in ("Added", "Fixed", "Changed", "Removed")


def test_build_groups_order():
    commits = [
        {"sha": "aaaaaaa", "subject": "fix: a", "body": ""},
        {"sha": "bbbbbbb", "subject": "feat: b", "body": ""},
    ]
    g = build_groups(commits)
    assert list(g.keys()) == ["Added", "Fixed", "Changed", "Removed"]
    assert len(g["Added"]) == 1 and len(g["Fixed"]) == 1


def test_render_marks_breaking():
    g = {"Added": [{"msg": "new format", "sha": "abc1234", "breaking": True}],
         "Fixed": [], "Changed": [], "Removed": []}
    md = render_markdown(g, "v1.0.0", "HEAD")
    assert "BREAKING" in md and "new format" in md


def test_render_empty():
    g = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    md = render_markdown(g, None, "HEAD")
    assert "No notable changes" in md


def _git(cwd, *args):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, capture_output=True)


def test_integration_temp_repo():
    with tempfile.TemporaryDirectory() as d:
        _git(d, "init")
        _git(d, "config", "user.email", "t@t.com")
        _git(d, "config", "user.name", "t")
        open(os.path.join(d, "a.txt"), "w").write("1")
        _git(d, "add", ".")
        _git(d, "commit", "-m", "feat: first feature")
        _git(d, "tag", "v0.1.0")
        open(os.path.join(d, "b.txt"), "w").write("2")
        _git(d, "add", ".")
        _git(d, "commit", "-m", "fix: second bugfix")
        assert get_last_tag(d) == "v0.1.0"
        commits = get_commits("v0.1.0", "HEAD", d)
        assert len(commits) == 1
        assert commits[0]["subject"] == "fix: second bugfix"

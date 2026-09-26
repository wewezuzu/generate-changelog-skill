"""Stdlib-only check runner (mirrors tests/test_changelog.py, no pytest needed)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skills", "generate-changelog", "scripts"))
from changelog import build_groups, classify, get_commits, get_last_tag, render_markdown

passed = failed = 0
def check(name, fn):
    global passed, failed
    try:
        fn(); passed += 1; print("PASS %s" % name)
    except AssertionError as e:
        failed += 1; print("FAIL %s: %s" % (name, e))

def t_feat(): assert classify("feat: add login", "")[0] == "Added"
def t_fix(): assert classify("fix: crash on empty", "")[0] == "Fixed"
def t_ref(): assert classify("refactor: split parser", "")[0] == "Changed"
def t_rm(): assert classify("remove: drop legacy api", "")[0] == "Removed"
def t_br1():
    c, b, _ = classify("feat!: new format", ""); assert c == "Added" and b
def t_br2(): assert classify("fix: x", "BREAKING CHANGE: drops v1")[1]
def t_scope(): assert classify("feat(auth): oauth", "")[0] == "Added"
def t_kw_fix(): assert classify("repair null pointer", "")[0] == "Fixed"
def t_kw_add(): assert classify("implement csv exporter", "")[0] == "Added"
def t_kw_rm(): assert classify("delete temp files", "")[0] == "Removed"
def t_kw_ch(): assert classify("update readme typo", "")[0] == "Changed"
def t_order():
    g = build_groups([{"sha": "aaaaaaa", "subject": "fix: a", "body": ""}, {"sha": "bbbbbbb", "subject": "feat: b", "body": ""}])
    assert list(g.keys()) == ["Added", "Fixed", "Changed", "Removed"]
def t_break_md():
    md = render_markdown({"Added": [{"msg": "n", "sha": "abc1234", "breaking": True}], "Fixed": [], "Changed": [], "Removed": []}, "v1", "HEAD")
    assert "BREAKING" in md
def t_empty():
    md = render_markdown({"Added": [], "Fixed": [], "Changed": [], "Removed": []}, None, "HEAD")
    assert "No notable changes" in md
def t_git():
    with tempfile.TemporaryDirectory() as d:
        def g(*a): subprocess.run(["git"] + list(a), cwd=d, check=True, capture_output=True)
        g("init"); g("config", "user.email", "t@t.com"); g("config", "user.name", "t")
        open(os.path.join(d, "a.txt"), "w").write("1"); g("add", "."); g("commit", "-m", "feat: first")
        g("tag", "v0.1.0")
        open(os.path.join(d, "b.txt"), "w").write("2"); g("add", "."); g("commit", "-m", "fix: second")
        assert get_last_tag(d) == "v0.1.0"
        cs = get_commits("v0.1.0", "HEAD", d); assert len(cs) == 1

for i, (n, f) in enumerate([("feat", t_feat), ("fix", t_fix), ("refactor", t_ref), ("remove", t_rm), ("breaking-!", t_br1), ("breaking-body", t_br2), ("scope", t_scope), ("kw-fix", t_kw_fix), ("kw-add", t_kw_add), ("kw-rm", t_kw_rm), ("kw-changed", t_kw_ch), ("order", t_order), ("breaking-md", t_break_md), ("empty", t_empty), ("git-integration", t_git)], 1):
    check("%02d-%s" % (i, n), f)
print("== %d passed, %d failed ==" % (passed, failed))
sys.exit(1 if failed else 0)

"""`pytest_failset.py` is what makes "no regressions" a measurement, so a hole
in its parser silently weakens every such claim in the audit trail.

Two were found by reviewing session 1's work:

1. `^(FAILED|ERROR)\\s+(\\S+)` truncated at the first space, so parametrized ids
   containing spaces collapsed into one set entry. This suite has such ids —
   `test_real_failure_normalizes[asian_high / PDH-asian_high]` and three
   siblings all truncated to `...[asian_high`.
2. Nothing checked that the ids recovered accounted for the run's own totals, so
   the collapse was invisible.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "pytest_failset", REPO_ROOT / "scripts/pytest_failset.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAILSET = _load()

SUMMARY = """FAILED tests/t.py::test_space[a b] - assert False
FAILED tests/t.py::test_space[a c] - assert False
FAILED tests/t.py::test_space[a - d] - assert False
FAILED tests/t.py::TestC::test_plain - AssertionError: nope
ERROR tests/other.py
4 failed, 2 passed, 1 error in 0.03s"""


def test_parametrized_ids_with_spaces_stay_distinct():
    parsed = FAILSET._parse(SUMMARY)
    assert set(parsed["failed"]) == {
        "tests/t.py::test_space[a b]",
        "tests/t.py::test_space[a c]",
        "tests/t.py::test_space[a - d]",   # a param containing the reason separator
        "tests/t.py::TestC::test_plain",
    }
    assert parsed["errored"] == ["tests/other.py"]


def test_a_parse_that_does_not_account_for_the_totals_says_so():
    """The guard that makes any future hole loud rather than silent."""

    truncated = SUMMARY.replace("4 failed", "9 failed")
    parsed = FAILSET._parse(truncated)
    assert parsed["parse_complete"] is False
    assert "recovered" in parsed["parse_note"]


def test_a_complete_parse_is_marked_complete():
    assert FAILSET._parse(SUMMARY)["parse_complete"] is True


@pytest.mark.parametrize(
    "tail,expected",
    [
        ("tests/a.py::test_x - boom", "tests/a.py::test_x"),
        ("tests/a.py::test_x", "tests/a.py::test_x"),
        ("tests/a.py::test_x[1-2] - boom", "tests/a.py::test_x[1-2]"),
        ("tests/a.py::test_x[a [nested] b] - boom", "tests/a.py::test_x[a [nested] b]"),
        ("tests/a.py", "tests/a.py"),
        # A collection error whose MESSAGE contains brackets must not have the
        # message swallowed into the id — this was a real bug in the first
        # version of the bracket-matching rule, caught by the A/B it exists to
        # support ("ERROR tests/test_a1_analyze.py - FileNotFoundError: [Errno 2]").
        ("tests/a.py - FileNotFoundError: [Errno 2] no such file", "tests/a.py"),
        ("tests/a.py::test_x - ValueError: got [1, 2]", "tests/a.py::test_x"),
    ],
)
def test_nodeid_extraction(tail, expected):
    assert FAILSET._extract_nodeid(tail) == expected


def test_the_run_always_passes_continue_on_collection_errors():
    """Without it the suite aborts at collection and executes ZERO tests while
    exiting like a completed run — the single flag that decides whether any of
    this means anything."""

    source = (REPO_ROOT / "scripts/pytest_failset.py").read_text()
    assert '"--continue-on-collection-errors"' in source


def test_coloured_pytest_summary_is_parsed_and_normalised():
    """Presentation escapes and platform separators cannot change a failure identity."""

    output = (
        "\x1b[31mFAILED\x1b[0m .\\tests\\t.py::test_space[a b] - boom\n"
        "\x1b[31mERROR\x1b[0m tests\\other.py\n"
        "\x1b[31m1 failed\x1b[0m, \x1b[32m2 passed\x1b[0m, "
        "\x1b[31m1 error\x1b[0m in 0.03s"
    )
    parsed = FAILSET._parse(output)
    assert parsed["failed"] == ["tests/t.py::test_space[a b]"]
    assert parsed["errored"] == ["tests/other.py"]
    assert parsed["totals"] == {"failed": 1, "passed": 2, "error": 1}
    assert parsed["parse_complete"] is True


def test_pytest_runner_neutralises_parent_colour_environment(monkeypatch):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(cmd=cmd, **kwargs)
        return subprocess.CompletedProcess(cmd, 0, stdout="1 passed in 0.01s\n", stderr="")

    monkeypatch.setenv("FORCE_COLOR", "3")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(FAILSET.subprocess, "run", fake_run)
    output, returncode = FAILSET._run_pytest(["tests/t.py"])
    assert returncode == 0 and "1 passed" in output
    assert "--color=no" in seen["cmd"]
    assert "FORCE_COLOR" not in seen["env"]
    assert seen["env"]["NO_COLOR"] == "1"
    assert seen["env"]["PY_COLORS"] == "0"


# ---------------------------------------------------------------------------------------------
# Session L (B139): a killed run wrote a green-looking baseline.
#
# A full-suite `capture` was terminated by an outer timeout. pytest never printed its counts
# line, so the record landed with `totals: {}`, `failed: []`, `parse_complete: true` and
# `pytest_returncode: -15`. `capture` did exit 2, but the FILE was indistinguishable from a clean
# run and `diff` would have consumed it. Reading an incomplete capture as the baseline makes every
# regression look pre-existing; reading it as the "after" makes every pre-existing failure look
# fixed and prints "No regressions." Both directions are silent, which is the one thing this tool
# exists not to be.
#
# Behavioural tests: drive `cmd_capture`/`cmd_diff` and assert on what they write and return,
# rather than grepping the source for a string (which passes against a wrong implementation).
# ---------------------------------------------------------------------------------------------
import argparse
import json


def _write(tmp_path, name, **fields):
    record = {
        "captured_utc": "2026-07-27T00:00:00Z", "commit": "0" * 40, "commit_subject": "x",
        "dirty": False, "pytest_args": ["tests/"], "pytest_returncode": 0,
        "failed": [], "errored": [], "totals": {"passed": 10}, "parse_complete": True,
        "parse_note": "", "usable_as_baseline": True, "unusable_reasons": [],
    }
    record.update(fields)
    path = tmp_path / name
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def _capture_with(monkeypatch, tmp_path, output_text, returncode):
    monkeypatch.setattr(FAILSET, "_run_pytest", lambda args: (output_text, returncode))
    out = tmp_path / "cap.json"
    rc = FAILSET.cmd_capture(argparse.Namespace(output=str(out), pytest_args=["tests/"]))
    return rc, json.loads(out.read_text(encoding="utf-8"))


def test_a_signal_killed_capture_is_written_but_marked_unusable(monkeypatch, tmp_path):
    """The exact Session L failure: SIGTERM mid-run, no counts line, no failures parsed."""
    rc, record = _capture_with(monkeypatch, tmp_path, "", -15)
    assert rc == 2
    assert record["usable_as_baseline"] is False
    assert any("signal 15" in r for r in record["unusable_reasons"])
    assert any("no outcomes were parsed" in r or "no counts line" in r
               for r in record["unusable_reasons"])


def test_a_killed_run_that_did_print_counts_is_still_unusable(monkeypatch, tmp_path):
    """The more dangerous case: killed AFTER a summary line, so it parses 'successfully'.

    Before the fix this produced non-empty totals, a clean parse and exit 0 — a silently
    truncated baseline. The returncode is the only surviving evidence, so it must be checked.
    """
    text = "FAILED tests/t.py::test_a - boom\n1 failed, 5 passed in 1.00s"
    rc, record = _capture_with(monkeypatch, tmp_path, text, -15)
    assert rc == 2
    assert record["totals"] == {"failed": 1, "passed": 5}      # it did parse
    assert record["failed"] == ["tests/t.py::test_a"]           # and recovered the id
    assert record["usable_as_baseline"] is False                # and is still not a baseline


def test_a_complete_run_stays_usable(monkeypatch, tmp_path):
    rc, record = _capture_with(
        monkeypatch, tmp_path, "FAILED tests/t.py::test_a - boom\n1 failed, 5 passed in 1.00s", 1)
    assert rc == 0
    assert record["usable_as_baseline"] is True
    assert record["unusable_reasons"] == []


def test_diff_refuses_an_unusable_side_in_both_positions(tmp_path, capsys):
    good = _write(tmp_path, "good.json", failed=["tests/t.py::test_a"], totals={"failed": 1})
    bad = _write(tmp_path, "bad.json", usable_as_baseline=False,
                 unusable_reasons=["killed by signal 15"], totals={})
    assert FAILSET.cmd_diff(argparse.Namespace(before=str(bad), after=str(good))) == 2
    assert FAILSET.cmd_diff(argparse.Namespace(before=str(good), after=str(bad))) == 2
    assert "REFUSING" in capsys.readouterr().err


def test_diff_refuses_a_legacy_record_that_predates_the_usability_field(tmp_path):
    """Captures written before this fix carry the same hazard and have no flag to check."""
    good = _write(tmp_path, "good.json", failed=["tests/t.py::test_a"], totals={"failed": 1})
    legacy = _write(tmp_path, "legacy.json", totals={}, pytest_returncode=-15)
    record = json.loads(legacy.read_text(encoding="utf-8"))
    record.pop("usable_as_baseline")
    record.pop("unusable_reasons")
    legacy.write_text(json.dumps(record), encoding="utf-8")
    assert FAILSET.cmd_diff(argparse.Namespace(before=str(legacy), after=str(good))) == 2


def test_diff_still_compares_two_good_captures(tmp_path):
    before = _write(tmp_path, "b.json", failed=["tests/t.py::test_a"], totals={"failed": 1})
    after = _write(tmp_path, "a.json", failed=["tests/t.py::test_a"], totals={"failed": 1})
    assert FAILSET.cmd_diff(argparse.Namespace(before=str(before), after=str(after))) == 0
    regressed = _write(tmp_path, "r.json",
                       failed=["tests/t.py::test_a", "tests/t.py::test_b"],
                       totals={"failed": 2})
    assert FAILSET.cmd_diff(argparse.Namespace(before=str(before), after=str(regressed))) == 1


# ---------------------------------------------------------------------------------------------
# Session M (B145): the same defect, caught at the other end of the pipe.
#
# L marks the artifact at CAPTURE time (`usable_as_baseline` / `unusable_reasons`); M refuses at
# COMPARISON time (`_refuse_if_it_did_not_run`). Kept both at integration (Session O, B180): they
# are complementary, not rival — L's flag cannot protect a capture written before the field
# existed by a tool that has since been replaced, and M's guard cannot stop a bad capture from
# being written and later cited by something other than `diff`.
#
# A capture that executed nothing must be REFUSED, not compared.
#
# Found the hard way on 2026-07-27, by this tool doing it to its own session: a full-suite capture
# was SIGTERMed, wrote `totals: {}` with zero node ids, and `diff` reported
# "694 fixed, 0 REGRESSED, No regressions." An empty failure set is indistinguishable from a
# perfect one to set arithmetic, so the tool whose whole purpose is preventing unearned
# "no regressions" claims produced the most unearned one available.
#
# `capture` already warned and exited 2 — but that exit code is lost through a pipe, and the JSON
# it wrote stayed silently usable. The refusal has to be at the point of comparison, because that
# is where the claim gets made.
# ---------------------------------------------------------------------------------------------

def _rec(**over):
    base = {
        "pytest_args": ["tests/"], "pytest_returncode": 0, "parse_complete": True,
        "parse_note": "", "commit": "a" * 40, "commit_subject": "x", "captured_utc": "2026-07-27T00:00:00Z",
        "failed": ["tests/t.py::a"], "errored": [],
        "totals": {"failed": 1, "passed": 10},
    }
    base.update(over)
    return base


def test_a_capture_that_executed_nothing_is_refused():
    from scripts.pytest_failset import _refuse_if_it_did_not_run
    problem = _refuse_if_it_did_not_run(
        _rec(totals={}, failed=[], pytest_returncode=-15), "after", "/tmp/x.json")
    assert problem and "executed NO tests" in problem


def test_a_capture_killed_by_a_signal_is_refused_even_if_it_got_some_results():
    """A truncated failure set is worse than an empty one: it looks plausible."""
    from scripts.pytest_failset import _refuse_if_it_did_not_run
    problem = _refuse_if_it_did_not_run(
        _rec(pytest_returncode=-15, totals={"failed": 3, "passed": 40}), "after", "/tmp/x.json")
    assert problem and "killed by signal 15" in problem


def test_an_incompletely_parsed_capture_is_refused():
    from scripts.pytest_failset import _refuse_if_it_did_not_run
    problem = _refuse_if_it_did_not_run(
        _rec(parse_complete=False, parse_note="counts did not add up"), "before", "/tmp/x.json")
    assert problem and "did not parse completely" in problem


def test_a_healthy_capture_is_not_refused():
    """Control. Without this the three assertions above would pass against a blanket refusal."""
    from scripts.pytest_failset import _refuse_if_it_did_not_run
    assert _refuse_if_it_did_not_run(_rec(), "before", "/tmp/x.json") is None
    # A run with only skips still executed something and must compare.
    assert _refuse_if_it_did_not_run(
        _rec(failed=[], totals={"skipped": 4}), "before", "/tmp/x.json") is None


# ---------------------------------------------------------------------------------------------
# Session O (B182): the scope guard needed an auditable escape hatch, not a weaker guard.
#
# Session K's A/B captured its baseline with `--ignore=<its own new test file>` rather than checking
# the tree back out, then verified — did not assume — that the ignored file contributes nothing to
# either failure set. That is a sound comparison, and `receipt` refused to emit for it, so K's
# receipt could not carry the embedded block M's rule requires. Two sessions' good work in direct
# tension.
#
# The fix is a justification that is REQUIRED, RECORDED, and RENDERED — so the next reader judges
# the reasoning instead of inheriting a silently-relaxed check. A bare `--force` would have been the
# wrong shape: it removes the guard without leaving evidence of why.
# ---------------------------------------------------------------------------------------------


def _receipt_ns(tmp_path, before, after, **over):
    ns = dict(before=str(before), after=str(after), output=str(tmp_path / "r.md"),
              title="T", scope_difference_justification=None)
    ns.update(over)
    return argparse.Namespace(**ns)


def test_receipt_still_refuses_differing_scopes_by_default(tmp_path, capsys):
    """The guard must not have been weakened — no flag, no receipt."""
    b = _write(tmp_path, "b.json", pytest_args=["tests/", "--ignore=tests/new.py"])
    a = _write(tmp_path, "a.json", pytest_args=["tests/"])
    assert FAILSET.cmd_receipt(_receipt_ns(tmp_path, b, a)) == 2
    assert "REFUSING" in capsys.readouterr().err
    assert not (tmp_path / "r.md").exists(), "a refused receipt must not be written"


def test_a_justified_scope_difference_is_recorded_in_the_embedded_block(tmp_path):
    b = _write(tmp_path, "b.json", pytest_args=["tests/", "--ignore=tests/new.py"])
    a = _write(tmp_path, "a.json", pytest_args=["tests/"])
    why = "the ignored file contributes zero node ids to either failure set; verified, not assumed"
    assert FAILSET.cmd_receipt(_receipt_ns(tmp_path, b, a, scope_difference_justification=why)) == 0
    text = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert why in text, "the justification must be visible in the prose, not only in the JSON"
    block = json.loads(re.search(r"```json\s*(\{.*?\})\s*```", text, re.S).group(1))
    assert block["scope_difference"]["justification"] == why
    assert block["scope_difference"]["before"] == ["tests/", "--ignore=tests/new.py"]


def test_an_unjustified_receipt_carries_no_scope_difference_key(tmp_path):
    """Control: the key appears only when there is something to declare."""
    b = _write(tmp_path, "b.json")
    a = _write(tmp_path, "a.json")
    assert FAILSET.cmd_receipt(_receipt_ns(tmp_path, b, a)) == 0
    block = json.loads(
        re.search(r"```json\s*(\{.*?\})\s*```", (tmp_path / "r.md").read_text(), re.S).group(1))
    assert "scope_difference" not in block


# ---------------------------------------------------------------------------
# `scope` -- blast radius. Session AT.
#
# These drive `cmd_scope` with a stubbed diff and a stubbed index, so they test the
# DECISION rather than this repository's current file layout. A scoping bug is
# expensive in one direction only: under-scoping produces a false "no regressions"
# that nothing downstream can detect, which is the exact claim this whole module
# exists to make un-fakeable.
# ---------------------------------------------------------------------------

class _ScopeNS:
    def __init__(self, tmp_path, **kw):
        self.base = "BASE"
        self.head = "HEAD"
        self.include_worktree = False
        self.standing = None
        self.output = str(tmp_path / "scope.json")
        for k, v in kw.items():
            setattr(self, k, v)


def _scope(monkeypatch, tmp_path, changed, by_module=None, by_literal=None, **kw):
    monkeypatch.setattr(FAILSET, "_changed_paths", lambda *a, **k: sorted(changed))
    monkeypatch.setattr(FAILSET, "_build_index", lambda: (by_module or {}, by_literal or {}))
    ns = _ScopeNS(tmp_path, **kw)
    code = FAILSET.cmd_scope(ns)
    return code, json.loads(Path(ns.output).read_text(encoding="utf-8"))


def test_a_src_change_scopes_to_the_tests_that_reach_it(monkeypatch, tmp_path):
    code, rec = _scope(
        monkeypatch, tmp_path, ["src/components/thing.py"],
        by_module={"src.components.thing": {"tests/test_thing.py", "tests/test_other.py"}})
    assert code == 0
    assert rec["full_suite"] is False
    assert rec["pytest_args"] == ["tests/test_other.py", "tests/test_thing.py"]


def test_a_conftest_change_escalates_to_the_full_suite(monkeypatch, tmp_path):
    """No import edge to follow: a conftest can change collection for anything."""
    code, rec = _scope(monkeypatch, tmp_path, ["tests/conftest.py", "src/components/thing.py"],
                       by_module={"src.components.thing": {"tests/test_thing.py"}})
    assert rec["full_suite"] is True
    assert rec["pytest_args"] == ["tests/"]
    assert "escape list" in rec["reason"]


def test_a_config_change_escalates_to_the_full_suite(monkeypatch, tmp_path):
    _, rec = _scope(monkeypatch, tmp_path, ["config/agent_config.yaml"])
    assert rec["full_suite"] is True


def test_deleting_a_test_file_escalates_to_the_full_suite(monkeypatch, tmp_path):
    """A deleted path cannot be passed to pytest on the after side, so a scoped A/B
    would report the removal as neither fixed nor regressed -- silently."""
    _, rec = _scope(monkeypatch, tmp_path, ["tests/test_gone.py"])
    assert rec["full_suite"] is True
    assert rec["deleted_tests"] == ["tests/test_gone.py"]
    assert "DELETES" in rec["reason"]


def test_an_unrecognised_path_escalates_rather_than_being_ignored(monkeypatch, tmp_path):
    """Fail-safe: `scope` must never silently decide an unknown path is harmless."""
    _, rec = _scope(monkeypatch, tmp_path, ["scripts/run_book_supervisor.ps1"])
    assert rec["full_suite"] is True
    assert rec["unresolved"] == ["scripts/run_book_supervisor.ps1"]


def test_an_artifact_named_by_a_test_literal_pulls_that_test_in(monkeypatch, tmp_path):
    """A test asserting on a research ledger has no import edge to it. Changing the
    ledger must still run the test."""
    ledger = "research/operations/route/LEDGER.jsonl"
    _, rec = _scope(monkeypatch, tmp_path, [ledger],
                    by_literal={ledger: {"tests/test_route_artifacts.py"}})
    assert rec["full_suite"] is False
    assert rec["pytest_args"] == ["tests/test_route_artifacts.py"]
    assert rec["selected_because"]["tests/test_route_artifacts.py"] == [ledger]


def test_a_repo_root_file_joins_by_basename(monkeypatch, tmp_path):
    """`run_book.py` is loaded by spec_from_file_location, so there is no import edge
    and no directory prefix -- basename is the only join available."""
    _, rec = _scope(monkeypatch, tmp_path, ["run_book.py"],
                    by_literal={"run_book.py": {"tests/test_run_book_importable.py"}})
    assert rec["pytest_args"] == ["tests/test_run_book_importable.py"]


def test_an_all_inert_diff_reaches_no_test_and_owes_no_ab(monkeypatch, tmp_path):
    """The headline case. A docs-only branch must not run 11,400 tests -- and must not
    produce an empty capture either, because two empty failure sets compare as perfect."""
    code, rec = _scope(monkeypatch, tmp_path, ["docs/audits/x/RESULT.md", ".context/note.md"])
    assert code == 3
    assert rec["no_tests_reached"] is True
    assert rec["full_suite"] is False
    assert rec["pytest_args"] == []
    assert "NO TEST REACHED" in rec["reason"]


def test_capture_refuses_a_scope_that_reached_no_test(monkeypatch, tmp_path, capsys):
    code, rec = _scope(monkeypatch, tmp_path, ["docs/audits/x/RESULT.md"])
    assert rec["no_tests_reached"] is True
    ns = argparse.Namespace(output=str(tmp_path / "cap.json"),
                            scope=str(tmp_path / "scope.json"), pytest_args=[])
    assert FAILSET.cmd_capture(ns) == 2
    assert "REFUSING" in capsys.readouterr().err
    assert not (tmp_path / "cap.json").exists()


def test_the_standing_failure_set_is_unioned_in(monkeypatch, tmp_path):
    """A change can fix or break a pre-existing failure in a file it does not import.
    Scoping must not make that invisible."""
    standing = tmp_path / "standing.json"
    standing.write_text(json.dumps({
        "failed": ["tests/scripts/test_pytest_failset_parsing.py::test_x"], "errored": []}))
    _, rec = _scope(monkeypatch, tmp_path, ["src/components/thing.py"],
                    by_module={"src.components.thing": {"tests/test_thing.py"}},
                    standing=str(standing))
    assert "tests/scripts/test_pytest_failset_parsing.py" in rec["pytest_args"]
    assert "tests/test_thing.py" in rec["pytest_args"]


def test_capture_refuses_scope_plus_explicit_args(tmp_path, capsys):
    """Both sides of an A/B must run the same args; an override defeats the point."""
    scope = tmp_path / "scope.json"
    scope.write_text(json.dumps({"pytest_args": ["tests/a.py"], "reason": "r",
                                 "no_tests_reached": False}))
    ns = argparse.Namespace(output=str(tmp_path / "cap.json"), scope=str(scope),
                            pytest_args=["tests/b.py"])
    assert FAILSET.cmd_capture(ns) == 2
    assert "REFUSING" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------------
# Orchestrator, wave-7 train merge: the committed baseline. The literal `baseline` resolves to
# the capture the orchestrator commits once per merge train, so no session ever re-captures the
# before side of an A/B (16 re-captures produced 5 false REGRESSION reports, all load flakes).


def test_the_literal_baseline_resolves_to_the_committed_capture(monkeypatch, tmp_path):
    committed = tmp_path / "FAILSET_BASELINE_MAIN.json"
    committed.write_text(json.dumps({
        "failed": ["tests/t.py::test_a"], "errored": [], "totals": {"failed": 1},
        "usable_as_baseline": True, "unusable_reasons": [],
    }), encoding="utf-8")
    monkeypatch.setattr(FAILSET, "BASELINE_CAPTURE", committed)
    assert FAILSET._resolve_capture_arg("baseline") == str(committed)
    # Any other string passes through untouched — including paths that happen to contain it.
    assert FAILSET._resolve_capture_arg("my_baseline.json") == "my_baseline.json"


def test_diff_against_the_missing_baseline_refuses_loudly(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(FAILSET, "BASELINE_CAPTURE", tmp_path / "absent.json")
    with pytest.raises(SystemExit) as exc:
        FAILSET._resolve_capture_arg("baseline")
    assert exc.value.code == 2
    assert "REFUSING" in capsys.readouterr().err


def test_diff_accepts_the_baseline_literal_end_to_end(monkeypatch, tmp_path):
    committed = _write(tmp_path, "FAILSET_BASELINE_MAIN.json",
                       failed=["tests/t.py::test_a"], totals={"failed": 1})
    monkeypatch.setattr(FAILSET, "BASELINE_CAPTURE", committed)
    same = _write(tmp_path, "same.json", failed=["tests/t.py::test_a"], totals={"failed": 1})
    assert FAILSET.cmd_diff(argparse.Namespace(before="baseline", after=str(same))) == 0
    regressed = _write(tmp_path, "worse.json",
                       failed=["tests/t.py::test_a", "tests/t.py::test_b"],
                       totals={"failed": 2})
    assert FAILSET.cmd_diff(argparse.Namespace(before="baseline", after=str(regressed))) == 1

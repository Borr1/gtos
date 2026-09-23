#!/usr/bin/env python3
"""Capture and diff pytest failure sets, so "no regressions" is a measurement.

`CLAUDE.md` §6 requires an A/B against the parent commit before any "no regressions"
claim. That is impractical by eye here: the suite at 4d2407c77 is 692 failed / 9482
passed / 39 errors and takes ~10.5 minutes, and both prior audits reported "11
failures" because they were measuring an ~885-test subset. This tool makes the
comparison mechanical.

It also pins the one flag that decides whether the run means anything at all:
without ``--continue-on-collection-errors`` the suite aborts at collection with 12
errors and executes **zero** tests, while still exiting like a completed run.

Usage
-----
  # record a baseline (optionally scoped to a subset)
  python3 scripts/pytest_failset.py capture -o baseline.json
  python3 scripts/pytest_failset.py capture -o book.json -- tests/ultimate_book

  # after a change, record again and diff
  python3 scripts/pytest_failset.py capture -o after.json
  python3 scripts/pytest_failset.py diff baseline.json after.json

`diff` exits 1 if any test regressed (passing/absent -> failing), 0 otherwise.
Newly-fixed tests never fail the diff; they are reported.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# pytest short-summary lines: "FAILED tests/x.py::test_y - AssertionError: ..."
# Collection errors arrive as "ERROR tests/x.py" with no ::test part.
_SUMMARY = re.compile(r"^(FAILED|ERROR)\s+(.+)$")
_COUNTS = re.compile(r"(\d+)\s+(passed|failed|skipped|error|errors|xfailed|xpassed|deselected)")
# CSI/OSC escapes emitted when a caller exports FORCE_COLOR.  A wave-20 full
# capture recovered zero node ids from otherwise valid ``\x1b[31mFAILED\x1b[0m``
# lines.  The mismatch guard made that failure loud, but a verifier should be
# robust to presentation bytes in the first place.
_ANSI = re.compile(
    r"(?:\x1B\][^\x07]*(?:\x07|\x1B\\)|\x1B\[[0-?]*[ -/]*[@-~])"
)


def _strip_ansi(text: str) -> str:
    """Remove terminal presentation escapes without touching node-id bytes."""

    return _ANSI.sub("", text)


def _run_pytest(pytest_args: list[str]) -> tuple[str, int]:
    cmd = [
        sys.executable, "-m", "pytest",
        "-q", "--tb=no", "--color=no", "-p", "no:cacheprovider",
        # Without this the run aborts at collection and measures nothing.
        "--continue-on-collection-errors",
        *(pytest_args or ["tests/"]),
    ]
    print(f"$ {' '.join(cmd)}", file=sys.stderr, flush=True)
    env = os.environ.copy()
    # Keep the capture deterministic even when the parent shell forces colour.
    # ``--color=no`` is the pytest-side authority; these also cover plugins and
    # libraries which colour their own summary text.
    env.pop("FORCE_COLOR", None)
    env["NO_COLOR"] = "1"
    env["PY_COLORS"] = "0"
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env)
    return proc.stdout + proc.stderr, proc.returncode


def _normalise_nodeid(nodeid: str) -> str:
    """Canonical failure identity across terminals and host path separators.

    Only the path prefix is slash-normalised; parameter ids are semantic bytes
    and may legitimately contain backslashes.  NFC prevents visually identical
    Unicode parameter ids from comparing as different strings.
    """

    nodeid = unicodedata.normalize("NFC", _strip_ansi(nodeid.strip()))
    path, marker, suffix = nodeid.partition("::")
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path + (marker + suffix if marker else "")


def _extract_nodeid(rest: str) -> str:
    r"""Pull the node id out of a short-summary line's tail.

    The old rule was `(\S+)`, which truncated at the first space. A
    parametrized id like `test_x[asian_high / PDH-asian_high]` contains spaces,
    so several distinct parametrizations collapsed into ONE set entry and the
    failure set silently under-recorded. This suite has parametrized ids with
    spaces, so that was not hypothetical.

    pytest emits `<nodeid> - <reason>`. Bracket-matching first, because a
    parameter value may itself contain " - " and the brackets are balanced.
    """

    separator = rest.find(" - ")
    bracket = rest.find("[")
    # Bracket-match only when the bracket is part of the id, i.e. it opens
    # BEFORE the reason separator. Otherwise a collection error whose message
    # happens to contain brackets ("ERROR tests/x.py - FileNotFoundError:
    # [Errno 2] ...") swallows the message into the id.
    if bracket != -1 and (separator == -1 or bracket < separator):
        depth = 0
        for index, char in enumerate(rest):
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return _normalise_nodeid(rest[: index + 1])
    head = rest if separator == -1 else rest[:separator]
    return _normalise_nodeid(head.split()[0] if head.split() else head)


def _parse(output: str) -> dict:
    output = _strip_ansi(output)
    failed: set[str] = set()
    errored: set[str] = set()
    for line in output.splitlines():
        m = _SUMMARY.match(line)
        if not m:
            continue
        kind, rest = m.group(1), m.group(2)
        (failed if kind == "FAILED" else errored).add(_extract_nodeid(rest))

    totals: dict[str, int] = {}
    for line in reversed(output.splitlines()):
        found = _COUNTS.findall(line)
        if found and ("passed" in line or "failed" in line or "error" in line):
            for count, label in found:
                totals[label.rstrip("s") if label != "passed" else "passed"] = int(count)
            break
    # Make any future parsing hole LOUD instead of silent. If the ids we
    # recovered do not account for the run's own totals, every downstream
    # "no regressions" claim is measuring an incomplete set.
    parse_complete = True
    parse_note = ""
    expected = totals.get("failed", 0) + totals.get("error", 0)
    recovered = len(failed) + len(errored)
    if totals and recovered != expected:
        parse_complete = False
        parse_note = (
            f"recovered {recovered} ids but pytest reported {expected} "
            f"(failed={totals.get('failed', 0)}, error={totals.get('error', 0)}); "
            "ids collided or a summary line was not matched"
        )

    return {
        "failed": sorted(failed),
        "errored": sorted(errored),
        "totals": totals,
        "parse_complete": parse_complete,
        "parse_note": parse_note,
    }


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


#: The committed baseline: main's full-suite failure set, captured once per merge train by the
#: orchestrator and committed alongside the receipts. Passing the literal ``baseline`` as the
#: `before` side of `diff`/`receipt` resolves to this path, so nobody ever re-captures the before
#: side of an A/B — that re-capture cost ~10.5 minutes per session and produced five false
#: REGRESSION reports (all load flakes) across the 16 runs that retired it (wave-7 agreement §2).
BASELINE_CAPTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/audits/fable5-vision-audit-20260725/receipts/FAILSET_BASELINE_MAIN.json"
)


def _resolve_capture_arg(arg: str) -> str:
    """Resolve the literal ``baseline`` to the committed baseline capture."""
    if arg != "baseline":
        return arg
    if not BASELINE_CAPTURE.is_file():
        print(
            f"REFUSING: no committed baseline at {BASELINE_CAPTURE}.\n"
            "The orchestrator commits it once per merge train; if it is genuinely absent, "
            "capture one and commit it rather than diffing against a private re-capture.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return str(BASELINE_CAPTURE)


def cmd_capture(ns: argparse.Namespace) -> int:
    scope_record = None
    pytest_args = ns.pytest_args
    if getattr(ns, "scope", None):
        scope_record = json.loads(Path(ns.scope).read_text(encoding="utf-8"))
        if pytest_args:
            print("REFUSING: --scope and explicit pytest args together. The scope file exists so "
                  "both sides of the A/B run the SAME args; overriding it defeats that.",
                  file=sys.stderr)
            return 2
        if scope_record.get("no_tests_reached"):
            print("REFUSING: this scope reached no test at all. An A/B over zero tests compares "
                  "two empty failure sets and reports 'no regressions' unconditionally.\n  "
                  + scope_record["reason"], file=sys.stderr)
            return 2
        pytest_args = scope_record["pytest_args"]
        print(f"scope: {scope_record['reason']}", file=sys.stderr)
    output, returncode = _run_pytest(pytest_args)
    parsed = _parse(output)
    record = {
        "captured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": _git("rev-parse", "HEAD"),
        "commit_subject": _git("log", "-1", "--format=%s"),
        "dirty": bool(_git("status", "--porcelain")),
        "pytest_args": pytest_args or ["tests/"],
        "pytest_returncode": returncode,
        **parsed,
    }
    if scope_record is not None:
        record["scope"] = {k: scope_record[k] for k in
                           ("base", "head", "full_suite", "reason", "changed_paths")}
    # A capture that did not finish is not a baseline, and the artifact must say so on its face.
    # Session L hit this: a full-suite capture was killed by an outer timeout (returncode -15,
    # i.e. SIGTERM), pytest never printed a summary line, and the tool wrote a well-formed record
    # with `totals: {}`, `failed: []`, `parse_complete: true`. `capture` did exit 2 -- but the
    # FILE on disk was indistinguishable from a clean green run, and `diff` would have consumed it
    # happily. The exit code is not the artifact; the artifact is the artifact.
    unusable_reasons: list[str] = []
    if returncode < 0:
        unusable_reasons.append(
            f"pytest was killed by signal {-returncode} (returncode {returncode}); the run did not "
            "finish, so this failure set is a truncation of an unknown fraction of the suite"
        )
    if not parsed["totals"]:
        unusable_reasons.append(
            "pytest printed no counts line, so no outcomes were parsed and the empty failure set "
            "below is an absence of measurement, not an absence of failures"
        )
    if not parsed.get("parse_complete", True):
        unusable_reasons.append(parsed.get("parse_note") or "parse incomplete")
    record["usable_as_baseline"] = not unusable_reasons
    record["unusable_reasons"] = unusable_reasons

    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    t = record["totals"]
    print(
        f"captured {len(record['failed'])} failed / {len(record['errored'])} errored"
        f" (totals: {t}) -> {out}"
    )
    for reason in unusable_reasons:
        print(f"WARNING: {reason}", file=sys.stderr)
    if unusable_reasons:
        print("marked usable_as_baseline=false; `diff` will refuse it.", file=sys.stderr)
        return 2
    return 0


def _refuse_if_it_did_not_run(record: dict, label: str, path: str) -> str | None:
    """Reject a capture that executed nothing, instead of comparing against it.

    Found the hard way on 2026-07-27: a full-suite capture was SIGTERMed
    (``pytest_returncode == -15``), wrote ``totals: {}`` with zero node ids, and ``diff``
    cheerfully reported **"694 fixed, 0 REGRESSED, No regressions."** An empty failure set is
    indistinguishable from a perfect one to set arithmetic — so the tool whose entire purpose is
    preventing unearned "no regressions" claims produced the most unearned one possible.

    ``capture`` already warns and exits 2, but that exit code is lost through a pipe (``| tail``),
    and the JSON it writes is silently usable afterwards. The refusal has to live here, at the point
    of comparison, because that is where the claim is made.
    """
    totals = record.get("totals") or {}
    executed = sum(int(totals.get(k, 0)) for k in
                   ("passed", "failed", "error", "errors", "skipped", "xfailed", "xpassed"))
    rc = record.get("pytest_returncode")
    if executed == 0:
        return (f"REFUSING: the {label} capture ({path}) executed NO tests "
                f"(totals={totals!r}, pytest_returncode={rc}). "
                f"An empty failure set compares as a perfect one. Re-capture it.")
    if isinstance(rc, int) and rc < 0:
        return (f"REFUSING: the {label} capture ({path}) was killed by signal {-rc} "
                f"(pytest_returncode={rc}), so its failure set is truncated, not complete. "
                f"Re-capture it.")
    if not record.get("parse_complete", True):
        return (f"REFUSING: the {label} capture ({path}) did not parse completely: "
                f"{record.get('parse_note')!r}")
    return None


def _both_captures_ran(before: dict, after: dict, bpath: str, apath: str) -> bool:
    problems = [p for p in (_refuse_if_it_did_not_run(before, "before", bpath),
                            _refuse_if_it_did_not_run(after, "after", apath)) if p]
    for p in problems:
        print(p, file=sys.stderr)
    return not problems


def cmd_diff(ns: argparse.Namespace) -> int:
    ns.before = _resolve_capture_arg(ns.before)
    ns.after = _resolve_capture_arg(ns.after)
    before = json.loads(Path(ns.before).read_text(encoding="utf-8"))
    after = json.loads(Path(ns.after).read_text(encoding="utf-8"))

    if not _both_captures_ran(before, after, ns.before, ns.after):
        return 2

    if before.get("pytest_args") != after.get("pytest_args"):
        print(
            f"REFUSING: scopes differ.\n  before: {before.get('pytest_args')}"
            f"\n  after : {after.get('pytest_args')}\n"
            "An A/B across different scopes is not a comparison.",
            file=sys.stderr,
        )
        return 2

    # Refuse a side that recorded itself as not a measurement. Reading an incomplete capture as a
    # baseline makes every regression look pre-existing; reading one as the "after" makes every
    # pre-existing failure look fixed and reports "No regressions." Both directions are silent.
    for side, rec, path in (("before", before, ns.before), ("after", after, ns.after)):
        if rec.get("usable_as_baseline") is False:
            print(
                f"REFUSING: {side} ({path}) is marked unusable:\n  "
                + "\n  ".join(rec.get("unusable_reasons") or ["(no reason recorded)"]),
                file=sys.stderr,
            )
            return 2
        # Captures written before `usable_as_baseline` existed carry the same hazards; detect them
        # from the fields they do have rather than trusting their age.
        if "usable_as_baseline" not in rec:
            legacy: list[str] = []
            if (rec.get("pytest_returncode") or 0) < 0:
                legacy.append(f"pytest_returncode {rec['pytest_returncode']} (killed by signal)")
            if not rec.get("totals"):
                legacy.append("no totals parsed")
            if not rec.get("parse_complete", True):
                legacy.append(rec.get("parse_note") or "parse incomplete")
            if legacy:
                print(
                    f"REFUSING: {side} ({path}) predates the usability field and looks incomplete:\n  "
                    + "\n  ".join(legacy),
                    file=sys.stderr,
                )
                return 2

    b_bad = set(before["failed"]) | set(before["errored"])
    a_bad = set(after["failed"]) | set(after["errored"])
    regressed = sorted(a_bad - b_bad)
    fixed = sorted(b_bad - a_bad)

    print(f"before {before['commit'][:9]} ({before['commit_subject']!r}): {len(b_bad)} bad")
    print(f"after  {after['commit'][:9]} ({after['commit_subject']!r}): {len(a_bad)} bad")
    print(f"unchanged: {len(b_bad & a_bad)}   fixed: {len(fixed)}   REGRESSED: {len(regressed)}")

    if fixed:
        print("\nFIXED:")
        for t in fixed:
            print(f"  + {t}")
    real, flaky = _partition_regressions(regressed)
    if flaky:
        print("\nLOAD-FLAKE (registered, not a regression — see KNOWN_LOAD_FLAKES for the evidence):")
        for t in flaky:
            print(f"  ~ {t}\n      {KNOWN_LOAD_FLAKES[t]}")
    if real:
        print("\nREGRESSED (this is what blocks a 'no regressions' claim):")
        for t in real:
            print(f"  - {t}")
        return 1
    print("\nNo regressions." + (" (load flakes above are registered and verified.)" if flaky else ""))
    return 0


#: Fence marker for the machine-readable block every committed A/B receipt must carry.
RECEIPT_FENCE = "gtos-ab-receipt-v1"


def cmd_receipt(ns: argparse.Namespace) -> int:
    """Emit a COMMITTABLE markdown receipt from two capture JSONs.

    Standing rule, from `receipts/WAVE2_INTEGRATION_AB.md`: **an A/B that is not committed did not
    happen.** The wave-2 A/B was genuinely run and lived in a scratchpad, so to the next reader it did
    not exist — and the third review's adversarial pass correctly recorded that as a missing receipt.

    The rule was prose. This is the mechanism, and the design point is that the receipt EMBEDS its two
    captures rather than pointing at them. A receipt that references `/tmp/before.json` is exactly as
    unverifiable as no receipt at all, because the file it names is gone by the time anyone reads it.
    `tests/test_ab_receipts_are_self_contained.py` enforces that every receipt in the tree carries the
    embedded block, so a prose receipt saying "we ran it and it was clean" cannot pass as one.
    """
    ns.before = _resolve_capture_arg(ns.before)
    ns.after = _resolve_capture_arg(ns.after)
    before = json.loads(Path(ns.before).read_text(encoding="utf-8"))
    after = json.loads(Path(ns.after).read_text(encoding="utf-8"))
    if not _both_captures_ran(before, after, ns.before, ns.after):
        return 2
    scope_justification = getattr(ns, "scope_difference_justification", None)
    if before.get("pytest_args") != after.get("pytest_args") and not scope_justification:
        print("REFUSING: scopes differ; an A/B across different scopes is not a comparison.",
              file=sys.stderr)
        print(f"  before: {before.get('pytest_args')!r}\n  after : {after.get('pytest_args')!r}",
              file=sys.stderr)
        print("If the difference is provably immaterial to the failure set, say why with "
              "--scope-difference-justification. The reason is recorded IN the receipt, so the "
              "next reader judges it rather than inheriting it.", file=sys.stderr)
        return 2

    b_bad = sorted(set(before["failed"]) | set(before["errored"]))
    a_bad = sorted(set(after["failed"]) | set(after["errored"]))
    regressed = sorted(set(a_bad) - set(b_bad))
    fixed = sorted(set(b_bad) - set(a_bad))
    embedded = {
        "schema": RECEIPT_FENCE,
        "scope": before.get("pytest_args"),
        "before": {k: before.get(k) for k in
                   ("commit", "commit_subject", "captured_utc", "dirty", "totals")},
        "after": {k: after.get(k) for k in
                  ("commit", "commit_subject", "captured_utc", "dirty", "totals")},
        "bad_before": len(b_bad), "bad_after": len(a_bad),
        "unchanged": len(set(b_bad) & set(a_bad)),
        "fixed": fixed, "regressed": regressed,
        # The full sets, so the receipt is re-derivable without the capture files.
        "bad_before_nodeids": b_bad, "bad_after_nodeids": a_bad,
    }
    if scope_justification:
        # Recorded, never silent. A scope difference that is merely ASSERTED immaterial is the same
        # defect class as an uncommitted A/B: the claim outlives the evidence for it.
        embedded["scope_difference"] = {
            "before": before.get("pytest_args"), "after": after.get("pytest_args"),
            "justification": scope_justification,
        }
    lines = [
        f"# {ns.title}", "",
        f"**{len(b_bad)} bad → {len(a_bad)} bad · {len(fixed)} fixed · "
        f"**{len(regressed)} REGRESSED**." if regressed else
        f"**{len(b_bad)} bad → {len(a_bad)} bad · {len(fixed)} fixed · 0 regressed. No regressions.**",
        "",
        "Compared by **failure set**, not by count — counts are not portable across worktrees.", "",
        "| | before | after |", "|---|---|---|",
        f"| commit | `{before['commit'][:9]}` | `{after['commit'][:9]}` |",
        f"| captured (UTC) | {before.get('captured_utc')} | {after.get('captured_utc')} |",
        f"| working tree | {'dirty' if before.get('dirty') else 'clean'} | "
        f"{'dirty' if after.get('dirty') else 'clean'} |",
        f"| failed | {before['totals'].get('failed', 0)} | {after['totals'].get('failed', 0)} |",
        f"| errored | {before['totals'].get('error', 0)} | {after['totals'].get('error', 0)} |",
        f"| **bad** | **{len(b_bad)}** | **{len(a_bad)}** |",
        f"| passed | {before['totals'].get('passed', 0)} | {after['totals'].get('passed', 0)} |",
        f"| skipped | {before['totals'].get('skipped', 0)} | {after['totals'].get('skipped', 0)} |",
        "",
    ]
    if regressed:
        lines += ["## REGRESSED", ""] + [f"- `{t}`" for t in regressed] + [""]
    if fixed:
        lines += [f"## Fixed ({len(fixed)})", ""] + [f"- `{t}`" for t in fixed] + [""]
    if scope_justification:
        lines += [
            "## Scope difference — declared, not hidden", "",
            f"- before: `{before.get('pytest_args')}`",
            f"- after : `{after.get('pytest_args')}`", "",
            f"**Why this is still a comparison:** {scope_justification}", "",
        ]
    lines += [
        "## Embedded captures", "",
        "Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as",
        "no receipt at all, because that file is gone by the time anyone reads this.", "",
        "```json", json.dumps(embedded, indent=1), "```", "",
    ]
    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"receipt -> {out}  ({len(b_bad)} -> {len(a_bad)} bad, {len(regressed)} regressed)")
    return 1 if regressed else 0


#: Tests that fail under concurrent load and pass in isolation. Registered because the cost of
#: NOT registering them is measured: across 16 A/B runs on 2026-07-29, five reported a REGRESSION
#: and **all five were one of these**. Zero real regressions were caught by a full-suite A/B in
#: that period; the two genuine catches came from reading the failure list, not the count. Each
#: false alarm cost 5-15 minutes to disprove by re-running at both HEAD and base.
#:
#: An entry here does NOT hide the test. It is still reported, under LOAD-FLAKE rather than
#: REGRESSED, and `diff` still exits 1 for anything unregistered. The discipline that matters is
#: unchanged: a name only lands here after it has been shown to fail at the BASE commit too, or to
#: pass in isolation at the commit that "broke" it. Never add one to make a receipt look clean.
KNOWN_LOAD_FLAKES: dict[str, str] = {
    "tests/test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration":
        "Session Z A/B. Verified: fails 1 of 3 in isolation at Z's HEAD and 1 of 2 at base 82f8e02dc.",
    "tests/test_replay_columnar_source.py::test_verification_retains_no_rows":
        "Session Y A/B. Verified: 3/3 pass in isolation at both HEAD and base; whole file 29/29 at both.",
    "tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment":
        "Session W certification. Reported as FIXED, not regressed; same load sensitivity, asserts a "
        "threaded flush after a fixed sleep.",
    "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict":
        "Wave-18 train A/B (2026-08-01). Verified: 1/1 in isolation and whole file 43/43 at the same "
        "commit (bca8c4466) whose full-suite run reported it failed; no wave-18 session touched "
        "cuts.py or this test. Same load-sensitivity class as the two entries above.",
}


def _partition_regressions(regressed: list) -> tuple:
    """Split into (real, load_flake) so a known-flaky name cannot be reported as a regression."""
    real = [t for t in regressed if t not in KNOWN_LOAD_FLAKES]
    flaky = [t for t in regressed if t in KNOWN_LOAD_FLAKES]
    return real, flaky


# ---------------------------------------------------------------------------
# Blast-radius scoping
#
# The full suite is ~11,400 tests and ~10.5 minutes, and it is run on both sides of
# every A/B. Most branches cannot possibly affect most of it: a docs-and-new-tests
# branch has no import edge into 99% of the suite. `scope` computes what a diff can
# actually reach and emits pytest args for it, so the same comparison costs a
# fraction of the time.
#
# Two properties it is built to keep:
#
#   * **Fail-safe.** Anything the mapper cannot resolve -- a conftest, a config file,
#     an unrecognised path -- escalates the whole run to `tests/`. Under-scoping is a
#     silent false "no regressions"; over-scoping only costs minutes.
#   * **Declared.** The scope and the reason for it are written into the capture and
#     surface in the receipt, so a reader judges the scope instead of inheriting it.
#
# It does NOT replace the full-suite A/B for every branch. Two cases still need
# `tests/`: a branch that DELETES tests (a deleted path cannot be passed to pytest on
# the after side, so removals under-report as neither fixed nor regressed), and any
# branch touching the escape list below.
# ---------------------------------------------------------------------------

#: A change to one of these can alter collection, fixtures, dependency resolution or
#: interpreter behaviour for tests that import none of the changed code. There is no
#: import edge to follow, so scoping is abandoned and the full suite runs.
_SCOPE_ESCAPES = (
    "conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "Makefile",
    "requirements", ".gitattributes", ".github/", "config/",
)

#: Trees with no import edge into the suite. A change here is still matched against
#: every test file's string literals before it is dismissed -- a test that asserts on
#: `research/.../LEDGER.jsonl` must run when that ledger changes, even though nothing
#: imports it.
_INERT_PREFIXES = (
    "docs/", ".context/", "research/", "shadow_logs/", "pipeline_state/", "data/",
    "operations/", "prompts/", "mt5_ea/", "agents/", "skills/", ".claude/", ".codex/",
    "knowledge_base/", "validation_integrity/receipts/",
)

_IMPORT_LINE = re.compile(
    r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import\s+(.+)$|import\s+([A-Za-z_][\w.]*))")
_PATH_LITERAL = re.compile(r"['\"]((?:src|scripts|tests|research|config|docs|data|operations)/[^'\"\s]+)['\"]")
#: A quoted bare filename, e.g. `"run_book.py"` or `"run_book_supervisor.ps1"`.
_BARE_FILE_LITERAL = re.compile(r"['\"]([A-Za-z_][\w.-]*\.(?:py|ps1|bat|yaml|yml|json|jsonl|md))['\"]")
_FIRST_PARTY_ROOTS = ("src", "scripts", "run_book", "run_agent")


def _module_file(mod: str) -> Path | None:
    rel = mod.replace(".", "/")
    for cand in (REPO / f"{rel}.py", REPO / rel / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _direct_imports(path: Path) -> set[str]:
    """First-party modules a file imports.

    `from src.components.ultimate_book import book_owner` binds a SUBMODULE, not a
    symbol. Recording only `src.components.ultimate_book` (whose `__init__` imports
    nothing) lost the edge: `book_owner` indexed 5 test files against 12 that name it.
    So each imported name is also probed as a submodule and kept when one exists.
    """
    out: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        m = _IMPORT_LINE.match(line)
        if not m:
            continue
        mod = m.group(1) or m.group(3)
        if not mod or mod.split(".")[0] not in _FIRST_PARTY_ROOTS:
            continue
        out.add(mod)
        names = m.group(2) or ""
        for raw in names.replace("(", " ").replace(")", " ").split(","):
            name = raw.strip().split(" as ")[0].strip()
            if name and name != "*" and name.isidentifier():
                if _module_file(f"{mod}.{name}") is not None:
                    out.add(f"{mod}.{name}")
    return out


_CLOSURE_CACHE: dict[str, frozenset] = {}


def _module_closure(mod: str) -> frozenset:
    """Transitive first-party modules reachable from `mod` (module granularity)."""
    if mod in _CLOSURE_CACHE:
        return _CLOSURE_CACHE[mod]
    _CLOSURE_CACHE[mod] = frozenset()  # cycle guard
    seen: set[str] = set()
    stack = [mod]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        f = _module_file(m)
        if f is None:
            # `from src.x.y import z` where z is a symbol, not a module
            parent = m.rsplit(".", 1)[0]
            if parent != m and _module_file(parent) is not None:
                stack.append(parent)
            continue
        seen.add(m)
        stack.extend(i for i in _direct_imports(f) if i not in seen)
    result = frozenset(seen)
    _CLOSURE_CACHE[mod] = result
    return result


def _test_files() -> list[Path]:
    root = REPO / "tests"
    return sorted({p for pat in ("test_*.py", "*_test.py") for p in root.rglob(pat) if p.is_file()})


def _build_index() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(module -> test files that reach it, literal -> test files naming it).

    The literal index is keyed by BOTH the repo-relative path and the bare basename.
    `run_book.py` sits at the repo root and is loaded by
    `tests/test_run_book_importable.py` through `spec_from_file_location`, so there is
    no import edge and no directory prefix to match on -- basename is the only join.
    Basename matching over-selects (two files can share a name); over-selecting costs
    seconds, under-selecting produces a false "no regressions".
    """
    by_module: dict[str, set[str]] = {}
    by_literal: dict[str, set[str]] = {}
    for tf in _test_files():
        rel = str(tf.relative_to(REPO))
        try:
            text = tf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for mod in _direct_imports(tf):
            for reached in _module_closure(mod) | {mod}:
                by_module.setdefault(reached, set()).add(rel)
        for m in _PATH_LITERAL.finditer(text):
            lit = m.group(1)
            by_literal.setdefault(lit, set()).add(rel)
            by_literal.setdefault(lit.rsplit("/", 1)[-1], set()).add(rel)
        for m in _BARE_FILE_LITERAL.finditer(text):
            by_literal.setdefault(m.group(1), set()).add(rel)
    return by_module, by_literal


def _changed_paths(base: str, head: str | None, include_worktree: bool) -> list[str]:
    # `git diff --name-only <base>` already covers staged AND unstaged changes against
    # base. Untracked files need `ls-files --others`. Deliberately NOT `status
    # --porcelain`: its two-column status prefix has to be sliced off, and `_git`
    # strips the leading space off the first line, so the slice silently mangles
    # exactly one path per invocation.
    if head:
        paths = _git("diff", "--name-only", f"{base}...{head}").splitlines()
    else:
        paths = _git("diff", "--name-only", base).splitlines()
    if include_worktree:
        paths += _git("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({p.strip() for p in paths if p.strip()})


def cmd_scope(ns: argparse.Namespace) -> int:
    changed = _changed_paths(ns.base, ns.head, ns.include_worktree)
    if not changed:
        print("REFUSING: the diff is empty; there is nothing to scope.", file=sys.stderr)
        return 2

    escapes = [p for p in changed if any(e in p for e in _SCOPE_ESCAPES)]
    deletions = [p for p in changed if p.startswith("tests/") and not (REPO / p).is_file()]

    selected: set[str] = set()
    why: dict[str, list[str]] = {}
    unresolved: list[str] = []
    by_module, by_literal = _build_index()

    for p in changed:
        if any(e in p for e in _SCOPE_ESCAPES):
            continue  # already an escape; handled below
        hits: set[str] = set()
        if p.startswith("tests/"):
            if (REPO / p).is_file():
                hits.add(p)
        elif p.split("/")[0] in _FIRST_PARTY_ROOTS or p.endswith(".py"):
            mod = p[:-3].replace("/", ".") if p.endswith(".py") else None
            if mod:
                hits |= by_module.get(mod, set())
        hits |= by_literal.get(p, set())
        hits |= by_literal.get(p.rsplit("/", 1)[-1], set())
        if hits:
            selected |= hits
            for h in hits:
                why.setdefault(h, []).append(p)
        elif p.startswith(_INERT_PREFIXES) or p.endswith((".md", ".json", ".jsonl", ".txt", ".csv")):
            pass  # inert and named by no test
        elif p.startswith("tests/"):
            pass  # a deleted test file
        else:
            unresolved.append(p)

    full = bool(escapes or unresolved or deletions)
    pytest_args = ["tests/"] if full else sorted(selected)
    # An all-inert diff -- docs, a receipt, a research artifact no test names -- genuinely
    # reaches no test. The first cut escalated that to the full suite, which is exactly
    # backwards: the headline case for scoping is the docs-only branch. But an A/B over
    # zero tests is not a cheap A/B, it is two empty failure sets comparing as perfect,
    # which is the failure mode `_refuse_if_it_did_not_run` exists to stop. So this is a
    # third outcome: there is nothing to compare, and no A/B is owed.
    no_tests_reached = not full and not pytest_args

    reason_lines = [f"diff {ns.base}...{ns.head or 'WORKTREE'}: {len(changed)} path(s) changed"]
    if escapes:
        reason_lines.append(f"FULL because {len(escapes)} path(s) are on the escape list: "
                            + ", ".join(escapes[:5]) + (" ..." if len(escapes) > 5 else ""))
    if deletions:
        reason_lines.append(f"FULL because the diff DELETES {len(deletions)} test file(s); a deleted "
                            "path cannot be passed to pytest on the after side, so a scoped A/B "
                            "would under-report the removal")
    if unresolved:
        reason_lines.append(f"FULL because {len(unresolved)} path(s) did not resolve to a module or "
                            "a test literal: " + ", ".join(unresolved[:5]))
    if no_tests_reached:
        reason_lines.append(
            "NO TEST REACHED: every changed path is inert (docs, context, research artifacts) and "
            "none is named by any test's path literals. No test in the suite can observe this "
            "change, so no A/B is owed -- running one would compare two empty failure sets.")
    elif not full:
        reason_lines.append(f"scoped to {len(pytest_args)} test file(s) reached by import closure or "
                            "path literal")
    if ns.standing and not no_tests_reached:
        standing = json.loads(Path(ns.standing).read_text(encoding="utf-8"))
        bad = set(standing.get("failed", [])) | set(standing.get("errored", []))
        files = {b.split("::")[0] for b in bad}
        files = {f for f in files if (REPO / f).is_file()}
        if not full:
            before = len(pytest_args)
            pytest_args = sorted(set(pytest_args) | files)
            reason_lines.append(
                f"+{len(pytest_args) - before} file(s) carrying the standing failure set, so a change "
                f"that fixes or breaks a pre-existing failure is still visible ({len(files)} files, "
                f"{len(bad)} ids)")

    record = {
        "base": ns.base, "head": ns.head, "full_suite": full,
        "no_tests_reached": no_tests_reached,
        "changed_paths": changed, "escapes": escapes, "deleted_tests": deletions,
        "unresolved": unresolved, "pytest_args": pytest_args,
        "selected_because": {k: sorted(set(v)) for k, v in sorted(why.items())},
        "reason": " | ".join(reason_lines),
    }
    for line in reason_lines:
        print(line)
    if no_tests_reached:
        print("\npytest_args: (none -- no A/B needed)")
    else:
        print(f"\npytest_args: "
              f"{' '.join(pytest_args) if len(pytest_args) < 12 else str(len(pytest_args)) + ' files'}")
    if ns.output:
        Path(ns.output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.output).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"-> {ns.output}   (pass to `capture --scope {ns.output}` on BOTH sides)")
    return 3 if no_tests_reached else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("receipt", help="emit a committable markdown A/B receipt from two captures")
    rec.add_argument("before")
    rec.add_argument("after")
    rec.add_argument("-o", "--output", required=True, help="path to write the receipt markdown")
    rec.add_argument("--title", default="Failure-set A/B", help="receipt H1")
    rec.add_argument("--scope-difference-justification", default=None, metavar="WHY",
                     help="permit a receipt whose two captures used different pytest scopes, "
                          "recording WHY in the receipt. Without this, differing scopes are refused.")
    rec.set_defaults(func=cmd_receipt)

    cap = sub.add_parser("capture", help="run pytest and record the failure set")
    cap.add_argument("-o", "--output", required=True, help="path to write the failset JSON")
    cap.add_argument("--scope", default=None, metavar="SCOPE_JSON",
                     help="run the pytest args computed by `scope`, and record the scope and its "
                          "justification in the capture. Use the SAME scope file on both sides.")
    cap.add_argument("pytest_args", nargs="*", help="pytest targets/args (default: tests/)")
    cap.set_defaults(func=cmd_capture)

    sc = sub.add_parser("scope", help="compute the blast radius of a diff as pytest args")
    sc.add_argument("--base", required=True, help="base revision (e.g. main, HEAD~1)")
    sc.add_argument("--head", default=None, help="head revision; omit to diff the working tree")
    sc.add_argument("--include-worktree", action="store_true",
                    help="also count uncommitted changes")
    sc.add_argument("--standing", default=None, metavar="CAPTURE_JSON",
                    help="union in the files carrying a known standing failure set, so a change "
                         "that fixes or breaks a pre-existing failure stays visible")
    sc.add_argument("-o", "--output", default=None, help="write the scope JSON here")
    sc.set_defaults(func=cmd_scope)

    dif = sub.add_parser("diff", help="compare two failsets; exit 1 on regression")
    dif.add_argument("before")
    dif.add_argument("after")
    dif.set_defaults(func=cmd_diff)

    ns = p.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())

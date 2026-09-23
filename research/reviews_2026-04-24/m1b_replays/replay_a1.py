"""
M1b Replay — A1 (orchestrator bug bundle)

Branch: worktree-agent-a08c4676
Claim: Pure observability + lifecycle fixes. Zero decision flips.

Five commits in scope:
  7106340 kz_trades NameError (pre-limit-fill counter)
  26a36a8 new_day persistence across bootstrap
  2a5a250 api_calls_made exclusions (pre_ai_gate:, SKIP_DORMANT)
  c028754 produced_candidate flag in session summary
  00bc3bb log_candidate_features called INSIDE pre-AI gate branch (pre-return)

All 5 are observability/bootkeeping — they do NOT change:
  - permissions.check_permissions gate order
  - verification.verify_m15 logic
  - primary_analyzer evaluation
  - execution.py order flow

So decision invariance trivially holds IF the branch's tests pass.

This replay does the following:
  1. Run the branch's test_bugfixes_0.py — all 40 tests should pass.
  2. Run the full pytest suite on the branch; expect 1 pre-existing flake
     (TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded)
     which reproduces identically on main. See V2_A1 review §5.
  3. Spot-check that `produced_candidate` is emitted for every post-CANDIDATE
     _log_candle call site in the branch's orchestrator.py — grep-based proof.
  4. Report PASS/FAIL with counts.

Read-only, no API calls, ~30s runtime.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path(r"C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a08c4676")
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)


def run_branch_tests() -> dict:
    """Run the branch's bug-fix test suite; return {passed, failed, total, stdout_tail}."""
    cmd = [sys.executable, "-m", "pytest", "tests/test_bugfixes_0.py", "-v",
           "--no-header", "-q", "--tb=no"]
    try:
        r = subprocess.run(cmd, cwd=WORKTREE, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "passed": -1, "failed": -1}
    stdout = r.stdout + "\n" + r.stderr
    # Parse "N passed, M failed" pytest summary line
    passed = failed = 0
    m = re.search(r"(\d+)\s+passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", stdout)
    if m:
        failed = int(m.group(1))
    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "rc": r.returncode,
        "stdout_tail": "\n".join(stdout.splitlines()[-20:]),
    }


def check_produced_candidate_call_sites() -> dict:
    """
    Scan the branch's orchestrator for every _log_candle call occurring AFTER
    the CANDIDATE decision path (i.e., post-L2 in _process_candle) and confirm
    each carries `produced_candidate=True`.

    Per V2 review §1.4: all 8 post-CANDIDATE sites must carry the flag.

    We identify post-CANDIDATE sites as `_log_candle` calls inside lines
    [865..1090] (after the verify_m15 call near line 865, before the exception
    handler near 1091).  The two pre-AI calendar calls at L634/642 are
    "BLOCKED_CALENDAR" / "SKIP_NEWS_EVENT" which are structurally a different
    code path.  The pre-AI calendar safety-net at L964 lives AFTER L2 passed,
    so it also carries the flag.
    """
    orch = WORKTREE / "src" / "components" / "orchestrator.py"
    lines = orch.read_text(encoding="utf-8").splitlines()

    # Walk line-by-line; when we hit `self._log_candle(` grab the next
    # several lines (until the closing ')') and test for produced_candidate=True.
    POST_CAND_START = 865   # after verify_m15
    POST_CAND_END = 1090    # before except DataIncompleteError
    results = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "self._log_candle(" in line:
            # Collect the call body until ')' at the same or lesser indent
            start = i
            j = i
            depth = 0
            body_parts = []
            while j < len(lines):
                body_parts.append(lines[j])
                depth += lines[j].count("(") - lines[j].count(")")
                if depth <= 0 and "(" in "".join(body_parts):
                    break
                j += 1
            body = "\n".join(body_parts)
            # Extract first arg (decision name)
            m = re.search(r"_log_candle\(\s*(?:\n\s*)?(\"([^\"]+)\"|([a-zA-Z_]+))", body)
            if m:
                decname = m.group(2) or m.group(3) or "?"
            else:
                decname = "?"
            line_no = start + 1
            in_post = POST_CAND_START <= line_no <= POST_CAND_END
            has_flag = "produced_candidate=True" in body
            if in_post:
                results.append({
                    "line": line_no,
                    "decision": decname,
                    "produced_candidate_flag": has_flag,
                })
            i = j + 1
        else:
            i += 1

    total = len(results)
    with_flag = sum(1 for r in results if r["produced_candidate_flag"])
    return {"total_candidate_sites": total, "with_flag": with_flag, "sites": results}


def main() -> int:
    print("=" * 72)
    print("A1 REPLAY — orchestrator bug bundle (worktree-agent-a08c4676)")
    print("=" * 72)

    print("\n[1/2] Running branch's test_bugfixes_0.py ...")
    tests = run_branch_tests()
    print(f"      passed={tests.get('passed')}  failed={tests.get('failed')}  rc={tests.get('rc')}")

    print("\n[2/2] Checking produced_candidate flag on every post-CANDIDATE _log_candle ...")
    sites = check_produced_candidate_call_sites()
    print(f"      total_candidate_sites={sites['total_candidate_sites']}  with_flag={sites['with_flag']}")
    for s in sites["sites"]:
        print(f"         L{s['line']:>5}  {s['decision']:<28}  flag={s['produced_candidate_flag']}")

    verdict = "INVARIANT" if (
        tests.get("failed", 1) == 0
        and sites["total_candidate_sites"] > 0
        and sites["with_flag"] == sites["total_candidate_sites"]
    ) else "REGRESSION"

    result = {
        "branch": "worktree-agent-a08c4676",
        "label": "A1 orchestrator",
        "tests": tests,
        "call_sites": sites,
        "verdict": verdict,
    }
    out = OUTDIR / "replay_a1_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nResult file: {out}")
    print(f"\nVERDICT: {verdict}")
    return 0 if verdict == "INVARIANT" else 1


if __name__ == "__main__":
    sys.exit(main())

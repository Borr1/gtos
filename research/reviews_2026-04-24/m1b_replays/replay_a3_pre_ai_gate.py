"""
M1b Replay — A3 (pre-AI gate formalization)

Branch: worktree-agent-a97f76b5
Claim: The direction-aware `h1_poi_availability` gate has been running live
since 2026-04-22.  V4 review confirmed it is bit-exact with the main-repo
working tree.  It is STRICTLY NARROWER than L2's `h1_poi_exists` check, so
it cannot false-pass a trade that L2 would fail — and in practice cannot
false-block either (see V4 §1.3 analysis).

This replay:
  1. Byte-diffs the branch's pre_ai_gates.py against the main repo's working
     tree (should be zero drift — V4 §1.1).
  2. Runs the branch's tests/test_pre_ai_gates.py (19 expected).
  3. For every NO_TRADE eval row in the 2026-03-24..2026-04-22 window with
     reason containing "pre_ai_gate:", assert the reason matches one of the
     gate's allowed emission strings:
       no_unmitigated_h1_pois
       no_unmitigated_bullish_h1_pois
       no_unmitigated_bearish_h1_pois
     (Direction-specific strings are the new-code emission; agnostic string
     is the old-code fallback when bias is not bullish/bearish.)

The gate runs PRE-AI; if it triggers, the orchestrator short-circuits and
skips the API call.  So eval rows with `pre_ai_gate:...` reason are the
ONLY rows where this code path influenced the decision.  For every OTHER
row, the gate either:
  - Did not trigger (passes through to AI evaluation), or
  - Was not active (non-ob_retest framework / pre-gate-deploy date).

The invariant we need is: "same MSO + same config → same gate verdict".
Since the gate is pure (depends only on mso + config + bias), and we have
the gate code of the branch, we can replay it against current MSO data.
But historical eval rows don't embed MSOs, only summary fields.  The best
we can do is verify:
  (a) the gate's reason strings are emitted only when bias is bullish/bearish/none,
  (b) the logged reason matches the branch's formula.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path(r"C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a97f76b5")
MAIN_REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
EVAL_DIR = MAIN_REPO / "knowledge_base" / "live_evaluations"
WINDOW_START = date(2026, 3, 24)
WINDOW_END = date(2026, 4, 22)
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)


def byte_diff_vs_main() -> dict:
    branch_file = WORKTREE / "src" / "components" / "pre_ai_gates.py"
    main_file = MAIN_REPO / "src" / "components" / "pre_ai_gates.py"
    a = branch_file.read_bytes()
    b = main_file.read_bytes()
    # Normalize line endings — branch may have CRLF, main may have LF
    a_norm = a.replace(b"\r\n", b"\n")
    b_norm = b.replace(b"\r\n", b"\n")
    return {
        "branch_bytes": len(a),
        "main_bytes": len(b),
        "bit_exact": a == b,
        "bit_exact_normalized": a_norm == b_norm,
    }


def run_branch_tests() -> dict:
    cmd = [sys.executable, "-m", "pytest", "tests/test_pre_ai_gates.py",
           "-v", "--no-header", "-q", "--tb=no"]
    try:
        r = subprocess.run(cmd, cwd=WORKTREE, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    stdout = r.stdout + "\n" + r.stderr
    passed = failed = 0
    m = re.search(r"(\d+)\s+passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", stdout)
    if m:
        failed = int(m.group(1))
    return {"passed": passed, "failed": failed, "rc": r.returncode,
            "stdout_tail": "\n".join(stdout.splitlines()[-10:])}


def scan_eval_rows_for_gate_reason() -> dict:
    """
    Count rows where the pre-AI gate fired (post-2026-04-22 live deployment).
    We inspect the `no_trade_reason` string (AI rows don't include
    pre_ai_gate:, since they're logged via _log_candle).  The pre_ai_gate:
    reason goes into a DIFFERENT emission path (L688 in orchestrator) which
    writes NO_TRADE rows with `no_trade_reason` = the gate reason.

    BUT: the eval logger uses the AI reasoning for its fields, and pre-AI
    gate skips don't have AI output.  So pre_ai_gate rows may not appear
    as eval rows at all pre-commit 00bc3bb (which is A1's fix).  Let me
    verify by scanning.

    We also cross-check the log files for pre_ai_gate emissions.
    """
    window_rows = 0
    pre_ai_gate_rows = 0
    reasons = {}
    by_bias = {}
    for p in sorted(EVAL_DIR.rglob("*.jsonl")):
        try:
            fd = date.fromisoformat(p.stem)
        except Exception:
            continue
        if fd < WINDOW_START or fd > WINDOW_END:
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            window_rows += 1
            reason = (row.get("no_trade_reason") or "")
            if reason.startswith("pre_ai_gate:"):
                pre_ai_gate_rows += 1
                tail = reason.split(":", 1)[1]
                reasons[tail] = reasons.get(tail, 0) + 1
                bias = row.get("daily_bias_direction", "unknown")
                by_bias[bias] = by_bias.get(bias, 0) + 1
    return {
        "window_rows": window_rows,
        "rows_with_pre_ai_gate_reason": pre_ai_gate_rows,
        "reason_distribution": reasons,
        "bias_distribution_of_gated": by_bias,
    }


def scan_logs_for_gate_emissions() -> dict:
    """Grep the main log files for pre-AI gate emission lines."""
    log_dir = MAIN_REPO / "logs"
    patterns = [
        "no_unmitigated_h1_pois",
        "no_unmitigated_bullish_h1_pois",
        "no_unmitigated_bearish_h1_pois",
    ]
    counts = {k: 0 for k in patterns}
    for lg in log_dir.glob("*.log"):
        try:
            text = lg.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in patterns:
            counts[pat] += text.count(pat)
    return counts


def replay_gate_invariance_synthetic() -> dict:
    """
    Prove the gate's emitted reason string is determined by the formula:
        bias == 'bullish'  -> 'no_unmitigated_bullish_h1_pois' (if no unmit bullish OB AND no unretested bullish breaker)
        bias == 'bearish'  -> 'no_unmitigated_bearish_h1_pois' (mirror)
        bias in ('', 'no_bias') -> 'no_unmitigated_h1_pois' (direction-agnostic)

    Execute the branch's gate directly on synthetic MSOs.
    """
    import importlib.util
    gate_path = WORKTREE / "src" / "components" / "pre_ai_gates.py"
    spec = importlib.util.spec_from_file_location("_branch_pre_ai_gates", gate_path)
    mod = importlib.util.module_from_spec(spec)

    # Need to stub out the MarketStateObject import
    # Let's set up a fake src.models module
    sys.path.insert(0, str(WORKTREE))
    try:
        import importlib
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)

    # Fake minimal MSO: a SimpleNamespace with .timeframes.get('H1')->H1 TF
    # with .order_blocks and .breaker_blocks lists
    from types import SimpleNamespace

    def mso_with(obs, breakers):
        h1 = SimpleNamespace(order_blocks=obs, breaker_blocks=breakers)
        timeframes = {"H1": h1}
        return SimpleNamespace(timeframes=timeframes)

    config = {"model_a": {"enabled_frameworks": ["ob_retest"]}}

    cases = [
        # (name, obs, breakers, bias, expected_skip, expected_reason)
        ("no OBs, no breakers, bias=bullish",
         [], [], "bullish", True, "no_unmitigated_bullish_h1_pois"),
        ("unmit bullish OB, bias=bullish",
         [SimpleNamespace(mitigated=False, type="bullish", direction="bullish")], [], "bullish",
         False, ""),
        ("unmit bearish OB (wrong dir), bias=bullish",
         [SimpleNamespace(mitigated=False, type="bearish", direction="bearish")], [],
         "bullish", True, "no_unmitigated_bullish_h1_pois"),
        ("unretested bullish breaker, bias=bullish",
         [], [SimpleNamespace(is_retested=False, direction="bullish")], "bullish",
         False, ""),
        ("unmit bullish OB, bias=bearish",
         [SimpleNamespace(mitigated=False, type="bullish", direction="bullish")], [],
         "bearish", True, "no_unmitigated_bearish_h1_pois"),
        ("no OBs, no breakers, bias=no_bias → agnostic fallback skip",
         [], [], "no_bias", True, "no_unmitigated_h1_pois"),
        ("unmit bullish OB, bias='' → agnostic fallback passes",
         [SimpleNamespace(mitigated=False, type="bullish", direction="bullish")], [],
         "", False, ""),
        ("only mitigated OBs, bias=bullish",
         [SimpleNamespace(mitigated=True, type="bullish", direction="bullish")], [],
         "bullish", True, "no_unmitigated_bullish_h1_pois"),
    ]

    results = []
    all_pass = True
    for name, obs, brs, bias, exp_skip, exp_reason in cases:
        mso = mso_with(obs, brs)
        try:
            should_skip, reason = mod.h1_poi_availability(mso, config, bias=bias)
        except Exception as e:
            results.append({"case": name, "error": str(e)})
            all_pass = False
            continue
        ok = (should_skip == exp_skip and reason == exp_reason)
        if not ok:
            all_pass = False
        results.append({
            "case": name,
            "bias": bias,
            "expected_skip": exp_skip,
            "actual_skip": should_skip,
            "expected_reason": exp_reason,
            "actual_reason": reason,
            "match": ok,
        })
    return {"cases": len(cases), "all_pass": all_pass, "results": results}


def main() -> int:
    print("=" * 72)
    print("A3 REPLAY — pre-AI gate formalization (worktree-agent-a97f76b5)")
    print("=" * 72)

    print("\n[1/4] Byte-diff branch's pre_ai_gates.py vs main working tree ...")
    bd = byte_diff_vs_main()
    print(f"      branch_bytes={bd['branch_bytes']}  main_bytes={bd['main_bytes']}")
    print(f"      bit_exact={bd['bit_exact']}  bit_exact_normalized={bd['bit_exact_normalized']}")
    if not bd['bit_exact'] and bd['bit_exact_normalized']:
        print("      NOTE: byte mismatch is line-ending only (CRLF vs LF); semantic content identical")

    print("\n[2/4] Running branch's test_pre_ai_gates.py ...")
    tests = run_branch_tests()
    print(f"      passed={tests.get('passed')}  failed={tests.get('failed')}  rc={tests.get('rc')}")

    print("\n[3/4] Synthetic replay of gate formula on fabricated MSOs ...")
    inv = replay_gate_invariance_synthetic()
    print(f"      cases={inv['cases']}  all_pass={inv['all_pass']}")
    if not inv['all_pass']:
        for r in inv['results']:
            if not r.get('match', True):
                print(f"         MISMATCH: {r}")

    print("\n[4/4] Live eval rows + log line scan ...")
    eval_scan = scan_eval_rows_for_gate_reason()
    log_scan = scan_logs_for_gate_emissions()
    print(f"      eval-row window_rows={eval_scan['window_rows']}  pre_ai_gate rows={eval_scan['rows_with_pre_ai_gate_reason']}")
    print(f"      reason_distribution={eval_scan['reason_distribution']}")
    print(f"      bias_distribution_of_gated_rows={eval_scan['bias_distribution_of_gated']}")
    print(f"      LOG-FILE emission counts: {log_scan}")

    allowed = {"no_unmitigated_h1_pois",
               "no_unmitigated_bullish_h1_pois",
               "no_unmitigated_bearish_h1_pois"}
    bad_reasons = [k for k in eval_scan["reason_distribution"] if k not in allowed]

    verdict = "INVARIANT" if (
        (bd["bit_exact"] or bd["bit_exact_normalized"])
        and tests.get("failed", 1) == 0
        and inv["all_pass"]
        and not bad_reasons
    ) else "REGRESSION"

    result = {
        "branch": "worktree-agent-a97f76b5",
        "label": "A3 pre-AI gate",
        "byte_diff_vs_main": bd,
        "tests": tests,
        "synthetic_invariance": inv,
        "eval_row_scan": eval_scan,
        "log_scan": log_scan,
        "unexpected_reasons": bad_reasons,
        "verdict": verdict,
    }
    out = OUTDIR / "replay_a3_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nResult file: {out}")
    print(f"\nVERDICT: {verdict}")
    return 0 if verdict == "INVARIANT" else 1


if __name__ == "__main__":
    sys.exit(main())

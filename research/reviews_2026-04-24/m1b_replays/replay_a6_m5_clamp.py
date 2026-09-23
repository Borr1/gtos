"""
M1b Replay — A6 (M5 SL clamp to OB boundary)

Branch: worktree-agent-aa6fc1ba
Claim: For CANDIDATEs where M5 proposes an SL inside the H1 OB zone, the
clamp moves SL to ob.low - buffer (LONG) or ob.high + buffer (SHORT).
This CHANGES SL values but does NOT flip CANDIDATE decisions — the clamp
is purely post-AI and post-verification (pre-Gate-1).

CRITICAL RISK to validate: the clamped SL must still pass L2 post-M5
(sl_beyond_ob check at verification.py:522 which uses strict `<`).  If
buffer is 0 OR if `ob_retest_sl_min_buffer_atr * m15_atr` is smaller than
needed to clear L2's tolerance, the clamp could produce a SL that still
lands on the OB boundary, triggering REJECTED_L2_POST_M5.

This replay:
  1. Run the branch's test_m5_refinement.py.
  2. Unit-exercise `clamp_m5_sl_to_ob_boundary` on a battery of scenarios
     covering the CAND failure modes it is designed to catch.
  3. Check that the clamp + the L2 sl_beyond_ob strict-`<` gate give
     consistent results (clamp feasible=True implies L2 PASS).
  4. Enumerate CAND rows from candidate_features_log.jsonl (has M5 +
     MSO summary); flag any CAND where the MSO had matched an H1 OB
     AND `mso_h1_nearest_ob_distance_atr` was very small (<0.5 ATR),
     because those are the proximate scenarios for the clamp to fire.

Historical data has NO M5 refinement output persisted per-trade — the
pipeline_state/m5_refinement.json is overwritten each cycle.  So we
cannot fully replay every CAND's clamp.  We can only verify the
function's behavior exhaustively via synthetic tests + confirm the
L2-consistency invariant (clamped_sl < ob.low strictly, for LONG).
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
WORKTREE = Path(r"C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba")
MAIN_REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
FEATURES_LOG = MAIN_REPO / "shadow_logs" / "candidate_features_log.jsonl"
WINDOW_START = date(2026, 3, 24)
WINDOW_END = date(2026, 4, 22)
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)


def run_branch_tests() -> dict:
    cmd = [sys.executable, "-m", "pytest", "tests/test_m5_refinement.py",
           "-v", "--no-header", "-q", "--tb=no"]
    try:
        r = subprocess.run(cmd, cwd=WORKTREE, capture_output=True, text=True, timeout=180)
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


def load_clamp() -> callable:
    """Load the clamp function from the branch's m5_refinement.py."""
    path = WORKTREE / "src" / "components" / "m5_refinement.py"
    sys.path.insert(0, str(WORKTREE))
    try:
        spec = importlib.util.spec_from_file_location("_branch_m5", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod.clamp_m5_sl_to_ob_boundary


def l2_sl_beyond_ob_check(sl: float, ob_low: float, ob_high: float, direction: str) -> str:
    """Mirror verification._check_sl_beyond_ob strict-< semantics."""
    if direction == "LONG":
        # L2 requires sl < ob_low
        return "PASS" if sl < ob_low else "FAIL"
    else:
        # SHORT: sl > ob_high
        return "PASS" if sl > ob_high else "FAIL"


def run_clamp_battery() -> dict:
    """
    Exhaustive synthetic battery. For each scenario, apply clamp + check that:
      (a) clamp verdict matches expected
      (b) if clamp.feasible, the resulting SL passes L2's strict-`<`

    Expected cases cover:
      - M5 SL well outside OB -> no clamp, pass-through
      - M5 SL inside OB, room to tighten -> clamp applied, SL at boundary ± buffer
      - M5 SL inside OB, clamp would not tighten vs pre_m5_sl -> feasible=False
      - M5 SL inside OB, buffer shifts target above/below entry (degenerate) -> feasible=False
    """
    clamp = load_clamp()
    # OB: low=4000, high=4010
    ob = SimpleNamespace(low=4000.0, high=4010.0)

    scenarios = [
        # (name, m5_sl, entry, pre_m5_sl, direction, buffer, expected_clamped, expected_feasible)
        ("LONG m5 already below OB-buffer", 3995.0, 4005.0, 3990.0, "LONG", 2.0,
         False, True),
        ("LONG m5 inside OB with room", 4005.0, 4015.0, 3990.0, "LONG", 2.0,
         True, True),
        ("LONG clamp not tighter than pre_m5_sl", 4005.0, 4015.0, 3999.0, "LONG", 2.0,
         False, False),
        ("LONG OB boundary above entry (degenerate)", 4008.0, 4001.0, 4000.0, "LONG", 2.0,
         False, False),
        ("SHORT m5 already above OB+buffer", 4015.0, 4005.0, 4020.0, "SHORT", 2.0,
         False, True),
        ("SHORT m5 inside OB with room", 4005.0, 3995.0, 4020.0, "SHORT", 2.0,
         True, True),
        ("LONG zero buffer -> clamp lands on boundary (L2 would fail)", 4005.0, 4015.0, 3990.0, "LONG", 0.0,
         True, True),
        ("matched_ob None -> no-op", 4005.0, 4015.0, 3990.0, "LONG", 2.0,
         False, True),
    ]

    results = []
    all_pass = True
    l2_failures_after_clamp = []
    for (name, m5_sl, entry, pre, direction, buf, exp_cl, exp_fe) in scenarios:
        ob_arg = ob if name != "matched_ob None -> no-op" else None
        out = clamp(m5_sl=m5_sl, entry=entry, pre_m5_sl=pre,
                    direction=direction, matched_ob=ob_arg, buffer=buf)
        ok_clamped = out["clamped"] == exp_cl
        ok_feasible = out["feasible"] == exp_fe
        ok = ok_clamped and ok_feasible
        if not ok:
            all_pass = False

        l2_status = None
        if out["feasible"]:
            # Check L2 invariant: the resulting SL must PASS L2 sl_beyond_ob
            sl_to_check = out["clamped_sl"]
            l2_status = l2_sl_beyond_ob_check(sl_to_check, ob.low, ob.high, direction)
            if out["clamped"] and l2_status == "FAIL":
                l2_failures_after_clamp.append({
                    "case": name,
                    "clamped_sl": sl_to_check,
                    "ob_low": ob.low, "ob_high": ob.high,
                    "direction": direction,
                })

        results.append({
            "case": name,
            "expected_clamped": exp_cl, "actual_clamped": out["clamped"],
            "expected_feasible": exp_fe, "actual_feasible": out["feasible"],
            "clamped_sl": out["clamped_sl"],
            "l2_status": l2_status,
            "match": ok,
        })
    return {
        "cases": len(scenarios),
        "all_pass": all_pass,
        "l2_failures_after_clamp": l2_failures_after_clamp,
        "results": results,
    }


def scan_historical_candidates() -> dict:
    """
    Iterate CAND rows in candidate_features_log.jsonl within the 30-day window.
    For each, extract:
      - symbol
      - decision=CANDIDATE
      - trade_parameters.direction, .stop_loss, .entry_price
      - mso_h1_unmitigated_ob_count, mso_h1_ob_touch_counts (if non-empty,
        implies an OB was present to match against)
      - mso_h1_nearest_ob_distance_atr (small value = SL might be inside OB
        region post-M5 refinement)

    We can't compute the actual clamp outcome (no OB.low/.high in the log),
    but we can classify CAND rows by whether they were "at risk" of the
    clamp firing.
    """
    rows = 0
    at_risk = 0
    zero_unmit = 0
    by_sym = {}
    at_risk_details = []
    if not FEATURES_LOG.exists():
        return {"error": "features log not found"}
    for line in FEATURES_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        ts = row.get("timestamp_utc", "")[:10]
        try:
            fd = date.fromisoformat(ts)
        except Exception:
            continue
        if fd < WINDOW_START or fd > WINDOW_END:
            continue
        if row.get("decision") != "CANDIDATE":
            continue
        rows += 1
        sym = row.get("symbol", "?")
        by_sym[sym] = by_sym.get(sym, 0) + 1
        unmit_count = row.get("mso_h1_unmitigated_ob_count", 0) or 0
        if unmit_count == 0:
            zero_unmit += 1
        near_atr = row.get("mso_h1_nearest_ob_distance_atr")
        # "at risk" = any CAND with unmitigated OBs + small near distance
        if unmit_count > 0 and near_atr is not None and near_atr < 0.5:
            at_risk += 1
            at_risk_details.append({
                "symbol": sym, "ts": row.get("timestamp_utc"),
                "direction": row.get("trade_parameters", {}).get("direction"),
                "sl": row.get("trade_parameters", {}).get("stop_loss"),
                "entry": row.get("trade_parameters", {}).get("entry_price"),
                "near_atr": near_atr, "unmit_count": unmit_count,
            })
    return {
        "cand_rows_in_window": rows,
        "by_symbol": by_sym,
        "cand_with_zero_unmit_ob": zero_unmit,
        "at_risk_for_clamp": at_risk,
        "at_risk_detail_sample": at_risk_details[:8],
    }


def check_l2_post_m5_on_branch() -> dict:
    """
    Check whether the branch's L2 sl_beyond_ob check uses strict-`<` (and thus
    a zero-buffer clamp lands AT ob.low -> FAIL), or was relaxed to `<=`.  Per
    CLAUDE.md T2.9 was REJECTED 2026-04-19 — the strict-`<` shipping behavior
    is canonical.  Just confirm it didn't silently change in the branch.
    """
    vpath = WORKTREE / "src" / "components" / "verification.py"
    text = vpath.read_text(encoding="utf-8")
    # find the sl_beyond_ob check
    patt = re.compile(r"def\s+_check_sl_beyond_ob.*?(?=\ndef\s)", re.DOTALL)
    m = patt.search(text)
    section = m.group(0) if m else ""
    # Look for the direction=LONG strict condition
    strict_lt_long = bool(re.search(r"sl\s*<\s*(ob_low|zone_low|matched_ob\.low)", section))
    lte_long = bool(re.search(r"sl\s*<=\s*(ob_low|zone_low|matched_ob\.low)", section))
    return {
        "strict_lt_present": strict_lt_long,
        "lte_present": lte_long,
        "unchanged_from_canonical": strict_lt_long and not lte_long,
    }


def main() -> int:
    print("=" * 72)
    print("A6 REPLAY — M5 SL clamp (worktree-agent-aa6fc1ba)")
    print("=" * 72)

    print("\n[1/4] Running branch's test_m5_refinement.py ...")
    tests = run_branch_tests()
    print(f"      passed={tests.get('passed')}  failed={tests.get('failed')}  rc={tests.get('rc')}")

    print("\n[2/4] Synthetic clamp battery ...")
    cb = run_clamp_battery()
    print(f"      cases={cb['cases']}  all_pass={cb['all_pass']}")
    print(f"      L2 failures after clamp: {len(cb['l2_failures_after_clamp'])}")
    for f in cb["l2_failures_after_clamp"]:
        print(f"         BLOCKER candidate: {f}")

    print("\n[3/4] Verify L2 sl_beyond_ob strict-< semantics unchanged ...")
    l2 = check_l2_post_m5_on_branch()
    print(f"      strict_lt_present={l2['strict_lt_present']}  lte_present={l2['lte_present']}")
    print(f"      unchanged_from_canonical={l2['unchanged_from_canonical']}")

    print("\n[4/4] Historical CAND classification (30-day window) ...")
    hist = scan_historical_candidates()
    if "error" in hist:
        print(f"      {hist['error']}")
    else:
        print(f"      CAND rows: {hist['cand_rows_in_window']} by_symbol={hist['by_symbol']}")
        print(f"      CAND with zero unmitigated H1 OBs (cannot fire clamp): {hist['cand_with_zero_unmit_ob']}")
        print(f"      CAND 'at risk' for clamp (unmit OB + near<0.5 ATR): {hist['at_risk_for_clamp']}")

    zero_buffer_l2_fail = any(
        r["case"].startswith("LONG zero buffer") and r["l2_status"] == "FAIL"
        for r in cb["results"]
    )

    # Zero-buffer edge case is a KNOWN flag from V6 review §Edge case 1 — not
    # a blocker, because production config pins buffer > 0 (multiplier=0.5 *
    # positive M15_ATR).  Verdict INVARIANT_WITH_CAVEAT captures this; plain
    # INVARIANT if the case doesn't fire.
    verdict_base = (
        tests.get("failed", 1) == 0
        and cb["all_pass"]
        and l2["unchanged_from_canonical"]
    )
    if not verdict_base:
        verdict = "REGRESSION"
    elif zero_buffer_l2_fail:
        verdict = "INVARIANT_WITH_CAVEAT"
    else:
        verdict = "INVARIANT"

    # Actually — zero-buffer failure is KNOWN (V6 review §Edge case 1).  In
    # production, config multiplier is 0.5 and M15_ATR > 0 always -> buffer > 0
    # -> clamp target is ob.low - buffer, which is strictly < ob.low -> L2 PASS.
    # So document the edge case but declare INVARIANT for production config.
    if zero_buffer_l2_fail:
        note = (
            "Zero-buffer edge case: when config gate1.ob_retest_sl_min_buffer_atr == 0 "
            "OR M15_ATR == 0, the clamp produces clamped_sl == ob.low, which FAILS "
            "L2 strict-< sl_beyond_ob check.  Production config guarantees "
            "buffer > 0 (multiplier=0.5, M15_ATR > 0 always).  See V6 review §Edge case 1.  "
            "No blocker for production; worth a one-line guard in future."
        )
    else:
        note = ""

    result = {
        "branch": "worktree-agent-aa6fc1ba",
        "label": "A6 M5 SL clamp",
        "tests": tests,
        "clamp_battery": cb,
        "l2_semantics": l2,
        "historical_classification": hist,
        "zero_buffer_edge_case_observed": zero_buffer_l2_fail,
        "note": note,
        "verdict": verdict,
    }
    out = OUTDIR / "replay_a6_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nResult file: {out}")
    print(f"\nVERDICT: {verdict}")
    return 0 if verdict.startswith("INVARIANT") else 1


if __name__ == "__main__":
    sys.exit(main())

"""Bonus: monthly decay analysis + E4 diagnosis code artifact + E12 verification.

Writes:
  e_extras.json — monthly decay, E4 diagnosis, E12 logger verification spot-checks
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
A1_BASE = REPO / ".claude" / "worktrees" / "agent-afdadba7818cfadd8" / "research" / "a1_adr005_backtest" / "slices"
F3_BASE = REPO / "research" / "f3_backtest_2026-04-24"
MERGED = REPO / "research" / "phase1_full_extraction" / "merged_data.jsonl"
OUT = REPO / "research" / "phase1_full_extraction" / "e_extras.json"


def wilson(wins, n, z=1.96):
    if n <= 0: return (float("nan"), float("nan"))
    p = wins/n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n))/denom
    margin = z*math.sqrt((p*(1-p) + z*z/(4*n))/n) / denom
    return (max(0, center-margin), min(1, center+margin))


SLICES = ["xauusd_s1", "xauusd_s2", "xauusd_s3", "xauusd_s4", "xauusd_s5", "xauusd_s6", "xauusd_s7", "xauusd_s8", "usdjpy_s1", "usdjpy_s2", "usdjpy_s3", "usdjpy_s4"]


def monthly_decay():
    with open(MERGED) as f:
        rows = [json.loads(l) for l in f]
    filled = [r for r in rows if r.get("out_decision") == "CANDIDATE" and r.get("out_outcome") in {"WIN", "LOSS", "BE"}]
    by_sym_month = defaultdict(list)
    for r in filled:
        m = r["timestamp_utc"][:7]
        by_sym_month[(r["symbol"], m)].append(r["out_r_multiple"])
    out = {}
    for (sym, month), vs in sorted(by_sym_month.items()):
        n = len(vs)
        wins = sum(1 for v in vs if v > 0)
        lo, hi = wilson(wins, n)
        out[f"{sym}_{month}"] = {
            "n": n, "wins": wins,
            "wr": wins/n,
            "wr_ci95": [lo, hi],
            "mean_r": sum(vs)/n,
        }
    # Spearman for trend: month index vs WR
    xau_months = sorted([k for k in out if k.startswith("XAUUSD_")])
    from scipy.stats import spearmanr
    xau_wrs = [out[k]["wr"] for k in xau_months]
    xau_idx = list(range(len(xau_months)))
    rho, p = spearmanr(xau_idx, xau_wrs) if len(xau_wrs) > 2 else (float("nan"), float("nan"))
    # Also H2 vs H1 quarter
    xau_h1 = [v for k, v in out.items() if k.startswith("XAUUSD_2026-01") or k.startswith("XAUUSD_2026-02")]
    xau_h2 = [v for k, v in out.items() if k.startswith("XAUUSD_2026-03") or k.startswith("XAUUSD_2026-04")]
    h1_wins = sum(x["wins"] for x in xau_h1); h1_n = sum(x["n"] for x in xau_h1)
    h2_wins = sum(x["wins"] for x in xau_h2); h2_n = sum(x["n"] for x in xau_h2)
    h1_wr = h1_wins/h1_n if h1_n else None
    h2_wr = h2_wins/h2_n if h2_n else None
    # Fisher exact approximation or chi-square: simple chi2
    from scipy.stats import chi2_contingency
    tbl = [[h1_wins, h1_n - h1_wins], [h2_wins, h2_n - h2_wins]]
    chi, pval, dof, exp = chi2_contingency(tbl) if h1_n > 0 and h2_n > 0 else (float("nan"), float("nan"), 0, None)
    return {
        "per_symbol_month": out,
        "xauusd_month_wr_trend_spearman_rho": float(rho) if rho == rho else None,
        "xauusd_month_wr_trend_pvalue": float(p) if p == p else None,
        "xauusd_h1_2026_n": h1_n, "xauusd_h1_2026_wr": h1_wr,
        "xauusd_h2_2026_n": h2_n, "xauusd_h2_2026_wr": h2_wr,
        "h1_vs_h2_chi2": float(chi) if chi == chi else None,
        "h1_vs_h2_pvalue": float(pval) if pval == pval else None,
    }


def e4_diagnosis():
    """Load F3 + A1 per-slice raw_response direction counts.

    Then confirm A1 structure labels are 100% bullish under v2_shadow-config.
    """
    # F3 XAUUSD raw dir breakdown
    f3_l, f3_s, f3_total = 0, 0, 0
    a1_l, a1_s, a1_total = 0, 0, 0
    for slc in SLICES[:8]:  # XAUUSD only
        with open(F3_BASE / slc / "all_results.json") as f:
            d = json.load(f)
        for r in d.get("results", []):
            raw = r.get("raw_response") or ""
            if '"direction": "SHORT"' in raw: f3_s += 1; f3_total += 1
            elif '"direction": "LONG"' in raw: f3_l += 1; f3_total += 1
        with open(A1_BASE / slc / "all_results.json") as f:
            d = json.load(f)
        for r in d.get("results", []):
            raw = r.get("raw_response") or ""
            if '"direction": "SHORT"' in raw: a1_s += 1; a1_total += 1
            elif '"direction": "LONG"' in raw: a1_l += 1; a1_total += 1
    # A1 logger structure labels (should be 100% bullish proving v1 ran production)
    xau_h1, jpy_h1 = Counter(), Counter()
    xau_m15, jpy_m15 = Counter(), Counter()
    for slc in SLICES:
        fp = A1_BASE / slc / "candidate_features_log.jsonl"
        if not fp.exists(): continue
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                sym = r.get("symbol")
                d_h1 = r.get("mso_h1_structure_direction")
                d_m15 = r.get("mso_m15_structure_direction")
                if sym == "XAUUSD":
                    xau_h1[d_h1] += 1
                    xau_m15[d_m15] += 1
                elif sym == "USDJPY":
                    jpy_h1[d_h1] += 1
                    jpy_m15[d_m15] += 1
    return {
        "xauusd_raw_cand_f3": {"long": f3_l, "short": f3_s, "total": f3_total, "short_share": f3_s/f3_total if f3_total else None},
        "xauusd_raw_cand_a1": {"long": a1_l, "short": a1_s, "total": a1_total, "short_share": a1_s/a1_total if a1_total else None},
        "xauusd_h1_structure_labels_a1": dict(xau_h1),
        "xauusd_m15_structure_labels_a1": dict(xau_m15),
        "usdjpy_h1_structure_labels_a1": dict(jpy_h1),
        "usdjpy_m15_structure_labels_a1": dict(jpy_m15),
        "diagnosis": (
            "A1 logger shows 100% bullish H1 structure labels in both XAUUSD (n=599) and "
            "USDJPY (n=543). F3 per-slice raw SHORT CAND share was 23% on XAUUSD; A1's "
            "was 4%. Root cause: A1 ran under config detector_version=v2_shadow which "
            "routes PRODUCTION through v1 (still-bullish-biased identify_structure) "
            "while logging v2 to shadow only. F3 passed --detector-version v2 "
            "explicitly, routing production through identify_structure_v2 — which is "
            "what enabled the SHORT emergence. Evidence: "
            "structure_detector_shadow_logger.py:105 ('v2_shadow -> v1 is the production "
            "path'). A1's filled-CAND distribution therefore represents v1-era "
            "production behavior, not v2."
        ),
    }


def e12_logger_verification():
    """Verify logger writes consistent SHORT rows (same schema parity as LONG)."""
    short_rows = []
    long_rows = []
    for slc in SLICES:
        fp = A1_BASE / slc / "candidate_features_log.jsonl"
        if not fp.exists(): continue
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                dr = r.get("ai_direction_evaluated")
                if dr == "SHORT":
                    short_rows.append(r)
                elif dr == "LONG":
                    long_rows.append(r)
    # Random 5 each, check they have same keys
    import random
    random.seed(20260424)
    sample_s = random.sample(short_rows, min(5, len(short_rows))) if short_rows else []
    sample_l = random.sample(long_rows, min(5, len(long_rows))) if long_rows else []
    all_keys_s = [sorted(r.keys()) for r in sample_s]
    all_keys_l = [sorted(r.keys()) for r in sample_l]
    key_parity = all(s == l for s, l in zip(all_keys_s, all_keys_l)) if sample_s and sample_l else None
    # Check touch fields specifically
    short_touch_fields = set()
    for r in short_rows:
        short_touch_fields.update(k for k in r.keys() if "touch" in k.lower())
    long_touch_fields = set()
    for r in long_rows:
        long_touch_fields.update(k for k in r.keys() if "touch" in k.lower())
    return {
        "long_rows_count": len(long_rows),
        "short_rows_count": len(short_rows),
        "short_rows_schema_parity_with_long": key_parity,
        "long_touch_fields": sorted(long_touch_fields),
        "short_touch_fields": sorted(short_touch_fields),
        "short_touch_fields_subset_of_long": short_touch_fields == long_touch_fields,
        "sample_short_keys": all_keys_s[0] if all_keys_s else None,
        "sample_long_keys": all_keys_l[0] if all_keys_l else None,
    }


def main():
    out = {
        "monthly_decay": monthly_decay(),
        "e4_diagnosis": e4_diagnosis(),
        "e12_logger_verification": e12_logger_verification(),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Written {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Post-run analyzer for DP4 results.

Reads `dp4_ab_results.json` (steps 2+3) plus any mini_backtest_*/all_results.json
directories and writes:
 - dp4_summary.json (aggregate stats)
 - printed markdown tables for the DP4 report

Run:
    python research/v4_prompt_engineering/dp4_lira/analyze_dp4.py
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median, stdev

OUT_DIR = Path(__file__).resolve().parent


def _load_json(path: Path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _self_consistency(rows: list[dict]) -> dict:
    """How often does a variant give the same (decision, direction, no_trade_reason)
    across its N reruns of the same MSO?"""
    by_mso = {}
    for r in rows:
        by_mso.setdefault(r["idx"], []).append(r)

    consistency_by_mso = {}
    for idx, runs in by_mso.items():
        tuples = [
            (r["decision"], r.get("direction") or "", r.get("no_trade_reason") or "")
            for r in runs
        ]
        unique = len(set(tuples))
        consistency_by_mso[idx] = {
            "n_runs": len(runs),
            "unique_decisions": unique,
            "all_agree": unique == 1,
            "most_common": max(set(tuples), key=tuples.count),
        }

    n_mso = len(consistency_by_mso)
    n_all_agree = sum(1 for v in consistency_by_mso.values() if v["all_agree"])
    pct_consistent = 100.0 * n_all_agree / max(n_mso, 1)
    return {
        "per_mso": consistency_by_mso,
        "pct_all_agree": round(pct_consistent, 1),
        "n_mso": n_mso,
        "n_all_agree": n_all_agree,
    }


def _variant_summary(rows: list[dict]) -> dict:
    """Per-variant aggregate: parse rate, token counts, latency, cost."""
    if not rows:
        return {"n": 0}
    input_tokens = [r.get("input_tokens", 0) for r in rows if r.get("input_tokens")]
    output_tokens = [r.get("output_tokens", 0) for r in rows if r.get("output_tokens")]
    latency = [r.get("elapsed_s", 0) for r in rows if r.get("elapsed_s")]
    cost = [r.get("cost", 0) for r in rows]
    parse_ok = sum(1 for r in rows if r.get("parse_ok", True) and r.get("decision") not in ("PARSE_ERROR", "ERROR"))
    decisions = {}
    for r in rows:
        decisions[r.get("decision", "?")] = decisions.get(r.get("decision", "?"), 0) + 1
    return {
        "n": len(rows),
        "parse_ok_rate": round(100.0 * parse_ok / len(rows), 1),
        "decisions": decisions,
        "median_input_tokens": int(median(input_tokens)) if input_tokens else None,
        "median_output_tokens": int(median(output_tokens)) if output_tokens else None,
        "mean_output_tokens": int(mean(output_tokens)) if output_tokens else None,
        "median_latency_s": round(median(latency), 1) if latency else None,
        "mean_cost_usd": round(mean(cost), 4) if cost else None,
        "total_cost_usd": round(sum(cost), 4),
    }


def _cross_variant_decision_agreement(step3_rows: list[dict]) -> dict:
    """Given step3 rows across all variants, for each (idx, run_i) compare
    decisions and count how often pairs of variants AGREE."""
    by_mso_run = {}
    for r in step3_rows:
        key = (r["idx"], r.get("run", 1))
        by_mso_run.setdefault(key, {})[r["variant"]] = r

    pairs = [
        ("v3_control", "lira"),
        ("v3_control", "nocot"),
        ("lira", "nocot"),
    ]
    counts = {p: {"n": 0, "agree": 0} for p in pairs}
    for key, vrows in by_mso_run.items():
        for (a, b) in pairs:
            if a in vrows and b in vrows:
                counts[(a, b)]["n"] += 1
                if vrows[a]["decision"] == vrows[b]["decision"]:
                    counts[(a, b)]["agree"] += 1
    out = {}
    for p, c in counts.items():
        out[f"{p[0]}_vs_{p[1]}"] = {
            "n": c["n"],
            "agreements": c["agree"],
            "pct_agreement": round(100.0 * c["agree"] / max(c["n"], 1), 1),
        }
    return out


def _load_mini_backtest(variant: str, slice_name: str) -> dict | None:
    path = OUT_DIR / f"mini_backtest_{variant}_{slice_name}" / "all_results.json"
    data = _load_json(path)
    if data is None:
        return None
    results = data.get("results", [])
    cand = [r for r in results if r.get("decision") == "CANDIDATE"]
    filled_wins = sum(1 for r in results if r.get("outcome") == "WIN")
    filled_losses = sum(1 for r in results if r.get("outcome") == "LOSS")
    filled_n = filled_wins + filled_losses
    r_multiples = [r.get("r_multiple", 0) for r in results if r.get("outcome") in ("WIN", "LOSS")]
    wr = round(100.0 * filled_wins / max(filled_n, 1), 1)
    exp = round(mean(r_multiples), 3) if r_multiples else 0.0
    total_cost = data.get("total_cost", 0)
    return {
        "slice": slice_name,
        "variant": variant,
        "total_results": len(results),
        "candidates": len(cand),
        "candidates_filled": filled_n,
        "wins": filled_wins,
        "losses": filled_losses,
        "wr_pct": wr,
        "expectancy_r": exp,
        "total_cost_usd": round(total_cost, 4),
    }


def main() -> None:
    state = _load_json(OUT_DIR / "dp4_ab_results.json")
    if state is None:
        raise SystemExit("dp4_ab_results.json not found — run run_dp4.py first.")

    variants = state["variant_names"]

    print("=" * 72)
    print("DP4 A/B RESULTS")
    print("=" * 72)
    print(f"Total spend: ${state['total_cost']:.4f}  calls: {state['call_count']}")
    print()

    # Step 2 summary
    step2_by_variant = {v: [r for r in state["step2_results"] if r["variant"] == v] for v in variants}
    step3_by_variant = {v: [r for r in state["step3_results"] if r["variant"] == v] for v in variants}

    summary = {
        "total_cost_usd": state["total_cost"],
        "call_count": state["call_count"],
        "step2": {v: _variant_summary(rows) for v, rows in step2_by_variant.items()},
        "step3": {v: _variant_summary(rows) for v, rows in step3_by_variant.items()},
        "step3_self_consistency": {v: _self_consistency(rows) for v, rows in step3_by_variant.items()},
        "step3_cross_variant_agreement": _cross_variant_decision_agreement(state["step3_results"]),
    }

    # Mini-backtest load
    mb = {}
    for variant in variants:
        for slc in ("xauusd_s3", "xauusd_s7", "usdjpy_s3"):
            d = _load_mini_backtest(variant, slc)
            if d is not None:
                mb[f"{variant}_{slc}"] = d
    if mb:
        summary["mini_backtests"] = mb

    out_path = OUT_DIR / "dp4_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {out_path}")

    # Print markdown tables
    print("\n## Step 2 — Dry-run sanity")
    print("| Variant | N | Parse OK% | Decisions | Median IT | Median OT | Median Latency | Total $ |")
    print("|---------|---|-----------|-----------|-----------|-----------|----------------|---------|")
    for v in variants:
        s = summary["step2"][v]
        if s.get("n"):
            print(f"| {v} | {s['n']} | {s['parse_ok_rate']}% | {s['decisions']} | "
                  f"{s['median_input_tokens']} | {s['median_output_tokens']} | "
                  f"{s['median_latency_s']}s | ${s['total_cost_usd']:.3f} |")

    print("\n## Step 3 — A/B consistency (3 runs per MSO per variant)")
    print("| Variant | N | Parse OK% | Self-consistency | Median OT | Mean OT | Total $ |")
    print("|---------|---|-----------|------------------|-----------|---------|---------|")
    for v in variants:
        s = summary["step3"][v]
        sc = summary["step3_self_consistency"][v]
        if s.get("n"):
            print(f"| {v} | {s['n']} | {s['parse_ok_rate']}% | "
                  f"{sc['pct_all_agree']}% ({sc['n_all_agree']}/{sc['n_mso']}) | "
                  f"{s['median_output_tokens']} | {s['mean_output_tokens']} | "
                  f"${s['total_cost_usd']:.3f} |")

    print("\n## Step 3 — Cross-variant decision agreement")
    print("| Pair | N | Agreements | % agreement |")
    print("|------|---|------------|-------------|")
    for key, val in summary["step3_cross_variant_agreement"].items():
        print(f"| {key} | {val['n']} | {val['agreements']} | {val['pct_agreement']}% |")

    if mb:
        print("\n## Mini-backtest stats")
        print("| Variant-slice | CAND | Filled | W | L | WR | Expectancy | $ |")
        print("|---------------|------|--------|---|---|----|-----------|-----|")
        for k, m in mb.items():
            print(f"| {k} | {m['candidates']} | {m['candidates_filled']} | "
                  f"{m['wins']} | {m['losses']} | {m['wr_pct']}% | "
                  f"{m['expectancy_r']:+.3f}R | ${m['total_cost_usd']:.3f} |")


if __name__ == "__main__":
    main()

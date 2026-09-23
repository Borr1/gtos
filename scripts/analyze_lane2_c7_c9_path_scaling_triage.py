#!/usr/bin/env python3
"""Triage Lane 2 backlog items C-7 and C-9 from committed artifacts.

Research/tooling only. This script consolidates the Path-9 K54 diagnostics and
the raw-OHLC path-scaling artifact chain. It does not promote or alter live
trading behavior.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.methodology_alternatives import auc_rank_binary


OUT_JSON = ROOT / "research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.json"
OUT_MD = ROOT / "research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md"

K54_V2_CPCV = ROOT / "research/ml_program/models/k54_v2/cpcv_paired_results.json"
PATH9_AUDIT = ROOT / "research/ml_program/audit/_stat_reeval/q3_path9.json"
STAT_REEVAL = ROOT / "research/ml_program/audit/statistical_reevaluation.md"
V0_REPORT = ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md"
V2_FINAL = ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_FINAL_DISPOSITION_2026-05-02.md"
V2B_ROLLING = ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.json"
V2_CONFLUENCE = ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json"
V3_REPLAY = ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fold_ranges(fold_meta: list[dict[str, Any]]) -> list[tuple[int, int]]:
    ranges = []
    start = 0
    for row in fold_meta:
        n = int(row["n"])
        ranges.append((start, start + n))
        start += n
    return ranges


def aggregate_fold_auc_diffs(
    payload: dict[str, Any],
    *,
    path_key: str,
    candidate_prob_key: str,
    benchmark_prob_key: str,
) -> list[dict[str, Any]]:
    by_idx: dict[int, dict[str, Any]] = {}
    for path in payload.get(path_key, []):
        test_idx = path.get("test_idx") or []
        candidate = path.get(candidate_prob_key) or []
        benchmark = path.get(benchmark_prob_key) or []
        y_true = path.get("y_te") or []
        if not (len(test_idx) == len(candidate) == len(benchmark) == len(y_true)):
            continue
        for idx, cand_score, bench_score, y_val in zip(test_idx, candidate, benchmark, y_true):
            row = by_idx.setdefault(int(idx), {"candidate": [], "benchmark": [], "y": int(y_val)})
            row["candidate"].append(float(cand_score))
            row["benchmark"].append(float(bench_score))

    out = []
    for fold, (start, end) in enumerate(fold_ranges(payload.get("fold_meta", []))):
        meta = payload["fold_meta"][fold]
        fold_y = []
        fold_candidate = []
        fold_benchmark = []
        for idx in range(start, end):
            row = by_idx.get(idx)
            if not row:
                continue
            fold_y.append(int(row["y"]))
            fold_candidate.append(sum(row["candidate"]) / len(row["candidate"]))
            fold_benchmark.append(sum(row["benchmark"]) / len(row["benchmark"]))
        auc_candidate = auc_rank_binary(fold_y, fold_candidate)
        auc_benchmark = auc_rank_binary(fold_y, fold_benchmark)
        diff = None
        if auc_candidate.auc is not None and auc_benchmark.auc is not None:
            diff = auc_candidate.auc - auc_benchmark.auc
        out.append(
            {
                "fold": fold,
                "n": len(fold_y),
                "date_min": meta.get("date_min"),
                "date_max": meta.get("date_max"),
                "candidate_auc": auc_candidate.auc,
                "benchmark_auc": auc_benchmark.auc,
                "auc_diff": diff,
                "n_positive": auc_candidate.n_positive,
                "n_negative": auc_candidate.n_negative,
            }
        )
    return out


def path_diff_summary(k54_v2: dict[str, Any], path9_id: int) -> dict[str, Any]:
    rows = []
    for row in k54_v2.get("paths_fixed_hp", []):
        diff = finite(row.get("auc_diff"))
        rows.append({"path": int(row["path"]), "auc_diff": diff, "n_test": int(row.get("n_test", 0))})
    ranked = sorted([row for row in rows if row["auc_diff"] is not None], key=lambda row: row["auc_diff"], reverse=True)
    path9 = next(row for row in rows if row["path"] == path9_id)
    return {
        "path_rows": rows,
        "positive_path_count": sum(1 for row in rows if row["auc_diff"] is not None and row["auc_diff"] > 0),
        "negative_path_count": sum(1 for row in rows if row["auc_diff"] is not None and row["auc_diff"] < 0),
        "path9_rank_by_auc_diff": 1 + next(i for i, row in enumerate(ranked) if row["path"] == path9_id),
        "path9_auc_diff": path9["auc_diff"],
        "max_auc_diff": ranked[0]["auc_diff"],
        "min_auc_diff": ranked[-1]["auc_diff"],
    }


def summarize_path9(path9: dict[str, Any], fold_rows: list[dict[str, Any]], path_summary: dict[str, Any]) -> dict[str, Any]:
    n_test = int(path9["n_test"])
    month_counts = path9["month_counts"]
    symbol_counts = path9["symbol_counts"]
    group_aucs = path9["group_aucs"]
    symbol_aucs = path9["symbol_aucs"]
    path_folds = set(path9["test_fold_pair"])
    path_fold_rows = [row for row in fold_rows if row["fold"] in path_folds]
    other_fold_rows = [row for row in fold_rows if row["fold"] not in path_folds]
    positive_symbols = [
        symbol for symbol, row in symbol_aucs.items() if finite(row.get("auc_diff")) is not None and row["auc_diff"] > 0
    ]
    negative_symbols = [
        symbol for symbol, row in symbol_aucs.items() if finite(row.get("auc_diff")) is not None and row["auc_diff"] < 0
    ]
    positive_groups = [
        group for group, row in group_aucs.items() if finite(row.get("auc_diff")) is not None and row["auc_diff"] > 0
    ]
    feb_share = month_counts.get("2026-02", 0) / n_test
    top_symbol_share = max(symbol_counts.values()) / n_test

    return {
        "path_id": path9["path_id"],
        "n_test": n_test,
        "date_range": path9["date_range"],
        "test_fold_pair": path9["test_fold_pair"],
        "month_counts": month_counts,
        "feb_2026_share": feb_share,
        "symbol_counts": symbol_counts,
        "top_symbol_share": top_symbol_share,
        "direction_counts": path9["direction_counts"],
        "win_rate": path9["win_rate"],
        "group_auc_diffs": {group: row["auc_diff"] for group, row in group_aucs.items()},
        "symbol_auc_diffs": {symbol: row["auc_diff"] for symbol, row in symbol_aucs.items()},
        "positive_group_count": len(positive_groups),
        "group_count": len(group_aucs),
        "positive_symbol_count": len(positive_symbols),
        "negative_symbols": negative_symbols,
        "symbol_count": len(symbol_aucs),
        "path_level_auc_diff": path_summary["path9_auc_diff"],
        "path_rank_by_auc_diff": path_summary["path9_rank_by_auc_diff"],
        "path_fold_replication_rows": path_fold_rows,
        "non_path_fold_rows": other_fold_rows,
        "classification": "CROSS_COHORT_TEMPORAL_WINDOW_SIGNAL_NOT_SINGLE_SYMBOL",
        "replication_read": (
            "The Feb-heavy window is cross-cohort, but it does not replicate as a stable all-window effect: "
            "Path 9 is the strongest CPCV path, while 6 of 15 fixed-HP paths are negative and fold 4 is negative after the window."
        ),
    }


def summarize_c9(v2b: dict[str, Any], v2_confluence: dict[str, Any], v3: dict[str, Any]) -> dict[str, Any]:
    v2b_counters = v2b.get("scope_counters", {})
    fvg_summary = v3.get("summary", {}).get("V3_FVG_ONLY_RESCUE_RISK_BANK", {})
    fvg_concentration = (
        v3.get("concentration", {})
        .get("symbol_session_side", {})
        .get("V3_FVG_ONLY_RESCUE_RISK_BANK", {})
    )

    return {
        "completed_components": [
            {
                "component": "protocol_frozen",
                "artifact": rel(V0_REPORT),
                "status": "DONE",
                "result": "Raw-OHLC ablation/path-scaling protocol exists; V0 explicitly blocked L2 attribution and reentry.",
            },
            {
                "component": "v0_base_j46_lock_only",
                "artifact": rel(V0_REPORT),
                "status": "DONE",
                "result": "J46_J49_ONLY led at 0.05R cost with net_mean_r=0.190128; best lock-only minus J46=-0.019758 globally.",
            },
            {
                "component": "v2_structural_selector",
                "artifact": rel(V2_FINAL),
                "status": "DONE_DISCOVERY",
                "result": "STRUCT_SWING_PROTECTED_V2 beat J46 globally by +0.024511 net R at 0.05R cost, but concentration blocked promotion.",
            },
            {
                "component": "v2_confluence_deep_dive",
                "artifact": rel(V2_CONFLUENCE),
                "status": "ACCEPTED_CANDIDATE_DISCOVERY",
                "result": "FVG and OB confluence/disagreement pockets are positive same-dataset discoveries; Composite remains an over-lock warning.",
            },
            {
                "component": "v2b_forward_status_tool",
                "artifact": rel(V2B_ROLLING),
                "status": v2b.get("validation_status"),
                "result": "Prospective rows exist, but resolved post-cutoff OB-boundary/J46 pairs are still zero.",
            },
            {
                "component": "v3_exploratory_reentry_replay",
                "artifact": rel(V3_REPLAY),
                "status": "STRONGER_THAN_BASELINE_DISCOVERY_ONLY",
                "result": "V3_FVG_ONLY_RESCUE_RISK_BANK has mean_delta_vs_j46=+0.270259 on existing replay, but same-dataset discovery cannot validate reentry.",
            },
        ],
        "blockers": [
            "Deterministic L2 candidate reconstruction is still required for L2 on/off architecture attribution.",
            "V2b has 0 resolved post-cutoff OB-boundary/J46 pairs, so structural level quality is not forward-validated.",
            "Close-and-reenter path scaling needs pending lifecycle truth and original POI/pre-fill fields before risk accounting is trustworthy.",
            "Historical OHLC cost/slippage remains an R-sensitivity model, not measured broker cost.",
        ],
        "trigger": (
            "Resume C-9 when L2 reconstruction exists, V2b has resolved post-cutoff pairs that meet sample floors, "
            "and pending-lifecycle/pre-fill fields are joined for reentry accounting."
        ),
        "v2b_scope_counters": {
            "rows_after_cutoff": v2b_counters.get("rows_after_cutoff"),
            "wanted_variant_rows_seen": v2b_counters.get("wanted_variant_rows_seen"),
            "wanted_resolved_rows_after_cutoff": v2b_counters.get("wanted_resolved_rows_after_cutoff"),
        },
        "v3_fvg_only_rescue": {
            "eligible_n": fvg_summary.get("eligible_n"),
            "headline_resolved_n": fvg_summary.get("headline_resolved_n"),
            "mean_r": fvg_summary.get("mean_r"),
            "mean_delta_vs_j46": fvg_summary.get("mean_delta_vs_j46"),
            "top_symbol_session_side_share": fvg_concentration.get("top_share"),
        },
        "status": "BLOCKED_WITH_REASON",
        "classification": "PARTIAL_CHAIN_COMPLETE_BUT_C9_NOT_FULLY_EXECUTABLE",
    }


def build_payload() -> dict[str, Any]:
    k54_v2 = load_json(K54_V2_CPCV)
    path9 = load_json(PATH9_AUDIT)
    v2b = load_json(V2B_ROLLING)
    v2_confluence = load_json(V2_CONFLUENCE)
    v3 = load_json(V3_REPLAY)

    fold_rows = aggregate_fold_auc_diffs(
        k54_v2,
        path_key="paths_fixed_hp",
        candidate_prob_key="p_v2_te",
        benchmark_prob_key="p_v1_te",
    )
    path_summary = path_diff_summary(k54_v2, int(path9["path_id"]))
    c7 = summarize_path9(path9, fold_rows, path_summary)
    c9 = summarize_c9(v2b, v2_confluence, v3)

    task_classifications = {
        "C-7": {
            "status": "DONE",
            "artifact": rel(OUT_MD),
            "classification": "Path-9 deep-dive completed: Feb-heavy, cross-cohort temporal-window signal; replication scan shows fragility rather than stable all-window lift.",
            "promotion_allowed": False,
        },
        "C-9": {
            "status": "BLOCKED_WITH_REASON",
            "artifact": rel(OUT_MD),
            "classification": "Architecture/path-scaling chain is partially completed, but the full C-9 comparison is blocked by L2 reconstruction, unresolved V2b forward pairs, and missing lifecycle/pre-fill fields for reentry.",
            "blocked_by": "; ".join(c9["blockers"]),
            "trigger": c9["trigger"],
            "promotion_allowed": False,
        },
    }

    return {
        "schema_version": "lane2_c7_c9_path_scaling_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "source_files": [
            rel(K54_V2_CPCV),
            rel(PATH9_AUDIT),
            rel(STAT_REEVAL),
            rel(V0_REPORT),
            rel(V2_FINAL),
            rel(V2B_ROLLING),
            rel(V2_CONFLUENCE),
            rel(V3_REPLAY),
        ],
        "task_classifications": task_classifications,
        "c7_path9_deep_dive": c7,
        "c7_k54_v2_fixed_hp_path_summary": path_summary,
        "c7_fold_replication_scan": fold_rows,
        "c9_path_scaling_status": c9,
    }


def fmt_float(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return out


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    tasks = payload["task_classifications"]
    c7 = payload["c7_path9_deep_dive"]
    c9 = payload["c9_path_scaling_status"]
    path_summary = payload["c7_k54_v2_fixed_hp_path_summary"]

    fold_rows = [
        [
            row["fold"],
            row["date_min"],
            row["date_max"],
            row["n"],
            fmt_float(row["candidate_auc"]),
            fmt_float(row["benchmark_auc"]),
            fmt_float(row["auc_diff"]),
        ]
        for row in payload["c7_fold_replication_scan"]
    ]
    path_rows = [
        [row["path"], row["n_test"], fmt_float(row["auc_diff"])]
        for row in path_summary["path_rows"]
    ]
    component_rows = [
        [row["component"], row["status"], row["artifact"], row["result"]]
        for row in c9["completed_components"]
    ]

    lines = [
        "# Lane 2 C-7 / C-9 Path Scaling Triage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question",
        "",
        "Classify the remaining Lane 2 backlog items C-7 and C-9 from committed artifacts, closing only what is answered and converting the rest into precise blockers.",
        "",
        "## Classification",
        "",
        *table(
            ["id", "status", "classification", "blocker/trigger"],
            [
                [
                    item_id,
                    row["status"],
                    row["classification"],
                    row.get("blocked_by") or row.get("trigger") or "",
                ]
                for item_id, row in tasks.items()
            ],
        ),
        "",
        "## C-7 Path-9 Deep Dive",
        "",
        f"- Path-9 date range: `{c7['date_range'][0]}` to `{c7['date_range'][1]}`.",
        f"- Test rows: `{c7['n_test']}`; February 2026 share: `{fmt_float(c7['feb_2026_share'])}`.",
        f"- Top-symbol share: `{fmt_float(c7['top_symbol_share'])}`; positive groups: `{c7['positive_group_count']}/{c7['group_count']}`; positive symbols: `{c7['positive_symbol_count']}/{c7['symbol_count']}`.",
        f"- Path-level AUC diff: `{fmt_float(c7['path_level_auc_diff'])}`; rank among fixed-HP CPCV paths: `{c7['path_rank_by_auc_diff']}`.",
        f"- Classification: `{c7['classification']}`.",
        "",
        "Path 9 worked because the Feb-heavy Q1 2026 window lifted K54 v2 versus v1 across all four effective groups and six of seven symbols. It was not a single-symbol XAU artifact; XAGUSD was the only negative symbol-level diff.",
        "",
        "## C-7 Replication Scan",
        "",
        "Fold-level reconstruction averages each row's K54 v2/v1 prediction across the CPCV paths that tested that row, then recomputes paired AUC by chronological fold.",
        "",
        *table(["fold", "date min", "date max", "n", "K54 v2 AUC", "K54 v1 AUC", "diff"], fold_rows),
        "",
        "Fixed-HP CPCV path diffs:",
        "",
        *table(["path", "n", "AUC diff"], path_rows),
        "",
        c7["replication_read"],
        "",
        "C-7 is therefore closed as a diagnostic: the composition question is answered and the replication check says the effect is temporal-fragile, not a reusable all-window condition.",
        "",
        "## C-9 Path-Scaling Chain",
        "",
        *table(["component", "status", "artifact", "result"], component_rows),
        "",
        "## C-9 Blockers",
        "",
        *[f"- {blocker}" for blocker in c9["blockers"]],
        "",
        f"Trigger: {c9['trigger']}",
        "",
        "Current V2b counters:",
        "",
        *table(
            ["rows after cutoff", "wanted variant rows", "wanted resolved rows"],
            [
                [
                    c9["v2b_scope_counters"]["rows_after_cutoff"],
                    c9["v2b_scope_counters"]["wanted_variant_rows_seen"],
                    c9["v2b_scope_counters"]["wanted_resolved_rows_after_cutoff"],
                ]
            ],
        ),
        "",
        "The strongest current V3 branch remains discovery-only:",
        "",
        *table(
            ["variant", "eligible", "resolved", "mean R", "mean delta vs J46", "top group share"],
            [
                [
                    "V3_FVG_ONLY_RESCUE_RISK_BANK",
                    c9["v3_fvg_only_rescue"]["eligible_n"],
                    c9["v3_fvg_only_rescue"]["headline_resolved_n"],
                    fmt_float(c9["v3_fvg_only_rescue"]["mean_r"]),
                    fmt_float(c9["v3_fvg_only_rescue"]["mean_delta_vs_j46"]),
                    fmt_float(c9["v3_fvg_only_rescue"]["top_symbol_session_side_share"]),
                ]
            ],
        ),
        "",
        "## Ambiguity Ledger",
        "",
        "- C-7 uses existing K54 v2 CPCV artifacts; it does not open or relabel forward data.",
        "- C-9 has meaningful completed subcomponents, but the exact backlog request includes L2 on/off and close-and-reenter variants that are not executable to validation standard yet.",
        "- V3 positive discovery remains same-dataset and reentry-accounting-limited; it is not validation.",
        "- All path-scaling artifacts retain `NO_PROMOTION_VERDICT`.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(OUT_JSON))
    parser.add_argument("--output-md", default=str(OUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload()
    write_json(payload, Path(args.output_json))
    write_markdown(payload, Path(args.output_md))
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "classifications={}".format(
            {key: value["status"] for key, value in payload["task_classifications"].items()}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

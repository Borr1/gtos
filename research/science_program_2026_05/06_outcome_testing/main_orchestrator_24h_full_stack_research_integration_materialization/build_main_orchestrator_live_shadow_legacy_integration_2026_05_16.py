from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
OUT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)

INPUTS = {
    "live_state": Path(".context/LIVE_STATE.md"),
    "broker_actual_r_audit": Path("shadow_logs/broker_actual_r_audit.jsonl"),
    "trade_index_lifecycle_audit": Path("shadow_logs/trade_index_lifecycle_audit.jsonl"),
    "account_pnl_truth_reconciliation": Path("shadow_logs/account_pnl_truth_reconciliation.jsonl"),
    "account_history_deals_latest": Path("data/account_history/mt5_deals_2026-04-27_2026-05-11.jsonl"),
    "candidate_ltf_path_order": Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    "live_mechanical_strategy_shadow_outcomes": Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    "nofill_forward_source_capture": Path("shadow_logs/nofill_forward_source_capture.jsonl"),
    "scid_forward_source_capture": Path("shadow_logs/scid_forward_source_capture.jsonl"),
    "fvg_ob_confluence_audit": Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
    "sierra_confluence_source_status": Path("shadow_logs/sierra_confluence_source_status.jsonl"),
    "sierra_depth_feature_snapshots": Path("shadow_logs/sierra_depth_feature_snapshots.jsonl"),
    "sierra_proxy_registry_status": Path("shadow_logs/sierra_proxy_registry_status.jsonl"),
    "v2b_forward_pair_resolution_audit": Path("shadow_logs/v2b_forward_pair_resolution_audit.jsonl"),
    "j46_j49_audit": Path("research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json"),
    "s79_side_aware_context": Path("research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json"),
    "v2_structural_selector": Path("research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json"),
    "v2b_forward_audit": Path("research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json"),
    "fvg_ob_confluence_program": Path("research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json"),
    "k55_shadow": Path("research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json"),
    "nas100_orderflow": Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json"),
    "sierra_depth": Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json"),
    "gbpjpy_proxy_gap": Path("research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json"),
    "live_shadow_opportunity_summary": Path("research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json"),
    "live_shadow_data_health": Path("research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json"),
}

OUTPUTS = {
    "input_snapshot": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_INPUT_SNAPSHOT_{DATE}.json",
    "exact_proxy_ledger": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_EXACT_PROXY_R_LEDGER_{DATE}.jsonl",
    "duplicate_aware_summary": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_DUPLICATE_AWARE_SUMMARY_{DATE}.json",
    "legacy_decision_ledger": OUT_DIR / f"MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl",
    "summary_md": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_INTEGRATION_SUMMARY_{DATE}.md",
    "manifest": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_OUTPUT_MANIFEST_{DATE}.json",
}

PATH_ORDER_PROXY_R = {
    "entry_then_tp1_before_sl": 1.5,
    "entry_then_tp1": 1.5,
    "entry_then_sl_before_tp1": -1.0,
    "entry_then_sl": -1.0,
    "tp1_area_reached_without_entry_touch": 0.0,
    "no_entry_touch_by_ltf_asof": 0.0,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(*parts: Any) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_no, {"_parse_error": str(exc), "_raw": line[:500]}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            f.write("\n")


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "positive": sum(1 for v in values if v > 0),
        "negative": sum(1 for v in values if v < 0),
        "zero": sum(1 for v in values if v == 0),
    }


def latest_by_key(rows: list[dict[str, Any]], key_fields: list[str], time_field: str) -> dict[tuple[Any, ...], dict[str, Any]]:
    latest: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        if key not in latest or str(row.get(time_field) or "") >= str(latest[key].get(time_field) or ""):
            latest[key] = row
    return latest


def build_input_snapshot() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "inputs": {
            label: {
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "sha256": sha256_file(path),
            }
            for label, path in INPUTS.items()
        },
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def materialize_exact_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    broker_seen: dict[str, dict[str, Any]] = {}
    for line_no, row in iter_jsonl(INPUTS["broker_actual_r_audit"]):
        if "_parse_error" in row:
            continue
        actual_r = safe_float(row.get("broker_actual_r"))
        if actual_r is None or not row.get("actual_r_claim_allowed"):
            continue
        key = str(row.get("ticket") or row.get("trade_id") or row.get("row_key"))
        if key in broker_seen:
            continue
        broker_seen[key] = row
        rows.append(
            {
                "result_id": "exact_broker_actual_r:" + stable_id(key),
                "result_layer": "broker_actual_r_audit_unique",
                "source_file": str(INPUTS["broker_actual_r_audit"]),
                "source_sha256": sha256_file(INPUTS["broker_actual_r_audit"]),
                "source_line_no": line_no,
                "unique_trade_key": key,
                "symbol": row.get("symbol"),
                "trade_id": row.get("trade_id"),
                "ticket": row.get("ticket"),
                "decision_time_utc": row.get("decision_time_utc"),
                "exact_r": actual_r,
                "proxy_r": None,
                "claim_boundary": "Exact broker actual-R claim allowed only for this unique ticket/trade row.",
                "validation_safe": False,
                "live_effect": False,
            }
        )

    trade_seen: dict[str, dict[str, Any]] = {}
    for line_no, row in iter_jsonl(INPUTS["trade_index_lifecycle_audit"]):
        if "_parse_error" in row:
            continue
        actual_r = safe_float(row.get("actual_r"))
        if actual_r is None:
            continue
        key = str(row.get("trade_record_trade_id") or row.get("trade_id") or row.get("row_key"))
        if key in trade_seen:
            continue
        trade_seen[key] = row
        rows.append(
            {
                "result_id": "exact_trade_index_actual_r:" + stable_id(key),
                "result_layer": "trade_index_lifecycle_actual_r_unique",
                "source_file": str(INPUTS["trade_index_lifecycle_audit"]),
                "source_sha256": sha256_file(INPUTS["trade_index_lifecycle_audit"]),
                "source_line_no": line_no,
                "unique_trade_key": key,
                "symbol": row.get("symbol"),
                "candidate_id": row.get("candidate_id"),
                "trade_id": row.get("trade_record_trade_id"),
                "decision_time_utc": row.get("decision_time_utc"),
                "exact_r": actual_r,
                "proxy_r": None,
                "claim_boundary": "Trade-index actual-R row; duplicate-aware count is unique trade_record_trade_id.",
                "validation_safe": False,
                "live_effect": False,
            }
        )

    deal_profit_values: list[float] = []
    for _line_no, row in iter_jsonl(INPUTS["account_history_deals_latest"]):
        profit = safe_float(row.get("profit"))
        if profit is not None:
            deal_profit_values.append(profit)

    summary = {
        "broker_actual_r_unique_trades": summarize([safe_float(r.get("exact_r")) for r in rows if r["result_layer"] == "broker_actual_r_audit_unique"]),
        "trade_index_actual_r_unique_trades": summarize([safe_float(r.get("exact_r")) for r in rows if r["result_layer"] == "trade_index_lifecycle_actual_r_unique"]),
        "account_history_deal_rows": len(deal_profit_values),
        "account_history_profit_sum": sum(deal_profit_values) if deal_profit_values else None,
        "exact_claim_boundary": "Exact/account R remains sparse. Do not infer exact R beyond unique broker/trade-index/account-history rows.",
    }
    return rows, summary


def materialize_proxy_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    ltf_rows: list[dict[str, Any]] = []
    for line_no, row in iter_jsonl(INPUTS["candidate_ltf_path_order"]):
        if "_parse_error" in row:
            continue
        label = row.get("path_order_label")
        if label not in PATH_ORDER_PROXY_R:
            continue
        proxy_r = PATH_ORDER_PROXY_R[label]
        record = {
            **row,
            "_line_no": line_no,
            "_proxy_r": proxy_r,
        }
        ltf_rows.append(record)
    ltf_latest = latest_by_key(ltf_rows, ["candidate_id"], "asof_latest_candle_utc")
    ltf_raw_values = [r["_proxy_r"] for r in ltf_rows]
    ltf_dedup_values = [r["_proxy_r"] for r in ltf_latest.values()]
    rows.extend(
        [
            {
                "result_id": "proxy_live_ltf_path_order_raw:" + stable_id("raw"),
                "result_layer": "candidate_ltf_path_order_raw",
                "source_file": str(INPUTS["candidate_ltf_path_order"]),
                "source_sha256": sha256_file(INPUTS["candidate_ltf_path_order"]),
                "exact_r": None,
                "proxy_r": summarize(ltf_raw_values).get("mean"),
                "proxy_r_summary": summarize(ltf_raw_values),
                "duplicate_policy": "raw_row_count_not_sample_size",
                "validation_safe": False,
                "live_effect": False,
            },
            {
                "result_id": "proxy_live_ltf_path_order_duplicate_aware:" + stable_id("candidate_latest"),
                "result_layer": "candidate_ltf_path_order_duplicate_aware_candidate_latest",
                "source_file": str(INPUTS["candidate_ltf_path_order"]),
                "source_sha256": sha256_file(INPUTS["candidate_ltf_path_order"]),
                "exact_r": None,
                "proxy_r": summarize(ltf_dedup_values).get("mean"),
                "proxy_r_summary": summarize(ltf_dedup_values),
                "duplicate_policy": "latest_computable_row_per_candidate_id",
                "unique_candidates": len(ltf_latest),
                "validation_safe": False,
                "live_effect": False,
            },
        ]
    )

    strategy_rows: list[dict[str, Any]] = []
    for line_no, row in iter_jsonl(INPUTS["live_mechanical_strategy_shadow_outcomes"]):
        if "_parse_error" in row:
            continue
        proxy_r = safe_float(row.get("strategy_proxy_r"))
        if proxy_r is None:
            continue
        strategy_rows.append({**row, "_line_no": line_no, "_proxy_r": proxy_r})
    strategy_latest = latest_by_key(strategy_rows, ["candidate_id", "strategy_id"], "asof_latest_candle_utc")
    by_strategy_raw: dict[str, list[float]] = defaultdict(list)
    by_strategy_latest: dict[str, list[float]] = defaultdict(list)
    for row in strategy_rows:
        by_strategy_raw[str(row.get("strategy_id"))].append(row["_proxy_r"])
    for row in strategy_latest.values():
        by_strategy_latest[str(row.get("strategy_id"))].append(row["_proxy_r"])
    for strategy_id in sorted(by_strategy_raw):
        rows.append(
            {
                "result_id": "proxy_live_strategy_raw:" + stable_id(strategy_id),
                "result_layer": "live_mechanical_strategy_shadow_outcomes_raw",
                "source_file": str(INPUTS["live_mechanical_strategy_shadow_outcomes"]),
                "source_sha256": sha256_file(INPUTS["live_mechanical_strategy_shadow_outcomes"]),
                "strategy_id": strategy_id,
                "exact_r": None,
                "proxy_r": summarize(by_strategy_raw[strategy_id]).get("mean"),
                "proxy_r_summary": summarize(by_strategy_raw[strategy_id]),
                "duplicate_policy": "raw_strategy_rows_not_sample_size",
                "validation_safe": False,
                "live_effect": False,
            }
        )
        rows.append(
            {
                "result_id": "proxy_live_strategy_duplicate_aware:" + stable_id(strategy_id),
                "result_layer": "live_mechanical_strategy_shadow_outcomes_duplicate_aware",
                "source_file": str(INPUTS["live_mechanical_strategy_shadow_outcomes"]),
                "source_sha256": sha256_file(INPUTS["live_mechanical_strategy_shadow_outcomes"]),
                "strategy_id": strategy_id,
                "exact_r": None,
                "proxy_r": summarize(by_strategy_latest[strategy_id]).get("mean"),
                "proxy_r_summary": summarize(by_strategy_latest[strategy_id]),
                "duplicate_policy": "latest_computable_row_per_candidate_id_strategy_id",
                "validation_safe": False,
                "live_effect": False,
            }
        )

    summary = {
        "candidate_ltf_path_order": {
            "raw": summarize(ltf_raw_values),
            "duplicate_aware_latest_per_candidate": summarize(ltf_dedup_values),
            "candidate_universe": len({r.get("candidate_id") for r in ltf_rows}),
            "path_order_counts": dict(Counter(r.get("path_order_label") for r in ltf_rows)),
        },
        "live_mechanical_strategy_shadow_outcomes": {
            "raw": summarize([r["_proxy_r"] for r in strategy_rows]),
            "duplicate_aware_latest_per_candidate_strategy": summarize([r["_proxy_r"] for r in strategy_latest.values()]),
            "candidate_universe": len({r.get("candidate_id") for r in strategy_rows}),
            "strategy_pair_universe": len(strategy_latest),
            "by_strategy_raw": {k: summarize(v) for k, v in sorted(by_strategy_raw.items())},
            "by_strategy_duplicate_aware": {k: summarize(v) for k, v in sorted(by_strategy_latest.items())},
        },
    }
    return rows, summary


def json_input_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"exists": True, "parse_error": str(exc)}
    return {
        "exists": True,
        "top_level_keys": sorted(data.keys())[:20] if isinstance(data, dict) else None,
        "sha256": sha256_file(path),
    }


def build_legacy_decisions() -> list[dict[str, Any]]:
    specs = [
        (
            "V2_OB_BOUNDARY_PATH_SCALING",
            "REPLAY_DUPLICATE_AWARE_OB_BOUNDARY_ONLY",
            "REPLAY_NOW_WITH_LOCAL_DATA_OR_REDESIGN_STRESS",
            ["v2_structural_selector", "live_shadow_opportunity_summary"],
            "V2 structural signal remains usable only as duplicate-aware replay material; composite/swing promotion is killed.",
        ),
        (
            "V2B_FORWARD",
            "RECOMPUTE_DUPLICATE_AWARE_SUMMARIES_NO_PROMOTION",
            "REPLAY_NOW_WITH_LOCAL_DATA_OR_REDESIGN_STRESS",
            ["v2b_forward_audit", "v2b_forward_pair_resolution_audit"],
            "Forward rows are rich but duplicate inflation and absent broker actual-R prevent promotion.",
        ),
        (
            "FVG_OB_CONFLUENCE",
            "REPLAY_EXACT_COUNTABLE_SUBSET_ONLY_NO_PROMOTION",
            "REPLAY_NOW_WITH_LOCAL_DATA_OR_REDESIGN_STRESS",
            ["fvg_ob_confluence_program", "fvg_ob_confluence_audit"],
            "Both-fire denominator is too small and many rows lack FVG entry/lock metadata.",
        ),
        (
            "J46_J49_POLICY",
            "KEEP_AND_REPAIR_XAGUSD_ACCOUNT_HISTORY_JOIN",
            "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT",
            ["j46_j49_audit", "trade_index_lifecycle_audit"],
            "Policy is already implemented/enabled; remaining action is account-history join repair for the XAGUSD row.",
        ),
        (
            "S79_SIDE_AWARE",
            "KEEP_S79_AND_SIDE_AWARE_KILL_LITERAL_VOL_RANK_GATE",
            "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT",
            ["s79_side_aware_context"],
            "S79 and side-aware context remain supported; literal vol-rank side-aware gate is killed.",
        ),
        (
            "K54_K55",
            "KILL_K54_SAME_COHORT_ITERATION_BUILD_K55_ONLY_AFTER_LABEL_BUNDLE",
            "KILL_OR_AVOID_WITH_EVIDENCE",
            ["k55_shadow"],
            "K54 architecture iteration on same cohort is killed; K55 needs target/feature bundle plus broker labels.",
        ),
        (
            "NOFILL_FORWARD_SOURCE_CAPTURE",
            "UPGRADE_CAPTURE_CONTRACT_NOT_SCORE_ROWS",
            "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT",
            ["nofill_forward_source_capture", "scid_forward_source_capture"],
            "No-fill rows are source-control infrastructure; capture entry-touch spread, broker pending-order truth, cancel/expiry reason, and event order.",
        ),
        (
            "SIERRA_ORDERFLOW",
            "KEEP_NQ_YM_DIAGNOSTIC_ONLY_BLOCK_XAGUSD_GBPJPY_EDGE_INPUT",
            "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
            ["nas100_orderflow", "sierra_depth", "gbpjpy_proxy_gap", "sierra_confluence_source_status"],
            "Sierra/orderflow remains diagnostic/source context; no live filter and no GBPJPY direct proxy.",
        ),
        (
            "LIVE_SHADOW_STRATEGY_FOLLOW",
            "USE_FOR_DUPLICATE_AWARE_REPLAY_AND_FAILURE_INTELLIGENCE_ONLY",
            "REPLAY_NOW_WITH_LOCAL_DATA_OR_REDESIGN_STRESS",
            ["live_shadow_opportunity_summary", "live_shadow_data_health", "live_mechanical_strategy_shadow_outcomes"],
            "Live/shadow rows are useful for duplicate-aware replay and failure intelligence but not promotion.",
        ),
        (
            "TRAILING_STOP_EXIT_VARIANT",
            "QUEUE_DEFAULT_OFF_SHADOW_LOGGER_NOT_LIVE_SWITCH",
            "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT",
            [],
            "Trailing stop remains a strong shadow-logger candidate, not a live switch without OOS shadow.",
        ),
        (
            "PARTIAL_CLOSE_EXPANSION",
            "DO_NOT_QUEUE_NEW_PARTIAL_VARIANTS_KEEP_EXISTING_SHADOW_ONLY",
            "KILL_OR_AVOID_WITH_EVIDENCE",
            [],
            "Partial-close expansion is not supported; keep existing Variant C shadow only.",
        ),
        (
            "PORTFOLIO_VOL_MANAGED_SIZING",
            "KILL_PORTFOLIO_BARROSO_NAS100_ONLY_DEFAULT_OFF_SHADOW",
            "KILL_OR_AVOID_WITH_EVIDENCE",
            [],
            "Portfolio-wide vol-managed sizing fails; NAS100-only can be shadowed default-off.",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for family, decision, bucket, labels, summary in specs:
        paths = [INPUTS[label] for label in labels]
        rows.append(
            {
                "decision_id": "legacy_decision:" + stable_id(family),
                "family": family,
                "decision": decision,
                "bucket": bucket,
                "artifact_paths_checked": [str(p) for p in paths],
                "input_hashes": {str(p): sha256_file(p) for p in paths},
                "evidence_summary": summary,
                "safe_flags": {
                    "NO_PROMOTION_VERDICT": True,
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
            }
        )
    return rows


def write_summary_md(summary: dict[str, Any]) -> None:
    lines = [
        "# Main Orchestrator Live/Shadow And Legacy Integration",
        "",
        f"Generated: {summary['generated_utc']}",
        "",
        "## Exact R Boundary",
        "",
        f"- Broker actual-R unique trades: {summary['exact']['broker_actual_r_unique_trades']['count']}",
        f"- Trade-index actual-R unique trades: {summary['exact']['trade_index_actual_r_unique_trades']['count']}",
        f"- Account-history deal rows / profit sum: {summary['exact']['account_history_deal_rows']} / {summary['exact']['account_history_profit_sum']}",
        "",
        "## Proxy R Surfaces",
        "",
        f"- LTF path raw rows / mean R: {summary['proxy']['candidate_ltf_path_order']['raw']['count']} / {summary['proxy']['candidate_ltf_path_order']['raw']['mean']}",
        f"- LTF path duplicate-aware candidates / mean R: {summary['proxy']['candidate_ltf_path_order']['duplicate_aware_latest_per_candidate']['count']} / {summary['proxy']['candidate_ltf_path_order']['duplicate_aware_latest_per_candidate']['mean']}",
        f"- Live strategy raw rows / mean R: {summary['proxy']['live_mechanical_strategy_shadow_outcomes']['raw']['count']} / {summary['proxy']['live_mechanical_strategy_shadow_outcomes']['raw']['mean']}",
        f"- Live strategy duplicate-aware pairs / mean R: {summary['proxy']['live_mechanical_strategy_shadow_outcomes']['duplicate_aware_latest_per_candidate_strategy']['count']} / {summary['proxy']['live_mechanical_strategy_shadow_outcomes']['duplicate_aware_latest_per_candidate_strategy']['mean']}",
        "",
        "## Decision Boundary",
        "",
        "Live/shadow and legacy rows are research-only integration evidence. They do not authorize promotion, validation-safe claims, or live behavior changes.",
        "",
    ]
    OUTPUTS["summary_md"].write_text("\n".join(lines), encoding="utf-8", newline="\n")


def build_manifest() -> dict[str, Any]:
    artifacts = []
    for label, path in OUTPUTS.items():
        if label == "manifest":
            continue
        artifacts.append(
            {
                "label": label,
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_input_snapshot()
    exact_rows, exact_summary = materialize_exact_rows()
    proxy_rows, proxy_summary = materialize_proxy_rows()
    legacy_rows = build_legacy_decisions()

    result_rows = exact_rows + proxy_rows
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": snapshot["generated_utc"],
        "exact": exact_summary,
        "proxy": proxy_summary,
        "counts": {
            "exact_proxy_ledger_rows": len(result_rows),
            "legacy_decision_rows": len(legacy_rows),
            "exact_result_rows": len(exact_rows),
            "proxy_result_rows": len(proxy_rows),
        },
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }

    write_json(OUTPUTS["input_snapshot"], snapshot)
    write_jsonl(OUTPUTS["exact_proxy_ledger"], result_rows)
    write_json(OUTPUTS["duplicate_aware_summary"], summary)
    write_jsonl(OUTPUTS["legacy_decision_ledger"], legacy_rows)
    write_summary_md(summary)
    write_json(OUTPUTS["manifest"], build_manifest())
    print(json.dumps({"ok": True, "counts": summary["counts"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

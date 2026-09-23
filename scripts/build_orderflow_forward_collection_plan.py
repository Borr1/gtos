#!/usr/bin/env python3
"""Build the next disciplined orderflow collection plan.

Research/tooling only. This script does not fetch Databento data. It reads the
current orderflow manifest, diagnostics, coverage audits, and current
candidate-feature log to decide what data should be collected next and what
should remain blocked.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc  # noqa: E402


RESEARCH_DIR = "research/databento_orderflow_capture_2026-05-02"
DEFAULT_SOURCE_LOG = "shadow_logs/candidate_features_log.jsonl"
DEFAULT_MANIFEST = f"{RESEARCH_DIR}/ORDERFLOW_EVENT_WINDOW_MANIFEST_PROXY_EXPANDED_2026-05-02.json"
DEFAULT_TRADES_FETCH_PLAN = f"{RESEARCH_DIR}/ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_PROXY_EXPANDED_2026-05-02.json"
DEFAULT_MBP1_FETCH_PLAN = f"{RESEARCH_DIR}/ORDERFLOW_DEPTH_MBP1_PILOT_FETCH_PLAN_OF_DATA_7_2026-05-02.json"
DEFAULT_MBP10_FETCH_PLAN = f"{RESEARCH_DIR}/ORDERFLOW_DEPTH_MBP10_ESTIMATE_OF_DATA_9_2026-05-02.json"
DEFAULT_TRADES_DIAG = f"{RESEARCH_DIR}/ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_PROXY_EXPANDED_2026-05-02.json"
DEFAULT_MBP1_DIAG = f"{RESEARCH_DIR}/ORDERFLOW_DEPTH_MBP1_FEATURE_DIAGNOSTIC_OF_DATA_8_2026-05-02.json"
DEFAULT_MBP10_DIAG = f"{RESEARCH_DIR}/ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02.json"
DEFAULT_COVERAGE_AUDIT = f"{RESEARCH_DIR}/ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_PROXY_EXPANDED_2026-05-02.json"
DEFAULT_LIMIT_RECON = f"{RESEARCH_DIR}/ORDERFLOW_LIMIT_INTENT_RECONCILIATION_AUDIT_OF_DATA_11_2026-05-02.json"
DEFAULT_NAS_READINESS = f"{RESEARCH_DIR}/ORDERFLOW_NAS100_HYPOTHESIS_READINESS_AUDIT_OF_DATA_12_2026-05-02.json"
DEFAULT_OUTPUT_JSON = f"{RESEARCH_DIR}/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_13_2026-05-02.json"
DEFAULT_OUTPUT_MD = f"{RESEARCH_DIR}/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_13_2026-05-02.md"


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_optional_json(path: Path | str) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    return load_json(p)


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _sorted_counter(values: list[Any]) -> dict[str, int]:
    return dict(sorted((str(key), value) for key, value in Counter(values).items()))


def _event_class_count(group: dict[str, Any], event_class: str) -> int:
    total = 0
    for item in group.get("event_classes") or []:
        if len(item) >= 2 and item[0] == event_class:
            total += int(item[1])
    return total


def _is_after_cap(value: str | None, cap: str | None) -> bool:
    if not value or not cap:
        return False
    return value >= cap


def summarize_source_log(rows: list[dict[str, Any]], supported_symbols: set[str], available_end_utc: str | None) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("decision") == "CANDIDATE"]
    supported_candidates = [row for row in candidates if row.get("symbol") in supported_symbols]
    unsupported_candidates = [row for row in candidates if row.get("symbol") not in supported_symbols]
    post_cap_rows = [
        row for row in rows if _is_after_cap(row.get("candle_close_utc") or row.get("timestamp_utc"), available_end_utc)
    ]
    post_cap_candidates = [row for row in post_cap_rows if row.get("decision") == "CANDIDATE"]
    return {
        "rows_loaded_current": len(rows),
        "available_end_utc_from_manifest": available_end_utc,
        "rows_after_available_end": len(post_cap_rows),
        "candidates_after_available_end": len(post_cap_candidates),
        "symbols": _sorted_counter([row.get("symbol") or "none" for row in rows]),
        "candidate_symbols": _sorted_counter([row.get("symbol") or "none" for row in candidates]),
        "supported_candidate_count": len(supported_candidates),
        "unsupported_candidate_count": len(unsupported_candidates),
        "unsupported_candidate_symbols": _sorted_counter([row.get("symbol") or "none" for row in unsupported_candidates]),
    }


def summarize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    events = manifest.get("events") or []
    groups = manifest.get("fetch_groups") or []
    candidate_events = [row for row in events if row.get("event_class") == "candidate"]
    candidate_groups = [group for group in groups if _event_class_count(group, "candidate") > 0]
    return {
        "manifest_schema_version": manifest.get("schema_version"),
        "rows_loaded_at_manifest_build": (manifest.get("inputs") or {}).get("rows_loaded"),
        "available_end_utc": (manifest.get("inputs") or {}).get("available_end_utc"),
        "supported_symbol_map": (manifest.get("inputs") or {}).get("supported_symbol_map") or {},
        "event_count": len(events),
        "candidate_event_count": len(candidate_events),
        "candidate_events_by_symbol": _sorted_counter([row.get("symbol") or "none" for row in candidate_events]),
        "fetch_group_count": len(groups),
        "candidate_fetch_groups": [
            {
                "group_id": group.get("group_id"),
                "symbols": group.get("gtos_symbols") or [],
                "candidate_events": _event_class_count(group, "candidate"),
                "event_count": group.get("event_count"),
                "start_utc": group.get("start_utc"),
                "end_utc": group.get("end_utc"),
            }
            for group in candidate_groups
        ],
    }


def summarize_fetch_plan(fetch_plan: dict[str, Any] | None) -> dict[str, Any]:
    if not fetch_plan:
        return {"loaded": False}
    statuses = Counter(row.get("status") for row in fetch_plan.get("groups") or [])
    return {
        "loaded": True,
        "executed": fetch_plan.get("executed"),
        "blocked": fetch_plan.get("blocked"),
        "schema": (fetch_plan.get("inputs") or {}).get("schema"),
        "groups": len(fetch_plan.get("groups") or []),
        "status_counts": dict(sorted((str(k), v) for k, v in statuses.items())),
        "total_estimated_cost_usd": fetch_plan.get("total_estimated_cost_usd"),
    }


def summarize_feature_diag(diag: dict[str, Any] | None) -> dict[str, Any]:
    if not diag:
        return {"loaded": False}
    rows = [
        row
        for row in diag.get("feature_rows") or []
        if row.get("is_primary_proxy") and row.get("data_status") == "ok"
    ]
    candidate_rows = [row for row in rows if row.get("event_class") == "candidate"]
    context_rows = [row for row in rows if row.get("event_class") != "candidate"]
    synthetic_rows = [row for row in candidate_rows if row.get("candidate__synthetic_realized_r") is not None]
    return {
        "loaded": True,
        "primary_ok_rows": len(rows),
        "candidate_rows": len(candidate_rows),
        "context_rows": len(context_rows),
        "candidate_synthetic_rows": len(synthetic_rows),
        "candidate_synthetic_winners": sum(float(row["candidate__synthetic_realized_r"]) > 0 for row in synthetic_rows),
        "candidate_synthetic_losers": sum(float(row["candidate__synthetic_realized_r"]) <= 0 for row in synthetic_rows),
        "candidate_rows_by_symbol": _sorted_counter([row.get("symbol") or "none" for row in candidate_rows]),
    }


def coverage_by_symbol(coverage: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in coverage.get("audit_rows") or []:
        symbol = row.get("symbol") or "none"
        bucket = out.setdefault(
            symbol,
            {
                "rows": 0,
                "synthetic_labels": 0,
                "actual_r": 0,
                "synthetic_outcomes": Counter(),
                "coverage_classes": Counter(),
                "final_outcomes": Counter(),
            },
        )
        bucket["rows"] += 1
        bucket["synthetic_labels"] += bool(row.get("synthetic_realized_r_available"))
        bucket["actual_r"] += bool(row.get("actual_realized_r_available"))
        bucket["synthetic_outcomes"][row.get("synthetic_outcome") or "none"] += 1
        bucket["coverage_classes"][row.get("coverage_class") or "none"] += 1
        bucket["final_outcomes"][row.get("final_outcome") or "none"] += 1
    for bucket in out.values():
        bucket["synthetic_outcomes"] = dict(sorted(bucket["synthetic_outcomes"].items()))
        bucket["coverage_classes"] = dict(sorted(bucket["coverage_classes"].items()))
        bucket["final_outcomes"] = dict(sorted(bucket["final_outcomes"].items()))
    return dict(sorted(out.items()))


def build_collection_actions(
    *,
    manifest_summary: dict[str, Any],
    coverage_summary: dict[str, Any],
    nas_readiness: dict[str, Any],
    limit_recon: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    nas_gates = (nas_readiness.get("readiness_gates") or {}).get("failed") or []
    nas_labels = nas_readiness.get("label_counts") or {}
    limit_counts = (limit_recon or {}).get("counts") or (limit_recon or {}).get("synthesis") or {}
    return [
        {
            "action_id": "A1_NAS100_FORWARD_LABEL_AND_DEPTH_COLLECTION",
            "priority": 1,
            "scope": "NAS100 GTOS CANDIDATE rows plus pre-declared matched context rows",
            "current_evidence": {
                "manifest_candidate_events": (manifest_summary.get("candidate_events_by_symbol") or {}).get("NAS100", 0),
                "synthetic_winners": nas_labels.get("synthetic_winners"),
                "synthetic_losers": nas_labels.get("synthetic_losers"),
                "actual_r": (coverage_summary.get("NAS100") or {}).get("actual_r", 0),
                "failed_readiness_gates": nas_gates,
            },
            "data_policy": "Forward collect trades + MBP-1 for every new supported NAS100 candidate; collect MBP-10 only for pre-declared candidate/comparator windows.",
            "cost_policy": "Estimate before execution; MBP-10 is targeted only, not broad structural-context collection.",
            "status": "COLLECT_FORWARD_NOT_REPLAY",
            "reason": "The current NAS100 clue is real enough for forensics but has winner n=1, actual-R n=1, and MBP-10 candidate n below gate.",
        },
        {
            "action_id": "A2_XAUUSD_LIMIT_INTENT_TELEMETRY",
            "priority": 2,
            "scope": "XAUUSD LIMIT_PLACED rows and future pending-limit lifecycle rows",
            "current_evidence": {
                "limit_rows_audited": limit_counts.get("limit_rows_audited", 0),
                "broker_actual_r_rows": limit_counts.get("broker_actual_r_rows", 0),
                "counterfactual_m1_tp_rows": limit_counts.get("counterfactual_m1_tp_rows", 0),
            },
            "data_policy": "Do not fetch more market data for the audited historical row; the missing evidence is live pending-intent candle telemetry.",
            "cost_policy": "Zero Databento spend until telemetry exists; the row is an execution-forensics issue, not an orderflow-alpha label.",
            "status": "BLOCKED_BY_MISSING_LIVE_TELEMETRY",
            "reason": "The historical XAUUSD row has no broker-fill evidence despite counterfactual M1 TP; it cannot be converted into actual R.",
        },
        {
            "action_id": "A3_XAUUSD_CONTINUATION_CONTRAST",
            "priority": 3,
            "scope": "XAUUSD CANDIDATE rows",
            "current_evidence": {
                "manifest_candidate_events": (manifest_summary.get("candidate_events_by_symbol") or {}).get("XAUUSD", 0),
                "coverage": coverage_summary.get("XAUUSD", {}),
            },
            "data_policy": "Keep trades collection for new XAUUSD candidates; add MBP-1/MBP-10 only after both winner and loser labels exist.",
            "cost_policy": "Avoid depth spend on unlabeled May 1 rows until candidate/outcome join catches up.",
            "status": "WAIT_FOR_LABEL_CONTRAST",
            "reason": "The current XAUUSD joined sample is two synthetic winners and zero losers, which cannot identify a continuation-quality rule.",
        },
        {
            "action_id": "A4_UNSUPPORTED_SYMBOL_PROXY_MAPPING",
            "priority": 4,
            "scope": "Symbols in current candidate-feature log without validated CME proxy mapping",
            "current_evidence": {},
            "data_policy": "Do not pull futures data for unsupported symbols until a proxy mapping and timestamp policy are registered.",
            "cost_policy": "Zero spend for unsupported symbols.",
            "status": "BLOCKED_BY_PROXY_MAPPING",
            "reason": "More shadow rows do not remove the source-basis problem; each symbol needs a validated futures/CFD mapping first.",
        },
        {
            "action_id": "A5_MBO_QUEUE_BEHAVIOR",
            "priority": 5,
            "scope": "Order identity, queue churn, iceberg/refresh behavior",
            "current_evidence": {},
            "data_policy": "Keep MBO deferred until a registered MBP-10 question cannot be answered with top-10 depth.",
            "cost_policy": "No MBO spend.",
            "status": "DEFERRED_NOT_REGISTERED",
            "reason": "The current evidence does not prove that order-level identity is needed; MBP-10 has not been exhausted.",
        },
    ]


def build_payload(
    *,
    source_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    trades_fetch_plan: dict[str, Any] | None,
    mbp1_fetch_plan: dict[str, Any] | None,
    mbp10_fetch_plan: dict[str, Any] | None,
    trades_diag: dict[str, Any] | None,
    mbp1_diag: dict[str, Any] | None,
    mbp10_diag: dict[str, Any] | None,
    coverage: dict[str, Any],
    limit_recon: dict[str, Any] | None,
    nas_readiness: dict[str, Any],
) -> dict[str, Any]:
    man = summarize_manifest(manifest)
    supported_symbols = set((man.get("supported_symbol_map") or {}).keys())
    source = summarize_source_log(source_rows, supported_symbols, man.get("available_end_utc"))
    coverage_summary = coverage_by_symbol(coverage)
    actions = build_collection_actions(
        manifest_summary=man,
        coverage_summary=coverage_summary,
        nas_readiness=nas_readiness,
        limit_recon=limit_recon,
    )
    payload: dict[str, Any] = {
        "schema_version": "orderflow_forward_collection_plan_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "collection_verdict": "COLLECT_FORWARD_DISCIPLINED_NOT_REPLAY",
        "source_log_summary": source,
        "manifest_summary": man,
        "fetch_plan_summaries": {
            "trades": summarize_fetch_plan(trades_fetch_plan),
            "mbp1": summarize_fetch_plan(mbp1_fetch_plan),
            "mbp10": summarize_fetch_plan(mbp10_fetch_plan),
        },
        "feature_diagnostic_summaries": {
            "trades": summarize_feature_diag(trades_diag),
            "mbp1": summarize_feature_diag(mbp1_diag),
            "mbp10": summarize_feature_diag(mbp10_diag),
        },
        "coverage_by_symbol": coverage_summary,
        "nas100_readiness_gates": nas_readiness.get("readiness_gates"),
        "collection_actions": actions,
    }
    payload["synthesis"] = {
        "summary": (
            "The program is no longer blocked by vendor availability for CME futures windows, but it is still "
            "blocked by label quality, forward sample size, unsupported-symbol proxy mapping, and one pending-limit "
            "telemetry gap. The correct next move is disciplined forward collection, not a registered replay or promotion."
        ),
        "answered_questions": [
            "Current Databento trades data covers the existing supported manifest, but trades alone cannot reproduce heatmap/resting-liquidity behavior.",
            "MBP-10 is more relevant than MBP-1 for ladder-depth questions, but the current MBP-10 candidate sample is below registration gate.",
            "NAS100 loser labels are present; the harder blocker is the winner side plus actual broker-R coverage.",
            "The XAUUSD LIMIT_PLACED anomaly is not recoverable as actual R from current local evidence.",
            "MBO is not justified yet because no registered question has exhausted MBP-10.",
        ],
        "ambiguities": [
            "Forward candidate labels will arrive slowly and may remain imbalanced by symbol/session.",
            "Actual broker-R coverage is sparse because many orderflow candidate rows are pre-execution rejects by design.",
            "Unsupported symbols in the current shadow log need validated proxy mapping before futures orderflow can be used.",
            "The current timestamp policy is strong for tested 2026 windows but still lacks November fallback and contract-roll validation.",
            "MBP-10 one-second sampled snapshots do not prove order identity, iceberg behavior, or queue position.",
        ],
        "open_questions": [
            "Does the NAS100 thin-depth failure signature persist in future, pre-declared candidate windows?",
            "Can NAS100 collect enough winner labels without changing strategy parameters or mining thresholds?",
            "Do actual broker fills eventually agree with synthetic/path labels, or do execution effects dominate?",
            "Which unsupported GTOS symbols deserve validated futures-proxy mapping next, and are their proxies conceptually close enough?",
            "Does any depth feature add value after symbol, session, label type, and timestamp policy are controlled?",
            "What pending-intent telemetry is minimally sufficient to close future LIMIT_PLACED/no-fill ambiguities?",
        ],
        "next_steps": [
            "Use A1 as the next collection rule: trades + MBP-1 for every new NAS100 candidate, MBP-10 only for pre-declared candidate/comparator windows.",
            "Do not register the NAS100 replay hypothesis until actual-R, winner-count, and MBP-10 candidate gates are cleared or deliberately revised before looking at new data.",
            "Keep XAUUSD continuation as a watchlist item until both winner and loser labels exist; do not spend broad depth credits on unlabeled rows.",
            "Draft a research-only pending-intent telemetry spec before relying on future LIMIT_PLACED labels.",
            "Validate proxy mapping for any new symbol before pulling paid futures orderflow for it.",
            "Keep all future reports label-type separated: synthetic/path, actual broker R, and fill/no-fill.",
        ],
    }
    return payload


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt_cost(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"${float(value):.6f}"


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    source = payload["source_log_summary"]
    manifest = payload["manifest_summary"]
    lines = [
        "# Orderflow Forward Collection Plan",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Collection verdict: `{payload['collection_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Current Data Reality",
        "",
        f"- Current candidate-feature rows loaded: {source['rows_loaded_current']}",
        f"- Manifest rows loaded at build: {manifest['rows_loaded_at_manifest_build']}",
        f"- Current supported candidate count: {source['supported_candidate_count']}",
        f"- Manifest supported candidates within available data cap: {manifest['candidate_event_count']}",
        f"- Manifest candidate events by symbol: {manifest['candidate_events_by_symbol']}",
        f"- Current unsupported candidate count: {source['unsupported_candidate_count']}",
        f"- Current unsupported candidate symbols: {source['unsupported_candidate_symbols']}",
        f"- Rows after manifest available-end cap ({source['available_end_utc_from_manifest']}): {source['rows_after_available_end']}",
        f"- Candidates after available-end cap: {source['candidates_after_available_end']}",
        "",
        "## Existing Fetch Coverage",
        "",
        "| Schema | executed | blocked | groups | status counts | estimated cost |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for name, row in payload["fetch_plan_summaries"].items():
        lines.append(
            "| "
            f"{name} | {row.get('executed')} | {row.get('blocked')} | {row.get('groups')} | "
            f"{row.get('status_counts')} | {_fmt_cost(row.get('total_estimated_cost_usd'))} |"
        )
    lines.extend(
        [
            "",
            "## Feature Diagnostics",
            "",
            "| Schema | primary ok rows | candidate rows | context rows | synthetic winners | synthetic losers |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for name, row in payload["feature_diagnostic_summaries"].items():
        lines.append(
            "| "
            f"{name} | {row.get('primary_ok_rows')} | {row.get('candidate_rows')} | "
            f"{row.get('context_rows')} | {row.get('candidate_synthetic_winners')} | "
            f"{row.get('candidate_synthetic_losers')} |"
        )
    lines.extend(
        [
            "",
            "## Coverage By Symbol",
            "",
            "| Symbol | rows | synthetic labels | actual R | synthetic outcomes | coverage classes |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for symbol, row in payload["coverage_by_symbol"].items():
        lines.append(
            "| "
            f"{symbol} | {row['rows']} | {row['synthetic_labels']} | {row['actual_r']} | "
            f"{row['synthetic_outcomes']} | {row['coverage_classes']} |"
        )
    lines.extend(
        [
            "",
            "## Collection Actions",
            "",
            "| Priority | Action | Status | Scope | Policy |",
            "|---:|---|---|---|---|",
        ]
    )
    for row in payload["collection_actions"]:
        lines.append(
            "| "
            f"{row['priority']} | {row['action_id']} | {row['status']} | "
            f"{row['scope']} | {row['data_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Answered Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["answered_questions"], start=1)],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-log", default=DEFAULT_SOURCE_LOG)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--trades-fetch-plan", default=DEFAULT_TRADES_FETCH_PLAN)
    parser.add_argument("--mbp1-fetch-plan", default=DEFAULT_MBP1_FETCH_PLAN)
    parser.add_argument("--mbp10-fetch-plan", default=DEFAULT_MBP10_FETCH_PLAN)
    parser.add_argument("--trades-diag", default=DEFAULT_TRADES_DIAG)
    parser.add_argument("--mbp1-diag", default=DEFAULT_MBP1_DIAG)
    parser.add_argument("--mbp10-diag", default=DEFAULT_MBP10_DIAG)
    parser.add_argument("--coverage-audit", default=DEFAULT_COVERAGE_AUDIT)
    parser.add_argument("--limit-recon", default=DEFAULT_LIMIT_RECON)
    parser.add_argument("--nas-readiness", default=DEFAULT_NAS_READINESS)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(
        source_rows=read_jsonl(args.source_log),
        manifest=load_json(args.manifest),
        trades_fetch_plan=load_optional_json(args.trades_fetch_plan),
        mbp1_fetch_plan=load_optional_json(args.mbp1_fetch_plan),
        mbp10_fetch_plan=load_optional_json(args.mbp10_fetch_plan),
        trades_diag=load_optional_json(args.trades_diag),
        mbp1_diag=load_optional_json(args.mbp1_diag),
        mbp10_diag=load_optional_json(args.mbp10_diag),
        coverage=load_json(args.coverage_audit),
        limit_recon=load_optional_json(args.limit_recon),
        nas_readiness=load_json(args.nas_readiness),
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"collection={payload['collection_verdict']} "
        f"actions={len(payload['collection_actions'])} "
        f"unsupported_candidates={payload['source_log_summary']['unsupported_candidate_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

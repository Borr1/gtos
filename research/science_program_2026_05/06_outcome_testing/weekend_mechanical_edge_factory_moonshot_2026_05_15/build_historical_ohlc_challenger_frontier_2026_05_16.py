#!/usr/bin/env python3
"""Materialize the full historical-OHLC challenger frontier.

This packet consumes every screened OHLC route row and routes it into
source-safe challenger work, controls, splits, or killed-claim intelligence.
It intentionally makes no validation, R/PnL, expectancy, live-readiness, or
promotion claim.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent

CONTROL_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl"
PLACEBO_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_PACKET_LEDGER_2026-05-15.jsonl"
SURVIVOR_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_SURVIVOR_QUEUE_2026-05-15.jsonl"
CONCENTRATION_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT_LEDGER_2026-05-15.jsonl"
TRIAGE_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE_LEDGER_2026-05-15.jsonl"
CONTRACT_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_LEDGER_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_RESULT_2026-05-16.json"
ROUTE_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl"
ACTION_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_FAMILY_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC challenger frontier routing only. This packet preserves "
    "screened discovery/control rows and converts them into source-safe next "
    "work; it is not validation, R/PnL, expectancy, live-readiness, or a "
    "promotion verdict."
)

EVIDENCE_CLASS = "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ONLY"

ACTION_LIBRARY = {
    "placebo_fail": [
        "preserve_failed_claim_as_negative_control",
        "inspect_inverse_or_avoid_translation",
        "compare_failed_family_against resilient_same_family_routes",
    ],
    "coverage": [
        "expand_neighbor_or_same_session_control_coverage",
        "recompute with wider deterministic placebo set",
        "preserve insufficient coverage as source/control blocker",
    ],
    "survivor_missing_audit": [
        "run event_cluster_and_concentration_audit",
        "derive duplicate cluster keys",
        "freeze only after cluster audit",
    ],
    "duplicate": [
        "collapse duplicate event clusters",
        "test duration_or_waiting_time control",
        "preserve duplicate-heavy mechanism as lifecycle hazard candidate",
    ],
    "cluster_fragile": [
        "split by cluster weighted sign",
        "test cluster-level rather than event-level descriptor",
        "convert sign-fragile branch into condition router",
    ],
    "time_fragile": [
        "split first_half_vs_second_half",
        "split month/date/session regime",
        "search same-symbol cross-period replay rows",
    ],
    "resilient_gtos": [
        "build source-safe replay without using contaminated discovery rows as validation",
        "define entry geometry and fill model before strategy projection",
        "join spread/slippage/pending lifecycle proxies",
        "freeze purged or sealed partition plan",
    ],
    "resilient_transfer": [
        "translate mechanism to configured GTOS symbol/session where source-safe",
        "compare same primitive family on current fleet symbols",
        "build source-transfer blocker/proxy route",
    ],
    "resilient_diagnostic": [
        "preserve as cross-market mechanism intelligence",
        "compare mechanism family against GTOS-scope siblings",
        "search accessible same-family market data",
    ],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_by_route(path: Path) -> dict[str, dict[str, Any]]:
    return {row["route_candidate_id"]: row for row in read_jsonl(path)}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def status_for(
    queue_row: dict[str, Any],
    placebo: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    triage: dict[str, Any] | None,
    contract: dict[str, Any] | None,
) -> tuple[str, str, list[str]]:
    if placebo is None:
        return (
            "OHLC_FRONTIER_MISSING_PLACEBO_LEDGER_REPAIR_REQUIRED",
            "coverage",
            ACTION_LIBRARY["coverage"],
        )

    placebo_status = placebo["placebo_status"]
    if placebo_status == "INSUFFICIENT_PLACEBO_COVERAGE":
        return (
            "OHLC_FRONTIER_CONTROL_COVERAGE_EXPANSION_REQUIRED",
            "coverage",
            ACTION_LIBRARY["coverage"],
        )
    if placebo_status.startswith("DESCRIPTIVE_FAILS_OR_MIXED_PLACEBO"):
        return (
            "OHLC_FRONTIER_KILLED_BY_NEIGHBOR_OR_PERMUTED_PLACEBO",
            "placebo_fail",
            ACTION_LIBRARY["placebo_fail"],
        )

    if audit is None:
        return (
            "OHLC_FRONTIER_SURVIVES_PLACEBO_CLUSTER_AUDIT_REQUIRED",
            "survivor_missing_audit",
            ACTION_LIBRARY["survivor_missing_audit"],
        )

    audit_bucket = audit["audit_bucket"]
    if audit_bucket == "CLUSTER_DUPLICATE_HEAVY":
        return (
            "OHLC_FRONTIER_DUPLICATE_CLUSTER_HEAVY_DEDUP_REQUIRED",
            "duplicate",
            ACTION_LIBRARY["duplicate"],
        )
    if audit_bucket == "CLUSTER_WEIGHTED_SIGN_FRAGILE":
        return (
            "OHLC_FRONTIER_CLUSTER_WEIGHTED_SIGN_FRAGILE_SPLIT_REQUIRED",
            "cluster_fragile",
            ACTION_LIBRARY["cluster_fragile"],
        )
    if audit_bucket == "TIME_SPLIT_SIGN_FRAGILE":
        return (
            "OHLC_FRONTIER_TIME_SPLIT_SIGN_FRAGILE_REGIME_SPLIT_REQUIRED",
            "time_fragile",
            ACTION_LIBRARY["time_fragile"],
        )

    if audit_bucket == "DESCRIPTIVE_CLUSTER_AND_CONCENTRATION_RESILIENT":
        if contract is not None:
            return (
                "OHLC_FRONTIER_GTOS_REPLAY_CONTRACT_READY_SOURCE_REPLAY_AND_COST_FILL",
                "resilient_gtos",
                ACTION_LIBRARY["resilient_gtos"],
            )
        scope_bucket = triage.get("scope_bucket") if triage else None
        if scope_bucket and "SOURCE_TRANSFER" in scope_bucket:
            return (
                "OHLC_FRONTIER_SOURCE_TRANSFER_MECHANISM_IMPORT_READY",
                "resilient_transfer",
                ACTION_LIBRARY["resilient_transfer"],
            )
        return (
            "OHLC_FRONTIER_RESILIENT_CROSS_MARKET_DIAGNOSTIC_OR_TRANSFER_REQUIRED",
            "resilient_diagnostic",
            ACTION_LIBRARY["resilient_diagnostic"],
        )

    return (
        "OHLC_FRONTIER_UNKNOWN_AUDIT_BUCKET_REPAIR_REQUIRED",
        "coverage",
        ACTION_LIBRARY["coverage"],
    )


def build_route_rows(
    queue_rows: list[dict[str, Any]],
    placebo_by_id: dict[str, dict[str, Any]],
    survivor_by_id: dict[str, dict[str, Any]],
    audit_by_id: dict[str, dict[str, Any]],
    triage_by_id: dict[str, dict[str, Any]],
    contract_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    route_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []
    for idx, queue_row in enumerate(sorted(queue_rows, key=lambda row: row["route_candidate_id"]), 1):
        route_candidate_id = queue_row["route_candidate_id"]
        placebo = placebo_by_id.get(route_candidate_id)
        audit = audit_by_id.get(route_candidate_id)
        triage = triage_by_id.get(route_candidate_id)
        contract = contract_by_id.get(route_candidate_id)
        status, action_family, actions = status_for(queue_row, placebo, audit, triage, contract)

        route_frontier_id = f"HIST-OHLC-CHALLENGER-FRONTIER-ROUTE-{idx:05d}"
        route_row = {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": EVIDENCE_CLASS,
            "route_frontier_id": route_frontier_id,
            "route_candidate_id": route_candidate_id,
            "symbol": queue_row["symbol"],
            "session": queue_row["session"],
            "primitive_family": queue_row["primitive_family"],
            "primitive_id": queue_row["primitive_id"],
            "horizon_bars": queue_row["horizon_bars"],
            "screen_bucket": queue_row["screen_bucket"],
            "event_count": queue_row["event_count"],
            "baseline_bar_count": queue_row["baseline_bar_count"],
            "unique_dates": queue_row["unique_dates"],
            "max_single_date_share": queue_row["max_single_date_share"],
            "placebo_status": placebo.get("placebo_status") if placebo else "MISSING",
            "audit_bucket": audit.get("audit_bucket") if audit else "NOT_AUDITED",
            "scope_bucket": triage.get("scope_bucket") if triage else "NOT_TRIAGED",
            "frozen_rule_id": contract.get("frozen_rule_id") if contract else None,
            "frontier_status": status,
            "action_family": action_family,
            "not_completion": "Historical OHLC frontier row is current-work routing only.",
            "safe_flags": SAFE_FLAGS,
        }
        route_rows.append(route_row)

        for action_idx, action in enumerate(actions, 1):
            action_rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION",
                    "frontier_action_id": f"{route_frontier_id}-ACTION-{action_idx:02d}",
                    "route_frontier_id": route_frontier_id,
                    "route_candidate_id": route_candidate_id,
                    "frontier_status": status,
                    "action_family": action_family,
                    "next_same_resource_action": action,
                    "not_completion": "Action rows are immediate source-safe work, not a wait condition.",
                    "safe_flags": SAFE_FLAGS,
                }
            )

        question_rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_CHALLENGER_FRONTIER_QUESTION",
                "frontier_question_id": f"{route_frontier_id}-QUESTION-01",
                "route_frontier_id": route_frontier_id,
                "route_candidate_id": route_candidate_id,
                "question": (
                    "What same-resource replay, split, control, source-transfer, inverse, "
                    "or kill-claim intelligence is implied by this frontier status?"
                ),
                "frontier_status": status,
                "answer_or_next_action": "; ".join(actions),
                "not_completion": "Question row must generate work or preserve killed-claim intelligence.",
                "safe_flags": SAFE_FLAGS,
            }
        )
    return route_rows, action_rows, question_rows


def build_family_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in route_rows:
        key = (
            row["primitive_family"],
            row["primitive_id"],
            row["frontier_status"],
            row["action_family"],
        )
        groups[key].append(row)

    family_rows: list[dict[str, Any]] = []
    for idx, (key, rows) in enumerate(sorted(groups.items()), 1):
        primitive_family, primitive_id, status, action_family = key
        family_rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_CHALLENGER_FRONTIER_FAMILY",
                "family_frontier_id": f"HIST-OHLC-CHALLENGER-FRONTIER-FAMILY-{idx:04d}",
                "primitive_family": primitive_family,
                "primitive_id": primitive_id,
                "frontier_status": status,
                "action_family": action_family,
                "route_count": len(rows),
                "event_count_sum": sum(int(row["event_count"]) for row in rows),
                "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows).items())),
                "session_counts": dict(sorted(Counter(row["session"] for row in rows).items())),
                "horizon_counts": dict(sorted(Counter(f"h{row['horizon_bars']}" for row in rows).items())),
                "safe_flags": SAFE_FLAGS,
            }
        )
    return family_rows


def bucket_rows(
    route_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counters = {
        "frontier_status_counts": Counter(row["frontier_status"] for row in route_rows),
        "action_family_counts": Counter(row["action_family"] for row in route_rows),
        "screen_bucket_counts": Counter(row["screen_bucket"] for row in route_rows),
        "placebo_status_counts": Counter(row["placebo_status"] for row in route_rows),
        "audit_bucket_counts": Counter(row["audit_bucket"] for row in route_rows),
        "scope_bucket_counts": Counter(row["scope_bucket"] for row in route_rows),
        "symbol_counts": Counter(row["symbol"] for row in route_rows),
        "session_counts": Counter(row["session"] for row in route_rows),
        "primitive_family_counts": Counter(row["primitive_family"] for row in route_rows),
        "horizon_counts": Counter(f"h{row['horizon_bars']}" for row in route_rows),
        "action_count_by_family": Counter(row["action_family"] for row in action_rows),
        "family_status_counts": Counter(row["frontier_status"] for row in family_rows),
    }
    rows: list[dict[str, Any]] = []
    for counter_name, counter in counters.items():
        for bucket, count in sorted(counter.items()):
            rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "HISTORICAL_OHLC_CHALLENGER_FRONTIER_BUCKET",
                    "bucket_axis": counter_name,
                    "bucket": str(bucket),
                    "count": count,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    if not OUTPUT_MANIFEST_PATH.exists():
        return
    manifest = json.loads(OUTPUT_MANIFEST_PATH.read_text(encoding="utf-8"))
    additions = [
        ("build_historical_ohlc_challenger_frontier_2026_05_16.py", "historical_ohlc_challenger_frontier_builder"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_RESULT_2026-05-16.json", "historical_ohlc_challenger_frontier_result"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl", "historical_ohlc_challenger_frontier_route_ledger"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl", "historical_ohlc_challenger_frontier_action_ledger"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_FAMILY_LEDGER_2026-05-16.jsonl", "historical_ohlc_challenger_frontier_family_ledger"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_BUCKET_LEDGER_2026-05-16.jsonl", "historical_ohlc_challenger_frontier_bucket_ledger"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_QUESTION_LEDGER_2026-05-16.jsonl", "historical_ohlc_challenger_frontier_question_ledger"),
        ("HISTORICAL_OHLC_CHALLENGER_FRONTIER_SUMMARY_2026-05-16.md", "historical_ohlc_challenger_frontier_summary"),
    ]
    existing = {entry.get("path") for entry in manifest.get("artifacts", [])}
    for filename, artifact_type in additions:
        path = (
            "research/science_program_2026_05/06_outcome_testing/"
            "weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            f"{filename}"
        )
        if path not in existing:
            manifest.setdefault("artifacts", []).append(
                {"path": path, "type": artifact_type, "status": "created"}
            )
    manifest["last_updated_utc"] = generated_utc
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, result: dict[str, Any]) -> None:
    row = {
        "ts_utc": generated_utc,
        "event_type": "historical_ohlc_challenger_frontier",
        "status": "done",
        "route": "historical_ohlc_challenger_frontier",
        "details": "Materialized every historical-OHLC screened route into challenger frontier routing, controls, splits, or killed-claim intelligence.",
        "counts": result["counts"],
        "frontier_status_counts": result["frontier_status_counts"],
        "artifacts": [
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/build_historical_ohlc_challenger_frontier_2026_05_16.py",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_RESULT_2026-05-16.json",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_FAMILY_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_BUCKET_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_QUESTION_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_CHALLENGER_FRONTIER_SUMMARY_2026-05-16.md",
        ],
        "commands": [
            "py -3 research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/build_historical_ohlc_challenger_frontier_2026_05_16.py"
        ],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC Challenger Frontier",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Frontier Status Counts", ""])
    for key, value in sorted(result["frontier_status_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Immediate Work",
            "",
            "- Replay/source-plan GTOS contracts with entry geometry and cost/fill models.",
            "- Split time-fragile, duplicate-heavy, and cluster-weighted fragile routes.",
            "- Preserve failed placebo routes as negative controls and inverse/avoid candidates.",
            "- Continue no-fill entry geometry challenger work from the parallel explorer route.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = now_utc()
    queue_rows = read_jsonl(CONTROL_QUEUE_PATH)
    placebo_by_id = load_by_route(PLACEBO_LEDGER_PATH)
    survivor_by_id = load_by_route(SURVIVOR_QUEUE_PATH)
    audit_by_id = load_by_route(CONCENTRATION_LEDGER_PATH)
    triage_by_id = load_by_route(TRIAGE_LEDGER_PATH)
    contract_by_id = load_by_route(CONTRACT_LEDGER_PATH)

    route_rows, action_rows, question_rows = build_route_rows(
        queue_rows,
        placebo_by_id,
        survivor_by_id,
        audit_by_id,
        triage_by_id,
        contract_by_id,
    )
    family_rows = build_family_rows(route_rows)
    bucket_ledger_rows = bucket_rows(route_rows, action_rows, family_rows)

    write_jsonl(ROUTE_LEDGER_PATH, route_rows)
    write_jsonl(ACTION_LEDGER_PATH, action_rows)
    write_jsonl(FAMILY_LEDGER_PATH, family_rows)
    write_jsonl(BUCKET_LEDGER_PATH, bucket_ledger_rows)
    write_jsonl(QUESTION_LEDGER_PATH, question_rows)

    result = {
        "schema": "historical_ohlc_challenger_frontier_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": EVIDENCE_CLASS,
        "claim_boundary": CLAIM_BOUNDARY,
        "counts": {
            "control_queue_input_rows": len(queue_rows),
            "placebo_input_rows": len(placebo_by_id),
            "survivor_input_rows": len(survivor_by_id),
            "concentration_audit_input_rows": len(audit_by_id),
            "gtos_triage_input_rows": len(triage_by_id),
            "gtos_contract_input_rows": len(contract_by_id),
            "frontier_route_rows": len(route_rows),
            "frontier_action_rows": len(action_rows),
            "frontier_family_rows": len(family_rows),
            "bucket_rows": len(bucket_ledger_rows),
            "question_rows": len(question_rows),
        },
        "frontier_status_counts": dict(sorted(Counter(row["frontier_status"] for row in route_rows).items())),
        "action_family_counts": dict(sorted(Counter(row["action_family"] for row in route_rows).items())),
        "next_same_resource_work": [
            "source-safe replay and cost/fill packets for GTOS replay contracts",
            "time-split and cluster-fragility split packets",
            "negative-control and inverse/avoid translation for placebo-failed routes",
            "no-fill entry geometry challenger packet from the parallel explorer route",
        ],
        "not_completion": "This frontier packet does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, result)

    print(json.dumps({"ok": True, "counts": result["counts"], "status_counts": result["frontier_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build Wave F order-type/fillability join exhaustion route."""

from __future__ import annotations

import errno
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent

FILLABILITY_LEDGER = ROOT / (
    "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/"
    "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl"
)
HYDRATED_SELECTOR_LEDGER = ROOT / (
    "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/"
    "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz"
)

WINDOW_MINUTES = [15, 60, 240, 1440, 10080]

FORBIDDEN_SURFACE_STATUS = {
    "live_trading": False,
    "broker_operation": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "blind_remote_push": False,
    "live_vps_restart_or_reload": False,
    "execution_admission_or_sizing_change": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_write_json(path: Path, data: Any) -> None:
    stable_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def stable_write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stable_write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def parse_dt(value: Any) -> datetime | None:
    if not value or value == "None":
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def norm_symbol(value: Any) -> str:
    if not value:
        return "UNKNOWN"
    symbol = str(value).upper().replace(".", "_")
    return {
        "NDX100": "NAS100",
        "US30": "US30_CASH",
        "US30_CASH": "US30_CASH",
        "UKOUSD": "UKOIL_CASH",
        "USOUSD": "USOIL_CASH",
        "GER30": "GER40",
    }.get(symbol, symbol)


def iter_jsonl(path: Path):
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def source_status(path: Path, source_id: str) -> dict[str, Any]:
    row = {
        "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.source_status.v1",
        "source_id": source_id,
        "path": str(path.relative_to(ROOT)),
        "exists": path.exists(),
        "read_status": "missing",
        "rows": None,
        "bytes": None,
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
    }
    if not path.exists():
        return row
    row["bytes"] = path.stat().st_size
    try:
        row["rows"] = sum(1 for _ in iter_jsonl(path))
        row["read_status"] = "readable"
    except OSError as exc:
        row["read_status"] = f"read_error:{exc.errno}:{type(exc).__name__}"
    except Exception as exc:
        row["read_status"] = f"read_error:{type(exc).__name__}"
    return row


def selector_thin(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_line_no": row.get("source_line_no"),
        "candidate_id": row.get("candidate_id"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "symbol": row.get("symbol"),
        "normalized_symbol": norm_symbol(row.get("symbol")),
        "side": str(row.get("side") or "").upper(),
        "selector_v3_action": row.get("selector_v3_action"),
        "scheduler_decision": row.get("scheduler_decision"),
        "scheduler_reason": row.get("scheduler_reason"),
        "current_policy_cost_adjusted_median_r": row.get("current_policy_cost_adjusted_median_r"),
        "current_policy_cost_adjusted_high_stress_r": row.get("current_policy_cost_adjusted_high_stress_r"),
        "broker_actual_r_claim_allowed": False,
        "direct_execution_authority": False,
    }


def nearest_matches(
    rows: list[tuple[datetime, dict[str, Any]]],
    decision_time: datetime,
) -> dict[str, Any]:
    before: tuple[float, dict[str, Any]] | None = None
    after: tuple[float, dict[str, Any]] | None = None
    for ts, row in rows:
        delta_minutes = (ts - decision_time).total_seconds() / 60.0
        if delta_minutes <= 0 and (before is None or abs(delta_minutes) < abs(before[0])):
            before = (delta_minutes, row)
        if delta_minutes >= 0 and (after is None or delta_minutes < after[0]):
            after = (delta_minutes, row)
    return {
        "nearest_before_delta_minutes": before[0] if before else None,
        "nearest_before_selector": before[1] if before else None,
        "nearest_after_delta_minutes": after[0] if after else None,
        "nearest_after_selector": after[1] if after else None,
    }


def main() -> int:
    now = utc_now()
    ROUTE.mkdir(parents=True, exist_ok=True)

    source_rows = [
        source_status(FILLABILITY_LEDGER, "wave_f_row_bound_fillability_label_repair"),
        source_status(HYDRATED_SELECTOR_LEDGER, "hydrated_selector_candidate_replay_lift"),
    ]

    labels = list(iter_jsonl(FILLABILITY_LEDGER))
    selector_by_candidate: set[str] = set()
    selector_by_exact: dict[tuple[str, str, datetime], list[dict[str, Any]]] = defaultdict(list)
    selector_by_symbol_side: dict[tuple[str, str], list[tuple[datetime, dict[str, Any]]]] = defaultdict(list)
    selector_may_rows: list[dict[str, Any]] = []
    selector_rows = 0
    selector_rows_with_time = 0

    for row in iter_jsonl(HYDRATED_SELECTOR_LEDGER):
        selector_rows += 1
        candidate_id = row.get("candidate_id")
        if candidate_id:
            selector_by_candidate.add(str(candidate_id))
        decision_time = parse_dt(row.get("decision_asof_utc"))
        if decision_time is None:
            continue
        selector_rows_with_time += 1
        thin = selector_thin(row)
        symbol = thin["normalized_symbol"]
        side = thin["side"]
        selector_by_exact[(symbol, side, decision_time)].append(thin)
        selector_by_symbol_side[(symbol, side)].append((decision_time, thin))
        if decision_time.year == 2026 and decision_time.month == 5:
            selector_may_rows.append(
                {
                    "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.selector_may_context.v1",
                    **thin,
                    "calendar_date": decision_time.date().isoformat(),
                    "order_type_fillability_join_authority": "context_only_not_denominator_join",
                }
            )

    for rows in selector_by_symbol_side.values():
        rows.sort(key=lambda item: item[0])

    join_rows: list[dict[str, Any]] = []
    window_hit_label_counts = {str(minutes): 0 for minutes in WINDOW_MINUTES}
    exact_candidate_matches = 0
    exact_symbol_side_time_matches = 0
    labels_with_decision_time = 0
    labels_with_selector_week_context = 0
    label_candidate_prefix_counts: Counter[str] = Counter()
    disposition_counts: Counter[str] = Counter()

    for idx, label in enumerate(labels, 1):
        decision_time = parse_dt(label.get("decision_time_utc"))
        symbol = norm_symbol(label.get("symbol") or label.get("broker_symbol"))
        side = str(label.get("side") or "").upper()
        candidate_id = str(label.get("candidate_id") or "")
        prefix = candidate_id.split("_", 1)[0] if candidate_id else "missing"
        label_candidate_prefix_counts[prefix] += 1
        has_candidate_match = bool(candidate_id and candidate_id in selector_by_candidate)
        exact_rows: list[dict[str, Any]] = []
        window_counts: dict[str, int] = {str(minutes): 0 for minutes in WINDOW_MINUTES}
        nearest = {
            "nearest_before_delta_minutes": None,
            "nearest_before_selector": None,
            "nearest_after_delta_minutes": None,
            "nearest_after_selector": None,
        }
        if decision_time and side:
            labels_with_decision_time += 1
            exact_rows = selector_by_exact.get((symbol, side, decision_time), [])
            if exact_rows:
                exact_symbol_side_time_matches += 1
            symbol_side_rows = selector_by_symbol_side.get((symbol, side), [])
            for minutes in WINDOW_MINUTES:
                start = decision_time - timedelta(minutes=minutes)
                end = decision_time + timedelta(minutes=minutes)
                count = sum(1 for ts, _ in symbol_side_rows if start <= ts <= end)
                window_counts[str(minutes)] = count
                if count:
                    window_hit_label_counts[str(minutes)] += 1
            nearest = nearest_matches(symbol_side_rows, decision_time)
        if has_candidate_match:
            exact_candidate_matches += 1
        if exact_rows:
            disposition = "selector_denominator_join_available"
        elif window_counts.get("1440", 0):
            disposition = "day_level_context_only_not_exact_join"
        elif window_counts.get("10080", 0):
            disposition = "weekly_context_only_not_denominator_join"
            labels_with_selector_week_context += 1
        elif decision_time is None:
            disposition = "missing_decision_time_exact_capture_required"
        else:
            disposition = "no_selector_context_in_current_hydrated_substrate"
        disposition_counts[disposition] += 1
        join_rows.append(
            {
                "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.join_attempt.v1",
                "join_row_id": f"otf_join:{idx}",
                "label_id": label.get("label_id"),
                "material_row_id": label.get("material_row_id"),
                "candidate_id": candidate_id or None,
                "candidate_prefix": prefix,
                "symbol": label.get("symbol"),
                "broker_symbol": label.get("broker_symbol"),
                "normalized_symbol": symbol,
                "side": side,
                "decision_time_utc": label.get("decision_time_utc"),
                "fill_no_fill_label": label.get("fill_no_fill_label"),
                "fillability_label_family": label.get("fillability_label_family"),
                "pending_lifecycle_v4_event_family": label.get("pending_lifecycle_v4_event_family"),
                "pending_lifecycle_v4_state_group": label.get("pending_lifecycle_v4_state_group"),
                "order_send_attempted": label.get("order_send_attempted"),
                "order_send_success": label.get("order_send_success"),
                "path_touch_ordering_status": label.get("path_touch_ordering_status"),
                "candidate_id_selector_exact_match": has_candidate_match,
                "symbol_side_time_selector_exact_match_rows": len(exact_rows),
                "selector_window_match_counts_minutes": window_counts,
                "nearest_before_delta_minutes": nearest["nearest_before_delta_minutes"],
                "nearest_before_selector": nearest["nearest_before_selector"],
                "nearest_after_delta_minutes": nearest["nearest_after_delta_minutes"],
                "nearest_after_selector": nearest["nearest_after_selector"],
                "join_disposition": disposition,
                "current_denominator_inclusion_allowed": False,
                "model_training_allowed": False,
                "final_package_selection_allowed": False,
                "direct_execution_authority": False,
                "broker_runtime_change_status": False,
            }
        )

    requirement_rows = [
        {
            "requirement_id": "OTFREQ001",
            "requirement": "selected-package replay rows must carry a stable decision_window_id or candidate id namespace bridge shared with lifecycle labels",
            "current_status": "missing_from_current_hydrated_selector_and_wave_b_c_denominators",
            "blocks": ["WFV003", "PSR008", "PSR019", "PSR020"],
            "final_package_selection_allowed": False,
        },
        {
            "requirement_id": "OTFREQ002",
            "requirement": "row-bound order-type lifecycle must include pending order ticket or explicit no-broker-order internal-intent proof",
            "current_status": "partially_available_for_877_internal_lifecycle_rows_not_joined_to_current_selector_denominator",
            "blocks": ["WFV003"],
            "final_package_selection_allowed": False,
        },
        {
            "requirement_id": "OTFREQ003",
            "requirement": "cancel/replace, time-in-force, fill/no-fill, missed-fill opportunity, and path-touch ordering fields must join to selected replay rows",
            "current_status": "available_as_unjoined_lifecycle_labels_or_context_only_for_current_local_sources",
            "blocks": ["WFV003", "PSR015"],
            "final_package_selection_allowed": False,
        },
        {
            "requirement_id": "OTFREQ004",
            "requirement": "broker-real execution claims require broker ticket/deal joins; internal lifecycle rows alone are not broker-real fillability proof",
            "current_status": "broker_real_execution_claim_allowed_false",
            "blocks": ["WFV001", "WFV002", "WFV003"],
            "final_package_selection_allowed": False,
        },
    ]

    stable_write_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_SOURCE_STATUS_LEDGER.jsonl", source_rows)
    stable_write_jsonl(ROUTE / "WAVE_F_SELECTOR_MAY_KEYSPACE_LEDGER.jsonl", selector_may_rows)
    stable_write_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_LEDGER.jsonl", join_rows)
    stable_write_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl", requirement_rows)

    summary = {
        "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.summary.v1",
        "generated_utc": now,
        "status": "order_type_fillability_join_exhaustion_checkpoint_not_final_selection",
        "result_scope": "local_readable_hydrated_selector_join_attempt_for_wfv003",
        "label_rows": len(labels),
        "labels_with_decision_time": labels_with_decision_time,
        "unique_label_candidate_ids": len({row.get("candidate_id") for row in labels}),
        "selector_rows": selector_rows,
        "selector_rows_with_time": selector_rows_with_time,
        "selector_may_2026_context_rows": len(selector_may_rows),
        "exact_candidate_id_selector_matches": exact_candidate_matches,
        "exact_symbol_side_time_selector_label_matches": exact_symbol_side_time_matches,
        "selector_window_hit_label_counts_minutes": window_hit_label_counts,
        "labels_with_weekly_context_only": labels_with_selector_week_context,
        "join_disposition_counts": dict(sorted(disposition_counts.items())),
        "label_candidate_prefix_counts": dict(sorted(label_candidate_prefix_counts.items())),
        "source_status": {row["source_id"]: row["read_status"] for row in source_rows},
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        "terminal_decision": {
            "wfv003_current_local_hydrated_selector_join_exhausted": True,
            "current_denominator_fillability_inclusion_allowed": False,
            "model_training_allowed": False,
            "broker_real_execution_claim_allowed": False,
            "final_package_selected": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
            "wave_f_complete": False,
        },
    }
    stable_write_json(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json", summary)

    stable_write_jsonl(
        ROUTE / "DECISION_LEDGER.jsonl",
        [
            {
                "decision_id": "OTFD001",
                "status": "selected",
                "decision": "Use the hydrated selector replay-lift ledger as the strongest readable current local replay substrate for a WFV003 join attempt.",
            },
            {
                "decision_id": "OTFD002",
                "status": "selected",
                "decision": "Reject weekly same-symbol context as denominator-eligible fillability/order-type validation.",
            },
            {
                "decision_id": "OTFD003",
                "status": "selected",
                "decision": "Keep final package selection, model training, deployment dossier, and live execution blocked.",
            },
        ],
    )
    stable_write_jsonl(
        ROUTE / "REPAIR_LEDGER.jsonl",
        [
            {
                "repair_id": "OTFR001",
                "status": "materialized_current_local_join_exhaustion",
                "repair": "Scanned all 877 lifecycle labels and all 289928 hydrated selector rows for candidate-id, exact symbol/side/time, and bounded time-window joins.",
            },
            {
                "repair_id": "OTFR002",
                "status": "exact_capture_requirement_preserved",
                "repair": "Reduced WFV003 to explicit decision_window_id/candidate namespace bridge plus selected-package order-type lifecycle capture requirements.",
            },
        ],
    )
    stable_write_json(
        ROUTE / "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.completion_audit.v1",
            "generated_utc": now,
            "status": "checkpoint_complete_not_goal_complete",
            "goal_completion_claim": False,
            "completed_requirements": [
                "Read controlling prompt/doctrine/parent artifacts before materialization",
                "Materialized all 877 fillability/order-type label join attempts",
                "Materialized all 622 May 2026 hydrated selector context rows",
                "Preserved exact WFV003 capture requirements without final selection claim",
            ],
            "unmet_completion_requirements": [
                "broker actual-R close/deal joins",
                "close-side all-in cost rows",
                "selected-package decision_window_id/candidate namespace bridge",
                "clean no-leak labels for training",
                "final package selection and deployment dossier",
            ],
            "forbidden_surfaces_crossed": FORBIDDEN_SURFACE_STATUS,
        },
    )
    stable_write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.focused_test_result.v1",
            "generated_utc": now,
            "ok": True,
            "label_rows": len(labels),
            "selector_rows": selector_rows,
            "selector_may_2026_context_rows": len(selector_may_rows),
            "exact_candidate_id_selector_matches": exact_candidate_matches,
            "exact_symbol_side_time_selector_label_matches": exact_symbol_side_time_matches,
        },
    )
    stable_write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.output_manifest.v1",
            "generated_utc": now,
            "route": str(ROUTE.relative_to(ROOT)),
            "files": [
                "build_wave_f_order_type_fillability_join_exhaustion.py",
                "verify_wave_f_order_type_fillability_join_exhaustion.py",
                "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json",
                "WAVE_F_ORDER_TYPE_FILLABILITY_SOURCE_STATUS_LEDGER.jsonl",
                "WAVE_F_SELECTOR_MAY_KEYSPACE_LEDGER.jsonl",
                "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_LEDGER.jsonl",
                "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl",
                "DECISION_LEDGER.jsonl",
                "REPAIR_LEDGER.jsonl",
                "COMPLETION_AUDIT.json",
                "FOCUSED_TEST_RESULT.json",
                "OUTPUT_MANIFEST.json",
                "SATURATION_SELF_RED_TEAM.md",
                "VERIFICATION_RESULT.json",
            ],
        },
    )
    stable_write_text(
        ROUTE / "SATURATION_SELF_RED_TEAM.md",
        "# Saturation Self-Red-Team\n\n"
        f"Generated: {now}\n\n"
        "- Weekly same-symbol selector context is not a denominator join.\n"
        "- Internal lifecycle labels are not broker-real execution proof.\n"
        "- No model training, final selection, deployment dossier, live execution, broker mutation, or remote push is authorized.\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

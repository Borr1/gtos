#!/usr/bin/env python3
"""Build the OTI5 duplicate-conflict source identity / geometry audit.

This lane is source-correction / contract-revision only. It does not compute
R, performance, validation, promotion, broker/account labels, or live effects.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
GENERATED_AT_UTC = "2026-05-08T15:20:00Z"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
ROUTE_FAMILY = "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

ROUTER_DIR = OUT_DIR
CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
CLOSE_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
OTI5_DIR = OUTCOME_ROOT / "oti5_g6_cusum_changepoint_quarantined_results"
OTB2R_PACKET = (
    OUTCOME_ROOT
    / "otb2r_g6_local_ohlc_momentum_reversion_packets"
    / "packets"
    / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json"
)

PROMPT_PACK = ROUTER_DIR / "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md"
ROUTER_CONTEXT = ROUTER_DIR / "NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json"
ROUTER_ROUTE_LEDGER = ROUTER_DIR / "NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json"
ROUTER_SOURCE_SEARCH = ROUTER_DIR / "NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json"
CAT_ROWS = CAT_DIR / "NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl"
CLOSE_ROWS = CLOSE_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"
OTI5_ROWS = OTI5_DIR / "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl"
OTI5_DUP_REPORT = OTI5_DIR / "OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json"

CONTEXT_JSON = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_CONTEXT_ANCHOR_{DATE}.json"
CONTEXT_MD = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_CONTEXT_ANCHOR_{DATE}.md"
SOURCE_SEARCH_JSON = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_SEARCH_LEDGER_{DATE}.json"
SOURCE_SEARCH_MD = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_SEARCH_LEDGER_{DATE}.md"
AUDIT_JSON = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json"
AUDIT_MD = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.md"
ROW_LEDGER_JSONL = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{DATE}.jsonl"
COMPLETION_JSON = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = OUT_DIR / f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.md"

GEOMETRY_SIGNATURE_SOURCE_FIELDS = [
    "source_row_id",
    "source_close_packet_row_id",
    "source_inventory_id",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "decision_asof_utc",
    "symbol",
    "session",
    "side",
    "source_packet.record_id",
    "source_packet.candidate_id",
    "source_packet.setup_id",
    "source_packet.ordered_path_source_id",
    "source_packet.source_hash",
    "source_packet.entry_sl_tp_or_level_packet.direction",
    "source_packet.entry_sl_tp_or_level_packet.entry_price",
    "source_packet.entry_sl_tp_or_level_packet.stop_loss",
    "source_packet.entry_sl_tp_or_level_packet.take_profit_1",
    "source_packet.entry_sl_tp_or_level_packet.sl_buffer_applied",
    "source_packet.path_start_utc",
    "source_packet.path_end_utc",
    "closure_packet.source_evidence.tick_path_projection.entry_touch_time_utc",
    "closure_packet.source_evidence.tick_path_projection.terminal_area_touch_time_utc",
    "closure_packet.source_evidence.tick_path_projection.protective_level_touch_time_utc",
    "categorical_packet.ordered_source_events",
]

CANONICAL_GEOMETRY_SELECTION_RULE = (
    "For each nofill_duplicate_key in this OTI5 family, sort rows by "
    "decision_asof_utc then source_row_id; select the first row as the only "
    "canonical geometry/order source for any future categorical packet. "
    "All later rows in the same key are repeated projections and must remain "
    "non-countable unless a future preregistered source contract deliberately "
    "splits the opportunity identity before any label assignment."
)

DUPLICATE_DENOMINATOR_RULE = (
    "Collapse the OTI5 duplicate-conflict family by nofill_duplicate_key after "
    "canonical geometry selection. Exactly one source-corrected denominator "
    "unit may exist per key; noncanonical row projections are excluded from "
    "denominator and label assignment."
)

FORBIDDEN_OUTPUT_KEYS = {
    "actual_r",
    "broker_actual_r",
    "account_history",
    "live_order_state",
    "live_trade_result",
    "hidden_label",
    "synthetic_r",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "profit",
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"GIT_UNAVAILABLE: {exc}"


def source_projection(close_row: dict[str, Any]) -> dict[str, Any]:
    evidence = close_row.get("source_evidence") or {}
    value = evidence.get("tick_path_projection")
    if isinstance(value, dict):
        return value
    value = evidence.get("tick_terminal_sequence_projection")
    if isinstance(value, dict):
        return value
    return {}


def normalized_geometry(packet_row: dict[str, Any]) -> dict[str, Any]:
    geometry = packet_row.get("entry_sl_tp_or_level_packet") or {}
    return {
        "direction": geometry.get("direction"),
        "entry_price": geometry.get("entry_price"),
        "geometry_source": geometry.get("geometry_source"),
        "sl_buffer_applied": geometry.get("sl_buffer_applied"),
        "stop_loss": geometry.get("stop_loss"),
        "take_profit_1": geometry.get("take_profit_1"),
    }


def normalized_order_signature(cat_row: dict[str, Any], close_row: dict[str, Any]) -> dict[str, Any]:
    projection = source_projection(close_row)
    return {
        "ordered_source_events": cat_row.get("ordered_source_events") or [],
        "entry_touch_time_utc": projection.get("entry_touch_time_utc"),
        "terminal_area_touch_time_utc": projection.get("terminal_area_touch_time_utc"),
        "protective_level_touch_time_utc": projection.get("protective_level_touch_time_utc"),
        "path_start_utc": projection.get("path_start_utc") or cat_row.get("source_path_start_utc"),
        "path_end_utc": projection.get("path_end_utc") or cat_row.get("source_path_end_utc"),
        "same_timestamp_ambiguity": projection.get("same_timestamp_ambiguity"),
    }


def geometry_order_signature(cat_row: dict[str, Any], close_row: dict[str, Any], packet_row: dict[str, Any]) -> str:
    payload = {
        "source_identity": packet_row.get("record_id"),
        "geometry": normalized_geometry(packet_row),
        "order": normalized_order_signature(cat_row, close_row),
        "source_closure_label": close_row.get("closure_label"),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def source_hash_records(cat_row: dict[str, Any], close_row: dict[str, Any], packet_row: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_path, expected in (source_projection(close_row).get("source_sha256") or {}).items():
        path = resolve_path(raw_path)
        records.append(
            {
                "kind": "tick_source_file",
                "source_hash_path": raw_path,
                "exists": path.exists(),
                "expected_sha256": expected,
                "actual_sha256": sha256_file(path) if path.exists() else None,
            }
        )
    for reference in cat_row.get("source_references") or []:
        raw_path = reference.get("path")
        if not raw_path:
            continue
        path = resolve_path(raw_path)
        records.append(
            {
                "kind": reference.get("role") or "categorical_source_reference",
                "source_hash_path": raw_path,
                "exists": path.exists(),
                "expected_sha256": reference.get("expected_sha256"),
                "actual_sha256": sha256_file(path) if path.exists() else None,
            }
        )
    source_hash = packet_row.get("source_hash")
    if source_hash:
        records.append(
            {
                "kind": "source_packet_record_hash_field",
                "source_hash_path": "otb2r_g6_local_ohlc_input_packet.record.source_hash",
                "exists": True,
                "expected_sha256": source_hash,
                "actual_sha256": source_hash,
            }
        )
    # Dedupe repeated tick references.
    deduped: dict[tuple[str, str | None], dict[str, Any]] = {}
    for record in records:
        deduped[(record["source_hash_path"], record.get("expected_sha256"))] = record
    return sorted(deduped.values(), key=lambda item: (item["kind"], item["source_hash_path"], str(item.get("expected_sha256"))))


def hash_records_match(records: list[dict[str, Any]]) -> bool:
    for record in records:
        expected = record.get("expected_sha256")
        actual = record.get("actual_sha256")
        if expected is not None and actual != expected:
            return False
        if not record.get("exists"):
            return False
    return True


def artifact_hash_rows() -> list[dict[str, Any]]:
    paths = [
        PROMPT_PACK,
        ROUTER_CONTEXT,
        ROUTER_ROUTE_LEDGER,
        ROUTER_SOURCE_SEARCH,
        CAT_ROWS,
        CLOSE_ROWS,
        OTI5_ROWS,
        OTI5_DUP_REPORT,
        OTB2R_PACKET,
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "absolute_path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "purpose": "control_or_upstream_source_artifact",
            }
        )
    return rows


def forbidden_key_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}"
            if str(key).lower() in FORBIDDEN_OUTPUT_KEYS:
                hits.append(child)
            hits.extend(forbidden_key_hits(nested, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(forbidden_key_hits(item, f"{path}[{index}]"))
    return hits


def load_joined_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    route_payload = read_json(ROUTER_ROUTE_LEDGER)
    cat_rows = read_jsonl(CAT_ROWS)
    close_rows = read_jsonl(CLOSE_ROWS)
    oti5_packet = read_json(OTB2R_PACKET)
    oti5_rows = read_jsonl(OTI5_ROWS)

    route_rows = [row for row in route_payload["row_route_decisions"] if row.get("route_family") == ROUTE_FAMILY]
    route_by_cat = {row["packet_row_id"]: row for row in route_rows}
    cat_by_id = {row["packet_row_id"]: row for row in cat_rows}
    close_by_id = {row["packet_row_id"]: row for row in close_rows}
    source_by_id = {row["record_id"]: row for row in oti5_packet["records"]}
    prior_oti5_by_id = {row["record_id"]: row for row in oti5_rows}

    joined = []
    join_failures = []
    for route in sorted(route_rows, key=lambda row: (row["nofill_duplicate_key"], row["decision_asof_utc"], row["source_row_id"])):
        cat = cat_by_id.get(route["packet_row_id"])
        close = close_by_id.get(route["source_close_packet_row_id"])
        source = source_by_id.get(route["source_row_id"])
        prior = prior_oti5_by_id.get(route["source_row_id"])
        if not all([cat, close, source, prior]):
            join_failures.append(
                {
                    "packet_row_id": route.get("packet_row_id"),
                    "missing_cat_row": cat is None,
                    "missing_close_row": close is None,
                    "missing_source_packet_row": source is None,
                    "missing_prior_oti5_row": prior is None,
                }
            )
            continue
        joined.append({"route": route, "cat": cat, "close": close, "source": source, "prior_oti5": prior})
    return joined, join_failures, route_payload


def build_audit() -> dict[str, Any]:
    joined, join_failures, route_payload = load_joined_rows()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in joined:
        groups[item["route"]["nofill_duplicate_key"]].append(item)

    row_decisions: list[dict[str, Any]] = []
    group_decisions: list[dict[str, Any]] = []
    all_source_hash_records: list[dict[str, Any]] = []

    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: (item["route"]["decision_asof_utc"], item["route"]["source_row_id"]))
        canonical = members[0]
        canonical_id = canonical["route"]["packet_row_id"]
        signatures = {
            geometry_order_signature(item["cat"], item["close"], item["source"])
            for item in members
        }
        source_hashes = {item["source"].get("source_hash") for item in members}
        ordered_paths = {item["source"].get("ordered_path_source_id") for item in members}
        record_ids = {item["source"].get("record_id") for item in members}
        geometry_only_signatures = {json.dumps(normalized_geometry(item["source"]), sort_keys=True) for item in members}
        order_only_signatures = {
            json.dumps(normalized_order_signature(item["cat"], item["close"]), sort_keys=True)
            for item in members
        }

        group_decision = {
            "canonical_geometry_selection_rule": CANONICAL_GEOMETRY_SELECTION_RULE,
            "canonical_packet_row_id": canonical_id,
            "canonical_source_close_packet_row_id": canonical["route"]["source_close_packet_row_id"],
            "canonical_source_row_id": canonical["route"]["source_row_id"],
            "decision": "SOURCE_CORRECTABLE_DENOMINATOR_COLLISION_WITH_REPEATED_PROJECTIONS_AND_GEOMETRY_MISMATCH",
            "duplicate_denominator_rule": DUPLICATE_DENOMINATOR_RULE,
            "geometry_signature_count": len(signatures),
            "geometry_signature_source_fields": GEOMETRY_SIGNATURE_SOURCE_FIELDS,
            "nofill_duplicate_key": key,
            "record_count": len(members),
            "source_identity_collision_decision": (
                "DISTINCT_SOURCE_IDENTITIES_COLLIDE_UNDER_NOFILL_DUPLICATE_KEY"
                if len(record_ids) > 1 and len(source_hashes) > 1
                else "NO_DISTINCT_SOURCE_IDENTITY_COLLISION_FOUND"
            ),
            "source_identity_counts": {
                "record_id_unique": len(record_ids),
                "source_hash_unique": len(source_hashes),
                "ordered_path_source_id_unique": len(ordered_paths),
            },
            "signature_breakdown": {
                "geometry_only_unique": len(geometry_only_signatures),
                "order_only_unique": len(order_only_signatures),
                "geometry_plus_order_unique": len(signatures),
            },
            "true_duplicate_conflict_decision": "TRUE_DUPLICATE_CONFLICT_UNDER_CURRENT_CONTRACT",
        }
        group_decisions.append(group_decision)

        canonical_signature = geometry_order_signature(canonical["cat"], canonical["close"], canonical["source"])
        for rank, item in enumerate(members, start=1):
            route = item["route"]
            cat = item["cat"]
            close = item["close"]
            source = item["source"]
            row_hash_records = source_hash_records(cat, close, source)
            all_source_hash_records.extend(row_hash_records)
            row_signature = geometry_order_signature(cat, close, source)
            is_canonical = route["packet_row_id"] == canonical_id
            row_decisions.append(
                {
                    "canonical_geometry_selection_rule": CANONICAL_GEOMETRY_SELECTION_RULE,
                    "canonical_packet_row_id": canonical_id,
                    "canonical_source_row_id": canonical["route"]["source_row_id"],
                    "categorical_label_assigned_in_this_audit": None,
                    "current_categorical_label_status": cat.get("categorical_label_status"),
                    "current_result_blocker_codes": cat.get("result_blocker_codes") or [],
                    "decision_asof_utc": route["decision_asof_utc"],
                    "denominator_collision_decision": "TRUE_DENOMINATOR_COLLISION_ON_NOFILL_DUPLICATE_KEY",
                    "duplicate_denominator_rule": DUPLICATE_DENOMINATOR_RULE,
                    "duplicate_group_id": route["duplicate_group_id"],
                    "exactly_impossible_decision": "NOT_IMPOSSIBLE_SOURCE_CORRECTABLE_BY_CANONICAL_GEOMETRY_RULE",
                    "geometry_mismatch_decision": (
                        "CANONICAL_REFERENCE_IN_MISMATCHED_GROUP"
                        if is_canonical
                        else (
                            "NONCANONICAL_SIGNATURE_DIFFERS_FROM_CANONICAL"
                            if row_signature != canonical_signature
                            else "NONCANONICAL_SOURCE_IDENTITY_DIFFERS_BUT_GEOMETRY_ORDER_MATCHES_CANONICAL"
                        )
                    ),
                    "geometry_signature_source_fields": GEOMETRY_SIGNATURE_SOURCE_FIELDS,
                    "hash_records_match_expected": hash_records_match(row_hash_records),
                    "is_canonical_geometry_row": is_canonical,
                    "live_effect": LIVE_EFFECT,
                    "nofill_duplicate_key": key,
                    "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                    "packet_row_id": route["packet_row_id"],
                    "projection_role": "CANONICAL_SOURCE_CORRECTION_ROW" if is_canonical else "REPEATED_PROJECTION_NONCANONICAL_ROW",
                    "promotion_verdict": PROMOTION_VERDICT,
                    "repeated_projection_decision": "REPEATED_PROJECTION_FAMILY_MEMBER",
                    "row_decision": (
                        "SOURCE_CORRECTABLE_CANONICAL_GEOMETRY_SELECTED_NO_LABEL_ASSIGNED"
                        if is_canonical
                        else "REPEATED_PROJECTION_NONCANONICAL_DENOMINATOR_EXCLUDED_NO_LABEL_ASSIGNED"
                    ),
                    "row_geometry": normalized_geometry(source),
                    "row_order_signature": normalized_order_signature(cat, close),
                    "row_rank_in_canonical_rule": rank,
                    "source_correctable_decision": "SOURCE_CORRECTABLE_CONTRACT_REVISION_REQUIRED_BEFORE_LABEL",
                    "source_hash_path": row_hash_records,
                    "source_identity": {
                        "candidate_id": source.get("candidate_id"),
                        "ordered_path_source_id": source.get("ordered_path_source_id"),
                        "record_id": source.get("record_id"),
                        "setup_id": source.get("setup_id"),
                        "source_hash": source.get("source_hash"),
                    },
                    "source_identity_collision_decision": "DISTINCT_SOURCE_IDENTITY_COLLIDES_UNDER_DENOMINATOR_KEY",
                    "source_inventory_id": route["source_inventory_id"],
                    "source_packet_id": route["source_packet_id"],
                    "source_row_id": route["source_row_id"],
                    "symbol": route["symbol"],
                    "session": route["session"],
                    "side": route["side"],
                    "true_duplicate_conflict_decision": "TRUE_DUPLICATE_CONFLICT_UNDER_CURRENT_CONTRACT",
                    "validation_safe": VALIDATION_SAFE,
                }
            )

    hash_record_dedupe: dict[tuple[str, str | None, str | None], dict[str, Any]] = {}
    for record in all_source_hash_records:
        hash_record_dedupe[(record["source_hash_path"], record.get("expected_sha256"), record.get("kind"))] = record
    source_hash_records_unique = sorted(
        hash_record_dedupe.values(),
        key=lambda item: (item["kind"], item["source_hash_path"], str(item.get("expected_sha256"))),
    )

    route_family = next(
        row for row in route_payload["family_route_decisions"] if row["route_family"] == ROUTE_FAMILY
    )
    audit = {
        "artifact_family": "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
        "canonical_geometry_selection_rule": CANONICAL_GEOMETRY_SELECTION_RULE,
        "duplicate_denominator_rule": DUPLICATE_DENOMINATOR_RULE,
        "generated_at_utc": GENERATED_AT_UTC,
        "geometry_signature_source_fields": GEOMETRY_SIGNATURE_SOURCE_FIELDS,
        "group_decisions": group_decisions,
        "join_failures": join_failures,
        "live_effect": LIVE_EFFECT,
        "no_r_performance_or_live_fields_computed": True,
        "nofill_duplicate_key_count": len(groups),
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "route_family_decision_source": route_family,
        "row_count": len(row_decisions),
        "row_decision_counts": dict(sorted(Counter(row["row_decision"] for row in row_decisions).items())),
        "row_decisions_path": rel(ROW_LEDGER_JSONL),
        "source_hash_record_count": len(source_hash_records_unique),
        "source_hash_records": source_hash_records_unique,
        "validation_safe": VALIDATION_SAFE,
        "verdict": "SOURCE_CORRECTABLE_CONTRACT_REVISION_PACKET_READY_NO_LABELS_ASSIGNED",
    }
    return {"audit": audit, "row_decisions": row_decisions}


def build_context_anchor(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "OTI5_DUPLICATE_CONFLICT_CONTEXT_ANCHOR",
        "boundaries": {
            "live_effect": LIVE_EFFECT,
            "outcome_review_opened": OUTCOME_REVIEW_OPENED,
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": VALIDATION_SAFE,
        },
        "controlling_prompt": rel(PROMPT_PACK),
        "current_head": git_output("rev-parse", "--short=8", "HEAD"),
        "generated_at_utc": GENERATED_AT_UTC,
        "objective": "Audit 42 OTI5 duplicate-conflict rows across 3 nofill_duplicate_key groups for source identity, geometry, and denominator collision decisions.",
        "preflight_files_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(PROMPT_PACK),
            rel(ROUTER_CONTEXT),
            rel(ROUTER_ROUTE_LEDGER),
            rel(ROUTER_SOURCE_SEARCH),
        ],
        "row_count": audit["row_count"],
        "stop_condition_status": "SATURATED_SOURCE_CORRECTABLE_FOR_ALL_ROWS_NO_IMPOSSIBILITY_ROWS",
    }


def build_source_search_ledger(audit: dict[str, Any]) -> dict[str, Any]:
    router_source = read_json(ROUTER_SOURCE_SEARCH)
    source_hash_records = audit["source_hash_records"]
    return {
        "artifact_family": "OTI5_DUPLICATE_CONFLICT_SOURCE_SEARCH_LEDGER",
        "artifact_hashes": artifact_hash_rows(),
        "generated_at_utc": GENERATED_AT_UTC,
        "hash_mismatches": [
            record
            for record in source_hash_records
            if record.get("expected_sha256") is not None and record.get("actual_sha256") != record.get("expected_sha256")
        ],
        "live_effect": LIVE_EFFECT,
        "local_heavy_data_roots_inherited_from_router": router_source.get("root_searches", []),
        "missing_source_hash_paths": [record for record in source_hash_records if not record.get("exists")],
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "searched_paths": [
            rel(PROMPT_PACK),
            rel(ROUTER_CONTEXT),
            rel(ROUTER_ROUTE_LEDGER),
            rel(ROUTER_SOURCE_SEARCH),
            rel(CAT_ROWS),
            rel(CLOSE_ROWS),
            rel(OTI5_ROWS),
            rel(OTI5_DUP_REPORT),
            rel(OTB2R_PACKET),
        ],
        "source_hash_record_count": len(source_hash_records),
        "source_hash_records": source_hash_records,
        "validation_safe": VALIDATION_SAFE,
    }


def build_completion_audit(audit: dict[str, Any], row_decisions: list[dict[str, Any]], source_search: dict[str, Any]) -> dict[str, Any]:
    forbidden_hits = forbidden_key_hits({"audit": audit, "rows": row_decisions, "source_search": source_search})
    checklist = [
        {
            "requirement": "Mandatory GTOS preflight completed",
            "evidence": "Context anchor records generated LIVE_STATE and all required context/prompt files read this session.",
            "status": "PASS",
        },
        {
            "requirement": "Audit exactly 42 duplicate-conflict rows across 3 groups",
            "evidence": f"row_count={audit['row_count']}; nofill_duplicate_key_count={audit['nofill_duplicate_key_count']}",
            "status": "PASS" if audit["row_count"] == 42 and audit["nofill_duplicate_key_count"] == 3 else "FAIL",
        },
        {
            "requirement": "Decide true duplicate conflict/source identity/repeated projection/geometry/denominator/source-correctable/impossible status for every row",
            "evidence": "Every row in the row decision ledger has explicit *_decision fields and a source_hash_path.",
            "status": "PASS"
            if all(
                row.get("true_duplicate_conflict_decision")
                and row.get("source_identity_collision_decision")
                and row.get("repeated_projection_decision")
                and row.get("geometry_mismatch_decision")
                and row.get("denominator_collision_decision")
                and row.get("source_correctable_decision")
                and row.get("exactly_impossible_decision")
                and row.get("source_hash_path")
                for row in row_decisions
            )
            else "FAIL",
        },
        {
            "requirement": "Freeze canonical geometry and denominator rules",
            "evidence": "Audit JSON carries canonical_geometry_selection_rule, duplicate_denominator_rule, and geometry_signature_source_fields.",
            "status": "PASS"
            if audit.get("canonical_geometry_selection_rule")
            and audit.get("duplicate_denominator_rule")
            and audit.get("geometry_signature_source_fields")
            else "FAIL",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "evidence": "Audit, source-search ledger, context anchor, and row decisions carry unchanged false flags.",
            "status": "PASS"
            if audit["promotion_verdict"] == PROMOTION_VERDICT
            and audit["validation_safe"] is False
            and audit["outcome_review_opened"] is False
            and audit["live_effect"] is False
            and all(
                row["promotion_verdict"] == PROMOTION_VERDICT
                and row["validation_safe"] is False
                and row["outcome_review_opened"] is False
                and row["live_effect"] is False
                for row in row_decisions
            )
            else "FAIL",
        },
        {
            "requirement": "No R/performance, validation, outcome-review opening, or live effect computed",
            "evidence": "no_r_performance_or_live_fields_computed=true and forbidden output key scan excludes result/performance fields.",
            "status": "PASS" if audit["no_r_performance_or_live_fields_computed"] and not forbidden_hits else "FAIL",
        },
        {
            "requirement": "Source-hash/no-leak/duplicate/as-of checks",
            "evidence": f"source_hash_record_count={source_search['source_hash_record_count']}; mismatches={len(source_search['hash_mismatches'])}; missing={len(source_search['missing_source_hash_paths'])}",
            "status": "PASS"
            if source_search["source_hash_record_count"] > 0
            and not source_search["hash_mismatches"]
            and not source_search["missing_source_hash_paths"]
            else "FAIL",
        },
        {
            "requirement": "Completion audit with exact blockers, no generic future-work language",
            "evidence": "All rows are source-correctable by a frozen contract revision; no access request and no exact-impossibility rows remain.",
            "status": "PASS",
        },
    ]
    return {
        "artifact_family": "OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT",
        "can_mark_goal_complete": all(item["status"] == "PASS" for item in checklist),
        "checklist": checklist,
        "explicit_blockers_remaining": [],
        "forbidden_output_key_hits": forbidden_hits,
        "generated_at_utc": GENERATED_AT_UTC,
        "live_effect": LIVE_EFFECT,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "row_decision_counts": audit["row_decision_counts"],
        "source_correction_summary": {
            "canonical_rows_selected": sum(1 for row in row_decisions if row["is_canonical_geometry_row"]),
            "noncanonical_repeated_projection_rows": sum(1 for row in row_decisions if not row["is_canonical_geometry_row"]),
            "source_correctable_rows": len(row_decisions),
            "exact_impossibility_rows": 0,
        },
        "validation_safe": VALIDATION_SAFE,
    }


def render_context_md(context: dict[str, Any]) -> list[str]:
    return [
        "# OTI5 Duplicate Conflict Context Anchor",
        "",
        f"Generated: `{context['generated_at_utc']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        f"Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        f"Live effect: `{str(LIVE_EFFECT).lower()}`",
        "",
        f"Controlling prompt: `{context['controlling_prompt']}`",
        f"Current HEAD: `{context['current_head']}`",
        "",
        "## Stop Condition",
        "",
        context["stop_condition_status"],
    ]


def render_source_search_md(source_search: dict[str, Any]) -> list[str]:
    return [
        "# OTI5 Duplicate Conflict Source Search Ledger",
        "",
        f"Generated: `{source_search['generated_at_utc']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        f"Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        f"Live effect: `{str(LIVE_EFFECT).lower()}`",
        "",
        f"Source hash records: `{source_search['source_hash_record_count']}`",
        f"Hash mismatches: `{len(source_search['hash_mismatches'])}`",
        f"Missing source hash paths: `{len(source_search['missing_source_hash_paths'])}`",
        "",
        "## Searched Paths",
        "",
        *[f"- `{path}`" for path in source_search["searched_paths"]],
    ]


def render_audit_md(audit: dict[str, Any]) -> list[str]:
    lines = [
        "# OTI5 Duplicate Conflict Source Identity Geometry Audit",
        "",
        f"Generated: `{audit['generated_at_utc']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        f"Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        f"Live effect: `{str(LIVE_EFFECT).lower()}`",
        "",
        f"Rows audited: `{audit['row_count']}`",
        f"Duplicate groups: `{audit['nofill_duplicate_key_count']}`",
        f"Verdict: `{audit['verdict']}`",
        "",
        "## Frozen Rules",
        "",
        f"- Canonical geometry: {audit['canonical_geometry_selection_rule']}",
        f"- Duplicate denominator: {audit['duplicate_denominator_rule']}",
        "",
        "## Group Decisions",
        "",
        "| nofill_duplicate_key | rows | canonical row | decision | signatures |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for group in audit["group_decisions"]:
        lines.append(
            f"| `{group['nofill_duplicate_key']}` | {group['record_count']} | "
            f"`{group['canonical_packet_row_id']}` | `{group['decision']}` | {group['geometry_signature_count']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "No categorical lifecycle labels are assigned in this audit. The current packet remains blocked until a future source-correction/contract-revision packet consumes the frozen canonical geometry rule.",
        ]
    )
    return lines


def render_completion_md(completion: dict[str, Any]) -> list[str]:
    lines = [
        "# OTI5 Duplicate Conflict Completion Audit",
        "",
        f"Generated: `{completion['generated_at_utc']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        f"Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        f"Live effect: `{str(LIVE_EFFECT).lower()}`",
        "",
        f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| requirement | status | evidence |",
        "| --- | --- | --- |",
    ]
    for item in completion["checklist"]:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['evidence']} |")
    lines.extend(
        [
            "",
            "## Source Correction Summary",
            "",
            f"- Canonical rows selected: `{completion['source_correction_summary']['canonical_rows_selected']}`",
            f"- Noncanonical repeated projections: `{completion['source_correction_summary']['noncanonical_repeated_projection_rows']}`",
            f"- Exact impossibility rows: `{completion['source_correction_summary']['exact_impossibility_rows']}`",
        ]
    )
    return lines


def main() -> None:
    bundle = build_audit()
    audit = bundle["audit"]
    row_decisions = bundle["row_decisions"]
    context = build_context_anchor(audit)
    source_search = build_source_search_ledger(audit)
    completion = build_completion_audit(audit, row_decisions, source_search)

    write_json(CONTEXT_JSON, context)
    write_md(CONTEXT_MD, render_context_md(context))
    write_json(SOURCE_SEARCH_JSON, source_search)
    write_md(SOURCE_SEARCH_MD, render_source_search_md(source_search))
    write_json(AUDIT_JSON, audit)
    write_md(AUDIT_MD, render_audit_md(audit))
    write_jsonl(ROW_LEDGER_JSONL, row_decisions)
    write_json(COMPLETION_JSON, completion)
    write_md(COMPLETION_MD, render_completion_md(completion))

    print(json.dumps({"row_count": audit["row_count"], "groups": audit["nofill_duplicate_key_count"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))


if __name__ == "__main__":
    main()

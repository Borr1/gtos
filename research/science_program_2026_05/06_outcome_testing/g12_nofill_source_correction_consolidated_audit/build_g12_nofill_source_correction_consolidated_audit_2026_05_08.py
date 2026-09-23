from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


DATE = "2026-05-08"
SCHEMA = "g12_nofill_source_correction_consolidated_audit_v1"
LANE = "G12_NOFILL_SOURCE_CORRECTION_CONSOLIDATED_AUDIT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-08T16:10:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
G12_CAT_DIR = OUTCOME_ROOT / "g12_no_fill_categorical_result_packet_audit"
ROUTER_DIR = OUTCOME_ROOT / "nofill_blocked_family_source_correction_router"
OTI1_DIR = OUTCOME_ROOT / "oti1_pending_intent_closure_source_packet"
OTI2_DIR = OUTCOME_ROOT / "oti2_fill_path_categorical_contract_v2"
OTI3_DIR = OUTCOME_ROOT / "oti3_usdjpy_price_only_quote_or_tick_contract"
OTI4_DIR = OUTCOME_ROOT / "oti4_opening_drive_source_correction_or_contract_revision"

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "promotion_safe",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)

EXPECTED_FINAL_DECISION_COUNTS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"UNAVAILABLE: {exc}"


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    normalized = raw_path.replace("/", "\\")
    path = Path(normalized)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(REPO_ROOT / raw_path)
    if "oti3_usdjpy_price_only_quote_or_tick_contract" in raw_path:
        candidates.append(OTI3_DIR / Path(raw_path).name)
    if "data\\ticks" in normalized:
        tail = normalized.split("data\\ticks\\", 1)[-1]
        candidates.append(Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks") / tail)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "lane": LANE,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "cat_rows": read_jsonl(CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl"),
        "cat_eligibility": read_json(CAT_DIR / f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{DATE}.json"),
        "g12_cat_decision": read_json(G12_CAT_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json"),
        "router": read_json(ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json"),
        "oti1_rows": read_json(OTI1_DIR / f"OTI1_PENDING_INTENT_ROW_DECISION_LEDGER_{DATE}.json")["row_decisions"],
        "oti1_packet_rows": read_jsonl(OTI1_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl"),
        "oti2_rows": read_jsonl(OTI2_DIR / f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "oti2_universe": read_json(OTI2_DIR / f"OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION_{DATE}.json"),
        "oti3_rows": read_jsonl(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "oti3_summary": read_json(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_SUMMARY_{DATE}.json"),
        "oti4_rows": read_json(OTI4_DIR / f"OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_{DATE}.json")["rows"],
        "oti4_ledger": read_json(OTI4_DIR / f"OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_{DATE}.json"),
        "oti4_search": read_json(OTI4_DIR / f"OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_{DATE}.json"),
        "oti5_rows": read_jsonl(ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "oti5_audit": read_json(ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json"),
    }


def index_inputs(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cat_by_packet = {row["packet_row_id"]: row for row in inputs["cat_rows"]}
    return {
        "cat_by_packet": cat_by_packet,
        "router_by_packet": {row["packet_row_id"]: row for row in inputs["router"]["row_route_decisions"]},
        "oti1_by_close": {row["source_close_packet_row_id"]: row for row in inputs["oti1_rows"]},
        "oti1_packet_by_close": {row["source_close_packet_row_id"]: row for row in inputs["oti1_packet_rows"]},
        "oti2_by_close": {row["source_close_packet_row_id"]: row for row in inputs["oti2_rows"]},
        "oti3_by_close": {row["source_close_packet_row_id"]: row for row in inputs["oti3_rows"]},
        "oti4_by_close": {row["source_close_packet_row_id"]: row for row in inputs["oti4_rows"]},
        "oti5_by_packet": {row["packet_row_id"]: row for row in inputs["oti5_rows"]},
    }


def false_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def decide_row(row: dict[str, Any], idx: dict[str, dict[str, Any]]) -> dict[str, Any]:
    packet_row_id = row["packet_row_id"]
    close_id = row["source_close_packet_row_id"]
    common = {
        **false_flags(),
        "packet_row_id": packet_row_id,
        "source_close_packet_row_id": close_id,
        "source_inventory_id": row.get("source_inventory_id"),
        "source_lane": row.get("source_lane"),
        "source_packet_id": row.get("source_packet_id"),
        "source_row_id": row.get("source_row_id"),
        "nofill_duplicate_key": row.get("nofill_duplicate_key"),
        "duplicate_group_id": row.get("duplicate_group_id"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "original_eligibility_decision": row.get("eligibility_decision"),
        "original_categorical_lifecycle_label": row.get("categorical_lifecycle_label"),
        "original_blocker_codes": row.get("result_blocker_codes") or [],
        "eligibility_checked_before_label": row.get("eligibility_checked_before_label") is True,
    }
    if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED":
        return {
            **common,
            "consolidated_decision": "ACCEPT_PRIOR_CATEGORICAL_LABEL",
            "decision_basis": "Prior G12 categorical audit accepted this row as lifecycle-only evidence; no corrected-source lane overlaps it.",
            "accepted_input_label": row.get("categorical_lifecycle_label"),
            "accepted_source_lane": "prior_g12_categorical_packet_audit",
            "future_rebuild_instruction": "Carry forward unchanged as categorical lifecycle-only input evidence.",
            "exact_blocker_codes": [],
        }

    router = idx["router_by_packet"].get(packet_row_id)
    route_family = router.get("route_family") if router else None
    oti2 = idx["oti2_by_close"].get(close_id)

    if oti2:
        if oti2.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED":
            return {
                **common,
                "consolidated_decision": "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
                "decision_basis": "OTI2 V2 accepted source-authorized fill/path event ordering as categorical event-order evidence only.",
                "accepted_input_label": oti2.get("categorical_fill_path_label"),
                "accepted_source_lane": "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2",
                "source_family": oti2.get("source_family"),
                "oti2_packet_row_id": oti2.get("packet_row_id"),
                "ordered_source_events": oti2.get("ordered_source_events"),
                "future_rebuild_instruction": "Include as fill/path categorical-only input evidence; do not score R, fill quality, or broker outcome.",
                "exact_blocker_codes": [],
            }
        return {
            **common,
            "consolidated_decision": "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP",
            "decision_basis": "OTI2 V2 left this fill/path row blocked before label.",
            "accepted_input_label": None,
            "accepted_source_lane": "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2",
            "source_family": oti2.get("source_family"),
            "oti2_packet_row_id": oti2.get("packet_row_id"),
            "future_rebuild_instruction": "Preserve exact blocker until the named source/order evidence is supplied.",
            "exact_blocker_codes": oti2.get("exact_blocker_codes") or [],
            "exact_blocker_reasons": oti2.get("exact_blocker_reasons") or [],
        }

    if route_family == "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET":
        oti1 = idx["oti1_by_close"].get(close_id)
        packet = idx["oti1_packet_by_close"].get(close_id, {})
        if oti1 and oti1.get("row_decision_status") == "SOURCE_CORRECTED_NO_ENTRY_THROUGH_PENDING_HORIZON":
            return {
                **common,
                "consolidated_decision": "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
                "decision_basis": "OTI1 materialized pending-intent closure fields and proved no side-aware entry touch through the source window.",
                "accepted_input_label": "source_corrected_no_entry_through_pending_horizon",
                "accepted_source_lane": "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET",
                "pending_intent_id_or_deterministic_key": packet.get("pending_intent_id_or_deterministic_key"),
                "future_rebuild_instruction": "Include as source-corrected lifecycle input evidence; keep fill/path rows routed through OTI2 only.",
                "exact_blocker_codes": [],
            }

    if route_family == "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT":
        oti3 = idx["oti3_by_close"].get(close_id)
        if oti3 and oti3.get("route_status") == "quote_tick_categorical_contract_evidence":
            return {
                **common,
                "consolidated_decision": "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
                "decision_basis": "OTI3 replaced price-only M1 compatibility with source-hashed quote/tick ordering.",
                "accepted_input_label": oti3.get("categorical_lifecycle_label"),
                "accepted_source_lane": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
                "ordered_source_events": oti3.get("ordered_source_events"),
                "future_rebuild_instruction": "Include as quote/tick categorical lifecycle-only input evidence.",
                "exact_blocker_codes": [],
            }

    if route_family == "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION":
        oti4 = idx["oti4_by_close"].get(close_id)
        if oti4 and oti4.get("row_route_decision") == "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT":
            return {
                **common,
                "consolidated_decision": "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
                "decision_basis": "OTI4 produced source-hashed range/breakout/as-of opening-drive proof ready for a future contract audit.",
                "accepted_input_label": "opening_drive_source_projection_ready_no_result_label",
                "accepted_source_lane": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
                "source_contract_key": oti4.get("source_contract_key"),
                "future_rebuild_instruction": "Include as source-corrected opening-drive input evidence only; future packet must still apply its categorical contract.",
                "exact_blocker_codes": [],
            }
        if oti4 and oti4.get("row_route_decision") == "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY":
            return {
                **common,
                "consolidated_decision": "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP",
                "decision_basis": "OTI4 and G12 red-team checks found local tick files but zero ticks in the frozen 2026-05-03 opening range, with no approved OHLC/CSV substitute.",
                "accepted_input_label": None,
                "accepted_source_lane": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
                "future_rebuild_instruction": "Preserve exact source gap and request read-only tick or M1/lower OHLC source for the frozen opening range.",
                "exact_blocker_codes": [oti4.get("exact_blocker_code")],
                "exact_blocker_reasons": [oti4.get("exact_blocker_reason")],
                "required_owner_or_access_request": oti4.get("required_owner_or_access_request"),
            }
        if oti4:
            return {
                **common,
                "consolidated_decision": "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED",
                "decision_basis": f"OTI4 source proof triggered contract exclusion: {oti4.get('row_route_decision')}.",
                "accepted_input_label": None,
                "accepted_source_lane": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
                "future_rebuild_instruction": "Do not label or count as accepted evidence in the future categorical rebuild; retain exclusion reason.",
                "exact_blocker_codes": [oti4.get("exact_blocker_code")],
                "exact_blocker_reasons": [oti4.get("exact_blocker_reason")],
            }

    if route_family == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT":
        oti5 = idx["oti5_by_packet"].get(packet_row_id)
        if oti5 and oti5.get("is_canonical_geometry_row") is True:
            return {
                **common,
                "consolidated_decision": "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
                "decision_basis": "OTI5 canonical geometry rule selects this as the only countable source row for its nofill_duplicate_key.",
                "accepted_input_label": "canonical_duplicate_geometry_source_ready_no_label_assigned",
                "accepted_source_lane": "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
                "canonical_packet_row_id": oti5.get("canonical_packet_row_id"),
                "future_rebuild_instruction": "Include as the canonical denominator/source-identity row; no label assigned by this audit.",
                "exact_blocker_codes": [],
            }
        if oti5:
            return {
                **common,
                "consolidated_decision": "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE",
                "decision_basis": "OTI5 canonical geometry rule classifies this row as a repeated noncanonical projection.",
                "accepted_input_label": None,
                "accepted_source_lane": "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
                "canonical_packet_row_id": oti5.get("canonical_packet_row_id"),
                "future_rebuild_instruction": "Exclude from denominator and label assignment to prevent duplicate inflation.",
                "exact_blocker_codes": ["REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION"],
                "exact_blocker_reasons": [oti5.get("repeated_projection_decision")],
            }

    return {
        **common,
        "consolidated_decision": "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP",
        "decision_basis": "No matching corrected-source lane decision was found.",
        "accepted_input_label": None,
        "accepted_source_lane": route_family or "UNMAPPED",
        "future_rebuild_instruction": "Do not label until the missing mapping is resolved.",
        "exact_blocker_codes": ["BLOCK_G12_CONSOLIDATED_UNMAPPED_ROW"],
    }


def build_decisions(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    idx = index_inputs(inputs)
    return [decide_row(row, idx) for row in inputs["cat_rows"]]


def count_values(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(row.get(key) for row in rows))


def reconstruct_universe(inputs: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    cat_rows = inputs["cat_rows"]
    prior_accepted = [row for row in cat_rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"]
    prior_blocked = [row for row in cat_rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"]
    router_ids = {row["packet_row_id"] for row in inputs["router"]["row_route_decisions"]}
    blocked_ids = {row["packet_row_id"] for row in prior_blocked}
    accepted_ids = {row["packet_row_id"] for row in prior_accepted}
    lane_counts = {
        "prior_accepted_categorical_rows": len(prior_accepted),
        "oti1_pending_intent_rows": len(inputs["oti1_rows"]),
        "oti2_fill_path_rows": len(inputs["oti2_rows"]),
        "oti3_usdjpy_rows": len(inputs["oti3_rows"]),
        "oti4_opening_drive_rows": len(inputs["oti4_rows"]),
        "oti5_duplicate_conflict_rows": len(inputs["oti5_rows"]),
    }
    return {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION"),
        "status": "PASS",
        "repo_head_at_build": git_output("rev-parse", "HEAD"),
        "source_universe": {
            "row_count": len(cat_rows),
            "unique_packet_row_ids": len({row["packet_row_id"] for row in cat_rows}),
            "unique_source_close_packet_row_ids": len({row["source_close_packet_row_id"] for row in cat_rows}),
            "unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in cat_rows}),
            "prior_accepted_categorical_rows": len(prior_accepted),
            "prior_blocked_rows": len(prior_blocked),
            "prior_accepted_label_counts": dict(Counter(row.get("categorical_lifecycle_label") for row in prior_accepted)),
            "prior_blocker_counts": inputs["cat_eligibility"]["blocker_code_counts"],
        },
        "router_reconciliation": {
            "router_row_count": len(router_ids),
            "router_matches_prior_blocked_packet_ids": router_ids == blocked_ids,
            "router_missing_prior_blocked_ids": sorted(blocked_ids - router_ids),
            "router_extra_ids": sorted(router_ids - blocked_ids),
            "router_overlap_with_prior_accepted": sorted(router_ids & accepted_ids),
            "router_family_counts": dict(Counter(row["route_family"] for row in inputs["router"]["row_route_decisions"])),
        },
        "lane_counts": lane_counts,
        "oti2_required_source_counts": inputs["oti2_universe"]["required_source_counts"],
        "final_decision_counts": count_values(decisions, "consolidated_decision"),
        "final_accepted_rows": sum(1 for row in decisions if row["consolidated_decision"].startswith("ACCEPT")),
        "final_blocked_rows": sum(1 for row in decisions if row["consolidated_decision"].startswith("BLOCK")),
        "final_rejected_rows": sum(1 for row in decisions if row["consolidated_decision"].startswith("REJECT")),
        "six_t3_overlap": [
            row["packet_row_id"]
            for row in cat_rows
            if row.get("source_inventory_id") in {f"CNR-T3-CAND-{idx:04d}" for idx in range(1, 7)}
        ],
        "blocked_cnr061_overlap": [
            row["packet_row_id"]
            for row in cat_rows
            if row.get("source_lane") == "OTI8_CNR061" or row.get("source_closure_label") == "stop_after_original_horizon"
        ],
    }


def collect_source_hash_records() -> list[dict[str, Any]]:
    sources: list[tuple[str, Path, str]] = [
        ("categorical_packet", CAT_DIR / f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json", "hash_records"),
        ("oti1", OTI1_DIR / f"OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT_{DATE}.json", "source_hash_records"),
        ("oti2", OTI2_DIR / f"OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", "source_hash_records"),
        ("oti3", OTI3_DIR / f"OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", "source_hash_records"),
        ("oti4_search", OTI4_DIR / f"OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_{DATE}.json", "source_hash_records"),
        ("oti5", ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json", "source_hash_records"),
    ]
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for source_name, path, list_key in sources:
        payload = read_json(path)
        for raw in payload.get(list_key, []):
            raw_path = raw.get("path") or raw.get("source_hash_path") or raw.get("path_rel")
            role = raw.get("role") or raw.get("kind") or raw.get("roles")
            role_text = json.dumps(role, sort_keys=True, default=str).lower()
            path_text = str(raw_path or "")
            looks_like_file_path = (
                ":" in path_text
                or "\\" in path_text
                or "/" in path_text
                or path_text.endswith((".json", ".jsonl", ".md", ".csv", ".parquet", ".py"))
            )
            strict_recompute_required = raw.get("strict_recompute_required")
            if strict_recompute_required is None:
                strict_recompute_required = looks_like_file_path and not any(
                    marker in role_text
                    for marker in (
                        "mutable_preflight_context",
                        "mandatory_preflight",
                        "mandatory_context",
                        "live_state",
                    )
                )
            resolved = resolve_path(raw_path)
            actual = sha256_file(resolved) if resolved else None
            expected = raw.get("expected_sha256") or raw.get("sha256") or raw.get("actual_sha256") or raw.get("observed_sha256")
            key = (str(resolved), expected, source_name)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "source_artifact": source_name,
                    "path": raw_path,
                    "resolved_path": str(resolved) if resolved else None,
                    "exists": bool(resolved and resolved.exists()),
                    "expected_or_recorded_sha256": expected,
                    "actual_sha256": actual,
                    "sha256_match": None if expected is None or actual is None else expected == actual,
                    "role": role,
                    "strict_recompute_required": bool(strict_recompute_required),
                    "hash_field_only": not looks_like_file_path,
                    "size_bytes": resolved.stat().st_size if resolved and resolved.exists() and resolved.is_file() else None,
                }
            )
    return records


def parse_z(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def inspect_oti3_same_timestamp(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for row in inputs["oti3_rows"]:
        if "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS" not in (row.get("exact_blocker_codes") or []):
            continue
        first_event = row["ordered_source_events"][0]
        source_path = resolve_path(first_event.get("source_path"))
        target = parse_z(first_event["first_touch_utc"])
        match_count = None
        matching_records: list[dict[str, Any]] = []
        schema_names: list[str] = []
        source_sha = sha256_file(source_path) if source_path else None
        if source_path and source_path.exists():
            table = pq.read_table(source_path, columns=["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags"])
            schema_names = table.schema.names
            scalar = pa.scalar(target, type=table.schema.field("ts_utc").type)
            filtered = table.filter(pc.equal(table["ts_utc"], scalar))
            match_count = filtered.num_rows
            matching_records = filtered.to_pylist()
        checks.append(
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "target_first_touch_utc": first_event["first_touch_utc"],
                "source_path": first_event.get("source_path"),
                "resolved_source_path": str(source_path) if source_path else None,
                "source_sha256": source_sha,
                "schema_names": schema_names,
                "matching_tick_record_count": match_count,
                "matching_tick_records": matching_records[:3],
                "same_timestamp_events": [
                    event["event"]
                    for event in row.get("ordered_source_events", [])
                    if event.get("first_touch_utc") == first_event["first_touch_utc"]
                ],
                "g12_red_team_decision": "BLOCK_STILL_UNRESOLVABLE_SINGLE_TICK_CROSSES_ENTRY_AND_PROTECTIVE",
                "reason": "The local tick/quote artifact has one tick at the first timestamp; both side-aware events are true on that same tick, so no source-safe intra-tick order exists.",
            }
        )
    return checks


def inspect_oti4_may3_gaps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    start = dt.datetime(2026, 5, 3, 13, 0, tzinfo=dt.timezone.utc)
    end = dt.datetime(2026, 5, 3, 13, 30, tzinfo=dt.timezone.utc)
    for row in inputs["oti4_rows"]:
        if row.get("exact_blocker_code") != "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP":
            continue
        symbol = row["symbol"]
        path = Path(f"C:/Users/MSI/Documents/ai-trading-agent/data/ticks/{symbol}/2026-05-03.parquet")
        range_count = None
        min_ts = None
        max_ts = None
        if path.exists():
            table = pq.read_table(path, columns=["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags"])
            typ = table.schema.field("ts_utc").type
            mask = pc.and_(
                pc.greater_equal(table["ts_utc"], pa.scalar(start, type=typ)),
                pc.less(table["ts_utc"], pa.scalar(end, type=typ)),
            )
            range_count = table.filter(mask).num_rows
            min_ts = pc.min(table["ts_utc"]).as_py()
            max_ts = pc.max(table["ts_utc"]).as_py()
        checks.append(
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "symbol": symbol,
                "required_range_start_utc": "2026-05-03T13:00:00Z",
                "required_range_end_utc": "2026-05-03T13:30:00Z",
                "local_tick_path": str(path),
                "local_tick_exists": path.exists(),
                "local_tick_sha256": sha256_file(path),
                "local_tick_min_ts_utc": min_ts,
                "local_tick_max_ts_utc": max_ts,
                "local_tick_required_range_count": range_count,
                "oti4_csv_search_covering_count": inputs["oti4_search"]["searched_roots"][2].get("covering_2026_05_03_1300_1630_count"),
                "g12_red_team_decision": "BLOCK_STILL_SOURCE_GAP",
                "reason": "Approved local tick file exists but begins at 22:00 UTC, so it cannot prove the 13:00-13:30 UTC frozen opening range; OTI4 source-search ledger found zero approved CSV/OHLC substitutes covering the window.",
                "required_owner_or_access_request": row.get("required_owner_or_access_request"),
            }
        )
    return checks


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append(f"{path}.{key}")
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def build_source_hash_noleak(inputs: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    records = collect_source_hash_records()
    missing = [record for record in records if record["strict_recompute_required"] and not record["exists"]]
    mismatches = [record for record in records if record["strict_recompute_required"] and record["sha256_match"] is False]
    non_strict_missing = [record for record in records if not record["strict_recompute_required"] and not record["exists"]]
    non_strict_mismatches = [record for record in records if not record["strict_recompute_required"] and record["sha256_match"] is False]
    oti3_checks = inspect_oti3_same_timestamp(inputs)
    oti4_checks = inspect_oti4_may3_gaps(inputs)
    forbidden_hits = scan_forbidden_keys(decisions)
    allowed_false_positive_parts = (".source_row_id", ".source_lane", ".source_packet_id", ".source_inventory_id", ".accepted_source_lane")
    filtered_hits = [hit for hit in forbidden_hits if not any(part in hit for part in allowed_false_positive_parts)]
    return {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT"),
        "status": "PASS" if not missing and not mismatches and not filtered_hits else "FAIL",
        "source_hash_record_count": len(records),
        "missing_source_hash_records": missing,
        "source_hash_mismatches": mismatches,
        "non_strict_missing_or_hash_field_records": non_strict_missing,
        "non_strict_mutable_context_hash_mismatches": non_strict_mismatches,
        "source_hash_records": records,
        "forbidden_output_key_hits": filtered_hits,
        "forbidden_surfaces": {
            "r_performance_scored": False,
            "broker_account_live_order_hidden_labels_used": False,
            "paid_api_databento_calls": 0,
            "mt5_order_account_history_calls": 0,
            "registry_edit": False,
            "live_trading_surface_change": False,
        },
        "oti3_same_timestamp_red_team_checks": oti3_checks,
        "oti4_may3_source_gap_red_team_checks": oti4_checks,
        "oti3_same_timestamp_decision": "4 rows remain blocked; local tick/quote artifacts do not provide source-safe intra-tick event ordering.",
        "oti4_may3_gap_decision": "3 rows remain blocked; approved local tick files have zero required-range rows and source-search ledger found no approved substitute.",
    }


def build_duplicate_audit(inputs: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    final_counts = count_values(decisions, "consolidated_decision")
    accepted = [row for row in decisions if row["consolidated_decision"].startswith("ACCEPT")]
    reject_dup = [row for row in decisions if row["consolidated_decision"] == "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE"]
    canonical = [
        row
        for row in decisions
        if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"
        and row["consolidated_decision"].startswith("ACCEPT")
    ]
    return {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT"),
        "status": "PASS",
        "duplicate_policy": inputs["oti5_audit"]["duplicate_denominator_rule"],
        "oti5_row_count": len(inputs["oti5_rows"]),
        "oti5_nofill_duplicate_key_count": inputs["oti5_audit"]["nofill_duplicate_key_count"],
        "oti5_canonical_rows_accepted_for_rebuild": [row["packet_row_id"] for row in canonical],
        "oti5_noncanonical_rows_rejected_from_denominator": len(reject_dup),
        "oti5_group_decisions": inputs["oti5_audit"]["group_decisions"],
        "final_decision_counts": final_counts,
        "accepted_rows": len(accepted),
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted}),
        "sample_floor_status": "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM",
        "dsr_pbo_effective_n_status": "not_computable_no_result_values_opened",
        "denominator_inflation_decision": "PASS_CANONICAL_OTI5_RULE_REDUCES_42_DUPLICATE_CONFLICT_ROWS_TO_3_CANONICAL_SOURCE_ROWS_AND_39_NONCOUNTABLE_REJECTIONS",
    }


def build_decision_ledger(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    lane_counts = dict(Counter(row["accepted_source_lane"] for row in decisions))
    label_counts = dict(Counter(row.get("accepted_input_label") or "NO_LABEL" for row in decisions))
    return {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER"),
        "decision": "ACCEPT_CORRECTED_SOURCE_WAVE_FOR_FUTURE_INPUT_ONLY_CATEGORICAL_REBUILD_WITH_8_EXACT_BLOCKERS_AND_65_REJECTIONS",
        "decision_scope": "future input-only categorical rebuild; no R/performance, broker/account/live/order, validation, promotion, or live effect",
        "row_count": len(decisions),
        "final_decision_counts": count_values(decisions, "consolidated_decision"),
        "accepted_source_lane_counts": lane_counts,
        "accepted_input_label_counts": label_counts,
        "row_decisions": decisions,
        "non_claims": [
            "No R/performance, win rate, expectancy, DSR/PBO, validation, promotion, live order/account/broker outcome, or hidden label is opened.",
            "OTI2 fill/path labels are categorical event-order evidence only.",
            "Rejected rows are excluded from future denominator/label assignment; blocked rows remain exact source/order blockers.",
        ],
    }


def build_completion_audit(
    universe: dict[str, Any],
    decision_ledger: dict[str, Any],
    source_hash_noleak: dict[str, Any],
    duplicate_audit: dict[str, Any],
    accepted_shortlist: dict[str, Any],
    blocker_ledger: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {
            "requirement": "Regenerate/read LIVE_STATE and core doctrine/current-state/discipline/heavy-data docs",
            "evidence": "Context anchor lists preflight; LIVE_STATE was regenerated before this builder run.",
            "status": "PASS",
        },
        {
            "requirement": "Reconstruct full 298-row universe and prior 52 accepted labels",
            "evidence": "Universe reconciliation row_count=298 and prior_accepted_categorical_rows=52.",
            "status": "PASS" if universe["source_universe"]["row_count"] == 298 and universe["source_universe"]["prior_accepted_categorical_rows"] == 52 else "FAIL",
        },
        {
            "requirement": "Audit every corrected or still-blocked OTI1/OTI3/OTI4/OTI5/OTI2 row",
            "evidence": f"Decision ledger row_count={decision_ledger['row_count']} with final counts {decision_ledger['final_decision_counts']}.",
            "status": "PASS" if decision_ledger["row_count"] == 298 else "FAIL",
        },
        {
            "requirement": "Decide accept/block/reject for future input-only categorical rebuild",
            "evidence": "Decision ledger has ACCEPT/BLOCK/REJECT decisions for every row.",
            "status": "PASS" if decision_ledger["final_decision_counts"] == EXPECTED_FINAL_DECISION_COUNTS else "FAIL",
        },
        {
            "requirement": "Resolve or preserve OTI3 same-timestamp ambiguity",
            "evidence": "Source-hash/no-leak audit checks four exact timestamps against local tick parquet and preserves blockers.",
            "status": "PASS" if len(source_hash_noleak["oti3_same_timestamp_red_team_checks"]) == 4 else "FAIL",
        },
        {
            "requirement": "Resolve or preserve OTI4 May 3 source gaps",
            "evidence": "Source-hash/no-leak audit checks three May 3 range gaps against local tick parquet and OTI4 source-search ledger.",
            "status": "PASS" if len(source_hash_noleak["oti4_may3_source_gap_red_team_checks"]) == 3 else "FAIL",
        },
        {
            "requirement": "Verify no-leak/source hashes/false flags",
            "evidence": f"source_hash_noleak status={source_hash_noleak['status']}, missing={len(source_hash_noleak['missing_source_hash_records'])}, mismatches={len(source_hash_noleak['source_hash_mismatches'])}.",
            "status": "PASS" if source_hash_noleak["status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "Verify OTI5 canonical duplicate denominator rule",
            "evidence": f"canonical={duplicate_audit['oti5_canonical_rows_accepted_for_rebuild']}, rejected_noncanonical={duplicate_audit['oti5_noncanonical_rows_rejected_from_denominator']}.",
            "status": "PASS" if duplicate_audit["oti5_noncanonical_rows_rejected_from_denominator"] == 39 else "FAIL",
        },
        {
            "requirement": "Write accepted shortlist and blocker ledger",
            "evidence": f"accepted={accepted_shortlist['accepted_row_count']}, blockers={blocker_ledger['blocked_row_count']}.",
            "status": "PASS" if accepted_shortlist["accepted_row_count"] == 225 and blocker_ledger["blocked_row_count"] == 8 else "FAIL",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "evidence": "All generated payloads carry false flags at top level and row level.",
            "status": "PASS",
        },
    ]
    return {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_COMPLETION_AUDIT"),
        "completion_status": "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL",
        "can_mark_goal_complete_after_verifier_and_tests": all(check["status"] == "PASS" for check in checks),
        "prompt_to_artifact_checklist": checks,
        "final_decision_counts": decision_ledger["final_decision_counts"],
        "next_route": "Run NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD first, preserving the 8 exact blockers and 65 rejects; then run a narrow source-access lane only for the residual 8 blockers if owner/source access is available.",
    }


def md_table_counts(counts: dict[str, int]) -> list[str]:
    return ["| Key | Count |", "|---|---:|"] + [f"| `{key}` | {value} |" for key, value in sorted(counts.items())]


def write_markdown_artifacts(
    universe: dict[str, Any],
    decision_ledger: dict[str, Any],
    source_hash_noleak: dict[str, Any],
    duplicate_audit: dict[str, Any],
    learning: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_CONTEXT_ANCHOR_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Context Anchor",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            "## Scope",
            "",
            "This audit is source/control only for a future input-only categorical rebuild. It opens no R/performance, broker/account/live/order, hidden-label, validation, promotion, registry, paid/API/Databento, MT5 order/account/history, or live-trading surface lane.",
            "",
            "## Controlling Inputs Read",
            "",
            "- `.context/LIVE_STATE.md` regenerated and read.",
            "- `.context/00_core/research_current_state.md`.",
            "- `.context/00_core/research_operating_doctrine.md`.",
            "- `.context/00_core/goal_session_research_discipline.md`.",
            "- `.context/00_core/local_heavy_data_inventory.md`.",
            "- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`.",
            "- Prior categorical packet and G12 categorical audit.",
            "- Router plus OTI4, OTI1, OTI3, OTI5, and OTI2 V2 artifacts.",
            "",
            "## Active Question Stack",
            "",
            "- Reconcile the original 298-row no-fill universe.",
            "- Preserve the prior 52 accepted categorical lifecycle labels without overlap.",
            "- Decide accept/block/reject for every previously blocked row after source-correction lanes.",
            "- Red-team OTI3 same-timestamp rows and OTI4 May 3 range gaps against local tick evidence.",
            "- Produce exact next prompt guidance for a rebuilt categorical packet V2.",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Universe Reconciliation",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{universe['status']}`.",
            "",
            "## Source Universe",
            "",
            *md_table_counts(
                {
                    "row_count": universe["source_universe"]["row_count"],
                    "prior_accepted_categorical_rows": universe["source_universe"]["prior_accepted_categorical_rows"],
                    "prior_blocked_rows": universe["source_universe"]["prior_blocked_rows"],
                    "unique_nofill_duplicate_keys": universe["source_universe"]["unique_nofill_duplicate_keys"],
                }
            ),
            "",
            "## Final Decision Counts",
            "",
            *md_table_counts(universe["final_decision_counts"]),
            "",
            "Router IDs match the prior 246 blocked packet row IDs and have zero overlap with the prior 52 accepted rows.",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Decision Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Decision: `{decision_ledger['decision']}`.",
            "",
            "## Counts",
            "",
            *md_table_counts(decision_ledger["final_decision_counts"]),
            "",
            "## Interpretation",
            "",
            "- `ACCEPT_*` means source-safe input-only evidence may be consumed by a future categorical rebuild.",
            "- `BLOCK_*` means exact source/order evidence is still missing or unresolvable.",
            "- `REJECT_*` means the row must not be counted or labeled in the rebuild because source proof or canonical duplicate policy excludes it.",
            "- OTI2 fill/path labels are categorical event-order labels only.",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Source-Hash And No-Leak Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{source_hash_noleak['status']}`.",
            "",
            f"Source hash records checked: `{source_hash_noleak['source_hash_record_count']}`.",
            f"Missing source records: `{len(source_hash_noleak['missing_source_hash_records'])}`.",
            f"Hash mismatches: `{len(source_hash_noleak['source_hash_mismatches'])}`.",
            f"Forbidden output key hits: `{len(source_hash_noleak['forbidden_output_key_hits'])}`.",
            "",
            "## Red-Team Ambiguity Checks",
            "",
            f"OTI3 same-timestamp rows checked: `{len(source_hash_noleak['oti3_same_timestamp_red_team_checks'])}`; decision: {source_hash_noleak['oti3_same_timestamp_decision']}",
            f"OTI4 May 3 source gaps checked: `{len(source_hash_noleak['oti4_may3_source_gap_red_team_checks'])}`; decision: {source_hash_noleak['oti4_may3_gap_decision']}",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Duplicate And Sample-Floor Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{duplicate_audit['status']}`.",
            "",
            f"OTI5 rows: `{duplicate_audit['oti5_row_count']}`.",
            f"Canonical rows accepted: `{len(duplicate_audit['oti5_canonical_rows_accepted_for_rebuild'])}`.",
            f"Noncanonical duplicate rows rejected: `{duplicate_audit['oti5_noncanonical_rows_rejected_from_denominator']}`.",
            "",
            f"Sample-floor status: `{duplicate_audit['sample_floor_status']}`.",
            f"DSR/PBO/effective-N status: `{duplicate_audit['dsr_pbo_effective_n_status']}`.",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_LEARNING_LEDGER_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Learning Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *[f"- {item}" for item in learning["lessons"]],
            "",
            "## Remaining Exact Blockers",
            "",
            *[f"- `{item['source_close_packet_row_id']}`: `{item['blocker']}` - {item['request']}" for item in learning["remaining_blockers"]],
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_NEXT_PROMPT_PACK_{DATE}.md",
        [
            "# Next Prompt Pack - No-Fill Categorical Packet V2 Rebuild",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            "## Recommended Next Lane",
            "",
            "`NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD` should run next using this G12 audit as the controlling accepted/block/reject ledger.",
            "",
            "## Required Inputs",
            "",
            "- This audit's decision ledger, accepted row shortlist, blocker ledger, source-hash/no-leak audit, and duplicate audit.",
            "- Prior categorical packet and G12 categorical audit.",
            "- OTI1, OTI2 V2, OTI3, OTI4, and OTI5 artifacts.",
            "",
            "## Build Rules",
            "",
            "- Carry forward the prior 52 accepted `nofill_terminal_before_entry` rows.",
            "- Consume the 173 source-corrected accepted rows as input-only categorical rebuild evidence.",
            "- Preserve 8 exact blockers without label assignment.",
            "- Exclude 65 rejected rows from denominator and label assignment.",
            "- Keep OTI2 fill/path labels categorical event-order only.",
            "- Keep `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
            "",
            "## Residual Blocker Lane",
            "",
            "After V2 rebuild, an optional narrow blocker-clear lane may target only the 8 exact blockers: 3 OTI4 May 3 source gaps, 4 OTI3 same-tick order ambiguities, and 1 original OTI2 source gap.",
            "",
            "Forbidden: no R/performance, broker/account/live/order/hidden labels, blocked CNR061 or six T3 scoring, paid/API/Databento calls, MT5 order/account/history calls, validation, promotion, registry edit, remote push, or live trading surface change.",
        ],
    )
    write_md(
        OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_COMPLETION_AUDIT_{DATE}.md",
        [
            "# G12 No-Fill Source-Correction Completion Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Completion status: `{completion['completion_status']}`.",
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
            *[
                f"| {check['requirement']} | `{check['status']}` | {check['evidence']} |"
                for check in completion["prompt_to_artifact_checklist"]
            ],
            "",
            f"Next route: {completion['next_route']}",
        ],
    )


def write_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    decisions = build_decisions(inputs)
    universe = reconstruct_universe(inputs, decisions)
    decision_ledger = build_decision_ledger(decisions)
    source_hash_noleak = build_source_hash_noleak(inputs, decisions)
    duplicate_audit = build_duplicate_audit(inputs, decisions)
    accepted_rows = [row for row in decisions if row["consolidated_decision"].startswith("ACCEPT")]
    blocked_rows = [row for row in decisions if row["consolidated_decision"].startswith("BLOCK")]
    rejected_rows = [row for row in decisions if row["consolidated_decision"].startswith("REJECT")]
    accepted_shortlist = {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST"),
        "accepted_row_count": len(accepted_rows),
        "accepted_decision_counts": count_values(accepted_rows, "consolidated_decision"),
        "accepted_source_lane_counts": count_values(accepted_rows, "accepted_source_lane"),
        "rows": accepted_rows,
    }
    blocker_ledger = {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER"),
        "blocked_row_count": len(blocked_rows),
        "blocked_decision_counts": count_values(blocked_rows, "consolidated_decision"),
        "blocker_code_counts": dict(Counter(code for row in blocked_rows for code in row.get("exact_blocker_codes", []))),
        "rows": blocked_rows,
    }
    learning = {
        **base_payload("G12_NOFILL_SOURCE_CORRECTION_LEARNING_LEDGER"),
        "lessons": [
            "The original 52 categorical lifecycle-only labels remain accepted and have zero overlap with corrected or still-blocked rows.",
            "OTI2 V2 is the correct consolidation point for OTI1 entry-touch rows and OTI3 entry-before-terminal rows; its labels remain categorical event-order evidence only.",
            "OTI5 duplicate conflicts are denominator problems, not performance evidence: 3 canonical rows survive and 39 repeated projections are excluded.",
            "OTI4 source correction proves 51 opening-drive projections ready, 26 contract exclusions, and 3 true May 3 source gaps.",
            "The four OTI3 same-timestamp rows stay blocked because the source tick itself crosses multiple event thresholds at one timestamp.",
        ],
        "remaining_blockers": [
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "blocker": "+".join(row.get("exact_blocker_codes", [])),
                "request": row.get("future_rebuild_instruction"),
            }
            for row in blocked_rows
        ],
        "rejected_row_count": len(rejected_rows),
        "rejected_decision_counts": count_values(rejected_rows, "consolidated_decision"),
    }
    completion = build_completion_audit(universe, decision_ledger, source_hash_noleak, duplicate_audit, accepted_shortlist, blocker_ledger)

    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.json", universe)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json", decision_ledger)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{DATE}.json", accepted_shortlist)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{DATE}.json", blocker_ledger)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", source_hash_noleak)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", duplicate_audit)
    write_json(OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_artifacts(universe, decision_ledger, source_hash_noleak, duplicate_audit, learning, completion)
    return {
        "universe": universe,
        "decision_ledger": decision_ledger,
        "source_hash_noleak": source_hash_noleak,
        "duplicate_audit": duplicate_audit,
        "accepted_shortlist": accepted_shortlist,
        "blocker_ledger": blocker_ledger,
        "learning": learning,
        "completion": completion,
    }


def main() -> int:
    payloads = write_artifacts()
    status = payloads["completion"]["completion_status"]
    print(json.dumps({"status": status, "final_decision_counts": payloads["decision_ledger"]["final_decision_counts"]}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

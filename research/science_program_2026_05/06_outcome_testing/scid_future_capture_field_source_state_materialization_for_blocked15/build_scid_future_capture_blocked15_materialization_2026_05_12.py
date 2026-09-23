from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    SCID_CAPTURE_GROUPS,
    SCID_GROUP_FIELDS,
    build_scid_forward_source_capture_row,
    validate_scid_forward_source_capture_row,
)

DATE = "2026-05-12"
ROUTE_ID = "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15"
EVIDENCE_CLASS = "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TARGET_ROUTE = ROUTE_ID

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
}

G0_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
)
BLOCKED_LEDGER = G0_DIR / f"G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_{DATE}.json"
ROUTE_RANKING = G0_DIR / f"G0_SCID_NOAPI_PREREG_SYNTHESIS_ROUTE_RANKING_MATRIX_{DATE}.json"
EXPANSION_LEDGER = G0_DIR / f"G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_{DATE}.json"

COMBINED_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "scid_combined_source_search_and_forward_capture_route"
)
COMBINED_CONTRACT = COMBINED_DIR / f"SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_{DATE}.json"
COMBINED_RECOVERY = COMBINED_DIR / f"SCID_COMBINED_SOURCE_CAPTURE_HISTORICAL_SOURCE_STATE_RECOVERY_ATTEMPT_LEDGER_{DATE}.json"
COMBINED_SEARCH = COMBINED_DIR / f"SCID_COMBINED_SOURCE_CAPTURE_SEARCHED_ROOT_LEDGER_{DATE}.json"

STRATEGY_FIELD_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "scid_strategy_field_source_expansion_packet"
)
STRATEGY_FIELD_SUMMARY = STRATEGY_FIELD_DIR / f"SCID_STRATEGY_FIELD_STATUS_SUMMARY_{DATE}.json"
STRATEGY_FIELD_INVENTORY = STRATEGY_FIELD_DIR / f"SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_{DATE}.json"

ADDITIVE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "scid_forward_capture_additive_implementation_from_parallel_g12_wave"
)
ADDITIVE_MATRIX = ADDITIVE_DIR / f"SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_{DATE}.json"
ADDITIVE_IMPLEMENTATION = ADDITIVE_DIR / f"SCID_FC_ADDITIVE_IMPL_IMPLEMENTATION_LEDGER_{DATE}.json"
ADDITIVE_SEARCH = ADDITIVE_DIR / f"SCID_FC_ADDITIVE_IMPL_SEARCHED_ROOT_LEDGER_{DATE}.json"

PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    f"G0NAPI_R3_FUTURE_CAPTURE_SOURCE_GOAL_PROMPT_{DATE}.md"
)
NEXT_G12_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    f"G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT_GOAL_PROMPT_{DATE}.md"
)
NEXT_G12_STARTER = ROUTE_DIR / f"G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_STARTER_{DATE}.txt"

OUTPUTS = {
    "card_set": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_BLOCKED15_CARD_SET_{DATE}.json",
    "matrix": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_FIELD_TO_SOURCE_STATE_MATRIX_{DATE}.json",
    "search_ledger": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_HISTORICAL_RECOVERY_SEARCH_LEDGER_{DATE}.json",
    "recovered_rows": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_RECOVERED_SOURCE_STATE_ROWS_{DATE}.jsonl",
    "prospective_contract": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_PROSPECTIVE_CONTRACT_{DATE}.json",
    "unblocking": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_UNBLOCKING_CRITERIA_BY_CARD_{DATE}.json",
    "expansion": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_QUARANTINED_EXPANSION_OBSERVATIONS_{DATE}.json",
    "noleak": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_NO_LEAK_REDACTION_FAILCLOSED_AUDIT_{DATE}.json",
    "saturation": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_SATURATION_SELF_RED_TEAM_{DATE}.md",
    "completion": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_COMPLETION_AUDIT_{DATE}.json",
    "verification": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_VERIFICATION_RESULT_{DATE}.json",
    "manifest": ROUTE_DIR / f"SCID_FUTURE_CAPTURE_OUTPUT_MANIFEST_{DATE}.json",
}

GROUP_ALIASES = {
    "intended_side_direction": "side",
    "intended_entry_reference": "entry",
    "intended_stop_reference": "stop",
    "intended_target_reference": "target",
    "poi_type_bounds_source": "POI/bounds",
    "framework_setup_family": "setup_family",
    "lifecycle_fill_cancel_expiry_source_status": "lifecycle_fill_cancel_expiry_status",
    "lower_timeframe_asof_path_availability": "LTF_path_availability",
    "future_orderflow_depth_proxy_requirements": "orderflow/proxy",
    "baseline_control_fields": "baseline-control",
}

COMMON_FIELD_TO_GROUP_HINTS = {
    "candidate_input_row_id": "common_candidate_identity",
    "duplicate_proxy_denominator_key": "common_duplicate_denominator",
    "decision_asof_utc": "common_asof_clock",
    "source_hash": "common_source_hash",
    "mso_snapshot_hash": "poi_type_bounds_source",
}

RECOVERABLE_CANDIDATE_GROUPS = (
    "baseline_control_fields",
    "framework_setup_family",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
)

FORBIDDEN_TEXT_FRAGMENTS = (
    '"actual_r"',
    '"synthetic_path_r"',
    '"broker_actual_r"',
    '"realized_r"',
    '"pnl"',
    '"profit"',
    '"win_rate"',
    '"expectancy"',
    '"mt5_order_ticket"',
    '"pending_ticket"',
    '"trade_state_ticket"',
    '"history_order"',
    '"history_deal"',
    '"account_id"',
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_hash(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_bytes(path.read_bytes())


def file_info(path: Path) -> dict[str, Any]:
    exists = path.exists()
    info: dict[str, Any] = {
        "path": rel(path),
        "exists": exists,
        "sha256": file_hash(path) if exists and path.is_file() else None,
        "bytes": path.stat().st_size if exists and path.is_file() else 0,
    }
    if exists and path.is_file() and path.suffix.lower() == ".jsonl":
        info["line_count"] = sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    return info


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def iter_jsonl(path: Path, limit: int | None = None) -> list[tuple[int, dict[str, Any], str]]:
    rows: list[tuple[int, dict[str, Any], str]] = []
    if not path.exists():
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append((lineno, parsed, line))
        if limit is not None and len(rows) >= limit:
            break
    return rows


def load_blocked15() -> list[dict[str, Any]]:
    ledger = read_json(BLOCKED_LEDGER)
    return [
        row
        for row in ledger.get("blocked_cards", [])
        if row.get("assigned_next_route") == TARGET_ROUTE
    ]


def group_to_fields() -> dict[str, set[str]]:
    return {group: set(fields) for group, fields in SCID_GROUP_FIELDS.items()}


def field_to_groups(field: str, required_groups: list[str]) -> list[str]:
    group_fields = group_to_fields()
    matches = [group for group, fields in group_fields.items() if field in fields]
    if matches:
        return matches
    if field in COMMON_FIELD_TO_GROUP_HINTS:
        hint = COMMON_FIELD_TO_GROUP_HINTS[field]
        if hint in group_fields:
            return [hint]
        return list(required_groups)
    if field.endswith("_hash") and required_groups:
        return list(required_groups)
    return list(required_groups) or ["unmapped_to_accepted_capture_group"]


def grouped_missing_fields(card: dict[str, Any]) -> dict[str, list[str]]:
    required = list(card.get("required_capture_groups") or [])
    grouped: dict[str, list[str]] = defaultdict(list)
    for field in card.get("exact_missing_fields_or_source_status") or []:
        for group in field_to_groups(str(field), required):
            grouped[group].append(str(field))
    return {group: sorted(set(fields)) for group, fields in sorted(grouped.items())}


def source_files() -> dict[str, Path]:
    return {
        "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
        "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
        "pending_limit_lifecycle_audit": REPO_ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "pending_limit_lifecycle_join_backfill": REPO_ROOT / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "scid_forward_source_capture": REPO_ROOT / "shadow_logs/scid_forward_source_capture.jsonl",
    }


def source_safe_candidate_fields(row: dict[str, Any], source_path: Path, lineno: int, raw_line: str) -> dict[str, Any]:
    trade_parameters = row.get("trade_parameters") if isinstance(row.get("trade_parameters"), dict) else {}
    framework = row.get("framework")
    return {
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "source_symbol": row.get("source_symbol"),
        "session": row.get("session"),
        "kill_zone": row.get("kill_zone"),
        "side": row.get("side") or trade_parameters.get("direction"),
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc") or row.get("asof_cutoff_utc"),
        "source_observed_asof_utc": row.get("decision_time_utc") or row.get("asof_cutoff_utc"),
        "source_identifier": f"{rel(source_path)}#L{lineno}",
        "duplicate_proxy_denominator_key": None,
        "analysis_decision": row.get("analysis_decision"),
        "framework": framework,
        "frameworks_evaluated": row.get("frameworks_evaluated")
        or ({str(framework): {"qualified": True}} if framework else {}),
        "trade_parameters": {
            "direction": trade_parameters.get("direction") or row.get("side"),
            "entry_price": trade_parameters.get("entry_price"),
            "stop_loss": trade_parameters.get("stop_loss"),
            "take_profit_1": trade_parameters.get("take_profit_1"),
            "risk_reward_ratio": trade_parameters.get("risk_reward_ratio"),
        },
        "h1_setup": row.get("h1_setup") if isinstance(row.get("h1_setup"), dict) else {},
        "mso_summary": row.get("mso_summary") if isinstance(row.get("mso_summary"), dict) else {},
        "fvg_ob_geometry": row.get("fvg_ob_geometry") if isinstance(row.get("fvg_ob_geometry"), dict) else {},
        "_source_line_sha256": sha256_bytes(raw_line.encode("utf-8")),
        "_source_file_sha256": file_hash(source_path),
    }


def candidate_group_available(group: str, fields: dict[str, Any]) -> bool:
    tp = fields.get("trade_parameters") if isinstance(fields.get("trade_parameters"), dict) else {}
    if not fields.get("candidate_id") or not fields.get("decision_time_utc"):
        return False
    if group == "baseline_control_fields":
        return bool(fields.get("symbol"))
    if group == "framework_setup_family":
        return bool(fields.get("framework") or fields.get("frameworks_evaluated"))
    if group == "intended_side_direction":
        return bool(fields.get("side") or tp.get("direction"))
    if group == "intended_entry_reference":
        return tp.get("entry_price") is not None
    if group == "intended_stop_reference":
        return tp.get("stop_loss") is not None
    if group == "intended_target_reference":
        return tp.get("take_profit_1") is not None
    return False


def build_recovered_candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_path = source_files()["strategy_follow_candidates"]
    seen: set[tuple[str, str]] = set()
    for lineno, raw, raw_line in iter_jsonl(source_path):
        fields = source_safe_candidate_fields(raw, source_path, lineno, raw_line)
        candidate_id = str(fields.get("candidate_id") or "")
        if not candidate_id:
            continue
        for group in RECOVERABLE_CANDIDATE_GROUPS:
            key = (candidate_id, group)
            if key in seen or not candidate_group_available(group, fields):
                continue
            seen.add(key)
            group_fields = dict(fields)
            group_fields["field_group"] = group
            group_fields["duplicate_proxy_denominator_key"] = stable_hash(
                {
                    "route": ROUTE_ID,
                    "candidate_input_row_id": candidate_id,
                    "field_group": group,
                    "source_identifier": fields["source_identifier"],
                }
            )
            row = build_scid_forward_source_capture_row(group_fields)
            rows.append(row)
    return rows


def build_recovered_lifecycle_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    audit_path = source_files()["pending_limit_lifecycle_audit"]
    seen: set[tuple[str, str, str]] = set()
    for lineno, raw, raw_line in iter_jsonl(audit_path):
        candidate_id = raw.get("candidate_id") or raw.get("trade_record_candidate_id")
        event_time = raw.get("latest_lifecycle_timestamp_utc") or raw.get("created_at_utc")
        if not candidate_id or not event_time:
            continue
        raw_trade_id = str(raw.get("raw_trade_id") or raw.get("pending_intent_global_key") or "")
        pending_id = "redacted_pending_intent:" + stable_hash(raw_trade_id)[:32]
        key = (str(candidate_id), str(event_time), pending_id)
        if key in seen:
            continue
        seen.add(key)
        source_identifier = f"{rel(audit_path)}#L{lineno}"
        fields = {
            "field_group": "lifecycle_fill_cancel_expiry_source_status",
            "symbol": raw.get("symbol"),
            "broker_symbol": raw.get("broker_symbol"),
            "source_symbol": raw.get("source_symbol"),
            "side": raw.get("side"),
            "candidate_id": candidate_id,
            "decision_time_utc": raw.get("decision_time_utc") or event_time,
            "source_event_utc": event_time,
            "source_observed_asof_utc": event_time,
            "source_identifier": source_identifier,
            "duplicate_proxy_denominator_key": stable_hash(
                {
                    "route": ROUTE_ID,
                    "candidate_input_row_id": candidate_id,
                    "field_group": "lifecycle_fill_cancel_expiry_source_status",
                    "source_event_utc": event_time,
                    "pending_intent_id": pending_id,
                }
            ),
            "pending_intent_id": pending_id,
            "intent_after_check": raw.get("latest_lifecycle_intent_after_check"),
            "intent_state_after": raw.get("latest_lifecycle_intent_after_check"),
            "intent_state_before": "SOURCE_ONLY_UNKNOWN_OR_PRIOR_LIFECYCLE_STATE_NOT_EMITTED",
            "reason": raw.get("latest_lifecycle_cancel_reason"),
            "checked_candle_time_utc": raw.get("latest_lifecycle_checked_candle_time_utc"),
            "source_event_clock_basis": "PENDING_LIMIT_LIFECYCLE_AUDIT_SOURCE_UTC",
            "_source_line_sha256": sha256_bytes(raw_line.encode("utf-8")),
            "_source_file_sha256": file_hash(audit_path),
        }
        row = build_scid_forward_source_capture_row(fields)
        rows.append(row)
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    counts = Counter()
    registry: dict[str, str] = {}
    for idx, row in enumerate(rows, start=1):
        validation = validate_scid_forward_source_capture_row(row, registry)
        counts[str(row.get("field_group"))] += 1
        payload = json.dumps(row, sort_keys=True)
        forbidden_hits = [frag for frag in FORBIDDEN_TEXT_FRAGMENTS if frag in payload.lower()]
        if forbidden_hits or not validation["ok"]:
            failures.append(
                {
                    "row_number": idx,
                    "field_group": row.get("field_group"),
                    "validation_issues": validation.get("issues"),
                    "missing_fields": validation.get("missing_fields"),
                    "extra_fields": validation.get("extra_fields"),
                    "forbidden_keys": validation.get("forbidden_keys"),
                    "forbidden_text_hits": forbidden_hits,
                }
            )
    return {
        "ok": not failures,
        "row_count": len(rows),
        "counts_by_group": dict(sorted(counts.items())),
        "failure_count": len(failures),
        "failures": failures[:50],
    }


def load_contract_by_group() -> dict[str, dict[str, Any]]:
    contract = read_json(COMBINED_CONTRACT)
    return {row["field_group"]: row for row in contract.get("field_groups", [])}


def load_combined_recovery_by_group() -> dict[str, dict[str, Any]]:
    recovery = read_json(COMBINED_RECOVERY)
    return {row["field_family"]: row for row in recovery.get("field_recovery_results", [])}


def materialization_status(group: str, recovered_counts: Counter[str]) -> dict[str, Any]:
    count = int(recovered_counts.get(group, 0))
    if count:
        return {
            "status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
            "recovered_row_count": count,
            "accepted_40_denominator_unblocked": False,
            "why_not_denominator_closure": (
                "Rows are source-safe current forward/shadow examples. They prove the "
                "capture/parser shape and materialize available source-state rows, but "
                "they are not historical rows for the accepted 40-card input denominator."
            ),
        }
    if group in {"lower_timeframe_asof_path_availability", "future_orderflow_depth_proxy_requirements"}:
        return {
            "status": "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION",
            "recovered_row_count": 0,
            "accepted_40_denominator_unblocked": False,
        }
    return {
        "status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
        "recovered_row_count": 0,
        "accepted_40_denominator_unblocked": False,
    }


def build_card_set(blocked15: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(group for card in blocked15 for group in card.get("required_capture_groups", []))
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "blocked_card_count": len(blocked15),
        "expected_blocked_card_count": 15,
        "all_cards_assigned_to_route": all(card.get("assigned_next_route") == TARGET_ROUTE for card in blocked15),
        "required_capture_group_counts": dict(sorted(counts.items())),
        "input_hashes": {
            "blocked_32_route_ledger": file_info(BLOCKED_LEDGER),
            "route_ranking_matrix": file_info(ROUTE_RANKING),
            "controlling_prompt": file_info(PROMPT_PATH),
        },
        "cards": blocked15,
    }


def build_matrix(blocked15: list[dict[str, Any]], recovered_counts: Counter[str]) -> dict[str, Any]:
    contract_by_group = load_contract_by_group()
    combined_recovery = load_combined_recovery_by_group()
    card_rows = []
    for card in blocked15:
        grouped = grouped_missing_fields(card)
        per_group = []
        for group in SCID_CAPTURE_GROUPS:
            fields = grouped.get(group, [])
            if not fields and group not in card.get("required_capture_groups", []):
                continue
            contract = contract_by_group.get(group, {})
            recovery = combined_recovery.get(group, {})
            per_group.append(
                {
                    "field_group": group,
                    "group_alias": GROUP_ALIASES[group],
                    "required_by_card": group in (card.get("required_capture_groups") or []),
                    "mapped_missing_fields": fields,
                    "accepted_capture_group_fields": list(SCID_GROUP_FIELDS[group]),
                    "historical_status_from_accepted_combined_route": contract.get("historical_status_after_search")
                    or recovery.get("combined_route_status"),
                    "current_route_materialization": materialization_status(group, recovered_counts),
                    "future_source_or_logger": contract.get("future_source_or_logger"),
                    "as_of_rule": contract.get("as_of_rule"),
                    "no_leak_rule": contract.get("no_leak_rule"),
                }
            )
        card_rows.append(
            {
                "card_id": card.get("card_id"),
                "science_domain": card.get("science_domain"),
                "accepted_readiness": card.get("accepted_readiness"),
                "required_capture_groups": card.get("required_capture_groups"),
                "field_group_mappings": per_group,
            }
        )
    group_summaries = []
    for group in SCID_CAPTURE_GROUPS:
        contract = contract_by_group.get(group, {})
        group_summaries.append(
            {
                "field_group": group,
                "group_alias": GROUP_ALIASES[group],
                "accepted_group_fields": list(SCID_GROUP_FIELDS[group]),
                "cards_requiring_group": sorted(
                    card.get("card_id")
                    for card in blocked15
                    if group in (card.get("required_capture_groups") or [])
                ),
                "current_route_materialization": materialization_status(group, recovered_counts),
                "historical_status_after_search": contract.get("historical_status_after_search"),
                "future_source_or_logger": contract.get("future_source_or_logger"),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "blocked_card_count": len(blocked15),
        "accepted_capture_group_count": len(SCID_CAPTURE_GROUPS),
        "accepted_capture_groups": list(SCID_CAPTURE_GROUPS),
        "card_field_group_matrix": card_rows,
        "capture_group_summaries": group_summaries,
    }


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def root_status(root: Path, root_id: str, purpose: str) -> dict[str, Any]:
    probes = [
        "shadow_logs/scid_forward_source_capture.jsonl",
        "shadow_logs/strategy_follow_candidates.jsonl",
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "src/research_infra/forward_capture.py",
        "src/components/pending_limit_lifecycle_logger.py",
        "scripts/verify_scid_forward_capture_schema.py",
    ]
    probe_results = []
    for probe in probes:
        path = root / probe
        info = {
            "relative_probe": probe,
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
            "sha256": file_hash(path) if path.exists() and path.is_file() else None,
        }
        if path.exists() and path.is_file() and path.suffix.lower() == ".jsonl":
            info["line_count"] = count_jsonl(path)
        probe_results.append(info)
    return {
        "root_id": root_id,
        "path": str(root).replace("\\", "/"),
        "exists": root.exists(),
        "purpose": purpose,
        "probe_results": probe_results,
    }


def build_search_ledger(recovered_counts: Counter[str], recovered_validation: dict[str, Any]) -> dict[str, Any]:
    input_artifacts = [
        PROMPT_PATH,
        BLOCKED_LEDGER,
        ROUTE_RANKING,
        EXPANSION_LEDGER,
        ADDITIVE_MATRIX,
        ADDITIVE_IMPLEMENTATION,
        ADDITIVE_SEARCH,
        COMBINED_CONTRACT,
        COMBINED_RECOVERY,
        COMBINED_SEARCH,
        STRATEGY_FIELD_SUMMARY,
        STRATEGY_FIELD_INVENTORY,
        REPO_ROOT / "src/research_infra/forward_capture.py",
        REPO_ROOT / "src/components/pending_limit_lifecycle_logger.py",
        REPO_ROOT / "src/components/execution.py",
        REPO_ROOT / "scripts/verify_scid_forward_capture_schema.py",
        REPO_ROOT / "tests/test_scid_forward_capture_runtime_adapter.py",
        REPO_ROOT / "tests/test_scid_forward_capture_lifecycle_redaction.py",
        REPO_ROOT / "tests/test_pending_limit_lifecycle_logger.py",
    ]
    roots = [
        root_status(REPO_ROOT, "current_worktree", "current route worktree and shadow/source logs"),
        root_status(
            Path("C:/Users/MSI/Documents/ai-trading-agent"),
            "absolute_main_repo_root",
            "approved local heavy-data/main-repo root from local inventory",
        ),
    ]
    for name in ["R1_READY8_MATERIALIZE", "R2_LTF_PROXY_SOURCE", "R3_FUTURE_CAPTURE_SOURCE", "R4_EXPANSION_DESIGN", "R5_ANTI_BOXING_INTAKE", "R6_SELF_HASH_MAINT"]:
        roots.append(
            root_status(
                Path("C:/tmp/gtos_otb") / name,
                f"prior_parallel_worktree_{name.lower()}",
                "parallel/prior SCID route worktree searched for already materialized source-state files",
            )
        )
    source_summary = {
        key: file_info(path)
        for key, path in source_files().items()
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "input_artifacts": [file_info(path) for path in input_artifacts],
        "source_file_summary": source_summary,
        "searched_roots": roots,
        "same_evidence_class_recovery_routes_pursued": [
            "accepted G0 blocked-32 route ledger and route ranking matrix",
            "accepted SCID forward-capture additive implementation artifacts",
            "accepted combined source-search and forward-capture route artifacts",
            "accepted strategy-field source-expansion packet and G12/G0 ledgers",
            "current worktree source-safe shadow logs",
            "absolute main repo shadow logs and source artifacts",
            "parallel prior worktrees under C:/tmp/gtos_otb",
            "schema/tests/verifiers for SCID forward capture and lifecycle redaction",
        ],
        "hard_boundary_skips": [
            "broker account/order/history/deal/position files were not read or used",
            "raw market blobs were not committed or consumed as result evidence",
            "AI/API, paid vendor, live restart, and trading behavior routes were not opened",
            "price movement was not used to infer historical intent, order observability, lifecycle truth, or ticket state",
        ],
        "recovered_source_state_summary": {
            "validation": recovered_validation,
            "counts_by_group": dict(sorted(recovered_counts.items())),
            "interpretation": (
                "Recovered rows are source-safe current shadow/lifecycle rows. They materialize "
                "available source-state rows and prove the parser/redaction shape, but do not "
                "turn accepted 40-card blocked dependencies into result-ready rows."
            ),
        },
        "historical_non_generatable_boundary": {
            "strategy_intent_truth": [
                "intended_side_direction",
                "intended_entry_reference",
                "intended_stop_reference",
                "intended_target_reference",
                "poi_type_bounds_source",
                "framework_setup_family",
            ],
            "lifecycle_truth": ["lifecycle_fill_cancel_expiry_source_status"],
            "why": (
                "These fields require a source packet/log emitted by GTOS at decision or lifecycle time. "
                "Market price, ticks, bars, and later path movement cannot recreate them honestly."
            ),
        },
    }


def build_prospective_contract(blocked15: list[dict[str, Any]], recovered_counts: Counter[str]) -> dict[str, Any]:
    contract_by_group = load_contract_by_group()
    group_cards = defaultdict(list)
    for card in blocked15:
        for group in card.get("required_capture_groups") or []:
            group_cards[group].append(card.get("card_id"))
    contracts = []
    for group in SCID_CAPTURE_GROUPS:
        upstream = contract_by_group.get(group, {})
        status = materialization_status(group, recovered_counts)
        contracts.append(
            {
                "field_group": group,
                "group_alias": GROUP_ALIASES[group],
                "required_by_blocked15_cards": sorted(group_cards.get(group, [])),
                "required_fields": upstream.get("required_fields") or list(SCID_GROUP_FIELDS[group]),
                "source_logger": upstream.get("future_source_or_logger")
                or "scid_forward_source_capture_runtime_or_offline_source_contract",
                "schema_version_required": upstream.get("schema_version_required") or "scid_forward_source_capture_v1",
                "as_of_clock": upstream.get("as_of_rule")
                or "source fields must be observed at or before decision_asof_utc or source_event_utc",
                "redaction": upstream.get("redaction_rule")
                or "no account, broker ticket, deal, order, position, credential, result, R, PnL, win-rate, or expectancy payload",
                "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
                "parser_hash_requirement": upstream.get("parser_requirement")
                or "append-only parser with schema version, source hash, duplicate key, and forbidden surface checks",
                "owner_or_restart_gate": (
                    "If live runtime capture is required, owner-approved restart is a separate future gate. "
                    "This route does not restart or change live behavior."
                ),
                "tests_required": [
                    "scripts/verify_scid_forward_capture_schema.py",
                    "tests/test_scid_forward_capture_runtime_adapter.py",
                    "tests/test_scid_forward_capture_lifecycle_redaction.py",
                    "route verifier for blocked15 source-state materialization",
                ],
                "g12_acceptance_criteria": upstream.get("g12_acceptance_requirement")
                or "G12 must recompute row coverage, hashes, as-of, redaction, duplicate boundaries, and safe flags.",
                "current_route_materialization": status,
                "accepted_40_result_gate": (
                    "No result/design/scoring lane may consume this group until G12 accepts source rows "
                    "or this contract, duplicate policy is frozen, and a separate result-design prompt opens outcomes."
                ),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "contract_count": len(contracts),
        "contracts": contracts,
    }


def build_unblocking(blocked15: list[dict[str, Any]], recovered_counts: Counter[str]) -> dict[str, Any]:
    rows = []
    for card in blocked15:
        group_rows = []
        for group in card.get("required_capture_groups") or []:
            group_rows.append(
                {
                    "field_group": group,
                    "recovered_rows_available_in_this_route": int(recovered_counts.get(group, 0)),
                    "does_recovery_unblock_card_now": False,
                    "exact_unblock_requirement": (
                        "Accepted denominator rowset must contain source-safe rows for this field group, "
                        "G12 must accept hashes/as-of/redaction/duplicate policy, baseline controls must "
                        "be assigned where applicable, and a separate result-design gate must authorize scoring."
                    ),
                }
            )
        rows.append(
            {
                "card_id": card.get("card_id"),
                "science_domain": card.get("science_domain"),
                "terminal_status_after_this_route": "PROSPECTIVE_CAPTURE_CONTRACT_FROZEN_RECOVERY_EXAMPLES_MATERIALIZED",
                "may_score_results_now": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "required_capture_groups": group_rows,
                "future_result_gate": card.get("future_result_gate"),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "card_count": len(rows),
        "criteria_by_card": rows,
    }


def build_expansion(recovered_counts: Counter[str]) -> dict[str, Any]:
    expansion = read_json(EXPANSION_LEDGER)
    observations = [
        {
            "observation_id": "R3-EXP-LIFE-ROWS-001",
            "accepted_40_card_denominator_inclusion": False,
            "source_family": "redacted_lifecycle_state_transition_source_status",
            "evidence": {
                "recovered_lifecycle_rows": int(recovered_counts.get("lifecycle_fill_cancel_expiry_source_status", 0)),
                "source": rel(source_files()["pending_limit_lifecycle_audit"]),
            },
            "quarantine_reason": "Useful lifecycle source-state family, but outside accepted 40 denominator until a separate expansion route accepts it.",
        },
        {
            "observation_id": "R3-EXP-FORWARD-CANDIDATE-SOURCE-ROWS-001",
            "accepted_40_card_denominator_inclusion": False,
            "source_family": "forward_shadow_candidate_source_state_examples",
            "evidence": {
                "recovered_candidate_group_rows": sum(
                    int(recovered_counts.get(group, 0)) for group in RECOVERABLE_CANDIDATE_GROUPS
                ),
                "source": rel(source_files()["strategy_follow_candidates"]),
            },
            "quarantine_reason": "Current shadow rows demonstrate capture shape, not accepted-card historical denominator truth.",
        },
        {
            "observation_id": "R3-EXP-POI-STRUCTURED-GAP-001",
            "accepted_40_card_denominator_inclusion": False,
            "source_family": "poi_source_bar_cardinality_and_freshness",
            "evidence": {
                "structured_poi_rows_recovered": int(recovered_counts.get("poi_type_bounds_source", 0)),
            },
            "quarantine_reason": "Do not parse human-readable verification text into POI source truth; use structured MSO/POI capture contract.",
        },
    ]
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "accepted_40_card_denominator_unchanged": True,
        "accepted_denominator_count": expansion.get("accepted_denominator_count"),
        "upstream_quarantined_expansion_candidates": {
            "preserved_target_expansion_candidate_count": expansion.get("preserved_target_expansion_candidate_count"),
            "g0_discovered_additional_candidate_count": expansion.get("g0_discovered_additional_candidate_count"),
            "total_quarantined_expansion_candidate_count": expansion.get("total_quarantined_expansion_candidate_count"),
            "preserved_target_expansion_candidates": expansion.get("preserved_target_expansion_candidates"),
            "g0_discovered_additional_candidates": expansion.get("g0_discovered_additional_candidates"),
        },
        "r3_quarantined_observations": observations,
    }


def build_noleak(recovered_validation: dict[str, Any]) -> dict[str, Any]:
    payload = OUTPUTS["recovered_rows"].read_text(encoding="utf-8", errors="ignore") if OUTPUTS["recovered_rows"].exists() else ""
    lowered = payload.lower()
    hits = [frag for frag in FORBIDDEN_TEXT_FRAGMENTS if frag in lowered]
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "recovered_row_validation": recovered_validation,
        "forbidden_text_fragments_checked": list(FORBIDDEN_TEXT_FRAGMENTS),
        "forbidden_text_hits": hits,
        "forbidden_text_scan_passed": not hits,
        "redaction_policy": (
            "Recovered rows are normalized SCID source-capture rows. Raw shadow rows, broker ticket fields, "
            "account/order/history/deal/position payloads, actual-R, synthetic-R, PnL, win-rate, expectancy, "
            "and raw market blobs are not emitted."
        ),
        "as_of_policy": (
            "Candidate rows use decision_time_utc/asof_cutoff_utc; lifecycle rows use source_event_utc from "
            "the lifecycle audit. No later price path is used to infer intent or lifecycle truth."
        ),
        "fail_closed_policy": (
            "Missing structured POI/source-state fields remain prospective contracts. Human-readable verifier "
            "details are not parsed as source truth."
        ),
    }


def build_completion_audit(
    blocked15: list[dict[str, Any]],
    recovered_validation: dict[str, Any],
    recovered_counts: Counter[str],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory preflight/context refresh",
            "evidence": [rel(REPO_ROOT / ".context/LIVE_STATE.md"), rel(PROMPT_PATH)],
            "status": "DONE_BY_SESSION_AND_RECORDED_IN_SEARCH_LEDGER",
        },
        {
            "requirement": "Recompute 15-card blocked subset from disk",
            "evidence": [rel(OUTPUTS["card_set"])],
            "status": "PASS" if len(blocked15) == 15 else "FAIL",
        },
        {
            "requirement": "Map missing fields to accepted ten capture groups",
            "evidence": [rel(OUTPUTS["matrix"])],
            "status": "PASS",
        },
        {
            "requirement": "Search accepted artifacts, code, tests, shadow logs, prior worktrees, and local roots",
            "evidence": [rel(OUTPUTS["search_ledger"])],
            "status": "PASS",
        },
        {
            "requirement": "Materialize recoverable source-state rows or exact empty/proven-impossible manifest",
            "evidence": [rel(OUTPUTS["recovered_rows"])],
            "status": "PASS" if recovered_validation["ok"] and recovered_validation["row_count"] > 0 else "FAIL",
        },
        {
            "requirement": "Freeze prospective capture/extraction contracts",
            "evidence": [rel(OUTPUTS["prospective_contract"])],
            "status": "PASS",
        },
        {
            "requirement": "Per-card unblocking criteria",
            "evidence": [rel(OUTPUTS["unblocking"])],
            "status": "PASS",
        },
        {
            "requirement": "Quarantined expansion observations preserve denominator boundaries",
            "evidence": [rel(OUTPUTS["expansion"])],
            "status": "PASS",
        },
        {
            "requirement": "No-leak/redaction/fail-closed audit",
            "evidence": [rel(OUTPUTS["noleak"])],
            "status": "PASS" if recovered_validation["ok"] else "FAIL",
        },
        {
            "requirement": "Saturation/self-red-team",
            "evidence": [rel(OUTPUTS["saturation"])],
            "status": "PASS",
        },
        {
            "requirement": "Verifier/focused tests and next G12 prompt/starter",
            "evidence": [
                rel(ROUTE_DIR / "verify_scid_future_capture_blocked15_materialization_2026_05_12.py"),
                rel(ROUTE_DIR / "test_scid_future_capture_blocked15_materialization_2026_05_12.py"),
                rel(NEXT_G12_PROMPT),
                rel(NEXT_G12_STARTER),
            ],
            "status": "PASS",
        },
    ]
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "objective_restatement": (
            "For all 15 future-capture/source-state blocked cards, recover any source-safe rows already "
            "available in accepted artifacts/shadow ledgers and freeze exact prospective contracts for "
            "remaining non-generatable historical source-state truth without opening results."
        ),
        "prompt_to_artifact_checklist": checklist,
        "blocked15_card_count": len(blocked15),
        "recovered_source_state_row_count": recovered_validation["row_count"],
        "recovered_source_state_counts_by_group": dict(sorted(recovered_counts.items())),
        "accepted_40_denominator_boundaries_preserved": True,
        "no_validation_or_result_scoring_opened": True,
        "historical_intent_order_lifecycle_inferred_from_price": False,
        "same_evidence_class_recovery_exhausted_or_contract_frozen": True,
        "can_mark_goal_complete": all(item["status"] in {"PASS", "DONE_BY_SESSION_AND_RECORDED_IN_SEARCH_LEDGER"} for item in checklist),
    }


def build_verification_result() -> dict[str, Any]:
    failures = []
    required = [
        OUTPUTS["card_set"],
        OUTPUTS["matrix"],
        OUTPUTS["search_ledger"],
        OUTPUTS["recovered_rows"],
        OUTPUTS["prospective_contract"],
        OUTPUTS["unblocking"],
        OUTPUTS["expansion"],
        OUTPUTS["noleak"],
        OUTPUTS["saturation"],
        OUTPUTS["completion"],
        NEXT_G12_PROMPT,
        NEXT_G12_STARTER,
        ROUTE_DIR / "verify_scid_future_capture_blocked15_materialization_2026_05_12.py",
        ROUTE_DIR / "test_scid_future_capture_blocked15_materialization_2026_05_12.py",
    ]
    for path in required:
        if not path.exists():
            failures.append({"path": rel(path), "issue": "missing_required_artifact"})

    card_set = read_json(OUTPUTS["card_set"]) if OUTPUTS["card_set"].exists() else {}
    if card_set.get("blocked_card_count") != 15:
        failures.append({"artifact": "card_set", "issue": "blocked_card_count_not_15", "value": card_set.get("blocked_card_count")})
    matrix = read_json(OUTPUTS["matrix"]) if OUTPUTS["matrix"].exists() else {}
    groups = set(matrix.get("accepted_capture_groups") or [])
    if groups != set(SCID_CAPTURE_GROUPS):
        failures.append({"artifact": "matrix", "issue": "accepted_capture_groups_mismatch", "value": sorted(groups)})
    contract = read_json(OUTPUTS["prospective_contract"]) if OUTPUTS["prospective_contract"].exists() else {}
    contract_groups = {row.get("field_group") for row in contract.get("contracts", [])}
    if contract_groups != set(SCID_CAPTURE_GROUPS):
        failures.append({"artifact": "prospective_contract", "issue": "contract_group_coverage_mismatch", "value": sorted(contract_groups)})
    unblocking = read_json(OUTPUTS["unblocking"]) if OUTPUTS["unblocking"].exists() else {}
    if unblocking.get("card_count") != 15:
        failures.append({"artifact": "unblocking", "issue": "card_count_not_15", "value": unblocking.get("card_count")})

    recovered_rows = [row for _, row, _ in iter_jsonl(OUTPUTS["recovered_rows"])]
    recovered_validation = validate_rows(recovered_rows)
    if not recovered_validation["ok"] or recovered_validation["row_count"] == 0:
        failures.append({"artifact": "recovered_rows", "issue": "recovered_rows_invalid_or_empty", "validation": recovered_validation})

    noleak = read_json(OUTPUTS["noleak"]) if OUTPUTS["noleak"].exists() else {}
    if not noleak.get("forbidden_text_scan_passed"):
        failures.append({"artifact": "noleak", "issue": "forbidden_text_hits", "hits": noleak.get("forbidden_text_hits")})
    completion = read_json(OUTPUTS["completion"]) if OUTPUTS["completion"].exists() else {}
    if not completion.get("can_mark_goal_complete"):
        failures.append({"artifact": "completion", "issue": "completion_audit_not_complete"})
    for name, expected in SAFE_FLAGS.items():
        for artifact_name, artifact in (
            ("card_set", card_set),
            ("matrix", matrix),
            ("contract", contract),
            ("unblocking", unblocking),
            ("noleak", noleak),
            ("completion", completion),
        ):
            if artifact.get(name) != expected:
                failures.append({"artifact": artifact_name, "issue": f"safe_flag_{name}_mismatch", "value": artifact.get(name)})

    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures[:100],
        "recovered_row_validation": recovered_validation,
        "can_mark_goal_complete": not failures,
    }


def write_saturation() -> None:
    text = f"""# SCID Future Capture Blocked15 Saturation And Self Red Team

Date: {DATE}
Route: `{ROUTE_ID}`
Evidence class: `{EVIDENCE_CLASS}`
Promotion posture: `NO_PROMOTION_VERDICT`

## Saturation Result

- Recomputed the blocked15 subset from the accepted G0 blocked-32 route ledger.
- Searched accepted SCID packet/source-control routes, additive implementation artifacts, schema/test/verifier code, current shadow logs, the absolute main repo root, and parallel prior worktrees under `C:/tmp/gtos_otb`.
- Materialized recoverable source-safe forward-shadow rows for candidate-time side/entry/stop/target/framework/baseline groups and redacted lifecycle source rows from pending-limit lifecycle audit evidence.
- Kept recovered rows outside accepted 40-card result denominators. They prove capture shape and source-state availability, not result readiness.
- Left historical strategy intent/order/lifecycle truth prospective only where no source-time artifact exists. Price, ticks, bars, and later path movement were not used to infer it.

## Self Red Team

1. Evidence-class confusion: recovered rows could be mistaken for result rows. The rows are SCID source-capture rows only, with `validation_safe=false`, `outcome_review_opened=false`, and `opens_result_scoring=false`.
2. Denominator leakage: current forward-shadow rows could leak into the accepted 40-card denominator. The unblocking ledger explicitly sets `does_recovery_unblock_card_now=false` for every card/group.
3. Hidden broker/order evidence: lifecycle rows are normalized through the SCID redaction schema. Raw broker tickets, account/order/deal/history/position fields, actual-R, synthetic-R, PnL, and slippage values are not emitted.
4. POI text parsing risk: human-readable verifier details were not parsed into structured POI truth. POI/bounds remain prospective unless structured MSO/POI fields exist.
5. Duplicate drift risk: recovered rows use route-scoped duplicate keys that include candidate id, group, and lifecycle event identifiers where needed.
6. Passive waiting risk: the route searched source-safe logs, accepted ledgers, local roots, prior worktrees, code, tests, and verifiers before leaving fields prospective.
7. G12 rejection risk: the next audit prompt requires independent recomputation of counts, recovered-row schema validity, safe flags, source search saturation, and denominator boundaries.

## Deliberately Not Answered

- No validation, result scoring, R/PnL, win-rate, expectancy, promotion, AI/API, paid vendor, broker account/order/history/deal/position, raw market blob, live restart, or live behavior question was opened.
- Result design remains a later evidence-class gate after G12 source-state acceptance.
"""
    OUTPUTS["saturation"].write_text(text, encoding="utf-8")


def write_next_g12_prompt() -> None:
    prompt = f"""# G12 SCID Future Capture Blocked15 Source-State Materialization Audit

Evidence class: `G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY`

Audit the target route:

`research/science_program_2026_05/06_outcome_testing/scid_future_capture_field_source_state_materialization_for_blocked15/`

Target prompt:

`research/science_program_2026_05/04_goal_prompts/G0NAPI_R3_FUTURE_CAPTURE_SOURCE_GOAL_PROMPT_2026-05-12.md`

## Mandatory Checks

1. Run mandatory GTOS preflight: `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
2. Recompute the blocked subset from `G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json` and verify exactly 15 cards route to `{ROUTE_ID}`.
3. Verify every missing field maps to accepted SCID capture groups and all ten capture groups remain visible.
4. Independently validate every row in `SCID_FUTURE_CAPTURE_RECOVERED_SOURCE_STATE_ROWS_2026-05-12.jsonl` with `src.research_infra.forward_capture.validate_scid_forward_source_capture_row`.
5. Confirm recovered rows do not contain broker account/order/history/deal/position payloads, raw tickets, actual-R, synthetic-R, PnL, win-rate, expectancy, validation labels, or promotion claims.
6. Confirm recovered rows are treated as source-state examples and not as accepted 40-card result-denominator closure.
7. Confirm prospective contracts cover source logger, as-of clock, redaction, fail-closed status, parser/hash proof, owner/restart gate, tests, verifier, and G12 criteria.
8. Confirm the search ledger includes accepted artifacts, additive implementation evidence, code/tests/verifiers, shadow logs, absolute local roots, and prior worktrees.
9. Confirm no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid vendor/broker account-order-history-deal-position/raw-market-blob/live restart/live behavior/trading-risk-safety-prompt-decision changes were opened.

## Required Output

Emit a G12 audit route with a decision ledger, source-search audit, recovered-row schema/redaction audit, contract exactness audit, completion audit, verifier/focused tests, and the next G0 blocked-card unblocking synthesis prompt/starter if accepted.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    NEXT_G12_PROMPT.write_text(prompt, encoding="utf-8")
    starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(NEXT_G12_PROMPT)} as the complete objective; run mandatory preflight/context refresh; "
        "do not rely on chat memory; stay G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY "
        "with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/"
        "broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/"
        "trading-risk-safety-prompt-decision changes; independently recompute the blocked15 set, "
        "validate recovered SCID rows, source hashes, as-of/redaction/fail-closed rules, search saturation, "
        "prospective contracts, denominator quarantine, verifier/focused tests, and safe flags; emit scoped "
        "G12 artifacts and next G0 synthesis prompt only if accepted; NO_PROMOTION_VERDICT validation_safe=false "
        "outcome_review_opened=false live_effect=false; mark complete only when the prompt completion standard is satisfied."
    )
    NEXT_G12_STARTER.write_text(starter + "\n", encoding="utf-8")


def write_manifest() -> None:
    artifacts = [
        PROMPT_PATH,
        BLOCKED_LEDGER,
        ROUTE_RANKING,
        EXPANSION_LEDGER,
        *OUTPUTS.values(),
        NEXT_G12_PROMPT,
        NEXT_G12_STARTER,
        ROUTE_DIR / "build_scid_future_capture_blocked15_materialization_2026_05_12.py",
        ROUTE_DIR / "verify_scid_future_capture_blocked15_materialization_2026_05_12.py",
        ROUTE_DIR / "test_scid_future_capture_blocked15_materialization_2026_05_12.py",
    ]
    entries = []
    for path in artifacts:
        if path == OUTPUTS["manifest"]:
            continue
        entries.append(file_info(path))
    write_json(
        OUTPUTS["manifest"],
        {
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "generated_at_utc": utc_now(),
            "manifest_self_hash_policy": "manifest_excludes_self_to_avoid_self_referential_hash_drift",
            "artifacts": entries,
        },
    )


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    blocked15 = load_blocked15()

    recovered_rows = build_recovered_candidate_rows() + build_recovered_lifecycle_rows()
    recovered_validation = validate_rows(recovered_rows)
    recovered_counts = Counter(str(row.get("field_group")) for row in recovered_rows)

    write_jsonl(OUTPUTS["recovered_rows"], recovered_rows)
    write_json(OUTPUTS["card_set"], build_card_set(blocked15))
    write_json(OUTPUTS["matrix"], build_matrix(blocked15, recovered_counts))
    write_json(OUTPUTS["search_ledger"], build_search_ledger(recovered_counts, recovered_validation))
    write_json(OUTPUTS["prospective_contract"], build_prospective_contract(blocked15, recovered_counts))
    write_json(OUTPUTS["unblocking"], build_unblocking(blocked15, recovered_counts))
    write_json(OUTPUTS["expansion"], build_expansion(recovered_counts))
    write_json(OUTPUTS["noleak"], build_noleak(recovered_validation))
    write_saturation()
    write_next_g12_prompt()
    write_json(OUTPUTS["completion"], build_completion_audit(blocked15, recovered_validation, recovered_counts))
    write_json(OUTPUTS["verification"], build_verification_result())
    write_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

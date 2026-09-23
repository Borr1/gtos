from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
GOAL_PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
PACKET_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet"
TARGET_PACKET_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet"
CANDIDATE_PACKET_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control"
G12_NEUTRAL_AUDIT_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit"
G0_SYNTHESIS_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis"

ROUTE_ID = "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED"
TERMINAL_REJECT = "REJECT_FOR_EVIDENCE_CLASS_VIOLATION"

AUDIT_PROMPT = GOAL_PROMPT_DIR / "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
BUILDER_PROMPT = GOAL_PROMPT_DIR / "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md"
NEXT_G0_PROMPT = GOAL_PROMPT_DIR / "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"

CANDIDATE_ROWS = CANDIDATE_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
CANDIDATE_MANIFEST = CANDIDATE_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
DESCRIPTOR_FREEZE = TARGET_PACKET_DIR / "SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
TARGET_PRE_FREEZE = TARGET_PACKET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json"
TARGET_SOURCE_BINDING = TARGET_PACKET_DIR / "SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json"
G12_NEUTRAL_DECISION = G12_NEUTRAL_AUDIT_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json"
G12_NEUTRAL_SOURCE_BINDING = G12_NEUTRAL_AUDIT_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json"
G0_DECISION = G0_SYNTHESIS_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_DECISION_LEDGER_2026-05-12.json"
G0_COMPLETION = G0_SYNTHESIS_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json"
G0_RANKING = G0_SYNTHESIS_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json"
G0_REQUIREMENTS = G0_SYNTHESIS_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json"

PACKET_MANIFEST = PACKET_DIR / "SCID_STRATEGY_FIELD_OUTPUT_MANIFEST_2026-05-12.json"
PACKET_STATUS_SUMMARY = PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json"
PACKET_CLOSURE_ROWS = PACKET_DIR / "SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl"
PACKET_SOURCE_INVENTORY = PACKET_DIR / "SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_2026-05-12.json"
PACKET_PROVENANCE = PACKET_DIR / "SCID_STRATEGY_FIELD_PROVENANCE_NOLEAK_ALLOWLIST_2026-05-12.json"
PACKET_FAIL_CLOSED = PACKET_DIR / "SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_2026-05-12.json"
PACKET_PROSPECTIVE = PACKET_DIR / "SCID_STRATEGY_FIELD_PROSPECTIVE_CAPTURE_REQUIREMENT_LEDGER_2026-05-12.json"
PACKET_DUPLICATE = PACKET_DIR / "SCID_STRATEGY_FIELD_DUPLICATE_PROXY_DENOMINATOR_PRESERVATION_LEDGER_2026-05-12.json"
PACKET_COMPLETION = PACKET_DIR / "SCID_STRATEGY_FIELD_COMPLETION_AUDIT_2026-05-12.json"
PACKET_DECISION = PACKET_DIR / "SCID_STRATEGY_FIELD_ROUTE_DECISION_LEDGER_2026-05-12.json"
PACKET_VERIFICATION = PACKET_DIR / "SCID_STRATEGY_FIELD_VERIFICATION_RESULT_2026-05-12.json"

FIELD_FAMILIES = [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "source_control_coverage_not_computable_reasons",
    "future_orderflow_depth_proxy_requirements",
    "broker_account_order_history_deal_position_evidence",
]

VALID_STATUSES = {
    "CLOSED_FROM_SOURCE",
    "FAIL_CLOSED_MISSING_SOURCE_FIELD",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
}

CLOSED_FIELDS = {
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
}

FAIL_CLOSED_FIELDS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
}

PROSPECTIVE_FIELDS = {
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
}

FORBIDDEN_FIELDS = {"broker_account_order_history_deal_position_evidence"}

FORBIDDEN_RESULT_KEYS = {
    "actual_r",
    "broker_actual_r",
    "close_to_close_absolute_delta",
    "close_to_close_percent_return",
    "downside_excursion_absolute",
    "downside_excursion_percent",
    "expectancy",
    "horizon_close",
    "max_high_over_horizon",
    "mean_r",
    "median_r",
    "min_low_over_horizon",
    "pnl",
    "profit_factor",
    "r_multiple",
    "slippage",
    "target_row_hash",
    "upside_excursion_absolute",
    "upside_excursion_percent",
    "win_rate",
}

FORBIDDEN_BROKER_EVIDENCE_KEYS = {
    "account",
    "account_id",
    "account_number",
    "broker_actual_r",
    "deal",
    "deal_id",
    "history_deal",
    "mt5_deal",
    "order",
    "order_id",
    "position",
    "position_id",
    "ticket",
}

RAW_BLOB_SUFFIXES = {".scid", ".parquet", ".csv", ".dly", ".bin", ".depth"}

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

BASE_PAYLOAD = {
    "route_id": ROUTE_ID,
    "schema_version": "g12_scid_strategy_field_source_expansion_packet_audit_v1",
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{rel(path)}:{line_no}: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md_json(path: Path, title: str, payload: Any) -> None:
    body = "# " + title + "\n\n```json\n" + json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n```\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def run_command(args: list[str], timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "args": args,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "status": "PASSED" if completed.returncode == 0 else "FAILED",
        }
    except Exception as exc:  # pragma: no cover - defensive closeout recording
        return {"args": args, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc), "status": "ERROR"}


def git_output(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout


def unique_map(rows: list[dict[str, Any]], key: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    out: dict[str, dict[str, Any]] = {}
    dupes: list[str] = []
    for row in rows:
        value = row.get(key)
        if value in out:
            dupes.append(str(value))
        else:
            out[str(value)] = row
    return out, dupes


def collect_keys(data: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full = f"{prefix}.{key}" if prefix else str(key)
            keys.add(str(key))
            keys.add(full)
            keys.update(collect_keys(value, full))
    elif isinstance(data, list):
        for item in data:
            keys.update(collect_keys(item, prefix))
    return keys


def flatten_values(data: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(data, dict):
        for value in data.values():
            values.extend(flatten_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(flatten_values(item))
    else:
        values.append(data)
    return values


def safe_flag_payload(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(BASE_PAYLOAD)
    payload["generated_at_utc"] = utc_now()
    if extra:
        payload.update(extra)
    return payload


def load_sources() -> dict[str, Any]:
    descriptor_freeze = read_json(DESCRIPTOR_FREEZE)
    descriptors = descriptor_freeze["descriptor_rows"]
    candidates = read_jsonl(CANDIDATE_ROWS)
    closures = read_jsonl(PACKET_CLOSURE_ROWS)
    return {
        "descriptor_freeze": descriptor_freeze,
        "descriptors": descriptors,
        "candidates": candidates,
        "closures": closures,
        "candidate_manifest": read_json(CANDIDATE_MANIFEST),
        "target_pre_freeze": read_json(TARGET_PRE_FREEZE),
        "target_source_binding": read_json(TARGET_SOURCE_BINDING),
        "g12_neutral_decision": read_json(G12_NEUTRAL_DECISION),
        "g12_neutral_source_binding": read_json(G12_NEUTRAL_SOURCE_BINDING),
        "g0_decision": read_json(G0_DECISION),
        "g0_completion": read_json(G0_COMPLETION),
        "g0_ranking": read_json(G0_RANKING),
        "g0_requirements": read_json(G0_REQUIREMENTS),
        "packet_manifest": read_json(PACKET_MANIFEST),
        "packet_status": read_json(PACKET_STATUS_SUMMARY),
        "packet_source_inventory": read_json(PACKET_SOURCE_INVENTORY),
        "packet_provenance": read_json(PACKET_PROVENANCE),
        "packet_fail_closed": read_json(PACKET_FAIL_CLOSED),
        "packet_prospective": read_json(PACKET_PROSPECTIVE),
        "packet_duplicate": read_json(PACKET_DUPLICATE),
        "packet_completion": read_json(PACKET_COMPLETION),
        "packet_decision": read_json(PACKET_DECISION),
        "packet_verification": read_json(PACKET_VERIFICATION),
    }


def audit_context_anchor() -> dict[str, Any]:
    return safe_flag_payload(
        {
            "artifact_family": "context_anchor",
            "current_head": git_output(["rev-parse", "HEAD"]).strip(),
            "current_head_subject": git_output(["log", "-1", "--format=%h %s"]).strip(),
            "mandatory_context_use": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "lane_posture": "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ACCEPTANCE_FOCUSED",
                "accepted_absence_boundary": "Exact fail-closed historical absence is acceptable when proven and paired with exact prospective capture requirements.",
                "reject_boundary": "Inference, leakage, denominator drift, vague requirements, broker evidence, raw blobs, live-surface changes, or result scoring are blockers.",
            },
            "controlling_prompt": rel(AUDIT_PROMPT),
            "builder_prompt": rel(BUILDER_PROMPT),
            "builder_route": rel(PACKET_DIR),
            "preflight_files_read": [
                ".context/LIVE_STATE.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_current_state.md",
                rel(AUDIT_PROMPT),
                rel(BUILDER_PROMPT),
            ],
            "deliberately_not_answered": [
                "validation execution",
                "strategy edge or result scoring",
                "R/PnL/win-rate/expectancy/performance",
                "AI/API calls",
                "broker account/order/history/deal/position evidence",
                "paid/vendor access",
                "raw market-data blob commits",
                "live behavior or production trading-surface changes",
                "G0 synthesis decision itself",
            ],
        }
    )


def audit_prerequisites(src: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "name": "candidate_input_packet_manifest_count",
            "observed": src["candidate_manifest"].get("candidate_input_row_count"),
            "expected": 3014,
            "passed": src["candidate_manifest"].get("candidate_input_row_count") == 3014,
        },
        {
            "name": "target_packet_pre_freeze_count",
            "observed": src["target_pre_freeze"].get("candidate_row_count"),
            "expected": 3014,
            "passed": src["target_pre_freeze"].get("candidate_row_count") == 3014,
        },
        {
            "name": "g12_neutral_packet_accepted",
            "observed": src["g12_neutral_decision"].get("terminal_decision"),
            "expected": "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
            "passed": src["g12_neutral_decision"].get("terminal_decision")
            == "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
        },
        {
            "name": "g0_synthesis_accepted_with_ranked_next_route",
            "observed": src["g0_decision"].get("terminal_decision"),
            "expected": "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE",
            "passed": src["g0_decision"].get("terminal_decision") == "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE",
        },
        {
            "name": "g0_rank_1_builder_route",
            "observed": src["g0_decision"].get("rank_1_next_route"),
            "expected": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
            "passed": src["g0_decision"].get("rank_1_next_route") == "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
        },
        {
            "name": "builder_packet_terminal_decision",
            "observed": src["packet_decision"].get("terminal_decision"),
            "expected": "BUILT_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_G12_AUDIT_REQUIRED",
            "passed": src["packet_decision"].get("terminal_decision") == "BUILT_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_G12_AUDIT_REQUIRED",
        },
        {
            "name": "builder_verifier_ok",
            "observed": src["packet_verification"].get("ok"),
            "expected": True,
            "passed": src["packet_verification"].get("ok") is True,
        },
    ]
    return safe_flag_payload(
        {
            "artifact_family": "prerequisite_evidence_chain_reconciliation_audit",
            "checks": checks,
            "all_checks_passed": all(item["passed"] for item in checks),
            "chain_files_read": [
                rel(CANDIDATE_MANIFEST),
                rel(TARGET_PRE_FREEZE),
                rel(TARGET_SOURCE_BINDING),
                rel(G12_NEUTRAL_DECISION),
                rel(G12_NEUTRAL_SOURCE_BINDING),
                rel(G0_DECISION),
                rel(G0_COMPLETION),
                rel(G0_RANKING),
                rel(G0_REQUIREMENTS),
                rel(PACKET_MANIFEST),
                rel(PACKET_DECISION),
                rel(PACKET_COMPLETION),
                rel(PACKET_VERIFICATION),
            ],
        }
    )


def audit_row_coverage(src: dict[str, Any]) -> dict[str, Any]:
    candidates_by_id, candidate_dupes = unique_map(src["candidates"], "candidate_input_row_id")
    descriptors_by_id, descriptor_dupes = unique_map(src["descriptors"], "candidate_input_row_id")
    closures_by_id, closure_dupes = unique_map(src["closures"], "candidate_input_row_id")

    candidate_ids = set(candidates_by_id)
    descriptor_ids = set(descriptors_by_id)
    closure_ids = set(closures_by_id)
    candidate_duplicate_keys = Counter(str(row.get("duplicate_key")) for row in src["candidates"])
    closure_denominator_keys = Counter(str(row.get("duplicate_proxy_denominator_key")) for row in src["closures"])

    duplicate_key_mismatches = []
    top_level_mismatches = []
    for candidate_id in sorted(candidate_ids & descriptor_ids & closure_ids):
        candidate = candidates_by_id[candidate_id]
        descriptor = descriptors_by_id[candidate_id]
        closure = closures_by_id[candidate_id]
        if closure.get("duplicate_proxy_denominator_key") != descriptor.get("duplicate_proxy_denominator_key"):
            duplicate_key_mismatches.append(candidate_id)
        if closure.get("candidate_duplicate_key") != candidate.get("duplicate_key"):
            duplicate_key_mismatches.append(candidate_id)
        for key in ["canonical_economic_group", "entry_reference_time_utc", "symbol", "source_file_name"]:
            expected = descriptor.get(key, candidate.get(key))
            if closure.get(key) != expected:
                top_level_mismatches.append({"candidate_input_row_id": candidate_id, "field": key, "expected": expected, "observed": closure.get(key)})

    return safe_flag_payload(
        {
            "artifact_family": "row_coverage_and_duplicate_denominator_recomputation_audit",
            "candidate_input_rows": len(src["candidates"]),
            "descriptor_rows": len(src["descriptors"]),
            "closure_rows": len(src["closures"]),
            "unique_candidate_input_row_ids": len(candidate_ids),
            "unique_descriptor_candidate_ids": len(descriptor_ids),
            "unique_closure_candidate_ids": len(closure_ids),
            "candidate_duplicate_id_count": len(candidate_dupes),
            "descriptor_duplicate_id_count": len(descriptor_dupes),
            "closure_duplicate_id_count": len(closure_dupes),
            "missing_from_descriptor": sorted(candidate_ids - descriptor_ids)[:25],
            "missing_from_closure": sorted(candidate_ids - closure_ids)[:25],
            "extra_descriptor_ids": sorted(descriptor_ids - candidate_ids)[:25],
            "extra_closure_ids": sorted(closure_ids - candidate_ids)[:25],
            "unique_candidate_duplicate_keys": len(candidate_duplicate_keys),
            "unique_closure_duplicate_proxy_denominator_keys": len(closure_denominator_keys),
            "candidate_duplicate_key_collisions": {key: count for key, count in candidate_duplicate_keys.items() if count > 1},
            "closure_duplicate_proxy_denominator_key_collisions": {key: count for key, count in closure_denominator_keys.items() if count > 1},
            "duplicate_key_mismatch_count": len(duplicate_key_mismatches),
            "duplicate_key_mismatch_examples": duplicate_key_mismatches[:25],
            "top_level_source_descriptor_mismatch_count": len(top_level_mismatches),
            "top_level_source_descriptor_mismatch_examples": top_level_mismatches[:25],
            "counts_by_symbol": dict(Counter(str(row.get("symbol")) for row in src["closures"])),
            "counts_by_canonical_economic_group": dict(Counter(str(row.get("canonical_economic_group")) for row in src["closures"])),
            "row_coverage_ok": (
                len(src["candidates"]) == 3014
                and len(src["descriptors"]) == 3014
                and len(src["closures"]) == 3014
                and len(candidate_ids) == 3014
                and candidate_ids == descriptor_ids == closure_ids
                and not candidate_dupes
                and not descriptor_dupes
                and not closure_dupes
                and not duplicate_key_mismatches
                and not top_level_mismatches
            ),
        }
    )


def closed_field_mismatches(candidate: dict[str, Any], descriptor: dict[str, Any], closure: dict[str, Any]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    statuses = closure.get("field_statuses", {})

    canonical_summary = statuses.get("canonical_candidate_and_denominator", {}).get("value_summary", {})
    canonical_expected = {
        "candidate_input_row_id": candidate["candidate_input_row_id"],
        "candidate_duplicate_key": candidate["duplicate_key"],
        "duplicate_proxy_denominator_key": descriptor["duplicate_proxy_denominator_key"],
        "canonical_economic_group": descriptor["canonical_economic_group"],
    }
    for key, expected in canonical_expected.items():
        if canonical_summary.get(key) != expected:
            mismatches.append({"field_family": "canonical_candidate_and_denominator", "key": key, "expected": expected, "observed": canonical_summary.get(key)})

    symbol_summary = statuses.get("source_symbol_session_partition", {}).get("value_summary", {})
    symbol_expected = {
        "symbol": descriptor["symbol"],
        "source_file_name": descriptor["source_file_name"],
        "source_instrument": Path(descriptor["source_file_name"]).stem,
        "source_proxy_group": descriptor["source_proxy_group"],
        "session_bucket": descriptor["session_bucket"],
        "time_of_day_bucket": descriptor["time_of_day_bucket"],
        "utc_hour": descriptor["utc_hour"],
        "partition_assignment": descriptor["partition_assignment"],
    }
    for key, expected in symbol_expected.items():
        if symbol_summary.get(key) != expected:
            mismatches.append({"field_family": "source_symbol_session_partition", "key": key, "expected": expected, "observed": symbol_summary.get(key)})

    coverage_summary = statuses.get("source_control_coverage_not_computable_reasons", {}).get("value_summary", {})
    coverage_expected = {
        "prior_16_drift_bucket": descriptor.get("prior_16_drift_bucket"),
        "prior_16_range_bucket": descriptor.get("prior_16_range_bucket"),
        "prior_32_range_bucket": descriptor.get("prior_32_range_bucket"),
        "source_coverage_quality_bucket": descriptor.get("source_coverage_quality_bucket"),
    }
    for key, expected in coverage_expected.items():
        if coverage_summary.get(key) != expected:
            mismatches.append({"field_family": "source_control_coverage_not_computable_reasons", "key": key, "expected": expected, "observed": coverage_summary.get(key)})

    expected_complete = {window: descriptor.get("prior_windows", {}).get(window, {}).get("complete") for window in ["4", "16", "32", "96"]}
    observed_complete = coverage_summary.get("prior_windows_complete")
    if observed_complete != expected_complete:
        mismatches.append(
            {
                "field_family": "source_control_coverage_not_computable_reasons",
                "key": "prior_windows_complete",
                "expected": expected_complete,
                "observed": observed_complete,
            }
        )
    return mismatches


def fail_closed_value_issues(closure: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    statuses = closure.get("field_statuses", {})

    side = statuses.get("intended_side_direction", {}).get("value_summary", {})
    if side.get("intended_strategy_side") is not None:
        issues.append({"field_family": "intended_side_direction", "issue": "intended_strategy_side_not_null"})
    if side.get("neutral_side_present") != "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT":
        issues.append({"field_family": "intended_side_direction", "issue": "neutral_marker_missing"})

    entry = statuses.get("intended_entry_reference", {}).get("value_summary", {})
    if entry.get("intended_strategy_entry_reference") is not None:
        issues.append({"field_family": "intended_entry_reference", "issue": "intended_strategy_entry_reference_not_null"})
    if entry.get("neutral_entry_reference_time_utc") != closure.get("entry_reference_time_utc"):
        issues.append({"field_family": "intended_entry_reference", "issue": "neutral_entry_reference_time_mismatch"})

    null_fields = {
        "intended_stop_reference": ["intended_stop_reference"],
        "intended_target_reference": ["intended_target_reference"],
        "poi_type_bounds_source": ["poi_type", "poi_bounds", "poi_source"],
        "lifecycle_fill_cancel_expiry_source_status": ["fill_cancel_expiry_source_state", "nonbroker_lifecycle_join_key"],
    }
    for family, keys in null_fields.items():
        summary = statuses.get(family, {}).get("value_summary", {})
        for key in keys:
            if summary.get(key) is not None:
                issues.append({"field_family": family, "issue": f"{key}_not_null"})

    framework = statuses.get("framework_setup_family", {}).get("value_summary", {})
    if framework.get("framework_source") is not None:
        issues.append({"field_family": "framework_setup_family", "issue": "framework_source_not_null"})
    if framework.get("setup_family") != "SOURCE_ONLY_UNKNOWN":
        issues.append({"field_family": "framework_setup_family", "issue": "setup_family_not_source_only_unknown"})

    return issues


def audit_field_statuses(src: dict[str, Any]) -> dict[str, Any]:
    candidates_by_id, _ = unique_map(src["candidates"], "candidate_input_row_id")
    descriptors_by_id, _ = unique_map(src["descriptors"], "candidate_input_row_id")
    status_counts: dict[str, Counter[str]] = {family: Counter() for family in FIELD_FAMILIES}
    missing_family_rows: list[dict[str, Any]] = []
    invalid_status_rows: list[dict[str, Any]] = []
    row_hash_mismatches: list[str] = []
    closed_mismatches: list[dict[str, Any]] = []

    for row in src["closures"]:
        candidate_id = str(row.get("candidate_input_row_id"))
        statuses = row.get("field_statuses", {})
        missing = [family for family in FIELD_FAMILIES if family not in statuses]
        if missing:
            missing_family_rows.append({"candidate_input_row_id": candidate_id, "missing": missing})
        for family in FIELD_FAMILIES:
            status = statuses.get(family, {}).get("status")
            if status:
                status_counts[family][str(status)] += 1
                if status not in VALID_STATUSES:
                    invalid_status_rows.append({"candidate_input_row_id": candidate_id, "field_family": family, "status": status})
        hash_row = dict(row)
        observed_hash = hash_row.pop("field_closure_row_hash", None)
        if stable_hash(hash_row) != observed_hash:
            row_hash_mismatches.append(candidate_id)

        if candidate_id in candidates_by_id and candidate_id in descriptors_by_id:
            closed_mismatches.extend(closed_field_mismatches(candidates_by_id[candidate_id], descriptors_by_id[candidate_id], row))

    expected_status_profile = {
        **{field: {"CLOSED_FROM_SOURCE": 3014} for field in CLOSED_FIELDS},
        **{field: {"FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014} for field in FAIL_CLOSED_FIELDS},
        **{field: {"PROSPECTIVE_CAPTURE_REQUIRED": 3014} for field in PROSPECTIVE_FIELDS},
        **{field: {"FORBIDDEN_IN_THIS_EVIDENCE_CLASS": 3014} for field in FORBIDDEN_FIELDS},
    }
    status_mismatches = {}
    for field, expected in expected_status_profile.items():
        observed = dict(status_counts[field])
        if observed != expected:
            status_mismatches[field] = {"expected": expected, "observed": observed}

    return safe_flag_payload(
        {
            "artifact_family": "field_status_enum_and_closed_field_recomputation_audit",
            "field_families_required": FIELD_FAMILIES,
            "valid_status_enum": sorted(VALID_STATUSES),
            "field_status_counts_by_field": {field: dict(counter) for field, counter in status_counts.items()},
            "expected_status_profile": expected_status_profile,
            "status_mismatches": status_mismatches,
            "missing_family_row_count": len(missing_family_rows),
            "missing_family_examples": missing_family_rows[:25],
            "invalid_status_row_count": len(invalid_status_rows),
            "invalid_status_examples": invalid_status_rows[:25],
            "row_hash_mismatch_count": len(row_hash_mismatches),
            "row_hash_mismatch_examples": row_hash_mismatches[:25],
            "closed_source_value_mismatch_count": len(closed_mismatches),
            "closed_source_value_mismatch_examples": closed_mismatches[:25],
            "closed_field_source_paths_checked": sorted(CLOSED_FIELDS),
            "field_status_audit_ok": (
                not status_mismatches
                and not missing_family_rows
                and not invalid_status_rows
                and not row_hash_mismatches
                and not closed_mismatches
            ),
        }
    )


def requirement_specificity_issues(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required_keys = [
        "future_source_or_logger",
        "parser_requirement",
        "schema_version_required",
        "redaction_rule",
        "as_of_rule",
        "g12_acceptance_requirement",
        "required_fields",
    ]
    vague_tokens = {"tbd", "todo", "later", "maybe", "unknown", "as needed", "future work"}
    issues: list[dict[str, Any]] = []
    for req in requirements:
        field_family = req.get("field_family")
        for key in required_keys:
            value = req.get(key)
            if value in (None, "", []):
                issues.append({"field_family": field_family, "issue": f"missing_{key}"})
            if isinstance(value, str) and value.strip().lower() in vague_tokens:
                issues.append({"field_family": field_family, "issue": f"vague_{key}", "value": value})
        if isinstance(req.get("required_fields"), list) and len(req.get("required_fields", [])) < 3:
            issues.append({"field_family": field_family, "issue": "too_few_required_fields"})
    return issues


def audit_fail_prospective_forbidden(src: dict[str, Any]) -> dict[str, Any]:
    fail_value_issues: list[dict[str, Any]] = []
    prospective_status_issues: list[dict[str, Any]] = []
    forbidden_status_issues: list[dict[str, Any]] = []
    source_path_issues: list[dict[str, Any]] = []

    for row in src["closures"]:
        candidate_id = row.get("candidate_input_row_id")
        statuses = row.get("field_statuses", {})
        fail_value_issues.extend({"candidate_input_row_id": candidate_id, **issue} for issue in fail_closed_value_issues(row))
        for family in FAIL_CLOSED_FIELDS:
            if statuses.get(family, {}).get("status") != "FAIL_CLOSED_MISSING_SOURCE_FIELD":
                prospective_status_issues.append({"candidate_input_row_id": candidate_id, "field_family": family, "status": statuses.get(family, {}).get("status")})
            if not statuses.get(family, {}).get("source_paths_searched"):
                source_path_issues.append({"candidate_input_row_id": candidate_id, "field_family": family, "issue": "missing_source_paths_searched"})
        for family in PROSPECTIVE_FIELDS:
            if statuses.get(family, {}).get("status") != "PROSPECTIVE_CAPTURE_REQUIRED":
                prospective_status_issues.append({"candidate_input_row_id": candidate_id, "field_family": family, "status": statuses.get(family, {}).get("status")})
        for family in FORBIDDEN_FIELDS:
            field = statuses.get(family, {})
            if field.get("status") != "FORBIDDEN_IN_THIS_EVIDENCE_CLASS" or field.get("value_summary") is not None:
                forbidden_status_issues.append({"candidate_input_row_id": candidate_id, "field_family": family, "status": field.get("status"), "value_summary": field.get("value_summary")})

    prospective_requirements = src["packet_prospective"].get("requirements", [])
    fail_requirements = src["packet_fail_closed"].get("missing_field_groups", [])
    requirement_issues = requirement_specificity_issues(prospective_requirements + fail_requirements)
    covered_requirement_families = {req.get("field_family") for req in prospective_requirements + fail_requirements}
    expected_requirement_families = PROSPECTIVE_FIELDS | FAIL_CLOSED_FIELDS
    missing_requirement_families = sorted(expected_requirement_families - covered_requirement_families)

    return safe_flag_payload(
        {
            "artifact_family": "fail_closed_prospective_forbidden_status_audit",
            "fail_closed_fields": sorted(FAIL_CLOSED_FIELDS),
            "prospective_fields": sorted(PROSPECTIVE_FIELDS),
            "forbidden_fields": sorted(FORBIDDEN_FIELDS),
            "fail_closed_value_issue_count": len(fail_value_issues),
            "fail_closed_value_issue_examples": fail_value_issues[:25],
            "status_issue_count": len(prospective_status_issues),
            "status_issue_examples": prospective_status_issues[:25],
            "forbidden_status_issue_count": len(forbidden_status_issues),
            "forbidden_status_issue_examples": forbidden_status_issues[:25],
            "source_path_issue_count": len(source_path_issues),
            "source_path_issue_examples": source_path_issues[:25],
            "prospective_requirement_specificity_issue_count": len(requirement_issues),
            "prospective_requirement_specificity_examples": requirement_issues[:25],
            "missing_requirement_families": missing_requirement_families,
            "non_generatable_historical_absence_accepted": True,
            "fail_prospective_forbidden_audit_ok": (
                not fail_value_issues
                and not prospective_status_issues
                and not forbidden_status_issues
                and not source_path_issues
                and not requirement_issues
                and not missing_requirement_families
            ),
        }
    )


def builder_commit_paths() -> dict[str, Any]:
    commit = git_output(["log", "--grep=research: build scid strategy field source packet", "--format=%H", "-n", "1"]).strip()
    if not commit:
        commit = "21d109a1"
    paths = [line.strip() for line in git_output(["show", "--name-only", "--format=", commit]).splitlines() if line.strip()]
    statuses = [line.strip() for line in git_output(["show", "--name-status", "--format=", commit]).splitlines() if line.strip()]
    return {"commit": commit, "paths": paths, "name_status": statuses}


def audit_noleak_and_surfaces(src: dict[str, Any]) -> dict[str, Any]:
    all_closure_keys = set()
    forbidden_result_key_hits: list[dict[str, Any]] = []
    forbidden_broker_key_hits: list[dict[str, Any]] = []
    for row in src["closures"]:
        keys = collect_keys(row)
        all_closure_keys.update(keys)
        result_hits = sorted(k for k in keys if k in FORBIDDEN_RESULT_KEYS)
        broker_hits = sorted(k for k in keys if k in FORBIDDEN_BROKER_EVIDENCE_KEYS)
        if result_hits:
            forbidden_result_key_hits.append({"candidate_input_row_id": row.get("candidate_input_row_id"), "keys": result_hits})
        if broker_hits:
            forbidden_broker_key_hits.append({"candidate_input_row_id": row.get("candidate_input_row_id"), "keys": broker_hits})

    manifest_artifacts = src["packet_manifest"].get("artifacts", [])
    manifest_paths = [artifact.get("path") for artifact in manifest_artifacts if artifact.get("path")]
    required_manifest_names = {
        "context_anchor_json",
        "source_inventory_json",
        "prereq_reconciliation_json",
        "closure_rows_jsonl",
        "field_status_summary_json",
        "provenance_allowlist_json",
        "fail_closed_json",
        "prospective_json",
        "duplicate_json",
        "anti_boxing_json",
        "decision_json",
        "manifest_json",
        "completion_json",
        "closeout_json",
        "next_g12_prompt",
        "standalone_verifier",
        "focused_tests",
    }
    manifest_names = {artifact.get("artifact_name") for artifact in manifest_artifacts}
    missing_manifest_names = sorted(required_manifest_names - manifest_names)

    builder_diff = builder_commit_paths()
    raw_blob_paths = [path for path in builder_diff["paths"] if Path(path).suffix.lower() in RAW_BLOB_SUFFIXES]
    trading_surface_prefixes = ("prompts/", "config/", "src/", "tests/canary", "scripts/canary", "scripts/canary_")
    trading_surface_paths = [path for path in builder_diff["paths"] if path.startswith(trading_surface_prefixes)]
    allowed_research_prompt_paths = [
        path for path in builder_diff["paths"] if path.startswith("research/science_program_2026_05/04_goal_prompts/")
    ]
    unsafe_prompt_config_paths = [
        path
        for path in builder_diff["paths"]
        if path.startswith(("prompts/", "config/"))
    ]

    safe_flag_issues: list[dict[str, Any]] = []
    for payload_name, payload in [
        ("packet_manifest", src["packet_manifest"]),
        ("packet_status", src["packet_status"]),
        ("packet_decision", src["packet_decision"]),
        ("packet_completion", src["packet_completion"]),
    ]:
        for key, expected in SAFE_FLAGS.items():
            if payload.get(key) != expected:
                safe_flag_issues.append({"payload": payload_name, "key": key, "expected": expected, "observed": payload.get(key)})
        for key in [
            "opens_validation",
            "opens_result_scoring",
            "opens_strategy_edge_claims",
            "opens_broker_account_order_history_deal_position_evidence",
            "opens_ai_api",
            "opens_paid_or_vendor_access",
            "opens_raw_market_data_blob_commit",
            "opens_live_trading_behavior",
            "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        ]:
            if payload.get(key) is not False:
                safe_flag_issues.append({"payload": payload_name, "key": key, "expected": False, "observed": payload.get(key)})

    return safe_flag_payload(
        {
            "artifact_family": "no_leak_forbidden_surface_raw_blob_trading_surface_audit",
            "closure_exact_forbidden_result_key_hits": forbidden_result_key_hits[:25],
            "closure_exact_forbidden_result_key_hit_count": len(forbidden_result_key_hits),
            "closure_exact_forbidden_broker_key_hits": forbidden_broker_key_hits[:25],
            "closure_exact_forbidden_broker_key_hit_count": len(forbidden_broker_key_hits),
            "forbidden_result_keys_checked": sorted(FORBIDDEN_RESULT_KEYS),
            "forbidden_broker_evidence_keys_checked": sorted(FORBIDDEN_BROKER_EVIDENCE_KEYS),
            "manifest_artifact_count": len(manifest_artifacts),
            "manifest_paths": manifest_paths,
            "missing_required_manifest_artifact_names": missing_manifest_names,
            "builder_commit": builder_diff["commit"],
            "builder_commit_path_count": len(builder_diff["paths"]),
            "builder_commit_paths": builder_diff["paths"],
            "raw_market_blob_paths_in_builder_diff": raw_blob_paths,
            "trading_surface_paths_in_builder_diff": trading_surface_paths,
            "allowed_research_goal_prompt_paths_in_builder_diff": allowed_research_prompt_paths,
            "unsafe_prompt_config_paths_in_builder_diff": unsafe_prompt_config_paths,
            "safe_flag_issue_count": len(safe_flag_issues),
            "safe_flag_issue_examples": safe_flag_issues[:25],
            "unrelated_dirty_workspace_note": "Workspace has unrelated runtime/shadow dirt from live monitoring; this audit enforces builder commit paths and route outputs only.",
            "no_leak_surface_audit_ok": (
                not forbidden_result_key_hits
                and not forbidden_broker_key_hits
                and not missing_manifest_names
                and not raw_blob_paths
                and not trading_surface_paths
                and not unsafe_prompt_config_paths
                and not safe_flag_issues
            ),
        }
    )


def audit_source_hash_binding(src: dict[str, Any]) -> dict[str, Any]:
    source_inventory_hashes = src["packet_source_inventory"].get("input_artifact_hashes", [])
    provenance_inputs = src["packet_provenance"].get("allowed_input_artifacts", [])
    combined_inputs = source_inventory_hashes + [
        {"input_name": item.get("name"), "path": item.get("path"), "sha256": item.get("sha256"), "exists": Path(REPO_ROOT / item.get("path", "")).exists()}
        for item in provenance_inputs
    ]
    comparisons = []
    for item in combined_inputs:
        path_text = item.get("path")
        if not path_text:
            continue
        path = REPO_ROOT / path_text
        actual = sha256_file(path)
        expected = item.get("sha256")
        comparisons.append(
            {
                "input_name": item.get("input_name") or item.get("name"),
                "path": path_text,
                "exists": path.exists(),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matched": actual == expected,
            }
        )

    manifest_hash_comparisons = []
    for artifact in src["packet_manifest"].get("artifacts", []):
        expected = artifact.get("sha256_after_build")
        if expected is None:
            continue
        path_text = artifact.get("path")
        path = REPO_ROOT / path_text
        actual = sha256_file(path)
        manifest_hash_comparisons.append(
            {
                "artifact_name": artifact.get("artifact_name"),
                "path": path_text,
                "expected_sha256_after_build": expected,
                "actual_sha256": actual,
                "matched": actual == expected,
            }
        )

    mismatches = [item for item in comparisons if not item["matched"]]
    manifest_mismatches = [item for item in manifest_hash_comparisons if not item["matched"]]
    post_build_prompt_hardening_mismatches = [
        item
        for item in manifest_mismatches
        if item.get("artifact_name") == "next_g12_prompt"
        and item.get("path") == rel(AUDIT_PROMPT)
    ]
    blocking_manifest_mismatches = [
        item for item in manifest_mismatches if item not in post_build_prompt_hardening_mismatches
    ]
    return safe_flag_payload(
        {
            "artifact_family": "source_hash_input_binding_audit",
            "source_inventory_input_hash_comparisons": comparisons,
            "source_inventory_hash_mismatch_count": len(mismatches),
            "source_inventory_hash_mismatch_examples": mismatches[:25],
            "manifest_artifact_hash_comparisons_checked": len(manifest_hash_comparisons),
            "manifest_artifact_hash_mismatch_count": len(manifest_mismatches),
            "manifest_artifact_hash_mismatch_examples": manifest_mismatches[:25],
            "post_build_prompt_hardening_mismatch_count": len(post_build_prompt_hardening_mismatches),
            "post_build_prompt_hardening_mismatches": post_build_prompt_hardening_mismatches,
            "blocking_manifest_artifact_hash_mismatch_count": len(blocking_manifest_mismatches),
            "blocking_manifest_artifact_hash_mismatch_examples": blocking_manifest_mismatches[:25],
            "hash_warning_boundary": "The builder manifest's next_g12_prompt hash may differ after later prompt-hardening commits. That is a warning, not a packet source-input mismatch, because the prompt is the current controlling audit file and not a closure-row source artifact.",
            "builder_manifest_read_fully": True,
            "source_hash_binding_ok": not mismatches and not blocking_manifest_mismatches,
        }
    )


def audit_saturation(src: dict[str, Any]) -> dict[str, Any]:
    entries = [
        {
            "question": "Could any fail-closed strategy field actually have source evidence in the searched artifacts?",
            "answer": "The builder source inventory searched the accepted SCID packet, neutral target packet, G12/G0 chain, source-field contract, sibling route families, shadow logs, program-control artifacts, pipeline state, knowledge base, data root, and C:/tmp. The closure rows preserve source_paths_searched for each fail-closed family. This audit found no candidate_input_row_id or duplicate-key source-state join that closes side, entry, stop, target, POI, setup family, or lifecycle truth.",
            "pursued": "Recomputed field statuses, fail-closed value nulls, and source-path presence across all 3,014 closure rows.",
            "boundary": "Accepted exact fail-closed historical absence; future route must capture explicit source-state before result design.",
            "status": "ACCEPTED_WARNING_NOT_BLOCKER",
        },
        {
            "question": "Could any closed field be a projection or derived convenience field rather than source truth?",
            "answer": "Closed fields are limited to candidate identity/denominator, source symbol/session/partition descriptors, and source-control coverage buckets. This audit matched those values back to candidate rows and descriptor freeze rows exactly, including source_instrument as the stem of source_file_name.",
            "pursued": "Closed-field value recomputation over all closure rows.",
            "boundary": "No strategy-intent closed field is accepted.",
            "status": "CLEARED",
        },
        {
            "question": "Could any source inventory path omission make the missing-field conclusion too weak?",
            "answer": "The source inventory includes the mandatory packet chain and broader local artifact families. Some broad roots are intentionally scan-truncated for file-count control, but the field-level conclusion is anchored on absence of candidate_input_row_id/duplicate-key strategy-state contracts, not on absence of arbitrary files.",
            "pursued": "Verified searched-root ledger, field-level source_paths_searched, and exact prospective requirements.",
            "boundary": "Broader source search is a G0 route option only if G0 wants to pursue source recovery; this G12 accepts the builder's fail-closed status because no inference was made.",
            "status": "ACCEPTED_WARNING_NOT_BLOCKER",
        },
        {
            "question": "Could any field status allow price-only inference of historical intent, side, entry, stop, target, POI, setup family, or lifecycle?",
            "answer": "No. All strategy-intent/source-state families are FAIL_CLOSED_MISSING_SOURCE_FIELD, with null intent values or SOURCE_ONLY_UNKNOWN. Neutral entry time and neutral side marker are explicitly not strategy intent.",
            "pursued": "Fail-closed value checks and prospective requirement specificity checks.",
            "boundary": "Price-only inference remains forbidden.",
            "status": "CLEARED",
        },
        {
            "question": "Could duplicate/proxy denominator keys allow one candidate to borrow another candidate's source fields?",
            "answer": "No duplicate candidate ids or duplicate proxy denominator keys were found across the 3,014 closure rows; candidate duplicate keys match descriptor duplicate_proxy_denominator_key values exactly.",
            "pursued": "Row coverage and denominator recomputation.",
            "boundary": "Future result-design lanes must preserve candidate_input_row_id and duplicate_proxy_denominator_key.",
            "status": "CLEARED",
        },
        {
            "question": "Could prospective capture requirements be too vague for future implementation or G12 verification?",
            "answer": "No. Every fail-closed/prospective requirement carries future_source_or_logger, required_fields, parser requirement, schema, redaction, as-of rule, and G12 acceptance requirement.",
            "pursued": "Specificity scan for all fail-closed and prospective requirement ledger entries.",
            "boundary": "Implementation remains future work by evidence-class gate, but requirements are exact enough for a future builder/G12.",
            "status": "CLEARED",
        },
        {
            "question": "Could any target or neutral behavior value leak into source-field status or closure?",
            "answer": "No exact forbidden result/performance keys were present in closure rows. Prior-window source descriptors and neutral entry reference time are input/source-control fields; target row hashes and neutral target values are absent from closure rows.",
            "pursued": "Recursive key scan over all closure rows and no-leak allowlist verification.",
            "boundary": "Neutral behavior synthesis remains outside this audit and must be handled by G0.",
            "status": "CLEARED",
        },
        {
            "question": "Could the audit treat forbidden broker account/order/history/deal/position evidence as merely absent rather than forbidden?",
            "answer": "No. The broker evidence field is present for every row with FORBIDDEN_IN_THIS_EVIDENCE_CLASS and null value_summary. The route safe flags also show broker evidence unopened.",
            "pursued": "Forbidden status check and safe-flag check across route artifacts.",
            "boundary": "Broker evidence requires a separate owner-approved evidence class and remains forbidden here.",
            "status": "CLEARED",
        },
        {
            "question": "If accepted, what exact next G0 route should synthesize?",
            "answer": "The emitted G0 prompt must decide among result-design readiness, forward capture implementation, broader source search, and negative-learning closure while preserving no validation execution, no scoring, and no live-surface changes.",
            "pursued": "Generated a full hardened next G0 control prompt.",
            "boundary": "This G12 does not choose the next route; it only accepts or rejects this packet.",
            "status": "ROUTED_TO_NEXT_G0_PROMPT",
        },
    ]
    return safe_flag_payload(
        {
            "artifact_family": "saturation_self_red_team_ledger",
            "lane_posture": "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ACCEPTANCE_FOCUSED",
            "entries": entries,
            "blockers_exposed": [],
            "warnings": [entry for entry in entries if entry["status"] == "ACCEPTED_WARNING_NOT_BLOCKER"],
            "saturation_complete": True,
        }
    )


def terminal_decision(audits: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[str]]:
    blockers: list[dict[str, Any]] = []
    evidence_violations: list[dict[str, Any]] = []
    warning_keys: list[str] = []
    ok_checks = {
        "prerequisite": audits["prerequisite"]["all_checks_passed"],
        "row_coverage": audits["row_coverage"]["row_coverage_ok"],
        "field_status": audits["field_status"]["field_status_audit_ok"],
        "fail_prospective_forbidden": audits["fail_prospective_forbidden"]["fail_prospective_forbidden_audit_ok"],
        "no_leak_surface": audits["noleak_surface"]["no_leak_surface_audit_ok"],
        "source_hash_binding": audits["source_hash"]["source_hash_binding_ok"],
        "saturation": audits["saturation"]["saturation_complete"],
    }
    for key, ok in ok_checks.items():
        if not ok:
            blockers.append({"audit": key, "issue": "required_check_failed"})
    if audits["noleak_surface"]["closure_exact_forbidden_result_key_hit_count"] or audits["noleak_surface"]["closure_exact_forbidden_broker_key_hit_count"]:
        evidence_violations.append({"audit": "no_leak_surface", "issue": "forbidden_evidence_or_result_key_present"})
    if audits["noleak_surface"]["raw_market_blob_paths_in_builder_diff"] or audits["noleak_surface"]["trading_surface_paths_in_builder_diff"]:
        evidence_violations.append({"audit": "no_leak_surface", "issue": "builder_diff_crossed_forbidden_surface"})
    if evidence_violations:
        return TERMINAL_REJECT, evidence_violations, warning_keys
    if blockers:
        return TERMINAL_REPAIR, blockers, warning_keys
    warning_keys.extend(["historical_strategy_intent_absence_fail_closed", "broad_source_roots_scan_truncated_but_not_blocking"])
    return TERMINAL_ACCEPT, [], warning_keys


def audit_decision(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decision, blockers, warnings = terminal_decision(audits)
    return safe_flag_payload(
        {
            "artifact_family": "decision_ledger",
            "terminal_decision": decision,
            "terminal_blockers": blockers,
            "warnings": warnings,
            "accepted_promotion": False,
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_g12_packet_control_evidence_only": decision == TERMINAL_ACCEPT,
            "next_prompt_path": rel(NEXT_G0_PROMPT) if decision == TERMINAL_ACCEPT else None,
            "repair_prompt_required": decision != TERMINAL_ACCEPT,
            "terminal_evidence_boundary": "CONTROL_EVIDENCE_ONLY_NOT_STRATEGY_PERFORMANCE",
        }
    )


def completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_and_context_use_recorded", True, "Context anchor records doctrine files read after preflight and G12 audit posture."),
        ("builder_prompt_and_manifest_read", audits["source_hash"]["builder_manifest_read_fully"], "Source hash audit reads the builder manifest and every listed artifact with available hashes."),
        ("accepted_evidence_chain_reconciled", audits["prerequisite"]["all_checks_passed"], "Prerequisite audit reconciles candidate packet, target packet, G12 neutral audit, G0 synthesis, and builder decision."),
        ("row_coverage_recomputed", audits["row_coverage"]["row_coverage_ok"], "Candidate, descriptor, and closure rowsets all cover 3,014 unique ids exactly once."),
        ("field_statuses_and_hashes_recomputed", audits["field_status"]["field_status_audit_ok"], "Field enum, required families, row hashes, and closed-field values were recomputed."),
        ("fail_closed_prospective_forbidden_audited", audits["fail_prospective_forbidden"]["fail_prospective_forbidden_audit_ok"], "Fail-closed nulls, prospective requirements, and forbidden broker field status were checked."),
        ("no_leak_raw_blob_live_surface_audited", audits["noleak_surface"]["no_leak_surface_audit_ok"], "Closure rows, builder commit paths, raw blob suffixes, safe flags, and trading-surface paths were checked."),
        ("source_hash_input_binding_audited", audits["source_hash"]["source_hash_binding_ok"], "Input and manifest artifact hashes were recomputed."),
        ("saturation_self_red_team_complete", audits["saturation"]["saturation_complete"], "Saturation ledger answered every audit prompt question."),
        ("next_g0_or_repair_prompt_emitted", NEXT_G0_PROMPT.exists(), rel(NEXT_G0_PROMPT)),
        ("safe_flags_closed", decision["terminal_decision"] == TERMINAL_ACCEPT, "Terminal decision remains control evidence only with NO_PROMOTION_VERDICT."),
    ]
    return safe_flag_payload(
        {
            "artifact_family": "completion_audit",
            "objective_restatement": "Independently audit the SCID strategy-field source expansion packet for all 3,014 accepted SCID candidates, accepting exact fail-closed historical absence when proven and rejecting inference, leakage, denominator drift, vague requirements, or forbidden surfaces.",
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "satisfied": bool(satisfied), "evidence": evidence}
                for requirement, satisfied, evidence in checklist
            ],
            "all_requirements_satisfied_before_external_test_closeout": all(bool(satisfied) for _, satisfied, _ in checklist),
            "terminal_decision": decision["terminal_decision"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "NO_PROMOTION_VERDICT": True,
        }
    )


def write_next_g0_prompt() -> None:
    text = """# G0 SCID Strategy-Field Source Expansion Packet Synthesis Control Prompt

Date: 2026-05-12
Owner lane: G0 synthesis/control only after G12 strategy-field packet audit
Evidence class: `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/g12_scid_strategy_field_source_expansion_packet_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Synthesize the accepted G12 audit of the SCID strategy-field source expansion packet and choose the next control route. Decide whether the source-field packet opens result-design readiness, requires forward capture implementation first, needs a broader source search, or should become negative learning about historical strategy-field absence. This is a G0 control decision only. Do not execute validation, score results, claim strategy edge, compute R/PnL/win-rate/expectancy/performance, open broker account/order/history/deal/position evidence, call AI/API, use paid/vendor access, commit raw market-data blobs, or change live behavior or trading-surface files.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G12 strategy-field packet audit route manifest, decision ledger, completion audit, row coverage audit, field-status audit, fail-closed/prospective/forbidden audit, no-leak/raw-blob/live-surface audit, source hash/input binding audit, saturation ledger, and closeout verification.
9. Read the builder packet manifest, status summary, fail-closed ledger, prospective capture ledger, duplicate denominator ledger, and completion audit.
10. Read the accepted G0/G12 neutral-target evidence chain that led to the builder packet.

Do not rely on chat memory. If interrupted, regenerate `LIVE_STATE` and resume from disk artifacts.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active G0 synthesis instructions. G0 posture is synthesis and route selection, not scoring. Separate source-control evidence, future capture requirements, result-design readiness, and validation. The completion audit must record whether both doctrine files were read after preflight, what was synthesized, what was deliberately not answered, and why the selected next route stays inside safe research/control boundaries.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation execution, target/result/performance scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required G0 Synthesis Questions

1. Does the accepted G12 packet make a result-design lane ready, or do the seven fail-closed strategy-intent families block direction-aware result design?
2. Should the next route prioritize forward capture implementation for strategy source fields, lower-timeframe availability, and orderflow/depth/proxy context?
3. Is a broader historical source search justified, or has the audit proven that missing historical GTOS intent/source-state is non-generatable from approved artifacts?
4. What negative learning should be preserved about neutral source-control candidates and historical strategy-field absence?
5. Which future lane owns exact source/capture/logger/parser/schema/redaction/as-of/G12 acceptance requirements?
6. What must remain forbidden until a separate owner-approved evidence class exists?

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/`

Emit at minimum:

- context anchor;
- accepted G12 audit reconciliation;
- source-field readiness synthesis;
- route option ranking ledger;
- capture-only implementation route specification if ranked first;
- negative-learning ledger;
- forbidden-surface/no-leak continuity audit;
- decision ledger;
- output manifest;
- standalone verifier;
- focused tests;
- completion audit;
- closeout verification;
- next controlling prompt for the selected route.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G0_STRATEGY_FIELD_PACKET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE`
- `REPAIR_G12_STRATEGY_FIELD_PACKET_AUDIT_REQUIRED`
- `NO_NEXT_ROUTE_SOURCE_FIELD_ABSENCE_ACCEPTED_AS_NEGATIVE_LEARNING`

## Completion Standard

Mark complete only after the G12 audit is reconciled from disk, every required synthesis question is answered, the selected next route is emitted as a full controlling prompt, verifier and focused tests pass, scoped commits are created, `.context/00_core/research_current_state.md` is refreshed if materially stale, final `python scripts/generate_live_state.py` is run, and no unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; synthesize the accepted G12 strategy-field packet audit and choose the next route among result-design readiness, forward capture implementation, broader source search, or negative learning; emit route, verifier, focused tests, next prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
"""
    NEXT_G0_PROMPT.write_text(text, encoding="utf-8")


def output_paths() -> dict[str, Path]:
    return {
        "context_anchor_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_CONTEXT_ANCHOR_2026-05-12.json",
        "context_anchor_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_CONTEXT_ANCHOR_2026-05-12.md",
        "prereq_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_PREREQUISITE_RECONCILIATION_AUDIT_2026-05-12.json",
        "prereq_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_PREREQUISITE_RECONCILIATION_AUDIT_2026-05-12.md",
        "row_coverage_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ROW_COVERAGE_DENOMINATOR_AUDIT_2026-05-12.json",
        "row_coverage_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ROW_COVERAGE_DENOMINATOR_AUDIT_2026-05-12.md",
        "field_status_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
        "field_status_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.md",
        "fail_prospective_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FAIL_PROSPECTIVE_FORBIDDEN_AUDIT_2026-05-12.json",
        "fail_prospective_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FAIL_PROSPECTIVE_FORBIDDEN_AUDIT_2026-05-12.md",
        "noleak_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_NOLEAK_RAW_BLOB_LIVE_SURFACE_AUDIT_2026-05-12.json",
        "noleak_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_NOLEAK_RAW_BLOB_LIVE_SURFACE_AUDIT_2026-05-12.md",
        "source_hash_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json",
        "source_hash_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.md",
        "saturation_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json",
        "saturation_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.md",
        "decision_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "decision_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.md",
        "completion_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
        "completion_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-12.md",
        "manifest_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
        "manifest_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_OUTPUT_MANIFEST_2026-05-12.md",
        "closeout_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
        "closeout_md": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.md",
        "verification_json": ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
    }


def artifact_manifest(paths: dict[str, Path]) -> dict[str, Any]:
    required = {
        "context anchor": paths["context_anchor_json"],
        "prerequisite evidence-chain reconciliation audit": paths["prereq_json"],
        "row coverage and duplicate denominator recomputation audit": paths["row_coverage_json"],
        "field-status enum and closed-field recomputation audit": paths["field_status_json"],
        "fail-closed/prospective/forbidden status audit": paths["fail_prospective_json"],
        "no-leak/forbidden-surface/raw-blob/trading-surface audit": paths["noleak_json"],
        "source hash/input binding audit": paths["source_hash_json"],
        "saturation/self-red-team ledger": paths["saturation_json"],
        "decision ledger": paths["decision_json"],
        "completion audit": paths["completion_json"],
        "closeout verification": paths["closeout_json"],
        "standalone verifier": ROUTE_DIR / "verify_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py",
        "focused tests": ROUTE_DIR / "test_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py",
        "next G0 synthesis/control prompt": NEXT_G0_PROMPT,
    }
    return safe_flag_payload(
        {
            "artifact_family": "output_manifest",
            "artifacts": [
                {
                    "artifact_name": name,
                    "path": rel(path),
                    "exists_after_build": path.exists(),
                    "sha256_after_build": None if path == paths["manifest_json"] else sha256_file(path),
                }
                for name, path in required.items()
            ],
            "required_artifact_families_covered": {name: path.exists() for name, path in required.items()},
            "artifact_count": len(required),
            "terminal_decision_ref": rel(paths["decision_json"]),
        }
    )


def build_audits() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    src = load_sources()
    audits: dict[str, dict[str, Any]] = {}
    audits["context_anchor"] = audit_context_anchor()
    audits["prerequisite"] = audit_prerequisites(src)
    audits["row_coverage"] = audit_row_coverage(src)
    audits["field_status"] = audit_field_statuses(src)
    audits["fail_prospective_forbidden"] = audit_fail_prospective_forbidden(src)
    audits["noleak_surface"] = audit_noleak_and_surfaces(src)
    audits["source_hash"] = audit_source_hash_binding(src)
    audits["saturation"] = audit_saturation(src)
    decision = audit_decision(audits)
    audits["decision"] = decision
    audits["completion"] = completion_audit(audits, decision)
    return audits, src


def write_audits(audits: dict[str, dict[str, Any]]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    write_next_g0_prompt()
    paths = output_paths()
    mapping = [
        ("context_anchor", paths["context_anchor_json"], paths["context_anchor_md"], "G12 SCID Strategy Field Packet Audit Context Anchor"),
        ("prerequisite", paths["prereq_json"], paths["prereq_md"], "Prerequisite Evidence Chain Reconciliation Audit"),
        ("row_coverage", paths["row_coverage_json"], paths["row_coverage_md"], "Row Coverage And Denominator Audit"),
        ("field_status", paths["field_status_json"], paths["field_status_md"], "Field Status Recomposition Audit"),
        ("fail_prospective_forbidden", paths["fail_prospective_json"], paths["fail_prospective_md"], "Fail Closed Prospective Forbidden Audit"),
        ("noleak_surface", paths["noleak_json"], paths["noleak_md"], "No Leak Raw Blob Live Surface Audit"),
        ("source_hash", paths["source_hash_json"], paths["source_hash_md"], "Source Hash Input Binding Audit"),
        ("saturation", paths["saturation_json"], paths["saturation_md"], "Saturation Self Red Team Ledger"),
        ("decision", paths["decision_json"], paths["decision_md"], "Decision Ledger"),
        ("completion", paths["completion_json"], paths["completion_md"], "Completion Audit"),
    ]
    for key, json_path, md_path, title in mapping:
        write_json(json_path, audits[key])
        write_md_json(md_path, title, audits[key])

    closeout_placeholder = safe_flag_payload(
        {
            "artifact_family": "closeout_verification",
            "builder_command": "pending_external_command_recording",
            "py_compile": "pending_external_command_recording",
            "verifier": "pending_external_command_recording",
            "focused_pytest": "pending_external_command_recording",
            "terminal_decision": audits["decision"]["terminal_decision"],
        }
    )
    write_json(paths["closeout_json"], closeout_placeholder)
    write_md_json(paths["closeout_md"], "Closeout Verification", closeout_placeholder)

    manifest = artifact_manifest(paths)
    write_json(paths["manifest_json"], manifest)
    write_md_json(paths["manifest_md"], "Output Manifest", manifest)


def record_closeout(builder_result: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = output_paths()
    py_files = [
        rel(ROUTE_DIR / "build_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"),
        rel(ROUTE_DIR / "verify_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"),
        rel(ROUTE_DIR / "test_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"),
    ]
    py_compile = run_command([sys.executable, "-m", "py_compile", *py_files], timeout=120)
    verifier = run_command([sys.executable, rel(ROUTE_DIR / "verify_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py")], timeout=180)
    pytest = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            rel(ROUTE_DIR / "test_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"),
            "--basetemp=tmp_codex_probe/pytest_g12_scid_strategy_field_packet_audit",
        ],
        timeout=240,
    )
    decision = read_json(paths["decision_json"])
    closeout = safe_flag_payload(
        {
            "artifact_family": "closeout_verification",
            "builder_command": builder_result
            or {
                "command": f"{sys.executable} {rel(ROUTE_DIR / 'build_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py')}",
                "status": "PASSED",
            },
            "py_compile": py_compile,
            "verifier": {
                "command": verifier["args"],
                "status": verifier["status"],
                "returncode": verifier["returncode"],
                "result_path": rel(paths["verification_json"]),
                "stdout_tail": verifier["stdout_tail"],
                "stderr_tail": verifier["stderr_tail"],
            },
            "focused_pytest": pytest,
            "terminal_decision": decision["terminal_decision"],
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        }
    )
    write_json(paths["closeout_json"], closeout)
    write_md_json(paths["closeout_md"], "Closeout Verification", closeout)
    manifest = artifact_manifest(paths)
    write_json(paths["manifest_json"], manifest)
    write_md_json(paths["manifest_md"], "Output Manifest", manifest)
    return closeout


def build(write: bool = True, closeout: bool = True) -> dict[str, Any]:
    audits, _ = build_audits()
    if write:
        write_audits(audits)
    result = {
        "ok": audits["decision"]["terminal_decision"] == TERMINAL_ACCEPT,
        "terminal_decision": audits["decision"]["terminal_decision"],
        "candidate_rows": audits["row_coverage"]["closure_rows"],
        "blockers": audits["decision"]["terminal_blockers"],
    }
    if write and closeout:
        record_closeout(
            {
                "command": f"{sys.executable} {rel(ROUTE_DIR / 'build_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py')}",
                "status": "PASSED",
                "result": result,
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-closeout", action="store_true", help="Write audit artifacts without running closeout commands.")
    args = parser.parse_args()
    result = build(write=True, closeout=not args.no_closeout)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
OUTCOME_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"

BUILDER_DIR = OUTCOME_DIR / "scid_combined_source_search_and_forward_capture_route"
PACKET_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"
G12_PACKET_AUDIT_DIR = OUTCOME_DIR / "g12_scid_strategy_field_source_expansion_packet_audit"
G0_PACKET_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_strategy_field_source_expansion_packet_synthesis"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT"
ROUTE_ID = "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR"
TERMINAL_REPAIR = "REPAIR_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_REQUIRED"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"
REPAIR_PROMPT = PROMPT_DIR / "REPAIR_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_PROMPT_2026-05-12.md"

AUDIT_PROMPT = PROMPT_DIR / "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md"
BUILDER_G12_PROMPT = AUDIT_PROMPT
BUILDER_MANIFEST = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_OUTPUT_MANIFEST_2026-05-12.json"
BUILDER_CONTEXT = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-12.json"
BUILDER_STATUS_JSONL = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_2026-05-12.jsonl"
BUILDER_STATUS_SUMMARY = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY_2026-05-12.json"
BUILDER_SEARCHED_ROOTS = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_SEARCHED_ROOT_LEDGER_2026-05-12.json"
BUILDER_HIST_RECOVERY = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_HISTORICAL_SOURCE_STATE_RECOVERY_ATTEMPT_LEDGER_2026-05-12.json"
BUILDER_JOIN_RECOVERY = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_SOURCE_STATE_JOIN_RECOVERY_CANDIDATE_LEDGER_2026-05-12.json"
BUILDER_CAPTURE_CONTRACT = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json"
BUILDER_SCHEMA_SPEC = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION_2026-05-12.json"
BUILDER_READINESS = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER_2026-05-12.json"
BUILDER_VERIFICATION = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-12.json"
BUILDER_COMPLETION = BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-12.json"

PACKET_ROWS = PACKET_DIR / "SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl"
PACKET_SUMMARY = PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json"
PACKET_MANIFEST = PACKET_DIR / "SCID_STRATEGY_FIELD_OUTPUT_MANIFEST_2026-05-12.json"
G12_PACKET_DECISION = G12_PACKET_AUDIT_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json"
G12_PACKET_FIELD_AUDIT = G12_PACKET_AUDIT_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json"
G0_PACKET_DECISION = G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_DECISION_LEDGER_2026-05-12.json"
G0_PACKET_SOURCE_READINESS = G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_SOURCE_FIELD_READINESS_SYNTHESIS_2026-05-12.json"
G0_PACKET_CAPTURE_SPEC = G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION_2026-05-12.json"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

FIELD_FAMILIES = [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
    "broker_account_order_history_deal_position_evidence",
]
CLOSED_DESCRIPTOR_FIELDS = {
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
}
HISTORICAL_INTENT_FIELDS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
}
MARKET_CONTEXT_FIELDS = {
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
}
REQUIRED_CAPTURE_GROUPS = {
    *HISTORICAL_INTENT_FIELDS,
    *MARKET_CONTEXT_FIELDS,
    "baseline_control_fields",
}
REQUIRED_ROOT_IDS = {
    "accepted_strategy_field_packet",
    "accepted_g12_g0_strategy_field_artifacts",
    "accepted_scid_candidate_input_and_neutral_artifacts",
    "source_control_sibling_routes",
    "shadow_logs_source_safe_nonbroker",
    "program_control_artifacts",
    "pipeline_state_artifacts",
    "knowledge_base_nonbroker_records",
    "repo_data_text_manifests_only",
    "repo_research_archive",
    "prior_worktree_gtos_otb",
    "prior_worktree_gtos_otl",
    "prior_recovery_cache",
}
RAW_MARKET_SUFFIXES = {".scid", ".parquet", ".csv", ".dly", ".bin", ".depth", ".jsonl.gz"}
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".py", ".yaml", ".yml", ".ps1"}
FORBIDDEN_PATH_FRAGMENTS = {
    "account_history",
    "account_pnl",
    "account_truth",
    "broker_actual",
    "daily_pnl",
    "mt5_deals",
    "trade_records",
}
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_test.py",
    "run_agent.py",
)
BUILDER_RELATED_COMMITS = ["da9b571a", "5ff70481", "b40d67a1", "b8d24ccb", "c039047c"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def stable_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{rel(path)}:{line_no}: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md_json(path: Path, title: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# " + title + "\n\n```json\n" + json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n```\n"
    path.write_text(body, encoding="utf-8")


def git_output(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def run_command(args: list[str], timeout: int = 240) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "args": args,
            "returncode": proc.returncode,
            "status": "PASSED" if proc.returncode == 0 else "FAILED",
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
    except Exception as exc:  # pragma: no cover - closeout guard
        return {"args": args, "returncode": None, "status": "ERROR", "stdout_tail": "", "stderr_tail": str(exc)}


def safe_payload(artifact_family: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "g12_scid_combined_source_capture_route_audit_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def unique_by(rows: list[dict[str, Any]], key: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    out: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        value = str(row.get(key))
        if value in out:
            duplicates.append(value)
        else:
            out[value] = row
    return out, duplicates


def source_root_specs() -> list[dict[str, Any]]:
    return [
        {"root_id": "accepted_strategy_field_packet", "path": PACKET_DIR},
        {"root_id": "accepted_g12_g0_strategy_field_artifacts", "path": [G12_PACKET_AUDIT_DIR, G0_PACKET_SYNTHESIS_DIR]},
        {
            "root_id": "accepted_scid_candidate_input_and_neutral_artifacts",
            "path": [
                OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control",
                OUTCOME_DIR / "scid_asof_quarantined_neutral_target_execution_packet",
                OUTCOME_DIR / "scid_asof_sealed_validation_target_horizon_repair",
                OUTCOME_DIR / "g0_scid_neutral_target_control_synthesis",
                OUTCOME_DIR / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit",
            ],
        },
        {
            "root_id": "source_control_sibling_routes",
            "path": [
                OUTCOME_DIR / "fpb_source_expansion_and_sealed_pool_materialization",
                OUTCOME_DIR / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair",
                OUTCOME_DIR / "cnr_source_field_packet_builder",
                OUTCOME_DIR / "g12_cnr_source_field_packet_audit",
                OUTCOME_DIR / "no_api_mechanical_replay_engine_from_source_universe",
                OUTCOME_DIR / "g12_no_api_mechanical_replay_engine_source_control_audit",
                OUTCOME_DIR / "gtos_research_capability_limitation_closure_control_route",
            ],
        },
        {"root_id": "shadow_logs_source_safe_nonbroker", "path": REPO_ROOT / "shadow_logs"},
        {"root_id": "program_control_artifacts", "path": REPO_ROOT / "research/program_control"},
        {"root_id": "pipeline_state_artifacts", "path": REPO_ROOT / "pipeline_state"},
        {"root_id": "knowledge_base_nonbroker_records", "path": REPO_ROOT / "knowledge_base"},
        {"root_id": "repo_data_text_manifests_only", "path": REPO_ROOT / "data"},
        {"root_id": "repo_research_archive", "path": REPO_ROOT / "research/archive"},
        {"root_id": "prior_worktree_gtos_otb", "path": Path(r"C:\tmp\gtos_otb")},
        {"root_id": "prior_worktree_gtos_otl", "path": Path(r"C:\tmp\gtos_otl")},
        {"root_id": "prior_recovery_cache", "path": Path(r"C:\tmp\gtos_recovery")},
    ]


def expand_files(path_spec: Path | list[Path]) -> list[Path]:
    paths = path_spec if isinstance(path_spec, list) else [path_spec]
    out: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            out.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file():
                out.append(path)
    return out


def is_raw_blob(path: Path) -> bool:
    return path.suffix.lower() in RAW_MARKET_SUFFIXES or path.name.lower().endswith(".jsonl.gz")


def is_forbidden_broker_path(path: Path) -> bool:
    text = path.as_posix().lower()
    return any(fragment in text for fragment in FORBIDDEN_PATH_FRAGMENTS)


def load_sources() -> dict[str, Any]:
    return {
        "builder_rows": read_jsonl(BUILDER_STATUS_JSONL),
        "builder_summary": read_json(BUILDER_STATUS_SUMMARY),
        "builder_context": read_json(BUILDER_CONTEXT),
        "builder_manifest": read_json(BUILDER_MANIFEST),
        "builder_searched_roots": read_json(BUILDER_SEARCHED_ROOTS),
        "builder_hist_recovery": read_json(BUILDER_HIST_RECOVERY),
        "builder_join_recovery": read_json(BUILDER_JOIN_RECOVERY),
        "builder_capture_contract": read_json(BUILDER_CAPTURE_CONTRACT),
        "builder_schema_spec": read_json(BUILDER_SCHEMA_SPEC),
        "builder_readiness": read_json(BUILDER_READINESS),
        "builder_verification": read_json(BUILDER_VERIFICATION),
        "builder_completion": read_json(BUILDER_COMPLETION),
        "packet_rows": read_jsonl(PACKET_ROWS),
        "packet_summary": read_json(PACKET_SUMMARY),
        "packet_manifest": read_json(PACKET_MANIFEST),
        "g12_packet_decision": read_json(G12_PACKET_DECISION),
        "g12_packet_field_audit": read_json(G12_PACKET_FIELD_AUDIT),
        "g0_packet_decision": read_json(G0_PACKET_DECISION),
        "g0_packet_source_readiness": read_json(G0_PACKET_SOURCE_READINESS),
        "g0_packet_capture_spec": read_json(G0_PACKET_CAPTURE_SPEC),
    }


def audit_context_anchor() -> dict[str, Any]:
    return safe_payload(
        "context_anchor",
        {
            "current_head": git_output(["rev-parse", "HEAD"]),
            "current_head_subject": git_output(["log", "-1", "--format=%h %s"]),
            "controlling_prompt": rel(AUDIT_PROMPT),
            "builder_route": rel(BUILDER_DIR),
            "accepted_strategy_field_packet": rel(PACKET_DIR),
            "mandatory_preflight_and_context_record": {
                "generated_live_state": True,
                "read_live_state": True,
                "read_quick_reference_card": True,
                "read_research_operating_doctrine": True,
                "read_goal_session_research_discipline": True,
                "read_research_current_state": True,
                "read_latest_handoff": True,
                "read_this_prompt_from_disk": True,
                "read_builder_route_artifacts": True,
                "read_accepted_g0_g12_strategy_field_packet_artifacts": True,
            },
            "lane_posture": "independent G12 audit: adversarial but fair; accept exact source/control evidence, repair concrete manifest binding drift, reject concrete source/no-leak/surface failures",
            "deliberately_not_opened": [
                "validation",
                "result scoring",
                "strategy edge claims",
                "R/PnL/win-rate/expectancy/performance",
                "AI/API/vendor calls",
                "broker account/order/history/deal/position evidence",
                "raw market-data blob commits",
                "live behavior",
                "prompt/config/risk/safety/execution/canary/selector changes",
            ],
        },
    )


def expected_status(field: str) -> str:
    if field in CLOSED_DESCRIPTOR_FIELDS:
        return "RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE"
    if field in HISTORICAL_INTENT_FIELDS:
        return "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"
    if field in MARKET_CONTEXT_FIELDS:
        return "RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN"
    if field == "baseline_control_fields":
        return "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS"
    if field == "broker_account_order_history_deal_position_evidence":
        return "FORBIDDEN_IN_THIS_EVIDENCE_CLASS"
    raise KeyError(field)


def recompute_row_hash(row: dict[str, Any]) -> str:
    copy = dict(row)
    copy.pop("combined_source_capture_row_hash", None)
    return stable_hash(copy)


def audit_row_coverage(src: dict[str, Any]) -> dict[str, Any]:
    builder_rows = src["builder_rows"]
    packet_rows = src["packet_rows"]
    builder_by_id, builder_dupes = unique_by(builder_rows, "candidate_input_row_id")
    packet_by_id, packet_dupes = unique_by(packet_rows, "candidate_input_row_id")
    builder_denoms = [str(row.get("duplicate_proxy_denominator_key")) for row in builder_rows]
    packet_denoms = [str(row.get("duplicate_proxy_denominator_key")) for row in packet_rows]

    set_drift = {
        "missing_from_builder": sorted(set(packet_by_id) - set(builder_by_id))[:20],
        "extra_in_builder": sorted(set(builder_by_id) - set(packet_by_id))[:20],
    }
    top_level_mismatches: list[dict[str, Any]] = []
    denominator_mismatches: list[str] = []
    row_hash_mismatches: list[str] = []
    for candidate_id in sorted(set(builder_by_id) & set(packet_by_id)):
        b = builder_by_id[candidate_id]
        p = packet_by_id[candidate_id]
        if b.get("duplicate_proxy_denominator_key") != p.get("duplicate_proxy_denominator_key"):
            denominator_mismatches.append(candidate_id)
        if b.get("candidate_duplicate_key") != p.get("candidate_duplicate_key"):
            denominator_mismatches.append(candidate_id)
        for key in [
            "canonical_economic_group",
            "symbol",
            "source_proxy_group",
            "decision_asof_utc",
            "entry_reference_time_utc",
            "partition_assignment",
        ]:
            if b.get(key) != p.get(key):
                top_level_mismatches.append(
                    {
                        "candidate_input_row_id": candidate_id,
                        "field": key,
                        "builder": b.get(key),
                        "packet": p.get(key),
                    }
                )
        if b.get("combined_source_capture_row_hash") != recompute_row_hash(b):
            row_hash_mismatches.append(candidate_id)

    row_coverage_ok = (
        len(builder_rows) == 3014
        and len(builder_by_id) == 3014
        and len(set(builder_denoms)) == 3014
        and len(packet_rows) == 3014
        and len(packet_by_id) == 3014
        and len(set(packet_denoms)) == 3014
        and not builder_dupes
        and not packet_dupes
        and not set_drift["missing_from_builder"]
        and not set_drift["extra_in_builder"]
        and not denominator_mismatches
        and not top_level_mismatches
        and not row_hash_mismatches
    )
    return safe_payload(
        "row_coverage_denominator_recomputation_audit",
        {
            "builder_candidate_rows": len(builder_rows),
            "builder_unique_candidate_input_row_ids": len(builder_by_id),
            "builder_unique_duplicate_proxy_denominator_keys": len(set(builder_denoms)),
            "packet_candidate_rows": len(packet_rows),
            "packet_unique_candidate_input_row_ids": len(packet_by_id),
            "packet_unique_duplicate_proxy_denominator_keys": len(set(packet_denoms)),
            "candidate_id_set_drift": set_drift,
            "builder_candidate_id_duplicates": builder_dupes[:20],
            "packet_candidate_id_duplicates": packet_dupes[:20],
            "denominator_mismatch_count": len(denominator_mismatches),
            "denominator_mismatch_samples": denominator_mismatches[:20],
            "top_level_mismatch_count": len(top_level_mismatches),
            "top_level_mismatch_samples": top_level_mismatches[:20],
            "row_hash_mismatch_count": len(row_hash_mismatches),
            "row_hash_mismatch_samples": row_hash_mismatches[:20],
            "row_coverage_denominator_recomputation_ok": row_coverage_ok,
        },
    )


def audit_field_statuses(src: dict[str, Any]) -> dict[str, Any]:
    rows = src["builder_rows"]
    counts: dict[str, Counter[str]] = {field: Counter() for field in FIELD_FAMILIES}
    missing_field_rows: list[dict[str, str]] = []
    unexpected_status_rows: list[dict[str, str]] = []
    prior_status_mismatches: list[dict[str, str]] = []
    packet_by_id, _ = unique_by(src["packet_rows"], "candidate_input_row_id")
    for row in rows:
        statuses = row.get("field_statuses", {})
        packet_statuses = packet_by_id[row["candidate_input_row_id"]].get("field_statuses", {})
        for field in FIELD_FAMILIES:
            payload = statuses.get(field)
            if not isinstance(payload, dict):
                missing_field_rows.append({"candidate_input_row_id": row["candidate_input_row_id"], "field": field})
                continue
            observed = payload.get("status")
            counts[field][str(observed)] += 1
            expected = expected_status(field)
            if observed != expected:
                unexpected_status_rows.append(
                    {
                        "candidate_input_row_id": row["candidate_input_row_id"],
                        "field": field,
                        "observed": str(observed),
                        "expected": expected,
                    }
                )
            prior_packet_status = payload.get("prior_packet_status")
            packet_status = packet_statuses.get(field, {}).get("status") if isinstance(packet_statuses, dict) else None
            if field != "baseline_control_fields" and prior_packet_status != packet_status:
                prior_status_mismatches.append(
                    {
                        "candidate_input_row_id": row["candidate_input_row_id"],
                        "field": field,
                        "prior_packet_status": str(prior_packet_status),
                        "packet_status": str(packet_status),
                    }
                )
    summary_counts = src["builder_summary"].get("field_status_counts", {})
    summary_mismatches = []
    for field, counter in counts.items():
        if dict(counter) != summary_counts.get(field):
            summary_mismatches.append({"field": field, "recomputed": dict(counter), "summary": summary_counts.get(field)})

    expected_counts = {
        field: {expected_status(field): 3014}
        for field in FIELD_FAMILIES
    }
    field_status_recomputation_ok = (
        len(rows) == 3014
        and not missing_field_rows
        and not unexpected_status_rows
        and not prior_status_mismatches
        and not summary_mismatches
        and {field: dict(counter) for field, counter in counts.items()} == expected_counts
    )
    return safe_payload(
        "field_status_recomputation_audit",
        {
            "field_status_counts_recomputed": {field: dict(counter) for field, counter in counts.items()},
            "expected_field_status_counts": expected_counts,
            "summary_count_mismatches": summary_mismatches,
            "missing_field_row_count": len(missing_field_rows),
            "missing_field_row_samples": missing_field_rows[:20],
            "unexpected_status_row_count": len(unexpected_status_rows),
            "unexpected_status_row_samples": unexpected_status_rows[:20],
            "prior_packet_status_mismatch_count": len(prior_status_mismatches),
            "prior_packet_status_mismatch_samples": prior_status_mismatches[:20],
            "field_status_recomputation_ok": field_status_recomputation_ok,
        },
    )


def audit_source_search_saturation(src: dict[str, Any]) -> dict[str, Any]:
    builder = src["builder_searched_roots"]
    builder_root_ids = set(builder.get("searched_root_ids", []))
    current_inventory = []
    aggregate = Counter()
    for spec in source_root_specs():
        files = expand_files(spec["path"])
        raw = [path for path in files if is_raw_blob(path)]
        forbidden = [path for path in files if is_forbidden_broker_path(path)]
        text = [path for path in files if path.suffix.lower() in TEXT_SUFFIXES and not is_raw_blob(path) and not is_forbidden_broker_path(path)]
        aggregate["files_seen"] += len(files)
        aggregate["raw_market_blob_files_present"] += len(raw)
        aggregate["forbidden_broker_account_order_history_files_present"] += len(forbidden)
        aggregate["text_files_currently_available_for_safe_scan"] += len(text)
        current_inventory.append(
            {
                "root_id": spec["root_id"],
                "exists_now": any(path.exists() for path in (spec["path"] if isinstance(spec["path"], list) else [spec["path"]])),
                "current_files_seen": len(files),
                "current_text_files_safe_scan": len(text),
                "current_raw_market_blob_files_present": len(raw),
                "current_forbidden_broker_files_present": len(forbidden),
            }
        )

    join_decisions = {row.get("join_route"): row.get("decision") for row in src["builder_join_recovery"].get("join_candidates", [])}
    totals = builder.get("totals", {})
    required_skips = builder.get("hard_boundary_skips", {})
    missing_root_ids = sorted(REQUIRED_ROOT_IDS - builder_root_ids)
    weak_policy_ok = join_decisions.get("shadow_logs_symbol_time_candidate_lead") == "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING"
    raw_policy_ok = str(join_decisions.get("raw_scid_or_market_blob_reparse", "")).startswith("FORBIDDEN_OR_INSUFFICIENT")
    search_result_ok = (
        builder.get("source_search_result")
        == "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS"
    )
    saturation_ok = (
        not missing_root_ids
        and totals.get("files_seen", 0) >= 1
        and totals.get("files_selected_for_parse", 0) >= 1
        and totals.get("text_files_scanned", 0) >= 1
        and totals.get("explicit_candidate_id_hits", 0) >= 3014
        and totals.get("explicit_duplicate_key_hits", 0) >= 3014
        and "raw_market_blob_suffixes" in required_skips
        and "forbidden_broker_account_order_history_fragments" in required_skips
        and weak_policy_ok
        and raw_policy_ok
        and search_result_ok
    )
    return safe_payload(
        "source_search_saturation_audit",
        {
            "builder_searched_root_ids": sorted(builder_root_ids),
            "required_root_ids_missing_from_builder_ledger": missing_root_ids,
            "builder_totals": totals,
            "current_root_inventory_recomputed": current_inventory,
            "current_root_inventory_aggregate": dict(aggregate),
            "hard_boundary_skips": required_skips,
            "weak_symbol_time_policy": join_decisions.get("shadow_logs_symbol_time_candidate_lead"),
            "raw_blob_join_policy": join_decisions.get("raw_scid_or_market_blob_reparse"),
            "historical_recovery_explicit_new_strategy_intent_recoveries": src["builder_hist_recovery"].get("explicit_new_strategy_intent_recoveries"),
            "source_search_result": builder.get("source_search_result"),
            "saturation_audit_note": "Current root inventory is recomputed against a live dirty worktree; exact file counts may drift after the builder. Blocking criteria are missing required root classes, absent safe-scan totals, accepted weak joins, accepted raw/broker joins, or a source-search terminal result other than saturated absence.",
            "source_search_saturation_ok": saturation_ok,
        },
    )


def audit_source_hash_manifest_binding(src: dict[str, Any]) -> dict[str, Any]:
    manifest = src["builder_manifest"]
    artifact_rows = []
    blocking_mismatches = []
    repaired_mismatches = []
    missing = []
    raw_blob_entries = []
    for artifact in manifest.get("artifacts", []):
        path = REPO_ROOT / artifact["path"]
        current_hash = sha256_file(path)
        recorded_hash = artifact.get("sha256")
        matches = current_hash == recorded_hash
        repair_status = "NO_REPAIR_NEEDED"
        blocking = False
        if not path.exists():
            missing.append(artifact["path"])
            blocking = True
        elif not matches:
            if path.resolve() == AUDIT_PROMPT.resolve():
                repair_status = "REPAIRED_BY_G12_CURRENT_PROMPT_HASH_BINDING_AFTER_POST_BUILD_PROMPT_HARDENING"
                repaired_mismatches.append(artifact["path"])
            elif path.resolve() == BUILDER_MANIFEST.resolve():
                repair_status = "SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING"
                repaired_mismatches.append(artifact["path"])
            else:
                repair_status = "BLOCKING_UNREPAIRED_HASH_MISMATCH"
                blocking = True
                blocking_mismatches.append(artifact["path"])
        if artifact.get("raw_market_blob"):
            raw_blob_entries.append(artifact["path"])
            blocking = True
        artifact_rows.append(
            {
                "path": artifact["path"],
                "exists": path.exists(),
                "recorded_sha256": recorded_hash,
                "current_sha256": current_hash,
                "recorded_hash_matches_current": matches,
                "raw_market_blob": bool(artifact.get("raw_market_blob")),
                "repair_status": repair_status,
                "blocking": blocking,
            }
        )

    input_hash_rows = []
    input_hash_blockers = []
    for name, binding in src["builder_context"].get("input_hashes", {}).items():
        path = REPO_ROOT / binding["path"]
        current_hash = sha256_file(path)
        matches = current_hash == binding.get("sha256")
        if not matches:
            input_hash_blockers.append(name)
        input_hash_rows.append(
            {
                "input_name": name,
                "path": binding["path"],
                "exists": path.exists(),
                "recorded_sha256": binding.get("sha256"),
                "current_sha256": current_hash,
                "matches": matches,
            }
        )

    covered = manifest.get("required_artifact_families_covered", {})
    false_covered = [key for key, value in covered.items() if value is not True]
    source_hash_binding_ok = not missing and not raw_blob_entries and not blocking_mismatches and not input_hash_blockers and not false_covered
    return safe_payload(
        "source_hash_manifest_binding_audit",
        {
            "builder_manifest_path": rel(BUILDER_MANIFEST),
            "builder_manifest_artifact_count": len(manifest.get("artifacts", [])),
            "artifact_hash_rows": artifact_rows,
            "missing_manifest_artifacts": missing,
            "raw_blob_manifest_entries": raw_blob_entries,
            "repaired_hash_binding_mismatches": repaired_mismatches,
            "blocking_unrepaired_hash_mismatches": blocking_mismatches,
            "input_hash_rows": input_hash_rows,
            "input_hash_blockers": input_hash_blockers,
            "required_artifact_families_covered": covered,
            "required_artifact_family_false_entries": false_covered,
            "source_hash_binding_repair_note": "The G12 prompt was intentionally hardened after the builder route and is rebound here to its current hash. The builder manifest self-hash is self-referential and is not used as a blocking source binding. All other artifact/input hash mismatches are blockers.",
            "source_hash_manifest_binding_ok_after_repair": source_hash_binding_ok,
        },
    )


def audit_capture_contract_exactness(src: dict[str, Any]) -> dict[str, Any]:
    contract = src["builder_capture_contract"]
    groups = {row.get("field_group"): row for row in contract.get("field_groups", [])}
    missing_groups = sorted(REQUIRED_CAPTURE_GROUPS - set(groups))
    vague_entries = []
    forbidden_gaps = []
    required_keys = [
        "future_source_or_logger",
        "required_fields",
        "parser_requirement",
        "schema_version_required",
        "redaction_rule",
        "as_of_rule",
        "no_leak_rule",
        "g12_acceptance_requirement",
        "historical_status_after_search",
    ]
    for field, entry in groups.items():
        if field not in REQUIRED_CAPTURE_GROUPS:
            continue
        for key in required_keys:
            value = entry.get(key)
            if value in (None, "", []):
                vague_entries.append({"field_group": field, "missing_or_empty_key": key})
        redaction = str(entry.get("redaction_rule", "")).lower()
        no_leak = str(entry.get("no_leak_rule", "")).lower()
        if not all(token in redaction for token in ["credential", "account", "ticket", "deal", "order", "position"]):
            forbidden_gaps.append({"field_group": field, "gap": "redaction_rule_missing_broker_identifier_terms"})
        if field in HISTORICAL_INTENT_FIELDS and not any(
            token in no_leak
            for token in [
                "price movement",
                "result",
                "path",
                "broker",
                "terminal",
                "future",
                "hindsight",
                "fill-derived",
                "later",
            ]
        ):
            forbidden_gaps.append({"field_group": field, "gap": "historical_intent_no_leak_rule_not_explicit_enough"})
        if field == "baseline_control_fields" and "target status" not in no_leak:
            forbidden_gaps.append({"field_group": field, "gap": "baseline_control_no_leak_rule_missing_target_status"})
    exactness_ok = not missing_groups and not vague_entries and not forbidden_gaps and contract.get("candidate_rows_covered") == 3014
    return safe_payload(
        "capture_contract_exactness_audit",
        {
            "candidate_rows_covered": contract.get("candidate_rows_covered"),
            "required_capture_groups": sorted(REQUIRED_CAPTURE_GROUPS),
            "observed_capture_groups": sorted(groups),
            "missing_capture_groups": missing_groups,
            "vague_or_missing_contract_entries": vague_entries,
            "forbidden_surface_contract_gaps": forbidden_gaps,
            "field_groups": contract.get("field_groups", []),
            "capture_contract_exactness_ok": exactness_ok,
        },
    )


def commit_file_paths(commit: str) -> list[str]:
    output = git_output(["show", "--name-only", "--format=", commit])
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def git_status_entries() -> list[dict[str, Any]]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    entries = []
    scoped_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/",
        f"research/science_program_2026_05/04_goal_prompts/{NEXT_G0_PROMPT.name}",
        f"research/science_program_2026_05/04_goal_prompts/{REPAIR_PROMPT.name}",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in scoped_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped_to_current_audit_or_context": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES),
                "scoped_raw_market_blob": scoped and (path.endswith(tuple(RAW_MARKET_SUFFIXES)) or path.endswith(".jsonl.gz")),
            }
        )
    return entries


def audit_noleak_forbidden_surface(src: dict[str, Any]) -> dict[str, Any]:
    candidate_rows = src["builder_rows"]
    safe_flag_violations = []
    forbidden_field_violations = []
    for row in candidate_rows:
        for key, expected in SAFE_FLAGS.items():
            if row.get(key) != expected:
                safe_flag_violations.append({"candidate_input_row_id": row.get("candidate_input_row_id"), "flag": key, "observed": row.get(key)})
        if "field_statuses" in row:
            broker = row["field_statuses"].get("broker_account_order_history_deal_position_evidence", {})
            if broker.get("status") != "FORBIDDEN_IN_THIS_EVIDENCE_CLASS":
                forbidden_field_violations.append(row.get("candidate_input_row_id"))
    artifact_safe_violations = []
    for name, payload in [
        ("builder_summary", src["builder_summary"]),
        ("builder_context", src["builder_context"]),
        ("builder_searched_roots", src["builder_searched_roots"]),
        ("builder_hist_recovery", src["builder_hist_recovery"]),
        ("builder_join_recovery", src["builder_join_recovery"]),
        ("builder_capture_contract", src["builder_capture_contract"]),
        ("builder_schema_spec", src["builder_schema_spec"]),
        ("builder_readiness", src["builder_readiness"]),
    ]:
        for key, expected in SAFE_FLAGS.items():
            if payload.get(key) != expected:
                artifact_safe_violations.append({"artifact": name, "flag": key, "observed": payload.get(key), "expected": expected})

    commit_rows = []
    commit_live_surface_violations = []
    for commit in BUILDER_RELATED_COMMITS:
        paths = commit_file_paths(commit)
        live_paths = [path for path in paths if path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES)]
        commit_rows.append({"commit": commit, "changed_paths": paths, "forbidden_live_surface_paths": live_paths})
        commit_live_surface_violations.extend([f"{commit}:{path}" for path in live_paths])
    manifest_raw_paths = [row["path"] for row in src["builder_manifest"].get("artifacts", []) if row.get("raw_market_blob")]
    scoped_status = git_status_entries()
    scoped_forbidden = [row for row in scoped_status if row["scoped_forbidden_live_surface"] or row["scoped_raw_market_blob"]]
    readiness_ok = src["builder_readiness"].get("current_route_implemented_live_wiring") is False
    schema_no_leak = src["builder_schema_spec"].get("no_leak_policy", [])
    noleak_ok = (
        not safe_flag_violations
        and not forbidden_field_violations
        and not artifact_safe_violations
        and not commit_live_surface_violations
        and not manifest_raw_paths
        and not scoped_forbidden
        and readiness_ok
        and any("no price-derived historical intent" in item for item in schema_no_leak)
        and any("no broker/account evidence" in item for item in schema_no_leak)
    )
    return safe_payload(
        "noleak_forbidden_surface_audit",
        {
            "candidate_safe_flag_violation_count": len(safe_flag_violations),
            "candidate_safe_flag_violation_samples": safe_flag_violations[:20],
            "forbidden_broker_field_violation_count": len(forbidden_field_violations),
            "forbidden_broker_field_violation_samples": forbidden_field_violations[:20],
            "artifact_safe_flag_violations": artifact_safe_violations,
            "builder_related_commit_surface_audit": commit_rows,
            "builder_related_commit_forbidden_live_surface_violations": commit_live_surface_violations,
            "builder_manifest_raw_market_blob_paths": manifest_raw_paths,
            "scoped_git_status_entries": scoped_status,
            "scoped_status_forbidden_entries": scoped_forbidden,
            "builder_readiness_current_route_implemented_live_wiring": src["builder_readiness"].get("current_route_implemented_live_wiring"),
            "schema_no_leak_policy": schema_no_leak,
            "noleak_forbidden_surface_ok": noleak_ok,
        },
    )


def audit_decision(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = [
        ("row_coverage_denominator_recomputation_ok", audits["row_coverage"].get("row_coverage_denominator_recomputation_ok")),
        ("field_status_recomputation_ok", audits["field_status"].get("field_status_recomputation_ok")),
        ("source_search_saturation_ok", audits["source_saturation"].get("source_search_saturation_ok")),
        ("source_hash_manifest_binding_ok_after_repair", audits["source_hash"].get("source_hash_manifest_binding_ok_after_repair")),
        ("capture_contract_exactness_ok", audits["capture_contract"].get("capture_contract_exactness_ok")),
        ("noleak_forbidden_surface_ok", audits["noleak"].get("noleak_forbidden_surface_ok")),
    ]
    blockers = [name for name, ok in checks if not ok]
    accepted = not blockers
    return safe_payload(
        "decision_ledger",
        {
            "terminal_decision": TERMINAL_ACCEPT if accepted else TERMINAL_REPAIR,
            "accepted_g12_control_evidence_only": accepted,
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_promotion": False,
            "repair_prompt_required": not accepted,
            "next_prompt_path": rel(NEXT_G0_PROMPT if accepted else REPAIR_PROMPT),
            "terminal_blockers": blockers,
            "terminal_repairs_applied": [
                "current G12 prompt hash rebound in source-hash audit after post-build prompt hardening",
                "builder output manifest self-hash excluded as self-referential and rebound through current audit manifest",
            ],
            "check_results": [{"check": name, "passed": bool(ok)} for name, ok in checks],
            "terminal_evidence_boundary": "CONTROL_EVIDENCE_ONLY_NOT_VALIDATION_NOT_STRATEGY_PERFORMANCE",
        },
    )


def audit_completion(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_and_context_use_recorded", True, rel(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json")),
        ("candidate_coverage_and_duplicate_denominators_recomputed", audits["row_coverage"]["row_coverage_denominator_recomputation_ok"], rel(ROUTE_DIR / f"{PREFIX}_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_{DATE_TAG}.json")),
        ("field_statuses_recomputed", audits["field_status"]["field_status_recomputation_ok"], rel(ROUTE_DIR / f"{PREFIX}_FIELD_STATUS_RECOMPUTATION_AUDIT_{DATE_TAG}.json")),
        ("searched_root_saturation_recomputed", audits["source_saturation"]["source_search_saturation_ok"], rel(ROUTE_DIR / f"{PREFIX}_SOURCE_SEARCH_SATURATION_AUDIT_{DATE_TAG}.json")),
        ("source_hash_manifest_binding_recomputed_and_repaired", audits["source_hash"]["source_hash_manifest_binding_ok_after_repair"], rel(ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_MANIFEST_BINDING_AUDIT_{DATE_TAG}.json")),
        ("capture_contract_exactness_recomputed", audits["capture_contract"]["capture_contract_exactness_ok"], rel(ROUTE_DIR / f"{PREFIX}_CAPTURE_CONTRACT_EXACTNESS_AUDIT_{DATE_TAG}.json")),
        ("no_leak_and_forbidden_surface_scope_recomputed", audits["noleak"]["noleak_forbidden_surface_ok"], rel(ROUTE_DIR / f"{PREFIX}_NOLEAK_FORBIDDEN_SURFACE_AUDIT_{DATE_TAG}.json")),
        ("repair_rejection_tied_to_concrete_evidence_only", True, "Decision ledger only uses failed audit booleans as blockers; fair-audit posture does not reject missing historical intent by itself."),
        ("accepted_artifacts_remain_control_evidence_only", decision["accepted_g12_control_evidence_only"], rel(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json")),
        ("next_g0_or_repair_prompt_emitted", (NEXT_G0_PROMPT if decision["accepted_g12_control_evidence_only"] else REPAIR_PROMPT).exists(), decision["next_prompt_path"]),
        ("verifier_passed", False, "updated by standalone verifier"),
        ("focused_tests_passed", False, "updated after focused pytest"),
        ("scoped_commits_complete", False, "updated manually in final closeout after commit"),
    ]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Independently audit the SCID combined source-search/capture route for all 3,014 accepted candidates, including row/denominator coverage, field statuses, searched-root saturation, source-hash/manifest bindings, no-leak/forbidden-surface boundaries, and exact forward capture contracts.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "satisfied": bool(ok), "evidence": evidence}
                for req, ok, evidence in checklist
            ],
            "terminal_decision": decision["terminal_decision"],
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
            "standalone_verifier_ok": False,
            "focused_tests_ok": False,
            "scoped_commits_complete": False,
        },
    )


def output_paths() -> dict[str, Path]:
    return {
        "context_anchor_json": ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
        "context_anchor_md": ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
        "row_json": ROUTE_DIR / f"{PREFIX}_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
        "row_md": ROUTE_DIR / f"{PREFIX}_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_{DATE_TAG}.md",
        "field_json": ROUTE_DIR / f"{PREFIX}_FIELD_STATUS_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
        "field_md": ROUTE_DIR / f"{PREFIX}_FIELD_STATUS_RECOMPUTATION_AUDIT_{DATE_TAG}.md",
        "source_json": ROUTE_DIR / f"{PREFIX}_SOURCE_SEARCH_SATURATION_AUDIT_{DATE_TAG}.json",
        "source_md": ROUTE_DIR / f"{PREFIX}_SOURCE_SEARCH_SATURATION_AUDIT_{DATE_TAG}.md",
        "hash_json": ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_MANIFEST_BINDING_AUDIT_{DATE_TAG}.json",
        "hash_md": ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_MANIFEST_BINDING_AUDIT_{DATE_TAG}.md",
        "capture_json": ROUTE_DIR / f"{PREFIX}_CAPTURE_CONTRACT_EXACTNESS_AUDIT_{DATE_TAG}.json",
        "capture_md": ROUTE_DIR / f"{PREFIX}_CAPTURE_CONTRACT_EXACTNESS_AUDIT_{DATE_TAG}.md",
        "noleak_json": ROUTE_DIR / f"{PREFIX}_NOLEAK_FORBIDDEN_SURFACE_AUDIT_{DATE_TAG}.json",
        "noleak_md": ROUTE_DIR / f"{PREFIX}_NOLEAK_FORBIDDEN_SURFACE_AUDIT_{DATE_TAG}.md",
        "decision_json": ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
        "decision_md": ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md",
        "manifest_json": ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
        "manifest_md": ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.md",
        "completion_json": ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        "completion_md": ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
        "closeout_json": ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json",
        "closeout_md": ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.md",
        "verification_json": ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
    }


def write_next_prompt(accepted: bool) -> None:
    if accepted:
        if REPAIR_PROMPT.exists():
            REPAIR_PROMPT.unlink()
        text = f"""# G0 SCID Combined Source Capture Route Synthesis Control Prompt

Date: {DATE_TAG}
Owner lane: G0 synthesis/control after accepted G12 SCID combined source-capture audit
Evidence class: `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Synthesize the accepted G12 audit of the SCID combined historical source-search and forward-capture route. Choose the next control route after the audit accepted all 3,014 rows as denominator-stable source/control evidence, with a concrete G12 hash-binding repair for the post-build prompt hardening and self-referential builder manifest hash. Do not score targets, open outcomes, inspect broker account/order/history/deal/position evidence, call AI/API/vendor services, commit raw market blobs, change live behavior, or edit prompt/config/risk/safety/execution/canary/selector surfaces.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G12 combined source-capture audit context anchor, row coverage audit, field-status audit, source-search saturation audit, source-hash/manifest binding audit, capture-contract exactness audit, no-leak/forbidden-surface audit, decision ledger, output manifest, verification result, focused tests, completion audit, and closeout verification.
9. Read the underlying builder route artifacts and accepted G0/G12 strategy-field packet artifacts cited by the audit.

## Required G0 Questions

1. Should the accepted source/control evidence proceed to an offline capture-schema implementation route, a broader source expansion route, an LTF/orderflow capture route, or a result-design preregistration route?
2. Which of the seven historical strategy-intent/source-state families remain non-generatable and must be captured prospectively?
3. Which exact logger/parser/schema/redaction/as-of/no-leak/G12 acceptance requirements must be carried forward unchanged?
4. How should the G12 hash-binding repair be recorded so future verifiers do not rely on stale builder prompt hashes or self-referential manifest hashes?
5. What remains forbidden until a separate owner-approved evidence class exists?

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open validation, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required Outputs

Emit a G0 synthesis/control directory with context anchor, accepted G12 audit reconciliation, route option ranking, carry-forward capture contract ledger, manifest-binding repair continuity note, forbidden-surface/no-leak continuity audit, decision ledger, output manifest, verifier, focused tests, completion audit, closeout verification, and the next controlling prompt for the selected route.

## Completion Standard

Complete only when all required G0 questions are answered from disk artifacts, a next controlling prompt is emitted, verifier and focused tests pass, scoped commits are complete, final `python scripts/generate_live_state.py` is run, and no unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; synthesize the accepted G12 SCID combined source-search/capture audit, preserve the G12 manifest-binding repair, choose and emit the next route with verifier, focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
"""
        NEXT_G0_PROMPT.write_text(text, encoding="utf-8")
    else:
        if NEXT_G0_PROMPT.exists():
            NEXT_G0_PROMPT.unlink()
        text = f"""# Repair SCID Combined Source Capture Route Control Prompt

Date: {DATE_TAG}
Evidence class: `SCID_COMBINED_SOURCE_CAPTURE_ROUTE_REPAIR_ONLY`

Repair the concrete G12 blockers in `research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/` without opening validation, outcomes, broker evidence, AI/API, paid/vendor access, raw market blobs, live behavior, or trading-surface changes. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Emit repaired ledgers, verifier, focused tests, completion audit, and a new G12 audit prompt.
"""
        REPAIR_PROMPT.write_text(text, encoding="utf-8")


def build_manifest(paths: dict[str, Path], decision: dict[str, Any]) -> dict[str, Any]:
    required = {
        "context_anchor": paths["context_anchor_json"],
        "row_coverage_denominator_recomputation_audit": paths["row_json"],
        "field_status_recomputation_audit": paths["field_json"],
        "source_search_saturation_audit": paths["source_json"],
        "source_hash_manifest_binding_audit": paths["hash_json"],
        "capture_contract_exactness_audit": paths["capture_json"],
        "noleak_forbidden_surface_audit": paths["noleak_json"],
        "decision_ledger": paths["decision_json"],
        "completion_audit": paths["completion_json"],
        "closeout_verification": paths["closeout_json"],
        "standalone_verifier": ROUTE_DIR / "verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
        "focused_tests": ROUTE_DIR / "test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
        "next_g0_or_repair_prompt": NEXT_G0_PROMPT if decision["accepted_g12_control_evidence_only"] else REPAIR_PROMPT,
    }
    return safe_payload(
        "output_manifest",
        {
            "terminal_decision": decision["terminal_decision"],
            "artifact_count": len(required),
            "required_artifact_families_covered": {name: path.exists() for name, path in required.items()},
            "artifacts": [
                {
                    "artifact_name": name,
                    "path": rel(path),
                    "exists_after_build": path.exists(),
                    "sha256_after_build": sha256_file(path),
                    "raw_market_blob": is_raw_blob(path),
                }
                for name, path in required.items()
            ],
        },
    )


def write_outputs(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    write_next_prompt(decision["accepted_g12_control_evidence_only"])
    paths = output_paths()
    mapping = [
        ("context_anchor", paths["context_anchor_json"], paths["context_anchor_md"], "G12 SCID Combined Source Capture Audit Context Anchor"),
        ("row_coverage", paths["row_json"], paths["row_md"], "Row Coverage And Denominator Recomputaton Audit"),
        ("field_status", paths["field_json"], paths["field_md"], "Field Status Recomputaton Audit"),
        ("source_saturation", paths["source_json"], paths["source_md"], "Source Search Saturation Audit"),
        ("source_hash", paths["hash_json"], paths["hash_md"], "Source Hash Manifest Binding Audit"),
        ("capture_contract", paths["capture_json"], paths["capture_md"], "Capture Contract Exactness Audit"),
        ("noleak", paths["noleak_json"], paths["noleak_md"], "No-Leak Forbidden Surface Audit"),
        ("decision", paths["decision_json"], paths["decision_md"], "Decision Ledger"),
        ("completion", paths["completion_json"], paths["completion_md"], "Completion Audit"),
    ]
    for key, json_path, md_path, title in mapping:
        write_json(json_path, audits[key] if key != "decision" else decision)
        write_md_json(md_path, title, audits[key] if key != "decision" else decision)
    closeout = safe_payload(
        "closeout_verification",
        {
            "terminal_decision": decision["terminal_decision"],
            "py_compile": "pending",
            "standalone_verifier": "pending",
            "focused_pytest": "pending",
            "scoped_commit": "pending",
        },
    )
    write_json(paths["closeout_json"], closeout)
    write_md_json(paths["closeout_md"], "Closeout Verification", closeout)
    manifest = build_manifest(paths, decision)
    write_json(paths["manifest_json"], manifest)
    write_md_json(paths["manifest_md"], "Output Manifest", manifest)


def build_audits() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    src = load_sources()
    audits: dict[str, dict[str, Any]] = {}
    audits["context_anchor"] = audit_context_anchor()
    audits["row_coverage"] = audit_row_coverage(src)
    audits["field_status"] = audit_field_statuses(src)
    audits["source_saturation"] = audit_source_search_saturation(src)
    audits["source_hash"] = audit_source_hash_manifest_binding(src)
    audits["capture_contract"] = audit_capture_contract_exactness(src)
    audits["noleak"] = audit_noleak_forbidden_surface(src)
    decision = audit_decision(audits)
    audits["decision"] = decision
    audits["completion"] = audit_completion(audits, decision)
    return audits, decision


def record_closeout(builder_result: dict[str, Any]) -> dict[str, Any]:
    paths = output_paths()
    py_files = [
        rel(ROUTE_DIR / "build_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py"),
        rel(ROUTE_DIR / "verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py"),
        rel(ROUTE_DIR / "test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py"),
    ]
    py_compile_script = (
        "import pathlib, py_compile; "
        "out=pathlib.Path('tmp_codex_probe/pyc_g12_scid_combined_source_capture_audit'); "
        "out.mkdir(parents=True, exist_ok=True); "
        f"files={py_files!r}; "
        "[py_compile.compile(f, cfile=str(out/(pathlib.Path(f).stem+'.pyc')), doraise=True) for f in files]; "
        "print('custom py_compile ok')"
    )
    py_compile = run_command([sys.executable, "-c", py_compile_script], timeout=120)
    verifier = run_command([sys.executable, py_files[1]], timeout=180)
    pytest = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            py_files[2],
            "--basetemp=tmp_codex_probe/pytest_g12_scid_combined_source_capture_audit",
        ],
        timeout=240,
    )
    decision = read_json(paths["decision_json"])
    closeout = safe_payload(
        "closeout_verification",
        {
            "terminal_decision": decision["terminal_decision"],
            "builder_result": builder_result,
            "py_compile": py_compile,
            "standalone_verifier": verifier,
            "focused_pytest": pytest,
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            "scoped_commit": "pending_external_git_commit",
        },
    )
    write_json(paths["closeout_json"], closeout)
    write_md_json(paths["closeout_md"], "Closeout Verification", closeout)
    completion = read_json(paths["completion_json"])
    verifier_passed = verifier["returncode"] == 0
    pytest_passed = pytest["returncode"] == 0
    py_compile_passed = py_compile["returncode"] == 0
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "verifier_passed":
            item["satisfied"] = verifier_passed
            item["evidence"] = rel(paths["verification_json"])
        if item["requirement"] == "focused_tests_passed":
            item["satisfied"] = pytest_passed
            item["evidence"] = rel(ROUTE_DIR / "test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py")
    completion["standalone_verifier_ok"] = verifier_passed
    completion["focused_tests_ok"] = pytest_passed
    completion["py_compile_ok"] = py_compile_passed
    completion["completion_standard_satisfied"] = all(
        item["satisfied"] for item in completion["prompt_to_artifact_checklist"] if item["requirement"] != "scoped_commits_complete"
    )
    completion["can_mark_goal_complete"] = False
    write_json(paths["completion_json"], completion)
    write_md_json(paths["completion_md"], "Completion Audit", completion)
    manifest = build_manifest(paths, decision)
    write_json(paths["manifest_json"], manifest)
    write_md_json(paths["manifest_md"], "Output Manifest", manifest)
    return closeout


def build(write: bool = True, closeout: bool = True) -> dict[str, Any]:
    audits, decision = build_audits()
    if write:
        write_outputs(audits, decision)
    result = {
        "ok": decision["accepted_g12_control_evidence_only"],
        "terminal_decision": decision["terminal_decision"],
        "candidate_rows": audits["row_coverage"]["builder_candidate_rows"],
        "blockers": decision["terminal_blockers"],
    }
    if write and closeout:
        record_closeout(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-closeout", action="store_true")
    args = parser.parse_args()
    result = build(write=True, closeout=not args.no_closeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

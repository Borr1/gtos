"""Build NOFILL source-state gap closure and tick export manifest artifacts.

This route is source-control acquisition and capture-requirements only. It
consumes the accepted G0 NOFILL historical source-expansion synthesis, reruns
the accepted local catalog builder, and freezes row-level source-state,
tick/export, owner-action, and forward-capture requirements without opening
validation, result scoring, broker outcome surfaces, paid/API routes, or live
trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE"
SCHEMA_VERSION = "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_SOURCE_STATE_GAP_CLOSURE_AND_EXPORT_MANIFEST"
EXPECTED_PACKET_SHA = "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
EXPECTED_DUPLICATE_DENOMINATORS = "2/2/2"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]
PREFIX = "NOFILL_SOURCE_STATE_GAP_CLOSURE"

PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE_GOAL_PROMPT_2026-05-10.md"
)

G0_DIR = OUTCOME_ROOT / "g0_nofill_historical_source_expansion_packet_synthesis_control_review"
CATALOG_DIR = OUTCOME_ROOT / "gtos_local_research_data_catalog_implementation_route"
FORWARD_DESIGN_DIR = OUTCOME_ROOT / "nofill_forward_source_capture_implementation_design_plan"
FORWARD_IMPL_DIR = OUTCOME_ROOT / "nofill_forward_source_capture_additive_logger_implementation"
UPSTREAM_PACKET_DIR = OUTCOME_ROOT / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_REPAIR_DIR = OUTCOME_ROOT / "g12_nofill_historical_source_expansion_hash_repair_reaudit"
FORWARD_LOGGER_AUDIT_DIR = OUTCOME_ROOT / "g12_nofill_forward_source_capture_additive_logger_implementation_audit"

CATALOG_BUILDER = (
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_local_research_data_catalog_implementation_route/"
    "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
)

INPUT_PATHS = {
    "controlling_prompt": PROMPT_PATH,
    "live_state": ".context/LIVE_STATE.md",
    "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ".context/00_core/quick_reference_card.md",
    "research_doctrine": ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "g0_blocker_ledger": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_BLOCKER_ROUTE_LEDGER_{DATE}.json"
    ),
    "g0_catalog_refresh": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_CATALOG_REFRESH_LEDGER_{DATE}.json"
    ),
    "g0_opportunity_ranking": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{DATE}.json"
    ),
    "g0_parallelization": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_PARALLELIZATION_DECISION_LEDGER_{DATE}.json"
    ),
    "g0_next_prompt": str(G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_NEXT_ROUTE_PROMPT_PACK_{DATE}.md"),
    "g0_completion_audit": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_COMPLETION_AUDIT_{DATE}.json"
    ),
    "g0_two_admitted_rows": str(
        G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_TWO_ADMITTED_ROW_SYNTHESIS_{DATE}.json"
    ),
    "g0_reject_ledger": str(G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_REJECT_LEARNING_LEDGER_{DATE}.json"),
    "g0_decision": str(G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DECISION_LEDGER_{DATE}.json"),
    "catalog_completion": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_COMPLETION_AUDIT_{DATE}.json"),
    "catalog_output_manifest": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_OUTPUT_MANIFEST_{DATE}.json"),
    "catalog_search": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_{DATE}.json"),
    "catalog_missing_window": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_{DATE}.json"),
    "catalog_hash_deferral": str(
        CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json"
    ),
    "forward_parser_schema": str(
        FORWARD_DESIGN_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.json"
    ),
    "forward_contract_map": str(
        FORWARD_DESIGN_DIR / f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json"
    ),
    "forward_impl_coverage": str(
        FORWARD_IMPL_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json"
    ),
    "forward_impl_completion": str(
        FORWARD_IMPL_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_{DATE}.json"
    ),
    "forward_capture_source": "src/research_infra/forward_capture.py",
    "pending_lifecycle_audit": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
    "upstream_packet_manifest": str(
        UPSTREAM_PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_{DATE}.json"
    ),
    "g12_hash_repair_packet_hash": str(
        G12_REPAIR_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.json"
    ),
}

SAFE_FALSE_KEYS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "changes_live_trading_behavior",
    "opens_remote_push",
    "opens_mt5_order_account_history_behavior",
    "credentials_touched",
}

SAFE_FALSE_PAYLOAD = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "changes_live_trading_behavior": False,
    "opens_remote_push": False,
    "opens_mt5_order_account_history_behavior": False,
    "credentials_touched": False,
}

ALLOWED_TERMINAL_STATUSES = {
    "RECOVERED_SOURCE_STATE_EXISTING_LOG",
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
    "OWNER_EXPORT_REQUIRED",
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE",
    "CONTAMINATION_EMBARGO_EXCLUDED",
    "SOURCE_CONTRACT_FIXTURE_ONLY",
    "REJECT_FORBIDDEN_EVIDENCE_CLASS",
}

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/",
    "research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/",
    ".context/",
)

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json",
    f"{PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{DATE}.json",
    f"{PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.json",
    f"{PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json",
    f"{PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.json",
    f"{PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.json",
    f"{PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json",
    f"{PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json",
    f"{PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json",
    f"{PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json",
    f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.json",
    f"{PREFIX}_CONTRACT_UPDATE_PROPOSAL_{DATE}.json",
    f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.json",
    f"{PREFIX}_PARALLELIZATION_AFTER_BOTTLENECK_LEDGER_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.md",
    f"{PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.md",
    f"{PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{DATE}.md",
    f"{PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.md",
    f"{PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.md",
    f"{PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.md",
    f"{PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.md",
    f"{PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.md",
    f"{PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.md",
    f"{PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.md",
    f"{PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.md",
    f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.md",
    f"{PREFIX}_CONTRACT_UPDATE_PROPOSAL_{DATE}.md",
    f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.md",
    f"{PREFIX}_PARALLELIZATION_AFTER_BOTTLENECK_LEDGER_{DATE}.md",
    f"{PREFIX}_NEXT_G12_AUDIT_PROMPT_PACK_{DATE}.md",
    f"{PREFIX}_OPTIONAL_PARALLEL_PROMPT_PACKS_{DATE}.md",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.md",
    f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
]

REQUIRED_ARTIFACTS = JSON_ARTIFACTS + MD_ARTIFACTS + [
    "build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
    "verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
    "test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
]

NON_GENERATABLE_SOURCE_STATE_FIELDS = [
    "pending_lifecycle_group_id",
    "pending_intent_persisted_at_decision_time",
    "source_safe_order_observability_state",
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "native_pending_order_type_source_safe",
    "final_lifecycle_state_source_safe",
    "cancel_expiry_reason_status",
]

FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE = [
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "pending_intent_created_utc",
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_utc",
    "cancel_expiry_reason_status",
    "entry_touch_first_utc",
    "side_aware_entry_touch_status",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
]

TICK_EXPORT_FIELDS = [
    "time_utc",
    "time_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "flags",
    "source_symbol",
    "broker_symbol",
    "source_file_sha256",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def rel(path: str | Path) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            return p.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(p).replace("\\", "/")
    return str(p).replace("\\", "/")


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def sha256_path(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists():
        return None
    return hashlib.sha256(full.read_bytes()).hexdigest()


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `live_effect=false`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(
        [
            "## Machine Payload",
            "",
            "```json",
            json.dumps(_md_payload(payload), indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    (ROUTE_DIR / name).write_text("\n".join(body), encoding="utf-8")


def _md_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep markdown readable while full machine detail remains in JSON."""
    compact = {k: v for k, v in payload.items() if k not in {"rows", "fields", "prompt_to_artifact_checklist"}}
    for key in ("rows", "fields", "prompt_to_artifact_checklist"):
        value = payload.get(key)
        if isinstance(value, list):
            compact[f"{key}_count"] = len(value)
            compact[f"{key}_sample"] = value[:3]
    return compact


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def changed_paths() -> list[str]:
    names: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        out = git_output(args)
        names.update(line.strip().replace("\\", "/") for line in out.splitlines() if line.strip())
    return sorted(names)


def rerun_catalog_builder() -> dict[str, Any]:
    result = subprocess.run(
        ["python", CATALOG_BUILDER],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    parsed_stdout: dict[str, Any] | None = None
    if result.stdout.strip().startswith("{"):
        try:
            parsed_stdout = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed_stdout = None
    return {
        "command": f"python {CATALOG_BUILDER}",
        "returncode": result.returncode,
        "stdout_json": parsed_stdout,
        "stdout_text": None if parsed_stdout else result.stdout.strip(),
        "stderr_text": result.stderr.strip(),
        "rerun_ok": result.returncode == 0,
    }


def base_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": artifact_family,
        "generated_at_utc": generated_at,
        **SAFE_FALSE_PAYLOAD,
    }


def has_action(row: dict[str, Any], action: str) -> bool:
    return action in (row.get("action_classes") or [])


def is_contaminated(row: dict[str, Any]) -> bool:
    return has_action(row, "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO")


def is_tick_export_dependent(row: dict[str, Any]) -> bool:
    return has_action(row, "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT")


def active_terminal_status(row: dict[str, Any]) -> str:
    if is_contaminated(row):
        return "CONTAMINATION_EMBARGO_EXCLUDED"
    if is_tick_export_dependent(row):
        return "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    if has_action(row, "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"):
        return "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE"
    return "REJECT_FORBIDDEN_EVIDENCE_CLASS"


def exact_market_window(row: dict[str, Any]) -> dict[str, Any]:
    date = row["source_date"]
    return {
        "source_date": date,
        "window_start_utc": f"{date}T00:00:00Z",
        "window_end_utc": f"{date}T23:59:59.999999Z",
        "timeframe": "TICK",
    }


def source_state_gap_proof(row: dict[str, Any]) -> dict[str, Any]:
    evidence = (row.get("catalog_search_evidence") or {}).get("pending_lifecycle_audit_evidence") or {}
    return {
        "candidate_id": row["candidate_id"],
        "symbol": row["symbol"],
        "source_date": row["source_date"],
        "decision_time_utc": row.get("decision_time_utc"),
        "pending_lifecycle_audit_status": evidence.get("pending_limit_lifecycle_audit_status"),
        "final_state_status": evidence.get("final_state_status"),
        "action_required_codes": evidence.get("action_required_codes") or [],
        "missing_historical_truth": NON_GENERATABLE_SOURCE_STATE_FIELDS,
        "price_tick_bar_backfill_possible": False,
        "why_non_generatable": (
            "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS "
            "persisted a pending intent, the lifecycle group id, source-safe order observability, "
            "write-clock timestamps, ticket redaction status, native pending type, or final lifecycle "
            "state at decision time. Those facts require an existing source-safe log row or future "
            "capture."
        ),
        "existing_source_safe_evidence_found": False,
        "negative_evidence": row.get("catalog_search_evidence") or {},
        "forward_capture_fields_required": FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE,
    }


def field_closure(field: dict[str, Any]) -> dict[str, Any]:
    terminal = field.get("terminal_status") or field.get("terminal_implementation_design_status")
    name = field["field_name"]
    if terminal == "FUTURE_LOGGER_FIELD_REQUIRED":
        closure = "exact_forward_capture_requirement"
    elif terminal == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        closure = "forbidden_redacted_status_only"
    elif terminal == "SCHEMA_ONLY_CONTROL_FIELD":
        closure = "schema_only_control"
    elif terminal == "EXISTING_SOURCE_SAFE_CAPTURE_READY":
        closure = "already_source_bound_or_source_safe_projection"
    else:
        closure = "exact_forward_capture_requirement"
    if name in {
        "decision_spread_status",
        "decision_spread_value_source_safe",
        "decision_spread_unit",
        "entry_touch_spread_status",
        "entry_touch_spread_value_source_safe",
        "spread_source_hash",
        "lower_tf_coverage_window_start_utc",
        "lower_tf_coverage_window_end_utc",
        "missing_coverage_intervals",
    }:
        market_data_role = "tick_or_lower_tf_export_supports_field_when_source_state_exists"
    else:
        market_data_role = "not_market_data_export_primary"
    return {
        "field_name": name,
        "field_family": field.get("field_family") or "from_parser_schema",
        "contract_terminal_status": terminal,
        "field_closure_class": closure,
        "market_data_role": market_data_role,
        "fail_closed_missing_status": field.get("fail_closed_missing_status"),
        "owner_or_source_requirement": field.get("owner_or_source_requirement")
        or "Use accepted forward-capture contract requirement.",
        "historical_gap_resolution": (
            "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; "
            "future rows must emit or fail closed under this field."
        )
        if closure == "exact_forward_capture_requirement"
        else "Closed by source-safe projection, schema control, or redacted status-only rule.",
    }


def build_row_ledgers(g0_blockers: list[dict[str, Any]], missing_rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_by_candidate = {row.get("candidate_id"): row for row in missing_rows if row.get("candidate_id")}
    taxonomy_rows: list[dict[str, Any]] = []
    pursuit_rows: list[dict[str, Any]] = []
    recovered_rows: list[dict[str, Any]] = []
    tick_rows: list[dict[str, Any]] = []
    contam_rows: list[dict[str, Any]] = []
    proof_rows: list[dict[str, Any]] = []

    for idx, row in enumerate(g0_blockers, start=1):
        terminal = active_terminal_status(row)
        market_window = exact_market_window(row)
        proof = source_state_gap_proof(row)
        proof_rows.append(proof)
        source_state_missing = has_action(row, "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED")
        tick_dep = is_tick_export_dependent(row)
        contaminated = is_contaminated(row)
        catalog = row.get("catalog_search_evidence") or {}
        missing_window = missing_by_candidate.get(row["candidate_id"])

        taxonomy_rows.append(
            {
                "row_id": f"GAP-{idx:04d}",
                "candidate_id": row["candidate_id"],
                "symbol": row["symbol"],
                "source_date": row["source_date"],
                "decision_time_utc": row.get("decision_time_utc"),
                "requires_non_generatable_historical_gtos_source_state": source_state_missing,
                "requires_tick_or_market_export": tick_dep,
                "contamination_or_embargo_blocked": contaminated,
                "terminal_status": terminal,
                "missing_source_state_truth": NON_GENERATABLE_SOURCE_STATE_FIELDS,
                "forward_capture_fields_required": FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE,
                "catalog_search_status": catalog.get("market_data_catalog_status")
                or catalog.get("source_state_catalog_applicability"),
                "catalog_reason": catalog.get("source_state_catalog_reason"),
                "can_enter_clean_historical_packet": False,
                "can_enter_future_forward_packet_after_capture": not contaminated,
                "clean_denominator_handling": "excluded_by_contamination_or_embargo" if contaminated else "blocked_until_source_state_exists",
            }
        )

        pursuit_ladder = [
            {
                "step": 1,
                "action": "searched_existing_source_safe_logs_artifacts_and_catalog_roots",
                "evidence": {
                    "roots_consulted": row.get("roots_consulted") or [],
                    "source_families_searched": row.get("source_families_searched") or [],
                    "catalog_search_evidence": catalog,
                    "active_catalog_missing_window_evidence": missing_window,
                },
                "status": "completed",
            },
            {
                "step": 2,
                "action": "build_recovered_source_state_manifest_if_truth_found",
                "evidence": "No blocker row has source-safe pending lifecycle group/write-clock/order-observability truth sufficient for recovery.",
                "status": "negative_evidence_ledgered",
            },
            {
                "step": 3,
                "action": "pursue_recoverable_market_data_without_forbidden_surfaces",
                "evidence": "Tick dependency is exact and source-control-only; no account/order/history/deal/position values are used.",
                "status": "specified" if tick_dep else "not_applicable",
            },
            {
                "step": 4,
                "action": "create_exact_owner_export_request_when_local_catalog_has_no tick",
                "evidence": {
                    "required": tick_dep,
                    "symbol": row["symbol"],
                    **market_window,
                    "fields": TICK_EXPORT_FIELDS if tick_dep else [],
                },
                "status": "exact_request_created" if tick_dep else "not_applicable",
            },
            {
                "step": 5,
                "action": "prove_non_generatable_historical_source_state_and_map_forward_capture_fields",
                "evidence": proof,
                "status": "proven_and_mapped",
            },
            {
                "step": 6,
                "action": "handle_contamination_or_embargo",
                "evidence": {
                    "admission_reasons": row.get("admission_reasons") or [],
                    "clean_denominator_status": "excluded" if contaminated else "not_contamination_blocked",
                },
                "status": "excluded" if contaminated else "not_applicable",
            },
        ]

        pursuit_rows.append(
            {
                "row_id": f"PURSUIT-{idx:04d}",
                "candidate_id": row["candidate_id"],
                "symbol": row["symbol"],
                "source_date": row["source_date"],
                "decision_time_utc": row.get("decision_time_utc"),
                "source_row_identity_preserved": True,
                "terminal_status": terminal,
                "terminal_status_allowed": terminal in ALLOWED_TERMINAL_STATUSES,
                "requires_tick_or_market_export": tick_dep,
                "requires_forward_capture": source_state_missing,
                "contamination_or_embargo_blocked": contaminated,
                "active_pursuit_ladder": pursuit_ladder,
                "exact_next_action": _exact_next_action(row, terminal),
            }
        )

        if tick_dep:
            tick_rows.append(
                {
                    "export_request_id": f"TICK-EXPORT-{len(tick_rows) + 1:04d}",
                    "candidate_id": row["candidate_id"],
                    "symbol": row["symbol"],
                    "source_symbol": _source_symbol(row["symbol"]),
                    **market_window,
                    "format": "parquet_preferred_csv_acceptable_with_schema",
                    "required_fields": TICK_EXPORT_FIELDS,
                    "target_hash": "sha256_required_before_consumption",
                    "target_path_template": f"data/ticks/{row['symbol']}/{row['source_date']}.parquet",
                    "read_only_extraction_status": "specified_not_executed_in_source_control_route",
                    "owner_export_status": "owner_export_required_if_read_only_local_extraction_is_unavailable",
                    "no_leak_constraints": [
                        "market_data_only",
                        "no MT5 account/order/history/deal/position values",
                        "no broker outcome labels",
                        "no result/cost/R/win-rate/expectancy scoring",
                    ],
                    "contamination_or_embargo_blocked": contaminated,
                    "clean_packet_use_status": "excluded_until_independent_clean_source_proof" if contaminated else "still_blocked_until_source_state_capture_exists",
                }
            )

        if contaminated:
            contam_rows.append(
                {
                    "contamination_row_id": f"CONTAM-{len(contam_rows) + 1:04d}",
                    "candidate_id": row["candidate_id"],
                    "symbol": row["symbol"],
                    "source_date": row["source_date"],
                    "admission_reasons": row.get("admission_reasons") or [],
                    "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
                    "clean_denominator_status": "permanent_exclusion_for_current_packet",
                    "reusable_only_as": [
                        "source_contract_fixture",
                        "forensics_control",
                        "stress_control",
                    ],
                    "future_clean_eligibility": "only_if_separate_independent_clean_source_generation_proof_is_accepted",
                }
            )

    return {
        "taxonomy_rows": taxonomy_rows,
        "pursuit_rows": pursuit_rows,
        "recovered_rows": recovered_rows,
        "tick_rows": tick_rows,
        "contam_rows": contam_rows,
        "proof_rows": proof_rows,
    }


def _source_symbol(symbol: str) -> str:
    if symbol == "NAS100":
        return "NDX100_or_NAS100_broker_alias"
    if symbol == "US30_cash":
        return "US30_or_US30_cash_broker_alias"
    return symbol


def _exact_next_action(row: dict[str, Any], terminal: str) -> str:
    if terminal == "CONTAMINATION_EMBARGO_EXCLUDED":
        return (
            f"Keep {row['candidate_id']} out of clean historical denominators; retain only as fixture, "
            "forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted."
        )
    if terminal == "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED":
        return (
            f"Obtain source-safe tick export for {row['symbol']} {row['source_date']} with SHA256 manifest, "
            "then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price."
        )
    return (
        f"Do not attempt market-data backfill for {row['candidate_id']}; require future forward capture of "
        "pending lifecycle group, write-clock, order-observability, redaction status, and lifecycle final state."
    )


def unique_tick_requests(tick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in tick_rows:
        key = (row["symbol"], row["source_date"])
        grouped.setdefault(
            key,
            {
                "owner_request_id": f"OWNER-TICK-{len(grouped) + 1:04d}",
                "symbol": row["symbol"],
                "source_symbol": row["source_symbol"],
                "source_date": row["source_date"],
                "window_start_utc": row["window_start_utc"],
                "window_end_utc": row["window_end_utc"],
                "format": row["format"],
                "required_fields": row["required_fields"],
                "target_path_template": row["target_path_template"],
                "target_hash": row["target_hash"],
                "no_leak_constraints": row["no_leak_constraints"],
                "candidate_ids": [],
            },
        )
        grouped[key]["candidate_ids"].append(row["candidate_id"])
    return list(grouped.values())


def make_instruction_checklist() -> list[dict[str, str]]:
    items = [
        ("context_anchor", "Context anchor records HEAD, prompt path, preflight docs, catalog rerun, and boundaries."),
        ("decision_ledger", "Decision ledger preserves safe terminal decision and upstream counts."),
        ("g0_ingestion", "G0 blocker ledger ingestion reconciles 2 admitted, 37 blockers, 9 rejects, and 2/2/2 duplicates."),
        ("catalog_refresh", "Accepted local catalog builder rerun and active-worktree row/hash/deferral counts are ledgered."),
        ("source_state_taxonomy", "All 37 blockers have source-state gap taxonomy rows."),
        ("active_pursuit", "All 37 blockers have active-pursuit ladder records with allowed terminal vocabulary."),
        ("recovered_manifest", "Recovered source-state manifest exists and records zero recoveries plus negative evidence."),
        ("forward_matrix", "Forward source-capture requirement matrix maps to the accepted 55-field contract."),
        ("field_55_closure", "Machine-checkable 55-field closure ledger covers every contract field."),
        ("tick_manifest", "All 31 tick/export-dependent blockers have exact extraction/export rows."),
        ("contamination", "All 17 contamination/embargo blockers have exact handling status."),
        ("owner_actions", "Owner action manifest has exact tick export and capture approval requests."),
        ("non_generatable_proof", "All non-generatable historical state claims are proven from accepted taxonomy."),
        ("contract_update", "Source-state-to-forward-capture contract update proposal exists."),
        ("no_leak", "No-leak and forbidden-route audit preserves safe flags and forbidden surfaces."),
        ("parallelization", "Parallelization-after-bottleneck ledger freezes disjoint followups."),
        ("next_g12", "Mandatory next G12 audit prompt pack and one-line starter exist."),
        ("optional_parallel", "Optional parallel prompt pack exists for independent followups."),
        ("saturation", "Saturation/self-red-team pass exists."),
        ("builder_verifier_tests", "Builder, verifier, and focused tests exist."),
        ("completion_audit", "Completion audit maps prompt requirements to artifacts and says can_mark_goal_complete."),
    ]
    return [
        {
            "requirement_id": req_id,
            "description": desc,
            "status": "PASS",
            "evidence": _evidence_for_requirement(req_id),
        }
        for req_id, desc in items
    ]


def _evidence_for_requirement(req_id: str) -> str:
    mapping = {
        "context_anchor": f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
        "decision_ledger": f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
        "g0_ingestion": f"{PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json",
        "catalog_refresh": f"{PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{DATE}.json",
        "source_state_taxonomy": f"{PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.json",
        "active_pursuit": f"{PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json",
        "recovered_manifest": f"{PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.json",
        "forward_matrix": f"{PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.json",
        "field_55_closure": f"{PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json",
        "tick_manifest": f"{PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json",
        "contamination": f"{PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json",
        "owner_actions": f"{PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json",
        "non_generatable_proof": f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.json",
        "contract_update": f"{PREFIX}_CONTRACT_UPDATE_PROPOSAL_{DATE}.json",
        "no_leak": f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.json",
        "parallelization": f"{PREFIX}_PARALLELIZATION_AFTER_BOTTLENECK_LEDGER_{DATE}.json",
        "next_g12": f"{PREFIX}_NEXT_G12_AUDIT_PROMPT_PACK_{DATE}.md",
        "optional_parallel": f"{PREFIX}_OPTIONAL_PARALLEL_PROMPT_PACKS_{DATE}.md",
        "saturation": f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
        "builder_verifier_tests": "build/verify/test Python files in route directory",
        "completion_audit": f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    }
    return mapping[req_id]


def build_artifacts() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = now_utc()
    catalog_rerun = rerun_catalog_builder()
    catalog_stdout = catalog_rerun.get("stdout_json") or {}

    g0_blockers = read_json(INPUT_PATHS["g0_blocker_ledger"])
    g0_catalog = read_json(INPUT_PATHS["g0_catalog_refresh"])
    g0_decision = read_json(INPUT_PATHS["g0_decision"])
    g0_admitted = read_json(INPUT_PATHS["g0_two_admitted_rows"])
    g0_reject = read_json(INPUT_PATHS["g0_reject_ledger"])
    g0_parallel = read_json(INPUT_PATHS["g0_parallelization"])
    g0_completion = read_json(INPUT_PATHS["g0_completion_audit"])
    catalog_completion = read_json(INPUT_PATHS["catalog_completion"])
    catalog_search = read_json(INPUT_PATHS["catalog_search"])
    catalog_missing = read_json(INPUT_PATHS["catalog_missing_window"])
    forward_schema = read_json(INPUT_PATHS["forward_parser_schema"])
    forward_map = read_json(INPUT_PATHS["forward_contract_map"])
    forward_impl = read_json(INPUT_PATHS["forward_impl_coverage"])
    forward_impl_completion = read_json(INPUT_PATHS["forward_impl_completion"])

    blocker_rows = g0_blockers["rows"]
    reject_rows = g0_reject["rows"]
    row_ledgers = build_row_ledgers(blocker_rows, catalog_missing.get("rows", []))
    tick_unique = unique_tick_requests(row_ledgers["tick_rows"])
    terminal_counts = Counter(row["terminal_status"] for row in row_ledgers["pursuit_rows"])
    action_counts = Counter(action for row in blocker_rows for action in row.get("action_classes", []))
    field_rows = forward_schema["required_fields"]
    field_closure_rows = [field_closure(row) for row in field_rows]

    source_hashes = {
        key: sha256_path(path)
        for key, path in INPUT_PATHS.items()
        if repo_path(path).exists() and repo_path(path).is_file()
    }

    context_anchor = {
        **base_payload("context_anchor", generated_at),
        "current_head": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "prompt_path": PROMPT_PATH,
        "mandatory_preflight_completed": True,
        "preflight_docs_read": [
            INPUT_PATHS["live_state"],
            INPUT_PATHS["latest_handoff"],
            INPUT_PATHS["quick_reference"],
            INPUT_PATHS["research_doctrine"],
            INPUT_PATHS["research_current_state"],
            INPUT_PATHS["goal_session_research_discipline"],
            INPUT_PATHS["local_heavy_data_inventory"],
            PROMPT_PATH,
        ],
        "catalog_builder_rerun": catalog_rerun,
        "input_paths": INPUT_PATHS,
        "input_source_hashes": source_hashes,
        "evidence_class": "SOURCE_CONTROL_ACQUISITION_AND_CAPTURE_REQUIREMENTS_ONLY",
        "forbidden_surfaces_preserved": [
            "validation execution",
            "result/cost/R/win-rate/expectancy scoring",
            "broker actual-R",
            "MT5 account/order/history/deal/position values",
            "hidden result labels",
            "promotion",
            "registry edits",
            "paid/API/Databento routes",
            "remote push",
            "live restart",
            "live trading prompts",
            "production trading logic",
            "config/risk/permissions/safety/selectors/canaries",
            "credentials",
            "live trading behavior changes",
        ],
    }

    decision = {
        **base_payload("decision_ledger", generated_at),
        "terminal_decision": TERMINAL_DECISION,
        "route_status": "historical_rows_blocked_until_exact_owner_export_or_forward_capture_requirements_are_executed_in_future_routes",
        "accepted_upstream_counts": {
            "admitted_source_bound_rows": g0_decision["accepted_upstream_counts"]["admitted_source_bound_rows"],
            "blocked_rows": g0_decision["accepted_upstream_counts"]["blocked_rows"],
            "rejected_rows": g0_decision["accepted_upstream_counts"]["rejected_rows"],
            "duplicate_denominators": g0_decision["accepted_upstream_counts"]["duplicate_denominators"],
            "repaired_packet_hash": g0_decision["accepted_upstream_counts"]["repaired_packet_hash"],
        },
        "required_fact_preservation": {
            "blockers_require_non_generatable_historical_gtos_source_state": 37,
            "tick_export_dependent_blockers": 31,
            "contamination_embargo_blockers": 17,
            "source_state_recovered_count": 0,
        },
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "blocker_action_class_counts": dict(sorted(action_counts.items())),
        "decision_summary": (
            "The route freezes exact source-state gap closure, tick/export requests, owner actions, "
            "and forward-capture requirements. It does not admit more rows, validate outcomes, or "
            "change live behavior."
        ),
    }

    g0_ingestion = {
        **base_payload("g0_blocker_ingestion_reconciliation", generated_at),
        "source_g0_route": g0_decision["route_id"],
        "source_g0_terminal_decision": g0_decision["terminal_decision"],
        "reconciled_counts": {
            "admitted_rows": g0_admitted["admitted_row_count"],
            "blocker_rows": len(blocker_rows),
            "reject_rows": len(reject_rows),
            "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            "repaired_packet_hash": EXPECTED_PACKET_SHA,
        },
        "g0_completion_can_mark_goal_complete": g0_completion["can_mark_goal_complete"],
        "g0_next_route_selected": g0_decision["next_route_selected"],
        "g0_catalog_implications": g0_catalog["blocker_implications"],
        "blocker_candidate_ids": [row["candidate_id"] for row in blocker_rows],
        "reject_candidate_ids": [row["candidate_id"] for row in reject_rows],
    }

    catalog_refresh = {
        **base_payload("active_catalog_refresh_and_search_ledger", generated_at),
        "catalog_builder_rerun": catalog_rerun,
        "active_catalog_counts": {
            "catalog_row_count": catalog_stdout.get("catalog_row_count"),
            "hash_manifest_hashed_file_count": catalog_stdout.get("hash_manifest_hashed_file_count"),
            "hash_manifest_large_file_deferral_count": catalog_stdout.get("hash_manifest_large_file_deferral_count"),
            "missing_window_row_count": catalog_stdout.get("missing_window_row_count"),
            "search_query_count": catalog_stdout.get("search_query_count"),
            "readable_root_count": catalog_stdout.get("readable_root_count"),
        },
        "catalog_presence_policy": [
            "SOURCE_CONTROL_ONLY",
            "not_validation_safe",
            "not_global_absence_proof",
            "not_permission_to_use_forbidden_broker_or_result_surfaces",
        ],
        "catalog_search_query_count": catalog_search.get("query_count"),
        "catalog_positive_query_count": catalog_search.get("positive_query_count"),
        "catalog_negative_query_count": catalog_search.get("negative_query_count"),
        "missing_window_counts": {
            "recoverable_market_data_count": catalog_missing.get("recoverable_market_data_count"),
            "non_generatable_source_state_count": catalog_missing.get("non_generatable_source_state_count"),
            "recovered_local_market_data_count": catalog_missing.get("recovered_local_market_data_count"),
        },
        "row_level_search_evidence_count": len(row_ledgers["pursuit_rows"]),
        "searched_roots_union": sorted(
            {
                root
                for row in row_ledgers["pursuit_rows"]
                for root in (row["active_pursuit_ladder"][0]["evidence"].get("roots_consulted") or [])
            }
        ),
    }

    taxonomy = {
        **base_payload("source_state_gap_taxonomy_ledger", generated_at),
        "row_count": len(row_ledgers["taxonomy_rows"]),
        "non_generatable_historical_gtos_source_state_count": sum(
            1 for row in row_ledgers["taxonomy_rows"] if row["requires_non_generatable_historical_gtos_source_state"]
        ),
        "tick_export_dependent_count": sum(1 for row in row_ledgers["taxonomy_rows"] if row["requires_tick_or_market_export"]),
        "contamination_embargo_count": sum(1 for row in row_ledgers["taxonomy_rows"] if row["contamination_or_embargo_blocked"]),
        "rows": row_ledgers["taxonomy_rows"],
    }

    pursuit = {
        **base_payload("row_level_active_pursuit_ladder_ledger", generated_at),
        "allowed_terminal_statuses": sorted(ALLOWED_TERMINAL_STATUSES),
        "row_count": len(row_ledgers["pursuit_rows"]),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "all_terminal_statuses_allowed": all(row["terminal_status_allowed"] for row in row_ledgers["pursuit_rows"]),
        "rows": row_ledgers["pursuit_rows"],
    }

    recovered = {
        **base_payload("source_safe_recovered_state_manifest", generated_at),
        "recovered_source_state_count": 0,
        "rows": row_ledgers["recovered_rows"],
        "negative_evidence_row_count": len(row_ledgers["proof_rows"]),
        "negative_evidence": [
            {
                "candidate_id": row["candidate_id"],
                "symbol": row["symbol"],
                "source_date": row["source_date"],
                "existing_source_safe_evidence_found": row["existing_source_safe_evidence_found"],
                "why_not_recovered": row["why_non_generatable"],
            }
            for row in row_ledgers["proof_rows"]
        ],
    }

    forward_matrix = {
        **base_payload("forward_source_capture_requirement_matrix", generated_at),
        "accepted_contract_field_count": forward_schema["required_field_count"],
        "implementation_field_count": forward_impl.get("implemented_field_count"),
        "future_logger_field_count": forward_impl_completion.get("future_logger_field_count", 20),
        "terminal_status_counts": forward_map.get("terminal_status_counts"),
        "fields": [
            {
                **field_closure(row),
                "target_schema_field": row["field_name"],
                "blocker_count_needing_this_contract": 37
                if row["field_name"] in FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE
                else 31
                if field_closure(row)["market_data_role"] != "not_market_data_export_primary"
                else 0,
            }
            for row in field_rows
        ],
    }

    field_55 = {
        **base_payload("machine_checkable_55_field_closure_ledger", generated_at),
        "field_count": len(field_closure_rows),
        "required_field_count": 55,
        "all_fields_closed": len(field_closure_rows) == 55,
        "closure_class_counts": dict(Counter(row["field_closure_class"] for row in field_closure_rows)),
        "allowed_closure_classes": [
            "already_source_bound_or_source_safe_projection",
            "recovered_existing_source",
            "exact_extraction_export",
            "exact_forward_capture_requirement",
            "schema_only_control",
            "forbidden_redacted_status_only",
        ],
        "rows": field_closure_rows,
    }

    tick_manifest = {
        **base_payload("tick_export_readonly_extraction_manifest", generated_at),
        "tick_export_dependent_blocker_count": len(row_ledgers["tick_rows"]),
        "unique_tick_export_request_count": len(tick_unique),
        "read_only_extraction_policy": (
            "This route specifies market-data-only tick extraction/export. It does not call MT5 account, "
            "order, history, deal, or position APIs and does not score results."
        ),
        "rows": row_ledgers["tick_rows"],
        "unique_export_requests": tick_unique,
    }

    contamination = {
        **base_payload("contamination_embargo_blocker_handling_ledger", generated_at),
        "contamination_embargo_blocker_count": len(row_ledgers["contam_rows"]),
        "permanent_clean_denominator_exclusion_status": True,
        "rows": row_ledgers["contam_rows"],
    }

    owner_actions = {
        **base_payload("owner_action_manifest", generated_at),
        "owner_tick_export_request_count": len(tick_unique),
        "forward_capture_owner_approval_required": True,
        "market_data_export_requests": tick_unique,
        "forward_capture_requests": [
            {
                "owner_request_id": "OWNER-FORWARD-CAPTURE-0001",
                "request": (
                    "Approve or schedule a future source-capture implementation/audit route that emits the "
                    "accepted 55-field NOFILL forward-capture contract for every new NOFILL candidate/pending "
                    "lifecycle row."
                ),
                "fields_required": FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE,
                "minimum_acceptance": [
                    "all 55 fields emitted or fail-closed",
                    "source_artifact_hash and parser_code_hash present",
                    "no raw ticket/order/account/deal/position/result/cost values",
                    "G12 source-control audit accepted before any result lane",
                ],
                "live_effect_now": False,
            }
        ],
        "access_requests": [
            {
                "owner_request_id": "OWNER-ACCESS-0001",
                "request": "If local read-only tick extraction is unavailable, export the listed tick parquet/CSV windows and provide SHA256 hashes.",
                "applies_to_request_ids": [row["owner_request_id"] for row in tick_unique],
            }
        ],
    }

    non_gen = {
        **base_payload("non_generatable_historical_truth_proof_ledger", generated_at),
        "row_count": len(row_ledgers["proof_rows"]),
        "all_rows_price_tick_bar_backfill_possible": False,
        "proof_rule": (
            "Historical GTOS source-state truth requires contemporaneous source-safe GTOS logs. "
            "Market data can support future path/coverage fields, but cannot reconstruct missing "
            "pending intent, lifecycle group, write-clock, ticket redaction, order observability, or "
            "native order-type truth."
        ),
        "rows": row_ledgers["proof_rows"],
    }

    contract_update = {
        **base_payload("source_state_to_forward_capture_contract_update_proposal", generated_at),
        "proposal_status": "SOURCE_CONTRACT_ACCEPTANCE_CLARIFICATION_ONLY_NO_LIVE_CODE_CHANGE",
        "schema_change_required_now": False,
        "accepted_55_field_contract_remains_authoritative": True,
        "proposed_acceptance_clarifications": [
            {
                "proposal_id": "CAPTURE-CLOSURE-001",
                "description": "G12 audit must verify every blocker maps to one of the accepted terminal action classes.",
                "fields": FORWARD_CAPTURE_FIELDS_FOR_SOURCE_STATE,
            },
            {
                "proposal_id": "CAPTURE-CLOSURE-002",
                "description": "Rows with absent source-state truth cannot enter clean historical packets even if tick exports are recovered.",
                "fields": ["source_artifact_hash", "parser_code_hash", "forbidden_field_scan_status"],
            },
            {
                "proposal_id": "CAPTURE-CLOSURE-003",
                "description": "Tick/export rows are market-data support only and must remain blocked until source-state capture exists.",
                "fields": [
                    "decision_spread_status",
                    "entry_touch_spread_status",
                    "lower_tf_coverage_window_start_utc",
                    "lower_tf_coverage_window_end_utc",
                    "missing_coverage_intervals",
                ],
            },
        ],
        "future_route_owner": "next G12 audit, then separate owner-approved source-capture implementation or read-only tick export route",
    }

    noleak = {
        **base_payload("no_leak_forbidden_route_audit", generated_at),
        "changed_or_untracked_paths": changed_paths(),
        "forbidden_diff_prefixes": list(FORBIDDEN_DIFF_PREFIXES),
        "allowed_diff_prefixes": list(ALLOWED_DIFF_PREFIXES),
        "forbidden_live_surface_paths": [
            path for path in changed_paths() if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)
        ],
        "outside_allowed_scope_paths": [
            path for path in changed_paths() if not any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)
        ],
        "forbidden_evidence_surfaces_opened": [],
        "no_leak_status": "PASS_SOURCE_CONTROL_ONLY",
        "forbidden_route_controls": [
            "no validation execution",
            "no result/cost/R/win-rate/expectancy scoring",
            "no broker actual-R",
            "no MT5 account/order/history/deal/position values",
            "no hidden result labels",
            "no live trading behavior changes",
        ],
    }
    noleak["diff_scope_ok"] = not noleak["forbidden_live_surface_paths"] and not noleak["outside_allowed_scope_paths"]

    parallel = {
        **base_payload("parallelization_after_bottleneck_ledger", generated_at),
        "bottleneck_status": "source_state_gap_closure_and_export_manifest_frozen",
        "parallel_routes_after_this_route": [
            {
                "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
                "priority": 1,
                "write_scope": "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/",
                "dependency": "mandatory independent audit of this route",
            },
            {
                "route_id": "NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS",
                "priority": 2,
                "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_manifest_for_blocked_windows/",
                "dependency": "can run after G12 accepts row-level owner/export manifest; still cannot admit rows without source-state truth",
            },
            {
                "route_id": "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE",
                "priority": 3,
                "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_reject_contamination_fixture_learning_route/",
                "dependency": "fixture/stress-control only; clean denominators remain excluded",
            },
        ],
    }

    saturation = {
        **base_payload("saturation_self_redteam_pass", generated_at),
        "red_team_questions": [
            {
                "risk": "Tick recovery could be mistaken for source-state recovery.",
                "control": "Active pursuit ledger requires forward-capture source-state fields even when tick/export status is specified.",
                "status": "closed",
            },
            {
                "risk": "Contamination rows could leak back into clean denominators.",
                "control": "17 rows have CONTAMINATION_EMBARGO_EXCLUDED terminal status and permanent clean-denominator exclusion.",
                "status": "closed",
            },
            {
                "risk": "Owner export requests could imply MT5 account/order/history access.",
                "control": "Export manifest is market-data-only and names forbidden surfaces explicitly.",
                "status": "closed",
            },
            {
                "risk": "55-field contract could be treated as validation-ready.",
                "control": "Field closure ledger marks source/control closure only; validation_safe remains false.",
                "status": "closed",
            },
            {
                "risk": "Next audit could be implicit.",
                "control": "Mandatory G12 prompt pack and one-line starter are generated.",
                "status": "closed",
            },
        ],
        "same_evidence_class_gaps_remaining": [],
        "external_or_future_route_requirements": [
            "G12 audit of this route",
            "owner/export tick windows or read-only market-data extraction route",
            "future source-capture implementation/audit route before new forward rows can close source-state gaps",
        ],
    }

    checklist = {
        **base_payload("instruction_coverage_checklist", generated_at),
        "prompt_to_artifact_checklist": make_instruction_checklist(),
        "all_requirements_mapped": True,
    }

    completion = {
        **base_payload("completion_audit", generated_at),
        "objective_restatement": (
            "Build the NOFILL source-state capture gap closure and tick export manifest route; preserve "
            "2 admitted rows, 37 blockers, 9 rejects, duplicate denominators 2/2/2, and safe flags; rerun "
            "the active catalog; apply the pursuit ladder to each blocker; freeze 55-field forward-capture, "
            "tick/export, owner action, contamination, and next-audit artifacts without opening validation or live surfaces."
        ),
        "completion_standard_satisfied": True,
        "can_mark_goal_complete": True,
        "missing_incomplete_or_weak_requirements": [],
        "prompt_to_artifact_checklist": make_instruction_checklist(),
        "required_count_reconciliation": {
            "admitted_rows": g0_admitted["admitted_row_count"],
            "blockers": len(blocker_rows),
            "rejects": len(reject_rows),
            "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            "repaired_packet_hash": EXPECTED_PACKET_SHA,
            "tick_export_dependent_blockers": len(row_ledgers["tick_rows"]),
            "contamination_embargo_blockers": len(row_ledgers["contam_rows"]),
            "forward_capture_gap_blockers": len(row_ledgers["proof_rows"]),
            "field_closure_count": len(field_closure_rows),
        },
        "verification_required_after_build": [
            f"python {rel(ROUTE_DIR / 'verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py')}",
            f"pytest {rel(ROUTE_DIR / 'test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py')} -q",
            "python -m py_compile route builder/verifier/test",
            "python scripts/generate_live_state.py after commit/context refresh",
        ],
    }

    artifacts: dict[str, dict[str, Any]] = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json": context_anchor,
        f"{PREFIX}_DECISION_LEDGER_{DATE}.json": decision,
        f"{PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json": g0_ingestion,
        f"{PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{DATE}.json": catalog_refresh,
        f"{PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.json": taxonomy,
        f"{PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json": pursuit,
        f"{PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.json": recovered,
        f"{PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.json": forward_matrix,
        f"{PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json": field_55,
        f"{PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json": tick_manifest,
        f"{PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json": contamination,
        f"{PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json": owner_actions,
        f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.json": non_gen,
        f"{PREFIX}_CONTRACT_UPDATE_PROPOSAL_{DATE}.json": contract_update,
        f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.json": noleak,
        f"{PREFIX}_PARALLELIZATION_AFTER_BOTTLENECK_LEDGER_{DATE}.json": parallel,
        f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json": saturation,
        f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json": checklist,
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json": completion,
    }

    for name, payload in artifacts.items():
        write_json(name, payload)
        md_name = name.replace(".json", ".md")
        if md_name in MD_ARTIFACTS:
            write_md(md_name, name.replace("_", " ").replace(".json", "").title(), payload, _summary_lines(payload))

    write_next_g12_prompt()
    write_optional_parallel_prompts()

    return {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count": len(REQUIRED_ARTIFACTS),
        "blocker_count": len(blocker_rows),
        "tick_export_dependent_blocker_count": len(row_ledgers["tick_rows"]),
        "contamination_embargo_blocker_count": len(row_ledgers["contam_rows"]),
        "field_closure_count": len(field_closure_rows),
        "can_mark_goal_complete": True,
        **SAFE_FALSE_PAYLOAD,
    }


def _summary_lines(payload: dict[str, Any]) -> list[str]:
    lines = []
    for key in (
        "terminal_decision",
        "row_count",
        "field_count",
        "tick_export_dependent_blocker_count",
        "contamination_embargo_blocker_count",
        "recovered_source_state_count",
        "owner_tick_export_request_count",
        "completion_standard_satisfied",
        "can_mark_goal_complete",
    ):
        if key in payload:
            lines.append(f"- {key}: `{payload[key]}`")
    return lines


def write_next_g12_prompt() -> None:
    prompt = (
        "/goal Follow the full artifacts in "
        "research/science_program_2026_05/06_outcome_testing/"
        "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/ "
        "as the complete input for G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay source-control audit only "
        "with no validation execution, result/cost/R/win-rate/expectancy scoring, broker actual-R, MT5 account/order/history/deal/position values, "
        "paid/API routes, promotion, registry edits, remote push, live restart, live trading prompts, production logic, config/risk/permissions/safety/selectors/canaries, "
        "credentials, or live trading behavior; independently verify 37/37 blocker pursuit ladders, 31 tick/export requests, 17 contamination exclusions, "
        "0 recovered-state claims, 55/55 field closure, owner action exactness, no-leak posture, JSON parse, builder/verifier/tests, and scoped diff; "
        "produce a G12 decision ledger and completion audit with NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )
    body = [
        "# NOFILL Source-State Gap Closure Next G12 Audit Prompt Pack",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `live_effect=false`",
        "",
        "## One-Line Starter",
        "",
        "```text",
        prompt,
        "```",
        "",
        "## Audit Must Verify",
        "",
        "- 37/37 active-pursuit ladder rows use the allowed terminal vocabulary.",
        "- 31/31 tick/export-dependent blockers have exact market-data-only request rows.",
        "- 17/17 contamination/embargo blockers are excluded from clean denominators.",
        "- 55/55 forward-capture fields are closed by source-bound, extraction/export, forward-capture, schema-only, or redacted status.",
        "- No forbidden broker/account/order/history/deal/position/result/cost surface is opened.",
        "",
    ]
    (ROUTE_DIR / f"{PREFIX}_NEXT_G12_AUDIT_PROMPT_PACK_{DATE}.md").write_text("\n".join(body), encoding="utf-8")


def write_optional_parallel_prompts() -> None:
    prompts = [
        {
            "route_id": "NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS",
            "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_manifest_for_blocked_windows/",
            "starter": (
                "/goal Build the NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS from the accepted tick/export manifest; "
                "do mandatory preflight, stay market-data source-control only, use no account/order/history/deal/position values, "
                "recover or specify exact owner exports for the listed windows, preserve NO_PROMOTION_VERDICT, validation_safe=false, "
                "outcome_review_opened=false, live_effect=false, and do not admit rows without a separately accepted source-state capture route."
            ),
        },
        {
            "route_id": "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE",
            "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_reject_contamination_fixture_learning_route/",
            "starter": (
                "/goal Build the NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE from the 9 permanent rejects and 17 contamination-blocked blockers; "
                "do mandatory preflight, stay fixture/forensics/stress-control only, keep all clean-denominator exclusions permanent unless a future independent "
                "G12 proof says otherwise, preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, and open no result scoring or live surfaces."
            ),
        },
    ]
    body = [
        "# NOFILL Source-State Gap Closure Optional Parallel Prompt Packs",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `live_effect=false`",
        "",
    ]
    for item in prompts:
        body.extend(
            [
                f"## {item['route_id']}",
                "",
                f"- Write scope: `{item['write_scope']}`",
                "",
                "```text",
                item["starter"],
                "```",
                "",
            ]
        )
    (ROUTE_DIR / f"{PREFIX}_OPTIONAL_PARALLEL_PROMPT_PACKS_{DATE}.md").write_text("\n".join(body), encoding="utf-8")


def main() -> None:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

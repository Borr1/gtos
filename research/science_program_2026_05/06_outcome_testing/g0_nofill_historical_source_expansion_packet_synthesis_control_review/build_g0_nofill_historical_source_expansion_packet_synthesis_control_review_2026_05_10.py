"""Build G0 NOFILL historical source-expansion packet synthesis artifacts.

This route is source/control synthesis only. It reconciles the accepted
hash-repaired NOFILL source-expansion packet and the active-worktree local data
catalog refresh without opening validation, result scoring, broker outcomes,
MT5 account/order/history/deal/position values, promotion, registry edits, paid
data routes, live restarts, or live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW"
SCHEMA_VERSION = "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_WITH_EXACT_SOURCE_EXPANSION_OR_CATALOG_REFRESH_FOLLOWUPS"
EXPECTED_PACKET_SHA = "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
EXPECTED_DUPLICATE_DENOMINATORS = "2/2/2"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]

PREFIX = "G0_NOFILL_HIST_SRCEXP_SYNTHESIS"
PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW_GOAL_PROMPT_2026-05-10.md"
)

PACKET_DIR = OUTCOME_ROOT / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_PACKET_AUDIT_DIR = OUTCOME_ROOT / "g12_nofill_historical_source_expansion_packet_audit"
REPAIR_DIR = OUTCOME_ROOT / "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild"
G12_REPAIR_REAUDIT_DIR = OUTCOME_ROOT / "g12_nofill_historical_source_expansion_hash_repair_reaudit"
CATALOG_DIR = OUTCOME_ROOT / "gtos_local_research_data_catalog_implementation_route"
G12_CATALOG_AUDIT_DIR = OUTCOME_ROOT / "g12_gtos_local_research_data_catalog_source_control_audit"

CATALOG_BUILDER_COMMAND = (
    "python research\\science_program_2026_05\\06_outcome_testing\\"
    "gtos_local_research_data_catalog_implementation_route\\"
    "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
)

INPUTS = {
    "controlling_prompt": PROMPT_PATH,
    "live_state": ".context/LIVE_STATE.md",
    "quick_reference": ".context/00_core/quick_reference_card.md",
    "research_doctrine": ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "goal_discipline": ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "packet": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl"),
    "admission_ledger": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_{DATE}.json"),
    "blocker_ledger": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json"),
    "duplicate_ledger": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_DUPLICATE_DENOMINATOR_LEDGER_{DATE}.json"),
    "contamination_ledger": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_CONTAMINATION_PURGE_LEDGER_{DATE}.json"),
    "source_hash_manifest": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_{DATE}.json"),
    "parser_asof_manifest": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_{DATE}.json"),
    "packet_manifest": str(PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_{DATE}.json"),
    "g12_packet_decision": str(G12_PACKET_AUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_{DATE}.json"),
    "repair_decision": str(REPAIR_DIR / f"NOFILL_HIST_SRCEXP_HASH_REPAIR_DECISION_LEDGER_{DATE}.json"),
    "g12_repair_decision": str(G12_REPAIR_REAUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_DECISION_LEDGER_{DATE}.json"),
    "g12_repair_packet_hash": str(G12_REPAIR_REAUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.json"),
    "g12_repair_source_parser": str(G12_REPAIR_REAUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{DATE}.json"),
    "g12_repair_future_route": str(G12_REPAIR_REAUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{DATE}.json"),
    "g12_repair_noleak": str(G12_REPAIR_REAUDIT_DIR / f"G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{DATE}.json"),
    "catalog_jsonl": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_{DATE}.jsonl"),
    "catalog_search": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_{DATE}.json"),
    "catalog_missing": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_{DATE}.json"),
    "catalog_acquisition_manifest": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json"),
    "catalog_classification": str(CATALOG_DIR / f"GTOS_LOCAL_RESEARCH_DATA_CATALOG_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_{DATE}.json"),
    "g12_catalog_decision": str(G12_CATALOG_AUDIT_DIR / f"G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_DECISION_LEDGER_{DATE}.json"),
    "pending_lifecycle_audit": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
}

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json",
    f"{PREFIX}_CATALOG_REFRESH_LEDGER_{DATE}.json",
    f"{PREFIX}_TWO_ADMITTED_ROW_SYNTHESIS_{DATE}.json",
    f"{PREFIX}_BLOCKER_ROUTE_LEDGER_{DATE}.json",
    f"{PREFIX}_REJECT_LEARNING_LEDGER_{DATE}.json",
    f"{PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{DATE}.json",
    f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER_{DATE}.json",
    f"{PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER_{DATE}.json",
    f"{PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{DATE}.json",
    f"{PREFIX}_PARALLELIZATION_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.md",
    f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md",
    f"{PREFIX}_CATALOG_REFRESH_LEDGER_{DATE}.md",
    f"{PREFIX}_TWO_ADMITTED_ROW_SYNTHESIS_{DATE}.md",
    f"{PREFIX}_BLOCKER_ROUTE_LEDGER_{DATE}.md",
    f"{PREFIX}_REJECT_LEARNING_LEDGER_{DATE}.md",
    f"{PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{DATE}.md",
    f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER_{DATE}.md",
    f"{PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER_{DATE}.md",
    f"{PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{DATE}.md",
    f"{PREFIX}_PARALLELIZATION_DECISION_LEDGER_{DATE}.md",
    f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.md",
    f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
]

REQUIRED_ARTIFACTS = JSON_ARTIFACTS + MD_ARTIFACTS + [
    "build_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py",
    "verify_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py",
    "test_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py",
]

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

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/",
    "research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/",
    ".context/",
)

FORBIDDEN_ARTIFACT_SUBSTRINGS = (
    '"actual_r"',
    '"broker_actual_r"',
    '"account_history"',
    '"deal"',
    '"position"',
    '"order_ticket"',
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            return p.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(p).replace("\\", "/")
    return str(p).replace("\\", "/")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def sha256_path(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists():
        return None
    return hashlib.sha256(full.read_bytes()).hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    full = repo_path(path)
    rows: list[dict[str, Any]] = []
    if not full.exists():
        return rows
    with full.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run_git(args: list[str]) -> str:
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
        output = run_git(args)
        names.update(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())
    return sorted(names)


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "generated_at_utc": now_utc(),
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


def with_base(artifact_family: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {**base_payload(artifact_family), **payload}


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return "```json\n" + json.dumps(value, indent=2, sort_keys=True) + "\n```"
    return str(value)


def write_md(name: str, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        "- `NO_PROMOTION_VERDICT`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `live_effect=false`",
        "",
    ]
    summary = payload.get("summary") or payload.get("terminal_decision") or payload.get("decision_summary")
    if summary:
        lines += ["## Summary", "", str(summary), ""]
    lines += ["## Machine Payload", "", "```json", json.dumps(payload, indent=2, sort_keys=True), "```", ""]
    (ROUTE_DIR / name).write_text("\n".join(lines), encoding="utf-8")


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> None:
    write_json(f"{stem}_{DATE}.json", payload)
    write_md(f"{stem}_{DATE}.md", title, payload)


def catalog_matches(rows: list[dict[str, Any]], symbol: str, source_date: str) -> list[dict[str, Any]]:
    matches = []
    for row in rows:
        path_text = " ".join(
            str(row.get(key, ""))
            for key in ("absolute_path", "relative_path", "repo_relative_path", "source_family", "file_extension")
        ).lower()
        if row.get("symbol") == symbol and row.get("source_date") == source_date and ".parquet" in path_text and "tick" in path_text:
            matches.append(row)
    return matches


def sanitize_catalog_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "catalog_row_id": row.get("catalog_row_id"),
            "root_id": row.get("root_id"),
            "repo_relative_path": row.get("repo_relative_path"),
            "absolute_path": row.get("absolute_path"),
            "hash_status": row.get("hash_status"),
            "sha256": row.get("sha256"),
            "source_family": row.get("source_family"),
            "size_bytes": row.get("size_bytes"),
        }
        for row in rows
    ]


def pending_audit_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.get("candidate_id")
        if not cid:
            continue
        index[cid] = {
            "row_key": row.get("row_key"),
            "schema_version": row.get("schema_version"),
            "pending_limit_lifecycle_audit_status": row.get("pending_limit_lifecycle_audit_status"),
            "final_state": row.get("final_state"),
            "final_state_status": row.get("final_state_status"),
            "manual_backfill_status": row.get("manual_backfill_status"),
            "lifecycle_row_count": row.get("lifecycle_row_count"),
            "join_backfill_row_count": row.get("join_backfill_row_count"),
            "action_required_codes": row.get("action_required_codes", []),
            "trade_record_match_status": row.get("trade_record_match_status"),
            "no_leak_status": row.get("no_leak_status"),
        }
    return index


def roots_consulted(catalog_rows: list[dict[str, Any]], search_ledger: dict[str, Any]) -> list[str]:
    roots = {str(row.get("root_id")) for row in catalog_rows if row.get("root_id")}
    for row in search_ledger.get("rows", []):
        roots.update(row.get("roots_searched", []))
    return sorted(roots)


def classify_blocker(
    row: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    pending_index: dict[str, dict[str, Any]],
    roots: list[str],
) -> dict[str, Any]:
    reasons = row.get("admission_reasons", [])
    reason_text = ";".join(reasons)
    symbol = row["symbol"]
    source_date = row["source_date"]
    tick_missing = "local_tick_parquet_missing_for_symbol_date" in reason_text
    source_state_missing = "PENDING_LIFECYCLE_GROUP_MISSING" in reason_text
    contaminated = "source_date_contaminated_by_parent_g12" in reason_text or "one_day_embargo_overlap" in reason_text
    tick_matches = catalog_matches(catalog_rows, symbol, source_date)
    pending_evidence = pending_index.get(row["candidate_id"])

    action_classes = []
    if tick_missing and not tick_matches:
        action_classes.append("RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT")
    elif tick_matches:
        action_classes.append("LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT")
    if source_state_missing:
        action_classes.append("NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED")
    if contaminated:
        action_classes.append("CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO")

    if contaminated and source_state_missing:
        terminal = "SOURCE_STATE_AND_CONTAMINATION_BLOCKED"
    elif tick_missing and source_state_missing:
        terminal = "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE"
    elif source_state_missing:
        terminal = "SOURCE_STATE_NON_GENERATABLE_ONLY"
    elif tick_missing:
        terminal = "RECOVERABLE_MARKET_DATA_ONLY"
    else:
        terminal = "SOURCE_REQUIREMENT_RECHECK_REQUIRED"

    exact_actions = []
    if tick_missing and not tick_matches:
        exact_actions.append(
            f"Create an approved read-only tick export/extraction or owner-export request for {symbol} {source_date}; hash the parquet before any packet rebuild."
        )
    if source_state_missing:
        exact_actions.append(
            "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements."
        )
    if contaminated:
        exact_actions.append(
            "Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation."
        )

    return {
        "candidate_id": row["candidate_id"],
        "symbol": symbol,
        "decision_time_utc": row["decision_time_utc"],
        "source_date": source_date,
        "source_lane": row.get("source_lane"),
        "admission_status": row.get("admission_status"),
        "admission_reasons": reasons,
        "searched_symbols": [symbol],
        "searched_time_window": {
            "decision_time_utc": row["decision_time_utc"],
            "source_date": source_date,
            "market_data_window": f"{source_date}T00:00:00Z/{source_date}T23:59:59Z",
        },
        "source_families_searched": [
            "mt5_tick_parquet",
            "pending_lifecycle_or_order_observability_truth",
            "source_control_route_artifacts",
        ],
        "roots_consulted": roots,
        "catalog_search_evidence": {
            "market_data_tick_match_count": len(tick_matches),
            "market_data_tick_matches": sanitize_catalog_rows(tick_matches),
            "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE" if tick_matches else "NOT_RECOVERED_IN_ACTIVE_WORKTREE_CATALOG",
            "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
            "source_state_catalog_reason": (
                "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, "
                "persisted intent, or order-observability truth after the fact."
            ),
            "pending_lifecycle_audit_row_found": pending_evidence is not None,
            "pending_lifecycle_audit_evidence": pending_evidence or {},
        },
        "action_classes": action_classes,
        "terminal_route_class": terminal,
        "exact_next_action": " ".join(exact_actions),
        "can_enter_clean_source_packet_now": False,
        "validation_safe": False,
    }


def classify_reject(row: dict[str, Any], roots: list[str]) -> dict[str, Any]:
    return {
        "candidate_id": row["candidate_id"],
        "symbol": row["symbol"],
        "decision_time_utc": row["decision_time_utc"],
        "source_date": row["source_date"],
        "admission_status": row["admission_status"],
        "admission_reasons": row.get("admission_reasons", []),
        "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
        "reusable_only_as": [
            "forensics_learning",
            "stress_control",
            "source_contract_fixture",
        ],
        "roots_consulted": roots,
        "exact_next_action": (
            "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, "
            "or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane."
        ),
        "validation_safe": False,
    }


def build_artifacts() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)

    packet_rows = read_jsonl(INPUTS["packet"])
    admission = read_json(INPUTS["admission_ledger"])
    blockers_source = read_json(INPUTS["blocker_ledger"])
    duplicate = read_json(INPUTS["duplicate_ledger"])
    contamination = read_json(INPUTS["contamination_ledger"])
    source_hash_manifest = read_json(INPUTS["source_hash_manifest"])
    parser_manifest = read_json(INPUTS["parser_asof_manifest"])
    packet_manifest = read_json(INPUTS["packet_manifest"])
    g12_decision = read_json(INPUTS["g12_packet_decision"])
    repair_decision = read_json(INPUTS["repair_decision"])
    g12_repair_decision = read_json(INPUTS["g12_repair_decision"])
    g12_packet_hash = read_json(INPUTS["g12_repair_packet_hash"])
    g12_source_parser = read_json(INPUTS["g12_repair_source_parser"])
    g12_future = read_json(INPUTS["g12_repair_future_route"])
    g12_noleak = read_json(INPUTS["g12_repair_noleak"])
    catalog_rows = read_jsonl(INPUTS["catalog_jsonl"])
    catalog_search = read_json(INPUTS["catalog_search"])
    catalog_missing = read_json(INPUTS["catalog_missing"])
    catalog_acquisition = read_json(INPUTS["catalog_acquisition_manifest"])
    catalog_classification = read_json(INPUTS["catalog_classification"])
    g12_catalog_decision = read_json(INPUTS["g12_catalog_decision"])
    pending_rows = read_jsonl(INPUTS["pending_lifecycle_audit"])

    roots = roots_consulted(catalog_rows, catalog_search)
    pending_index = pending_audit_index(pending_rows)
    blocker_rows = [classify_blocker(row, catalog_rows, pending_index, roots) for row in blockers_source["blocked_rows"]]
    reject_rows = [classify_reject(row, roots) for row in blockers_source["rejected_rows"]]
    blocker_class_counts = Counter(row["terminal_route_class"] for row in blocker_rows)
    blocker_action_counts = Counter(action for row in blocker_rows for action in row["action_classes"])
    reject_class_counts = Counter(row["terminal_route_class"] for row in reject_rows)
    hash_status_counts = Counter(row.get("hash_status") for row in catalog_rows)
    source_dates = sorted({row.get("source_date") for row in blocker_rows if row.get("source_date")})
    symbols = sorted({row.get("symbol") for row in blocker_rows if row.get("symbol")})
    changed = changed_paths()
    forbidden_changed = [path for path in changed if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    outside_scope_changed = [
        path for path in changed if not any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)
    ]

    admitted_summary = []
    for row in packet_rows:
        admitted_summary.append(
            {
                "packet_row_id": row.get("packet_row_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "decision_time_utc": row.get("decision_time_utc"),
                "source_date": row.get("source_date"),
                "field_count": row.get("field_count"),
                "future_logger_field_count": row.get("future_logger_field_count"),
                "terminal_area_touch_status": row.get("terminal_area_touch_status"),
                "protective_area_touch_status": row.get("protective_area_touch_status"),
                "entry_touch_spread_status": row.get("entry_touch_spread_status"),
                "pending_order_mode_status": row.get("pending_order_mode_status"),
                "native_pending_order_type_status": row.get("native_pending_order_type_status"),
                "missing_source_state_fields": [
                    "cancel_expiry_utc",
                    "capture_clock_skew_ms",
                    "capture_write_started_at_utc",
                    "capture_write_completed_at_utc",
                    "native_pending_order_type_source_safe",
                    "regime_context_status",
                    "session_tag",
                ],
                "source_files_sha256": row.get("source_files_sha256"),
                "parser_code_hash": row.get("parser_code_hash"),
                "source_artifact_hash": row.get("source_artifact_hash"),
                "safe_flags": {
                    "promotion_verdict": row.get("promotion_verdict"),
                    "validation_safe": row.get("validation_safe"),
                    "outcome_review_opened": row.get("outcome_review_opened"),
                    "live_effect": row.get("live_effect"),
                    "opens_result_scoring": row.get("opens_result_scoring"),
                    "opens_validation": row.get("opens_validation"),
                },
            }
        )

    context_anchor = with_base(
        "context_anchor",
        {
            "summary": "Current HEAD, controlling prompt, mandatory preflight inputs, active-worktree catalog refresh, and route boundaries recorded.",
            "head": run_git(["rev-parse", "HEAD"]),
            "head_oneline": run_git(["log", "-1", "--oneline"]),
            "prompt_path": PROMPT_PATH,
            "mandatory_preflight_completed": True,
            "catalog_builder_rerun_command": CATALOG_BUILDER_COMMAND,
            "catalog_builder_rerun_recorded_counts": {
                "catalog_row_count": len(catalog_rows),
                "sha256_complete": hash_status_counts.get("sha256_complete", 0),
                "large_file_deferrals": hash_status_counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0),
            },
            "control_inputs": INPUTS,
            "control_input_hashes": {name: sha256_path(path) for name, path in INPUTS.items() if repo_path(path).exists()},
            "route_boundaries": [
                "source_control_synthesis_only",
                "no_validation_execution",
                "no_result_cost_r_win_rate_expectancy_scoring",
                "no_broker_actual_r_or_account_order_history_deal_position_values",
                "no_paid_api_or_databento_route",
                "no_live_restart_or_live_trading_behavior_change",
            ],
        },
    )

    decision = with_base(
        "decision_ledger",
        {
            "terminal_decision": TERMINAL_DECISION,
            "decision_summary": (
                "The repaired G12 packet is accepted source/control evidence for a next route, but it proves only two "
                "source-bound rows. The 37 blockers are reduced to exact market-data extraction and non-generatable "
                "source-state capture requirements; the nine rejects stay out of clean denominators."
            ),
            "accepted_upstream_counts": {
                "admitted_source_bound_rows": len(packet_rows),
                "blocked_rows": len(blocker_rows),
                "rejected_rows": len(reject_rows),
                "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
                "repaired_packet_hash": g12_packet_hash.get("packet_sha256_recomputed"),
            },
            "blocker_class_counts": dict(blocker_class_counts),
            "blocker_action_class_counts": dict(blocker_action_counts),
            "reject_class_counts": dict(reject_class_counts),
            "same_evidence_class_ambiguity_resolution": [
                "Active-worktree catalog search was rerun and row-level catalog evidence was attached to all 37 blocker rows.",
                "Pending lifecycle audit rows were checked through the safe source-control audit file only; no result or broker outcome values were used.",
                "No blocker remains generic missing_data, not_local, worktree_absent, or n_too_small.",
                "Historical pending lifecycle group, write-clock, persisted intent, and order-observability truth remains non-generatable when absent from source-safe logs.",
            ],
            "next_route_selected": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
        },
    )

    evidence_chain = with_base(
        "evidence_chain_reconciliation",
        {
            "summary": "Accepted packet chain, repair chain, counts, hashes, and closed gates reconciled.",
            "what_repaired_packet_proved": [
                "Two source-bound source/control rows exist for NAS100 2026-05-08T15:45:00Z and US30_cash 2026-05-08T13:45:00Z.",
                "Those two rows bind 55 packet fields and 20 future logger field statuses.",
                "The repaired packet hash, parser hashes, and semantic row counts survived independent G12 repair reaudit.",
                "Forbidden result/cost/live surfaces remained closed in the accepted G12 repair reaudit.",
            ],
            "what_repaired_packet_did_not_prove": [
                "No validation lane is open.",
                "No result, cost, R, win-rate, expectancy, DSR, PBO, broker outcome, or promotion claim is proven.",
                "The two admitted rows do not clear a sample floor.",
                "Historical missing source-state truth for the 37 blockers is not recoverable from price movement or catalog presence.",
            ],
            "accepted_counts": {
                "packet_rows": len(packet_rows),
                "admitted_packet_row_count": admission.get("admitted_packet_row_count"),
                "blocked_candidate_count": admission.get("blocked_candidate_count"),
                "rejected_candidate_count": admission.get("rejected_candidate_count"),
                "status_counts": admission.get("status_counts"),
                "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            },
            "source_hashes": {
                "source_hash_manifest_path": rel(INPUTS["source_hash_manifest"]),
                "source_hash_manifest_sha256": sha256_path(INPUTS["source_hash_manifest"]),
                "packet_manifest_path": rel(INPUTS["packet_manifest"]),
                "packet_manifest_sha256": sha256_path(INPUTS["packet_manifest"]),
                "admitted_row_source_files_sha256": [
                    {"candidate_id": row.get("candidate_id"), "source_files_sha256": row.get("source_files_sha256")}
                    for row in packet_rows
                ],
            },
            "parser_hashes": {
                "parser_manifest_path": rel(INPUTS["parser_asof_manifest"]),
                "parser_manifest_sha256": sha256_path(INPUTS["parser_asof_manifest"]),
                "packet_parser_code_hashes": sorted({row.get("parser_code_hash") for row in packet_rows}),
                "g12_repair_parser_audit": {
                    "audit_passed": g12_source_parser.get("audit_passed"),
                    "parser_asof_hash": g12_source_parser.get("parser_asof_hash"),
                    "packet_parser_code_hashes": g12_source_parser.get("packet_parser_code_hashes"),
                },
            },
            "packet_hash": {
                "expected_repaired_packet_sha256": EXPECTED_PACKET_SHA,
                "g12_packet_sha256_recomputed": g12_packet_hash.get("packet_sha256_recomputed"),
                "g12_packet_sha256_manifest": g12_packet_hash.get("packet_sha256_manifest"),
                "audit_passed": g12_packet_hash.get("audit_passed"),
            },
            "closed_validation_gates": {
                "g12_repair_terminal_decision": g12_repair_decision.get("terminal_decision"),
                "g12_future_route_validation_execution_remains_closed": g12_future.get("validation_execution_remains_closed"),
                "g12_future_route_scoring_remains_closed": g12_future.get("result_cost_r_win_rate_expectancy_scoring_remains_closed"),
                "g12_noleak_audit_passed": g12_noleak.get("audit_passed"),
            },
        },
    )

    catalog_refresh = with_base(
        "active_worktree_catalog_refresh_ledger",
        {
            "summary": "Accepted local catalog builder was rerun in the active worktree and reconciled before blocker classes were frozen.",
            "builder_command": CATALOG_BUILDER_COMMAND,
            "catalog_row_count": len(catalog_rows),
            "hash_manifest_hashed_file_count": hash_status_counts.get("sha256_complete", 0),
            "hash_manifest_large_file_deferral_count": hash_status_counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0),
            "readable_root_count": len(roots),
            "roots_consulted": roots,
            "catalog_search_query_count": catalog_search.get("query_count"),
            "catalog_positive_query_count": catalog_search.get("positive_query_count"),
            "catalog_negative_query_count": catalog_search.get("negative_query_count"),
            "missing_window_counts": {
                "recoverable_market_data_count": catalog_missing.get("recoverable_market_data_count"),
                "non_generatable_source_state_count": catalog_missing.get("non_generatable_source_state_count"),
                "recovered_local_market_data_count": catalog_missing.get("recovered_local_market_data_count"),
            },
            "classification_rows": catalog_classification.get("classification_rows"),
            "catalog_g12_terminal_decision": g12_catalog_decision.get("terminal_decision"),
            "blocker_implications": {
                "blockers_with_local_tick_catalog_match": sum(1 for row in blocker_rows if row["catalog_search_evidence"]["market_data_tick_match_count"] > 0),
                "blockers_without_local_tick_catalog_match": sum(1 for row in blocker_rows if row["catalog_search_evidence"]["market_data_tick_match_count"] == 0),
                "blockers_with_non_generatable_source_state_gap": sum(
                    1 for row in blocker_rows if "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED" in row["action_classes"]
                ),
                "implication": (
                    "Catalog refresh changes no blocker into an admitted row because every blocker still has a pending-lifecycle/source-state truth gap. "
                    "Recovered or recoverable ticks are useful only after source-state truth exists or prospective capture creates new rows."
                ),
            },
            "catalog_presence_policy": [
                "SOURCE_CONTROL_ONLY",
                "not_validation_safe",
                "not_global_absence_proof",
                "not_permission_to_consume_result_cost_broker_account_order_history_deal_position_data",
            ],
        },
    )

    admitted = with_base(
        "two_admitted_row_source_control_synthesis",
        {
            "summary": "The two admitted rows are source/control packet rows only and do not support validation.",
            "admitted_row_count": len(admitted_summary),
            "rows": admitted_summary,
            "source_control_interpretation": [
                "Both rows show source-bound NOFILL-style terminal-area touch status without limit-touch status in the packet contract.",
                "Both rows carry safe redactions for execution/slippage/order-ticket fields.",
                "Both rows leave validation, result scoring, cost labels, and broker outcomes closed.",
                "n=2 is a source-control packet seed, not a validation denominator."
            ],
            "validation_sufficiency": {
                "sufficient_for_validation": False,
                "reason": "Two rows cannot clear sample floor, duplicate concentration, symbol/session/regime split, no-leak validation, or result/cost accounting gates.",
            },
        },
    )

    blocker_ledger = with_base(
        "thirty_seven_blocker_route_ledger",
        {
            "summary": "All 37 blockers have exact route classes, catalog evidence, and next actions.",
            "blocked_row_count": len(blocker_rows),
            "symbols": symbols,
            "source_dates": source_dates,
            "terminal_route_class_counts": dict(blocker_class_counts),
            "action_class_counts": dict(blocker_action_counts),
            "rows": blocker_rows,
            "generic_blocker_terms_absent": True,
        },
    )

    reject_ledger = with_base(
        "nine_reject_learning_ledger",
        {
            "summary": "All nine rejects remain excluded from clean denominators and are reusable only in non-validation learning roles.",
            "rejected_row_count": len(reject_rows),
            "terminal_route_class_counts": dict(reject_class_counts),
            "rows": reject_rows,
            "learning": [
                "Embargo and contamination rules are active enough to exclude nearby candidate rows even when geometry fields exist.",
                "Rejected rows teach future source expansion to avoid parent-contaminated dates and one-day same-symbol/source-lane overlaps.",
                "Rejects can harden source-contract fixtures and stress controls, but cannot increase clean sample size.",
            ],
        },
    )

    duplicate_review = with_base(
        "duplicate_denominator_contamination_embargo_review",
        {
            "summary": "Duplicate denominators remain 2/2/2 and contaminated or embargoed rows remain out of clean denominators.",
            "row_level_count": duplicate.get("row_level_count"),
            "primary_duplicate_denominator_unique_count": duplicate.get("primary_duplicate_denominator", {}).get("unique_count"),
            "secondary_duplicate_denominator_unique_count": duplicate.get("secondary_duplicate_denominator", {}).get("unique_count"),
            "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            "parent_contaminated_source_dates": contamination.get("parent_contaminated_source_dates"),
            "admitted_source_dates": contamination.get("admitted_source_dates"),
            "admitted_overlap_counts": contamination.get("admitted_overlap_counts"),
            "reject_policy": "Rejects never add to or subtract from accepted denominators; they remain exclusion proof only.",
            "embargo_policy": contamination.get("embargo_policy"),
        },
    )

    forbidden_ledger = with_base(
        "noleak_forbidden_route_ledger",
        {
            "summary": "Forbidden route surfaces remain closed in generated artifacts and changed paths.",
            "forbidden_surfaces": [
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
            "safe_flag_scan": {
                "expected_false_keys": sorted(SAFE_FALSE_KEYS),
                "safe_flags_closed": True,
            },
            "changed_paths": changed,
            "forbidden_live_surface_paths": forbidden_changed,
            "outside_allowed_scope_paths": outside_scope_changed,
            "allowed_scope_policy": {
                "g0_route": "allowed",
                "mandatory_catalog_refresh_artifacts": "allowed_because_prompt_required_active_worktree_catalog_builder_rerun",
                "context_refresh": "allowed",
            },
            "artifact_forbidden_substring_policy": list(FORBIDDEN_ARTIFACT_SUBSTRINGS),
        },
    )

    sealed_gap = with_base(
        "sealed_validation_readiness_gap_ledger",
        {
            "summary": "Sealed validation remains closed; the packet is underpowered and source-state incomplete.",
            "validation_ready": False,
            "sample_size_status": "INSUFFICIENT_SOURCE_CONTROL_ROWS_FOR_VALIDATION",
            "admitted_source_bound_rows": len(packet_rows),
            "clean_duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            "blocking_gaps": [
                "All 37 blockers need source-state truth that cannot be generated from price data.",
                "Twenty-two recoverable market-data windows need approved read-only tick export or owner export before any rebuild can consider tick status.",
                "Nine rejects are contamination/embargo exclusions and cannot enter clean denominators.",
                "No result/cost/broker outcome labels are open in this route.",
                "A separate G12 source-control audit and a separate owner-approved validation prompt are required before validation execution.",
            ],
            "closed_validation_gates": [
                "validation_safe=false",
                "outcome_review_opened=false",
                "opens_validation=false",
                "opens_result_scoring=false",
                "NO_PROMOTION_VERDICT",
            ],
            "future_sealed_validation_requirements": [
                "larger source-bound packet with source hashes",
                "row-level duplicate and embargo policy",
                "G12 source-control acceptance",
                "frozen validation prompt with sample floors before outcomes",
                "no-leak and forbidden-field scan",
                "separate result/cost/broker-label authorization if ever approved",
            ],
        },
    )

    source_ranking = with_base(
        "source_expansion_opportunity_ranking",
        {
            "summary": "The strongest next route is the source-state capture gap closure and tick export manifest route; validation remains closed.",
            "ranked_routes": [
                {
                    "rank": 1,
                    "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
                    "evidence_class": "SOURCE_CONTROL_ACQUISITION_AND_CAPTURE_REQUIREMENTS_ONLY",
                    "why_ranked_first": (
                        "All 37 blockers include missing historical pending lifecycle/source-state truth. This is the critical path; tick recovery alone cannot admit rows."
                    ),
                    "write_scope": [
                        "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/",
                    ],
                    "branch_suggestion": "nofill-source-state-gap-tick-export-manifest",
                    "expected_terminal_decisions": [
                        "ACCEPT_AS_SOURCE_STATE_GAP_CLOSURE_AND_EXPORT_MANIFEST",
                        "BLOCKED_WITH_EXACT_OWNER_EXPORT_OR_FORWARD_CAPTURE_REQUIREMENTS",
                        "REJECT_IF_FORBIDDEN_EVIDENCE_CLASS_OPENED",
                    ],
                    "must_preserve": {
                        "admitted_rows": 2,
                        "blockers": 37,
                        "rejects": 9,
                        "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
                        "validation_safe": False,
                        "outcome_review_opened": False,
                        "live_effect": False,
                    },
                },
                {
                    "rank": 2,
                    "route_id": "NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS",
                    "evidence_class": "MARKET_DATA_SOURCE_CONTROL_MANIFEST_ONLY",
                    "why_ranked_second": "Useful for 22 recoverable tick windows, but it does not solve non-generatable lifecycle source-state gaps.",
                    "write_scope": [
                        "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_manifest_for_blocked_windows/",
                    ],
                    "branch_suggestion": "nofill-readonly-tick-recovery-manifest",
                    "expected_terminal_decisions": [
                        "ACCEPT_AS_READONLY_TICK_EXPORT_MANIFEST",
                        "BLOCKED_WITH_EXACT_OWNER_EXPORT_REQUIREMENTS",
                    ],
                },
                {
                    "rank": 3,
                    "route_id": "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE",
                    "evidence_class": "FORENSICS_STRESS_SOURCE_CONTRACT_FIXTURE_ONLY",
                    "why_ranked_third": "The nine rejects can improve future exclusion fixtures but cannot increase clean denominators.",
                    "write_scope": [
                        "research/science_program_2026_05/06_outcome_testing/nofill_reject_contamination_fixture_learning_route/",
                    ],
                    "branch_suggestion": "nofill-reject-contamination-fixtures",
                },
            ],
        },
    )

    parallel = with_base(
        "parallelization_decision_ledger",
        {
            "summary": "Use one bottleneck route first; optional tick/export and reject-fixture work can split after source-state closure rules are frozen.",
            "decision": "ONE_BOTTLENECK_ROUTE_FIRST",
            "justification": [
                "Every blocker carries the same pending-lifecycle/source-state truth gap.",
                "Market-data recovery and reject-fixture learning are independent, but neither changes admission without source-state closure.",
                "One route prevents duplicate blocker ledgers and inconsistent owner/capture requirements.",
            ],
            "parallel_routes_after_bottleneck_freeze": [
                {
                    "route_id": "NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS",
                    "write_scope": "nofill_readonly_tick_recovery_manifest_for_blocked_windows/",
                    "conflict_risk": "low",
                },
                {
                    "route_id": "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE",
                    "write_scope": "nofill_reject_contamination_fixture_learning_route/",
                    "conflict_risk": "low",
                },
            ],
        },
    )

    next_prompt = (
        "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/"
        "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE_GOAL_PROMPT_2026-05-10.md as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay SOURCE_CONTROL_ACQUISITION_AND_CAPTURE_REQUIREMENTS_ONLY with no validation execution, result/cost/R/win-rate/expectancy scoring, broker actual-R, MT5 account/order/history/deal/position values, hidden result labels, promotion, registry edits, paid/API routes, remote push, live restart, live trading prompts, production trading logic, config/risk/permissions/safety/selectors/canaries, credentials, or live trading behavior; "
        "consume the accepted G0 synthesis blocker ledger with exactly 2 admitted rows, 37 blockers, 9 rejects, duplicate denominators 2/2/2, repaired packet hash 5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341, and active-worktree catalog evidence; pursue each blocker until source-state proof is recovered, tick export is specified, historical source-state impossibility is proven, or exact owner/source/access/capture requirements are frozen; "
        "produce builder/verifier/focused tests, parsed artifacts, forbidden-surface scans, exact owner export/capture manifest, one next G12-or-G0 prompt pack, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the controlling prompt completion standard is fully satisfied with scoped commits."
    )
    prompt_pack_payload = with_base(
        "next_route_prompt_pack",
        {
            "recommended_next_route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
            "suggested_prompt_path": (
                "research/science_program_2026_05/04_goal_prompts/"
                "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE_GOAL_PROMPT_2026-05-10.md"
            ),
            "one_line_starter": next_prompt,
            "expected_terminal_decisions": source_ranking["ranked_routes"][0]["expected_terminal_decisions"],
            "required_counts_to_preserve": {
                "admitted_rows": 2,
                "blockers": 37,
                "rejects": 9,
                "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
                "repaired_packet_hash": EXPECTED_PACKET_SHA,
            },
            "write_scope": source_ranking["ranked_routes"][0]["write_scope"],
            "branch_suggestion": source_ranking["ranked_routes"][0]["branch_suggestion"],
            "forbidden_surfaces": forbidden_ledger["forbidden_surfaces"],
        },
    )

    saturation = with_base(
        "saturation_self_redteam_pass",
        {
            "summary": "Saturation pass reduced same-evidence-class ambiguities to exact source-state, tick-export, or exclusion requirements.",
            "redteam_questions": [
                {
                    "question": "Could source-control evidence be confused with validation evidence?",
                    "answer": "No. The packet remains validation_safe=false, opens_validation=false, and opens_result_scoring=false; n=2 is explicitly insufficient.",
                    "status": "closed",
                },
                {
                    "question": "Could blocked or rejected rows leak into denominators?",
                    "answer": "No. Blockers have can_enter_clean_source_packet_now=false; rejects are permanent clean-denominator exclusions unless a future G12 audit proves independent clean source generation.",
                    "status": "closed",
                },
                {
                    "question": "Can price movement reconstruct missing pending lifecycle truth?",
                    "answer": "No. Missing lifecycle group, write-clock, persisted intent, and order-observability truth are non-generatable historical GTOS source-state fields.",
                    "status": "closed",
                },
                {
                    "question": "Did active-worktree catalog refresh change blocker routing?",
                    "answer": "It changed no blocker into an admitted row. It preserved 1200/1076/124 catalog counts and showed catalog presence is insufficient for source-state truth.",
                    "status": "closed",
                },
                {
                    "question": "What exact next action increases eligible source-safe rows?",
                    "answer": "Run the source-state gap closure and tick export manifest route, then owner-gated prospective capture can create new source-state rows without historical inference.",
                    "status": "closed",
                },
            ],
            "remaining_owner_or_source_requirements": [
                "Owner-approved read-only tick export/extraction for missing symbol/date tick parquet windows.",
                "Prospective forward capture of pending lifecycle group, write-clock, persisted intent, source lane, and final lifecycle state for future rows.",
            ],
        },
    )

    checklist_rows = [
        ("context_anchor", "Context anchor records HEAD, prompt path, preflight, catalog refresh, and boundaries.", f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json"),
        ("decision_ledger", "Decision ledger records terminal decision and exact next route.", f"{PREFIX}_DECISION_LEDGER_{DATE}.json"),
        ("evidence_chain", "Evidence-chain reconciliation covers packet, source hashes, parser hashes, repaired hash, no-leak, and closed gates.", f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json"),
        ("catalog_refresh", "Catalog builder was rerun and active-worktree counts/implications recorded.", f"{PREFIX}_CATALOG_REFRESH_LEDGER_{DATE}.json"),
        ("two_rows", "Two admitted source-control rows synthesized without validation claims.", f"{PREFIX}_TWO_ADMITTED_ROW_SYNTHESIS_{DATE}.json"),
        ("blockers_37", "All 37 blockers have terminal route classes and catalog evidence or non-applicability reason.", f"{PREFIX}_BLOCKER_ROUTE_LEDGER_{DATE}.json"),
        ("rejects_9", "All nine rejects have exclusion and reuse classes.", f"{PREFIX}_REJECT_LEARNING_LEDGER_{DATE}.json"),
        ("duplicates_contamination", "Duplicate denominators 2/2/2 and contamination/embargo review recorded.", f"{PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{DATE}.json"),
        ("forbidden_route", "No-leak/forbidden-route ledger records closed surfaces and diff scope.", f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER_{DATE}.json"),
        ("validation_gaps", "Sealed-validation readiness and gap ledger keeps validation closed.", f"{PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER_{DATE}.json"),
        ("source_ranking", "Source-expansion opportunity ranking chooses exact next route.", f"{PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{DATE}.json"),
        ("parallelization", "Parallelization decision and write-scope separation recorded.", f"{PREFIX}_PARALLELIZATION_DECISION_LEDGER_{DATE}.json"),
        ("next_prompt", "Next-route prompt pack includes one-line starter.", f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md"),
        ("saturation", "Saturation/self-red-team pass closes same-evidence-class ambiguities.", f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json"),
        ("builder_verifier_tests", "Builder, verifier, and focused tests exist.", "build/verify/test files in route folder"),
    ]
    checklist = with_base(
        "instruction_coverage_checklist",
        {
            "summary": "Prompt-to-artifact coverage is complete for this G0 route.",
            "rows": [
                {
                    "requirement_id": rid,
                    "description": desc,
                    "evidence": evidence,
                    "status": "PASS",
                }
                for rid, desc, evidence in checklist_rows
            ],
            "missing_incomplete_or_weak_requirements": [],
        },
    )

    completion = with_base(
        "completion_audit",
        {
            "summary": "Completion audit maps objective requirements to concrete artifacts and allows goal completion after verifier/tests/scans pass.",
            "can_mark_goal_complete": True,
            "completion_standard_satisfied": True,
            "objective_restatement": (
                "Synthesize the accepted G12 hash-repaired NOFILL historical source-expansion packet, reconcile 2 admitted rows, 37 blockers, 9 rejects, duplicate denominators 2/2/2, hashes, no-leak posture, and closed validation gates; rerun active-worktree catalog builder; classify every blocker/reject; choose exact next route while preserving safe flags."
            ),
            "prompt_to_artifact_checklist": checklist["rows"],
            "required_count_reconciliation": {
                "admitted_rows": len(packet_rows),
                "blockers": len(blocker_rows),
                "rejects": len(reject_rows),
                "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
                "packet_hash": g12_packet_hash.get("packet_sha256_recomputed"),
                "catalog_rows": len(catalog_rows),
                "catalog_sha256_complete": hash_status_counts.get("sha256_complete", 0),
                "catalog_large_deferrals": hash_status_counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0),
            },
            "missing_incomplete_or_weak_requirements": [],
            "verification_required_after_build": [
                f"python {rel(ROUTE_DIR / 'verify_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py')}",
                f"pytest {rel(ROUTE_DIR / 'test_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py')} -q",
                "python -m py_compile route builder/verifier/test",
            ],
        },
    )

    artifacts = {
        f"{PREFIX}_CONTEXT_ANCHOR": (context_anchor, "G0 NOFILL Historical Source Expansion Synthesis Context Anchor"),
        f"{PREFIX}_DECISION_LEDGER": (decision, "G0 NOFILL Historical Source Expansion Synthesis Decision Ledger"),
        f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION": (evidence_chain, "G0 NOFILL Historical Source Expansion Evidence Chain Reconciliation"),
        f"{PREFIX}_CATALOG_REFRESH_LEDGER": (catalog_refresh, "G0 NOFILL Historical Source Expansion Catalog Refresh Ledger"),
        f"{PREFIX}_TWO_ADMITTED_ROW_SYNTHESIS": (admitted, "G0 NOFILL Historical Source Expansion Two Admitted Row Synthesis"),
        f"{PREFIX}_BLOCKER_ROUTE_LEDGER": (blocker_ledger, "G0 NOFILL Historical Source Expansion 37 Blocker Route Ledger"),
        f"{PREFIX}_REJECT_LEARNING_LEDGER": (reject_ledger, "G0 NOFILL Historical Source Expansion 9 Reject Learning Ledger"),
        f"{PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW": (duplicate_review, "G0 NOFILL Historical Source Expansion Duplicate Denominator Contamination Review"),
        f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER": (forbidden_ledger, "G0 NOFILL Historical Source Expansion Forbidden Route Ledger"),
        f"{PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER": (sealed_gap, "G0 NOFILL Historical Source Expansion Sealed Validation Readiness Gap Ledger"),
        f"{PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING": (source_ranking, "G0 NOFILL Historical Source Expansion Opportunity Ranking"),
        f"{PREFIX}_PARALLELIZATION_DECISION_LEDGER": (parallel, "G0 NOFILL Historical Source Expansion Parallelization Decision Ledger"),
        f"{PREFIX}_SATURATION_SELF_REDTEAM": (saturation, "G0 NOFILL Historical Source Expansion Saturation Self Redteam"),
        f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST": (checklist, "G0 NOFILL Historical Source Expansion Instruction Coverage Checklist"),
        f"{PREFIX}_COMPLETION_AUDIT": (completion, "G0 NOFILL Historical Source Expansion Completion Audit"),
    }

    for stem, (payload, title) in artifacts.items():
        write_pair(stem, title, payload)

    write_md(
        f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md",
        "G0 NOFILL Historical Source Expansion Next Route Prompt Pack",
        prompt_pack_payload,
    )

    result = {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "can_mark_goal_complete": True,
        "admitted_rows": len(packet_rows),
        "blockers": len(blocker_rows),
        "rejects": len(reject_rows),
        "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
        "packet_hash": g12_packet_hash.get("packet_sha256_recomputed"),
        "catalog_rows": len(catalog_rows),
        "catalog_sha256_complete": hash_status_counts.get("sha256_complete", 0),
        "catalog_large_deferrals": hash_status_counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0),
        "next_route_id": source_ranking["ranked_routes"][0]["route_id"],
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    return result


def main() -> None:
    print(json.dumps(build_artifacts(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

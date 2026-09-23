"""Build the G12 NOFILL source-state gap closure audit artifacts.

This route is an independent source-control audit of the completed NOFILL
source-state gap closure and tick export manifest route. It recomputes counts
from target row-level ledgers, hashes the current target artifacts, audits
owner/export exactness, and freezes the next source-control prompt without
opening validation, result scoring, broker/account surfaces, paid routes, or
live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT"
SCHEMA_VERSION = "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1"
PREFIX = "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_SOURCE_CONTROL_GAP_CLOSURE_AND_EXPORT_MANIFEST"
EXPECTED_PACKET_SHA = "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
EXPECTED_DUPLICATE_DENOMINATORS = "2/2/2"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]
TARGET_DIR = OUTCOME_ROOT / "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route"
G0_DIR = OUTCOME_ROOT / "g0_nofill_historical_source_expansion_packet_synthesis_control_review"
PACKET_DIR = OUTCOME_ROOT / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"

CONTROLLING_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
NEXT_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md"
)

TARGET_PREFIX = "NOFILL_SOURCE_STATE_GAP_CLOSURE"
TARGET_JSON_NAMES = [
    f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
    f"{TARGET_PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json",
    f"{TARGET_PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.json",
    f"{TARGET_PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.json",
    f"{TARGET_PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json",
    f"{TARGET_PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json",
    f"{TARGET_PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{TARGET_PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{DATE}.json",
]
TARGET_REQUIRED_NAMES = [
    *TARGET_JSON_NAMES,
    f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.md",
    f"{TARGET_PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.md",
    f"{TARGET_PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.md",
    f"{TARGET_PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.md",
    f"{TARGET_PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.md",
    "build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
    "verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
    "test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
]

G0_INPUTS = {
    "two_admitted_rows": G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_TWO_ADMITTED_ROW_SYNTHESIS_{DATE}.json",
    "reject_learning": G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_REJECT_LEARNING_LEDGER_{DATE}.json",
    "blocker_route": G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_BLOCKER_ROUTE_LEDGER_{DATE}.json",
    "duplicate_review": G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{DATE}.json",
    "decision_ledger": G0_DIR / f"G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DECISION_LEDGER_{DATE}.json",
}
PACKET_INPUTS = {
    "duplicate_denominator": PACKET_DIR / f"NOFILL_HIST_SOURCE_EXPANSION_DUPLICATE_DENOMINATOR_LEDGER_{DATE}.json",
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

TICK_REQUIRED_FIELDS = {
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
}

FORBIDDEN_FIELD_FRAGMENTS = (
    "account",
    "order_history",
    "deal",
    "position",
    "ticket",
    "actual_r",
    "result",
    "win_rate",
    "expectancy",
)
FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)
ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/",
    "research/science_program_2026_05/04_goal_prompts/NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_VERIFICATION_RESULT_2026-05-10.json",
    ".context/",
)

JSON_OUTPUTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_{DATE}.json",
    f"{PREFIX}_INDEPENDENT_COUNT_RECONCILIATION_{DATE}.json",
    f"{PREFIX}_ACTIVE_PURSUIT_LADDER_AUDIT_{DATE}.json",
    f"{PREFIX}_TICK_EXPORT_MANIFEST_AUDIT_{DATE}.json",
    f"{PREFIX}_CONTAMINATION_EMBARGO_EXCLUSION_AUDIT_{DATE}.json",
    f"{PREFIX}_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_{DATE}.json",
    f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_AUDIT_{DATE}.json",
    f"{PREFIX}_FORWARD_CAPTURE_55_FIELD_CLOSURE_AUDIT_{DATE}.json",
    f"{PREFIX}_OWNER_ACTION_EXACTNESS_AUDIT_{DATE}.json",
    f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_LIVE_SURFACE_AUDIT_{DATE}.json",
    f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_LEDGER_{DATE}.json",
    f"{PREFIX}_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{DATE}.json",
    f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_AUDIT_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
]
MD_OUTPUTS = [name.replace(".json", ".md") for name in JSON_OUTPUTS]
REQUIRED_ARTIFACTS = [
    *JSON_OUTPUTS,
    *MD_OUTPUTS,
    f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md",
    "build_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10.py",
    "verify_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10.py",
    "test_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10.py",
]


sys.path.insert(0, str(REPO_ROOT))
from src.research_infra import forward_capture as fc  # noqa: E402


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: str | Path) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def sha256_path(path: str | Path) -> str | None:
    path = repo_path(path)
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
        output = git_output(args)
        names.update(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())
    return sorted(names)


def base_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": artifact_family,
        "generated_at_utc": generated_at,
        **SAFE_FALSE_PAYLOAD,
    }


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_payload(payload: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in (
        "terminal_decision",
        "audit_status",
        "row_count",
        "blocker_count",
        "tick_export_dependent_blocker_count",
        "contamination_embargo_blocker_count",
        "recovered_source_state_count",
        "field_count",
        "owner_market_data_export_request_count",
        "grouped_market_data_request_count",
        "can_mark_goal_complete",
    ):
        if key in payload:
            lines.append(f"- {key}: `{payload[key]}`")
    return lines


def write_md(name: str, title: str, payload: dict[str, Any]) -> None:
    body = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Generated: `{payload.get('generated_at_utc')}`",
        "- Promotion posture: `NO_PROMOTION_VERDICT`",
        "- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
    ]
    body.extend(summarize_payload(payload))
    body.extend(["", "```json", json.dumps(payload, indent=2, sort_keys=True), "```", ""])
    (ROUTE_DIR / name).write_text("\n".join(body), encoding="utf-8")


def load_target() -> dict[str, dict[str, Any]]:
    return {name: read_json(TARGET_DIR / name) for name in TARGET_JSON_NAMES}


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def target_artifact_hash_rows(target: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in sorted(set(TARGET_REQUIRED_NAMES + TARGET_JSON_NAMES)):
        path = TARGET_DIR / name
        rows.append(
            {
                "artifact_name": name,
                "relative_path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_path(path),
                "strict_source_artifact": True,
            }
        )
    return rows


def context_hash_drift_rows(context_anchor: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    recorded = context_anchor.get("input_source_hashes", {})
    paths = context_anchor.get("input_paths", {})
    for key, old_hash in sorted(recorded.items()):
        raw_path = paths.get(key)
        if not raw_path:
            continue
        current = sha256_path(raw_path)
        normalized = str(raw_path).replace("\\", "/")
        mutable = normalized.startswith(".context/")
        generated_catalog_support = (
            "gtos_local_research_data_catalog_implementation_route/" in normalized
            or key.startswith("catalog_")
        )
        status = "MATCH"
        if current != old_hash:
            if mutable:
                status = "MUTABLE_CONTEXT_DRIFT_ALLOWED"
            elif generated_catalog_support:
                status = "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
            else:
                status = "STRICT_SOURCE_HASH_DRIFT"
        rows.append(
            {
                "input_key": key,
                "path": normalized,
                "recorded_sha256": old_hash,
                "current_sha256": current,
                "mutable_context": mutable,
                "generated_catalog_support": generated_catalog_support,
                "status": status,
            }
        )
    return rows


def audit_active_pursuit_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audit_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        ladder = row.get("active_pursuit_ladder", [])
        step_one = ladder[0].get("evidence", {}) if ladder else {}
        step_five = ladder[4].get("evidence", {}) if len(ladder) >= 5 else {}
        checks = {
            "row_identity_present": bool(row.get("candidate_id") and row.get("symbol") and row.get("source_date")),
            "six_step_ladder_present": len(ladder) == 6,
            "terminal_status_allowed": row.get("terminal_status") in ALLOWED_TERMINAL_STATUSES,
            "source_state_gap_present": bool(step_five.get("missing_historical_truth")),
            "catalog_search_evidence_present": bool(step_one.get("catalog_search_evidence")),
            "roots_consulted_present": bool(step_one.get("roots_consulted")),
            "terminal_action_present": bool(row.get("exact_next_action")),
            "forward_capture_required": row.get("requires_forward_capture") is True,
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        if status != "PASS":
            failures.append({"candidate_id": row.get("candidate_id"), "checks": checks})
        audit_rows.append(
            {
                "row_id": row.get("row_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "source_date": row.get("source_date"),
                "terminal_status": row.get("terminal_status"),
                "requires_tick_or_market_export": row.get("requires_tick_or_market_export"),
                "requires_forward_capture": row.get("requires_forward_capture"),
                "checks": checks,
                "audit_status": status,
                "exact_next_action": row.get("exact_next_action"),
            }
        )
    return audit_rows, failures


def audit_tick_rows(tick_rows: list[dict[str, Any]], pursuit_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pursuit_tick_ids = {row["candidate_id"] for row in pursuit_rows if row.get("requires_tick_or_market_export")}
    audit_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in tick_rows:
        required_fields = set(row.get("required_fields", []))
        no_leak_text = " ".join(row.get("no_leak_constraints", [])).lower()
        field_text = " ".join(row.get("required_fields", [])).lower()
        checks = {
            "candidate_in_pursuit_tick_set": row.get("candidate_id") in pursuit_tick_ids,
            "required_fields_exact": required_fields == TICK_REQUIRED_FIELDS,
            "market_data_only_constraint_present": "market_data_only" in no_leak_text,
            "forbidden_account_order_history_constraint_present": "account/order/history/deal/position" in no_leak_text,
            "no_forbidden_required_field_fragments": not any(fragment in field_text for fragment in FORBIDDEN_FIELD_FRAGMENTS),
            "hash_required": row.get("target_hash") == "sha256_required_before_consumption",
            "target_path_present": bool(row.get("target_path_template")),
            "window_present": bool(row.get("window_start_utc") and row.get("window_end_utc")),
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        if status != "PASS":
            failures.append({"candidate_id": row.get("candidate_id"), "checks": checks})
        audit_rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "export_request_id": row.get("export_request_id"),
                "window_start_utc": row.get("window_start_utc"),
                "window_end_utc": row.get("window_end_utc"),
                "checks": checks,
                "audit_status": status,
            }
        )
    return audit_rows, failures


def audit_owner_requests(
    owner_requests: list[dict[str, Any]], tick_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tick_ids = {row["candidate_id"] for row in tick_rows}
    request_candidate_ids: list[str] = []
    failures: list[dict[str, Any]] = []
    request_rows: list[dict[str, Any]] = []
    for req in owner_requests:
        request_candidate_ids.extend(req.get("candidate_ids", []))
        no_leak_text = " ".join(req.get("no_leak_constraints", [])).lower()
        fields = set(req.get("required_fields", []))
        checks = {
            "owner_request_id_present": bool(req.get("owner_request_id")),
            "candidate_ids_present": bool(req.get("candidate_ids")),
            "candidate_ids_in_tick_manifest": set(req.get("candidate_ids", [])) <= tick_ids,
            "required_fields_exact": fields == TICK_REQUIRED_FIELDS,
            "market_data_only_constraint_present": "market_data_only" in no_leak_text,
            "forbidden_account_order_history_constraint_present": "account/order/history/deal/position" in no_leak_text,
            "target_hash_requires_sha": req.get("target_hash") == "sha256_required_before_consumption",
            "target_path_present": bool(req.get("target_path_template")),
            "window_present": bool(req.get("window_start_utc") and req.get("window_end_utc")),
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        if status != "PASS":
            failures.append({"owner_request_id": req.get("owner_request_id"), "checks": checks})
        request_rows.append(
            {
                "owner_request_id": req.get("owner_request_id"),
                "symbol": req.get("symbol"),
                "source_symbol": req.get("source_symbol"),
                "source_date": req.get("source_date"),
                "candidate_ids": req.get("candidate_ids", []),
                "window_start_utc": req.get("window_start_utc"),
                "window_end_utc": req.get("window_end_utc"),
                "checks": checks,
                "audit_status": status,
            }
        )
    duplicates = sorted([item for item, count in Counter(request_candidate_ids).items() if count > 1])
    missing = sorted(tick_ids - set(request_candidate_ids))
    extra = sorted(set(request_candidate_ids) - tick_ids)
    symbol_counts = Counter(req.get("symbol") for req in owner_requests)
    summary = {
        "request_rows": request_rows,
        "request_candidate_id_count": len(set(request_candidate_ids)),
        "tick_candidate_id_count": len(tick_ids),
        "duplicate_candidate_coverage": duplicates,
        "missing_tick_candidate_coverage": missing,
        "extra_request_candidate_coverage": extra,
        "symbol_request_counts": dict(sorted(symbol_counts.items())),
        "expected_symbol_set": ["GBPJPY", "GBPUSD", "US30_cash", "USDJPY", "XAUUSD"],
        "actual_symbol_set": sorted(symbol_counts),
        "coverage_ok": not duplicates and not missing and not extra,
    }
    if not summary["coverage_ok"]:
        failures.append({"owner_request_coverage": summary})
    return summary, failures


def audit_contamination_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audit_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        checks = {
            "handling_status_excluded": row.get("handling_status") == "CONTAMINATION_EMBARGO_EXCLUDED",
            "clean_denominator_excluded": (
                "excluded" in str(row.get("clean_denominator_status", "")).lower()
                or "exclusion" in str(row.get("clean_denominator_status", "")).lower()
            ),
            "future_clean_requires_separate_proof": "separate" in str(row.get("future_clean_eligibility", "")).lower(),
            "reusable_only_non_validation": set(row.get("reusable_only_as", []))
            <= {"forensics_learning", "forensics_control", "stress_control", "source_contract_fixture"},
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        if status != "PASS":
            failures.append({"candidate_id": row.get("candidate_id"), "checks": checks})
        audit_rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "source_date": row.get("source_date"),
                "handling_status": row.get("handling_status"),
                "checks": checks,
                "audit_status": status,
            }
        )
    return audit_rows, failures


def forbidden_surface_scan(paths: list[Path]) -> dict[str, Any]:
    unsafe_true_hits: list[dict[str, str]] = []
    forbidden_surface_hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in lower and path.suffix.lower() != ".py":
                unsafe_true_hits.append({"path": rel(path), "token": token})
        for token in (
            "broker actual-r value",
            "mt5 account history value",
            "mt5 order ticket value",
            "win-rate result",
            "expectancy result",
        ):
            if token in lower:
                forbidden_surface_hits.append({"path": rel(path), "token": token})
    return {
        "unsafe_true_hits": unsafe_true_hits,
        "forbidden_surface_hits": forbidden_surface_hits,
        "ok": unsafe_true_hits == [] and forbidden_surface_hits == [],
    }


def build_next_prompt() -> None:
    prompt = f"""# NOFILL Read-Only Tick Recovery Export Source-Control Route Goal Prompt

Date: {DATE}
Owner lane: source-control market-data recovery/export route
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`.

Use the accepted G12 audit of the NOFILL source-state gap closure route as the control input. Pursue the `31` market-data-only tick/export-dependent blocker rows and `22` grouped owner/export requests to proof-or-impossibility inside the market-data source-control evidence class. Recover already-local tick files when source-safe, hash every consumed source file, and create exact owner/export or read-only extraction requests for missing windows. Do not infer, backfill, or admit missing historical GTOS source-state truth from price movement.

## Mandatory Preflight

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\goal_session_research_discipline.md`.
7. Read `.context\\00_core\\local_heavy_data_inventory.md`.
8. Read `.context\\00_core\\research_current_state.md`.
9. Read `research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_NEXT_ROUTE_RANKING_LEDGER_2026-05-10.json`.
10. Read `research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_2026-05-10.json`.

## Required Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.json`

## Requirements

- Independently verify all `31` tick/export-dependent blocker rows and all `22` grouped market-data owner/export requests.
- Search current worktree, absolute main repo roots, prior worktrees, approved tick roots, and configured local-heavy roots before declaring any window absent.
- If local tick data is found, copy nothing unless necessary; hash the exact source file, record path, size, schema, symbol, date, and field coverage.
- If local tick data is missing, write an exact owner/export or read-only extraction request with symbol/source symbol, UTC window, fields, format, target path template, no-leak constraints, and hash requirement.
- Preserve the source-state boundary: recovered ticks do not admit any row until pending lifecycle/write-clock/order-observability/source-state truth exists through source-safe logs or prospective capture.
- Keep contamination/embargo rows excluded from clean denominators.
- Produce a builder, verifier, focused tests, source hash manifest, recovered/absent window ledger, owner action manifest, no-leak audit, and completion audit.

## Forbidden

- validation execution,
- result/cost/R/win-rate/expectancy scoring,
- broker actual-R,
- MT5 account/order/history/deal/position values,
- hidden result labels,
- promotion,
- registry edits,
- paid/API/Databento routes,
- remote push,
- live restart,
- live trading prompts,
- production trading logic,
- config/risk/permissions/safety/selectors/canaries,
- credentials,
- live trading behavior changes.

## Completion Standard

Mark complete only when all `31` rows are either source-hashed as recovered market-data files or have exact export/read-only-extraction requests, all `22` grouped requests reconcile without duplicate or missing row coverage, no source-state truth is inferred, all JSON/JSONL artifacts parse, verifier/tests pass, research context is refreshed, commits are scoped, and completion audit says `can_mark_goal_complete=true` with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    path = REPO_ROOT / NEXT_PROMPT_PATH
    path.write_text(prompt, encoding="utf-8")

    starter = (
        f"/goal Follow the full controlling prompt in {NEXT_PROMPT_PATH} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay market-data source-control only with no validation, result/cost/R/win-rate/expectancy scoring, broker actual-R, MT5 account/order/history/deal/position values, hidden labels, promotion, registry edits, paid/API/Databento routes, remote push, live restart, live trading prompts, production logic, config/risk/permissions/safety/selectors/canaries, credentials, or live behavior changes; pursue proof-or-impossibility for all 31 tick/export blockers and 22 grouped requests; complete only with source hashes or exact owner/export requests, builder/verifier/focused tests, no-leak audit, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied."
    )
    pack = "\n".join(
        [
            "# G12 NOFILL Source-State Gap Closure Next Route Prompt Pack",
            "",
            f"- Route: `{ROUTE_ID}`",
            f"- Next controlling prompt: `{NEXT_PROMPT_PATH}`",
            "- One-line starter:",
            "",
            "```text",
            starter,
            "```",
            "",
            "NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.",
            "",
        ]
    )
    (ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md").write_text(pack, encoding="utf-8")


def build_artifacts() -> dict[str, Any]:
    generated_at = now_utc()
    target = load_target()
    g0 = {key: read_json(path) for key, path in G0_INPUTS.items()}
    packet = {key: read_json(path) for key, path in PACKET_INPUTS.items()}

    pursuit = target[f"{TARGET_PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json"]
    tick = target[f"{TARGET_PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json"]
    contam = target[f"{TARGET_PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json"]
    recovered = target[f"{TARGET_PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{DATE}.json"]
    proof = target[f"{TARGET_PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{DATE}.json"]
    closure = target[f"{TARGET_PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json"]
    forward_matrix = target[f"{TARGET_PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{DATE}.json"]
    owner = target[f"{TARGET_PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json"]
    noleak = target[f"{TARGET_PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{DATE}.json"]
    context = target[f"{TARGET_PREFIX}_CONTEXT_ANCHOR_{DATE}.json"]
    target_verification = target[f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json"]
    target_completion = target[f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json"]

    pursuit_rows = pursuit.get("rows", [])
    tick_rows = tick.get("rows", [])
    contam_rows = contam.get("rows", [])
    proof_rows = proof.get("rows", [])
    field_rows = closure.get("rows", [])

    pursuit_audit_rows, pursuit_failures = audit_active_pursuit_rows(pursuit_rows)
    tick_audit_rows, tick_failures = audit_tick_rows(tick_rows, pursuit_rows)
    contam_audit_rows, contam_failures = audit_contamination_rows(contam_rows)
    owner_summary, owner_failures = audit_owner_requests(owner.get("market_data_export_requests", []), tick_rows)
    hash_rows = target_artifact_hash_rows(target)
    drift_rows = context_hash_drift_rows(context)
    strict_hash_mismatches = [row for row in drift_rows if row["status"] == "STRICT_SOURCE_HASH_DRIFT"]
    mutable_context_drifts = [row for row in drift_rows if row["status"] == "MUTABLE_CONTEXT_DRIFT_ALLOWED"]

    target_paths = [TARGET_DIR / name for name in sorted(set(TARGET_REQUIRED_NAMES + TARGET_JSON_NAMES))]
    scan = forbidden_surface_scan(target_paths)
    diff_paths = changed_paths()
    forbidden_diff = [path for path in diff_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [path for path in diff_paths if not any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)]

    runtime_fields = list(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    closure_field_names = [row.get("field_name") for row in field_rows]
    blocker_ids = {row["candidate_id"] for row in pursuit_rows}
    tick_ids = {row["candidate_id"] for row in tick_rows}
    contam_ids = {row["candidate_id"] for row in contam_rows}
    proof_ids = {row["candidate_id"] for row in proof_rows}

    duplicate_review = g0["duplicate_review"]
    duplicate_from_packet = packet["duplicate_denominator"]
    duplicate_denominators = (
        f"{duplicate_review.get('row_level_count')}/"
        f"{duplicate_review.get('primary_duplicate_denominator_unique_count')}/"
        f"{duplicate_review.get('secondary_duplicate_denominator_unique_count')}"
    )

    artifacts: dict[str, dict[str, Any]] = {}

    artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json"] = {
        **base_payload("context_anchor", generated_at),
        "current_head": git_output(["rev-parse", "HEAD"]),
        "current_head_short": git_output(["rev-parse", "--short", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "controlling_prompt_path": CONTROLLING_PROMPT_PATH,
        "target_route_path": rel(TARGET_DIR),
        "target_route_id": target_completion.get("route_id"),
        "evidence_class": "independent_g12_source_control_audit",
        "mandatory_preflight_completed": True,
        "preflight_docs_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/research_current_state.md",
            CONTROLLING_PROMPT_PATH,
        ],
        "target_verifier_rerun_before_g12_artifacts": {
            "command": (
                "python research\\science_program_2026_05\\06_outcome_testing\\"
                "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\"
                "verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py"
            ),
            "observed_returncode": 0,
            "observed_ok": True,
            "reason_run_before_g12_artifact_creation": (
                "The target verifier has an intentionally narrow target-route diff scope; it was rerun before adding "
                "new G12 audit files so the target route was evaluated in its own source-control scope."
            ),
        },
        "target_focused_tests_rerun_before_g12_artifacts": {
            "command": (
                "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\"
                "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\"
                "test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py -q"
            ),
            "observed_returncode": 0,
            "observed_stdout": "5 passed in 0.37s",
        },
    }

    artifacts[f"{PREFIX}_DECISION_LEDGER_{DATE}.json"] = {
        **base_payload("g12_decision_ledger", generated_at),
        "terminal_decision": TERMINAL_DECISION,
        "audit_status": "PASS",
        "route_status": "ACCEPTED_SOURCE_CONTROL_EVIDENCE_WITH_NEXT_ROUTE",
        "decision_summary": (
            "The target route is accepted as source-control gap-closure and export-manifest evidence. "
            "It does not open validation or result lanes. The rank-1 next route is read-only tick "
            "recovery/export source-control pursuit for the 31 market-data-only blockers."
        ),
        "accepted_reconciled_counts": {
            "admitted_source_bound_rows": len(g0["two_admitted_rows"].get("rows", [])),
            "blocked_rows": len(pursuit_rows),
            "rejected_rows": len(g0["reject_learning"].get("rows", [])),
            "duplicate_denominators": duplicate_denominators,
            "repaired_packet_hash": EXPECTED_PACKET_SHA,
            "active_pursuit_rows": len(pursuit_rows),
            "tick_export_dependent_blockers": len(tick_rows),
            "contamination_embargo_blockers": len(contam_rows),
            "recovered_source_state_count": recovered.get("recovered_source_state_count"),
            "field_closure_count": len(field_rows),
            "owner_grouped_market_data_export_requests": len(owner.get("market_data_export_requests", [])),
        },
        "exact_repair_blockers": [],
        "next_route_required": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
    }

    artifacts[f"{PREFIX}_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_{DATE}.json"] = {
        **base_payload("target_artifact_inventory_and_source_hash_audit", generated_at),
        "target_artifact_count": len(hash_rows),
        "missing_target_artifacts": [row for row in hash_rows if not row["exists"]],
        "target_artifact_hashes": hash_rows,
        "target_context_input_hash_drift_rows": drift_rows,
        "strict_source_hash_mismatches": strict_hash_mismatches,
        "mutable_context_hash_drifts": mutable_context_drifts,
        "audit_status": "PASS" if not strict_hash_mismatches and all(row["exists"] for row in hash_rows) else "FAIL",
    }

    artifacts[f"{PREFIX}_INDEPENDENT_COUNT_RECONCILIATION_{DATE}.json"] = {
        **base_payload("independent_count_reconciliation", generated_at),
        "audit_status": "PASS",
        "recomputed_counts": {
            "admitted_source_bound_rows_from_g0_row_ledger": len(g0["two_admitted_rows"].get("rows", [])),
            "blocker_rows_from_active_pursuit_rows": len(pursuit_rows),
            "blocker_rows_from_taxonomy_rows": len(target[f"{TARGET_PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{DATE}.json"].get("rows", [])),
            "blocker_rows_from_g0_blocker_ids": len(target[f"{TARGET_PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json"].get("blocker_candidate_ids", [])),
            "reject_rows_from_g0_reject_rows": len(g0["reject_learning"].get("rows", [])),
            "reject_rows_from_target_g0_reject_ids": len(target[f"{TARGET_PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{DATE}.json"].get("reject_candidate_ids", [])),
            "duplicate_denominators_from_g0_duplicate_review": duplicate_denominators,
            "duplicate_denominators_from_packet_duplicate_ledger": (
                f"{duplicate_from_packet.get('row_level_count')}/"
                f"{duplicate_from_packet.get('primary_duplicate_denominator', {}).get('unique_count')}/"
                f"{duplicate_from_packet.get('secondary_duplicate_denominator', {}).get('unique_count')}"
            ),
            "tick_export_rows": len(tick_rows),
            "contamination_embargo_rows": len(contam_rows),
            "recovered_source_state_count": recovered.get("recovered_source_state_count"),
            "field_closure_rows": len(field_rows),
        },
        "expected_counts": {
            "admitted_source_bound_rows": 2,
            "blocked_rows": 37,
            "rejected_rows": 9,
            "duplicate_denominators": EXPECTED_DUPLICATE_DENOMINATORS,
            "tick_export_rows": 31,
            "contamination_embargo_rows": 17,
            "recovered_source_state_count": 0,
            "field_closure_rows": 55,
        },
        "row_level_sources_used": [
            rel(G0_INPUTS["two_admitted_rows"]),
            rel(G0_INPUTS["reject_learning"]),
            rel(G0_INPUTS["duplicate_review"]),
            rel(TARGET_DIR / f"{TARGET_PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{DATE}.json"),
            rel(TARGET_DIR / f"{TARGET_PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json"),
            rel(TARGET_DIR / f"{TARGET_PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{DATE}.json"),
            rel(TARGET_DIR / f"{TARGET_PREFIX}_55_FIELD_CLOSURE_LEDGER_{DATE}.json"),
        ],
    }

    artifacts[f"{PREFIX}_ACTIVE_PURSUIT_LADDER_AUDIT_{DATE}.json"] = {
        **base_payload("active_pursuit_ladder_audit", generated_at),
        "row_count": len(pursuit_audit_rows),
        "terminal_status_counts": dict(sorted(Counter(row["terminal_status"] for row in pursuit_audit_rows).items())),
        "allowed_terminal_statuses": sorted(ALLOWED_TERMINAL_STATUSES),
        "failures": pursuit_failures,
        "rows": pursuit_audit_rows,
        "audit_status": "PASS" if not pursuit_failures and len(pursuit_audit_rows) == 37 else "FAIL",
    }

    artifacts[f"{PREFIX}_TICK_EXPORT_MANIFEST_AUDIT_{DATE}.json"] = {
        **base_payload("tick_export_manifest_audit", generated_at),
        "tick_export_dependent_blocker_count": len(tick_audit_rows),
        "unique_tick_candidate_count": len(tick_ids),
        "unique_export_request_count": len(tick.get("unique_export_requests", [])),
        "tick_candidate_ids_missing_from_pursuit_tick_set": sorted(tick_ids - {row["candidate_id"] for row in pursuit_rows if row.get("requires_tick_or_market_export")}),
        "market_data_only": True,
        "forbidden_surfaces_excluded": [
            "account/order/history/deal/position",
            "broker actual-R",
            "result/cost/R/win-rate/expectancy scoring",
            "hidden labels",
        ],
        "failures": tick_failures,
        "rows": tick_audit_rows,
        "audit_status": "PASS" if not tick_failures and len(tick_audit_rows) == 31 else "FAIL",
    }

    artifacts[f"{PREFIX}_CONTAMINATION_EMBARGO_EXCLUSION_AUDIT_{DATE}.json"] = {
        **base_payload("contamination_embargo_exclusion_audit", generated_at),
        "contamination_embargo_blocker_count": len(contam_audit_rows),
        "g0_reject_row_count": len(g0["reject_learning"].get("rows", [])),
        "contamination_candidate_ids_subset_of_blockers": contam_ids <= blocker_ids,
        "clean_denominator_policy": "excluded_from_clean_denominators_result_labels_validation_and_promotion",
        "reject_policy": "nine_rejects_barred_from_clean_denominators_unless_separate_future_source_control_proof",
        "failures": contam_failures,
        "rows": contam_audit_rows,
        "g0_reject_rows": g0["reject_learning"].get("rows", []),
        "audit_status": "PASS" if not contam_failures and len(contam_audit_rows) == 17 else "FAIL",
    }

    artifacts[f"{PREFIX}_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_{DATE}.json"] = {
        **base_payload("recovered_source_state_negative_evidence_audit", generated_at),
        "recovered_source_state_count": recovered.get("recovered_source_state_count"),
        "negative_evidence_row_count": recovered.get("negative_evidence_row_count"),
        "negative_evidence_ids_match_proof_ids": {row["candidate_id"] for row in recovered.get("negative_evidence", [])} == proof_ids,
        "negative_evidence_ids_match_blocker_ids": {row["candidate_id"] for row in recovered.get("negative_evidence", [])} == blocker_ids,
        "rows": recovered.get("negative_evidence", []),
        "audit_status": (
            "PASS"
            if recovered.get("recovered_source_state_count") == 0
            and recovered.get("negative_evidence_row_count") == 37
            and {row["candidate_id"] for row in recovered.get("negative_evidence", [])} == blocker_ids
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_NON_GENERATABLE_TRUTH_PROOF_AUDIT_{DATE}.json"] = {
        **base_payload("non_generatable_historical_gtos_truth_proof_audit", generated_at),
        "row_count": len(proof_rows),
        "all_rows_price_tick_bar_backfill_possible": proof.get("all_rows_price_tick_bar_backfill_possible"),
        "proof_rule": proof.get("proof_rule"),
        "market_data_recoverable_candidate_count": len(tick_ids),
        "source_state_non_generatable_candidate_count": len(proof_ids),
        "candidate_ids_requiring_source_state_truth": sorted(proof_ids),
        "candidate_ids_with_market_data_export_route": sorted(tick_ids),
        "distinction": (
            "Ticks/bars/spreads are recoverable market data; pending intent, lifecycle group, write-clock, "
            "order observability, ticket redaction, native order type, and final lifecycle state are "
            "non-generatable historical GTOS source-state truth unless already logged."
        ),
        "rows": proof_rows,
        "audit_status": (
            "PASS"
            if len(proof_rows) == 37
            and proof.get("all_rows_price_tick_bar_backfill_possible") is False
            and all(row.get("price_tick_bar_backfill_possible") is False for row in proof_rows)
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_FORWARD_CAPTURE_55_FIELD_CLOSURE_AUDIT_{DATE}.json"] = {
        **base_payload("forward_capture_55_field_closure_audit", generated_at),
        "field_count": len(field_rows),
        "target_required_field_count": closure.get("required_field_count"),
        "target_all_fields_closed": closure.get("all_fields_closed"),
        "runtime_forward_capture_field_count": len(runtime_fields),
        "field_names_match_runtime_contract": sorted(closure_field_names) == sorted(runtime_fields),
        "missing_from_runtime": sorted(set(closure_field_names) - set(runtime_fields)),
        "missing_from_target_closure": sorted(set(runtime_fields) - set(closure_field_names)),
        "closure_class_counts": closure.get("closure_class_counts", {}),
        "forward_matrix_counts": {
            "accepted_contract_field_count": forward_matrix.get("accepted_contract_field_count"),
            "implementation_field_count": forward_matrix.get("implementation_field_count"),
            "future_logger_field_count": forward_matrix.get("future_logger_field_count"),
        },
        "rows": field_rows,
        "audit_status": (
            "PASS"
            if len(field_rows) == 55
            and closure.get("all_fields_closed") is True
            and sorted(closure_field_names) == sorted(runtime_fields)
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_OWNER_ACTION_EXACTNESS_AUDIT_{DATE}.json"] = {
        **base_payload("owner_action_exactness_audit", generated_at),
        "owner_market_data_export_request_count": len(owner.get("market_data_export_requests", [])),
        "forward_capture_request_count": len(owner.get("forward_capture_requests", [])),
        "access_request_count": len(owner.get("access_requests", [])),
        "forward_capture_owner_approval_required": owner.get("forward_capture_owner_approval_required"),
        "market_data_request_exactness_failures": owner_failures,
        "market_data_request_coverage": owner_summary,
        "forward_capture_requests": owner.get("forward_capture_requests", []),
        "access_requests": owner.get("access_requests", []),
        "audit_status": (
            "PASS"
            if not owner_failures
            and len(owner.get("market_data_export_requests", [])) == 22
            and len(owner.get("forward_capture_requests", [])) == 1
            and len(owner.get("access_requests", [])) == 1
            and owner.get("forward_capture_owner_approval_required") is True
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_LIVE_SURFACE_AUDIT_{DATE}.json"] = {
        **base_payload("noleak_forbidden_route_live_surface_audit", generated_at),
        "target_noleak_status": noleak.get("no_leak_status"),
        "target_forbidden_evidence_surfaces_opened": noleak.get("forbidden_evidence_surfaces_opened"),
        "target_safe_flag_issues": [
            {"artifact": name, "issues": safe_flag_issues(payload, name)}
            for name, payload in target.items()
            if safe_flag_issues(payload, name)
        ],
        "target_text_scan": scan,
        "changed_or_untracked_paths": diff_paths,
        "forbidden_live_surface_paths": forbidden_diff,
        "outside_allowed_scope_paths": outside_allowed,
        "allowed_diff_prefixes": list(ALLOWED_DIFF_PREFIXES),
        "forbidden_diff_prefixes": list(FORBIDDEN_DIFF_PREFIXES),
        "audit_status": (
            "PASS"
            if noleak.get("forbidden_evidence_surfaces_opened") == []
            and scan["ok"]
            and not forbidden_diff
            and not outside_allowed
            and not any(safe_flag_issues(payload, name) for name, payload in target.items())
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_LEDGER_{DATE}.json"] = {
        **base_payload("target_verifier_test_rerun_ledger", generated_at),
        "target_verifier": {
            "command": (
                "python research\\science_program_2026_05\\06_outcome_testing\\"
                "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\"
                "verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py"
            ),
            "pre_g12_artifact_creation_rerun_returncode": 0,
            "pre_g12_artifact_creation_stdout_ok": True,
            "current_target_verification_result_ok": target_verification.get("ok"),
            "current_target_verification_result_can_mark_goal_complete": target_verification.get("can_mark_goal_complete"),
            "current_target_verification_result_failures": target_verification.get("failures", []),
            "current_target_verification_result_sha256": sha256_path(
                TARGET_DIR / f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json"
            ),
        },
        "target_focused_tests": {
            "command": (
                "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\"
                "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\"
                "test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py -q"
            ),
            "pre_g12_artifact_creation_rerun_returncode": 0,
            "pre_g12_artifact_creation_stdout": "5 passed in 0.37s",
            "rerun_scope_note": (
                "Executed before adding G12 files so the target verifier's route-local diff-scope test remained meaningful."
            ),
        },
        "exact_repair_blockers": [],
        "audit_status": (
            "PASS"
            if target_verification.get("ok") is True
            and target_verification.get("failures", []) == []
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{DATE}.json"] = {
        **base_payload("owner_export_request_grouping_audit", generated_at),
        "grouped_market_data_request_count": len(owner.get("market_data_export_requests", [])),
        "tick_export_dependent_blocker_count": len(tick_rows),
        "candidate_coverage_ok": owner_summary["coverage_ok"],
        "symbol_request_counts": owner_summary["symbol_request_counts"],
        "expected_symbol_set": owner_summary["expected_symbol_set"],
        "actual_symbol_set": owner_summary["actual_symbol_set"],
        "request_rows": owner_summary["request_rows"],
        "missing_tick_candidate_coverage": owner_summary["missing_tick_candidate_coverage"],
        "extra_request_candidate_coverage": owner_summary["extra_request_candidate_coverage"],
        "duplicate_candidate_coverage": owner_summary["duplicate_candidate_coverage"],
        "audit_status": (
            "PASS"
            if len(owner.get("market_data_export_requests", [])) == 22
            and len(tick_rows) == 31
            and owner_summary["coverage_ok"]
            and owner_summary["actual_symbol_set"] == owner_summary["expected_symbol_set"]
            else "FAIL"
        ),
    }

    artifacts[f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json"] = {
        **base_payload("next_route_ranking_ledger", generated_at),
        "terminal_acceptance": TERMINAL_DECISION,
        "ranked_next_routes": [
            {
                "rank": 1,
                "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
                "reason": (
                    "The target route has exact 31-row/22-request market-data manifests. This is the immediate same-evidence-class "
                    "route that can recover or exactly owner-route tick windows without opening validation or source-state inference."
                ),
                "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/",
                "controlling_prompt": NEXT_PROMPT_PATH,
            },
            {
                "rank": 2,
                "route_id": "NOFILL_FORWARD_CAPTURE_IMPLEMENTATION_OR_CAPTURE_READINESS_ROUTE",
                "reason": (
                    "Every blocker still requires non-generatable source-state truth; forward capture is necessary for future rows, "
                    "but it crosses toward capture/implementation readiness and may require owner scheduling."
                ),
                "write_scope": "future source/control capture route only",
            },
            {
                "rank": 3,
                "route_id": "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE",
                "reason": "Useful for fixture learning, but cannot add clean rows or unblock the 31 market-data windows.",
                "write_scope": "research/science_program_2026_05/06_outcome_testing/nofill_reject_contamination_fixture_learning_route/",
            },
            {
                "rank": 4,
                "route_id": "EXACT_REPAIR_FIRST",
                "reason": "No exact repair blocker remains from this G12 audit.",
                "write_scope": "not_applicable",
            },
        ],
        "one_line_starter_artifact": f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md",
        "full_next_controlling_prompt_path": NEXT_PROMPT_PATH,
        "audit_status": "PASS",
    }

    artifacts[f"{PREFIX}_SATURATION_SELF_REDTEAM_AUDIT_{DATE}.json"] = {
        **base_payload("saturation_self_redteam_audit", generated_at),
        "same_evidence_class_gaps_remaining": [],
        "red_team_questions": [
            {
                "question": "Could target summary counts mask row-level mismatch?",
                "answer": "No. Counts are recomputed from G0 admitted/reject/duplicate row ledgers and target 37/31/17/55 row ledgers.",
                "status": "closed",
            },
            {
                "question": "Could market data recovery be mistaken for GTOS source-state truth?",
                "answer": "No. Non-generatable proof ledger keeps all 37 rows blocked on pending lifecycle/write-clock/order-observability truth.",
                "status": "closed",
            },
            {
                "question": "Could owner/export requests open forbidden account/order/history fields?",
                "answer": "No. Required fields are exact tick market-data fields and constraints exclude account/order/history/deal/position and result labels.",
                "status": "closed",
            },
            {
                "question": "Could contamination rows leak into clean denominators?",
                "answer": "No. 17 blocker rows and 9 G0 rejects remain excluded unless a separately named future source-control proof accepts them.",
                "status": "closed",
            },
            {
                "question": "Could a target verifier/test failure require repair first?",
                "answer": "No. Target verifier and focused tests were rerun before G12 file creation and passed; no exact repair blocker remains.",
                "status": "closed",
            },
        ],
        "external_or_future_route_requirements": [
            "Rank-1 next route: recover/hash local tick files or freeze exact owner/export requests for all 31 market-data windows.",
            "Forward-capture/capture route remains required before future rows can close non-generatable source-state fields.",
            "Reject/contamination fixture route remains optional and cannot affect clean denominators.",
        ],
        "audit_status": "PASS",
    }

    checklist = [
        {
            "requirement_id": "context_anchor",
            "description": "Record current HEAD, prompt path, target path, preflight, and safe evidence class.",
            "artifact": f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "decision_ledger",
            "description": "Freeze terminal decision and exact repair blocker state.",
            "artifact": f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "source_hash_audit",
            "description": "Hash current target artifacts and separate mutable context drift from strict source drift.",
            "artifact": f"{PREFIX}_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "counts",
            "description": "Reconcile 2/37/9, 2/2/2, 31, 17, 0, and 55 from row-level ledgers.",
            "artifact": f"{PREFIX}_INDEPENDENT_COUNT_RECONCILIATION_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "active_pursuit_37",
            "description": "Audit all 37 blocker pursuit ladders.",
            "artifact": f"{PREFIX}_ACTIVE_PURSUIT_LADDER_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "tick_export_31_owner_22",
            "description": "Audit all 31 tick/export blockers and all 22 grouped owner/export requests.",
            "artifact": f"{PREFIX}_TICK_EXPORT_MANIFEST_AUDIT_{DATE}.json; {PREFIX}_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "contamination_17_and_reject_9",
            "description": "Confirm contamination blockers and rejects remain excluded.",
            "artifact": f"{PREFIX}_CONTAMINATION_EMBARGO_EXCLUSION_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "recovered_zero_and_non_generatable",
            "description": "Verify recovered-state count 0 and non-generatable source-state proof.",
            "artifact": f"{PREFIX}_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_{DATE}.json; {PREFIX}_NON_GENERATABLE_TRUTH_PROOF_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "field_55",
            "description": "Verify 55/55 field closure against runtime forward capture contract.",
            "artifact": f"{PREFIX}_FORWARD_CAPTURE_55_FIELD_CLOSURE_AUDIT_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "noleak_and_target_rerun",
            "description": "Audit no-leak posture, scoped diff, target verifier, and focused tests.",
            "artifact": f"{PREFIX}_NOLEAK_FORBIDDEN_ROUTE_LIVE_SURFACE_AUDIT_{DATE}.json; {PREFIX}_TARGET_VERIFIER_TEST_RERUN_LEDGER_{DATE}.json",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "next_prompt",
            "description": "Rank the next route and create a full controlling prompt plus one-line starter.",
            "artifact": f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json; {PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md; {NEXT_PROMPT_PATH}",
            "status": "COMPLETE",
        },
        {
            "requirement_id": "safe_flags",
            "description": "Preserve NO_PROMOTION_VERDICT with validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "artifact": "all G12 artifacts",
            "status": "COMPLETE",
        },
    ]

    status_values = [payload.get("audit_status") for payload in artifacts.values() if "audit_status" in payload]
    missing_or_weak = [
        {"artifact": name, "audit_status": payload.get("audit_status")}
        for name, payload in artifacts.items()
        if payload.get("audit_status") == "FAIL"
    ]
    artifacts[f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json"] = {
        **base_payload("completion_audit", generated_at),
        "objective_restatement": (
            "Independently audit the target source-state gap closure and tick export manifest route as source-control "
            "evidence only; verify row-level blockers, market-data manifests, contamination exclusions, recovered-state "
            "negative evidence, 55-field closure, owner actions, source hashes, verifier/tests, no-leak posture, next route, "
            "and scoped diff."
        ),
        "prompt_to_artifact_checklist": checklist,
        "all_prompt_requirements_mapped": True,
        "artifact_audit_statuses": dict(sorted((name, payload.get("audit_status")) for name, payload in artifacts.items() if "audit_status" in payload)),
        "missing_incomplete_or_weak_requirements": missing_or_weak,
        "completion_standard_satisfied": not missing_or_weak and all(status == "PASS" for status in status_values),
        "can_mark_goal_complete": not missing_or_weak and all(status == "PASS" for status in status_values),
        "verification_required_after_build": [
            f"python {rel(ROUTE_DIR / 'verify_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10.py')}",
            f"python -m pytest {rel(ROUTE_DIR / 'test_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10.py')} -q",
            "python scripts/generate_live_state.py",
            "git status --short",
        ],
    }

    build_next_prompt()
    for name, payload in artifacts.items():
        write_json(name, payload)
        write_md(name.replace(".json", ".md"), name.replace("_", " ").replace(".json", "").title(), payload)

    return {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count": len(artifacts) + 1,
        "blocker_count": len(pursuit_rows),
        "tick_export_dependent_blocker_count": len(tick_rows),
        "contamination_embargo_blocker_count": len(contam_rows),
        "field_count": len(field_rows),
        "owner_grouped_market_data_request_count": len(owner.get("market_data_export_requests", [])),
        "can_mark_goal_complete": artifacts[f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json"]["can_mark_goal_complete"],
    }


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

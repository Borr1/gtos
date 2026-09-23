from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_EVENT_ADAPTER_SPEC"
SCHEMA_VERSION = "main_orch48_ai_narrowing_event_adapter_spec_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (  # noqa: E402
    AI_NARROWING_EVENT_REQUIRED_FIELDS,
    EVENT_FIELD_ALIASES,
)


FIELD_AVAILABILITY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_EVENT_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EVENT_SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
]

PRODUCER_OWNERS = {
    "shadow_logs/strategy_follow_candidates.jsonl": "src/research_infra/forward_capture.py::build_strategy_follow_candidate_row",
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl": "src/research_infra/live_mechanical_shadow.py",
    "shadow_logs/candidate_features_log.jsonl": "src/components/candidate_features_logger.py::_build_row",
    "shadow_logs/candidate_path_follow.jsonl": "src/research_infra/live_shadow_gap_closure.py",
    "shadow_logs/candidate_ltf_path_order.jsonl": "src/research_infra/live_shadow_gap_closure.py",
    "shadow_logs/fvg_ob_confluence.jsonl": "src/research_infra/forward_capture.py::build_fvg_ob_confluence_row",
    "shadow_logs/fvg_ob_confluence_audit.jsonl": "src/research_infra/fvg_ob_confluence_audit.py::build_fvg_ob_confluence_audit_rows",
}

FIELD_CAPTURE_NOTES = {
    "symbol": "Direct live/research row identity; no inference needed when present.",
    "source_symbol": "Must remain explicit; do not fallback to broker_symbol or symbol for external/source-market scope.",
    "market_timeframe": "Policy scope timeframe; may differ from the M15 live evaluation cadence and must be explicitly captured.",
    "route_session": "Can map existing session or kill_zone aliases where present.",
    "horizon_id": "Policy/replay horizon identifier; no safe live-log default exists.",
    "source_component": "Moonshot policy source component; no safe runtime producer-name default exists.",
    "selected_side": "Can map existing side/direction aliases where present.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def aliases_for_field(field: str) -> tuple[str, ...]:
    return EVENT_FIELD_ALIASES.get(field, (field,))


def source_alias_counts(path: Path) -> dict[str, Counter[str]]:
    required_aliases = {
        field: aliases_for_field(field) for field in AI_NARROWING_EVENT_REQUIRED_FIELDS
    }
    counters = {field: Counter() for field in AI_NARROWING_EVENT_REQUIRED_FIELDS}
    if not path.exists():
        return counters
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for field, aliases in required_aliases.items():
                for alias in aliases:
                    if normalized(row.get(alias)):
                        counters[field][alias] += 1
    return counters


def adapter_resolution(field: str, alias_counts: dict[str, int]) -> str:
    if alias_counts.get(field, 0) > 0:
        return "DIRECT_FIELD_PRESENT"
    if any(count > 0 for alias, count in alias_counts.items() if alias != field):
        return "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING"
    return "MISSING_REQUIRES_EXPLICIT_UPSTREAM_CAPTURE"


def adapter_action(field: str, resolution: str) -> str:
    if resolution == "DIRECT_FIELD_PRESENT":
        return "copy_direct_field"
    if resolution == "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING":
        return "map_existing_alias_to_ai_narrowing_contract_field"
    if field in {"horizon_id", "market_timeframe", "source_component", "source_symbol"}:
        return "add_explicit_source_capture_before_policy_registry_use"
    return "add_upstream_capture_or_adapter_mapping_before_policy_registry_use"


def build() -> dict[str, Any]:
    availability_rows = read_jsonl(FIELD_AVAILABILITY_LEDGER)
    availability_by_source = {row["event_source_path"]: row for row in availability_rows}
    output_rows: list[dict[str, Any]] = []
    for source_path in EVENT_SOURCE_PATHS:
        source_key = source_path.as_posix()
        absolute = REPO / source_path
        availability = availability_by_source.get(source_key, {})
        alias_counters = source_alias_counts(absolute)
        for field in AI_NARROWING_EVENT_REQUIRED_FIELDS:
            aliases = aliases_for_field(field)
            counts = dict(sorted(alias_counters[field].items()))
            resolution = adapter_resolution(field, counts)
            output_rows.append(
                {
                    "adapter_spec_row_id": f"MAIN-ORCH48-AI-NARROWING-ADAPTER-SPEC-{len(output_rows) + 1:04d}",
                    "schema_version": SCHEMA_VERSION,
                    "source_path": source_key,
                    "source_exists": absolute.exists(),
                    "producer_owner": PRODUCER_OWNERS.get(source_key, "unknown"),
                    "source_rows_scanned": int(availability.get("event_source_rows") or 0),
                    "source_field_availability_status": availability.get("field_availability_status"),
                    "required_event_field": field,
                    "alias_candidates": list(aliases),
                    "alias_presence_counts": counts,
                    "adapter_resolution": resolution,
                    "adapter_action": adapter_action(field, resolution),
                    "field_capture_note": FIELD_CAPTURE_NOTES.get(field, ""),
                    "event_evaluation_surface": "AINarrowingPolicyRegistry.evaluate_event",
                    "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
                    "ai_call_skip_allowed_now": False,
                    "production_change_opened_now": False,
                    "live_ai_runtime_change_now": False,
                    "live_selector_change_now": False,
                    "paid_api_or_vendor_call": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "replay_r_reference_counted_as_new_main_result": False,
                }
            )
    write_jsonl(OUTPUT_LEDGER, output_rows)

    resolution_counts = Counter(row["adapter_resolution"] for row in output_rows)
    action_counts = Counter(row["adapter_action"] for row in output_rows)
    field_resolution_counts = {
        field: dict(
            sorted(
                Counter(
                    row["adapter_resolution"] for row in output_rows if row["required_event_field"] == field
                ).items()
            )
        )
        for field in AI_NARROWING_EVENT_REQUIRED_FIELDS
    }
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_field_availability_ledger": {
            "path": display_path(FIELD_AVAILABILITY_LEDGER),
            "rows": len(availability_rows),
            "sha256": sha256_path(FIELD_AVAILABILITY_LEDGER),
        },
        "adapter_spec_rows": len(output_rows),
        "source_count": len(EVENT_SOURCE_PATHS),
        "required_field_count": len(AI_NARROWING_EVENT_REQUIRED_FIELDS),
        "required_event_fields": list(AI_NARROWING_EVENT_REQUIRED_FIELDS),
        "adapter_resolution_counts": dict(sorted(resolution_counts.items())),
        "adapter_action_counts": dict(sorted(action_counts.items())),
        "field_resolution_counts": field_resolution_counts,
        "explicit_upstream_capture_required_fields": sorted(
            {
                row["required_event_field"]
                for row in output_rows
                if row["adapter_action"] == "add_explicit_source_capture_before_policy_registry_use"
            }
        ),
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in output_rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in output_rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in output_rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in output_rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in output_rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in output_rows
        ),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in output_rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in output_rows
        ),
        "implementation_effect": {
            "default_off_ai_narrowing_adapter_spec_available": True,
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_trading_or_live_broker_effect": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "adapter_spec_rows": len(output_rows),
        "adapter_resolution_counts": summary["adapter_resolution_counts"],
        "explicit_upstream_capture_required_fields": summary["explicit_upstream_capture_required_fields"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

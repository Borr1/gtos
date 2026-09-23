from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
BRIDGE_AUDIT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_AUDIT_LEDGER_{DATE}.jsonl"
BRIDGE_AUDIT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_AUDIT_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def build() -> dict[str, Any]:
    bridge_rows = read_jsonl(BRIDGE_AUDIT_LEDGER)
    bridge_summary = read_json(BRIDGE_AUDIT_SUMMARY)
    current_values = sorted(bridge_summary.get("global_bridge_required_values") or [])
    catalog_values = sorted(bridge_summary.get("global_catalog_uncovered_values") or [])
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(current_values, start=1):
        rows.append(
            {
                "guardrail_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-COMPONENT-GUARDRAIL-{index:04d}",
                "schema_version": "main_orch48_numeric_router_source_component_bridge_guardrail_v1",
                "row_kind": "current_source_component_value",
                "component_value": value,
                "guardrail_status": "EXPLICIT_MAPPING_REQUIRED_NOT_ASSUMED",
                "adapter_behavior": "blocked_by_default_in_bridge_aware_adapter",
                "accepted_mapping_target": "",
                "source_count_with_value": sum(value in (row.get("bridge_required_values") or []) for row in bridge_rows),
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    offset = len(rows)
    for index, value in enumerate(catalog_values, start=1):
        rows.append(
            {
                "guardrail_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-COMPONENT-GUARDRAIL-{offset + index:04d}",
                "schema_version": "main_orch48_numeric_router_source_component_bridge_guardrail_v1",
                "row_kind": "catalog_source_component_value",
                "component_value": value,
                "guardrail_status": "CATALOG_COMPONENT_UNMAPPED_BY_CURRENT_SOURCE_VALUES",
                "adapter_behavior": "requires_explicit_current_to_catalog_bridge_before_event_emission",
                "accepted_mapping_target": "",
                "catalog_contract_rows_with_value": int((bridge_summary.get("catalog_source_component_counts") or {}).get(value, 0)),
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("guardrail_status") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL",
        "schema_version": "main_orch48_numeric_router_source_component_bridge_guardrail_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_bridge_audit_ledger": {
            "path": str(BRIDGE_AUDIT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(bridge_rows),
            "sha256": sha256_path(BRIDGE_AUDIT_LEDGER),
        },
        "input_bridge_audit_summary": {
            "path": str(BRIDGE_AUDIT_SUMMARY.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_path(BRIDGE_AUDIT_SUMMARY),
        },
        "rows": len(rows),
        "current_source_component_value_rows": len(current_values),
        "catalog_source_component_value_rows": len(catalog_values),
        "accepted_mapping_rows": sum(1 for row in rows if row.get("accepted_mapping_target")),
        "guardrail_status_counts": dict(sorted(status_counts.items())),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
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
        "route_id": summary["route_id"],
        "rows": summary["rows"],
        "accepted_mapping_rows": summary["accepted_mapping_rows"],
        "guardrail_status_counts": summary["guardrail_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

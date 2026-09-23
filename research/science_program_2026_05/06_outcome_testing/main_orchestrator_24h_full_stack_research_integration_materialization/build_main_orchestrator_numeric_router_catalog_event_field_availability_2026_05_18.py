from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
REPO = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
]
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY_MANIFEST_{DATE}.json"


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


def field_is_present(row: dict[str, Any], field: str) -> bool:
    return normalized(row.get(field)) != ""


def build() -> dict[str, Any]:
    contracts = read_jsonl(CONTRACT_LEDGER)
    required_set_counts = Counter(tuple(row.get("required_event_fields") or []) for row in contracts)
    required_field_universe = sorted({field for fields in required_set_counts for field in fields})
    contract_rows = len(contracts)

    audit_rows: list[dict[str, Any]] = []
    for index, relative_path in enumerate(SOURCE_PATHS, start=1):
        path = REPO / relative_path
        parse_errors = 0
        rows_scanned = 0
        field_presence_counts: Counter[str] = Counter()
        rows_with_any_required_field = 0
        rows_with_full_required_universe = 0
        structurally_covered_required_sets: set[tuple[str, ...]] = set()

        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        parse_errors += 1
                        continue
                    rows_scanned += 1
                    available_fields = {
                        field for field in required_field_universe if field_is_present(row, field)
                    }
                    field_presence_counts.update(available_fields)
                    if available_fields:
                        rows_with_any_required_field += 1
                    if set(required_field_universe).issubset(available_fields):
                        rows_with_full_required_universe += 1
                    for required_set in required_set_counts:
                        if set(required_set).issubset(available_fields):
                            structurally_covered_required_sets.add(required_set)

        structurally_coverable_contract_rows = sum(
            required_set_counts[required_set] for required_set in structurally_covered_required_sets
        )
        audit_rows.append(
            {
                "availability_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-FIELD-AVAILABILITY-{index:04d}",
                "source_path": str(relative_path).replace("\\", "/"),
                "source_exists": path.exists(),
                "source_sha256": sha256_path(path) if path.exists() else None,
                "rows_scanned": rows_scanned,
                "parse_errors": parse_errors,
                "required_field_universe": required_field_universe,
                "field_presence_counts": dict(sorted(field_presence_counts.items())),
                "rows_with_any_required_field": rows_with_any_required_field,
                "rows_with_full_required_universe": rows_with_full_required_universe,
                "structurally_coverable_contract_rows": structurally_coverable_contract_rows,
                "structurally_coverable_contract_field_set_count": len(structurally_covered_required_sets),
                "contract_rows": contract_rows,
                "structurally_uncovered_contract_rows": contract_rows - structurally_coverable_contract_rows,
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, audit_rows)

    aggregate_field_counts: Counter[str] = Counter()
    for row in audit_rows:
        aggregate_field_counts.update(row["field_presence_counts"])
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY",
        "schema_version": "main_orch48_numeric_router_catalog_event_field_availability_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_contract_ledger": {
            "path": str(CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": contract_rows,
            "sha256": sha256_path(CONTRACT_LEDGER),
        },
        "source_rows": len(audit_rows),
        "existing_source_rows": sum(bool(row["source_exists"]) for row in audit_rows),
        "total_rows_scanned": sum(int(row["rows_scanned"]) for row in audit_rows),
        "total_parse_errors": sum(int(row["parse_errors"]) for row in audit_rows),
        "contract_rows": contract_rows,
        "required_field_universe": required_field_universe,
        "aggregate_field_presence_counts": dict(sorted(aggregate_field_counts.items())),
        "max_structurally_coverable_contract_rows_by_single_source": max(
            (int(row["structurally_coverable_contract_rows"]) for row in audit_rows),
            default=0,
        ),
        "sources_with_full_required_universe_rows": sum(
            int(row["rows_with_full_required_universe"]) > 0 for row in audit_rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in audit_rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in audit_rows
        ),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in audit_rows),
        "unconditional_scalar_use_allowed_rows": sum(
            bool(row.get("unconditional_scalar_use_allowed")) for row in audit_rows
        ),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in audit_rows
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
        "source_rows": summary["source_rows"],
        "total_rows_scanned": summary["total_rows_scanned"],
        "max_structurally_coverable_contract_rows_by_single_source": summary[
            "max_structurally_coverable_contract_rows_by_single_source"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

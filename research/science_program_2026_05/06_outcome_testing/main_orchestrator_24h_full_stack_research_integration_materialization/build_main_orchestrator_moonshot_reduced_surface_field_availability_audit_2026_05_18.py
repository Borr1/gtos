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
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_OUTPUT_MANIFEST_{DATE}.json"

EVENT_SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def contract_requirements(contract_rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_required_fields = sorted({field for row in contract_rows for field in row.get("required_event_fields") or []})
    base_required_fields = [
        "horizon_id",
        "market_timeframe",
        "route_session",
        "selected_side",
        "source_component",
        "source_symbol",
        "symbol",
    ]
    source_identity_fields = ["source_path", "source_file_sha256"]
    numeric_threshold_fields = [
        "selected_intrabar_cost_adjusted_simulated_r",
        "selected_minus_rejected_intrabar_cost_adjusted_r",
        "temporal_positive_winner_fold_share",
        "temporal_winner_consistency_share",
    ]
    return {
        "all_required_fields": all_required_fields,
        "base_required_fields": base_required_fields,
        "source_identity_fields": source_identity_fields,
        "numeric_threshold_fields": numeric_threshold_fields,
    }


def audit_source(path: Path, requirements: dict[str, Any]) -> dict[str, Any]:
    absolute = REPO / path
    row_count = 0
    parse_error_rows = 0
    field_counts = Counter()
    all_required = set(requirements["all_required_fields"])
    base_required = set(requirements["base_required_fields"])
    leakage_required = all_required
    rows_with_base = 0
    rows_with_leakage_required = 0
    if absolute.exists():
        with absolute.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row_count += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    parse_error_rows += 1
                    continue
                keys = set(row.keys())
                field_counts.update(keys & all_required)
                if base_required <= keys:
                    rows_with_base += 1
                if leakage_required <= keys:
                    rows_with_leakage_required += 1
    missing_fields = [field for field in requirements["all_required_fields"] if field_counts.get(field, 0) == 0]
    return {
        "event_source_path": str(path).replace("\\", "/"),
        "event_source_exists": absolute.exists(),
        "event_source_sha256": sha256_path(absolute) if absolute.exists() else None,
        "event_source_bytes": absolute.stat().st_size if absolute.exists() else None,
        "event_source_rows": row_count,
        "parse_error_rows": parse_error_rows,
        "required_field_presence_counts": dict(sorted(field_counts.items())),
        "missing_required_fields": missing_fields,
        "rows_with_base_required_fields": rows_with_base,
        "rows_with_leakage_reduced_required_fields": rows_with_leakage_required,
        "field_availability_status": "CURRENT_SOURCE_CAN_FEED_LEAKAGE_REDUCED_REGISTRY"
        if rows_with_leakage_required > 0
        else "CURRENT_SOURCE_MISSING_REDUCED_SURFACE_FIELDS",
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
    }


def build() -> dict[str, Any]:
    contracts = read_jsonl(CONTRACT_LEDGER)
    requirements = contract_requirements(contracts)
    rows = [
        {
            "field_availability_row_id": f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-FIELD-AUDIT-{index:04d}",
            **audit_source(path, requirements),
        }
        for index, path in enumerate(EVENT_SOURCE_PATHS, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(row["field_availability_status"] for row in rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_AUDIT",
        "schema_version": "main_orch48_moonshot_reduced_surface_field_availability_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "contract_ledger": str(CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "contract_ledger_sha256": sha256_path(CONTRACT_LEDGER),
        "contract_rows": len(contracts),
        "required_fields": requirements,
        "event_source_count": len(rows),
        "event_source_rows_total": sum(int(row.get("event_source_rows") or 0) for row in rows),
        "rows_with_base_required_fields_total": sum(int(row.get("rows_with_base_required_fields") or 0) for row in rows),
        "rows_with_leakage_reduced_required_fields_total": sum(
            int(row.get("rows_with_leakage_reduced_required_fields") or 0) for row in rows
        ),
        "field_availability_status_counts": dict(sorted(status_counts.items())),
        "source_paths": [row["event_source_path"] for row in rows],
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
        "event_source_count": len(rows),
        "rows_with_leakage_reduced_required_fields_total": summary["rows_with_leakage_reduced_required_fields_total"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

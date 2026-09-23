from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    numeric_router_catalog_event_contract_for_entry,
    summarize_numeric_router_catalog_event_contracts,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CATALOG_LEDGER_PATHS = [
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_{DATE}.jsonl",
]
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_MANIFEST_{DATE}.json"


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


def build() -> dict[str, Any]:
    contracts: list[dict[str, Any]] = []
    input_catalog_ledgers: list[dict[str, Any]] = []
    for path in CATALOG_LEDGER_PATHS:
        source_sha = sha256_path(path)
        rows = read_jsonl(path)
        input_catalog_ledgers.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "rows": len(rows),
                "sha256": source_sha,
            }
        )
        for index, row in enumerate(rows, start=1):
            contracts.append(
                numeric_router_catalog_event_contract_for_entry(
                    row,
                    contract_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-EVENT-CONTRACT-{len(contracts) + 1:08d}",
                    source_artifact=str(path.relative_to(REPO)).replace("\\", "/"),
                    source_line_no=index,
                    source_sha256=source_sha,
                )
            )
    write_jsonl(OUTPUT_LEDGER, contracts)

    contract_summary = summarize_numeric_router_catalog_event_contracts(contracts)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACTS",
        "schema_version": "main_orch48_numeric_router_catalog_event_contracts_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_catalog_ledgers": input_catalog_ledgers,
        "contract_rows": contract_summary["rows"],
        "input_action_rows": contract_summary["input_action_rows"],
        "catalog_type_counts": contract_summary["catalog_type_counts"],
        "catalog_priority_bucket_counts": contract_summary["catalog_priority_bucket_counts"],
        "required_event_field_counts": contract_summary["required_event_field_counts"],
        "min_required_event_field_count": contract_summary["min_required_event_field_count"],
        "max_required_event_field_count": contract_summary["max_required_event_field_count"],
        "ready_contract_rows": contract_summary["ready_contract_rows"],
        "live_effect_rows": contract_summary["live_effect_rows"],
        "runtime_score_allowed_rows": contract_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": contract_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": contract_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": contract_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": contract_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
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
        "contract_rows": summary["contract_rows"],
        "input_action_rows": summary["input_action_rows"],
        "catalog_type_counts": summary["catalog_type_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

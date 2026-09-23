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
    numeric_router_catalog_event_emitter_dry_run_for_source_rows,
    summarize_numeric_router_catalog_event_emitter_dry_runs,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
EMITTER_CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_MANIFEST_{DATE}.json"


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_jsonl_lenient(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    parse_errors = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                parse_errors += 1
    return rows, parse_errors


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
    contracts = read_jsonl(CONTRACT_LEDGER)
    emitter_contracts = read_jsonl(EMITTER_CONTRACT_LEDGER)
    dry_run_rows: list[dict[str, Any]] = []
    source_inputs: list[dict[str, Any]] = []
    for index, emitter in enumerate(emitter_contracts, start=1):
        source_path = str(emitter.get("source_path") or "")
        absolute_source = REPO / source_path
        source_rows, parse_errors = read_jsonl_lenient(absolute_source)
        dry_run = numeric_router_catalog_event_emitter_dry_run_for_source_rows(
            source_path=source_path,
            source_rows=source_rows,
            contract_rows=contracts,
            dry_run_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-EMITTER-DRY-RUN-{index:04d}",
        )
        dry_run["source_parse_errors"] = parse_errors
        dry_run_rows.append(dry_run)
        source_inputs.append(
            {
                "path": source_path,
                "rows": len(source_rows),
                "parse_errors": parse_errors,
                "sha256": sha256_path(absolute_source),
            }
        )
    write_jsonl(OUTPUT_LEDGER, dry_run_rows)

    dry_run_summary = summarize_numeric_router_catalog_event_emitter_dry_runs(dry_run_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN",
        "schema_version": "main_orch48_numeric_router_catalog_event_emitter_current_row_dry_run_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_contract_ledger": {
            "path": str(CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(contracts),
            "sha256": sha256_path(CONTRACT_LEDGER),
        },
        "input_emitter_contract_ledger": {
            "path": str(EMITTER_CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(emitter_contracts),
            "sha256": sha256_path(EMITTER_CONTRACT_LEDGER),
        },
        "input_source_files": source_inputs,
        "total_parse_errors": sum(item["parse_errors"] for item in source_inputs),
        **dry_run_summary,
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
        "source_rows_scanned": summary["source_rows_scanned"],
        "dry_run_status_counts": summary["dry_run_status_counts"],
        "emitted_complete_catalog_event_count": summary["emitted_complete_catalog_event_count"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

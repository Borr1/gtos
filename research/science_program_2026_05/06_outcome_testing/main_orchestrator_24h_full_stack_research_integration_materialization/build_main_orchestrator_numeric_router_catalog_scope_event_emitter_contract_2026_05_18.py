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
    numeric_router_catalog_scope_event_emitter_contract_for_source,
    summarize_numeric_router_catalog_scope_event_emitter_contracts,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
SOURCE_CAPTURE_PLAN_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_MANIFEST_{DATE}.json"


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
    source_capture_rows = read_jsonl(SOURCE_CAPTURE_PLAN_LEDGER)
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in source_capture_rows:
        by_source.setdefault(str(row.get("source_path") or ""), []).append(row)

    emitter_rows = [
        numeric_router_catalog_scope_event_emitter_contract_for_source(
            source_path=source_path,
            source_plan_rows=source_rows,
            contract_rows=contracts,
            emitter_contract_id=f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-SCOPE-EMITTER-{index:04d}",
        )
        for index, (source_path, source_rows) in enumerate(sorted(by_source.items()), start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, emitter_rows)

    emitter_summary = summarize_numeric_router_catalog_scope_event_emitter_contracts(emitter_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT",
        "schema_version": "main_orch48_numeric_router_catalog_scope_event_emitter_contract_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_contract_ledger": {
            "path": str(CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(contracts),
            "sha256": sha256_path(CONTRACT_LEDGER),
        },
        "input_source_capture_plan_ledger": {
            "path": str(SOURCE_CAPTURE_PLAN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(source_capture_rows),
            "sha256": sha256_path(SOURCE_CAPTURE_PLAN_LEDGER),
        },
        **emitter_summary,
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
        "source_count": summary["source_count"],
        "event_emitter_contract_status_counts": summary["event_emitter_contract_status_counts"],
        "historical_current_log_complete_after_catalog_attachment_rows": summary[
            "historical_current_log_complete_after_catalog_attachment_rows"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

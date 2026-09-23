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
    build_numeric_router_catalog_entries,
    summarize_numeric_router_catalog_entries,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
FAMILY_SPEC_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_LEDGER_{DATE}.jsonl"
CATALOG_LEDGER_BY_TYPE = {
    "default_off_scorer_registry_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_{DATE}.jsonl",
    "default_off_avoid_filter_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_{DATE}.jsonl",
    "default_off_context_guard_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_{DATE}.jsonl",
    "source_repair_queue_entry": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE_LEDGER_{DATE}.jsonl",
}
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG_MANIFEST_{DATE}.json"


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
    family_spec_sha = sha256_path(FAMILY_SPEC_LEDGER)
    family_specs = read_jsonl(FAMILY_SPEC_LEDGER)
    entries = build_numeric_router_catalog_entries(family_specs)
    entries_by_type: dict[str, list[dict[str, Any]]] = {catalog_type: [] for catalog_type in CATALOG_LEDGER_BY_TYPE}
    for entry in entries:
        entries_by_type.setdefault(entry["catalog_type"], []).append(entry)

    output_ledgers: list[dict[str, Any]] = []
    for catalog_type, path in CATALOG_LEDGER_BY_TYPE.items():
        rows = entries_by_type.get(catalog_type, [])
        write_jsonl(path, rows)
        output_ledgers.append(
            {
                "catalog_type": catalog_type,
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "rows": len(rows),
                "sha256": sha256_path(path),
            }
        )

    catalog_summary = summarize_numeric_router_catalog_entries(entries)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOGS",
        "schema_version": "main_orch48_numeric_router_implementation_catalogs_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_family_spec_ledger": {
            "path": str(FAMILY_SPEC_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(family_specs),
            "sha256": family_spec_sha,
        },
        "catalog_rows": catalog_summary["rows"],
        "input_action_rows": catalog_summary["input_action_rows"],
        "catalog_type_counts": catalog_summary["catalog_type_counts"],
        "catalog_priority_bucket_counts": catalog_summary["catalog_priority_bucket_counts"],
        "catalog_priority_bucket_input_action_counts": catalog_summary[
            "catalog_priority_bucket_input_action_counts"
        ],
        "implementation_target_counts": catalog_summary["implementation_target_counts"],
        "numeric_router_action_counts": catalog_summary["numeric_router_action_counts"],
        "symbol_counts": catalog_summary["symbol_counts"],
        "output_ledgers": output_ledgers,
        "live_effect_rows": catalog_summary["live_effect_rows"],
        "runtime_score_allowed_rows": catalog_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": catalog_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": catalog_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": catalog_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": catalog_summary[
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

    outputs = list(CATALOG_LEDGER_BY_TYPE.values()) + [OUTPUT_SUMMARY]
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
        "catalog_rows": summary["catalog_rows"],
        "input_action_rows": summary["input_action_rows"],
        "catalog_type_counts": summary["catalog_type_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

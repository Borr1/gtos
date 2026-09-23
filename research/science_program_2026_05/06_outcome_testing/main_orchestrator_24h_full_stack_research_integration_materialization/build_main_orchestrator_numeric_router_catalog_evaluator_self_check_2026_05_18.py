from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    NumericRouterImplementationCatalog,
    load_numeric_router_catalog_entries,
    numeric_router_catalog_event_from_entry,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CATALOG_LEDGER_PATHS = [
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_{DATE}.jsonl",
]
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_MANIFEST_{DATE}.json"


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


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build() -> dict[str, Any]:
    entries = load_numeric_router_catalog_entries(CATALOG_LEDGER_PATHS)
    catalog = NumericRouterImplementationCatalog(entries)
    self_check_rows: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        event = numeric_router_catalog_event_from_entry(entry)
        matches = catalog.evaluate_event(event)
        match_ids = [row.get("input_numeric_router_catalog_entry_id") for row in matches]
        own_entry_id = entry.get("numeric_router_catalog_entry_id")
        self_check_rows.append(
            {
                "self_check_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-EVAL-SELF-CHECK-{index:08d}",
                "input_numeric_router_catalog_entry_id": own_entry_id,
                "catalog_type": entry.get("catalog_type"),
                "catalog_priority_bucket": entry.get("catalog_priority_bucket"),
                "numeric_router_action": entry.get("numeric_router_action"),
                "symbol": entry.get("symbol"),
                "source_component": entry.get("source_component"),
                "input_action_rows": entry.get("input_action_rows"),
                "match_count": len(matches),
                "matched_own_entry": own_entry_id in match_ids,
                "matched_catalog_entry_id_sample": match_ids[:5],
                "self_check_status": "PASS" if own_entry_id in match_ids else "FAIL",
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, self_check_rows)

    catalog_summary = catalog.summarize_catalog()
    status_counts = dict(sorted(Counter(row["self_check_status"] for row in self_check_rows).items()))
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK",
        "schema_version": "main_orch48_numeric_router_catalog_evaluator_self_check_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_catalog_ledgers": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "rows": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in CATALOG_LEDGER_PATHS
        ],
        "self_check_rows": len(self_check_rows),
        "self_check_status_counts": status_counts,
        "catalog_summary": catalog_summary,
        "match_count_sum": sum(int(row.get("match_count") or 0) for row in self_check_rows),
        "live_effect_rows": 0,
        "runtime_score_allowed_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "unconditional_scalar_use_allowed_rows": 0,
        "replay_r_reference_counted_as_new_main_result_rows": 0,
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": status_counts.get("FAIL", 0) == 0,
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
        "ok": summary["can_continue_to_next_system_conversion_plate"],
        "route_id": summary["route_id"],
        "self_check_rows": summary["self_check_rows"],
        "self_check_status_counts": summary["self_check_status_counts"],
        "match_count_sum": summary["match_count_sum"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

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
    compact_scope_system_decision,
    compact_system_recommendation,
    summarize_scope_system_decisions,
    summarize_system_recommendations,
)


DATE = "2026-05-18"
SOURCE_DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SOURCE_ROUTE_DIR = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_ROUTER_SYSTEM_RECOMMENDATIONS"

SOURCE_FILES = {
    "result": f"{SOURCE_PREFIX}_RESULT_{SOURCE_DATE}.json",
    "executable_spec": f"{SOURCE_PREFIX}_EXECUTABLE_SPEC_{SOURCE_DATE}.json",
    "system_recommendation": f"{SOURCE_PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_{SOURCE_DATE}.jsonl",
    "scope_system_decision": f"{SOURCE_PREFIX}_SCOPE_SYSTEM_DECISION_LEDGER_{SOURCE_DATE}.jsonl",
    "scorer_registry_surface": f"{SOURCE_PREFIX}_SCORER_REGISTRY_SURFACE_LEDGER_{SOURCE_DATE}.jsonl",
    "avoid_comparator_score": f"{SOURCE_PREFIX}_AVOID_COMPARATOR_SCORE_LEDGER_{SOURCE_DATE}.jsonl",
    "context_guard_input": f"{SOURCE_PREFIX}_CONTEXT_GUARD_INPUT_LEDGER_{SOURCE_DATE}.jsonl",
    "source_repair_proof": f"{SOURCE_PREFIX}_SOURCE_REPAIR_PROOF_LEDGER_{SOURCE_DATE}.jsonl",
    "bucket": f"{SOURCE_PREFIX}_BUCKET_LEDGER_{SOURCE_DATE}.jsonl",
    "question": f"{SOURCE_PREFIX}_QUESTION_LEDGER_{SOURCE_DATE}.jsonl",
    "source_manifest": f"{SOURCE_PREFIX}_SOURCE_MANIFEST_LEDGER_{SOURCE_DATE}.jsonl",
    "symbol_system_decision_rollup": f"{SOURCE_PREFIX}_SYMBOL_SYSTEM_DECISION_ROLLUP_LEDGER_{SOURCE_DATE}.jsonl",
}

OUTPUT_SCOPE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCOPE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SYSTEM_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_LEDGER_{DATE}.jsonl"
OUTPUT_SOURCE_INVENTORY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_INVENTORY_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fs_path(path: Path) -> Path:
    if sys.platform.startswith("win") and path.is_absolute() and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path))
    return path


def path_exists(path: Path) -> bool:
    return path.exists() or fs_path(path).exists()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    source_path = path if path.exists() else fs_path(path)
    with source_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    source_path = path if path.exists() else fs_path(path)
    with source_path.open("rb") as handle:
        return sum(1 for _ in handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    source_path = path if path.exists() else fs_path(path)
    return json.loads(source_path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_path = path if path.exists() else fs_path(path)
    with source_path.open("r", encoding="utf-8") as handle:
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


def source_inventory_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for logical_name, filename in SOURCE_FILES.items():
        path = SOURCE_ROUTE_DIR / filename
        exists = path_exists(path)
        source_path = path if path.exists() else fs_path(path)
        rows.append(
            {
                "logical_name": logical_name,
                "source_path": str(path),
                "source_exists": exists,
                "source_bytes": source_path.stat().st_size if exists else None,
                "source_lines": count_lines(path) if exists else None,
                "source_sha256": sha256_path(path) if exists else None,
            }
        )
    return rows


def build() -> dict[str, Any]:
    result = read_json(SOURCE_ROUTE_DIR / SOURCE_FILES["result"])
    scope_source = SOURCE_ROUTE_DIR / SOURCE_FILES["scope_system_decision"]
    system_source = SOURCE_ROUTE_DIR / SOURCE_FILES["system_recommendation"]
    scope_sha = sha256_path(scope_source)
    system_sha = sha256_path(system_source)
    source_artifact_scope = str(scope_source)
    source_artifact_system = str(system_source)

    scope_rows = [
        compact_scope_system_decision(
            row,
            source_artifact=source_artifact_scope,
            source_line_no=index,
            source_sha256=scope_sha,
        )
        for index, row in enumerate(read_jsonl(scope_source), start=1)
    ]
    system_rows = [
        compact_system_recommendation(
            row,
            source_artifact=source_artifact_system,
            source_line_no=index,
            source_sha256=system_sha,
        )
        for index, row in enumerate(read_jsonl(system_source), start=1)
    ]
    inventory_rows = source_inventory_rows()

    write_jsonl(OUTPUT_SCOPE_LEDGER, scope_rows)
    write_jsonl(OUTPUT_SYSTEM_LEDGER, system_rows)
    write_jsonl(OUTPUT_SOURCE_INVENTORY, inventory_rows)

    scope_summary = summarize_scope_system_decisions(scope_rows)
    system_summary = summarize_system_recommendations(system_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECOMMENDATION_INTAKE",
        "schema_version": "main_orch48_numeric_router_system_recommendation_intake_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "source_route_dir": str(SOURCE_ROUTE_DIR),
        "source_result_sha256": sha256_path(SOURCE_ROUTE_DIR / SOURCE_FILES["result"]),
        "source_result_counts": result.get("counts") or {},
        "source_result_bucket_distributions": result.get("bucket_distributions") or {},
        "source_manifest_hash": result.get("source_manifest_hash"),
        "source_inventory_rows": len(inventory_rows),
        "source_inventory_missing_rows": sum(not row["source_exists"] for row in inventory_rows),
        "scope_system_decision_rows": scope_summary["rows"],
        "system_recommendation_rows": system_summary["rows"],
        "router_scope_decision_counts": scope_summary["router_scope_decision_counts"],
        "implementation_candidate_type_counts": scope_summary["implementation_candidate_type_counts"],
        "scope_symbol_counts": scope_summary["symbol_counts"],
        "scope_source_component_counts": scope_summary["source_component_counts"],
        "scope_row_count_sum": scope_summary["row_count_sum"],
        "scope_score_count_sum": scope_summary["score_count_sum"],
        "scope_scorer_event_count_sum": scope_summary["scorer_event_count_sum"],
        "scope_avoid_inverse_event_count_sum": scope_summary["avoid_inverse_event_count_sum"],
        "scope_context_stress_event_count_sum": scope_summary["context_stress_event_count_sum"],
        "scope_source_repair_event_count_sum": scope_summary["source_repair_event_count_sum"],
        "system_scorer_registry_surface_rows": system_summary["scorer_registry_surface_rows"],
        "system_avoid_comparator_score_rows": system_summary["avoid_comparator_score_rows"],
        "system_context_guard_input_rows": system_summary["context_guard_input_rows"],
        "system_source_repair_proof_rows": system_summary["source_repair_proof_rows"],
        "runtime_score_allowed_rows": scope_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": system_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": scope_summary["candidate_use_allowed_now_rows"]
        + system_summary["candidate_use_allowed_now_rows"],
        "summary_only_terminal_rows": scope_summary["summary_only_terminal_rows"],
        "live_effect_rows": scope_summary["live_effect_rows"] + system_summary["live_effect_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": system_summary[
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

    outputs = [OUTPUT_SCOPE_LEDGER, OUTPUT_SYSTEM_LEDGER, OUTPUT_SOURCE_INVENTORY, OUTPUT_SUMMARY]
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
        "scope_system_decision_rows": summary["scope_system_decision_rows"],
        "system_recommendation_rows": summary["system_recommendation_rows"],
        "source_inventory_rows": summary["source_inventory_rows"],
        "router_scope_decision_counts": summary["router_scope_decision_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

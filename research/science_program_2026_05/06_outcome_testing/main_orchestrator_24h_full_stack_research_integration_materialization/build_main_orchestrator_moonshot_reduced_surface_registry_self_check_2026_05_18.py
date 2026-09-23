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

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    ReducedSurfaceCandidateRegistry,
    event_from_candidate_scope,
    load_candidate_rows,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
CANDIDATE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_OUTPUT_MANIFEST_{DATE}.json"


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


def self_check_rows(candidates: list[dict[str, Any]], registry: ReducedSurfaceCandidateRegistry) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        event = event_from_candidate_scope(candidate)
        matches = registry.evaluate_event(event)
        matched_ids = [str(row.get("candidate_row_id") or "") for row in matches]
        candidate_id = str(candidate.get("candidate_row_id") or "")
        output.append(
            {
                "self_check_row_id": f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-REGISTRY-SELF-CHECK-{len(output) + 1:07d}",
                "candidate_row_id": candidate_id,
                "surface_scope_sha256": candidate.get("surface_scope_sha256"),
                "symbol": candidate.get("symbol"),
                "market_timeframe": candidate.get("market_timeframe"),
                "route_session": candidate.get("route_session"),
                "horizon_id": candidate.get("horizon_id"),
                "source_component": candidate.get("source_component"),
                "selected_side": candidate.get("selected_side"),
                "main_compiler_action": candidate.get("main_compiler_action"),
                "registry_event": event,
                "matched_candidate_rows": len(matches),
                "matched_candidate_row_ids": matched_ids,
                "self_match_found": candidate_id in matched_ids,
                "registry_self_check_status": "REDUCED_SURFACE_REGISTRY_SELF_CHECK_PASS"
                if candidate_id in matched_ids
                else "REDUCED_SURFACE_REGISTRY_SELF_CHECK_REPAIR",
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    return output


def build() -> dict[str, Any]:
    candidate_summary = read_json(CANDIDATE_SUMMARY)
    candidates = load_candidate_rows(CANDIDATE_LEDGER)
    registry = ReducedSurfaceCandidateRegistry(candidates)
    rows = self_check_rows(candidates, registry)
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(row["registry_self_check_status"] for row in rows)
    action_counts = Counter(row["main_compiler_action"] for row in rows)
    total_matches = sum(int(row.get("matched_candidate_rows") or 0) for row in rows)
    duplicate_scope_checks = sum(int(row.get("matched_candidate_rows") or 0) > 1 for row in rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK",
        "schema_version": "main_orch48_moonshot_reduced_surface_registry_self_check_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "candidate_summary": str(CANDIDATE_SUMMARY.relative_to(REPO)).replace("\\", "/"),
        "candidate_summary_sha256": sha256_path(CANDIDATE_SUMMARY),
        "candidate_rows": len(candidates),
        "self_check_rows": len(rows),
        "self_check_pass_rows": int(status_counts.get("REDUCED_SURFACE_REGISTRY_SELF_CHECK_PASS", 0)),
        "self_check_repair_rows": int(status_counts.get("REDUCED_SURFACE_REGISTRY_SELF_CHECK_REPAIR", 0)),
        "total_registry_match_rows": total_matches,
        "duplicate_scope_self_check_rows": duplicate_scope_checks,
        "action_decision_counts": dict(sorted(action_counts.items())),
        "registry_summary": registry.summarize_registry(),
        "upstream_candidate_summary": {
            "rows": (candidate_summary.get("candidate_summary") or {}).get("rows"),
            "matched_selection_rows": (candidate_summary.get("candidate_summary") or {}).get("matched_selection_rows"),
            "average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": (
                candidate_summary.get("candidate_summary") or {}
            ).get("average_selected_intrabar_cost_adjusted_simulated_r_mean_reference"),
        },
        "implementation_effect": {
            "code_surface": "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py",
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "result_reference_policy": {
            "counted_as_new_main_result_r": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
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
        "self_check_rows": len(rows),
        "self_check_pass_rows": summary["self_check_pass_rows"],
        "total_registry_match_rows": total_matches,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

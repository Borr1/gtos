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
    build_numeric_router_family_action_specs,
    summarize_numeric_router_family_action_specs,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_MANIFEST_{DATE}.json"


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
    action_sha = sha256_path(ACTION_LEDGER)
    action_rows = read_jsonl(ACTION_LEDGER)
    specs = build_numeric_router_family_action_specs(action_rows)
    write_jsonl(OUTPUT_LEDGER, specs)

    spec_summary = summarize_numeric_router_family_action_specs(specs)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPECS",
        "schema_version": "main_orch48_numeric_router_family_action_specs_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_action_ledger": {
            "path": str(ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(action_rows),
            "sha256": action_sha,
        },
        "family_spec_rows": spec_summary["rows"],
        "input_action_rows": spec_summary["input_action_rows"],
        "output_family_spec_counts": spec_summary["output_family_counts"],
        "output_family_input_action_counts": spec_summary["output_family_input_action_counts"],
        "family_spec_type_counts": spec_summary["family_spec_type_counts"],
        "numeric_router_action_counts": spec_summary["numeric_router_action_counts"],
        "implementation_target_counts": spec_summary["implementation_target_counts"],
        "symbol_counts": spec_summary["symbol_counts"],
        "live_effect_rows": spec_summary["live_effect_rows"],
        "runtime_score_allowed_rows": spec_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": spec_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": spec_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": spec_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": spec_summary[
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
        "family_spec_rows": summary["family_spec_rows"],
        "input_action_rows": summary["input_action_rows"],
        "implementation_target_counts": summary["implementation_target_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

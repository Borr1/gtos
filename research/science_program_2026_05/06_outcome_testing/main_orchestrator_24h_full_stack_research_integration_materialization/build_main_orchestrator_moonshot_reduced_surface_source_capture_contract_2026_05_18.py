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

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    load_candidate_rows,
    source_capture_contract_for_candidate,
    summarize_source_capture_contracts,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"


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
    candidates = load_candidate_rows(CANDIDATE_LEDGER)
    candidate_sha = sha256_path(CANDIDATE_LEDGER)
    candidate_artifact = str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/")
    rows = [
        source_capture_contract_for_candidate(
            candidate,
            contract_row_id=f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-SOURCE-CONTRACT-{index:07d}",
            source_artifact=candidate_artifact,
            source_line_no=index,
            source_sha256=candidate_sha,
        )
        for index, candidate in enumerate(candidates, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    contract_summary = summarize_source_capture_contracts(rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT",
        "schema_version": "main_orch48_moonshot_reduced_surface_source_capture_contract_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": candidate_artifact,
        "candidate_ledger_sha256": candidate_sha,
        "contract_summary": contract_summary,
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
        "continuation": {
            "next_plate": "wire source-capture contract into shadow/replay event production or use it as replay validator input",
            "can_continue_to_next_system_conversion_plate": True,
        },
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
        "contract_rows": len(rows),
        "required_numeric_fields": contract_summary["required_numeric_threshold_field_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

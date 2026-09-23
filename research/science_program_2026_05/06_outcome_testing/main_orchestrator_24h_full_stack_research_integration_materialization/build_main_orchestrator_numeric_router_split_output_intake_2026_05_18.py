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
    compact_numeric_router_output_row,
    summarize_numeric_router_output_rows,
)


DATE = "2026-05-18"
SOURCE_DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SOURCE_ROUTE_DIR = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_ROUTER_SYSTEM_RECOMMENDATIONS"

FAMILY_SOURCES = {
    "scorer_registry_surface": f"{SOURCE_PREFIX}_SCORER_REGISTRY_SURFACE_LEDGER_{SOURCE_DATE}.jsonl",
    "avoid_comparator_score": f"{SOURCE_PREFIX}_AVOID_COMPARATOR_SCORE_LEDGER_{SOURCE_DATE}.jsonl",
    "context_guard_input": f"{SOURCE_PREFIX}_CONTEXT_GUARD_INPUT_LEDGER_{SOURCE_DATE}.jsonl",
    "source_repair_proof": f"{SOURCE_PREFIX}_SOURCE_REPAIR_PROOF_LEDGER_{SOURCE_DATE}.jsonl",
}
FAMILY_OUTPUTS = {
    "scorer_registry_surface": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_SURFACE_LEDGER_{DATE}.jsonl",
    "avoid_comparator_score": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_SCORE_LEDGER_{DATE}.jsonl",
    "context_guard_input": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_LEDGER_{DATE}.jsonl",
    "source_repair_proof": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl",
}
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fs_path(path: Path) -> Path:
    if sys.platform.startswith("win") and path.is_absolute() and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path))
    return path


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    source_path = path if path.exists() else fs_path(path)
    rows: list[dict[str, Any]] = []
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


def build_family(family: str, source_path: Path, output_path: Path) -> dict[str, Any]:
    source_sha = sha256_path(source_path)
    source_rows = read_jsonl(source_path)
    output_rows = [
        compact_numeric_router_output_row(
            row,
            output_family=family,
            output_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-{family.upper().replace('_', '-')}-{index:08d}",
            source_artifact=str(source_path),
            source_line_no=index,
            source_sha256=source_sha,
        )
        for index, row in enumerate(source_rows, start=1)
    ]
    write_jsonl(output_path, output_rows)
    summary = summarize_numeric_router_output_rows(output_rows)
    return {
        "family": family,
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "source_rows": len(source_rows),
        "output_path": str(output_path.relative_to(REPO)).replace("\\", "/"),
        "output_rows": summary["rows"],
        "output_sha256": sha256_path(output_path),
        "live_effect_rows": summary["live_effect_rows"],
        "runtime_score_allowed_rows": summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
    }


def build() -> dict[str, Any]:
    family_summaries = [
        build_family(family, SOURCE_ROUTE_DIR / filename, FAMILY_OUTPUTS[family])
        for family, filename in FAMILY_SOURCES.items()
    ]
    output_rows_by_family = {row["family"]: row["output_rows"] for row in family_summaries}
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_INTAKE",
        "schema_version": "main_orch48_numeric_router_split_output_intake_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "source_route_dir": str(SOURCE_ROUTE_DIR),
        "family_summaries": family_summaries,
        "output_rows_by_family": output_rows_by_family,
        "total_output_rows": sum(row["output_rows"] for row in family_summaries),
        "live_effect_rows": sum(row["live_effect_rows"] for row in family_summaries),
        "runtime_score_allowed_rows": sum(row["runtime_score_allowed_rows"] for row in family_summaries),
        "runtime_candidate_use_permitted_rows": sum(
            row["runtime_candidate_use_permitted_rows"] for row in family_summaries
        ),
        "candidate_use_allowed_now_rows": sum(row["candidate_use_allowed_now_rows"] for row in family_summaries),
        "unconditional_scalar_use_allowed_rows": sum(
            row["unconditional_scalar_use_allowed_rows"] for row in family_summaries
        ),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            row["replay_r_reference_counted_as_new_main_result_rows"] for row in family_summaries
        ),
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [*FAMILY_OUTPUTS.values(), OUTPUT_SUMMARY]
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
        "total_output_rows": summary["total_output_rows"],
        "output_rows_by_family": output_rows_by_family,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

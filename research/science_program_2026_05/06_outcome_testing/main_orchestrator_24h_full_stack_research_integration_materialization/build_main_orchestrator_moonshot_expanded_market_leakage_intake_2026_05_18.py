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

from src.research_infra.moonshot_expanded_market_leakage_reduction import (
    compact_leakage_reduction_row,
    summarize_leakage_reduction_intake,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_REL = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MOONSHOT_ROUTE = MOONSHOT_ROOT / MOONSHOT_ROUTE_REL

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_OUTPUT_MANIFEST_{DATE}.json"

CONSUMED_FILES = [
    MOONSHOT_ROUTE_REL / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_TEMPORAL_ROBUSTNESS_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_ROW_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_AGGREGATE_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_MATCH_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_SYSTEM_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_SUMMARY_2026-05-17.md",
]

LEAKAGE_RESULT = (
    MOONSHOT_ROUTE
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_RESULT_2026-05-17.json"
)
LEAKAGE_LEDGER = (
    MOONSHOT_ROUTE
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION_ROW_LEDGER_2026-05-17.jsonl"
)
SPRINT_LEDGER = MOONSHOT_ROUTE / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_git(*args: str) -> dict[str, Any]:
    safe_directory = str(MOONSHOT_ROOT).replace("\\", "/")
    command = ["git", "-c", f"safe.directory={safe_directory}", *args]
    result = subprocess.run(
        command,
        cwd=MOONSHOT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def moonshot_snapshot() -> dict[str, Any]:
    return {
        "root": str(MOONSHOT_ROOT),
        "head": run_git("rev-parse", "HEAD"),
        "branch": run_git("branch", "--show-current"),
        "status_short": run_git("status", "--short"),
    }


def source_entry(path: Path) -> dict[str, Any]:
    absolute = MOONSHOT_ROOT / path
    if not absolute.exists():
        raise FileNotFoundError(f"Missing moonshot consumed file: {absolute}")
    return {
        "path": str(path).replace("\\", "/"),
        "absolute_path": str(absolute),
        "bytes": absolute.stat().st_size,
        "lines": count_lines(absolute) if absolute.suffix == ".jsonl" or absolute.suffix == ".md" else None,
        "sha256": sha256_path(absolute),
    }


def read_checkpoint_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with SPRINT_LEDGER.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            checkpoint = row.get("checkpoint")
            if isinstance(checkpoint, int) and checkpoint >= 215:
                rows.append(row)
    return rows


def read_leakage_rows(source_sha256: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_artifact = str(LEAKAGE_LEDGER.relative_to(MOONSHOT_ROOT)).replace("\\", "/")
    with LEAKAGE_LEDGER.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(
                compact_leakage_reduction_row(
                    row,
                    intake_row_id=f"MAIN-ORCH48-MOONSHOT-LEAKAGE-INTAKE-{len(rows) + 1:07d}",
                    source_artifact=source_artifact,
                    source_line_no=line_no,
                    source_sha256=source_sha256,
                )
            )
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build() -> dict[str, Any]:
    if not MOONSHOT_ROOT.exists():
        raise FileNotFoundError(f"Moonshot root not found: {MOONSHOT_ROOT}")

    source_manifest = [source_entry(path) for path in CONSUMED_FILES]
    source_sha_by_name = {Path(entry["path"]).name: entry["sha256"] for entry in source_manifest}
    result = load_json(LEAKAGE_RESULT)
    expected_output_sha = result.get("output_sha256") or {}
    actual_leakage_ledger_sha = source_sha_by_name[LEAKAGE_LEDGER.name]
    expected_leakage_ledger_sha = expected_output_sha.get(LEAKAGE_LEDGER.name)
    if expected_leakage_ledger_sha and actual_leakage_ledger_sha != expected_leakage_ledger_sha:
        raise ValueError(
            f"Moonshot leakage row ledger hash mismatch: {actual_leakage_ledger_sha} != {expected_leakage_ledger_sha}"
        )

    intake_rows = read_leakage_rows(actual_leakage_ledger_sha)
    write_jsonl(OUTPUT_LEDGER, intake_rows)

    checkpoint_rows = read_checkpoint_rows()
    checkpoint_counts = {
        str(row.get("checkpoint")): {
            key: value
            for key, value in row.items()
            if key
            in {
                "checkpoint",
                "event",
                "generated_utc",
                "surface_execution_rows",
                "terminal_execution_rows",
                "performance_rows",
                "side_pair_rows",
                "temporal_robustness_rows",
                "intrabar_geometry_rows",
                "implementation_selection_rows",
                "code_candidate_rows",
                "code_candidate_execution_rows",
                "leakage_reduction_rows",
                "continuation",
            }
        }
        for row in checkpoint_rows
    }
    intake_summary = summarize_leakage_reduction_intake(intake_rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE",
        "schema_version": "main_orch48_moonshot_expanded_market_leakage_intake_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "moonshot_snapshot": moonshot_snapshot(),
        "moonshot_consumed_checkpoint_range": "CP215_THROUGH_CP223_LEAKAGE_REDUCTION",
        "moonshot_checkpoint_counts": checkpoint_counts,
        "moonshot_leakage_result_counts": result.get("counts") or {},
        "moonshot_leakage_result_ok": result.get("ok"),
        "source_manifest_sha256": stable_json_sha(source_manifest),
        "source_manifest": source_manifest,
        "intake_summary": intake_summary,
        "action_decision_counts": intake_summary["main_compiler_action_counts"],
        "result_reference_policy": {
            "primary_truth": "moonshot simulated/proxy R is retained as replay reference fields",
            "counted_as_new_main_result_r": False,
            "reason": "This plate consumes moonshot implementation evidence into main-side default-off scope semantics; it does not double-count R beyond source ledgers.",
        },
        "implementation_effect": {
            "code_surface": "src/research_infra/moonshot_expanded_market_leakage_reduction.py",
            "tests": ["tests/research_infra/test_moonshot_expanded_market_leakage_reduction.py"],
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
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
                "lines": count_lines(path) if path.suffix == ".jsonl" else None,
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
        "source_manifest_sha256": summary["source_manifest_sha256"],
        "source_count": len(source_manifest),
        "intake_rows": len(intake_rows),
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def stable_json_sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    built = build()
    print(
        json.dumps(
            {
                "ok": True,
                "route_id": built["route_id"],
                "intake_rows": built["intake_summary"]["rows"],
                "source_manifest_sha256": built["source_manifest_sha256"],
            },
            sort_keys=True,
        )
    )

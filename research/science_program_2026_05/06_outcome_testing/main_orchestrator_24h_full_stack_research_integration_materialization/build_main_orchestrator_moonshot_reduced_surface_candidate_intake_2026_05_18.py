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
    compact_reduced_surface_execution_row,
    summarize_reduced_surface_candidates,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_REL = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MOONSHOT_ROUTE = MOONSHOT_ROOT / MOONSHOT_ROUTE_REL

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_OUTPUT_MANIFEST_{DATE}.json"

EXECUTION_RESULT = (
    MOONSHOT_ROUTE
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_RESULT_2026-05-17.json"
)
EXECUTION_LEDGER = (
    MOONSHOT_ROUTE
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_ROW_LEDGER_2026-05-17.jsonl"
)
SURFACE_LEDGER = (
    MOONSHOT_ROUTE
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_SURFACE_LEDGER_2026-05-17.jsonl"
)
SPRINT_LEDGER = MOONSHOT_ROUTE / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

CONSUMED_FILES = [
    MOONSHOT_ROUTE_REL / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_RESULT_2026-05-17.json",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_ROW_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_SURFACE_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_SELF_TEST_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_MATCH_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_AGGREGATE_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_SYSTEM_LEDGER_2026-05-17.jsonl",
    MOONSHOT_ROUTE_REL / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_SUMMARY_2026-05-17.md",
    Path("src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"),
    MOONSHOT_ROUTE_REL / "build_expanded_market_reduced_surface_execution_2026_05_17.py",
    MOONSHOT_ROUTE_REL / "verify_expanded_market_reduced_surface_execution_2026_05_17.py",
]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def stable_json_sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_git(*args: str) -> dict[str, Any]:
    safe_directory = str(MOONSHOT_ROOT).replace("\\", "/")
    command = ["git", "-c", f"safe.directory={safe_directory}", *args]
    result = subprocess.run(command, cwd=MOONSHOT_ROOT, text=True, capture_output=True, check=False)
    return {
        "args": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
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
        "lines": count_lines(absolute) if absolute.suffix in {".jsonl", ".md", ".py"} else None,
        "sha256": sha256_path(absolute),
    }


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                rows.append((line_no, json.loads(line)))
    return rows


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


def build_candidate_rows(source_sha_by_name: dict[str, str]) -> list[dict[str, Any]]:
    surface_rows_with_lines = read_jsonl_with_lines(SURFACE_LEDGER)
    surfaces_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for line_no, row in surface_rows_with_lines:
        row_id = str(row.get("reduced_surface_row_id") or "")
        if row_id in surfaces_by_id:
            raise ValueError(f"Duplicate reduced surface row id: {row_id}")
        surfaces_by_id[row_id] = (line_no, row)

    output: list[dict[str, Any]] = []
    execution_artifact = str(EXECUTION_LEDGER.relative_to(MOONSHOT_ROOT)).replace("\\", "/")
    surface_artifact = str(SURFACE_LEDGER.relative_to(MOONSHOT_ROOT)).replace("\\", "/")
    for line_no, execution_row in read_jsonl_with_lines(EXECUTION_LEDGER):
        surface_id = str(execution_row.get("input_reduced_surface_row_id") or "")
        if surface_id not in surfaces_by_id:
            raise ValueError(f"Missing surface row for execution surface id: {surface_id}")
        surface_line_no, surface_row = surfaces_by_id[surface_id]
        output.append(
            compact_reduced_surface_execution_row(
                execution_row,
                surface_row,
                candidate_row_id=f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-CANDIDATE-{len(output) + 1:07d}",
                execution_source_artifact=execution_artifact,
                execution_source_line_no=line_no,
                execution_source_sha256=source_sha_by_name[EXECUTION_LEDGER.name],
                surface_source_artifact=surface_artifact,
                surface_source_line_no=surface_line_no,
                surface_source_sha256=source_sha_by_name[SURFACE_LEDGER.name],
            )
        )
    return output


def build() -> dict[str, Any]:
    if not MOONSHOT_ROOT.exists():
        raise FileNotFoundError(f"Moonshot root not found: {MOONSHOT_ROOT}")

    source_manifest = [source_entry(path) for path in CONSUMED_FILES]
    source_sha_by_name = {Path(entry["path"]).name: entry["sha256"] for entry in source_manifest}
    result = load_json(EXECUTION_RESULT)
    expected_output_sha = result.get("output_sha256") or {}
    for filename, expected_sha in expected_output_sha.items():
        actual_sha = source_sha_by_name.get(filename)
        if actual_sha and actual_sha != expected_sha:
            raise ValueError(f"Moonshot output hash mismatch for {filename}: {actual_sha} != {expected_sha}")

    candidate_rows = build_candidate_rows(source_sha_by_name)
    write_jsonl(OUTPUT_LEDGER, candidate_rows)

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
                "reduced_surface_rows",
                "execution_rows",
                "continuation",
            }
        }
        for row in read_checkpoint_rows()
    }
    candidate_summary = summarize_reduced_surface_candidates(candidate_rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATES",
        "schema_version": "main_orch48_moonshot_reduced_surface_candidate_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "moonshot_snapshot": moonshot_snapshot(),
        "moonshot_consumed_checkpoint_range": "CP215_THROUGH_CP224_REDUCED_SURFACE_EXECUTION",
        "moonshot_checkpoint_counts": checkpoint_counts,
        "moonshot_reduced_surface_execution_counts": result.get("counts") or {},
        "moonshot_reduced_surface_execution_ok": result.get("ok"),
        "source_manifest_sha256": stable_json_sha(source_manifest),
        "source_manifest": source_manifest,
        "candidate_summary": candidate_summary,
        "action_decision_counts": candidate_summary["main_compiler_action_counts"],
        "implementation_effect": {
            "code_surface": "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py",
            "tests": ["tests/research_infra/test_moonshot_expanded_market_reduced_surface_execution.py"],
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "result_reference_policy": {
            "primary_truth": "moonshot reduced-surface execution R is preserved as branch-local replay reference evidence",
            "counted_as_new_main_result_r": False,
            "runtime_candidate_use_permitted": False,
            "reason": "This plate converts passing branch-local reduced executions into default-off candidate surfaces; it does not enable live use or double-count R.",
        },
        "continuation": {
            "next_plate": "compile reduced-surface candidates into GTOS scorer/selector registries or replay validators with explicit default-off gates",
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
        "candidate_rows": len(candidate_rows),
        "source_manifest_sha256": summary["source_manifest_sha256"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

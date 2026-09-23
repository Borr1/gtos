"""Materialize moonshot local unified computed actions into main decisions."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.moonshot_local_unified_action_intake import compact_intake_row, summarize_intake


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

MOONSHOT_ROOT = Path(r"")
MOONSHOT_SOURCE_DIR = (
    MOONSHOT_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"

SOURCE_FILES = {
    "default_off_code_candidate": f"{PREFIX}_DEFAULT_OFF_CODE_CANDIDATE_LEDGER_{DATE}.jsonl",
    "guard_registry_spec": f"{PREFIX}_GUARD_REGISTRY_SPEC_LEDGER_{DATE}.jsonl",
    "nofill_redesign_scoring": f"{PREFIX}_NOFILL_REDESIGN_SCORING_LEDGER_{DATE}.jsonl",
    "exact_control_source_repair": f"{PREFIX}_EXACT_CONTROL_SOURCE_REPAIR_LEDGER_{DATE}.jsonl",
    "score_with_control": f"{PREFIX}_SCORE_WITH_CONTROL_RESULT_LEDGER_{DATE}.jsonl",
    "current_claim_opportunity_audit": f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_AUDIT_LEDGER_{DATE}.jsonl",
    "computed_action_recheck_source": f"{PREFIX}_COMPUTED_ACTION_LEDGER_{DATE}.jsonl",
}
RESULT_JSON = MOONSHOT_SOURCE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
RUNTIME_SPEC_JSON = MOONSHOT_SOURCE_DIR / f"{PREFIX}_RUNTIME_SPEC_{DATE}.json"
SUMMARY_MD = MOONSHOT_SOURCE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"
SOURCE_MANIFEST_LEDGER = MOONSHOT_SOURCE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_{DATE}.jsonl"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_IMPLEMENTATION_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_IMPLEMENTATION_CANDIDATE_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def long_path(path: Path) -> str:
    resolved = str(path.resolve())
    return resolved if resolved.startswith("\\\\?\\") else "\\\\?\\" + resolved


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return handle.read()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_info(path: Path) -> dict[str, Any]:
    stat = os.stat(long_path(path))
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": int(stat.st_size),
    }


def git_snapshot() -> dict[str, Any]:
    command_base = [
        "git",
        "-c",
        "core.excludesfile=",
        "-c",
        "safe.directory=C:/tmp/",
        "-C",
        str(MOONSHOT_ROOT),
    ]
    head = subprocess.run([*command_base, "rev-parse", "--short", "HEAD"], check=False, capture_output=True, text=True)
    status = subprocess.run([*command_base, "status", "--short"], check=False, capture_output=True, text=True)
    branch = subprocess.run(
        [*command_base, "rev-parse", "--abbrev-ref", "HEAD"], check=False, capture_output=True, text=True
    )
    return {
        "path": str(MOONSHOT_ROOT),
        "exists": MOONSHOT_ROOT.exists(),
        "head_short": head.stdout.strip() if head.returncode == 0 else None,
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "status_short": [line for line in status.stdout.splitlines() if line.strip()] if status.returncode == 0 else None,
        "is_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        "head_error": head.stderr.strip() if head.returncode != 0 else None,
        "status_error": status.stderr.strip() if status.returncode != 0 else None,
    }


def read_jsonl(path: Path, *, family_filter: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(long_path(path), "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if family_filter and row.get("computed_action_family") != family_filter:
                continue
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    result_json = read_json(RESULT_JSON)
    runtime_spec = read_json(RUNTIME_SPEC_JSON)
    _ = read_text(SUMMARY_MD)

    source_paths = {label: MOONSHOT_SOURCE_DIR / name for label, name in SOURCE_FILES.items()}
    source_infos = {label: source_info(path) for label, path in source_paths.items()}
    auxiliary_infos = {
        "result_json": source_info(RESULT_JSON),
        "runtime_spec_json": source_info(RUNTIME_SPEC_JSON),
        "summary_md": source_info(SUMMARY_MD),
        "source_manifest_ledger": source_info(SOURCE_MANIFEST_LEDGER),
    }

    compact_rows: list[dict[str, Any]] = []
    source_file_row_counts: Counter[str] = Counter()

    for label, path in source_paths.items():
        family_filter = "RECHECK" if label == "computed_action_recheck_source" else None
        source_rows = read_jsonl(path, family_filter=family_filter)
        source_sha = source_infos[label]["sha256"]
        for source_row in source_rows:
            intake_id = f"MAIN-ORCH24-MOONSHOT-ACTION-INTAKE-{len(compact_rows) + 1:06d}"
            compact_rows.append(
                compact_intake_row(
                    source_row,
                    intake_row_id=intake_id,
                    source_artifact=path.name,
                    source_line_no=int(source_row["_source_line_no"]),
                    source_sha256=source_sha,
                )
            )
        source_file_row_counts[label] = len(source_rows)

    implementation_rows = [
        row
        for row in compact_rows
        if row.get("main_action_class") == "IMPLEMENTATION_CANDIDATE"
    ]
    intake_summary = summarize_intake(compact_rows)
    result_family_counts = result_json.get("bucket_distributions", {}).get("computed_action_family", {})
    runtime_family_counts = runtime_spec.get("computed_action_family_counts", {})
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "rows": len(compact_rows),
        "implementation_candidate_rows": len(implementation_rows),
        "source_file_row_counts": dict(sorted(source_file_row_counts.items())),
        "moonshot_snapshot": git_snapshot(),
        "source_files": source_infos,
        "auxiliary_files": auxiliary_infos,
        "result_json_all_action_result_rows_consumed": result_json.get("all_action_result_rows_consumed"),
        "runtime_candidate_use_allowed_now": runtime_spec.get("candidate_use_allowed_now"),
        "runtime_score_allowed": runtime_spec.get("runtime_score_allowed"),
        "runtime_unconditional_scalar_use_allowed": runtime_spec.get("unconditional_scalar_use_allowed"),
        "result_json_computed_action_family_counts": result_family_counts,
        "runtime_computed_action_family_counts": runtime_family_counts,
        **intake_summary,
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "uses_proxy_delta_as_r": False,
        },
    }
    return compact_rows, implementation_rows, summary


def build_manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "description": "Main-side intake of moonshot local unified computed actions into concrete default-off/source/guard decisions.",
        "generated_utc": summary["generated_utc"],
        "inputs": {
            **summary["source_files"],
            **summary["auxiliary_files"],
        },
        "outputs": {
            path.name: {"path": str(path), "sha256": sha256_file(path)}
            for path in outputs
            if path.exists()
        },
        "key_counts": {
            "rows": summary["rows"],
            "implementation_candidate_rows": summary["implementation_candidate_rows"],
            "main_action_class_counts": summary["main_action_class_counts"],
            "numeric_proxy_delta_rows": summary["numeric_proxy_delta_rows"],
            "numeric_proxy_delta_sum_not_r": summary["numeric_proxy_delta_sum_not_r"],
            "candidate_use_allowed_now_true_rows": summary["candidate_use_allowed_now_true_rows"],
            "live_effect_true_rows": summary["live_effect_true_rows"],
            "proxy_delta_counted_as_r_rows": summary["proxy_delta_counted_as_r_rows"],
        },
        "moonshot_snapshot": summary["moonshot_snapshot"],
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows, implementation_rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_jsonl(OUTPUT_IMPLEMENTATION_LEDGER, implementation_rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_IMPLEMENTATION_LEDGER, OUTPUT_SUMMARY]))
    write_json(
        OUTPUT_MANIFEST,
        build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_IMPLEMENTATION_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]),
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

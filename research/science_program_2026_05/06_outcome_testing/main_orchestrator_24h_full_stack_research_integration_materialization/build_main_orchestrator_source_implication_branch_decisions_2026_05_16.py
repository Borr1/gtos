"""Integrate moonshot SOURCE upgraded/degraded implications into main decisions.

This is a read-only consumer of the active moonshot worktree. It copies no raw
market data and does not modify the moonshot path.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_ROOT = Path(r"")
MOONSHOT_ROUTE_DIR = (
    MOONSHOT_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
INPUT_LEDGER = (
    MOONSHOT_ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
)
INPUT_RESULT = (
    MOONSHOT_ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_RESULT_2026-05-16.json"
)

OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_LEDGER_2026-05-16.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_SUMMARY_2026-05-16.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_OUTPUT_MANIFEST_2026-05-16.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

DECISION_MAP = {
    "PRESERVE_SOURCE_ACCEPTED_CHALLENGER_CANDIDATE": (
        "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE",
        "PRESERVE_DEFAULT_OFF_REPLAY_OR_CHALLENGER_PACKET_ONLY",
        "keep_confirmed_source",
    ),
    "DOWNGRADE_ACCEPTED_SOURCE_UNTIL_EXACT_SOURCE_OR_ALTERNATIVE_SOURCE_REPAIR": (
        "DOWNGRADE_OR_AVOID_ACCEPTED_SOURCE_BRANCH",
        "KILL_OR_AVOID_UNTIL_EXACT_SOURCE_REPAIR",
        "degrade_avoid_or_repair",
    ),
    "OPEN_SOURCE_CHALLENGER_REVIEW_FROM_REPAIR_BRANCH": (
        "UPGRADE_REPAIR_TO_SOURCE_CHALLENGER_REVIEW",
        "OPEN_DEFAULT_OFF_CHALLENGER_REVIEW_FROM_REPAIR_BRANCH",
        "upgraded_challenger_review",
    ),
    "OPEN_CHALLENGER_REVIEW_AFTER_M15_ORDERING_REPAIR": (
        "M15_ORDERING_REPAIR_THEN_CHALLENGER_REVIEW",
        "ROUTE_TO_M15_ORDERING_REPAIR_BEFORE_CHALLENGER_REVIEW",
        "m15_ordering_repair",
    ),
    "SPLIT_TO_M15_ORDERING_REPAIR_BEFORE_KEEPING_SOURCE_ACCEPTED": (
        "M15_ORDERING_REPAIR_BEFORE_KEEPING_SOURCE_ACCEPTED",
        "ROUTE_TO_M15_ORDERING_REPAIR_BEFORE_KEEP_OR_REPLAY",
        "m15_ordering_repair",
    ),
    "KEEP_SOURCE_REPAIR_OR_AVOID_DECISION": (
        "KEEP_REPAIR_OR_AVOID_DECISION",
        "KEEP_REPAIR_OR_AVOID_BRANCH_NOT_PROMOTION",
        "repair_or_avoid",
    ),
    "KEEP_REPAIR_DECISION_AND_ROUTE_AMBIGUITY_TO_M15_ORDERING_REPAIR": (
        "KEEP_REPAIR_WITH_M15_ORDERING_AMBIGUITY",
        "ROUTE_AMBIGUITY_TO_M15_ORDERING_REPAIR",
        "m15_ordering_repair",
    ),
    "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR_DECISION": (
        "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR",
        "PRESERVE_REQUIREMENT_ONLY_NO_R_OR_PROXY_DECISION",
        "source_requirement_only",
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def moonshot_relpath(path: Path) -> str:
    return path.relative_to(MOONSHOT_ROOT).as_posix()


def run_moonshot_git(args: list[str]) -> dict[str, Any]:
    command = [
        "git",
        "-c",
        f"safe.directory={MOONSHOT_ROOT.as_posix()}",
        "-C",
        str(MOONSHOT_ROOT),
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except Exception as exc:  # pragma: no cover - defensive environment snapshot
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def moonshot_git_snapshot() -> dict[str, Any]:
    head = run_moonshot_git(["rev-parse", "HEAD"])
    branch = run_moonshot_git(["branch", "--show-current"])
    return {
        "moonshot_root": str(MOONSHOT_ROOT),
        "head": head.get("stdout") if head.get("returncode") == 0 else None,
        "branch": branch.get("stdout") if branch.get("returncode") == 0 else None,
        "head_git": head,
        "branch_git": branch,
    }


def classify_git_status(status_stdout: str) -> str:
    if not status_stdout.strip():
        return "CLEAN_OR_COMMITTED_AT_MOONSHOT_HEAD"
    first = status_stdout.strip().split(maxsplit=1)[0]
    if first == "??":
        return "WORKING_TREE_ONLY_UNTRACKED"
    if first:
        return "WORKING_TREE_MODIFIED_OR_INDEX_CHANGED"
    return "UNKNOWN_GIT_STATUS"


def input_artifact_snapshot(path: Path) -> dict[str, Any]:
    relpath = moonshot_relpath(path)
    status = run_moonshot_git(["status", "--short", "--", relpath])
    status_stdout = str(status.get("stdout") or "")
    return {
        "path": str(path),
        "moonshot_relative_path": relpath,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "git_status": classify_git_status(status_stdout) if status.get("returncode") == 0 else "GIT_STATUS_UNAVAILABLE",
        "git_status_stdout": status_stdout,
        "git_status_stderr": status.get("stderr"),
        "git_status_returncode": status.get("returncode"),
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def build_decision_rows(rows: list[dict[str, Any]], *, input_hash: str, result_hash: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    generated = utc_now()
    for idx, row in enumerate(rows, start=1):
        proposed = str(row.get("proposed_system_use") or "")
        branch_decision, current_main_action, bucket = DECISION_MAP.get(
            proposed,
            (
                "UNMAPPED_SOURCE_IMPLICATION_REQUIRES_REVIEW",
                "DO_NOT_USE_UNTIL_MAPPING_REPAIRED",
                "mapping_repair_required",
            ),
        )
        out.append(
            {
                "row_id": f"MAIN-ORCH24-SOURCE-IMPL-{idx:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "source_implication_implementation_id": row.get("source_implication_implementation_id"),
                "source_branch_queue_id": row.get("branch_queue_id"),
                "route_candidate_id": row.get("route_candidate_id"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "side": row.get("side"),
                "entry_variant": row.get("entry_variant"),
                "target_stop_contract_id": row.get("target_stop_contract_id"),
                "source_implication_class": row.get("source_implication_class"),
                "bar_spread_recompute_decision": row.get("bar_spread_recompute_decision"),
                "proposed_system_use": proposed,
                "branch_decision": branch_decision,
                "current_main_action": current_main_action,
                "implementation_bucket": bucket,
                "m15_ordering_requirement": row.get("m15_ordering_requirement"),
                "data_requirement_state": row.get("data_requirement_state"),
                "source_gap_handling": row.get("source_gap_handling"),
                "claim_boundary": row.get("claim_boundary"),
                "source_manifest_hash": row.get("source_manifest_hash"),
                "input_source_ledger": str(INPUT_LEDGER),
                "input_source_ledger_sha256": input_hash,
                "input_result": str(INPUT_RESULT),
                "input_result_sha256": result_hash,
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_promotion": True,
            }
        )
    return out


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def build_manifest(paths: list[Path], *, input_hash: str, result_hash: str) -> dict[str, Any]:
    input_snapshots = {
        str(INPUT_LEDGER): input_artifact_snapshot(INPUT_LEDGER),
        str(INPUT_RESULT): input_artifact_snapshot(INPUT_RESULT),
    }
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(INPUT_LEDGER): input_hash,
            str(INPUT_RESULT): result_hash,
        },
        "input_artifact_snapshots": input_snapshots,
        "moonshot_git_snapshot": moonshot_git_snapshot(),
        "output_artifacts": {
            str(path.relative_to(ROUTE_DIR)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    source_rows = read_jsonl(INPUT_LEDGER)
    source_result = read_json(INPUT_RESULT)
    input_hash = sha256_file(INPUT_LEDGER)
    result_hash = sha256_file(INPUT_RESULT)
    decision_rows = build_decision_rows(source_rows, input_hash=input_hash, result_hash=result_hash)
    write_jsonl(OUTPUT_LEDGER, decision_rows)

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_INTEGRATION",
        "claim_boundary": (
            "Main-worktree integration of moonshot SOURCE upgraded/degraded branch decisions only; "
            "no broker R/PnL, win-rate, validation, promotion, live-readiness, or live behavior."
        ),
        "input_rows": len(source_rows),
        "decision_rows": len(decision_rows),
        "source_result_counts": source_result.get("counts", {}),
        "source_score_stats": source_result.get("score_stats", {}),
        "source_system_decision": source_result.get("system_decision", {}),
        "upstream_materialization_counts": source_result.get("upstream_materialization_counts", {}),
        "upstream_source_bar_counts": source_result.get("upstream_source_bar_counts", {}),
        "source_implication_class_counts": counter(decision_rows, "source_implication_class"),
        "proposed_system_use_counts": counter(decision_rows, "proposed_system_use"),
        "branch_decision_counts": counter(decision_rows, "branch_decision"),
        "implementation_bucket_counts": counter(decision_rows, "implementation_bucket"),
        "symbol_counts": counter(decision_rows, "symbol"),
        "entry_variant_counts": counter(decision_rows, "entry_variant"),
        "m15_ordering_requirement_counts": counter(decision_rows, "m15_ordering_requirement"),
        "source_input_hashes": {
            str(INPUT_LEDGER): input_hash,
            str(INPUT_RESULT): result_hash,
        },
        "input_artifact_snapshots": {
            str(INPUT_LEDGER): input_artifact_snapshot(INPUT_LEDGER),
            str(INPUT_RESULT): input_artifact_snapshot(INPUT_RESULT),
        },
        "moonshot_git_snapshot": moonshot_git_snapshot(),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY], input_hash=input_hash, result_hash=result_hash))
    print(json.dumps({"rows_written": len(decision_rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()

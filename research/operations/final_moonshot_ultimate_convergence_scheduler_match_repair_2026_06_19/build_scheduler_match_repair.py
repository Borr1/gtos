#!/usr/bin/env python3
"""Recover Scheduler V3 candidate-match rows from the committed gzip blob."""

from __future__ import annotations

import gzip
import io
import json
import errno
import hashlib
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEDULER_REL = "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_BLOCKED_EDGE_RECOVERY_LEDGER.jsonl.gz"
SCHEDULER_PATH = ROOT / SCHEDULER_REL
PRIOR_MATCH_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_convergence_candidate_level_match_materialization_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, material: Any) -> str:
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str)
    return prefix + "_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="\n") as handle:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def direct_source_status() -> dict[str, Any]:
    row = {
        "source_key": "scheduler_v3_blocked_edge",
        "path": SCHEDULER_REL,
        "exists": SCHEDULER_PATH.exists(),
        "bytes": SCHEDULER_PATH.stat().st_size if SCHEDULER_PATH.exists() else None,
        "direct_read_status": "missing",
        "git_blob_status": "not_attempted",
        "git_blob_sha256": None,
        "broker_runtime_change_status": False,
        "direct_execution_authority": False,
    }
    if not SCHEDULER_PATH.exists():
        return row
    try:
        with gzip.open(SCHEDULER_PATH, "rt", encoding="utf-8", errors="replace") as handle:
            handle.readline()
        row["direct_read_status"] = "readable"
    except OSError as exc:
        row["direct_read_status"] = "read_error:EDEADLK" if exc.errno == errno.EDEADLK else f"read_error:{type(exc).__name__}:{exc}"
    except Exception as exc:
        row["direct_read_status"] = f"read_error:{type(exc).__name__}:{exc}"
    return row


def extract_git_blob() -> tuple[Path, str]:
    tmp = tempfile.NamedTemporaryFile(prefix="scheduler_v3_blob_", suffix=".jsonl.gz", delete=False)
    tmp_path = Path(tmp.name)
    h = hashlib.sha256()
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{SCHEDULER_REL}"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        tmp.write(proc.stdout)
        h.update(proc.stdout)
    finally:
        tmp.close()
    return tmp_path, h.hexdigest()


def side(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().upper()
    if text in {"BUY", "LONG", "1", "+1", "UP"}:
        return "LONG"
    if text in {"SELL", "SHORT", "-1", "DOWN"}:
        return "SHORT"
    return text


def build() -> dict[str, Any]:
    now = utc_now()
    source_row = direct_source_status()
    blob_path, blob_sha = extract_git_blob()
    source_row["git_blob_status"] = "readable_committed_blob"
    source_row["git_blob_sha256"] = blob_sha

    rows: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    recovery_counts: Counter[str] = Counter()
    result_class_counts: Counter[str] = Counter()
    context_counts: Counter[tuple[str | None, ...]] = Counter()
    result_r_sum = 0.0
    missed_r_sum = 0.0
    result_r_rows = 0
    positive_result_rows = 0
    negative_result_rows = 0

    try:
        with gzip.open(blob_path, "rt", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                source = json.loads(line)
                canonical_side = side(source.get("side"))
                context_key = (
                    source.get("symbol"),
                    canonical_side,
                    source.get("session_bucket"),
                    source.get("framework"),
                    source.get("origin_family"),
                )
                context_counts[context_key] += 1
                result = source.get("result_r")
                missed = source.get("missed_result_r")
                if isinstance(result, (int, float)):
                    result_r_sum += float(result)
                    result_r_rows += 1
                    if result > 0:
                        positive_result_rows += 1
                    elif result < 0:
                        negative_result_rows += 1
                if isinstance(missed, (int, float)):
                    missed_r_sum += float(missed)
                action_counts[str(source.get("scheduler_v3_action_class") or "unknown")] += 1
                decision_counts[str(source.get("scheduler_v3_decision") or "unknown")] += 1
                recovery_counts[str(source.get("blocked_edge_recovery_status") or "unknown")] += 1
                result_class_counts[str(source.get("result_r_class") or "unknown")] += 1
                rows.append(
                    {
                        "schema_version": "gtos.final_moonshot.scheduler_match_repair.row.v1",
                        "match_row_id": stable_id(
                            "sched", [source.get("candidate_id"), source.get("source_replay_row_id"), index]
                        ),
                        "source_row_index": index,
                        "candidate_id": source.get("candidate_id"),
                        "candidate_time_utc": source.get("candidate_time_utc"),
                        "symbol": source.get("symbol"),
                        "side": canonical_side,
                        "session_bucket": source.get("session_bucket"),
                        "framework": source.get("framework"),
                        "origin_family": source.get("origin_family"),
                        "scheduler_v3_decision": source.get("scheduler_v3_decision"),
                        "scheduler_v3_action_class": source.get("scheduler_v3_action_class"),
                        "scheduler_v3_action": source.get("scheduler_v3_action"),
                        "blocked_edge_recovery_status": source.get("blocked_edge_recovery_status"),
                        "lane10b_classification": source.get("lane10b_classification"),
                        "result_r": source.get("result_r"),
                        "missed_result_r": source.get("missed_result_r"),
                        "result_r_class": source.get("result_r_class"),
                        "source_completeness_state": source.get("source_completeness_state"),
                        "source_replay_row_id": source.get("source_replay_row_id"),
                        "selected_row_id": source.get("selected_row_id"),
                        "lane10_row_id": source.get("lane10_row_id"),
                        "lane16_path_row_id": source.get("lane16_path_row_id"),
                        "lane17_whiteboard_row_id": source.get("lane17_whiteboard_row_id"),
                        "runtime_effect_boundary": source.get("runtime_effect_boundary"),
                        "candidate_use_allowed_now": False,
                        "direct_execution_authority": False,
                        "broker_runtime_change_status": False,
                        "forbidden_surface_crossed": False,
                    }
                )
    finally:
        blob_path.unlink(missing_ok=True)

    context_rows = [
        {
            "symbol": key[0],
            "side": key[1],
            "session_bucket": key[2],
            "framework": key[3],
            "origin_family": key[4],
            "scheduler_v3_rows": count,
        }
        for key, count in sorted(context_counts.items(), key=lambda item: tuple("" if part is None else str(part) for part in item[0]))
    ]
    aggregate_rows = []
    for name, counter in [
        ("scheduler_v3_action_class", action_counts),
        ("scheduler_v3_decision", decision_counts),
        ("blocked_edge_recovery_status", recovery_counts),
        ("result_r_class", result_class_counts),
    ]:
        aggregate_rows.extend({"aggregate": name, "key": key, "row_count": count} for key, count in sorted(counter.items()))

    summary = {
        "schema": "gtos.final_moonshot.scheduler_match_repair.summary.v1",
        "generated_utc": now,
        "status": "scheduler_v3_candidate_match_repaired_from_committed_blob_final_selection_still_blocked",
        "source_path": SCHEDULER_REL,
        "direct_read_status": source_row["direct_read_status"],
        "git_blob_status": source_row["git_blob_status"],
        "git_blob_sha256": blob_sha,
        "scheduler_v3_rows": len(rows),
        "context_group_rows": len(context_rows),
        "result_r_rows": result_r_rows,
        "positive_result_r_rows": positive_result_rows,
        "negative_result_r_rows": negative_result_rows,
        "result_r_sum": round(result_r_sum, 9),
        "missed_result_r_sum": round(missed_r_sum, 9),
        "final_package_selected": False,
        "model_training_allowed": False,
        "broker_runtime_change_status": False,
        "direct_execution_authority": False,
        "forbidden_surface_status": {
            "live_trading": False,
            "broker_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "blind_remote_push": False,
            "live_vps_restart_or_reload": False,
        },
    }
    repairs = [
        {
            "repair_id": "SMR001_scheduler_v3_worktree_read",
            "status": "repaired_by_committed_blob_fallback",
            "direct_read_status": source_row["direct_read_status"],
            "git_blob_status": source_row["git_blob_status"],
            "source": SCHEDULER_REL,
        },
        {
            "repair_id": "SMR002_final_selection_boundary",
            "status": "still_blocked",
            "required_repair": "Broker actual-R, close-side all-in cost, fillability/order-type joins, clean labels, deterministic baselines, and adversarial acceptance remain required.",
        },
    ]
    decisions = [
        {
            "decision_id": "SMRD001",
            "status": "selected",
            "decision": "Use the committed Git blob fallback to materialize all Scheduler V3 candidate-match rows while the worktree file read remains unreliable.",
        },
        {
            "decision_id": "SMRD002",
            "status": "selected",
            "decision": "Keep Scheduler V3 rows as source-bound proxy/replay evidence with no direct execution or broker-real authority.",
        },
    ]
    completion = {
        "schema": "gtos.final_moonshot.scheduler_match_repair.completion_audit.v1",
        "generated_utc": now,
        "goal_completion_claim": False,
        "status": "not_complete_continue",
        "instruction_coverage": {
            "live_state_regenerated": True,
            "starter_and_controlling_prompt_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "vps_source_of_truth_update_read": True,
            "same_evidence_class_repair_pursued": True,
            "no_arbitrary_top_n": True,
            "full_scheduler_v3_ledger_preserved": True,
        },
        "forbidden_surface_status": summary["forbidden_surface_status"],
    }
    manifest_files = [
        "build_scheduler_match_repair.py",
        "verify_scheduler_match_repair.py",
        "SCHEDULER_MATCH_REPAIR_SUMMARY.json",
        "SCHEDULER_MATCH_REPAIR_SOURCE_LEDGER.jsonl",
        "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz",
        "SCHEDULER_MATCH_CONTEXT_LEDGER.jsonl",
        "SCHEDULER_MATCH_AGGREGATE_LEDGER.jsonl",
        "SCHEDULER_MATCH_DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "SATURATION_SELF_RED_TEAM.md",
        "OUTPUT_MANIFEST.json",
        "VERIFICATION_RESULT.json",
    ]

    write_json(ROUTE / "SCHEDULER_MATCH_REPAIR_SUMMARY.json", summary)
    write_jsonl(ROUTE / "SCHEDULER_MATCH_REPAIR_SOURCE_LEDGER.jsonl", [source_row])
    (ROUTE / "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl").unlink(missing_ok=True)
    write_jsonl_gz(ROUTE / "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz", rows)
    write_jsonl(ROUTE / "SCHEDULER_MATCH_CONTEXT_LEDGER.jsonl", context_rows)
    write_jsonl(ROUTE / "SCHEDULER_MATCH_AGGREGATE_LEDGER.jsonl", aggregate_rows)
    write_jsonl(ROUTE / "SCHEDULER_MATCH_DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repairs)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.scheduler_match_repair.focused_test_result.v1",
            "generated_utc": now,
            "status": "pending_verifier",
            "scheduler_v3_rows": len(rows),
        },
    )
    write_text(
        ROUTE / "SATURATION_SELF_RED_TEAM.md",
        f"""# Scheduler Match Repair Self Red Team

Generated: {now}

- Worktree read failure was not treated as final: the committed Git blob was extracted and parsed.
- The full Scheduler V3 projection ledger is preserved; no top-N/sample cap was used.
- Scheduler rows are source-bound proxy/replay evidence only, not broker-real R or final package authority.
- Final selection remains blocked on broker actual-R, close-side all-in cost, clean labels, fillability/order-type joins, deterministic baselines, and adversarial acceptance.
""",
    )
    write_text(
        ROUTE / "SCHEDULER_MATCH_NEXT_PROMPT.md",
        f"""# Scheduler Match Follow-Up Prompt

Generated: {now}

Continue from current disk state. Use `SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz` as the full Scheduler V3 candidate-match projection and join it with the candidate-level match materialization route, Wave4R path comparators, and hydrated replay lift evidence. Preserve all source-bound/proxy/broker-real distinctions and do not select a final package until exact final-selection gates close.
""",
    )
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.scheduler_match_repair.output_manifest.v1",
            "generated_utc": now,
            "files": [{"path": name, "exists": (ROUTE / name).exists()} for name in manifest_files + ["SCHEDULER_MATCH_NEXT_PROMPT.md"]],
        },
    )
    blob_path.unlink(missing_ok=True)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

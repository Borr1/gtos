"""Consume FVG/OB confluence bucket evidence in the action queue."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import build_strategy_outcome_rows


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_FVG_OB = Path("shadow_logs/fvg_ob_confluence.jsonl")
INPUT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_FVG_OB_CONFLUENCE_SCORER"
KILL_DECISION = "KILL_FVG_OB_CONFLUENCE_SCORER_FOR_SINGLE_FAMILY_BUCKET_ROWS"
KEEP_DECISION = "KEEP_DEFAULT_OFF_FVG_OB_BUCKET_SHARED_PATH_PROXY_SCORER"
STRATEGY_ID = "FVG_OB_CONFLUENCE_OB_AFTER_FVG"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_utc(value: Any) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def latest_by_candidate(rows: list[dict[str, Any]], *, asof_key: str = "created_at_utc") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get(asof_key))
        previous = parse_utc(out.get(cid, {}).get(asof_key))
        if current >= previous:
            out[cid] = row
    return out


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc"))
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc"))
        if current_asof > previous_asof or (
            current_asof == previous_asof and current_created >= previous_created
        ):
            out[cid] = row
    return out


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = sum(numeric)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": round(total, 8),
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def scorer_row_for_candidate(
    candidate_id: str,
    candidates: dict[str, dict[str, Any]],
    fvg_ob: dict[str, dict[str, Any]],
    paths: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    candidate = candidates.get(candidate_id)
    path = paths.get(candidate_id)
    bucket_row = fvg_ob.get(candidate_id)
    if not candidate or not path or not bucket_row:
        return None
    enriched = {
        **candidate,
        "fvg_ob_confluence_context": {
            "bucket": bucket_row.get("bucket"),
            "created_at_utc": bucket_row.get("created_at_utc"),
            "source_file": bucket_row.get("source_file"),
        },
    }
    for row in build_strategy_outcome_rows(enriched, path, created_at_utc=utc_now()):
        if row.get("strategy_id") == STRATEGY_ID:
            return row
    return None


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    candidates = latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW))
    fvg_ob = latest_by_candidate(read_jsonl(INPUT_FVG_OB))
    paths = latest_path_by_candidate(read_jsonl(INPUT_PATH_FOLLOW))

    out: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    missing_context_rows = 0
    repaired_candidate_ids: set[str] = set()

    for row in source_rows:
        clean = {k: v for k, v in row.items() if k != "_source_line_no"}
        clean["generated_utc"] = generated
        clean["route_id"] = ROUTE_ID
        clean["safe_flags"] = SAFE_FLAGS

        if clean.get("implementation_decision") != TARGET_SOURCE_DECISION:
            clean["fvg_ob_bucket_repair_status"] = "NOT_TARGET_ROW"
            out.append(clean)
            continue

        cid = str(clean.get("candidate_id") or "")
        scorer_row = scorer_row_for_candidate(cid, candidates, fvg_ob, paths)
        if scorer_row is None:
            clean["fvg_ob_bucket_repair_status"] = "UNCHANGED_MISSING_BUCKET_OR_PATH_CONTEXT"
            missing_context_rows += 1
            out.append(clean)
            continue

        bucket = scorer_row.get("fvg_ob_confluence_bucket")
        bucket_counts[str(bucket or "MISSING")] += 1
        clean["fvg_ob_confluence_bucket"] = bucket
        clean["fvg_ob_confluence_bucket_source_status"] = scorer_row.get(
            "fvg_ob_confluence_bucket_source_status"
        )
        clean["fvg_ob_bucket_repair_source_file"] = scorer_row.get(
            "fvg_ob_confluence_bucket_source_file"
        )
        clean["fvg_ob_bucket_repair_strategy_status"] = scorer_row.get("strategy_status")
        clean["fvg_ob_bucket_repair_score_status"] = scorer_row.get("score_status")

        if scorer_row.get("strategy_status") == "KILLED_FVG_OB_CONFLUENCE_NOT_PRESENT":
            clean["fvg_ob_bucket_repair_status"] = "REPAIRED_KILL_SINGLE_FAMILY_BUCKET"
            clean["action_class"] = "KILL"
            clean["coverage_status"] = "KILLED_WITH_DECISION_TIME_SOURCE_EVIDENCE"
            clean["branch_decision"] = "KILL_ROW_NOT_FVG_OB_CONFLUENCE"
            clean["implementation_decision"] = KILL_DECISION
            clean["current_action"] = "KILL_SINGLE_FAMILY_BUCKET_FROM_FVG_OB_CONFLUENCE_SCORER"
            clean["data_requirement_state"] = "CLOSED_BY_DECISION_TIME_FVG_OB_BUCKET"
            clean["next_action"] = (
                "Do not score FVG/OB confluence for rows where the decision-time bucket is single-family."
            )
            clean["decision_evidence"] = "DECISION_TIME_FVG_OB_BUCKET_NOT_BOTH_FVG_AND_OB_FIRE"
            clean["scoring_boundary"] = "NO_FVG_OB_CONFLUENCE_PROXY_R_FOR_SINGLE_FAMILY_BUCKET"
            clean["proxy_r_delta"] = 0.0
            decision_counts[KILL_DECISION] += 1
            repaired_candidate_ids.add(cid)
        elif scorer_row.get("strategy_status") == "SCORED_FVG_OB_CONFLUENCE_PROXY_SHARED_CANDIDATE_PATH":
            after_proxy = safe_float(scorer_row.get("strategy_proxy_r"))
            clean["fvg_ob_bucket_repair_status"] = "REPAIRED_KEEP_BOTH_FIRE_BUCKET_PROXY"
            clean["action_class"] = "KEEP"
            clean["coverage_status"] = "KEPT_WITH_CURRENT_EVIDENCE"
            clean["branch_decision"] = scorer_row.get("branch_decision")
            clean["implementation_decision"] = KEEP_DECISION
            clean["current_action"] = "KEEP_BUCKET_ONLY_FVG_OB_SHARED_PATH_PROXY_SCORER_DEFAULT_OFF"
            clean["data_requirement_state"] = "CURRENT_BUCKET_PROXY_COMPUTED_EXACT_BOUNDS_STILL_MISSING"
            clean["next_action"] = (
                "Keep default-off bucket-only FVG/OB confluence proxy; require exact bounds for stronger claims."
            )
            clean["decision_evidence"] = scorer_row.get("decision_evidence")
            clean["scoring_boundary"] = scorer_row.get("scoring_boundary")
            clean["after_proxy_r"] = after_proxy
            clean["proxy_r_delta"] = after_proxy
            clean["selected_shift_proxy_r"] = after_proxy
            decision_counts[KEEP_DECISION] += 1
            repaired_candidate_ids.add(cid)
        else:
            clean["fvg_ob_bucket_repair_status"] = "UNCHANGED_UNSUPPORTED_SCORER_STATUS"

        clean["no_live_behavior"] = True
        clean["no_shadow_log_append"] = True
        out.append(clean)

    before_actions = Counter(row.get("action_class") for row in source_rows)
    after_actions = Counter(row.get("action_class") for row in out)
    before_decisions = Counter(row.get("implementation_decision") for row in source_rows)
    after_decisions = Counter(row.get("implementation_decision") for row in out)
    before_proxy = proxy_stats(source_rows)
    after_proxy = proxy_stats(out)
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Versioned action queue after FVG/OB confluence bucket repair. Single-family buckets are "
            "killed for the FVG/OB confluence scorer; both-fire bucket rows are scored as default-off "
            "bucket-only shared-path proxy while exact bounds remain required for stronger claims."
        ),
        "rows": len(out),
        "input_action_rows": len(source_rows),
        "fvg_ob_source_repair_rows_before": before_decisions.get(TARGET_SOURCE_DECISION, 0),
        "fvg_ob_source_repair_rows_after": after_decisions.get(TARGET_SOURCE_DECISION, 0),
        "repaired_action_rows": sum(decision_counts.values()),
        "repaired_candidate_ids": len(repaired_candidate_ids),
        "missing_context_rows": missing_context_rows,
        "bucket_counts_on_target_rows": dict(sorted(bucket_counts.items())),
        "repair_decision_counts": dict(sorted(decision_counts.items())),
        "before_action_class_counts": dict(sorted(before_actions.items())),
        "action_class_counts": dict(sorted(after_actions.items())),
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) - before_actions.get(key, 0)
        },
        "before_implementation_decision_counts": dict(sorted(before_decisions.items())),
        "implementation_decision_counts": dict(sorted(after_decisions.items())),
        "proxy_before": before_proxy,
        "proxy_after": after_proxy,
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "exact_r_rows": 0,
        "plate_decision": "FVG_OB_CONFLUENCE_BUCKET_SOURCE_REPAIR_CONSUMED",
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "input_action_ledger": INPUT_ACTION_LEDGER,
        "strategy_follow_candidates": INPUT_STRATEGY_FOLLOW,
        "fvg_ob_confluence": INPUT_FVG_OB,
        "candidate_path_follow": INPUT_PATH_FOLLOW,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "repaired_action_rows": summary["repaired_action_rows"],
            "fvg_ob_source_repair_rows_after": summary["fvg_ob_source_repair_rows_after"],
            "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "repaired_action_rows": summary["repaired_action_rows"],
                "fvg_ob_source_repair_rows_after": summary["fvg_ob_source_repair_rows_after"],
                "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
                "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

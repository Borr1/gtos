"""Consume structural metadata plus repaired LTF ordering into action rows."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

NEGATIVE_REDESIGN_BRANCH = "REDESIGN_STRUCTURAL_METADATA_LTF_RESOLVED_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
POSITIVE_IMPLEMENT_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_REPAIRED_POSITIVE_PROXY"
SWING_SOURCE_BRANCH = "PRESERVE_SWING_PROTECTED_SOURCE_REQUIREMENT_AFTER_STRUCTURAL_METADATA_REPAIR"
TICK_ORDER_BRANCH = "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl,
)

INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
    "live_mechanical_shadow_source": REPO_ROOT / "src/research_infra/live_mechanical_shadow.py",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_with_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def latest_by_candidate(rows: list[dict[str, Any]], *, key: str = "created_at_utc") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        if parse_utc(row.get(key)) >= parse_utc(out.get(cid, {}).get(key)):
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


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("after_proxy_r") is None
        and row.get("ltf_selector_repair_status") == "NOT_REPAIRED_SOURCE_METADATA_RECOMPUTE_REQUIRED"
    )


def build_recomputed_rows(target_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    candidates = latest_by_candidate(read_jsonl(INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_jsonl(INPUTS["candidate_path_follow"]))
    metadata_by_candidate = latest_structural_metadata_by_candidate(
        read_jsonl(INPUTS["live_structural_strategy_metadata"])
    )
    ltf_rows = read_jsonl(INPUTS["candidate_ltf_path_order"])
    lifecycle_rows = read_jsonl(INPUTS["pending_limit_lifecycle"])
    needed = {(str(row.get("candidate_id") or ""), str(row.get("strategy_id") or "")) for row in target_rows}
    recomputed: dict[tuple[str, str], dict[str, Any]] = {}
    for cid in sorted({cid for cid, _ in needed}):
        candidate = candidates.get(cid)
        path = paths.get(cid)
        metadata = metadata_by_candidate.get(cid)
        if not candidate or not path or not metadata:
            continue
        enriched = merge_structural_metadata_candidate(candidate, metadata)
        ltf = latest_ltf_for_candidate_asof(enriched, path, ltf_rows)
        lifecycle = latest_lifecycle_for_candidate_asof(enriched, path, lifecycle_rows)
        rows = build_strategy_outcome_rows(
            enriched,
            path,
            pending_lifecycle_row=lifecycle,
            ltf_row=ltf,
            created_at_utc=utc_now(),
        )
        for row in rows:
            key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
            if key in needed:
                row["structural_ltf_repair_source"] = {
                    "structural_metadata_created_at_utc": metadata.get("created_at_utc"),
                    "structural_metadata_backfilled_at_utc": metadata.get("backfilled_at_utc"),
                    "structural_metadata_no_leak_status": metadata.get("no_leak_status"),
                    "ltf_status": (ltf or {}).get("ltf_status"),
                    "ltf_asof_latest_candle_utc": (ltf or {}).get("asof_latest_candle_utc"),
                    "ltf_created_at_utc": (ltf or {}).get("created_at_utc"),
                    "ltf_path_order_label": (ltf or {}).get("path_order_label"),
                    "ltf_terminal_outcome_status": (ltf or {}).get("terminal_outcome_status"),
                    "ltf_terminal_event_utc": (ltf or {}).get("terminal_event_utc"),
                    "ltf_m1_bar_count": (ltf or {}).get("m1_bar_count"),
                    "path_asof_latest_candle_utc": path.get("asof_latest_candle_utc"),
                }
                recomputed[key] = row
    return recomputed


def preserve_requirement(row: dict[str, Any], *, branch: str, evidence: str, boundary: str, candidate: str) -> dict[str, Any]:
    row["action_class"] = "PRESERVE_REQUIREMENT"
    row["coverage_status"] = "SOURCE_REQUIREMENT_PRESERVED_AFTER_STRUCTURAL_LTF_REPAIR"
    row["branch_decision"] = branch
    row["implementation_decision"] = branch
    row["current_action"] = candidate
    row["implementation_candidate"] = candidate
    row["next_action"] = candidate
    row["decision_evidence"] = evidence
    row["scoring_boundary"] = boundary
    row["underlying_intelligence_preserved"] = True
    return row


def apply_structural_ltf_repair(row: dict[str, Any], recomputed: dict[str, Any]) -> dict[str, Any]:
    value = safe_float(recomputed.get("strategy_proxy_r"))
    row["before_structural_ltf_repair_action_class"] = row.get("action_class")
    row["before_structural_ltf_repair_branch_decision"] = row.get("branch_decision")
    row["before_structural_ltf_repair_after_score_status"] = row.get("after_score_status")
    row["before_structural_ltf_repair_after_outcome_status"] = row.get("after_outcome_status")
    row["before_structural_ltf_repair_after_proxy_r"] = row.get("after_proxy_r")
    row["after_strategy_status"] = recomputed.get("strategy_status")
    row["after_score_status"] = recomputed.get("score_status")
    row["after_outcome_status"] = recomputed.get("outcome_status")
    row["after_proxy_r"] = value
    row["outcome_source"] = recomputed.get("outcome_source")
    row["ltf_path_order_label"] = recomputed.get("ltf_path_order_label")
    row["ltf_terminal_outcome_status"] = recomputed.get("ltf_terminal_outcome_status")
    row["ltf_terminal_event_utc"] = recomputed.get("ltf_terminal_event_utc")
    row["ltf_terminal_order_ambiguity"] = recomputed.get("ltf_terminal_order_ambiguity")
    row["structural_ltf_repair_source"] = recomputed.get("structural_ltf_repair_source")

    if value is not None and recomputed.get("score_status") == "COMPUTED_FROM_LTF_PATH_ORDER":
        row["structural_ltf_repair_status"] = "REPAIRED_STRUCTURAL_METADATA_AND_LTF_ORDERING"
        row["current_row_proxy_count_delta"] = 1
        row["data_requirement_state"] = "STRUCTURAL_METADATA_AND_LTF_ORDERING_SOURCE_REPAIRED"
        if value < 0:
            row["action_class"] = "REDESIGN"
            row["coverage_status"] = "REDESIGN_REQUIRED_STRUCTURAL_METADATA_LTF_RESOLVED_ADVERSE_CLUSTER"
            row["branch_decision"] = NEGATIVE_REDESIGN_BRANCH
            row["implementation_decision"] = NEGATIVE_REDESIGN_BRANCH
            row["current_action"] = "REDESIGN_STRUCTURAL_METADATA_LTF_RESOLVED_AVOID_OR_CONTEXT_FILTER"
            row["implementation_candidate"] = "REDESIGN_STRUCTURAL_METADATA_LTF_RESOLVED_AVOID_OR_CONTEXT_FILTER"
            row["next_action"] = "REDESIGN_STRUCTURAL_METADATA_LTF_RESOLVED_AVOID_OR_CONTEXT_FILTER"
            row["decision_evidence"] = (
                "STRUCTURAL_METADATA_AND_RECOVERED_M1_LTF_ORDERING_RESOLVED_ADVERSE_PROXY"
            )
            row["scoring_boundary"] = (
                "CURRENT_CLAIM_NOT_IMPLEMENTED_FOR_STRUCTURAL_METADATA_LTF_RESOLVED_ADVERSE_ROWS"
            )
            row["underlying_intelligence_preserved"] = True
            row["missed_opportunity_audit"] = {
                "kill_scope": "NOT_KILLED_REDESIGN_STRUCTURAL_LTF_ADVERSE_CLUSTER",
                "preserve_as": "STRUCTURAL_METADATA_LTF_RESOLVED_AVOID_INVERSE_OR_CONTEXT_FILTER",
                "unsupported_current_claim": (
                    "BROAD_STRUCTURAL_METADATA_DEFAULT_OFF_IMPLEMENTATION_FOR_LTF_RESOLVED_ADVERSE_ROWS"
                ),
                "what_was_tried": (
                    "REPAIRED_STRUCTURAL_METADATA_SOURCE_AND_LTF_SELECTOR_USING_RECOVERED_M1_PATH_ORDER"
                ),
                "what_could_make_it_work": (
                    "SYMBOL_SIDE_SESSION_REGIME_OR_SOURCE_FILTER_THAT_SEPARATES_ADVERSE_CONTEXTS"
                ),
                "next_route": (
                    "TEST_STRUCTURAL_METADATA_LTF_RESOLVED_ADVERSE_ROWS_AS_AVOID_INVERSE_OR_CONTEXT_FILTER"
                ),
            }
            return row
        row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
        row["coverage_status"] = "IMPLEMENTATION_CANDIDATE_STRUCTURAL_METADATA_LTF_POSITIVE_PROXY"
        row["branch_decision"] = POSITIVE_IMPLEMENT_BRANCH
        row["implementation_decision"] = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_RESOLVED_PROXY_SCORER"
        row["current_action"] = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_RESOLVED_PROXY_SCORER"
        row["implementation_candidate"] = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_RESOLVED_PROXY_SCORER"
        row["next_action"] = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_RESOLVED_PROXY_SCORER"
        row["decision_evidence"] = (
            "STRUCTURAL_METADATA_AND_RECOVERED_M1_LTF_ORDERING_RESOLVED_POSITIVE_PROXY"
        )
        row["scoring_boundary"] = "STRUCTURAL_METADATA_LTF_RESOLVED_PROXY_NO_LIVE_ENTRY_CHANGE"
        return row

    if recomputed.get("score_status") == "AMBIGUOUS_LTF_ORDER":
        row["structural_ltf_repair_status"] = "PRESERVED_SAME_M1_TICK_ORDER_REQUIREMENT"
        row["after_proxy_r"] = None
        return preserve_requirement(
            row,
            branch=TICK_ORDER_BRANCH,
            evidence="STRUCTURAL_METADATA_REPAIRED_BUT_LTF_ORDER_REMAINS_SAME_M1_AMBIGUOUS",
            boundary="NO_STRUCTURAL_METADATA_PROXY_R_WITHOUT_TICK_ORDER_FOR_SAME_M1_TERMINAL_EVENT",
            candidate="PRESERVE_TICK_ORDER_SOURCE_REQUIREMENT_FOR_STRUCTURAL_METADATA_ROW",
        )

    row["structural_ltf_repair_status"] = "PRESERVED_SWING_SOURCE_REQUIREMENT"
    row["after_proxy_r"] = None
    return preserve_requirement(
        row,
        branch=SWING_SOURCE_BRANCH,
        evidence=str(recomputed.get("strategy_status") or "STRUCTURAL_LTF_REPAIR_NO_NUMERIC_PROXY"),
        boundary="NO_SWING_PROTECTED_PROXY_R_WITHOUT_REQUIRED_SWING_STOP_SOURCE_FIELDS",
        candidate="PRESERVE_SWING_PROTECTED_STOP_SOURCE_CAPTURE_REQUIREMENT",
    )


def materialize(input_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    targets = [row for row in input_rows if target_row(row)]
    recomputed = build_recomputed_rows(targets)
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in input_rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if target_row(row):
            key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
            after = recomputed.get(key)
            if after is None:
                row["structural_ltf_repair_status"] = "NOT_REPAIRED_RECOMPUTE_ROW_MISSING"
                stats["target_rows_not_repaired"] += 1
            else:
                row = apply_structural_ltf_repair(row, after)
                status = str(row.get("structural_ltf_repair_status") or "")
                stats[status] += 1
                value = safe_float(row.get("after_proxy_r"))
                if value is not None:
                    stats["new_numeric_proxy_rows"] += 1
                    if value > 0:
                        stats["positive_numeric_rows"] += 1
                    elif value < 0:
                        stats["negative_numeric_rows"] += 1
                if row.get("action_class") == "REDESIGN":
                    stats["implement_to_redesign_rows"] += 1
                if row.get("action_class") == "PRESERVE_REQUIREMENT":
                    stats["implement_to_preserve_requirement_rows"] += 1
        else:
            row["structural_ltf_repair_status"] = "NOT_TARGET_ROW"
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, *INPUTS.values()]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in inputs
            if path.exists()
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl_with_lines(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    output_rows, stats = materialize(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before = proxy_summary(input_rows)
    after = proxy_summary(output_rows)
    repaired = [
        row
        for row in output_rows
        if row.get("structural_ltf_repair_status") != "NOT_TARGET_ROW"
    ]
    repaired_values = [safe_float(row.get("after_proxy_r")) for row in repaired]
    repaired_values = [value for value in repaired_values if value is not None]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR",
        "claim_boundary": (
            "Consumes repaired structural metadata together with repaired LTF selector ordering. "
            "Resolved positive rows remain default-off implementation candidates; resolved adverse rows "
            "move to redesign/avoid-filter candidates; unresolved swing/tick-order rows become source requirements."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_before": counter(input_rows, "action_class"),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "action_class_delta_vs_previous": {
            key: counter(output_rows, "action_class").get(key, 0)
            - counter(input_rows, "action_class").get(key, 0)
            for key in sorted(set(counter(input_rows, "action_class")) | set(counter(output_rows, "action_class")))
            if counter(output_rows, "action_class").get(key, 0)
            != counter(input_rows, "action_class").get(key, 0)
        },
        "numeric_proxy_rows_before": before["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after["numeric_proxy_rows"],
        "proxy_r_sum_before": before["proxy_r_sum"],
        "proxy_r_sum_after": after["proxy_r_sum"],
        "proxy_r_sum_delta": round(after["proxy_r_sum"] - before["proxy_r_sum"], 8),
        "touched_rows": len(repaired),
        "repaired_numeric_proxy_rows": len(repaired_values),
        "repaired_proxy_r_sum": round(sum(repaired_values), 8),
        "repaired_positive_rows": sum(1 for value in repaired_values if value > 0),
        "repaired_negative_rows": sum(1 for value in repaired_values if value < 0),
        "repair_status_counts": counter(output_rows, "structural_ltf_repair_status"),
        "repaired_branch_counts": counter(repaired, "branch_decision"),
        "repaired_strategy_counts": counter(repaired, "strategy_id"),
        "repaired_symbol_side_counts": dict(
            Counter(f"{row.get('symbol')}|{row.get('side')}" for row in repaired)
        ),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "STRUCTURAL_METADATA_LTF_REPAIR_CONSUMED_INTO_ACTION_LEDGER",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "touched_rows": len(repaired),
                "numeric_proxy_rows_after": after["numeric_proxy_rows"],
                "proxy_r_sum_after": after["proxy_r_sum"],
                "action_delta": summary["action_class_delta_vs_previous"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

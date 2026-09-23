#!/usr/bin/env python3
"""Build no-fill entry-geometry ambiguity and invalid-geometry split packet.

This packet consumes the repair/proxy packet and opens the next source-safe
work layer: M1 ambiguity stress rows, M15 envelope control/reconstruction
routes, and invalid-TP1 retargeting/redesign branches. It emits mechanical
inputs and routing labels only; it does not score outcomes, R, PnL,
expectancy, win-rate, live-readiness, or promotion.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

REPAIR_RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_RESULT_2026-05-16.json"
REPAIR_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BRANCH_LEDGER_2026-05-16.jsonl"
REPAIR_CANDIDATE_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_CANDIDATE_LEDGER_2026-05-16.jsonl"
REPAIR_BUCKET_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BUCKET_LEDGER_2026-05-16.jsonl"
REPAIR_SPREAD_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_SPREAD_LEDGER_2026-05-16.jsonl"
CHALLENGER_DENOMINATOR_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR_LEDGER_2026-05-16.jsonl"
LTF_PATH_ORDER_PATH = REPO / "shadow_logs" / "candidate_ltf_path_order.jsonl"
PATH_FOLLOW_PATH = REPO / "shadow_logs" / "candidate_path_follow.jsonl"

RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_RESULT_2026-05-16.json"
BRANCH_STATUS_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BRANCH_STATUS_LEDGER_2026-05-16.jsonl"
M1_STRESS_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M1_STRESS_LEDGER_2026-05-16.jsonl"
M15_CONTROL_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M15_CONTROL_LEDGER_2026-05-16.jsonl"
INVALID_GEOMETRY_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_INVALID_GEOMETRY_LEDGER_2026-05-16.jsonl"
CANDIDATE_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_CANDIDATE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "No-fill ambiguity/split packet only. Rows are stress assumptions, "
    "target-redesign inputs, and source-control routes; no validation, R/PnL, "
    "expectancy, win-rate, live-readiness, or live behavior change is claimed."
)

M1_AMBIGUITY_ASSUMPTIONS = [
    "ENTRY_BEFORE_TP1_WITHIN_RECOVERED_M1_ENVELOPE",
    "TP1_BEFORE_ENTRY_WITHIN_RECOVERED_M1_ENVELOPE",
    "SAME_M1_ORDER_UNRESOLVED_NEEDS_TICK_OR_BIDASK_REPLAY",
]

M15_CONTROL_ASSUMPTIONS = [
    "M15_ENVELOPE_ENTRY_BEFORE_TP1_POSSIBLE",
    "M15_ENVELOPE_TP1_BEFORE_ENTRY_POSSIBLE",
    "M15_ENVELOPE_NO_INTRABAR_ORDER_CLAIM",
    "LOWER_TIMEFRAME_RECONSTRUCTION_REQUIRED_FROM_OWNED_CURRENT_FREE_SOURCES",
]

INVALID_GEOMETRY_VARIANTS = [
    "RETARGET_ORIGINAL_RR_FROM_PROPOSED_ENTRY",
    "RETARGET_MIN_1R_FROM_PROPOSED_ENTRY",
    "MARKET_ENTRY_REDESIGN_REQUIRES_NEW_TARGET_FAMILY",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        REPAIR_RESULT_PATH,
        REPAIR_BRANCH_PATH,
        REPAIR_CANDIDATE_PATH,
        REPAIR_BUCKET_PATH,
        REPAIR_SPREAD_PATH,
        CHALLENGER_DENOMINATOR_PATH,
        LTF_PATH_ORDER_PATH,
        PATH_FOLLOW_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "status": "HASHED",
                }
            )
        else:
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                    "status": "MISSING_FAIL_CLOSED",
                }
            )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("asof_latest_candle_utc") or ""),
        str(row.get("created_at_utc") or row.get("backfilled_at_utc") or ""),
        str(row.get("row_key") or row.get("candidate_id") or ""),
    )


def latest_by_candidate(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        current = latest.get(candidate_id)
        if current is None or sort_key(row) >= sort_key(current):
            latest[candidate_id] = row
    return latest


def numeric(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def side_adjusted_distance(side: str, entry: float | None, level: float | None) -> float | None:
    if entry is None or level is None:
        return None
    if side == "LONG":
        return rounded(level - entry)
    if side == "SHORT":
        return rounded(entry - level)
    return None


def side_adjusted_risk(side: str, entry: float | None, stop: float | None) -> float | None:
    if entry is None or stop is None:
        return None
    if side == "LONG":
        return rounded(entry - stop)
    if side == "SHORT":
        return rounded(stop - entry)
    return None


def target_from_risk(side: str, entry: float | None, risk: float | None, multiple: float) -> float | None:
    if entry is None or risk is None or risk <= 0:
        return None
    if side == "LONG":
        return rounded(entry + risk * multiple)
    if side == "SHORT":
        return rounded(entry - risk * multiple)
    return None


def original_rr(side: str, original_entry: float | None, stop: float | None, original_tp: float | None) -> float | None:
    risk = side_adjusted_risk(side, original_entry, stop)
    reward = side_adjusted_distance(side, original_entry, original_tp)
    if risk is None or reward is None or risk <= 0:
        return None
    return rounded(reward / risk)


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "nofill_entry_geometry_ambiguity_split_packet",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "nofill_entry_geometry_ambiguity_split_packet",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    repair_result = read_json(REPAIR_RESULT_PATH)
    repair_branch_rows = [row for row in read_jsonl(REPAIR_BRANCH_PATH) if not row.get("_parse_error")]
    repair_candidate_rows = [row for row in read_jsonl(REPAIR_CANDIDATE_PATH) if not row.get("_parse_error")]
    denominator_rows = [row for row in read_jsonl(CHALLENGER_DENOMINATOR_PATH) if not row.get("_parse_error")]
    ltf_by_candidate = latest_by_candidate(LTF_PATH_ORDER_PATH)

    branch_status_rows: list[dict[str, Any]] = []
    m1_stress_rows: list[dict[str, Any]] = []
    m15_control_rows: list[dict[str, Any]] = []
    invalid_geometry_rows: list[dict[str, Any]] = []
    branch_status_by_candidate: dict[str, Counter[str]] = defaultdict(Counter)

    for branch in repair_branch_rows:
        status = branch.get("proxy_projection_status")
        candidate_id = branch["candidate_id"]
        branch_status_rows.append(
            {
                "branch_id": branch["branch_id"],
                "candidate_id": candidate_id,
                "symbol": branch.get("symbol"),
                "side": branch.get("side"),
                "framework": branch.get("framework"),
                "branch_type": branch.get("branch_type"),
                "proxy_projection_status": status,
                "geometry_status": branch.get("geometry_status"),
                "path_proxy_status": branch.get("path_proxy_status"),
                "side_adjusted_tp_room": branch.get("side_adjusted_tp_room"),
                "decision_spread_status_after_proxy": branch.get("decision_spread_status_after_proxy"),
                "lifecycle_proxy_status": branch.get("lifecycle_proxy_status"),
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BRANCH_STATUS",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
        )
        branch_status_by_candidate[candidate_id][str(status)] += 1

        side = str(branch.get("side") or "")
        proposed_entry = numeric(branch.get("proposed_entry_price_input_only"))
        original_entry = numeric(branch.get("original_entry_price"))
        stop = numeric(branch.get("stop_loss"))
        original_tp = numeric(branch.get("take_profit_1"))
        risk = side_adjusted_risk(side, proposed_entry, stop)
        rr = original_rr(side, original_entry, stop, original_tp)

        if status == "NO_SCORE_PROXY_READY_M1_RECOVERED_ORDER_AMBIGUOUS":
            ltf_row = ltf_by_candidate.get(candidate_id, {})
            for assumption in M1_AMBIGUITY_ASSUMPTIONS:
                m1_stress_rows.append(
                    {
                        "stress_id": f"{branch['branch_id']}::{assumption}",
                        "branch_id": branch["branch_id"],
                        "candidate_id": candidate_id,
                        "symbol": branch.get("symbol"),
                        "side": side,
                        "branch_type": branch.get("branch_type"),
                        "assumption": assumption,
                        "proposed_entry_price_input_only": branch.get("proposed_entry_price_input_only"),
                        "take_profit_1": branch.get("take_profit_1"),
                        "side_adjusted_tp_room": branch.get("side_adjusted_tp_room"),
                        "m1_bar_count": ltf_row.get("m1_bar_count"),
                        "tp1_first_touch_utc": ltf_row.get("tp1_first_touch_utc"),
                        "entry_first_touch_utc": ltf_row.get("entry_first_touch_utc"),
                        "same_m1_ambiguity": ltf_row.get("same_m1_ambiguity"),
                        "stress_result_role": "ORDER_ASSUMPTION_ONLY_NO_OUTCOME_SCORE",
                        "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M1_STRESS",
                        "claim_boundary": CLAIM_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                        "source_manifest_hash": manifest_hash,
                        "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                    }
                )
        elif status == "NO_SCORE_PROXY_AVAILABLE_M15_ENVELOPE_ONLY_LTF_REQUIRED":
            for assumption in M15_CONTROL_ASSUMPTIONS:
                m15_control_rows.append(
                    {
                        "control_id": f"{branch['branch_id']}::{assumption}",
                        "branch_id": branch["branch_id"],
                        "candidate_id": candidate_id,
                        "symbol": branch.get("symbol"),
                        "side": side,
                        "branch_type": branch.get("branch_type"),
                        "assumption": assumption,
                        "proposed_entry_price_input_only": branch.get("proposed_entry_price_input_only"),
                        "take_profit_1": branch.get("take_profit_1"),
                        "side_adjusted_tp_room": branch.get("side_adjusted_tp_room"),
                        "source_route": "attempt_owned_current_free_ltf_reconstruction_or_m15_envelope_stress_control",
                        "control_result_role": "ENVELOPE_ASSUMPTION_ONLY_NO_INTRABAR_ORDER_CLAIM",
                        "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M15_CONTROL",
                        "claim_boundary": CLAIM_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                        "source_manifest_hash": manifest_hash,
                        "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                    }
                )
        elif status == "ROUTE_SPLIT_INVALID_TP1_GEOMETRY":
            for variant in INVALID_GEOMETRY_VARIANTS:
                if variant == "RETARGET_ORIGINAL_RR_FROM_PROPOSED_ENTRY":
                    target = target_from_risk(side, proposed_entry, risk, rr if rr is not None else 1.5)
                    target_rule = "new target preserves original side-adjusted RR if computable; fallback 1.5R"
                elif variant == "RETARGET_MIN_1R_FROM_PROPOSED_ENTRY":
                    target = target_from_risk(side, proposed_entry, risk, 1.0)
                    target_rule = "new target is 1.0R from proposed entry for stress/comparison input"
                else:
                    target = None
                    target_rule = "market-entry redesign requires separate target family; original TP1 cannot be reused"
                invalid_geometry_rows.append(
                    {
                        "split_id": f"{branch['branch_id']}::{variant}",
                        "branch_id": branch["branch_id"],
                        "candidate_id": candidate_id,
                        "symbol": branch.get("symbol"),
                        "side": side,
                        "branch_type": branch.get("branch_type"),
                        "split_variant": variant,
                        "original_entry_price": branch.get("original_entry_price"),
                        "proposed_entry_price_input_only": branch.get("proposed_entry_price_input_only"),
                        "original_take_profit_1": branch.get("take_profit_1"),
                        "stop_loss": branch.get("stop_loss"),
                        "side_adjusted_original_tp_room_from_proposed": branch.get("side_adjusted_tp_room"),
                        "side_adjusted_risk_from_proposed": risk,
                        "original_rr_estimate": rr,
                        "redesigned_take_profit_1_input_only": target,
                        "target_rule": target_rule,
                        "split_result_role": "TARGET_REDESIGN_INPUT_ONLY_NO_OUTCOME_SCORE",
                        "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_INVALID_GEOMETRY",
                        "claim_boundary": CLAIM_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                        "source_manifest_hash": manifest_hash,
                        "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                    }
                )

    candidate_rows: list[dict[str, Any]] = []
    for candidate in repair_candidate_rows:
        candidate_id = candidate["candidate_id"]
        counts = branch_status_by_candidate[candidate_id]
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "symbol": candidate.get("symbol"),
                "side": candidate.get("side"),
                "framework": candidate.get("framework"),
                "branch_count": sum(counts.values()),
                "proxy_projection_status_counts": dict(sorted(counts.items())),
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_CANDIDATE",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
        )

    bucket_axes = {
        "proxy_projection_status": Counter(row["proxy_projection_status"] for row in branch_status_rows),
        "m1_assumption": Counter(row["assumption"] for row in m1_stress_rows),
        "m15_assumption": Counter(row["assumption"] for row in m15_control_rows),
        "invalid_geometry_variant": Counter(row["split_variant"] for row in invalid_geometry_rows),
        "candidate_status_combo": Counter(
            "|".join(f"{status}:{count}" for status, count in row["proxy_projection_status_counts"].items())
            for row in candidate_rows
        ),
    }
    bucket_rows: list[dict[str, Any]] = []
    for axis, counter in bucket_axes.items():
        for bucket, count in sorted(counter.items()):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": bucket,
                    "count": count,
                    "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BUCKET",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

    question_rows: list[dict[str, Any]] = [
        {
            "question_id": "NOFILL-AMBIGUITY-SPLIT-QUESTION-001",
            "question": "Which same-resource replay resolves the M1 recovered order ambiguity?",
            "row_count": len(m1_stress_rows),
            "next_same_resource_action": "attempt tick/bid-ask replay or same-M1 assumption stress for all M1 stress rows",
            "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "question_id": "NOFILL-AMBIGUITY-SPLIT-QUESTION-002",
            "question": "Which lower-timeframe source or envelope stress best handles M15-only no-fill branches?",
            "row_count": len(m15_control_rows),
            "next_same_resource_action": "search owned/current/free LTF sources, then run M15-envelope stress controls if exact LTF stays unavailable",
            "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "question_id": "NOFILL-AMBIGUITY-SPLIT-QUESTION-003",
            "question": "Which target family replaces invalid original TP1 geometry?",
            "row_count": len(invalid_geometry_rows),
            "next_same_resource_action": "materialize target-retargeting and market-entry redesign grids against source-safe path controls",
            "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
    ]

    counts = {
        "branch_status_rows": len(branch_status_rows),
        "bucket_rows": len(bucket_rows),
        "candidate_rows": len(candidate_rows),
        "challenger_denominator_rows": len(denominator_rows),
        "invalid_geometry_split_rows": len(invalid_geometry_rows),
        "m15_control_rows": len(m15_control_rows),
        "m1_stress_rows": len(m1_stress_rows),
        "question_rows": len(question_rows),
        "repair_branch_rows": len(repair_branch_rows),
        "repair_candidate_rows": len(repair_candidate_rows),
        "source_manifest_rows": len(manifest_rows),
    }
    result = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "nofill_entry_geometry_ambiguity_split_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This ambiguity/split packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "upstream_repair_counts": repair_result.get("counts", {}),
        "proxy_projection_status_counts": dict(sorted(bucket_axes["proxy_projection_status"].items())),
        "m1_assumption_counts": dict(sorted(bucket_axes["m1_assumption"].items())),
        "m15_assumption_counts": dict(sorted(bucket_axes["m15_assumption"].items())),
        "invalid_geometry_variant_counts": dict(sorted(bucket_axes["invalid_geometry_variant"].items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "attempt tick/bid-ask replay for the M1 recovered ambiguity rows",
            "attempt owned/current/free lower-timeframe reconstruction for M15-only controls",
            "materialize target-retargeting grids for invalid-TP1 rows",
            "compare market-entry redesign target families on source-safe controls",
        ],
    }

    write_jsonl(BRANCH_STATUS_PATH, branch_status_rows)
    write_jsonl(M1_STRESS_PATH, m1_stress_rows)
    write_jsonl(M15_CONTROL_PATH, m15_control_rows)
    write_jsonl(INVALID_GEOMETRY_PATH, invalid_geometry_rows)
    write_jsonl(CANDIDATE_PATH, candidate_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# No-Fill Entry Geometry Ambiguity/Split Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet preserves every repair/proxy branch and opens the next same-resource work layer without scoring outcomes.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Proxy Projection Status Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(bucket_axes["proxy_projection_status"].items())),
                "",
                "## Immediate Work",
                "",
                "- Attempt tick/bid-ask replay for the M1 recovered ambiguity rows.",
                "- Attempt owned/current/free lower-timeframe reconstruction for M15-only controls.",
                "- Materialize target-retargeting grids for invalid-TP1 rows.",
                "- Compare market-entry redesign target families on source-safe controls.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": counts, "proxy_projection_status_counts": result["proxy_projection_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

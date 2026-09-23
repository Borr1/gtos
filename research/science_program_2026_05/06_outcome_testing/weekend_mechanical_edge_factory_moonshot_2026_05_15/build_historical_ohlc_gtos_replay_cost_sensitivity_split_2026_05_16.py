#!/usr/bin/env python3
"""Split OHLC replay cost-sensitivity signatures into immediate work routes."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

COST_SENSITIVITY_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_RESULT_2026-05-16.json"
SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SIGNATURE_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_RESULT_2026-05-16.json"
CHANGED_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_CHANGED_SIGNATURE_LEDGER_2026-05-16.jsonl"
GRADIENT_REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_GRADIENT_REQUIREMENT_LEDGER_2026-05-16.jsonl"
UNFILLED_SPLIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_UNFILLED_LEDGER_2026-05-16.jsonl"
AMBIGUITY_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_AMBIGUITY_SIGNATURE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay cost-sensitivity split packet only. Rows split "
    "descriptor transitions into source-search, ambiguity, unfilled, and stress "
    "routes; no validation, R/PnL, expectancy, win-rate, live-readiness, "
    "promotion, or live behavior change is claimed."
)


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
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [COST_SENSITIVITY_RESULT_PATH, SIGNATURE_PATH, COST_STATUS_PATH, TARGET_STOP_CONTRACT_PATH]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def seq_from_id(value: Any) -> int:
    return int(str(value).rsplit("-", 1)[-1])


def invert_codes(code_map: dict[str, str]) -> dict[int, str]:
    return {int(code): status for code, status in code_map.items()}


def statuses_from_signature(row: dict[str, Any], first_touch_codes: dict[int, str]) -> dict[str, str]:
    return {
        "ZERO_COST_CONTROL": first_touch_codes[int(row["z"])],
        "SYMBOL_MEDIAN_SPREAD_PROXY": first_touch_codes[int(row["md"])],
        "SYMBOL_MAX_SPREAD_PROXY": first_touch_codes[int(row["mx"])],
        "STATIC_CONSERVATIVE_FALLBACK_PROXY": first_touch_codes[int(row["st"])],
    }


def transition_signature(statuses: dict[str, str]) -> str:
    return "|".join(f"{model}={status}" for model, status in statuses.items())


def changed_models(statuses: dict[str, str]) -> list[str]:
    zero = statuses["ZERO_COST_CONTROL"]
    return [model for model, status in statuses.items() if model != "ZERO_COST_CONTROL" and status != zero]


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_cost_sensitivity_split_packet",
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
        "route": "historical_ohlc_gtos_replay_cost_sensitivity_split_packet",
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
    result = read_json(COST_SENSITIVITY_RESULT_PATH)
    first_touch_codes = invert_codes(result["first_touch_status_codes"])
    sensitivity_codes = invert_codes(result["sensitivity_status_codes"])
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    target_rows = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]
    cost_by_entry_seq: dict[int, dict[str, Any]] = {}
    for row in cost_rows:
        cost_by_entry_seq.setdefault(seq_from_id(row["entry_variant_id"]), row)
    target_by_seq = {seq_from_id(row["target_stop_contract_id"]): row for row in target_rows}

    changed_rows: list[dict[str, Any]] = []
    gradient_rows: list[dict[str, Any]] = []
    unfilled_rows: list[dict[str, Any]] = []
    ambiguity_rows: list[dict[str, Any]] = []
    status_counter: Counter[str] = Counter()
    route_status_counter: Counter[tuple[str, str]] = Counter()
    entry_status_counter: Counter[tuple[str, str]] = Counter()
    target_status_counter: Counter[tuple[str, str]] = Counter()
    changed_model_counter: Counter[str] = Counter()
    ambiguity_status_counter: Counter[str] = Counter()

    for row in read_jsonl(SIGNATURE_PATH):
        if row.get("_parse_error"):
            continue
        signature_id = f"OHLC-GTOS-COST-SENS-SIG-{int(row['s']):05d}"
        entry_seq = int(row["ev"])
        target_seq = int(row["tc"])
        cost = cost_by_entry_seq[entry_seq]
        target = target_by_seq[target_seq]
        sensitivity_status = sensitivity_codes[int(row["cs"])]
        statuses = statuses_from_signature(row, first_touch_codes)
        changed = changed_models(statuses)
        has_ambiguity = any(
            status == "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS"
            for status in statuses.values()
        )
        status_counter[sensitivity_status] += 1
        route_status_counter[(str(cost["route_candidate_id"]), sensitivity_status)] += 1
        entry_status_counter[(str(cost["entry_variant"]), sensitivity_status)] += 1
        target_status_counter[(str(target["target_stop_contract_id"]), sensitivity_status)] += 1
        for model in changed:
            changed_model_counter[model] += 1

        base = {
            "cost_sensitivity_signature_id": signature_id,
            "entry_variant_id": cost["entry_variant_id"],
            "event_id": cost["event_id"],
            "route_candidate_id": cost["route_candidate_id"],
            "symbol": cost["symbol"],
            "side": cost["side"],
            "entry_variant": cost["entry_variant"],
            "target_stop_contract_id": target["target_stop_contract_id"],
            "target_multiple": target["target_multiple_of_rolling_median_range"],
            "stop_multiple": target["stop_multiple_of_rolling_median_range"],
            "cost_sensitivity_status": sensitivity_status,
            "changed_models": changed,
            "transition_signature": transition_signature(statuses),
            "has_same_m15_ambiguity": has_ambiguity,
            "source_manifest_hash": manifest_hash,
        }
        if sensitivity_status in {
            "ZERO_TO_SPREAD_PROXY_DESCRIPTOR_SHIFT",
            "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE",
        }:
            changed_rows.append(
                {
                    **base,
                    "split_action": "SPLIT_CHANGED_COST_DESCRIPTOR_BY_ROUTE_ENTRY_TARGET_STOP",
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_CHANGED_SIGNATURE",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
        if sensitivity_status == "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE":
            gradient_rows.append(
                {
                    **base,
                    "gradient_requirement_status": "EXACT_SPREAD_SLIPPAGE_SOURCE_SEARCH_OR_CONSERVATIVE_STRESS_NOW",
                    "next_same_resource_action": "search exact spread/slippage source for route/date/symbol or build conservative stress bounds from owned logs",
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_GRADIENT_REQUIREMENT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
        if sensitivity_status == "COST_INVARIANT_POST_SIGNAL_UNFILLED":
            unfilled_rows.append(
                {
                    **base,
                    "unfilled_split_status": "COST_INVARIANT_RETEST_LIMIT_NOT_RETOUCHED_POST_SIGNAL",
                    "next_same_resource_action": "split retest-limit unfilled rows from market-entry descriptors and route to LTF reconstruction/stress",
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_UNFILLED_SPLIT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
        if has_ambiguity:
            ambiguity_status_counter[sensitivity_status] += 1
            ambiguity_rows.append(
                {
                    **base,
                    "ambiguity_split_status": "SAME_M15_TARGET_STOP_AMBIGUITY_PRESENT_IN_AT_LEAST_ONE_COST_MODEL",
                    "next_same_resource_action": "route to M1/tick reconstruction or conservative target/stop ordering stress bounds",
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_AMBIGUITY_SIGNATURE",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    bucket_rows: list[dict[str, Any]] = []

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_value = "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket)
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": bucket_value,
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("cost_sensitivity_status", status_counter)
    add_bucket("route_candidate_id__cost_sensitivity_status", route_status_counter)
    add_bucket("entry_variant__cost_sensitivity_status", entry_status_counter)
    add_bucket("target_stop_contract__cost_sensitivity_status", target_status_counter)
    add_bucket("changed_cost_model", changed_model_counter)
    add_bucket("ambiguity_signature_status", ambiguity_status_counter)

    question_rows = [
        {
            "question_id": "OHLC-GTOS-COST-SENS-SPLIT-QUESTION-001",
            "question": "Which changed cost-sensitive signatures are route/entry/target-stop families rather than isolated rows?",
            "row_count": len(changed_rows),
            "next_same_resource_action": "aggregate changed signatures by route, entry variant, and target/stop contract and compare to ambiguity/unfilled splits",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-SPLIT-QUESTION-002",
            "question": "Which gradient-sensitive signatures need exact spread/slippage source search versus stress-bound proxy?",
            "row_count": len(gradient_rows),
            "next_same_resource_action": "search owned logs/source roots for exact spread rows; if absent, build source-safe stress bounds",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-SPLIT-QUESTION-003",
            "question": "Which unfilled and same-M15 ambiguous signatures need LTF/tick reconstruction first?",
            "row_count": len(unfilled_rows) + len(ambiguity_rows),
            "next_same_resource_action": "join unfilled/ambiguity signatures to available M1/tick paths and no-fill geometry packets",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "ambiguity_signature_rows": len(ambiguity_rows),
        "bucket_rows": len(bucket_rows),
        "changed_signature_rows": len(changed_rows),
        "gradient_requirement_rows": len(gradient_rows),
        "question_rows": len(question_rows),
        "signature_input_rows": result["counts"]["signature_rows"],
        "source_manifest_rows": len(manifest_rows),
        "unfilled_split_rows": len(unfilled_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_cost_sensitivity_split_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This cost-sensitivity split packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "cost_sensitivity_status_counts": dict(sorted(status_counter.items())),
        "changed_cost_model_counts": dict(sorted(changed_model_counter.items())),
        "ambiguity_signature_status_counts": dict(sorted(ambiguity_status_counter.items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "upstream_cost_sensitivity_counts": result["counts"],
        "next_same_resource_work": [
            "aggregate changed signatures by route/entry/target-stop family",
            "search exact spread/slippage source for gradient-sensitive rows or build conservative stress bounds",
            "join unfilled and ambiguity signatures to M1/tick/no-fill reconstruction routes",
        ],
    }

    write_jsonl(CHANGED_SIGNATURE_PATH, changed_rows)
    write_jsonl(GRADIENT_REQUIREMENT_PATH, gradient_rows)
    write_jsonl(UNFILLED_SPLIT_PATH, unfilled_rows)
    write_jsonl(AMBIGUITY_SIGNATURE_PATH, ambiguity_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Cost-Sensitivity Split",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet splits changed, gradient-sensitive, unfilled, and same-M15 ambiguous cost-sensitivity signatures into immediate work routes.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Immediate Work",
                "",
                "- Aggregate changed signatures by route/entry/target-stop family.",
                "- Search exact spread/slippage source for gradient-sensitive rows or build conservative stress bounds.",
                "- Join unfilled and ambiguity signatures to M1/tick/no-fill reconstruction routes.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

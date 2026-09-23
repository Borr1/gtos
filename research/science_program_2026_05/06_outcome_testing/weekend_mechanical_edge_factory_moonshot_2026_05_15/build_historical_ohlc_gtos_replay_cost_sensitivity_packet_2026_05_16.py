#!/usr/bin/env python3
"""Build historical OHLC GTOS replay cost-sensitivity packet.

Consumes the compact path-control grid and compares zero-cost descriptors
against median/max/static spread proxy descriptors for every entry variant and
target/stop contract. This is source-control evidence only, not validation or
performance evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

PATH_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_RESULT_2026-05-16.json"
PATH_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_GRID_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_RESULT_2026-05-16.json"
SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SIGNATURE_LEDGER_2026-05-16.jsonl"
MODEL_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_MODEL_DELTA_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

COST_MODELS = [
    "ZERO_COST_CONTROL",
    "SYMBOL_MEDIAN_SPREAD_PROXY",
    "SYMBOL_MAX_SPREAD_PROXY",
    "STATIC_CONSERVATIVE_FALLBACK_PROXY",
]
NONZERO_COST_MODELS = COST_MODELS[1:]
MODEL_CODES = {model: index for index, model in enumerate(COST_MODELS)}
FIRST_TOUCH_STATUS_CODES = {
    "MISSING_MODEL_STATUS": 0,
    "MISSING_ZERO_COST_STATUS": 1,
    "NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON": 2,
    "POST_SIGNAL_ENTRY_NOT_FILLED_WITHIN_HORIZON": 3,
    "STOP_TOUCH_BEFORE_TARGET_M15_PROXY": 4,
    "STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY": 5,
    "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS": 6,
    "TARGET_TOUCH_BEFORE_STOP_M15_PROXY": 7,
    "TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY": 8,
}
SENSITIVITY_STATUS_CODES = {
    "COST_SIGNATURE_INCOMPLETE_FAIL_CLOSED": 0,
    "COST_INVARIANT_DESCRIPTOR": 1,
    "COST_INVARIANT_POST_SIGNAL_UNFILLED": 2,
    "ZERO_TO_SPREAD_PROXY_DESCRIPTOR_SHIFT": 3,
    "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE": 4,
}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay cost-sensitivity packet only. Rows compare "
    "path-control descriptor transitions across zero and spread-proxy cost "
    "models; no validation, R/PnL, expectancy, win-rate, live-readiness, "
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
    paths = [PATH_RESULT_PATH, PATH_GRID_PATH, COST_STATUS_PATH, TARGET_STOP_CONTRACT_PATH]
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


def classify_signature(status_by_model: dict[str, str]) -> str:
    zero = status_by_model.get("ZERO_COST_CONTROL")
    nonzero = [status_by_model.get(model) for model in NONZERO_COST_MODELS]
    if any(status is None for status in [zero, *nonzero]):
        return "COST_SIGNATURE_INCOMPLETE_FAIL_CLOSED"
    if all(status == zero for status in nonzero):
        if zero == "POST_SIGNAL_ENTRY_NOT_FILLED_WITHIN_HORIZON":
            return "COST_INVARIANT_POST_SIGNAL_UNFILLED"
        return "COST_INVARIANT_DESCRIPTOR"
    if len(set(nonzero)) == 1:
        return "ZERO_TO_SPREAD_PROXY_DESCRIPTOR_SHIFT"
    return "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE"


def transition_label(zero_status: str, model_status: str) -> str:
    if zero_status == model_status:
        return "UNCHANGED_FROM_ZERO_COST"
    return f"{zero_status}__TO__{model_status}"


def model_change_mask(changed_models: list[str]) -> int:
    mask = 0
    for model in changed_models:
        if model == "SYMBOL_MEDIAN_SPREAD_PROXY":
            mask |= 1
        elif model == "SYMBOL_MAX_SPREAD_PROXY":
            mask |= 2
        elif model == "STATIC_CONSERVATIVE_FALLBACK_PROXY":
            mask |= 4
    return mask


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_cost_sensitivity_packet",
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
        "route": "historical_ohlc_gtos_replay_cost_sensitivity_packet",
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
    path_result = read_json(PATH_RESULT_PATH)
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    target_contract_rows = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]
    cost_by_seq = {seq_from_id(row["cost_fill_id"]): row for row in cost_rows}
    cost_by_entry_variant: dict[str, dict[str, Any]] = {}
    for row in cost_rows:
        cost_by_entry_variant.setdefault(str(row["entry_variant_id"]), row)
    target_by_seq = {seq_from_id(row["target_stop_contract_id"]): row for row in target_contract_rows}

    grouped: dict[tuple[str, int], dict[str, str]] = {}
    for row in read_jsonl(PATH_GRID_PATH):
        if row.get("_parse_error"):
            continue
        cost = cost_by_seq.get(int(row["cf"]))
        if not cost:
            continue
        key = (str(cost["entry_variant_id"]), int(row["tc"]))
        grouped.setdefault(key, {})[str(cost["cost_model"])] = str(row["st"])

    signature_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    signature_status_counter: Counter[str] = Counter()
    route_status_counter: Counter[tuple[str, str]] = Counter()
    entry_variant_status_counter: Counter[tuple[str, str]] = Counter()
    target_contract_status_counter: Counter[tuple[str, str]] = Counter()
    transition_counter: Counter[str] = Counter()
    transition_codes: dict[str, int] = {}

    def transition_code(label: str) -> int:
        if label not in transition_codes:
            transition_codes[label] = len(transition_codes) + 1
        return transition_codes[label]

    for sig_index, ((entry_variant_id, target_seq), status_by_model) in enumerate(sorted(grouped.items()), 1):
        zero_status = status_by_model.get("ZERO_COST_CONTROL", "MISSING_ZERO_COST_STATUS")
        cost = cost_by_entry_variant[entry_variant_id]
        target_contract = target_by_seq[target_seq]
        signature_status = classify_signature(status_by_model)
        changed_models = [
            model
            for model in NONZERO_COST_MODELS
            if status_by_model.get(model) != zero_status
        ]
        signature_status_counter[signature_status] += 1
        route_status_counter[(str(cost["route_candidate_id"]), signature_status)] += 1
        entry_variant_status_counter[(str(cost["entry_variant"]), signature_status)] += 1
        target_contract_status_counter[(str(target_contract["target_stop_contract_id"]), signature_status)] += 1
        signature_rows.append(
            {
                "s": sig_index,
                "ev": seq_from_id(entry_variant_id),
                "tc": target_seq,
                "z": FIRST_TOUCH_STATUS_CODES[zero_status],
                "md": FIRST_TOUCH_STATUS_CODES[status_by_model.get("SYMBOL_MEDIAN_SPREAD_PROXY", "MISSING_MODEL_STATUS")],
                "mx": FIRST_TOUCH_STATUS_CODES[status_by_model.get("SYMBOL_MAX_SPREAD_PROXY", "MISSING_MODEL_STATUS")],
                "st": FIRST_TOUCH_STATUS_CODES[status_by_model.get("STATIC_CONSERVATIVE_FALLBACK_PROXY", "MISSING_MODEL_STATUS")],
                "cs": SENSITIVITY_STATUS_CODES[signature_status],
                "cm": model_change_mask(changed_models),
            }
        )
        for model in NONZERO_COST_MODELS:
            transition = transition_label(zero_status, status_by_model.get(model, "MISSING_MODEL_STATUS"))
            transition_counter[transition] += 1
            delta_rows.append(
                {
                    "d": len(delta_rows) + 1,
                    "s": sig_index,
                    "m": MODEL_CODES[model],
                    "tr": transition_code(transition),
                    "ch": status_by_model.get(model) != zero_status,
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
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("cost_sensitivity_status", signature_status_counter)
    add_bucket("route_candidate_id__cost_sensitivity_status", route_status_counter)
    add_bucket("entry_variant__cost_sensitivity_status", entry_variant_status_counter)
    add_bucket("target_stop_contract__cost_sensitivity_status", target_contract_status_counter)
    add_bucket("zero_to_cost_model_transition_status", transition_counter)

    question_rows = [
        {
            "question_id": "OHLC-GTOS-COST-SENS-QUESTION-001",
            "question": "Which entry/target/stop signatures change descriptor class once spread proxies are applied?",
            "row_count": len(signature_rows),
            "next_same_resource_action": "split changed signatures by route, entry variant, and target/stop contract",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-QUESTION-002",
            "question": "Which spread proxy source creates descriptor gradients rather than a uniform zero-to-spread shift?",
            "row_count": signature_status_counter.get("SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE", 0),
            "next_same_resource_action": "route gradient-sensitive rows into exact spread/slippage source search or conservative stress bounds",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-QUESTION-003",
            "question": "Which cost-invariant post-signal unfilled rows should be split from market-entry path controls?",
            "row_count": signature_status_counter.get("COST_INVARIANT_POST_SIGNAL_UNFILLED", 0),
            "next_same_resource_action": "split retest-limit unfilled signatures from market-entry descriptors and route to LTF reconstruction",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "cost_fill_status_input_rows": len(cost_rows),
        "model_delta_rows": len(delta_rows),
        "path_grid_input_rows": path_result.get("counts", {}).get("path_control_grid_rows"),
        "question_rows": len(question_rows),
        "signature_rows": len(signature_rows),
        "source_manifest_rows": len(manifest_rows),
        "target_stop_contract_input_rows": len(target_contract_rows),
    }
    result = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_cost_sensitivity_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This cost-sensitivity packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "cost_models": COST_MODELS,
        "model_codes": {str(code): model for model, code in MODEL_CODES.items()},
        "first_touch_status_codes": {str(code): status for status, code in FIRST_TOUCH_STATUS_CODES.items()},
        "sensitivity_status_codes": {str(code): status for status, code in SENSITIVITY_STATUS_CODES.items()},
        "transition_status_codes": {str(code): status for status, code in sorted(transition_codes.items(), key=lambda item: item[1])},
        "signature_compact_schema": {
            "s": "signature sequence; reconstruct OHLC-GTOS-COST-SENS-SIG-{s:05d}",
            "ev": "entry variant sequence; reconstruct OHLC-GTOS-REPLAY-ENTRY-{ev:05d}",
            "tc": "target/stop contract sequence; reconstruct OHLC-GTOS-PATH-TARGETSTOP-{tc:03d}",
            "z": "zero-cost first-touch status code",
            "md": "symbol-median-spread first-touch status code",
            "mx": "symbol-max-spread first-touch status code",
            "st": "static-conservative-spread first-touch status code",
            "cs": "cost-sensitivity status code",
            "cm": "changed-model bitmask: median=1, max=2, static=4",
        },
        "model_delta_compact_schema": {
            "d": "delta sequence; reconstruct OHLC-GTOS-COST-SENS-DELTA-{d:06d}",
            "s": "signature sequence join key",
            "m": "comparison model code",
            "tr": "zero-to-model transition status code",
            "ch": "descriptor changed from zero-cost boolean",
        },
        "cost_sensitivity_status_counts": dict(sorted(signature_status_counter.items())),
        "transition_status_counts": dict(sorted(transition_counter.items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "upstream_path_counts": path_result.get("counts", {}),
        "next_same_resource_work": [
            "split changed cost-sensitive signatures by route and entry variant",
            "route gradient-sensitive rows into exact spread/slippage source search or conservative stress bounds",
            "split cost-invariant post-signal unfilled rows from market-entry path controls",
            "join cost sensitivity to same-M15 ambiguity and no-fill geometry controls",
        ],
    }

    write_jsonl(SIGNATURE_PATH, signature_rows)
    write_jsonl(MODEL_DELTA_PATH, delta_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Cost-Sensitivity Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet compares zero-cost path descriptors against median/max/static spread proxy descriptors for every entry variant and target/stop contract.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Cost Sensitivity Status Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(signature_status_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Split changed cost-sensitive signatures by route and entry variant.",
                "- Route gradient-sensitive rows into exact spread/slippage source search or conservative stress bounds.",
                "- Split cost-invariant post-signal unfilled rows from market-entry path controls.",
                "- Join cost sensitivity to same-M15 ambiguity and no-fill geometry controls.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": counts, "cost_sensitivity_status_counts": result["cost_sensitivity_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

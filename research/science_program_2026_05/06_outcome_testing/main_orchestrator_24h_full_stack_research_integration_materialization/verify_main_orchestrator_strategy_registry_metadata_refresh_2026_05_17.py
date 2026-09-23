"""Verify strategy registry metadata refresh plate."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
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

from src.research_infra.forward_capture import FOLLOW_STRATEGY_REGISTRY


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_2026-05-17.jsonl"
)
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = (
    ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_VERIFICATION_RESULT_{DATE}.json"
)

WATCHED_STRATEGY_IDS = {
    "V2_STRUCT_FVG_MID_EDGE",
    "V3_FVG_ONLY_RESCUE_RISK_BANK",
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
    "V2_STRUCT_SWING_PROTECTED",
    "V2_STRUCT_COMPOSITE_ANY",
    "V3_FVG_THEN_OB_TAIL_RISK_BANK",
    "V3_OB_LOCK_PULLBACK_RISK_BANK",
    "V3_OB_LOCK_COST_AWARE_MIN_R",
    "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
    "PENDING_LIMIT_LIFECYCLE",
}

EXPECTED_STRATEGY_PROXY = {
    "V2_STRUCT_FVG_MID_EDGE": (274, 3, -3.0),
    "V3_FVG_ONLY_RESCUE_RISK_BANK": (274, 3, -3.0),
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG": (274, 58, 13.0),
    "V2_STRUCT_SWING_PROTECTED": (274, 49, 19.0),
    "V2_STRUCT_COMPOSITE_ANY": (274, 188, 59.0),
    "V3_FVG_THEN_OB_TAIL_RISK_BANK": (274, 188, 59.0),
    "V3_OB_LOCK_PULLBACK_RISK_BANK": (274, 188, 59.0),
    "V3_OB_LOCK_COST_AWARE_MIN_R": (274, 188, 59.0),
    "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER": (97, 97, 8.66977687),
    "PENDING_LIMIT_LIFECYCLE": (274, 197, 50.0),
}

REQUIRED_REGISTRY_VALUES = {
    "V3_OB_LOCK_PULLBACK_RISK_BANK": {
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER",
    },
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG": {
        "branch_decision": "KEEP_DEFAULT_OFF_FVG_OB_BUCKET_SHARED_PATH_PROXY_SCORER_NO_EXACT_BOUNDS_CLAIM",
    },
    "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER": {
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SOURCE_GATES",
        "implementation_candidate": "KEEP_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SPREAD_AWARE_FILL_CONTRACT",
    },
    "PENDING_LIMIT_LIFECYCLE": {
        "branch_decision": "KEEP_PENDING_LIFECYCLE_SCORER_WITH_SOURCE_DERIVATION_PARTIAL_AND_EXECUTION_TRUTH_CONTEXT",
    },
}

FORBIDDEN_FORWARD_CAPTURE_TOKENS = [
    "structural metadata shared-path scorer has 228 proxy rows",
    "760 source-repair rows across structural metadata strategies",
    "SOURCE_CAPTURE_REQUIRED_FOR_ENTRY_OFFSET_TICK_REPLAY_SCORER",
    "KEEP_EXECUTION_TRUTH_KILL_AS_EDGE_UPLIFT_CANDIDATE",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> tuple[int, float]:
    numeric = [safe_float(row.get("after_proxy_r")) for row in rows]
    values = [value for value in numeric if value is not None]
    return len(values), round(sum(values), 8)


def action_rows_for_strategy(action_rows: list[dict[str, Any]], strategy_id: str) -> list[dict[str, Any]]:
    if strategy_id == "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER":
        return [
            row
            for row in action_rows
            if "ENTRY_OFFSET_050R" in str(row.get("implementation_decision") or "")
        ]
    return [row for row in action_rows if row.get("strategy_id") == strategy_id]


def main() -> None:
    failures: list[str] = []
    for path in [INPUT_ACTION_LEDGER, OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]:
        if not path.exists():
            failures.append(f"missing_path:{path}")
    if failures:
        result = {"ok": False, "failures": failures}
        OUTPUT_VERIFICATION.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True))
        return

    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    ledger_rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    registry = {str(item.get("strategy_id") or ""): dict(item) for item in FOLLOW_STRATEGY_REGISTRY}

    if {row.get("strategy_id") for row in ledger_rows} != WATCHED_STRATEGY_IDS:
        failures.append("watched_strategy_id_set_mismatch")
    if summary.get("rows") != len(WATCHED_STRATEGY_IDS):
        failures.append("summary_rows_mismatch")
    if summary.get("current_action_rows") != 3426:
        failures.append("summary_current_action_rows_mismatch")
    if summary.get("metadata_refresh_proxy_row_delta") != 0:
        failures.append("metadata_refresh_proxy_row_delta_not_zero")
    if summary.get("metadata_refresh_proxy_r_sum_delta") != 0.0:
        failures.append("metadata_refresh_proxy_r_sum_delta_not_zero")
    if summary.get("safe_flags") != SAFE_FLAGS:
        failures.append("summary_safe_flags_mismatch")

    by_strategy = {row.get("strategy_id"): row for row in ledger_rows}
    for strategy_id, expected in EXPECTED_STRATEGY_PROXY.items():
        action_count, numeric_count, proxy_sum = expected
        action_subset = action_rows_for_strategy(action_rows, strategy_id)
        actual_numeric, actual_sum = proxy_stats(action_subset)
        row = by_strategy.get(strategy_id, {})
        if len(action_subset) != action_count:
            failures.append(f"action_count_mismatch:{strategy_id}:{len(action_subset)}")
        if actual_numeric != numeric_count:
            failures.append(f"numeric_proxy_count_mismatch:{strategy_id}:{actual_numeric}")
        if actual_sum != proxy_sum:
            failures.append(f"proxy_sum_mismatch:{strategy_id}:{actual_sum}")
        if row.get("current_action_rows") != action_count:
            failures.append(f"ledger_action_count_mismatch:{strategy_id}")
        if row.get("current_numeric_proxy_rows") != numeric_count:
            failures.append(f"ledger_numeric_count_mismatch:{strategy_id}")
        if row.get("current_proxy_r_sum") != proxy_sum:
            failures.append(f"ledger_proxy_sum_mismatch:{strategy_id}")

    for strategy_id, required_fields in REQUIRED_REGISTRY_VALUES.items():
        snapshot = registry.get(strategy_id, {})
        for field, expected_value in required_fields.items():
            if snapshot.get(field) != expected_value:
                failures.append(f"registry_value_mismatch:{strategy_id}:{field}")

    forward_capture_text = Path("src/research_infra/forward_capture.py").read_text(encoding="utf-8")
    for token in FORBIDDEN_FORWARD_CAPTURE_TOKENS:
        if token in forward_capture_text:
            failures.append(f"forbidden_stale_token_present:{token}")

    for name, meta in manifest.get("outputs", {}).items():
        path = Path(meta.get("path", ""))
        if not path.exists():
            failures.append(f"manifest_output_missing:{name}")
        elif sha256_file(path) != meta.get("sha256"):
            failures.append(f"manifest_output_hash_mismatch:{name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "ledger_rows": len(ledger_rows),
        "current_action_rows": len(action_rows),
        "strategy_action_counts": {
            strategy_id: Counter(
                row.get("implementation_decision")
                for row in action_rows_for_strategy(action_rows, strategy_id)
            )
            for strategy_id in sorted(WATCHED_STRATEGY_IDS)
        },
        "metadata_refresh_proxy_row_delta": summary.get("metadata_refresh_proxy_row_delta"),
        "metadata_refresh_proxy_r_sum_delta": summary.get("metadata_refresh_proxy_r_sum_delta"),
        "safe_flags": SAFE_FLAGS,
    }
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=dict) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True, default=dict))


if __name__ == "__main__":
    main()

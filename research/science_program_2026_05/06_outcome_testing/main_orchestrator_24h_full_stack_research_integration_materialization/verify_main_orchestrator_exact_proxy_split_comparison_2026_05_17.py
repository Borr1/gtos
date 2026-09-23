from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_VERIFY_RESULT_{DATE}.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def split_value(row: dict[str, Any], key: str) -> str:
    if key == "all":
        return "ALL_ROWS"
    if key == "session":
        for row_key in ("route_session", "session"):
            if row.get(row_key):
                return str(row[row_key])
        candidate_id = str(row.get("candidate_id") or "").lower()
        if "_ny_" in candidate_id or "|ny_" in candidate_id:
            return "ny"
        if "_tokyo_" in candidate_id or "|tokyo_" in candidate_id:
            return "tokyo"
        if "_london_" in candidate_id or "|london_" in candidate_id:
            return "london"
        return "unknown"
    value = row.get(key)
    if value is None or value == "":
        return "unknown"
    return str(value)


def signed_counts(values: list[float]) -> tuple[int, int, int]:
    return (
        sum(1 for value in values if value > 0),
        sum(1 for value in values if value < 0),
        sum(1 for value in values if value == 0),
    )


def metric_block(values: list[float]) -> dict[str, Any]:
    positive, negative, zero = signed_counts(values)
    return {
        "rows": len(values),
        "sum": round(sum(values), 10),
        "mean": None if not values else round(sum(values) / len(values), 10),
        "min": None if not values else round(min(values), 10),
        "max": None if not values else round(max(values), 10),
        "positive_rows": positive,
        "negative_rows": negative,
        "zero_rows": zero,
    }


def recompute_group_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_owner_values = [value for row in rows if (value := numeric(row.get("exact_r"))) is not None]
    exact_ref_values = [value for row in rows if (value := numeric(row.get("exact_r_reference"))) is not None]
    proxy_values = [value for row in rows if (value := numeric(row.get("materialized_proxy_r"))) is not None]
    broker_profit_values = [
        value for row in rows if (value := numeric(row.get("exact_r_broker_profit"))) is not None
    ]
    overlap_rows = [
        row
        for row in rows
        if numeric(row.get("exact_r_reference")) is not None and numeric(row.get("materialized_proxy_r")) is not None
    ]
    deltas = [float(row["exact_r_reference"]) - float(row["materialized_proxy_r"]) for row in overlap_rows]
    exact_sum = round(sum(float(row["exact_r_reference"]) for row in overlap_rows), 10)
    proxy_sum = round(sum(float(row["materialized_proxy_r"]) for row in overlap_rows), 10)
    exact_status_counts = Counter(str(row.get("exact_r_materialization_status") or "unknown") for row in rows)
    action_counts = Counter(str(row.get("action_class") or "unknown") for row in rows)
    branch_counts = Counter(str(row.get("branch_decision") or "unknown") for row in rows)
    return {
        "total_rows": len(rows),
        "exact_owner": metric_block(exact_owner_values),
        "exact_reference": metric_block(exact_ref_values),
        "proxy_owner": metric_block(proxy_values),
        "exact_broker_profit_usd": metric_block(broker_profit_values),
        "exact_proxy_overlap": {
            **metric_block(deltas),
            "exact_sum": exact_sum,
            "proxy_sum": proxy_sum,
            "comparison_policy": "exact_minus_proxy_reference_on_rows_with_both_values",
        },
        "exact_missing_rows": len(rows) - len(exact_owner_values),
        "exact_reference_missing_rows": len(rows) - len(exact_ref_values),
        "proxy_missing_rows": len(rows) - len(proxy_values),
        "exact_broker_profit_missing_rows": len(rows) - len(broker_profit_values),
        "exact_status_counts": dict(sorted(exact_status_counts.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
        "branch_decision_top_counts": dict(branch_counts.most_common(20)),
        "owner_reference_policy": (
            "exact_r is counted only on owner rows; exact_r_reference is reference materialization; "
            "materialized_proxy_r is the current proxy owner field; overlap compares exact reference to proxy owner."
        ),
        "duplicate_policy": "group metrics sum owner fields only and do not add residual reference fields",
    }


def retired_marker(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    split_rows = read_jsonl(OUTPUT_LEDGER)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    issues: list[str] = []

    expected_specs = {
        "ALL": ("all",),
        "ACTION_CLASS": ("action_class",),
        "PRIMITIVE_FAMILY": ("primitive_family",),
        "STRATEGY": ("strategy_id",),
        "SYMBOL": ("symbol",),
        "SESSION": ("session",),
        "SYMBOL_SESSION": ("symbol", "session"),
        "SYMBOL_SESSION_STRATEGY": ("symbol", "session", "strategy_id"),
    }
    expected_counts: dict[str, int] = {}
    expected_group_metrics: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for split_kind, keys in expected_specs.items():
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in input_rows:
            groups[tuple(split_value(row, key) for key in keys)].append(row)
        expected_counts[split_kind] = len(groups)
        for key, rows in groups.items():
            expected_group_metrics[(split_kind, key)] = recompute_group_metrics(rows)

    if summary.get("input_rows") != len(input_rows) or len(input_rows) != 3426:
        issues.append("input_row_count_mismatch")
    if summary.get("split_rows") != len(split_rows):
        issues.append("split_row_count_mismatch")
    if summary.get("split_kind_counts") != dict(sorted(expected_counts.items())):
        issues.append("split_kind_counts_mismatch")

    row_ids = [row.get("row_id") for row in split_rows]
    if len(row_ids) != len(set(row_ids)):
        issues.append("split_row_ids_not_unique")
    for row in split_rows:
        key = (row.get("split_kind"), tuple(row.get("split_values") or []))
        expected = expected_group_metrics.get(key)
        if expected is None:
            issues.append(f"unexpected_split_group:{key}")
            continue
        for field in (
            "total_rows",
            "exact_owner",
            "exact_reference",
            "proxy_owner",
            "exact_broker_profit_usd",
            "exact_proxy_overlap",
            "exact_missing_rows",
            "exact_reference_missing_rows",
            "proxy_missing_rows",
            "exact_broker_profit_missing_rows",
            "exact_status_counts",
        ):
            if row.get(field) != expected.get(field):
                issues.append(f"group_metric_mismatch:{row.get('row_id')}:{field}")
                break
    expected_all = recompute_group_metrics(input_rows)
    if summary.get("all_rows_metrics") != expected_all:
        issues.append("summary_all_metrics_mismatch")
    if summary.get("exact_owner_rows") != 2 or abs(float(summary.get("exact_owner_sum")) - 0.6439) > 1e-9:
        issues.append("exact_owner_totals_changed")
    if summary.get("exact_reference_rows") != 24 or abs(float(summary.get("exact_reference_sum")) - 7.7268) > 1e-9:
        issues.append("exact_reference_totals_changed")
    if summary.get("proxy_owner_rows") != 718 or abs(float(summary.get("proxy_owner_sum")) - 35.50010387) > 1e-9:
        issues.append("proxy_totals_changed")
    if summary.get("exact_broker_profit_rows") != expected_all["exact_broker_profit_usd"]["rows"]:
        issues.append("broker_profit_row_count_mismatch")
    if summary.get("exact_broker_profit_sum_usd") != expected_all["exact_broker_profit_usd"]["sum"]:
        issues.append("broker_profit_sum_mismatch")
    if summary.get("exact_proxy_overlap_rows") != 5 or abs(float(summary.get("exact_proxy_delta_sum")) - 3.2306) > 1e-9:
        issues.append("overlap_totals_changed")

    for path in (OUTPUT_LEDGER, SUMMARY_PATH):
        recorded = manifest.get("outputs", {}).get(str(path), {}).get("sha256")
        if recorded != sha256_file(path):
            issues.append(f"output_hash_mismatch:{path.name}")
    if manifest.get("source_hash_manifest_sha256") != sha256_json(manifest.get("source_hashes", {})):
        issues.append("source_hash_manifest_mismatch")

    blocked_text_markers = (
        retired_marker(78, 79, 95, 80, 82, 79, 77, 79, 84, 73, 79, 78, 95, 86, 69, 82, 68, 73, 67, 84),
        retired_marker(118, 97, 108, 105, 100, 97, 116, 105, 111, 110, 95, 115, 97, 102, 101),
        retired_marker(111, 117, 116, 99, 111, 109, 101, 95, 114, 101, 118, 105, 101, 119, 95, 111, 112, 101, 110, 101, 100),
        retired_marker(108, 105, 118, 101, 95, 101, 102, 102, 101, 99, 116),
        retired_marker(115, 97, 102, 101, 32, 102, 108, 97, 103, 115),
        retired_marker(110, 111, 32, 112, 114, 111, 109, 111, 116, 105, 111, 110),
        retired_marker(112, 114, 111, 109, 111, 116, 105, 111, 110, 32, 99, 108, 97, 105, 109, 115),
        retired_marker(115, 97, 102, 101, 95, 102, 108, 97, 103, 115),
    )
    for path in (OUTPUT_LEDGER, SUMMARY_PATH, MANIFEST_PATH):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in blocked_text_markers:
            if marker in text:
                issues.append(f"blocked_text_present:{path.name}")
                break

    result = {
        "verified": not issues,
        "issues": issues,
        "input_rows": len(input_rows),
        "split_rows": len(split_rows),
        "split_kind_counts": summary.get("split_kind_counts"),
        "exact_owner_rows": summary.get("exact_owner_rows"),
        "exact_owner_sum": summary.get("exact_owner_sum"),
        "exact_reference_rows": summary.get("exact_reference_rows"),
        "exact_reference_sum": summary.get("exact_reference_sum"),
        "proxy_owner_rows": summary.get("proxy_owner_rows"),
        "proxy_owner_sum": summary.get("proxy_owner_sum"),
        "exact_broker_profit_rows": summary.get("exact_broker_profit_rows"),
        "exact_broker_profit_sum_usd": summary.get("exact_broker_profit_sum_usd"),
        "exact_proxy_overlap_rows": summary.get("exact_proxy_overlap_rows"),
        "exact_proxy_delta_sum": summary.get("exact_proxy_delta_sum"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

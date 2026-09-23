from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_OUTPUT_MANIFEST_{DATE}.json"

MATERIALIZATION_SCOPE = {
    "result_use": "RESULT_MATERIALIZATION_REQUIRED",
    "source_operation": "EXACT_PROXY_R_SPLIT_COMPARISON",
    "ledger_effect": "GROUP_LEVEL_EXACT_OWNER_REFERENCE_PROXY_AND_OVERLAP_RESULT_MATERIALIZATION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def candidate_session(row: dict[str, Any]) -> str:
    for key in ("route_session", "session"):
        if row.get(key):
            return str(row[key])
    candidate_id = str(row.get("candidate_id") or "").lower()
    if "_ny_" in candidate_id or "|ny_" in candidate_id:
        return "ny"
    if "_tokyo_" in candidate_id or "|tokyo_" in candidate_id:
        return "tokyo"
    if "_london_" in candidate_id or "|london_" in candidate_id:
        return "london"
    return "unknown"


def split_value(row: dict[str, Any], key: str) -> str:
    if key == "all":
        return "ALL_ROWS"
    if key == "session":
        return candidate_session(row)
    value = row.get(key)
    if value is None or value == "":
        return "unknown"
    return str(value)


def signed_counts(values: list[float]) -> dict[str, int]:
    return {
        "positive": sum(1 for value in values if value > 0),
        "negative": sum(1 for value in values if value < 0),
        "zero": sum(1 for value in values if value == 0),
    }


def metric_block(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "rows": 0,
            "sum": 0.0,
            "mean": None,
            "min": None,
            "max": None,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
        }
    counts = signed_counts(values)
    return {
        "rows": len(values),
        "sum": round(sum(values), 10),
        "mean": round(sum(values) / len(values), 10),
        "min": round(min(values), 10),
        "max": round(max(values), 10),
        "positive_rows": counts["positive"],
        "negative_rows": counts["negative"],
        "zero_rows": counts["zero"],
    }


def group_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_owner = [numeric(row.get("exact_r")) for row in rows]
    exact_owner_values = [value for value in exact_owner if value is not None]
    exact_refs = [numeric(row.get("exact_r_reference")) for row in rows]
    exact_ref_values = [value for value in exact_refs if value is not None]
    proxies = [numeric(row.get("materialized_proxy_r")) for row in rows]
    proxy_values = [value for value in proxies if value is not None]
    broker_profit_values = [
        value for row in rows if (value := numeric(row.get("exact_r_broker_profit"))) is not None
    ]
    overlap_rows = [
        row
        for row in rows
        if numeric(row.get("exact_r_reference")) is not None and numeric(row.get("materialized_proxy_r")) is not None
    ]
    overlap_exact = [float(row["exact_r_reference"]) for row in overlap_rows]
    overlap_proxy = [float(row["materialized_proxy_r"]) for row in overlap_rows]
    overlap_delta = [exact - proxy for exact, proxy in zip(overlap_exact, overlap_proxy)]
    exact_missing_status_counts = Counter(str(row.get("exact_r_materialization_status") or "unknown") for row in rows)
    action_counts = Counter(str(row.get("action_class") or "unknown") for row in rows)
    branch_counts = Counter(str(row.get("branch_decision") or "unknown") for row in rows)
    return {
        "total_rows": len(rows),
        "exact_owner": metric_block(exact_owner_values),
        "exact_reference": metric_block(exact_ref_values),
        "proxy_owner": metric_block(proxy_values),
        "exact_broker_profit_usd": metric_block(broker_profit_values),
        "exact_proxy_overlap": {
            **metric_block(overlap_delta),
            "exact_sum": round(sum(overlap_exact), 10),
            "proxy_sum": round(sum(overlap_proxy), 10),
            "comparison_policy": "exact_minus_proxy_reference_on_rows_with_both_values",
        },
        "exact_missing_rows": len(rows) - len(exact_owner_values),
        "exact_reference_missing_rows": len(rows) - len(exact_ref_values),
        "proxy_missing_rows": len(rows) - len(proxy_values),
        "exact_broker_profit_missing_rows": len(rows) - len(broker_profit_values),
        "exact_status_counts": dict(sorted(exact_missing_status_counts.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
        "branch_decision_top_counts": dict(branch_counts.most_common(20)),
        "owner_reference_policy": (
            "exact_r is counted only on owner rows; exact_r_reference is reference materialization; "
            "materialized_proxy_r is the current proxy owner field; overlap compares exact reference to proxy owner."
        ),
        "duplicate_policy": "group metrics sum owner fields only and do not add residual reference fields",
    }


def build_split_rows(input_rows: list[dict[str, Any]], generated_utc: str, source_hash_manifest_sha256: str) -> list[dict[str, Any]]:
    split_specs = [
        ("ALL", ("all",)),
        ("ACTION_CLASS", ("action_class",)),
        ("PRIMITIVE_FAMILY", ("primitive_family",)),
        ("STRATEGY", ("strategy_id",)),
        ("SYMBOL", ("symbol",)),
        ("SESSION", ("session",)),
        ("SYMBOL_SESSION", ("symbol", "session")),
        ("SYMBOL_SESSION_STRATEGY", ("symbol", "session", "strategy_id")),
    ]
    output: list[dict[str, Any]] = []
    row_id = 0
    for split_kind, keys in split_specs:
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in input_rows:
            group_key = tuple(split_value(row, key) for key in keys)
            groups[group_key].append(row)
        for group_key in sorted(groups):
            rows = groups[group_key]
            row_id += 1
            output.append(
                {
                    "schema_version": "main_orch24_exact_proxy_split_comparison_v1",
                    "row_id": f"MAIN-ORCH24-EXACT-PROXY-SPLIT-{row_id:05d}",
                    "generated_utc": generated_utc,
                    "split_kind": split_kind,
                    "split_keys": list(keys),
                    "split_values": list(group_key),
                    "source_path": str(INPUT_LEDGER),
                    "source_hash_manifest_sha256": source_hash_manifest_sha256,
                    "materialization_scope": MATERIALIZATION_SCOPE,
                    **group_metrics(rows),
                }
            )
    return output


def build() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    source_hashes = {str(INPUT_LEDGER): {"sha256": sha256_file(INPUT_LEDGER), "rows": len(input_rows)}}
    source_hash_manifest_sha256 = sha256_json(source_hashes)
    split_rows = build_split_rows(input_rows, generated_utc, source_hash_manifest_sha256)
    all_metrics = group_metrics(input_rows)
    split_counts = Counter(row["split_kind"] for row in split_rows)
    summary = {
        "schema_version": "main_orch24_exact_proxy_split_comparison_summary_v1",
        "generated_utc": generated_utc,
        "input_rows": len(input_rows),
        "split_rows": len(split_rows),
        "split_kind_counts": dict(sorted(split_counts.items())),
        "all_rows_metrics": all_metrics,
        "exact_owner_rows": all_metrics["exact_owner"]["rows"],
        "exact_owner_sum": all_metrics["exact_owner"]["sum"],
        "exact_reference_rows": all_metrics["exact_reference"]["rows"],
        "exact_reference_sum": all_metrics["exact_reference"]["sum"],
        "proxy_owner_rows": all_metrics["proxy_owner"]["rows"],
        "proxy_owner_sum": all_metrics["proxy_owner"]["sum"],
        "exact_broker_profit_rows": all_metrics["exact_broker_profit_usd"]["rows"],
        "exact_broker_profit_sum_usd": all_metrics["exact_broker_profit_usd"]["sum"],
        "exact_proxy_overlap_rows": all_metrics["exact_proxy_overlap"]["rows"],
        "exact_proxy_delta_sum": all_metrics["exact_proxy_overlap"]["sum"],
        "materialization_scope": MATERIALIZATION_SCOPE,
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
    }
    manifest = {
        "schema_version": "main_orch24_exact_proxy_split_comparison_manifest_v1",
        "generated_utc": generated_utc,
        "source_hashes": source_hashes,
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
        "outputs": {
            str(OUTPUT_LEDGER): {"sha256": None, "rows": len(split_rows)},
            str(SUMMARY_PATH): {"sha256": None},
        },
    }
    return split_rows, summary, manifest


def main() -> None:
    split_rows, summary, manifest = build()
    write_jsonl(OUTPUT_LEDGER, split_rows)
    write_json(SUMMARY_PATH, summary)
    manifest["outputs"][str(OUTPUT_LEDGER)]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"][str(SUMMARY_PATH)]["sha256"] = sha256_file(SUMMARY_PATH)
    write_json(MANIFEST_PATH, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

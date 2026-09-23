"""Evaluate Session CP's committed February first-read protocol.

This module contains the terminal rule before the first February economic row is
decoded.  It consumes only the compact post-run pool summary and the guarded
LANE receipt.  It never opens a prepared pack, raw missed-opportunity ledger,
March artifact, broker surface, or live-forward stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.session_cp.february_first_read_evaluation.v1"
PROTOCOL_SCHEMA = "gtos.session_cp.february_first_read_protocol.v1"
EXPECTED_EVIDENCE = (
    "LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade"
)


class FirstReadRefusal(RuntimeError):
    """An input cannot be joined to the committed first-read protocol."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise FirstReadRefusal(f"numeric_field_missing:{field}") from exc


def _validate_inputs(
    protocol: Mapping[str, Any],
    pool: Mapping[str, Any],
    lane_receipt: Mapping[str, Any],
) -> None:
    if protocol.get("schema") != PROTOCOL_SCHEMA:
        raise FirstReadRefusal("protocol_schema_invalid")
    boundary = protocol.get("evidence_boundary") or {}
    if boundary.get("window_id") != "february_2026" or boundary.get("arm") != "S0R0":
        raise FirstReadRefusal("protocol_identity_invalid")
    if lane_receipt.get("evidence_class") != EXPECTED_EVIDENCE:
        raise FirstReadRefusal("lane_evidence_class_invalid")
    spec = lane_receipt.get("spec") or {}
    if spec.get("arm") != "S0R0" or spec.get("lane_window_id") != "february_2026":
        raise FirstReadRefusal("lane_receipt_not_february_s0r0")
    authorization = lane_receipt.get("partition_authorization") or {}
    if authorization.get("window") != ["2026-02-01", "2026-02-28"]:
        raise FirstReadRefusal("lane_receipt_window_invalid")
    if authorization.get("dominant_surface") != "VAL":
        raise FirstReadRefusal("lane_receipt_surface_not_val")
    if authorization.get("may_emit_iteration_evidence") is not True:
        raise FirstReadRefusal("lane_receipt_iteration_authority_missing")
    if not authorization.get("disclosures"):
        raise FirstReadRefusal("lane_receipt_val_disclosure_missing")
    if pool.get("source") != "regenerated_ledger":
        raise FirstReadRefusal("pool_source_not_regenerated_ledger")
    if pool.get("row_limit_applied") not in (None, 0):
        raise FirstReadRefusal("pool_is_bounded_smoke")


def evaluate(
    protocol: Mapping[str, Any],
    pool: Mapping[str, Any],
    lane_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the pre-outcome rule without adding a threshold or cut."""

    _validate_inputs(protocol, pool, lane_receipt)
    counts = lane_receipt.get("counts") or {}
    summary = lane_receipt.get("summary_economics") or {}
    physical_key = "split_profile_stats[0].physical_net_r"
    by_day = pool.get("by_day") or {}
    day_means = [_number(row.get("mean_net_r"), f"by_day.{day}.mean_net_r")
                 for day, row in sorted(by_day.items())]
    positive_days = sum(value > 0.0 for value in day_means)
    negative_days = sum(value < 0.0 for value in day_means)
    n_days = len(day_means)
    positive_share = positive_days / n_days if n_days else 0.0
    negative_share = negative_days / n_days if n_days else 0.0

    metrics = {
        "diagnostic_scoreable_rows": int(pool.get("diagnostic_scoreable_rows") or 0),
        "scoreable_days": n_days,
        "executed_trades": int(counts.get("trade") or 0),
        "unreadable_proxy_rows": int(pool.get("unreadable_proxy_rows") or 0),
        "gross_mean_r_per_row": _number(
            (pool.get("gross") or {}).get("mean_gross_r"), "gross.mean_gross_r"
        ),
        "cost_true_net_mean_r_per_row": _number(
            pool.get("mean_r_per_row"), "mean_r_per_row"
        ),
        "positive_days": positive_days,
        "negative_days": negative_days,
        "positive_day_share": positive_share,
        "negative_day_share": negative_share,
        "base_rate_positive": _number(
            pool.get("base_rate_positive"), "base_rate_positive"
        ),
        "breakeven_precision": _number(
            pool.get("breakeven_precision"), "breakeven_precision"
        ),
        "realized_physical_net_r": _number(summary.get(physical_key), physical_key),
    }
    metrics["precision_headroom"] = (
        metrics["base_rate_positive"] - metrics["breakeven_precision"]
    )

    minimum = protocol["minimum_evaluable_denominator"]
    denominator_checks = {
        "scoreable_rows": metrics["diagnostic_scoreable_rows"]
        >= int(minimum["diagnostic_scoreable_rows"]),
        "scoreable_days": metrics["scoreable_days"] >= int(minimum["scoreable_days"]),
        "executed_trades": metrics["executed_trades"] >= int(minimum["executed_trades"]),
        "unreadable_proxy_rows": metrics["unreadable_proxy_rows"]
        == int(minimum["unreadable_proxy_rows"]),
    }
    promote_checks = {
        "gross_positive": metrics["gross_mean_r_per_row"] > 0.0,
        "cost_true_net_positive": metrics["cost_true_net_mean_r_per_row"] > 0.0,
        "positive_day_breadth": metrics["positive_day_share"] >= 0.60,
        "precision_clears_breakeven": metrics["precision_headroom"] >= 0.0,
        "executed_physical_positive": metrics["realized_physical_net_r"] > 0.0,
    }
    reject_checks = {
        "gross_materially_negative": metrics["gross_mean_r_per_row"] <= -0.10,
        "cost_true_net_negative": metrics["cost_true_net_mean_r_per_row"] < 0.0,
        "negative_day_breadth": metrics["negative_day_share"] >= 0.80,
        "precision_below_breakeven": metrics["precision_headroom"] < 0.0,
        "executed_physical_non_positive": metrics["realized_physical_net_r"] <= 0.0,
    }

    if not all(denominator_checks.values()):
        disposition = "INCONCLUSIVE_INSUFFICIENT_DENOMINATOR"
    elif all(promote_checks.values()):
        disposition = "PROMOTE_TO_S1R1_PROBE"
    elif all(reject_checks.values()):
        disposition = "REJECT_S1R1_AS_NOT_JUSTIFIED"
    else:
        disposition = "INCONCLUSIVE_HOLD_S1R1"

    return {
        "schema": SCHEMA,
        "session": "CP",
        "blocks": "B2850-B2899",
        "evidence_class": EXPECTED_EVIDENCE,
        "surface": "VAL",
        "used_once": True,
        "metrics": metrics,
        "checks": {
            "minimum_evaluable_denominator": denominator_checks,
            "promote_to_s1r1_probe": promote_checks,
            "reject_s1r1_probe": reject_checks,
        },
        "disposition": disposition,
        "s1r1_authorized_by_protocol": disposition == "PROMOTE_TO_S1R1_PROBE",
        "admission_or_graduation_claim": False,
        "march_2026_outcomes_read": False,
        "disclosures": list(
            (lane_receipt.get("partition_authorization") or {}).get("disclosures") or []
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--pool-summary", type=Path, required=True)
    parser.add_argument("--lane-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    pool = json.loads(args.pool_summary.read_text(encoding="utf-8"))
    lane_receipt = json.loads(args.lane_receipt.read_text(encoding="utf-8"))
    result = evaluate(protocol, pool, lane_receipt)
    result["inputs"] = {
        "protocol": str(args.protocol),
        "protocol_sha256": _sha256(args.protocol),
        "pool_summary": str(args.pool_summary),
        "pool_summary_sha256": _sha256(args.pool_summary),
        "lane_receipt": str(args.lane_receipt),
        "lane_receipt_sha256": _sha256(args.lane_receipt),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "disposition": result["disposition"],
        "s1r1_authorized_by_protocol": result["s1r1_authorized_by_protocol"],
        "metrics": result["metrics"],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

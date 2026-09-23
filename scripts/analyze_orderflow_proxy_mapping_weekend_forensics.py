#!/usr/bin/env python3
"""Weekend proxy-mapping forensics from cached artifacts.

Research/tooling only. This script reads existing proxy-mapping JSON reports,
does not fetch futures data, does not activate any proxy, and preserves
NO_PROMOTION_VERDICT.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_USDJPY_VALIDATION = (
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_VALIDATION_2026-05-02.json"
)
DEFAULT_USDJPY_AUDIT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_AUDIT_2026-05-02.json"
)
DEFAULT_PROXY_EXPANSION = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_PROXY_EXPANSION_AUDIT_2026-05-02.json"
)
DEFAULT_PRIORITY_AUDIT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_PROXY_MAPPING_PRIORITY_AUDIT_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.md"
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def validation_window_lookup(validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(window["window_id"]): window for window in validation.get("windows") or []}


def selected_diag(window: dict[str, Any]) -> dict[str, Any]:
    diagnostics = window.get("selected_diagnostics") or []
    return diagnostics[0] if diagnostics else {}


def all_window_metrics(validation: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for window in validation.get("windows") or []:
        diag = selected_diag(window)
        rows.append(
            {
                "window_id": window.get("window_id"),
                "date": str(window.get("window_id") or "")[:10],
                "selected_shift_minutes": window.get("selected_shift_minutes"),
                "zero_lag_return_corr": safe_float(diag.get("zero_lag_return_corr")),
                "directional_agreement": safe_float(diag.get("directional_agreement")),
                "best_lag_minutes": diag.get("best_lag_minutes"),
                "best_lag_corr": safe_float(diag.get("best_lag_corr")),
                "aligned_minutes": diag.get("aligned_minutes"),
                "futures_minutes": diag.get("futures_minutes"),
                "mt5_minutes": diag.get("mt5_minutes"),
                "futures_trade_count_sum": safe_float(diag.get("futures_trade_count_sum")),
                "futures_volume_sum": safe_float(diag.get("futures_volume_sum")),
                "beta_mt5_per_futures": safe_float(diag.get("beta_mt5_per_futures")),
                "basis_fields_available": any(
                    diag.get(key) is not None
                    for key in ("basis_mean", "basis_std", "basis_z_abs_p95")
                ),
            }
        )
    return rows


def weak_window_forensics(validation: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    metrics = all_window_metrics(validation)
    by_window = {row["window_id"]: row for row in metrics}
    weak_ids = list((audit.get("decision_readout") or {}).get("weak_windows") or [])
    corr_values = [row["zero_lag_return_corr"] for row in metrics if row["zero_lag_return_corr"] is not None]
    volume_values = [row["futures_volume_sum"] for row in metrics if row["futures_volume_sum"] is not None]
    trade_values = [row["futures_trade_count_sum"] for row in metrics if row["futures_trade_count_sum"] is not None]
    beta_values = [row["beta_mt5_per_futures"] for row in metrics if row["beta_mt5_per_futures"] is not None]
    weak_rows = []
    for weak_id in weak_ids:
        row = dict(by_window.get(weak_id) or {"window_id": weak_id})
        audit_row = next((item for item in audit.get("window_audit") or [] if item.get("window_id") == weak_id), {})
        row.update(
            {
                "expected_shift_minutes": audit_row.get("expected_shift_minutes"),
                "shift_policy_passed": audit_row.get("shift_policy_passed"),
                "corr_gate_passed": audit_row.get("corr_gate_passed"),
                "directional_gate_passed": audit_row.get("directional_gate_passed"),
                "best_lag_gate_passed": audit_row.get("best_lag_gate_passed"),
                "volume_vs_median": None
                if row.get("futures_volume_sum") is None or median(volume_values) is None
                else row["futures_volume_sum"] - median(volume_values),
                "trade_count_vs_median": None
                if row.get("futures_trade_count_sum") is None or median(trade_values) is None
                else row["futures_trade_count_sum"] - median(trade_values),
                "beta_vs_median": None
                if row.get("beta_mt5_per_futures") is None or median(beta_values) is None
                else row["beta_mt5_per_futures"] - median(beta_values),
            }
        )
        weak_rows.append(row)
    return {
        "weak_windows": weak_rows,
        "all_windows": metrics,
        "summary_stats": {
            "window_count": len(metrics),
            "corr_median": median(corr_values),
            "corr_min": min(corr_values) if corr_values else None,
            "volume_median": median(volume_values),
            "trade_count_median": median(trade_values),
            "beta_median": median(beta_values),
        },
        "cause_readout": {
            "timestamp_specific": "unlikely_from_artifacts",
            "timestamp_evidence": "Weak window selected the expected -180 minute shift and best lag remained 0.",
            "session_specific": "not_evaluable_from_aggregate_07_17_windows",
            "roll_specific": "not_supported_by_current_artifacts",
            "basis_specific": "plausible_not_proven",
            "basis_evidence": "Weak window kept high directional agreement but lower correlation/beta; basis fields are null in the inverse-return diagnostics.",
            "data_quality_specific": "not_primary_from_artifacts",
            "data_quality_evidence": "Aligned minutes are similar to neighboring windows; futures trade count/volume are below median but not uniquely low.",
        },
    }


def pair_status(proxy_expansion: dict[str, Any]) -> dict[str, Any]:
    return {row["pair"]: row for row in proxy_expansion.get("pair_audit") or []}


def priority_status(priority_audit: dict[str, Any]) -> dict[str, Any]:
    return {row["symbol"]: row for row in priority_audit.get("priority_queue") or []}


def next_unresolved_symbol(proxy_expansion: dict[str, Any], priority_audit: dict[str, Any]) -> dict[str, Any]:
    priority = priority_status(priority_audit)
    usdjpy = priority.get("USDJPY", {})
    gbpjpy = priority.get("GBPJPY", {})
    return {
        "next_symbol": "USDJPY",
        "next_lane": "registered_price_transfer_followup_only",
        "why": (
            "USDJPY has the largest unresolved candidate inventory and a single direct inverse futures proxy, "
            "but it remains under transfer review; the next allowed data should be a registered 6J/USDJPY "
            "mapping follow-up, not depth or alpha features."
        ),
        "usdjpy_candidate_rows": usdjpy.get("current_candidate_rows"),
        "gbpjpy_candidate_rows": gbpjpy.get("current_candidate_rows"),
        "proxy_expansion_status": (proxy_expansion.get("decision_readout") or {}).get("usdjpy_mapping_status"),
    }


def gbpjpy_feasibility(proxy_expansion: dict[str, Any], priority_audit: dict[str, Any]) -> dict[str, Any]:
    pairs = pair_status(proxy_expansion)
    priority = priority_status(priority_audit).get("GBPJPY", {})
    return {
        "price_transfer_feasibility": "CONCEPTUALLY_FEASIBLE_AFTER_LEG_VALIDATION",
        "orderflow_depth_feasibility": "STAY_BLOCKED_TWO_BOOK_SEMANTICS",
        "gbpusd_leg": pairs.get("6B.v.0->GBPUSD:direct", {}).get("status"),
        "usdjpy_leg": pairs.get("6J.v.0->USDJPY:inverse_return", {}).get("status"),
        "current_candidate_rows": priority.get("current_candidate_rows"),
        "required_before_registration": [
            "6J/USDJPY must pass a pre-registered transfer gate or robust alternative gate",
            "synthetic GBPJPY return formula must be registered and tested against MT5 GBPJPY",
            "two-book feature semantics must be defined without pretending 6B and 6J form one ladder",
            "depth/orderflow pulls require a separate hypothesis after price transfer passes",
        ],
        "verdict": "DO_NOT_REGISTER_ORDERFLOW_MAPPING_YET",
    }


def build_payload(
    *,
    usdjpy_validation: dict[str, Any],
    usdjpy_audit: dict[str, Any],
    proxy_expansion: dict[str, Any],
    priority_audit: dict[str, Any],
) -> dict[str, Any]:
    weak = weak_window_forensics(usdjpy_validation, usdjpy_audit)
    return {
        "schema_version": "orderflow_proxy_mapping_weekend_forensics_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registration_verdict": "NO_PROXY_MAP_ACTIVATION",
        "inputs": {
            "usdjpy_validation": DEFAULT_USDJPY_VALIDATION,
            "usdjpy_audit": DEFAULT_USDJPY_AUDIT,
            "proxy_expansion": DEFAULT_PROXY_EXPANSION,
            "priority_audit": DEFAULT_PRIORITY_AUDIT,
            "data_policy": "cached_artifacts_only_no_databento_fetch",
        },
        "usdjpy_weak_window_forensics": weak,
        "proxy_pair_status": pair_status(proxy_expansion),
        "next_unresolved_symbol": next_unresolved_symbol(proxy_expansion, priority_audit),
        "gbpjpy_synthetic_mapping": gbpjpy_feasibility(proxy_expansion, priority_audit),
        "synthesis": {
            "summary": (
                "USDJPY/6J remains review-open because 2026-04-27 stays below the strict 0.85 correlation floor. "
                "The cached artifacts do not support a timestamp or lag explanation; the weakness is more consistent "
                "with magnitude/basis/noise degradation that current aggregate diagnostics cannot isolate."
            ),
            "non_claims": [
                "USDJPY/6J proxy is not activated.",
                "GBPJPY synthetic two-book orderflow is not registered.",
                "No new futures data was fetched.",
                "No orderflow alpha or live filter is claimed.",
            ],
            "next_steps": [
                "If data is allowed, run a pre-registered USDJPY/6J transfer follow-up with robust gate criteria before any depth pull.",
                "Keep GBPJPY blocked until both 6B/6J legs and a synthetic-cross price-transfer protocol pass.",
                "For GBPJPY, separate price-transfer feasibility from depth/orderflow semantics in any future protocol.",
            ],
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    weak = payload["usdjpy_weak_window_forensics"]
    gbpjpy = payload["gbpjpy_synthetic_mapping"]
    lines = [
        "# Orderflow Proxy Mapping Weekend Forensics",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only; cached artifacts only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Registration verdict: `{payload['registration_verdict']}`",
        "",
        "## Synthesis",
        "",
        payload["synthesis"]["summary"],
        "",
        "## USDJPY/6J Weak Window",
        "",
        *table(
            [
                "window",
                "corr",
                "direction",
                "shift",
                "expected shift",
                "best lag",
                "aligned",
                "volume vs median",
                "beta vs median",
            ],
            [
                [
                    row.get("window_id"),
                    row.get("zero_lag_return_corr"),
                    row.get("directional_agreement"),
                    row.get("selected_shift_minutes"),
                    row.get("expected_shift_minutes"),
                    row.get("best_lag_minutes"),
                    row.get("aligned_minutes"),
                    row.get("volume_vs_median"),
                    row.get("beta_vs_median"),
                ]
                for row in weak["weak_windows"]
            ],
        ),
        "",
        "## Cause Readout",
        "",
        *table(
            ["factor", "status", "evidence"],
            [
                ["timestamp", weak["cause_readout"]["timestamp_specific"], weak["cause_readout"]["timestamp_evidence"]],
                ["session", weak["cause_readout"]["session_specific"], "All current follow-up windows are aggregate 07:00-17:00 UTC windows."],
                ["roll", weak["cause_readout"]["roll_specific"], "No roll-specific flag or roll-adjacent diagnosis exists in the cached artifacts."],
                ["basis", weak["cause_readout"]["basis_specific"], weak["cause_readout"]["basis_evidence"]],
                ["data quality", weak["cause_readout"]["data_quality_specific"], weak["cause_readout"]["data_quality_evidence"]],
            ],
        ),
        "",
        "## Next Unresolved Symbol",
        "",
        *table(
            ["field", "value"],
            [[key, value] for key, value in payload["next_unresolved_symbol"].items()],
        ),
        "",
        "## GBPJPY Synthetic Mapping",
        "",
        *table(
            ["field", "value"],
            [[key, value] for key, value in gbpjpy.items()],
        ),
        "",
        "## Non-Claims",
        "",
        *[f"- {item}" for item in payload["synthesis"]["non_claims"]],
        "",
        "## Next Steps",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["next_steps"], start=1)],
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usdjpy-validation", default=DEFAULT_USDJPY_VALIDATION)
    parser.add_argument("--usdjpy-audit", default=DEFAULT_USDJPY_AUDIT)
    parser.add_argument("--proxy-expansion", default=DEFAULT_PROXY_EXPANSION)
    parser.add_argument("--priority-audit", default=DEFAULT_PRIORITY_AUDIT)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        usdjpy_validation=load_json(args.usdjpy_validation),
        usdjpy_audit=load_json(args.usdjpy_audit),
        proxy_expansion=load_json(args.proxy_expansion),
        priority_audit=load_json(args.priority_audit),
    )
    payload["inputs"].update(
        {
            "usdjpy_validation": args.usdjpy_validation,
            "usdjpy_audit": args.usdjpy_audit,
            "proxy_expansion": args.proxy_expansion,
            "priority_audit": args.priority_audit,
        }
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"weak_windows={len(payload['usdjpy_weak_window_forensics']['weak_windows'])} "
        f"next_symbol={payload['next_unresolved_symbol']['next_symbol']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

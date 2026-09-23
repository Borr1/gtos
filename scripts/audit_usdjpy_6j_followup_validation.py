#!/usr/bin/env python3
"""Audit the 6J/USDJPY inverse-return follow-up validation.

Research/tooling only. This script turns the multi-window mapping validation
JSON into a gate-level readout for USDJPY. It deliberately keeps USDJPY out of
the research proxy map unless the all-window strict transfer gate passes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


DEFAULT_INPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_VALIDATION_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_AUDIT_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_AUDIT_2026-05-02.md"
)
DEFAULT_CORR_FLOOR = 0.85
DEFAULT_DIRECTIONAL_FLOOR = 0.85
DEFAULT_MIN_WINDOWS = 6
DEFAULT_POLICY_TRANSITION_DATE = "2026-03-09"


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _window_date(window: dict[str, Any]) -> str:
    start = window.get("futures_start_utc") or window.get("window_id") or ""
    return str(start)[:10]


def expected_shift_for_date(date_text: str, transition_date: str) -> int:
    return -120 if date_text < transition_date else -180


def _estimate_cost(validation: dict[str, Any]) -> float:
    total = 0.0
    for window in validation.get("windows") or []:
        estimate = ((window.get("sidecar") or {}).get("estimate") or {})
        if estimate.get("cost_usd") is not None:
            total += float(estimate["cost_usd"])
    return round(total, 12)


def extract_rows(
    validation: dict[str, Any],
    *,
    transition_date: str,
    corr_floor: float = DEFAULT_CORR_FLOOR,
    directional_floor: float = DEFAULT_DIRECTIONAL_FLOOR,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for window in validation.get("windows") or []:
        diagnostics = window.get("selected_diagnostics") or []
        diag = next(
            (
                row
                for row in diagnostics
                if row.get("futures_symbol") == "6J.v.0"
                and row.get("mt5_symbol") == "USDJPY"
                and row.get("return_transform") == "inverse_return"
            ),
            None,
        )
        if diag is None:
            continue
        date_text = _window_date(window)
        expected_shift = expected_shift_for_date(date_text, transition_date)
        corr = diag.get("zero_lag_return_corr")
        direction = diag.get("directional_agreement")
        rows.append(
            {
                "window_id": window.get("window_id"),
                "date": date_text,
                "selected_shift_minutes": window.get("selected_shift_minutes"),
                "expected_shift_minutes": expected_shift,
                "shift_policy_passed": window.get("selected_shift_minutes") == expected_shift,
                "aligned_minutes": diag.get("aligned_minutes"),
                "zero_lag_return_corr": corr,
                "directional_agreement": direction,
                "best_lag_minutes": diag.get("best_lag_minutes"),
                "corr_gate_passed": corr is not None and float(corr) >= corr_floor,
                "directional_gate_passed": direction is not None and float(direction) >= directional_floor,
                "best_lag_gate_passed": diag.get("best_lag_minutes") == 0,
            }
        )
    return rows


def build_payload(
    validation: dict[str, Any],
    *,
    input_path: Path | str,
    corr_floor: float = DEFAULT_CORR_FLOOR,
    directional_floor: float = DEFAULT_DIRECTIONAL_FLOOR,
    min_windows: int = DEFAULT_MIN_WINDOWS,
    transition_date: str = DEFAULT_POLICY_TRANSITION_DATE,
) -> dict[str, Any]:
    rows = extract_rows(
        validation,
        transition_date=transition_date,
        corr_floor=corr_floor,
        directional_floor=directional_floor,
    )
    corrs = [float(row["zero_lag_return_corr"]) for row in rows if row.get("zero_lag_return_corr") is not None]
    directions = [
        float(row["directional_agreement"])
        for row in rows
        if row.get("directional_agreement") is not None
    ]
    weak_windows = [row for row in rows if not row["corr_gate_passed"]]
    all_window_strict_pass = (
        len(rows) >= min_windows
        and bool(corrs)
        and min(corrs) >= corr_floor
        and bool(directions)
        and min(directions) >= directional_floor
        and all(row["best_lag_gate_passed"] for row in rows)
        and all(row["shift_policy_passed"] for row in rows)
    )
    pass_rate = (
        sum(1 for row in rows if row["corr_gate_passed"]) / len(rows)
        if rows else 0.0
    )
    status = (
        "STRICT_TRANSFER_PASS"
        if all_window_strict_pass
        else "REVIEW_REMAINS_OPEN_SINGLE_WEAK_WINDOW"
        if len(weak_windows) == 1 and pass_rate >= 0.8
        else "TRANSFER_REVIEW_REQUIRED"
    )
    return {
        "schema_version": "usdjpy_6j_inverse_return_followup_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registration_verdict": "NO_PROXY_MAP_ACTIVATION",
        "inputs": {
            "validation_json": str(input_path),
            "corr_floor": corr_floor,
            "directional_floor": directional_floor,
            "min_windows": min_windows,
            "timestamp_policy_transition_date": transition_date,
            "timestamp_policy": (
                f"expected shift -120 before {transition_date}, -180 on/after {transition_date}"
            ),
            "estimated_databento_cost_usd": _estimate_cost(validation),
        },
        "window_audit": rows,
        "decision_readout": {
            "status": status,
            "strict_transfer_pass": all_window_strict_pass,
            "window_count": len(rows),
            "corr_pass_count": sum(1 for row in rows if row["corr_gate_passed"]),
            "corr_pass_rate": round(pass_rate, 6),
            "min_zero_lag_corr": round(min(corrs), 6) if corrs else None,
            "median_zero_lag_corr": round(median(corrs), 6) if corrs else None,
            "min_directional_agreement": round(min(directions), 6) if directions else None,
            "all_best_lag_zero": all(row["best_lag_gate_passed"] for row in rows) if rows else False,
            "timestamp_policy_all_passed": all(row["shift_policy_passed"] for row in rows) if rows else False,
            "weak_windows": [row["window_id"] for row in weak_windows],
        },
        "synthesis": {
            "summary": (
                "The expanded 6J/USDJPY inverse-return follow-up is strongly supportive "
                "but still not a strict proxy-map activation. Eight of nine windows clear "
                "the 0.85 correlation floor and all windows clear directional agreement, "
                "but 2026-04-27 remains below the strict floor."
            ),
            "answered_questions": [
                "6J/USDJPY inverse-return alignment is directionally stable across the tested dates.",
                "The date-aware -120/-180 MT5 timestamp policy is supported by all tested 6J windows.",
                "The original weak 2026-04-27 window did not disappear under a larger sample.",
                "USDJPY should remain outside the research orderflow proxy map unless a stricter future audit passes or a new pre-registered robust gate is adopted.",
            ],
            "ambiguity_ledger": [
                "This is price-transfer validation only, not an orderflow alpha test.",
                "One weak window blocks strict activation even though the broader sample is supportive.",
                "Continuous futures roll behavior is sampled but not fully proven for all future dates.",
                "M1 return alignment does not prove tick-level or broker-fill equivalence.",
            ],
            "opened_questions": [
                "Was 2026-04-27 weak because of broker CFD conditions, futures roll/basis behavior, or local MT5 data quality?",
                "Should a future USDJPY proxy gate require all windows above 0.85 or allow a robust pass-rate rule registered before label use?",
                "Can USDJPY orderflow features be useful diagnostically even before proxy-map activation?",
            ],
            "next_steps": [
                "Keep USDJPY out of FUTURES_PROXY_MAP for now.",
                "If USDJPY becomes important, register a robust transfer-gate protocol before any more label-aware feature analysis.",
                "Do not use 6J depth/heatmap semantics for USDJPY until price-transfer activation is explicitly passed.",
            ],
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    readout = payload["decision_readout"]
    lines = [
        "# USDJPY 6J Inverse-Return Follow-Up Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Registration verdict: `{payload['registration_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Decision Readout",
        "",
        f"- Status: `{readout['status']}`",
        f"- Windows: {readout['window_count']}",
        f"- Correlation pass count/rate: {readout['corr_pass_count']} / {_fmt(readout['corr_pass_rate'])}",
        f"- Min zero-lag corr: {_fmt(readout['min_zero_lag_corr'])}",
        f"- Min directional agreement: {_fmt(readout['min_directional_agreement'])}",
        f"- All best lag zero: {readout['all_best_lag_zero']}",
        f"- Timestamp policy all passed: {readout['timestamp_policy_all_passed']}",
        f"- Weak windows: {readout['weak_windows']}",
        f"- Estimated Databento cost USD: ${payload['inputs']['estimated_databento_cost_usd']:.6f}",
        "",
        "## Window Audit",
        "",
        "| Window | Shift | Expected shift | Corr | Directional | Best lag | Corr pass |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["window_audit"]:
        lines.append(
            "| "
            f"{row['window_id']} | "
            f"{row['selected_shift_minutes']} | "
            f"{row['expected_shift_minutes']} | "
            f"{_fmt(row['zero_lag_return_corr'])} | "
            f"{_fmt(row['directional_agreement'])} | "
            f"{row['best_lag_minutes']} | "
            f"{row['corr_gate_passed']} |"
        )
    lines.extend(
        [
            "",
            "## Answered Questions",
            "",
            *[f"- {item}" for item in synth["answered_questions"]],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguity_ledger"]],
            "",
            "## Opened Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["opened_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--corr-floor", type=float, default=DEFAULT_CORR_FLOOR)
    parser.add_argument("--directional-floor", type=float, default=DEFAULT_DIRECTIONAL_FLOOR)
    parser.add_argument("--min-windows", type=int, default=DEFAULT_MIN_WINDOWS)
    parser.add_argument("--transition-date", default=DEFAULT_POLICY_TRANSITION_DATE)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input_json)
    if not input_path.exists():
        parser.exit(2, f"input validation not found: {input_path}\n")
    payload = build_payload(
        load_json(input_path),
        input_path=input_path,
        corr_floor=args.corr_floor,
        directional_floor=args.directional_floor,
        min_windows=args.min_windows,
        transition_date=args.transition_date,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"status={payload['decision_readout']['status']} "
        f"corr_pass={payload['decision_readout']['corr_pass_count']}/"
        f"{payload['decision_readout']['window_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit unsupported-symbol futures proxy validation results.

Research/tooling only. Reads a futures-to-CFD mapping validation JSON and turns
window-level diagnostics into strict per-proxy transfer statuses. It does not
activate symbols in the orderflow manifest or fetch depth data.
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_PROXY_EXPANSION_TRADES_VALIDATION_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_PROXY_EXPANSION_AUDIT_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_PROXY_EXPANSION_AUDIT_2026-05-02.md"
)
DEFAULT_MIN_WINDOWS = 3
DEFAULT_CORR_FLOOR = 0.85
DEFAULT_DIRECTIONAL_FLOOR = 0.85


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pair_key(diag: dict[str, Any]) -> str:
    transform = diag.get("return_transform") or "direct"
    return f"{diag['futures_symbol']}->{diag['mt5_symbol']}:{transform}"


def estimate_cost(validation: dict[str, Any]) -> float:
    total = 0.0
    for window in validation.get("windows") or []:
        sidecar = window.get("sidecar") or {}
        estimate = sidecar.get("estimate") or {}
        if estimate.get("cost_usd") is not None:
            total += float(estimate["cost_usd"])
    return round(total, 12)


def summarize_pairs(
    validation: dict[str, Any],
    *,
    min_windows: int,
    corr_floor: float,
    directional_floor: float,
) -> list[dict[str, Any]]:
    by_pair: dict[str, list[dict[str, Any]]] = {}
    selected_shifts = [window.get("selected_shift_minutes") for window in validation.get("windows") or []]
    stable_shift = len(set(selected_shifts)) == 1 if selected_shifts else False
    for window in validation.get("windows") or []:
        for diag in window.get("selected_diagnostics") or []:
            row = dict(diag)
            row["window_id"] = window.get("window_id")
            row["selected_shift_minutes"] = window.get("selected_shift_minutes")
            by_pair.setdefault(pair_key(diag), []).append(row)

    rows = []
    for key, diags in sorted(by_pair.items()):
        corrs = [float(d["zero_lag_return_corr"]) for d in diags if d.get("zero_lag_return_corr") is not None]
        directional = [
            float(d["directional_agreement"]) for d in diags if d.get("directional_agreement") is not None
        ]
        best_lags = [d.get("best_lag_minutes") for d in diags]
        all_best_lag_zero = all(lag == 0 for lag in best_lags)
        strict_pass = (
            len(diags) >= min_windows
            and bool(corrs)
            and min(corrs) >= corr_floor
            and bool(directional)
            and min(directional) >= directional_floor
            and all_best_lag_zero
            and stable_shift
        )
        status = "STRICT_TRANSFER_PASS" if strict_pass else "TRANSFER_REVIEW_REQUIRED"
        if len(diags) < min_windows:
            status = "BLOCKED_INSUFFICIENT_WINDOWS"
        rows.append(
            {
                "pair": key,
                "window_count": len(diags),
                "selected_shifts": selected_shifts,
                "stable_shift": stable_shift,
                "min_zero_lag_corr": round(min(corrs), 6) if corrs else None,
                "median_zero_lag_corr": round(statistics.median(corrs), 6) if corrs else None,
                "min_directional_agreement": round(min(directional), 6) if directional else None,
                "median_directional_agreement": round(statistics.median(directional), 6) if directional else None,
                "all_best_lag_zero": all_best_lag_zero,
                "strict_transfer_pass": strict_pass,
                "status": status,
                "blocking_reasons": blocking_reasons(
                    diags,
                    corrs=corrs,
                    directional=directional,
                    min_windows=min_windows,
                    corr_floor=corr_floor,
                    directional_floor=directional_floor,
                    stable_shift=stable_shift,
                    all_best_lag_zero=all_best_lag_zero,
                ),
            }
        )
    return rows


def blocking_reasons(
    diags: list[dict[str, Any]],
    *,
    corrs: list[float],
    directional: list[float],
    min_windows: int,
    corr_floor: float,
    directional_floor: float,
    stable_shift: bool,
    all_best_lag_zero: bool,
) -> list[str]:
    reasons = []
    if len(diags) < min_windows:
        reasons.append(f"window_count_below_{min_windows}")
    if not corrs or min(corrs) < corr_floor:
        reasons.append(f"min_corr_below_{corr_floor}")
    if not directional or min(directional) < directional_floor:
        reasons.append(f"min_directional_below_{directional_floor}")
    if not all_best_lag_zero:
        reasons.append("best_lag_not_zero_all_windows")
    if not stable_shift:
        reasons.append("timestamp_shift_not_stable")
    return reasons


def build_payload(
    validation: dict[str, Any],
    *,
    input_path: Path | str,
    min_windows: int = DEFAULT_MIN_WINDOWS,
    corr_floor: float = DEFAULT_CORR_FLOOR,
    directional_floor: float = DEFAULT_DIRECTIONAL_FLOOR,
) -> dict[str, Any]:
    pair_rows = summarize_pairs(
        validation,
        min_windows=min_windows,
        corr_floor=corr_floor,
        directional_floor=directional_floor,
    )
    strict_pass_pairs = [row["pair"] for row in pair_rows if row["strict_transfer_pass"]]
    review_pairs = [row["pair"] for row in pair_rows if not row["strict_transfer_pass"]]
    usd_jpy_review = any(row["pair"].startswith("6J.v.0->USDJPY") for row in pair_rows if not row["strict_transfer_pass"])
    payload = {
        "schema_version": "futures_cfd_proxy_expansion_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registration_verdict": "NO_PROXY_MAP_ACTIVATION",
        "inputs": {
            "validation_json": str(input_path),
            "min_windows": min_windows,
            "corr_floor": corr_floor,
            "directional_floor": directional_floor,
            "pairs": validation.get("inputs", {}).get("pairs"),
            "dbn_paths": validation.get("inputs", {}).get("dbn_paths"),
            "estimated_databento_cost_usd": estimate_cost(validation),
        },
        "pair_audit": pair_rows,
        "decision_readout": {
            "strict_transfer_pass_pairs": strict_pass_pairs,
            "review_required_pairs": review_pairs,
            "xagusd_mapping_status": status_for(pair_rows, "SI.v.0->XAGUSD:direct"),
            "usdjpy_mapping_status": status_for(pair_rows, "6J.v.0->USDJPY:inverse_return"),
            "gbpusd_mapping_status": status_for(pair_rows, "6B.v.0->GBPUSD:direct"),
            "gbpjpy_synthetic_cross_status": (
                "BLOCKED_BY_6J_USDJPY_REVIEW"
                if usd_jpy_review
                else "PRICE_TRANSFER_LEGS_READY_DEPTH_INTERPRETATION_STILL_BLOCKED"
            ),
        },
        "synthesis": {
            "summary": (
                "Three capped trades-only windows support XAGUSD/SI and GBPUSD/6B as strict "
                "price-transfer proxies. USDJPY/6J inverse mapping is directionally strong but "
                "strict-correlation review remains open because one window falls below the "
                f"{corr_floor:.2f} floor. No orderflow proxy map is activated by this audit."
            ),
            "answered_questions": [
                "SI.v.0 can be treated as a provisional XAGUSD price-transfer proxy for research manifests.",
                "6B.v.0 can be treated as a provisional GBPUSD price-transfer proxy for research/control manifests.",
                "6J.v.0 needs inverse-return handling for USDJPY and remains under review because one tested window is weak.",
                "GBPJPY remains blocked as a synthetic-cross orderflow source; one leg is under review and depth semantics are two-book, not one ladder.",
            ],
            "ambiguity_ledger": [
                "This is price-transfer validation only; it does not validate any orderflow alpha feature.",
                "The tested windows are three April 2026 windows, not a roll/date-transition proof.",
                "USDJPY directional agreement is high, but the strict return-correlation floor is not clean across all windows.",
                "Depth, LVN/HVN, absorption, and heatmap questions are still blocked until event-window hypotheses are registered.",
                "Continuous futures roll behavior remains untested for these symbols.",
            ],
            "opened_questions": [
                "Does 6J/USDJPY recover above the strict floor across additional dates and roll-adjacent windows?",
                "Can XAGUSD and GBPUSD event-window manifests be built without label leakage or observer/live-scope confusion?",
                "Does any trades-level feature add signal after controlling for symbol/session and synthetic versus actual labels?",
                "Can GBPJPY price transfer be represented by synchronized 6B/6J returns without pretending the depth book is unified?",
            ],
            "next_steps": [
                "Add XAGUSD/SI and GBPUSD/6B to research-only event-manifest tooling in a separate tested commit if needed.",
                "Run one targeted 6J/USDJPY follow-up set before using USDJPY futures orderflow beyond diagnostics.",
                "Keep GBPJPY orderflow blocked until both legs pass price transfer and a separate two-book feature hypothesis is registered.",
                "Do not fetch mbp-1, mbp-10, or MBO for newly mapped symbols until a symbol-specific event-window hypothesis is registered.",
            ],
        },
    }
    return payload


def status_for(rows: list[dict[str, Any]], pair: str) -> str:
    for row in rows:
        if row["pair"] == pair:
            return row["status"]
    return "NOT_TESTED"


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else ""
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(value) for value in row) + " |")
    return out


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Futures Proxy Expansion Audit",
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
        "## Pair Audit",
        "",
        *_table(
            [
                "Pair",
                "Status",
                "Windows",
                "Min corr",
                "Median corr",
                "Min direction",
                "Best lag all zero",
                "Blocking reasons",
            ],
            [
                [
                    row["pair"],
                    row["status"],
                    row["window_count"],
                    row["min_zero_lag_corr"],
                    row["median_zero_lag_corr"],
                    row["min_directional_agreement"],
                    row["all_best_lag_zero"],
                    row["blocking_reasons"],
                ]
                for row in payload["pair_audit"]
            ],
        ),
        "",
        "## Decision Readout",
        "",
        *_table(
            ["Decision", "Status"],
            [[key, value] for key, value in payload["decision_readout"].items()],
        ),
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
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--min-windows", type=int, default=DEFAULT_MIN_WINDOWS)
    parser.add_argument("--corr-floor", type=float, default=DEFAULT_CORR_FLOOR)
    parser.add_argument("--directional-floor", type=float, default=DEFAULT_DIRECTIONAL_FLOOR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validation = load_json(args.input_json)
    payload = build_payload(
        validation,
        input_path=args.input_json,
        min_windows=args.min_windows,
        corr_floor=args.corr_floor,
        directional_floor=args.directional_floor,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    for row in payload["pair_audit"]:
        print(f"{row['pair']}: {row['status']} min_corr={row['min_zero_lag_corr']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run multi-window futures-to-CFD mapping validation.

Research/tooling only. Reads local Databento DBN files and MT5 M1 CSVs, tests
candidate MT5 timestamp shifts, then writes JSON + Markdown validation reports.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.futures_cfd_mapping import (  # noqa: E402
    MappingPair,
    aggregate_futures_m1,
    default_pairs,
    diagnose_pair,
    load_databento_trades,
    load_mt5_m1,
    parse_pair,
)


DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_MAPPING_MULTIDAY_REPORT_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_MAPPING_MULTIDAY_REPORT_2026-05-02.md"
)
DEFAULT_SHIFTS = (-240, -180, -120, -60, 0)
PRIMARY_PAIR_KEYS = {
    ("GC.v.0", "XAUUSD"),
    ("NQ.v.0", "NAS100"),
    ("YM.v.0", "US30_cash"),
}


def format_pair(pair: MappingPair) -> str:
    suffix = "" if pair.return_transform == "direct" else f":{pair.return_transform}"
    return f"{pair.futures_symbol}:{pair.mt5_symbol}{suffix}"


def parse_csv_ints(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def parse_dbn_args(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        for part in value.split(","):
            stripped = part.strip()
            if stripped:
                paths.append(Path(stripped))
    if not paths:
        raise ValueError("at least one DBN path is required")
    return paths


def _window_id(path: Path, futures_m1_index) -> str:
    if len(futures_m1_index) == 0:
        return path.stem
    start = futures_m1_index.min().strftime("%Y-%m-%dT%H:%M")
    end = futures_m1_index.max().strftime("%Y-%m-%dT%H:%M")
    return f"{start}_{end}"


def _load_sidecar(path: Path) -> dict[str, Any] | None:
    sidecar = path.with_suffix(path.suffix + ".meta.json")
    if not sidecar.exists():
        return None
    return json.loads(sidecar.read_text(encoding="utf-8"))


def _primary_score(
    diags: list[Any],
    primary_pair_keys: set[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    keys = primary_pair_keys or PRIMARY_PAIR_KEYS
    primary = [
        item
        for item in diags
        if (item.futures_symbol, item.mt5_symbol) in keys
        and item.zero_lag_return_corr is not None
        and item.aligned_minutes >= 60
    ]
    corrs = [float(item.zero_lag_return_corr) for item in primary]
    abs_corrs = [abs(value) for value in corrs]
    return {
        "primary_count": len(primary),
        "median_abs_corr": statistics.median(abs_corrs) if abs_corrs else None,
        "min_abs_corr": min(abs_corrs) if abs_corrs else None,
        "mean_abs_corr": statistics.mean(abs_corrs) if abs_corrs else None,
    }


def _score_key(score: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(score["primary_count"] or 0),
        float(score["median_abs_corr"] or -1.0),
        float(score["min_abs_corr"] or -1.0),
    )


def run_window(
    path: Path,
    pairs: list[MappingPair],
    shifts: list[int],
    *,
    mt5_dir: Path | str,
    max_lag_minutes: int,
) -> dict[str, Any]:
    trades = load_databento_trades([path])
    futures_m1 = aggregate_futures_m1(trades)
    if futures_m1.empty:
        raise ValueError(f"no futures rows after aggregation: {path}")

    start = futures_m1.index.min().isoformat()
    # Add one minute to make the exclusive end include the final futures minute.
    end = (futures_m1.index.max() + pd.Timedelta(minutes=1)).isoformat()

    shift_rows = []
    primary_pair_keys = {(pair.futures_symbol, pair.mt5_symbol) for pair in pairs}
    for shift in shifts:
        mt5_cache = {}
        diags = []
        for pair in pairs:
            if pair.mt5_symbol not in mt5_cache:
                mt5_cache[pair.mt5_symbol] = load_mt5_m1(
                    pair.mt5_symbol,
                    data_dir=mt5_dir,
                    start=start,
                    end=end,
                    time_shift_minutes=shift,
                )
            diags.append(
                diagnose_pair(
                    futures_m1,
                    mt5_cache[pair.mt5_symbol],
                    pair,
                    max_lag_minutes=max_lag_minutes,
                )
            )
        score = _primary_score(diags, primary_pair_keys=primary_pair_keys)
        shift_rows.append(
            {
                "shift_minutes": shift,
                "score": score,
                "diagnostics": [asdict(item) for item in diags],
            }
        )

    best = max(shift_rows, key=lambda row: _score_key(row["score"]))
    return {
        "window_id": _window_id(path, futures_m1.index),
        "dbn_path": str(path),
        "sidecar": _load_sidecar(path),
        "futures_start_utc": start,
        "futures_end_exclusive_utc": end,
        "selected_shift_minutes": best["shift_minutes"],
        "selected_score": best["score"],
        "selected_diagnostics": best["diagnostics"],
        "candidate_shift_scores": [
            {
                "shift_minutes": row["shift_minutes"],
                "score": row["score"],
            }
            for row in shift_rows
        ],
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Futures To CFD Mapping Multi-Day Report",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Window Results",
        "",
        "| Window | Selected shift | Primary median abs corr | Primary min abs corr | GC corr | NQ corr | YM corr | ES->US30 corr |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for window in payload["windows"]:
        diag_by_pair = {
            f"{d['futures_symbol']}->{d['mt5_symbol']}": d
            for d in window["selected_diagnostics"]
        }
        def _corr(key: str) -> str:
            value = diag_by_pair.get(key, {}).get("zero_lag_return_corr")
            return "" if value is None else f"{value:.4f}"
        def _score_value(key: str) -> str:
            value = window["selected_score"].get(key)
            return "" if value is None else f"{value:.4f}"
        lines.append(
            "| "
            f"{window['window_id']} | "
            f"{window['selected_shift_minutes']} | "
            f"{_score_value('median_abs_corr')} | "
            f"{_score_value('min_abs_corr')} | "
            f"{_corr('GC.v.0->XAUUSD')} | "
            f"{_corr('NQ.v.0->NAS100')} | "
            f"{_corr('YM.v.0->US30_cash')} | "
            f"{_corr('ES.v.0->US30_cash')} |"
        )

    lines.extend(["", "## Selected Pair Diagnostics", ""])
    lines.extend(
        [
            "| Window | Pair | Transform | Aligned minutes | Zero-lag corr | Best lag | Best-lag corr | Directional agreement |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for window in payload["windows"]:
        for diag in window["selected_diagnostics"]:
            def _num(key: str) -> str:
                value = diag.get(key)
                return "" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)
            lines.append(
                "| "
                f"{window['window_id']} | "
                f"{diag['futures_symbol']}->{diag['mt5_symbol']} | "
                f"{diag.get('return_transform', 'direct')} | "
                f"{diag['aligned_minutes']} | "
                f"{_num('zero_lag_return_corr')} | "
                f"{_num('best_lag_minutes')} | "
                f"{_num('best_lag_corr')} | "
                f"{_num('directional_agreement')} |"
            )

    lines.extend(
        [
            "",
            "## Synthesis",
            "",
            *[f"- {item}" for item in payload["synthesis"]["bullets"]],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in payload["synthesis"]["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["next_steps"], start=1)],
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")


def build_synthesis(windows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_shifts = [window["selected_shift_minutes"] for window in windows]
    stable_shift = len(set(selected_shifts)) == 1
    shift_windows: dict[int, list[str]] = {}
    total_cost = 0.0
    cost_count = 0
    for window in windows:
        shift_windows.setdefault(window["selected_shift_minutes"], []).append(window["window_id"])
        sidecar = window.get("sidecar") or {}
        estimate = sidecar.get("estimate") or {}
        cost = estimate.get("cost_usd")
        if cost is not None:
            total_cost += float(cost)
            cost_count += 1
    primary_mins = [
        window["selected_score"]["min_abs_corr"]
        for window in windows
        if window["selected_score"]["min_abs_corr"] is not None
    ]
    weak_windows = [
        window["window_id"]
        for window in windows
        if window["selected_score"]["min_abs_corr"] is None
        or window["selected_score"]["min_abs_corr"] < 0.85
    ]
    summary = (
        "Multi-day futures-to-CFD mapping validation checks whether CME futures "
        "can be used as an orderflow signal source for MT5 CFD execution symbols. "
        "This remains a transfer-quality diagnostic, not an alpha or promotion claim."
    )
    bullets = [
        f"Selected MT5 timestamp shifts: {selected_shifts}.",
        "Timestamp correction is stable across tested windows." if stable_shift else "Timestamp correction is seasonal/date-dependent across tested windows.",
        f"Shift-to-window map: {shift_windows}.",
        f"Primary minimum absolute correlation by window: {primary_mins}.",
    ]
    if cost_count:
        bullets.append(f"Databento estimated cost represented by sidecars: ${total_cost:.4f} across {cost_count} windows.")
    if weak_windows:
        bullets.append(f"Weak primary-transfer windows needing follow-up: {weak_windows}.")
    else:
        bullets.append("All tested windows passed the provisional primary-transfer correlation floor.")
    return {
        "summary": summary,
        "bullets": bullets,
        "ambiguities": [
            "This validates price-transfer quality, not orderflow alpha.",
            "Sampled windows are still finite and selected for diagnostics, not a formal population proof.",
            "The exact MT5 server-time/DST transition boundary still needs a full calendar audit.",
            "Roll-date behavior remains untested unless a selected window spans a futures roll.",
            "MT5 tick-level alignment is still pending; M1 alignment can hide sub-minute slippage and quote lag.",
            "Depth/heatmap schemas are not evaluated by trades-only mapping.",
        ],
        "open_questions": [
            "What exact date-aware MT5 timestamp policy removes the seasonal -120/-180 shift without per-window hindsight?",
            "Do futures orderflow features add signal beyond the already-high futures/CFD price transfer?",
            "Which event windows deserve mbp-1/mbp-10 depth pulls after trades-level transfer passes?",
            "Does YM remain the best direct US30 proxy in all tested regimes?",
        ],
        "next_steps": [
            "Build an event-window manifest from GTOS candidate/opportunity timestamps before any broad depth pull.",
            "Add trades-level orderflow features: CVD, delta shift, absorption proxy, trade-count bars, LVN/HVN/POC.",
            "Run OF-STRUCTURE-1: LVN-inside-FVG and VWAP-reclaim tests on harvested windows.",
            "Only then pull depth/heatmap windows for the subset where price-transfer and trades-level signals pass.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbn", action="append", required=True)
    parser.add_argument("--mt5-dir", default="data/historical_2026")
    parser.add_argument("--pair", action="append")
    parser.add_argument("--candidate-shifts", default=",".join(str(x) for x in DEFAULT_SHIFTS))
    parser.add_argument("--max-lag-minutes", type=int, default=5)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dbn_paths = parse_dbn_args(args.dbn)
    missing = [str(path) for path in dbn_paths if not path.exists()]
    if missing:
        parser.exit(2, f"missing DBN file(s): {missing}\n")
    pairs = [parse_pair(item) for item in args.pair] if args.pair else default_pairs()
    shifts = parse_csv_ints(args.candidate_shifts)
    windows = [
        run_window(
            path,
            pairs,
            shifts,
            mt5_dir=args.mt5_dir,
            max_lag_minutes=args.max_lag_minutes,
        )
        for path in dbn_paths
    ]
    payload = {
        "schema_version": "futures_cfd_mapping_multiday_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "dbn_paths": [str(path) for path in dbn_paths],
            "mt5_dir": args.mt5_dir,
            "pairs": [format_pair(pair) for pair in pairs],
            "candidate_shifts": shifts,
            "max_lag_minutes": args.max_lag_minutes,
        },
        "windows": windows,
        "synthesis": build_synthesis(windows),
    }
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    for window in windows:
        score = window["selected_score"]
        print(
            f"{window['window_id']}: shift={window['selected_shift_minutes']} "
            f"median_abs_corr={score['median_abs_corr']} "
            f"min_abs_corr={score['min_abs_corr']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run A2 — Per-Month Per-Instrument Rolling 50-Trade WR/ExpR Decay Velocity.

Pure-Python CLI that:
  1. Loads filled trades from ``knowledge_base/trade_records/{SYMBOL}/*.json``
     (per the live schema). Optionally augments with the legacy
     ``knowledge_base/index/_trade_index.json`` (batch trades pre-dating
     v1.1 instrumentation).
  2. Computes rolling WR/ExpR series per instrument.
  3. Computes per-instrument decay slope + p-value with Bonferroni
     correction across the family of seven decay-slope tests.
  4. Writes ``series.jsonl`` (one row per (instrument, window_end_date)),
     ``summary.json`` (per-instrument verdicts + concentration label),
     and ``report.md`` (verdict table + reasoning).

No AI calls. No production-config touched. Read-only on
``knowledge_base/``; writes only inside the chosen ``--output-dir``.

Usage:
    python scripts/research/run_a2_decay_velocity.py \
        --output-dir research/decay_diagnostic/A2_decay_velocity \
        --window 50 \
        --symbols XAUUSD US30_cash USDJPY GBPJPY GBPUSD XAGUSD NAS100
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research_infra.decay_velocity import (  # noqa: E402
    InstrumentVerdict,
    RollingSeries,
    SlopeResult,
    _extract_realized_r,
    _extract_symbol,
    _extract_timestamp,
    _is_filled,
    build_per_instrument_verdicts,
    decay_concentration,
    decay_slope,
    per_instrument_decay_velocity,
    rolling_window_wr_exp,
)


DEFAULT_SYMBOLS = (
    "XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100",
)
DEFAULT_TRADE_RECORDS_DIR = ROOT / "knowledge_base" / "trade_records"
DEFAULT_AUX_INDEX = ROOT / "knowledge_base" / "index" / "_trade_index.json"


def _gather_trades(
    trade_records_dir: Path,
    symbols: Iterable[str],
    aux_index_path: Path | None,
) -> dict[str, list[dict]]:
    """Read filled trades per symbol from disk.

    Mirrors what ``per_instrument_decay_velocity`` does internally, but
    returned so the script can show exact filled counts and feed the
    H1/H2 split.

    Symbol matching is case-insensitive but the *requested label* is
    preserved as the dict key (e.g. ``US30_cash`` stays ``US30_cash`` in
    output even though the disk dir / aux records may use a different
    case). This keeps the report's instrument labels stable regardless
    of underlying storage case.
    """
    requested_canonical = list(symbols)
    # Map uppercase → canonical (caller-supplied) form.
    canonical_by_upper: dict[str, str] = {s.upper(): s for s in requested_canonical}
    out: dict[str, list[dict]] = {s: [] for s in requested_canonical}
    seen_ids: dict[str, set[str]] = {s: set() for s in requested_canonical}

    if trade_records_dir.is_dir():
        for sym_dir in sorted(trade_records_dir.iterdir()):
            if not sym_dir.is_dir():
                continue
            sym_upper = sym_dir.name.upper()
            canonical = canonical_by_upper.get(sym_upper)
            if canonical is None:
                continue
            for fp in sorted(sym_dir.glob("*.json")):
                try:
                    record = json.loads(fp.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(record, dict):
                    continue
                if "symbol" not in record or not record.get("symbol"):
                    record["symbol"] = canonical
                if not _is_filled(record):
                    continue
                meta = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
                tid = record.get("trade_id") or (meta.get("trade_id") if meta else None)
                if tid:
                    if tid in seen_ids[canonical]:
                        continue
                    seen_ids[canonical].add(tid)
                out[canonical].append(record)

    # Aux index
    if aux_index_path and aux_index_path.exists():
        try:
            doc = json.loads(aux_index_path.read_text(encoding="utf-8"))
        except Exception:
            doc = None
        if isinstance(doc, dict):
            aux_trades = doc.get("trades")
            if isinstance(aux_trades, list):
                for t in aux_trades:
                    if not isinstance(t, dict):
                        continue
                    sym_extracted = _extract_symbol(t)
                    if sym_extracted is None:
                        continue
                    canonical = canonical_by_upper.get(sym_extracted.upper())
                    if canonical is None:
                        continue
                    if not _is_filled(t):
                        continue
                    tid = t.get("trade_id")
                    if tid and tid in seen_ids[canonical]:
                        continue
                    if tid:
                        seen_ids[canonical].add(tid)
                    out[canonical].append(t)

    return out


def _build_series_from_trades(trades_map: dict[str, list[dict]], window: int) -> dict[str, RollingSeries]:
    series_map: dict[str, RollingSeries] = {}
    for sym, trades in trades_map.items():
        s = rolling_window_wr_exp(trades, window=window)
        # Pin symbol to the requested key (rolling_window_wr_exp infers it)
        series_map[sym] = RollingSeries(
            symbol=sym, window=s.window, points=s.points, total_trades=s.total_trades,
        )
    return series_map


def _write_series_jsonl(out_dir: Path, series_map: dict[str, RollingSeries]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "series.jsonl"
    with fp.open("w", encoding="utf-8") as f:
        for sym, series in series_map.items():
            for p in series.points:
                f.write(json.dumps({
                    "instrument": sym,
                    "window_index": p.window_index,
                    "window_end_iso": p.timestamp.isoformat(),
                    "window_end_date": p.timestamp.date().isoformat(),
                    "n": p.n,
                    "wr": round(p.wr, 6),
                    "exp_r": round(p.exp_r, 6),
                    "window_size": series.window,
                    "total_trades": series.total_trades,
                }) + "\n")
    return fp


def _write_summary(
    out_dir: Path,
    verdicts: dict[str, InstrumentVerdict],
    *,
    window: int,
    bonferroni_n: int,
    n_min: int,
    alpha: float,
    concentration_label: str,
    concentration_reasoning: str,
    trade_records_dir: Path,
    aux_index_path: Path | None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "summary.json"

    def _v(v: InstrumentVerdict) -> dict:
        return {
            "symbol": v.symbol,
            "n_total": v.n_total,
            "n_windows": v.n_windows,
            "h1_wr": _round_or_nan(v.h1_wr, 4),
            "h2_wr": _round_or_nan(v.h2_wr, 4),
            "slope_per_30d": _round_or_nan(v.slope_per_30d, 6),
            "slope_per_window": _round_or_nan(v.slope_per_window, 6),
            "p_value_raw": _round_or_nan(v.p_value_raw, 6),
            "p_value_bonferroni": _round_or_nan(v.p_value_bonferroni, 6),
            "avg_window_days": _round_or_nan(v.avg_window_days, 4),
            "verdict": v.verdict,
        }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": window,
        "n_min": n_min,
        "alpha": alpha,
        "bonferroni_n": bonferroni_n,
        "trade_records_dir": str(trade_records_dir.resolve()),
        "aux_index_path": str(aux_index_path.resolve()) if aux_index_path else None,
        "instruments": [
            _v(verdicts[s]) for s in sorted(verdicts.keys())
        ],
        "decay_concentration": concentration_label,
        "concentration_reasoning": concentration_reasoning,
    }
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return fp


def _round_or_nan(x: float, digits: int) -> float | None:
    if not isinstance(x, (int, float)):
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(float(x), digits)


def _format_pp(x: float) -> str:
    """Format a pp/30d slope value as e.g. '-3.4 pp/mo' or '—'."""
    if not math.isfinite(x):
        return "—"
    return f"{x * 100:+.1f}"


def _format_wr(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    return f"{x * 100:.1f}%"


def _format_p(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    if x < 1e-4:
        return f"{x:.2e}"
    return f"{x:.4f}"


def _write_report(
    out_dir: Path,
    verdicts: dict[str, InstrumentVerdict],
    *,
    window: int,
    bonferroni_n: int,
    n_min: int,
    alpha: float,
    concentration_label: str,
    concentration_reasoning: str,
    trade_records_dir: Path,
    aux_index_path: Path | None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "report.md"

    syms_sorted = sorted(verdicts.keys())
    lines = []
    lines.append("# A2 — Per-Instrument Rolling-Window Decay Velocity")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        f"Per-instrument rolling **{window}-trade non-overlapping windows** of WR + Exp R, "
        "computed on realised-R per filled trade. Slope = OLS regression of WR over "
        "window-index, scaled to per-30-days via mean wall-clock window duration. "
        f"Bonferroni-correct across **N={bonferroni_n}** decay-slope tests "
        "(one per instrument with ≥3 windows). "
        f"Verdict thresholds: ``DECAYING`` requires n ≥ {n_min} AND p_corrected < {alpha}."
    )
    lines.append("")
    lines.append("Data sources:")
    lines.append(f"- Trade records dir: `{trade_records_dir.resolve()}`")
    if aux_index_path:
        lines.append(f"- Aux index: `{aux_index_path.resolve()}`")
    else:
        lines.append("- Aux index: (none)")
    lines.append("")
    lines.append("## Strategic verdict")
    lines.append("")
    lines.append("| Instrument | n | n_win | H1 WR | H2 WR | slope pp/mo | p (raw) | p (Bonferroni) | verdict |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in syms_sorted:
        v = verdicts[s]
        lines.append(
            f"| {v.symbol} | {v.n_total} | {v.n_windows} | {_format_wr(v.h1_wr)} | "
            f"{_format_wr(v.h2_wr)} | {_format_pp(v.slope_per_30d)} | "
            f"{_format_p(v.p_value_raw)} | {_format_p(v.p_value_bonferroni)} | "
            f"{v.verdict} |"
        )
    lines.append("")
    lines.append(f"**Decay concentration:** `{concentration_label}`")
    lines.append("")
    lines.append("**Reasoning:**")
    lines.append("")
    lines.append(concentration_reasoning)
    lines.append("")

    # Per-instrument decay narrative
    lines.append("## Per-instrument detail")
    lines.append("")
    for s in syms_sorted:
        v = verdicts[s]
        lines.append(f"### {s}")
        lines.append("")
        if v.verdict == "INSUFFICIENT_N":
            lines.append(
                f"- Filled trades: **{v.n_total}** (threshold n ≥ {n_min}). "
                "No realised-R data on disk meets the minimum sample. "
                "Verdict: `INSUFFICIENT_N`."
            )
        elif v.verdict == "INCONCLUSIVE":
            lines.append(
                f"- Filled trades: **{v.n_total}**, full windows: **{v.n_windows}**, "
                f"avg window duration: {v.avg_window_days:.1f}d." if math.isfinite(v.avg_window_days) else
                f"- Filled trades: **{v.n_total}**, full windows: **{v.n_windows}**."
            )
            lines.append(
                f"- H1 WR {_format_wr(v.h1_wr)} → H2 WR {_format_wr(v.h2_wr)}, "
                f"slope {_format_pp(v.slope_per_30d)} pp/mo, p_raw={_format_p(v.p_value_raw)}, "
                f"p_corrected={_format_p(v.p_value_bonferroni)}. "
                f"Trend not significant after Bonferroni; cannot reject null."
            )
        elif v.verdict == "STABLE":
            lines.append(
                f"- Filled trades: **{v.n_total}**, full windows: **{v.n_windows}**. "
                f"H1 WR {_format_wr(v.h1_wr)} → H2 WR {_format_wr(v.h2_wr)}, "
                f"slope {_format_pp(v.slope_per_30d)} pp/mo. "
                f"Absolute slope < 1pp/mo → no meaningful trend."
            )
        elif v.verdict in ("DECAYING", "IMPROVING"):
            lines.append(
                f"- Filled trades: **{v.n_total}**, full windows: **{v.n_windows}**, "
                f"avg window duration: {v.avg_window_days:.1f}d." if math.isfinite(v.avg_window_days) else
                f"- Filled trades: **{v.n_total}**, full windows: **{v.n_windows}**."
            )
            lines.append(
                f"- H1 WR {_format_wr(v.h1_wr)} → H2 WR {_format_wr(v.h2_wr)}, "
                f"slope {_format_pp(v.slope_per_30d)} pp/mo, p_raw={_format_p(v.p_value_raw)}, "
                f"p_corrected={_format_p(v.p_value_bonferroni)} < {alpha} → **{v.verdict}**."
            )
        else:
            lines.append(f"- Verdict: `{v.verdict}`.")
        lines.append("")

    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- **Walk-level vs realised-R discipline.** All slopes here are computed on "
        "actual realised R per filled trade. Walk-level / structural-proxy decay "
        "indicators (see `research/instrument_expansion_2026-04-25/02_decay_analysis.py`) "
        "are NOT the same metric and have been shown to reverse against realised-R "
        "outcomes in prior research (`feedback_walk_level_evidence_not_predictive`)."
    )
    lines.append(
        "- **Filled-trade availability.** The live ``trade_records/`` pipeline only "
        "populates ``exit.realized_R`` after a real broker fill. Under the FTMO "
        "free-trial EA exclusion, no live trades have filled yet (see ADR-A3 / "
        "`research/a3_trade_record_instrumentation/README.md`). Until paid-challenge "
        "fills accumulate, instruments with `INSUFFICIENT_N` verdicts are reflecting "
        "the data gap, not real-world stability."
    )
    lines.append(
        "- **Non-overlapping windows.** Each window is independent (step == window) "
        "to keep the slope-regression p-value calibrated. A 50-trade window over "
        "150 trades therefore yields 3 points — barely enough for a regression. "
        "Add more fills before expanding to overlapping/sliding windows."
    )
    lines.append(
        "- **Bonferroni denominator.** N = number of instruments with ≥ 3 full windows "
        "(i.e. instruments where a slope p-value could be computed). Instruments with "
        "INSUFFICIENT_N do not consume α budget."
    )
    lines.append("")

    fp.write_text("\n".join(lines), encoding="utf-8")
    return fp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory to write series.jsonl, summary.json, report.md.",
    )
    parser.add_argument(
        "--window", type=int, default=50,
        help="Rolling-window size in trades (default: 50).",
    )
    parser.add_argument(
        "--symbols", nargs="*", default=list(DEFAULT_SYMBOLS),
        help=f"Instruments to analyse (default: {' '.join(DEFAULT_SYMBOLS)}).",
    )
    parser.add_argument(
        "--trade-records-dir",
        default=str(DEFAULT_TRADE_RECORDS_DIR),
        help="Override trade_records dir (default: knowledge_base/trade_records).",
    )
    parser.add_argument(
        "--aux-index",
        default=str(DEFAULT_AUX_INDEX),
        help="Path to legacy _trade_index.json for batch trades. Pass empty string "
             "to disable. Default: knowledge_base/index/_trade_index.json.",
    )
    parser.add_argument(
        "--n-min", type=int, default=20,
        help="Min filled trades for a non-INSUFFICIENT_N verdict (default: 20).",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Bonferroni-corrected significance threshold (default: 0.05).",
    )
    args = parser.parse_args(argv)

    trade_records_dir = Path(args.trade_records_dir).resolve()
    aux_index_path: Path | None
    if args.aux_index and args.aux_index.strip():
        aux_index_path = Path(args.aux_index).resolve()
    else:
        aux_index_path = None
    out_dir = Path(args.output_dir).resolve()

    print(f"[A2] trade_records_dir = {trade_records_dir}", file=sys.stderr)
    print(f"[A2] aux_index_path    = {aux_index_path}", file=sys.stderr)
    print(f"[A2] symbols           = {args.symbols}", file=sys.stderr)
    print(f"[A2] window            = {args.window}", file=sys.stderr)
    print(f"[A2] output_dir        = {out_dir}", file=sys.stderr)

    trades_map = _gather_trades(trade_records_dir, args.symbols, aux_index_path)
    series_map = _build_series_from_trades(trades_map, window=args.window)

    print(f"[A2] per-symbol filled-trade counts:", file=sys.stderr)
    for sym in sorted(args.symbols):
        # Note: RollingSeries.__len__() returns len(points), so an empty-points
        # series is falsy → must use explicit ``is None`` check, NOT ``or``.
        s = series_map.get(sym)
        if s is None:
            s = RollingSeries(sym, args.window, tuple(), 0)
        print(f"[A2]   {sym}: {s.total_trades} filled, {len(s)} full window(s)", file=sys.stderr)

    # Bonferroni denominator: count instruments where slope p-value is finite
    slopes = {sym: decay_slope(s) for sym, s in series_map.items()}
    n_tested = sum(1 for sr in slopes.values() if math.isfinite(sr.p_value))
    bonferroni_n = max(1, n_tested)

    verdicts = build_per_instrument_verdicts(
        series_map, trades_map,
        n_min=args.n_min, alpha=args.alpha,
        bonferroni_n=bonferroni_n,
    )

    concentration_label, concentration_reasoning_summary = decay_concentration(verdicts)

    # Build a richer reasoning string for the report
    lines = [concentration_reasoning_summary]
    decaying = [v for v in verdicts.values() if v.verdict == "DECAYING"]
    improving = [v for v in verdicts.values() if v.verdict == "IMPROVING"]
    if decaying:
        lines.append(
            "Fastest decay: "
            + ", ".join(
                f"{v.symbol} ({v.slope_per_30d * 100:+.1f}pp/mo, p_corr={v.p_value_bonferroni:.3g})"
                for v in sorted(decaying, key=lambda x: x.slope_per_30d)
            )
            + "."
        )
    if improving:
        lines.append(
            "Improving: "
            + ", ".join(
                f"{v.symbol} ({v.slope_per_30d * 100:+.1f}pp/mo)"
                for v in sorted(improving, key=lambda x: -x.slope_per_30d)
            )
            + "."
        )
    insufficient_syms = [v.symbol for v in verdicts.values() if v.verdict == "INSUFFICIENT_N"]
    if insufficient_syms:
        lines.append(
            f"Insufficient sample (n < {args.n_min}): "
            + ", ".join(insufficient_syms)
            + ". Cannot draw a verdict; reflects the FTMO-free-trial EA exclusion "
              "blocking live fills (see `research/a3_trade_record_instrumentation/README.md`)."
        )
    concentration_reasoning = " ".join(lines)

    series_fp = _write_series_jsonl(out_dir, series_map)
    summary_fp = _write_summary(
        out_dir, verdicts,
        window=args.window, bonferroni_n=bonferroni_n,
        n_min=args.n_min, alpha=args.alpha,
        concentration_label=concentration_label,
        concentration_reasoning=concentration_reasoning,
        trade_records_dir=trade_records_dir,
        aux_index_path=aux_index_path,
    )
    report_fp = _write_report(
        out_dir, verdicts,
        window=args.window, bonferroni_n=bonferroni_n,
        n_min=args.n_min, alpha=args.alpha,
        concentration_label=concentration_label,
        concentration_reasoning=concentration_reasoning,
        trade_records_dir=trade_records_dir,
        aux_index_path=aux_index_path,
    )
    print(f"[A2] wrote {series_fp}", file=sys.stderr)
    print(f"[A2] wrote {summary_fp}", file=sys.stderr)
    print(f"[A2] wrote {report_fp}", file=sys.stderr)
    print(f"[A2] decay_concentration: {concentration_label}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

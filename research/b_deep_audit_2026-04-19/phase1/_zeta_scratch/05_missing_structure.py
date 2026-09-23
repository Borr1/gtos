"""
For each NO_TRADE record where forward price hit +1.5 ATR (in inferred direction)
within 4h, sample and inspect the chart. Look for:
  - A visible OB that market_state.py missed
  - A FVG that wasn't emitted
  - A liquidity sweep that should have qualified
  - Equal highs/lows aligned with the move

Dump markdown with 10 samples per instrument + ASCII chart.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


def load_m15(symbol: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["time"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    return rows


def load_nas100():
    results = []
    for i in range(1, 6):
        p = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19" / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        results += d["results"]
    return results


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if "results" in d:
        return d["results"]
    return d


def normalize_ts(ts: str) -> str:
    t = ts.strip()
    if t.endswith("Z"):
        t = t[:-1]
    t = t.replace("T", " ")
    if len(t) == 16:
        t = t + ":00"
    return t


def atr14(m15: list[dict], idx: int, period: int = 14) -> float:
    if idx < period:
        return 0.0
    tr = []
    for k in range(idx - period, idx):
        h, l = m15[k + 1]["high"], m15[k + 1]["low"]
        pc = m15[k]["close"]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(tr) / len(tr) if tr else 0.0


def ascii_chart(window: list[dict], signal_idx: int, lvls: dict[str, float] = None) -> str:
    lvls = lvls or {}
    highs = [c["high"] for c in window] + [v for v in lvls.values() if isinstance(v, (int, float))]
    lows = [c["low"] for c in window] + [v for v in lvls.values() if isinstance(v, (int, float))]
    hi, lo = max(highs), min(lows)
    if hi == lo:
        return "(flat)"
    rows = 18
    lines = [[" "] * len(window) for _ in range(rows)]

    def row_for(price):
        frac = (hi - price) / (hi - lo)
        return max(0, min(rows - 1, int(frac * (rows - 1))))

    for i, c in enumerate(window):
        r_hi = row_for(c["high"])
        r_lo = row_for(c["low"])
        r_o = row_for(c["open"])
        r_c = row_for(c["close"])
        bull = c["close"] >= c["open"]
        body_top = min(r_o, r_c)
        body_bot = max(r_o, r_c)
        for r in range(r_hi, r_lo + 1):
            if body_top <= r <= body_bot:
                lines[r][i] = "█" if bull else "░"
            else:
                lines[r][i] = "│"
        if i == signal_idx:
            lines[0][i] = "S"

    for name, price in lvls.items():
        if not isinstance(price, (int, float)):
            continue
        r = row_for(price)
        for i in range(len(window)):
            if lines[r][i] == " ":
                lines[r][i] = name[0]

    header = f"  range {lo:.4f}-{hi:.4f} span={hi-lo:.4f}"
    body = "\n".join("".join(r) for r in lines)
    return f"{header}\n{body}"


def find_no_trade_winners(results: list[dict], m15: list[dict], k_atr_tp: float = 1.5, horizon_candles: int = 16) -> list[dict]:
    """
    For each NO_TRADE, check if forward price moved k_atr_tp×ATR in EITHER direction within horizon.
    Return list of records where this happened in ONE direction only (clean missed winner).
    """
    m15_idx = {c["time"]: i for i, c in enumerate(m15)}
    winners = []
    for r in results:
        if r.get("decision") != "NO_TRADE":
            continue
        ts = normalize_ts(r["candle_time"])
        idx = m15_idx.get(ts)
        if idx is None:
            continue
        atr = atr14(m15, idx)
        if atr <= 0:
            continue
        signal_close = m15[idx]["close"]
        long_tp = signal_close + k_atr_tp * atr
        long_sl = signal_close - 1.0 * atr
        short_tp = signal_close - k_atr_tp * atr
        short_sl = signal_close + 1.0 * atr
        end = min(len(m15), idx + horizon_candles + 1)
        long_outcome, short_outcome = "U", "U"
        for j in range(idx + 1, end):
            c = m15[j]
            # LONG
            if long_outcome == "U":
                if c["low"] <= long_sl:
                    long_outcome = "L"
                elif c["high"] >= long_tp:
                    long_outcome = "W"
            if short_outcome == "U":
                if c["high"] >= short_sl:
                    short_outcome = "L"
                elif c["low"] <= short_tp:
                    short_outcome = "W"
            if long_outcome != "U" and short_outcome != "U":
                break
        # Clean winners: ONE direction won, other lost or unresolved
        if long_outcome == "W" and short_outcome != "W":
            winners.append({"record": r, "idx": idx, "direction": "LONG", "atr": atr,
                            "signal_close": signal_close, "tp": long_tp, "sl": long_sl})
        elif short_outcome == "W" and long_outcome != "W":
            winners.append({"record": r, "idx": idx, "direction": "SHORT", "atr": atr,
                            "signal_close": signal_close, "tp": short_tp, "sl": short_sl})
    return winners


def main():
    random.seed(7)
    summary = []
    detail_lines = ["# Zeta — Missing-Structure Sample on NO_TRADE Winners", ""]

    for symbol, loader in [
        ("NAS100", load_nas100),
        ("XAUUSD", lambda: load(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json")),
        ("EURUSD", lambda: load(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json")),
    ]:
        results = loader()
        m15 = load_m15(symbol)
        winners = find_no_trade_winners(results, m15)
        no_trade_total = sum(1 for r in results if r.get("decision") == "NO_TRADE")
        summary.append({
            "symbol": symbol,
            "no_trade_total": no_trade_total,
            "clean_directional_winners": len(winners),
            "pct_no_trade_that_winners": round(100 * len(winners) / no_trade_total, 2) if no_trade_total else 0.0,
        })
        detail_lines.append(f"\n## {symbol}")
        detail_lines.append(f"n NO_TRADE={no_trade_total}; clean-direction winners (1.5ATR TP, 1ATR SL, 4h)={len(winners)}"
                            f" = {100*len(winners)/no_trade_total:.2f}%")

        sampled = random.sample(winners, min(10, len(winners)))
        for s in sampled:
            r = s["record"]
            reason = r.get("no_trade_reason", "")
            idx = s["idx"]
            window = m15[max(0, idx - 8): idx + 16]
            signal_in_window = idx - max(0, idx - 8)
            lvls = {
                "E": s["signal_close"],
                "T": s["tp"],
                "X": s["sl"],
            }
            chart = ascii_chart(window, signal_in_window, lvls)
            detail_lines.append(f"\n### {s['record']['candle_time']} kz={r.get('kill_zone')} "
                                f"direction_that_won={s['direction']} atr={s['atr']:.4f}")
            detail_lines.append(f"- NO_TRADE reason: `{reason[:200]}`")
            detail_lines.append(f"- Signal close={s['signal_close']:.4f} TP (1.5ATR)={s['tp']:.4f} SL (1ATR)={s['sl']:.4f}")
            detail_lines.append("```text")
            detail_lines.append(chart)
            detail_lines.append("```")

    # Summary table
    out_lines = ["# Zeta — Missing-Structure Summary Table\n"]
    out_lines.append("| Symbol | NO_TRADE | Clean-direction winners (1.5ATR, 4h) | % |")
    out_lines.append("|---|---:|---:|---:|")
    for s in summary:
        out_lines.append(f"| {s['symbol']} | {s['no_trade_total']} | {s['clean_directional_winners']} | {s['pct_no_trade_that_winners']}% |")

    out_md = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "05_missing_structure.md"
    out_md.write_text("\n".join(out_lines) + "\n\n" + "\n".join(detail_lines), encoding="utf-8")

    print("Summary:")
    for s in summary:
        print(f"  {s['symbol']}: NO_TRADE={s['no_trade_total']} winners={s['clean_directional_winners']} ({s['pct_no_trade_that_winners']}%)")
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    main()

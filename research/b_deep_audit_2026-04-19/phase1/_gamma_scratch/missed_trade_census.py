#!/usr/bin/env python3
"""Agent gamma — Missed-trade opportunity-cost census (phase1 discovery).

For each sim record (XAUUSD, NAS100, EURUSD-secondary), measure the forward
price behaviour that would have determined outcome if the record HAD been
traded. Three decision slices:

  NO_TRADE         — direction proxied from `bias` field (when non-null).
                     We measure directional persistence: did price move
                     ±X ATR(M15)*1.5 (proxy for +1.5R) in `bias` direction
                     within 4h / 12h / 24h of candle close?

  REJECTED_L2      — full (entry, SL, TP1) present. Use compute_outcome()
                     at honest per-instrument epsilon. Bucket by l2_reason
                     prefix.

  BLOCKED_LIMIT    — same as REJECTED_L2 but bucketed by block_reason prefix.

Quarterly/monthly evolution:

  We split by *month* (Jan / Feb / Mar / Apr 2026) because the entire dataset
  is 2026-Q1 + early-Q2 (Jan 2 – Apr 17). Calling it "Q2-2025 → Q1-2026" as
  the brief does is nomenclature only — the code uses calendar months.
  Decay-tracking hypothesis holds regardless.

Usage:
    python research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/missed_trade_census.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv  # noqa: E402
from scripts.simulate_t7_live_period import (  # noqa: E402
    EPSILON_BY_SYMBOL,
    compute_outcome,
)

# ── Helpers ──────────────────────────────────────────────────────────────

def _month_key(rec: dict) -> str:
    """Calendar-month bucket key like '2026-01'."""
    d = rec.get("date") or ""
    return d[:7] if len(d) >= 7 else "unknown"


def _is_degenerate(rec: dict, tol: float = 1e-6) -> bool:
    e = rec.get("entry_price") or 0
    s = rec.get("stop_loss") or 0
    t = rec.get("take_profit_1") or 0
    if e == 0 or s == 0 or t == 0:
        return True
    return (
        abs(e - s) < tol
        or abs(e - t) < tol
        or abs(s - t) < tol
    )


def _l2_prefix(rec: dict) -> str:
    lr = rec.get("l2_reason") or ""
    return lr.split(":")[0].strip() or "unknown"


def _block_prefix(rec: dict) -> str:
    br = rec.get("block_reason") or ""
    return br.split(" (")[0].strip() or "unknown"


# ── Load sim records per symbol ──────────────────────────────────────────

def _load_records(symbol: str) -> list[dict]:
    if symbol == "NAS100":
        out = []
        for i in range(1, 6):
            p = _PROJECT_ROOT / f"research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{i}/NAS100_t7_simulation.json"
            d = json.load(open(p))
            out.extend(d.get("results", d))
        return out
    if symbol == "EURUSD":
        p = _PROJECT_ROOT / "research/t7_live_simulation/EURUSD_t7_simulation.json"
        d = json.load(open(p))
        return d.get("results", d)
    if symbol == "XAUUSD":
        p = _PROJECT_ROOT / "research/t7_live_simulation/all_results_jan_apr10.json"
        d = json.load(open(p))
        return d.get("results", d)
    raise ValueError(symbol)


def _load_m15(symbol: str) -> list[dict]:
    p = _PROJECT_ROOT / f"data/historical_2026/{symbol}_M15.csv"
    return parse_tradingview_csv(p)


# ── ATR estimate per symbol from M15 (for NO_TRADE 1.5R-proxy TP) ────────

def _m15_atr(m15: list[dict], periods: int = 14) -> float:
    """Simple SMA ATR from last `periods` candles; we use dataset-average."""
    if len(m15) < periods + 2:
        return 0.0
    total = 0.0
    n = 0
    for c in m15[-periods:]:
        tr = c["high"] - c["low"]
        total += tr
        n += 1
    return total / n if n else 0.0


# ── NO_TRADE forward hit-rate census ─────────────────────────────────────

def _nt_forward_hit(
    rec: dict,
    m15_by_time: dict[str, int],
    m15: list[dict],
    target_R_in_atr: float,
    atr_proxy: float,
    horizon_candles: int,
) -> str | None:
    """Did price move ±target_R_in_atr * atr_proxy in bias direction within
    `horizon_candles` M15 candles after the signal candle?

    Returns:
      'HIT_TP'  — bias-directional +1.5R (proxy) first.
      'HIT_SL'  — inverse bias movement −1R (proxy) first.
      'NEITHER' — horizon exhausted without either.
      None      — no bias / missing price / candle lookup fail.
    """
    bias = rec.get("bias")
    if bias not in ("bullish", "bearish"):
        return None
    ct = rec.get("candle_time")
    if not ct:
        return None
    idx = m15_by_time.get(ct)
    if idx is None:
        return None
    # Entry = close of signal candle (approximate; no price in NO_TRADE schema)
    sig = m15[idx]
    entry = sig.get("close")
    if entry is None:
        return None

    # Proxy: 1R = 1 × ATR (one unit of risk). TP_proxy = entry + 1.5 * ATR, SL_proxy = entry - 1 * ATR.
    if bias == "bullish":
        tp_proxy = entry + target_R_in_atr * atr_proxy
        sl_proxy = entry - 1.0 * atr_proxy
    else:
        tp_proxy = entry - target_R_in_atr * atr_proxy
        sl_proxy = entry + 1.0 * atr_proxy

    end = min(idx + 1 + horizon_candles, len(m15))
    for i in range(idx + 1, end):
        h, l = m15[i]["high"], m15[i]["low"]
        if bias == "bullish":
            # Check SL first (order-of-fill approximation: intrabar ambiguity)
            # Use conservative convention — check SL first only when low breaches before high
            # Since we have no intrabar data, flag as HIT_SL if SL hit that candle even if TP also hit
            # (conservative, tilts against the "missed winners" claim)
            if l <= sl_proxy:
                return "HIT_SL"
            if h >= tp_proxy:
                return "HIT_TP"
        else:
            if h >= sl_proxy:
                return "HIT_SL"
            if l <= tp_proxy:
                return "HIT_TP"
    return "NEITHER"


def _nt_census(
    nt_recs: list[dict],
    m15: list[dict],
    symbol: str,
) -> dict:
    """Per-symbol NO_TRADE forward census at 4h/12h/24h horizons.

    4h  = 16 M15 candles
    12h = 48
    24h = 96
    """
    m15_by_time = {c["time"]: i for i, c in enumerate(m15)}
    atr = _m15_atr(m15, periods=14 * 96)  # dataset-wide average ATR (stable)
    horizons = {"4h": 16, "12h": 48, "24h": 96}

    with_bias = [r for r in nt_recs if r.get("bias") in ("bullish", "bearish")]
    stats = {"n_total": len(nt_recs), "n_with_bias": len(with_bias), "atr_used": round(atr, 4)}

    for label, h in horizons.items():
        tp_hits = sl_hits = neither = none_ret = 0
        per_month = defaultdict(lambda: [0, 0, 0])  # [tp, sl, neither]
        for r in with_bias:
            out = _nt_forward_hit(r, m15_by_time, m15, 1.5, atr, h)
            mk = _month_key(r)
            if out is None:
                none_ret += 1
            elif out == "HIT_TP":
                tp_hits += 1
                per_month[mk][0] += 1
            elif out == "HIT_SL":
                sl_hits += 1
                per_month[mk][1] += 1
            else:
                neither += 1
                per_month[mk][2] += 1
        resolved = tp_hits + sl_hits
        stats[label] = {
            "tp_first": tp_hits,
            "sl_first": sl_hits,
            "neither": neither,
            "skipped_none": none_ret,
            "resolved": resolved,
            "hypo_WR%": round(100 * tp_hits / resolved, 1) if resolved else None,
            "hypo_ExpR": round((1.5 * tp_hits - 1.0 * sl_hits) / max(len(with_bias), 1), 3),
            "per_month": {k: {"tp": v[0], "sl": v[1], "neither": v[2]} for k, v in sorted(per_month.items())},
        }
    return stats


# ── L2 / BLOCKED_LIMIT counterfactual ────────────────────────────────────

def _bucket_outcomes(
    recs: list[dict],
    m15: list[dict],
    symbol: str,
    epsilon: float | None = None,
) -> list[dict]:
    outs = []
    orig_eps = EPSILON_BY_SYMBOL.get(symbol)
    if epsilon is not None:
        EPSILON_BY_SYMBOL[symbol] = epsilon
    try:
        for rec in recs:
            if not (rec.get("entry_price") and rec.get("stop_loss") and rec.get("take_profit_1")):
                outs.append({"outcome": "UNKNOWN", "reason": "missing_prices"})
                continue
            # Retrieve candle_close from M15 CSV (XAUUSD sim records don't carry it)
            cc = rec.get("candle_close")
            if cc is None:
                # Lookup from M15 by candle_time
                for c in m15:
                    if c["time"] == rec["candle_time"]:
                        cc = c["close"]
                        break
            cand = {
                "entry_price": rec["entry_price"],
                "stop_loss": rec["stop_loss"],
                "take_profit_1": rec["take_profit_1"],
                "direction": rec.get("direction", "LONG"),
                "candle_close": cc,
                "candle_time": rec["candle_time"],
                "symbol": symbol,
            }
            outs.append(compute_outcome(cand, m15, symbol=symbol))
    finally:
        if epsilon is not None:
            if orig_eps is None:
                EPSILON_BY_SYMBOL.pop(symbol, None)
            else:
                EPSILON_BY_SYMBOL[symbol] = orig_eps
    return outs


def _agg(recs: list[dict], outs: list[dict]) -> dict:
    w = l = u = o = k = 0
    sum_r = 0.0
    n_real = 0
    for rec, oc in zip(recs, outs):
        if _is_degenerate(rec):
            continue
        n_real += 1
        out = oc.get("outcome")
        r = oc.get("r_multiple") or 0
        if out == "WIN":
            w += 1
            sum_r += r
        elif out == "LOSS":
            l += 1
            sum_r += r
        elif out == "UNFILLED":
            u += 1
        elif out == "OPEN":
            o += 1
        else:
            k += 1
    resolved = w + l
    return {
        "n_total": len(recs),
        "n_degenerate": sum(1 for r in recs if _is_degenerate(r)),
        "n_real": n_real,
        "W": w,
        "L": l,
        "UNFILLED": u,
        "OPEN": o,
        "UNKNOWN": k,
        "resolved": resolved,
        "WR%": round(100 * w / resolved, 1) if resolved else None,
        "sumR": round(sum_r, 2),
        "expR": round(sum_r / max(n_real, 1), 3),
    }


def _monthly_agg(recs: list[dict], outs: list[dict]) -> dict[str, dict]:
    per_m = defaultdict(lambda: ([], []))
    for r, o in zip(recs, outs):
        per_m[_month_key(r)][0].append(r)
        per_m[_month_key(r)][1].append(o)
    return {mk: _agg(rs, os) for mk, (rs, os) in sorted(per_m.items())}


def _bucket_by_reason(recs: list[dict], keyfn) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for r in recs:
        out[keyfn(r)].append(r)
    return dict(out)


# ── Significance helpers ────────────────────────────────────────────────

def _binom_pvalue_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Two-sided exact binomial p. Returns None for n=0."""
    if n <= 0:
        return None
    def pmf(i): return comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    obs = pmf(k)
    tail = sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs + 1e-15)
    return min(tail, 1.0)


# ── Driver per instrument ────────────────────────────────────────────────

def run_instrument(symbol: str) -> dict:
    print(f"\n[{symbol}] loading records ...")
    recs = _load_records(symbol)
    m15 = _load_m15(symbol)
    eps = EPSILON_BY_SYMBOL.get(symbol, 0.05)

    # Decision slices
    nt = [r for r in recs if r.get("decision") == "NO_TRADE"]
    l2 = [r for r in recs if r.get("decision") == "REJECTED_L2"]
    bl = [r for r in recs if r.get("decision") == "BLOCKED_LIMIT"]
    cand = [r for r in recs if r.get("decision") == "CANDIDATE"]

    print(f"[{symbol}] n_recs={len(recs)} | NT={len(nt)} L2={len(l2)} BL={len(bl)} CAND={len(cand)} eps={eps}")

    # 1) NO_TRADE forward hit-rate census
    nt_stats = _nt_census(nt, m15, symbol)

    # 2) L2 aggregate + per-bucket
    l2_outs = _bucket_outcomes(l2, m15, symbol)
    l2_agg = _agg(l2, l2_outs)
    l2_monthly = _monthly_agg(l2, l2_outs)
    l2_by = _bucket_by_reason(l2, _l2_prefix)
    l2_bucket_stats = {}
    for reason, rs in l2_by.items():
        os_ = _bucket_outcomes(rs, m15, symbol)
        l2_bucket_stats[reason] = {
            "stats": _agg(rs, os_),
            "monthly": _monthly_agg(rs, os_),
        }

    # 3) BLOCKED_LIMIT aggregate + per-bucket
    bl_outs = _bucket_outcomes(bl, m15, symbol)
    bl_agg = _agg(bl, bl_outs)
    bl_monthly = _monthly_agg(bl, bl_outs)
    bl_by = _bucket_by_reason(bl, _block_prefix)
    bl_bucket_stats = {}
    for reason, rs in bl_by.items():
        os_ = _bucket_outcomes(rs, m15, symbol)
        bl_bucket_stats[reason] = {
            "stats": _agg(rs, os_),
            "monthly": _monthly_agg(rs, os_),
        }

    # 4) CANDIDATE monthly baseline (accepted — for comparison to "missed" decay)
    cand_outs = _bucket_outcomes(cand, m15, symbol)
    cand_agg = _agg(cand, cand_outs)
    cand_monthly = _monthly_agg(cand, cand_outs)

    return {
        "symbol": symbol,
        "n_total": len(recs),
        "nt": nt_stats,
        "cand": {"agg": cand_agg, "monthly": cand_monthly},
        "l2": {"agg": l2_agg, "monthly": l2_monthly, "buckets": l2_bucket_stats},
        "bl": {"agg": bl_agg, "monthly": bl_monthly, "buckets": bl_bucket_stats},
    }


def main() -> int:
    out = {}
    for sym in ("XAUUSD", "NAS100", "EURUSD"):
        out[sym] = run_instrument(sym)

    outp = _PROJECT_ROOT / "research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/census_out.json"
    outp.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\n-> wrote {outp}")

    # Quick console summary
    for sym in ("XAUUSD", "NAS100", "EURUSD"):
        s = out[sym]
        print(f"\n=== {sym} ===")
        print(f"  CAND : agg {s['cand']['agg']}")
        print(f"  L2   : agg {s['l2']['agg']}")
        print(f"  BL   : agg {s['bl']['agg']}")
        print(f"  NT n_with_bias={s['nt']['n_with_bias']}")
        for h in ("4h", "12h", "24h"):
            d = s["nt"][h]
            print(f"     {h} hypo_WR={d['hypo_WR%']} expR={d['hypo_ExpR']} tp={d['tp_first']} sl={d['sl_first']} neither={d['neither']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

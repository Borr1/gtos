"""Run edge tests over EVERY M15 candle (not just T7 sampled candles).
This gives us:
  - Full hour-of-day coverage (including extended hours and overnight)
  - Larger n for statistical power
  - Honest cross-instrument comparison

Forward-replay uses 1.0×ATR SL / 1.5×ATR TP / 4h horizon — same as T7-sampled run.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from load_data import load_m15, load_h1, load_h4, load_d1, in_any_kz
from forward_replay import replay_hypothetical
from features import build_features

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")

INSTRUMENTS = ["XAUUSD", "EURUSD", "NAS100", "USDJPY", "GBPJPY", "US30", "GBPUSD"]


def _sig_test_prop(wins, n, null_p=0.5):
    if n == 0:
        return 1.0
    if n < 30:
        from math import comb
        k = wins
        p_at_least = sum(comb(n, i) * (null_p ** i) * ((1 - null_p) ** (n - i)) for i in range(k, n + 1))
        p_at_most = sum(comb(n, i) * (null_p ** i) * ((1 - null_p) ** (n - i)) for i in range(0, k + 1))
        return min(1.0, 2 * min(p_at_least, p_at_most))
    p_hat = wins / n
    se = math.sqrt(null_p * (1 - null_p) / n)
    z = (p_hat - null_p) / se
    from math import erfc
    return erfc(abs(z) / math.sqrt(2))


def scan_symbol(symbol, sample_step=1):
    """Walk every Nth M15 candle (sample_step=1 = all), build features, replay both directions,
    and collect the dataset."""
    print(f"  Loading {symbol}...", flush=True)
    m15 = load_m15(symbol)
    if not m15:
        print(f"    (no M15 data for {symbol})", flush=True)
        return []
    h1 = load_h1(symbol)
    h4 = load_h4(symbol)
    d1 = load_d1(symbol)
    print(f"    m15={len(m15)} h1={len(h1)} h4={len(h4)} d1={len(d1)}", flush=True)

    rows = []
    # Start from idx 100 so we have enough history for ATR, H1/H4/D1 trends
    for idx in range(100, len(m15) - 16, sample_step):
        t = m15[idx]["time"]
        # Only Mon-Fri (trading days)
        if t.weekday() >= 5:
            continue
        rec = {
            "candle_time": t,
            "symbol": symbol,
            "_parsed_time": t,
        }
        feats = build_features(rec, m15, h1, h4, d1)
        if feats is None:
            continue
        o = replay_hypothetical(m15, idx, horizon_minutes=4 * 60,
                                sl_atr_mult=1.0, tp_atr_mult=1.5)
        if o is None:
            continue
        row = {
            **feats,
            "long_outcome": o["long_outcome"],
            "short_outcome": o["short_outcome"],
            "winner": o["winner"],
            "bars_to_resolve": o["bars_to_resolve_winner"],
        }
        rows.append(row)
    print(f"    scanned rows: {len(rows)}", flush=True)
    return rows


def _signal_rate(rows, signal_fn, direction_fn):
    """For all rows where signal_fn(row)==True AND direction_fn(row) in ('LONG','SHORT'),
    compute WR based on whether the predicted direction hypothetical WIN'd."""
    hits = []
    for r in rows:
        if not signal_fn(r):
            continue
        d = direction_fn(r)
        if d not in ("LONG", "SHORT"):
            continue
        oc = r["long_outcome"] if d == "LONG" else r["short_outcome"]
        if oc in ("WIN", "LOSS"):
            hits.append((d, oc, r))
    n = len(hits)
    wins = sum(1 for d, oc, r in hits if oc == "WIN")
    return hits, wins, n


def _base_directional_winrate(rows):
    """Baseline: without any signal, how often does LONG vs SHORT resolve?
    i.e., if you picked LONG blindly, what's your 1.5R / 1.0R WR?
    This tells us our null expectation for the 'pick a side' problem."""
    n_long_resolved = sum(1 for r in rows if r["long_outcome"] in ("WIN", "LOSS"))
    n_long_wins = sum(1 for r in rows if r["long_outcome"] == "WIN")
    n_short_resolved = sum(1 for r in rows if r["short_outcome"] in ("WIN", "LOSS"))
    n_short_wins = sum(1 for r in rows if r["short_outcome"] == "WIN")
    return {
        "n_long_resolved": n_long_resolved,
        "n_long_wins": n_long_wins,
        "wr_long": n_long_wins / n_long_resolved if n_long_resolved else None,
        "n_short_resolved": n_short_resolved,
        "n_short_wins": n_short_wins,
        "wr_short": n_short_wins / n_short_resolved if n_short_resolved else None,
    }


def edge_fvg_only(rows):
    sig = lambda r: r.get("fvg_m15") in ("bull", "bear") and r.get("h1_dir") == ("bullish" if r.get("fvg_m15") == "bull" else "bearish")
    direction = lambda r: "LONG" if r.get("fvg_m15") == "bull" else "SHORT"
    return _signal_rate(rows, sig, direction)


def edge_sweep_displacement(rows):
    def sig(r):
        if not r.get("displacement_high"):
            return False
        sweep_hi = any(r.get(k) for k in ("sweep_pdh", "sweep_asian_hi", "sweep_london_hi"))
        sweep_lo = any(r.get(k) for k in ("sweep_pdl", "sweep_asian_lo", "sweep_london_lo"))
        if sweep_hi == sweep_lo:
            return False
        direction = "SHORT" if sweep_hi else "LONG"
        # H1-aligned
        if direction == "SHORT" and r.get("h1_dir") == "bullish":
            return False
        if direction == "LONG" and r.get("h1_dir") == "bearish":
            return False
        return True

    def direction(r):
        sweep_hi = any(r.get(k) for k in ("sweep_pdh", "sweep_asian_hi", "sweep_london_hi"))
        return "SHORT" if sweep_hi else "LONG"
    return _signal_rate(rows, sig, direction)


def edge_fib50_d1(rows):
    def sig(r):
        d = r.get("fib50_dist_atr")
        if d is None or abs(d) > 0.25:
            return False
        return r.get("d1_dir") in ("bullish", "bearish")

    def direction(r):
        return "LONG" if r.get("d1_dir") == "bullish" else "SHORT"
    return _signal_rate(rows, sig, direction)


def edge_triple_align(rows):
    """NEW: D1 + H4 + H1 all same direction, buy LONG if bullish, SHORT if bearish."""
    def sig(r):
        return r.get("alignment_trend") in ("bullish", "bearish")

    def direction(r):
        return "LONG" if r.get("alignment_trend") == "bullish" else "SHORT"
    return _signal_rate(rows, sig, direction)


def edge_triple_align_plus_fvg(rows):
    """D1+H4+H1 aligned AND M15 FVG in that direction."""
    def sig(r):
        a = r.get("alignment_trend")
        if a not in ("bullish", "bearish"):
            return False
        fvg = r.get("fvg_m15")
        if a == "bullish" and fvg != "bull":
            return False
        if a == "bearish" and fvg != "bear":
            return False
        return True
    def direction(r):
        return "LONG" if r.get("alignment_trend") == "bullish" else "SHORT"
    return _signal_rate(rows, sig, direction)


def edge_triple_align_plus_sweep(rows):
    """D1+H4+H1 aligned AND sweep in reversal direction."""
    def sig(r):
        a = r.get("alignment_trend")
        if a not in ("bullish", "bearish"):
            return False
        sweep_hi = any(r.get(k) for k in ("sweep_pdh", "sweep_asian_hi", "sweep_london_hi"))
        sweep_lo = any(r.get(k) for k in ("sweep_pdl", "sweep_asian_lo", "sweep_london_lo"))
        if a == "bullish" and not sweep_lo:
            return False
        if a == "bearish" and not sweep_hi:
            return False
        return True
    def direction(r):
        return "LONG" if r.get("alignment_trend") == "bullish" else "SHORT"
    return _signal_rate(rows, sig, direction)


def edge_pdh_pdl_reject(rows):
    """Price rejects PDH or PDL (sweep then reversal), regardless of H1 bias."""
    def sig(r):
        return r.get("sweep_pdh") or r.get("sweep_pdl")

    def direction(r):
        if r.get("sweep_pdh"):
            return "SHORT"
        return "LONG"
    return _signal_rate(rows, sig, direction)


def edge_asian_range_break(rows):
    """Sweep of Asian session high/low with displacement."""
    def sig(r):
        if not r.get("displacement_high"):
            return False
        return r.get("sweep_asian_hi") or r.get("sweep_asian_lo")

    def direction(r):
        if r.get("sweep_asian_hi"):
            return "SHORT"
        return "LONG"
    return _signal_rate(rows, sig, direction)


def summarize(hits, wins, n, label, baseline_wr=0.5):
    losses = n - wins
    wr = wins / n if n else None
    exp_r = (wins * 1.5 - losses * 1.0) / n if n else None
    p_raw = _sig_test_prop(wins, n, null_p=baseline_wr) if n >= 10 else None
    return {
        "label": label,
        "n": n,
        "w": wins,
        "l": losses,
        "wr": wr,
        "exp_r": exp_r,
        "p_raw_vs_null": p_raw,
        "null_p": baseline_wr,
    }


def per_instrument_edge(rows_by_inst, edge_fn, label, baseline_wr=0.5):
    out = {}
    for inst, rows in rows_by_inst.items():
        hits, wins, n = edge_fn(rows)
        out[inst] = summarize(hits, wins, n, label, baseline_wr)
    return out


def hour_of_day_win_rates(rows_by_inst):
    """Per-instrument, per-hour: LONG win rate and SHORT win rate (without any signal)."""
    out = {}
    for inst, rows in rows_by_inst.items():
        per_hour = defaultdict(lambda: {"n": 0, "long_resolved": 0, "long_wins": 0,
                                        "short_resolved": 0, "short_wins": 0})
        for r in rows:
            h = r.get("hour_utc")
            per_hour[h]["n"] += 1
            if r["long_outcome"] in ("WIN", "LOSS"):
                per_hour[h]["long_resolved"] += 1
                if r["long_outcome"] == "WIN":
                    per_hour[h]["long_wins"] += 1
            if r["short_outcome"] in ("WIN", "LOSS"):
                per_hour[h]["short_resolved"] += 1
                if r["short_outcome"] == "WIN":
                    per_hour[h]["short_wins"] += 1
        out[inst] = {h: dict(d) for h, d in per_hour.items()}
    return out


def main():
    # Scan every 4th M15 candle (every hour) to keep runtime reasonable but still big n
    # Actually, every candle is fine — we already scan ~6000 per symbol × 7 symbols = 42k total.
    # Setting sample_step=2 halves it to ~21k, still plenty.
    rows_by_inst = {}
    for sym in INSTRUMENTS:
        rows_by_inst[sym] = scan_symbol(sym, sample_step=1)

    # Save all rows (lean version) for further analysis
    all_rows_lean = []
    for inst, rows in rows_by_inst.items():
        for r in rows:
            all_rows_lean.append({
                "symbol": r["symbol"],
                "candle_time": str(r["candle_time"]),
                "hour_utc": r["hour_utc"],
                "kz": r["kz"],
                "day_of_week": r["day_of_week"],
                "d1_dir": r["d1_dir"],
                "h4_dir": r["h4_dir"],
                "h1_dir": r["h1_dir"],
                "alignment_trend": r["alignment_trend"],
                "fvg_m15": r["fvg_m15"],
                "displacement_atr": r["displacement_atr"],
                "displacement_high": r["displacement_high"],
                "sweep_pdh": r["sweep_pdh"],
                "sweep_pdl": r["sweep_pdl"],
                "sweep_asian_hi": r["sweep_asian_hi"],
                "sweep_asian_lo": r["sweep_asian_lo"],
                "sweep_london_hi": r["sweep_london_hi"],
                "sweep_london_lo": r["sweep_london_lo"],
                "fib50_dist_atr": r["fib50_dist_atr"],
                "pd_frac": r["pd_frac"],
                "long_outcome": r["long_outcome"],
                "short_outcome": r["short_outcome"],
                "winner": r["winner"],
            })
    with open(OUT_DIR / "all_candles_features_outcomes.json", "w", encoding="utf-8") as f:
        json.dump({"n": len(all_rows_lean), "rows": all_rows_lean}, f, default=str)

    # Baseline directional WR per instrument
    baselines = {}
    for inst, rows in rows_by_inst.items():
        baselines[inst] = _base_directional_winrate(rows)

    # Edge tests per instrument
    edge_funcs = [
        ("fvg_only_h1_aligned", edge_fvg_only),
        ("sweep_displacement_h1_aligned", edge_sweep_displacement),
        ("fib50_equilibrium_d1_aligned", edge_fib50_d1),
        ("triple_align_d1_h4_h1", edge_triple_align),
        ("triple_align_plus_fvg", edge_triple_align_plus_fvg),
        ("triple_align_plus_sweep", edge_triple_align_plus_sweep),
        ("pdh_pdl_reject", edge_pdh_pdl_reject),
        ("asian_range_break", edge_asian_range_break),
    ]
    edges = {}
    for name, fn in edge_funcs:
        # Compute per-instrument, using the instrument's OWN baseline as the null
        per_inst = {}
        for inst, rows in rows_by_inst.items():
            hits, wins, n = fn(rows)
            # Use per-inst baseline LONG or SHORT WR depending on the direction mix
            # Simpler: use the overall per-inst LONG WR (they're close to SHORT)
            null_p = 0.5
            b = baselines[inst]
            if b["wr_long"] is not None and b["wr_short"] is not None:
                null_p = (b["wr_long"] + b["wr_short"]) / 2
            per_inst[inst] = summarize(hits, wins, n, name, baseline_wr=null_p)
        # Combined: pool all instruments
        all_hits = 0
        all_wins = 0
        for inst, rows in rows_by_inst.items():
            _, w, n = fn(rows)
            all_hits += n
            all_wins += w
        # Combined null: weighted average baseline
        all_null = sum(((baselines[i]["wr_long"] or 0.5) + (baselines[i]["wr_short"] or 0.5)) / 2
                       * len(rows_by_inst[i]) for i in rows_by_inst) / sum(len(rows_by_inst[i]) for i in rows_by_inst)
        combined = summarize([], all_wins, all_hits, name, baseline_wr=all_null)
        edges[name] = {"combined": combined, "per_instrument": per_inst}

    # Bonferroni — 8 edges × 7 instruments
    all_ps = []
    for name, e in edges.items():
        for inst, s in e["per_instrument"].items():
            if s["p_raw_vs_null"] is not None:
                all_ps.append((name, inst, s["p_raw_vs_null"]))
    k = len(all_ps)
    bonf_map = {(n, i): min(1.0, p * k) for n, i, p in all_ps}
    for name, e in edges.items():
        for inst, s in e["per_instrument"].items():
            s["p_bonferroni"] = bonf_map.get((name, inst))

    # Hour-of-day tables
    hod = hour_of_day_win_rates(rows_by_inst)

    out = {
        "instruments": INSTRUMENTS,
        "baselines": baselines,
        "edges": edges,
        "hour_of_day": hod,
        "n_bonferroni_family": k,
    }
    with open(OUT_DIR / "full_scan_output.json", "w", encoding="utf-8") as f:
        json.dump(out, f, default=str, indent=2)

    # Print summary
    print("\n=== BASELINES (directional WR with no signal) ===")
    for inst, b in baselines.items():
        wrl = b["wr_long"]
        wrs = b["wr_short"]
        print(f"  {inst}: wr_long={wrl:.3f} (n={b['n_long_resolved']})  wr_short={wrs:.3f} (n={b['n_short_resolved']})")

    print("\n=== EDGES ===")
    for name, e in edges.items():
        c = e["combined"]
        wr_c = c["wr"] if c["wr"] is not None else 0.0
        expr_c = c["exp_r"] if c["exp_r"] is not None else 0.0
        print(f"\n  [{name}] combined: n={c['n']} wr={wr_c:.3f} expR={expr_c:.3f}")
        for inst, s in e["per_instrument"].items():
            wr = s["wr"] if s["wr"] is not None else 0
            expr = s["exp_r"] if s["exp_r"] is not None else 0
            pb = s.get("p_bonferroni")
            pbstr = f"{pb:.4f}" if pb is not None else "na"
            pr = s.get("p_raw_vs_null")
            prstr = f"{pr:.4f}" if pr is not None else "na"
            print(f"    {inst}: n={s['n']:5d} wr={wr:.3f} expR={expr:.3f} nullWR={s['null_p']:.3f} p_raw={prstr} p_bonf={pbstr}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 3 T2 — XAUUSD Root-Cause Discriminator.

Goal: narrow the 5-candidate hypothesis set using:
  - Option B: Cross-instrument discrimination (detector/prompt bugs should affect
    US30/USDJPY/GBPJPY equally; regime change and arbitrage are XAUUSD-specific).
  - Supporting: volatility regime shift direct measurement from M15 CSV.

Critical invariant: all backtest sessions were generated in a single batch run
on 2026-04-04 (verified by file mtimes). This means 2024 vs 2026 trades were
all evaluated with the SAME model + SAME prompt + SAME detector code. Therefore
any 2024-vs-2026 delta in trade outcomes isolates MARKET behavior, not code.

Tests:
  T1. Cross-instrument winner-MFE compression 2025 vs 2026 (MW U).
  T2. Cross-instrument fast-loss rate shift 2025 vs 2026 (Fisher exact).
  T3. Cross-instrument bad-entry rate shift 2025 vs 2026 (proportion test).
  T4. CANDIDATE rate shift 2024/25 vs 2026 per instrument.
  T5. Direct volatility regime measurement per instrument (M15 CSV).

Output: written to stdout + saved to _T2_output.json.
"""
import csv
import glob
import json
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
OUT = Path(r"C:/Users/MSI/Documents/ai-trading-agent/research/b_deep_audit_2026-04-19/phase3/_T2_scratch")
OUT.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD", "NZDUSD"]


def fisher_exact_2sided(a, b, c, d):
    """Two-sided Fisher exact test."""
    from math import comb
    n1, n2 = a + b, c + d
    total = a + b + c + d
    if total == 0 or total > 1000:
        return None
    col1 = a + c
    obs_p = comb(n1, a) * comb(n2, c) / comb(total, col1)
    p_sum = 0.0
    for k in range(max(0, col1 - n2), min(n1, col1) + 1):
        a_ = k
        b_ = n1 - a_
        c_ = col1 - a_
        d_ = n2 - c_
        if a_ < 0 or b_ < 0 or c_ < 0 or d_ < 0:
            continue
        pk = comb(n1, a_) * comb(n2, c_) / comb(total, col1)
        if pk <= obs_p + 1e-15:
            p_sum += pk
    return min(1.0, p_sum)


def mw_u_p(a, b):
    """Two-sided Mann-Whitney U via normal approximation."""
    if len(a) < 5 or len(b) < 5:
        return None
    combined = [(v, 0) for v in a] + [(v, 1) for v in b]
    combined.sort(key=lambda x: x[0])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r_a = sum(ranks[i] for i, (_, g) in enumerate(combined) if g == 0)
    n1, n2 = len(a), len(b)
    u_a = r_a - n1 * (n1 + 1) / 2
    u = min(u_a, n1 * n2 - u_a)
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sigma == 0:
        return None
    z = (u - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return p


def load_all_trades():
    """Load backtest trades for all symbols."""
    all_trades = {}
    for sym in SYMBOLS:
        base = ROOT / "knowledge_base_backtest" / "sessions" / sym
        if not base.exists():
            continue
        trades = []
        for fn in sorted(base.glob("*.json")):
            with open(fn, encoding="utf-8") as f:
                d = json.load(f)
            ts = d.get("trade_summary", {})
            if not ts.get("trade_taken"):
                continue
            for t in ts.get("trades", []):
                t2 = dict(t)
                t2["date"] = d.get("date")
                trades.append(t2)
        all_trades[sym] = trades
    return all_trades


def load_candidate_rates():
    """Count CANDIDATEs per year per symbol."""
    out = {}
    for sym in SYMBOLS:
        base = ROOT / "knowledge_base_backtest" / "sessions" / sym
        if not base.exists():
            continue
        by_year_c = defaultdict(int)
        by_year_n = defaultdict(int)
        for fn in sorted(base.glob("*.json")):
            y = fn.name[:4]
            with open(fn, encoding="utf-8") as f:
                d = json.load(f)
            evals = d.get("candle_evaluations", [])
            by_year_n[y] += len(evals)
            by_year_c[y] += sum(1 for e in evals if e.get("decision") == "CANDIDATE")
        out[sym] = {y: {"n_eval": by_year_n[y], "n_cand": by_year_c[y],
                        "rate": by_year_c[y] / by_year_n[y] if by_year_n[y] else 0}
                    for y in sorted(by_year_c.keys())}
    return out


def compute_volatility_regime():
    """Per-instrument M15 %-range over time."""
    out = {}
    # Maps symbol to file path
    # Data dir may have either historical/{sym}_M15.csv or data/{sym}_M15.csv
    file_candidates = {
        "XAUUSD": "data/historical/XAUUSD_M15.csv",
        "EURUSD": "data/historical/EURUSD_M15.csv",
        "GBPUSD": "data/historical/GBPUSD_M15.csv",
        "GBPJPY": "data/historical/GBPJPY_M15.csv",
        "NZDUSD": "data/historical/NZDUSD_M15.csv",
        "US30_cash": "data/historical/US30_cash_M15.csv",
    }
    # Also try data/{sym}_M15.csv if missing
    for sym, p in file_candidates.items():
        fp = ROOT / p
        if not fp.exists():
            alt = ROOT / f"data/{sym}_M15.csv"
            if alt.exists():
                fp = alt
            else:
                continue
        by_ym_rng = defaultdict(list)
        by_ym_pct = defaultdict(list)
        try:
            with open(fp, encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                    ym = t.strftime("%Y-%m")
                    hi = float(row["high"])
                    lo = float(row["low"])
                    cl = float(row["close"])
                    by_ym_rng[ym].append(hi - lo)
                    by_ym_pct[ym].append((hi - lo) / cl if cl else 0)
        except Exception as e:
            print(f"Error loading {fp}: {e}")
            continue
        # Compare earliest 6 months to 2026-Q1 (if available)
        times = sorted(by_ym_rng.keys())
        if not times:
            continue
        first = times[0]
        first_pct = statistics.median(by_ym_pct[first]) * 10000  # bp
        q1_2026_months = [t for t in times if t.startswith("2026-0") and t[-2:] in ("01", "02", "03")]
        if q1_2026_months:
            late_vals = []
            for m in q1_2026_months:
                late_vals.extend(by_ym_pct[m])
            late_pct = statistics.median(late_vals) * 10000
        else:
            late_pct = statistics.median(by_ym_pct[times[-1]]) * 10000
        out[sym] = {
            "first_month": first,
            "first_pct_range_bp": first_pct,
            "q1_2026_pct_range_bp": late_pct,
            "volatility_regime_ratio": late_pct / first_pct if first_pct else None,
        }
    return out


def run():
    print("=" * 80)
    print("PHASE 3 T2 — XAUUSD ROOT-CAUSE DISCRIMINATOR")
    print("=" * 80)
    print("Critical invariant: ALL backtest sessions generated 2026-04-04 batch.")
    print("Therefore 2024-vs-2026 deltas isolate MARKET behavior (code held const).")
    print()

    all_trades = load_all_trades()
    for sym, t in all_trades.items():
        print(f"{sym}: n_trades={len(t)}")
    print()

    # ==================================================================
    # Test 1 — Cross-instrument winner MFE compression 2025 vs 2026
    # ==================================================================
    print("-" * 80)
    print("T1: Winner MFE (median R) — 2025 vs 2026 by instrument")
    print("Mann-Whitney U (two-sided); n_min=5 for each side")
    print(f'{"Sym":<10} {"25_n":>5} {"25_med":>8} {"26_n":>5} {"26_med":>8} {"MW_p":>10} {"verdict":>12}')
    t1_results = {}
    for sym, trades in all_trades.items():
        w_25 = [t.get("mfe_r") for t in trades if t.get("date", "")[:4] == "2025"
                and t.get("outcome") == "WIN" and t.get("mfe_r") is not None]
        w_26 = [t.get("mfe_r") for t in trades if t.get("date", "")[:4] == "2026"
                and t.get("outcome") == "WIN" and t.get("mfe_r") is not None]
        if len(w_25) < 5 or len(w_26) < 5:
            verdict = "n_insuf"
            p = None
            med_25 = statistics.median(w_25) if w_25 else 0
            med_26 = statistics.median(w_26) if w_26 else 0
        else:
            p = mw_u_p(w_25, w_26)
            med_25 = statistics.median(w_25)
            med_26 = statistics.median(w_26)
            if p is not None and p < 0.05 and med_26 < med_25:
                verdict = "COMPRESS"
            elif p is not None and p < 0.05 and med_26 > med_25:
                verdict = "EXPAND"
            else:
                verdict = "no-sig"
        t1_results[sym] = {
            "25_n": len(w_25), "25_med": med_25,
            "26_n": len(w_26), "26_med": med_26,
            "mw_p": p, "verdict": verdict,
        }
        p_str = f"{p:.4f}" if p is not None else "NA"
        print(f'{sym:<10} {len(w_25):>5} {med_25:>8.2f} {len(w_26):>5} {med_26:>8.2f} {p_str:>10} {verdict:>12}')
    print()

    # ==================================================================
    # Test 2 — Cross-instrument fast-loss rate 2025 vs 2026
    # ==================================================================
    print("-" * 80)
    print("T2: Fast-loss rate (losses with MFE < 0.3R) — 2025 vs 2026")
    print("Fisher exact 2-sided")
    print(f'{"Sym":<10} {"25_nL":>5} {"25_FL":>5} {"26_nL":>5} {"26_FL":>5} {"fisher_p":>10} {"verdict":>12}')
    t2_results = {}
    for sym, trades in all_trades.items():
        l_25 = [t for t in trades if t.get("date", "")[:4] == "2025"
                and t.get("outcome") == "LOSS" and t.get("mfe_r") is not None]
        l_26 = [t for t in trades if t.get("date", "")[:4] == "2026"
                and t.get("outcome") == "LOSS" and t.get("mfe_r") is not None]
        fl_25 = sum(1 for t in l_25 if t["mfe_r"] < 0.3)
        fl_26 = sum(1 for t in l_26 if t["mfe_r"] < 0.3)
        if len(l_25) + len(l_26) < 5:
            p = None
            verdict = "n_insuf"
        else:
            p = fisher_exact_2sided(fl_25, len(l_25) - fl_25, fl_26, len(l_26) - fl_26)
            # Directional
            p_25 = fl_25 / len(l_25) if l_25 else 0
            p_26 = fl_26 / len(l_26) if l_26 else 0
            if p is not None and p < 0.05:
                verdict = "FASTER" if p_26 > p_25 else "SLOWER"
            else:
                verdict = "no-sig"
        t2_results[sym] = {
            "25_n": len(l_25), "25_fl": fl_25,
            "26_n": len(l_26), "26_fl": fl_26,
            "fisher_p": p, "verdict": verdict,
        }
        p_str = f"{p:.4f}" if p is not None else "NA"
        print(f'{sym:<10} {len(l_25):>5} {fl_25:>5} {len(l_26):>5} {fl_26:>5} {p_str:>10} {verdict:>12}')
    print()

    # ==================================================================
    # Test 3 — Bad-entry rate (α's signature) 2025 vs 2026
    # ==================================================================
    print("-" * 80)
    print("T3: Bad-entry rate (ALL trades with MFE < 0.2R) — 2025 vs 2026")
    print("Fisher exact 2-sided")
    print(f'{"Sym":<10} {"25_n":>5} {"25_BE":>5} {"25_%":>6} {"26_n":>5} {"26_BE":>5} {"26_%":>6} {"fisher_p":>10} {"verdict":>12}')
    t3_results = {}
    for sym, trades in all_trades.items():
        t_25 = [t for t in trades if t.get("date", "")[:4] == "2025" and t.get("mfe_r") is not None]
        t_26 = [t for t in trades if t.get("date", "")[:4] == "2026" and t.get("mfe_r") is not None]
        be_25 = sum(1 for t in t_25 if t["mfe_r"] < 0.2)
        be_26 = sum(1 for t in t_26 if t["mfe_r"] < 0.2)
        if not t_25 or not t_26:
            p = None
            verdict = "n_insuf"
            p_25 = p_26 = 0
        else:
            p = fisher_exact_2sided(be_25, len(t_25) - be_25, be_26, len(t_26) - be_26)
            p_25 = be_25 / len(t_25) * 100
            p_26 = be_26 / len(t_26) * 100
            if p is not None and p < 0.05:
                verdict = "WORSE" if p_26 > p_25 else "BETTER"
            else:
                verdict = "no-sig"
        t3_results[sym] = {
            "25_n": len(t_25), "25_be": be_25, "25_pct": p_25,
            "26_n": len(t_26), "26_be": be_26, "26_pct": p_26,
            "fisher_p": p, "verdict": verdict,
        }
        p_str = f"{p:.4f}" if p is not None else "NA"
        print(f'{sym:<10} {len(t_25):>5} {be_25:>5} {p_25:>5.1f}% {len(t_26):>5} {be_26:>5} {p_26:>5.1f}% {p_str:>10} {verdict:>12}')
    print()

    # ==================================================================
    # Test 4 — CANDIDATE rate shift 2024/25 vs 2026
    # ==================================================================
    print("-" * 80)
    print("T4: CANDIDATE rate 2025 vs 2026 per instrument")
    cand_rates = load_candidate_rates()
    t4_results = {}
    print(f'{"Sym":<10} {"25_eval":>8} {"25_cand":>8} {"25_%":>6} {"26_eval":>8} {"26_cand":>8} {"26_%":>6} {"delta":>6}')
    for sym in cand_rates:
        d25 = cand_rates[sym].get("2025", {})
        d26 = cand_rates[sym].get("2026", {})
        r_25 = d25.get("rate", 0) * 100
        r_26 = d26.get("rate", 0) * 100
        delta = r_26 - r_25
        t4_results[sym] = {
            "25_eval": d25.get("n_eval", 0), "25_cand": d25.get("n_cand", 0), "25_pct": r_25,
            "26_eval": d26.get("n_eval", 0), "26_cand": d26.get("n_cand", 0), "26_pct": r_26,
            "delta_pp": delta,
        }
        print(f'{sym:<10} {d25.get("n_eval",0):>8} {d25.get("n_cand",0):>8} {r_25:>5.1f}% {d26.get("n_eval",0):>8} {d26.get("n_cand",0):>8} {r_26:>5.1f}% {delta:+5.1f}')
    print()

    # ==================================================================
    # Test 5 — Volatility regime shift per instrument
    # ==================================================================
    print("-" * 80)
    print("T5: Volatility regime — median M15 %-range")
    vol = compute_volatility_regime()
    print(f'{"Sym":<10} {"first":>8} {"first_bp":>10} {"2026Q1_bp":>10} {"ratio":>6}')
    for sym, d in vol.items():
        fr = d.get("first_month")
        fp = d.get("first_pct_range_bp", 0)
        lp = d.get("q1_2026_pct_range_bp", 0)
        r = d.get("volatility_regime_ratio") or 0
        print(f'{sym:<10} {fr:>8} {fp:>9.2f}bp {lp:>9.2f}bp {r:>5.2f}x')
    print()

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 80)
    print("DISCRIMINATION SUMMARY")
    print("=" * 80)
    summary = {
        "T1_winner_mfe": t1_results,
        "T2_fast_loss": t2_results,
        "T3_bad_entry": t3_results,
        "T4_candidate_rate": t4_results,
        "T5_volatility_regime": vol,
    }

    # Which instruments show XAUUSD-like degradation?
    print()
    print("Which instruments show the full XAUUSD degradation signature?")
    print("(Winner MFE compression AND fast-loss increase AND bad-entry increase)")
    for sym in all_trades:
        t1v = t1_results[sym]["verdict"]
        t2v = t2_results[sym]["verdict"]
        t3v = t3_results[sym]["verdict"]
        compressed = t1v == "COMPRESS"
        faster = t2v == "FASTER" or (t2_results[sym]["25_fl"] / max(1, t2_results[sym]["25_n"]) <
                                     t2_results[sym]["26_fl"] / max(1, t2_results[sym]["26_n"]))
        bad_entry_up = t3v == "WORSE"
        match = sum([compressed, faster, bad_entry_up])
        print(f"  {sym:<10} winnerMFE={t1v:<10} fastLoss={t2v:<10} badEntry={t3v:<10} match={match}/3")

    # Save
    with open(OUT / "_T2_output.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print()
    print(f"Full output: {OUT / '_T2_output.json'}")


if __name__ == "__main__":
    run()

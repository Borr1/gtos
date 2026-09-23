"""Cross-instrument class-bias data mining.

Mines all Tier 2 backtests + a1/a2 backtests + Tier 1 reports + production
trade records for evidence on the class-bias hypothesis (metals/JPY help, indices/tight-FX hurt).

$0 API. Pure Python.
"""
from __future__ import annotations

import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TIER2_DIR = ROOT / "research" / "instrument_expansion_2026-04-25"
A1_DIR = ROOT / "research" / "a1_adr005_backtest"
A2_DIR = ROOT / "research" / "a2_v2_active_backtest"
PHASE1_DIR = ROOT / "research" / "phase1_full_extraction"
TRADE_RECORDS = ROOT / "knowledge_base" / "trade_records"

# -----------------------------
# Asset class taxonomy
# -----------------------------
CLASS_OF = {
    "XAUUSD": "metals",
    "XAGUSD": "metals",
    "USDJPY": "jpy_pairs",
    "GBPJPY": "jpy_pairs",
    "EURJPY": "jpy_pairs",
    "AUDJPY": "jpy_pairs",
    "CHFJPY": "jpy_pairs",
    "GBPUSD": "tight_fx",
    "EURUSD": "tight_fx",
    "AUDUSD": "tight_fx",
    "NZDUSD": "tight_fx",
    "USDCHF": "tight_fx",
    "USDCAD": "tight_fx",
    "EURGBP": "tight_fx",
    "US30_cash": "indices",
    "US30": "indices",
    "NAS100": "indices",
    "GER40": "indices",
    "UK100": "indices",
    "SPX500": "indices",
    "JP225": "indices",
    "BTCUSD": "crypto",
    "ETHUSD": "crypto",
    "USOIL_cash": "energy",
    "UKOIL_cash": "energy",
}

# -----------------------------
# Stats helpers
# -----------------------------
def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def two_proportion_z_p(w1: int, n1: int, w2: int, n2: int) -> float:
    """Two-proportion z-test, return two-sided p (raw)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = w1 / n1, w2 / n2
    p = (w1 + w2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    # two-sided
    return 2 * (1 - _normal_cdf(abs(z)))


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# -----------------------------
# Tier 2 mining
# -----------------------------
TIER2_INSTRUMENTS = ["xagusd", "ger40", "uk100", "eurusd", "nas100"]


def load_tier2_slice(symbol_dir: str) -> list[dict[str, Any]]:
    """Load all CAND results from all slices for a symbol."""
    sdir = TIER2_DIR / f"tier2_{symbol_dir}"
    rows: list[dict[str, Any]] = []
    if not sdir.exists():
        return rows
    # Sort numerically: s1 ... s12 (some have s01 ... s12; deduplicate)
    seen_paths: set[Path] = set()
    slice_dirs = sorted(
        [d for d in sdir.iterdir() if d.is_dir() and re.match(r"s\d+", d.name)],
        key=lambda p: int(re.match(r"s(\d+)", p.name).group(1)),
    )
    # Dedupe: prefer s1 over s01, s2 over s02, etc.
    # Actually some symbols only have s1-s7 (no s01 series). Let's be careful.
    deduped = {}
    for sd in slice_dirs:
        n = int(re.match(r"s(\d+)", sd.name).group(1))
        if n in deduped:
            # Prefer the shorter name (s1 over s01) — same number.
            if len(sd.name) < len(deduped[n].name):
                deduped[n] = sd
        else:
            deduped[n] = sd
    for n in sorted(deduped):
        sd = deduped[n]
        ar = sd / "all_results.json"
        if not ar.exists():
            continue
        if ar in seen_paths:
            continue
        seen_paths.add(ar)
        try:
            with open(ar, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        for r in data.get("results", []):
            r["_slice"] = sd.name
            rows.append(r)
    return rows


# -----------------------------
# Live trade records
# -----------------------------
def load_live_trade_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not TRADE_RECORDS.exists():
        return rows
    for sym_dir in TRADE_RECORDS.iterdir():
        if not sym_dir.is_dir():
            continue
        for f in sym_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fh:
                    rec = json.load(fh)
                rec["_symbol"] = sym_dir.name
                rec["_file"] = f.name
                rows.append(rec)
            except Exception:
                continue
    return rows


# -----------------------------
# Per-instrument summary
# -----------------------------
def summarise_results(symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    cands = [r for r in rows if r.get("decision") == "CANDIDATE"]
    filled = [r for r in cands if r.get("outcome") in ("WIN", "LOSS")]
    rejected_l2 = [r for r in rows if str(r.get("decision", "")).upper() in ("REJECTED_L2",)]
    blocked = [r for r in rows if str(r.get("decision", "")).upper() in ("BLOCKED_LIMIT", "BLOCKED")]
    no_trade = [r for r in rows if r.get("decision") == "NO_TRADE"]
    parse_err = [r for r in rows if r.get("decision") == "PARSE_ERROR"]

    wins = sum(1 for r in filled if r.get("outcome") == "WIN")
    losses = sum(1 for r in filled if r.get("outcome") == "LOSS")
    n = len(filled)
    wr = wins / n if n else 0.0
    wci = wilson_ci(wins, n)

    rs = [r.get("r_multiple", 0.0) or 0.0 for r in filled]
    total_r = sum(rs)
    exp_r = total_r / n if n else 0.0

    # Per direction
    long_filled = [r for r in filled if r.get("direction") == "LONG"]
    short_filled = [r for r in filled if r.get("direction") == "SHORT"]
    long_wins = sum(1 for r in long_filled if r.get("outcome") == "WIN")
    short_wins = sum(1 for r in short_filled if r.get("outcome") == "WIN")
    long_n, short_n = len(long_filled), len(short_filled)
    long_wr = long_wins / long_n if long_n else 0.0
    short_wr = short_wins / short_n if short_n else 0.0
    long_ci = wilson_ci(long_wins, long_n)
    short_ci = wilson_ci(short_wins, short_n)

    # Per framework
    fw = Counter(r.get("framework", "ob_retest") for r in filled)
    by_fw = defaultdict(lambda: {"n": 0, "wins": 0, "total_r": 0.0})
    for r in filled:
        fwk = r.get("framework", "ob_retest")
        by_fw[fwk]["n"] += 1
        if r.get("outcome") == "WIN":
            by_fw[fwk]["wins"] += 1
        by_fw[fwk]["total_r"] += r.get("r_multiple", 0.0) or 0.0

    by_fw_summary = {}
    for fw_name, st in by_fw.items():
        nfw = st["n"]
        wr_fw = st["wins"] / nfw if nfw else 0.0
        ci_fw = wilson_ci(st["wins"], nfw)
        by_fw_summary[fw_name] = {
            "n": nfw,
            "wins": st["wins"],
            "wr": wr_fw,
            "wr_ci": ci_fw,
            "exp_r": st["total_r"] / nfw if nfw else 0.0,
            "total_r": st["total_r"],
        }

    return {
        "symbol": symbol,
        "n_records": len(rows),
        "n_cands": len(cands),
        "n_filled": n,
        "n_rejected_l2": len(rejected_l2),
        "n_blocked_limit": len(blocked),
        "n_no_trade": len(no_trade),
        "n_parse_err": len(parse_err),
        "wins": wins,
        "losses": losses,
        "wr": wr,
        "wr_ci": wci,
        "exp_r": exp_r,
        "total_r": total_r,
        "long_n": long_n,
        "long_wr": long_wr,
        "long_wr_ci": long_ci,
        "short_n": short_n,
        "short_wr": short_wr,
        "short_wr_ci": short_ci,
        "by_framework": by_fw_summary,
    }


# -----------------------------
# Mechanical OB-retest WR baselines (from 01_STRUCTURAL_SCREEN)
# -----------------------------
MECH_OB_WR = {
    "BTCUSD": (89, 55, 0.618),
    "UK100": (74, 45, 0.608),
    "NZDUSD": (73, 44, 0.603),
    "XAGUSD": (67, 40, 0.597),
    "GER40": (69, 41, 0.594),
    "JP225": (69, 40, 0.580),
    "USDCHF": (85, 48, 0.565),
    "XAUUSD": (62, 35, 0.571),
    "GBPJPY": (80, 44, 0.557),
    "US30_cash": (68, 37, 0.544),
    "SPX500": (62, 33, 0.532),
    "AUDJPY": (74, 40, 0.541),
    "NAS100": (64, 34, 0.531),
    "ETHUSD": (93, 50, 0.538),
    "AUDUSD": (75, 40, 0.533),
    "CHFJPY": (78, 41, 0.532),
    "EURGBP": (67, 35, 0.522),
    "EURUSD": (63, 32, 0.508),
    "GBPUSD": (66, 31, 0.470),
    "EURJPY": (73, 34, 0.466),
    "USDJPY": (92, 41, 0.446),
    "USDCAD": (71, 28, 0.394),
    "UKOIL_cash": (63, 22, 0.349),
    "USOIL_cash": (53, 14, 0.264),
}

# Microstructure metrics from 01/02/03 reports
DISP_RATE = {
    "BTCUSD": 4.23, "ETHUSD": 4.90, "USDJPY": 4.69, "USDCHF": 5.31,
    "EURGBP": 5.92, "XAGUSD": 7.29, "XAUUSD": 6.50, "AUDJPY": 5.65,
    "EURJPY": 5.69, "GBPJPY": 5.78, "CHFJPY": 5.65, "EURUSD": 5.55,
    "USDCAD": 5.49, "AUDUSD": 5.70, "NZDUSD": 5.56, "UK100": 6.73,
    "GER40": 6.83, "NAS100": 5.71, "SPX500": 6.95, "JP225": 6.05,
    "US30_cash": 6.41, "USOIL_cash": 5.18, "UKOIL_cash": 5.46,
}

FVG_DENSITY = {
    "BTCUSD": 12.18, "ETHUSD": 12.30, "USDJPY": 14.65, "USDCHF": 13.85,
    "EURGBP": 9.73, "XAGUSD": 18.71, "XAUUSD": 16.77, "AUDJPY": 13.85,
    "EURJPY": 13.21, "GBPJPY": 12.02, "CHFJPY": 12.72, "EURUSD": 14.15,
    "USDCAD": 14.02, "AUDUSD": 14.25, "NZDUSD": 13.67, "UK100": 11.96,
    "GER40": 11.32, "NAS100": 11.78, "SPX500": 13.05, "JP225": 12.97,
    "US30_cash": 10.86, "USOIL_cash": 7.62, "UKOIL_cash": 9.19,
}

EQ_RATE = {
    "BTCUSD": 39.3, "ETHUSD": 38.9, "USDJPY": 39.4, "USDCHF": 39.5,
    "EURGBP": 41.6, "XAGUSD": 36.2, "XAUUSD": 36.0, "AUDJPY": 39.7,
    "EURJPY": 39.7, "GBPJPY": 39.5, "CHFJPY": 39.8, "EURUSD": 40.9,
    "USDCAD": 39.7, "AUDUSD": 39.7, "NZDUSD": 39.6, "UK100": 39.4,
    "GER40": 39.5, "NAS100": 39.7, "SPX500": 38.5, "JP225": 39.0,
    "US30_cash": 39.5, "USOIL_cash": 41.7, "UKOIL_cash": 41.4,
}

ROUND_GRAVITY = {
    "USDJPY": 21.12, "GBPJPY": 12.67, "GER40": 11.47, "XAUUSD": 11.36,
    "NZDUSD": 11.09, "CHFJPY": 10.85, "EURGBP": 10.84, "USOIL_cash": 10.80,
    "NAS100": 10.34, "USDCAD": 10.34, "AUDJPY": 10.0, "AUDUSD": 9.5,
    "GBPUSD": 9.0, "JP225": 9.5, "SPX500": 9.0, "UK100": 9.5,
    "US30_cash": 9.0, "EURJPY": 9.5, "EURUSD": 9.0, "USDCHF": 8.5,
    "XAGUSD": 9.0, "ETHUSD": 8.42, "UKOIL_cash": 9.0, "BTCUSD": 7.72,
}

SPREAD_R_COST_PCT = {
    "XAUUSD": 2.25, "US30_cash": 2.26, "GER40": 3.10, "NAS100": 4.40,
    "UKOIL_cash": 5.28, "USOIL_cash": 6.60, "JP225": 6.95, "SPX500": 7.34,
    "UK100": 7.70, "USDJPY": 9.45, "GBPUSD": 12.6, "BTCUSD": 12.2,
    "XAGUSD": 11.7, "GBPJPY": 20.5, "EURJPY": 24.1, "EURUSD": 24.2,
    "ETHUSD": 21.4, "AUDJPY": 25.6, "CHFJPY": 26.3, "USDCAD": 26.8,
    "USDCHF": 26.8, "AUDUSD": 29.9, "EURGBP": 48.8, "NZDUSD": 49.6,
}

TREND_STRENGTH = {
    "BTCUSD": 0.142, "ETHUSD": 0.078, "USDJPY": 0.030, "USDCHF": 0.075,
    "EURGBP": 0.039, "XAGUSD": 0.155, "XAUUSD": 0.061, "AUDJPY": 0.074,
    "EURJPY": 0.080, "GBPJPY": 0.057, "CHFJPY": 0.083, "EURUSD": 0.039,
    "USDCAD": 0.063, "AUDUSD": 0.057, "NZDUSD": 0.044, "UK100": 0.080,
    "GER40": 0.065, "NAS100": 0.068, "SPX500": 0.119, "JP225": 0.059,
    "US30_cash": 0.058, "USOIL_cash": 0.063, "UKOIL_cash": 0.087,
}


# -----------------------------
# Production live snapshots — use F3 / phase1 / a2 numbers from CLAUDE.md
# -----------------------------
# These are F3 12-slice backtest fleet numbers (from Wave 2 v2_shadow and
# A2 v2-active backtest; CLAUDE.md sections 4 and 11).
# F3 was "shadow" but with v2 detector active for SHORT/LONG.
F3_RESULTS = {
    "XAUUSD": {"n_filled": 11, "wins_long": 5, "n_long": 11, "wins_short": 2, "n_short": 2,
               "wr": 11/13 if False else 7/13, "exp_r": 0.0, "total_r": 0.0,
               "note": "F3 raw: SHORT 2/2 = 100%. LONG 5/11 = 45.5%. Combined 7/13 ≈ 53.8%"},
    "USDJPY": {"n_filled": 19, "wins_long": 11, "n_long": 19, "wins_short": 0, "n_short": 0,
               "wr": 11/19, "exp_r": 0.447, "total_r": 8.5,
               "note": "USDJPY 0/426 raw SHORT CANDs in F3 — bull-bias residual"},
}
# A2 v2-active backtest (12 slices)
A2_RESULTS = {
    "XAUUSD": {"n_raw": 13, "n_filled": 11, "wr": 0.4545, "exp_r": 0.136, "total_r": 1.5,
               "long_n": 9, "long_wr": 0.333, "short_n": 2, "short_wr": 1.0},
    "USDJPY": {"n_raw": 24, "n_filled": 19, "wr": 0.5789, "exp_r": 0.447, "total_r": 8.5,
               "long_n": 19, "long_wr": 0.5789, "short_n": 0, "short_wr": 0.0},
}

# CLAUDE.md baseline live WR
LIVE_BASELINE_WR = {
    "XAUUSD": (129, int(round(0.62 * 129)), 0.62),  # 80/129
    "US30_cash": (41, int(round(0.585 * 41)), 0.585),
    "USDJPY": (33, int(round(0.758 * 33)), 0.758),
    "GBPJPY": (42, int(round(0.571 * 42)), 0.571),
}


# -----------------------------
# Run analysis
# -----------------------------
def main() -> None:
    out: dict[str, Any] = {}

    # Tier 2 per-instrument summaries
    tier2_summaries = {}
    tier2_raw_rows = {}
    for s in TIER2_INSTRUMENTS:
        rows = load_tier2_slice(s)
        sym = {"xagusd": "XAGUSD", "ger40": "GER40", "uk100": "UK100",
               "eurusd": "EURUSD", "nas100": "NAS100"}[s]
        tier2_summaries[sym] = summarise_results(sym, rows)
        tier2_raw_rows[sym] = rows
        n_filled = tier2_summaries[sym]["n_filled"]
        n_cands = tier2_summaries[sym]["n_cands"]
        wr = tier2_summaries[sym]["wr"]
        print(f"{sym}: {n_cands} CANDs, {n_filled} filled, WR {wr:.1%}")

    out["tier2"] = tier2_summaries

    # Class-bias summary table
    class_table = []
    # Tier 2 newcomers
    for sym, summ in tier2_summaries.items():
        cls = CLASS_OF.get(sym, "?")
        mech = MECH_OB_WR.get(sym, (0, 0, 0.0))
        ai_wr = summ["wr"]
        mech_wr = mech[2]
        uplift = (ai_wr - mech_wr) * 100  # pp
        ai_wins = summ["wins"]
        ai_n = summ["n_filled"]
        if ai_n > 0:
            # 2-prop z vs mechanical
            p = two_proportion_z_p(ai_wins, ai_n, mech[1], mech[0]) if mech[0] > 0 else 1.0
        else:
            p = 1.0
        class_table.append({
            "symbol": sym,
            "class": cls,
            "mech_n": mech[0],
            "mech_wr": mech_wr,
            "ai_n": ai_n,
            "ai_wins": ai_wins,
            "ai_wr": ai_wr,
            "ai_wr_ci": summ["wr_ci"],
            "ai_exp_r": summ["exp_r"],
            "uplift_pp": uplift,
            "p_uplift": p,
            "n_rejected_l2": summ["n_rejected_l2"],
            "long_n": summ["long_n"],
            "long_wr": summ["long_wr"],
            "long_wr_ci": summ["long_wr_ci"],
            "short_n": summ["short_n"],
            "short_wr": summ["short_wr"],
            "short_wr_ci": summ["short_wr_ci"],
            "by_framework": summ["by_framework"],
        })

    # Tier 2 already-tested: XAUUSD, USDJPY, GBPJPY, GBPUSD, US30 from existing CLAUDE.md
    # We have F3 numbers + A2 numbers + live baseline.
    # For XAUUSD A2 v2-active is the most apples-to-apples (uses production prompt).
    extra = []
    extra.append({
        "symbol": "XAUUSD",
        "class": "metals",
        "mech_n": MECH_OB_WR["XAUUSD"][0],
        "mech_wr": MECH_OB_WR["XAUUSD"][2],
        "ai_n": A2_RESULTS["XAUUSD"]["n_filled"],
        "ai_wins": int(round(A2_RESULTS["XAUUSD"]["wr"] * A2_RESULTS["XAUUSD"]["n_filled"])),
        "ai_wr": A2_RESULTS["XAUUSD"]["wr"],
        "ai_wr_ci": wilson_ci(int(round(A2_RESULTS["XAUUSD"]["wr"] * A2_RESULTS["XAUUSD"]["n_filled"])),
                              A2_RESULTS["XAUUSD"]["n_filled"]),
        "ai_exp_r": A2_RESULTS["XAUUSD"]["exp_r"],
        "uplift_pp": (A2_RESULTS["XAUUSD"]["wr"] - MECH_OB_WR["XAUUSD"][2]) * 100,
        "long_n": A2_RESULTS["XAUUSD"]["long_n"],
        "long_wr": A2_RESULTS["XAUUSD"]["long_wr"],
        "short_n": A2_RESULTS["XAUUSD"]["short_n"],
        "short_wr": A2_RESULTS["XAUUSD"]["short_wr"],
        "source": "A2 v2-active 12-slice",
    })
    extra.append({
        "symbol": "USDJPY",
        "class": "jpy_pairs",
        "mech_n": MECH_OB_WR["USDJPY"][0],
        "mech_wr": MECH_OB_WR["USDJPY"][2],
        "ai_n": A2_RESULTS["USDJPY"]["n_filled"],
        "ai_wins": int(round(A2_RESULTS["USDJPY"]["wr"] * A2_RESULTS["USDJPY"]["n_filled"])),
        "ai_wr": A2_RESULTS["USDJPY"]["wr"],
        "ai_wr_ci": wilson_ci(int(round(A2_RESULTS["USDJPY"]["wr"] * A2_RESULTS["USDJPY"]["n_filled"])),
                              A2_RESULTS["USDJPY"]["n_filled"]),
        "ai_exp_r": A2_RESULTS["USDJPY"]["exp_r"],
        "uplift_pp": (A2_RESULTS["USDJPY"]["wr"] - MECH_OB_WR["USDJPY"][2]) * 100,
        "long_n": A2_RESULTS["USDJPY"]["long_n"],
        "long_wr": A2_RESULTS["USDJPY"]["long_wr"],
        "short_n": A2_RESULTS["USDJPY"]["short_n"],
        "short_wr": A2_RESULTS["USDJPY"]["short_wr"],
        "source": "A2 v2-active 12-slice",
    })
    # GBPJPY, GBPUSD, US30: use live baseline from CLAUDE.md (n=42, n=??, n=41)
    # Their AI-filtered live WR is the production figure; mechanical is from screen.
    extra.append({
        "symbol": "GBPJPY",
        "class": "jpy_pairs",
        "mech_n": MECH_OB_WR["GBPJPY"][0],
        "mech_wr": MECH_OB_WR["GBPJPY"][2],
        "ai_n": LIVE_BASELINE_WR["GBPJPY"][0],
        "ai_wins": LIVE_BASELINE_WR["GBPJPY"][1],
        "ai_wr": LIVE_BASELINE_WR["GBPJPY"][2],
        "ai_wr_ci": wilson_ci(LIVE_BASELINE_WR["GBPJPY"][1], LIVE_BASELINE_WR["GBPJPY"][0]),
        "ai_exp_r": None,
        "uplift_pp": (LIVE_BASELINE_WR["GBPJPY"][2] - MECH_OB_WR["GBPJPY"][2]) * 100,
        "source": "live batch n=42",
    })
    extra.append({
        "symbol": "US30_cash",
        "class": "indices",
        "mech_n": MECH_OB_WR["US30_cash"][0],
        "mech_wr": MECH_OB_WR["US30_cash"][2],
        "ai_n": LIVE_BASELINE_WR["US30_cash"][0],
        "ai_wins": LIVE_BASELINE_WR["US30_cash"][1],
        "ai_wr": LIVE_BASELINE_WR["US30_cash"][2],
        "ai_wr_ci": wilson_ci(LIVE_BASELINE_WR["US30_cash"][1], LIVE_BASELINE_WR["US30_cash"][0]),
        "ai_exp_r": None,
        "uplift_pp": (LIVE_BASELINE_WR["US30_cash"][2] - MECH_OB_WR["US30_cash"][2]) * 100,
        "source": "live batch n=41",
    })
    extra.append({
        "symbol": "XAUUSD_LIVE_BATCH",
        "class": "metals",
        "mech_n": MECH_OB_WR["XAUUSD"][0],
        "mech_wr": MECH_OB_WR["XAUUSD"][2],
        "ai_n": LIVE_BASELINE_WR["XAUUSD"][0],
        "ai_wins": LIVE_BASELINE_WR["XAUUSD"][1],
        "ai_wr": LIVE_BASELINE_WR["XAUUSD"][2],
        "ai_wr_ci": wilson_ci(LIVE_BASELINE_WR["XAUUSD"][1], LIVE_BASELINE_WR["XAUUSD"][0]),
        "ai_exp_r": None,
        "uplift_pp": (LIVE_BASELINE_WR["XAUUSD"][2] - MECH_OB_WR["XAUUSD"][2]) * 100,
        "source": "live batch n=129 (CLAUDE.md)",
    })

    # ======================
    # Class-aggregate
    # ======================
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in class_table + extra:
        by_class[row["class"]].append(row)

    class_aggregate = {}
    for cls, members in by_class.items():
        # Pool wins, n
        total_ai_n = sum(m["ai_n"] for m in members if m["ai_n"])
        total_ai_wins = sum(m["ai_wins"] for m in members if m["ai_wins"])
        total_mech_n = sum(m["mech_n"] for m in members)
        total_mech_wins = sum(int(round(m["mech_wr"] * m["mech_n"])) for m in members)
        ai_wr = total_ai_wins / total_ai_n if total_ai_n else 0.0
        mech_wr = total_mech_wins / total_mech_n if total_mech_n else 0.0
        ai_ci = wilson_ci(total_ai_wins, total_ai_n)
        mech_ci = wilson_ci(total_mech_wins, total_mech_n)
        uplift = (ai_wr - mech_wr) * 100
        # 2-prop z
        p = two_proportion_z_p(total_ai_wins, total_ai_n, total_mech_wins, total_mech_n)
        class_aggregate[cls] = {
            "members": [m["symbol"] for m in members],
            "ai_n": total_ai_n,
            "ai_wins": total_ai_wins,
            "ai_wr": ai_wr,
            "ai_wr_ci": ai_ci,
            "mech_n": total_mech_n,
            "mech_wins": total_mech_wins,
            "mech_wr": mech_wr,
            "mech_wr_ci": mech_ci,
            "uplift_pp": uplift,
            "p_uplift": p,
        }

    out["class_table"] = class_table + extra
    out["class_aggregate"] = class_aggregate

    # ======================
    # GER40 March slice deep dive
    # ======================
    ger40_rows = tier2_raw_rows.get("GER40", [])
    s5_rows = [r for r in ger40_rows if r.get("_slice") == "s5"]
    s5_filled = [r for r in s5_rows if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS")]
    s5_summary = {
        "n_records": len(s5_rows),
        "n_cands": sum(1 for r in s5_rows if r.get("decision") == "CANDIDATE"),
        "n_filled": len(s5_filled),
        "fills": []
    }
    for r in s5_filled:
        s5_summary["fills"].append({
            "candle_time": r.get("candle_time"),
            "kill_zone": r.get("kill_zone"),
            "direction": r.get("direction"),
            "entry": r.get("entry_price"),
            "sl": r.get("stop_loss"),
            "tp1": r.get("take_profit_1"),
            "outcome": r.get("outcome"),
            "realized_r": r.get("r_multiple"),
            "framework": r.get("framework", "ob_retest"),
            "h1_direction": r.get("h1_direction"),
            "setup_grade": r.get("setup_grade"),
            "bias": r.get("bias"),
            "candle_close": r.get("candle_close"),
        })

    out["ger40_s5_diagnosis"] = s5_summary

    # ======================
    # Per-framework cross-instrument
    # ======================
    framework_grid = {}  # (framework, symbol) -> stats
    for sym, summ in tier2_summaries.items():
        for fw, st in summ["by_framework"].items():
            framework_grid[(fw, sym)] = st

    out["framework_grid"] = {f"{fw}|{sym}": st for (fw, sym), st in framework_grid.items()}

    # ======================
    # L2 rejection share per class
    # ======================
    l2_reject = {}
    for sym, summ in tier2_summaries.items():
        cls = CLASS_OF.get(sym, "?")
        n_raw = summ["n_cands"] + summ["n_rejected_l2"]
        share = summ["n_rejected_l2"] / n_raw if n_raw > 0 else 0.0
        l2_reject[sym] = {
            "class": cls,
            "n_cands_kept": summ["n_cands"],
            "n_l2_rejected": summ["n_rejected_l2"],
            "n_raw_setups": n_raw,
            "l2_reject_share": share,
        }
    out["l2_rejection"] = l2_reject

    # ======================
    # NO_TRADE reason analysis (look for class-bias hints)
    # ======================
    no_trade_reasons_by_class: dict[str, Counter] = defaultdict(Counter)
    for sym, rows in tier2_raw_rows.items():
        cls = CLASS_OF.get(sym, "?")
        for r in rows:
            if r.get("decision") == "NO_TRADE":
                reason = r.get("no_trade_reason", "?")
                # Compress prescreen reasons
                if isinstance(reason, str) and reason.startswith("prescreen:"):
                    reason = "prescreen"
                no_trade_reasons_by_class[cls][reason] += 1

    out["no_trade_reasons_by_class"] = {cls: dict(c.most_common(10))
                                         for cls, c in no_trade_reasons_by_class.items()}

    # ======================
    # Save
    # ======================
    out_path = ROOT / "research" / "per_framework_class_analysis" / "mining_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"\nSaved {out_path}")

    # Print summary table
    print("\n=== CLASS BIAS TABLE ===")
    print(f"{'symbol':<20} {'class':<12} {'mech_wr':>8} {'ai_wr':>8} {'uplift':>10} {'ai_n':>5}")
    for r in class_table + extra:
        print(f"{r['symbol']:<20} {r['class']:<12} "
              f"{r['mech_wr']:>7.1%} {r['ai_wr']:>7.1%} "
              f"{r['uplift_pp']:>+9.1f}pp {r['ai_n']:>5}")

    print("\n=== CLASS AGGREGATE ===")
    for cls, st in class_aggregate.items():
        print(f"{cls:<14} mech {st['mech_wr']:.1%} (n={st['mech_n']}) "
              f"-> AI {st['ai_wr']:.1%} (n={st['ai_n']}) "
              f"uplift {st['uplift_pp']:+.1f}pp p={st['p_uplift']:.3g}")

    print("\n=== GER40 S5 March (8 losses) ===")
    print(f"records={s5_summary['n_records']} cands={s5_summary['n_cands']} filled={s5_summary['n_filled']}")
    for fill in s5_summary["fills"]:
        rr = fill['realized_r'] if fill['realized_r'] is not None else 0.0
        print(f"  {fill['candle_time']} {fill['kill_zone']:<8} {fill['direction']:<5} "
              f"@ {fill['entry']} SL {fill['sl']} -> {fill['outcome']:<5} {rr:+.2f}R "
              f"close@{fill['candle_close']}")


if __name__ == "__main__":
    main()

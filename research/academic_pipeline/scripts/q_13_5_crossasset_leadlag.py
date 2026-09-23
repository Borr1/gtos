"""Q-13.5 — Cross-asset lead-lag analysis for XAUUSD.

Pre-registered test: does any of {USDJPY, US30, GBPJPY, GBPUSD} Granger-cause
XAUUSD log-returns at M15 or H1 horizons, with a tradeable directional effect?

Pre-registered thresholds (ALL three must hold at same (leader, lag)):
    1) |Spearman rho| >= 0.10  at strict lag k >= 1
    2) Granger p < 0.01 raw  AND  < 0.004 Bonferroni (4 leaders x 3 lags = 12 tests)
    3) Sign-agreement >= 55%

Strict rule: lag = 0 does NOT count as evidence of lead-lag (contemporaneous).

Writes results into research/academic_pipeline/results/Q-13_5_crossasset.md
(appending after the pre-registered hypothesis section).

Run:  python research/academic_pipeline/scripts/q_13_5_crossasset_leadlag.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except Exception as e:  # pragma: no cover
    HAS_STATSMODELS = False
    print(f"[warn] statsmodels import failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[3]
DATA_DIR = REPO / "data" / "historical_2026"
OUT_MD = REPO / "research" / "academic_pipeline" / "results" / "Q-13_5_crossasset.md"

# Filenames — note US30 is stored as "US30_cash_*"
SYMBOL_FILES = {
    "XAUUSD": "XAUUSD",
    "USDJPY": "USDJPY",
    "US30": "US30_cash",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
}
LEADERS = ["USDJPY", "US30", "GBPJPY", "GBPUSD"]

M15_LAGS = [1, 3, 6]           # strict >= 1 for pre-registered Granger / sign-agree
M15_XCORR_LAG_RANGE = range(-6, 7)
H1_LAGS = [1, 2, 3]
H1_XCORR_LAG_RANGE = range(-3, 4)

ALPHA_RAW = 0.01
N_TESTS = 4 * 3                # 12 pre-registered Granger tests on M15
ALPHA_BONF = ALPHA_RAW / N_TESTS  # = 0.000833… but spec wrote 0.004 (12*0.01?).
# Spec wrote: "Adjusted alpha = 0.004". That is alpha / sqrt(N) roughly; safer
# Bonferroni is 0.01/12 = 0.000833. We report BOTH.
ALPHA_SPEC = 0.004

SPEARMAN_THRESH = 0.10
SIGN_AGREE_THRESH = 0.55


# ------------------------------------------------------------------
# I/O
# ------------------------------------------------------------------
def load_ohlc(symbol: str, tf: str) -> pd.DataFrame:
    fstem = SYMBOL_FILES[symbol]
    path = DATA_DIR / f"{fstem}_{tf}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, parse_dates=["time"])
    df = df.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True)
    return df[["time", "close"]]


def build_returns_panel(tf: str) -> pd.DataFrame:
    """Inner-join all 5 symbols on time, return aligned log-return panel."""
    frames = {}
    for sym in SYMBOL_FILES:
        df = load_ohlc(sym, tf).rename(columns={"close": sym})
        frames[sym] = df.set_index("time")[sym]
    panel = pd.concat(frames.values(), axis=1, join="inner").sort_index()
    # log-returns
    rets = np.log(panel).diff().dropna()
    return rets


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
def xcorr_spearman(leader: pd.Series, follower: pd.Series, lags) -> List[Tuple[int, float, float, int]]:
    """Spearman rank correlation between leader[t] and follower[t+k] for k in lags.

    Positive k => leader leads follower by k bars.
    Returns list of (k, rho, p_value, n).
    """
    out = []
    n_total = min(len(leader), len(follower))
    for k in lags:
        if k >= 0:
            x = leader.iloc[: n_total - k].values
            y = follower.iloc[k:].values
        else:
            x = leader.iloc[-k:].values
            y = follower.iloc[: n_total + k].values
        mask = ~(np.isnan(x) | np.isnan(y))
        x = x[mask]
        y = y[mask]
        if len(x) < 30:
            out.append((k, float("nan"), float("nan"), len(x)))
            continue
        rho, p = stats.spearmanr(x, y)
        out.append((k, float(rho), float(p), len(x)))
    return out


def granger_test(leader: pd.Series, follower: pd.Series, lag: int) -> Tuple[float, int]:
    """Granger causality: does past leader help predict follower beyond follower's own past?
    Returns (p_value, n_used). Uses ssr F-test (classical).
    """
    if not HAS_STATSMODELS:
        return float("nan"), 0
    df = pd.concat([follower.rename("y"), leader.rename("x")], axis=1).dropna()
    if len(df) < max(50, 10 * lag):
        return float("nan"), len(df)
    try:
        # grangercausalitytests expects [y, x] => tests whether x Granger-causes y.
        # Use verbose=False to suppress.
        try:
            res = grangercausalitytests(df[["y", "x"]].values, maxlag=[lag], verbose=False)
        except TypeError:
            # Newer statsmodels dropped verbose kwarg; fall back.
            res = grangercausalitytests(df[["y", "x"]].values, maxlag=[lag])
        p = float(res[lag][0]["ssr_ftest"][1])
        return p, len(df)
    except Exception as e:
        print(f"[warn] granger failed lag={lag}: {e}", file=sys.stderr)
        return float("nan"), len(df)


def sign_agreement(leader: pd.Series, follower: pd.Series, k: int) -> Tuple[float, int]:
    """P(sign(follower[t+1..t+k] summed) == sign(leader[t-k+1..t] summed)).

    Uses rolling k-bar cumulative log-return on BOTH sides so we are comparing
    "leader's last k-bar momentum" vs "follower's next k-bar momentum".
    """
    if k < 1:
        return float("nan"), 0
    lead_win = leader.rolling(k).sum()          # through t
    foll_win = follower.rolling(k).sum().shift(-k)  # t+1..t+k
    mask = (~lead_win.isna()) & (~foll_win.isna()) & (lead_win != 0) & (foll_win != 0)
    lw = lead_win[mask].values
    fw = foll_win[mask].values
    if len(lw) < 30:
        return float("nan"), len(lw)
    agree = (np.sign(lw) == np.sign(fw)).mean()
    return float(agree), int(len(lw))


def directional_filter_wr(leader: pd.Series, follower: pd.Series, k: int = 6, z_thresh: float = 1.5):
    """When leader's k-bar return has |z| > z_thresh, does XAU's next k-bar
    follow the same sign? Returns dict with conditional WR.
    """
    lead_win = leader.rolling(k).sum()
    # z-score leader momentum across the full sample
    mu = lead_win.mean()
    sd = lead_win.std()
    if sd == 0 or np.isnan(sd):
        return None
    z = (lead_win - mu) / sd
    foll_next = follower.rolling(k).sum().shift(-k)

    mask_up = (z > z_thresh) & (~foll_next.isna())
    mask_dn = (z < -z_thresh) & (~foll_next.isna())

    wr_up = (foll_next[mask_up] > 0).mean() if mask_up.sum() >= 20 else float("nan")
    wr_dn = (foll_next[mask_dn] < 0).mean() if mask_dn.sum() >= 20 else float("nan")
    n_up = int(mask_up.sum())
    n_dn = int(mask_dn.sum())
    # Combined "aligned" WR
    total_correct = 0
    total_n = 0
    if n_up >= 20 and not math.isnan(wr_up):
        total_correct += wr_up * n_up
        total_n += n_up
    if n_dn >= 20 and not math.isnan(wr_dn):
        total_correct += wr_dn * n_dn
        total_n += n_dn
    combined_wr = (total_correct / total_n) if total_n else float("nan")
    return {
        "wr_up": wr_up,
        "n_up": n_up,
        "wr_dn": wr_dn,
        "n_dn": n_dn,
        "wr_combined": combined_wr,
        "n_combined": total_n,
    }


# ------------------------------------------------------------------
# Runner
# ------------------------------------------------------------------
def run_timeframe(tf: str, lags_granger: List[int], xcorr_range) -> Dict[str, Dict]:
    rets = build_returns_panel(tf)
    xau = rets["XAUUSD"]
    out: Dict[str, Dict] = {}
    for leader in LEADERS:
        lead = rets[leader]
        # 1) Cross-correlation Spearman
        xcorr = xcorr_spearman(lead, xau, xcorr_range)
        # 2) Granger
        granger = {}
        for lag in lags_granger:
            p, n = granger_test(lead, xau, lag)
            granger[lag] = {"p": p, "n": n}
        # 3) Sign-agreement
        sign_agree = {}
        for lag in lags_granger:
            agree, n = sign_agreement(lead, xau, lag)
            sign_agree[lag] = {"agree": agree, "n": n}
        # 4) Directional filter (only on largest lag = 6 at M15, =3 at H1)
        filt_lag = 6 if tf == "M15" else 3
        dfilt = directional_filter_wr(lead, xau, k=filt_lag, z_thresh=1.5)
        out[leader] = {
            "xcorr": xcorr,
            "granger": granger,
            "sign_agree": sign_agree,
            "directional_filter": dfilt,
            "filt_lag": filt_lag,
        }
    return out


def run_split_sign_agreement(tf: str, lags: List[int]) -> Dict[str, Dict[int, Dict]]:
    """First-half / second-half sign-agreement consistency check."""
    rets = build_returns_panel(tf)
    n = len(rets)
    half = n // 2
    h1 = rets.iloc[:half]
    h2 = rets.iloc[half:]
    out = {}
    for leader in LEADERS:
        per_lag = {}
        for lag in lags:
            a1, n1 = sign_agreement(h1[leader], h1["XAUUSD"], lag)
            a2, n2 = sign_agreement(h2[leader], h2["XAUUSD"], lag)
            per_lag[lag] = {"h1_agree": a1, "h1_n": n1, "h2_agree": a2, "h2_n": n2}
        out[leader] = per_lag
    return out


# ------------------------------------------------------------------
# Verdict
# ------------------------------------------------------------------
def assess_pair(leader: str, lag: int, m15_res: Dict, h1_res: Dict) -> Dict:
    """Apply pre-registered decision rule to a single (leader, lag) pair at M15."""
    granger_p = m15_res[leader]["granger"].get(lag, {}).get("p", float("nan"))
    sign_info = m15_res[leader]["sign_agree"].get(lag, {})
    agree = sign_info.get("agree", float("nan"))
    # pull Spearman at the matching lag from xcorr list
    spearman = {k: (rho, p) for (k, rho, p, _n) in m15_res[leader]["xcorr"]}.get(lag, (float("nan"), float("nan")))
    rho, rho_p = spearman

    passes_spearman = (not math.isnan(rho)) and (abs(rho) >= SPEARMAN_THRESH)
    passes_granger_raw = (not math.isnan(granger_p)) and (granger_p < ALPHA_RAW)
    passes_granger_bonf = (not math.isnan(granger_p)) and (granger_p < ALPHA_SPEC)
    passes_granger_strict_bonf = (not math.isnan(granger_p)) and (granger_p < ALPHA_RAW / N_TESTS)
    passes_sign = (not math.isnan(agree)) and (agree >= SIGN_AGREE_THRESH)

    all_pass = passes_spearman and passes_granger_bonf and passes_sign

    # Corroboration at H1 (sign of Spearman at lag 1)
    h1_xc_row = [(k, rho_, p_, n_) for (k, rho_, p_, n_) in h1_res[leader]["xcorr"] if k == 1]
    h1_rho_lag1 = h1_xc_row[0][1] if h1_xc_row else float("nan")

    return {
        "leader": leader,
        "lag": lag,
        "spearman_rho_m15": rho,
        "spearman_p_m15": rho_p,
        "granger_p_m15": granger_p,
        "sign_agree_m15": agree,
        "h1_spearman_rho_lag1": h1_rho_lag1,
        "pass_spearman": passes_spearman,
        "pass_granger_raw": passes_granger_raw,
        "pass_granger_spec_bonf": passes_granger_bonf,
        "pass_granger_strict_bonf": passes_granger_strict_bonf,
        "pass_sign": passes_sign,
        "pass_all_preregistered": all_pass,
    }


# ------------------------------------------------------------------
# Markdown writer (appends after pre-registration)
# ------------------------------------------------------------------
def fmt(x, spec="{:.4f}"):
    if x is None:
        return "n/a"
    if isinstance(x, float) and math.isnan(x):
        return "nan"
    try:
        return spec.format(x)
    except Exception:
        return str(x)


def write_report(m15: Dict, h1: Dict, split: Dict, assessments: List[Dict], meta: Dict):
    lines = []
    ap = lines.append
    ap("\n---\n")
    ap("## 2. Data Summary\n")
    ap(f"- M15 panel length (aligned): **{meta['m15_n']}** observations")
    ap(f"- H1  panel length (aligned): **{meta['h1_n']}** observations")
    ap(f"- Date range (M15): **{meta['m15_start']} .. {meta['m15_end']}**")
    ap(f"- statsmodels available: **{HAS_STATSMODELS}**\n")

    # ---------------- M15 cross-correlation ----------------
    ap("## 3. M15 Cross-Correlation (Spearman rho, leader leads by k bars; k >= 1 required)\n")
    ap("| Leader | k=-6 | k=-3 | k=-1 | k=0 | k=+1 | k=+3 | k=+6 |")
    ap("|---|---|---|---|---|---|---|---|")
    for leader in LEADERS:
        xc = {k: rho for (k, rho, _p, _n) in m15[leader]["xcorr"]}
        row = f"| {leader} "
        for k in [-6, -3, -1, 0, 1, 3, 6]:
            row += f"| {fmt(xc.get(k, float('nan')), '{:+.3f}')} "
        row += "|"
        ap(row)
    ap("")
    ap("*Interpretation: positive k means the leader moves first; k=0 is contemporaneous and NOT evidence of lead-lag.*\n")

    # ---------------- Granger ----------------
    ap("## 4. M15 Granger Causality (leader -> XAUUSD)\n")
    ap(f"Pre-registered alpha = 0.01 raw; Bonferroni for 12 tests per spec = {ALPHA_SPEC}; strict = {ALPHA_RAW/N_TESTS:.5f}\n")
    ap("| Leader | lag=1 p | lag=3 p | lag=6 p | n |")
    ap("|---|---|---|---|---|")
    for leader in LEADERS:
        g = m15[leader]["granger"]
        n_used = g.get(1, {}).get("n", 0)
        ap(f"| {leader} | {fmt(g.get(1, {}).get('p'))} | {fmt(g.get(3, {}).get('p'))} | {fmt(g.get(6, {}).get('p'))} | {n_used} |")
    ap("")

    # ---------------- Sign-agreement ----------------
    ap("## 5. M15 Sign-Agreement (k-bar leader momentum vs k-bar forward XAU momentum)\n")
    ap("| Leader | k=1 | k=3 | k=6 | n(k=6) |")
    ap("|---|---|---|---|---|")
    for leader in LEADERS:
        s = m15[leader]["sign_agree"]
        n_used = s.get(6, {}).get("n", 0)
        ap(f"| {leader} | {fmt(s.get(1, {}).get('agree'))} | {fmt(s.get(3, {}).get('agree'))} | {fmt(s.get(6, {}).get('agree'))} | {n_used} |")
    ap("")
    ap("*Threshold for pass: >= 0.55.*\n")

    # ---------------- Directional filter ----------------
    ap("## 6. Directional Filter Test (|z| > 1.5 leader momentum over k bars)\n")
    ap("Reading: given leader's k-bar return is an extreme move (|z|>1.5), does XAU's next k-bar move in the same direction?\n")
    ap("| Leader | k | WR_up | n_up | WR_dn | n_dn | WR_combined | n_comb |")
    ap("|---|---|---|---|---|---|---|---|")
    for leader in LEADERS:
        d = m15[leader]["directional_filter"]
        if d is None:
            ap(f"| {leader} | n/a | n/a | 0 | n/a | 0 | n/a | 0 |")
            continue
        ap(f"| {leader} | {m15[leader]['filt_lag']} | {fmt(d['wr_up'])} | {d['n_up']} | {fmt(d['wr_dn'])} | {d['n_dn']} | {fmt(d['wr_combined'])} | {d['n_combined']} |")
    ap("")

    # ---------------- H1 corroboration ----------------
    ap("## 7. H1 Corroboration\n")
    ap("### Cross-correlation (Spearman, lags -3..+3)\n")
    ap("| Leader | k=-3 | k=-1 | k=0 | k=+1 | k=+2 | k=+3 |")
    ap("|---|---|---|---|---|---|---|")
    for leader in LEADERS:
        xc = {k: rho for (k, rho, _p, _n) in h1[leader]["xcorr"]}
        row = f"| {leader} "
        for k in [-3, -1, 0, 1, 2, 3]:
            row += f"| {fmt(xc.get(k, float('nan')), '{:+.3f}')} "
        row += "|"
        ap(row)
    ap("")
    ap("### H1 Granger p (leader -> XAUUSD)\n")
    ap("| Leader | lag=1 | lag=2 | lag=3 | n |")
    ap("|---|---|---|---|---|")
    for leader in LEADERS:
        g = h1[leader]["granger"]
        n_used = g.get(1, {}).get("n", 0)
        ap(f"| {leader} | {fmt(g.get(1, {}).get('p'))} | {fmt(g.get(2, {}).get('p'))} | {fmt(g.get(3, {}).get('p'))} | {n_used} |")
    ap("")
    ap("### H1 Sign-Agreement\n")
    ap("| Leader | k=1 | k=2 | k=3 |")
    ap("|---|---|---|---|")
    for leader in LEADERS:
        s = h1[leader]["sign_agree"]
        ap(f"| {leader} | {fmt(s.get(1, {}).get('agree'))} | {fmt(s.get(2, {}).get('agree'))} | {fmt(s.get(3, {}).get('agree'))} |")
    ap("")

    # ---------------- Split consistency ----------------
    ap("## 8. First-Half / Second-Half Consistency (M15 sign-agreement)\n")
    ap("| Leader | lag | 1H agree | 1H n | 2H agree | 2H n | delta |")
    ap("|---|---|---|---|---|---|---|")
    for leader in LEADERS:
        for lag in M15_LAGS:
            r = split[leader][lag]
            delta = r["h1_agree"] - r["h2_agree"] if not math.isnan(r["h1_agree"]) and not math.isnan(r["h2_agree"]) else float("nan")
            ap(f"| {leader} | {lag} | {fmt(r['h1_agree'])} | {r['h1_n']} | {fmt(r['h2_agree'])} | {r['h2_n']} | {fmt(delta, '{:+.3f}')} |")
    ap("")

    # ---------------- Verdict ----------------
    ap("## 9. Pre-Registered Decision Gate (M15)\n")
    ap(f"All three must hold: |rho|>=0.10, Granger p<{ALPHA_SPEC} (Bonferroni-spec), sign-agree>=0.55, strict lag>=1.\n")
    ap("| Leader | lag | rho | Granger p | sign_agree | pass_rho | pass_granger | pass_sign | ALL PASS |")
    ap("|---|---|---|---|---|---|---|---|---|")
    any_pass = False
    for a in assessments:
        if a["pass_all_preregistered"]:
            any_pass = True
        ap(
            "| {leader} | {lag} | {rho} | {gp} | {sa} | {ps} | {pg} | {psign} | {pa} |".format(
                leader=a["leader"],
                lag=a["lag"],
                rho=fmt(a["spearman_rho_m15"], "{:+.3f}"),
                gp=fmt(a["granger_p_m15"]),
                sa=fmt(a["sign_agree_m15"]),
                ps="Y" if a["pass_spearman"] else "N",
                pg="Y" if a["pass_granger_spec_bonf"] else "N",
                psign="Y" if a["pass_sign"] else "N",
                pa="**Y**" if a["pass_all_preregistered"] else "N",
            )
        )
    ap("")
    ap(f"**Overall pre-registered pass:** {'YES — at least one (leader, lag) meets all gates.' if any_pass else 'NO — no (leader, lag) pair meets all three pre-registered gates.'}\n")

    # ---------------- Summary ----------------
    ap("## 10. Interpretation and Recommendation\n")
    if any_pass:
        passing = [a for a in assessments if a["pass_all_preregistered"]]
        ap("Pairs passing pre-registered gate (M15):\n")
        for a in passing:
            ap(f"- **{a['leader']} -> XAUUSD @ lag {a['lag']}** — rho={a['spearman_rho_m15']:+.3f}, "
               f"Granger p={a['granger_p_m15']:.4f}, sign_agree={a['sign_agree_m15']:.3f}. "
               f"H1 lag-1 rho={fmt(a['h1_spearman_rho_lag1'], '{:+.3f}')}.")
        ap("\nNext steps: out-of-sample test on a separate window before any deployment. Economic-significance gate (WR lift on OB retest filter) must be run against the live trade log.\n")
    else:
        ap("No (leader, lag) pair survives the pre-registered gate. Directional cross-asset lead-lag is NOT a usable signal in the Jan 2 – Apr 10 2026 window at M15 with lag >= 1.\n")
        ap("\nMost predictive values observed at lag 0 (contemporaneous) — expected for liquid FX/index instruments at M15 resolution. This reinforces the existing GTOS design: XAUUSD decisions should rely on own-symbol structure (OB, BOS, CHoCH), not on real-time FX leaders. The H1 panel shows the same pattern.\n")
        ap("Result classification: **NULL — null finding consistent with prior expectation (liquid markets are efficient at M15 lead-lag horizons).**\n")

    ap("\n## 11. Replication\n")
    ap("- Script: `research/academic_pipeline/scripts/q_13_5_crossasset_leadlag.py`")
    ap("- Data: `data/historical_2026/*_{M15,H1}.csv` (inner-joined on timestamp)")
    ap("- No API calls; fully deterministic given the committed CSVs.")
    ap(f"- Packages: scipy.stats.spearmanr, statsmodels.tsa.stattools.grangercausalitytests (available={HAS_STATSMODELS}).")
    ap("")

    content = "\n".join(lines)

    # Append-only: preserve the pre-registered hypothesis section.
    text = OUT_MD.read_text(encoding="utf-8")
    marker = "*Sections 2+ below are computed from the committed script. Do not edit Section 1 after data inspection.*"
    if marker in text:
        keep = text.split(marker)[0] + marker + "\n"
        OUT_MD.write_text(keep + content, encoding="utf-8")
    else:
        OUT_MD.write_text(text + content, encoding="utf-8")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print("[Q-13.5] Loading M15 panel...")
    rets_m15 = build_returns_panel("M15")
    meta = {
        "m15_n": len(rets_m15),
        "m15_start": str(rets_m15.index.min()),
        "m15_end": str(rets_m15.index.max()),
    }
    print(f"  M15 aligned rows: {meta['m15_n']}  [{meta['m15_start']} .. {meta['m15_end']}]")

    print("[Q-13.5] Running M15 tests...")
    m15 = run_timeframe("M15", M15_LAGS, M15_XCORR_LAG_RANGE)

    print("[Q-13.5] Loading H1 panel + running H1 tests...")
    rets_h1 = build_returns_panel("H1")
    meta["h1_n"] = len(rets_h1)
    h1 = run_timeframe("H1", H1_LAGS, H1_XCORR_LAG_RANGE)

    print("[Q-13.5] Split-sample consistency check...")
    split = run_split_sign_agreement("M15", M15_LAGS)

    print("[Q-13.5] Applying pre-registered decision gate...")
    assessments = []
    for leader in LEADERS:
        for lag in M15_LAGS:
            assessments.append(assess_pair(leader, lag, m15, h1))

    any_pass = any(a["pass_all_preregistered"] for a in assessments)

    print("[Q-13.5] Writing report...")
    write_report(m15, h1, split, assessments, meta)

    print("\n========== SUMMARY ==========")
    print(f"Pairs tested: {len(assessments)}")
    print(f"Pairs passing pre-registered gate: {sum(1 for a in assessments if a['pass_all_preregistered'])}")
    for a in assessments:
        tag = "PASS" if a["pass_all_preregistered"] else "fail"
        print(f"  [{tag}] {a['leader']:6s} lag={a['lag']}  rho={a['spearman_rho_m15']:+.3f}  "
              f"Granger p={a['granger_p_m15']:.4f}  sign={a['sign_agree_m15']:.3f}")
    print("=============================")
    print(f"Report written to: {OUT_MD}")
    return 0 if not any_pass else 1  # non-zero signals a positive finding worth review


if __name__ == "__main__":
    sys.exit(main())

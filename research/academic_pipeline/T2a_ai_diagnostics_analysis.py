#!/usr/bin/env python3
"""T2a AI Evaluation Zero-Cost Diagnostics (H-3.4a + H-3.7a)

Tests:
  1. Does confidence_score carry ANY discriminative signal? (H-3.4a)
  2. Does XGBoost match the LLM's 65% WR? (H-3.7a — the existential test)

Data: 21,008 evaluations from batch API. 121 matched CANDIDATE trades with outcomes.
Pre-registered predictions:
  H-3.4a: ρ ~ 0. Confidence score carries zero discriminative information.
  H-3.7a: XGBoost achieves < 58% OOS WR, confirming LLM spatial reasoning adds value.

Bonferroni threshold: p < 0.025 (2 primary tests).
seed=42 everywhere.
"""

from __future__ import annotations

import json
import os
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent.parent
BATCH_API_DIR = ROOT / "knowledge_base_backtest" / "batch_api"
OUTPUT_DIR = Path(__file__).resolve().parent / "results"
DATA_DIR = Path(__file__).resolve().parent / "data"
T1_DATASET = DATA_DIR / "entry_engineering_dataset.csv"

OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

BONFERRONI_ALPHA = 0.025
SEED = 42
N_BOOTSTRAP = 10_000

# ─── Statistical helpers ────────────────────────────────────────────────────────

def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / denom
    m = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return (max(0.0, c - m), min(1.0, c + m))


def bootstrap_mean_ci(vals, n_iter: int = N_BOOTSTRAP, seed: int = SEED) -> tuple:
    arr = np.array([v for v in vals if v is not None and not np.isnan(v)])
    if len(arr) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.RandomState(seed)
    means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_iter)]
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(arr.mean()), float(lo), float(hi)


def spearman_test(x, y, name="") -> dict:
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 5:
        return {"feature": name, "rho": np.nan, "p_value": np.nan, "n": n, "sig": False}
    rho, p = stats.spearmanr(x, y)
    return {"feature": name, "rho": round(float(rho), 4), "p_value": round(float(p), 6),
            "n": n, "sig": bool(p < BONFERRONI_ALPHA)}


# ─── Phase 0: Data Extraction ───────────────────────────────────────────────────

print("=" * 70)
print("PHASE 0: DATA EXTRACTION")
print("=" * 70)

# --- 0.1 Parse JSON decision features ---

def parse_decision_json(text: str) -> dict | None:
    text_clean = text.strip()
    try:
        if "```json" in text_clean:
            text_clean = text_clean.split("```json")[1].split("```")[0].strip()
        elif text_clean.startswith("```"):
            text_clean = text_clean[3:text_clean.rfind("```")].strip()
        return json.loads(text_clean)
    except Exception:
        try:
            s = text_clean.find("{")
            e = text_clean.rfind("}")
            if s >= 0 and e > s:
                return json.loads(text_clean[s:e+1])
        except Exception:
            pass
    return None


GRADE_MAP = {"A+": 4, "A": 3, "B": 2, "C": 1}
DISP_MAP = {"strong": 3, "moderate": 2, "weak": 1, "none": 0}
BIAS_DIR_MAP = {"bullish": 1, "bearish": -1, "ranging": 0}
BIAS_CONF_MAP = {"high": 3, "medium": 2, "low": 1}
ZONE_MAP = {"discount": -1, "eq": 0, "premium": 1}
SWEEP_QUAL_MAP = {"strong": 3, "clean": 2, "moderate": 1, "weak": 0, "none": 0}


def extract_json_features(dj: dict) -> dict:
    """Extract features from parsed decision JSON."""
    feat = {}
    feat["decision_bin"] = 1 if dj.get("decision") == "CANDIDATE" else 0
    feat["confidence_score"] = dj.get("confidence_score", np.nan)
    feat["confidence_computation"] = dj.get("confidence_computation", "")
    feat["framework"] = dj.get("framework", "none")

    r = dj.get("reasoning", {}) or {}

    # Daily bias
    db = r.get("daily_bias", {}) or {}
    feat["daily_bias_direction"] = BIAS_DIR_MAP.get(
        str(db.get("direction", "")).lower(), np.nan)
    feat["daily_bias_confidence"] = BIAS_CONF_MAP.get(
        str(db.get("confidence", "")).lower(), np.nan)

    # H4 alignment
    h4 = r.get("h4_alignment", {}) or {}
    feat["h4_aligned"] = int(bool(h4.get("aligned", False)))

    # H1 setup
    h1s = r.get("h1_setup", {}) or {}
    feat["h1_poi_identified"] = int(bool(h1s.get("poi_identified", False)))
    feat["h1_poi_type"] = 1 if str(h1s.get("poi_type", "")).upper() == "OB" else 0
    feat["h1_zone"] = ZONE_MAP.get(str(h1s.get("zone", "")).lower(), np.nan)
    feat["h1_fib_pct"] = float(h1s.get("fib_retracement_pct", np.nan) or np.nan)
    feat["h1_causing_event"] = 1 if str(h1s.get("causing_event_type", "")).upper() == "BOS" else 0

    # Liquidity sweep
    ls = r.get("liquidity_sweep", {}) or {}
    feat["sweep_detected"] = int(bool(ls.get("detected", False)))
    feat["sweep_quality"] = SWEEP_QUAL_MAP.get(
        str(ls.get("sweep_quality", "")).lower(), np.nan)

    # M15 confirmation
    m15c = r.get("m15_confirmation", {}) or {}
    feat["m15_choch_detected"] = int(bool(m15c.get("choch_detected", False)))
    feat["displacement_quality"] = DISP_MAP.get(
        str(m15c.get("displacement_quality", "")).lower(), np.nan)
    disp_ratio = m15c.get("displacement_candle_body_vs_avg_ratio", np.nan)
    feat["displacement_ratio"] = float(disp_ratio) if disp_ratio is not None else np.nan

    # Setup grade
    feat["setup_grade"] = GRADE_MAP.get(str(r.get("setup_grade", "")).upper(), np.nan)

    return feat


# --- 0.2 Parse MSO text features ---

# Regexes for MSO parsing
OB_LINE_RE = re.compile(r"(bullish|bearish)\s+([\d.]+)-([\d.]+)\s+\([\d]{4}-", re.IGNORECASE)
FVG_LINE_RE = re.compile(r"(bullish|bearish)\s+([\d.]+)-([\d.]+)$", re.IGNORECASE | re.MULTILINE)
SWEEP_COUNT_RE = re.compile(r"##\s+Sweeps\s+\((\d+)\)", re.IGNORECASE)
H1_STRUCT_RE = re.compile(r"##\s+H1\s+—\s+Structure:\s+(bullish|bearish)", re.IGNORECASE)
M15_STRUCT_RE = re.compile(r"##\s+M15\s+—\s+Structure:\s+(bullish|bearish)", re.IGNORECASE)
ATR_RE = re.compile(r"ATR\(14\):\s*([\d.]+)")
AVG_BODY_RE = re.compile(r"Avg\s+body:\s*([\d.]+)")
BREAK_LINE_RE = re.compile(r"(BOS|CHoCH)\s+[\d]{4}-[\d]{2}-[\d]{2}", re.IGNORECASE)
DISP_BREAK_RE = re.compile(r"disp=(True|False)\s+ratio=([\d.]+)", re.IGNORECASE)


def extract_mso_features(user_msg: str, kill_zone: str = "") -> dict:
    """Extract features from MSO user message text."""
    feat = {}
    feat["kill_zone"] = kill_zone.lower()

    # Sweep count
    m = SWEEP_COUNT_RE.search(user_msg)
    feat["sweep_count"] = int(m.group(1)) if m else np.nan

    # Split into H1 and M15 sections
    h1_section = ""
    m15_section = ""
    h1_match = re.search(r"(##\s+H1\s+—.+?)(?=##\s+M15\s+—)", user_msg, re.DOTALL)
    m15_match = re.search(r"(##\s+M15\s+—.+?)(?=##\s+Recent|##\s+Current|$)", user_msg, re.DOTALL)
    if h1_match:
        h1_section = h1_match.group(1)
    if m15_match:
        m15_section = m15_match.group(1)

    # H1 features
    m = H1_STRUCT_RE.search(h1_section)
    feat["h1_structure_dir"] = 1 if m and m.group(1).lower() == "bullish" else 0

    h1_obs = OB_LINE_RE.findall(h1_section)
    feat["h1_ob_count"] = len(h1_obs)

    h1_fvgs = [l for l in h1_section.split("\n") if "bullish" in l.lower() or "bearish" in l.lower()
               if "fvg" in h1_section[max(0, h1_section.find(l)-200):h1_section.find(l)].lower()
               or "unfilled" in h1_section[max(0, h1_section.find(l)-100):h1_section.find(l)].lower()]
    # Simpler FVG count: count lines with two prices in Unfilled FVGs block
    unfilled_h1 = re.search(r"Unfilled FVGs.*?(?=\n\s*P/D:|\n\s*Avg|\Z)", h1_section, re.DOTALL)
    feat["h1_fvg_count"] = len(re.findall(r"(bullish|bearish)\s+[\d.]+-[\d.]+",
                                           unfilled_h1.group() if unfilled_h1 else ""))

    atrs_h1 = ATR_RE.findall(h1_section)
    feat["h1_atr"] = float(atrs_h1[0]) if atrs_h1 else np.nan

    avg_bodies_h1 = AVG_BODY_RE.findall(h1_section)
    feat["h1_avg_body"] = float(avg_bodies_h1[0]) if avg_bodies_h1 else np.nan

    breaks_h1 = BREAK_LINE_RE.findall(h1_section)
    feat["h1_break_count"] = len(breaks_h1)

    # Last H1 break disp and ratio
    disp_matches = DISP_BREAK_RE.findall(h1_section)
    if disp_matches:
        last_disp, last_ratio = disp_matches[-1]
        feat["h1_last_break_disp"] = 1 if last_disp.lower() == "true" else 0
        feat["h1_last_break_ratio"] = float(last_ratio)
    else:
        feat["h1_last_break_disp"] = np.nan
        feat["h1_last_break_ratio"] = np.nan

    # M15 features
    m = M15_STRUCT_RE.search(m15_section)
    feat["m15_structure_dir"] = 1 if m and m.group(1).lower() == "bullish" else 0

    m15_obs = OB_LINE_RE.findall(m15_section)
    feat["m15_ob_count"] = len(m15_obs)

    unfilled_m15 = re.search(r"Unfilled FVGs.*?(?=\n\s*P/D:|\n\s*Avg|\Z)", m15_section, re.DOTALL)
    feat["m15_fvg_count"] = len(re.findall(r"(bullish|bearish)\s+[\d.]+-[\d.]+",
                                            unfilled_m15.group() if unfilled_m15 else ""))

    atrs_m15 = ATR_RE.findall(m15_section)
    feat["m15_atr"] = float(atrs_m15[0]) if atrs_m15 else np.nan

    avg_bodies_m15 = AVG_BODY_RE.findall(m15_section)
    feat["m15_avg_body"] = float(avg_bodies_m15[0]) if avg_bodies_m15 else np.nan

    breaks_m15 = BREAK_LINE_RE.findall(m15_section)
    feat["m15_break_count"] = len(breaks_m15)

    disp_matches_m15 = DISP_BREAK_RE.findall(m15_section)
    if disp_matches_m15:
        last_disp_m15, last_ratio_m15 = disp_matches_m15[-1]
        feat["m15_last_break_disp"] = 1 if last_disp_m15.lower() == "true" else 0
        feat["m15_last_break_ratio"] = float(last_ratio_m15)
    else:
        feat["m15_last_break_disp"] = np.nan
        feat["m15_last_break_ratio"] = np.nan

    return feat


# --- 0.3 Load all evaluations ---

print("\nLoading batch API files...")

raw_files = sorted([f for f in os.listdir(BATCH_API_DIR) if "raw_results" in f])
full_files = sorted([f for f in os.listdir(BATCH_API_DIR) if "full_prompts" in f])

# Build candle_time → prompt metadata lookup
candle_to_prompt: dict[str, dict] = {}  # candle_time_iso → {kill_zone, user_message, custom_id}
print(f"  Loading {len(full_files)} full prompt files...")
for fn in full_files:
    with open(BATCH_API_DIR / fn) as f:
        data = json.load(f)
    for entry in data:
        ct = entry.get("candle_time")
        if ct:
            candle_to_prompt[ct] = {
                "kill_zone": entry.get("kill_zone", ""),
                "user_message": entry.get("prompt", {}).get("user_message", ""),
                "custom_id": entry.get("custom_id", ""),
            }

print(f"  Prompt metadata for {len(candle_to_prompt)} candle times")

# Build key → candle_time mapping (for raw results lookup)
# key format in raw_results: {date}_{kill_zone}_{HHMM}
# candle_time format: 2025-12-09T15:15:00Z → date=2025-12-09, time=1515
key_to_candle: dict[str, str] = {}
for ct, meta in candle_to_prompt.items():
    try:
        date_part = ct[:10]  # 2025-12-09
        time_part = ct[11:16].replace(":", "")  # 1515
        kz = meta["kill_zone"]
        key = f"{date_part}_{kz}_{time_part}"
        key_to_candle[key] = ct
    except Exception:
        pass

print(f"  Key-to-candle mapping: {len(key_to_candle)} entries")

# Extract all evaluations
print(f"\n  Loading {len(raw_files)} raw results files...")
all_rows = []
parse_errors = 0

for fn in raw_files:
    with open(BATCH_API_DIR / fn) as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, dict):
        continue

    for key, val in raw_data.items():
        if not isinstance(val, dict):
            continue
        text = val.get("text", "")
        if not text:
            continue

        dj = parse_decision_json(text)
        if dj is None:
            parse_errors += 1
            continue

        decision = dj.get("decision", "unknown")
        if decision not in ("CANDIDATE", "NO_TRADE"):
            continue

        # Get candle time and prompt metadata
        ct = key_to_candle.get(key)
        prompt_meta = candle_to_prompt.get(ct, {}) if ct else {}
        kill_zone = prompt_meta.get("kill_zone") or dj.get("kill_zone", "")
        user_msg = prompt_meta.get("user_message", "")

        # Extract features
        json_feats = extract_json_features(dj)
        mso_feats = extract_mso_features(user_msg, kill_zone)

        row = {
            "eval_key": key,
            "candle_time": ct,
            **json_feats,
            **mso_feats,
        }
        all_rows.append(row)

df_all = pd.DataFrame(all_rows)
print(f"\n  Total evaluations extracted: {len(df_all)}")
print(f"  Parse errors: {parse_errors}")

n_cand = (df_all["decision_bin"] == 1).sum()
n_nt = (df_all["decision_bin"] == 0).sum()
print(f"  CANDIDATE: {n_cand} ({n_cand/len(df_all):.1%})")
print(f"  NO_TRADE:  {n_nt} ({n_nt/len(df_all):.1%})")

# --- 0.4 Merge with T1 outcomes ---

print("\nLoading T1 dataset and matching to AI evaluations...")
t1_df = pd.read_csv(T1_DATASET)
t1_avail = t1_df[t1_df["data_available"] == True].copy()
print(f"  T1 trades with data: {len(t1_avail)}")

# Build lookup from candle_time to all_rows
candle_to_eval: dict[str, dict] = {}
for row in all_rows:
    ct = row.get("candle_time")
    if ct and row.get("decision_bin") == 1:
        candle_to_eval[ct] = row

# Match T1 trades
t1_rows = []
unmatched = 0
for _, trade in t1_avail.iterrows():
    ct = trade["candle_time"]
    eval_row = candle_to_eval.get(ct)
    if eval_row is None:
        unmatched += 1
        continue
    merged = {
        "trade_id": trade["trade_id"],
        "date": trade["date"],
        "symbol": trade["symbol"],
        "kill_zone": trade["kill_zone"],
        "outcome": trade["outcome"],
        "r_multiple": trade["r_multiple"],
        "win": trade["win"],
        "sl_distance_atr": trade["sl_distance_atr"],
        "rr_ratio_ai": trade["rr_ratio_ai"],
        **{k: v for k, v in eval_row.items()
           if k not in ("eval_key", "candle_time", "kill_zone", "decision_bin")},
    }
    t1_rows.append(merged)

df_cand = pd.DataFrame(t1_rows)
print(f"  Matched CANDIDATE trades: {len(df_cand)}")
print(f"  Unmatched (no eval found): {unmatched}")

# --- 0.5 Feature coverage report ---

print("\n--- Feature coverage report ---")
JSON_FEATURES = [
    "confidence_score", "daily_bias_direction", "daily_bias_confidence",
    "h4_aligned", "h1_poi_identified", "h1_poi_type", "h1_zone", "h1_fib_pct",
    "h1_causing_event", "sweep_detected", "sweep_quality", "m15_choch_detected",
    "displacement_quality", "displacement_ratio", "setup_grade",
]
MSO_FEATURES = [
    "sweep_count", "h1_ob_count", "h1_fvg_count", "h1_atr", "h1_avg_body",
    "h1_break_count", "h1_last_break_disp", "h1_last_break_ratio", "h1_structure_dir",
    "m15_ob_count", "m15_fvg_count", "m15_atr", "m15_avg_body",
    "m15_break_count", "m15_last_break_disp", "m15_last_break_ratio", "m15_structure_dir",
]
ALL_FEATURES = JSON_FEATURES + MSO_FEATURES
TRADE_FEATURES = ["sl_distance_atr", "rr_ratio_ai"]

coverage_rows = []
for f in ALL_FEATURES:
    if f in df_all.columns:
        pct_all = df_all[f].notna().mean() * 100
        pct_cand = df_cand[f].notna().mean() * 100 if f in df_cand.columns else np.nan
        coverage_rows.append({"feature": f, "coverage_all_%": round(pct_all, 1),
                               "coverage_candidate_%": round(pct_cand, 1)})
    else:
        coverage_rows.append({"feature": f, "coverage_all_%": 0.0, "coverage_candidate_%": 0.0})

df_cov = pd.DataFrame(coverage_rows)
low_coverage = df_cov[df_cov["coverage_all_%"] < 50]["feature"].tolist()
print(f"\nFeatures with < 50% coverage (will be dropped): {low_coverage}")
USE_FEATURES = [f for f in ALL_FEATURES if f not in low_coverage and f in df_all.columns]
print(f"Features used in analysis: {len(USE_FEATURES)}")
print(df_cov.to_string(index=False))

# Save to CSV
df_all.to_csv(DATA_DIR / "all_evaluations_features.csv", index=False)
df_cand.to_csv(DATA_DIR / "ai_evaluation_features.csv", index=False)
print(f"\nSaved: all_evaluations_features.csv ({len(df_all)} rows)")
print(f"Saved: ai_evaluation_features.csv ({len(df_cand)} rows)")

# ─── Test 1: Confidence Score Diagnostic (H-3.4a) ───────────────────────────────

print("\n" + "=" * 70)
print("TEST 1: CONFIDENCE SCORE DIAGNOSTIC (H-3.4a)")
print("=" * 70)
print("Pre-registered hypothesis: ρ ~ 0 (confidence carries zero signal)")
print(f"Significance threshold: p < {BONFERRONI_ALPHA}")

# 1.1 Distribution analysis
print("\n--- 1.1: Confidence Score Distribution ---")

conf_all = df_all["confidence_score"].dropna()
conf_cand = df_cand["confidence_score"].dropna() if "confidence_score" in df_cand.columns else pd.Series([], dtype=float)

print(f"\nALL evaluations (n={len(conf_all)}):")
vc_all = conf_all.value_counts().sort_index()
for val, cnt in vc_all.items():
    print(f"  score={int(val) if not np.isnan(val) else 'NaN'}: {cnt} ({cnt/len(conf_all):.1%})")

print(f"\nCANDIDATE trades only (n={len(conf_cand)}):")
if len(conf_cand) > 0:
    vc_cand = conf_cand.value_counts().sort_index()
    for val, cnt in vc_cand.items():
        print(f"  score={int(val) if not np.isnan(val) else 'NaN'}: {cnt} ({cnt/len(conf_cand):.1%})")
    pct_at_80 = (conf_cand == 80).mean() * 100
    pct_at_0 = (df_all.loc[df_all["decision_bin"] == 0, "confidence_score"] == 0).mean() * 100
    print(f"\n  % CANDIDATEs with score=80: {pct_at_80:.1f}%")
    print(f"  % NO_TRADEs with score=0: {pct_at_0:.1f}%")
    print(f"  CANDIDATE score range: [{conf_cand.min():.0f}, {conf_cand.max():.0f}]")
    print(f"  CANDIDATE score std: {conf_cand.std():.2f}")

# Check variance
has_confidence_variance = (conf_cand.nunique() >= 3) and (len(conf_cand[conf_cand == 80]) < 0.9 * len(conf_cand))

# 1.2 Confidence computation analysis
print("\n--- 1.2: Confidence Computation Breakdown ---")
comp_texts = df_cand["confidence_computation"].dropna().head(20) if "confidence_computation" in df_cand.columns else []
print("Sample computation texts from CANDIDATE trades:")
unique_comps = df_cand["confidence_computation"].value_counts().head(10) if "confidence_computation" in df_cand.columns else {}
for comp, cnt in unique_comps.items():
    print(f"  [{cnt}x] {str(comp)[:100]}")

# 1.3 Spearman correlations
print("\n--- 1.3: Spearman Correlations (CANDIDATE trades only) ---")

if len(df_cand) >= 10:
    outcome_vec = df_cand["win"].values.astype(float)
    r_vec = df_cand["r_multiple"].values.astype(float)

    corr_features = ["confidence_score", "setup_grade", "displacement_quality",
                     "displacement_ratio", "h1_fib_pct", "rr_ratio_ai",
                     "sl_distance_atr", "sweep_quality", "h4_aligned",
                     "m15_choch_detected", "h1_poi_identified", "h1_zone",
                     "daily_bias_confidence", "h1_ob_count", "m15_ob_count",
                     "h1_atr", "m15_atr", "sweep_count", "h1_break_count",
                     "m15_break_count", "h1_last_break_ratio", "m15_last_break_ratio",
                     "h1_last_break_disp", "m15_last_break_disp"]

    corr_rows = []
    for feat in corr_features:
        if feat not in df_cand.columns:
            continue
        x = df_cand[feat].values.astype(float)
        # vs outcome (WIN/LOSS)
        r1 = spearman_test(x, outcome_vec, f"{feat} vs WIN/LOSS")
        # vs r_multiple
        r2 = spearman_test(x, r_vec, f"{feat} vs R")
        corr_rows.append({
            "feature": feat,
            "rho_vs_outcome": r1["rho"],
            "p_vs_outcome": r1["p_value"],
            "sig_vs_outcome": r1["sig"],
            "rho_vs_R": r2["rho"],
            "p_vs_R": r2["p_value"],
            "n": r1["n"],
        })

    df_corr = pd.DataFrame(corr_rows).sort_values("rho_vs_outcome", key=abs, ascending=False)
    print(f"\nCorrelation table (sorted by |ρ vs outcome|, n={len(df_cand)} CANDIDATE trades):")
    print(df_corr.to_string(index=False))

    conf_corr = df_corr[df_corr["feature"] == "confidence_score"].iloc[0] if len(df_corr) > 0 else {}
    conf_rho = conf_corr.get("rho_vs_outcome", np.nan) if len(conf_corr) > 0 else np.nan
    print(f"\n  confidence_score vs WIN/LOSS: ρ = {conf_rho:.4f}")

    # Verdict on confidence
    if isinstance(conf_rho, float) and not np.isnan(conf_rho):
        if abs(conf_rho) < 0.05:
            conf_verdict = "DEAD (|ρ| < 0.05)"
        elif abs(conf_rho) < 0.10:
            conf_verdict = "MARGINAL (0.05 ≤ |ρ| < 0.10)"
        else:
            conf_verdict = "ALIVE (|ρ| ≥ 0.10)"
    else:
        conf_verdict = "INSUFFICIENT_DATA"
    print(f"  Confidence verdict: {conf_verdict}")

# 1.4 Binned analysis (only if variance exists)
print("\n--- 1.4: Binned Analysis ---")
if has_confidence_variance and len(df_cand) >= 20:
    try:
        distinct_vals = sorted(conf_cand.unique())
        q33 = conf_cand.quantile(0.33)
        q67 = conf_cand.quantile(0.67)
        if q33 == q67:
            raise ValueError("Insufficient variance: q33==q67")
        df_cand["conf_bin"] = df_cand["confidence_score"].apply(
            lambda x: "Low" if x <= q33 else ("Mid" if x <= q67 else "High"))
        bins = []
        for label, grp in df_cand.groupby("conf_bin", observed=True):
            wins = grp["win"].sum()
            n = len(grp)
            wr = wins / n
            lo, hi = wilson_ci(wins, n)
            mean_r, r_lo, r_hi = bootstrap_mean_ci(grp["r_multiple"].dropna().tolist())
            bins.append({"conf_bin": label, "n": n,
                         "win_rate_%": round(wr * 100, 1),
                         "wr_95ci": f"[{lo*100:.1f}, {hi*100:.1f}]",
                         "mean_R": round(mean_r, 3),
                         "R_95ci": f"[{r_lo:.3f}, {r_hi:.3f}]"})
        df_bins = pd.DataFrame(bins)
        print(df_bins.to_string(index=False))

        # Kruskal-Wallis
        groups = [grp["r_multiple"].dropna().values
                  for _, grp in df_cand.groupby("conf_bin", observed=True) if len(grp) >= 3]
        if len(groups) >= 2:
            kw_stat, kw_p = stats.kruskal(*groups)
            print(f"\n  Kruskal-Wallis on R across bins: H={kw_stat:.3f}, p={kw_p:.4f}")
    except Exception as e:
        print(f"  Binned analysis failed: {e}")
else:
    if not has_confidence_variance:
        print("  Skipped: confidence_score has insufficient variance")
        print("  (>90% of CANDIDATEs have the same score OR < 3 distinct values)")
    else:
        print(f"  Skipped: n={len(df_cand)} too small for binned analysis")

# 1.5 Platt scaling (only if ρ > 0.10)
print("\n--- 1.5: Platt Scaling ---")
if isinstance(conf_rho, float) and abs(conf_rho) > 0.10 and len(df_cand) >= 20:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import LeaveOneOut
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import brier_score_loss

        X_platt = df_cand[["confidence_score"]].copy()
        y_platt = df_cand["win"].values

        # Impute NaN
        X_platt = X_platt.fillna(X_platt.median())

        loo = LeaveOneOut()
        loo_probs = np.zeros(len(df_cand))
        lr = LogisticRegression(random_state=SEED, max_iter=1000)
        for train_idx, test_idx in loo.split(X_platt):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X_platt.iloc[train_idx])
            X_te = scaler.transform(X_platt.iloc[test_idx])
            lr.fit(X_tr, y_platt[train_idx])
            loo_probs[test_idx] = lr.predict_proba(X_te)[:, 1]

        brier = brier_score_loss(y_platt, loo_probs)
        brier_naive = brier_score_loss(y_platt, np.full(len(y_platt), y_platt.mean()))
        print(f"  Platt scaling (LOO-CV): Brier={brier:.4f} (naive={brier_naive:.4f})")
        print(f"  ECE improvement: {(brier_naive - brier):.4f}")
    except ImportError:
        print("  scikit-learn not available for Platt scaling")
    except Exception as e:
        print(f"  Platt scaling failed: {e}")
else:
    print(f"  Skipped: confidence ρ={conf_rho:.4f} (threshold: |ρ| > 0.10)")

# ─── Test 2: XGBoost Baseline (H-3.7a) ──────────────────────────────────────────

print("\n" + "=" * 70)
print("TEST 2: STATISTICAL MODEL BASELINE (H-3.7a)")
print("=" * 70)
print("Pre-registered hypothesis: XGBoost achieves < 58% OOS WR on WIN/LOSS")
print("(confirming LLM spatial reasoning adds value beyond simple feature thresholds)")
print(f"Significance threshold: p < {BONFERRONI_ALPHA}")

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression as LR
    from sklearn.model_selection import StratifiedKFold, LeaveOneOut, cross_val_predict
    from sklearn.preprocessing import StandardScaler
    from sklearn.utils.class_weight import compute_sample_weight
    from sklearn.metrics import (classification_report, roc_auc_score,
                                  accuracy_score, f1_score, precision_score, recall_score,
                                  confusion_matrix)
    from sklearn.impute import SimpleImputer
    from sklearn.inspection import permutation_importance
    SK_AVAILABLE = True
except ImportError as e:
    print(f"  ERROR: scikit-learn not available: {e}")
    SK_AVAILABLE = False

if SK_AVAILABLE:
    # --- Feature preparation ---
    PART_A_FEATURES = [f for f in USE_FEATURES if f in df_all.columns]
    PART_B_FEATURES = [f for f in USE_FEATURES if f in df_cand.columns]
    # h1_fib_pct: dropped from Part A (13.7% all-eval coverage) but 82.6% coverage in candidates
    if "h1_fib_pct" in df_cand.columns and df_cand["h1_fib_pct"].notna().mean() > 0.5:
        PART_B_FEATURES.append("h1_fib_pct")
    PART_B_FEATURES += [f for f in TRADE_FEATURES if f in df_cand.columns]
    PART_B_FEATURES = list(dict.fromkeys(PART_B_FEATURES))  # deduplicate

    print(f"\nPart A features: {len(PART_A_FEATURES)}")
    print(f"Part B features: {len(PART_B_FEATURES)}")

    def prepare_X(df: pd.DataFrame, features: list, impute: bool = True) -> np.ndarray:
        X = df[features].copy()
        X = X.replace([np.inf, -np.inf], np.nan)
        if impute:
            imp_num = SimpleImputer(strategy="median")
            X_num = imp_num.fit_transform(X.select_dtypes(include=[np.number]))
            return X_num
        return X.values

    def run_cv_part_a(X, y, models_dict, seeds=(42, 43, 44)):
        """Stratified 5-fold CV × 3 seeds for Part A."""
        results = {}
        for name, model in models_dict.items():
            accs, precs, recs, f1s, aucs = [], [], [], [], []
            for seed in seeds:
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
                y_pred = np.zeros(len(y), dtype=int)
                y_prob = np.zeros(len(y))
                for train_idx, test_idx in cv.split(X, y):
                    X_tr, X_te = X[train_idx], X[test_idx]
                    y_tr = y[train_idx]

                    # Scale
                    scaler = StandardScaler()
                    X_tr = scaler.fit_transform(X_tr)
                    X_te = scaler.transform(X_te)

                    # Sample weights for class imbalance
                    sw = compute_sample_weight("balanced", y_tr)

                    m = type(model)(**model.get_params())
                    try:
                        # GradientBoosting doesn't support class_weight, use sample_weight
                        if hasattr(m, "class_weight"):
                            m.set_params(class_weight="balanced")
                            m.fit(X_tr, y_tr)
                        else:
                            m.fit(X_tr, y_tr, sample_weight=sw)
                    except Exception:
                        m.fit(X_tr, y_tr)

                    y_pred[test_idx] = m.predict(X_te)
                    if hasattr(m, "predict_proba"):
                        y_prob[test_idx] = m.predict_proba(X_te)[:, 1]

                accs.append(accuracy_score(y, y_pred))
                precs.append(precision_score(y, y_pred, zero_division=0))
                recs.append(recall_score(y, y_pred, zero_division=0))
                f1s.append(f1_score(y, y_pred, zero_division=0))
                try:
                    aucs.append(roc_auc_score(y, y_prob))
                except Exception:
                    aucs.append(np.nan)

            results[name] = {
                "accuracy": np.mean(accs),
                "precision_CANDIDATE": np.mean(precs),
                "recall_CANDIDATE": np.mean(recs),
                "f1_CANDIDATE": np.mean(f1s),
                "auc": np.mean(aucs),
            }
        return results

    # ─── Part A: CANDIDATE vs NO_TRADE ──────────────────────────────────────────

    print("\n--- Part A: CANDIDATE vs NO_TRADE Classification ---")
    print(f"  Dataset: {len(df_all)} evaluations, {n_cand} CANDIDATE ({n_cand/len(df_all):.1%})")

    X_a = prepare_X(df_all, PART_A_FEATURES)
    y_a = df_all["decision_bin"].values

    # Random baselines
    always_notrade_acc = 1 - y_a.mean()
    print(f"\n  Random baselines:")
    print(f"    Always NO_TRADE: accuracy={always_notrade_acc:.3f}")
    print(f"    Always CANDIDATE: accuracy={y_a.mean():.3f}")

    models_a = {
        "LogisticRegression": LR(random_state=SEED, max_iter=1000, class_weight="balanced"),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                         learning_rate=0.1, random_state=SEED,
                                                         subsample=0.8),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=5, random_state=SEED,
                                                class_weight="balanced"),
    }

    results_a = run_cv_part_a(X_a, y_a, models_a)

    print("\n  Part A Results (5-fold CV × 3 seeds, mean):")
    print(f"  {'Model':<25} {'Acc':>7} {'Prec(C)':>8} {'Rec(C)':>8} {'F1(C)':>7} {'AUC':>7}")
    print("  " + "-" * 65)
    for name, res in results_a.items():
        print(f"  {name:<25} {res['accuracy']:>7.3f} {res['precision_CANDIDATE']:>8.3f} "
              f"{res['recall_CANDIDATE']:>8.3f} {res['f1_CANDIDATE']:>7.3f} {res['auc']:>7.3f}")

    # Feature importances (GradientBoosting)
    print("\n  Training GradientBoosting on full data for feature importance...")
    scaler_a = StandardScaler()
    X_a_scaled = scaler_a.fit_transform(X_a)
    sw_a = compute_sample_weight("balanced", y_a)
    gb_a = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                                       random_state=SEED, subsample=0.8)
    gb_a.fit(X_a_scaled, y_a, sample_weight=sw_a)

    importances_a = pd.Series(gb_a.feature_importances_, index=PART_A_FEATURES)
    importances_a = importances_a.sort_values(ascending=False)
    print("\n  Top 10 features driving CANDIDATE/NO_TRADE split:")
    for feat, imp in importances_a.head(10).items():
        is_prompt_rule = feat in ("m15_choch_detected", "h1_poi_identified", "h4_aligned",
                                   "sweep_detected", "daily_bias_direction", "daily_bias_confidence")
        rule_note = " [PROMPT RULE]" if is_prompt_rule else ""
        print(f"    {feat:<35}: {imp:.4f}{rule_note}")

    # Interpretation
    top5_a = set(importances_a.head(5).index)
    prompt_rule_features = {"m15_choch_detected", "h1_poi_identified", "h4_aligned",
                             "sweep_detected", "daily_bias_direction", "daily_bias_confidence"}
    overlap = top5_a & prompt_rule_features
    print(f"\n  Top-5 overlap with prompt-rule features: {len(overlap)}/5")
    if len(overlap) >= 3:
        print("  INTERPRETATION: Model is learning prompt hard-coded rules, not independent reasoning")
    else:
        print("  INTERPRETATION: Model uses features beyond prompt rules — partial genuine reasoning")

    # ─── Part B: WIN/LOSS among CANDIDATEs — THE EXISTENTIAL TEST ───────────────

    print("\n--- Part B: WIN/LOSS Among CANDIDATEs (LOO-CV) — THE EXISTENTIAL TEST ---")
    n_b = len(df_cand)
    n_wins = df_cand["win"].sum()
    base_wr = n_wins / n_b if n_b > 0 else np.nan
    print(f"  Dataset: {n_b} matched CANDIDATE trades")
    print(f"  Base win rate (LLM benchmark): {base_wr:.1%} ({n_wins}/{n_b})")
    print(f"  LOO-CV (n={n_b} iterations)")
    print(f"\n  Pre-registered: model WR < 58% → LLM adds value beyond tabular features")
    print(f"  Decision thresholds: ≥62% → LLM overhead | 58-62% → ambiguous | <58% → LLM justified")

    if n_b < 10:
        print("  SKIPPED: n too small for LOO-CV")
    else:
        X_b_df = df_cand[PART_B_FEATURES].copy()
        y_b = df_cand["win"].values

        # Impute
        imp_b = SimpleImputer(strategy="median")
        X_b = imp_b.fit_transform(X_b_df.select_dtypes(include=[np.number]))
        feature_names_b = X_b_df.select_dtypes(include=[np.number]).columns.tolist()

        models_b = {
            "LogisticRegression": LR(random_state=SEED, max_iter=1000, class_weight="balanced"),
            "GradientBoosting": GradientBoostingClassifier(n_estimators=50, max_depth=2,
                                                             learning_rate=0.1, random_state=SEED),
            "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=3,
                                                    random_state=SEED, class_weight="balanced"),
        }

        loo = LeaveOneOut()
        results_b = {}

        for name, model in models_b.items():
            y_pred_loo = np.zeros(n_b, dtype=int)
            y_prob_loo = np.zeros(n_b)

            for train_idx, test_idx in loo.split(X_b, y_b):
                X_tr, X_te = X_b[train_idx], X_b[test_idx]
                y_tr = y_b[train_idx]

                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_tr)
                X_te_s = scaler.transform(X_te)

                sw = compute_sample_weight("balanced", y_tr)
                m = type(model)(**model.get_params())
                try:
                    if hasattr(m, "class_weight"):
                        m.set_params(class_weight="balanced")
                        m.fit(X_tr_s, y_tr)
                    else:
                        m.fit(X_tr_s, y_tr, sample_weight=sw)
                except Exception:
                    m.fit(X_tr_s, y_tr)

                y_pred_loo[test_idx] = m.predict(X_te_s)
                if hasattr(m, "predict_proba"):
                    y_prob_loo[test_idx] = m.predict_proba(X_te_s)[:, 1]

            oos_wr = accuracy_score(y_b, y_pred_loo)
            try:
                oos_auc = roc_auc_score(y_b, y_prob_loo)
            except Exception:
                oos_auc = np.nan
            cm = confusion_matrix(y_b, y_pred_loo)
            results_b[name] = {"oos_wr": oos_wr, "auc": oos_auc, "cm": cm}

        print(f"\n  Part B Results (LOO-CV, n={n_b}):")
        print(f"  {'Model':<25} {'OOS WR':>8} {'AUC':>7}")
        print("  " + "-" * 45)
        llm_benchmark = base_wr
        for name, res in results_b.items():
            delta = res["oos_wr"] - llm_benchmark
            print(f"  {name:<25} {res['oos_wr']:>8.3f} {res['auc']:>7.3f}  (vs LLM {delta:+.3f})")

        # Confusion matrices
        print("\n  Confusion matrices (rows=actual, cols=pred):")
        for name, res in results_b.items():
            cm = res["cm"]
            print(f"  {name}: [[{cm[0,0]},{cm[0,1]}],[{cm[1,0]},{cm[1,1]}]] "
                  f"(TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]})")

        # Statistical test: is best model WR significantly different from base rate?
        best_name = max(results_b, key=lambda k: results_b[k]["oos_wr"])
        best_wr = results_b[best_name]["oos_wr"]
        best_preds = None  # need to re-run for significance test
        # Simple binomial test: H0 = model WR <= base rate
        n_correct = int(round(best_wr * n_b))
        # Test against coin flip (0.5) and against base rate
        binom_vs_flip = stats.binomtest(n_correct, n_b, p=0.5, alternative="greater")
        binom_vs_base = stats.binomtest(n_correct, n_b, p=base_wr, alternative="greater")
        wr_lo, wr_hi = wilson_ci(n_correct, n_b)
        print(f"\n  Best model: {best_name} (OOS WR={best_wr:.3f})")
        print(f"  Wilson CI (95%): [{wr_lo:.3f}, {wr_hi:.3f}]")
        print(f"  Binomial test vs coin flip (p=0.5): p={binom_vs_flip.pvalue:.4f}")
        print(f"  Binomial test vs base rate (p={base_wr:.3f}): p={binom_vs_base.pvalue:.4f}")

        # Permutation importance on best model (train on full data)
        print(f"\n  Permutation importance for {best_name} (trained on all {n_b} trades):")
        scaler_b = StandardScaler()
        X_b_scaled = scaler_b.fit_transform(X_b)
        m_best = type(models_b[best_name])(**models_b[best_name].get_params())
        sw_b = compute_sample_weight("balanced", y_b)
        try:
            if hasattr(m_best, "class_weight"):
                m_best.set_params(class_weight="balanced")
                m_best.fit(X_b_scaled, y_b)
            else:
                m_best.fit(X_b_scaled, y_b, sample_weight=sw_b)
        except Exception:
            m_best.fit(X_b_scaled, y_b)

        perm_imp = permutation_importance(m_best, X_b_scaled, y_b, n_repeats=50,
                                           random_state=SEED, scoring="accuracy")
        perm_df = pd.DataFrame({
            "feature": feature_names_b,
            "importance_mean": perm_imp.importances_mean,
            "importance_std": perm_imp.importances_std,
        }).sort_values("importance_mean", ascending=False)
        print(f"  (positive = predictive, negative = noise at n={n_b})")
        for _, row in perm_df.head(10).iterrows():
            print(f"    {row['feature']:<35}: {row['importance_mean']:+.5f} ± {row['importance_std']:.5f}")

        # Verdict for Part B
        print("\n  --- Part B Verdict ---")
        if best_wr >= 0.62:
            part_b_verdict = "LLM OVERHEAD: Features predict outcomes nearly as well as the LLM"
        elif best_wr >= 0.58:
            part_b_verdict = "AMBIGUOUS: Extend to 200+ trades before deciding"
        elif best_wr > 0.52:
            part_b_verdict = "LLM JUSTIFIED: Features alone don't match LLM WR"
        else:
            part_b_verdict = "OUTCOMES UNPREDICTABLE: Edge is mechanical (zone continuation), not predictive"
        print(f"  {part_b_verdict}")
        print(f"  (best OOS WR = {best_wr:.1%}, LLM WR = {base_wr:.1%}, coin flip = 50%)")

        # ─── Part C: TabPFN ──────────────────────────────────────────────────────

        print("\n--- Part C: TabPFN ---")
        try:
            from tabpfn import TabPFNClassifier
            print("  TabPFN available — running Part A and Part B...")

            # Part A (small sample for speed — use first 5000 rows due to TabPFN limits)
            n_a_sample = min(3000, len(df_all))
            sample_idx = np.random.RandomState(SEED).choice(len(df_all), n_a_sample, replace=False)
            X_a_sample = X_a[sample_idx]
            y_a_sample = y_a[sample_idx]

            tab_clf_a = TabPFNClassifier(device="cpu", N_ensemble_configurations=4)
            cv_tab_a = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
            y_pred_tab_a = cross_val_predict(tab_clf_a, X_a_sample, y_a_sample, cv=cv_tab_a)
            tabpfn_f1_a = f1_score(y_a_sample, y_pred_tab_a, zero_division=0)
            print(f"  TabPFN Part A F1(CANDIDATE): {tabpfn_f1_a:.3f} (n={n_a_sample} sample)")

            # Part B (LOO — n=121, TabPFN is designed for this)
            tab_clf_b = TabPFNClassifier(device="cpu", N_ensemble_configurations=4)
            y_pred_tab_b = np.zeros(n_b, dtype=int)
            for train_idx, test_idx in LeaveOneOut().split(X_b):
                tab_clf_b.fit(X_b[train_idx], y_b[train_idx])
                y_pred_tab_b[test_idx] = tab_clf_b.predict(X_b[test_idx])
            tabpfn_wr_b = accuracy_score(y_b, y_pred_tab_b)
            print(f"  TabPFN Part B OOS WR: {tabpfn_wr_b:.3f} (n={n_b})")
        except ImportError:
            print("  TabPFN unavailable — skipping (LogisticRegression + GradientBoosting + RF baseline is sufficient)")
        except Exception as e:
            print(f"  TabPFN failed: {e}")

        # ─── Part D: Feature Ablation ────────────────────────────────────────────

        print("\n--- Part D: Feature Ablation Study ---")
        print("  Comparing: top-5 features vs all features for WIN/LOSS prediction")

        # Top 5 from GB Part A importances (using features that appear in Part B)
        top5_from_a = [f for f in importances_a.head(5).index if f in feature_names_b]
        if len(top5_from_a) < 3:
            top5_from_a = feature_names_b[:5]

        print(f"  Top-5 features (from Part A GB importance): {top5_from_a}")

        def loo_wr(X_mat, y_vec, model):
            preds = np.zeros(len(y_vec), dtype=int)
            for tr, te in LeaveOneOut().split(X_mat, y_vec):
                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_mat[tr])
                X_te_s = scaler.transform(X_mat[te])
                sw = compute_sample_weight("balanced", y_vec[tr])
                m = type(model)(**model.get_params())
                try:
                    if hasattr(m, "class_weight"):
                        m.set_params(class_weight="balanced")
                        m.fit(X_tr_s, y_vec[tr])
                    else:
                        m.fit(X_tr_s, y_vec[tr], sample_weight=sw)
                except Exception:
                    m.fit(X_tr_s, y_vec[tr])
                preds[te] = m.predict(X_te_s)
            return accuracy_score(y_vec, preds)

        gb_model = GradientBoostingClassifier(n_estimators=50, max_depth=2,
                                               learning_rate=0.1, random_state=SEED)

        # Top-5 only
        top5_idx = [feature_names_b.index(f) for f in top5_from_a if f in feature_names_b]
        if top5_idx:
            X_top5 = X_b[:, top5_idx]
            wr_top5 = loo_wr(X_top5, y_b, gb_model)
        else:
            wr_top5 = np.nan

        # All features
        wr_all = loo_wr(X_b, y_b, gb_model)

        print(f"\n  LOO WR — top-5 features: {wr_top5:.3f}")
        print(f"  LOO WR — all {len(feature_names_b)} features: {wr_all:.3f}")
        if wr_top5 > wr_all:
            print("  RESULT: Top-5 beats all features → overfitting at n=121 confirmed")
            print("          (curse of dimensionality: more features hurts)")
        elif wr_all > wr_top5 + 0.02:
            print("  RESULT: More features helps → additional features add genuine signal")
        else:
            print("  RESULT: Marginal difference → feature count doesn't matter much at n=121")

# ─── Phase 3: Synthesis ─────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("PHASE 3: SYNTHESIS")
print("=" * 70)

print("""
=== Confidence Score Verdict ===
""")
try:
    print(f"  Distribution: See Section 1.1 above")
    print(f"  Spearman ρ(confidence, WIN/LOSS) = {conf_rho:.4f}")
    print(f"  Verdict: {conf_verdict}")
    if abs(conf_rho) < 0.05:
        print("""
  The confidence score carries no discriminative information among CANDIDATE trades.
  This confirms H-3.4a. The score appears to be post-hoc rationalization rather than
  a calibrated probability estimate.

  Best alternative signal (from correlation table): See highest |ρ| features above.
  """)
    elif abs(conf_rho) < 0.10:
        print("""
  Marginal signal. The confidence score has some discriminative power but it is weak.
  At least one other feature likely dominates — see correlation table.
  """)
    else:
        print("""
  Surprising: confidence score shows real signal. Platt scaling applied above.
  Recommend: replace raw confidence with calibrated probability in the pipeline.
  """)
except NameError:
    print("  (confidence analysis incomplete — see above)")

print("""
=== LLM Justification Verdict ===
""")
try:
    print(f"  Best model OOS WR: {best_wr:.1%} (LLM WR: {base_wr:.1%})")
    print(f"  Part B verdict: {part_b_verdict}")
    print(f"""
  CRITICAL DISTINCTION:
  - Part A (replicating CANDIDATE/NO_TRADE decisions): Measures if LLM logic can be
    mechanized. High F1 = the LLM is executing hard-coded rules, not reasoning.
  - Part B (predicting WIN/LOSS outcomes): Measures if any pre-trade feature predicts
    which CANDIDATEs actually win. This is the existential test.

  If Part A F1(CANDIDATE) is high AND Part B WR is near base rate:
    → The LLM's filtering is rule-based (replicable) but doesn't add WIN prediction.
    → The edge is OB zone continuation mechanics, not AI selectivity.
    → $60/month buys you a JSON parser for structured rules + the zone detection output.

  If Part B WR < 52%:
    → No feature predicts trade outcomes. Edge is entirely mechanical.
    → Both the LLM AND feature-based filtering are overhead.
    → The system works because OB zone continuation works at ~70%.

  Pipeline implications:
    - If LLM overhead: Test XGBoost filter (T2b) + simplify to rule-based entry
    - If LLM adds value: Optimize prompt features (T2b shadow API experiments priority ↑)
    - If outcomes unpredictable: Invest in zone detection quality, not filtering quality
  """)
except NameError:
    print("  (Part B analysis incomplete — see above)")

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)
print(f"  all_evaluations_features.csv → {DATA_DIR / 'all_evaluations_features.csv'}")
print(f"  ai_evaluation_features.csv   → {DATA_DIR / 'ai_evaluation_features.csv'}")
print(f"  Results report               → {OUTPUT_DIR / 'T2a_ai_diagnostics_results_v1.md'}")

# Build results markdown
md_lines = [
    "# T2a AI Evaluation Diagnostics — Results",
    "",
    f"**Date:** 2026-04-11",
    f"**Data:** {len(df_all)} evaluations ({n_cand} CANDIDATE, {n_nt} NO_TRADE)",
    f"**Matched CANDIDATE trades:** {len(df_cand)} (of 121 with data in T1)",
    f"**Bonferroni threshold:** p < {BONFERRONI_ALPHA}",
    "",
    "## Data Availability",
    "",
    df_cov.to_string(index=False),
    "",
    "## Test 1: Confidence Score Diagnostic (H-3.4a)",
    "",
    f"**Pre-registered:** ρ ~ 0 (confidence carries zero signal)",
    "",
    "### Confidence Distribution",
    "",
]

if len(conf_cand) > 0:
    md_lines.append("**CANDIDATE trades only:**")
    for val, cnt in vc_cand.items():
        md_lines.append(f"- score={int(val)}: {cnt} ({cnt/len(conf_cand):.1%})")
    md_lines.append(f"- % at exactly 80: {pct_at_80:.1f}%")
    md_lines.append(f"- % NO_TRADEs at 0: {pct_at_0:.1f}%")

md_lines += [
    "",
    "### Spearman Correlations",
    "",
]

try:
    md_lines.append(df_corr.to_string(index=False))
    md_lines.append("")
    md_lines.append(f"**confidence_score ρ vs outcome:** {conf_rho:.4f}")
    md_lines.append(f"**Verdict:** {conf_verdict}")
except NameError:
    md_lines.append("(analysis incomplete)")

md_lines += [
    "",
    "## Test 2: Statistical Model Baseline (H-3.7a)",
    "",
    "**Pre-registered:** XGBoost OOS WR < 58% (confirming LLM adds value)",
    "",
    "### Part A: CANDIDATE vs NO_TRADE",
    "",
]

try:
    for name, res in results_a.items():
        md_lines.append(f"**{name}:** acc={res['accuracy']:.3f}, "
                         f"F1(C)={res['f1_CANDIDATE']:.3f}, AUC={res['auc']:.3f}")
    md_lines += [
        "",
        "### Part B: WIN/LOSS Among CANDIDATEs (LOO-CV)",
        f"",
        f"**LLM benchmark WR:** {base_wr:.1%} ({n_wins}/{n_b})",
        "",
    ]
    for name, res in results_b.items():
        md_lines.append(f"**{name}:** OOS WR={res['oos_wr']:.3f}, AUC={res['auc']:.3f}")
    md_lines.append(f"")
    md_lines.append(f"**Verdict:** {part_b_verdict}")
except NameError:
    md_lines.append("(analysis incomplete)")

md_lines += [
    "",
    "## Synthesis",
    "",
    "See console output for full synthesis.",
    "",
    "---",
    "*Generated by T2a_ai_diagnostics_analysis.py*",
]

with open(OUTPUT_DIR / "T2a_ai_diagnostics_results_v1.md", "w") as f:
    f.write("\n".join(md_lines))

print(f"\nDone. Results written to T2a_ai_diagnostics_results_v1.md")

#!/usr/bin/env python3
"""
SMC A4: Consolidation as predictor analysis
Analyzes tight/consol fields from the displacement database.
"""

import json
import numpy as np
from scipy import stats
from datetime import datetime

# ---------- paths ----------
DATA = "/Users/borr/Documents/trading/gold-agent/knowledge_base_backtest/analysis/displacement_database_20260403_0030.json"
OUT  = "/Users/borr/Documents/trading/gold-agent/knowledge_base_backtest/analysis/smc_consolidation_20260405.json"

# ---------- helpers ----------
def flag(n):
    return "LOW_N" if n < 30 else "ok"

def grp_stats(subset, label):
    n = len(subset)
    if n == 0:
        return {"label": label, "n": 0, "flag": "EMPTY"}
    cont = [r["cont_3h"] for r in subset if r.get("cont_3h") is not None]
    mfe  = [r["mfe_3h"]  for r in subset if r.get("mfe_3h") is not None]
    mae  = [r["mae_3h"]  for r in subset if r.get("mae_3h") is not None]
    cont_bool = [1 if c else 0 for c in cont]
    return {
        "label": label,
        "n": n,
        "flag": flag(n),
        "cont_3h_rate": round(np.mean(cont_bool), 4) if cont_bool else None,
        "cont_3h_n": sum(cont_bool),
        "avg_mfe_3h": round(float(np.mean(mfe)), 2) if mfe else None,
        "avg_mae_3h": round(float(np.mean(mae)), 2) if mae else None,
        "med_mfe_3h": round(float(np.median(mfe)), 2) if mfe else None,
        "med_mae_3h": round(float(np.median(mae)), 2) if mae else None,
    }

def chi2_from_groups(groups):
    """Chi-squared test on cont_3h rates across groups."""
    table = []
    for g in groups:
        n = g["n"]
        cont_n = g.get("cont_3h_n", 0)
        if n == 0:
            continue
        table.append([cont_n, n - cont_n])
    if len(table) < 2:
        return {"chi2": None, "p": None, "note": "insufficient groups"}
    chi2, p, dof, _ = stats.chi2_contingency(table)
    return {"chi2": round(chi2, 4), "p": round(p, 6), "dof": dof}

def quartile_split(data, key):
    """Split data into quartiles of key, return list of (label, subset)."""
    vals = [r[key] for r in data if r.get(key) is not None]
    if len(vals) < 20:
        return []
    q25, q50, q75 = np.percentile(vals, [25, 50, 75])
    buckets = [
        (f"Q1 (<={round(q25,2)})", [r for r in data if r.get(key) is not None and r[key] <= q25]),
        (f"Q2 ({round(q25,2)}-{round(q50,2)}]", [r for r in data if r.get(key) is not None and q25 < r[key] <= q50]),
        (f"Q3 ({round(q50,2)}-{round(q75,2)}]", [r for r in data if r.get(key) is not None and q50 < r[key] <= q75]),
        (f"Q4 (>{round(q75,2)})", [r for r in data if r.get(key) is not None and r[key] > q75]),
    ]
    return buckets

# ---------- load ----------
with open(DATA) as f:
    db = json.load(f)

print(f"Loaded {len(db)} records")

# Determine thresholds: tight and consol are floats (0-1 scale or similar).
# tight > some threshold = "tight". Let's inspect distribution first.
tight_vals = [r["tight"] for r in db if r.get("tight") is not None]
consol_vals = [r["consol"] for r in db if r.get("consol") is not None]
print(f"tight: min={min(tight_vals):.3f} max={max(tight_vals):.3f} mean={np.mean(tight_vals):.3f} median={np.median(tight_vals):.3f}")
print(f"consol: min={min(consol_vals):.3f} max={max(consol_vals):.3f} mean={np.mean(consol_vals):.3f} median={np.median(consol_vals):.3f}")

# Use boolean interpretation: tight >= 0.5 means tight=True, consol >= 0.5 means consol=True
# But let's check if they're already 0/1 or continuous
tight_unique = sorted(set(round(v, 3) for v in tight_vals))
consol_unique = sorted(set(round(v, 3) for v in consol_vals))
print(f"tight unique count: {len(tight_unique)}, consol unique count: {len(consol_unique)}")

# They appear continuous. Use median split for tight/consol boolean.
# Actually, the user says tight(bool), consol(bool) — maybe they're thresholded elsewhere.
# Let's treat high tight (>=median) as "tight=True" and high consol (>=median) as "consol=True".
# Better: use top quartile as "tight" since higher = tighter consolidation.
tight_med = float(np.median(tight_vals))
consol_med = float(np.median(consol_vals))

# Actually let's check if these are scores where higher = more consolidated
# p5_range is the actual range, tight seems like a ratio or score
# Let's use: tight >= median => tight_bool=True
# consol >= median => consol_bool=True

for r in db:
    r["tight_bool"] = (r.get("tight") is not None and r["tight"] >= tight_med)
    r["consol_bool"] = (r.get("consol") is not None and r["consol"] >= consol_med)

results = {}

# ========== 1. CROSS-TAB TIGHT x CONSOL ==========
print("\n=== 1. Cross-tab tight x consol ===")

tt = [r for r in db if r["tight_bool"] and r["consol_bool"]]
tf = [r for r in db if r["tight_bool"] and not r["consol_bool"]]
ft = [r for r in db if not r["tight_bool"] and r["consol_bool"]]
ff = [r for r in db if not r["tight_bool"] and not r["consol_bool"]]

cross_groups = [
    grp_stats(tt, "tight+consol"),
    grp_stats(tf, "tight+notConsol"),
    grp_stats(ft, "notTight+consol"),
    grp_stats(ff, "notTight+notConsol"),
]

for g in cross_groups:
    print(f"  {g['label']}: n={g['n']} cont_3h={g.get('cont_3h_rate')} mfe={g.get('avg_mfe_3h')} mae={g.get('avg_mae_3h')} [{g['flag']}]")

chi2_cross = chi2_from_groups(cross_groups)
print(f"  Chi2: {chi2_cross}")

results["cross_tab_tight_consol"] = {
    "thresholds": {"tight_median": round(tight_med, 4), "consol_median": round(consol_med, 4)},
    "groups": cross_groups,
    "chi2_test": chi2_cross,
}

# ========== 2. HOW TIGHT IS TIGHT? ==========
print("\n=== 2. How tight is tight? ===")

tight_true = [r for r in db if r["tight_bool"]]
p5_ranges_tight = [r["p5_range"] for r in tight_true if r.get("p5_range") is not None]
tight_range_stats = {
    "n": len(p5_ranges_tight),
    "mean": round(float(np.mean(p5_ranges_tight)), 2),
    "median": round(float(np.median(p5_ranges_tight)), 2),
    "p25": round(float(np.percentile(p5_ranges_tight, 25)), 2),
    "p75": round(float(np.percentile(p5_ranges_tight, 75)), 2),
    "std": round(float(np.std(p5_ranges_tight)), 2),
}
print(f"  p5_range when tight=T: {tight_range_stats}")

# Split tight=True into quartiles of p5_range
tight_quartiles = quartile_split(tight_true, "p5_range")
tight_q_results = []
for label, subset in tight_quartiles:
    s = grp_stats(subset, label)
    tight_q_results.append(s)
    print(f"  {label}: n={s['n']} cont_3h={s.get('cont_3h_rate')} [{s['flag']}]")

chi2_tight_q = chi2_from_groups(tight_q_results)
print(f"  Chi2 across quartiles: {chi2_tight_q}")

# Also: does tighter (lower p5_range) correlate?
# Correlation between p5_range and cont_3h for tight=True
p5_cont = [(r["p5_range"], 1 if r["cont_3h"] else 0) for r in tight_true
           if r.get("p5_range") is not None and r.get("cont_3h") is not None]
if len(p5_cont) > 10:
    corr, corr_p = stats.pointbiserialr([x[1] for x in p5_cont], [x[0] for x in p5_cont])
    corr_result = {"correlation": round(corr, 4), "p_value": round(corr_p, 6)}
else:
    corr_result = {"note": "insufficient data"}

results["tight_range_analysis"] = {
    "p5_range_stats_when_tight": tight_range_stats,
    "quartile_split": tight_q_results,
    "chi2_across_quartiles": chi2_tight_q,
    "p5_range_vs_cont3h_correlation": corr_result,
    "interpretation": "Lower p5_range = tighter consolidation. Check if Q1 (tightest) has higher cont_3h."
}

# ========== 3. CONSOLIDATION DURATION PROXY (p10_range) ==========
print("\n=== 3. p10_range quartiles ===")

p10_quartiles = quartile_split(db, "p10_range")
p10_q_results = []
for label, subset in p10_quartiles:
    s = grp_stats(subset, label)
    p10_q_results.append(s)
    print(f"  {label}: n={s['n']} cont_3h={s.get('cont_3h_rate')} mfe={s.get('avg_mfe_3h')} [{s['flag']}]")

chi2_p10 = chi2_from_groups(p10_q_results)
print(f"  Chi2: {chi2_p10}")

results["p10_range_quartiles"] = {
    "groups": p10_q_results,
    "chi2_test": chi2_p10,
    "interpretation": "Lower p10_range = tighter 10-candle consolidation. Check monotonic improvement."
}

# ========== 4. CONSOLIDATION x KZ INTERACTION ==========
print("\n=== 4. KZ interaction ===")

kz_interactions = {}
for consol_type, consol_key, consol_label in [("tight_bool", "tight", "tight"), ("consol_bool", "consol", "consol")]:
    groups = [
        grp_stats([r for r in db if r[consol_type] and r.get("kz") == True], f"{consol_label}+KZ"),
        grp_stats([r for r in db if r[consol_type] and r.get("kz") != True], f"{consol_label}+notKZ"),
        grp_stats([r for r in db if not r[consol_type] and r.get("kz") == True], f"not{consol_label}+KZ"),
        grp_stats([r for r in db if not r[consol_type] and r.get("kz") != True], f"not{consol_label}+notKZ"),
    ]
    chi2 = chi2_from_groups(groups)
    kz_interactions[consol_label] = {"groups": groups, "chi2_test": chi2}
    print(f"  --- {consol_label} x KZ ---")
    for g in groups:
        print(f"    {g['label']}: n={g['n']} cont_3h={g.get('cont_3h_rate')} [{g['flag']}]")
    print(f"    Chi2: {chi2}")

results["kz_interaction"] = kz_interactions

# ========== 5. CONSOLIDATION x D1 ALIGNMENT ==========
print("\n=== 5. D1 alignment interaction ===")

for r in db:
    d1 = r.get("d1_dir", "")
    direction = r.get("direction", "")
    r["d1_aligned"] = (d1 == direction) or (d1 == "bullish" and direction == "bullish") or (d1 == "bearish" and direction == "bearish")

d1_groups = [
    grp_stats([r for r in db if r["tight_bool"] and r["d1_aligned"]], "tight+d1_aligned"),
    grp_stats([r for r in db if r["tight_bool"] and not r["d1_aligned"]], "tight+d1_not_aligned"),
    grp_stats([r for r in db if not r["tight_bool"] and r["d1_aligned"]], "notTight+d1_aligned"),
    grp_stats([r for r in db if not r["tight_bool"] and not r["d1_aligned"]], "notTight+d1_not_aligned"),
]
chi2_d1 = chi2_from_groups(d1_groups)

print("  --- tight x d1_aligned ---")
for g in d1_groups:
    print(f"    {g['label']}: n={g['n']} cont_3h={g.get('cont_3h_rate')} [{g['flag']}]")
print(f"    Chi2: {chi2_d1}")

results["d1_interaction"] = {
    "groups": d1_groups,
    "chi2_test": chi2_d1,
}

# ========== 6. SESSION SPLIT ==========
print("\n=== 6. Session split ===")

sessions = {}
for sess in ["london", "ny"]:
    sess_data = [r for r in db if r.get("session") == sess]
    tight_in_sess = [r for r in sess_data if r["tight_bool"]]
    not_tight_in_sess = [r for r in sess_data if not r["tight_bool"]]
    sessions[sess] = {
        "total_n": len(sess_data),
        "tight_n": len(tight_in_sess),
        "tight_pct": round(len(tight_in_sess) / len(sess_data) * 100, 1) if sess_data else 0,
        "tight": grp_stats(tight_in_sess, f"{sess}_tight"),
        "not_tight": grp_stats(not_tight_in_sess, f"{sess}_notTight"),
    }
    print(f"  {sess}: total={len(sess_data)} tight={len(tight_in_sess)} ({sessions[sess]['tight_pct']}%)")
    print(f"    tight cont_3h={sessions[sess]['tight'].get('cont_3h_rate')} notTight cont_3h={sessions[sess]['not_tight'].get('cont_3h_rate')}")

# Check for other sessions
all_sessions = set(r.get("session") for r in db)
print(f"  All sessions in data: {all_sessions}")
for sess in all_sessions:
    if sess not in ["london", "ny"]:
        sess_data = [r for r in db if r.get("session") == sess]
        sessions[sess] = {
            "total_n": len(sess_data),
            "tight": grp_stats([r for r in sess_data if r["tight_bool"]], f"{sess}_tight"),
            "not_tight": grp_stats([r for r in sess_data if not r["tight_bool"]], f"{sess}_notTight"),
        }

results["session_split"] = sessions

# ========== 7. p5_char ANALYSIS ==========
print("\n=== 7. p5_char analysis ===")

p5_chars = set(r.get("p5_char") for r in db if r.get("p5_char") is not None)
print(f"  Unique p5_char values: {sorted(p5_chars)}")

p5_char_results = {}
for char in sorted(p5_chars):
    subset = [r for r in db if r.get("p5_char") == char]
    s = grp_stats(subset, char)
    p5_char_results[char] = s
    print(f"  {char}: n={s['n']} cont_3h={s.get('cont_3h_rate')} mfe={s.get('avg_mfe_3h')} mae={s.get('avg_mae_3h')} [{s['flag']}]")

# Chi2 across all p5_char groups
chi2_p5char = chi2_from_groups(list(p5_char_results.values()))
print(f"  Chi2: {chi2_p5char}")

results["p5_char_analysis"] = {
    "unique_values": sorted(p5_chars),
    "groups": p5_char_results,
    "chi2_test": chi2_p5char,
}

# ========== 8. DISCOVERY vs VALIDATION ==========
print("\n=== 8. Discovery vs Validation ===")

dv_results = {}
for period in ["disc", "val"]:
    pdata = [r for r in db if r.get("set") == period]
    print(f"\n  --- {period} (n={len(pdata)}) ---")

    # Cross-tab tight x consol
    p_tt = [r for r in pdata if r["tight_bool"] and r["consol_bool"]]
    p_tf = [r for r in pdata if r["tight_bool"] and not r["consol_bool"]]
    p_ft = [r for r in pdata if not r["tight_bool"] and r["consol_bool"]]
    p_ff = [r for r in pdata if not r["tight_bool"] and not r["consol_bool"]]
    cross = [
        grp_stats(p_tt, "tight+consol"),
        grp_stats(p_tf, "tight+notConsol"),
        grp_stats(p_ft, "notTight+consol"),
        grp_stats(p_ff, "notTight+notConsol"),
    ]
    chi2_c = chi2_from_groups(cross)
    for g in cross:
        print(f"    {g['label']}: n={g['n']} cont_3h={g.get('cont_3h_rate')} [{g['flag']}]")

    # p5_char
    p5c = {}
    for char in sorted(p5_chars):
        subset = [r for r in pdata if r.get("p5_char") == char]
        p5c[char] = grp_stats(subset, char)

    # KZ interaction (tight)
    kz_tight = [
        grp_stats([r for r in pdata if r["tight_bool"] and r.get("kz") == True], "tight+KZ"),
        grp_stats([r for r in pdata if r["tight_bool"] and r.get("kz") != True], "tight+notKZ"),
        grp_stats([r for r in pdata if not r["tight_bool"] and r.get("kz") == True], "notTight+KZ"),
        grp_stats([r for r in pdata if not r["tight_bool"] and r.get("kz") != True], "notTight+notKZ"),
    ]

    # D1 alignment
    d1_g = [
        grp_stats([r for r in pdata if r["tight_bool"] and r["d1_aligned"]], "tight+d1_aligned"),
        grp_stats([r for r in pdata if r["tight_bool"] and not r["d1_aligned"]], "tight+d1_not_aligned"),
        grp_stats([r for r in pdata if not r["tight_bool"] and r["d1_aligned"]], "notTight+d1_aligned"),
        grp_stats([r for r in pdata if not r["tight_bool"] and not r["d1_aligned"]], "notTight+d1_not_aligned"),
    ]

    # p10 quartiles
    p10_q = quartile_split(pdata, "p10_range")
    p10_qr = [grp_stats(s, l) for l, s in p10_q]

    dv_results[period] = {
        "n": len(pdata),
        "cross_tab": {"groups": cross, "chi2_test": chi2_c},
        "p5_char": p5c,
        "kz_interaction_tight": {"groups": kz_tight, "chi2_test": chi2_from_groups(kz_tight)},
        "d1_interaction": {"groups": d1_g, "chi2_test": chi2_from_groups(d1_g)},
        "p10_quartiles": {"groups": p10_qr, "chi2_test": chi2_from_groups(p10_qr)},
    }

results["discovery_vs_validation"] = dv_results

# ========== 9. VERDICT ==========
print("\n=== VERDICT ===")

# Summarize key findings
tt_rate = results["cross_tab_tight_consol"]["groups"][0].get("cont_3h_rate")
ff_rate = results["cross_tab_tight_consol"]["groups"][3].get("cont_3h_rate")
chi2_p = results["cross_tab_tight_consol"]["chi2_test"].get("p")

# Best p5_char
best_char = max(p5_char_results.items(), key=lambda x: x[1].get("cont_3h_rate", 0) if x[1]["n"] >= 30 else 0)
worst_char = min(p5_char_results.items(), key=lambda x: x[1].get("cont_3h_rate", 1) if x[1]["n"] >= 30 else 1)

# Disc vs val consistency
disc_tt = dv_results["disc"]["cross_tab"]["groups"][0].get("cont_3h_rate")
val_tt = dv_results["val"]["cross_tab"]["groups"][0].get("cont_3h_rate") if "val" in dv_results else None

verdict = {
    "tight_plus_consol_cont_3h": tt_rate,
    "neither_cont_3h": ff_rate,
    "lift_pct_points": round((tt_rate - ff_rate) * 100, 1) if tt_rate and ff_rate else None,
    "chi2_p_value": chi2_p,
    "statistically_significant": chi2_p < 0.05 if chi2_p else None,
    "best_p5_char": {"char": best_char[0], "cont_3h": best_char[1].get("cont_3h_rate"), "n": best_char[1]["n"]},
    "worst_p5_char": {"char": worst_char[0], "cont_3h": worst_char[1].get("cont_3h_rate"), "n": worst_char[1]["n"]},
    "disc_tight_consol_rate": disc_tt,
    "val_tight_consol_rate": val_tt,
    "disc_val_consistent": abs(disc_tt - val_tt) < 0.05 if disc_tt and val_tt else None,
    "summary": []
}

# Build summary sentences
if chi2_p and chi2_p < 0.05:
    verdict["summary"].append(f"Consolidation state significantly predicts continuation (p={chi2_p:.4f}).")
else:
    verdict["summary"].append(f"Consolidation state does NOT significantly predict continuation (p={chi2_p}).")

if tt_rate and ff_rate:
    verdict["summary"].append(f"tight+consol: {tt_rate:.1%} vs neither: {ff_rate:.1%} ({verdict['lift_pct_points']:+.1f} pp).")

if disc_tt and val_tt:
    if abs(disc_tt - val_tt) < 0.05:
        verdict["summary"].append(f"Effect holds in validation (disc={disc_tt:.1%}, val={val_tt:.1%}).")
    else:
        verdict["summary"].append(f"WARNING: disc/val divergence (disc={disc_tt:.1%}, val={val_tt:.1%}).")

verdict["summary"].append(f"Best p5_char: {best_char[0]} ({best_char[1].get('cont_3h_rate'):.1%}, n={best_char[1]['n']}).")

# KZ synergy
kz_tight_rate = results["kz_interaction"]["tight"]["groups"][0].get("cont_3h_rate")
kz_not_tight_rate = results["kz_interaction"]["tight"]["groups"][2].get("cont_3h_rate")
if kz_tight_rate and kz_not_tight_rate:
    verdict["summary"].append(f"tight+KZ: {kz_tight_rate:.1%} vs notTight+KZ: {kz_not_tight_rate:.1%}.")

results["verdict"] = verdict

for line in verdict["summary"]:
    print(f"  {line}")

# ========== SAVE ==========
results["metadata"] = {
    "generated": datetime.now().isoformat(),
    "source": DATA,
    "total_records": len(db),
    "tight_threshold": f">= median ({round(tight_med, 4)})",
    "consol_threshold": f">= median ({round(consol_med, 4)})",
    "note": "tight and consol are continuous scores; median split used for boolean grouping"
}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

with open(OUT, "w") as f:
    json.dump(results, f, indent=2, cls=NpEncoder)

print(f"\nSaved to {OUT}")

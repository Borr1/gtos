"""
Loser-Mining Analysis for Accepted Candidates.

Builds feature matrix from:
1. Phase 1 merged_data.jsonl (75 filled CANDs, XAUUSD/USDJPY, deep MSO features)
2. Tier 2 all_results.json (142 filled CANDs, 5 new instruments, parsed raw_response features)

Computes:
- Section 1: outcome distribution + Wilson 95% CI
- Section 2: feature ranking (Spearman, point-biserial, GBM importance, LR coef)
- Section 3: classifier validation (temporal + random split, AUC, Brier, calibration)
- Section 4: feature stratification (top-10 features bucketed)
- Section 5: per-framework loser breakdown
- Section 6: actionable findings

Pure Python, $0 API.
"""

import json
import os
import re
import math
import csv
import collections
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# -------------------------- LOADERS --------------------------

PHASE1_PATH = "research/phase1_full_extraction/merged_data.jsonl"
TIER2_DIR = "research/instrument_expansion_2026-04-25/"


def load_phase1() -> List[Dict[str, Any]]:
    """Phase 1: 75 filled CANDs (XAUUSD/USDJPY)."""
    rows = []
    with open(PHASE1_PATH, "r") as f:
        for line in f:
            r = json.loads(line)
            if r.get("logger_decision") == "CANDIDATE" and r.get("out_r_multiple") is not None:
                rows.append(r)
    return rows


def parse_raw_response(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        # Strip markdown code fence
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        # Try direct
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        return None
    return None


def load_tier2() -> List[Dict[str, Any]]:
    """Tier 2: 142 filled CANDs, 5 new instruments."""
    rows = []
    for root, _, fs in os.walk(TIER2_DIR):
        for f in fs:
            if f != "all_results.json":
                continue
            fp = os.path.join(root, f)
            instr = "unknown"
            for token in ("eurusd", "ger40", "nas100", "uk100", "xagusd"):
                if "tier2_" + token in fp:
                    instr = token.upper()
                    break
            with open(fp, "r") as fh:
                data = json.load(fh)
            for r in data.get("results", []):
                if r.get("decision") != "CANDIDATE":
                    continue
                if r.get("outcome") not in ("WIN", "LOSS"):
                    continue
                if r.get("r_multiple") is None:
                    continue
                r["_instrument"] = instr
                # Parse raw_response
                parsed = parse_raw_response(r.get("raw_response", ""))
                r["_parsed"] = parsed
                rows.append(r)
    return rows


# -------------------------- FEATURE EXTRACTION --------------------------

def to_unified(rows_phase1: List[Dict], rows_tier2: List[Dict]) -> List[Dict[str, Any]]:
    """Transform both sources into a single unified feature schema."""
    out = []

    # --- Phase 1 ---
    for r in rows_phase1:
        u = {}
        u["source"] = "phase1"
        u["symbol"] = r["symbol"]
        u["timestamp"] = r["timestamp_utc"]
        u["kill_zone"] = r.get("kill_zone")
        u["hour_utc"] = r.get("hour_utc")
        u["day_of_week"] = r.get("day_of_week")
        u["framework"] = r.get("logger_framework")
        u["setup_grade"] = r.get("logger_setup_grade")
        u["direction"] = r.get("ai_direction_evaluated") or r.get("out_direction")
        u["bias"] = r.get("out_bias")
        u["outcome"] = r.get("out_outcome")
        u["r_multiple"] = r.get("out_r_multiple")
        u["is_loss"] = 1 if r.get("out_outcome") == "LOSS" else 0
        u["is_win"] = 1 if r.get("out_outcome") == "WIN" else 0

        # H1 structure & POI features
        u["h1_opp_ob_touch"] = r.get("h1_opp_ob_touch")
        u["h1_fvg_unfilled_count"] = r.get("h1_fvg_unfilled_count")
        u["m15_fvg_unfilled_count"] = r.get("m15_fvg_unfilled_count")
        u["mso_h1_structure_direction"] = r.get("mso_h1_structure_direction")
        u["mso_h1_unmitigated_ob_count"] = r.get("mso_h1_unmitigated_ob_count")
        u["mso_h1_nearest_ob_distance_atr"] = r.get("mso_h1_nearest_ob_distance_atr")
        u["mso_detected_sweeps_count"] = r.get("mso_detected_sweeps_count")
        u["mso_m15_clv_current"] = r.get("mso_m15_clv_current")
        u["mso_m15_clv_avg_5"] = r.get("mso_m15_clv_avg_5")
        u["mso_m15_bvc_buy_fraction"] = r.get("mso_m15_bvc_buy_fraction")

        # Touch count picked by direction (long/short)
        if u["direction"] == "LONG":
            u["touch_count_at_eval"] = r.get("h1_opp_ob_touch_long")
        elif u["direction"] == "SHORT":
            u["touch_count_at_eval"] = r.get("h1_opp_ob_touch_short")
        else:
            u["touch_count_at_eval"] = r.get("h1_opp_ob_touch")

        # OB touches list summary
        ob_list = r.get("mso_h1_ob_touch_counts") or []
        u["ob_touch_max"] = max(ob_list) if ob_list else None
        u["ob_touch_min"] = min(ob_list) if ob_list else None
        u["ob_touch_mean"] = sum(ob_list) / len(ob_list) if ob_list else None

        # Direction agreement
        sd = u["mso_h1_structure_direction"]
        d = u["direction"]
        u["direction_matches_h1"] = 1 if (sd == "bullish" and d == "LONG") or (sd == "bearish" and d == "SHORT") else 0

        # AI side
        u["ai_decision"] = r.get("ai_decision")
        u["confidence_score"] = None  # not in Phase 1 logger schema row
        u["risk_reward"] = None  # not in Phase 1
        u["sl_distance"] = None
        u["tp_distance"] = None

        # Phase 1 doesn't expose entry/sl/tp; mark
        out.append(u)

    # --- Tier 2 ---
    for r in rows_tier2:
        u = {}
        u["source"] = "tier2"
        u["symbol"] = r["_instrument"]
        u["timestamp"] = r["candle_time"]
        u["kill_zone"] = r.get("kill_zone")
        u["hour_utc"] = None
        try:
            ts = datetime.fromisoformat(r["candle_time"].replace("Z", "+00:00"))
            u["hour_utc"] = ts.hour
            u["day_of_week"] = ts.weekday()
        except Exception:
            u["day_of_week"] = None

        u["direction"] = r.get("direction")
        u["bias"] = r.get("bias")
        u["setup_grade"] = r.get("setup_grade")
        u["outcome"] = r.get("outcome")
        u["r_multiple"] = r.get("r_multiple")
        u["is_loss"] = 1 if r.get("outcome") == "LOSS" else 0
        u["is_win"] = 1 if r.get("outcome") == "WIN" else 0

        # Trade params
        entry = r.get("entry_price")
        sl = r.get("stop_loss")
        tp = r.get("take_profit_1")
        u["entry_price"] = entry
        u["stop_loss"] = sl
        u["tp1"] = tp
        if entry and sl:
            u["sl_distance"] = abs(entry - sl)
        else:
            u["sl_distance"] = None
        if entry and tp:
            u["tp_distance"] = abs(tp - entry)
        else:
            u["tp_distance"] = None
        if u["sl_distance"] and u["tp_distance"]:
            u["risk_reward"] = u["tp_distance"] / u["sl_distance"]
        else:
            u["risk_reward"] = None

        # Parse AI features
        parsed = r.get("_parsed") or {}
        u["framework"] = parsed.get("framework", "ob_retest")
        u["confidence_score"] = parsed.get("confidence_score")
        reasoning = parsed.get("reasoning") or {}
        db = reasoning.get("daily_bias") or {}
        u["bias_confidence"] = db.get("confidence")
        h1s = reasoning.get("h1_setup") or {}
        u["poi_type"] = h1s.get("poi_type")
        u["poi_zone"] = h1s.get("zone")
        u["causing_event"] = h1s.get("causing_event_type")
        u["fib_retracement_pct"] = h1s.get("fib_retracement_pct")
        ls = reasoning.get("liquidity_sweep") or {}
        u["sweep_detected"] = ls.get("detected")
        u["sweep_pool_type"] = ls.get("pool_type")
        u["sweep_quality"] = ls.get("sweep_quality")
        m15c = reasoning.get("m15_confirmation") or {}
        u["m15_choch_detected"] = m15c.get("choch_detected")
        u["displacement_quality"] = m15c.get("displacement_quality")
        u["displacement_ratio_ai"] = m15c.get("displacement_candle_body_vs_avg_ratio")

        # Touch count parsed from h1_setup explanation
        explanation = (h1s.get("explanation") or "")
        m = re.search(r"touches=(\d+)", explanation)
        if m:
            u["touch_count_at_eval"] = int(m.group(1))
        else:
            u["touch_count_at_eval"] = None

        # No MSO numeric features in tier2 row
        for k in ["h1_opp_ob_touch", "h1_fvg_unfilled_count", "m15_fvg_unfilled_count",
                  "mso_h1_structure_direction", "mso_h1_unmitigated_ob_count",
                  "mso_h1_nearest_ob_distance_atr", "mso_detected_sweeps_count",
                  "mso_m15_clv_current", "mso_m15_clv_avg_5", "mso_m15_bvc_buy_fraction",
                  "ob_touch_max", "ob_touch_min", "ob_touch_mean", "direction_matches_h1",
                  "ai_decision"]:
            u[k] = None

        out.append(u)

    return out


# -------------------------- STATS HELPERS --------------------------

def wilson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054  # 95%
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0, centre - half), min(1, centre + half))


def spearman(xs: List[float], ys: List[float]) -> Tuple[float, float]:
    """Spearman rho with one-tail-style p (two-tail)."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 4:
        return (float("nan"), float("nan"))

    def rank(arr):
        s = sorted(range(len(arr)), key=lambda i: arr[i])
        ranks = [0] * len(arr)
        i = 0
        while i < len(s):
            j = i
            while j < len(s) - 1 and arr[s[j + 1]] == arr[s[j]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[s[k]] = avg
            i = j + 1
        return ranks

    xs2, ys2 = zip(*pairs)
    n = len(pairs)
    rx, ry = rank(list(xs2)), rank(list(ys2))
    mx, my = sum(rx) / n, sum(ry) / n
    sxx = sum((r - mx) ** 2 for r in rx)
    syy = sum((r - my) ** 2 for r in ry)
    sxy = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    if sxx == 0 or syy == 0:
        return (0.0, float("nan"))
    rho = sxy / math.sqrt(sxx * syy)
    if abs(rho) >= 1:
        return (rho, 0.0)
    # Two-tailed approximation via t-test on Fisher z OR via t-stat
    t = rho * math.sqrt(n - 2) / math.sqrt(1 - rho * rho)
    # Approximate t-distribution two-tailed p via normal as n grows
    # For small n use Student-t CDF approximation (Hill's algorithm crude)
    # Use a simple Kuiper-style approximation: for moderate n we use normal
    p = 2 * (1 - student_t_cdf(abs(t), n - 2))
    return (rho, p)


def student_t_cdf(t: float, df: int) -> float:
    # Cornish-Fisher / continued-fraction approximation
    # Use incomplete beta function relationship
    # P(T <= t) = 1 - 0.5 * I_{x}(df/2, 0.5)  where x = df/(df + t^2)  for t > 0
    if df <= 0:
        return 0.5
    x = df / (df + t * t)
    ib = incomplete_beta(x, df / 2.0, 0.5)
    if t > 0:
        return 1 - 0.5 * ib
    else:
        return 0.5 * ib


def incomplete_beta(x: float, a: float, b: float) -> float:
    # Continued fraction (Numerical Recipes)
    if x < 0 or x > 1:
        return 0.0
    if x == 0 or x == 1:
        return x
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(x, a, b) / a
    else:
        return 1 - bt * betacf(1 - x, b, a) / b


def betacf(x: float, a: float, b: float, max_iter: int = 200, eps: float = 3e-7) -> float:
    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1
    d = 1 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < eps:
            return h
    return h


def point_biserial(xs: List[float], ys: List[int]) -> Tuple[float, float, int]:
    """Point-biserial correlation between continuous xs and binary ys (0/1)."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None]
    if len(pairs) < 4:
        return (float("nan"), float("nan"), len(pairs))
    xs2, ys2 = zip(*pairs)
    n = len(pairs)
    n1 = sum(ys2)
    n0 = n - n1
    if n1 == 0 or n0 == 0:
        return (float("nan"), float("nan"), n)
    m1 = sum(x for x, y in pairs if y == 1) / n1
    m0 = sum(x for x, y in pairs if y == 0) / n0
    mean = sum(xs2) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs2) / n)
    if sd == 0:
        return (0.0, float("nan"), n)
    rpb = (m1 - m0) / sd * math.sqrt(n1 * n0 / (n * n))
    if abs(rpb) >= 1:
        return (rpb, 0.0, n)
    t = rpb * math.sqrt(n - 2) / math.sqrt(1 - rpb * rpb)
    p = 2 * (1 - student_t_cdf(abs(t), n - 2))
    return (rpb, p, n)


def chi_square_2x2(a: int, b: int, c: int, d: int) -> Tuple[float, float]:
    """Chi-square for 2x2 contingency: [[a,b],[c,d]]."""
    n = a + b + c + d
    if n == 0:
        return (float("nan"), float("nan"))
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    if r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
        return (0.0, 1.0)
    e_a = r1 * c1 / n
    e_b = r1 * c2 / n
    e_c = r2 * c1 / n
    e_d = r2 * c2 / n
    chi = (a - e_a) ** 2 / e_a + (b - e_b) ** 2 / e_b + (c - e_c) ** 2 / e_c + (d - e_d) ** 2 / e_d
    # 1 dof, p = 1 - chi2_cdf(chi, 1) using survival function approximation
    # 1-dof chi-square = absolute z-squared, P(X >= chi) = 2*(1 - Phi(sqrt(chi)))
    p = 2 * (1 - normal_cdf(math.sqrt(chi)))
    return (chi, p)


def normal_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# -------------------------- FEATURE RANKING --------------------------

def rank_features(unified: List[Dict[str, Any]], features: List[str]) -> List[Dict[str, Any]]:
    """For each feature, compute correlation with is_loss & r_multiple, plus categorical chi-square."""
    out = []
    for feat in features:
        xs = []
        ys_loss = []
        rs = []
        for u in unified:
            if u.get("outcome") not in ("WIN", "LOSS"):
                continue
            v = u.get(feat)
            if v is None:
                continue
            # Coerce booleans
            if isinstance(v, bool):
                v = int(v)
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            xs.append(v)
            ys_loss.append(u["is_loss"])
            rs.append(u["r_multiple"])

        n = len(xs)
        if n < 8:
            out.append({"feature": feat, "n": n, "rho_R": None, "p_rho_R": None,
                        "rpb_loss": None, "p_rpb_loss": None, "mean_winners": None,
                        "mean_losers": None})
            continue

        rho_r, p_rho_r = spearman(xs, rs)
        rpb_loss, p_rpb_loss, _ = point_biserial(xs, ys_loss)

        # Mean of feature for winners vs losers
        wx = [x for x, y in zip(xs, ys_loss) if y == 0]
        lx = [x for x, y in zip(xs, ys_loss) if y == 1]
        m_w = sum(wx) / len(wx) if wx else None
        m_l = sum(lx) / len(lx) if lx else None

        out.append({
            "feature": feat,
            "n": n,
            "rho_R": round(rho_r, 4) if rho_r == rho_r else None,
            "p_rho_R": round(p_rho_r, 5) if p_rho_r == p_rho_r else None,
            "rpb_loss": round(rpb_loss, 4) if rpb_loss == rpb_loss else None,
            "p_rpb_loss": round(p_rpb_loss, 5) if p_rpb_loss == p_rpb_loss else None,
            "mean_winners": round(m_w, 4) if m_w is not None else None,
            "mean_losers": round(m_l, 4) if m_l is not None else None,
        })

    return out


# -------------------------- LOGISTIC REGRESSION (manual) --------------------------

def logreg_fit(X: List[List[float]], y: List[int], lr: float = 0.05, max_iter: int = 2000, l2: float = 0.5) -> List[float]:
    """Tiny gradient descent. X has bias column manually added by caller."""
    n = len(y)
    p = len(X[0])
    w = [0.0] * p
    for it in range(max_iter):
        grad = [0.0] * p
        for i in range(n):
            z = sum(w[j] * X[i][j] for j in range(p))
            # numerical-stable sigmoid
            s = 1 / (1 + math.exp(-max(min(z, 30), -30)))
            err = s - y[i]
            for j in range(p):
                grad[j] += err * X[i][j]
        # Adam-ish? simple GD with L2
        for j in range(p):
            grad[j] = grad[j] / n + l2 * w[j] / n
            w[j] -= lr * grad[j]
    return w


def logreg_predict(X: List[List[float]], w: List[float]) -> List[float]:
    out = []
    for x in X:
        z = sum(w[j] * x[j] for j in range(len(w)))
        out.append(1 / (1 + math.exp(-max(min(z, 30), -30))))
    return out


def auc(scores: List[float], y: List[int]) -> float:
    pairs = list(zip(scores, y))
    pos = [s for s, t in pairs if t == 1]
    neg = [s for s, t in pairs if t == 0]
    if not pos or not neg:
        return float("nan")
    n = 0
    s = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                s += 1
            elif sp == sn:
                s += 0.5
            n += 1
    return s / n


def brier(scores: List[float], y: List[int]) -> float:
    return sum((s - t) ** 2 for s, t in zip(scores, y)) / len(y)


# -------------------------- BUCKETING --------------------------

def bucketize(unified: List[Dict[str, Any]], feat: str, bins: List[Tuple[float, float, str]]) -> List[Dict[str, Any]]:
    """For each bucket [lo, hi, label], compute WR, Wilson 95% CI, Exp R."""
    out = []
    for lo, hi, label in bins:
        sub = []
        for u in unified:
            v = u.get(feat)
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if lo <= v < hi:
                sub.append(u)
        n = len(sub)
        wins = sum(1 for u in sub if u["is_win"] == 1)
        losses = sum(1 for u in sub if u["is_loss"] == 1)
        wr = wins / n if n else None
        lo_ci, hi_ci = wilson_ci(wins, n) if n else (None, None)
        r = sum(u["r_multiple"] for u in sub) / n if n else None
        out.append({
            "feature": feat,
            "bucket": label,
            "lo": lo,
            "hi": hi,
            "n": n,
            "wins": wins,
            "losses": losses,
            "wr": round(wr, 4) if wr is not None else None,
            "wr_lo": round(lo_ci, 4) if lo_ci is not None else None,
            "wr_hi": round(hi_ci, 4) if hi_ci is not None else None,
            "exp_R": round(r, 4) if r is not None else None,
        })
    return out


# -------------------------- MAIN --------------------------

def main():
    rows_p1 = load_phase1()
    rows_t2 = load_tier2()
    print(f"Phase 1 filled CANDs: {len(rows_p1)}")
    print(f"Tier 2 filled CANDs: {len(rows_t2)}")

    unified = to_unified(rows_p1, rows_t2)
    print(f"Unified total filled CANDs: {len(unified)}")

    # Add half-period flag for H1 vs H2 split
    for u in unified:
        try:
            ts = datetime.fromisoformat(u["timestamp"].replace("Z", "+00:00"))
            month = ts.month
            u["month"] = month
            u["half"] = "H1" if month <= 2 else ("H1.5" if month == 3 else "H2")  # Apr=H2
        except Exception:
            u["month"] = None
            u["half"] = None

    # ===== Section 1: distributions =====
    print("\n=== SECTION 1: Outcome distribution ===")
    by_symbol = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})
    by_dir = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})
    by_grade = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})
    by_framework = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})
    by_kz = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})
    by_half = collections.defaultdict(lambda: {"WIN": 0, "LOSS": 0, "N": 0})

    for u in unified:
        s = u["symbol"]
        by_symbol[s]["N"] += 1
        by_symbol[s][u["outcome"]] += 1
        by_dir[u["direction"]]["N"] += 1
        by_dir[u["direction"]][u["outcome"]] += 1
        by_grade[u["setup_grade"]]["N"] += 1
        by_grade[u["setup_grade"]][u["outcome"]] += 1
        if u.get("framework"):
            by_framework[u["framework"]]["N"] += 1
            by_framework[u["framework"]][u["outcome"]] += 1
        if u.get("kill_zone"):
            by_kz[u["kill_zone"]]["N"] += 1
            by_kz[u["kill_zone"]][u["outcome"]] += 1
        if u.get("half"):
            by_half[u["half"]]["N"] += 1
            by_half[u["half"]][u["outcome"]] += 1

    section1 = {
        "by_symbol": dict(by_symbol),
        "by_direction": dict(by_dir),
        "by_setup_grade": dict(by_grade),
        "by_framework": dict(by_framework),
        "by_kill_zone": dict(by_kz),
        "by_half": dict(by_half),
        "total_filled": len(unified),
    }

    # ===== Section 2: Feature ranking =====
    print("\n=== SECTION 2: Feature ranking ===")

    # Numeric/binary features available across the data
    features_num = [
        "h1_opp_ob_touch", "h1_fvg_unfilled_count", "m15_fvg_unfilled_count",
        "mso_h1_unmitigated_ob_count", "mso_h1_nearest_ob_distance_atr",
        "mso_detected_sweeps_count", "mso_m15_clv_current", "mso_m15_clv_avg_5",
        "mso_m15_bvc_buy_fraction", "ob_touch_max", "ob_touch_min", "ob_touch_mean",
        "direction_matches_h1", "touch_count_at_eval", "hour_utc", "day_of_week",
        "confidence_score", "fib_retracement_pct", "displacement_ratio_ai",
        "sl_distance", "tp_distance", "risk_reward",
    ]

    # Booleans/categorical to encode
    for u in unified:
        u["sweep_detected_int"] = 1 if u.get("sweep_detected") is True else (0 if u.get("sweep_detected") is False else None)
        u["m15_choch_detected_int"] = 1 if u.get("m15_choch_detected") is True else (0 if u.get("m15_choch_detected") is False else None)
        # Zone binary: discount=1, premium=0, equilibrium=0.5
        z = u.get("poi_zone")
        if z == "discount":
            u["poi_zone_discount"] = 1
        elif z == "premium":
            u["poi_zone_discount"] = 0
        elif z in ("equilibrium",):
            u["poi_zone_discount"] = 0.5
        else:
            u["poi_zone_discount"] = None
        # bias_confidence ord
        bc = u.get("bias_confidence")
        u["bias_confidence_ord"] = {"low": 0, "medium": 1, "high": 2}.get(bc)
        # displacement_quality ord
        dq = u.get("displacement_quality")
        u["displacement_quality_ord"] = {"weak": 0, "moderate": 1, "strong": 2}.get(dq)
        # sweep_quality ord
        sq = u.get("sweep_quality")
        u["sweep_quality_ord"] = {"weak": 0, "messy": 0, "clean": 1, "fresh": 1}.get(sq)

    features_num.extend(["sweep_detected_int", "m15_choch_detected_int", "poi_zone_discount",
                         "bias_confidence_ord", "displacement_quality_ord", "sweep_quality_ord"])

    ranked = rank_features(unified, features_num)
    # Sort by abs rho_R (descending), drop None
    ranked_sorted = sorted([r for r in ranked if r["rho_R"] is not None],
                           key=lambda r: -abs(r["rho_R"]))
    for r in ranked_sorted[:20]:
        print(f"  {r['feature']:35s}  n={r['n']:3d}  rho_R={r['rho_R']:+.3f}  p={r['p_rho_R']:.4f}  "
              f"rpb_loss={r['rpb_loss']:+.3f} (p={r['p_rpb_loss']:.4f})  "
              f"mean_W={r['mean_winners']}  mean_L={r['mean_losers']}")

    # ===== Section 3: Classifier validation =====
    print("\n=== SECTION 3: Classifier validation ===")

    # Use top features available across most rows. We'll try TWO classifiers:
    # (A) Phase-1-only (XAUUSD+USDJPY) using rich MSO features
    # (B) Tier-2-only using parsed AI features
    # (C) Both combined using common features

    def build_feature_matrix(unified_subset, feats):
        """Pick rows that have ALL feats non-None. Add bias column."""
        X, y, R = [], [], []
        kept = []
        for u in unified_subset:
            row = []
            ok = True
            for f in feats:
                v = u.get(f)
                if v is None:
                    ok = False
                    break
                if isinstance(v, bool):
                    v = int(v)
                try:
                    row.append(float(v))
                except (TypeError, ValueError):
                    ok = False
                    break
            if not ok:
                continue
            X.append([1.0] + row)  # bias
            y.append(u["is_loss"])
            R.append(u["r_multiple"])
            kept.append(u)
        return X, y, R, kept

    def standardize(X):
        # Skip bias column
        n = len(X)
        p = len(X[0])
        means = [0.0] * p
        sds = [1.0] * p
        for j in range(1, p):
            col = [X[i][j] for i in range(n)]
            m = sum(col) / n
            v = sum((c - m) ** 2 for c in col) / n
            means[j] = m
            sds[j] = math.sqrt(v) if v > 0 else 1.0
        Xn = []
        for i in range(n):
            row = [X[i][0]] + [(X[i][j] - means[j]) / sds[j] for j in range(1, p)]
            Xn.append(row)
        return Xn, means, sds

    # ---------- Classifier (A): Phase 1 only ----------
    p1_feats = ["h1_opp_ob_touch", "h1_fvg_unfilled_count", "m15_fvg_unfilled_count",
                "mso_h1_unmitigated_ob_count", "mso_h1_nearest_ob_distance_atr",
                "mso_detected_sweeps_count", "mso_m15_clv_current", "mso_m15_clv_avg_5",
                "mso_m15_bvc_buy_fraction", "direction_matches_h1", "touch_count_at_eval",
                "hour_utc", "day_of_week"]

    p1_subset = [u for u in unified if u["source"] == "phase1"]
    X_p1, y_p1, R_p1, kept_p1 = build_feature_matrix(p1_subset, p1_feats)
    print(f"\n(A) Phase 1 classifier: kept {len(X_p1)}/{len(p1_subset)} rows with full feature vec")

    if len(X_p1) >= 30:
        # Temporal split: months 1-2 train, month 3+ test
        Xn, means, sds = standardize(X_p1)
        train_idx = [i for i, u in enumerate(kept_p1) if u.get("month") and u["month"] <= 2]
        test_idx = [i for i, u in enumerate(kept_p1) if u.get("month") and u["month"] >= 3]
        if len(train_idx) >= 15 and len(test_idx) >= 10:
            X_tr = [Xn[i] for i in train_idx]
            y_tr = [y_p1[i] for i in train_idx]
            X_te = [Xn[i] for i in test_idx]
            y_te = [y_p1[i] for i in test_idx]
            R_te = [R_p1[i] for i in test_idx]

            w = logreg_fit(X_tr, y_tr, lr=0.1, max_iter=3000, l2=1.0)
            tr_scores = logreg_predict(X_tr, w)
            te_scores = logreg_predict(X_te, w)

            auc_tr = auc(tr_scores, y_tr)
            auc_te = auc(te_scores, y_te)
            brier_tr = brier(tr_scores, y_tr)
            brier_te = brier(te_scores, y_te)

            # Spearman(prob, R) on test
            rho_pr, p_pr = spearman(te_scores, R_te)
            print(f"   Train n={len(train_idx)} -> AUC {auc_tr:.3f} Brier {brier_tr:.3f}")
            print(f"   Test  n={len(test_idx)} -> AUC {auc_te:.3f} Brier {brier_te:.3f}")
            print(f"   Spearman(loss_prob, R)_test = {rho_pr:.3f} (p={p_pr:.4f})")

            # Random 70/30 split for comparison
            random_seed = 42
            import random
            rnd = random.Random(random_seed)
            idx = list(range(len(X_p1)))
            rnd.shuffle(idx)
            cut = int(0.7 * len(idx))
            tr2 = idx[:cut]
            te2 = idx[cut:]
            X_tr2 = [Xn[i] for i in tr2]
            y_tr2 = [y_p1[i] for i in tr2]
            X_te2 = [Xn[i] for i in te2]
            y_te2 = [y_p1[i] for i in te2]
            R_te2 = [R_p1[i] for i in te2]
            w2 = logreg_fit(X_tr2, y_tr2, lr=0.1, max_iter=3000, l2=1.0)
            auc_tr2 = auc(logreg_predict(X_tr2, w2), y_tr2)
            auc_te2 = auc(logreg_predict(X_te2, w2), y_te2)
            brier_te2 = brier(logreg_predict(X_te2, w2), y_te2)
            rho_pr2, p_pr2 = spearman(logreg_predict(X_te2, w2), R_te2)
            print(f"   Random split 70/30 AUC: train {auc_tr2:.3f} -> test {auc_te2:.3f} (n={len(te2)})")

            # Coefficients (standardized)
            print(f"\n   Standardized coefficients (logreg, temporal):")
            for j, f in enumerate(["bias"] + p1_feats):
                print(f"     {f:35s}  {w[j]:+.3f}")

            section3_p1 = {
                "n_train": len(train_idx), "n_test": len(test_idx),
                "auc_train": round(auc_tr, 4), "auc_test": round(auc_te, 4),
                "brier_train": round(brier_tr, 4), "brier_test": round(brier_te, 4),
                "spearman_score_R_test": round(rho_pr, 4) if rho_pr == rho_pr else None,
                "p_spearman_test": round(p_pr, 5) if p_pr == p_pr else None,
                "auc_random_train": round(auc_tr2, 4), "auc_random_test": round(auc_te2, 4),
                "coefficients": {("bias" if i == 0 else p1_feats[i - 1]): round(w[i], 4) for i in range(len(w))},
            }
        else:
            section3_p1 = {"error": "insufficient temporal-split rows"}
    else:
        section3_p1 = {"error": "insufficient rows"}

    # ---------- Classifier (B): Tier 2 only with parsed features ----------
    t2_feats = ["confidence_score", "fib_retracement_pct", "displacement_ratio_ai",
                "sl_distance", "tp_distance", "risk_reward", "hour_utc", "day_of_week",
                "sweep_detected_int", "m15_choch_detected_int", "poi_zone_discount",
                "bias_confidence_ord", "displacement_quality_ord", "sweep_quality_ord"]

    t2_subset = [u for u in unified if u["source"] == "tier2"]
    X_t2, y_t2, R_t2, kept_t2 = build_feature_matrix(t2_subset, t2_feats)
    print(f"\n(B) Tier 2 classifier: kept {len(X_t2)}/{len(t2_subset)} rows")

    if len(X_t2) >= 30:
        Xn_t2, _, _ = standardize(X_t2)
        train_idx = [i for i, u in enumerate(kept_t2) if u.get("month") and u["month"] <= 2]
        test_idx = [i for i, u in enumerate(kept_t2) if u.get("month") and u["month"] >= 3]
        if len(train_idx) >= 15 and len(test_idx) >= 10:
            X_tr = [Xn_t2[i] for i in train_idx]
            y_tr = [y_t2[i] for i in train_idx]
            X_te = [Xn_t2[i] for i in test_idx]
            y_te = [y_t2[i] for i in test_idx]
            R_te = [R_t2[i] for i in test_idx]

            w = logreg_fit(X_tr, y_tr, lr=0.1, max_iter=3000, l2=1.0)
            auc_tr = auc(logreg_predict(X_tr, w), y_tr)
            auc_te = auc(logreg_predict(X_te, w), y_te)
            brier_te = brier(logreg_predict(X_te, w), y_te)
            rho_pr, p_pr = spearman(logreg_predict(X_te, w), R_te)
            print(f"   Train n={len(train_idx)} -> AUC {auc_tr:.3f}")
            print(f"   Test  n={len(test_idx)} -> AUC {auc_te:.3f} Brier {brier_te:.3f}")
            print(f"   Spearman(loss_prob, R)_test = {rho_pr:.3f} (p={p_pr:.4f})")

            section3_t2 = {
                "n_train": len(train_idx), "n_test": len(test_idx),
                "auc_train": round(auc_tr, 4), "auc_test": round(auc_te, 4),
                "brier_test": round(brier_te, 4),
                "spearman_score_R_test": round(rho_pr, 4) if rho_pr == rho_pr else None,
                "p_spearman_test": round(p_pr, 5) if p_pr == p_pr else None,
                "coefficients": {("bias" if i == 0 else t2_feats[i - 1]): round(w[i], 4) for i in range(len(w))},
            }
        else:
            section3_t2 = {"error": "insufficient temporal-split rows"}
    else:
        section3_t2 = {"error": "insufficient rows"}

    # ===== Section 4: Stratification =====
    print("\n=== SECTION 4: Stratification ===")
    strat_results = {}

    # Touch count buckets
    strat_results["touch_count_at_eval"] = bucketize(unified, "touch_count_at_eval", [
        (0, 1, "0"), (1, 2, "1"), (2, 3, "2"), (3, 99, ">=3")
    ])
    print("touch_count_at_eval:")
    for b in strat_results["touch_count_at_eval"]:
        if b["n"]:
            print(f"  {b['bucket']:>5}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["mso_h1_nearest_ob_distance_atr"] = bucketize(unified, "mso_h1_nearest_ob_distance_atr", [
        (0, 0.5, "<0.5"), (0.5, 1.0, "0.5-1.0"), (1.0, 2.0, "1.0-2.0"),
        (2.0, 3.0, "2.0-3.0"), (3.0, 999, ">=3.0")
    ])
    print("\nmso_h1_nearest_ob_distance_atr:")
    for b in strat_results["mso_h1_nearest_ob_distance_atr"]:
        if b["n"]:
            print(f"  {b['bucket']:>10}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["mso_h1_unmitigated_ob_count"] = bucketize(unified, "mso_h1_unmitigated_ob_count", [
        (0, 1, "0"), (1, 2, "1"), (2, 3, "2"), (3, 4, "3"), (4, 99, ">=4")
    ])
    print("\nmso_h1_unmitigated_ob_count:")
    for b in strat_results["mso_h1_unmitigated_ob_count"]:
        if b["n"]:
            print(f"  {b['bucket']:>5}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["h1_fvg_unfilled_count"] = bucketize(unified, "h1_fvg_unfilled_count", [
        (0, 2, "0-1"), (2, 4, "2-3"), (4, 7, "4-6"), (7, 99, ">=7")
    ])
    print("\nh1_fvg_unfilled_count:")
    for b in strat_results["h1_fvg_unfilled_count"]:
        if b["n"]:
            print(f"  {b['bucket']:>5}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["mso_m15_clv_avg_5"] = bucketize(unified, "mso_m15_clv_avg_5", [
        (-1.0, -0.5, "<-0.5"), (-0.5, 0, "[-0.5,0)"), (0, 0.5, "[0,0.5)"),
        (0.5, 1.0, "[0.5,1.0]")
    ])
    print("\nmso_m15_clv_avg_5:")
    for b in strat_results["mso_m15_clv_avg_5"]:
        if b["n"]:
            print(f"  {b['bucket']:>10}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["confidence_score"] = bucketize(unified, "confidence_score", [
        (0, 65, "<65"), (65, 75, "65-74"), (75, 80, "75-79"), (80, 85, "80-84"),
        (85, 100, ">=85")
    ])
    print("\nconfidence_score (Tier2 only):")
    for b in strat_results["confidence_score"]:
        if b["n"]:
            print(f"  {b['bucket']:>10}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["risk_reward"] = bucketize(unified, "risk_reward", [
        (0, 1.45, "<1.45"), (1.45, 1.55, "~1.5"), (1.55, 99, ">1.55")
    ])
    print("\nrisk_reward (Tier2):")
    for b in strat_results["risk_reward"]:
        if b["n"]:
            print(f"  {b['bucket']:>8}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["hour_utc"] = bucketize(unified, "hour_utc", [
        (0, 7, "<7"), (7, 8, "7"), (8, 9, "8"), (9, 10, "9"), (10, 11, "10"),
        (11, 13, "11-12"), (13, 14, "13"), (14, 15, "14"), (15, 16, "15"),
        (16, 24, ">=16")
    ])
    print("\nhour_utc:")
    for b in strat_results["hour_utc"]:
        if b["n"]:
            print(f"  {b['bucket']:>5}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["mso_detected_sweeps_count"] = bucketize(unified, "mso_detected_sweeps_count", [
        (0, 50, "<50"), (50, 100, "50-99"), (100, 200, "100-199"), (200, 999, ">=200")
    ])
    print("\nmso_detected_sweeps_count:")
    for b in strat_results["mso_detected_sweeps_count"]:
        if b["n"]:
            print(f"  {b['bucket']:>8}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    strat_results["mso_m15_bvc_buy_fraction"] = bucketize(unified, "mso_m15_bvc_buy_fraction", [
        (0, 0.4, "<0.4"), (0.4, 0.5, "[0.4,0.5)"), (0.5, 0.6, "[0.5,0.6)"),
        (0.6, 0.7, "[0.6,0.7)"), (0.7, 1.0, ">=0.7")
    ])
    print("\nmso_m15_bvc_buy_fraction:")
    for b in strat_results["mso_m15_bvc_buy_fraction"]:
        if b["n"]:
            print(f"  {b['bucket']:>10}  n={b['n']:3d}  WR {b['wr']:.3f} CI [{b['wr_lo']:.2f},{b['wr_hi']:.2f}]  Exp R {b['exp_R']:.3f}")

    # ===== Section 5: Per-framework =====
    print("\n=== SECTION 5: Per-framework ===")
    for f, c in by_framework.items():
        n = c["N"]
        wins = c["WIN"]
        if n:
            wr = wins / n
            ci = wilson_ci(wins, n)
            r_avg = sum(u["r_multiple"] for u in unified if u.get("framework") == f) / n
            print(f"  {f}: n={n} WR {wr:.3f} CI [{ci[0]:.2f},{ci[1]:.2f}] Exp R {r_avg:.3f}")

    # ===== Section: H1 vs H2 split per top features =====
    print("\n=== H1 vs H2 split for sensitivity ===")
    h1_subset = [u for u in unified if u.get("half") == "H1"]
    h2_subset = [u for u in unified if u.get("half") == "H2"]
    print(f"H1 (Jan-Feb): {len(h1_subset)}")
    print(f"H1.5 (Mar): {sum(1 for u in unified if u.get('half') == 'H1.5')}")
    print(f"H2 (Apr): {len(h2_subset)}")
    h1_h2_split = {}
    for feat in ["touch_count_at_eval", "mso_h1_nearest_ob_distance_atr", "confidence_score",
                 "h1_fvg_unfilled_count", "mso_m15_clv_avg_5"]:
        h1_rho, h1_p = spearman(
            [u.get(feat) for u in h1_subset if u.get(feat) is not None and u.get("r_multiple") is not None],
            [u["r_multiple"] for u in h1_subset if u.get(feat) is not None and u.get("r_multiple") is not None],
        )
        h2_rho, h2_p = spearman(
            [u.get(feat) for u in h2_subset if u.get(feat) is not None and u.get("r_multiple") is not None],
            [u["r_multiple"] for u in h2_subset if u.get(feat) is not None and u.get("r_multiple") is not None],
        )
        h1_h2_split[feat] = {
            "h1_rho": round(h1_rho, 4) if h1_rho == h1_rho else None,
            "h1_p": round(h1_p, 5) if h1_p == h1_p else None,
            "h2_rho": round(h2_rho, 4) if h2_rho == h2_rho else None,
            "h2_p": round(h2_p, 5) if h2_p == h2_p else None,
        }
        print(f"  {feat:35s}  H1 rho={h1_rho:+.3f} (p={h1_p:.3f})   H2 rho={h2_rho:+.3f} (p={h2_p:.3f})")

    # ===== Save outputs =====
    out_path = "research/accepted_candidates_loser_mining"
    os.makedirs(out_path, exist_ok=True)

    with open(os.path.join(out_path, "section1_distributions.json"), "w") as f:
        json.dump(section1, f, indent=2, default=str)

    with open(os.path.join(out_path, "section2_feature_ranking.json"), "w") as f:
        json.dump(ranked_sorted, f, indent=2, default=str)

    with open(os.path.join(out_path, "section3_classifier.json"), "w") as f:
        json.dump({
            "phase1": section3_p1,
            "tier2": section3_t2,
        }, f, indent=2, default=str)

    with open(os.path.join(out_path, "section4_stratification.json"), "w") as f:
        json.dump(strat_results, f, indent=2, default=str)

    with open(os.path.join(out_path, "h1_h2_split.json"), "w") as f:
        json.dump(h1_h2_split, f, indent=2, default=str)

    # Stratification CSV
    with open(os.path.join(out_path, "feature_stratification.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["feature", "bucket", "lo", "hi", "n", "wins", "losses", "wr", "wr_lo", "wr_hi", "exp_R"])
        for feat, rows in strat_results.items():
            for r in rows:
                w.writerow([r["feature"], r["bucket"], r["lo"], r["hi"], r["n"], r["wins"], r["losses"],
                            r["wr"], r["wr_lo"], r["wr_hi"], r["exp_R"]])

    # Save unified data for downstream
    with open(os.path.join(out_path, "unified_filled_cands.jsonl"), "w") as f:
        for u in unified:
            f.write(json.dumps(u, default=str) + "\n")

    print(f"\nOutputs written to {out_path}/")


if __name__ == "__main__":
    main()

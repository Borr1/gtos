#!/usr/bin/env python3
"""A1-OPEN (a1b), step 2: the clean-room corrected null, generalized and re-run per affected arm.

Recipe (identical in posture to ``a1_corrected_null_v2.py``, which derived and defended it):

  * independent fold segments (the concatenation seams are physically real);
  * within-fold AR(1) at the pooled within-fold lag-1 rho, model risk spanned by a rho grid
    {max(rho-SE,0), rho, min(rho+SE,0.95), full-series lag-1} — the same grid rule the clean-room
    used (its grid {0.197, 0.372, 0.489, 0.548} falls out of this rule on the breaker's series);
  * per-fold scale; innovations Gaussian OR resampled standardized AR residuals (skew kept);
  * statistic T = mean / (sd_ddof1 / sqrt(n)) on the pooling-weighted series (whose plain mean IS
    the gate's pooled statistic);
  * p = P_H0(T >= T_obs), add-one, 3 seeds per variant, PRIMARY p = max over (rho x innovation)
    variants — the spec's own both_conservative philosophy applied to model risk.

Generalizations beyond the breaker (documented, deterministic):
  * folds with 0 evaluable days are dropped (contribute nothing to the series);
  * per-fold scale uses the fold's own sd for folds with >= MIN_DAYS_OWN_SD days; shorter folds
    (including 1-day folds, whose sd is undefined/0) use the pooled within-fold sd, df-weighted
    across folds with >= 2 days.  A 1-day segment is a single stationary draw at that scale;
  * rho pairs pool across folds with >= 2 days; residuals pool across folds with >= 3 days.

Chunk size is held at 100_000 like the clean-room so the breaker rerun consumes the RNG stream
identically and must reproduce A1_CORRECTED_NULL_V2.json's counts exactly (a self-check that the
generalization did not drift).  Memory stays < ~400 MB (largest arm: n=184, chunk x (n + burn)).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CAP_CS = HERE / "A1_CAPTURED_SERIES.json"
CAP_AU = HERE / "A1B_AU_CAPTURED_SERIES.json"
OUT = HERE / "A1B_CORRECTED_NULL_RESULTS.json"

SEEDS = (9101, 9102, 9103)
CHUNK = 100_000
BURN = 30
MIN_DAYS_OWN_SD = 5


# ------------------------------------------------------------------ diagnostics --
def fold_slices(seg_lens: list[int]) -> list[slice]:
    out, i = [], 0
    for L in seg_lens:
        out.append(slice(i, i + L))
        i += L
    return out


def within_fold_stats(x: np.ndarray, seg_lens: list[int]) -> dict:
    """Pooled within-fold lag-1 rho, SE, per-fold scales (with short-fold fallback),
    standardized AR residual pool.  Mirrors a1_corrected_null_v2.within_fold_stats and
    reduces to it exactly when every fold has >= MIN_DAYS_OWN_SD days."""
    slices = [sl for sl in fold_slices(seg_lens) if sl.stop > sl.start]
    rho_num = rho_den = 0.0
    n_pairs = 0
    for sl in slices:
        if sl.stop - sl.start < 2:
            continue
        seg = x[sl] - x[sl].mean()
        rho_num += float((seg[:-1] * seg[1:]).sum())
        rho_den += float((seg * seg).sum())
        n_pairs += (sl.stop - sl.start) - 1
    if rho_den <= 0 or n_pairs < 2:
        raise ValueError("cannot estimate within-fold rho")
    rho_w = rho_num / rho_den
    se_rho = math.sqrt(max(1.0 - rho_w**2, 1e-12) / n_pairs)

    # pooled within-fold sd (df-weighted) for the short-fold fallback
    ss = 0.0
    df = 0
    for sl in slices:
        L = sl.stop - sl.start
        if L >= 2:
            seg = x[sl] - x[sl].mean()
            ss += float((seg * seg).sum())
            df += L - 1
    pooled_sd = math.sqrt(ss / df)

    fold_sds = []
    sd_basis = []
    for sl in slices:
        L = sl.stop - sl.start
        if L >= MIN_DAYS_OWN_SD:
            fold_sds.append(float(x[sl].std(ddof=0)))
            sd_basis.append("own")
        else:
            fold_sds.append(pooled_sd)
            sd_basis.append("pooled_within_fold")

    resid_pool = []
    for sl in slices:
        L = sl.stop - sl.start
        if L >= 3:
            seg = x[sl] - x[sl].mean()
            s = float(x[sl].std(ddof=0))
            if s > 0:
                r = seg[1:] - rho_w * seg[:-1]
                resid_pool.extend((r / (s * math.sqrt(max(1 - rho_w**2, 1e-12)))).tolist())
    resid = np.asarray(resid_pool)
    resid = (resid - resid.mean()) / resid.std(ddof=0)

    d = x - x.mean()
    lag1_full = float(np.dot(d[:-1], d[1:]) / np.dot(d, d))

    return {"rho_within": rho_w, "se_rho": se_rho, "n_pairs": n_pairs,
            "fold_sds": fold_sds, "fold_sd_basis": sd_basis,
            "pooled_within_sd": pooled_sd, "lag1_full_series": lag1_full,
            "resid_skew": float(((resid - resid.mean()) ** 3).mean() / resid.std() ** 3),
            "resid": resid,
            "seg_lens_used": [sl.stop - sl.start for sl in slices]}


# ------------------------------------------------- fitted-model calibration --
def calibrated_p(x: np.ndarray, seg_lens: list[int], rho: float,
                 fold_sds: list[float], resid: np.ndarray | None,
                 n_sims: int, seed: int) -> dict:
    n = x.size
    t_obs = float(x.mean() / (x.std(ddof=1) / math.sqrt(n)))
    rng = np.random.default_rng(seed)
    lens = [L for L in seg_lens if L > 0]
    count = 0
    done = 0
    while done < n_sims:
        m = min(CHUNK, n_sims - done)
        cols = []
        for L, s_f in zip(lens, fold_sds):
            T = L + BURN
            if resid is None:
                e = rng.standard_normal((m, T))
            else:
                e = resid[rng.integers(0, resid.size, size=(m, T))]
            z = np.empty((m, T))
            z[:, 0] = e[:, 0]
            for t in range(1, T):
                z[:, t] = rho * z[:, t - 1] + e[:, t]
            seg = z[:, BURN:]
            seg = seg * (s_f * math.sqrt(1 - rho * rho))
            cols.append(seg)
        xs = np.concatenate(cols, axis=1)
        t_sim = xs.mean(axis=1) / (xs.std(axis=1, ddof=1) / math.sqrt(n))
        count += int(np.count_nonzero(t_sim >= t_obs))
        done += m
        del cols, xs, t_sim
    return {"rho": rho, "seed": seed, "n_sims": int(n_sims), "t_obs": t_obs,
            "count_ge": int(count), "p_add_one": (1 + count) / (n_sims + 1)}


def corrected_p_for_arm(series: list[float], seg_lens: list[int],
                        n_sims_per_seed: int) -> dict:
    x = np.asarray(series, dtype=float)
    assert x.size == sum(seg_lens), (x.size, seg_lens)
    diag = within_fold_stats(x, seg_lens)
    resid = diag.pop("resid")
    rho_w, se = diag["rho_within"], diag["se_rho"]
    rho_grid = sorted({round(max(rho_w - se, 0.0), 3), round(rho_w, 3),
                       round(min(rho_w + se, 0.95), 3),
                       round(max(diag["lag1_full_series"], 0.0), 3)})
    variants = []
    for rho in rho_grid:
        for law, rz in (("gaussian", None), ("residual_bootstrap", resid)):
            runs = [calibrated_p(x, diag["seg_lens_used"], rho, diag["fold_sds"],
                                 rz, n_sims_per_seed, seed) for seed in SEEDS]
            pooled_count = sum(r["count_ge"] for r in runs)
            pooled_n = sum(r["n_sims"] for r in runs)
            variants.append({
                "rho": rho, "innovations": law,
                "per_seed": [{k: r[k] for k in ("seed", "count_ge", "p_add_one")}
                             for r in runs],
                "pooled": {"n_sims": pooled_n, "count_ge": pooled_count,
                           "p_add_one": (1 + pooled_count) / (pooled_n + 1)},
            })
    pooled_ps = [v["pooled"]["p_add_one"] for v in variants]
    worst = max(variants, key=lambda v: v["pooled"]["p_add_one"])
    return {
        "diagnostics": diag,
        "rho_grid": rho_grid,
        "variants": variants,
        "corrected_p": max(pooled_ps),
        "corrected_p_min_variant": min(pooled_ps),
        "argmax_variant": {"rho": worst["rho"], "innovations": worst["innovations"]},
        "t_obs": float(x.mean() / (x.std(ddof=1) / math.sqrt(x.size))),
        "n": int(x.size),
        "n_sims_total_per_variant": n_sims_per_seed * len(SEEDS),
    }


# ---------------------------------------------------------- BH substitution --
def bh_substitute(co_pvalues: dict[str, float | None], target: str,
                  corrected_p: float, m_family: int, alpha: float = 0.10) -> dict:
    """Reproduce the receipt's multiplicity block with the corrected p substituted for the
    target only; co-judged members stay at their published p; members without a computed
    null pad at 1.0 (the gate's own convention)."""
    sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
    from src.research_infra.walkforward.stats import benjamini_hochberg
    names = sorted(co_pvalues)
    ps = []
    for nm in names:
        if nm == target:
            ps.append(float(corrected_p))
        else:
            v = co_pvalues[nm]
            ps.append(float(v) if isinstance(v, (int, float)) and math.isfinite(v) else 1.0)
    n_pad = m_family - len(ps)
    assert n_pad >= 0, (m_family, len(ps))
    ps_full = ps + [1.0] * n_pad
    res = benjamini_hochberg(ps_full, alpha)
    qi = res["qvalues"][names.index(target)]
    return {"m": m_family, "alpha": alpha, "q_value": qi,
            "rejected": bool(res["rejected"][names.index(target)]),
            "k": res["k"]}


# ----------------------------------------------------------------------- run --
def main() -> int:
    out = {
        "schema": "gtos-a1b-corrected-null-results-v1",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "recipe": "clean-room corrected null (A1_CLEANROOM_NULL_DERIVATION.md section 5), "
                  "generalized to arbitrary fold structures; primary p = max over "
                  "(rho grid x innovation law) variants; 3 seeds per variant",
        "arms": [],
    }

    # ---- 1. the breaker (CS receipt, family 59) — reproduces the clean-room -------
    cs = json.loads(CAP_CS.read_text())
    call = cs["captured"]["combined_null_calls"][0]
    series = [float(v) for v in call["series"]]
    seg_lens = [11, 11, 9]
    res = corrected_p_for_arm(series, seg_lens, 700_000)
    sub = bh_substitute({"cq_current_breaker_re_entry_inverted_5d_stop_0p25d": None},
                        "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
                        res["corrected_p"], 59)
    row = {
        "member": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
        "receipt": "wave19-breaker-folds phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json",
        "publishing_session": "CS",
        "published": {"p_raw": 0.0025997400259974, "q_value": 0.1533846615338466,
                      "verdict": "REJECT", "m": 59},
        "corrected": {**{k: res[k] for k in ("corrected_p", "corrected_p_min_variant",
                                              "argmax_variant", "t_obs", "n",
                                              "rho_grid", "n_sims_total_per_variant")},
                      "diagnostics": res["diagnostics"], "bh": sub},
        "variants": res["variants"],
        "cleanroom_reference": {"expected_p": 0.0013033,
                                "expected_argmax_rho": 0.548,
                                "note": "must reproduce A1_CORRECTED_NULL_V2.json (same seeds, "
                                        "same chunking) — self-check of the generalization"},
    }
    out["arms"].append(row)
    print(f"CS breaker: corrected_p={res['corrected_p']:.6g} q={sub['q_value']:.4f} "
          f"argmax={res['argmax_variant']}", flush=True)

    # ---- 2. the sixteen AU arms (family 48) --------------------------------------
    au = json.loads(CAP_AU.read_text())
    assert au["reproduction_all_pass"], "AU capture failed receipt reproduction; refusing"
    for arm in au["arms"]:
        series = [float(v) for v in arm["null_call"]["series"]]
        seg_lens = arm["fold_segment_day_counts"]
        res = corrected_p_for_arm(series, seg_lens, 200_000)
        co = {nm: v["p_raw"] for nm, v in arm["co_judged_pvalues"].items()}
        sub = bh_substitute(co, arm["sleeve"], res["corrected_p"],
                            arm["published"]["declared_family_size"])
        # baseline check: substituting the PUBLISHED p must reproduce the published q
        base = bh_substitute(co, arm["sleeve"], arm["published"]["p_raw"],
                             arm["published"]["declared_family_size"])
        row = {
            "member": arm["sleeve"],
            "arm": arm["arm"], "band": arm["band"],
            "receipt": "phase12/receipts/AU_EXIT_WIRING_V1.json"
                       f" gate_rows[{arm['sleeve']}].arms[{arm['arm_index']}]",
            "publishing_session": "AU",
            "published": arm["published"],
            "baseline_bh_reproduces_published_q":
                abs(base["q_value"] - arm["published"]["q_value"]) < 1e-12,
            "corrected": {**{k: res[k] for k in ("corrected_p", "corrected_p_min_variant",
                                                  "argmax_variant", "t_obs", "n",
                                                  "rho_grid", "n_sims_total_per_variant")},
                          "diagnostics": res["diagnostics"], "bh": sub},
            "variants": res["variants"],
        }
        out["arms"].append(row)
        print(f"{arm['sleeve']:36s} {arm['arm']:10s} {arm['band']:20s} "
              f"pub_p={arm['published']['p_raw']:.6g} corr_p={res['corrected_p']:.6g} "
              f"q={sub['q_value']:.4f} baseline_ok={row['baseline_bh_reproduces_published_q']}",
              flush=True)

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

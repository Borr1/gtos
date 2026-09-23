#!/usr/bin/env python3
"""A1 clean-room, step 3: the corrected null, done honestly.

Step 2 (a1_null_analysis.py) established four facts that shape what "corrected"
must mean here:

  1. The implemented rule is not rotation-invariant and its exact p ranges
     1/2048..10/2048 across the 31 circular anchorings (verdict flips at 14/31).
  2. Its null variance is 64.8% signal (mu-contamination) -- conservative under H1.
  3. Its block length (3) was forced by the min_blocks=8 support cap; the spec's
     own AR decorrelation rule wanted L=7. At L=3 and lag1=0.49, EVERY resampling
     rule tested is anti-conservative under a matched AR(1) null at the decision
     alpha (original 3.8x; naively-centred variants far worse; CBB ~6x at 1%).
  4. The centred sign-flip support cannot reach the observed mean AT ANY block
     length or phase (max atom = 73% of observed at L=3), so its exact p is a
     hard 0 and only a resampling-with-replacement or model-based null can put a
     number on this tail.

Therefore the corrected null here is built by DIRECT FINITE-SAMPLE CALIBRATION:
fit the dependence structure the data actually show (three independent fold
segments of 11/11/9 days -- the concatenation seams are real; within-fold AR(1)
persistence; per-fold scale; innovation law either Gaussian or resampled AR
residuals so the skew is kept), impose H0 mean=0 exactly, and compute
P_H0(T >= T_obs) for the studentised weighted mean T = mean/ (sd/sqrt(n)) by
plain Monte Carlo. No block length, no phase, no support cap, no plug-in df
formula -- the calibration IS the fixed-b/finite-sample correction, computed
exactly under the declared model. Model risk is spanned by a rho grid covering
the measured within-fold lag-1 (0.412) +/- ~1 SE plus the full-series lag-1
(0.489) as a conservative upper member, and the primary corrected p is the MAX
across variants (the spec's own both_conservative philosophy applied to model
risk).

Also computed:
  * exact CBB tails at L=3 (FFT bracket) and L=7 (exact enumeration) on the
    real centred series -- the face-value corrected-resampling numbers, kept as
    diagnostics, NOT the primary (fact 3 above);
  * CBB L=7 MC at 1e6 x 3 seeds (the spec-shaped corrected resampler);
  * an independent re-verification of the step-2 size simulation at the
    decision alpha (fresh implementation);
  * the closed-form benchmarks (AR plug-in z, Kish-t at several rho,
    batch-means t, fold-mean t) for the fragility table.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CAP = HERE / "A1_CAPTURED_SERIES.json"
OUT = HERE / "A1_CORRECTED_NULL_V2.json"

FOLD_SLICES = [slice(0, 11), slice(11, 22), slice(22, 31)]
ADMIT_P = 0.10 / 59


# --------------------------------------------------------------- diagnostics --
def within_fold_stats(x: np.ndarray) -> dict:
    rho_num = rho_den = 0.0
    n_pairs = 0
    sds = []
    resid_pool = []
    for sl in FOLD_SLICES:
        seg = x[sl] - x[sl].mean()
        sds.append(float(x[sl].std(ddof=0)))
        rho_num += float((seg[:-1] * seg[1:]).sum())
        rho_den += float((seg * seg).sum())
        n_pairs += len(seg) - 1
    rho_w = rho_num / rho_den
    for sl in FOLD_SLICES:
        seg = x[sl] - x[sl].mean()
        r = seg[1:] - rho_w * seg[:-1]
        resid_pool.extend((r / (x[sl].std(ddof=0) * math.sqrt(1 - rho_w**2))).tolist())
    resid = np.asarray(resid_pool)
    resid = (resid - resid.mean()) / resid.std(ddof=0)
    se_rho = math.sqrt((1 - rho_w**2) / n_pairs)
    return {"rho_within": rho_w, "se_rho": se_rho, "fold_sds": sds,
            "resid_skew": float(((resid - resid.mean()) ** 3).mean() / resid.std() ** 3),
            "resid": resid}


# ------------------------------------------------- fitted-model calibration --
def calibrated_p(x: np.ndarray, rho: float, fold_sds: list[float],
                 resid: np.ndarray | None, n_sims: int, seed: int) -> dict:
    """P_H0(T >= T_obs) with T = mean / (sd_ddof1 / sqrt(n)), under mean-zero
    AR(1)-within-fold segments (independent across folds), per-fold scale,
    innovations Gaussian (resid=None) or resampled standardized AR residuals."""
    n = x.size
    t_obs = float(x.mean() / (x.std(ddof=1) / math.sqrt(n)))
    rng = np.random.default_rng(seed)
    lens = [sl.stop - sl.start for sl in FOLD_SLICES]
    burn = 30
    count = 0
    chunk = 100_000
    done = 0
    while done < n_sims:
        m = min(chunk, n_sims - done)
        cols = []
        for L, s_f in zip(lens, fold_sds):
            T = L + burn
            if resid is None:
                e = rng.standard_normal((m, T))
            else:
                e = resid[rng.integers(0, resid.size, size=(m, T))]
            z = np.empty((m, T))
            z[:, 0] = e[:, 0]
            for t in range(1, T):
                z[:, t] = rho * z[:, t - 1] + e[:, t]
            seg = z[:, burn:]
            # scale so the STATIONARY sd is s_f (innovations are unit-sd)
            seg = seg * (s_f * math.sqrt(1 - rho * rho))
            cols.append(seg)
        xs = np.concatenate(cols, axis=1)          # (m, 31), mean-zero process
        t_sim = xs.mean(axis=1) / (xs.std(axis=1, ddof=1) / math.sqrt(n))
        count += int(np.count_nonzero(t_sim >= t_obs))
        done += m
    return {"rho": rho, "seed": seed, "n_sims": int(n_sims), "t_obs": t_obs,
            "count_ge": int(count), "p_add_one": (1 + count) / (n_sims + 1)}


# ------------------------------------------------------- exact CBB tails ----
def cbb_windows(c: np.ndarray, L: int) -> tuple[np.ndarray, np.ndarray]:
    """Full-window sums (length L) and the truncated final-window sums, per the
    gate's construction: ceil(n/L) blocks, concatenated then truncated to n."""
    n = c.size
    wrapped = np.concatenate([c, c[: L - 1]]) if L > 1 else c
    W = np.array([wrapped[s:s + L].sum() for s in range(n)])
    n_blocks = math.ceil(n / L)
    tail_len = n - (n_blocks - 1) * L
    V = np.array([wrapped[s:s + tail_len].sum() for s in range(n)])
    return W, V


def cbb_exact_L7(x: np.ndarray) -> dict:
    """Exact tail at L=7: 4 full windows + 1 length-3 window, 31^5 combos."""
    c = x - x.mean()
    thr = float(x.sum()) - 1e-9
    W, V = cbb_windows(c, 7)
    s4 = W[:, None] + W[None, :]
    s4 = (s4[:, :, None] + W[None, None, :]).ravel()          # 31^3
    s4 = np.sort((s4[:, None] + W[None, :]).ravel())          # 31^4 sorted
    total = 0
    for v in V:
        total += s4.size - int(np.searchsorted(s4, thr - v, side="left"))
    N = 31 ** 5
    return {"L": 7, "n_combos": N, "count_ge": int(total),
            "p_exact": total / N, "p_add_one": (1 + total) / (N + 1)}


def cbb_fft_bracket(x: np.ndarray, L: int, bin_width: float = 5e-4) -> dict:
    """Rigorous upper/lower bracket on the exact CBB tail by binned convolution.

    Each window-sum atom is snapped down (upper bound on tail) or up (lower
    bound) by at most bin_width; k convolutions accumulate at most k*bin_width
    of threshold slack, which the bracket absorbs.
    """
    c = x - x.mean()
    thr = float(x.sum())
    W, V = cbb_windows(c, L)
    n_blocks = math.ceil(x.size / L)
    k_full = n_blocks - 1
    lo = min(W.min() * k_full + V.min(), 0) - 1.0
    hi = max(W.max() * k_full + V.max(), 0) + 1.0
    nbins = int(math.ceil((hi - lo) / bin_width)) + 2
    # the (k_full+1)-fold convolution needs room for the FULL summed support
    size = 1 << int(math.ceil(math.log2((k_full + 1) * nbins + 8)))

    def tail(round_up: bool) -> float:
        def pmf(vals):
            p = np.zeros(size)
            idx = np.ceil((vals - lo) / bin_width) if round_up else np.floor(
                (vals - lo) / bin_width)
            for i in idx.astype(int):
                p[i] += 1.0 / len(vals)
            return p
        pw = np.fft.rfft(pmf(W))
        acc = pw ** k_full * np.fft.rfft(pmf(V))
        dist = np.fft.irfft(acc, size)
        dist = np.clip(dist, 0.0, None)
        # value of bin i ~ lo + i*bin_width (+ per-conv rounding absorbed below)
        slack = (k_full + 1) * bin_width
        cut = thr + slack if round_up else thr - slack
        i0 = int(math.ceil((cut - (k_full + 1) * lo) / bin_width))
        return float(dist[max(i0, 0):].sum())

    return {"L": L, "bin_width": bin_width,
            "p_upper": tail(round_up=False), "p_lower": tail(round_up=True)}


def cbb_mc(x: np.ndarray, L: int, n_boot: int, seed: int) -> dict:
    a = np.asarray(x, float)
    n = a.size
    obs = float(a.mean())
    c = a - obs
    wrapped = np.concatenate([c, c[: L - 1]]) if L > 1 else c
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / L)
    offs = np.arange(L)
    count = 0
    done = 0
    while done < n_boot:
        m = min(200_000, n_boot - done)
        starts = rng.integers(0, n, size=(m, n_blocks))
        idx = (starts[:, :, None] + offs[None, None, :]).reshape(m, n_blocks * L)[:, :n]
        count += int(np.count_nonzero(wrapped[idx].mean(axis=1) >= obs))
        done += m
    return {"L": L, "n_boot": n_boot, "seed": seed, "count_ge": count,
            "p_add_one": (1 + count) / (n_boot + 1)}


# ------------------------------------------- independent size re-check ------
def size_recheck(rho: float, n: int, n_sims: int, seed: int, alpha: float) -> dict:
    """Fresh implementation: size of the original fixed-phase uncentred rule and
    the centred fixed-phase rule at `alpha`, exact per-sim p via doubling."""
    rng = np.random.default_rng(seed)
    L = 3
    n_blocks = math.ceil(n / L)
    pmap = np.empty(n, dtype=int)
    for b in range(n_blocks):
        pmap[b * L:(b + 1) * L] = b
    pmap = pmap[:n]
    rej_o = rej_c = 0
    chunk = 5000
    done = 0
    while done < n_sims:
        m = min(chunk, n_sims - done)
        e = rng.standard_normal((m, n + 20))
        xs = np.empty_like(e)
        xs[:, 0] = e[:, 0] / math.sqrt(1 - rho * rho)
        for t in range(1, n + 20):
            xs[:, t] = rho * xs[:, t - 1] + e[:, t]
        xs = xs[:, 20:]
        obs = xs.sum(axis=1)
        for centred in (False, True):
            base = xs - xs.mean(axis=1, keepdims=True) if centred else xs
            bs = np.zeros((m, n_blocks))
            for b in range(n_blocks):
                bs[:, b] = base[:, pmap == b].sum(axis=1)
            atoms = np.zeros((m, 1))
            for b in range(n_blocks):
                col = bs[:, b:b + 1]
                atoms = np.concatenate([atoms + col, atoms - col], axis=1)
            p = np.count_nonzero(atoms >= obs[:, None] - 1e-12, axis=1) / (1 << n_blocks)
            r = int(np.count_nonzero(p <= alpha))
            if centred:
                rej_c += r
            else:
                rej_o += r
        done += m
    return {"rho": rho, "alpha": alpha, "n_sims": n_sims,
            "size_original": rej_o / n_sims, "size_centred_fixed": rej_c / n_sims}


# ----------------------------------------------------------------------- run --
def main() -> int:
    cap = json.loads(CAP.read_text())
    x = np.array([float(v) for v in cap["captured"]["combined_null_calls"][0]["series"]])
    n = x.size

    diag = within_fold_stats(x)
    resid = diag.pop("resid")
    rho_w = diag["rho_within"]
    se = diag["se_rho"]

    out: dict = {
        "schema": "gtos-a1-cleanroom-corrected-null-v2",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "diagnostics": {**diag,
                        "lag1_full_series": float(np.dot(x[:-1] - x.mean(), x[1:] - x.mean())
                                                  / np.dot(x - x.mean(), x - x.mean())),
                        "t_obs_studentised": float(x.mean() / (x.std(ddof=1) / math.sqrt(n)))},
    }

    # --- primary: fitted-model calibration across the model-risk span --------
    rho_grid = sorted({round(max(rho_w - se, 0.0), 3), round(rho_w, 3),
                       round(min(rho_w + se, 0.95), 3), 0.489})
    variants = []
    for rho in rho_grid:
        for law, rz in (("gaussian", None), ("residual_bootstrap", resid)):
            runs = [calibrated_p(x, rho, diag["fold_sds"], rz, 700_000, seed)
                    for seed in (9101, 9102, 9103)]
            pooled_count = sum(r["count_ge"] for r in runs)
            pooled_n = sum(r["n_sims"] for r in runs)
            variants.append({
                "rho": rho, "innovations": law,
                "per_seed": [{k: r[k] for k in ("seed", "count_ge", "p_add_one")}
                             for r in runs],
                "pooled": {"n_sims": pooled_n, "count_ge": pooled_count,
                           "p_add_one": (1 + pooled_count) / (pooled_n + 1)},
            })
    out["calibrated_variants"] = variants
    pooled_ps = [v["pooled"]["p_add_one"] for v in variants]
    out["primary_corrected_p"] = {
        "definition": ("max over fitted-model variants (rho grid x innovation law) "
                       "of the calibrated studentised-mean tail, "
                       "both_conservative applied to model risk"),
        "p": max(pooled_ps),
        "p_min_variant": min(pooled_ps),
        "argmax": max(variants, key=lambda v: v["pooled"]["p_add_one"])["rho"],
    }

    # --- diagnostics: exact CBB tails + MC seeds ------------------------------
    out["cbb_exact_L7"] = cbb_exact_L7(x)
    out["cbb_bracket_L3"] = cbb_fft_bracket(x, 3)
    out["cbb_bracket_L7_check"] = cbb_fft_bracket(x, 7)
    out["cbb_mc_L7"] = [cbb_mc(x, 7, 1_000_000, seed) for seed in (20260729, 1, 2)]

    # --- independent size re-check at the decision alpha ----------------------
    out["size_recheck_L3"] = size_recheck(0.489, n, 50_000, 4242, ADMIT_P)

    # --- verdicts --------------------------------------------------------------
    def q(p):
        return min(1.0, 59 * p)
    rows = []
    rows.append(("original_gate_mc", 0.0025997400259974))
    rows.append(("original_exact_phase0", 4 / 2048))
    rows.append(("corrected_primary_calibrated_max", out["primary_corrected_p"]["p"]))
    rows.append(("corrected_calibrated_min_variant", out["primary_corrected_p"]["p_min_variant"]))
    rows.append(("cbb_face_value_exact_L7", out["cbb_exact_L7"]["p_exact"]))
    out["verdict_table"] = [
        {"rule": name, "p": p, "q_at_59": q(p),
         "verdict_at_alpha_0.10": "ADMIT" if q(p) <= 0.10 else "REJECT"}
        for name, p in rows
    ]

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("diagnostics", "primary_corrected_p",
                                          "cbb_exact_L7", "cbb_bracket_L3",
                                          "size_recheck_L3", "verdict_table")},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""A1 clean-room, step 2: the null itself.

Everything here operates on the 31-point weighted OOS day series captured at the
gate's own `combined_null_p` call site (a1_capture_series.py, byte-exact gate
reproduction). Sections:

  S1  Original implemented rule (fixed-phase block sign-flip, block=3):
      exact enumeration of its full 2^11-atom support, MC reproduction at the
      gate's seed plus 3 more seeds, support cap.
  S2  Rotation sweep: the same rule applied at every circular rotation of the
      series (31 anchor phases). If the rule were rotation-invariant these 31
      exact p-values would be one number. They are not.
  S3  Variance identity: sum(B_b^2) = sum(C_b^2) + 4*mu*(mu - x_last) + 91*mu^2
      -- the observed mean mu sits inside the null variance (signal
      contamination), and the phase enters through C_b(phi) and x_last(phi).
  S4  Corrected nulls for H0: mean <= 0 imposed by centring (the least
      favourable boundary), preserving short-horizon dependence:
        (a) centred circular block sign-flip, phase drawn uniformly per draw
            (rotation-invariant by construction) -- exact full-support
            enumeration (31 x 2048 atoms) + MC at 1e6 x 3 seeds;
        (b) centred circular block bootstrap (the gate's own bootstrap arm,
            identical construction to stats.day_block_bootstrap_p) at 1e6 x 3
            seeds;
        (c) studentised uncentred sign-flip (Chung-Romano style cross-check).
      Corrected gate p = max((a),(b)) under the spec's own both_conservative.
  S5  BH q at the declared family of 59 (58 padded at p=1.0), verdict at 0.10.
  S6  Sensitivity: block in {2,3,4,5,6,7} x 3 seeds for every rule.
  S7  Type-I validity simulation under two mean-zero AR(1) nulls (Gaussian and
      skew-matched) at the decision-relevant alphas, for the original rule, the
      centred fixed-phase rule, the centred phase-mixed rule, and the CBB.

No file outside this directory is touched.
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
OUT = HERE / "A1_NULL_ANALYSIS_RAW.json"

ALPHA = 0.10
FAMILY = 59
ADMIT_P = ALPHA / FAMILY  # BH rank-1 bar: p <= alpha/m  <=>  q = m*p <= alpha


# ------------------------------------------------------------------ helpers --
def circular_blocks(n: int, L: int, phase: int) -> list[np.ndarray]:
    """Circular partition of range(n) into ceil(n/L) blocks anchored at `phase`.

    Blocks are consecutive runs of length L on the circle starting at `phase`;
    the final block is short when L does not divide n. phase=0 with no wrap is
    exactly the implemented rule's partition.
    """
    order = [(phase + k) % n for k in range(n)]
    return [np.asarray(order[i:i + L]) for i in range(0, n, L)]


def block_sums(x: np.ndarray, L: int, phase: int) -> np.ndarray:
    return np.asarray([float(x[b].sum()) for b in circular_blocks(len(x), L, phase)])


def all_signed_sums(sums: np.ndarray) -> np.ndarray:
    """All 2^B values of sum_b s_b * sums[b], via doubling. B <= 20 expected."""
    atoms = np.zeros(1)
    for s in sums:
        atoms = np.concatenate([atoms + s, atoms - s])
    return atoms


def exact_signflip_p(x: np.ndarray, L: int, phase: int, *, centred: bool) -> dict:
    """Exact tail of the block sign-flip null at one phase.

    centred=False: group randomisation test; identity atom == observed, so the
    count is >= 1 and p_exact = count/2^B (the group convention).
    centred=True:  H0-imposed reference distribution (like the bootstrap);
    p_exact = mass >= observed and may be 0. Both also report the
    Phipson-Smyth style (1+count)/(N+1) bound.
    """
    n = len(x)
    obs_sum = float(x.sum())
    base = x - x.mean() if centred else x
    sums = block_sums(base, L, phase)
    atoms = all_signed_sums(sums)  # signed totals; statistic = atom / n
    count = int(np.count_nonzero(atoms >= obs_sum - 1e-12))
    N = atoms.size
    return {
        "n_atoms": int(N),
        "n_distinct_atoms": int(np.unique(np.round(atoms, 9)).size),
        "count_ge_obs": count,
        "p_exact": count / N,
        "p_add_one": (1 + count) / (N + 1),
        "null_sd_of_mean": float(np.sqrt((sums ** 2).sum()) / n),
        "max_atom_over_obs": float(np.abs(atoms).max() / abs(obs_sum)),
        "block_sums": [float(v) for v in sums],
    }


def exact_signflip_p_mixed(x: np.ndarray, L: int, *, centred: bool) -> dict:
    """Exact tail of the phase-mixed (rotation-averaged) sign-flip null."""
    n = len(x)
    obs_sum = float(x.sum())
    base = x - x.mean() if centred else x
    total = 0
    N = 0
    per_phase_p = []
    max_reach = 0.0
    sd_acc = 0.0
    for phase in range(n):
        sums = block_sums(base, L, phase)
        atoms = all_signed_sums(sums)
        c = int(np.count_nonzero(atoms >= obs_sum - 1e-12))
        total += c
        N += atoms.size
        per_phase_p.append(c / atoms.size)
        max_reach = max(max_reach, float(np.abs(atoms).max()))
        sd_acc += float((sums ** 2).sum())
    return {
        "n_atoms": int(N),
        "count_ge_obs": int(total),
        "p_exact": total / N,
        "p_add_one": (1 + total) / (N + 1),
        "per_phase_p_min": float(min(per_phase_p)),
        "per_phase_p_max": float(max(per_phase_p)),
        "max_atom_over_obs": max_reach / abs(obs_sum),
        "null_sd_of_mean_mixed": float(np.sqrt(sd_acc / n) / n),
    }


def mc_signflip_mixed_centred(x: np.ndarray, L: int, n_perm: int, seed: int) -> dict:
    """MC draw of the corrected rule: uniform phase + Rademacher block signs."""
    n = len(x)
    obs = float(x.mean())
    c = x - obs
    rng = np.random.default_rng(seed)
    phases = rng.integers(0, n, size=n_perm)
    # Pre-expand per phase: day -> block index map
    maps = []
    n_blocks = math.ceil(n / L)
    for phase in range(n):
        m = np.empty(n, dtype=np.int64)
        for b, idx in enumerate(circular_blocks(n, L, phase)):
            m[idx] = b
        maps.append(m)
    maps = np.stack(maps)  # (n, n) phase -> day -> block
    count = 0
    chunk = 200_000
    for lo in range(0, n_perm, chunk):
        hi = min(lo + chunk, n_perm)
        ph = phases[lo:hi]
        signs = rng.choice(np.array([-1.0, 1.0]), size=(hi - lo, n_blocks))
        day_signs = np.take_along_axis(
            signs, maps[ph], axis=1
        )  # (m, n): sign of each day's block
        stats = (day_signs * c[None, :]).mean(axis=1)
        count += int(np.count_nonzero(stats >= obs))
    return {
        "n_perm": int(n_perm),
        "seed": int(seed),
        "count_ge_obs": int(count),
        "p_add_one": (1 + count) / (n_perm + 1),
    }


def cbb_p(x: np.ndarray, L: int, n_boot: int, seed: int) -> dict:
    """Circular block bootstrap p for H0: mean <= 0, identical construction to
    stats.day_block_bootstrap_p (centre, wrap, uniform starts), vectorised in
    chunks so n_boot can be 1e6."""
    a = np.asarray(x, dtype=float)
    n = a.size
    observed = float(a.mean())
    Lc = max(1, min(int(L), n))
    centred = a - observed
    wrapped = np.concatenate([centred, centred[: Lc - 1]]) if Lc > 1 else centred
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / Lc)
    offs = np.arange(Lc)
    count = 0
    acc_mean = 0.0
    acc_m2 = 0.0
    done = 0
    chunk = 200_000
    while done < n_boot:
        m = min(chunk, n_boot - done)
        starts = rng.integers(0, n, size=(m, n_blocks))
        idx = (starts[:, :, None] + offs[None, None, :]).reshape(m, n_blocks * Lc)[:, :n]
        boot_means = wrapped[idx].mean(axis=1)
        count += int(np.count_nonzero(boot_means >= observed))
        acc_mean += float(boot_means.sum())
        acc_m2 += float((boot_means ** 2).sum())
        done += m
    mu = acc_mean / n_boot
    sd = math.sqrt(max(acc_m2 / n_boot - mu * mu, 0.0))
    return {
        "n_boot": int(n_boot),
        "seed": int(seed),
        "count_ge_obs": int(count),
        "p_add_one": (1 + count) / (n_boot + 1),
        "null_mean": mu,
        "null_sd": sd,
    }


def studentised_signflip(x: np.ndarray, L: int, *, mixed: bool) -> dict:
    """Uncentred block sign-flip with T = mean/sd (Chung-Romano studentisation).

    Group-exact under jointly block-sign-symmetric H0, and the studentisation
    removes most of the location contamination without centring. Exact
    enumeration (the support is small).
    """
    n = len(x)
    t_obs = float(x.mean() / x.std())
    phases = range(n) if mixed else [0]
    count = 0
    N = 0
    for phase in phases:
        blocks = circular_blocks(n, L, phase)
        n_blocks = len(blocks)
        # Enumerate all sign vectors; build day-level sign matrix per atom.
        m = np.empty(n, dtype=np.int64)
        for b, idx in enumerate(blocks):
            m[idx] = b
        svecs = np.array(
            [[1.0 if (k >> b) & 1 == 0 else -1.0 for b in range(n_blocks)]
             for k in range(1 << n_blocks)]
        )
        day_signs = svecs[:, m]                       # (2^B, n)
        flipped = day_signs * x[None, :]
        means = flipped.mean(axis=1)
        sds = flipped.std(axis=1)
        t = np.where(sds > 0, means / np.where(sds > 0, sds, 1.0), 0.0)
        count += int(np.count_nonzero(t >= t_obs - 1e-15))
        N += t.size
    return {"t_obs": t_obs, "n_atoms": int(N), "count_ge_obs": int(count),
            "p_exact": count / N, "p_add_one": (1 + count) / (N + 1)}


# ------------------------------------------------------- validity simulation --
def simulate_validity(rho: float, skew_target: float, n: int, n_sims: int,
                      L: int, alphas: list[float], seed: int) -> dict:
    """Type-I error of each rule under a mean-zero AR(1) null.

    Innovations: standard normal, or a centred/scaled gamma matched to the
    requested marginal skew (gamma skew = 2/sqrt(k); AR(1) damps the marginal
    skew, so the innovation skew is set to skew_target * (1-rho^3)^-1 ... in
    practice we set gamma skew so the simulated MARGINAL skew ~ skew_target,
    calibrated empirically below rather than by formula).
    Exact per-sim p for the sign-flip rules via subset-sum doubling; the CBB is
    handled by the caller (heavier).
    """
    rng = np.random.default_rng(seed)
    out = {"rho": rho, "skew_target": skew_target, "n_sims": n_sims, "L": L}
    n_blocks = math.ceil(n / L)

    # Build phase->day->block maps once.
    maps = np.stack([
        _phase_map(n, L, phase) for phase in range(n)
    ])

    # innovation generator
    if skew_target == 0.0:
        def innov(size):
            return rng.standard_normal(size)
    else:
        # gamma(k) has skew 2/sqrt(k); AR aggregation shrinks marginal skew by
        # roughly (1-rho)^1.5/(1-rho^3)^0.5 ... calibrate k empirically:
        k = _calibrate_gamma_k(rho, skew_target, n, rng)
        out["gamma_shape_k"] = k

        def innov(size):
            g = rng.gamma(k, 1.0, size)
            return (g - k) / math.sqrt(k)

    counts = {
        "orig_fixed_uncentred": np.zeros(len(alphas), dtype=np.int64),
        "centred_fixed": np.zeros(len(alphas), dtype=np.int64),
        "centred_mixed": np.zeros(len(alphas), dtype=np.int64),
    }
    marg_skew_acc, marg_lag1_acc = [], []

    chunk = 4000
    done = 0
    while done < n_sims:
        m = min(chunk, n_sims - done)
        eps = innov((m, n + 20))
        xs = np.empty((m, n + 20))
        xs[:, 0] = eps[:, 0] / math.sqrt(1 - rho * rho)
        for t in range(1, n + 20):
            xs[:, t] = rho * xs[:, t - 1] + eps[:, t]
        xs = xs[:, 20:]  # burn-in
        if done == 0:
            s = xs - xs.mean(axis=1, keepdims=True)
            m3 = (s ** 3).mean(axis=1)
            sd = xs.std(axis=1)
            marg_skew_acc.append(float(np.nanmean(m3 / np.where(sd > 0, sd ** 3, np.nan))))
            num = (s[:, :-1] * s[:, 1:]).sum(axis=1)
            den = (s ** 2).sum(axis=1)
            marg_lag1_acc.append(float(np.nanmean(num / np.where(den > 0, den, np.nan))))

        obs_sum = xs.sum(axis=1)                    # observed n*mean per sim

        # -- original rule: uncentred, phase 0 ------------------------------
        bs0 = _all_block_sums(xs, maps[0], n_blocks)          # (m, B)
        tail0 = _tail_count_doubling(bs0, obs_sum)            # count of 2^B atoms >= obs
        p0 = tail0 / (1 << n_blocks)
        # -- centred, phase 0 ------------------------------------------------
        cx = xs - xs.mean(axis=1, keepdims=True)
        bs0c = _all_block_sums(cx, maps[0], n_blocks)
        p1 = _tail_count_doubling(bs0c, obs_sum) / (1 << n_blocks)
        # -- centred, phase-mixed (exact mixture over all phases) -----------
        tot = np.zeros(m, dtype=np.int64)
        for phase in range(n):
            bsc = _all_block_sums(cx, maps[phase], n_blocks)
            tot += _tail_count_doubling(bsc, obs_sum)
        p2 = tot / float(n * (1 << n_blocks))

        for i, a in enumerate(alphas):
            counts["orig_fixed_uncentred"][i] += int(np.count_nonzero(p0 <= a))
            counts["centred_fixed"][i] += int(np.count_nonzero(p1 <= a))
            counts["centred_mixed"][i] += int(np.count_nonzero(p2 <= a))
        done += m

    out["marginal_skew_measured"] = marg_skew_acc[0] if marg_skew_acc else None
    out["marginal_lag1_measured"] = marg_lag1_acc[0] if marg_lag1_acc else None
    out["alphas"] = alphas
    out["rejection_rates"] = {
        k: [c / n_sims for c in v.tolist()] for k, v in counts.items()
    }
    return out


def _phase_map(n: int, L: int, phase: int) -> np.ndarray:
    m = np.empty(n, dtype=np.int64)
    for b, idx in enumerate(circular_blocks(n, L, phase)):
        m[idx] = b
    return m


def _all_block_sums(xs: np.ndarray, pmap: np.ndarray, n_blocks: int) -> np.ndarray:
    """(m, n) series + day->block map -> (m, B) block sums."""
    m = xs.shape[0]
    out = np.zeros((m, n_blocks))
    for b in range(n_blocks):
        cols = np.nonzero(pmap == b)[0]
        out[:, b] = xs[:, cols].sum(axis=1)
    return out


def _tail_count_doubling(bs: np.ndarray, obs: np.ndarray) -> np.ndarray:
    """Per-row count of signed subset sums >= obs, via vectorised doubling.

    bs: (m, B) block sums; obs: (m,). Returns (m,) int counts over 2^B atoms.
    """
    m, B = bs.shape
    atoms = np.zeros((m, 1))
    for b in range(B):
        col = bs[:, b:b + 1]
        atoms = np.concatenate([atoms + col, atoms - col], axis=1)
    return np.count_nonzero(atoms >= obs[:, None] - 1e-12, axis=1)


def _calibrate_gamma_k(rho: float, skew_target: float, n: int,
                       rng: np.random.Generator) -> float:
    """Pick gamma shape k so the AR(1) marginal skew ~ skew_target."""
    best_k, best_err = 1.0, math.inf
    for k in [0.15, 0.25, 0.4, 0.6, 0.9, 1.3, 2.0, 3.0, 5.0, 8.0]:
        g = rng.gamma(k, 1.0, (2000, n + 20))
        e = (g - k) / math.sqrt(k)
        x = np.empty_like(e)
        x[:, 0] = e[:, 0]
        for t in range(1, e.shape[1]):
            x[:, t] = rho * x[:, t - 1] + e[:, t]
        x = x[:, 20:]
        s = x - x.mean(axis=1, keepdims=True)
        sd = x.std(axis=1)
        sk = float(np.nanmean((s ** 3).mean(axis=1) / np.where(sd > 0, sd ** 3, np.nan)))
        err = abs(sk - skew_target)
        if err < best_err:
            best_k, best_err = k, err
    return best_k


def cbb_validity(rho: float, skew_target: float, n: int, n_sims: int, L: int,
                 n_boot: int, alphas: list[float], seed: int) -> dict:
    rng = np.random.default_rng(seed)
    if skew_target == 0.0:
        def innov(size):
            return rng.standard_normal(size)
        k = None
    else:
        k = _calibrate_gamma_k(rho, skew_target, n, rng)

        def innov(size):
            g = rng.gamma(k, 1.0, size)
            return (g - k) / math.sqrt(k)
    n_blocks = math.ceil(n / L)
    offs = np.arange(L)
    counts = np.zeros(len(alphas), dtype=np.int64)
    chunk = 200
    done = 0
    while done < n_sims:
        m = min(chunk, n_sims - done)
        eps = innov((m, n + 20))
        xs = np.empty((m, n + 20))
        xs[:, 0] = eps[:, 0] / math.sqrt(1 - rho * rho) if skew_target == 0.0 else eps[:, 0]
        for t in range(1, n + 20):
            xs[:, t] = rho * xs[:, t - 1] + eps[:, t]
        xs = xs[:, 20:]
        obs = xs.mean(axis=1)
        cx = xs - obs[:, None]
        wrapped = np.concatenate([cx, cx[:, : L - 1]], axis=1) if L > 1 else cx
        starts = rng.integers(0, n, size=(m, n_boot, n_blocks))
        idx = (starts[:, :, :, None] + offs[None, None, None, :]).reshape(
            m, n_boot, n_blocks * L)[:, :, :n]
        boot = np.take_along_axis(
            wrapped[:, None, :].repeat(1, axis=1), idx, axis=2
        ) if False else np.stack(
            [wrapped[i][idx[i]] for i in range(m)]
        )
        bm = boot.mean(axis=2)                       # (m, n_boot)
        ps = (1 + np.count_nonzero(bm >= obs[:, None], axis=1)) / (n_boot + 1)
        for i, a in enumerate(alphas):
            counts[i] += int(np.count_nonzero(ps <= a))
        done += m
    return {"rho": rho, "skew_target": skew_target, "gamma_shape_k": k,
            "n_sims": n_sims, "n_boot": n_boot, "L": L, "alphas": alphas,
            "rejection_rates": [c / n_sims for c in counts.tolist()]}


# ----------------------------------------------------------------------- run --
def main() -> int:
    cap = json.loads(CAP.read_text())
    call = cap["captured"]["combined_null_calls"][0]
    x = np.array([float(v) for v in call["series"]])
    n = x.size
    L_spec = int(call["block"])
    seed_spec = int(call["seed"])
    n_perm_spec = int(call["n_perm"])
    obs = float(x.mean())
    assert n == 31 and L_spec == 3 and seed_spec == 20260729

    results: dict = {
        "schema": "gtos-a1-cleanroom-null-analysis-raw-v1",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "series": {
            "n": n,
            "observed_mean": obs,
            "sd": float(x.std()),
            "skewness": float(((x - obs) ** 3).mean() / x.std() ** 3),
            "lag1_autocorr": float(
                np.dot(x[:-1] - obs, x[1:] - obs) / np.dot(x - obs, x - obs)
            ),
            "values": [repr(float(v)) for v in x],
        },
        "gate_params": {"block": L_spec, "n_perm": n_perm_spec, "seed": seed_spec,
                        "n_boot": int(call["n_boot"]), "mode": call["mode"]},
    }

    # ---- S1: original rule, exact + MC ------------------------------------
    s1 = exact_signflip_p(x, L_spec, 0, centred=False)
    results["S1_original_exact"] = s1
    sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801")
    from src.research_infra.validation_integrity.perm_null import (  # noqa: E402
        block_permutation_test,
    )
    mc = {}
    for seed in (20260729, 1, 2, 3):
        r = block_permutation_test(list(x), block=L_spec, n_perm=10_000,
                                   stat="mean", seed=seed)
        mc[str(seed)] = {"p_value": r["p_value"], "null_mean": r["null_mean"],
                         "null_std": r["null_std"]}
    big = block_permutation_test(list(x), block=L_spec, n_perm=1_000_000,
                                 stat="mean", seed=20260729)
    mc["1e6_at_gate_seed"] = {"p_value": big["p_value"]}
    results["S1_original_mc"] = mc

    # ---- S2: rotation sweep ------------------------------------------------
    rots = []
    for r in range(n):
        y = np.roll(x, -r)
        e = exact_signflip_p(y, L_spec, 0, centred=False)
        rots.append({"rotation": r, "p_exact": e["p_exact"],
                     "count": e["count_ge_obs"],
                     "null_sd": e["null_sd_of_mean"]})
    ps = [r_["p_exact"] for r_ in rots]
    results["S2_rotation_sweep"] = {
        "per_rotation": rots,
        "p_min": min(ps), "p_max": max(ps),
        "p_median": float(np.median(ps)),
        "p_phase0": ps[0],
        "distinct_p_values": sorted(set(ps)),
        "max_over_min": max(ps) / min(ps) if min(ps) > 0 else math.inf,
    }

    # ---- S3: variance identity --------------------------------------------
    B = np.asarray(s1["block_sums"])
    C = block_sums(x - obs, L_spec, 0)
    lens = np.array([len(b) for b in circular_blocks(n, L_spec, 0)], dtype=float)
    results["S3_variance_identity"] = {
        "sum_B_sq": float((B ** 2).sum()),
        "sum_C_sq": float((C ** 2).sum()),
        "mu": obs,
        "sum_len_sq": float((lens ** 2).sum()),
        "mu2_term": float(obs * obs * (lens ** 2).sum()),
        "cross_term": float(4 * obs * (obs - x[-1])),
        "identity_residual": float(
            (B ** 2).sum()
            - ((C ** 2).sum() + 4 * obs * (obs - x[-1]) + obs * obs * (lens ** 2).sum())
        ),
        "null_var_uncentred": float((B ** 2).sum() / n / n),
        "null_var_centred": float((C ** 2).sum() / n / n),
        "signal_share_of_null_variance": float(
            1.0 - (C ** 2).sum() / (B ** 2).sum()
        ),
    }

    # ---- S4: corrected nulls ----------------------------------------------
    s4 = {}
    s4["centred_fixed_phase_exact"] = exact_signflip_p(x, L_spec, 0, centred=True)
    s4["centred_mixed_exact"] = exact_signflip_p_mixed(x, L_spec, centred=True)
    s4["uncentred_mixed_exact"] = exact_signflip_p_mixed(x, L_spec, centred=False)
    s4["centred_mixed_mc"] = [
        mc_signflip_mixed_centred(x, L_spec, 1_000_000, seed)
        for seed in (20260729, 1, 2)
    ]
    s4["cbb"] = [cbb_p(x, L_spec, 1_000_000, seed) for seed in (20260729, 1, 2)]
    s4["cbb_gate_config_repro"] = cbb_p(x, L_spec, 10_000, 20260729)
    s4["studentised_fixed"] = studentised_signflip(x, L_spec, mixed=False)
    s4["studentised_mixed"] = studentised_signflip(x, L_spec, mixed=True)
    results["S4_corrected"] = s4

    # corrected gate p under both_conservative: max(perm arm, boot arm),
    # each arm at its own add-one bound, per seed
    per_seed = []
    for i, seed in enumerate((20260729, 1, 2)):
        pp = s4["centred_mixed_mc"][i]["p_add_one"]
        pb = s4["cbb"][i]["p_add_one"]
        per_seed.append({"seed": seed, "perm": pp, "boot": pb, "max": max(pp, pb)})
    results["S4_corrected_gate_p"] = per_seed

    # ---- S5: BH at the declared family -------------------------------------
    from src.research_infra.walkforward.stats import benjamini_hochberg  # noqa: E402
    def bh_at(p):
        ps = [p] + [1.0] * (FAMILY - 1)
        r = benjamini_hochberg(ps, ALPHA)
        return {"p": p, "q": r["qvalues"][0], "rejected": bool(r["rejected"][0])}
    s5 = {
        "original_mc_gate": bh_at(0.0025997400259974),
        "original_exact": bh_at(s1["p_exact"]),
        "corrected_each_seed": [bh_at(row["max"]) for row in per_seed],
        "admit_bar_p": ADMIT_P,
    }
    results["S5_bh"] = s5

    # ---- S6: sensitivity ----------------------------------------------------
    sens = []
    for Lb in (2, 3, 4, 5, 6, 7):
        row = {"block": Lb, "n_blocks": math.ceil(n / Lb),
               "orig_exact_phase0": exact_signflip_p(x, Lb, 0, centred=False)["p_exact"]}
        rot_ps = [exact_signflip_p(np.roll(x, -r), Lb, 0, centred=False)["p_exact"]
                  for r in range(n)]
        row["orig_exact_rot_min"] = min(rot_ps)
        row["orig_exact_rot_max"] = max(rot_ps)
        cm = exact_signflip_p_mixed(x, Lb, centred=True)
        row["centred_mixed_exact_p"] = cm["p_exact"]
        row["centred_mixed_max_atom_over_obs"] = cm["max_atom_over_obs"]
        row["centred_mixed_support"] = cm["n_atoms"]
        row["cbb"] = [cbb_p(x, Lb, 1_000_000, seed)["p_add_one"]
                      for seed in (20260729, 1, 2)]
        # corrected gate p (both_conservative analogue): max of the corrected
        # permutation arm (exact tail; 0 when the observed value is beyond the
        # whole support) and the CBB arm, at the worst of the three seeds.
        row["corrected_gate_p_worst_seed"] = max(max(row["cbb"]), cm["p_exact"])
        sens.append(row)
    results["S6_sensitivity"] = sens

    # ---- S7: validity simulation -------------------------------------------
    rho = results["series"]["lag1_autocorr"]
    skew = results["series"]["skewness"]
    alphas = [ADMIT_P, 0.01, 0.05, 0.10]
    results["S7_validity"] = {
        "gaussian": simulate_validity(rho, 0.0, n, 200_000, L_spec, alphas, 7001),
        "skewed": simulate_validity(rho, skew, n, 200_000, L_spec, alphas, 7002),
        "cbb_gaussian": cbb_validity(rho, 0.0, n, 20_000, L_spec, 4999,
                                     [0.01, 0.05, 0.10], 7003),
        "cbb_skewed": cbb_validity(rho, skew, n, 20_000, L_spec, 4999,
                                   [0.01, 0.05, 0.10], 7004),
    }

    OUT.write_text(json.dumps(results, indent=1, default=str))
    print(json.dumps({
        "S1_exact_p": s1["p_exact"],
        "S2_rot": {"min": results["S2_rotation_sweep"]["p_min"],
                   "max": results["S2_rotation_sweep"]["p_max"],
                   "phase0": ps[0]},
        "S3_signal_share": results["S3_variance_identity"]["signal_share_of_null_variance"],
        "S4_centred_mixed_exact": s4["centred_mixed_exact"]["p_exact"],
        "S4_max_atom_over_obs": s4["centred_mixed_exact"]["max_atom_over_obs"],
        "S4_cbb": [r["p_add_one"] for r in s4["cbb"]],
        "S4_gate_p": [r["max"] for r in per_seed],
        "S5": s5,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

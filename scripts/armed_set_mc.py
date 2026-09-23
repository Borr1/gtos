"""The Monte Carlo for the book that is actually going to be armed.

    python3 scripts/armed_set_mc.py                 # writes ARMED_SET_MC_V1.json
    python3 scripts/armed_set_mc.py --paths 20000   # cheap smoke run

WHAT THIS ANSWERS THAT `MC_FIRM_TRUE_V1.json` DOES NOT
------------------------------------------------------
Q's grid measures three *derived* books: all-11, each account's cost survivors, and the
two-account intersection. The book Borhen has approved is a **named** one -- four sleeves
selected by `run_book.py --tags` with `ultimate_book_include_clean3: true` -- and two
questions about it were never asked:

1. **At what sizing?** Every published `p_pass` is computed at
   `risk = dial x (sd_reference_book / sd_variant)` (`build_survivor_book.py:64`). For the
   four-sleeve book on FTMO's forward window that factor is **0.4234**, so the published
   0.99675 describes an account risking **0.847%** per correlated unit. **The CONFIGURED
   profile carries no such factor.** `admission.py:1470` reads
   `base_risk = prof.risk_per_unit_A`, and for `clean3_w7_ceiling_nom2p00` that is
   **0.020**, flat. (Stated that way deliberately: the module DOES have a vol term --
   `CLEAN3_VOL_SCALE = 0.9481` is pre-multiplied into every W5 `clean3_*`/`clean4_*`
   profile at `admission.py:686-731`. The W7 dials dropped it on purpose, `:752-760`.) The
   two conventions differ by 2.36x before the conviction bins and ~2.1x after (the sealed
   grid uses the full Kelly bins, the live book the half bins, because
   `ultimate_book_kelly_conservative: true`).

2. **Against which governor?** The live sizer is not `risk x R`. It is
   `base x conf x kelly_half x cap_mult`, first-fit-descending-capped at a 4% gross open
   risk ceiling (`admission.py:1334,1321`), blocked below a -9% static drawdown, and
   shrunk proportionally by `derisk_mode: smooth` -- which is **inert above the initial
   balance**, so it does nothing at all at FTMO's current equity. Two of those run against
   the book and one runs for it. `mc_governed` models all three.

Neither correction is a rule change, so neither is in Q's ladder. Both are sizing, and
sizing is what the owner actually chose.

CONTROLS
--------
`mc_governed` with the governor disabled is required to be **bit-identical** to
`mc_firm_rules.mc`, which is itself bit-identical to the sealed
`INTEG_portfolio_build_w2.mc_series`. So the chain from the sealed engine to every number
here is exact, and each difference is attributable to exactly one named change.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
# `scripts/research/` is a REGULAR package (it has an __init__.py) and a regular package
# beats a namespace portion at ANY sys.path position -- so the moment `scripts/` is
# searchable, `import research` resolves there and `research.operations.*` stops resolving
# for the whole process. Python puts the script's own directory on sys.path automatically,
# so appending is not enough either. Pin the repo-root package first, with sys.path
# temporarily restricted to the repo root, and everything after it is harmless.
# Session V's full-suite A/B measured the alternative as 6 unexplained regressions in
# tests/test_audit_b6_* and tests/test_b7_5_*.
_sys_path = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: E402,F401
finally:
    sys.path[:] = _sys_path
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402
import recost_w7_validation as M  # noqa: E402

OUT = REPO / "research/operations/w7_recost_2026_07_27/ARMED_SET_MC_V1.json"

# The armed book, and the two books it has to be compared against. NAMED, not derived --
# a confidence floor cannot produce ARMED_4 (`sub_xvol_pullback` sits at 0.45, below
# `metals_ob_micro` at 0.30's peers), so `--tags` is the only mechanism that selects it.
ARMED_4 = ["metals_core", "crypto", "energy_agri", "sub_xvol_pullback"]
CONF_FLOOR_3 = ["metals_core", "crypto", "energy_agri"]
BOTH_3 = ["crypto", "energy_agri", "sub_xvol_pullback"]

SETS = collections.OrderedDict([
    ("ARMED_4", ARMED_4),
    ("CONF_FLOOR_3", CONF_FLOOR_3),          # ARMED_4 minus sub_xvol_pullback
    ("BOTH_3", BOTH_3),                      # Q's SURVIVORS_BOTH_ACCOUNTS -- a DIFFERENT three
    ("ALL_11_BOOK_OF_RECORD", None),         # None -> the whole book of record
])

# FTMO, 2026-07-29. Balance = equity = 107,879.56 is the only figure this repo can witness
# (`VPS_EXPORT_FINDINGS.md:107`, the read-only VPS export, zero open positions). The Session
# V commission quotes 107,872.28; the two differ by $7.28 (0.007%) and nothing below turns
# on which is used. The repo-witnessed figure is the one modelled, and both are reported.
FTMO_EQUITY_WITNESSED = 107879.56
FTMO_EQUITY_COMMISSION = 107872.28
FTMO_INITIAL = 100000.0
# 269 deals over 2026-06-01..07-03 (same source), so FTMO's 4-day phase-1 minimum is served.
FTMO_PHASE1_DAYS_SERVED = 4

GROSS_OPEN_RISK_CAP = 0.04   # admission.py GovernorLimits.gross_open_risk_cap_pct
MAXDD_ENTRY_BLOCK = 0.09     # admission.py GovernorLimits.max_dd_entry_block_pct
MAXDD_LIMIT = 0.10


# ------------------------------------------------------------------------------------
# 1. Per-sleeve daily matrices -- the input the live sizer needs and `mc()` does not have
# ------------------------------------------------------------------------------------
def sleeve_day_matrix(rows, keep, acct, cm, nights, forward, ignore_intra=False):
    """(days, sleeves, raw_R) for one book/carry cell.

    `M.build_matrix_from` folds the confidence weight into its cells; the live sizer needs
    the RAW day-mean R because it applies confidence itself, as a property of the unit
    rather than of the return. Dividing back out is exact -- `conf` is a nonzero per-sleeve
    constant -- and `assert_matrix_reconstructs` checks the round trip on every cell.

    `ignore_intra=True` rebuilds the day-means WITHOUT the research `intra_size` ramp, which
    is what the live generators do for all four armed sleeves. Same day axis by
    construction (`intra_size` cannot make a firing day disappear), so only the values move.
    """
    sub = [r for r in rows if r["sleeve"] in keep]
    for r in sub:
        n = M.SLEEVE_MAX_NIGHTS[r["sleeve"]] if nights == "max" else nights
        c, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
        r["R_s"] = None if c is None else r["R_gross"] - c
    days, sleeves, Mx, _ = M.build_matrix_from(sub, "R_s")
    idx = [j for j, s in enumerate(sleeves) if s in keep]
    cols = [sleeves[j] for j in idx]
    if ignore_intra:
        per = {s: collections.defaultdict(list) for s in cols}
        for r in sub:
            if r.get("R_s") is not None:
                per[r["sleeve"]][r["date"]].append(r["R_s"])
        raw = [[statistics.fmean(per[s][d]) if per[s].get(d) else 0.0 for s in cols]
               for d in days]
    else:
        raw = [[Mx[i][j] / M.BOOK_CONF[sleeves[j]] for j in idx] for i in range(len(days))]
    if forward:
        sel = [i for i, d in enumerate(days) if d.year >= 2025]
        days = [days[i] for i in sel]
        raw = [raw[i] for i in sel]
    return days, cols, raw


def comb_from(raw, cols, kelly):
    """The scalar daily series `mc()` consumes, rebuilt from the raw matrix."""
    km = Q.kelly_fn(kelly)
    out = []
    for row in raw:
        vals = [row[j] * M.BOOK_CONF[cols[j]] for j in range(len(cols))]
        na = sum(1 for v in vals if abs(v) > 1e-9)
        out.append(sum(v * km(na) for v in vals))
    return out


# ------------------------------------------------------------------------------------
# 2. The governed MC -- the live sizing chain inside the bootstrap
# ------------------------------------------------------------------------------------
def mc_governed(raw, cols, base_risk, rules: Q.Rules, n_paths, seed_base=1,
                kelly=Q.KELLY_SEALED, gross_cap=None, derisk=False,
                start_equity=1.0, start_days_served=0, scale=1.0):
    """`mc_firm_rules.mc` with the day's P&L built from per-sleeve units, not a scalar.

    With `gross_cap=None` and `derisk=False` this is REQUIRED to be bit-identical to
    `mc_firm_rules.mc(comb_from(raw, cols, kelly), base_risk * scale, ...)`; the RNG is
    driven in exactly the same order and `sum_s conf_s * kelly * R_s * base = comb * base`
    exactly. `assert_governed_reduces` enforces it.

    `gross_cap` is the live 4% gross open-risk ceiling, applied first-fit-descending by
    unit confidence exactly as `admission._enforce_gross_open_risk_cap` does -- including
    its measured defect (it sheds by FIT, not by conviction, so at 4% headroom with four
    clusters firing it admits metals and the 0.45-confidence substrate sleeve and sheds
    crypto and energy). Modelled per book-day only: the live cap also counts risk still
    open from PRIOR days, and the survivor sleeves carry 320-hour horizons, so the live cap
    binds at least as often as this. The approximation therefore flatters the book.

    `derisk` is `derisk_mode: smooth` (`admission.py:1342`): `cap_mult = 1 - dd/0.10` where
    `dd` is measured from the STATIC initial balance, so it is exactly 1.0 whenever equity
    is at or above it. Plus the -9% entry block, which stops new units before the wall.
    """
    km = Q.kelly_fn(kelly)
    confs = [M.BOOK_CONF[c] for c in cols]
    order = sorted(range(len(cols)), key=lambda j: -confs[j])
    n = len(raw)
    block, pathcap = rules.block, rules.pathcap
    targets, nph = rules.targets, len(rules.targets)
    dlim, mlim = rules.daily_limit, rules.maxdd_limit
    daily_firm = rules.daily_basis == Q.DAILY_FIRM
    dd_firm = rules.maxdd_basis == Q.DD_FIRM
    floor = 1.0 - mlim
    mintd = rules.min_trading_days
    latch = rules.min_days_model == "latch"
    risk = base_risk * scale

    outs = collections.Counter()
    dlist = []
    shed_days = 0
    total_days = 0
    for s in range(n_paths):
        rng = random.Random(s * 131 + seed_base + int(risk * 1e6))
        eq = start_equity
        peak = max(1.0, start_equity)
        res = "timeout"
        dc = 0
        dcp = start_days_served
        ph = 0
        for _ in range(pathcap):
            start = rng.randrange(n)
            broke = False
            for k in range(block):
                row = raw[(start + k) % n]
                na = sum(1 for j in range(len(cols))
                         if abs(row[j] * confs[j]) > 1e-9)
                kl = km(na)
                mult = 1.0
                if derisk:
                    dd = 1.0 - eq                      # static reference == initial balance
                    if dd >= MAXDD_ENTRY_BLOCK:
                        # New entries blocked. In this model that is ABSORBING -- there are
                        # no open positions to recover on and no further entries, so equity
                        # can never move again. Recording it as `timeout` would hide a
                        # failure inside a PATHCAP artefact, so it gets its own outcome and
                        # is counted against the book.
                        dc += 1
                        dcp += 1
                        res = "fail_entry_block"
                        broke = True
                        break
                    if dd > 0:
                        mult = max(0.0, 1.0 - dd / MAXDD_LIMIT)
                dp = 0.0
                if gross_cap is None:
                    for j in range(len(cols)):
                        dp += risk * confs[j] * kl * mult * row[j]
                else:
                    avail = gross_cap
                    shed = False
                    for j in order:
                        if abs(row[j] * confs[j]) <= 1e-9:
                            continue
                        u = risk * confs[j] * kl * mult
                        if u <= avail + 1e-9:
                            avail -= u
                            dp += u * row[j]
                        else:
                            shed = True
                    total_days += 1
                    shed_days += 1 if shed else 0
                dc += 1
                dcp += 1
                if (eq * dp <= -dlim) if daily_firm else (dp <= -dlim):
                    res = "fail_daily"
                    broke = True
                    break
                eq *= (1 + dp)
                peak = max(peak, eq)
                if (eq <= floor) if dd_firm else ((peak - eq) / peak >= mlim):
                    res = "fail_maxdd"
                    broke = True
                    break
                if eq - 1.0 >= targets[ph]:
                    if mintd is not None and dcp < mintd:
                        if not latch:
                            continue
                        dc += mintd - dcp
                    ph += 1
                    if ph == nph:
                        res = "pass"
                        broke = True
                        break
                    eq = 1.0
                    peak = 1.0
                    dcp = 0
            if broke:
                break
        outs[res] += 1
        if res == "pass":
            dlist.append(dc)
    p = outs["pass"] / n_paths
    return dict(
        p_pass=p, p_fail_dd=outs["fail_maxdd"] / n_paths,
        p_fail_daily=outs["fail_daily"] / n_paths, p_timeout=outs["timeout"] / n_paths,
        p_fail_entry_block=outs["fail_entry_block"] / n_paths,
        med_days_pass=int(statistics.median(dlist)) if dlist else None,
        se_p_pass=math.sqrt(p * (1 - p) / n_paths),
        gross_cap_bound_day_share=(round(shed_days / total_days, 5) if total_days else None))


# ------------------------------------------------------------------------------------
# 3. Concentration -- the doubt the dossier ranks first
# ------------------------------------------------------------------------------------
def haircut(raw, cols, sleeve, lam):
    """Make one sleeve `lam` times as good as it looks, without making it quieter.

    An overfit sleeve has an inflated MEAN and an honest dispersion, so scaling all its
    R values by `lam` is the wrong model -- it shrinks the variance too, which flatters
    the book by cutting the very tail the drawdown rule tests. Instead subtract
    `(1-lam) * mu` from the sleeve on the days it FIRED, where `mu` is its own mean over
    those days. Its total contribution scales by `lam`; its per-firing-day dispersion is
    untouched; its zero days stay zero, so the day axis and `n_active` do not move.
    """
    if sleeve not in cols:
        return raw
    j = cols.index(sleeve)
    eps = 1e-9 / M.BOOK_CONF[sleeve]     # the SAME threshold comb_from counts n_active on
    fired = [i for i in range(len(raw)) if abs(raw[i][j]) > eps]
    if not fired:
        return raw
    mu = statistics.fmean(raw[i][j] for i in fired)
    out = [list(r) for r in raw]
    for i in fired:
        v = raw[i][j] - (1.0 - lam) * mu
        # A haircut that lands a firing day exactly on the n_active threshold would drop
        # that day out of the Kelly count and change the day axis -- the one thing this
        # function promises not to do. Nudge off the boundary rather than fail silently.
        if abs(v) <= eps:
            v = math.copysign(eps * 1.000001, v if v != 0.0 else raw[i][j])
        out[i][j] = v
    return out


def scale_haircut(raw, cols, sleeve, lam):
    """The naive alternative -- scale the sleeve's R outright. Reported as a sensitivity
    so the choice of haircut model is visible rather than assumed."""
    if sleeve not in cols:
        return raw
    j = cols.index(sleeve)
    out = [list(r) for r in raw]
    for i in range(len(raw)):
        out[i][j] = raw[i][j] * lam
    return out


def exact_sign_flip_p(diff_nonzero):
    """Exact one-sided p for `sum(diff) <= 0` by enumerating all 2^n sign patterns.

    The right instrument once you know the effective sample size. The ARMED-4 minus
    FLOOR-3 difference series is exactly 0.0 on every day `sub_xvol_pullback` did not fire
    -- both books have identical `n_active`, identical Kelly, and cancel term by term -- so
    a bootstrap advertising 128 days is resampling 13. With n that small the exact
    randomisation test is both cheaper and honest; the block bootstrap's own p is
    anti-conservative (a percentile of resamples around the OBSERVED value, never
    re-centred on the null).
    """
    n = len(diff_nonzero)
    if n == 0 or n > 22:
        return None
    obs = sum(diff_nonzero)
    hits = 0
    for mask in range(1 << n):
        s = 0.0
        for i, v in enumerate(diff_nonzero):
            s += v if (mask >> i) & 1 else -v
        if s >= obs:
            hits += 1
    return round(hits / (1 << n), 6)


def zero_edge_null(raw, cols, sleeve, comb3_total, n_draws=4000, seed=20260729,
                   variant="iid_boot"):
    """What a WORTHLESS fourth sleeve is worth, because it is not worth zero.

    Adding any sleeve raises `n_active` on the days it fires, which raises `kelly_mult` for
    the OTHER sleeves that day. So the four-sleeve book can beat the three-sleeve book with
    a fourth sleeve that has no edge at all, and the binary "beats FLOOR-3" flag carries
    almost no information until that baseline is measured.

    `perm` permutes the demeaned firing values (zero SAMPLE edge -- isolates the pure
    Kelly/day-axis artifact). `iid_boot` resamples them with replacement (zero POPULATION
    edge, with realistic 13-day sample-mean noise) and is the right null for "would a
    worthless sleeve have looked like this".
    """
    j = cols.index(sleeve)
    fired = [i for i in range(len(raw)) if abs(raw[i][j]) > 1e-12]
    if not fired:
        return None
    mu = statistics.fmean(raw[i][j] for i in fired)
    dev = [raw[i][j] - mu for i in fired]
    rng = random.Random(seed)
    obs_total = sum(comb_from(raw, cols, Q.KELLY_HALF))
    wins = 0
    ge_obs = 0
    advs = []
    for _ in range(n_draws):
        if variant == "perm":
            vals = dev[:]
            rng.shuffle(vals)
        else:
            vals = [dev[rng.randrange(len(dev))] for _ in dev]
        r2 = [list(r) for r in raw]
        for k, i in enumerate(fired):
            r2[i][j] = vals[k]
        t = sum(comb_from(r2, cols, Q.KELLY_HALF))
        advs.append(t - comb3_total)
        wins += 1 if t > comb3_total else 0
        ge_obs += 1 if (t - comb3_total) >= (obs_total - comb3_total) else 0
    advs.sort()
    return dict(
        variant=variant, n_draws=n_draws,
        p_zero_edge_sleeve_beats_floor3=round(wins / n_draws, 5),
        null_advantage_median=round(advs[n_draws // 2], 4),
        null_advantage_p95=round(advs[int(0.95 * n_draws)], 4),
        null_advantage_mean=round(statistics.fmean(advs), 4),
        p_null_advantage_ge_observed=round(ge_obs / n_draws, 5),
        observed_advantage=round(obs_total - comb3_total, 4))


def block_bootstrap_ci(series, n_boot=20000, block=5, seed=20260729, qs=(2.5, 50.0, 97.5)):
    """Circular block bootstrap of the SUM of a book-day series.

    The sum, not the mean: monthly return is `sum(comb) / months * risk`, so the sum is the
    quantity the headline is built from and it is invariant to which day axis a book has.
    Block 5 is the sealed bootstrap's own block length, which is what carries the
    day-clustering R measured (`crypto` 104 fires on 67 dates, lag-1 rho 0.441).
    """
    n = len(series)
    if n == 0:
        return None
    nb = max(1, round(n / block))
    rng = random.Random(seed)
    tot = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(nb):
            st = rng.randrange(n)
            for k in range(block):
                s += series[(st + k) % n]
        tot.append(s * n / (nb * block))
    tot.sort()
    return {f"p{q}": round(tot[min(len(tot) - 1, int(q / 100.0 * len(tot)))], 4) for q in qs}


def paired_block_bootstrap(a_days, a_comb, b_days, b_comb, n_boot=20000, block=5,
                           seed=20260729):
    """P(book A's window total <= book B's) under a paired circular block bootstrap.

    The two books have DIFFERENT day axes -- dropping a sleeve removes the days only it
    fired on -- so the difference is taken on the UNION axis with zero fill, which is what
    the calendar sees. Resampling the difference series (not the two totals separately)
    keeps the two books on the same drawn days, which is the whole point: they share most
    of their trades and an unpaired comparison would drown the difference in common noise.
    """
    idx = {d: i for i, d in enumerate(sorted(set(a_days) | set(b_days)))}
    diff = [0.0] * len(idx)
    for d, v in zip(a_days, a_comb):
        diff[idx[d]] += v
    for d, v in zip(b_days, b_comb):
        diff[idx[d]] -= v
    n = len(diff)
    nb = max(1, round(n / block))
    rng = random.Random(seed)
    tot = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(nb):
            st = rng.randrange(n)
            for k in range(block):
                s += diff[(st + k) % n]
        tot.append(s * n / (nb * block))
    tot.sort()
    lo = tot[int(0.025 * len(tot))]
    hi = tot[int(0.975 * len(tot))]
    nz = [v for v in diff if abs(v) > 1e-12]
    return dict(observed_diff_total_r=round(sum(diff), 4),
                boot_median=round(tot[len(tot) // 2], 4),
                ci95=[round(lo, 4), round(hi, 4)],
                p_advantage_le_zero_block_bootstrap=round(
                    sum(1 for t in tot if t <= 0) / len(tot), 5),
                block=block,
                union_days=n,
                # The number that decides how much any of this is worth. The two books
                # differ only by one sleeve, so the difference is exactly 0.0 on every day
                # that sleeve did not fire and the effective sample is tiny.
                effective_nonzero_days=len(nz),
                p_advantage_le_zero_exact_sign_flip=exact_sign_flip_p(nz),
                note=("Use the exact sign-flip p. The block-bootstrap p is a percentile "
                      "around the observed value rather than a re-centred null, so it is "
                      "anti-conservative, and it advertises union_days when the effective "
                      "sample is effective_nonzero_days."))


# ------------------------------------------------------------------------------------
# 4. Frequency -- `book_days_per_calendar_month` is a modelled quantity
# ------------------------------------------------------------------------------------
def from_here_governed(rows, acct, cm, paths, rules_by_label):
    """The from-here start AND the live governor together -- the closest single model to
    what would actually happen if the book were armed on FTMO tomorrow.

    Worth running separately because the two corrections interact in opposite directions.
    `derisk_mode: smooth` measures drawdown from the STATIC initial balance, so from
    $107,880 it is switched off until the account has given back all $7,880; from a fresh
    $100,000 it engages on the first losing day. So the governor is worth LESS from here
    than the fresh-challenge grid in `live_governor` suggests.
    """
    e0 = FTMO_EQUITY_WITNESSED / FTMO_INITIAL
    out = {}
    for name, keep in (("ARMED_4", ARMED_4), ("CONF_FLOOR_3", CONF_FLOOR_3),
                       ("BOTH_3", BOTH_3)):
        for nights in (0.0, 1.0, "max"):
            days, cols, raw = sleeve_day_matrix(rows, keep, acct, cm, nights, True)
            comb = comb_from(raw, cols, Q.KELLY_HALF)
            months = ((max(days).year - min(days).year) * 12
                      + (max(days).month - min(days).month) + 1)
            sess = Q.weekday_sessions(min(days), max(days))
            node = {}
            for lab, e, served in (("from_100k", 1.0, 0),
                                   ("from_here", e0, FTMO_PHASE1_DAYS_SERVED)):
                for rlab in ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES"):
                    r = mc_governed(raw, cols, Q.DIAL, rules_by_label[rlab], paths,
                                    seed_base=1, kelly=Q.KELLY_HALF,
                                    gross_cap=GROSS_OPEN_RISK_CAP, derisk=True,
                                    start_equity=e, start_days_served=served)
                    node[f"{lab}|{rlab}"] = dict(
                        **derived(r, sess, len(days), statistics.fmean(comb),
                                  len(days) / months, Q.DIAL),
                        p_fail_entry_block=round(r["p_fail_entry_block"], 6))
                    print(f"   FHGOV {name:14s} n{nights!s:5s} {lab:10s} {rlab:18s} "
                          f"p={r['p_pass']:.5f}", flush=True)
            out[f"{name}|fwd_nights_{nights if nights != 'max' else 'max'}"] = node
    out["_note"] = ("Full live sizing + 4% gross cap + smooth de-risk + the -9% entry block, "
                    "from a fresh $100,000 and from FTMO's actual $107,879.56. Smooth is "
                    "measured from the STATIC initial balance, so from here it does nothing "
                    "until the account is back under $100,000.")
    return out


SELECTION_WINDOWS = (("2015_2019", 2015, 2019), ("pre_2025", 2000, 2024),
                     ("selection_window_2025plus", 2025, 2100), ("all_2015_2026", 2000, 2100))


def outside_the_selection_window(rows, acct, cm, sd_book, paths, rules_by_label):
    """The forward window IS the selection window, so evaluate the book outside it.

    `build_survivor_book.py:60` filters the "forward" window with `d.year >= 2025`. That
    predicate is character-for-character the one the ORIGINAL sleeve selection used as its
    verdict gate -- `KB7_growth_kelly_sizing.py:130` and `INTEG_portfolio_build_w2.py:331`,
    both `d.year >= 2025`. The route's own adversarial audit says so in as many words
    (`AUDIT_exec_and_untouched.md` section (b)): *"NO clean out-of-sample slice exists ...
    the sleeves and dial were chosen to look good on exactly this window."* That file is
    committed, and `git grep -l AUDIT_exec_and_untouched` returns **nothing** -- no
    downstream document cites it.

    So the headline `2.617 %/month` is an in-sample-to-selection number. This function
    prices the same book on the slices that are not.
    """
    out = {}
    for name, keep in (("ARMED_4", ARMED_4), ("CONF_FLOOR_3", CONF_FLOOR_3),
                       ("BOTH_3", BOTH_3)):
        days, cols, raw = sleeve_day_matrix(rows, keep, acct, cm, "max", False)
        for lab, lo, hi in SELECTION_WINDOWS:
            sel = [i for i, d in enumerate(days) if lo <= d.year <= hi]
            if not sel:
                continue
            dd = [days[i] for i in sel]
            rr = [raw[i] for i in sel]
            cf = comb_from(rr, cols, Q.KELLY_SEALED)
            ch = comb_from(rr, cols, Q.KELLY_HALF)
            sd = statistics.pstdev(cf)
            vs = sd_book / sd if sd else 0.0
            months = ((max(dd).year - min(dd).year) * 12
                      + (max(dd).month - min(dd).month) + 1)
            bdpm = len(dd) / months
            sess = Q.weekday_sessions(min(dd), max(dd))
            node = dict(book_days=len(dd), calendar_months=months,
                        book_days_per_calendar_month=round(bdpm, 3),
                        density_pct=round(100 * len(dd) / sess, 2),
                        vol_scale=round(vs, 4), total_r=round(sum(cf), 3))
            for conv, comb, risk in (("published", cf, Q.DIAL * vs),
                                     ("live", ch, Q.DIAL)):
                mean_r = statistics.fmean(comb)
                node[conv] = dict(
                    eff_risk_pct=round(100 * risk, 4),
                    mean_r_per_book_day=round(mean_r, 5),
                    worst_day_pct_of_equity=round(100 * min(comb) * risk, 4),
                    monthly_pct_calendar=round(mean_r * risk * bdpm * 100, 3),
                    rules={k: derived(Q.mc(comb, risk, r, paths, seed_base=1),
                                      sess, len(dd), mean_r, bdpm, risk)
                           for k, r in (("L4_FIRM_TRUE_PH1",
                                         rules_by_label["L4_FIRM_TRUE_PH1"]),
                                        ("P2_BOTH_PHASES",
                                         rules_by_label["P2_BOTH_PHASES"]))})
            out[f"{name}|{lab}"] = node
            print(f"   OOS {name:14s} {lab:26s} bd/mo={bdpm:5.2f} "
                  f"mo%pub={node['published']['monthly_pct_calendar']:7.3f} "
                  f"p_pub={node['published']['rules']['L4_FIRM_TRUE_PH1']['p_pass']:.5f}",
                  flush=True)
    out["_note"] = (
        "`build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130` use the SAME "
        "d.year >= 2025 predicate -- the evaluation window is the selection window. "
        "AUDIT_exec_and_untouched.md section (b) says so and is cited by nothing.")
    return out


def intra_size_convention(rows, acct, cm, paths, rules_by_label=None):
    """A fourth sizing divergence, and it is not the same kind as the other three.

    `intra_size` is a research-side intra-sleeve confidence ramp: the generator sized a
    marginal setup down. `recost_w7_validation.build_matrix_from:897` folds it into the
    RETURN (`v * intra_size` inside the day-mean), so every published figure for these
    sleeves is conditioned on down-sizing weak setups.

    **The live generators for the four armed sleeves never set it.** `TradeIntent.intra_size`
    defaults to 1.0 (`admission.py:849`) and the only generator in the tree that passes a
    value is `generate_metals_softband` (`sleeves/metals.py:218`) -- not `generate_metals`
    (`:203`), not `crypto.py:65`, not `energy_agri.py:62`, not `substrate.py:113`. So live
    takes FULL size on the setups the research took at a fraction.

    Measured both ways here. Whether it helps or hurts the edge depends on whether the ramp
    was informative; that it raises the risk is not in question.
    """
    out = {}
    for name, keep in (("ARMED_4", ARMED_4), ("CONF_FLOOR_3", CONF_FLOOR_3),
                       ("BOTH_3", BOTH_3)):
        for nights in (0.0, 1.0, "max"):
            days, cols, raw = sleeve_day_matrix(rows, keep, acct, cm, nights, True)
            _, cols_ni, raw_ni = sleeve_day_matrix(rows, keep, acct, cm, nights, True,
                                                   ignore_intra=True)
            assert cols == cols_ni
            a = comb_from(raw, cols, Q.KELLY_HALF)
            b = comb_from(raw_ni, cols, Q.KELLY_HALF)
            rl = rules_by_label or {}
            labs = [("L0_LEGACY_SEALED", Q.Rules.LEGACY)]
            labs += [(k, rl[k]) for k in ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES") if k in rl]
            pa = {k: round(Q.mc(a, Q.DIAL, r, paths, seed_base=1)["p_pass"], 6)
                  for k, r in labs}
            pb = {k: round(Q.mc(b, Q.DIAL, r, paths, seed_base=1)["p_pass"], 6)
                  for k, r in labs}
            ra, rb = dict(p_pass=pa["L0_LEGACY_SEALED"]), dict(p_pass=pb["L0_LEGACY_SEALED"])
            mean_intra = {}
            for sl in keep:
                v = [r["intra_size"] for r in rows
                     if r["sleeve"] == sl and r["source"] == "W3"]
                mean_intra[sl] = round(statistics.fmean(v), 4) if v else 1.0
            out[f"{name}|fwd_nights_{nights if nights != 'max' else 'max'}"] = dict(
                mean_research_intra_size=mean_intra,
                research_convention=dict(
                    total_r=round(sum(a), 4), mean_r=round(statistics.fmean(a), 5),
                    sd_r=round(statistics.pstdev(a), 5),
                    worst_day_pct=round(100 * min(a) * Q.DIAL, 4),
                    p_pass=pa),
                live_convention_intra_1=dict(
                    total_r=round(sum(b), 4), mean_r=round(statistics.fmean(b), 5),
                    sd_r=round(statistics.pstdev(b), 5),
                    worst_day_pct=round(100 * min(b) * Q.DIAL, 4),
                    p_pass=pb),
                total_r_ratio_live_over_research=round(sum(b) / sum(a), 4) if sum(a) else None,
                sd_ratio_live_over_research=(round(statistics.pstdev(b)
                                                   / statistics.pstdev(a), 4)
                                             if statistics.pstdev(a) else None))
    out["_note"] = ("Only generate_metals_softband sets intra_size live (sleeves/metals.py:218). "
                    "None of the four armed sleeves does, so the live unit confidence is "
                    "conf * 1.0 while the published series is conf * mean(R * intra_size).")
    return out


def sizing_provenance(cells, sd_book):
    """How far apart the two sizing conventions actually are -- measured, per book.

    The naive arithmetic says 1/vol_scale, i.e. 2.36x for the armed book. That is WRONG,
    and the reason it is wrong is the thing the live package's own comment claims:

      "In the W7 final book the volatility reshape is the KELLY-LITE conviction
       multiplier, which the deployable path applies as a RUNTIME multiplier in
       size_correlated_units (kelly_lite=True) ... matching the locked W7 MC where the
       Kelly-folded series was vol-matched at VS_final=0.7504."
      `src/components/ultimate_book/admission.py:752-760` -- the LIVE authority, which is
      what `bridge.py` imports. The identical text also sits in the route copy
      `ultimate_book_live_package.py:562-569`, which does not run.

    Half-Kelly IS a volatility reshape and it does absorb part of the gap. So the honest
    multiple is `(sd_half/sd_full) / vol_scale`, not `1/vol_scale`, and it is measured
    here rather than argued. The claim quoted above is separately checkable and is checked
    in `w7_certification_check`: the reshape half-Kelly delivers is NOT 0.7504, and
    `INTEG_W7_final_book.py:171` shows why the substitution cannot work in principle --
    `VS_final = round(sd_book / sd_final, 4)  # Kelly runs hotter -> smaller vol_scale`.
    The vol match EXISTS to undo Kelly's inflation, so a milder Kelly can only stand in
    for part of it.
    """
    out = {}
    for (name, nights, fwd), c in cells.items():
        if not fwd:
            continue
        cf = comb_from(c["raw"], c["cols"], Q.KELLY_SEALED)
        ch = comb_from(c["raw"], c["cols"], Q.KELLY_HALF)
        sf, sh = statistics.pstdev(cf), statistics.pstdev(ch)
        reshape = sh / sf if sf else 0.0
        pub = Q.DIAL * c["vol_scale"]
        live_in_full_units = Q.DIAL * reshape
        out[f"{name}|fwd_nights_{nights if nights != 'max' else 'max'}"] = dict(
            vol_scale_published=round(c["vol_scale"], 4),
            published_eff_risk_pct=round(100 * pub, 4),
            half_kelly_reshape=round(reshape, 4),
            live_risk_in_full_kelly_units_pct=round(100 * live_in_full_units, 4),
            live_multiple_over_published=round(live_in_full_units / pub, 3) if pub else None,
            naive_multiple_ignoring_kelly=round(1.0 / c["vol_scale"], 3))
    return out


def w7_certification_check(rows, sd_book):
    """Does the live 2.0% dial's own certification describe the live 2.0% dial?

    `ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"]` carries base/fwd/stress statistics
    0.9553 / 0.9562 / 0.5021. Those three numbers are read here from
    `INTEG_W7_FINAL_RESULT.json` to find which row produced them, and the row's own
    `sizeA_eff` says at what risk. Everything below is read from the artifact, not
    transcribed.
    """
    p = (REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
         / "INTEG_W7_FINAL_RESULT.json")
    if not p.is_file():
        return dict(status="artifact_absent", path=str(p))
    art = json.loads(p.read_text())
    from src.components.ultimate_book.admission import ALLOCATION_PROFILES
    prof = ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"]
    want = (prof.base_p_both, prof.fwd_p_both, prof.stress15_p_both)
    match = [k for k, v in art.get("two_account_final", {}).items()
             if (v.get("base_p_both"), v.get("fwd_p_both"),
                 v.get("stress15_p_both")) == want]
    row = art["two_account_final"][match[0]] if match else None

    # the reshape half-Kelly delivers on the SAME basis the vol match was computed on:
    # the 11-sleeve legacy-R series over the full window.
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, Mx, _ = M.build_matrix_from(rows, "R_legacy")
    nact = [sum(1 for v in row_ if abs(v) > 1e-9) for row_ in Mx]
    kf, kh = Q.kelly_fn(Q.KELLY_SEALED), Q.kelly_fn(Q.KELLY_HALF)
    cf = [sum(v * kf(nact[i]) for v in Mx[i]) for i in range(len(Mx))]
    ch = [sum(v * kh(nact[i]) for v in Mx[i]) for i in range(len(Mx))]
    reshape = statistics.pstdev(ch) / statistics.pstdev(cf)
    vs_locked = art["variant_daily"]["final"]["vs"]
    return dict(
        profile_stats=dict(base_p_both=prof.base_p_both, fwd_p_both=prof.fwd_p_both,
                           stress15_p_both=prof.stress15_p_both),
        matching_artifact_rows=match,
        matched_row=row,
        profile_risk_per_unit_A=prof.risk_per_unit_A,
        profile_risk_per_unit_B=prof.risk_per_unit_B,
        locked_vs_final=vs_locked,
        locked_eff_risk_A_pct=round(100 * row["sizeA_eff"], 4) if row else None,
        half_kelly_reshape_on_locked_basis=round(reshape, 4),
        live_eff_in_full_kelly_units_pct=round(100 * prof.risk_per_unit_A * reshape, 4),
        live_over_certified=(round(prof.risk_per_unit_A * reshape / row["sizeA_eff"], 4)
                             if row else None),
        reshape_claim_holds=bool(abs(reshape - vs_locked) <= 0.02),
        note=("admission.py:752-760 justifies dropping the vol match by asserting the "
              "Kelly-lite multiplier IS the reshape. Measured, not assumed. "
              "INTEG_W7_final_book.py:171 -- 'Kelly runs hotter -> smaller vol_scale' "
              "-- shows VS_final exists to UNDO Kelly inflation, so a milder Kelly "
              "can only stand in for part of it."))


def concentration(cells, rows, acct, cm, paths, boot, L4):
    """The commission's question 3, with four corrections its first version needed.

    1. **A shared sleeve must be haircut in BOTH books.** `crypto` is in ARMED-4 and in
       FLOOR-3, so cutting it only in ARMED-4 and differencing against an uncut FLOOR-3
       measures the haircut, not the composition choice. The first version did that and
       published `beats_conf_floor3: false` for crypto at lambda <= 0.5, which is a
       category error: haircut both and the ARMED-4-vs-FLOOR-3 gap is nearly invariant to
       crypto, because crypto cancels.
    2. **The break-even bisection must bracket a root.** `lo, hi = 0.0, 1.0` with
       `adv(lam) > 0` everywhere halves `hi` to 2^-30 and reports 0.0 with no failure
       signal -- indistinguishable from a true break-even at 0. The advantage is exactly
       linear in lambda, so it is solved rather than searched.
    3. **A zero-edge fourth sleeve is not neutral**, because it raises `n_active` and
       therefore the Kelly multiplier on the other three. `zero_edge_null` prices that.
    4. **Leave-one-out on `p_pass` inverts the ranking.** Dropping `crypto` cuts the book's
       daily sd far more than its mean, so `p_pass` rises to ~1.0 while book-days fall 35 %
       -- the book gets safer and much slower. `expected_passes_per_year` is reported
       beside it as the statistic that does not invert.
    """
    conc = dict(
        question=("How much of the four-sleeve advantage survives if sub_xvol_pullback is "
                  "half as good as it looks?"),
        haircut_model=(
            "demean-preserving: subtract (1-lam)*mu from the sleeve on the days it fired, "
            "so its edge scales by lam and its dispersion does not. `scale` is a SIZE "
            "sensitivity, not a competing haircut model -- it scales mean and sd together "
            "so the sleeve's Sharpe is invariant by construction, which is why it can raise "
            "p_pass while cutting total R. Do not read the two as disagreeing about "
            "overfitting."),
        shared_sleeve_rule=("A sleeve present in BOTH books is haircut in both. Only "
                            "sub_xvol_pullback is exclusive to ARMED-4."))
    for nights in (0.0, 1.0, "max"):
        c4 = cells[("ARMED_4", nights, True)]
        c3 = cells[("CONF_FLOOR_3", nights, True)]
        key = f"fwd_nights_{nights if nights != 'max' else 'max'}"
        node = dict(paired_bootstrap={}, haircut={}, leave_one_out={}, window_totals={})
        comb4 = comb_from(c4["raw"], c4["cols"], Q.KELLY_HALF)
        comb3 = comb_from(c3["raw"], c3["cols"], Q.KELLY_HALF)
        node["window_totals"] = dict(
            armed4_total_r=round(sum(comb4), 4), conf_floor3_total_r=round(sum(comb3), 4),
            armed4_book_days=len(comb4), conf_floor3_book_days=len(comb3),
            armed4_ci95_total_r=block_bootstrap_ci(comb4, n_boot=boot),
            conf_floor3_ci95_total_r=block_bootstrap_ci(comb3, n_boot=boot))
        node["paired_bootstrap"] = paired_block_bootstrap(
            c4["days"], comb4, c3["days"], comb3, n_boot=boot)
        node["paired_bootstrap_block_sensitivity"] = {
            f"block_{b}": paired_block_bootstrap(
                c4["days"], comb4, c3["days"], comb3, n_boot=boot,
                block=b)["p_advantage_le_zero_block_bootstrap"]
            for b in (1, 2, 3, 5, 10, 20)}
        node["daily_autocorrelation"] = daily_autocorr(comb4, c4["days"], c4["cols"],
                                                       c4["raw"])
        for lab, var in (("permutation_zero_sample_edge", "perm"),
                         ("iid_bootstrap_zero_population_edge", "iid_boot")):
            node.setdefault("zero_edge_null", {})[lab] = zero_edge_null(
                c4["raw"], c4["cols"], "sub_xvol_pullback", sum(comb3),
                n_draws=min(4000, max(500, boot // 5)), variant=var)
            print(f"   NULL {key} {lab}: "
                  f"{node['zero_edge_null'][lab]['p_zero_edge_sleeve_beats_floor3']}",
                  flush=True)
        # leave-one-out over the armed four
        for drop in ARMED_4:
            keep = [s for s in ARMED_4 if s != drop]
            d, cols_, raw_ = sleeve_day_matrix(rows, keep, acct, cm, nights, True)
            cmb = comb_from(raw_, cols_, Q.KELLY_HALF)
            months = ((max(d).year - min(d).year) * 12 + (max(d).month - min(d).month) + 1)
            r = Q.mc(cmb, Q.DIAL, L4, paths, seed_base=1)
            dv = derived(r, Q.weekday_sessions(min(d), max(d)), len(d),
                         statistics.fmean(cmb), len(d) / months, Q.DIAL)
            node["leave_one_out"][f"drop_{drop}"] = dict(
                sleeves=sorted(keep), book_days=len(d),
                total_r=round(sum(cmb), 4),
                sd_unit_r=round(statistics.pstdev(cmb), 5),
                share_of_armed4_total=round(sum(cmb) / sum(comb4), 4) if sum(comb4) else None,
                expected_passes_per_year=(
                    round(dv["p_pass"] * 365.0 / dv["median_calendar_days_to_pass"], 3)
                    if dv["median_calendar_days_to_pass"] else None),
                **dv)
            print(f"   LOO {key} drop_{drop} p={r['p_pass']:.5f}", flush=True)
        base = derived(Q.mc(comb4, Q.DIAL, L4, paths, seed_base=1), c4["sessions"],
                       c4["book_days"], statistics.fmean(comb4), c4["bdpm"], Q.DIAL)
        node["leave_one_out"]["ARMED_4_baseline"] = dict(
            sleeves=sorted(ARMED_4), book_days=len(comb4),
            total_r=round(sum(comb4), 4), sd_unit_r=round(statistics.pstdev(comb4), 5),
            share_of_armed4_total=1.0,
            expected_passes_per_year=(
                round(base["p_pass"] * 365.0 / base["median_calendar_days_to_pass"], 3)
                if base["median_calendar_days_to_pass"] else None),
            **base)
        # haircut sweep -- shared sleeves cut in BOTH books
        for sleeve in ("sub_xvol_pullback", "crypto"):
            shared = sleeve in c3["cols"]
            for model, fn in (("demean", haircut), ("scale", scale_haircut)):
                for lam in (1.0, 0.75, 0.5, 0.25, 0.0):
                    hr4 = fn(c4["raw"], c4["cols"], sleeve, lam)
                    cmb = comb_from(hr4, c4["cols"], Q.KELLY_HALF)
                    ref = (sum(comb_from(fn(c3["raw"], c3["cols"], sleeve, lam),
                                         c3["cols"], Q.KELLY_HALF))
                           if shared else sum(comb3))
                    r = Q.mc(cmb, Q.DIAL, L4, paths, seed_base=1)
                    node["haircut"].setdefault(sleeve, {}).setdefault(model, {})[
                        f"lambda_{lam}"] = dict(
                        total_r=round(sum(cmb), 4),
                        shared_with_conf_floor3=shared,
                        conf_floor3_total_r_at_same_lambda=round(ref, 4),
                        total_r_vs_conf_floor3=round(sum(cmb) - ref, 4),
                        beats_conf_floor3=bool(sum(cmb) > ref),
                        **derived(r, c4["sessions"], c4["book_days"],
                                  statistics.fmean(cmb), c4["bdpm"], Q.DIAL))
                    print(f"   HAIRCUT {key} {sleeve} {model} lam={lam} "
                          f"p={r['p_pass']:.5f} tot={sum(cmb):.2f} vs {ref:.2f}", flush=True)
        # break-even lambda, solved rather than searched. The advantage is exactly linear
        # in lambda (the haircut subtracts a constant per firing day), so two points fix it.
        def adv(lam):
            return sum(comb_from(haircut(c4["raw"], c4["cols"], "sub_xvol_pullback", lam),
                                 c4["cols"], Q.KELLY_HALF)) - sum(comb3)
        a1, a0 = adv(1.0), adv(0.0)
        slope = a1 - a0
        node["breakeven_lambda_vs_conf_floor3"] = (
            round(-a0 / slope, 4) if abs(slope) > 1e-12 else None)
        node["breakeven_linearity_residual"] = round(
            abs(adv(0.5) - (a0 + 0.5 * slope)), 12)
        node["advantage_at_lambda_1"] = round(a1, 4)
        node["advantage_at_lambda_0"] = round(a0, 4)
        node["breakeven_note"] = (
            "NEGATIVE break-even means ARMED-4 beats FLOOR-3 on window total R even with "
            "sub_xvol_pullback's edge at zero -- the residual is the Kelly/day-axis "
            "artifact, and `zero_edge_null` says how large that artifact is in expectation "
            "(which is larger than the lambda=0 point, because lambda=0 pins the sample "
            "mean at exactly zero rather than drawing it).")
        conc[key] = node
    return conc


def daily_autocorr(comb, days, cols, raw, lags=10):
    """Lag-1..k autocorrelation of the daily series, and of the FIRING indicator.

    They are different quantities and only one of them justifies a bootstrap block length.
    Session R's `crypto` lag-1 rho 0.441 is a property of when the sleeve trades; the
    bootstrap resamples RETURNS, so the block must come from the return series."""
    def ac(x, k):
        n = len(x)
        m = statistics.fmean(x)
        den = sum((v - m) ** 2 for v in x)
        if den <= 0 or n <= k:
            return None
        return sum((x[i] - m) * (x[i + k] - m) for i in range(n - k)) / den
    # NOTE: on the BOOK-DAY axis the firing indicator is identically 1 -- a book-day is by
    # definition a day something fired -- so its autocorrelation is undefined here. It is
    # only meaningful on a session axis, which this series does not carry. Reported as the
    # reason rather than as a bare None.
    rho = [ac(comb, k) for k in range(1, lags + 1)]
    vif = 1.0 + 2.0 * sum((1 - k / len(comb)) * (rho[k - 1] or 0.0)
                          for k in range(1, lags + 1))
    return dict(
        n=len(comb),
        rho_1_to_10=[round(r, 4) if r is not None else None for r in rho],
        two_over_sqrt_n=round(2.0 / math.sqrt(len(comb)), 4),
        variance_inflation_factor_10_lags=round(vif, 4),
        firing_indicator_rho1="undefined_on_a_book_day_axis_identically_1",
        note=("VIF <= 1 means the daily series carries no positive dependence to correct "
              "for and a block length of 1 is what the data supports. Session R's rho_1 "
              "0.441 for crypto is a property of the FIRING pattern on a session axis; the "
              "bootstrap resamples returns on the book-day axis, where the firing indicator "
              "is identically 1. Only the returns are resampled, so only they set the block."))


def frequency_profile(days):
    """Per-calendar-month book-day counts, so the headline's 7.11 can be read as a
    distribution rather than a mean. `monthly_pct_calendar` multiplies the mean R per
    book-day BY this number, so a month at the low end of the distribution earns
    proportionally less and the 38-day live window's ZERO is a tail this has to contain."""
    per = collections.Counter((d.year, d.month) for d in days)
    a, b = min(days), max(days)
    months = [(a.year + (a.month - 1 + k) // 12, (a.month - 1 + k) % 12 + 1)
              for k in range((b.year - a.year) * 12 + (b.month - a.month) + 1)]
    counts = sorted(per.get(m, 0) for m in months)
    n = len(counts)
    return dict(
        n_calendar_months=n, mean=round(statistics.fmean(counts), 3),
        # statistics.median, not counts[n//2] -- the latter is the UPPER median on
        # an even count and reported 7 where the true median is 6.5 (n=18).
        median=statistics.median(counts), p10=counts[max(0, int(0.10 * n))],
        p90=counts[min(n - 1, int(0.90 * n))], min=counts[0], max=counts[-1],
        months_with_zero_book_days=sum(1 for c in counts if c == 0),
        share_months_at_or_below_3=round(sum(1 for c in counts if c <= 3) / n, 4),
        by_month={f"{y}-{m:02d}": per.get((y, m), 0) for y, m in months})


# ------------------------------------------------------------------------------------
# 5. Controls
# ------------------------------------------------------------------------------------
def assert_matrix_reconstructs(raw, cols, comb_sealed):
    """The raw matrix must rebuild the series `mc_firm_rules.series` produced -- EXACTLY.

    Exact equality, not a tolerance. `(y/c)*c == y` is false in binary64 for most `y` at
    c = 0.85, 0.8 or 0.45 (8.2 %, 2.5 % and 5.5 % of random doubles fail), so the round trip
    is not exact in general. It is exact HERE because `build_matrix_from:898` builds every
    cell as `fmean(v) * BOOK_CONF[sl]`, so `y` is already in the image of `x c` -- measured
    0 of 156,612 inexact. That is a property of an upstream implementation detail, which is
    exactly the kind of thing a 1e-12 tolerance (about 10,000 ulp) would let rot. Session
    V's arithmetic refuter found the tolerance; this is the fix."""
    mine = comb_from(raw, cols, Q.KELLY_SEALED)
    return [(i, mine[i], comb_sealed[i]) for i in range(len(mine))
            if mine[i] != comb_sealed[i]]


def assert_governed_reduces(raw, cols, risk, rules, n_paths=20000):
    """`mc_governed` ungoverned == `mc_firm_rules.mc` == the sealed engine, on the real data.

    **This is an empirical result, not an arithmetic identity, and the difference matters.**
    `mc()` computes `dp = (sum_j m_j * k) * risk`; `mc_governed` computes
    `dp = sum_j risk * conf_j * k * raw_j`. Distributing `risk` over the sum is not exact in
    binary64: measured over all 18,480 day-values in this grid, **50.26 % differ bitwise**,
    by at most 3 ulp (4.16e-17). A constructed single-sleeve series where `dp` lands exactly
    on -0.05 flips `p_fail_daily` from 1.0 to 0.0. So the control CAN fail.

    It does not fail here, with about six orders of margin: the tightest barrier approach
    anywhere in the real grid is 2.8e-9 (a target crossing) against a perturbation bounded
    by ~1e-15 after 19 days of compounding. Session V's arithmetic refuter established both
    halves; the docstring used to claim the identity and now states the measurement.

    Run over BOTH conventions -- the sealed one and the half-Kelly/live-nominal one every
    headline `live_governor` figure uses, which the first version never tested."""
    bad = []
    for kelly, rk in ((Q.KELLY_SEALED, risk), (Q.KELLY_HALF, Q.DIAL)):
        g = mc_governed(raw, cols, rk, rules, n_paths, seed_base=1, kelly=kelly)
        m = Q.mc(comb_from(raw, cols, kelly), rk, rules, n_paths, seed_base=1)
        bad += [(kelly, k) for k in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout",
                                     "med_days_pass") if g[k] != m[k]]
    return bad


def derived(res, sessions, book_days, mean_r, bdpm, risk):
    md = res["med_days_pass"]
    return dict(
        p_pass=round(res["p_pass"], 6), se_p_pass=round(res["se_p_pass"], 6),
        p_fail_dd=round(res["p_fail_dd"], 6), p_fail_daily=round(res["p_fail_daily"], 6),
        p_timeout=round(res["p_timeout"], 6),
        median_book_days_to_pass=md,
        median_calendar_days_to_pass=round(md * sessions / book_days) if md else None,
        monthly_pct_calendar=round(mean_r * risk * bdpm * 100, 3))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=200_000)
    ap.add_argument("--boot", type=int, default=20_000)
    ap.add_argument("--account", default="FTMO")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--addendum", action="store_true",
                    help="compute only intra_size_convention and merge into an existing "
                         "--out, without re-running the rest (the --shares-only pattern)")
    a = ap.parse_args(argv)
    acct = a.account

    print("loading the book ...", flush=True)
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    pool = collections.defaultdict(list)
    for r in rows:
        c = r[f"cost_{acct}"]
        if c["status"] == "priced":
            pool[r["sleeve"]].append(c["cost_ex_swap_r"])
    cm = {k: statistics.median(v) for k, v in pool.items()}
    all11 = list(M.CORE8_ORDER) + list(M.CLEAN3_CONF)

    if a.addendum:
        p = Path(a.out)
        doc = json.loads(p.read_text())
        rbl = {r.label: r for r in Q.rule_sets(acct)[0]}
        doc["intra_size_convention"] = intra_size_convention(
            rows, acct, cm, a.paths, rules_by_label=rbl)
        doc["outside_the_selection_window"] = outside_the_selection_window(
            rows, acct, cm, sd_book, a.paths, rbl)
        doc["from_here_governed"] = from_here_governed(rows, acct, cm, a.paths, rbl)
        # `concentration` needs the same cell shape `main` builds. Rebuild just the six
        # (book, carry) forward cells it touches rather than the whole 24-cell grid.
        _cells = {}
        for _name, _keep in (("ARMED_4", ARMED_4), ("CONF_FLOOR_3", CONF_FLOOR_3)):
            for _n in (0.0, 1.0, "max"):
                _d, _c, _r = sleeve_day_matrix(rows, _keep, acct, cm, _n, True)
                _m = ((max(_d).year - min(_d).year) * 12
                      + (max(_d).month - min(_d).month) + 1)
                _cells[(_name, _n, True)] = dict(
                    days=_d, cols=_c, raw=_r,
                    sessions=Q.weekday_sessions(min(_d), max(_d)),
                    book_days=len(_d), bdpm=len(_d) / _m)
        doc["concentration"] = concentration(_cells, rows, acct, cm, a.paths, a.boot,
                                             rbl["L4_FIRM_TRUE_PH1"])
        p.write_text(json.dumps(doc, indent=1, default=str))
        print(f"merged intra_size_convention into {p}")
        return doc

    rules_by_label = {r.label: r for r in Q.rule_sets(acct)[0]}
    L0, L4, P2 = (rules_by_label["L0_LEGACY_SEALED"],
                  rules_by_label["L4_FIRM_TRUE_PH1"],
                  rules_by_label["P2_BOTH_PHASES"])
    firm_ph1_mindays = rules_by_label["L6_FIRM_TRUE_PH1_MINDAYS_LATCH"]

    out = dict(
        schema="gtos.w7_recost.armed_set_mc.v1",
        generated_by="scripts/armed_set_mc.py",
        account=acct,
        question=("The published MC measures three DERIVED books at a vol-matched sizing "
                  "no live path implements. Measure the NAMED book that is being armed, "
                  "at the sizing the live path actually applies, across the carry band."),
        dial_nominal_pct=Q.DIAL * 100,
        sets={k: (v or all11) for k, v in SETS.items()},
        set_provenance=dict(
            ARMED_4="the approved book; run_book.py --tags + ultimate_book_include_clean3: true",
            CONF_FLOOR_3="ARMED_4 minus sub_xvol_pullback -- what a confidence floor selects",
            BOTH_3=("Q's SURVIVORS_BOTH_ACCOUNTS. A DIFFERENT three: it drops metals_core "
                    "and keeps sub_xvol_pullback. Included because the two 'three-sleeve "
                    "books' in the record are not the same book."),
            ALL_11_BOOK_OF_RECORD="the published comparator"),
        sizing_conventions=dict(
            published=dict(kelly=Q.KELLY_SEALED, risk_basis=Q.RISK_VOL_MATCHED,
                           source="build_survivor_book.py:64 -- risk = dial * sd_ref/sd_var"),
            live=dict(kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL,
                      source=("admission.py:1470 base_risk = prof.risk_per_unit_A = 0.020; "
                              "kelly bins from admission.KELLY_LITE_BINS_HALF because "
                              "ultimate_book_kelly_conservative: true"))),
        n_paths=a.paths, sd_book_reference=round(sd_book, 5),
        controls=dict(), sizing_provenance={}, w7_certification_check={},
        grid={}, live_governor={}, from_here={},
        concentration={}, frequency={})

    # --- build every cell once ------------------------------------------------------
    cells = {}
    for name, keep in SETS.items():
        keep = keep or all11
        for nights in (0.0, 1.0, "max"):
            for fwd in (True, False):
                days, cols, raw = sleeve_day_matrix(rows, keep, acct, cm, nights, fwd)
                sub = [r for r in rows if r["sleeve"] in keep]
                _, comb_sealed, risk_pub, vs = Q.series(
                    sub, acct, cm, nights, sd_book, forward=fwd)
                sess = Q.weekday_sessions(min(days), max(days))
                months = ((max(days).year - min(days).year) * 12
                          + (max(days).month - min(days).month) + 1)
                cells[(name, nights, fwd)] = dict(
                    days=days, cols=cols, raw=raw, comb_sealed=comb_sealed,
                    risk_published=risk_pub, vol_scale=vs, sessions=sess,
                    book_days=len(days), bdpm=len(days) / months)

    # --- controls -------------------------------------------------------------------
    print("control 1/3: raw matrix rebuilds the published series ...", flush=True)
    recon_bad = []
    for k, c in cells.items():
        recon_bad += [(k, *b) for b in assert_matrix_reconstructs(
            c["raw"], c["cols"], c["comb_sealed"])]
    print(f"   {len(cells)} cells, {len(recon_bad)} mismatches", flush=True)

    print("control 2/3: mc_governed(ungoverned) == mc_firm_rules.mc == sealed engine ...",
          flush=True)
    ident_bad = []
    for k, c in cells.items():
        ident_bad += [(k, f) for f in assert_governed_reduces(
            c["raw"], c["cols"], c["risk_published"], L0)]
    print(f"   {len(ident_bad)} disagreements", flush=True)

    print("control 3/3: mc_firm_rules.mc == INTEG_portfolio_build_w2.mc_series ...",
          flush=True)
    W2 = M._route_mc()
    w2_bad = []
    for k, c in cells.items():
        mine = Q.mc(c["comb_sealed"], c["risk_published"], Q.Rules.LEGACY, 20000, seed_base=1)
        theirs = W2.mc_series(c["comb_sealed"], c["risk_published"], n_paths=20000,
                              seed_base=1)
        w2_bad += [(k, f) for f in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout",
                                    "med_days_pass") if mine[f] != theirs[f]]
    print(f"   {len(w2_bad)} disagreements", flush=True)
    out["controls"] = dict(
        matrix_reconstruction_mismatches=len(recon_bad),
        governed_reduces_to_mc_disagreements=len(ident_bad),
        mc_equals_sealed_engine_disagreements=len(w2_bad),
        cells=len(cells),
        meaning=("Every number below descends from INTEG_portfolio_build_w2.mc_series by a "
                 "chain of bit-identical steps, so each difference is attributable to one "
                 "named change and to nothing else."))
    if recon_bad or ident_bad or w2_bad:
        raise SystemExit(f"CONTROL FAILED recon={recon_bad[:3]} ident={ident_bad[:3]} "
                         f"w2={w2_bad[:3]}")

    out["sizing_provenance"] = sizing_provenance(cells, sd_book)
    out["w7_certification_check"] = w7_certification_check(rows, sd_book)
    print("sizing provenance:", json.dumps(
        out["sizing_provenance"].get("ARMED_4|fwd_nights_max", {})), flush=True)

    # --- the grid: every set x carry x sizing convention -----------------------------
    for (name, nights, fwd), c in cells.items():
        key = f"{'fwd' if fwd else 'full'}_nights_{nights if nights != 'max' else 'max'}"
        node = out["grid"].setdefault(name, {}).setdefault(key, dict(
            book_days=c["book_days"], weekday_sessions=c["sessions"],
            book_days_per_calendar_month=round(c["bdpm"], 2),
            vol_scale=round(c["vol_scale"], 4)))
        for conv, kelly, risk in (("published", Q.KELLY_SEALED, c["risk_published"]),
                                  ("live", Q.KELLY_HALF, Q.DIAL)):
            comb = comb_from(c["raw"], c["cols"], kelly)
            mean_r = statistics.fmean(comb)
            sub = dict(eff_risk_pct=round(risk * 100, 4),
                       mean_r_per_book_day=round(mean_r, 5),
                       worst_day_pct_of_equity=round(100 * min(comb) * risk, 4),
                       best_day_pct_of_equity=round(100 * max(comb) * risk, 4),
                       sd_day_pct_of_equity=round(100 * statistics.pstdev(comb) * risk, 4),
                       rules={})
            for lab, rl in (("L0_LEGACY_SEALED", L0), ("L4_FIRM_TRUE_PH1", L4),
                            ("P2_BOTH_PHASES", P2)):
                r = Q.mc(comb, risk, rl, a.paths, seed_base=1)
                sub["rules"][lab] = derived(r, c["sessions"], c["book_days"], mean_r,
                                            c["bdpm"], risk)
                print(f"   {name:22s} {key:16s} {conv:9s} {lab:20s} "
                      f"p={r['p_pass']:.5f}", flush=True)
            node[conv] = sub

    # --- the live governor, on the armed book and its two comparators ----------------
    for name in ("ARMED_4", "CONF_FLOOR_3", "BOTH_3"):
        for nights in (0.0, 1.0, "max"):
            c = cells[(name, nights, True)]
            key = f"fwd_nights_{nights if nights != 'max' else 'max'}"
            row = {}
            for lab, cap, dr in (("live_uncapped", None, False),
                                 ("live_gross_cap_4pct", GROSS_OPEN_RISK_CAP, False),
                                 ("live_gross_cap_and_smooth_derisk", GROSS_OPEN_RISK_CAP,
                                  True)):
                for rlab, rl in (("L4_FIRM_TRUE_PH1", L4), ("P2_BOTH_PHASES", P2)):
                    r = mc_governed(c["raw"], c["cols"], Q.DIAL, rl, a.paths,
                                    seed_base=1, kelly=Q.KELLY_HALF, gross_cap=cap,
                                    derisk=dr)
                    comb = comb_from(c["raw"], c["cols"], Q.KELLY_HALF)
                    row.setdefault(lab, {})[rlab] = dict(
                        **derived(r, c["sessions"], c["book_days"],
                                  statistics.fmean(comb), c["bdpm"], Q.DIAL),
                        p_fail_entry_block=round(r["p_fail_entry_block"], 6),
                        gross_cap_bound_day_share=r["gross_cap_bound_day_share"])
                    print(f"   GOV {name:14s} {key:14s} {lab:34s} {rlab:18s} "
                          f"p={r['p_pass']:.5f}", flush=True)
            out["live_governor"].setdefault(name, {})[key] = row

    # --- from here: FTMO is 1.97% from its phase-1 target, not 10% -------------------
    e0 = FTMO_EQUITY_WITNESSED / FTMO_INITIAL
    out["from_here"] = dict(
        equity_witnessed=FTMO_EQUITY_WITNESSED,
        equity_in_commission_prompt=FTMO_EQUITY_COMMISSION,
        source="docs/audits/fable5-vision-audit-20260725/VPS_EXPORT_FINDINGS.md:107",
        start_equity_units=round(e0, 7),
        remaining_to_phase1_target_pct_of_initial=round(100 * (1.10 - e0), 4),
        remaining_to_phase1_target_pct_of_current_equity=round(
            100 * (1.10 * FTMO_INITIAL - FTMO_EQUITY_WITNESSED) / FTMO_EQUITY_WITNESSED, 4),
        remaining_usd=round(1.10 * FTMO_INITIAL - FTMO_EQUITY_WITNESSED, 2),
        headroom_to_static_floor_usd=round(FTMO_EQUITY_WITNESSED - 0.90 * FTMO_INITIAL, 2),
        headroom_to_static_floor_pct_of_current_equity=round(
            100 * (e0 - 0.90) / e0, 3),
        phase1_days_served=FTMO_PHASE1_DAYS_SERVED,
        note=("Every published p_pass starts at 1.0 -- a fresh $100,000 challenge. FTMO is "
              "not there. It needs $2,120.44 more, which is 2.120% of the initial balance "
              "and 1.966% of current equity -- the commission's '1.97%' is the second "
              "denominator -- and it has $17,879.56 of room to a STATIC $90,000 floor. Its "
              "4-day phase-1 minimum is already served (269 deals, 2026-06-01..07-03). "
              "Phase 2 still starts fresh at 1.0, so the 2-step figure moves much less "
              "than the phase-1 one. The head start is real money made by the live core-8 "
              "book, NOT by the four sleeves being armed."),
        cells={})
    for name in ("ARMED_4", "CONF_FLOOR_3", "BOTH_3"):
        for nights in (0.0, 1.0, "max"):
            c = cells[(name, nights, True)]
            key = f"{name}|fwd_nights_{nights if nights != 'max' else 'max'}"
            node = {}
            for conv, kelly, risk in (("published", Q.KELLY_SEALED, c["risk_published"]),
                                      ("live", Q.KELLY_HALF, Q.DIAL)):
                comb = comb_from(c["raw"], c["cols"], kelly)
                mean_r = statistics.fmean(comb)
                for lab, rl, e, served in (
                        ("phase1_from_100k", L4, 1.0, 0),
                        ("phase1_from_here", L4, e0, 0),
                        ("phase1_from_here_mindays_served", firm_ph1_mindays, e0,
                         FTMO_PHASE1_DAYS_SERVED),
                        ("phase1_from_here_mindays_unserved", firm_ph1_mindays, e0, 0),
                        ("two_step_from_100k", P2, 1.0, 0),
                        ("two_step_from_here", P2, e0, 0)):
                    r = Q.mc(comb, risk, rl, a.paths, seed_base=1,
                             start_equity=e, start_days_served=served)
                    node.setdefault(conv, {})[lab] = derived(
                        r, c["sessions"], c["book_days"], mean_r, c["bdpm"], risk)
                    print(f"   FROMHERE {name:14s} n{nights!s:5s} {conv:9s} {lab:34s} "
                          f"p={r['p_pass']:.5f}", flush=True)
            out["from_here"]["cells"][key] = node

    # --- concentration ---------------------------------------------------------------
    out["concentration"] = concentration(cells, rows, acct, cm, a.paths, a.boot, L4)

    # --- frequency -------------------------------------------------------------------
    for name in ("ARMED_4", "CONF_FLOOR_3", "BOTH_3", "ALL_11_BOOK_OF_RECORD"):
        for fwd in (True, False):
            c = cells[(name, "max", fwd)]
            out["frequency"][f"{name}|{'fwd' if fwd else 'full'}"] = frequency_profile(
                c["days"])

    p = Path(a.out)
    p.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {p}")
    return out


if __name__ == "__main__":
    main()

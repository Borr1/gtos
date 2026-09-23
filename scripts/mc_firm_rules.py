"""The challenge-pass Monte Carlo, with the firm rules as parameters instead of constants.

    python3 scripts/mc_firm_rules.py            # writes MC_FIRM_TRUE_V1.json
    python3 scripts/mc_firm_rules.py --paths 20000   # cheap smoke run

REPRODUCING THE COMMITTED ARTIFACT BYTE-FOR-BYTE
------------------------------------------------
One command is NOT enough, and the difference is one top-level key's position. Session Q
added `contribution_shares` to `main()` after generating the artifact and merged it in
through `--shares-only`, which appends the key at the END of the document; a single run
places it before `accounts`. Measured by Session V (B381): a fresh 200,000-path run at HEAD
is **semantically identical to the committed file -- 0 differences over every scalar, list
and key** -- and differs from it in 226,931 byte positions, all of them that one move. The
exact sequence that reproduces sha256 `886dcf69859cfe135024896a287674f8ec008695f5e99c47be
12429239f4301d`:

    python3 scripts/mc_firm_rules.py --out /tmp/mc.json      # 200,000 paths, ~40 min
    python3 - <<'EOF'
    import json, pathlib
    p = pathlib.Path('/tmp/mc.json'); d = json.loads(p.read_text())
    d.pop('contribution_shares')
    p.write_text(json.dumps(d, indent=1, default=str))
    EOF
    python3 scripts/mc_firm_rules.py --shares-only --out /tmp/mc.json

The key is left where it is rather than moved, because moving it would change the bytes of
the committed artifact for cosmetic reasons. This note is the fix.

WHY THIS FILE EXISTS
--------------------
`INTEG_portfolio_build.py:298` fixes the challenge rules as module constants:

    TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05; BLOCK = 5; N = 20000; PATHCAP = 2000

`INTEG_portfolio_build_w2.py:250` rebinds them and `mc_series` (`:252-270`) reads them as
globals. Every published `p_pass` in `SURVIVOR_BOOK_V1.json` comes through that engine, so
every published `p_pass` is computed against one rule set -- redacted_account's 8% phase-1 target,
a drawdown measured from the running peak, and a daily loss measured as a percentage of the
day's opening equity.

Measured firm rules (`broker_truth_layer_2026_07_27/FIRM_RULES_V1.json`) differ from that on
three axes, and NOT all in the same direction:

  TARGET  FTMO phase 1 is 10.0% [MEASURED, FTMO's own captured page], not 8%.
          redacted_account phase 1 is 8.0% [TRANSFERRED]. So the constant is right for one
          account and 2 percentage points too easy for the other.   -> legacy OPTIMISTIC (FTMO)

  MAXDD   FTMO's max overall loss is "static (not trailing) for 2-Step", floor $90,000
          [MEASURED]. The engine tests (peak-eq)/peak >= 0.10, which is a TRAILING stop and
          is strictly harder to survive whenever peak > 1.       -> legacy PESSIMISTIC (both)

  DAILY   Both firms define the daily allowance as a FIXED CASH amount = 5% of the initial
          balance. redacted_account's own worked example is decisive: "if you start a new day with
          $110,000 and lose $5,000 ... losing $5,000 breaches the limit ... even though your
          equity has not dropped to $95,000." The engine tests dp <= -0.05 where dp is a
          return on the day's OPENING equity, so at $110,000 it permits $5,500.
                                                                   -> legacy OPTIMISTIC (both)

THE ENGINE IS NOT REIMPLEMENTED, IT IS GENERALISED
--------------------------------------------------
`mc()` below is byte-for-byte the same arithmetic as `INTEG_portfolio_build_w2.mc_series`
when `Rules.LEGACY` is passed -- same seeds, same circular block bootstrap, same comparison
order, same early-exit semantics. `verify_bit_identity()` asserts that over every series in
the published grid, and `tests/test_mc_firm_rules.py` asserts it in CI. That is what makes
the comparison a controlled one: a difference in the output can only come from the rule
change, because nothing else changed.

Nothing in the sealed route is edited. `INTEG_portfolio_build.TARGET` is still 0.08 and the
8% result is still reproducible by `scripts/build_survivor_book.py` (byte-identical).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass
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

import recost_w7_validation as M  # noqa: E402

DIAL = 0.020  # config/agent_config.yaml:1246-1394, profile clean3_w7_ceiling_nom2p00
OUT = REPO / "research/operations/w7_recost_2026_07_27/MC_FIRM_TRUE_V1.json"
PUBLISHED = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
FIRM_RULES = REPO / "research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json"

# Basis tokens. The string is the contract; `mc()` branches on it once per call.
DAILY_LEGACY = "pct_of_day_start_equity"      # dp <= -limit                (engine as sealed)
DAILY_FIRM = "cash_pct_of_initial"            # eq*dp <= -limit             (both firms)
DD_LEGACY = "trailing_from_peak"              # (peak-eq)/peak >= limit     (engine as sealed)
DD_FIRM = "static_floor_of_initial"           # eq <= 1 - limit ($90,000)   (FTMO [MEASURED])


@dataclass(frozen=True)
class Rules:
    """One challenge rule set. `block`/`pathcap` are the sealed bootstrap shape.

    `targets` is a tuple of phase profit targets. `(0.08,)` is a one-phase evaluation and
    reduces exactly to the sealed engine. `(0.10, 0.05)` is FTMO's 2-Step: on clearing
    phase 1 the account is reset to its initial balance and phase 2 begins with the same
    loss limits and a 5% target -- so equity and peak reset, and the day counter does not.
    """

    label: str
    targets: tuple = (0.08,)
    daily_limit: float = 0.05
    daily_basis: str = DAILY_LEGACY
    maxdd_limit: float = 0.10
    maxdd_basis: str = DD_LEGACY
    min_trading_days: int | None = None
    # "latch": on reaching target the operator stops taking risk and waits out the minimum
    #          (what the profile's mandatory derisk_mode would do). p_pass cannot fall.
    # "at_risk": keep trading the book at full size until the minimum is served. A bound.
    min_days_model: str = "latch"
    block: int = 5
    pathcap: int = 2000

    def as_dict(self):
        d = dict(self.__dict__)
        d["targets"] = list(d["targets"])
        return d


Rules.LEGACY = Rules(label="LEGACY_SEALED_ENGINE")


def mc(vals, risk, rules: Rules, n_paths: int, seed_base: int = 0,
       start_equity: float = 1.0, start_days_served: int = 0):
    """Block-bootstrap challenge MC. Identical to `INTEG_portfolio_build_w2.mc_series`
    under `Rules.LEGACY` and the default `start_equity`/`start_days_served`; see the
    module docstring and `verify_bit_identity`.

    `start_equity` is the account's CURRENT equity in units of its initial balance, so
    1.0 is a fresh challenge and 1.07872 is FTMO on 2026-07-29. Every limit stays
    anchored where the firm anchors it -- the target at `initial x (1+t)`, the static
    floor at `initial x (1-mlim)`, the daily allowance at `5% of initial` -- so raising
    it moves the account nearer the target AND further from the floor at the same time.
    That is the whole point of asking the question from here rather than from $100,000.
    `peak` starts at `max(1, start_equity)`, i.e. the current equity is assumed to BE the
    high-water mark; that is the optimistic reading and it only bites the trailing
    (`DD_LEGACY`) basis, which is not FTMO's measured rule.

    `start_days_served` is trading days already booked in the CURRENT phase. It exists
    because `min_trading_days` is inert from a standing start (a book that needs ~19 days
    to make 10% cannot fail a 4-day minimum) and becomes binding from a from-here start,
    where the remaining distance is 1.97% and the median pass is a handful of days.
    """
    n = len(vals)
    block, pathcap = rules.block, rules.pathcap
    targets, nph = rules.targets, len(rules.targets)
    dlim, mlim = rules.daily_limit, rules.maxdd_limit
    daily_firm = rules.daily_basis == DAILY_FIRM
    dd_firm = rules.maxdd_basis == DD_FIRM
    # FTMO states the static rule as a cash FLOOR ("$90,000"), not as a drawdown fraction.
    # Testing `eq <= floor` is both the firm's own wording and better conditioned than
    # `(1.0 - eq) >= mlim`, which misses the exact boundary: 1.0 - 0.9 is 0.0999...8.
    floor = 1.0 - mlim
    mintd = rules.min_trading_days
    latch = rules.min_days_model == "latch"

    outs = collections.Counter()
    dlist = []
    phase_reached = collections.Counter()
    for s in range(n_paths):
        rng = random.Random(s * 131 + seed_base + int(risk * 1e6))
        eq = start_equity
        peak = max(1.0, start_equity)
        res = "timeout"
        dc = 0        # total days traded across all phases
        dcp = start_days_served  # days traded in the current phase (min-days is per phase)
        ph = 0
        for _ in range(pathcap):
            start = rng.randrange(n)
            broke = False
            for k in range(block):
                dp = vals[(start + k) % n] * risk
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
                            continue          # keep trading at full size
                        dc += mintd - dcp     # stop risking, serve out the minimum
                    ph += 1
                    if ph == nph:
                        res = "pass"
                        broke = True
                        break
                    eq = 1.0                  # phase reset: fresh account, same limits
                    peak = 1.0
                    dcp = 0
            if broke:
                break
        outs[res] += 1
        phase_reached[ph] += 1
        if res == "pass":
            dlist.append(dc)
    md = int(statistics.median(dlist)) if dlist else None
    p = outs["pass"] / n_paths
    return dict(
        p_pass=p, p_fail_dd=outs["fail_maxdd"] / n_paths,
        p_fail_daily=outs["fail_daily"] / n_paths, p_timeout=outs["timeout"] / n_paths,
        med_days_pass=md, n_paths=n_paths,
        se_p_pass=math.sqrt(p * (1 - p) / n_paths),
        phases_cleared={str(k): v / n_paths for k, v in sorted(phase_reached.items())})


# ------------------------------------------------------------------------------------
# Series construction -- mirrors build_survivor_book.econ() up to (days, comb, risk).
# Verified against the published artifact for all 24 cells by `verify_series`.
# ------------------------------------------------------------------------------------
def weekday_sessions(a, b):
    return sum(1 for i in range((b - a).days + 1)
               if (a + dt.timedelta(days=i)).weekday() < 5)


# ------------------------------------------------------------------------------------
# Sizing conventions. The sealed grid is `KELLY_SEALED` + `RISK_VOL_MATCHED`; the live
# book runs `KELLY_HALF` + `RISK_LIVE_NOMINAL`, and they are NOT the same size.
#
#   RISK_VOL_MATCHED  risk = dial x (sd_book / sd_variant). `build_survivor_book.econ:64`.
#                     Every published `eff_risk_pct` is this. It re-scales each candidate
#                     book to the 11-sleeve reference book's per-book-day volatility, so a
#                     sparse book -- which has a LARGER per-book-day sd because it only has
#                     days on which it fired -- is sized DOWN. Survivors/fwd: x0.4234.
#   RISK_LIVE_NOMINAL risk = dial, full stop. This is what the deployable path does:
#                     `admission.py:1470` sets `base_risk = prof.risk_per_unit_A`, which for
#                     `clean3_w7_ceiling_nom2p00` is 0.020 with no volatility term anywhere
#                     downstream (`size_correlated_units` -> `unit_risk = base * conf *
#                     derisk_mult`). The W5 `clean3_*` profiles DID pre-multiply a vol scale
#                     into the constant; the W7 dials deliberately do not
#                     (`ultimate_book_live_package.py:561-567`, "CONVENTION DIFFERENCE").
#
#   KELLY_SEALED      (0.85, 1.10, 1.60) cap 1.75 -- `recost_w7_validation.kelly_mult`.
#   KELLY_HALF        (0.748, 0.991, 1.241) -- `admission.KELLY_LITE_BINS_HALF`, which is
#                     what `ultimate_book_kelly_conservative: true` selects live.
#   KELLY_NONE        1.0 -- the flat book, for isolating what the Kelly tilt is worth.
#
# The half bins are READ from the live module, not transcribed, so a correction there
# propagates here. Same discipline as `rule_sets()` reading FIRM_RULES_V1.json.
# ------------------------------------------------------------------------------------
KELLY_SEALED = "sealed_full_bins"
KELLY_HALF = "live_half_bins"
KELLY_NONE = "flat"
RISK_VOL_MATCHED = "vol_matched_to_reference_book"
RISK_LIVE_NOMINAL = "live_nominal_per_unit"


def _live_half_bins():
    sys.path.insert(0, str(REPO))
    from src.components.ultimate_book.admission import KELLY_LITE_BINS_HALF
    return KELLY_LITE_BINS_HALF


def kelly_fn(kelly):
    if kelly == KELLY_SEALED:
        return M.kelly_mult
    if kelly == KELLY_NONE:
        return lambda na: 1.0
    if kelly == KELLY_HALF:
        bins = _live_half_bins()

        def _half(na):
            for lo, hi, m in bins:
                if lo <= na <= hi:
                    return min(m, M.KELLY_CAP)
            return 1.0
        return _half
    raise SystemExit(f"unknown kelly convention: {kelly}")


def series(sub, acct, cm, nights, sd_book, dial=DIAL, forward=False,
           kelly=KELLY_SEALED, risk_basis=RISK_VOL_MATCHED):
    """(days, comb, risk, vol_scale) for one grid cell -- the same construction as
    `scripts/build_survivor_book.py:50-70` at the default conventions."""
    km = kelly_fn(kelly)
    for r in sub:
        n = M.SLEEVE_MAX_NIGHTS[r["sleeve"]] if nights == "max" else nights
        c, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
        r["R_s"] = None if c is None else r["R_gross"] - c
    days, _, Mx, _ = M.build_matrix_from(sub, "R_s")
    nact = [sum(1 for v in row if abs(v) > 1e-9) for row in Mx]
    Mk = [[v * km(nact[i]) for v in Mx[i]] for i in range(len(Mx))]
    comb = [sum(r) for r in Mk]
    if forward:
        pair = [(v, d) for v, d in zip(comb, days) if d.year >= 2025]
        comb = [v for v, _ in pair]
        days = [d for _, d in pair]
    sd = statistics.pstdev(comb)
    vs = sd_book / sd if sd else 0.0
    risk = dial * vs if risk_basis == RISK_VOL_MATCHED else dial
    return days, comb, risk, vs


def _priced_pool(rows, acct):
    pool = collections.defaultdict(list)
    for r in rows:
        c = r[f"cost_{acct}"]
        if c["status"] == "priced":
            pool[r["sleeve"]].append(c["cost_ex_swap_r"])
    return pool


def parse_sleeve_set(spec):
    """`NAME=sleeve_a,sleeve_b` -> (NAME, [sleeve_a, sleeve_b]). Fails closed on an
    unknown sleeve, because a typo would otherwise silently measure a smaller book."""
    if "=" not in spec:
        raise SystemExit(f"--sleeve-set wants NAME=a,b,c; got {spec!r}")
    name, _, rest = spec.partition("=")
    sleeves = [s.strip() for s in rest.split(",") if s.strip()]
    if not sleeves:
        raise SystemExit(f"--sleeve-set {name} names no sleeves")
    unknown = [s for s in sleeves if s not in M.BOOK_CONF]
    if unknown:
        raise SystemExit(f"--sleeve-set {name}: unknown sleeve(s) {unknown}; "
                         f"the book of record is {sorted(M.BOOK_CONF)}")
    dupes = [s for s in set(sleeves) if sleeves.count(s) > 1]
    if dupes:
        raise SystemExit(f"--sleeve-set {name}: repeated sleeve(s) {sorted(dupes)}")
    return name.strip(), sleeves


def build_cells(extra_sets=None, kelly=KELLY_SEALED, risk_basis=RISK_VOL_MATCHED):
    """Every (account, variant, window, nights) cell in the published grid, with its
    bootstrap series and effective risk. 24 cells. Also returns each account's survivor
    set -- which is NOT the same set on both accounts, and that matters (see the report).

    `extra_sets` is an ordered {name: [sleeve, ...]} of EXPLICITLY NAMED books, appended
    after the three derived variants so the derived grid keeps its published shape and
    ordering. It exists because the three derived variants are all *computed* selections
    (all-11, per-account survivors, the two-account intersection) and the book that is
    actually going to be armed is a NAMED one: `run_book.py --tags` plus
    `ultimate_book_include_clean3: true`. Nothing in the published grid measures a book
    chosen that way, and `sub_xvol_pullback`'s registry confidence of 0.45 means no
    confidence floor can select it (`admission.CLEAN3_REGISTRY`).
    """
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")

    # The survivor set is per account and the two are NOT the same. redacted_account charges
    # metals_core 0.0638 R/night against FTMO's 0.0431, which puts its break-even at 329 h
    # against a 320 h ceiling -- it misses by 2.8 % of its own horizon. FTMO charges
    # vp_euidx_pocgrav 0.0260 against redacted_account's 0.0175, which does the same in reverse.
    # So `SURVIVORS_ONLY` names a different portfolio on each account, and the book that
    # survives on BOTH -- the one OD3_DOSSIER_SURVIVOR_BOOK.md §0 describes -- is the
    # three-sleeve intersection, which no published grid measures. Measure it.
    tabs, survs = {}, {}
    for acct in ("FTMO", "redacted_account"):
        cm = {k: statistics.median(v) for k, v in _priced_pool(rows, acct).items()}
        tabs[acct] = (cm, M.sleeve_table(rows, acct, cm))
        survs[acct] = [sl for sl, v in tabs[acct][1].items() if v["survives_at_max_carry"]]
    both = [sl for sl in survs["FTMO"] if sl in survs["redacted_account"]]

    cells = []
    survivors = {}
    for acct in ("FTMO", "redacted_account"):
        cm, tab = tabs[acct]
        surv = survs[acct]
        survivors[acct] = sorted(surv)
        named = list((extra_sets or {}).items())
        for label, keep in ([("ALL_11_BOOK_OF_RECORD", list(tab)),
                             ("SURVIVORS_ONLY", surv),
                             ("SURVIVORS_BOTH_ACCOUNTS", both)] + named):
            sub = [r for r in rows if r["sleeve"] in keep]
            for fwd in (False, True):
                for nights in (0.0, 1.0, "max"):
                    days, comb, risk, vs = series(sub, acct, cm, nights, sd_book,
                                                  forward=fwd, kelly=kelly,
                                                  risk_basis=risk_basis)
                    a, b = min(days), max(days)
                    sess = weekday_sessions(a, b)
                    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
                    cells.append(dict(
                        account=acct, variant=label,
                        window="forward_2025+" if fwd else "full_2015_2026",
                        nights="sleeve_max" if nights == "max" else nights,
                        key=f"{'fwd' if fwd else 'full'}_nights_"
                            f"{nights if nights != 'max' else 'max'}",
                        sleeves=sorted(keep), comb=comb, risk=risk, vol_scale=vs,
                        book_days=len(days), weekday_sessions=sess,
                        book_days_per_calendar_month=len(days) / months,
                        mean_r_per_book_day=statistics.fmean(comb),
                        worst_day_unit_r=min(comb), best_day_unit_r=max(comb),
                        sd_unit_r=statistics.pstdev(comb)))
    return cells, sd_book, survivors


# ------------------------------------------------------------------------------------
# Controls
# ------------------------------------------------------------------------------------
def verify_bit_identity(cells, n_paths=20000):
    """`mc(..., Rules.LEGACY)` must equal `W2.mc_series(...)` exactly, on every cell.

    Not "close to". Exactly. The engines share seeds and comparison order, so any drift
    is a bug in this file, and the whole point of the file is that it introduces none."""
    W2 = M._route_mc()
    bad = []
    for c in cells:
        mine = mc(c["comb"], c["risk"], Rules.LEGACY, n_paths, seed_base=1)
        theirs = W2.mc_series(c["comb"], c["risk"], n_paths=n_paths, seed_base=1)
        for k in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout", "med_days_pass"):
            if mine[k] != theirs[k]:
                bad.append((c["account"], c["variant"], c["key"], k, mine[k], theirs[k]))
    return bad


#: The three published columns that move when the COST artifact gains coverage, as against
#: `book_days`, which cannot: the day axis is decided by which sleeves fired on which dates,
#: and re-pricing a trade never adds or removes a day. That asymmetry is what makes
#: `--allow-cost-artifact-drift` safe -- see `verify_series`.
_COST_DERIVED_COLUMNS = ("eff_risk_pct", "vol_scale", "mean_r_per_book_day")


def verify_series(cells, sizing_sealed=True, allow_cost_drift=False):
    """The reconstructed series must reproduce the published artifact's own summary
    columns. If `eff_risk_pct`, `mean_r_per_book_day` and `book_days` all match, the
    bootstrap input is the published one and only the rules can differ.

    Under a non-sealed sizing convention (`--kelly` / `--risk-basis`) three of those four
    columns are SUPPOSED to move, so checking them would fail by construction. The one
    that is convention-invariant is `book_days` -- the day axis is decided by which
    sleeves fired, and neither the conviction bins nor the risk basis touches it -- so
    that check is kept and the other three are dropped with the reason recorded in the
    artifact (`controls.series_reconstruction_scope`). Returns (bad, scope, drift).

    `allow_cost_drift` (2026-07-30, Session AI) -- WHY IT EXISTS AND WHY IT IS NOT A FUDGE
    -----------------------------------------------------------------------------------
    At HEAD this control fails on 36 of 36 cells, and the cause is benign: commits
    `8f6da5150` ("price the six symbols that were blocking the LIVE book's own scores") and
    `33d854189` ("close the metals tick gap") extended `BROKER_TRUE_COSTS_V1.json` AFTER
    Session Q sealed its figures. FTMO now carries 167 priced instruments against
    redacted_account's 76, so `crypto` goes MEASURED 35 -> 72 and `idxrev` 4,939 -> 5,876, and only
    the FTMO half of the grid moves. More measured coverage is strictly better evidence; the
    artifact is simply older than its inputs.

    So the flag turns mismatches on the THREE COST-DERIVED columns into a published `drift`
    block while `book_days` stays a HARD failure. That split is the whole safety argument: a
    cost re-pricing cannot change which days a sleeve traded, so a `book_days` mismatch means
    a different TRADE SET -- a real defect this flag must never hide. The default is unchanged
    and still fails closed.
    """
    pub = json.loads(PUBLISHED.read_text())
    scope = "all_four_columns" if sizing_sealed else "book_days_only_sizing_convention_differs"
    if sizing_sealed and allow_cost_drift:
        scope = "book_days_hard_plus_published_cost_drift"
    bad, drift = [], []
    for c in cells:
        # SURVIVORS_BOTH_ACCOUNTS and any --sleeve-set book are new here and have no
        # published counterpart to check.
        if c["variant"] not in pub["accounts"][c["account"]]["variants"]:
            continue
        p = pub["accounts"][c["account"]]["variants"][c["variant"]][c["key"]]
        checks = [("book_days", c["book_days"], p["book_days"])]
        if sizing_sealed:
            checks += [("eff_risk_pct", round(c["risk"] * 100, 3), p["eff_risk_pct"]),
                       ("vol_scale", round(c["vol_scale"], 4), p["vol_scale"]),
                       ("mean_r_per_book_day", round(c["mean_r_per_book_day"], 5),
                        p["mean_r_per_book_day"])]
        for name, mine, theirs in checks:
            if mine == theirs:
                continue
            row = (c["account"], c["variant"], c["key"], name, mine, theirs)
            if allow_cost_drift and name in _COST_DERIVED_COLUMNS:
                drift.append(row)
            else:
                bad.append(row)
    return bad, scope, drift


def contribution_shares(cells, kelly=KELLY_SEALED):
    """Per-sleeve share of each variant's total conf-weighted daily unit-R.

    `OD3_DOSSIER_SURVIVOR_BOOK.md` §5.1 -- the dominant doubt -- is a concentration
    claim: 46.9 % of the survivor book's edge sits on 194 in-sample trades in `crypto`
    and `sub_xvol_pullback`. That share is a property of the BOOK, so it moves when the
    composition moves, and BOTH-3 drops the one sleeve with 11 years of history. Compute
    it per variant rather than carrying B161's four-sleeve figure across.

    Basis: **Kelly columns, signed denominator** -- B161's own stated basis
    ("FTMO survivors, Kelly columns") and the route's convention at
    `INTEG_portfolio_build.py:385`. A negative sleeve therefore shows a negative share and
    the shares still sum to 100."""
    st = M.build([])
    rows = st["rows"]
    km = kelly_fn(kelly)
    out = {}
    for c in cells:
        keep, acct = set(c["sleeves"]), c["account"]
        cm = {k: statistics.median(v) for k, v in _priced_pool(rows, acct).items()}
        sub = [r for r in rows if r["sleeve"] in keep]
        nights = 0.0 if c["nights"] == 0.0 else (1.0 if c["nights"] == 1.0 else "max")
        for r in sub:
            n = M.SLEEVE_MAX_NIGHTS[r["sleeve"]] if nights == "max" else nights
            cost, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
            r["R_s"] = None if cost is None else r["R_gross"] - cost
        days, sleeves, Mx, _ = M.build_matrix_from(sub, "R_s")
        nact = [sum(1 for v in row if abs(v) > 1e-9) for row in Mx]
        Mk = [[v * km(nact[i]) for v in Mx[i]] for i in range(len(Mx))]
        idx = [i for i, d in enumerate(days)
               if (d.year >= 2025 or c["window"] != "forward_2025+")]
        tot = {s: sum(Mk[i][j] for i in idx) for j, s in enumerate(sleeves) if s in keep}
        T = sum(tot.values())
        A = sum(abs(v) for v in tot.values()) or 1.0
        # A signed denominator is the route's convention and is the right one while the
        # book has a clear positive total. It degenerates when winners and losers cancel:
        # the 11-sleeve book at worst carry nets to ~0, and shares computed against it run
        # to 379 % and -358 %, which is arithmetic, not information. A NEGATIVE total is
        # worse -- every positive sleeve then reads as a negative "share of the edge".
        # Publish a share only where the net is positive and at least half the gross.
        out[f"{acct}|{c['variant']}|{c['key']}"] = dict(
            shares=({s: round(100.0 * v / T, 2)
                     for s, v in sorted(tot.items(), key=lambda kv: -kv[1])}
                    if T >= 0.50 * A else None),
            signed_total=round(T, 3), abs_total=round(A, 3),
            degenerate=bool(T < 0.50 * A))
    return out


def rule_sets(acct):
    """The rule ladder for one account, ordered so each step isolates one change.

    Firm values are read from FIRM_RULES_V1.json at run time rather than transcribed,
    so a correction to the broker-truth layer propagates here without an edit."""
    fr = json.loads(FIRM_RULES.read_text())["firms"][acct]["rules"]
    t1 = fr["profit_target_pct"]["phase1"] / 100.0
    t2 = fr["profit_target_pct"]["phase2"] / 100.0
    dl = fr["max_daily_loss_pct"]["value"] / 100.0
    ml = fr["max_overall_loss_pct"]["value"] / 100.0
    mtd = fr["minimum_trading_days"]["value"]

    firm = dict(daily_limit=dl, daily_basis=DAILY_FIRM,
                maxdd_limit=ml, maxdd_basis=DD_FIRM)
    out = [
        Rules(label="L0_LEGACY_SEALED"),
        Rules(label="L1_TARGET_ONLY", targets=(t1,)),
        Rules(label="L2_DAILY_ONLY", daily_limit=dl, daily_basis=DAILY_FIRM),
        Rules(label="L3_MAXDD_ONLY", maxdd_limit=ml, maxdd_basis=DD_FIRM),
        Rules(label="L4_FIRM_TRUE_PH1", targets=(t1,), **firm),
        Rules(label="L5_FIRM_TRUE_PH1_TRAILING_DD", targets=(t1,),
              daily_limit=dl, daily_basis=DAILY_FIRM, maxdd_limit=ml,
              maxdd_basis=DD_LEGACY),
        Rules(label="L6_FIRM_TRUE_PH1_MINDAYS_LATCH", targets=(t1,),
              min_trading_days=mtd, min_days_model="latch", **firm),
        Rules(label="L7_FIRM_TRUE_PH1_MINDAYS_ATRISK", targets=(t1,),
              min_trading_days=mtd, min_days_model="at_risk", **firm),
        Rules(label="P1_PHASE2_ALONE", targets=(t2,), **firm),
        Rules(label="P2_BOTH_PHASES", targets=(t1, t2), **firm),
        Rules(label="P3_BOTH_PHASES_MINDAYS_LATCH", targets=(t1, t2),
              min_trading_days=mtd, min_days_model="latch", **firm),
        Rules(label="P4_BOTH_PHASES_TRAILING_DD", targets=(t1, t2),
              daily_limit=dl, daily_basis=DAILY_FIRM, maxdd_limit=ml,
              maxdd_basis=DD_LEGACY),
    ]
    return out, dict(target_ph1=t1, target_ph2=t2, daily_limit=dl,
                     maxdd_limit=ml, minimum_trading_days=mtd)


def daily_rule_headroom(cells):
    """Deterministic, not simulated: can the daily rule fire at all in this cell?

    The bootstrap only ever draws days that exist in `comb`, so the largest single-day
    loss any path can take is `min(comb) * risk` on a day-start equity of at most
    `1 + target`. If that is smaller than the 5% allowance, no path can breach under
    EITHER basis and the choice of denominator is provably decision-irrelevant here."""
    out = []
    for c in cells:
        worst_dp = c["worst_day_unit_r"] * c["risk"]
        # legacy breaches at dp <= -0.05; firm at eq*dp <= -0.05 with eq <= 1 + target.
        out.append(dict(
            account=c["account"], variant=c["variant"], key=c["key"],
            worst_day_pct_of_equity=round(100 * worst_dp, 4),
            legacy_can_fire=bool(worst_dp <= -0.05),
            firm_can_fire_at_eq_1p10=bool(1.10 * worst_dp <= -0.05),
            headroom_ratio_firm=round(abs(1.10 * worst_dp) / 0.05, 4)))
    return out


# ------------------------------------------------------------------------------------
# Report
# ------------------------------------------------------------------------------------
def _derived(cell, res):
    """Calendar restatement of an MC result, on the same basis as SURVIVOR_BOOK_V1."""
    md = res["med_days_pass"]
    return dict(
        median_book_days_to_pass=md,
        median_calendar_days_to_pass=(
            round(md * cell["weekday_sessions"] / cell["book_days"]) if md else None),
        monthly_pct_calendar=round(cell["mean_r_per_book_day"] * cell["risk"]
                                   * cell["book_days_per_calendar_month"] * 100, 3))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=200_000,
                    help="MC paths per cell (the sealed engine uses 20000)")
    ap.add_argument("--verify-paths", type=int, default=20_000,
                    help="paths used for the bit-identity proof against the sealed engine")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--shares-only", action="store_true",
                    help="recompute contribution_shares and merge into an existing --out, "
                         "without re-running the Monte Carlo")
    ap.add_argument("--sleeve-set", action="append", default=[], metavar="NAME=a,b,c",
                    help="measure an EXPLICITLY NAMED book, e.g. "
                         "--sleeve-set ARMED_4=metals_core,crypto,energy_agri,sub_xvol_pullback. "
                         "Repeatable. Appended after the three derived variants, so the "
                         "published grid keeps its shape when this is not passed.")
    ap.add_argument("--kelly", default=KELLY_SEALED,
                    choices=(KELLY_SEALED, KELLY_HALF, KELLY_NONE),
                    help="day-level conviction bins. Default is the sealed grid's full bins; "
                         "the live book runs the half bins (kelly_conservative: true)")
    ap.add_argument("--risk-basis", default=RISK_VOL_MATCHED,
                    choices=(RISK_VOL_MATCHED, RISK_LIVE_NOMINAL),
                    help="how the dial becomes a per-unit risk. Default is the sealed grid's "
                         "vol match to the reference book; the live path applies the nominal "
                         "directly (admission.py:1470)")
    ap.add_argument("--start-equity", type=float, default=1.0,
                    help="current equity in units of the INITIAL balance (FTMO 2026-07-29: "
                         "1.0787228). Limits stay anchored to the initial balance.")
    ap.add_argument("--allow-cost-artifact-drift", action="store_true",
                    help="turn mismatches on the three COST-DERIVED published columns into a "
                         "published `drift` block instead of a hard failure. `book_days` "
                         "stays a hard failure. Needed at HEAD because 8f6da5150 and "
                         "33d854189 extended BROKER_TRUE_COSTS_V1.json after Q sealed its "
                         "figures; see verify_series.")
    ap.add_argument("--start-days-served", type=int, default=0,
                    help="trading days already booked in the current phase; only matters "
                         "together with --start-equity and a min-trading-days rule set")
    a = ap.parse_args(argv)

    extra = collections.OrderedDict(parse_sleeve_set(s) for s in a.sleeve_set)
    sealed_shape = (not extra and a.kelly == KELLY_SEALED
                    and a.risk_basis == RISK_VOL_MATCHED
                    and a.start_equity == 1.0 and a.start_days_served == 0)

    print("building the grid cells ...", flush=True)
    cells, sd_book, survivors = build_cells(extra, kelly=a.kelly, risk_basis=a.risk_basis)

    if a.shares_only:
        # `--shares-only` merges into an EXISTING artifact, and its --out defaults to the
        # committed one. Under a non-sealed convention it would silently rewrite every
        # published share on a different basis, inject rows for an ad-hoc book, and write
        # no marker -- because the `sizing_convention` block lives further down a path this
        # branch returns before reaching. Found by Session V's arithmetic refuter.
        if not sealed_shape:
            raise SystemExit(
                "--shares-only refuses a non-sealed sizing convention: it merges into an "
                "existing artifact and cannot record that the basis changed. Re-run the "
                "full grid to a fresh --out instead.")
        p = Path(a.out)
        doc = json.loads(p.read_text())
        doc["contribution_shares"] = contribution_shares(cells, kelly=a.kelly)
        p.write_text(json.dumps(doc, indent=1, default=str))
        print(f"merged contribution_shares into {p}")
        return doc

    sizing_sealed = a.kelly == KELLY_SEALED and a.risk_basis == RISK_VOL_MATCHED
    print("control 1/2: series reconstruction vs the published artifact ...", flush=True)
    bad_series, series_scope, drift = verify_series(
        cells, sizing_sealed=sizing_sealed, allow_cost_drift=a.allow_cost_artifact_drift)
    print(f"   {len(cells)} cells, {len(bad_series)} column mismatches, "
          f"{len(drift)} tolerated cost drifts ({series_scope})", flush=True)

    print(f"control 2/2: bit-identity vs INTEG_portfolio_build_w2.mc_series "
          f"({a.verify_paths} paths x {len(cells)} cells) ...", flush=True)
    bad_ident = verify_bit_identity(cells, n_paths=a.verify_paths)
    print(f"   {len(bad_ident)} disagreements", flush=True)
    if bad_series or bad_ident:
        raise SystemExit(f"CONTROL FAILED  series={bad_series[:4]} identity={bad_ident[:4]}")

    out = dict(
        schema="gtos.w7_recost.mc_firm_true.v1",
        generated_by="scripts/mc_firm_rules.py",
        question=("Re-run the survivor-book challenge MC at each firm's MEASURED rules "
                  "instead of the sealed engine's single hardcoded rule set."),
        sealed_engine=dict(
            module="research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                   "INTEG_portfolio_build.py:298",
            constants="TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05; BLOCK = 5; N = 20000; "
                      "PATHCAP = 2000",
            unedited=True,
            reproducibility=("scripts/build_survivor_book.py still reproduces "
                             "SURVIVOR_BOOK_V1.json byte-identically")),
        firm_rules_source="research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json",
        dial_nominal_pct=DIAL * 100,
        n_paths=a.paths,
        sd_book_reference=round(sd_book, 5),
        survivor_sets=survivors,
        survivor_sets_note=(
            "The two accounts do not select the same book. FTMO keeps metals_core and drops "
            "vp_euidx_pocgrav; redacted_account does the reverse. Only 3 of 4 sleeves are common. "
            "Any 'SURVIVORS_ONLY' row is therefore an account-specific composition."),
        controls=dict(
            series_reconstruction_mismatches=len(bad_series),
            series_reconstruction_scope=series_scope,
            cost_artifact_drift_tolerated=len(drift),
            cost_artifact_drift_rows=drift[:60],
            cost_artifact_drift_cause=(
                "8f6da5150 and 33d854189 extended BROKER_TRUE_COSTS_V1.json after Session Q "
                "sealed these figures. FTMO carries 167 priced instruments to redacted_account's "
                "76, so crypto goes MEASURED 35 -> 72 and idxrev 4,939 -> 5,876 and only the "
                "FTMO half of the grid re-prices. `book_days` is unaffected and is still a "
                "hard control." if drift else None),
            bit_identity_disagreements=len(bad_ident),
            bit_identity_paths=a.verify_paths,
            bit_identity_cells=len(cells),
            meaning=("mc(Rules.LEGACY) equals INTEG_portfolio_build_w2.mc_series exactly on "
                     "every cell, so every difference below is caused by the rule change and "
                     "by nothing else.")),
        daily_rule_headroom=daily_rule_headroom(cells),
        contribution_shares=contribution_shares(cells, kelly=a.kelly),
        accounts={})

    # Only present when something non-sealed was asked for, so the default invocation
    # still writes the same document. `sealed_shape` and the `--shares-only` refusal are
    # both asserted by tests/test_armed_set_mc.py rather than trusted.
    if not sealed_shape:
        out["sizing_convention"] = dict(
            kelly=a.kelly, risk_basis=a.risk_basis,
            start_equity=a.start_equity, start_days_served=a.start_days_served,
            named_sleeve_sets={k: v for k, v in extra.items()},
            series_reconstruction_scope=series_scope,
            note=("The sealed grid is kelly=sealed_full_bins + "
                  "risk_basis=vol_matched_to_reference_book. The LIVE book runs "
                  "live_half_bins + live_nominal_per_unit "
                  "(admission.py:1470 and ultimate_book_kelly_conservative: true)."))

    def run(vals, risk, rules, seed_base=1):
        return mc(vals, risk, rules, a.paths, seed_base=seed_base,
                  start_equity=a.start_equity, start_days_served=a.start_days_served)

    for acct in ("FTMO", "redacted_account"):
        rs, firm = rule_sets(acct)
        out["accounts"][acct] = dict(
            firm_rules=firm,
            rule_sets={r.label: r.as_dict() for r in rs},
            variants=collections.defaultdict(dict))
        acc = out["accounts"][acct]
        for cell in [c for c in cells if c["account"] == acct]:
            res_by_rule = {}
            for r in rs:
                res = run(cell["comb"], cell["risk"], r)
                res_by_rule[r.label] = dict(
                    p_pass=round(res["p_pass"], 6),
                    se_p_pass=round(res["se_p_pass"], 6),
                    p_fail_dd=round(res["p_fail_dd"], 6),
                    p_fail_daily=round(res["p_fail_daily"], 6),
                    p_timeout=round(res["p_timeout"], 6),
                    **_derived(cell, res))
                print(f"   {acct:11s} {cell['variant']:22s} {cell['key']:16s} "
                      f"{r.label:32s} p_pass={res['p_pass']:.5f}", flush=True)

            # --- risk-dial sweep at the corrected rules --------------------------------
            # The commission fixes the dial at 2.0% because that is the live profile. The
            # OD-3 dossier's own option A is "canary at a reduced dial", and nothing in
            # the record prices that option, so price it here. `risk = dial * vol_scale`,
            # so a dial change is a pure rescale of the same series.
            #
            # SURVIVORS_ONLY only, deliberately. The 11-sleeve book at worst carry has a
            # daily mean of ~0.007 R (FTMO) and -0.055 R (redacted_account); shrink the dial on a
            # driftless or negative series and the barrier problem stops being drift-
            # dominated, so paths random-walk toward the 10,000-day PATHCAP instead of
            # terminating. The result would be dominated by p_timeout, which is an artifact
            # of PATHCAP rather than an answer, and it costs hours to produce. The dial
            # question is a survivor-book canary question anyway.
            dials = {}
            for lab in (("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES")
                        if cell["variant"].startswith("SURVIVORS") else ()):
                rr = [r for r in rs if r.label == lab][0]
                dials[lab] = {}
                for d in (0.005, 0.0075, 0.010, 0.015):
                    rk = cell["risk"] * d / DIAL
                    res = run(cell["comb"], rk, rr)
                    dials[lab][f"{d*100:.3f}%"] = dict(
                        eff_risk_pct=round(rk * 100, 4),
                        p_pass=round(res["p_pass"], 6),
                        p_fail_dd=round(res["p_fail_dd"], 6),
                        p_fail_daily=round(res["p_fail_daily"], 6),
                        p_timeout=round(res["p_timeout"], 6),
                        median_book_days_to_pass=res["med_days_pass"],
                        median_calendar_days_to_pass=(
                            round(res["med_days_pass"] * cell["weekday_sessions"]
                                  / cell["book_days"]) if res["med_days_pass"] else None),
                        monthly_pct_calendar=round(
                            cell["mean_r_per_book_day"] * rk
                            * cell["book_days_per_calendar_month"] * 100, 3))
                dials[lab][f"{DIAL*100:.3f}%"] = dict(
                    eff_risk_pct=round(cell["risk"] * 100, 4),
                    **{k: v for k, v in res_by_rule[lab].items()
                       if k in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout",
                                "median_book_days_to_pass", "median_calendar_days_to_pass",
                                "monthly_pct_calendar")})

            # --- null controls, on the same cell, same seeds, same risk ---
            demeaned = [v - cell["mean_r_per_book_day"] for v in cell["comb"]]
            firm_ph1 = [r for r in rs if r.label == "L4_FIRM_TRUE_PH1"][0]
            nulls = dict(
                zero_drift_firm_true=round(
                    run(demeaned, cell["risk"], firm_ph1)["p_pass"], 6),
                zero_drift_legacy=round(
                    run(demeaned, cell["risk"], Rules.LEGACY)["p_pass"], 6),
                seed_noise_legacy=[round(run(cell["comb"], cell["risk"], Rules.LEGACY,
                                            seed_base=sb)["p_pass"], 6)
                                   for sb in (1, 2, 3)])
            nulls["seed_noise_spread"] = round(max(nulls["seed_noise_legacy"])
                                               - min(nulls["seed_noise_legacy"]), 6)

            acc["variants"][cell["variant"]][cell["key"]] = dict(
                window=cell["window"], nights=cell["nights"], sleeves=cell["sleeves"],
                book_days=cell["book_days"], weekday_sessions=cell["weekday_sessions"],
                book_days_per_calendar_month=round(cell["book_days_per_calendar_month"], 2),
                mean_r_per_book_day=round(cell["mean_r_per_book_day"], 5),
                worst_day_unit_r=round(cell["worst_day_unit_r"], 5),
                vol_scale=round(cell["vol_scale"], 4),
                eff_risk_pct=round(cell["risk"] * 100, 3),
                rules=res_by_rule, dial_sweep=dials, null_controls=nulls)
        acc["variants"] = dict(acc["variants"])

    p = Path(a.out)
    p.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {p}")
    return out


if __name__ == "__main__":
    main()

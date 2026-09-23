#!/usr/bin/env python3
"""Build ``LIVE_EVIDENCE_CALIBRATION_V1.json`` -- the measured null the live gate tests against.

Why this artifact exists
------------------------
`learning_actuator.recommend()` had to answer a question it could not answer from a constant:
**how many live fills before live evidence is allowed to move a sleeve's weight?** A single
`MIN_N`-style number is wrong in both directions. At the measured generation rates
(`phase3/receipts/G4_GENERATION_RATE.json`) 30 live fills for `crypto` is years away, so a
symmetric bar makes live evidence permanently inert; and a small bar applied upward would let
three lucky fills size a sleeve up.

So the standard is asymmetric and *per sleeve*, and the boundary is measured rather than chosen:

    H0 -- "this sleeve is still behaving as its cost-true validation says"

Under H0 the next `n` live R-multiples are draws from the sleeve's own validated per-trade R
distribution, relocated to the broker-true claim mean. The gate fires when cumulative live R
crosses a sequential boundary ``b_n = n*claim - c*sd*sqrt(n)``, and `c` is solved so that the
probability a **healthy** sleeve ever crosses within its first `n_max` live trades equals a stated
budget. Two budgets give the two-step escalation: `familywise_down` -> soft down-weight,
`familywise_kill` -> gate. Nothing else about the rule is tunable.

Two earlier drafts of this file were wrong, and both failures are worth keeping visible
----------------------------------------------------------------------------------------
1. **Per-n ``np.quantile``.** Per-trade R has a large point mass at the stop (measured at
   **35.9%-71.4%** of trades across the 11 survivor sleeves),
   and a quantile at small n lands *inside* that atom -- so a single routine losing trade read as
   a 1-in-200 event. The artifact reported ``stop_outs_to_gate = 1`` for 9 of 11 sleeves: the rule
   would have gated the whole armed book on its first loser.
2. **Per-n error rates at all.** Even corrected for the atom, a per-n alpha is not the error rate
   the system experiences, because the rule is re-evaluated after *every* fill. What is controlled
   now is first passage over the whole sequence.

Shape and location come from different places, deliberately
-----------------------------------------------------------
* **Shape** is the empirical per-trade R record in the W3/W5 stream caches -- the same rows whose
  means Session N re-costed (verified here: the cache mean reproduces
  `SURVIVOR_BOOK_V1.json:cached_net_r` for every sleeve). Resampling the real distribution avoids
  a normal approximation that is badly wrong at small n.
* **Location** is the broker-true net R from `SURVIVOR_BOOK_V1.json`, per account, at the carry
  basis that decided the sleeve's tier (``net_r.n_horizon_mean``). Using the cached mean would
  re-import the legacy cost map F39 corrected.

Both accounts get their own claim, because the same sleeve has different broker-true economics on
FTMO and redacted_account (Session Q measured that the survivor sets differ). The boundary WIDTH `c` is
provably invariant to the location shift, so it is identical across accounts by construction -- an
earlier version threaded one RNG through every cell and published the resulting Monte-Carlo noise
(metals_core 2.805 vs 2.789) as if it were measured per-account structure.

Two directional caveats, both corrected after refutation
--------------------------------------------------------
* **The location choice is pessimistic, and it costs detection power.** An earlier version of this
  docstring said the null's inherited selection bias was "the safe direction: an optimistic claim
  makes a shortfall easier to detect, so the gate fires sooner". That is backwards as a statement
  about this artifact. Every `relocation_shift_r` here is NEGATIVE, the boundary drops 1:1 with the
  claim, and the gate therefore fires **later**. `n_horizon_mean` costs 29-76 points of gate power
  against a genuinely dead sleeve versus `n0`. See `power_if_edge_gone`.
* **The claim basis cancels out of the legibility columns.** Because `cum_shifted = cum + shift*n`
  and `mu = cached_mean + shift`, the shift cancels in the crossing condition -- so `c_down`,
  `c_kill` and the `stop_outs_*` figures are invariant to `--claim-key`. It moves the runtime
  `thresholds_*_r` (which are compared against unshifted realized live R) and nothing else.

SESSION AE, 2026-07-30 (B863-B872). TWO CHANGES, ONE OF THEM A DEFECT IN THE V1 ARTIFACT.
-----------------------------------------------------------------------------------------
**1. "Family-wise" was per sleeve per account, which is not a family.** R published this as a
stated limitation (its section 4 item 14): with a 0.20 budget per cell and 11 sleeves x 2 accounts
calibrated, the probability that *at least one healthy sleeve in the book* is spuriously
down-weighted in its first `n_max` fills is bounded by 22 x 0.20, and across the three armed
sleeves alone it is ~0.75. The budget the owner reads and the error the system delivers were
different numbers. `--family-scope` now sets which they are: `book` (default) divides the budget
across every calibrated cell by Bonferroni, so the stated figure is the book-level one; `account`
corrects within an account; `cell` reproduces V1 exactly. All three are solved from the same
simulated paths and published side by side in `familywise_sensitivity`, **with the power cost**,
because the correction buys honesty by making an already weak detector weaker and that trade is the
owner's to make, not this file's.

Bonferroni rather than Sidak deliberately: the sleeves are correlated (they trade overlapping
symbols on overlapping days), Sidak's exactness assumes independence, and the union bound holds
whatever the dependence structure is.

**2. THE V1 ARTIFACT IS NOT REPRODUCIBLE FROM THIS SCRIPT, AND ONE OF R's PUBLISHED CLAIMS IS
FALSE.** [MEASURED] The per-cell seed was `abs(hash((SEED, account, sleeve)))`, and CPython
randomises `str.__hash__` per process unless `PYTHONHASHSEED` is set -- three runs here produced
336168621, 1028826546 and 3564764250 for the same cell. So every re-run of the builder draws
different Monte-Carlo paths and lands on different boundaries. On top of that, seeding per
*(account, sleeve)* gives the two accounts of one sleeve independent noise, so R's section 4 item 11
("the two accounts now agree exactly, which is the truthful result") does not hold in the file it
shipped: of the 11 calibrated sleeves, **1** has both `c_down` and `c_kill` identical across
accounts (crypto 2.246469 vs 2.248893; metals_softband kill 3.478433 vs 3.457709).

The fix is R's own argument taken one step further. `c` is provably invariant to the location
shift, so the two accounts' cells for one sleeve are *the same computation* and must share one
stream: the seed is now `blake2b(f"{SEED}|{sleeve}")`, per SLEEVE, deterministic across processes.
The two accounts then agree exactly by construction rather than approximately by luck, the artifact
regenerates byte-identically, and each sleeve is simulated once instead of twice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import statistics as st
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
W3 = REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/INTEG_W3_streams_cache.pkl"
W5 = REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/INTEG_W5_new_streams_cache.pkl"
SURVIVOR = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
# V2 lives under docs/ because research/operations/ is sparse-checkout-excluded: an artifact there
# can be committed, absent from a working tree and leave `git status` clean. V1 is left where R put
# it, untouched -- it is the evidence behind R's published table and superseding is not deleting.
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/LIVE_EVIDENCE_CALIBRATION_V2.json"

# False-alarm budgets: the probability that a sleeve which is STILL HEALTHY trips the boundary at
# some point in its first N_MAX live trades. Asymmetric on purpose. Down-weighting is reversible and
# costs forgone profit; gating is the strong action.
#
# WHAT THESE NUMBERS NOW MEAN, AND IT CHANGED IN AE. They are BOOK-LEVEL under the default
# `--family-scope book`: the probability that *at least one* healthy sleeve anywhere in the
# re-rated book is spuriously actioned. Under `--family-scope cell` they revert to R's per-cell
# reading. The distinction is not cosmetic -- at 22 calibrated cells the same 0.20 means either
# "one healthy sleeve in five books" or "a near-certainty in every book".
FAMILYWISE_DOWN = 0.20
FAMILYWISE_KILL = 0.02
FAMILY_SCOPES = ("book", "armed", "account", "cell")
DEFAULT_FAMILY_SCOPE = "armed"
N_MAX = 60
DRAWS = 100_000
SEED = 20260729
# WHICH CARRY BASIS THE CLAIM IS READ AT. This is the single most consequential constant in the
# file and it is an OWNER decision, not a measurement -- CLAUDE.md section 4 states the carry band is
# precisely OD-3's open question (one night of carry -> P(pass) 0.951 and 1.97 %/month; held to the
# structural horizon -> 0.450 and 0.13 %/month), and no exit index survives in any cache.
#
# `n_horizon_mean` charges 13.369 nights and is the basis the survivor book's TIERS were decided at,
# so it is the default for consistency with them. It is also the pessimistic end, and it is in
# tension with this session's own producer, which measures a median live hold of 1.262 h -- roughly
# n0 territory. That tension is not resolvable from the record and must not be resolved silently:
# `carry_sensitivity` below publishes every basis so the reader sees what the choice costs. At n0
# three sleeves the horizon basis calls negative are positive (metals_softband +0.334,
# vp_euidx_pocgrav +0.272, sub_mid_dn_revert +0.271).
CLAIM_KEY = "n_horizon_mean"
CARRY_BASES = ("n0", "n1", "n2", "n3", "n_horizon_mean", "n_max")
STOP_CLUSTER_MAX_R = -0.9  # rows at or below this are the stop-out atom (measured, not assumed)
# A real full stop-out, measured on the live record by this session's own producer (two occurrences,
# -1.0078 R and -1.0038 R). Used for the legibility columns because a stop-out is a mechanical -1 R
# event plus costs: it does NOT scale with the sleeve's mean re-costing. See `stop_outs_*_measured`.
MEASURED_FULL_STOP_OUT_R = -1.01


def load_validated_streams() -> tuple[dict, dict]:
    """Per-sleeve validated per-trade R (cached net, legacy-cost basis), flat and grouped by day.

    The day grouping is what makes the null honest. Trades are **not** iid: `sub_xvol_pullback`'s 90
    trades sit on 33 dates with up to 12 on one day and lag-1 autocorrelation 0.511; `crypto` 104 on
    67 dates, rho 0.441. Resampling individual trades therefore understates the dispersion of a
    cumulative path, and a boundary solved against that null delivers a far looser error budget than
    it advertises -- measured by a refuter at **2.1x to 7.7x** the stated rate (crypto kill 0.0956
    against a stated 0.020). Resampling whole DAYS preserves the same-day clustering.
    """
    rows: dict = {}
    for path in (W3, W5):
        if not path.is_file():
            raise SystemExit(
                f"missing validated stream cache {path}. It is the shape of the null; there is no "
                "substitute for it and inventing a distribution here would be the F38 failure mode."
            )
        with open(path, "rb") as fh:
            rows.update(pickle.load(fh))
    flat, by_day = {}, {}
    for k, v in rows.items():
        if not v:
            continue
        flat[k] = [float(r["R"]) for r in v]
        days: dict = {}
        for r in v:
            days.setdefault(str(r.get("date")), []).append(float(r["R"]))
        by_day[k] = list(days.values())
    return flat, by_day


def _crossing_rate(cum: np.ndarray, boundary: np.ndarray) -> float:
    """Share of simulated H0 paths that touch the boundary at any n <= N_MAX (first passage)."""
    return float((cum <= boundary).any(axis=1).mean())


def _solve_c(cum: np.ndarray, mu: float, sd: float, target: float) -> tuple[float, float]:
    """Smallest boundary width `c` whose FAMILY-WISE crossing rate is <= target.

    The boundary is ``b_n = n*mu - c*sd*sqrt(n)`` -- the natural sequential shape, since the
    cumulative sum's dispersion under H0 grows as sqrt(n).

    Why family-wise rather than a per-n quantile. The rule is re-evaluated after **every** live
    fill, so a per-n alpha is not the error rate the system experiences: it is one test out of
    N_MAX, and the probability that *some* n trips is far larger than alpha. Calibrating the
    first-passage probability makes the tunable the quantity an owner can actually reason about --
    "how often are we willing to spuriously down-weight a healthy sleeve over its first 60 live
    trades" -- instead of a per-test number that silently compounds.

    It also removes the n=1 pathology for free. Per-n quantiles put the alpha-point inside the
    point mass at the stop, so a single routine losing trade read as a 1-in-200 event; a sqrt(n)
    boundary at c ~ 2-3 sits far below any single-trade outcome, so the gate simply cannot fire on
    one trade.
    """
    n = np.arange(1, cum.shape[1] + 1, dtype=float)
    lo, hi = 0.0, 12.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _crossing_rate(cum, mu * n - mid * sd * np.sqrt(n)) <= target:
            hi = mid
        else:
            lo = mid
    return hi, _crossing_rate(cum, mu * n - hi * sd * np.sqrt(n))


def _day_block_paths(days: list[list[float]], shift: float, rng: np.random.Generator) -> np.ndarray:
    """DRAWS x N_MAX cumulative paths built by resampling whole trading days, then truncating."""
    lens = np.array([len(d) for d in days], dtype=int)
    flat = np.concatenate([np.asarray(d, dtype=float) + shift for d in days])
    starts = np.concatenate([[0], np.cumsum(lens)[:-1]])
    # Draw enough day-blocks that the shortest possible run still reaches N_MAX trades.
    n_blocks = int(np.ceil(N_MAX / max(1, lens.min()))) + 2
    pick = rng.integers(0, len(days), size=(DRAWS, n_blocks))
    out = np.empty((DRAWS, N_MAX), dtype=float)
    for i in range(DRAWS):
        buf: list[float] = []
        for b in pick[i]:
            s, ln = starts[b], lens[b]
            buf.extend(flat[s:s + ln])
            if len(buf) >= N_MAX:
                break
        while len(buf) < N_MAX:                     # degenerate: all blocks tiny
            b = int(rng.integers(0, len(days)))
            buf.extend(flat[starts[b]:starts[b] + lens[b]])
        out[i] = buf[:N_MAX]
    return np.cumsum(out, axis=1)


def sleeve_seed(sleeve: str) -> int:
    """Deterministic per-SLEEVE RNG seed.

    Per sleeve, not per (account, sleeve): `c` is provably invariant to the location shift, so the
    two accounts' cells for one sleeve are the same computation and sharing a stream makes them
    agree exactly instead of differing by Monte-Carlo noise. And `blake2b` rather than `hash()`,
    which CPython randomises per process -- V1's seeds, and therefore V1's boundaries, could not be
    regenerated from V1's own generator. Both measured; see the module docstring.
    """
    h = hashlib.blake2b(f"{SEED}|{sleeve}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big") % (2 ** 32)


def simulate(sample: list[float], days: list[list[float]], rng: np.random.Generator) -> dict:
    """The expensive half, done once per sleeve: H0 and H1 cumulative-R path ensembles.

    Both are built at shift 0. The crossing condition is shift-invariant --
    ``cum + shift*n <= (cached_mean + shift)*n - c*sd*sqrt(n)`` reduces to
    ``cum <= cached_mean*n - c*sd*sqrt(n)`` -- so one ensemble serves every account and every carry
    basis, and only the published `thresholds_*_r` move with the claim.
    """
    arr = np.asarray(sample, dtype=float)
    mean0 = float(arr.mean())
    return {
        "sd": float(np.std(arr)),
        "cached_mean": mean0,
        "cum_dep": _day_block_paths(days, 0.0, rng),                      # H0: still healthy
        "cum_iid": np.cumsum(rng.choice(arr, size=(DRAWS, N_MAX), replace=True), axis=1),
        "dead": _day_block_paths([[x - mean0 for x in d] for d in days], 0.0, rng),  # H1: edge gone
    }


def calibrate(sim: dict, mu: float, shift: float, targets: dict) -> dict:
    """Boundaries for cumulative live R at each named error budget, calibrated on first passage.

    Solved against a **day-block** null (see `load_validated_streams`) so the stated error budget is
    the one actually delivered. The iid version of this understated the crossing rate by 2.1x-7.7x.
    The iid rate is still reported alongside, as `attained_familywise_*_iid`, so the size of the
    dependence correction is visible rather than buried.

    `targets` maps a scope label to `(down_budget, kill_budget)`. Solving several from one ensemble
    costs a bisection each and nothing else, which is what makes the family-wise sensitivity table
    free: the simulation, not the solve, is the expensive part.
    """
    sd = sim["sd"]
    n = np.arange(1, N_MAX + 1, dtype=float)
    # Solve in the unshifted frame (shift-invariant), publish thresholds in the claim frame.
    mu0 = sim["cached_mean"]
    out: dict = {}
    for label, (t_down, t_kill) in targets.items():
        c_down, rate_down = _solve_c(sim["cum_dep"], mu0, sd, t_down)
        c_kill, rate_kill = _solve_c(sim["cum_dep"], mu0, sd, t_kill)
        b_down0 = mu0 * n - c_down * sd * np.sqrt(n)
        b_kill0 = mu0 * n - c_kill * sd * np.sqrt(n)
        b_down = mu * n - c_down * sd * np.sqrt(n)
        b_kill = mu * n - c_kill * sd * np.sqrt(n)

        # POWER: if the edge is entirely gone (mean 0, same shape and clustering), how often and how
        # soon does the boundary fire? Calibration controls false alarms; without this the artifact
        # says nothing about whether it would ever catch a dead sleeve — and the family-wise
        # correction is paid for entirely out of this column.
        def _power(b):
            # `sim["dead"]` is mean-zero RAW R, which is what "the edge is entirely gone" means in
            # the same units the live record is measured in; the boundary is in the claim frame.
            hit = sim["dead"] <= b
            ever = hit.any(axis=1)
            first = np.where(ever, hit.argmax(axis=1) + 1, 0)
            return (round(float(ever.mean()), 4),
                    int(np.median(first[ever])) if ever.any() else None)
        p_down, med_down = _power(b_down)
        p_kill, med_kill = _power(b_kill)

        out[label] = {
            "budget_down": round(t_down, 8),
            "budget_kill": round(t_kill, 8),
            "c_down": round(c_down, 6),
            "c_kill": round(c_kill, 6),
            "attained_percell_down": round(rate_down, 6),
            "attained_percell_kill": round(rate_kill, 6),
            "attained_percell_down_iid": round(_crossing_rate(sim["cum_iid"], b_down0), 6),
            "attained_percell_kill_iid": round(_crossing_rate(sim["cum_iid"], b_kill0), 6),
            "power_if_edge_gone": {
                "p_down_weight_within_n_max": p_down, "median_n_to_down_weight": med_down,
                "p_gate_within_n_max": p_kill, "median_n_to_gate": med_kill,
                "note": "H1 = the sleeve's edge is entirely gone (mean 0, shape and day-clustering "
                        "unchanged). A low p_gate means a dead sleeve is likely never gated within "
                        "n_max fills — a limitation of the standard, published rather than hidden.",
            },
            "down": {str(i + 1): round(float(b_down[i]), 6) for i in range(N_MAX)},
            "kill": {str(i + 1): round(float(b_kill[i]), 6) for i in range(N_MAX)},
        }
    return out


def first_n_tripped(thresholds: dict, per_trade_r: float) -> int | None:
    """Smallest n at which a run of n trades each returning `per_trade_r` trips the threshold.

    Reported so the standard is legible without reading the artifact: "this sleeve down-weights
    after N consecutive full stop-outs". A missing key means no threshold is attainable at that n
    (the atom exceeds alpha), so the gate cannot fire there and the run continues.
    """
    for n in range(1, N_MAX + 1):
        t = thresholds.get(str(n))
        if t is not None and per_trade_r * n <= t:
            return n
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--claim-key", default=CLAIM_KEY, choices=list(CARRY_BASES),
        help=(
            "carry basis the sleeve's claim is read at (default %(default)s). This is an OWNER "
            "decision, not a measurement -- see the CLAIM_KEY comment. At n0 three sleeves the "
            "default calls negative are positive."
        ),
    )
    ap.add_argument(
        "--family-scope", default=DEFAULT_FAMILY_SCOPE, choices=list(FAMILY_SCOPES),
        help=(
            "what the stated false-alarm budget is a budget FOR (default %(default)s). `book`: at "
            "least one healthy sleeve anywhere in the re-rated book, Bonferroni-corrected across "
            "every calibrated cell. `account`: within one account. `cell`: per sleeve per account, "
            "which is what V1 shipped and what R section 4 item 14 flagged as not a family at all. All "
            "three are published in `familywise_sensitivity` whichever is chosen."
        ),
    )
    args = ap.parse_args()
    claim_key = args.claim_key
    scope = args.family_scope

    streams, streams_by_day = load_validated_streams()
    survivor = json.loads(SURVIVOR.read_text())

    # PASS 1 — how big is the family? A Bonferroni divisor cannot be chosen after seeing which
    # cells survive the solve, so the calibratable set is enumerated first, from the two conditions
    # that decide it: a validated stream (shape) and a claim at this carry basis (location).
    cells: list[tuple[str, str]] = []
    armed_cells: list[tuple[str, str]] = []
    for account, abook in survivor["accounts"].items():
        survivors = set(abook.get("survivors") or [])
        for sleeve, rec in abook["sleeves"].items():
            if streams.get(sleeve) and rec.get("net_r", {}).get(claim_key) is not None:
                cells.append((account, sleeve))
                if sleeve in survivors:
                    armed_cells.append((account, sleeve))
    k_book = len(cells)
    k_armed = max(1, len(armed_cells))
    k_account = {a: sum(1 for acc, _ in cells if acc == a) for a in survivor["accounts"]}

    def _k(name: str, account: str) -> int:
        return {"book": k_book, "armed": k_armed,
                "account": max(1, k_account.get(account, 1)), "cell": 1}[name]

    def _divisor(account: str) -> int:
        return _k(scope, account)

    doc: dict = {
        "schema": "gtos.learning_lane.live_evidence_calibration.v2",
        "generated_by": "scripts/build_live_evidence_calibration.py",
        "supersedes": "research/operations/learning_lane_2026_07_29/LIVE_EVIDENCE_CALIBRATION_V1.json",
        "familywise_down": FAMILYWISE_DOWN,
        "familywise_kill": FAMILYWISE_KILL,
        "familywise_scope": scope,
        "familywise_correction": {
            "method": "bonferroni",
            "why_not_sidak": (
                "Sidak is exact under independence and these sleeves are not independent -- they "
                "trade overlapping symbols on overlapping days. The union bound holds whatever the "
                "dependence structure is, and being conservative about a FALSE ALARM budget is the "
                "cheap direction: it costs detection power, which is published beside it."
            ),
            "family_size_book": k_book,
            "family_size_armed": k_armed,
            "family_size_by_account": k_account,
            "armed_cells": [f"{a}/{s}" for a, s in armed_cells],
            "per_cell_budget_down": FAMILYWISE_DOWN / _divisor(cells[0][0] if cells else ""),
            "per_cell_budget_kill": FAMILYWISE_KILL / _divisor(cells[0][0] if cells else ""),
            "why_armed_is_the_default": (
                "A multiplicity bill is owed on the tests whose OUTCOME CAN CHANGE SOMETHING. The "
                "lane re-rates every calibrated cell, but only a sleeve in an account's survivor "
                "set can have its weight moved, so correcting across all "
                f"{k_book} cells charges for {k_book - k_armed} decisions nobody can take. "
                f"`armed` corrects across the {k_armed} survivor cells; `book` is available and is "
                "the conservative end. The difference is not academic -- at `book` the "
                "down-weight brake on the armed four needs 11-24 consecutive stop-outs against "
                "4-9 at `cell`, and P(gating a genuinely dead armed sleeve within 60 fills) falls "
                "to 0.03-0.45. Both are published per cell in `familywise_sensitivity`; the choice "
                "is the owner's and it is queued for him."
            ),
            "what_v1_delivered": (
                f"V1 solved every cell at the full {FAMILYWISE_DOWN}/{FAMILYWISE_KILL}, so with "
                f"{k_book} calibrated cells the book-level down-weight false-alarm rate was bounded "
                f"by {round(min(1.0, k_book * FAMILYWISE_DOWN), 3)} rather than {FAMILYWISE_DOWN} "
                "(R section 4 item 14, published there as a stated limitation)."
            ),
        },
        "n_max": N_MAX,
        "null_hypothesis": (
            "the sleeve is still behaving as its cost-true validation says: the next n live "
            "R-multiples are iid draws from its validated per-trade R distribution, relocated to "
            "the broker-true claim mean"
        ),
        "bootstrap": {
            "draws": DRAWS,
            "seed": SEED,
            "method": "iid resample with replacement; cumulative sums nested across n",
            "why_not_normal": (
                "R is hard-floored near -1 and right-skewed with a large point mass at the stop; a "
                "normal approximation is materially wrong at the small n where the gate fires"
            ),
            "error_rate_basis": (
                "FIRST PASSAGE, not per-n. The rule is re-evaluated after every fill, so the "
                "quantity controlled is P(a healthy sleeve trips the boundary at ANY n <= n_max)."
            ),
        },
        "shape_source": {
            "paths": [str(W3.relative_to(REPO)), str(W5.relative_to(REPO))],
            "field": "R (cached net, legacy cost map basis)",
            "note": "shape only -- location is replaced by the broker-true claim below",
        },
        "claim_key": claim_key,
        "location_source": {
            "path": str(SURVIVOR.relative_to(REPO)),
            "field": f"accounts.<account>.sleeves.<sleeve>.net_r.{claim_key}",
            "why": (
                "the carry basis that decided the sleeve's survivor tier; using the cached mean "
                "would re-import the legacy cost map that F39 corrected"
            ),
        },
        "known_bias": (
            "the null inherits the validation's own in-sample selection bias. That is the safe "
            "direction for a downward gate -- an optimistic claim makes a shortfall easier to "
            "detect, so the gate fires sooner, not later. Stated, not corrected."
        ),
        "accounts": {},
    }

    sims: dict = {}
    for account, abook in survivor["accounts"].items():
        out_sleeves: dict = {}
        for sleeve, rec in abook["sleeves"].items():
            sample = streams.get(sleeve)
            if not sample:
                out_sleeves[sleeve] = {
                    "calibrated": False,
                    "reason": (
                        f"no validated per-trade R stream for {sleeve!r} in the W3/W5 caches; the "
                        "live gate cannot fire for it and must report UNCALIBRATED rather than "
                        "assume a distribution"
                    ),
                }
                continue
            claim = rec.get("net_r", {}).get(claim_key)
            if claim is None:
                out_sleeves[sleeve] = {
                    "calibrated": False,
                    "reason": f"survivor book has no net_r.{claim_key} for {sleeve!r} on {account}",
                }
                continue
            cached_mean = st.mean(sample)
            # The docstring claims the cache reproduces the survivor book's cached_net_r. A
            # refuter pointed out it was a claim, not a check -- swap either input and shape
            # and location would silently come from different books. Now it is a check.
            book_cached = rec.get('cached_net_r')
            if book_cached is not None and abs(cached_mean - float(book_cached)) > 1e-4:
                raise SystemExit(
                    f'{account}/{sleeve}: stream-cache mean {cached_mean:.6f} does not match '
                    f'SURVIVOR_BOOK cached_net_r {book_cached:.6f}. Shape and location would '
                    'come from different books; refusing to build.')
            shift = float(claim) - cached_mean
            # Simulated ONCE per sleeve and reused across accounts, on a deterministic per-sleeve
            # seed. See `sleeve_seed`: V1 used `hash()`, which CPython randomises per process, and
            # seeded per (account, sleeve), which gave the same sleeve's two accounts independent
            # noise. Both are why V1's FTMO/redacted_account `c` values differ on 10 of 11 sleeves while
            # its own R section 4 item 11 says they "now agree exactly".
            if sleeve not in sims:
                sims[sleeve] = simulate(sample, streams_by_day[sleeve],
                                        np.random.default_rng(sleeve_seed(sleeve)))
            div = _divisor(account)
            targets = {name: (FAMILYWISE_DOWN / _k(name, account),
                              FAMILYWISE_KILL / _k(name, account))
                       for name in FAMILY_SCOPES}
            solved = calibrate(sims[sleeve], float(claim), shift, targets)
            th = solved[scope]
            # A "full stop-out" is the stop-out ATOM's typical value, not the empirical minimum.
            # The minimum is one observation with probability 1/n_validated and using it made the
            # legibility figures fire a trade too early.
            cluster = [x for x in sample if x <= STOP_CLUSTER_MAX_R]
            stop_out_r = (st.median(cluster) if cluster else min(sample)) + shift

            def _legibility(entry: dict) -> dict:
                return {
                    "c_down": entry["c_down"], "c_kill": entry["c_kill"],
                    "budget_down": entry["budget_down"], "budget_kill": entry["budget_kill"],
                    "attained_percell_down": entry["attained_percell_down"],
                    "attained_percell_kill": entry["attained_percell_kill"],
                    "stop_outs_to_down_weight_measured":
                        first_n_tripped(entry["down"], MEASURED_FULL_STOP_OUT_R),
                    "stop_outs_to_gate_measured":
                        first_n_tripped(entry["kill"], MEASURED_FULL_STOP_OUT_R),
                    "power_if_edge_gone": entry["power_if_edge_gone"],
                }

            out_sleeves[sleeve] = {
                "calibrated": True,
                "validated_n": len(sample),
                "cached_mean_r": round(cached_mean, 6),
                "claim_mean_r": round(float(claim), 6),
                "relocation_shift_r": round(shift, 6),
                "sd_r": round(st.pstdev(sample), 6),
                "winrate_validated": round(sum(1 for x in sample if x > 0) / len(sample), 4),
                "stop_cluster_n": len(cluster),
                "full_stop_out_r": round(stop_out_r, 6),
                "survivor_tier": rec.get("survivor_tier"),
                "boundary_form": "b_n = n*claim_mean_r - c*sd_relocated*sqrt(n)",
                "familywise_scope": scope,
                "familywise_divisor": div,
                "budget_down_per_cell": round(th["budget_down"], 8),
                "budget_kill_per_cell": round(th["budget_kill"], 8),
                "c_down": th["c_down"],
                "c_kill": th["c_kill"],
                # Renamed from `attained_familywise_*` in V1: the quantity is the PER-CELL first
                # passage rate, and calling it family-wise is what made the limitation invisible.
                "attained_percell_down": th["attained_percell_down"],
                "attained_percell_kill": th["attained_percell_kill"],
                "attained_percell_down_iid": th["attained_percell_down_iid"],
                "attained_percell_kill_iid": th["attained_percell_kill_iid"],
                "power_if_edge_gone": th["power_if_edge_gone"],
                "familywise_sensitivity": {k: _legibility(v) for k, v in solved.items()},
                "thresholds_down_r": th["down"],
                "thresholds_kill_r": th["kill"],
                "stop_outs_to_down_weight": first_n_tripped(th["down"], stop_out_r),
                "stop_outs_to_gate": first_n_tripped(th["kill"], stop_out_r),
                "measured_full_stop_out_r": MEASURED_FULL_STOP_OUT_R,
                "stop_outs_to_down_weight_measured":
                    first_n_tripped(th["down"], MEASURED_FULL_STOP_OUT_R),
                "stop_outs_to_gate_measured":
                    first_n_tripped(th["kill"], MEASURED_FULL_STOP_OUT_R),
                "stop_out_basis_note": (
                    "the relocated figure charges the stop-out horizon-mean carry, which a fast stop-out does not pay; the _measured pair uses a real live stop-out and is the honest one"),
                "carry_sensitivity": {k: rec.get("net_r", {}).get(k) for k in CARRY_BASES},
            }
        doc["accounts"][account] = out_sleeves

    # The union bound, MEASURED rather than asserted: the book-level false-alarm rate is at most the
    # sum of the attained per-cell rates, whatever the dependence between sleeves.
    cal_rows = [r for sl in doc["accounts"].values() for r in sl.values() if r.get("calibrated")]
    armed_names = {f"{a}/{s}" for a, s in armed_cells}
    armed_rows = [r for a, sl in doc["accounts"].items() for s, r in sl.items()
                  if r.get("calibrated") and f"{a}/{s}" in armed_names]

    def _bound(rows):
        return {
            "down": round(min(1.0, sum(r["attained_percell_down"] for r in rows)), 6),
            "kill": round(min(1.0, sum(r["attained_percell_kill"] for r in rows)), 6),
            "n_cells": len(rows),
        }

    doc["attained_familywise_upper_bound"] = {
        "basis": "sum of the attained per-cell first-passage rates (Bonferroni union bound); holds "
                 "whatever the dependence between sleeves",
        "over_all_calibrated_cells": _bound(cal_rows),
        "over_armed_cells_only": _bound(armed_rows),
        "read_this_as": (
            f"at scope {scope!r} the stated {FAMILYWISE_DOWN}/{FAMILYWISE_KILL} budgets are "
            "delivered over the family named by that scope, and the OTHER row above shows what the "
            "same calibration delivers over the wider or narrower set. V1 delivered "
            f"{round(min(1.0, len(cal_rows) * FAMILYWISE_DOWN), 3)} over all cells."
        ),
    }

    # The design property, checked rather than assumed: braking must stay cheaper than sizing up.
    # The correction is paid for out of brake sensitivity, so it can invert this — and where it
    # does, that is a fact the owner needs, not one to discover after arming.
    support_bar = 30  # learning_actuator.LIVE_MIN_N_SUPPORT
    inverted = []
    for a, sl in doc["accounts"].items():
        for s, r in sl.items():
            if not r.get("calibrated"):
                continue
            d = r["stop_outs_to_down_weight_measured"]
            if d is None or d >= support_bar:
                inverted.append({"cell": f"{a}/{s}", "stop_outs_to_down_weight_measured": d,
                                 "armed": f"{a}/{s}" in armed_names})
    doc["asymmetry_check"] = {
        "rule": f"a sleeve must down-weight in fewer than {support_bar} stop-outs, the same bar a "
                "live size-up must clear; otherwise 'gating is cheap, sizing is dear' is false for it",
        "cells_where_it_fails": inverted,
        "armed_cells_where_it_fails": [c for c in inverted if c["armed"]],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"wrote {args.out}")
    print(f"family scope {scope}: {k_book} calibrated cells, per-cell budgets "
          f"{FAMILYWISE_DOWN / _divisor(cells[0][0] if cells else ''):.5f} / "
          f"{FAMILYWISE_KILL / _divisor(cells[0][0] if cells else ''):.5f}")
    ub = doc["attained_familywise_upper_bound"]
    print(f"upper bound over all {ub['over_all_calibrated_cells']['n_cells']} cells: "
          f"down {ub['over_all_calibrated_cells']['down']}, kill {ub['over_all_calibrated_cells']['kill']}")
    print(f"upper bound over the {ub['over_armed_cells_only']['n_cells']} armed cells: "
          f"down {ub['over_armed_cells_only']['down']}, kill {ub['over_armed_cells_only']['kill']}")
    fails = doc["asymmetry_check"]["cells_where_it_fails"]
    print(f"asymmetry fails on {len(fails)} cell(s), "
          f"{len(doc['asymmetry_check']['armed_cells_where_it_fails'])} of them armed")
    for account, sleeves in doc["accounts"].items():
        print(f"\n=== {account} ===")
        print(f"{'sleeve':22s} {'tier':34s} {'claim':>8s} {'sd':>6s} {'->down':>7s} {'->gate':>7s} "
              f"{'V1->down':>9s} {'V1->gate':>9s} {'P(gate|dead)':>13s} {'V1 P(g|d)':>10s}")
        for s, r in sleeves.items():
            if not r.get("calibrated"):
                print(f"{s:22s} UNCALIBRATED")
                continue
            cellv = r["familywise_sensitivity"]["cell"]
            print(
                f"{s:22s} {str(r['survivor_tier']):34s} {r['claim_mean_r']:8.4f} {r['sd_r']:6.3f} "
                f"{str(r['stop_outs_to_down_weight_measured']):>7s} "
                f"{str(r['stop_outs_to_gate_measured']):>7s} "
                f"{str(cellv['stop_outs_to_down_weight_measured']):>9s} "
                f"{str(cellv['stop_outs_to_gate_measured']):>9s} "
                f"{r['power_if_edge_gone']['p_gate_within_n_max']:13.4f} "
                f"{cellv['power_if_edge_gone']['p_gate_within_n_max']:10.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

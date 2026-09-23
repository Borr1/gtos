"""learning_actuator.py — the LEARNING SYSTEM: the actuation half of the feedback loop (default-off).

The live `edge_reconciler` is BRAKE-ONLY (it measures per-sleeve realized expectancy and raises a decay alarm,
but its own text is "sizing keeps full weight; review the sleeve" — it never ACTUATES). The account-level governor
(smooth DD-defense + stress-derisk) is shrink-only and never per-sleeve. So the actuation half of the loop is OPEN
(live limitation L5). This module closes it: an EVIDENCE-DRIVEN, PER-SLEEVE, BOUNDED re-rating recommender.

DISCIPLINE (the program's one hard rule, encoded here):
  - EVERY-SPLIT is the bar: a sleeve is only "earning" if positive on train AND oos AND sealed (the anti-overfit
    guard). Negative/flat every split (with enough n) -> GATE. Positive every split -> keep/size. Mixed -> hold+flag.
  - MATERIALITY/SAMPLE floor: below MIN_N the BACKTEST half is INSUFFICIENT and never actuates on its own.
    Amended 2026-07-29 (B274): thin backtest evidence must not make a sleeve immune to its own live record --
    `crypto` has one split at n>=MIN_N and is armed -- so a live refutation can still down-weight or gate a
    sleeve whose backtest verdict is INSUFFICIENT_EVIDENCE.
  - BOUNDED: the recommended confidence multiplier is clamped to [0, MAX_UP] and additionally to the owner's
    dial; the actuator can ZERO a sleeve (gate) but never size it beyond MAX_UP (no runaway). Ruin-safe.
  - DEFAULT-OFF: `enabled=False` => recommendation-only (logs, no live sizing change). Live actuation is an OWNER
    decision (flip `enabled` + the per-namespace config). This module NEVER mutates a broker or a live config.

WHAT SESSION AE CHANGED, 2026-07-30 (B850-B899). Three things, in dependency order.
--------------------------------------------------------------------------------
**1. The backtest half is cost-true, so the cost-true VETO is retired.** The every-split evidence used to be
the CP4/CP5 replay at the legacy cost map -- the one F38 found charged zero commission and F39 found credited
tick erosion with the wrong sign. R could not fix that (no cost-true splits existed) so it bolted on
`cost_true_survivor is False -> block any size-up`. `cost_true_splits.py` now feeds this module Session AA's
broker-true day-series, and the veto is gone: a sleeve whose economics die at broker truth now says so in its
own split means. The property the veto protected -- **no size-up on cost-discredited evidence** -- is asserted
against the real artifact in `test_learning_actuator_cost_true.py`, where it holds by construction rather than
by patch. `cost_true_survivor` / `cost_true_tier` survive as REPORTING labels; nothing keys off them.

**2. n is DAY-BLOCKED.** `MIN_N = 30` is a sample floor and trades that cluster on days are not 30 independent
things. R measured the clustering on this book (`sub_xvol_pullback` 90 trades on 33 dates, lag-1 rho 0.511;
`crypto` 104 on 67, rho 0.441) and applied the correction to the live *null* only, leaving the admission floor
counting raw trades. Both halves now count day-blocks when the producer knows them (`*_days`,
`live_day_blocks`). Evidence that does not carry a day structure still admits on its trade count -- that is
the strictly more permissive path, it exists only for hand-entered legacy triples, and the production loader
always supplies days.

**3. Composition is BIDIRECTIONAL, at two different speeds.** `_apply_live` used to be `min(backtest,
live_cap)`: live could only ever brake. Live evidence that a sleeve *outperforms* its backtest was
unrepresentable, which is not a learning loop. It can now raise -- see `_apply_live` for the rule and for why
the two speeds are what they are.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple, Optional

MIN_N = 30          # per-split sample floor below which evidence is INSUFFICIENT to actuate
MAX_UP = 1.25       # max confidence multiplier (bounded; no runaway size-up)
GATE_MULT = 0.0     # gate = remove the sleeve's size (it still generates; admission/size zeroed)
FLOOR_MULT = 0.5    # soft down-weight when evidence is weak-negative but not decisively dead

# --- live evidence ----------------------------------------------------------------------------
# Hard floor on live fills below which live evidence cannot act AT ALL, in either direction. The
# calibrated boundary already makes a 1- or 2-trade gate impossible, but this floor does not
# depend on the artifact being built correctly -- an earlier draft of the calibration would have
# gated the whole armed book on its first losing trade, and a rule whose safety rests entirely on
# an input file being right is not safe.
LIVE_MIN_N = 3
# Live fills required before live evidence may SUPPORT a size-up. Deliberately the same bar as a
# backtest split: cheap to gate, expensive to size.
LIVE_MIN_N_SUPPORT = MIN_N
# ...and the same bar again in the unit that actually carries independent information. A sleeve
# that took 30 fills across 9 days has not produced 30 observations of anything.
LIVE_MIN_DAY_BLOCKS_SUPPORT = MIN_N

# --- the raise side ---------------------------------------------------------------------------
# How much a single re-rate cycle may add to a sleeve's CURRENT multiplier on live evidence.
# A "re-rate cycle" is one owner-applied re-rating, not one tick: the lane is recommendation-only,
# so each step through this ladder is a human decision on a fresh reading of the record. From an
# undisturbed 1.00 it therefore takes five of them to reach MAX_UP, and each one has to survive a
# record that still clears the support bar.
LIVE_UP_STEP = 0.05
# The most live evidence may ever add above 1.0 in total, mirroring the backtest half's own
# `min(0.25, worst)` mapping so a spectacular live mean cannot buy more size than a spectacular
# backtest one.
LIVE_UP_MAX_EXCESS = 0.25

# --- the materiality band, now SYMMETRIC ------------------------------------------------------
# Adopted 2026-07-30 by Session AP (B1350-B1399) under Borhen's blanket ratification of AE's own
# written recommendation. AE §5 measured the asymmetry and filed it as an owner decision:
#
#   "`every_neg` is a bare sign test with no n band, while `every_pos` requires worst >= +0.05.
#    Proposed repair: a symmetric flat band, which is a change to the standing rule and
#    therefore the owner's."
#
# The instance was `idxrev`: on cost-true splits its means are -0.0243 / -0.0124 / +0.0079, and a
# sealed mean of +0.0079 on n=1145 -- four orders of magnitude inside the band the raise side
# demands -- broke the every-split SIGN test and moved the sleeve GATE -> HOLD_FLAG. A rule whose
# brake fires on any non-positive number while its raise needs +0.05 is not one rule, it is two.
#
# WHAT THE SYMMETRY DOES, AND THE ONE THING IT DELIBERATELY DOES NOT DO. The mirror of
# `every_pos and worst >= +BAND -> SIZE_UP` is `every_neg and best <= -BAND -> GATE`. Applied
# naively that would DELETE a brake whenever a sleeve is negative-but-weakly-so, which is the
# permissive direction and not something a symmetry argument earns. So the band degrades the
# brake instead of removing it: `every_neg` with a best above -BAND becomes DOWN_WEIGHT x0.5
# rather than GATE x0.0. The sleeve is still braked, proportionately, and the verdict says the
# band did it.
MATERIALITY_BAND = 0.05


@dataclass
class SleeveEvidence:
    """per-sleeve every-split evidence (deep-history replay and/or live realized, R per trade)."""
    sleeve: str
    train_meanR: Optional[float] = None
    oos_meanR: Optional[float] = None
    sealed_meanR: Optional[float] = None
    train_n: int = 0
    oos_n: int = 0
    sealed_n: int = 0
    # Distinct trading DAYS behind each split. 0 => unknown, and the split then admits on its trade
    # count (the more permissive reading, kept only for legacy hand-entered evidence).
    train_days: int = 0
    oos_days: int = 0
    sealed_days: int = 0
    status: str = ""               # research registry status (train_validated / breadth_falsified / forward_only)
    # Where the backtest half came from, carried into every receipt so a reader of a recommendation
    # can tell cost-true evidence from the legacy cost map without leaving the artifact.
    evidence_basis: str = ""
    live_meanR: Optional[float] = None
    live_n: int = 0
    # Distinct live trading days behind `live_n`. Same role as `*_days` above, and the bar a live
    # size-up must clear (`LIVE_MIN_DAY_BLOCKS_SUPPORT`).
    live_day_blocks: int = 0
    # Sequential rejection boundaries for CUMULATIVE live R at exactly `live_n` fills, taken from
    # LIVE_EVIDENCE_CALIBRATION_V*.json. None => this sleeve is not calibrated and the live gate
    # cannot fire for it (it reports UNCALIBRATED rather than assuming a distribution).
    live_gate_threshold_r: Optional[float] = None   # cross => soft down-weight
    live_kill_threshold_r: Optional[float] = None   # cross => gate
    # ORDERED realized live R, one entry per fill, oldest first -- and the boundary pair at each
    # prefix length. Supplied together they make the rule test FIRST PASSAGE, which is the quantity
    # the calibration actually solved for (R section 4 item 12). Absent, the rule falls back to the
    # point-in-time test at `live_n` and says so.
    live_r_series: Optional[tuple] = None
    live_boundary_curve: Optional[tuple] = None     # ((down_r, kill_r), ...) indexed n=1..len
    # Coverage class of the cost inside live_meanR: MEASURED / PARTIAL_EXIT_DEAL_ONLY.
    live_cost_coverage: Optional[str] = None
    # The multiplier this sleeve is CURRENTLY deployed at. The live raise ladder steps up from here,
    # so a sleeve cannot jump from its deployed weight to the ceiling on one reading of the record.
    current_conf_mult: float = 1.0
    # Broker-true survivor labels from SURVIVOR_BOOK_V1.json. REPORTING ONLY since 2026-07-30 --
    # they used to drive a size-up veto, which existed solely because the every-split evidence was
    # the legacy-cost CP4/CP5 replay. With `cost_true_splits.py` feeding this module the veto has
    # nothing left to contain; see the module docstring.
    cost_true_survivor: Optional[bool] = None
    cost_true_tier: Optional[str] = None

    def split_records(self) -> list:
        """(name, meanR, n_trades, n_days, n_effective, unit) for the three backtest splits."""
        raw = [("train", self.train_meanR, self.train_n, self.train_days),
               ("oos", self.oos_meanR, self.oos_n, self.oos_days),
               ("sealed", self.sealed_meanR, self.sealed_n, self.sealed_days)]
        out = []
        for name, m, n_tr, n_d in raw:
            if n_d > 0:
                out.append((name, m, int(n_tr), int(n_d), int(n_d), "day_blocks"))
            else:
                out.append((name, m, int(n_tr), int(n_d), int(n_tr), "trades"))
        return out

    def splits(self):
        """Back-compatible (name, meanR, n_effective) triples."""
        return [(s, m, eff) for s, m, _nt, _nd, eff, _u in self.split_records()]

    def evaluable_splits(self, *, day_blocked: bool = True):
        """The BACKTEST splits that clear the sample floor.

        `day_blocked=True` (the default, and what a SIZE-UP must clear) counts independent days;
        `day_blocked=False` counts raw trades, which is the looser reading and what a BRAKE is
        allowed to use. `recommend()` evaluates both and takes the more conservative — see the
        `_backtest_verdict` call site for why the floor is asymmetric too.

        Live evidence is deliberately not one of these: it enters through `_live_stage`, which is
        calibrated against a different null and moves at different speeds in the two directions.
        """
        out = []
        for name, m, n_tr, n_d, eff, _unit in self.split_records():
            n = eff if day_blocked else n_tr
            if m is not None and n >= MIN_N:
                out.append((name, m, n))
        return out

    def live_sum_r(self) -> Optional[float]:
        """Cumulative realized live R. The boundary is defined on the sum, not the mean."""
        if self.live_meanR is None or self.live_n <= 0:
            return None
        return float(self.live_meanR) * int(self.live_n)

    def live_blocks(self) -> int:
        """Independent live observations: distinct days when known, else the raw fill count."""
        return int(self.live_day_blocks) if self.live_day_blocks else int(self.live_n or 0)


@dataclass
class Recommendation:
    sleeve: str
    conf_mult: float                 # multiply the sleeve's deployed confidence by this (clamped [0, MAX_UP])
    gate: bool                       # True => zero the sleeve's size
    verdict: str                     # KEEP / SIZE_UP / DOWN_WEIGHT / GATE / INSUFFICIENT_EVIDENCE / HOLD_FLAG
    reason: str
    actuated: bool = False           # True only if enabled=True (i.e. the conf_mult is meant to be applied live)
    # What the live record said, independently of what the backtest said.
    live_verdict: str = "ABSENT"     # ABSENT / THIN / UNCALIBRATED / CONSISTENT / SUPPORTING /
                                     # NEGATIVE_NOT_DECISIVE / REFUTED_DOWN / REFUTED_KILL / UNUSABLE
    live_n: int = 0
    live_day_blocks: int = 0
    live_sum_r: Optional[float] = None
    backtest_verdict: str = ""       # the verdict before the live stage was composed in
    # "first_passage" when the ordered series was available (what the boundary was calibrated on),
    # "point_in_time" when only a mean and a count were, "none" when there is no live record.
    live_evaluation: str = "none"
    live_first_passage_n: Optional[int] = None   # the fill index at which the boundary was first crossed
    live_raised: bool = False        # True when the live half LIFTED the backtest multiplier
    owner_dial_cap: float = MAX_UP


class _LiveStage(NamedTuple):
    verdict: str
    cap: float                       # ceiling the live half imposes on conf_mult (the brake)
    raise_to: Optional[float]        # target the live half is willing to lift TO (None => no raise)
    gate: bool
    reason: str
    evaluation: str
    first_passage_n: Optional[int]


# --------------------------------------------------------------------------- the live stage

def _first_passage(series, curve) -> Optional[tuple]:
    """Worst boundary ever crossed by the cumulative live R path -> (verdict, n, cum).

    THE FIX FOR R SECTION 4 ITEM 12. The calibration solves for FIRST PASSAGE -- "the probability a healthy
    sleeve trips the boundary at ANY n <= n_max" -- while the shipped rule tested the boundary only
    at the current `n`. Those are different quantities, and the difference is not academic in the
    safe direction: a sleeve that crossed the gate boundary at fill 9 and recovered by fill 14 was
    reported as healthy at fill 14, so the delivered detection behaviour was never the one solved
    for. R could not fix it because `SleeveEvidence` carried a mean and a count and a first-passage
    test needs the ordered path. It carries the path now.

    Latching is one-way and terminal for a kill: a crossing that later recovers still happened, and
    the error budget was paid for it either way. The budget is an `n_max`-fill budget (R item 13:
    the same boundary run to n=1000 delivers 0.051 against a stated 0.020, because a constant-`c`
    sqrt(n) boundary is not anytime-valid), so the epoch a series covers must be the re-rate cycle,
    not all of history. The producer owns that window; this function scores whatever it is given.
    """
    if not series or not curve:
        return None
    cum = 0.0
    worst = None
    for k, r in enumerate(series, start=1):
        if k > len(curve):
            break
        cum += float(r)
        if cum != cum:  # NaN anywhere poisons every comparison below and would fail OPEN
            return ("UNUSABLE", k, cum)
        down_b, kill_b = curve[k - 1]
        if kill_b is not None and cum <= float(kill_b):
            return ("REFUTED_KILL", k, cum)
        if worst is None and down_b is not None and cum <= float(down_b):
            worst = ("REFUTED_DOWN", k, cum)
    return worst


def _live_stage(ev: SleeveEvidence) -> _LiveStage:
    """Live realized evidence -> the brake it imposes and the raise it is willing to support.

    Four rules, and the whole design is in them.

    **1. Silence is never negative evidence.** `live_n == 0` returns a cap of MAX_UP and no raise,
    i.e. no effect whatsoever. A sleeve that has not fired has said nothing. This is not a detail:
    K's G4 measured `metals_core` 0 fires from 990 invocations, `crypto` 0/440 and `energy_agri`
    0/332 over the entire 38-day live window, all consistent with natural low frequency (empirical
    P(zero in a 38-day window) 0.369 / 0.284 / 0.638, and 0.075 for five silent together). A rule
    that read quiet as bad would gate the armed book in its first two months.

    **2. The brake is fast and the raise is slow, and the asymmetry is a claim about evidence, not
    a mood.** A brake and a raise are not symmetric decisions. Braking on a false alarm costs
    forgone profit on a sleeve that is still fine and is reversible on the next reading. Raising on
    a false alarm puts more capital behind a sleeve at exactly the moment its recent record is
    flattering it, on a prop account where the drawdown limit is absorbing -- the loss is not
    reversible by a later re-rate. So the brake fires on 4-8 stop-outs against a calibrated
    boundary and the raise needs `LIVE_MIN_N_SUPPORT` fills across `LIVE_MIN_DAY_BLOCKS_SUPPORT`
    distinct days, fully measured cost, and still only moves by `LIVE_UP_STEP` per cycle.

    **3. Gating is cheap, sizing is dear.** The down-weight boundary is crossed by 4-8 consecutive
    full stop-outs on the armed sleeves; supporting a size-up needs 30 fills on 30 days. That
    asymmetry is calibrated rather than asserted -- the boundary comes from the sleeve's own
    validated R distribution under a day-block null
    (`LIVE_EVIDENCE_CALIBRATION_V*.json`).

    **4. First passage, when the path is available.** See `_first_passage`.

    On cost coverage: a cost class weaker than MEASURED may still GATE but may never SUPPORT.
    Understating cost is the F38 direction, and a live record that says "refuted" *despite*
    possibly-understated costs is evidence a fortiori; the same record saying "healthy" is not.
    """
    n = int(ev.live_n or 0)
    s = ev.live_sum_r()
    if n <= 0 or s is None:
        return _LiveStage("ABSENT", MAX_UP, None, False,
                          "no live fills — silence is not evidence", "none", None)
    if s != s:  # NaN
        # A NaN defeats every comparison below, so it would silently fail OPEN: the brake would
        # never engage and the sleeve would read as healthy. Refuse the record instead.
        return _LiveStage("UNUSABLE", 1.0, None, False,
                          f"live record over {n} fill(s) is not a number; refusing it and blocking "
                          "size-up rather than letting NaN pass every threshold test",
                          "none", None)
    if n < LIVE_MIN_N:
        return _LiveStage("THIN", MAX_UP, None, False,
                          f"only {n} live fill(s) (<{LIVE_MIN_N}); too thin to act in either direction",
                          "none", None)

    fp = _first_passage(ev.live_r_series, ev.live_boundary_curve)
    evaluation = "first_passage" if (ev.live_r_series and ev.live_boundary_curve) else "point_in_time"
    if fp is not None:
        kind, at_n, cum = fp
        if kind == "UNUSABLE":
            return _LiveStage("UNUSABLE", 1.0, None, False,
                              f"live R series is not a number at fill {at_n}; refusing the record "
                              "and blocking size-up", evaluation, at_n)
        if kind == "REFUTED_KILL":
            return _LiveStage("REFUTED_KILL", GATE_MULT, None, True,
                              f"live cumulative {cum:+.3f}R crossed the GATE boundary at fill {at_n} "
                              f"of {n} — the live record refutes the sleeve's validated claim "
                              "(first passage; a later recovery does not un-cross it)",
                              evaluation, at_n)
        return _LiveStage("REFUTED_DOWN", FLOOR_MULT, None, False,
                          f"live cumulative {cum:+.3f}R crossed the DOWN-WEIGHT boundary at fill "
                          f"{at_n} of {n} — live is materially short of the validated claim "
                          "(first passage)", evaluation, at_n)

    if evaluation == "point_in_time":
        # No ordered path: test the boundary where it stands. This under-detects relative to what
        # was calibrated (see `_first_passage`) and is labelled so a receipt shows which test ran.
        if ev.live_kill_threshold_r is not None and s <= ev.live_kill_threshold_r:
            return _LiveStage("REFUTED_KILL", GATE_MULT, None, True,
                              f"live cumulative {s:+.3f}R over {n} fills crosses the GATE boundary "
                              f"({ev.live_kill_threshold_r:+.3f}R) — the live record refutes the "
                              "sleeve's validated claim", evaluation, n)

        if ev.live_gate_threshold_r is not None and s <= ev.live_gate_threshold_r:
            return _LiveStage("REFUTED_DOWN", FLOOR_MULT, None, False,
                              f"live cumulative {s:+.3f}R over {n} fills crosses the DOWN-WEIGHT "
                              f"boundary ({ev.live_gate_threshold_r:+.3f}R) — live is materially "
                              "short of the validated claim", evaluation, n)

    calibrated = (ev.live_gate_threshold_r is not None or ev.live_kill_threshold_r is not None
                  or bool(ev.live_boundary_curve))
    if not calibrated:
        # Not calibrated: cannot test against the claim. A negative live mean still blocks a
        # size-up — that needs no calibration, only a sign.
        if float(ev.live_meanR) <= 0.0:
            return _LiveStage("UNCALIBRATED", 1.0, None, False,
                              f"live {ev.live_meanR:+.3f}R x{n} is negative but this sleeve has no "
                              "calibrated boundary; blocking size-up, not gating", evaluation, None)
        return _LiveStage("UNCALIBRATED", MAX_UP, None, False,
                          f"live {ev.live_meanR:+.3f}R x{n}, no calibrated boundary", evaluation, None)
    if float(ev.live_meanR) <= 0.0:
        return _LiveStage("NEGATIVE_NOT_DECISIVE", 1.0, None, False,
                          f"live {ev.live_meanR:+.3f}R x{n} is negative but inside the boundary; "
                          "hold, no size-up", evaluation, None)

    blocks = ev.live_blocks()
    if n >= LIVE_MIN_N_SUPPORT:
        # PERMIT-ONLY-MEASURED, not deny-a-known-bad-string. Corrected 2026-07-29 (B275) after a
        # refuter measured that the previous form -- `coverage.upper() == "MODELLED"` -> refuse --
        # tested for a value the producer cannot emit. `live_evidence` emits only "MEASURED" or
        # "PARTIAL_EXIT_DEAL_ONLY", so the guard was dead code, while `PARTIAL_EXIT_DEAL_ONLY` --
        # which drops the ENTRY commission and is therefore the F38 direction itself, and which
        # carried 15 of 17 sleeve-rows in the first shipped receipt -- sailed through to SUPPORTING
        # reading ~0.03 R/fill better than the same trades priced whole. `None`, `""`, a trailing
        # space and a misspelling all did too. Deny by default; only a fully measured cost supports.
        if (ev.live_cost_coverage or "").strip().upper() != "MEASURED":
            return _LiveStage("NEGATIVE_NOT_DECISIVE", 1.0, None, False,
                              f"live {ev.live_meanR:+.3f}R x{n} is positive but its cost coverage is "
                              f"{ev.live_cost_coverage!r}, not MEASURED; an incompletely-priced "
                              "record may gate, never support a size-up (F38 direction)",
                              evaluation, None)
        if blocks < LIVE_MIN_DAY_BLOCKS_SUPPORT:
            return _LiveStage("CONSISTENT", MAX_UP, None, False,
                              f"live {ev.live_meanR:+.3f}R x{n} clears the fill bar but sits on "
                              f"{blocks} distinct day(s) (<{LIVE_MIN_DAY_BLOCKS_SUPPORT}); same-day "
                              "fills are not independent observations, so this supports no size-up "
                              "— and it brakes nothing either", evaluation, None)
        target = 1.0 + min(LIVE_UP_MAX_EXCESS, float(ev.live_meanR))
        return _LiveStage("SUPPORTING", MAX_UP, target, False,
                          f"live {ev.live_meanR:+.3f}R x{n} over {blocks} distinct days at MEASURED "
                          f"cost clears the support bar; willing to lift toward x{target:.3f}",
                          evaluation, None)
    return _LiveStage("CONSISTENT", 1.0, None, False,
                      f"live {ev.live_meanR:+.3f}R x{n} is consistent with the claim but under the "
                      f"{LIVE_MIN_N_SUPPORT}-fill support bar; hold, no size-up", evaluation, None)


def recommend(ev: SleeveEvidence, *, enabled: bool = False,
              owner_dial_cap: Optional[float] = None) -> Recommendation:
    """the learning rule: evidence -> a bounded per-sleeve re-rating recommendation. Pure; default-off.

    The backtest half is evaluated TWICE and the more conservative answer wins.

    Day-blocking the sample floor is right for a size-up and wrong for a brake, and measuring it
    made that concrete rather than theoretical. Over the 29 cost-true sleeves the day-blocked floor
    moved exactly two verdicts, one in each direction: `sub_xvol_pullback` lost a SIZE_UP x1.25
    (35 oos trades on 19 days, 37 sealed on 13 — the concentration FOURTH_REVIEW warns about), and
    `kz_london_crypto_low` lost a **GATE** (negative on all three splits, but only its 167-day oos
    clears 30 days). Withdrawing a gate because the evidence is day-thin is the fail-open direction
    for a brake, and it was introduced by the same change that closed a fail-open on the raise side.

    So the floor is asymmetric, exactly like everything else in this module: a size-up must clear
    the day-blocked floor, a brake may fire off the looser trade-count floor, and `min()` of the two
    multipliers is what is returned.

    `owner_dial_cap` is the owner's ceiling on any recommended multiplier. It is HIS number, not a
    measurement: sleeve composition, the risk dial and the allocation profile are his calls
    (CLAUDE.md section 5), and this rule must not be able to recommend past them whatever the evidence
    says. Default `MAX_UP`, i.e. unchanged behaviour.
    """
    dial = MAX_UP if owner_dial_cap is None else min(MAX_UP, float(owner_dial_cap))
    strict = _backtest_verdict(ev, ev.evaluable_splits(day_blocked=True))
    loose = _backtest_verdict(ev, ev.evaluable_splits(day_blocked=False))
    v = strict if strict.conf_mult <= loose.conf_mult else loose
    if strict.verdict != loose.verdict:
        v.reason = (f"{v.reason} FLOOR: day-blocked evidence says {strict.verdict} "
                    f"x{strict.conf_mult:.2f} and raw-trade evidence says {loose.verdict} "
                    f"x{loose.conf_mult:.2f}; the more conservative of the two is taken, because a "
                    "size-up must clear the day-blocked floor and a brake need not.")
    v = _apply_min_n_disagreement(ev, v)
    return _apply_live(ev, v, enabled, dial)


def _apply_min_n_disagreement(ev: SleeveEvidence, v: Recommendation) -> Recommendation:
    """A split dropped for sample size that DISAGREES IN SIGN caps the recommendation at KEEP.

    Adopted 2026-07-30 by Session AP under Borhen's blanket ratification of AE §3.2's own written
    recommendation. It lived in `phase7/receipts/ae_owner_evidence.min_n_disagreement_rule` as a
    receipt-side probe; adopting it means moving it into the lane, which is the only place it can
    actually bind.

    ONE-SIDED BY CONSTRUCTION. It can only ever remove a size-up. It cannot gate, down-weight or
    rescue anything, so the worst it can do is leave a sleeve at the weight it already carries.
    That is why it is safe to adopt in a lane that recommends on armed money.

    WHY IT EXISTS. R §4 item 15: `metals_core` FTMO's SIZE_UP x1.15 survived only because its one
    negative split (oos -0.061 on n=24) fell under `MIN_N` and was dropped -- so "positive on
    every split" was satisfied by discarding the split that disagreed. AE measured the instance as
    already resolved by cost-true evidence (the negative is now a 232-trade / 118-day OOS that no
    floor can discard, and the sleeve is DOWN_WEIGHT x0.50) and the RULE as still open.

    WHAT IT COSTS, MEASURED BY AE OVER BOTH BASES: on the 29 cost-true sleeves it moves NOTHING --
    all four current size-ups (`crypto`, `vol_compression`, `mx_btcusd`, `mx_ethusd`) have no
    disagreeing dropped split. On the legacy CP4/CP5 basis it moves exactly `metals_core`,
    x1.146 -> KEEP x1.00, which is the case R named. Free today, and it forecloses the recurrence.
    """
    if v.conf_mult <= 1.0:
        return v
    admitted = ev.evaluable_splits(day_blocked=False)
    admitted_names = {n for n, _m, _e in admitted}
    dropped = [(s, m, eff) for s, m, _nt, _nd, eff, _u in ev.split_records()
               if m is not None and s not in admitted_names]
    disagree = [(s, m, eff) for s, m, eff in dropped if m <= 0.0]
    if not disagree:
        return v
    v.conf_mult = 1.0
    v.verdict = "KEEP"
    v.reason += (" MIN_N DISAGREEMENT RULE (AE §3.2, ratified 2026-07-30): size-up refused because "
                 + ", ".join(f"{s} {m:+.3f} (n_eff {eff} < {MIN_N})" for s, m, eff in disagree)
                 + " was dropped for sample size and disagrees in sign with the admitted splits. "
                   "One-sided: this rule can only ever remove a size-up.")
    return v


def _backtest_verdict(ev: SleeveEvidence, splits: list) -> Recommendation:
    """The every-split rule over one admitted set of splits. No live evidence, no clamping."""
    if len(splits) < 2:
        # `recommend()` still composes the live half onto this: thin BACKTEST evidence must not make
        # a sleeve immune to its own live record — `crypto` has only one split at n>=MIN_N and it is
        # one of the armed sleeves. If it loses 8 straight live fills the rule has to be able to
        # say so.
        return Recommendation(
            ev.sleeve, 1.0, False, "INSUFFICIENT_EVIDENCE",
            f"only {len(splits)} split(s) with n>={MIN_N}; hold current weight, keep observing.",
            False)
    means = [m for _, m, _ in splits]
    # THE BAND GOES ON THE SIGN TEST, NOT ON THE GATE THRESHOLD. `every_neg` no longer lets an
    # IMMATERIALLY POSITIVE split veto "negative everywhere" — which is the defect AE filed, in
    # the direction AE filed it. The gate threshold itself is untouched, so this rule can only
    # ever ADD a brake.
    #
    # Session AP's first attempt did the opposite and an adversarial pass caught it. It required
    # `best <= -MATERIALITY_BAND` for a GATE, which (a) did not repair AE's own instance — idxrev
    # on cost-true splits is HOLD_FLAG at both commits, because its +0.0079 still vetoed
    # `every_neg` — and (b) WITHDREW the gate from four of the 29 cost-true sleeves, including
    # `vss_fxcross_london_up_low`, which loses 0.3749 R/trade on its train split and stopped
    # gating because its LEAST-negative split was -0.0377. A rule that reads the least-negative
    # split to decide a gate lets one near-zero number excuse ruinous ones.
    # Two clauses, and the second is not decoration. A sleeve with NO split below zero has shown
    # no negative evidence at all, and gating it because none of its splits is *materially*
    # positive would brake a small real edge — caught by
    # `test_live_may_now_raise_but_only_by_one_step`'s +0.01/+0.01/+0.01 fixture, which the
    # one-clause version GATED. So: an immaterially positive split no longer vetoes a negative
    # reading, and a sleeve that is merely thin-positive is still not a non-edge.
    _pos_material = [m for m in means if m > MATERIALITY_BAND]
    every_neg = (not _pos_material) and any(m < 0.0 for m in means)
    every_pos = all(m > 0.0 for m in means)
    worst = min(means); best = max(means)
    _band_saved_the_brake = every_neg and best > 0.0
    if every_neg:
        v = Recommendation(ev.sleeve, GATE_MULT, True, "GATE",
                           f"NEGATIVE/flat on EVERY evaluable split ({_fmt(ev)}) — a non-edge by the every-split bar; "
                           f"recommend gate (size->0). status={ev.status}."
                           + (f" MATERIALITY BAND (AE §5, ratified 2026-07-30): the best split "
                              f"{best:+.4f} is POSITIVE but inside +/-{MATERIALITY_BAND}, so it no "
                              f"longer vetoes the every-split reading. Before this rule a mean four "
                              f"orders of magnitude inside the band a size-up must clear could "
                              f"WITHDRAW this brake." if _band_saved_the_brake else ""))
    elif every_pos and worst >= MATERIALITY_BAND:
        # strongly positive every split -> modest, bounded size-up
        mult = min(MAX_UP, 1.0 + min(0.25, worst))
        v = Recommendation(ev.sleeve, round(mult, 3), False, "SIZE_UP" if mult > 1.0 else "KEEP",
                           f"POSITIVE every split ({_fmt(ev)}), worst {worst:+.3f} — earning by the every-split bar; "
                           f"recommend keep/bounded size-up x{mult:.2f} (cap {MAX_UP}).")
    elif every_pos:
        v = Recommendation(ev.sleeve, 1.0, False, "KEEP",
                           f"positive every split but thin ({_fmt(ev)}); keep deployed weight, no size-up.")
    else:
        # mixed: positive some, negative others -> down-weight if the negatives are large + high-n, else hold+flag
        neg_heavy = any(m < -MATERIALITY_BAND and n >= 3 * MIN_N for s, m, n in splits)
        if neg_heavy:
            v = Recommendation(ev.sleeve, FLOOR_MULT, False, "DOWN_WEIGHT",
                               f"MIXED with a large high-n negative split ({_fmt(ev)}); recommend soft down-weight x{FLOOR_MULT}.")
        else:
            v = Recommendation(ev.sleeve, 1.0, False, "HOLD_FLAG",
                               f"MIXED across splits ({_fmt(ev)}); hold current weight, FLAG for review (regime-dependent).")
    return v


def _apply_live(ev: SleeveEvidence, v: Recommendation, enabled: bool, dial: float) -> Recommendation:
    """Compose the backtest verdict with the live record — in BOTH directions, at two speeds.

    This function used to be one line and one property: ``min(backtest, live_cap)``. Live evidence
    could only ever lower the multiplier, which was the right containment while the backtest half
    was the legacy-cost CP4/CP5 replay -- with a discredited baseline the only safe direction is
    down. AA's cost-true splits removed that reason, and a loop that can only subtract is not a
    learning loop: a sleeve that outperforms its own validation forever reads as "at best, declines
    to brake".

    The rule now:

    * **BRAKE — fast, and exactly as R built it.** 4-8 stop-outs against the day-blocked boundary
      down-weight; the kill boundary gates. A gate set here is terminal for this reading.
    * **RAISE — slow, and only from the top of the evidence stack.** `SUPPORTING` (>= 30 fills on
      >= 30 distinct days, positive, inside the boundary, cost fully MEASURED) may lift the
      multiplier by at most `LIVE_UP_STEP` above what the sleeve is *currently deployed at*, never
      above `MAX_UP`, and never above the owner's dial. It may never un-gate: a sleeve the
      every-split bar calls a non-edge stays gated however good its recent live record is. `idxrev`
      is the live case -- registry-falsified, zero-edge on 5,597 cost-true trades, and the only
      live-profitable sleeve in the live window (B63).

    The two speeds are not symmetric because the two errors are not. A false brake costs forgone
    profit and reverses on the next reading. A false raise adds size at the moment a sleeve's
    recent record is flattering it, on a prop account whose drawdown limit is absorbing, and no
    later re-rate reverses the loss it funds. That is why the asymmetry survives the change of
    direction: it is a statement about the payoff, not about nerve.
    """
    st = _live_stage(ev)
    v.backtest_verdict = v.verdict
    v.live_verdict = st.verdict
    v.live_n = int(ev.live_n or 0)
    v.live_day_blocks = ev.live_blocks() if ev.live_n else 0
    v.live_sum_r = ev.live_sum_r()
    v.live_evaluation = st.evaluation
    v.live_first_passage_n = st.first_passage_n
    v.owner_dial_cap = dial

    # --- brake ---------------------------------------------------------------------------------
    if st.cap < v.conf_mult:
        v.conf_mult = st.cap
        if st.verdict == "REFUTED_KILL":
            v.verdict = "GATE"
        elif st.verdict == "REFUTED_DOWN":
            v.verdict = "DOWN_WEIGHT"
        elif v.verdict == "SIZE_UP":
            v.verdict = "KEEP"
    if st.gate:
        v.gate = True
        v.verdict = "GATE"

    # --- raise ---------------------------------------------------------------------------------
    # The guard is "live may not raise a sleeve the BACKTEST half is BRAKING", stated as a
    # property rather than as a verdict-name check. It used to read `not v.gate and v.verdict !=
    # "GATE"`, which protected exactly one of the two brake states -- so a sleeve the backtest
    # half DOWN_WEIGHTed for a large high-n negative split could be lifted to SIZE_UP x1.05 by a
    # flattering live run. MEASURED as a PRE-EXISTING hole at 5065ed24c, not one introduced with
    # the symmetric band: the same probe (train +0.30 / oos -0.20 / sealed +0.30 at n=200 each,
    # live +1.5 on 200 fills over 200 days) returns `backtest=DOWN_WEIGHT final=SIZE_UP x1.05` at
    # the parent commit and at HEAD before this line changed.
    #
    # It matters because it is the exact failure this function's own docstring names: "a false
    # raise adds size at the moment a sleeve's recent record is flattering it, on a prop account
    # whose drawdown limit is absorbing, and no later re-rate reverses the loss it funds." A
    # sleeve whose own validation splits are braking it is that case by definition. Fixed by
    # Session AP (B1350-B1399) while adopting AE's symmetric band, which turned the hole from
    # latent into reachable by giving `every_neg` a second, non-GATE outcome.
    _braking = ("GATE", "DOWN_WEIGHT")
    if st.raise_to is not None and not v.gate and v.verdict != "GATE" \
            and v.backtest_verdict not in _braking:
        ceiling = min(MAX_UP, dial, float(ev.current_conf_mult) + LIVE_UP_STEP)
        proposed = min(float(st.raise_to), ceiling)
        if proposed > v.conf_mult:
            v.conf_mult = round(proposed, 6)
            v.verdict = "SIZE_UP"
            v.live_raised = True
            v.reason = (f"{v.reason} LIVE RAISE: lifted from x{ev.current_conf_mult:.3f} to "
                        f"x{v.conf_mult:.3f} (step cap {LIVE_UP_STEP}, ceiling "
                        f"x{min(MAX_UP, dial):.3f}).")

    if st.verdict != "ABSENT":
        v.reason = f"{v.reason} LIVE: {st.reason}."

    v.conf_mult = max(0.0, min(MAX_UP, dial, v.conf_mult))
    if v.verdict == "SIZE_UP" and v.conf_mult <= 1.0:
        # The dial (or the step cap) took the size-up away; the verdict must not still claim one.
        v.verdict = "KEEP"
        v.live_raised = False
    v.actuated = bool(enabled) and v.verdict in ("GATE", "DOWN_WEIGHT", "SIZE_UP")
    return v


def _fmt(ev: SleeveEvidence) -> str:
    """Split summary carrying BOTH counts, because they are the same evidence read two ways."""
    parts = []
    for name, m, n_tr, n_d, eff, unit in ev.split_records():
        if m is None:
            continue
        parts.append(f"{name} {m:+.3f}(n{n_tr}" + (f"/d{n_d}" if n_d else "") + ")")
    return ", ".join(parts)


def rerate_book(evidence: list, *, enabled: bool = False,
                owner_dial_cap: Optional[float] = None) -> dict:
    """run the learning rule over all sleeves -> {sleeve: Recommendation}. Default-off (recommendation-only).

    Refuses duplicate sleeve names rather than letting the last one win. The system is two-account
    by construction and this takes a flat list, so merging FTMO and redacted_account evidence would
    silently discard one account's verdict -- and which one survived depended on list ORDER, so the
    same two records could return `GATE x0.0` or `SIZE_UP x1.25` (found by a refuter, B277). Callers
    must re-rate per account; `rerate_book_from_live.py` already does.
    """
    seen = [ev.sleeve for ev in evidence]
    dupes = sorted({s for s in seen if seen.count(s) > 1})
    if dupes:
        raise ValueError(
            f"rerate_book received duplicate sleeve name(s) {dupes}. Evidence must be re-rated one "
            "account at a time; silently keeping the last would make the verdict order-dependent."
        )
    return {ev.sleeve: recommend(ev, enabled=enabled, owner_dial_cap=owner_dial_cap)
            for ev in evidence}

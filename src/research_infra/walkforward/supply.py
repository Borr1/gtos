"""Research-side specs for the generators the production path cannot reach. Session AK.

WHAT THIS IS FOR
----------------
Four sleeves in this repository have a generator and **no entry in any of `sleeves/registry.py`'s
three `SleeveSpec` tables** (`BUILT`, `CANDIDATE_BUILT`, `MARKET_EXPANSION_BUILT`), so
`active_specs` can never return them, `GenerationPort` can never drive them, and **no
walk-forward gate run in this programme had ever judged them**:

    vol_squeeze              H4  indices     — the first genuinely-new factory sleeve
    ny_index_momentum        M15 indices     — NY killzone continuation, mid-vol only
    structural_retest        M15 3 classes   — the estate's ONLY short-side mechanism
    session_leadlag_genuine  M15 3 followers — registered for SIZING since wave 6, and the only
                                               sleeve in the estate that can be sized and cannot
                                               fire

**Two scope corrections, both from an adversarial pass on this module's own first draft (B972),
and both worth reading before quoting any of it.**

*"No walk has ever judged them" was too wide and is now scoped to the walk-forward gate.* It is
established by receipt search — no phase3–7 gate receipt and no pre-AK `TRIAL_LEDGER` row carries
any of the four — and NOT by the registry absence, which does not imply it (`run_gate` takes
trades from any source; this module's own driver bypasses `active_specs` entirely). What the three
non-leadlag sleeves DO have is a full `CandidateSpec` in `candidate_registry.py:48-85` with
every-split economics, and explicit quarantine verdicts from the 2026-06-17 principal audit in
`CANDIDATE_DECISION` (`:209-223`) — `structural_retest`'s reads *"full three-cell daily-unit audit
failed: meanR -0.071032, train/oos/sealed -0.053274/-0.082925/-0.086833."* So "no `SleeveSpec`" is
true and "no spec at all" would be false, and this session's cell decomposition should be read as
the broker-true restatement of a recorded verdict rather than as a first look.

*`session_leadlag_genuine` had no generator MODULE in this package, not no generator.*
`KB6_session_stacks.py:77` `gen_session_leadlag_genuine()` mines the same four legs through
`KB5_leadlag_subh4.mine_pair` and has existed for weeks; it produced the `n=390 / +0.4598 R`
forward numbers and the `ADDITIVE` vol-matched-MC verdict in `KB6_SESSION_STACKS_RESULT.json` that
`admission.py:267-277` cites while registering the sleeve at conf 0.15. Session AA scoped this
correctly — `AA_ORPHAN_TRIAGE_V1.json` says *"no generator module **in
src/components/ultimate_book/sleeves/**"* — and the first draft of this docstring dropped the
scope.

`AA_ESTATE_WALK_RESULT.md` §4 routed the first three to Borhen as *"one one-line decision, not a
research project"*, and it is right that the registry edit is one line each. What it does not
say, and what this module measures, is that **the edit is not the same size for all four**: the
first three need only a spec, while `session_leadlag_genuine` needs a channel the generation path
does not have (`LIVE_WIRING_GAP`).

THIS DOES NOT TOUCH THE LIVE PATH, AND THAT IS THE POINT
---------------------------------------------------------
`sleeves/registry.py` is left alone: FTMO is armed, and adding a spec there would change what
`active_specs` resolves for anything that reads it. Instead, this module carries a
**research-side** spec — the same five facts a `SleeveSpec` carries plus the provenance and the
authored exit contract — and the driver walks bar series directly, which is exactly the
equivalence Session AF established and measured (`SESSION_AF_FAMILY_EXPANSION_RESULT.md` §1: ten
of ten trade counts and median holds exact against `W_MX_PILOT.json`). The proposed registry edit
is published as DATA (`REGISTRY_EDIT_PROPOSAL`) so the result document and the receipt cannot
disagree about what is being proposed, and Borhen decides.

WHY EACH SPEC CARRIES A `bar_count`, AND WHY ONE OF THEM IS 513
---------------------------------------------------------------
The live engine hands a generator `bars[i-(n-1):i+1]` for `n = max(bar_count, spec.bar_count)`
(`book_engine.py:483`). For three of these four sleeves the window length does not matter beyond
the warmup floor: every quantity they read is a fixed lookback from `i`, so any `n` past the
floor gives an identical answer.

**`structural_retest` is not one of them, and that is a latent generator defect.**
`_htf_trend_at` (`structural_retest.py:82-103` at HEAD; it was `:66-87` before B950 added 22 lines
above it, and the first draft of this docstring carried the stale anchor) rebuilds its 16-bar HTF
blocks from **index 0 of the window it was handed** and sets `completed_at_i` before appending the
block bar `i` closes. So the reference block is `[16*(floor(i/16)-1), 16*floor(i/16)-1]` in WINDOW
coordinates — exact for every window length in [513, 4000), 0 mismatches — and which ABSOLUTE bars
that is depends on `n mod 16`: the block ends adjacent to the decision bar iff `n ≡ 1 (mod 16)`,
and ends 16 bars earlier when `n ≡ 0 (mod 16)`. **The same bar can therefore be traded or not
traded purely on how much history the caller supplied**: measured at 513 against 528 on three
symbols, jaccard 0.759, 169 trades only at 513 and 79 only at 528.

Two claims about this that the first draft made and that are WITHDRAWN, both refuted by an
adversarial pass on this module (B972):

* **"513 is the only aligned phase" is false.** Every `bar_count ≡ 1 (mod 16)` is equally aligned
  (529, 545, 561, …), which follows from `MIN_BARS = 512` being `32*16`. 513 is the SMALLEST
  aligned length above that floor, which is why it is chosen — not the only one.
* **"and hence a different DIRECTION" is structurally impossible.** Each `(class, session)` pair
  appears exactly once in `WHITELIST`, so a fixed bar can match at most one regime and therefore
  one direction. Measured: of the 782 (symbol, decision-bar) pairs present at both phases, the
  direction flips on **0**. The phase changes trade/no-trade, never long/short.

And "aligned" claims less than it sounds: the 513 block is a rolling 16-bar aggregate ending at
`i-1`, which is a calendar H4 candle on only 6.5 % of those trades and not even 16 contiguous M15
bars on 9.8 % of them. There is no HTF grid here to be aligned to, so no repair should be scoped
as restoring one.

Filed as a repair-queue row; **not repaired here**, because changing the chunking changes the rule
the three whitelist cells were verified under, and that is a re-derivation, not a port.

THE PREFILTERS ARE NECESSARY CONDITIONS, AND THE PARITY IS MEASURED
-------------------------------------------------------------------
`structural_retest` costs O(window) per decision bar (a 513-long ATR list plus a 513-step HTF
chunking), and the M15 archive is 2.7 M bars. Walking it naively is hours. Each spec therefore
carries a `prefilter`: a cheap predicate that is a **necessary condition** for its generator to
emit, evaluated from full-series arrays.

The safety argument is THREE arguments, not the one the first draft gave, and an adversarial pass
on this module is why:

1. **The ATR reads are bit-identical.** `atr14(bars, j)` reads only `bars[j-14 .. j]`
   (`primitives.py:23-30`), so for any window index `j >= 14` the value equals
   `atr14(full_series, lo + j)`. And no generator here can read below 14 at ANY `bar_count`,
   because each one's warmup floor exceeds its deepest ATR lookback by at least 14 —
   `vol_squeeze` 87 against `j-60`, `ny_index_momentum` 520 against `j-480`, `structural_retest`
   512 against `j-99`, `session_leadlag` 15 against `j`. So `bar_count` is free for the PREFILTER
   even though it is not free for `structural_retest`'s HTF phase.
2. **The clock is memoised per UTC hour, and that is exact** because both DST transition instants
   are on the hour — see `server_hm_series`, including the reason its first version gave wrongly.
3. **One comparison is NOT the same float expression on both sides, so its necessity is MEASURED
   rather than proven.** `structural_retest`'s vol gate compares `a` against a RUNNING sum with
   subtraction here (`build_series_context`) while `generate()` recomputes a FRESH 100-term sum
   (`structural_retest.py:186`). Algebraically equal, **not bit-equal**: max relative difference
   **1.255e-13**. The 1.4 boundary is exactly reachable because prices are quantised — on XTZUSD at
   2025-07-11T22:30Z the generator reads exactly 1.4 while this array reads 1.4000000000000101 — so
   a drift the other way could in principle make the prefilter refuse a bar the generator would
   take. Measured: **0 gate flips in 1,424,028 bars, 1 at-risk bar, 0 of them in a whitelisted
   cell.**

None of that is evidence, so the driver runs unfiltered walks and compares trade sets. Measured on
**every symbol of every spec — 37 walks — plus both authored-UTC populations: 0 candidates dropped
anywhere.** The artifact's `prefilter_parity` carries the one-symbol-per-spec subset the driver runs
inline; the full sweep is recorded in `SESSION_AK_SLEEVE_SUPPLY_RESULT.md` §7.10. A prefilter that
silently dropped candidates would make every downstream number a statement about a smaller sleeve.

Offline and pure: no broker module, no config write, no order.
"""

from __future__ import annotations

import contextlib
import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional, Sequence

from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15
from src.components.ultimate_book.primitives import atr14

__all__ = [
    "LIVE_WIRING_GAP",
    "REGISTRY_EDIT_PROPOSAL",
    "ResearchSleeveSpec",
    "SUPPLY_SPECS",
    "SeriesContext",
    "authored_clock",
    "build_series_context",
    "server_hm_series",
]

SCHEMA = "gtos.walkforward.supply.v1"


# =====================================================================================
# the server-clock index
# =====================================================================================

def server_hm_series(times: Sequence[dt.datetime]) -> list[tuple[Optional[int], Optional[int]]]:
    """`(server_hour, server_minute)` per bar, memoised on the UTC hour.

    `_server_clock.server_hour_minute` resolves the DST rule per call, and the archive is 2.7 M
    M15 bars, so the naive loop is the driver's dominant cost. Memoising on the UTC HOUR is
    exact rather than convenient: `broker_clock.NEW_YORK_PLUS_7` transitions when
    `America/New_York` does, and **both transition instants land on a whole UTC hour** — 07:00 UTC
    in spring and **06:00 UTC** in autumn (`broker_clock.py:130,136`) — so no two bars inside one
    UTC hour can straddle one.

    **The "07:00 UTC in both directions" this docstring first claimed was wrong** (autumn is
    06:00), caught by an adversarial pass on this module. The conclusion is unchanged because all it
    needs is that each instant is on the hour, which is what is now stated. Measured identical to
    the per-bar function over 783,094 archive bars and across all six 2024-2026 transition
    instants; a test pins it on both 2026 transition days with a guard proving the sampled day
    actually changes offset.
    """
    from src.components.ultimate_book.sleeves._server_clock import server_hour_minute

    out: list[tuple[Optional[int], Optional[int]]] = []
    cache: dict[tuple, tuple[Optional[int], Optional[int]]] = {}
    for t in times:
        if t is None:
            out.append((None, None))
            continue
        key = (t.year, t.month, t.day, t.hour)
        hit = cache.get(key)
        if hit is None:
            hm = server_hour_minute(t)
            # The minute is unaffected by a whole-hour offset, so the hour is what the cache
            # holds and the minute is taken from the bar itself. Storing the resolved pair
            # would be wrong for every bar in the hour except the first.
            hit = cache[key] = (hm[0], None)
        out.append((hit[0], t.minute if hit[0] is not None else None))
    return out


# =====================================================================================
# the per-series context a prefilter reads
# =====================================================================================

@dataclass
class SeriesContext:
    """Full-series quantities every prefilter is allowed to read. Computed once per series."""

    symbol: str
    timeframe: int
    bars: list
    times: list
    #: `atr14(bars, k)` for every k. Identical to the value the generator computes inside any
    #: window whose index for that bar is >= 14 (see the module docstring).
    atr: list[float]
    #: Rolling mean of the last 100 ATRs ENDING AT k inclusive, i.e. `mean(atr[k-99:k+1])`.
    #: `structural_retest.generate` computes exactly this (`:170`).
    atr_sma100: list[Optional[float]]
    #: `(server_hour, server_minute)` per bar.
    server_hm: list[tuple[Optional[int], Optional[int]]]


def build_series_context(symbol: str, timeframe: int, bars: Sequence, times: Sequence,
                         *, need_sma100: bool = False,
                         need_server_clock: bool = False) -> SeriesContext:
    n = len(bars)
    atr = [atr14(bars, k) for k in range(n)]
    sma: list[Optional[float]] = []
    if need_sma100:
        run = 0.0
        for k in range(n):
            run += atr[k]
            if k >= 100:
                run -= atr[k - 100]
            sma.append(run / 100.0 if k >= 99 else None)
    hm: list[tuple[Optional[int], Optional[int]]] = (
        server_hm_series(times) if need_server_clock else [])
    return SeriesContext(symbol=symbol, timeframe=timeframe, bars=list(bars), times=list(times),
                         atr=atr, atr_sma100=sma, server_hm=hm)


# =====================================================================================
# the prefilters
# =====================================================================================

def _prefilter_vol_squeeze(ctx: SeriesContext, i: int, *, authored_utc_clock: bool = False) -> bool:
    """Necessary conditions from `vol_squeeze.generate` (`:56-75`), all ATR-only.

    Reproduces, in order: the warmup floor, `a > 0`, the HTF trend gate (`|close - close[-50]| >
    ATR`), the squeeze test (mean of the last 12 ATRs at or below the 25th-percentile of the last
    60) and the expansion test (`range >= 1.1 * ATR`). The body/direction test is left to the
    generator because it is already cheap.
    """
    from src.components.ultimate_book.sleeves import vol_squeeze as VS

    if i < VS.MED_LB + VS.COMP_LB + 15:
        return False
    A = ctx.atr
    a = A[i]
    if a <= 0:
        return False
    B = ctx.bars
    if i < VS.TREND_LB:
        return False
    diff = B[i].c - B[i - VS.TREND_LB].c
    if not (diff > a or diff < -a):
        return False
    window = sorted(A[i - VS.MED_LB:i])
    if not window:
        return False
    thr = window[int(VS.SQ_PCT * len(window))]
    recent = A[i - VS.COMP_LB:i]
    if not recent or (sum(recent) / len(recent)) > thr:
        return False
    return (B[i].h - B[i].l) >= VS.EXP_K * a


def _prefilter_ny_index_momentum(ctx: SeriesContext, i: int, *,
                                 authored_utc_clock: bool = False) -> bool:
    """`ny_index_momentum` fires only at the server 17:00 M15 bar (`:78`) past its 520-bar floor.

    That single gate is a 1-in-96 filter and it is the generator's own, so nothing else is needed.
    `authored_utc_clock` has no effect: this sleeve already routes through `_server_clock`
    (`:41-48`), which is why it is not part of the F7 A/B.
    """
    from src.components.ultimate_book.sleeves import ny_index_momentum as NIM

    if i < NIM.MIN_BARS or i < NIM.WINDOW:
        return False
    if ctx.atr[i] <= 0:
        return False
    h, m = ctx.server_hm[i] if ctx.server_hm else (None, None)
    return h == NIM.DECISION_HOUR and m == NIM.DECISION_MIN


def _prefilter_structural_retest(ctx: SeriesContext, i: int, *,
                                 authored_utc_clock: bool = False) -> bool:
    """Necessary conditions from `structural_retest.generate` (`:159-176`).

    Reproduces the 512-bar floor, `a > 0`, the high-vol gate (`a/sma100 >= 1.4` AND
    `a >= 1.2*sma100`) and the session bucket — the last of which must be a bucket that appears
    in `WHITELIST` for this symbol's class at all, or no regime can match it. The HTF trend and
    the five detectors are left to the generator; they are the expensive half and they are the
    half that cannot be hoisted exactly (see the `bar_count = 513` note in the module docstring).

    `authored_utc_clock=True` reads the session off the RAW UTC hour, which is what the sleeve
    did before B950's F7 repair. The prefilter has to follow whichever clock the generator is
    running under or it would drop bars the generator would have taken.
    """
    from src.components.ultimate_book.sleeves import structural_retest as SR

    if i < SR.MIN_BARS or i < 100:
        return False
    A = ctx.atr
    a = A[i]
    if a <= 0:
        return False
    sma = ctx.atr_sma100[i] if i < len(ctx.atr_sma100) else None
    if not sma or sma <= 0:
        return False
    if a / sma < SR.HIGH_VOL or a < SR.GATE_K * sma:
        return False
    cls = SR._CLASS_OF.get(ctx.symbol)
    if cls is None:
        return False
    h = ctx.times[i].hour if authored_utc_clock else (
        ctx.server_hm[i][0] if ctx.server_hm else None)
    sess = SR._session(h)
    if sess is None:
        return False
    return any(c == cls and s == sess for (c, s, _r, _v) in SR.WHITELIST)


def _prefilter_session_leadlag(ctx: SeriesContext, i: int, *,
                               authored_utc_clock: bool = False) -> bool:
    """`session_leadlag_genuine`'s cheap half: the ATR and the session window.

    The leader-impulse `|z| >= zthr` test is the real filter, but it needs the leader feed, which
    is the driver's to hold; the driver evaluates it inside the generator. This prefilter only
    removes the ~2/3 of bars outside every leg's session window.
    """
    from src.components.ultimate_book.sleeves import session_leadlag as SL

    legs = tuple(l for l in SL.LEGS if l.follower == ctx.symbol)
    if not legs:
        return False
    if i < SL.MIN_BARS or ctx.atr[i] <= 0:
        return False
    h = ctx.times[i].hour if authored_utc_clock else (
        ctx.server_hm[i][0] if ctx.server_hm else None)
    return any(SL.session_ok(h, l.session) for l in legs)


# =====================================================================================
# the spec table
# =====================================================================================

@dataclass(frozen=True)
class ResearchSleeveSpec:
    """A `SleeveSpec` plus the four things a research walk needs and the live one does not."""

    tag: str
    module: str
    timeframe: int
    on_surface: tuple[str, ...]
    #: The window the driver hands the generator, i.e. what `spec.bar_count` would be.
    bar_count: int
    #: `WARMUP` cluster name the live spec would carry. Only used for reporting: the driver's
    #: floor is `bar_count`, which is at or above every one of these generators' own floor.
    cluster: str
    #: The exit contract the sleeve's own docstring authorises, since `SLEEVE_EXIT_PROFILES`
    #: has no entry for any of these four (verified: all four fall to `DEFAULT_EXIT_PROFILE`).
    authored_exit: dict
    #: file:line for the structure claim and for the verification claim in the docstring.
    provenance: str
    #: Why the production path cannot reach it, in one sentence.
    why_unreachable: str
    prefilter: Callable[..., bool]
    #: True when this sleeve's own clock was wrong before B950 and both readings are published.
    f7_ab: bool = False
    #: True when the generator needs an input the generation path cannot supply.
    needs_cross_symbol_feed: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def generator(self) -> Callable[..., Any]:
        import importlib

        mod = importlib.import_module(
            f"src.components.ultimate_book.sleeves.{self.module}")
        return mod.generate

    def needs(self) -> dict[str, bool]:
        return {
            "need_sma100": self.tag == "structural_retest",
            "need_server_clock": self.tag != "vol_squeeze",
        }


SUPPLY_SPECS: dict[str, ResearchSleeveSpec] = {
    "vol_squeeze": ResearchSleeveSpec(
        tag="vol_squeeze", module="vol_squeeze", timeframe=TF_H4,
        on_surface=("GER40", "UK100", "SPX500", "NAS100", "US30_cash"),
        # Every quantity is a fixed lookback from i (max MED_LB+COMP_LB+15 = 87), so any window
        # past the floor is identical. 260 is the engine default (`book_engine.py:483`).
        bar_count=260, cluster="index",
        authored_exit={
            "policy": "fixed_target", "target_r": 3.0, "time_stop_bars": None,
            "cite": "sleeves/vol_squeeze.py:30 TARGET_R=3.0; the intent carries "
                    "target_dist = 3 * stop_dist, so the target IS the contract and no "
                    "time stop is authored",
        },
        provenance="sleeves/vol_squeeze.py:1-36 — every-split-positive at real cost on the "
                   "4-index cell (train +0.243 / oos +0.129 / sealed +0.227), random-entry "
                   "placebo p=0.003, negative control (coil breakout WITHOUT the ATR-percentile "
                   "vol-state) NULL every split, corr_to_book -0.111, ~156 trades/yr; US30_cash "
                   "added 2026-06-17 with its own re-derivation and an honest caveat that it is "
                   "US-beta breadth rather than orthogonal diversification",
        why_unreachable="no SleeveSpec in sleeves/registry.py (BUILT / CANDIDATE_BUILT / "
                        "MARKET_EXPANSION_BUILT all omit it), so active_specs cannot return it "
                        "and GenerationPort cannot drive it",
        prefilter=_prefilter_vol_squeeze,
        notes=("no time gate at all, so no F7 exposure",),
    ),
    "ny_index_momentum": ResearchSleeveSpec(
        tag="ny_index_momentum", module="ny_index_momentum", timeframe=TF_M15,
        on_surface=("SPX500", "GER40", "UK100", "US30_cash", "NAS100", "JP225"),
        # MIN_BARS = 520 and the window index must EXCEED it (`:72` `i < MIN_BARS`), so 521.
        bar_count=521, cluster="index",
        authored_exit={
            "policy": "time_stop", "target_r": None, "time_stop_bars": 20,
            "cite": "sleeves/ny_index_momentum.py:18,33 — 'EXIT = hold to session close "
                    "(MAXBARS time-stop) or stop; target None', MAXBARS = 20 M15 bars = 5 h. "
                    "Note this MATCHES ny_crypto_momentum's live profile "
                    "(execution_packets.py:64-65, time_stop_bars=20), the sleeve it is the "
                    "index sibling of — so the number needs no unit conversion (B750: "
                    "time_stop_bars is M15 units for every sleeve)",
        },
        provenance="sleeves/ny_index_momentum.py:1-20 — pooled n=863, every-split positive "
                   "(train +0.178 / oos +0.175 / sealed +0.257), CORRECT random-entry-same-exit "
                   "null p=0.0000, both sides positive (LONG 538 +0.221 / SHORT 325 +0.162, so "
                   "not index bullish drift), drift-null p=0.005, one negative year (2023); "
                   "UK100 kept at -0.083 to avoid post-hoc member selection",
        why_unreachable="no SleeveSpec in sleeves/registry.py",
        prefilter=_prefilter_ny_index_momentum,
        notes=("already routes its decision hour through _server_clock (`:41-48`), so it "
               "carries no F7 defect and is not part of the A/B",),
    ),
    "structural_retest": ResearchSleeveSpec(
        tag="structural_retest", module="structural_retest", timeframe=TF_M15,
        on_surface=(
            "BTCUSD", "ETHUSD", "XRPUSD", "XTZUSD", "DASHUSD", "DOTUSD", "ADAUSD", "LTCUSD",
            "XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
            "XCUUSD",
            "SPX500", "GER40", "UK100", "US30_cash", "NAS100", "JP225",
        ),
        # 513 = 32*16 + 1: the SMALLEST length above the MIN_BARS=512 floor at which the HTF
        # reference block ends adjacent to the decision bar. Every bar_count = 1 (mod 16) is
        # equally aligned; 513 is not unique, only minimal. See the module docstring.
        bar_count=513, cluster="index",
        authored_exit={
            "policy": "fixed_target_time_stop", "target_r": 2.0, "time_stop_bars": 32,
            "cite": "sleeves/structural_retest.py:13,28-29 — 'Exit = fixed 2R + 32-bar "
                    "time-stop', TARGET_R = 2.0, MAXBARS = 32 M15 bars = 8 h",
        },
        provenance="sleeves/structural_retest.py:8-15 — three PRINCIPAL-VERIFIED whitelist "
                   "cells, one-per-bar deduped at real cost: (crypto, NY, dn, high) SHORT "
                   "n=5957 +0.057/+0.055/+0.073 null p=0.043; (metal, London, dn, high) SHORT "
                   "n=2017 +0.143/+0.075/+0.283 null p=0.043 with 9 metals positive; (index, "
                   "Asian, up, high) LONG n=1291 +0.057/+0.091/+0.188 null p=0.010",
        why_unreachable="no SleeveSpec in sleeves/registry.py; also absent from "
                        "candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES, which "
                        "tests/ultimate_book/test_candidate_promotion_plumbing.py:74 pins",
        prefilter=_prefilter_structural_retest, f7_ab=True,
        notes=(
            "the estate's ONLY short-side mechanism: two of its three cells are SHORT, and "
            "neither account currently carries any deliberate short exposure",
            "NOT an unexamined sleeve: candidate_registry.py:77-85 catalogues it at confidence "
            "0.0 with status quarantined_daily_unit_failure, and CANDIDATE_DECISION (:209-223) "
            "records the 2026-06-17 principal audit's verdict — 'full three-cell daily-unit "
            "audit failed: meanR -0.071032'. What is new here is the broker-true walk-forward "
            "gate, not the first look",
            "its session buckets were raw UTC until B950 (F7, uncorrected here because the "
            "sleeve is in no registry and so was not in the deployed set the B29/B54 repair "
            "enumerated). Both clock readings are published",
            "its HTF trend is window-phase dependent (see module docstring); bar_count=513 is "
            "the smallest aligned reading above its own MIN_BARS floor, and the sensitivity is "
            "measured at 24 % of the trade set",
        ),
    ),
    "session_leadlag_genuine": ResearchSleeveSpec(
        tag="session_leadlag_genuine", module="session_leadlag", timeframe=TF_M15,
        on_surface=("GER40", "USDJPY", "AUDJPY"),
        bar_count=260, cluster="leadlag",
        authored_exit={
            "policy": "per_leg", "target_r": 4.0, "time_stop_bars": 64,
            "cite": "KB5_leadlag_subh4.py:145,176-182 — maxbars=64 M15 bars (16 h); T2.0 legs "
                    "carry target_dist = 2*ATR against a 0.5*ATR stop, i.e. 4 R; the TRAIL leg "
                    "carries no target and arms at 2 R with a 1 R gap. THREE legs are T2.0 and "
                    "ONE is TRAIL, which SLEEVE_EXIT_PROFILES (one profile per sleeve) cannot "
                    "express — so a uniform-contract variant is measured beside the faithful one",
        },
        provenance="admission.py:267-277 CLEAN4_REGISTRY conf 0.15, forward-only: FWD +0.46 R "
                   "on n=390, 36 % win, ~195 trades/yr, corr +0.053 vs book, ADDITIVE on the "
                   "vol-matched stress MC (Sharpe 0.1522 -> 0.1586, stress@1 % +2.51, @1.5 % "
                   "+2.03). Mechanism: KB6_session_stacks.py:52-58 (the LL_FWD legs) driving "
                   "KB5_leadlag_subh4.py:145-185 (mine_pair)",
        why_unreachable="the generator did not exist until B960, AND the generation path has no "
                        "cross-symbol channel to feed it a leader series — see LIVE_WIRING_GAP",
        prefilter=_prefilter_session_leadlag, f7_ab=True, needs_cross_symbol_feed=True,
        notes=(
            "its registry surface is six symbols and only THREE are followers; US30_cash is a "
            "leader and SPX500/NAS100 appear in no leg — the authored-vs-tradeable universe "
            "collision AA §3.2 measured on four other sleeves",
            "the graduation condition in its own note ('when a 3rd fwd year exists') is the "
            "kind of wait FOURTH_REVIEW §2.1 converts to a measurement; the M15 archive is "
            "2024-01..2026-07, which is 2.5 years and not 3",
        ),
    ),
}


#: The plumbing `session_leadlag_genuine` would need to run live, stated once so the next
#: session does not have to re-derive it. Published in the artifact.
LIVE_WIRING_GAP: dict[str, Any] = {
    "sleeve": "session_leadlag_genuine",
    "what_is_missing": (
        "a cross-symbol bar channel in the generation path. `SleeveSpec` (sleeves/registry.py:34-43) "
        "carries `aux_timeframe`/`aux_count`, and `book_engine` fills them from the SAME symbol at "
        "a second timeframe — `vp_euidx_pocgrav`'s M1 volume profile is the only user. No field, "
        "and no call site, passes another INSTRUMENT's bars to a generator."
    ),
    "smallest_sufficient_change": [
        "SleeveSpec gains `leader_symbols: tuple[str, ...] = ()` and `leader_count: int = 0`",
        "book_engine's per-spec fetch loop additionally fetches those symbols at the spec "
        "timeframe and passes them as a `leader_feeds` mapping",
        "the leader series must be resolved through symbol_map.build_broker_symbol_resolver, "
        "never by hand (walkforward/registry.py's docstring records what happened when a "
        "session probed canonical names instead)",
    ],
    "why_it_is_not_free": (
        "it widens the engine's per-cycle fetch by one instrument per leg and adds a staleness "
        "question the single-symbol path does not have: a leader bar can be missing or stale "
        "independently of the follower's. The generator already fails closed on an absent feed; "
        "a live version needs the same refusal on a STALE one, which is book_engine.py:512's "
        "rule applied to a second series."
    ),
    "owner_decision": (
        "whether to spend that on a conf-0.15 forward-only sleeve. This lane's job was to "
        "produce the number that makes the question answerable, not to answer it."
    ),
}


#: The one-line-per-sleeve registry edit AA §4 routed to Borhen, as data rather than prose.
#: NOTHING here is applied: `sleeves/registry.py` is untouched on this branch.
REGISTRY_EDIT_PROPOSAL: dict[str, dict] = {
    "vol_squeeze": {
        "table": "CANDIDATE_BUILT",
        "line": ('"vol_squeeze": SleeveSpec("vol_squeeze", vol_squeeze.generate, TF_H4, '
                 '"index", vol_squeeze.ON_SURFACE, bar_count=260),'),
        "also_needs": ["an execution_packets.SLEEVE_EXIT_PROFILES entry (fixed 3R target)",
                       "an admission.py confidence weight if it is ever to be sized"],
        "live_safe_because": (
            "CANDIDATE_BUILT is gated on ultimate_book_include_candidate_book AND the "
            "candidate allowlist; adding a spec cannot arm it. But note the fail-open shape "
            "registry.py:130-134 has: an EMPTY allowlist means ALL candidates, so the edit is "
            "only inert while the deployed allowlist stays non-empty."),
    },
    "ny_index_momentum": {
        "table": "CANDIDATE_BUILT",
        "line": ('"ny_index_momentum": SleeveSpec("ny_index_momentum", '
                 'ny_index_momentum.generate, TF_M15, "index", ny_index_momentum.ON_SURFACE, '
                 'bar_count=521),'),
        "also_needs": ["a SLEEVE_EXIT_PROFILES entry (time_stop 20, no target — identical to "
                       "its sibling ny_crypto_momentum's)"],
        "live_safe_because": "as above",
    },
    "structural_retest": {
        "table": "CANDIDATE_BUILT",
        "line": ('"structural_retest": SleeveSpec("structural_retest", '
                 'structural_retest.generate, TF_M15, "index", structural_retest.ON_SURFACE, '
                 'bar_count=513),'),
        "also_needs": ["a SLEEVE_EXIT_PROFILES entry (2R target + time_stop 32)",
                       "the HTF phase question settled, because bar_count is not a free "
                       "parameter for this generator (module docstring)"],
        "live_safe_because": "as above",
    },
    "session_leadlag_genuine": {
        "table": "not yet proposable",
        "line": None,
        "also_needs": ["the cross-symbol feed in LIVE_WIRING_GAP",
                       "a SLEEVE_EXIT_PROFILES entry, which cannot express its per-leg "
                       "geometry as written"],
        "live_safe_because": (
            "n/a — a spec without the leader feed would register a generator that returns None "
            "on every bar. Fail-closed, but it would look like a sleeve that never fires rather "
            "than one that cannot."),
    },
}


# =====================================================================================
# the F7 A/B
# =====================================================================================

@contextlib.contextmanager
def authored_clock(*modules: str) -> Iterator[dict[str, str]]:
    """Temporarily restore the RAW-UTC hour reading a sleeve had before its F7 repair.

    Used to publish both bounds of the clock repair rather than only the corrected one, exactly
    as `EXIT_FRONTIER_V1` publishes both trail bounds. Swaps the module's `_hour` for the naive
    `t.hour` version and restores the original on exit **including on exception** — with a
    post-restore identity assertion, because a research sweep that left a production module
    monkeypatched would be a defect that surfaces in a different session.

    Only the three modules whose clock this programme has actually repaired are accepted —
    `structural_retest` and `session_leadlag` (Session AK, B950/B960) and `substrate` (Session AM,
    B1200). A general monkeypatch helper for arbitrary sleeve modules is a back door nobody needs,
    and the refusal is what keeps that true.
    """
    import importlib

    #: module -> the attribute whose pre-repair form was the raw UTC hour.
    allowed = {"structural_retest": "_hour",       # reads its own `_hour`
               "session_leadlag": "server_hour",   # reads the clock inline
               "substrate": "_session_hour"}       # B1200: `sub_mid_dn_revert`'s session=ny bucket
    bad = sorted(set(modules) - set(allowed))
    if bad:
        raise ValueError(
            f"authored_clock only covers the modules whose clock this programme repaired "
            f"({sorted(allowed)}); refused: {bad}")
    saved: dict[str, Any] = {}
    mods: dict[str, Any] = {}
    try:
        for name in modules:
            mod = importlib.import_module(f"src.components.ultimate_book.sleeves.{name}")
            mods[name] = mod
            attr = allowed[name]
            saved[name] = getattr(mod, attr)
            setattr(mod, attr, _authored_hour)
        yield {n: "raw UTC t.hour (pre-repair)" for n in modules}
    finally:
        for name, mod in mods.items():
            attr = allowed[name]
            setattr(mod, attr, saved[name])
            assert getattr(mod, attr) is saved[name]


def _authored_hour(t):
    """`structural_retest._hour` exactly as it stood before B950 — raw UTC, no conversion."""
    if t is None:
        return None
    if hasattr(t, "hour"):
        return t.hour
    s = str(t)
    return int(s[11:13]) if len(s) >= 13 else None


TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}

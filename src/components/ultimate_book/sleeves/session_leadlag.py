"""session_leadlag.py — the generator for `session_leadlag_genuine`, built at last (Session AK, B960).

WHAT THIS CLOSES
----------------
`session_leadlag_genuine` has been REGISTERED and sizeable since wave 6 — `admission.py:267-277`,
`CLEAN4_REGISTRY`, conf 0.15, forward-validated at **+0.46 R on n=390** with corr +0.053 to the
book and additive on the vol-matched stress MC (Sharpe 0.1522 -> 0.1586) — and it has had **no
generator**, so it could be sized and could never fire. `FOURTH_REVIEW.md:143`/`:406` carries it
as a standing item; `AA_ESTATE_WALK_RESULT.md` §2.6 records it as *"the estate's only artifact
with no evidence of any kind reachable from this machine"* because it is absent even from the
cached daily-R streams.

WHY IT WAS NEVER BUILT, AND IT IS NOT AN OVERSIGHT
---------------------------------------------------
Every other sleeve in this package is a function of ONE symbol's own bars. This one is not: it
reads a **leader** instrument's impulse and trades a **follower**. The generator contract
(`registry.py:37`) hands a generator `(symbol, bars, ...)` plus at most ONE `aux_*` feed, which
`bar_provider` fills from *the same symbol* at a second timeframe (`vp_euidx`'s M1 volume
profile is the only user). **There is no cross-symbol channel in the generation path at all** —
so wiring this sleeve was never a one-line registry edit; it needs a feed the engine does not
have. That is stated here rather than discovered again, and the exact plumbing it would need is
in `research_infra/walkforward/supply.py` -> `LIVE_WIRING_GAP`.

The generator therefore takes the leader feed as an explicit keyword and **returns None when it
is absent**. That makes it live-safe by construction: if this module were ever registered before
the engine can supply leaders, it emits nothing rather than something wrong.

THE MECHANISM, VERBATIM FROM THE RESEARCH THAT SELECTED IT
-----------------------------------------------------------
Source of truth is `KB6_session_stacks.py:77-88` (`gen_session_leadlag_genuine`, the DEPLOYABLE
subset) driving `KB5_leadlag_subh4.py:145-185` (`mine_pair`). Both are in the repo. The four legs
are the `LL_FWD` table at `KB6_session_stacks.py:52-58` verbatim — the null-cleared genuine
cross-asset LEADs where the leader carries the edge (leader-adds-dR > 0.25) and both forward
years are positive. The deep-train JPY-cross legs (`LL_FX_CORE`) are **excluded on purpose**: at
27-31 % win they injected the broad sleeve's fat 1.5x stress tail and cost 22 points of stress
pass-rate. The ETH leg is excluded as a crypto-sleeve double count.

Per leg, at the close of M15 bar `i` on the shared grid:

  1. LEADER IMPULSE: `z` = the leader's cumulative log return over `look` CLOSED M15 bars,
     z-scored against a TRAILING window of `VOLWIN` such sums ending at `i-1` (no lookahead).
     Fire only when `|z| >= zthr`.
  2. SESSION GATE on the decision bar's hour.
  3. DIRECTION: `sign(z) * relsign`, then negated for a `reversion` leg.
  4. STOP = `0.5 * ATR14(follower, i)`; the R unit.
  5. GEOMETRY: `T2.0` -> target `2.0 * ATR` (i.e. **4x the stop**, because the stop is half an
     ATR and the target is two whole ones — they are separately scaled in `mine_pair`, which is
     easy to misread); `TRAIL` -> no target, arm at `2 x stop`, gap `1 x stop`.
  6. Entry at the follower's close on the SAME timestamp (both bars closed -> same-close
     decision, no lookahead).

TWO PLACES THIS DEPARTS FROM `mine_pair`, BOTH DELIBERATE AND BOTH STATED
--------------------------------------------------------------------------
* **The session gate is on the BROKER SERVER clock.** `KB5_leadlag_subh4._session_ok` (`:117-125`)
  reads `ts.hour` off the research CSV archive, whose stamps are broker server wall clock — so
  `ny_open = 13..16` is a *server* window, and `_session_ok`'s own comment ("winter UTC") is
  wrong about its own data. Comparing it to the live feed's true UTC is finding F7 exactly, and
  it is what `_server_clock` exists to prevent. Built correct here; the as-authored UTC reading
  is available for the A/B through `walkforward.supply.authored_clock`, and both are published.
* **`min_gap` is NOT enforced here.** `mine_pair` refuses a trade within 4 follower bars of the
  previous one, which is per-series state. A generator that remembered its own last fire would
  not be a pure function of the decision bar, and every leak-freedom claim in this package rests
  on generators being exactly that. Live the equivalent constraint is stronger and already
  enforced downstream — `same_symbol_lifecycle_v4` allows one position per broker symbol — so
  the research proxy belongs in the driver. It is applied there, declared, and both counts are
  published.

Leak-free: every quantity is at index <= i on both series, and the leader's z-score window ends
at `i-1`. Offline and pure: no broker module, no socket, no order.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_hour
from .spot_choice import ask, bar_id

#: Trailing window of cumulative-return sums the leader impulse is z-scored against.
#: `KB5_leadlag_subh4.leader_signal(..., volwin=200)`.
VOLWIN = 200
#: `mine_pair(..., maxbars=64)` — 64 M15 bars = a 16 h forward horizon.
MAXBARS = 64
#: `mine_pair`: `stop = 0.5 * atr` on the FOLLOWER's own M15 ATR14.
STOP_ATR_MULT = 0.5
#: `mine_pair`: `min_gap=4` follower bars between consecutive fires. Applied by the driver, not
#: here — see the module docstring.
MIN_GAP_BARS = 4
#: atr14 needs `i >= 14`; `mine_pair` requires `i >= 14` for the same reason.
MIN_BARS = 15


@dataclass(frozen=True)
class Leg:
    """One (leader -> follower) hypothesis, verbatim from `KB6_session_stacks.py:52-58`."""

    leader: str
    follower: str
    relsign: int
    look: int
    zthr: float
    thesis: str          # "momentum" | "reversion"
    geom: str            # "T2.0" | "TRAIL"
    session: str         # "ny_open" | "london_ny"
    note: str = ""


#: The four `LL_FWD` legs, in the declared order. This ORDER is load-bearing: `AUDJPY` is the
#: follower of two legs, so when both qualify on one bar the first declared wins, and that has
#: to be a fixed property of the table rather than of dict iteration.
LEGS: tuple[Leg, ...] = (
    Leg("USDJPY", "AUDJPY", +1, 8, 2.5, "momentum", "T2.0", "london_ny",
        "+0.55, leader adds +0.77"),
)

SLEEVE = "session_leadlag_genuine"

#: The registry surface is six symbols (`admission.py:269`) and only three of them are FOLLOWERS.
#: `US30_cash` is a leader, and `SPX500`/`NAS100` appear in no leg at all — the same
#: authored-universe-vs-tradeable-universe naming collision AA §3.2 measured on four other
#: sleeves, reproduced here so nobody reads six symbols as six tradeable legs.
FOLLOWERS: tuple[str, ...] = tuple(dict.fromkeys(l.follower for l in LEGS))
LEADERS: tuple[str, ...] = tuple(dict.fromkeys(l.leader for l in LEGS))
ON_SURFACE: tuple[str, ...] = FOLLOWERS

_LEGS_BY_FOLLOWER: dict[str, tuple[Leg, ...]] = {
    f: tuple(l for l in LEGS if l.follower == f) for f in FOLLOWERS
}



_SESSION_WINDOW = {
    "all": "any server hour",
    "london_open": "7 <= server hour < 10",
    "ny_open": "13 <= server hour < 16",
    "ny_session": "13 <= server hour < 21",
    "london_ny": "7 <= server hour < 16",
    "asia": "0 <= server hour < 7",
}

def session_ok(server_h: Optional[int], session: str) -> bool:
    """`KB5_leadlag_subh4._session_ok` (`:117-125`), on the SERVER hour. None fails closed."""
    if server_h is None:
        return False
    if session == "all":
        return True
    if session == "london_open":
        return 7 <= server_h < 10
    if session == "ny_open":
        return 13 <= server_h < 16
    if session == "ny_session":
        return 13 <= server_h < 21
    if session == "london_ny":
        return 7 <= server_h < 16
    if session == "asia":
        return 0 <= server_h < 7
    return False


class LeaderImpulse:
    """The leader's z-scored cumulative log return on the M15 grid, memoised per `look`.

    A faithful port of `KB5_leadlag_subh4.leader_signal` (`:100-115`), including its exact
    z-scoring convention: the mean and the **population** standard deviation of the `VOLWIN`
    cumulative sums at indices `[i-VOLWIN, i)` — i.e. strictly before `i`, which is what makes
    it leak-free. A sample standard deviation would give a systematically smaller z and let more
    trades through the `zthr` gate, so the divisor is not a detail.

    Built once per leader series by the caller and handed to `generate` as a feed, which is what
    keeps the generator itself a pure function of the decision bar.
    """

    __slots__ = ("_times", "_lr", "_z")

    def __init__(self, times: Sequence, closes: Sequence[float]) -> None:
        if len(times) != len(closes):
            raise ValueError(
                f"leader times/closes length mismatch: {len(times)} != {len(closes)}")
        self._times = list(times)
        n = len(closes)
        lr = [0.0] * n
        for i in range(1, n):
            c0, c1 = closes[i - 1], closes[i]
            lr[i] = math.log(c1 / c0) if (c0 > 0 and c1 > 0) else 0.0
        self._lr = lr
        self._z: dict[int, dict] = {}

    def _build(self, look: int) -> dict:
        lr = self._lr
        n = len(lr)
        out: dict = {}
        if n < look + VOLWIN + 5:
            return out
        cum = [0.0] * n
        for i in range(look, n):
            cum[i] = sum(lr[i - look + 1:i + 1])
        for i in range(look + VOLWIN, n):
            win = cum[i - VOLWIN:i]
            m = sum(win) / len(win)
            var = sum((x - m) ** 2 for x in win) / len(win)
            if var > 0:
                out[self._times[i]] = (cum[i] - m) / math.sqrt(var)
        return out

    def z(self, ts, look: int) -> Optional[float]:
        table = self._z.get(look)
        if table is None:
            table = self._z[look] = self._build(look)
        return table.get(ts)

    def covers(self, ts) -> bool:
        """True when `ts` is inside the leader's own bar span (used for coverage reporting)."""
        if not self._times:
            return False
        j = bisect.bisect_left(self._times, ts)
        return j < len(self._times) and self._times[j] == ts


def target_dist_for(geom: str, atr: float, stop_dist: float) -> Optional[float]:
    """`mine_pair`'s geometry, restated once so no caller re-derives it wrongly.

    `T2.0` is `target_dist = tmult * a` where `a` is the ATR and the stop is `0.5 * a`, so the
    target sits at **4 R**, not 2. `TRAIL` carries no target.
    """
    if geom == "TRAIL":
        return None
    if geom.startswith("T"):
        return float(geom[1:]) * atr
    raise ValueError(f"unknown leadlag geometry {geom!r}")


def trail_for(geom: str, stop_dist: float) -> tuple[Optional[float], Optional[float]]:
    """`(trail_arm, trail_gap)` in PRICE for a `TRAIL` leg, else `(None, None)`.

    `mine_pair`: `trail_arm=2*stop, trail_gap=1*stop`.
    """
    if geom != "TRAIL":
        return None, None
    return 2.0 * stop_dist, 1.0 * stop_dist


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None,
             leader_feeds: Optional[Mapping[str, LeaderImpulse]] = None,
             **_) -> Optional[TradeIntent]:
    """Emit a genuine-cross-asset-lead TradeIntent on the latest closed M15 bar, else None.

    `leader_feeds` maps leader symbol -> `LeaderImpulse`. Absent or empty feeds stay a
    process-alive return: this sleeve cannot be evaluated without the leader it is named for.
    Session window, missing feed, and the z threshold are Choices.
    """
    legs = _LEGS_BY_FOLLOWER.get(symbol)
    if not legs or not bars or not leader_feeds:
        return None
    i = len(bars) - 1
    t = bar_time if bar_time is not None else (
        bar_times[i] if bar_times and len(bar_times) == len(bars) else None)
    if t is None:
        return None
    h = server_hour(t)
    if h is None:
        return None
    if i < 14:
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None
    sd = STOP_ATR_MULT * a
    if sd <= 0:
        return None
    spots = {
        "warmup_short": {
            "condition": f"latest bar index {i} is below {MIN_BARS}",
            "measured": i < MIN_BARS,
        },
    }
    packed = []
    for leg in legs:
        key = f"{leg.leader}|{leg.follower}|{leg.look}|{leg.geom}|{leg.session}"
        bounds = _SESSION_WINDOW.get(leg.session, "unlisted session")
        feed = leader_feeds.get(leg.leader)
        z = None if feed is None else feed.z(t, leg.look)
        spots[key + "|session"] = {
            "condition": f"server hour {h} is outside the {leg.session} window ({bounds})",
            "measured": not session_ok(h, leg.session),
        }
        spots[key + "|feed"] = {
            "condition": f"leader feed for {leg.leader} is absent",
            "measured": feed is None,
        }
        spots[key + "|impulse"] = {
            "condition": (
                f"leader impulse z for {leg.leader} look {leg.look} is missing "
                f"or its absolute value is below {leg.zthr}"
            ),
            "measured": z is None or abs(z) < leg.zthr,
        }
        packed.append((leg, key, z))
    sides = ask(
        sleeve=SLEEVE,
        symbol=symbol,
        bar_id=bar_id(decision_day, i, bar_time, bar_times),
        spots=spots,
    )
    if sides.get("warmup_short") != "condition_false":
        return None
    for leg, key, z in packed:
        sess = sides.get(key + "|session")
        feed_side = sides.get(key + "|feed")
        impulse = sides.get(key + "|impulse")
        if sess is None or feed_side is None or impulse is None:
            return None
        if sess == "condition_true" or feed_side == "condition_true" or impulse == "condition_true":
            continue
        if z is None:
            continue
        base = (1 if z > 0 else -1) * leg.relsign
        d = base if leg.thesis == "momentum" else -base
        return TradeIntent(
            sleeve=SLEEVE, symbol=symbol, direction=d, decision_day=decision_day,
            stop_dist=sd, target_dist=target_dist_for(leg.geom, a, sd),
            ll_impulse=f"{leg.leader}->{leg.follower}@{leg.geom}",
            decision_hour=h,
        )
    return None

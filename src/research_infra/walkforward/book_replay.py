"""The merged book: shared equity, the production sizer, the governor, the interaction.

WHY THIS EXISTS
---------------
Every economic number this programme has produced about the `ultimate_book` family is a
**per-sleeve** number. `SURVIVOR_BOOK_V1.json` is a table of per-sleeve mean R.
`W_MX_PILOT.json` is twelve independent verdicts. `scripts/recost_w7_validation.py` builds a
day matrix and sums the sleeve columns (`:904, :924-925`) with no governor at all — no soft
stop, no gross cap, no de-risk multiplier, no correlated-unit bucketing, and its Kelly bins
re-declared as literals rather than imported.

Nothing anywhere runs the sleeves **together**, through the sizer that actually sizes them,
against one equity curve. That is the owner's question and this module is the answer to it.

**The interaction cuts both ways, which is the whole point.**

- `book_engine.py:452-453` (DF-1) exists because a sleeve that generates but cannot be sized
  still inflates the Kelly-lite conviction count and over-sizes every *other* unit that day.
  The Kelly bins are step functions (`admission.py:931`), so one extra distinct sleeve
  crossing a bin edge is a step change in every real unit's size.
- Correlated sleeves firing together consume one 4% gross-open-risk cap
  (`admission.py:1361`), and they collide on the placement gates — two sleeves that want the
  same broker symbol on the same day produce **one** position, not two
  (`book_owner.py:1780-1807`).
- A book of individually-mediocre uncorrelated sleeves can beat a book of two good
  correlated ones, and only a shared-equity walk can show which.

None of that is visible in a sum of per-sleeve means, and none of it is arithmetic you can
do on a table.

WHAT IS PRODUCTION AND WHAT IS THIS MODULE'S
---------------------------------------------
Production, called and never reimplemented:

    sizing + governor   `replay_policy.sleeve_book.SleeveBookPolicy.decide`
                        -> `bridge.evaluate_vnext_ultimate_book_admission`
                        -> `admission.admit_and_size` / `size_correlated_units`
                        -> `admission.evaluate_governor`
    cluster key         `admission.cluster_of`
    registry            `admission.effective_registry`
    reactive de-risk    `admission.compute_stress_derisk_state`
    reset window        `governor_state.GovernorStateBuilder.reset_window_date`
    cost                `src.costs.cost_r`

This module owns exactly three things, and each is a *fact the policy requires its caller to
supply* (`sleeve_book.ADAPTER_DIVERGENCES` names them): the equity walk, the open-position
book, and the subset of live placement gates that are evaluable offline.

THE CANDIDATE -> UNIT MAPPING IS READ, NOT GUESSED
---------------------------------------------------
`size_correlated_units` buckets intents by `(decision_day, cluster)` and emits units in
`sorted(buckets.items())` order (`admission.py:1180`); `_enforce_gross_open_risk_cap`
returns "asdict() dicts in the ORIGINAL unit order" (`:1323`). So unit *i* corresponds to
the *i*-th sorted `(decision_day, cluster)` key. This module reconstructs those keys with
the production `cluster_of` and then **asserts** that the emitted units agree on cluster and
`n_trades` at every index. A disagreement raises rather than being papered over — the
alternative is silently attributing one unit's risk to another sleeve's trades.

FIVE DIVERGENCES FROM LIVE, STATED HERE RATHER THAN IN A FOOTNOTE
-------------------------------------------------------------------
1. **Floating P&L is unknown, and the two models are NOT a bracket.** The trade records
   carry a final R and no path, so equity between entry and exit cannot be marked. Two
   models are run — `floating="none"` (equity = realised balance) and
   `floating="worst_case"` (every open position marked at its stop) — but an adversarial
   refuter measured that the pessimistic one can size **4.0000×** LARGER: marking equity
   down pushes `gain = (equity - dd_ref)/dd_ref` back below `profit_target_pct`, which
   REMOVES the OPS-03 profit-target de-risk (`admission.py:1353-1357`, `cap_mult *= 0.25`).
   The governor is non-monotone in equity by design, so "worst case" is worst for drawdown
   and not worst for size. Both are reported, neither is called a bound, and
   `diagnostics.floating_non_monotone` records when the pessimistic model produced the
   larger book.
2. **Cycles are candidate instants, not every bar close.** A bar close with no candidate
   produces no intent and therefore no unit, so the decision path is unchanged; only the
   number of no-op `decide()` calls differs.
3. **Nine placement gates are not evaluable offline** and every one is listed in
   `NOT_APPLIED_GATES` — computed as the complement of `APPLIED_GATES` against
   `sleeve_book.PLACEMENT_GATES` rather than hand-listed, because an earlier revision of
   this docstring said "five" while the computed tuple held nine. All nine are placement
   gates and can only REDUCE the realised trade count. Two size-REDUCING paths outside that
   list are also absent: the AI-companion risk multiplier (`book_owner.py:1837`,
   `control_state.py:508`, rejected above 1.0) and lot normalisation
   (`execution.py:2345,3384-3392` — `math.floor` plus a terminal `below_min_lot` shed). All
   omissions therefore run one way: this book is optimistic against live, never pessimistic.
4. **Entry is the decision bar's close** and the fill is `primitives.simulate_detail`'s, so
   slippage beyond the cost model's own term is not modelled.
5. **Sizing is off realized balance**, matching `execution.py:3360`
   (`risk_amount = account_balance * risk_pct/100`) rather than equity.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
import tempfile
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from src.components.ultimate_book.admission import (
    cluster_of,
    compute_stress_derisk_state,
    effective_registry,
)
from src.components.ultimate_book.governor_state import GovernorStateBuilder
from src.research_infra.replay_policy.core import AccountDayState, PolicyCandidate
from src.research_infra.replay_policy.sleeve_book import PLACEMENT_GATES, SleeveBookPolicy

__all__ = [
    "BookTrade",
    "BookConfig",
    "BookResult",
    "replay_book",
    "book_daily_series",
    "book_stats",
]

SCHEMA = "gtos.walkforward.book_replay.v1"

#: The gates this module DOES apply, with the live line that owns each.
APPLIED_GATES: dict[str, str] = {
    "already_placed_this_bar": "book_owner.py:1678 — (sleeve, symbol, decision_bar_iso) once",
    "already_placed_today": "book_owner.py:1683-1693 — (sleeve, symbol, decision_day) once",
    "cluster_unit_already_placed_today": (
        "book_owner.py:1694-1704 — OFF live (agent_config.yaml:1373 "
        "ultimate_book_one_unit_per_cluster_per_day: false); applied only when enabled"),
    "sleeve_already_holds_symbol": "book_owner.py:1755-1759",
    "same_broker_symbol_already_placed_this_cycle": "book_owner.py:1769-1779",
    "same_broker_symbol_open_position_lifecycle_guard": "book_owner.py:1780-1807",
}
NOT_APPLIED_GATES: tuple[str, ...] = tuple(
    g for g in PLACEMENT_GATES if g not in APPLIED_GATES
)


@dataclass(frozen=True)
class BookTrade:
    """One candidate the book may or may not take, with its outcome already labelled.

    `r_net` is realised R **after** broker-true cost. The book decides whether to take the
    trade and at what risk; it cannot change the trade's R, which is a property of the price
    path and the geometry.
    """

    sleeve: str
    symbol: str                 # BROKER symbol
    symbol_canonical: str
    entry_utc: dt.datetime
    exit_utc: dt.datetime
    direction: int
    stop_dist: float
    entry_price: float
    r_net: float
    decision_day: str
    decision_bar_iso: str | None = None
    timeframe: int | None = None
    intra_size: float = 1.0
    ll_impulse: str | None = None
    decision_hour: int | None = None
    vp_loc: str | None = None
    features: dict[str, Any] = field(default_factory=dict)

    def candidate(self) -> PolicyCandidate:
        return PolicyCandidate(
            sleeve=self.sleeve,
            # CANONICAL, because that is what the live intent carries
            # (`book_engine.py:474`: "meta + intent.symbol stay canonical for placement").
            symbol=self.symbol_canonical,
            direction=self.direction,
            decision_day=self.decision_day,
            stop_dist=self.stop_dist,
            intra_size=self.intra_size,
            entry_ref=self.entry_price,
            decision_bar_iso=self.decision_bar_iso,
            timeframe=self.timeframe,
            ll_impulse=self.ll_impulse,
            decision_hour=self.decision_hour,
            vp_loc=self.vp_loc,
            features=dict(self.features),
        )


@dataclass(frozen=True)
class BookConfig:
    """Everything about the run that is not the trades."""

    #: The `gtos_vnext_runtime` block. Passed through to `SleeveBookPolicy` unmodified.
    runtime: dict
    sleeves: tuple[str, ...]
    label: str = "book"
    starting_balance: float = 100_000.0
    #: "none" = equity is the realized balance; "worst_case" = every open position marked at
    #: its stop. The two bracket the unknown floating P&L. See divergence 1.
    floating: str = "none"
    account_side: str = "A"
    #: The account's DAILY-LOSS RESET calendar. FTMO resets at 00:00 CE(S)T
    #: (`config/profiles/operator_profile.yaml:104`), which is NOT its MT5 server clock.
    reset_rule: str | None = "europe_prague"
    #: Static fallback for the reset window when `reset_rule` cannot be resolved.
    reset_offset_hours: float = 3.0
    #: The MT5 SERVER whose wall clock keys the closed-deal day for the reactive de-risk
    #: overlay. A THIRD clock, and it is not the reset calendar: `book_engine.py:165-168`
    #: feeds `compute_stress_derisk_state` the broker's own detected offset, while the
    #: governor's reset window uses `reset_rule`. For FTMO-Server3 they differ by an hour
    #: all year (server +2/+3 = New York + 7; Prague +1/+2). Using one for the other puts
    #: the ladder's day boundary in the wrong place.
    broker_clock_server: str | None = "FTMO-Server3"
    #: Feed the production reactive de-risk overlay from this run's own closed trades.
    stress_derisk_from_own_history: bool = True
    #: Feed the running per-day distinct-sleeve conviction count from this run's own history.
    running_conviction: bool = True

    def __post_init__(self) -> None:
        if self.floating not in ("none", "worst_case"):
            raise ValueError(f"floating must be 'none' or 'worst_case', got {self.floating!r}")
        if self.starting_balance <= 0:
            raise ValueError("starting_balance must be > 0")


@dataclass
class BookResult:
    config: BookConfig
    #: (utc_instant, realized_balance) after every settlement.
    equity_curve: list[tuple[dt.datetime, float]] = field(default_factory=list)
    #: One row per PLACED trade.
    placed: list[dict] = field(default_factory=list)
    #: Counts of why candidates did not become positions.
    rejections: dict[str, int] = field(default_factory=dict)
    n_candidates: int = 0
    n_cycles: int = 0
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def final_balance(self) -> float:
        return self.equity_curve[-1][1] if self.equity_curve else self.config.starting_balance

    def as_dict(self) -> dict[str, Any]:
        st = book_stats(self)
        return {
            "schema": SCHEMA,
            "label": self.config.label,
            "sleeves": list(self.config.sleeves),
            "floating_model": self.config.floating,
            "n_candidates": self.n_candidates,
            "n_cycles": self.n_cycles,
            "n_placed": len(self.placed),
            "rejections": dict(sorted(self.rejections.items(), key=lambda kv: -kv[1])),
            "stats": st,
            "diagnostics": self.diagnostics,
            "placement_gates_applied": sorted(APPLIED_GATES),
            "placement_gates_not_applied": list(NOT_APPLIED_GATES),
        }


# =====================================================================================


def _pnl_pct_of_balance(risk_pct_per_trade: float, r_net: float) -> float:
    """The book's own arithmetic: risk fraction x realised R.

    `execution.py:3360` computes `risk_amount = account_balance * (risk_pct/100)` where
    `risk_pct` is `risk_pct_per_trade * 100` (`execution_packets.py:215`), so the currency
    P&L of a trade is `balance * risk_pct_per_trade * R`.
    """
    return float(risk_pct_per_trade) * float(r_net)


def replay_book(trades: Iterable[BookTrade], cfg: BookConfig) -> BookResult:
    """Walk one shared equity curve through the production sizer.

    Events are ordered `(instant, kind)` with settlements ahead of entries at the same
    instant, so a position that closes on the bar another opens has already released its
    gross-risk headroom — which is what live sees, because the close is a broker event and
    the open is a decision taken after it.
    """
    sleeves = set(cfg.sleeves)
    rows = [t for t in trades if t.sleeve in sleeves]
    res = BookResult(config=cfg, n_candidates=len(rows))
    if not rows:
        res.equity_curve = [(dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
                             cfg.starting_balance)]
        return res

    registry = _registry_for(cfg.runtime)
    # strict_config=True, because `sleeve_book.py:193-202` says why it exists: the bridge
    # defaults differ from live on the two dial-deciding keys, and "a replay that fell back
    # to them would size a different book". Hardcoding False silently accepted a config
    # block with every dial key missing and sized `metals_core` 37.5% smaller with an
    # all-`None` provenance record instead of refusing.
    policy = SleeveBookPolicy(cfg.runtime, account=cfg.account_side, strict_config=True)
    gsb = GovernorStateBuilder(
        tempfile.mkdtemp(prefix="gtos_book_replay_"),
        namespace=cfg.label,
        static_initial_balance=cfg.starting_balance,
        daily_reset_offset_hours=cfg.reset_offset_hours,
        reset_rule=cfg.reset_rule,
    )
    server_rule = None
    if cfg.broker_clock_server:
        from src.utils.broker_clock import resolve_rule  # noqa: PLC0415

        server_rule = resolve_rule(cfg.broker_clock_server)
    one_per_cluster = bool(cfg.runtime.get("ultimate_book_one_unit_per_cluster_per_day", False))
    exempt = set(cfg.runtime.get("ultimate_book_cluster_cap_exempt_clusters") or ())

    by_instant: dict[dt.datetime, list[BookTrade]] = {}
    for t in rows:
        by_instant.setdefault(t.entry_utc, []).append(t)
    # Entry instants, in order. Settlements are not separate events: `_settle_through(now)`
    # runs first inside each cycle, which is what live sees too — `manage_open_positions`
    # runs before `run_cycle` on every tick, so a close at the decision bar has already
    # released its gross-risk headroom by the time the decision is taken. (An earlier
    # revision built `(instant, kind)` tuples with a `kind=0` settle event that was never
    # constructed; the machinery was dead and the docstring described it as live.)
    cycles: list[dt.datetime] = sorted(by_instant)

    balance = cfg.starting_balance
    high_water = cfg.starting_balance
    res.equity_curve.append((cycles[0], balance))

    open_positions: list[dict] = []          # {exit_utc, risk_pct, r_net, sleeve, symbol, ...}
    placed_bar: set = set()
    placed_day: set = set()
    placed_cluster_day: dict = {}
    #: reset-window key -> the balance at the instant the window OPENED. Not the balance at
    #: the first cycle inside it: `_settle_through` runs first, so anchoring on the
    #: post-settlement balance made `realized_today_pct` identically 0.0 on the first cycle
    #: of every window and left the soft daily stop blind to any loss realised earlier in
    #: that window. Live anchors on the window BOUNDARY and subtracts realised closed P&L
    #: since it (`governor_state.py:172-212`).
    window_open_balance: dict[str, float] = {}
    day_sleeves_running: dict[str, set] = {}
    closed_deals: list[dict] = []            # for `compute_stress_derisk_state`
    rej: dict[str, int] = {}
    straddles = 0
    cap_bound_cycles = 0

    def _server_offset_h(now: dt.datetime) -> float:
        """The MT5 SERVER offset, which keys the closed-deal day for the de-risk overlay.

        Not the reset-window offset. `book_engine.py:165-168` feeds
        `compute_stress_derisk_state` the broker's own detected offset and falls back to
        `governor_daily_reset_offset_hours` only when it cannot be read; the governor's
        reset window meanwhile uses `reset_rule`. For FTMO-Server3 the two differ by an
        hour all year — server +2/+3 (New York + 7), Prague +1/+2.
        """
        if server_rule is None:
            return float(cfg.reset_offset_hours)
        from src.utils.broker_clock import offset_seconds_at_utc  # noqa: PLC0415

        return offset_seconds_at_utc(now, server_rule) / 3600.0

    def _mark_window(now: dt.datetime) -> None:
        """Record the window-open balance BEFORE anything settles into the new window."""
        window_open_balance.setdefault(gsb.reset_window_date(now), balance)

    def _settle_through(now: dt.datetime) -> None:
        nonlocal balance, high_water
        due = [p for p in open_positions if p["exit_utc"] <= now]
        if not due:
            return
        for p in sorted(due, key=lambda q: q["exit_utc"]):
            # Charged on the balance AT PLACEMENT, matching `execution.py:3360`
            # (`risk_amount = account_balance * risk_pct/100`, evaluated when the order is
            # sent). Charging it on the settlement balance made the P&L depend on what else
            # happened to close during the hold — a path dependence live does not have — and
            # silently broke `book_daily_series`'s documented `risk_pct * R` identity.
            _mark_window(p["exit_utc"])
            pnl = p["balance_at_entry"] * _pnl_pct_of_balance(p["risk_pct"], p["r_net"])
            balance += pnl
            high_water = max(high_water, balance)
            p["pnl"] = pnl
            p["balance_after"] = balance
            closed_deals.append({
                "sleeve": p["sleeve"],
                "profit": pnl,
                # A BROKER-SERVER epoch, not a UTC one. `compute_stress_derisk_state`
                # (`admission.py:446`) decodes `time` with `fromtimestamp(t, utc).date()` and
                # its docstring says so — "the broker-server deal epoch (server wall clock as
                # a unix ts; utcfromtimestamp -> the server-local datetime)" — while `today`
                # on the next line is `(now_utc + offset_hours).date()`. A true UTC epoch
                # would put the two sides an offset apart, so every deal in the last hours of
                # a UTC day would be attributed to the wrong server-day and the leak-free
                # "today excluded" cut would slice in the wrong place. Server wall clock =
                # UTC + offset, so the server epoch is the UTC instant shifted forward.
                "time": (p["exit_utc"]
                         + dt.timedelta(hours=_server_offset_h(p["exit_utc"]))).timestamp(),
            })
            res.equity_curve.append((p["exit_utc"], balance))
        open_positions[:] = [p for p in open_positions if p["exit_utc"] > now]

    _mark_window(cycles[0])
    for now in cycles:
        _mark_window(now)
        _settle_through(now)
        batch = by_instant[now]
        res.n_cycles += 1

        # ---- placement gates that precede sizing ---------------------------------------
        # Live applies these AFTER admission (`book_owner.py:1637+`), i.e. a gated intent
        # still counted toward the day's Kelly conviction. Reproduced: the gates below run
        # after `decide()`, not before it. Only the per-cycle broker-symbol collision has to
        # be resolved inside the loop, and it is.
        cands = [t.candidate() for t in batch]

        # ---- account facts the policy requires its caller to supply ---------------------
        # Live's `_open_risk_pct` (`book_engine.py:632-665`) is worst-case-stop risk over
        # CURRENT equity. Each position's `risk_pct` is a fraction of the balance it was
        # placed on, so rescaling by `balance_at_entry / balance` puts it on the denominator
        # live uses. Summing the raw fractions made the 4% gross cap bind late in a
        # drawdown and early in a run-up.
        open_risk_pct = (
            math.fsum(p["risk_pct"] * p["balance_at_entry"] for p in open_positions) / balance
            if balance > 0 else 0.0
        )
        equity = balance
        if cfg.floating == "worst_case":
            equity = balance - balance * open_risk_pct
        win = gsb.reset_window_date(now)
        anchor = window_open_balance.get(win, balance)
        # Both sides of the governor's view move together under `worst_case`, as they do
        # live (`governor_state.py:271` derives `realized_today_pct` from the same equity).
        # Marking equity down while leaving `realized_today_pct` on the realised balance
        # made the pessimistic model only half-pessimistic.
        realized_today_pct = ((equity - anchor) / anchor) if anchor > 0 else 0.0

        cycle: dict[str, Any] = {}
        if cfg.stress_derisk_from_own_history:
            cycle["stress_state"] = compute_stress_derisk_state(
                closed_deals, now, offset_hours=_server_offset_h(now))
        if cfg.running_conviction:
            # The live `RunningConvictionLedger.update_and_count`
            # (`running_conviction_state.py:60-82`) UNIONS THIS CYCLE'S firing sleeves into
            # the persisted set FIRST and returns the count INCLUDING them; `book_engine.py`
            # passes that straight to the sizer, which takes
            # `na = max(per_cycle, running)` (`admission.py:1208-1210`).
            #
            # Updating after `decide()` — as this did — made the override one cycle stale,
            # so on every cycle after the first on a multi-sleeve day the running count was
            # short by this cycle's own sleeves. Measured by an adversarial refuter: `crypto`
            # on cycle 2 sized at 0.012716 against live's 0.016847, a ratio of 0.7548. That
            # is a 24.5% systematic under-size on exactly the interaction this module exists
            # to measure. It is not look-ahead: the sleeves being counted are firing NOW.
            for c in cands:
                day_sleeves_running.setdefault(c.decision_day, set()).add(c.sleeve)
            cycle["n_active_override"] = {
                d: len(s) for d, s in day_sleeves_running.items()
            }

        state = AccountDayState(
            equity=equity,
            high_water=max(high_water, equity),
            realized_today_pct=realized_today_pct,
            open_risk_pct=open_risk_pct,
            max_dd_reference_equity=float(cfg.starting_balance),
            account=cfg.account_side,
            namespace=cfg.label,
            cycle=cycle,
        )
        decision = policy.decide(cands, state)

        if not cfg.running_conviction:
            for c in cands:
                day_sleeves_running.setdefault(c.decision_day, set()).add(c.sleeve)

        if not decision.new_entries_allowed:
            # The bridge overwrites the top-level reason with the GATE reason whenever a gate
            # blocks (`bridge.py:480-506`), and `SleeveBookPolicy.decide` catches every
            # exception into `adapter_failed_closed:` (`sleeve_book.py:296-302`). Filing all
            # three under `governor:` made a broken dial read as "the governor braked".
            diag = dict(decision.diagnostics or {})
            auth = dict(decision.authority or {})
            if str(decision.reason).startswith("adapter_failed_closed"):
                why = f"adapter:{decision.reason}"
            elif diag.get("sizing_refused_before_governor"):
                why = f"sizing_refused:{decision.reason}"
            elif decision.governor is None:
                why = f"gate:{auth.get('bridge_reason') or decision.reason}"
            else:
                why = f"governor:{decision.reason}"
            _bump(rej, why, len(batch))
            continue

        sized_cands = _survivors(cands, cfg.runtime)
        unit_by_key = _map_units(decision.units, sized_cands, registry)
        if unit_by_key is None:
            raise RuntimeError(
                "unit mapping failed: the emitted units do not agree with the "
                "(decision_day, cluster) buckets the sizer documents at admission.py:1180, "
                "even after applying the sizer's own pre-count filters "
                "(filter_w7_dropped_symbols, precount_intent_filter). Refusing to attribute "
                f"risk by guess. cycle={now.isoformat()} "
                f"units={[(u.cluster, u.n_trades) for u in decision.units]} "
                f"buckets={sorted({(c.decision_day, cluster_of(c.sleeve, registry)) for c in sized_cands})}"
            )
        dropped_by_sizer = {id(c) for c in cands} - {id(c) for c in sized_cands}
        if len({c.decision_day for c in cands}) > 1:
            straddles += 1
        if any((u.reason or "") == "gross_risk_cap_would_exceed" for u in decision.units):
            cap_bound_cycles += 1

        cycle_symbols: set = set()
        for t, c in zip(batch, cands):
            if id(c) in dropped_by_sizer:
                # Dropped INSIDE the sizer by a production filter — W7 illiquid-leg removal
                # (`admission.py:1499`) or one of the pre-count DROPPING filters
                # (`:1126-1133`: VP acceptance, L5 learning GATE, A8 metals confluence, S1
                # damage quarantine). These are live behaviour, not harness behaviour.
                _bump(rej, "sizer_precount_filter_dropped_intent")
                continue
            key = (c.decision_day, cluster_of(c.sleeve, registry) or "__unknown__")
            unit = unit_by_key.get(key)
            if unit is None or not unit.sized or unit.risk_pct_per_trade <= 0.0:
                _bump(rej, f"unit:{unit.reason if unit else 'no_unit'}")
                continue
            if (t.sleeve, t.symbol, t.decision_bar_iso) in placed_bar:
                _bump(rej, "already_placed_this_bar")
                continue
            if (t.sleeve, t.symbol, t.decision_day) in placed_day:
                _bump(rej, "already_placed_today")
                continue
            if one_per_cluster and key[1] not in exempt:
                seen_bar = placed_cluster_day.get(key)
                if seen_bar is not None and seen_bar != t.decision_bar_iso:
                    _bump(rej, "cluster_unit_already_placed_today")
                    continue
            if any(p["sleeve"] == t.sleeve and p["symbol"] == t.symbol for p in open_positions):
                _bump(rej, "sleeve_already_holds_symbol")
                continue
            if t.symbol in cycle_symbols:
                _bump(rej, "same_broker_symbol_already_placed_this_cycle")
                continue
            if any(p["symbol"] == t.symbol for p in open_positions):
                # The single largest interaction between correlated sleeves: two sleeves that
                # want the same broker symbol produce ONE position, not two.
                _bump(rej, "same_broker_symbol_open_position_lifecycle_guard")
                continue

            cycle_symbols.add(t.symbol)
            placed_bar.add((t.sleeve, t.symbol, t.decision_bar_iso))
            placed_day.add((t.sleeve, t.symbol, t.decision_day))
            placed_cluster_day[key] = t.decision_bar_iso
            pos = {
                "sleeve": t.sleeve, "symbol": t.symbol, "entry_utc": now,
                "exit_utc": t.exit_utc, "risk_pct": float(unit.risk_pct_per_trade),
                "r_net": float(t.r_net), "unit_risk_pct": float(unit.unit_risk_pct),
                "cluster": key[1], "decision_day": c.decision_day,
                "confidence": float(unit.confidence), "tags": list(unit.tags),
                "balance_at_entry": balance,
                # The reactive de-risk state the policy was handed at this instant. Recorded
                # because without it a differential re-size against `admit_and_size` compares
                # two different books: the harness feeds a real ladder/co-loss state from its
                # own closed deals while a naive direct call gets the neutral default, and the
                # gap is exactly the ladder multiplier (0.80 at step 1).
                "stress_state": (
                    (int(cycle["stress_state"].consecutive_loss_days),
                     float(cycle["stress_state"].trailing_neg_frac))
                    if cycle.get("stress_state") is not None else None),
                "realized_today_pct": realized_today_pct,
                "open_risk_pct_at_entry": open_risk_pct,
            }
            open_positions.append(pos)
            res.placed.append(pos)

    # settle whatever is still open at the end of the record
    if open_positions:
        _settle_through(max(p["exit_utc"] for p in open_positions))

    res.rejections = rej
    res.diagnostics = {
        "starting_balance": cfg.starting_balance,
        "final_balance": balance,
        "high_water": high_water,
        "n_decision_day_straddle_cycles": straddles,
        "n_cycles_where_gross_cap_shed_a_unit": cap_bound_cycles,
        "n_intents_dropped_by_sizer_precount_filters": rej.get(
            "sizer_precount_filter_dropped_intent", 0),
        "reset_window_rule": cfg.reset_rule,
        "broker_clock_server": cfg.broker_clock_server,
        "policy": dict(policy.describe()),
    }
    return res


def _bump(d: dict, k: str, n: int = 1) -> None:
    d[k] = d.get(k, 0) + n


def _registry_for(runtime: dict) -> dict:
    from src.components.ultimate_book.book_engine import (  # noqa: PLC0415
        _candidate_book_sleeves,
        _market_expansion_sleeves,
    )

    return effective_registry(
        include_clean3=bool(runtime.get("ultimate_book_include_clean3", False)),
        include_clean4=bool(runtime.get("ultimate_book_include_clean4", False)),
        include_candidate_book=bool(runtime.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(runtime) or None,
        include_market_expansion_book=bool(
            runtime.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(runtime) or None,
    )


def _survivors(cands: Sequence[PolicyCandidate], runtime: dict) -> list[PolicyCandidate]:
    """The candidates that reach `size_correlated_units`' bucketing, per the PRODUCTION filters.

    `admit_and_size` drops intents in two places before any unit exists:
    `filter_w7_dropped_symbols` (`admission.py:1497-1500`, the W7 illiquid energy legs) and
    `precount_intent_filter` (`:1126-1133`, the VP-acceptance noise cut, the L5 learning
    GATE, the A8 metals confluence gate and the S1 symbol-damage quarantine). Rebuilding the
    bucket keys from the UNFILTERED candidate list therefore produced a key set the emitted
    units could not match, and `_map_units` — correctly — refused.

    Measured by an adversarial refuter: under the ACTUAL live dial
    (`ultimate_book_drop_w7_symbols: true` at `agent_config.yaml:1291`,
    `ultimate_book_metals_confluence_gate: true` at `:1315`) the harness raised on any
    candidate set containing `NATGAS_cash`/`HEATOIL_c` — carriers of `energy_agri`, an
    UNCONDITIONAL survivor sleeve — or an A8-failing metals intent. It could not run the
    live dial at all.

    Both filters are CALLED here, not reimplemented, with the same flags `admit_and_size`
    reads. Identity is preserved via `id()` because `TradeIntent` is frozen and equal
    intents would otherwise be indistinguishable.
    """
    from src.components.ultimate_book.admission import (  # noqa: PLC0415
        filter_w7_dropped_symbols,
        precount_intent_filter,
    )
    from src.research_infra.replay_policy.sleeve_book import _to_trade_intent  # noqa: PLC0415

    intents, by_id = [], {}
    for c in cands:
        it = _to_trade_intent(c)
        intents.append(it)
        by_id[id(it)] = c
    if bool(runtime.get("ultimate_book_drop_w7_symbols", False)):
        intents, _dropped = filter_w7_dropped_symbols(intents, enabled=True)
    intents = precount_intent_filter(
        intents,
        vp_acceptance=bool(runtime.get("ultimate_book_vp_acceptance", False)),
        learning_rerate=runtime.get("ultimate_book_learning_rerate") or None,
        metals_confluence_gate=bool(runtime.get("ultimate_book_metals_confluence_gate", False)),
        symbol_damage_guard=bool(runtime.get("ultimate_book_symbol_damage_guard", False)),
        symbol_damage_metrics=None,
    )
    return [by_id[id(it)] for it in intents if id(it) in by_id]


def _map_units(units: Sequence[Any], cands: Sequence[PolicyCandidate], registry: dict):
    """`(decision_day, cluster)` -> the unit the sizer emitted for it, or None on disagreement.

    `size_correlated_units` iterates `sorted(buckets.items())` (`admission.py:1180`) and the
    gross-risk cap preserves that order (`:1323`), so index *i* is the *i*-th sorted key.
    Verified rather than assumed: cluster and `n_trades` must match at every index.
    """
    buckets: dict[tuple[str, str], int] = {}
    for c in cands:
        k = (c.decision_day, cluster_of(c.sleeve, registry) or "__unknown__")
        buckets[k] = buckets.get(k, 0) + 1
    keys = sorted(buckets)
    if len(keys) != len(units):
        return None
    out = {}
    for k, u in zip(keys, units):
        if u.cluster != k[1] or int(u.n_trades) != buckets[k]:
            return None
        out[k] = u
    return out


# =====================================================================================
# reading a result


def book_daily_series(res: BookResult, *, key: str = "exit") -> dict[dt.date, float]:
    """Book P&L per day, as a FRACTION of the balance at each trade's entry.

    Fraction-of-balance rather than currency, because the book compounds and a currency
    series would fold the compounding into every downstream statistic. `key="exit"` keys a
    trade to the day it settled (when the P&L is realised, which is what an equity curve
    sees); `key="entry"` keys it to the day it was decided, matching `panel.build_daily_panel`
    so a book series can be compared with a sleeve series on the same axis.
    """
    out: dict[dt.date, float] = {}
    for p in res.placed:
        if "pnl" not in p:
            continue
        d = (p["exit_utc"] if key == "exit" else p["entry_utc"]).date()
        out[d] = out.get(d, 0.0) + p["pnl"] / p["balance_at_entry"]
    return dict(sorted(out.items()))


def book_stats(res: BookResult) -> dict[str, Any]:
    """Headline economics of one book run. Every field is computed, none is assumed."""
    curve = res.equity_curve
    start = res.config.starting_balance
    final = curve[-1][1] if curve else start
    peak = start
    max_dd = 0.0
    max_dd_at = None
    for ts, b in curve:
        peak = max(peak, b)
        dd = (peak - b) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd, max_dd_at = dd, ts
    daily = book_daily_series(res)
    daily_entry = book_daily_series(res, key="entry")
    vals = list(daily.values())
    mean = statistics.fmean(vals) if vals else 0.0
    sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    sharpe = (mean / sd) if sd > 0 else 0.0
    span_days = None
    if curve and len(curve) > 1:
        span_days = (curve[-1][0] - curve[0][0]).days or None
    years = (span_days / 365.25) if span_days else None
    cagr = ((final / start) ** (1.0 / years) - 1.0) if years and final > 0 else None
    r_sum = math.fsum(p["r_net"] for p in res.placed)
    return {
        "n_placed": len(res.placed),
        "sum_r_net": round(r_sum, 4),
        "mean_r_net_per_trade": round(r_sum / len(res.placed), 5) if res.placed else None,
        "starting_balance": start,
        "final_balance": round(final, 2),
        "total_return_pct": round((final / start - 1.0) * 100.0, 3),
        "max_drawdown_pct": round(max_dd * 100.0, 3),
        "max_drawdown_at": max_dd_at.isoformat() if max_dd_at else None,
        "n_trading_days": len(daily),
        "book_daily_mean_frac": round(mean, 8),
        "book_daily_sd_frac": round(sd, 8),
        "book_daily_sharpe": round(sharpe, 5),
        "day_axis": ("exit — the day the P&L was realised, which is what an equity curve "
                     "sees. GateSpec.day_key defaults to 'entry' (spec.py:132), so the "
                     "entry-axis figures below are the ones comparable with a sleeve panel."),
        "n_trading_days_entry_axis": len(daily_entry),
        "book_daily_sharpe_entry_axis": (
            round(statistics.fmean(list(daily_entry.values()))
                  / statistics.pstdev(list(daily_entry.values())), 5)
            if len(daily_entry) > 1 and statistics.pstdev(list(daily_entry.values())) > 0
            else 0.0),
        "span_days": span_days,
        "cagr_pct": round(cagr * 100.0, 3) if cagr is not None else None,
        "first": curve[0][0].isoformat() if curve else None,
        "last": curve[-1][0].isoformat() if curve else None,
    }

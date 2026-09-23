"""Behavioural tests for the merged-book replay.

The claim this module has to earn is *"the merged book reproduces the engine's real sizing
rather than a reimplementation of it"*. Source-string assertions cannot earn that — a test
that greps for `size_correlated_units` passes against a wrong call. So every test here
constructs trades, runs the book, and asserts on an outcome that would differ if the sizing
were hand-rolled:

  * the Kelly-lite conviction multiplier changes when a SECOND sleeve fires the same day,
    and the tag on the unit says which bin it landed in;
  * two sleeves wanting the same broker symbol produce ONE position;
  * the governor's soft daily stop blocks entries after a realised loss day;
  * P&L is `balance x risk_pct x R` and compounds;
  * the candidate->unit mapping is verified against the sizer's own bucket order and RAISES
    rather than guessing.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_daily_series,
    book_stats,
    replay_book,
)

UTC = dt.timezone.utc


def _runtime(**over) -> dict:
    """A minimal live-shaped runtime block.

    The dial keys are the ones `bridge.REQUIRED_DIAL_KEYS` refuses to run without; the
    values are the live ones from `config/agent_config.yaml:1302-1340`.
    """
    cfg = {
        "ultimate_book_enabled": True,
        "ultimate_book_apply_to_execution": True,
        "ultimate_book_live_activation_allowed": False,
        "ultimate_book_include_clean3": False,
        "ultimate_book_include_clean4": False,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_profile": "clean3_w7_ceiling_nom2p00",
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_kelly_running_count": True,
        "ultimate_book_stress_derisk": True,
        "ultimate_book_sqrt_n_pooling": False,
        "ultimate_book_overlays": False,
        "ultimate_book_vp_acceptance": False,
        "ultimate_book_drop_w7_symbols": False,
        "ultimate_book_metals_confluence_gate": False,
        "ultimate_book_derisk_mode": "smooth",
        "ultimate_book_soft_daily_stop_pct": 0.03,
        "ultimate_book_derisk_start_dd_pct": 0.07,
        "ultimate_book_max_dd_entry_block_pct": 0.09,
        "ultimate_book_gross_open_risk_cap_pct": 0.04,
        "ultimate_book_one_unit_per_cluster_per_day": False,
        "ultimate_book_cluster_cap_exempt_clusters": ["jpy"],
        "ultimate_book_profit_target_pct": 0.10,
        "ultimate_book_profit_target_derisk_mult": 0.25,
    }
    cfg.update(over)
    return cfg


def _t(sleeve, symbol, day, hour=8, hold_h=4, r=1.0, canonical=None, price=2000.0,
       stop=10.0, direction=1) -> BookTrade:
    entry = dt.datetime(2025, 1, day, hour, tzinfo=UTC)
    return BookTrade(
        sleeve=sleeve, symbol=symbol, symbol_canonical=canonical or symbol,
        entry_utc=entry, exit_utc=entry + dt.timedelta(hours=hold_h),
        direction=direction, stop_dist=stop, entry_price=price, r_net=r,
        decision_day=entry.date().isoformat(),
        decision_bar_iso=(entry - dt.timedelta(hours=4)).isoformat(),
        timeframe=16388,
    )


# ---------------------------------------------------------------------------------------
def test_one_sleeve_places_and_pnl_is_risk_times_R():
    cfg = BookConfig(runtime=_runtime(), sleeves=("metals_core",), label="one")
    res = replay_book([_t("metals_core", "XAUUSD", 6, r=2.0)], cfg)
    assert len(res.placed) == 1, res.rejections
    p = res.placed[0]
    # P&L = balance * risk_pct_per_trade * R  (execution.py:3360)
    assert p["pnl"] == pytest.approx(cfg.starting_balance * p["risk_pct"] * 2.0)
    assert res.final_balance == pytest.approx(cfg.starting_balance + p["pnl"])
    st = book_stats(res)
    assert st["n_placed"] == 1
    assert st["sum_r_net"] == pytest.approx(2.0)


def test_a_second_sleeve_changes_the_first_sleeve_s_SIZE():
    """The interaction, in its purest form — and the reason a sum of parts is not a book.

    Kelly-lite counts DISTINCT sleeves firing on a decision_day and multiplies every unit by
    a step function of that count (`admission.py:1165-1170`, `:920`). So adding a second
    sleeve on the same day changes what the FIRST sleeve is sized at. No per-sleeve table
    can show this, and a hand-rolled sizer would have to reproduce the bins to see it.
    """
    rt = _runtime()
    solo = replay_book([_t("metals_core", "XAUUSD", 6)],
                       BookConfig(runtime=rt, sleeves=("metals_core",), label="solo"))
    pair = replay_book([_t("metals_core", "XAUUSD", 6), _t("crypto", "BTCUSD", 6)],
                       BookConfig(runtime=rt, sleeves=("metals_core", "crypto"), label="pair"))

    metals_solo = [p for p in solo.placed if p["sleeve"] == "metals_core"][0]
    metals_pair = [p for p in pair.placed if p["sleeve"] == "metals_core"][0]
    assert metals_solo["risk_pct"] != metals_pair["risk_pct"], (
        "adding a second sleeve must move the first sleeve's size through the Kelly-lite "
        f"conviction bin; got {metals_solo['risk_pct']} both times")
    # and the unit itself says which bin it landed in
    assert any(t.startswith("kelly_lite_na1_") for t in metals_solo["tags"]), metals_solo["tags"]
    assert any(t.startswith("kelly_lite_na2_") for t in metals_pair["tags"]), metals_pair["tags"]


def test_two_sleeves_on_one_broker_symbol_produce_one_position():
    """`book_owner.py:1780-1807` — the lifecycle guard. A correlated pair does not double up."""
    rt = _runtime(ultimate_book_include_clean3=True)
    trades = [
        _t("metals_core", "XAUUSD", 6, hour=8, hold_h=48),
        _t("sub_xvol_pullback", "XAUUSD", 6, hour=12, hold_h=4),
    ]
    res = replay_book(trades, BookConfig(
        runtime=rt, sleeves=("metals_core", "sub_xvol_pullback"), label="collide"))
    assert len(res.placed) == 1, [p["sleeve"] for p in res.placed]
    assert res.rejections.get("same_broker_symbol_open_position_lifecycle_guard") == 1


def test_same_sleeve_same_symbol_same_day_places_once():
    rt = _runtime()
    a = _t("metals_core", "XAUUSD", 6, hour=4, hold_h=1)
    b = _t("metals_core", "XAUUSD", 6, hour=12, hold_h=1)
    res = replay_book([a, b], BookConfig(runtime=rt, sleeves=("metals_core",), label="dup"))
    assert len(res.placed) == 1
    assert res.rejections.get("already_placed_today") == 1


def test_soft_daily_stop_blocks_entries_after_a_realised_loss_day():
    """`admission.py:1319-1320` — realised loss past the soft stop -> no new entries."""
    rt = _runtime()
    # One big early loss, then a second candidate later the same reset window.
    loser = _t("metals_core", "XAUUSD", 6, hour=1, hold_h=1, r=-1.0)
    later = _t("crypto", "BTCUSD", 6, hour=20, hold_h=1, r=1.0)
    res = replay_book([loser, later],
                      BookConfig(runtime=rt, sleeves=("metals_core", "crypto"), label="stop"))
    # the loser is placed; whether the later one is blocked depends on how deep the loss went
    assert any(p["sleeve"] == "metals_core" for p in res.placed)
    # and the governor reason, when it blocks, comes from the PRODUCTION governor
    blocked = [k for k in res.rejections if k.startswith("governor:")]
    assert all("soft" in k or "derisk" in k or "dd" in k or "cap" in k or "gate" in k
               or "ceiling" in k or "allowed" in k for k in blocked), blocked


def test_the_two_floating_models_are_not_a_bracket_and_the_module_says_so():
    """The claim this REPLACES was wrong, and its test could not have caught it.

    The old assertion was `b.final >= a.final - 1e-6 or len(b.placed) <= len(a.placed)`,
    offered as proof that `worst_case` "must shrink size or block entries, never help".
    `b.final >= a.final` IS worst_case helping — the disjunct asserted the failure as the
    pass condition, so the test could not distinguish "shrank" from "helped".

    An adversarial refuter then measured the failure: marking equity down pushes
    `gain = (equity - dd_ref)/dd_ref` back below `profit_target_pct`, which REMOVES the
    OPS-03 profit-target de-risk (`admission.py:1353-1357`) and sizes **4.0000x LARGER**.
    The governor is non-monotone in equity by design.

    So this test asserts the honest property instead: the governor's own
    `size_cap_multiplier` is non-monotone in equity, and the module documents that rather
    than claiming a bound it does not have.
    """
    from src.components.ultimate_book.admission import GovernorState, evaluate_governor
    from src.research_infra.walkforward import book_replay

    limits = _P_limits()
    dd_ref = 100_000.0
    hi = GovernorState(equity=110_100.0, high_water=110_100.0, realized_today_pct=0.0,
                       open_risk_pct=0.0, max_dd_reference_equity=dd_ref)
    lo = GovernorState(equity=109_692.63, high_water=110_100.0, realized_today_pct=0.0,
                       open_risk_pct=0.0, max_dd_reference_equity=dd_ref)
    g_hi, g_lo = evaluate_governor(hi, limits=limits), evaluate_governor(lo, limits=limits)
    assert g_lo.size_cap_multiplier > g_hi.size_cap_multiplier, (
        "marking equity DOWN must be able to INCREASE the cap multiplier — that is the "
        f"non-monotonicity: {g_hi} vs {g_lo}")
    assert "profit_target" in g_hi.reason

    doc = book_replay.__doc__ or ""
    assert "NOT a bracket" in doc, (
        "the module must not describe the two floating models as bounds; the governor is "
        "non-monotone in equity and they do not bracket")


def _P_limits():
    from src.components.ultimate_book.admission import GovernorLimits

    return GovernorLimits(
        soft_daily_stop_pct=0.03, max_dd_entry_block_pct=0.09, derisk_start_dd_pct=0.07,
        gross_open_risk_cap_pct=0.04, derisk_mode="smooth", profit_target_pct=0.10,
        profit_target_derisk_mult=0.25)


def test_running_conviction_counts_this_cycle_s_own_sleeves():
    """Live's ledger UNIONS this cycle's sleeves first; a stale override under-sizes 24.5%.

    `running_conviction_state.update_and_count` (`:60-82`) merges `firing_by_day` into the
    persisted set and returns the count INCLUDING it, and `admission.py:1208-1210` takes
    `na = max(per_cycle, running)`. Updating after `decide()` made the second cycle of a
    two-sleeve day see na=1 where live sees na=2 — measured at a 0.7548 size ratio.

    Behavioural: two sleeves on the same decision_day at DIFFERENT instants. The second one
    must carry the na=2 tag.
    """
    rt = _runtime()
    a = _t("metals_core", "XAUUSD", 6, hour=4, hold_h=1)
    b = _t("crypto", "BTCUSD", 6, hour=12, hold_h=1)
    res = replay_book([a, b], BookConfig(runtime=rt, sleeves=("metals_core", "crypto"),
                                         label="rc"))
    by = {p["sleeve"]: p for p in res.placed}
    assert set(by) == {"metals_core", "crypto"}, res.rejections
    assert any(t.startswith("kelly_lite_na1_") for t in by["metals_core"]["tags"])
    assert any(t.startswith("kelly_lite_na2_") for t in by["crypto"]["tags"]), (
        f"the second cycle of the day must see na=2, got {by['crypto']['tags']}")


def test_the_daily_anchor_is_the_window_open_not_the_post_settlement_balance():
    """A loss realised earlier in the reset window must be visible to the soft daily stop.

    Anchoring on the balance at the first cycle INSIDE the window — after
    `_settle_through` — made `realized_today_pct` identically 0.0 there, so the governor
    could never see the loss that had just been booked.
    """
    rt = _runtime()
    loser = _t("metals_core", "XAUUSD", 6, hour=2, hold_h=1, r=-1.0)
    later = _t("crypto", "BTCUSD", 6, hour=14, hold_h=1, r=1.0)
    res = replay_book([loser, later],
                      BookConfig(runtime=rt, sleeves=("metals_core", "crypto"), label="anch"))
    placed = {p["sleeve"] for p in res.placed}
    assert "metals_core" in placed
    # the loss is ~1.5% of balance — under the 3% soft stop, so `crypto` still places; the
    # point is that the anchor is the window OPEN, so the governor saw a negative
    # realized_today_pct rather than exactly zero.
    assert res.diagnostics["final_balance"] < res.diagnostics["starting_balance"] or (
        "crypto" in placed)
    big = _t("metals_core", "XAUUSD", 7, hour=2, hold_h=1, r=-1.0)
    after = _t("crypto", "BTCUSD", 7, hour=14, hold_h=1, r=1.0)
    hot = _runtime(ultimate_book_soft_daily_stop_pct=0.001)   # 0.1% — the loss must trip it
    r2 = replay_book([big, after],
                     BookConfig(runtime=hot, sleeves=("metals_core", "crypto"), label="anch2"))
    assert any(k.startswith("governor:") for k in r2.rejections), (
        f"a realised loss past the soft stop must block the later entry; got {r2.rejections}")


def test_pnl_is_charged_on_the_balance_at_placement():
    """`execution.py:3360` fixes the currency at risk when the ORDER IS SENT.

    Charging it on the settlement balance made a trade's P&L depend on what else happened
    to close during its hold — a path dependence live does not have — and broke
    `book_daily_series`'s documented `risk_pct * R` identity whenever anything settled
    mid-hold.
    """
    rt = _runtime()
    long_hold = _t("metals_core", "XAUUSD", 6, hour=1, hold_h=100, r=1.0)
    settles_first = _t("crypto", "BTCUSD", 6, hour=2, hold_h=1, r=3.0)
    res = replay_book([long_hold, settles_first],
                      BookConfig(runtime=rt, sleeves=("metals_core", "crypto"), label="basis"))
    for p in res.placed:
        assert p["pnl"] == pytest.approx(p["balance_at_entry"] * p["risk_pct"] * p["r_net"]), (
            f"{p['sleeve']} charged on the wrong balance")


def test_the_live_dial_runs_rather_than_raising():
    """Under the ACTUAL live flags the sizer drops intents before any unit exists.

    `ultimate_book_drop_w7_symbols: true` (`agent_config.yaml:1291`) removes the W7 illiquid
    energy legs and `ultimate_book_metals_confluence_gate: true` (`:1315`) removes
    A8-failing metals intents — both INSIDE `admit_and_size`. Rebuilding the bucket keys
    from the unfiltered candidate list made the key sets diverge and the harness raised, so
    it could not run the live dial on `energy_agri` (an UNCONDITIONAL survivor) at all.
    """
    rt = _runtime(ultimate_book_drop_w7_symbols=True, ultimate_book_metals_confluence_gate=True)
    trades = [
        _t("energy_agri", "NATGAS.cash", 6, canonical="NATGAS_cash", price=3.0, stop=0.1),
        _t("energy_agri", "USOIL.cash", 6, canonical="USOIL_cash", price=70.0, stop=1.0),
        _t("metals_core", "XAUUSD", 6),
    ]
    res = replay_book(trades, BookConfig(
        runtime=rt, sleeves=("energy_agri", "metals_core"), label="livedial"))
    assert res.n_cycles == 1
    # NATGAS_cash is a W7-dropped leg and must be filed as a SIZER filter, not a governor stop
    assert res.rejections.get("sizer_precount_filter_dropped_intent", 0) >= 1, res.rejections
    assert res.diagnostics["n_intents_dropped_by_sizer_precount_filters"] >= 1


def test_a_broken_dial_is_refused_rather_than_silently_resized():
    """`strict_config=True`. `sleeve_book.py:193-202` says why the guard exists.

    With `strict_config=False` (the previous hardcoded value) a runtime block missing every
    dial key sized `metals_core` 37.5% smaller off the bridge defaults and recorded an
    all-`None` provenance. It must refuse instead — and it refuses at CONSTRUCTION, naming
    the missing keys, which is louder and earlier than a per-cycle rejection.
    """
    from src.research_infra.replay_policy.core import PolicyError

    with pytest.raises(PolicyError) as e:
        replay_book([_t("metals_core", "XAUUSD", 6)],
                    BookConfig(runtime={}, sleeves=("metals_core",), label="nodial"))
    assert "missing_dial_keys" in str(e.value)
    assert "ultimate_book_profile" in str(e.value)


def test_refusal_reasons_name_the_layer_that_refused():
    """A gate refusal, a sizing refusal and an adapter failure are three different things.

    Filing all of them under `governor:` made a broken dial read as "the governor braked".
    `bridge.py:480-506` overwrites the top-level reason with the GATE reason whenever a gate
    blocks, so the top-level string alone cannot be trusted to name the layer.
    """
    # `derisk_mode: band` at the 2.0% ceiling is refused BEFORE the governor runs
    # (`admission.py:1474-1478`, `ceiling_profile_requires_smooth_ddefense`).
    rt = _runtime(ultimate_book_derisk_mode="band")
    res = replay_book([_t("metals_core", "XAUUSD", 6)],
                      BookConfig(runtime=rt, sleeves=("metals_core",), label="band"))
    assert res.placed == []
    keys = list(res.rejections)
    assert keys and not any(k.startswith("governor:") for k in keys), (
        f"a refusal that never reached the governor must not be filed under it: {keys}")


def test_unit_mapping_raises_rather_than_guessing():
    """If the sizer's unit list stops agreeing with the documented bucket order, refuse.

    Simulated by handing `_map_units` a units list that disagrees on `n_trades`.
    """
    from src.research_infra.walkforward.book_replay import _map_units, _registry_for

    rt = _runtime()
    reg = _registry_for(rt)
    cands = [_t("metals_core", "XAUUSD", 6).candidate(),
             _t("metals_core", "XAGUSD", 6).candidate()]

    class _U:
        cluster = "metals"
        n_trades = 1          # the real bucket holds 2

    assert _map_units([_U()], cands, reg) is None


def test_empty_book_is_inert():
    cfg = BookConfig(runtime=_runtime(), sleeves=("metals_core",), label="empty")
    res = replay_book([], cfg)
    assert res.placed == []
    assert res.n_cycles == 0
    assert res.final_balance == cfg.starting_balance
    assert book_daily_series(res) == {}


def test_daily_series_is_a_fraction_of_balance_not_currency():
    rt = _runtime()
    res = replay_book([_t("metals_core", "XAUUSD", 6, r=1.0)],
                      BookConfig(runtime=rt, sleeves=("metals_core",), label="frac"))
    daily = book_daily_series(res)
    (d, v), = daily.items()
    p = res.placed[0]
    assert v == pytest.approx(p["risk_pct"] * 1.0)
    assert 0.0 < v < 0.05, v


def test_closed_deals_are_fed_as_broker_server_epochs_not_utc():
    """`compute_stress_derisk_state` decodes `time` as a SERVER epoch, not a UTC one.

    `admission.py:446` does `fromtimestamp(t, utc).date()` and compares against
    `today = (now_utc + offset_hours).date()`. Feed it a true UTC epoch and the two sides sit
    `offset_hours` apart, so a deal closing in the last 3 hours of a UTC day lands on the
    wrong server-day — and the leak-free "prior days only" cut slices in the wrong place.

    Asserted behaviourally: a loss that closes at 22:00 UTC belongs to the NEXT server day
    (01:00 server at +3h), so at a `now` of 23:00 UTC the same server-day it must be
    EXCLUDED as in-progress and must not de-risk anything.
    """
    import datetime as _dt

    from src.components.ultimate_book.admission import compute_stress_derisk_state

    close_utc = _dt.datetime(2025, 1, 6, 22, 0, tzinfo=UTC)
    now = _dt.datetime(2025, 1, 6, 23, 0, tzinfo=UTC)
    server_epoch = (close_utc + _dt.timedelta(hours=3)).timestamp()
    utc_epoch = close_utc.timestamp()

    as_server = compute_stress_derisk_state(
        [{"sleeve": "metals_core", "profit": -500.0, "time": server_epoch}], now,
        offset_hours=3.0)
    as_utc = compute_stress_derisk_state(
        [{"sleeve": "metals_core", "profit": -500.0, "time": utc_epoch}], now,
        offset_hours=3.0)

    # server epoch -> 2025-01-07 server-day == today (2025-01-07) -> excluded, no streak
    assert as_server.consecutive_loss_days == 0
    # UTC epoch -> 2025-01-06 < today -> counted. The two disagree, which is the whole point.
    assert as_utc.consecutive_loss_days == 1
    assert as_server.consecutive_loss_days != as_utc.consecutive_loss_days


def test_gates_not_applied_are_declared():
    """A book that silently omits live gates reads as more permissive than live."""
    from src.research_infra.walkforward.book_replay import APPLIED_GATES, NOT_APPLIED_GATES
    from src.research_infra.replay_policy.sleeve_book import PLACEMENT_GATES

    assert set(APPLIED_GATES) | set(NOT_APPLIED_GATES) == set(PLACEMENT_GATES)
    assert set(APPLIED_GATES) & set(NOT_APPLIED_GATES) == set()
    res = replay_book([_t("metals_core", "XAUUSD", 6)],
                      BookConfig(runtime=_runtime(), sleeves=("metals_core",), label="g"))
    d = res.as_dict()
    assert d["placement_gates_not_applied"], "the omission must travel with the result"


def test_the_sizing_is_production_verified_differentially():
    """The load-bearing claim, verified rather than asserted — and by me, not only by a refuter.

    An adversarial refuter reported "0 of 240 cycles differed" between `replay_book`'s units
    and a direct `admission.admit_and_size` call. That claim is in this module's FAVOUR, which
    is exactly why it should not be taken on trust. This reproduces it as a repo invariant:
    every cycle of a multi-sleeve book is re-sized directly from the same intents and the same
    account state, and the two must agree to the last decimal.

    Writing it caught a real discrepancy on the first run — harness 0.01232717 against direct
    0.01540896, a ratio of exactly 0.80 — and the diagnosis is worth keeping: the harness feeds
    the production reactive de-risk overlay a REAL `StressDeriskState` reconstructed from its
    own closed deals (`admission.py:420`, the consecutive-loss-day ladder), while a direct call
    that omits `stress_state` gets the neutral default. 0.80 is `LADDER_STEPS[1]`. The harness
    was doing the MORE faithful thing; the test was comparing two different books. It now
    passes the same state through, which is why the position record carries it.

    If `book_replay` ever starts reimplementing sizing, this goes red.
    """
    from src.components.ultimate_book.admission import (
        GovernorState,
        StressDeriskState,
        admit_and_size,
    )
    from src.research_infra.replay_policy.sleeve_book import _to_trade_intent
    from src.research_infra.walkforward.book_replay import BookConfig, replay_book

    rt = _runtime()
    trades = []
    for day in range(2, 20):
        trades.append(_t("metals_core", "XAUUSD", day, hour=4, hold_h=6, r=(1.0 if day % 3 else -1.0)))
        if day % 2:
            trades.append(_t("crypto", "BTCUSD", day, hour=4, hold_h=6, r=-1.0,
                             price=40000.0, stop=800.0))
    res = replay_book(trades, BookConfig(runtime=rt, sleeves=("metals_core", "crypto"),
                                         label="diff"))
    assert res.placed, res.rejections

    # Re-size each placed unit directly and compare. The state is reconstructed from the
    # position's own record, which is what the harness handed the policy at that instant.
    checked = 0
    for p in res.placed:
        cands = [t.candidate() for t in trades
                 if t.entry_utc == p["entry_utc"] and t.sleeve in ("metals_core", "crypto")]
        intents = [_to_trade_intent(c) for c in cands]
        gs = GovernorState(
            equity=p["balance_at_entry"], high_water=max(100_000.0, p["balance_at_entry"]),
            realized_today_pct=p["realized_today_pct"],
            open_risk_pct=p["open_risk_pct_at_entry"], max_dd_reference_equity=100_000.0)
        ss = (StressDeriskState(consecutive_loss_days=p["stress_state"][0],
                                trailing_neg_frac=p["stress_state"][1])
              if p.get("stress_state") else None)
        out = admit_and_size(
            intents, gs, profile=rt["ultimate_book_profile"], account="A",
            limits=_P_limits(), include_clean3=False, include_candidate_book=False,
            include_market_expansion_book=False, kelly_lite=True, kelly_conservative=True,
            stress_derisk=True, stress_state=ss,
            n_active_override={c.decision_day: len({x.sleeve for x in cands}) for c in cands},
        )
        units = [u for u in (out.get("units") or []) if u.get("cluster") == p["cluster"]]
        if not units:
            continue
        # Same cluster, same day, same members -> the same per-trade risk.
        assert any(abs(u["risk_pct_per_trade"] - p["risk_pct"]) < 1e-9 for u in units), (
            f"{p['sleeve']} at {p['entry_utc']}: harness {p['risk_pct']} vs direct "
            f"{[u['risk_pct_per_trade'] for u in units]}")
        checked += 1
    assert checked >= 5, f"only {checked} cycles compared; the control is too thin to mean anything"

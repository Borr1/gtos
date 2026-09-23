"""Leak-free RUNNING per-day conviction count: monotone+idempotent store, the bounded-by-full-day
proof, the sizer override sandwich, engine gating (default-OFF), and the correctness-critical filter
parity. The size-up is the recovery of the live per-cycle under-sizing UP to the validated full-day
1.25% convention — never above it."""
import json
import os
import tempfile
from datetime import datetime, timezone
from types import SimpleNamespace

from src.components.ultimate_book.running_conviction_state import RunningConvictionLedger
from src.components.ultimate_book.admission import (
    GovernorLimits, GovernorState, admit_and_size,
    kelly_lite_conviction_multiplier, precount_intent_filter, size_correlated_units, TradeIntent,
)
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine


class _MT5:
    def get_candles(self, *a, **k):
        return []
    def get_account_equity(self):
        return 100000.0


def test_running_ledger_monotone_and_idempotent():
    with tempfile.TemporaryDirectory() as d:
        L = RunningConvictionLedger(d, namespace="t")
        day = "2026-06-15"
        assert L.update_and_count({day: {"idxrev"}}) == {day: 1}
        assert L.update_and_count({day: {"crypto"}}) == {day: 2}
        assert L.update_and_count({day: {"crypto"}}) == {day: 2}            # idempotent re-tick
        assert L.update_and_count({day: {"metals_core", "energy_agri"}}) == {day: 4}
        assert L.update_and_count({day: {"idxrev"}}) == {day: 4}            # monotone (never drops)


def test_running_ledger_new_day_reset_and_prune():
    with tempfile.TemporaryDirectory() as d:
        L = RunningConvictionLedger(d, namespace="t")
        L.update_and_count({"2026-06-13": {"a", "b"}})
        L.update_and_count({"2026-06-14": {"a"}})
        assert L.update_and_count({"2026-06-15": {"x"}}) == {"2026-06-15": 1}   # new day starts fresh
        store = json.load(open(os.path.join(d, "pipeline_state", "ultimate_book", "t", "firing_sleeves.json")))
        assert set(store["days"]) == {"2026-06-14", "2026-06-15"}              # oldest pruned


def test_running_count_bounded_by_full_day_and_multiplier_monotone():
    # running count is a SUBSET of the full-day union => count_running <= count_full at every t, and the
    # half-Kelly bins are monotone => multiplier(running) <= multiplier(full): the size-up can never
    # exceed the already-validated full-day envelope.
    for run, full in [(1, 1), (1, 2), (2, 3), (2, 4), (3, 4), (4, 7)]:
        assert run <= full
        mr = kelly_lite_conviction_multiplier(run, enabled=True, conservative=True)
        mf = kelly_lite_conviction_multiplier(full, enabled=True, conservative=True)
        assert mr <= mf


def test_sizer_override_sandwiched_between_per_cycle_and_full_day():
    day = "2026-06-15"
    intents = [TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day, stop_dist=20.0)]
    base = 0.0125  # 1.25% nominal
    r_cycle = size_correlated_units(intents, base_risk_per_unit=base, include_clean3=True,
                                    kelly_lite=True, kelly_conservative=True)[0].unit_risk_pct
    r_run = size_correlated_units(intents, base_risk_per_unit=base, include_clean3=True,
                                  kelly_lite=True, kelly_conservative=True,
                                  n_active_override={day: 2})[0].unit_risk_pct
    # per-cycle na=1 -> 0.748 bin; running na=max(1,2)=2 -> 0.991 bin (the exact 0.14025% -> 0.185813%
    # recovery that removes the live FTMO/FN cross-account split). unit_risk_pct is rounded to 8dp.
    assert abs(r_cycle - base * 0.15 * 0.748) < 1e-7
    assert abs(r_run - base * 0.15 * 0.991) < 1e-7
    assert r_run > r_cycle                                                   # sizes UP toward nominal
    # override below the per-cycle count is clamped UP to the safe per-cycle floor (never sizes down)
    r_clamp = size_correlated_units(intents, base_risk_per_unit=base, include_clean3=True,
                                    kelly_lite=True, kelly_conservative=True,
                                    n_active_override={day: 0})[0].unit_risk_pct
    assert abs(r_clamp - r_cycle) < 1e-12


def test_route_override_is_authoritative_over_future_slate_members():
    day = "2026-06-15"
    intents = [
        TradeIntent("idxrev", "SPX500", -1, day, 20.0),
        TradeIntent("metals_core", "XAUUSD", 1, day, 10.0),
    ]
    ordinary = size_correlated_units(
        intents,
        base_risk_per_unit=0.0125,
        include_clean3=True,
        kelly_lite=True,
        kelly_conservative=True,
        n_active_override={day: 1},
    )
    routed = size_correlated_units(
        intents,
        base_risk_per_unit=0.0125,
        include_clean3=True,
        kelly_lite=True,
        kelly_conservative=True,
        n_active_override={day: 1},
        n_active_override_authoritative=True,
    )
    assert all("kelly_lite_na2_x0.991" in u.overlays_applied for u in ordinary)
    assert all("kelly_lite_na1_x0.748" in u.overlays_applied for u in routed)
    assert all(a.unit_risk_pct > b.unit_risk_pct for a, b in zip(ordinary, routed))


def test_override_none_is_byte_identical_to_per_cycle():
    day = "2026-06-15"
    intents = [TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day, stop_dist=20.0),
               TradeIntent(sleeve="metals_core", symbol="XAUUSD", direction=1, decision_day=day, stop_dist=10.0)]
    a = size_correlated_units(intents, base_risk_per_unit=0.0125, include_clean3=True,
                              kelly_lite=True, kelly_conservative=True)
    b = size_correlated_units(intents, base_risk_per_unit=0.0125, include_clean3=True,
                              kelly_lite=True, kelly_conservative=True, n_active_override=None)
    assert [u.unit_risk_pct for u in a] == [u.unit_risk_pct for u in b]      # None => locked-MC parity


def test_engine_override_off_by_default_and_on_when_flagged():
    day = "2026-06-15"
    its = [TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day, stop_dist=20.0)]
    eng_off = UltimateBookLiveEngine({"ultimate_book_kelly_lite": True}, _MT5(), tempfile.mkdtemp())
    assert eng_off._running_conviction_override(its) is None                 # default OFF -> per-cycle
    eng_on = UltimateBookLiveEngine(
        {"ultimate_book_kelly_lite": True, "ultimate_book_kelly_running_count": True},
        _MT5(), tempfile.mkdtemp())
    assert eng_on._running_conviction_override(its) == {day: 1}


def test_refused_preview_does_not_persist_or_inflate_the_next_candidate():
    """A cost/permission refusal is provisional only; accepted placement owns the commit."""
    day = "2026-06-15"
    with tempfile.TemporaryDirectory() as d:
        eng = UltimateBookLiveEngine(
            {"ultimate_book_kelly_lite": True, "ultimate_book_kelly_running_count": True},
            _MT5(), d, namespace="operator")
        refused = TradeIntent(sleeve="asian_fade", symbol="EURUSD", direction=1,
                              decision_day=day, stop_dist=0.001)
        admissible = TradeIntent(sleeve="idxrev", symbol="UK100", direction=1,
                                 decision_day=day, stop_dist=50.0)
        path = os.path.join(
            d, "pipeline_state", "ultimate_book", "operator", "firing_sleeves.json")

        assert eng._running_conviction_override([refused]) == {day: 1}
        assert not os.path.exists(path)  # preview is read-only; refusal leaves no durable state
        assert eng._running_conviction_override([admissible]) == {day: 1}

        assert eng.commit_running_conviction(admissible) == {day: 1}
        store = json.load(open(path))
        assert store == {"days": {day: ["idxrev"]}}
        assert eng.commit_running_conviction(admissible) == {day: 1}  # accepted retry is idempotent
        assert json.load(open(path)) == store
        assert eng._running_conviction_override([refused]) == {day: 2}
        assert json.load(open(path)) == store  # later preview still does not mutate the commit set


def test_same_slate_cost_refusal_cannot_raise_or_cap_an_accepted_sibling(tmp_path):
    """The final route count is placement truth, not the all-candidate slate.

    Three candidates enter one evaluation, so the historical preview honestly reproduces ``na=3``.
    Under deliberately narrow gross headroom the all-slate sizing sheds crypto and index.  Crypto is
    reconsidered first (the existing FFD priority), receives ``na=1`` at its send boundary, and fits.
    Energy is then refused by the downstream cost gate.  Index receives ``na=2`` -- placed crypto plus
    itself, never refused energy -- and also fits.  Only the two placed sleeves may become durable.

    REAL CODE DEFECT caught here (2026-08-25 pre-existing-failure clearing, f5max-ship;
    DO-NOT-EDIT-TEST): index routes at na=1 (x0.748) instead of na=2 (x0.991) because the
    owner's conviction commit getattr's ``record_placement_conviction``, which
    UltimateBookLiveEngine does not define (it has ``commit_running_conviction``,
    book_engine.py:1680) — crypto's placement never becomes durable, so the sibling
    under-counts.  Src fix applied centrally; verified green under the one-line engine alias.
    """
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    day = "2026-08-12"
    now = datetime(2026, 8, 12, 8, 1, tzinfo=timezone.utc)
    runtime = {
        "ultimate_book_enabled": True,
        "ultimate_book_apply_to_execution": True,
        "ultimate_book_live_activation_allowed": True,
        "ultimate_book_live_broker_authority": True,
        "ultimate_book_disable_broad_selector": True,
        "ultimate_book_profile": "clean3_w7_measured_nom1p25",
        "ultimate_book_derisk_mode": "band",
        "ultimate_book_include_clean3": True,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_stress_derisk": False,
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_kelly_running_count": True,
        "ultimate_book_drop_w7_symbols": False,
        "ultimate_book_gross_open_risk_cap_pct": 0.010,
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": False,
        "ultimate_book_max_entry_lateness_frac": 10.0,
    }
    cfg = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "instruments": {
            "USOIL_cash": {"market": {"mt5_symbol": "USOIL.cash"}},
            "BTCUSD": {"market": {"mt5_symbol": "BTCUSD"}},
            "SPX500": {"market": {"mt5_symbol": "SPX500"}},
        },
        "gtos_vnext_runtime": runtime,
    }

    class _Broker(_MT5):
        def get_account_balance(self):
            return 100000.0

        def get_open_positions(self):
            return []

        def get_tick(self, symbol):
            # This test owns conviction persistence, not the independently tested stale-tick
            # market gate.  A fixed wall-clock tick made the test start failing 15 minutes
            # after its fixture timestamp even though conviction behavior was unchanged.
            return SimpleNamespace(
                bid=100.0,
                ask=100.1,
                time=datetime.now(timezone.utc),
            )

    class _ExecutionEngine:
        active_trade = None

    class _Router:
        placed_risks = []

        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, execution_engine, sized_unit, intent, tick, account_state, balance):
            self.placed_risks.append((intent.sleeve, sized_unit.risk_pct_per_trade))
            return {
                "placed": True,
                "trade_state": SimpleNamespace(ticket=8181),
                "trade_params": {"candidate_id": f"test::{intent.sleeve}"},
                "candidate_id": f"test::{intent.sleeve}",
            }

    owner = UltimateBookOwner(
        cfg,
        _Broker(),
        str(tmp_path),
        namespace="operator",
        engine_factory=lambda symbol, sleeve=None: _ExecutionEngine(),
    )
    engine = owner.engine
    engine.config.update(runtime)
    intents = [
        TradeIntent("energy_agri", "USOIL_cash", 1, day, 1.0, target_dist=2.0),
        TradeIntent("crypto", "BTCUSD", 1, day, 10.0, target_dist=20.0),
        TradeIntent("idxrev", "SPX500", -1, day, 20.0, target_dist=40.0),
    ]
    gs = GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )
    slate_override = engine._running_conviction_override(intents)
    assert slate_override == {day: 3}, "the test must reproduce the contaminated evaluation preview"
    shadow = admit_and_size(
        intents,
        gs,
        profile="clean3_w7_measured_nom1p25",
        account="A",
        limits=GovernorLimits(gross_open_risk_cap_pct=0.010),
        include_clean3=True,
        kelly_lite=True,
        kelly_conservative=True,
        n_active_override=slate_override,
    )
    assert shadow["new_entries_allowed"] is True
    by_member = {tuple(u["sleeve_members"]): u for u in shadow["units"]}
    assert by_member[("crypto",)]["reason"] == "gross_risk_cap_would_exceed"
    assert by_member[("energy_agri",)]["reason"] == "sized"
    assert by_member[("idxrev",)]["reason"] == "gross_risk_cap_would_exceed"
    expected_crypto_risk = size_correlated_units(
        [intents[1]],
        base_risk_per_unit=0.0125,
        include_clean3=True,
        kelly_lite=True,
        kelly_conservative=True,
        n_active_override={day: 1},
        n_active_override_authoritative=True,
    )[0].risk_pct_per_trade
    expected_index_risk = size_correlated_units(
        [intents[2]],
        base_risk_per_unit=0.0125,
        include_clean3=True,
        kelly_lite=True,
        kelly_conservative=True,
        n_active_override={day: 2},
        n_active_override_authoritative=True,
    )[0].risk_pct_per_trade

    def _evaluate(*, now_utc=None, tags=None):
        decision = SimpleNamespace(
            runtime_effect_now=True,
            decision_status="execute_now",
            realized_units=list(shadow["units"]),
            would_units=list(shadow["units"]),
            governor=dict(shadow["governor"]),
            kelly_running_count=True,
            kelly_lite=True,
        )
        return {
            "ok": True,
            "reason": "execute_now",
            "n_intents": len(intents),
            "runtime_effect_now": True,
            "decision": decision,
            "governor_state": gs,
            "intents": list(intents),
            "meta": [
                {"tag": intent.sleeve, "symbol": intent.symbol,
                 "decision_bar_iso": now.isoformat(), "timeframe": 16388}
                for intent in intents
            ],
        }

    engine.evaluate = _evaluate
    router = owner.router = _Router()
    owner._spread_cost_screen = lambda intent, tick: (
        "missing_cost:pretrade_cost_model_status_passed"
        if intent.sleeve == "energy_agri" else None
    )
    owner._emit_cycle_runtime_learning = lambda *args, **kwargs: None
    owner._f5_emit_slate = lambda *args, **kwargs: None
    owner._f5_on_open = lambda *args, **kwargs: None
    owner._notify_cost_skip = lambda *args, **kwargs: None
    owner._notify_placed = lambda *args, **kwargs: None
    owner._persist_trade_record = lambda *args, **kwargs: None
    owner._load_trade_record = lambda *args, **kwargs: {}
    owner._runtime_learning_trade_context = lambda **kwargs: {}
    owner._ledger.record = lambda *args, **kwargs: {}

    result = owner.run_cycle(now_utc=now)
    state_path = (tmp_path / "pipeline_state" / "ultimate_book" /
                  "operator" / "firing_sleeves.json")
    assert len(result["placed"]) == 2
    assert router.placed_risks == [
        ("crypto", expected_crypto_risk),
        ("idxrev", expected_index_risk),
    ]
    route = result["running_conviction_routes"]
    assert [(row["sleeve"], row["count"]) for row in route] == [
        ("crypto", 1),
        ("idxrev", 2),
    ]
    assert all(
        row["basis"] == "durable_placements_plus_current_candidate"
        for row in route
    )
    assert "kelly_lite_na1_x0.748" in route[0]["overlays_applied"]
    assert "kelly_lite_na2_x0.991" in route[1]["overlays_applied"]
    assert any(
        isinstance(row, dict)
        and row.get("reason") == "missing_cost:pretrade_cost_model_status_passed"
        and row.get("sleeve") == "energy_agri"
        for row in result["skipped"]
    )
    assert json.loads(state_path.read_text(encoding="utf-8")) == {
        "days": {day: ["crypto", "idxrev"]}
    }

def test_engine_override_respects_vp_acceptance_filter():
    # CORRECTNESS-CRITICAL: a non-above_va sub_mid_dn_revert is dropped by vp_acceptance in the full-day
    # path, so the running count must NOT count it (else running could exceed full-day, breaking bound).
    day = "2026-06-15"
    its = [TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day, stop_dist=20.0),
           TradeIntent(sleeve="sub_mid_dn_revert", symbol="USDJPY", direction=1, decision_day=day,
                       stop_dist=0.5, vp_loc="below_va")]
    eng = UltimateBookLiveEngine(
        {"ultimate_book_kelly_lite": True, "ultimate_book_kelly_running_count": True,
         "ultimate_book_vp_acceptance": True, "ultimate_book_include_clean3": True},
        _MT5(), tempfile.mkdtemp())
    assert eng._running_conviction_override(its) == {day: 1}                 # sub_mid_dn dropped -> only idxrev


def test_owner_commits_conviction_only_after_accepted_placement_and_hook_resolves():
    """Pin the accepted-placement conviction-commit sequence at the TRUE live-lineage contract.

    ROOT-CAUSE REWRITE 2026-08-25 (owner-directed pre-existing-failure clearing, f5max-ship).
    The prior version pinned a mechanism that exists on NO lineage in this repository:
    it required an owner method ``_commit_running(intent)`` after ``ledger_row = self._ledger.record``
    and forbade the string ``record_placement_conviction``.  ``git grep`` across every branch
    (main, f5-live, governor-hole-20260824, codex/f5-conviction-repair-20260812, ...) finds no
    ``_commit_running`` anywhere — the test was unsatisfiable as written (STALE EXPECTATION).

    The live F5 lineage (f5-live@68bad3751 = every live byte committed; overlaid here at
    338553883) commits conviction via ``self.engine.record_placement_conviction(intent)``
    immediately after placement truth (``if result["placed"]:``) and BEFORE the best-effort
    ledger row — deliberately, per the in-source comment: persisting before the downstream
    cost/permission/lifecycle/broker gates would let a refused sleeve raise every later
    unit's nominal Kelly multiplier.  The protections that must survive, now pinned:

    1. ORDER: router.place -> placed-truth guard -> conviction commit -> trade-record persist.
    2. NO EARLY COMMIT: no conviction-commit call before the placed-truth guard — a refused
       sleeve can never raise or cap an accepted sibling (the same property
       test_same_slate_cost_refusal_cannot_raise_or_cap_an_accepted_sibling proves end-to-end).
    3. HOOK RESOLVES (the tripwire the old test's last assert was groping for): the method
       name the owner getattr's MUST exist on the real UltimateBookLiveEngine.  The
       ``callable()`` guard around the getattr silently no-ops when the name dangles, which
       is a REAL live defect this suite caught on 2026-08-25: book_owner called
       ``record_placement_conviction`` while book_engine defined only
       ``commit_running_conviction`` (book_engine.py:1680), so durable conviction state was
       never written and every send-boundary route under-counted.  This assertion is
       direction-agnostic: it extracts whatever name the owner uses and requires the engine
       to provide it.
    """
    import inspect
    import re
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    source = inspect.getsource(UltimateBookOwner.run_cycle)
    route = source.index("result = self.router.place")
    placed = source.index('if result["placed"]:', route)
    commit_match = re.search(r'getattr\(self\.engine,\s*"(\w+)"', source[placed:])
    assert commit_match, "run_cycle lost its post-placement conviction-commit hook"
    commit = placed + commit_match.start()
    persist = source.index("self._persist_trade_record", commit)
    assert route < placed < commit < persist
    # Protection 2: the commit hook name must not be invoked anywhere before placement truth.
    hook_name = commit_match.group(1)
    assert hook_name not in source[:placed], (
        "conviction commit reachable before the placed-truth guard: a refusal could "
        "raise an accepted sibling's Kelly multiplier"
    )
    # Protection 3: the hook must RESOLVE on the real engine (catches the silent-no-op
    # dangling-name defect; red until the central src repair lands — see the module's
    # cost-refusal test failing on the identical root cause).
    assert callable(getattr(UltimateBookLiveEngine, hook_name, None)), (
        f"book_owner.run_cycle commits conviction via engine.{hook_name!s}, but "
        f"UltimateBookLiveEngine does not define it — the callable() guard makes this a "
        f"silent no-op: firing_sleeves.json is never written and every "
        f"route_unit_with_committed_conviction under-counts (basis label "
        f"'durable_placements_plus_current_candidate' becomes false)"
    )


# ---- PlacementLedger cross-process incremental refresh (idempotency defense-in-depth) ----
def test_placement_ledger_sees_other_process_record():
    from src.components.ultimate_book.placement_ledger import PlacementLedger
    with tempfile.TemporaryDirectory() as d:
        a = PlacementLedger(d, "ns")          # worker A
        b = PlacementLedger(d, "ns")          # worker B (same on-disk ledger)
        assert b.already_placed("idxrev", "SPX500", "2026-06-15T09:00:00") is False
        a.record("idxrev", "SPX500", "2026-06-15T09:00:00", ticket=1)   # A places + records
        # B must now SEE A's record via the incremental disk re-read (was the TOCTOU double-place bug)
        assert b.already_placed("idxrev", "SPX500", "2026-06-15T09:00:00") is True
        # an unrelated key is still free
        assert b.already_placed("idxrev", "UK100", "2026-06-15T09:00:00") is False


# --------------------------------------------------------------------------- #
# D-AK1 — an intent the sizer REFUSES as `unknown_sleeve` is still counted in the
# conviction breadth, and therefore still sizes UP every other unit that day.
#
# Found 2026-07-30 by Session AK (B970) while running the diversifier door: four candidate
# sleeves that no registry can reach were rejected 449/1469/2803/873 times each with
# `unit:fail_closed:unknown_sleeve:<name>` and STILL moved the armed book's placements.
#
# The mechanism is the one D3 fixed for a different filter, surviving for the VALIDITY check:
# `admission.py:1165-1170` counts distinct sleeves across ALL of today's intents, and
# `:1163-1165` refuses the unknown one afterwards, at unit construction. `precount_intent_filter`
# (`:1004-1051`) is documented as "the ONE definition of the DROPPING pre-count filters" and it
# enumerates the TILT/GATE drops — it has no known-sleeve check, because until now nothing could
# generate a sleeve the sizer could not size.
#
# NOT live-reachable today: B325 measured that the generation registry and `effective_registry`
# resolve the SAME 29 sleeves, so no sleeve generates that cannot be sized. It becomes reachable
# the moment a generation spec is added without the matching `admission` confidence weight — which
# is exactly the one-line registry edit `SESSION_AA_ESTATE_WALK_RESULT.md` §4 routed to the owner
# and `walkforward/supply.REGISTRY_EDIT_PROPOSAL` re-states. That is why this test exists BEFORE
# the edit rather than after it.
# --------------------------------------------------------------------------- #

_AK_UNKNOWN = "zz_not_in_any_registry_ak"


def test_an_unknown_sleeve_the_sizer_refuses_still_inflates_everyone_elses_unit():
    day = "2026-06-15"
    base = 0.0125
    known = TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day,
                        stop_dist=20.0)
    unknown = TradeIntent(sleeve=_AK_UNKNOWN, symbol="SPX500", direction=1, decision_day=day,
                          stop_dist=20.0)

    alone = size_correlated_units([known], base_risk_per_unit=base, include_clean3=True,
                                  kelly_lite=True, kelly_conservative=True)
    withbad = size_correlated_units([known, unknown], base_risk_per_unit=base,
                                    include_clean3=True, kelly_lite=True,
                                    kelly_conservative=True)

    # The unknown sleeve IS refused — that half works.
    refused = [u for u in withbad if "unknown_sleeve" in (u.reason or "")]
    assert refused, [u.reason for u in withbad]
    assert _AK_UNKNOWN in refused[0].reason
    assert refused[0].sized is False and refused[0].unit_risk_pct == 0.0

    # ...and the KNOWN sleeve's unit is nonetheless LARGER, because na went 1 -> 2.
    a = next(u for u in alone if u.sleeve_members == ("idxrev",))
    b = next(u for u in withbad if u.sleeve_members == ("idxrev",))
    assert a.overlays_applied == ("kelly_lite_na1_x0.748",)
    assert b.overlays_applied == ("kelly_lite_na2_x0.991",)     # the refused sleeve was COUNTED
    assert b.unit_risk_pct > a.unit_risk_pct
    # the exact half-Kelly bin crossing: 0.748 -> 0.991 is +32.49 % on a unit that risks real money
    assert abs(b.unit_risk_pct / a.unit_risk_pct - 0.991 / 0.748) < 1e-4
    assert (a.unit_risk_pct, b.unit_risk_pct) == (0.0014025, 0.00185813)


def test_the_precount_filter_does_not_drop_an_unknown_sleeve():
    """The property that makes the test above true, stated where the fix would go.

    If a future session adds a known-sleeve check to `precount_intent_filter`, this test goes red
    and should be DELETED along with the one above — the defect would be fixed. It is written as
    an assertion about today's behaviour rather than a wish so that the repair is a deliberate act.
    """
    day = "2026-06-15"
    intents = [TradeIntent(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day=day,
                           stop_dist=20.0),
               TradeIntent(sleeve=_AK_UNKNOWN, symbol="SPX500", direction=1, decision_day=day,
                           stop_dist=20.0)]
    kept = precount_intent_filter(intents, vp_acceptance=True, metals_confluence_gate=True)
    assert len(kept) == 2
    assert any(i.sleeve == _AK_UNKNOWN for i in kept)

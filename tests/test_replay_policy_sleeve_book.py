"""Behavioural tests for the Phase-2 policy core and ``SleeveBookPolicy``.

Every test here asserts on *behaviour* — a decision, a number, a refusal — not on
source text.  This wave found a source-string test that passed against a wrong
implementation, and seven test files validating a different checkout through a
hardcoded ``sys.path.insert``; a test that greps source proves nothing.

The load-bearing test is ``test_golden_reproduces_a_real_live_packet``: it
reproduces, to full recorded precision, a unit the live book actually sized on a
funded account on 2026-06-18.  If the port ever drifts, that is where it shows.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.research_infra.replay_policy import (
    AccountDayState,
    DecisionCore,
    InertPolicy,
    Policy,
    PolicyCandidate,
    PolicyError,
    SleeveBookPolicy,
)
from src.research_infra.replay_policy import packet_validation as V
from src.research_infra.replay_policy.sleeve_book import _P

REPO = Path(__file__).resolve().parents[1]
DAY = "2026-06-18"


@pytest.fixture(scope="module")
def live_config() -> dict:
    """The committed live runtime block, as the live worker reads it."""

    with open(REPO / "config" / "agent_config.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)["gtos_vnext_runtime"]


@pytest.fixture
def policy(live_config) -> SleeveBookPolicy:
    return SleeveBookPolicy(live_config)


def _state(**overrides) -> AccountDayState:
    base = {
        "equity": 100000.0,
        "high_water": 100000.0,
        "realized_today_pct": 0.0,
        "open_risk_pct": 0.0,
        "max_dd_reference_equity": 100000.0,
    }
    base.update(overrides)
    return AccountDayState(**base)


def _candidate(sleeve: str, symbol: str, *, day: str = DAY, side: int = 1, **kw):
    return PolicyCandidate(
        sleeve=sleeve, symbol=symbol, direction=side, decision_day=day,
        stop_dist=kw.pop("stop_dist", 10.0), **kw,
    )


def _unit_for(decision, cluster: str):
    matches = [u for u in decision.units if u.cluster == cluster]
    assert matches, f"no unit for cluster {cluster!r}; got {[u.cluster for u in decision.units]}"
    return matches[0]


# ---------------------------------------------------------------------------
# the interface
# ---------------------------------------------------------------------------
def test_sleeve_book_satisfies_the_policy_protocol(policy):
    assert isinstance(policy, Policy)
    assert isinstance(InertPolicy(), Policy)


def test_decision_core_hosts_more_than_one_policy_and_keeps_them_attributable(policy):
    core = DecisionCore([policy, InertPolicy()])
    out = core.decide_all([_candidate("crypto", "BTCUSD")], _state())
    assert set(out) == {"sleeve_book_w7", "inert"}
    assert out["sleeve_book_w7"].units, "the book sized nothing on a valid candidate"
    assert out["inert"].units == ()


def test_decision_core_refuses_duplicate_policy_ids(policy):
    with pytest.raises(PolicyError, match="duplicate_policy_id"):
        DecisionCore([policy, SleeveBookPolicy(policy._config)])


def test_decision_core_refuses_an_empty_policy_set():
    with pytest.raises(PolicyError, match="at_least_one_policy"):
        DecisionCore([])


def test_every_hosted_policy_sees_the_same_candidates():
    """A policy that mutates its input cannot change what the next one decides."""

    class Vandal:
        policy_id = "vandal"

        def describe(self):
            return {}

        def decide(self, candidates, state):
            list(candidates).clear()
            return InertPolicy("vandal").decide(candidates, state)

    inert = InertPolicy("witness")
    core = DecisionCore([Vandal(), inert])
    out = core.decide_all([_candidate("crypto", "BTCUSD")], _state())
    assert out["witness"].diagnostics["n_candidates_in"] == 1


def test_strict_config_refuses_a_config_missing_the_dial(live_config):
    thin = {k: v for k, v in live_config.items() if k != "ultimate_book_profile"}
    with pytest.raises(PolicyError, match="missing_dial_keys.*ultimate_book_profile"):
        SleeveBookPolicy(thin)


def test_decide_never_raises_on_a_hostile_config():
    """The live book never breaks the live path; nor may the port."""

    broken = SleeveBookPolicy({"ultimate_book_profile": object()}, strict_config=False)
    decision = broken.decide([_candidate("crypto", "BTCUSD")], _state())
    assert decision.new_entries_allowed is False
    assert decision.units == ()


# ---------------------------------------------------------------------------
# the registry
# ---------------------------------------------------------------------------
def test_live_dial_resolves_the_29_sleeve_book_from_the_live_registry(policy):
    """8 core + 9 candidate + 12 market-expansion, resolved not asserted."""

    registry = policy.active_sleeves()
    assert len(registry) == 29
    assert policy.confidence_of("metals_core") == pytest.approx(1.00)
    assert policy.confidence_of("idxrev") == pytest.approx(0.15)
    assert policy.cluster_of("metals_core") == "metals"
    # clean_3 is OFF live, so its sleeves are unknown and would fail closed.
    assert "sub_xvol_pullback" not in registry


def test_registry_tracks_the_flag_rather_than_a_hardcoded_list(live_config):
    """Turning the candidate book off must shrink the registry, not a constant."""

    off = dict(live_config)
    off["ultimate_book_include_candidate_book"] = False
    off["ultimate_book_include_market_expansion_book"] = False
    assert len(SleeveBookPolicy(off).active_sleeves()) == 8


def test_the_candidate_package_sleeve_ledger_is_not_this_registry(policy):
    """The contract-bound JSONL is a different, shadow-only registry.

    `SESSION_H` calls it "your source of truth for the static registry"; it is
    not.  Its 82 rows are outcome-mined groupings of the *broad* system's
    candidate families and share zero sleeve names with the book.
    """

    path = (
        REPO
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
    )
    if not path.is_file() or path.stat().st_size < 1000:
        pytest.skip("sleeve registry ledger absent or an unhydrated LFS pointer")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    assert rows, "probe control: the ledger must parse to rows before a zero means anything"
    ledger_ids = {str(r.get("sleeve_id") or "") for r in rows}
    assert ledger_ids, "probe control: rows must carry sleeve_id"
    assert not (ledger_ids & set(policy.active_sleeves()))


# ---------------------------------------------------------------------------
# cluster collapse and the day key
# ---------------------------------------------------------------------------
def test_same_cluster_same_day_collapses_into_one_unit_and_splits_the_risk(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD"), _candidate("metals_core", "XAGUSD")],
        _state(),
    )
    unit = _unit_for(decision, "metals")
    assert unit.n_trades == 2
    assert unit.risk_pct_per_trade == pytest.approx(unit.unit_risk_pct / 2)


def test_different_clusters_stay_independent_units(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD"), _candidate("crypto", "BTCUSD")],
        _state(),
    )
    assert {u.cluster for u in decision.units} == {"metals", "crypto"}


def test_the_day_key_partitions_units_even_within_one_cluster(policy):
    """The correlated-unit key is (decision_day, cluster), so a day boundary splits."""

    decision = policy.decide(
        [
            _candidate("metals_core", "XAUUSD", day="2026-06-18"),
            _candidate("metals_core", "XAGUSD", day="2026-06-19"),
        ],
        _state(),
    )
    metals = [u for u in decision.units if u.cluster == "metals"]
    assert len(metals) == 2
    assert all(u.n_trades == 1 for u in metals)


def test_unit_confidence_is_the_strongest_member_not_the_sum(policy):
    """metals_core 1.00 with metals_ob_micro 0.30 sizes at the max, not 1.30."""

    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD"), _candidate("metals_ob_micro", "XAGUSD")],
        _state(),
    )
    unit = _unit_for(decision, "metals")
    assert set(unit.members) == {"metals_core", "metals_ob_micro"}
    kelly = _P.kelly_lite_conviction_multiplier(2, enabled=True, conservative=True)
    assert unit.confidence == pytest.approx(round(1.00 * kelly, 6))


# ---------------------------------------------------------------------------
# Kelly-lite bins
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "n_active,expected",
    [(1, 0.748), (2, 0.991), (3, 0.991), (4, 1.241), (9, 1.241)],
)
def test_half_kelly_bins_are_the_live_edges(policy, n_active, expected):
    """Live runs kelly_conservative=True, so the half-Kelly bins apply."""

    state = _state()
    state = AccountDayState(
        equity=state.equity, high_water=state.high_water,
        realized_today_pct=0.0, open_risk_pct=0.0,
        max_dd_reference_equity=state.max_dd_reference_equity,
        cycle={"n_active_override": {DAY: n_active}},
    )
    decision = policy.decide([_candidate("metals_core", "XAUUSD")], state)
    unit = _unit_for(decision, "metals")
    assert unit.confidence == pytest.approx(round(1.00 * expected, 6))
    assert any(f"_x{expected:g}" in tag for tag in unit.tags), unit.tags


def test_running_count_override_can_only_raise_the_kelly_count(policy):
    """na = max(per_cycle, running): a stale store can never size below the floor."""

    two_candidates = [_candidate("metals_core", "XAUUSD"), _candidate("crypto", "BTCUSD")]
    stale = AccountDayState(
        equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
        open_risk_pct=0.0, max_dd_reference_equity=100000.0,
        cycle={"n_active_override": {DAY: 1}},
    )
    unit = _unit_for(policy.decide(two_candidates, stale), "metals")
    assert unit.confidence == pytest.approx(round(1.00 * 0.991, 6))


# ---------------------------------------------------------------------------
# de-risk
# ---------------------------------------------------------------------------
def test_smooth_derisk_is_proportional_from_the_first_basis_point(policy):
    """cap_mult = 1 - dd/0.10, so 2% drawdown sizes at 0.80."""

    decision = policy.decide([_candidate("metals_core", "XAUUSD")], _state(equity=98000.0))
    assert decision.governor["size_cap_multiplier"] == pytest.approx(0.80)


def test_band_derisk_holds_full_size_until_the_start_band(live_config):
    """The other mode, ported too: full size to 7%, then linear to the wall."""

    banded = dict(live_config)
    banded["ultimate_book_derisk_mode"] = "band"
    # The 2.0% ceiling refuses band defense outright, so use the 1.25% dial.
    banded["ultimate_book_profile"] = "clean3_w7_measured_nom1p25"
    policy = SleeveBookPolicy(banded)
    assert policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(equity=95000.0)
    ).governor["size_cap_multiplier"] == pytest.approx(1.0)
    assert policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(equity=91500.0)
    ).governor["size_cap_multiplier"] == pytest.approx(0.5, abs=1e-4)


def test_the_ceiling_dial_fails_closed_without_smooth_defense(live_config):
    """The 2.0% dial is only certified with smooth de-risk, and refuses without it.

    The refusal happens before the governor runs, so its observable signature is
    ``governor is None`` with no units — the live decision object exposes no
    field carrying the sizing layer's own reason once a gate has overwritten the
    top-level one.  See the defect register.
    """

    banded = dict(live_config)
    banded["ultimate_book_derisk_mode"] = "band"
    decision = SleeveBookPolicy(banded).decide(
        [_candidate("metals_core", "XAUUSD")], _state()
    )
    assert decision.new_entries_allowed is False
    assert decision.units == ()
    assert decision.governor is None
    assert decision.diagnostics["sizing_refused_before_governor"] is True


def test_a_governor_block_is_distinguishable_from_a_dial_refusal(policy):
    """Both stop the book; only one means the dial is uncertified."""

    blocked = policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(realized_today_pct=-0.03)
    )
    assert blocked.new_entries_allowed is False
    assert blocked.governor is not None
    assert blocked.diagnostics["sizing_refused_before_governor"] is False


def test_reactive_ladder_shrinks_and_is_labelled(policy):
    state = AccountDayState(
        equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
        open_risk_pct=0.0, max_dd_reference_equity=100000.0,
        cycle={"stress_state": _P.StressDeriskState(consecutive_loss_days=1)},
    )
    unit = _unit_for(policy.decide([_candidate("metals_core", "XAUUSD")], state), "metals")
    baseline = _unit_for(policy.decide([_candidate("metals_core", "XAUUSD")], _state()), "metals")
    assert unit.unit_risk_pct == pytest.approx(baseline.unit_risk_pct * 0.80)
    assert "ladder_step1" in unit.tags


def test_the_reactive_overlay_can_only_ever_shrink(policy):
    """Floor 0.60; ladder x coloss cannot compound below it, and never widens."""

    worst = AccountDayState(
        equity=100000.0, high_water=100000.0, realized_today_pct=0.0,
        open_risk_pct=0.0, max_dd_reference_equity=100000.0,
        cycle={
            "stress_state": _P.StressDeriskState(
                consecutive_loss_days=9, trailing_neg_frac=1.0
            )
        },
    )
    unit = _unit_for(policy.decide([_candidate("metals_core", "XAUUSD")], worst), "metals")
    baseline = _unit_for(policy.decide([_candidate("metals_core", "XAUUSD")], _state()), "metals")
    assert unit.unit_risk_pct == pytest.approx(baseline.unit_risk_pct * 0.60)


# ---------------------------------------------------------------------------
# governor gates and gross-cap shedding
# ---------------------------------------------------------------------------
def test_soft_daily_stop_blocks_new_entries(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(realized_today_pct=-0.03)
    )
    assert decision.new_entries_allowed is False
    assert decision.reason == "soft_daily_stop_reached"


def test_gross_cap_exhaustion_blocks_new_entries(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(open_risk_pct=0.04)
    )
    assert decision.new_entries_allowed is False
    assert decision.reason == "gross_risk_cap_exhausted"


def _four_cluster_candidates():
    return [
        _candidate("metals_core", "XAUUSD"),
        _candidate("crypto", "BTCUSD"),
        _candidate("energy_agri", "USOIL_cash"),
        _candidate("idxrev", "UK100"),
    ]


def test_gross_cap_shedding_zeroes_the_unit_and_labels_it(policy):
    decision = policy.decide(_four_cluster_candidates(), _state(open_risk_pct=0.0350))
    assert decision.new_entries_allowed is True
    shed = [u for u in decision.units if not u.sized]
    assert shed, "the cap did not bind; the test would prove nothing"
    for unit in shed:
        assert unit.reason == "gross_risk_cap_would_exceed"
        assert unit.unit_risk_pct == 0.0
        assert unit.risk_pct_per_trade == 0.0
        assert unit.confidence > 0.0

    # D5 FIXED 2026-07-27: the shed unit now KEEPS its overlays_applied audit trail. The rebuild used
    # to omit the 9th field (admission.py:1337-1338), so a shed unit kept its confidence but lost the
    # record of why it had that confidence. This assertion used to read `unit.tags == ()` and pinned
    # the defect; it now pins the repair.
    #
    # Asserted against a POSITIVE CONTROL rather than "is non-empty": the same run's ADMITTED units
    # must carry the same kelly tag, so a regression that stripped tags from every unit (not just shed
    # ones) cannot make this test pass vacuously.
    admitted_tags = {t for u in decision.units if u.sized for t in u.tags}
    assert admitted_tags, "no admitted unit carried a tag; the tag assertion below would be vacuous"
    for unit in shed:
        assert set(unit.tags) & admitted_tags, (
            f"shed unit {unit.cluster} lost its sizing audit trail: tags={unit.tags!r}, "
            f"admitted units carried {sorted(admitted_tags)!r}"
        )


def test_gross_cap_shedding_is_first_fit_not_lowest_conviction_first(policy):
    """Pins the ACTUAL shed behaviour, which contradicts its own comment.

    ``admission.py:1320-1324`` says the descending-conviction order means the cap
    "sheds the LOWEST-conviction units first (it must NEVER starve the
    highest-conviction metals_core)".  It is a first-fit-descending greedy: each
    unit is tested against the *remaining* headroom in conviction order, so a
    large high-conviction unit that does not fit is shed while a small
    low-conviction unit that does fit is admitted.

    At 0.0150 headroom this admits ``idxrev`` (confidence 0.186, the weakest unit
    in the book) and sheds ``metals_core`` (confidence 1.241, the strongest) —
    exactly the outcome the comment says is impossible.  Ported faithfully; see
    the defect register for the correct behaviour and its value.
    """

    decision = policy.decide(_four_cluster_candidates(), _state(open_risk_pct=0.0250))
    sized = {u.cluster: u for u in decision.units if u.sized}
    shed = {u.cluster: u for u in decision.units if not u.sized}
    assert set(sized) == {"index"}, {k: v.confidence for k, v in sized.items()}
    assert "metals" in shed
    assert shed["metals"].confidence > sized["index"].confidence


def test_gross_cap_leaves_headroom_unused_when_the_shed_binds(policy):
    """A consequence of first-fit: admitted risk can sit well below the cap."""

    decision = policy.decide(_four_cluster_candidates(), _state())
    admitted = sum(u.unit_risk_pct for u in decision.units if u.sized)
    requested = 0.02 * sum(
        u.confidence for u in decision.units
    )  # every unit's confidence at the live nominal dial
    assert any(not u.sized for u in decision.units)
    assert admitted < 0.04, "the cap is 4%; admitted risk must respect it"
    assert admitted < requested


def test_metals_core_is_decided_first_when_headroom_admits_it(policy):
    """The comment's claim DOES hold while the cap binds only partially."""

    decision = policy.decide(_four_cluster_candidates(), _state())
    sized = {u.cluster for u in decision.units if u.sized}
    assert "metals" in sized


def test_circuit_breaker_blocks_everything(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD")], _state(operator_circuit_breaker=True)
    )
    assert decision.new_entries_allowed is False
    assert decision.reason == "circuit_breaker_open"


# ---------------------------------------------------------------------------
# fail-closed sizing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"stop_dist": 0.0}, "fail_closed:nonpositive_stop"),
        ({"side": 0}, "fail_closed:bad_direction"),
    ],
)
def test_a_bad_member_fails_its_whole_cluster_day_unit_closed(policy, kwargs, expected):
    decision = policy.decide([_candidate("metals_core", "XAUUSD", **kwargs)], _state())
    unit = _unit_for(decision, "metals")
    assert unit.sized is False
    assert unit.unit_risk_pct == 0.0
    assert unit.reason.startswith(expected)


def test_one_bad_member_zeroes_the_unit_its_healthy_sibling_shared(policy):
    """Fail-closed is unit-wide, not per-intent.  Ported as-is."""

    decision = policy.decide(
        [
            _candidate("metals_core", "XAUUSD"),
            _candidate("metals_softband", "XAGUSD", stop_dist=-1.0),
        ],
        _state(),
    )
    assert _unit_for(decision, "metals").sized is False


def test_an_unknown_sleeve_fails_closed_rather_than_sizing_at_zero_confidence(policy):
    decision = policy.decide([_candidate("not_a_sleeve", "XAUUSD")], _state())
    assert all(not u.sized for u in decision.units)
    assert any("unknown_sleeve" in u.reason for u in decision.units)


# ---------------------------------------------------------------------------
# authority is not the same question as the governor gate
# ---------------------------------------------------------------------------
def test_shadow_mode_still_reports_the_sized_book(policy):
    """live_activation_allowed=false suppresses placement, not sizing.

    Reading realized_units as "the decision" would make every shadow cycle look
    like a no-op — which is how ~99k live packets would read as an empty book.
    """

    decision = policy.decide([_candidate("metals_core", "XAUUSD")], _state())
    assert decision.authority["runtime_effect_now"] is False
    assert decision.authority["realized_unit_count"] == 0
    assert decision.units and decision.units[0].sized


def test_missing_cycle_inputs_are_reported_not_hidden(policy):
    decision = policy.decide([_candidate("metals_core", "XAUUSD")], _state())
    supplied = decision.diagnostics["cycle_inputs_supplied"]
    assert supplied["stress_state"] is False
    assert supplied["n_active_override"] is False


# ---------------------------------------------------------------------------
# allocations carry the OD-1 portfolio contract
# ---------------------------------------------------------------------------
def test_allocations_expose_symbol_side_stop_size_and_provenance(policy):
    decision = policy.decide(
        [_candidate("crypto", "BTCUSD", side=-1, stop_dist=900.0, entry_ref=62487.45)],
        _state(),
    )
    (allocation,) = decision.allocations
    assert allocation.symbol == "BTCUSD"
    assert allocation.side == -1
    assert allocation.entry == pytest.approx(62487.45)
    assert allocation.stop_dist == pytest.approx(900.0)
    assert allocation.size_risk_pct > 0
    assert allocation.provenance["sleeve"] == "crypto"
    assert allocation.provenance["policy_id"] == "sleeve_book_w7"


def test_total_risk_pct_counts_only_sized_units(policy):
    decision = policy.decide(
        [_candidate("metals_core", "XAUUSD"), _candidate("not_a_sleeve", "UK100")],
        _state(),
    )
    assert decision.total_risk_pct == pytest.approx(
        sum(u.unit_risk_pct for u in decision.units if u.sized)
    )


# ---------------------------------------------------------------------------
# the golden test: a real unit the live book sized on a funded account
# ---------------------------------------------------------------------------
def test_golden_reproduces_a_real_live_packet(live_config):
    """Reproduce a recorded live decision exactly.

    Source: runtime-learning packet ``unit_placed``, namespace
    ``operator_profile``, ``created_at_utc 2026-06-18T17:15:47``,
    ``candidate_id W7_BOOK::crypto::BTCUSD::2026-06-18::SHORT::ny_crypto_momentum``.
    Recorded unit: two BTCUSD/ETHUSD legs of ``ny_crypto_momentum``, Kelly count
    3 under half-Kelly, ladder step 1, governor multiplier 0.650855.
    """

    recorded = {
        "cluster": "crypto",
        "confidence": 0.27748,
        "n_trades": 2,
        "overlays_applied": ["kelly_lite_na3_x0.991", "ladder_step1"],
        "reason": "sized",
        "risk_pct_per_trade": 0.00180599,
        "sized": True,
        "sleeve_members": ["ny_crypto_momentum"],
        "unit_risk_pct": 0.00361198,
    }
    cap_mult = 0.650855
    # Invert the recorded governor multiplier into the equity that produces it.
    equity = 100000.0 * (1.0 - 0.10 * (1.0 - cap_mult))
    state = AccountDayState(
        equity=equity, high_water=100000.0, realized_today_pct=0.0,
        open_risk_pct=0.0, max_dd_reference_equity=100000.0,
        cycle={
            "n_active_override": {DAY: 3},
            "stress_state": _P.StressDeriskState(consecutive_loss_days=1),
        },
    )
    decision = SleeveBookPolicy(live_config).decide(
        [
            _candidate("ny_crypto_momentum", "BTCUSD", side=-1),
            _candidate("ny_crypto_momentum", "ETHUSD", side=-1),
        ],
        state,
    )
    assert decision.governor["size_cap_multiplier"] == pytest.approx(cap_mult, abs=5e-7)
    unit = _unit_for(decision, "crypto")
    assert list(unit.members) == recorded["sleeve_members"]
    assert unit.n_trades == recorded["n_trades"]
    assert unit.confidence == pytest.approx(recorded["confidence"], abs=1e-6)
    assert unit.unit_risk_pct == pytest.approx(recorded["unit_risk_pct"], abs=1e-8)
    assert unit.risk_pct_per_trade == pytest.approx(
        recorded["risk_pct_per_trade"], abs=1e-8
    )
    assert list(unit.tags) == recorded["overlays_applied"]
    assert unit.reason == recorded["reason"]


# ---------------------------------------------------------------------------
# the validation harness itself
# ---------------------------------------------------------------------------
def test_iter_packets_refuses_an_unhydrated_lfs_pointer(tmp_path):
    """A pointer read as data is indistinguishable from an empty result."""

    stub = tmp_path / "packets.jsonl"
    stub.write_text(
        "version https://git-lfs.github.com/spec/v1\noid sha256:0\nsize 1\n",
        encoding="utf-8",
    )
    with pytest.raises(V.ValidationError, match="unhydrated_lfs_pointer"):
        list(V.iter_packets(stub))


def test_iter_packets_refuses_a_missing_source(tmp_path):
    with pytest.raises(V.ValidationError, match="packet_source_absent"):
        list(V.iter_packets(tmp_path / "nope.jsonl"))


def test_direction_recovery_reports_whether_it_was_actually_recorded():
    assert V._direction_of({"direction": -1}) == (-1, True)
    assert V._direction_of({"direction": "SHORT"}) == (-1, True)
    assert V._direction_of(
        {"candidate_id": "W7_BOOK::crypto::BTCUSD::2026-06-18::SHORT::x"}
    ) == (-1, True)
    # The common case in the real export: absent, so defaulted and flagged.
    assert V._direction_of({"direction": None}) == (1, False)


def test_recorded_na_values_surfaces_more_than_one_kelly_count():
    units = [
        {"overlays_applied": ["kelly_lite_na9_x1.241"]},
        {"overlays_applied": ["kelly_lite_na1_x0.748"]},
    ]
    assert V.recorded_na_values(units) == [1, 9]


def test_governor_inversion_reproduces_the_multiplier_it_was_given():
    for cap in (1.0, 0.9, 0.650855, 0.5):
        state, limits = _state_from(cap)
        # D8 FIXED 2026-07-27: an ENABLED book now fails closed on a missing dial key rather than
        # silently defaulting it (bridge.REQUIRED_DIAL_KEYS), so this config must declare the full
        # dial. It previously leaned on `strict_config=False` to skip the policy's own check and then
        # on DEFAULT_CONFIG to supply the rest -- i.e. it was measuring governor inversion on a book
        # sized partly from the 1.25% first-cycle defaults while naming the 2.00% ceiling profile.
        # Declaring the dial explicitly is what the test always meant; `strict_config=False` now only
        # documents that the policy's own pre-check is not what is under test here.
        policy_cfg = {
            "ultimate_book_profile": "clean3_w7_ceiling_nom2p00",
            "ultimate_book_derisk_mode": "smooth",
            "ultimate_book_enabled": True,
            "ultimate_book_include_clean3": False,
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_kelly_lite": True,
            "ultimate_book_kelly_conservative": True,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_drop_w7_symbols": True,
        }
        decision = SleeveBookPolicy(policy_cfg, strict_config=False).decide(
            [_candidate("metals_core", "XAUUSD")],
            AccountDayState(
                equity=state.equity, high_water=state.high_water,
                realized_today_pct=0.0, open_risk_pct=0.0,
                max_dd_reference_equity=state.max_dd_reference_equity,
                cycle={"limits": limits},
            ),
        )
        assert decision.governor["size_cap_multiplier"] == pytest.approx(cap, abs=5e-7)


def _state_from(cap_mult: float):
    return V._state_reproducing_governor(
        {
            "allow_new_entries": True,
            "size_cap_multiplier": cap_mult,
            "available_gross_risk_pct": 0.04,
            "reason": "ok",
        },
        derisk_mode="smooth",
    )


def test_an_empty_cycle_is_compared_not_skipped():
    cycle = V.Cycle(
        cycle_id="ns|t|d",
        namespace="ns",
        created_at_utc="2026-06-18T00:00:00+00:00",
        bridge={"n_candidates_in": 0, "would_units": [], "decision_status": "no_candidates_this_bar"},
        packets=[{"event_type": "cycle_no_candidates", "namespace": "ns"}],
    )
    result = V.reconstruct_cycle(cycle)
    assert result.status == V.MATCH
    assert result.detail["kind"] == "empty_cycle"


def test_a_cycle_with_two_kelly_counts_is_reported_not_forced():
    cycle = V.Cycle(
        cycle_id="ns|t|d",
        namespace="ns",
        created_at_utc="2026-06-18T00:00:00+00:00",
        bridge={
            "n_candidates_in": 2,
            "governor": {"allow_new_entries": True, "size_cap_multiplier": 1.0,
                         "available_gross_risk_pct": 0.04, "reason": "ok"},
            "would_units": [
                {"cluster": "index", "sleeve_members": ["idxrev"],
                 "overlays_applied": ["kelly_lite_na9_x1.241"]},
                {"cluster": "crypto", "sleeve_members": ["vol_compression"],
                 "overlays_applied": ["kelly_lite_na1_x0.748"]},
            ],
        },
        packets=[
            {"event_type": "unit_admitted", "namespace": "ns", "sleeve": "idxrev",
             "symbol": "UK100", "decision_day": DAY},
        ],
    )
    result = V.reconstruct_cycle(cycle)
    assert result.status == V.MULTI_DAY_KELLY
    assert result.detail["recorded_na_values"] == [1, 9]


def test_an_unverifiable_governor_reconstruction_is_a_gap_not_a_match(live_config):
    """A reconstruction that cannot reproduce the record is never trusted."""

    cycle = V.Cycle(
        cycle_id="ns|t|d",
        namespace="ns",
        created_at_utc="2026-06-18T00:00:00+00:00",
        bridge={
            "profile": "clean3_w7_ceiling_nom2p00",
            "derisk_mode": "smooth",
            "n_candidates_in": 1,
            # An impossible pairing: full size with the daily stop tripped.
            "governor": {"allow_new_entries": True, "size_cap_multiplier": 1.0,
                         "available_gross_risk_pct": 0.04,
                         "reason": "soft_daily_stop_reached"},
            "would_units": [
                {"cluster": "metals", "sleeve_members": ["metals_core"], "n_trades": 1,
                 "confidence": 1.0, "risk_pct_per_trade": 0.02, "unit_risk_pct": 0.02,
                 "sized": True, "reason": "sized", "overlays_applied": []},
            ],
        },
        packets=[
            {"event_type": "unit_admitted", "namespace": "ns", "sleeve": "metals_core",
             "symbol": "XAUUSD", "decision_day": DAY, "direction": 1},
        ],
    )
    result = V.reconstruct_cycle(cycle, base_config=live_config)
    assert result.status == V.EVIDENCE_GAP
    assert result.detail["reason"] == "governor_reconstruction_unverified"


def test_config_from_bridge_prefers_the_recorded_flags_over_the_current_yaml(live_config):
    """Replaying today's dial against yesterday's decisions is not a replay."""

    cfg = V.config_from_bridge(
        {"profile": "clean3_w7_measured_nom1p25", "kelly_conservative": False},
        base=live_config,
    )
    assert cfg["ultimate_book_profile"] == "clean3_w7_measured_nom1p25"
    assert cfg["ultimate_book_kelly_conservative"] is False


def test_ledger_pair_writes_a_byte_identical_null_control(tmp_path):
    result = V.CycleResult(
        cycle_id="c", namespace="ns", created_at_utc="t", decision_day=DAY,
        status=V.MATCH,
        policy_units=[
            {"cluster": "metals", "sleeve_members": ["metals_core"], "n_trades": 1,
             "confidence": 1.0, "risk_pct_per_trade": 0.02, "unit_risk_pct": 0.02,
             "sized": True, "reason": "sized", "overlays_applied": []}
        ],
    )
    result.live_units = list(result.policy_units)
    dirs = V.ledger_pair([result], tmp_path)
    policy_file = next(dirs["policy"].glob("*_ORDER_LEDGER.jsonl"))
    null_file = next(dirs["null_control"].glob("*_ORDER_LEDGER.jsonl"))
    assert policy_file.read_bytes() == null_file.read_bytes()
    row = json.loads(policy_file.read_text(encoding="utf-8").splitlines()[0])
    assert row[V.IDENTITY_FIELD].startswith("ns|c|metals|metals_core")


# ---------------------------------------------------------------------------
# regression pins for three defects adversarial review found in the COMPARATOR
#
# None of the 52 tests above could have caught these: they exercise the policy,
# and all three were in the measuring harness around it. A validated port
# measured by an unvalidated comparator is not a validated result.
# ---------------------------------------------------------------------------
def test_an_empty_cycle_match_is_earned_by_actually_invoking_the_policy():
    """The empty-cycle branch must run the policy, not shortcut to MATCH.

    It used to return MATCH before constructing SleeveBookPolicy, which made
    4,306 of 4,908 reported matches free greens on a comparison that never ran.
    """

    cycle = V.Cycle(
        cycle_id="ns|t|d", namespace="ns", created_at_utc="2026-06-18T00:00:00+00:00",
        bridge={"n_candidates_in": 0, "would_units": [],
                "decision_status": "no_candidates_this_bar",
                "profile": "clean3_w7_ceiling_nom2p00", "derisk_mode": "smooth"},
        packets=[{"event_type": "cycle_no_candidates", "namespace": "ns"}],
    )
    result = V.reconstruct_cycle(cycle)
    assert result.status == V.MATCH
    assert result.detail["kind"] == "empty_cycle"
    # The policy ran: policy_units is populated (empty list), not left unset.
    assert result.policy_units == []


def test_an_empty_cycle_where_the_policy_sizes_something_is_a_disagreement(monkeypatch):
    """Mutation control on the branch above: a hallucinating policy must fail it."""

    class Hallucinating:
        def __init__(self, *a, **k):
            pass

        def decide(self, candidates, state):
            from src.research_infra.replay_policy.core import PolicyDecision, PolicyUnit

            return PolicyDecision(
                policy_id="x", new_entries_allowed=True, reason="ok",
                units=(PolicyUnit("metals", ("metals_core",), 1, 1.0, 0.02, 0.02,
                                  True, "sized"),),
            )

    monkeypatch.setattr(V, "SleeveBookPolicy", Hallucinating)
    cycle = V.Cycle(
        cycle_id="ns|t|d", namespace="ns", created_at_utc="2026-06-18T00:00:00+00:00",
        bridge={"n_candidates_in": 0, "would_units": []},
        packets=[{"event_type": "cycle_no_candidates", "namespace": "ns"}],
    )
    result = V.reconstruct_cycle(cycle)
    assert result.status == V.PORT_OR_LIVE_DEFECT
    assert result.field_differences[0]["field"] == "__present__"


def test_duplicate_cluster_member_units_do_not_collapse_into_one():
    """Two units can share (cluster, sleeve_members) legitimately.

    The correlated-unit key is (decision_day, cluster), so a cycle spanning two
    decision days emits two `index|idxrev` units. Keying the comparison on
    (cluster, members) alone silently dropped one and returned MATCH.
    """

    unit = {
        "cluster": "index", "sleeve_members": ["idxrev"], "n_trades": 1,
        "confidence": 0.1, "risk_pct_per_trade": 0.001, "unit_risk_pct": 0.001,
        "sized": True, "reason": "sized", "overlays_applied": [],
    }
    other = {**unit, "confidence": 0.2, "unit_risk_pct": 0.002,
             "risk_pct_per_trade": 0.002}
    status, differences = V._compare_units([unit], [unit, other])
    assert status == V.PORT_OR_LIVE_DEFECT, differences
    assert any(d["field"] == "__present__" for d in differences)


def test_two_identical_units_on_both_sides_still_match():
    """The occurrence key must not manufacture a difference from duplication."""

    unit = {
        "cluster": "index", "sleeve_members": ["idxrev"], "n_trades": 1,
        "confidence": 0.1, "risk_pct_per_trade": 0.001, "unit_risk_pct": 0.001,
        "sized": True, "reason": "sized", "overlays_applied": [],
    }
    status, differences = V._compare_units([unit, unit], [unit, unit])
    assert status == V.MATCH
    assert differences == []


def test_direction_recovery_reads_the_nested_admission_unit_members():
    """The third source, and the only one on 277 real packets."""

    packet = {
        "sleeve": "idxrev", "symbol": "UK100", "direction": None,
        "outcome": {"admission_unit_members": [
            {"sleeve": "idxrev", "symbol": "UK100", "direction": "SHORT"},
        ]},
    }
    assert V._direction_of(packet) == (-1, True)


def test_direction_recovery_ignores_a_member_for_a_different_symbol():
    """A unit's members can span symbols; the side must not be taken from a sibling."""

    packet = {
        "sleeve": "idxrev", "symbol": "UK100", "direction": None,
        "outcome": {"admission_unit_members": [
            {"sleeve": "idxrev", "symbol": "JP225", "direction": "SHORT"},
        ]},
    }
    assert V._direction_of(packet) == (1, False)

"""Behavioural tests for the packet-emitter hardening carry (Session P, B200-B219).

These assert behaviour, not source text. Several encode a measurement taken from the 99,112-packet
live export at `/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/` so that a
later change which breaks the measured semantics fails here rather than silently in the evidence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.components.ultimate_book.packet_economics import (
    TRANSFERRED,
    MEASURED,
    MODELLED,
    UNAVAILABLE,
    build_cost_block,
    build_economics_block,
    build_governor_block,
    build_holding_block,
    rollover_nights_crossed,
    weakest,
)
from src.components.ultimate_book.packet_guard import GuardedPacketWriter
from src.components.ultimate_book.runtime_learning_packet import (
    PACKET_ECONOMICS_KEY,
    PACKET_REJECTED_EVENT_TYPE,
    RuntimeLearningPacketWriter,
    build_packet_rejected_marker,
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)

FTMO = "FTMO-Server3"


def _writer(tmp_path):
    return RuntimeLearningPacketWriter(tmp_path, "shadow_logs/packets.jsonl")


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --------------------------------------------------------------------------------------
# 1. The guard: fail closed, never stop the book, never drop silently
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        [None],
        [{}],
        [{"event_type": "not_a_real_event"}],
        [{"packet_hash_sha256": object()}],
        ["a string, not a mapping"],
        [42],
        [{"event_type": "unit_placed", "outcome": {"self": None}}],
    ],
)
def test_guard_never_raises_on_any_input(tmp_path, payload):
    """The whole contract in one test: nothing the caller can pass makes the guard raise.

    A validator that can raise into the decision path is worse than no validator, because the
    live book's builder call sites are unguarded and an exception there aborts the tick before
    entries are placed.
    """
    guard = GuardedPacketWriter(_writer(tmp_path))
    report = guard.append_many(payload)  # must not raise
    assert report.submitted == len(payload or [])


def test_guard_writes_a_rejection_marker_into_the_main_log(tmp_path):
    """A refused packet leaves a hole; the marker is what makes the hole visible.

    This is the anti-false-green requirement. Recording the casualty only in the cycle summary --
    what the previous implementation did -- means a consumer reading the packet log alone sees a
    complete-looking stream that silently lost rows.
    """
    guard = GuardedPacketWriter(_writer(tmp_path))
    good = build_runtime_learning_packet(
        namespace="ns", event_type="unit_placed", outcome={"placement_status": "placed"}
    )
    report = guard.append_many([good, {"event_type": "bogus", "namespace": "ns"}])

    assert report.accepted == 1
    assert report.quarantined == 1
    assert report.unrecorded == 0

    rows = _read(tmp_path / "shadow_logs/packets.jsonl")
    assert [r["event_type"] for r in rows] == ["unit_placed", PACKET_REJECTED_EVENT_TYPE]

    marker = rows[1]
    assert marker["outcome"]["rejected_event_type"] == "bogus"
    assert marker["outcome"]["quarantined"] is True
    assert marker["outcome"]["rejection_issue_count"] >= 1
    # The marker must itself be a valid packet, or it is just a second class of corruption.
    assert validate_runtime_learning_packet(marker) == (True, [])


def test_guard_quarantines_the_full_body_not_just_the_issues(tmp_path):
    guard = GuardedPacketWriter(_writer(tmp_path))
    bad = {"event_type": "bogus", "namespace": "ns", "payload_we_must_not_lose": [1, 2, 3]}
    guard.append_many([bad])

    quarantined = _read(guard.quarantine_path)
    assert len(quarantined) == 1
    assert quarantined[0]["packet"]["payload_we_must_not_lose"] == [1, 2, 3]
    assert quarantined[0]["issues"]


def test_guard_does_not_discard_the_batch_when_one_packet_is_bad(tmp_path):
    """The old writer raised on the first invalid packet, discarding every valid one with it."""
    guard = GuardedPacketWriter(_writer(tmp_path))
    packets = [
        build_runtime_learning_packet(
            namespace="ns", event_type="unit_placed", outcome={"placement_status": str(i)}
        )
        for i in range(3)
    ]
    packets.insert(1, {"event_type": "bogus"})

    report = guard.append_many(packets)
    assert report.accepted == 3
    assert report.quarantined == 1

    kept = [r for r in _read(tmp_path / "shadow_logs/packets.jsonl") if r["event_type"] == "unit_placed"]
    assert len(kept) == 3


def test_rejection_marker_survives_a_packet_full_of_forbidden_keys(tmp_path):
    """The marker is built from a fixed template, so it cannot inherit the rejection reason."""
    marker = build_packet_rejected_marker(
        namespace="ns",
        rejected_event_type="unit_placed",
        rejected_packet_hash="deadbeef",
        issues=["forbidden_raw_keys:account_login,ticket", "packet_hash_mismatch"],
        quarantined=True,
    )
    ok, issues = validate_runtime_learning_packet(marker)
    assert ok, issues


# --------------------------------------------------------------------------------------
# 2. Holding time and its provenance
# --------------------------------------------------------------------------------------


def test_holding_prefers_broker_truth_and_labels_it_measured():
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-01T10:00:00+00:00",
            "placement_observed_at_utc": "2026-07-01T09:59:58.8+00:00",
            "broker_exit_time_utc": "2026-07-01T14:00:00+00:00",
            "closed_at_utc": "2026-07-01T14:00:27+00:00",
        },
        server=FTMO,
    )
    assert block["entry_source_field"] == "broker_fill_time_utc"
    assert block["exit_source_field"] == "broker_exit_time_utc"
    assert block["holding_provenance"] == MEASURED
    assert block["holding_seconds"] == pytest.approx(4 * 3600)


def test_holding_falls_back_to_poll_observations_and_says_so():
    """Measured on the live export: 53 of 151 closes have no broker exit deal. Those holds are
    still usable -- but a reader must be able to tell them from the measured ones.

    AMENDED: this originally used `management_checked_at_utc` as the exit, which encoded the
    censored-hold defect (see section 9). `closed_at_utc` is the correct poll-side fallback -- the
    book sets it only when it actually observed a close.
    """
    block = build_holding_block(
        {
            "placement_observed_at_utc": "2026-07-01T10:00:00+00:00",
            "closed_at_utc": "2026-07-01T12:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["entry_provenance"] == MODELLED
    assert block["exit_provenance"] == MODELLED
    assert block["holding_provenance"] == MODELLED
    assert block["holding_seconds"] == pytest.approx(2 * 3600)


def test_holding_publishes_the_observation_lag_rather_than_hiding_it():
    """The lags are the honest part: entry -1.2 s and exit +26.8 s are the measured medians."""
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-01T10:00:00+00:00",
            "placement_observed_at_utc": "2026-07-01T09:59:58.77+00:00",
            "broker_exit_time_utc": "2026-07-01T14:00:00+00:00",
            "closed_at_utc": "2026-07-01T14:00:26.8+00:00",
        },
        server=FTMO,
    )
    assert block["entry_observation_lag_seconds"] == pytest.approx(-1.23)
    assert block["exit_observation_lag_seconds"] == pytest.approx(26.8)


def test_holding_block_is_absent_rather_than_null_when_there_is_no_entry():
    """A block of nulls is indistinguishable from a block that was never filled."""
    assert build_holding_block({"reason": "no_candidates"}) is None
    assert build_holding_block(None) is None


def test_open_position_gets_a_censored_hold_not_a_missing_one():
    block = build_holding_block(
        {"broker_fill_time_utc": "2026-07-01T10:00:00+00:00"}, server=FTMO
    )
    assert block["position_open_at_emit"] is True
    assert block["holding_seconds"] is None
    assert block["holding_provenance"] == UNAVAILABLE


# --------------------------------------------------------------------------------------
# 3. Carry nights -- the field that decides OD-3's dominant uncertainty
# --------------------------------------------------------------------------------------


def test_a_full_week_charges_seven_nights_not_five():
    """The exact error Session N shipped and then withdrew.

    Scaling a horizon by 5/7 because weekend midnights are not charged reads the rule half way:
    the weekend is collected on the triple-swap weekday at weight 3.0, so a full week charges
    seven. Every H4 ceiling was understated 1.40x by the missing half.
    """
    nights, detail = rollover_nights_crossed(
        datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),   # Monday
        datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc),  # the following Monday
        server=FTMO,
    )
    assert nights == 7.0
    # Wednesday carries the weekend at weight 3; Sat/Sun carry nothing of their own.
    assert any(c.endswith("x3") for c in detail["crossings"])
    assert len(detail["crossings"]) == 5


def test_a_twelve_hour_hold_over_the_triple_swap_weekday_charges_three():
    """Session N's withdrawn claim was that the JPY sleeves 'cannot pay three nights of carry no
    matter what is assumed'. A 12 h hold crossing a Wednesday broker midnight charges exactly 3."""
    nights, _ = rollover_nights_crossed(
        datetime(2026, 7, 7, 20, 0, tzinfo=timezone.utc),  # Tue 23:00 broker wall
        datetime(2026, 7, 8, 8, 0, tzinfo=timezone.utc),
        server=FTMO,
    )
    assert nights == 3.0


def test_nights_are_counted_on_the_broker_clock_not_utc():
    """Broker wall = America/New_York + 7 h, so in summer the swap instant is 21:00 UTC.

    A two-hour hold from 20:00 to 22:00 UTC on a Monday crosses **no UTC midnight** and exactly
    **one** broker midnight (Tuesday's, at 21:00 UTC). Counting nights on the UTC calendar would
    charge this hold nothing.
    """
    nights, detail = rollover_nights_crossed(
        datetime(2026, 7, 6, 20, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 6, 22, 0, tzinfo=timezone.utc),
        server=FTMO,
    )
    assert nights == 1.0
    assert detail["crossings"] == ["2026-07-07x1"]
    assert detail["basis"] == "broker_wall_midnight"
    # The same window on the UTC calendar crosses nothing -- which is the whole point.
    assert datetime(2026, 7, 6, 20, 0).date() == datetime(2026, 7, 6, 22, 0).date()


def test_unknown_server_fails_closed_without_raising():
    """`resolve_rule` raises by design. Inside a live book that must become a refusal, not a crash."""
    nights, detail = rollover_nights_crossed(
        datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
        server="Some-Unmeasured-Server",
    )
    assert nights is None
    assert detail["error"] == "unknown_broker_clock_rule"


def test_night_crossings_are_published_so_the_total_can_be_disagreed_with():
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_exit_time_utc": "2026-07-09T12:00:00+00:00",
        },
        server=FTMO,
    )
    crossings = block["rollover_detail"]["crossings"]
    assert crossings, "a total without its inputs is the error class this block exists to prevent"
    assert block["rollover_nights"] == sum(float(c.rsplit("x", 1)[1]) for c in crossings)


# --------------------------------------------------------------------------------------
# 4. Cost: realized separated from modelled, absence separated from zero
# --------------------------------------------------------------------------------------


def test_cost_names_what_is_missing_rather_than_charging_zero():
    """Charging zero for an unknown cost is the F38 defect itself."""
    block = build_cost_block(
        {"broker_exit_commission": -3.5, "broker_exit_swap": -1.25}
    )
    assert block["realized_complete"] is False
    assert "broker_entry_commission" in block["realized_components_missing"]
    assert block["realized_cost_currency_total"] is None, "a partial sum is a wrong number"


def test_cost_totals_only_when_every_component_is_present():
    block = build_cost_block(
        {
            "broker_entry_commission": -3.5,
            "broker_entry_swap": 0.0,
            "broker_exit_commission": -3.5,
            "broker_exit_swap": -1.25,
            "broker_exit_fee": 0.0,
        }
    )
    assert block["realized_complete"] is True
    assert block["realized_cost_currency_total"] == pytest.approx(-8.25)


def test_modelled_and_realized_are_never_collapsed_into_one_number():
    """F38 and F39 were both invisible because a single net figure hid which component was wrong."""
    block = build_cost_block({"modelled_cost_r": 0.11, "broker_exit_commission": -3.5})
    assert block["modelled_cost_r"] == 0.11
    assert block["modelled_cost_provenance"] == MODELLED
    assert block["realized_provenance"] == MEASURED
    assert "net" not in block and "cost_error" not in block


# --------------------------------------------------------------------------------------
# 5. Governor: raw inputs, so the shed stops being self-validating
# --------------------------------------------------------------------------------------


class _Gov:
    equity = 101_250.0
    high_water = 102_000.0
    realized_today_pct = -0.004
    open_risk_pct = 0.0186
    operator_circuit_breaker = False
    max_dd_reference_equity = 100_000.0


class _Limits:
    gross_open_risk_cap_pct = 0.04
    soft_daily_stop_pct = 0.03
    max_dd_limit_pct = 0.10
    max_dd_entry_block_pct = 0.08
    derisk_start_dd_pct = 0.05
    derisk_mode = "smooth"
    profit_target_pct = 0.10


def test_governor_emits_the_raw_inputs_the_shed_arithmetic_needs():
    """Today only `available_gross_risk_pct` (= cap - open_risk) reaches a packet, and the cap is
    dynamically tightened at runtime -- so the difference alone is uninterpretable and utilization
    cannot be recovered. Emitting cap and open_risk separately is what makes the shed checkable."""
    block = build_governor_block(_Gov(), limits=_Limits(), day_anchor_equity=101_657.0)
    assert block["equity"] == 101_250.0
    assert block["open_risk_pct"] == 0.0186
    assert block["gross_open_risk_cap_pct"] == 0.04
    assert block["gross_cap_utilization"] == pytest.approx(0.465, abs=1e-3)
    assert block["gross_cap_bound"] is False


def test_governor_emits_the_day_anchor_that_realized_today_pct_discards():
    """`GovernorState` consumes the anchor to compute realized_today_pct and then drops it. Without
    it, checking the daily-loss band means re-deriving it from the number being checked."""
    block = build_governor_block(_Gov(), limits=_Limits(), day_anchor_equity=101_657.0)
    assert block["day_anchor_equity"] == 101_657.0
    recomputed = (block["equity"] - block["day_anchor_equity"]) / block["day_anchor_equity"]
    assert recomputed == pytest.approx(block["realized_today_pct"], abs=1e-5)


def test_governor_block_degrades_field_by_field_never_raises():
    class Hostile:
        @property
        def equity(self):
            raise RuntimeError("broker read failed")

    block = build_governor_block(Hostile(), limits=_Limits())
    assert block["equity"] is None
    assert block["gross_open_risk_cap_pct"] == 0.04


# --------------------------------------------------------------------------------------
# 6. Backward compatibility -- 99,112 live packets are the only live evidence there is
# --------------------------------------------------------------------------------------


def test_economics_block_is_optional_and_absence_is_valid():
    packet = build_runtime_learning_packet(
        namespace="ns", event_type="unit_placed", outcome={"placement_status": "placed"}
    )
    assert PACKET_ECONOMICS_KEY not in packet
    assert validate_runtime_learning_packet(packet) == (True, [])


def test_economics_block_round_trips_and_validates():
    economics = build_economics_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_exit_time_utc": "2026-07-07T12:00:00+00:00",
            "spread_r": 0.031,
        },
        server=FTMO,
    )
    packet = build_runtime_learning_packet(
        namespace="ns", event_type="position_closed", outcome={"placement_status": "closed"},
        economics=economics,
    )
    ok, issues = validate_runtime_learning_packet(packet)
    assert ok, issues
    reloaded = json.loads(json.dumps(packet, sort_keys=True, default=str))
    assert validate_runtime_learning_packet(reloaded)[0]
    assert reloaded[PACKET_ECONOMICS_KEY]["holding"]["rollover_nights"] == 1.0


def test_a_holding_time_without_a_provenance_label_is_refused():
    packet = build_runtime_learning_packet(
        namespace="ns", event_type="position_closed", outcome={"placement_status": "closed"},
        economics={"contract_version": "x", "holding": {"holding_seconds": 3600}},
    )
    ok, issues = validate_runtime_learning_packet(packet)
    assert not ok
    assert "economics_holding_seconds_without_provenance" in issues


def test_schema_version_is_unchanged_so_existing_packets_stay_readable():
    """Bumping SCHEMA_VERSION would make all 99,112 live packets fail `schema_version_mismatch`
    on read -- destroying the evidence in order to record an addition."""
    packet = build_runtime_learning_packet(namespace="ns", event_type="unit_placed")
    assert packet["schema_version"] == "ultimate_book_runtime_learning_packet_v1"


def test_weakest_provenance_wins():
    assert weakest(MEASURED, MODELLED) == MODELLED
    assert weakest(MEASURED, MEASURED) == MEASURED
    assert weakest() == UNAVAILABLE
    assert weakest(None, MEASURED) == MEASURED


# --------------------------------------------------------------------------------------
# 7. Deployment safety -- demonstrated, not asserted
#
# The bar from Session I's token carry: show the carry imports nothing from the coupling trap,
# that it is inert at every call site under current config, and that its failure mode is refusal
# rather than exception. The VPS is a live, funded, connected host with trade_allowed:true on both
# terminals; a carry that cannot be shown safe does not go.
# --------------------------------------------------------------------------------------

FORBIDDEN_IMPORT_ROOTS = (
    "MetaTrader5",
    "src.mt5",
    "src.components.execution",
    "src.components.orchestrator",
    "src.components.ultimate_book.order_router",
    "src.components.ultimate_book.book_engine",
    "src.components.broker_net_cost_engine",
)


@pytest.mark.parametrize(
    "module_name",
    [
        "src.components.ultimate_book.packet_economics",
        "src.components.ultimate_book.packet_guard",
    ],
)
def test_carry_modules_import_nothing_that_can_reach_a_broker(module_name):
    """Transitively. `create_mt5("live")` succeeds on macOS -- the ImportError only surfaces on
    .connect() -- so an import graph is the only construction-time evidence that means anything."""
    import importlib
    import sys as _sys

    importlib.import_module(module_name)
    module = _sys.modules[module_name]
    seen: set[str] = set()
    stack = [module]
    while stack:
        current = stack.pop()
        name = getattr(current, "__name__", "")
        if name in seen:
            continue
        seen.add(name)
        for attr in vars(current).values():
            child = getattr(attr, "__module__", None) or (
                attr.__name__ if isinstance(attr, type(module)) else None
            )
            if isinstance(child, str) and child.startswith("src.") and child not in seen:
                mod = _sys.modules.get(child)
                if mod is not None:
                    stack.append(mod)
    offenders = [
        name for name in seen if any(name.startswith(root) for root in FORBIDDEN_IMPORT_ROOTS)
    ]
    assert not offenders, f"{module_name} reaches {offenders}"


def test_economics_is_a_noop_for_every_event_type_that_carries_no_position():
    """Under current config the book's dominant traffic is cycle and skip events. The carry must
    add nothing to them -- 79 % of the stream must not grow a byte."""
    for outcome in (
        {"placement_status": "no_candidates"},
        {"placement_status": "skipped", "reason": "cost_screen_spread_r:0.２"},
        {"placement_status": "shadow"},
        {},
    ):
        assert build_economics_block(outcome, server=FTMO) is None


def test_the_failure_mode_is_refusal_not_exception():
    """Every input that cannot be honoured yields a labelled absence, not a raise and not a guess."""
    # Unresolvable clock -> refusal with a reason, no guessed offset.
    nights, detail = rollover_nights_crossed(
        datetime(2026, 7, 6, tzinfo=timezone.utc),
        datetime(2026, 7, 8, tzinfo=timezone.utc),
        server=None,
    )
    assert nights is None and detail["error"] == "unknown_broker_clock_rule"
    # Garbage timestamps -> block absent, nothing raised.
    assert build_holding_block({"broker_fill_time_utc": "not-a-time"}, server=FTMO) is None
    # Reversed interval -> refusal, not a negative night count.
    nights, detail = rollover_nights_crossed(
        datetime(2026, 7, 8, tzinfo=timezone.utc),
        datetime(2026, 7, 6, tzinfo=timezone.utc),
        server=FTMO,
    )
    assert nights is None and detail["error"] == "exit_before_entry"


def test_the_carry_survives_a_host_with_no_broker_clock_module():
    """`src/utils/broker_clock.py` is absent from the 2026-07-26 VPS export. A top-level import
    would raise at module load, propagate through book_owner, and break the live book's import --
    the worst outcome this carry could have. Absence must degrade the night count, nothing else."""
    import src.components.ultimate_book.packet_economics as pe

    original = pe.BROKER_CLOCK_AVAILABLE
    try:
        pe.BROKER_CLOCK_AVAILABLE = False
        block = pe.build_holding_block(
            {
                "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
                "broker_exit_time_utc": "2026-07-09T12:00:00+00:00",
            },
            server=FTMO,
        )
        # Holding time still measured; only the broker-clock-dependent night count refuses.
        assert block["holding_seconds"] == pytest.approx(3 * 24 * 3600)
        assert block["holding_provenance"] == MEASURED
        assert block["rollover_nights"] is None
        assert block["rollover_provenance"] == UNAVAILABLE
        assert block["rollover_detail"]["error"] == "broker_clock_module_unavailable"
    finally:
        pe.BROKER_CLOCK_AVAILABLE = original


def test_spread_observations_are_scoped_to_one_cycle():
    """Unbounded growth in a process that runs for months, and -- worse -- the risk of a later
    packet picking up an earlier decision bar's spread and wearing a `measured` label for it."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    owner = object.__new__(UltimateBookOwner)
    owner._spread_observations = {}

    class _Intent:
        sleeve, symbol, decision_bar_iso = "fx_jpy", "USDJPY", "2026-07-06T12:00:00"

    UltimateBookOwner._record_spread_observation(
        owner, _Intent(), spread_r=0.031, spread_price=0.004, max_spread_r=0.1, stop_dist=0.13
    )
    assert len(owner._spread_observations) == 1

    def _fresh():
        return {"sleeve": "fx_jpy", "symbol": "USDJPY", "decision_bar_iso": "2026-07-06T12:00:00"}

    attached = UltimateBookOwner._attach_spread_observation(owner, _fresh())
    assert attached["spread_r"] == 0.031
    assert attached["spread_r_provenance"] == MEASURED

    # A DIFFERENT decision bar must not inherit it -- the key carries the bar.
    later = {"sleeve": "fx_jpy", "symbol": "USDJPY", "decision_bar_iso": "2026-07-06T16:00:00"}
    assert "spread_r" not in UltimateBookOwner._attach_spread_observation(owner, later)

    # And after the per-cycle clear, nothing survives to be attached to a later cycle.
    owner._spread_observations.clear()
    assert UltimateBookOwner._attach_spread_observation(owner, _fresh()).get("spread_r") is None


# --------------------------------------------------------------------------------------
# 8. The silent hour-snap -- found by a refuter attacking this session's own bias claim
# --------------------------------------------------------------------------------------


def test_an_hour_snapped_fill_time_is_no_longer_labelled_measured():
    """`book_owner._iso_from_deal_time_near_reference` (:2818-2852) moves a broker deal time by up
    to +/-6 WHOLE HOURS to snap it to a local reference. The offset was computed, stored on the
    execution record, and read by nobody -- it appears in 0 of the 99,112 live packets. So no
    reader of that corpus can tell a raw broker timestamp from one moved six hours to agree with
    our clock, which is the broker-time-labelled-as-UTC hazard in its most dangerous form: the
    agreement that licenses the `_utc` label is manufactured by the label's own producer."""
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_fill_time_alignment_offset_seconds": 3 * 3600,
            "broker_exit_time_utc": "2026-07-06T18:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["entry_alignment_applied"] is True
    assert block["entry_alignment_offset_seconds"] == 3 * 3600
    assert block["entry_provenance"] == TRANSFERRED, "a moved measurement is not a measurement"
    assert block["holding_provenance"] == TRANSFERRED, "weakest input wins"


def test_an_unsnapped_fill_time_keeps_its_measured_label():
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_exit_time_utc": "2026-07-06T18:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["entry_alignment_applied"] is False
    assert block["entry_alignment_offset_seconds"] is None
    assert block["entry_provenance"] == MEASURED


def test_a_zero_offset_does_not_downgrade():
    """The producer writes the key only when the snap fired, but a defensive zero must not be
    read as an adjustment."""
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_fill_time_alignment_offset_seconds": 0,
            "broker_exit_time_utc": "2026-07-06T18:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["entry_alignment_applied"] is False
    assert block["entry_provenance"] == MEASURED


# --------------------------------------------------------------------------------------
# 9. The censored-hold defect -- found by a refuter attacking this session's safety claim.
#    This is the most serious thing this session got wrong, so it gets the most tests.
# --------------------------------------------------------------------------------------


def test_a_still_open_position_is_never_published_as_a_completed_hold():
    """`management_checked_at_utc` means "the book looked at this", not "it closed".

    book_owner sets it unconditionally immediately before the economics block is built, and it is
    present on 77,942 of 78,687 position_managed rows. Treating it as an exit fallback made
    `exit_at` non-None for EVERY management event: replayed over the live corpus that published
    71,969 open positions as completed holds, mean 20.85 h against a true 8.37 h -- a 2.49x
    overstatement of the exact quantity this module exists to measure, at a 476:1 ratio of
    fabricated to real samples, feeding the one number OD-3 turns on.
    """
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "management_checked_at_utc": "2026-07-09T12:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["position_open_at_emit"] is True
    assert block["holding_seconds"] is None, "an open position has no holding time"
    assert block["holding_provenance"] == UNAVAILABLE
    assert block.get("rollover_nights") is None, "no nights may be counted to a fabricated exit"
    assert block["exit_source_field"] is None


def test_the_open_position_still_yields_censored_evidence():
    """Dropping the observation would waste it. A right-censored hold is real evidence for a
    survival analysis -- provided nothing can average it in with completed holds by accident."""
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "management_checked_at_utc": "2026-07-09T12:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["elapsed_seconds_at_emit"] == pytest.approx(3 * 24 * 3600)
    assert block["elapsed_is_right_censored"] is True
    assert "holding_seconds" in block and block["holding_seconds"] is None


def test_a_genuine_mid_management_close_is_still_honoured():
    """88 position_managed rows in the live corpus carry a real broker exit deal -- positions that
    genuinely closed during management. The fix must not throw those away with the fabrications."""
    block = build_holding_block(
        {
            "broker_fill_time_utc": "2026-07-06T12:00:00+00:00",
            "broker_exit_time_utc": "2026-07-07T12:00:00+00:00",
            "management_checked_at_utc": "2026-07-09T12:00:00+00:00",
        },
        server=FTMO,
    )
    assert block["position_open_at_emit"] is False
    assert block["holding_seconds"] == pytest.approx(24 * 3600)
    assert block["exit_source_field"] == "broker_exit_time_utc"
    assert "elapsed_seconds_at_emit" not in block


def test_management_checked_is_not_an_exit_source_at_all():
    """Guards the fix at its root, so a later edit re-adding the fallback fails here."""
    from src.components.ultimate_book.packet_economics import _EXIT_SOURCES

    assert "management_checked_at_utc" not in {field for field, _ in _EXIT_SOURCES}


def test_a_logging_switch_cannot_stop_the_books(tmp_path):
    """`packet_enabled: true` + `packet_log_enabled: false` leaves the writer None. Falling through
    to the guard failed every packet as `unrecorded`, which feeds
    ai_companion/supervisor.py:517 -> :734-741 and raises `pause_new_entries` for every namespace.
    A logging switch must never be able to halt trading."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    owner = object.__new__(UltimateBookOwner)
    owner._runtime_learning_packet_enabled = True
    owner._runtime_learning_packet_log_enabled = False
    owner._runtime_learning_packet_log_path = "shadow_logs/p.jsonl"
    owner._convergence_advisory_enabled = False
    owner._convergence_advisory_log_enabled = False
    owner._runtime_learning_writer = None
    owner._namespace = "ns"
    summary = {}
    UltimateBookOwner._append_runtime_learning_packets(owner, summary, [{"a": 1}])

    status = summary["runtime_learning"]
    assert status.get("packet_write_error_count", 0) == 0, "must not report write errors"
    assert status.get("packets") == 0

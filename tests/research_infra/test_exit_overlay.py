import datetime as dt
import json
from pathlib import Path

import pytest

from src.research_infra.exit_overlay import (
    ExitOverlayError,
    ExitOverlaySpec,
    ExitPathPoint,
    SignedM1Bar,
    m1_points,
    replay_m1_conservative,
    replay_signed_path,
    shuffle_m1_blocks,
    shuffle_signed_increments,
    signed_m1_bars,
    tick_points,
    true_utc_tick_time_us,
)


REPO = Path(__file__).resolve().parents[2]
PROTOCOL = (
    REPO
    / "research/operations/wave19_sol_repair_2026_08_01/exit/OVERLAY_PROTOCOL.json"
)
DECISION_US = 1_000_000_000
MINUTE_US = 60_000_000


def point(minutes: float, signed_r: float, *, deadline_eligible: bool = True):
    return ExitPathPoint(
        time_us=DECISION_US + int(minutes * MINUTE_US),
        signed_r=signed_r,
        deadline_eligible=deadline_eligible,
        source_index=int(minutes * 10),
    )


def replay(spec, points, *, cost=0.1):
    return replay_signed_path(
        spec,
        points,
        decision_time_us=DECISION_US,
        cost_r=cost,
        source_mode="TEST_TICK",
    )


def spec(cell):
    return ExitOverlaySpec.from_protocol_cell(cell)


def test_frozen_protocol_has_exactly_40_parseable_default_off_cells():
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cells = payload["family"]["variants"]

    parsed = [ExitOverlaySpec.from_protocol_cell(cell) for cell in cells]

    assert len(parsed) == payload["family"]["declared_family_size"] == 40
    assert len({item.variant_id for item in parsed}) == 40
    assert parsed[0].kind == "identity"
    assert parsed[0].trigger_r == 1.0
    assert parsed[0].giveback_gap_r == 0.4


@pytest.mark.parametrize(
    "overlay",
    [
        ExitOverlaySpec("hybrid", "time_box", trigger_r=0.5, time_box_minutes=30),
        ExitOverlaySpec("zero-partial", "partial_harvest", trigger_r=0.5),
        ExitOverlaySpec(
            "hybrid-floor",
            "break_even",
            trigger_r=0.5,
            giveback_gap_r=0.2,
            move_stop_to_break_even=True,
        ),
    ],
)
def test_direct_construction_cannot_escape_the_frozen_one_alternative_shapes(
    overlay,
):
    with pytest.raises(ExitOverlayError, match="overlay_kind_shape_invalid"):
        overlay.validate()


def test_identity_replays_current_trigger_and_ratcheting_giveback():
    result = replay(
        spec({"id": "V00", "kind": "identity"}),
        [point(1, 0.4), point(2, 1.2), point(3, 0.7)],
    )

    assert result.exit_reason == "giveback_floor"
    assert result.gross_r == pytest.approx(0.8)
    assert result.net_r == pytest.approx(0.7)
    assert result.protective_floor_r == pytest.approx(0.8)


def test_break_even_is_a_standalone_alternative_not_compounded_giveback():
    result = replay(
        spec({"id": "BE", "kind": "break_even", "trigger_r": 0.5}),
        [point(1, 0.6), point(2, 0.1), point(3, -0.01)],
    )

    assert result.exit_reason == "break_even_floor"
    assert result.gross_r == 0.0
    assert result.net_r == -0.1


def test_partial_harvest_weights_original_size_and_charges_full_cost_once():
    result = replay(
        spec(
            {
                "id": "PH",
                "kind": "partial_harvest",
                "trigger_r": 0.5,
                "fraction": 0.5,
            }
        ),
        [point(1, 0.6), point(2, 2.1)],
        cost=0.2,
    )

    assert result.exit_reason == "hard_target"
    assert result.partial_realized_r == pytest.approx(0.25)
    assert result.remaining_fraction == pytest.approx(0.5)
    assert result.gross_r == pytest.approx(1.25)
    assert result.net_r == pytest.approx(1.05)


def test_favorable_gap_harvests_at_trigger_before_target_overshoot():
    result = replay(
        spec(
            {
                "id": "PH",
                "kind": "partial_harvest",
                "trigger_r": 1.25,
                "fraction": 0.5,
            }
        ),
        [point(1, 2.2)],
        cost=0.0,
    )

    assert result.partial_realized_r == pytest.approx(0.625)
    assert result.gross_r == pytest.approx(1.625)


def test_partial_then_break_even_protects_only_the_remaining_fraction():
    result = replay(
        spec(
            {
                "id": "PBE",
                "kind": "partial_then_break_even",
                "trigger_r": 0.75,
                "fraction": 0.5,
            }
        ),
        [point(1, 0.8), point(2, -0.1)],
        cost=0.05,
    )

    assert result.exit_reason == "break_even_floor"
    assert result.gross_r == pytest.approx(0.375)
    assert result.net_r == pytest.approx(0.325)


def test_time_box_uses_first_deadline_eligible_observation():
    result = replay(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [point(29, 0.2), point(30, 0.4, deadline_eligible=False), point(30, 0.3)],
        cost=0.0,
    )

    assert result.exit_reason == "time_box"
    assert result.gross_r == pytest.approx(0.3)


def test_target_strictly_before_deadline_retains_target_ownership():
    result = replay(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [point(29, 2.1), point(30, 0.4)],
        cost=0.0,
    )

    assert result.exit_reason == "hard_target"
    assert result.gross_r == pytest.approx(2.0)


def test_deadline_strictly_before_target_retains_timebox_ownership():
    result = replay(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [point(30, 0.4), point(31, 2.1)],
        cost=0.0,
    )

    assert result.exit_reason == "time_box"
    assert result.gross_r == pytest.approx(0.4)


def test_same_tick_target_deadline_collision_belongs_to_timebox():
    result = replay(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [point(30, 2.0)],
        cost=0.0,
    )

    assert result.exit_reason == "time_box"
    assert result.gross_r == pytest.approx(2.0)


def test_same_m1_target_deadline_collision_belongs_to_timebox_close():
    deadline_bar = SignedM1Bar(
        time_us=DECISION_US + 30 * MINUTE_US,
        open_r=0.2,
        high_r=2.4,
        low_r=0.1,
        close_r=0.4,
        source_index=30,
    )
    result = replay_m1_conservative(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [deadline_bar],
        decision_time_us=DECISION_US,
        cost_r=0.0,
    )

    assert result.open_high_low_close.exit_reason == "time_box"
    assert result.open_low_high_close.exit_reason == "time_box"
    assert result.selected.gross_r == pytest.approx(0.4)
    assert result.outcomes_differ is False


def test_deadline_gap_through_retained_target_is_timebox_capped_at_target():
    result = replay(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        [point(30, 2.7)],
        cost=0.0,
    )

    assert result.exit_reason == "time_box"
    assert result.exit_r_on_remaining == pytest.approx(2.0)
    assert result.gross_r == pytest.approx(2.0)


def test_m1_conservative_takes_lower_of_both_extrema_orderings():
    bars = (
        SignedM1Bar(
            time_us=DECISION_US + MINUTE_US,
            open_r=0.0,
            high_r=2.1,
            low_r=-1.1,
            close_r=0.2,
            source_index=0,
        ),
    )
    result = replay_m1_conservative(
        spec({"id": "TB", "kind": "time_box", "minutes": 30}),
        bars,
        decision_time_us=DECISION_US,
        cost_r=0.0,
    )

    assert result.open_high_low_close.gross_r == 2.0
    assert result.open_low_high_close.gross_r == -1.0
    assert result.selected.gross_r == -1.0
    assert result.selected.ambiguity is True
    assert result.outcomes_differ is True


def test_tick_path_uses_bid_for_long_and_ask_for_short():
    rows = [
        {
            "ts_utc": dt.datetime.fromtimestamp(
                (DECISION_US + 1_000) / 1_000_000,
                tz=dt.timezone.utc,
            ).isoformat(),
            "time_msc": (DECISION_US // 1000) + 7_200_001,
            "bid": 101.0,
            "ask": 102.0,
        }
    ]
    long = tick_points(
        rows,
        entry_price=100.0,
        stop_loss=99.0,
        side="LONG",
        decision_time_us=DECISION_US,
        horizon_time_us=DECISION_US + MINUTE_US,
    )
    short = tick_points(
        rows,
        entry_price=100.0,
        stop_loss=101.0,
        side="SHORT",
        decision_time_us=DECISION_US,
        horizon_time_us=DECISION_US + MINUTE_US,
    )

    assert long[0].signed_r == 1.0
    assert short[0].signed_r == -2.0


def test_tick_path_excludes_quotes_before_recorded_fill_without_moving_horizon():
    rows = [
        {
            "ts_utc": (
                dt.datetime.fromtimestamp(
                    (DECISION_US + offset * 1_000) / 1_000_000,
                    tz=dt.timezone.utc,
                ).isoformat()
            ),
            "time_msc": (DECISION_US // 1000) + 7_200_000 + offset,
            "bid": 100.0 + offset,
            "ask": 100.1 + offset,
        }
        for offset in (1, 2, 3)
    ]

    points = tick_points(
        rows,
        entry_price=100.0,
        stop_loss=99.0,
        side="LONG",
        decision_time_us=DECISION_US,
        path_start_time_us=DECISION_US + 2_000,
        horizon_time_us=DECISION_US + MINUTE_US,
    )

    assert [item.time_us for item in points] == [DECISION_US + 3_000]
    with pytest.raises(ExitOverlayError, match="path_start_outside"):
        tick_points(
            rows,
            entry_price=100.0,
            stop_loss=99.0,
            side="LONG",
            decision_time_us=DECISION_US,
            path_start_time_us=DECISION_US - 1,
            horizon_time_us=DECISION_US + MINUTE_US,
        )


def test_true_utc_tick_timestamp_rejects_raw_broker_epoch_and_disagreement():
    row = {
        "ts_utc": "2026-01-01T22:05:00.405000+00:00",
        "time": "2026-01-01T22:05:00.405000+00:00",
        "time_msc": 1767312300405,
    }

    assert true_utc_tick_time_us(row) == 1767305100405000
    with pytest.raises(ExitOverlayError, match="true_utc_timestamp_missing"):
        true_utc_tick_time_us({"time_msc": 1767312300405})
    with pytest.raises(ExitOverlayError, match="timestamp_disagreement"):
        true_utc_tick_time_us({**row, "time": "2026-01-01T22:05:01+00:00"})


def test_m1_side_normalization_preserves_favorable_and_adverse_extrema():
    rows = [
        {
            "time_utc": "2026-01-02T00:01:00+00:00",
            "open": 100.0,
            "high": 101.0,
            "low": 97.0,
            "close": 98.0,
        }
    ]
    bars = signed_m1_bars(rows, entry_price=100.0, stop_loss=101.0, side="SHORT")

    assert bars[0].high_r == 3.0
    assert bars[0].low_r == -1.0
    assert bars[0].close_r == 2.0
    assert [item.signed_r for item in m1_points(bars, high_first=True)] == [
        0.0,
        3.0,
        -1.0,
        2.0,
    ]


def test_increment_shuffle_is_seeded_and_preserves_increment_multiset():
    original = (point(1, 0.1), point(2, 0.4), point(3, -0.2))
    first = shuffle_signed_increments(original, seed=1901)
    second = shuffle_signed_increments(original, seed=1901)

    def increments(path):
        values = [0.0, *(item.signed_r for item in path)]
        return sorted(round(b - a, 12) for a, b in zip(values, values[1:]))

    assert first == second
    assert increments(first) == increments(original)
    assert [item.time_us for item in first] == [item.time_us for item in original]


def test_m1_block_shuffle_reconnects_from_zero_and_preserves_block_shapes():
    bars = (
        SignedM1Bar(1, 2.0, 2.4, 1.7, 2.2, 0),
        SignedM1Bar(2, -1.0, -0.5, -1.4, -0.8, 1),
    )
    shuffled = shuffle_m1_blocks(bars, seed=1901)

    assert shuffled[0].open_r == 0.0
    assert shuffled[1].open_r == pytest.approx(shuffled[0].close_r)
    original_shapes = sorted(
        (bar.close_r - bar.open_r, bar.high_r - bar.open_r, bar.low_r - bar.open_r)
        for bar in bars
    )
    shuffled_shapes = sorted(
        (bar.close_r - bar.open_r, bar.high_r - bar.open_r, bar.low_r - bar.open_r)
        for bar in shuffled
    )
    assert shuffled_shapes == pytest.approx(original_shapes)


def test_empty_and_predecision_paths_fail_closed():
    identity = spec({"id": "V00", "kind": "identity"})
    source_gap = replay(identity, [])

    assert source_gap.status == "SOURCE_GAP"
    assert source_gap.net_r is None
    with pytest.raises(ExitOverlayError, match="strictly_postdecision"):
        replay(
            identity,
            [
                ExitPathPoint(
                    time_us=DECISION_US,
                    signed_r=0.0,
                    deadline_eligible=True,
                    source_index=0,
                )
            ],
        )

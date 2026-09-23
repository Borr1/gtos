import hashlib
import importlib.util
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "src/research_infra/session_fc_exit_overlay.py"
EXECUTED_REPLAY = (
    REPO
    / "research/operations/wave19_sol_repair_2026_08_01/exit/"
    "EXECUTED_OVERLAY_REPLAY.json"
)
OVERLAY_RESULTS = (
    REPO
    / "research/operations/wave19_sol_repair_2026_08_01/exit/"
    "OVERLAY_RESULTS.json"
)


def load_fc_module():
    name = "session_fc_exit_overlay_test_module"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _independent_exit_oracle(spec, values, times_us, eligible, *, cost_r):
    """Small declarative oracle for the frozen event-priority state machine."""

    deadline = (
        spec.time_box_minutes * 60_000_000
        if spec.time_box_minutes is not None
        else None
    )
    deadline_time = next(
        (
            int(timestamp)
            for timestamp, can_close in zip(times_us, eligible)
            if deadline is not None and can_close and timestamp >= deadline
        ),
        None,
    )
    remaining = 1.0
    partial = 0.0
    floor = float(spec.hard_stop_r)
    mfe = 0.0
    triggered = False
    partial_done = False
    giveback_armed = False

    def close(index, reason, exit_r):
        gross = partial + remaining * float(exit_r)
        return {
            "gross_r": gross,
            "net_r": gross - cost_r,
            "exit_reason": reason,
            "exit_index": index,
            "exit_time_us": int(times_us[index]),
            "exit_r": float(exit_r),
            "partial_realized_r": partial,
            "remaining_fraction": remaining,
            "trigger_touched": triggered,
            "mfe_r": mfe,
            "protective_floor_r": floor,
        }

    for index, raw_value in enumerate(values):
        value = float(raw_value)
        if value <= spec.hard_stop_r:
            return close(index, "hard_stop", spec.hard_stop_r)
        if floor > spec.hard_stop_r and value <= floor:
            reason = "break_even_floor" if abs(floor) <= 1e-12 else "giveback_floor"
            return close(index, reason, floor)
        if deadline is not None and eligible[index] and times_us[index] >= deadline:
            mfe = max(mfe, value)
            return close(index, "time_box", min(value, spec.hard_target_r))

        mfe = max(mfe, value)
        if spec.trigger_r is not None and not triggered and value >= spec.trigger_r:
            triggered = True
            if spec.partial_fraction and not partial_done:
                partial += spec.partial_fraction * spec.trigger_r
                remaining -= spec.partial_fraction
                partial_done = True
            if spec.move_stop_to_break_even:
                floor = max(floor, 0.0)
            giveback_armed = spec.giveback_gap_r is not None

        if value >= spec.hard_target_r and times_us[index] != deadline_time:
            return close(index, "hard_target", spec.hard_target_r)
        if giveback_armed:
            floor = max(floor, mfe - spec.giveback_gap_r)

    return close(len(values) - 1, "horizon_terminal_mark", values[-1])


def test_frozen_analyzer_fast_path_matches_reference_for_all_cells():
    fc = load_fc_module()
    _, specs, _ = fc.load_protocol()

    receipt = fc.verify_fast_path(specs)

    assert receipt == {
        "status": "PASS",
        "seed": 3150,
        "random_paths": 80,
        "variants": 40,
        "comparisons": 3200,
        "reference": "src.research_infra.exit_overlay.replay_signed_path",
    }


def test_independent_state_machine_reproduces_all_3200_fast_and_reference_rows():
    fc = load_fc_module()
    _, specs, _ = fc.load_protocol()
    rng = random.Random(3150)
    checked = 0

    for case in range(80):
        level = 0.0
        path_values = []
        for _ in range(120):
            level += rng.uniform(-0.32, 0.34)
            path_values.append(level)
        if case % 4 == 0:
            path_values[9], path_values[19] = 0.55, -0.05
        elif case % 4 == 1:
            path_values[14], path_values[24] = 1.3, 0.7
        elif case % 4 == 2:
            path_values[34] = 2.1
        else:
            path_values[44] = -1.1

        values = np.asarray(path_values, dtype=np.float64)
        times = np.asarray(
            [(index + 1) * fc.MICROSECONDS_PER_MINUTE for index in range(120)],
            dtype=np.int64,
        )
        eligible = np.ones(len(values), dtype=np.bool_)
        path = fc.PathArrays(values, times, eligible, "HDC_ORACLE")
        points = tuple(
            fc.ExitPathPoint(int(times[index]), float(value), True, index)
            for index, value in enumerate(values)
        )
        for overlay in specs:
            oracle = _independent_exit_oracle(
                overlay, values, times, eligible, cost_r=0.137
            )
            reference = fc.replay_signed_path(
                overlay,
                points,
                decision_time_us=0,
                cost_r=0.137,
                source_mode="HDC_ORACLE",
            )
            fast = fc.fast_replay_one(
                overlay, path, decision_us=0, cost_r=0.137
            )
            reference_values = {
                "gross_r": reference.gross_r,
                "net_r": reference.net_r,
                "exit_reason": reference.exit_reason,
                "exit_index": reference.exit_source_index,
                "exit_time_us": reference.exit_time_us,
                "exit_r": reference.exit_r_on_remaining,
                "partial_realized_r": reference.partial_realized_r,
                "remaining_fraction": reference.remaining_fraction,
                "trigger_touched": reference.trigger_touched,
                "mfe_r": reference.mfe_r,
                "protective_floor_r": reference.protective_floor_r,
            }
            fast_values = {
                field: getattr(fast, field)
                for field in oracle
            }
            for actual in (reference_values, fast_values):
                for field, expected in oracle.items():
                    if isinstance(expected, float):
                        assert actual[field] == pytest.approx(expected, abs=1e-10)
                    else:
                        assert actual[field] == expected
            checked += 1

    assert checked == 3200


def test_vectorized_analyzer_matches_same_timestamp_deadline_priority_and_cap():
    fc = load_fc_module()
    overlay = fc.ExitOverlaySpec.from_protocol_cell(
        {"id": "TB", "kind": "time_box", "minutes": 30}
    )
    deadline = 30 * fc.MICROSECONDS_PER_MINUTE
    same_m1 = fc.PathArrays(
        values=np.asarray([2.4, 0.4], dtype=float),
        times_us=np.asarray([deadline, deadline], dtype=np.int64),
        deadline_eligible=np.asarray([False, True], dtype=np.bool_),
        source_mode="M1_TEST",
    )
    gap_tick = fc.PathArrays(
        values=np.asarray([2.7], dtype=float),
        times_us=np.asarray([deadline], dtype=np.int64),
        deadline_eligible=np.asarray([True], dtype=np.bool_),
        source_mode="TICK_TEST",
    )

    m1_result = fc.fast_replay_one(
        overlay, same_m1, decision_us=0, cost_r=0.0
    )
    gap_result = fc.fast_replay_one(
        overlay, gap_tick, decision_us=0, cost_r=0.0
    )

    assert (m1_result.exit_reason, m1_result.gross_r) == ("time_box", 0.4)
    assert (gap_result.exit_reason, gap_result.gross_r) == ("time_box", 2.0)


@pytest.mark.parametrize(
    (
        "cell",
        "values",
        "minutes",
        "eligible",
        "expected_reason",
        "expected_gross",
        "expected_exit_minute",
        "expected_partial",
    ),
    [
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [2.2, 0.4], [29, 30], [True, True], "hard_target", 2.0, 29, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.4, 2.2], [30, 31], [True, True], "time_box", 0.4, 30, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [2.7], [30], [True], "time_box", 2.0, 30, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.3, 2.2, 0.4], [30, 34, 35], [False, False, True],
         "hard_target", 2.0, 34, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.3, 0.4], [30, 35], [False, True], "time_box", 0.4, 35, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [2.7, 0.1], [29, 30], [True, True], "hard_target", 2.0, 29, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.4, 2.7], [30, 31], [True, True], "time_box", 0.4, 30, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [-1.7], [30], [True], "hard_stop", -1.0, 30, 0.0),
        ({"id": "PH", "kind": "partial_harvest", "trigger_r": 0.5,
          "fraction": 0.5},
         [0.6, 2.2], [10, 20], [True, True],
         "hard_target", 1.25, 20, 0.25),
        ({"id": "BE", "kind": "break_even", "trigger_r": 0.5},
         [0.6, -0.2], [10, 120], [True, True],
         "break_even_floor", 0.0, 120, 0.0),
        ({"id": "BE", "kind": "break_even", "trigger_r": 0.5},
         [0.6, -1.3], [10, 120], [True, True],
         "hard_stop", -1.0, 120, 0.0),
        ({"id": "V00", "kind": "identity"},
         [1.2, 0.7], [10, 120], [True, True],
         "giveback_floor", 0.8, 120, 0.0),
        ({"id": "V00", "kind": "identity"},
         [0.2, 0.3], [60, 120], [True, True],
         "horizon_terminal_mark", 0.3, 120, 0.0),
        # Both admissible M1 extrema orderings at the deadline are equivalent:
        # only the close is deadline-eligible, and target ownership is suppressed.
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.2, 2.4, 0.1, 0.4], [30, 30, 30, 30],
         [False, False, False, True], "time_box", 0.4, 30, 0.0),
        ({"id": "TB", "kind": "time_box", "minutes": 30},
         [0.2, 0.1, 2.4, 0.4], [30, 30, 30, 30],
         [False, False, False, True], "time_box", 0.4, 30, 0.0),
    ],
)
def test_temporal_state_machine_edge_table_matches_row_path_and_oracle(
    cell,
    values,
    minutes,
    eligible,
    expected_reason,
    expected_gross,
    expected_exit_minute,
    expected_partial,
):
    fc = load_fc_module()
    overlay = fc.ExitOverlaySpec.from_protocol_cell(cell)
    array_values = np.asarray(values, dtype=np.float64)
    times_us = np.asarray(
        [minute * fc.MICROSECONDS_PER_MINUTE for minute in minutes],
        dtype=np.int64,
    )
    deadline_eligible = np.asarray(eligible, dtype=np.bool_)
    path = fc.PathArrays(
        array_values, times_us, deadline_eligible, "HDC_EDGE_TABLE"
    )
    points = tuple(
        fc.ExitPathPoint(
            int(times_us[index]),
            float(value),
            bool(deadline_eligible[index]),
            index,
        )
        for index, value in enumerate(array_values)
    )
    oracle = _independent_exit_oracle(
        overlay,
        array_values,
        times_us,
        deadline_eligible,
        cost_r=0.2,
    )
    reference = fc.replay_signed_path(
        overlay,
        points,
        decision_time_us=0,
        cost_r=0.2,
        source_mode="HDC_EDGE_TABLE",
    )
    fast = fc.fast_replay_one(overlay, path, decision_us=0, cost_r=0.2)

    assert oracle["exit_reason"] == expected_reason
    assert oracle["gross_r"] == pytest.approx(expected_gross)
    assert oracle["net_r"] == pytest.approx(expected_gross - 0.2)
    assert oracle["exit_time_us"] == expected_exit_minute * fc.MICROSECONDS_PER_MINUTE
    assert oracle["partial_realized_r"] == pytest.approx(expected_partial)
    assert reference.exit_reason == fast.exit_reason == oracle["exit_reason"]
    assert reference.gross_r == fast.gross_r == pytest.approx(oracle["gross_r"])
    assert reference.net_r == fast.net_r == pytest.approx(oracle["net_r"])
    assert reference.exit_time_us == fast.exit_time_us == oracle["exit_time_us"]
    assert reference.partial_realized_r == fast.partial_realized_r == pytest.approx(
        oracle["partial_realized_r"]
    )
    assert reference.protective_floor_r == fast.protective_floor_r == pytest.approx(
        oracle["protective_floor_r"]
    )


def test_all_214_timebox_identities_and_economics_reproduce_independently():
    payload = json.loads(EXECUTED_REPLAY.read_text(encoding="utf-8"))
    published = json.loads(OVERLAY_RESULTS.read_text(encoding="utf-8"))
    train_dates = set(published["train_dates"])
    holdout_dates = set(published["holdout_dates"])
    outcomes = []
    full_identities = set()
    bucket_records = {
        "january_executed_train": [],
        "january_executed_holdout": [],
        "february_executed_attribution": payload["february"]["records"],
    }
    for record in payload["january"]["records"]:
        day = record["decision_time_utc"][:10]
        if day in train_dates:
            bucket_records["january_executed_train"].append(record)
        elif day in holdout_dates:
            bucket_records["january_executed_holdout"].append(record)
        else:
            pytest.fail(f"January record outside frozen split: {day}")

    for month in ("january", "february"):
        for record in payload[month]["records"]:
            for variant_id, overlay in record["overlays"].items():
                assert overlay["net_r"] == pytest.approx(
                    overlay["gross_r"] - record["cost_r"], abs=1e-10
                )
                if overlay["exit_reason"] != "time_box":
                    continue
                full_identities.add(
                    (
                        month,
                        record["candidate_id"],
                        record["decision_time_utc"],
                        record["symbol"],
                        record["side"],
                        variant_id,
                    )
                )
                outcomes.append(
                    {
                        "month": month,
                        "candidate_id": record["candidate_id"],
                        "variant_id": variant_id,
                        "exit_reason": overlay["exit_reason"],
                        "exit_time_utc": overlay["exit_time_utc"],
                        "gross_r": overlay["gross_r"],
                        "net_r": overlay["net_r"],
                        "source_mode": overlay["source_mode"],
                        "m1_ordering_ambiguous": overlay[
                            "m1_ordering_ambiguous"
                        ],
                    }
                )

    assert len(full_identities) == len(outcomes) == 214
    assert Counter(row["month"] for row in outcomes) == {
        "january": 100,
        "february": 114,
    }
    assert all(row["gross_r"] <= 2.0 for row in outcomes)

    for bucket, records in bucket_records.items():
        month = "february" if bucket.startswith("february") else "january"
        all_month_records = payload[month]["records"]
        for variant_id, cell in published["cells"].items():
            overlays = [(record, record["overlays"][variant_id]) for record in records]
            expected = cell[bucket]
            total_gross = math.fsum(row["gross_r"] for _, row in overlays)
            total_net = math.fsum(row["net_r"] for _, row in overlays)
            daily = defaultdict(list)
            for record, row in overlays:
                daily[record["decision_time_utc"][:10]].append(row["net_r"])
            calendar = (
                sorted(train_dates)
                if bucket == "january_executed_train"
                else sorted(holdout_dates)
                if bucket == "january_executed_holdout"
                else sorted(daily)
            )
            daily_net = {
                day: math.fsum(daily.get(day, ())) for day in calendar
            }
            assert expected["rows"] == len(overlays)
            assert expected["total_gross_r"] == pytest.approx(total_gross, abs=1e-8)
            assert expected["total_net_r"] == pytest.approx(total_net, abs=1e-8)
            assert expected["mean_gross_r"] == pytest.approx(
                total_gross / len(overlays), abs=1e-10
            )
            assert expected["mean_net_r"] == pytest.approx(
                total_net / len(overlays), abs=1e-10
            )
            assert set(expected["daily_net_r"]) == set(calendar)
            assert expected["daily_net_r"] == pytest.approx(daily_net, abs=1e-9)
            assert expected["source_modes"] == dict(
                sorted(Counter(row["source_mode"] for _, row in overlays).items())
            )
            assert expected["m1_ordering_ambiguity_rows"] == sum(
                bool(row["m1_ordering_ambiguous"]) for _, row in overlays
            )
            assert expected["positive_rows"] == sum(
                row["net_r"] > 0.0 for _, row in overlays
            )
            all_month_overlays = [
                record["overlays"][variant_id] for record in all_month_records
            ]
            assert expected["exit_reasons_full_dataset"] == dict(
                sorted(Counter(
                    row["exit_reason"] for row in all_month_overlays
                ).items())
            )
            assert expected["trigger_touched_rows_full_dataset"] == sum(
                bool(row["trigger_touched"]) for row in all_month_overlays
            )

    blob = json.dumps(
        outcomes,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    assert len(outcomes) == 214
    assert hashlib.sha256(blob).hexdigest() == (
        "d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d"
    )


def test_composite_identity_requires_side_symbol_time_and_candidate():
    fc = load_fc_module()
    row = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T00:15:00+00:00",
        "symbol": "XAUUSD",
        "direction": "SHORT",
    }

    assert fc.composite_key(row) == (
        "candidate-1",
        "2026-01-02T00:15:00+00:00",
        "XAUUSD",
        "SHORT",
    )
    with pytest.raises(fc.FCRefusal, match="composite_identity_invalid"):
        fc.composite_key({**row, "symbol": ""})


def test_month_guard_refuses_challenge_month_without_opening_a_source():
    fc = load_fc_module()

    with pytest.raises(fc.FCRefusal, match="march_outcome_boundary_violation"):
        fc.require_allowed_month("2026-03-01T00:00:00+00:00", context="synthetic")


def test_residual_choice_set_filter_matches_frozen_definition():
    fc = load_fc_module()
    base = {
        "broker_pretrade_cost_executable": True,
        "selector_action": "trade",
    }

    assert fc.pool_row_is_residual(base) is True
    assert fc.pool_row_is_residual({**base, "selector_action": "reject"}) is False
    assert (
        fc.pool_row_is_residual(
            {**base, "broker_pretrade_cost_executable": False}
        )
        is False
    )


def test_residual_choice_set_count_reads_frozen_nested_total_schema():
    fc = load_fc_module()

    assert fc.residual_choice_set_count({"A": {"total": {"n": 4509}}}) == 4509
    with pytest.raises(fc.FCRefusal, match="residual_choice_set_count_invalid"):
        fc.residual_choice_set_count({"A": {"total": {"n": "4509"}}})


def test_bh_adjustment_keeps_declared_40_cell_denominator():
    fc = load_fc_module()
    q_values = fc.bh_q_values([0.001, 0.01, *([1.0] * 38)])

    assert q_values[0] == pytest.approx(0.04)
    assert q_values[1] == pytest.approx(0.2)
    with pytest.raises(fc.FCRefusal, match="bh_family_denominator"):
        fc.bh_q_values([0.01] * 39)


def test_seeded_m1_block_shuffle_reconnects_from_zero():
    fc = load_fc_module()
    times = np.asarray([1, 2, 3], dtype=np.int64)
    opens = np.asarray([100.0, 101.0, 100.5])
    highs = np.asarray([101.5, 102.0, 101.0])
    lows = np.asarray([99.5, 100.0, 99.0])
    closes = np.asarray([101.0, 100.5, 100.0])

    high_first, low_first = fc.normalized_m1_arrays(
        times_us=times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        entry=100.0,
        stop=99.0,
        side="LONG",
        shuffled_seed=1901,
    )

    assert high_first.values[0] == 0.0
    assert low_first.values[0] == 0.0
    assert np.array_equal(high_first.times_us, np.repeat(times, 4))
    assert high_first.deadline_eligible.tolist() == [
        False,
        False,
        False,
        True,
    ] * 3


def test_executed_fast_paths_start_strictly_after_recorded_fill():
    fc = load_fc_module()
    decision_us = 1_000_000
    times = np.asarray([1_000_100, 1_000_200, 1_000_300], dtype=np.int64)
    ticks = fc.TickSeries(
        times_us=times,
        bid=np.asarray([100.1, 100.2, 100.3]),
        ask=np.asarray([100.2, 100.3, 100.4]),
    )

    tick_path = fc.tick_path(
        ticks,
        decision_us=decision_us,
        path_start_us=1_000_200,
        horizon_us=2_000_000,
        entry=100.0,
        stop=99.0,
        side="LONG",
    )
    assert tick_path is not None
    assert tick_path.times_us.tolist() == [1_000_300]

    bars = fc.M1Series(
        times_us=times,
        opens=np.asarray([100.0, 100.1, 100.2]),
        highs=np.asarray([100.2, 100.3, 100.4]),
        lows=np.asarray([99.9, 100.0, 100.1]),
        closes=np.asarray([100.1, 100.2, 100.3]),
    )
    sliced = fc._m1_slice_arrays(
        bars, path_start_us=1_000_200, horizon_us=2_000_000
    )
    assert sliced is not None
    assert sliced[0].tolist() == [1_000_300]


def test_look_ledger_preserves_invalidated_schema_and_prefill_runs():
    fc = load_fc_module()
    _, specs, _ = fc.load_protocol()
    top_three = [specs[1].variant_id, specs[2].variant_id, specs[3].variant_id]

    looks, runs = fc.look_rows(specs=specs, top_three=top_three)

    assert len(looks) == 40 + 52 + 52 + 52
    assert sum(row["valid_for_final_result"] for row in looks) == 52
    assert all(row["billed"] is False for row in looks)
    assert [row["status"] for row in runs] == [
        "INVALIDATED_BEFORE_RESULT_EMISSION",
        "INVALIDATED_AFTER_RESULT_EMISSION",
        "INVALIDATED_AFTER_RESULT_EMISSION",
        "VALID_FINAL",
    ]


def test_lane_tick_loader_uses_converted_true_utc_not_raw_broker_epoch(tmp_path):
    fc = load_fc_module()
    path = tmp_path / "ticks.jsonl"
    row = {
        "ts_utc": "2026-01-01T22:05:00.405000+00:00",
        "time": "2026-01-01T22:05:00.405000+00:00",
        "time_msc": 1767312300405,
        "bid": 1.1,
        "ask": 1.2,
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    record = fc.SourceRecord(
        symbol="EURUSD",
        timeframe="TICK",
        logical_path="synthetic/ticks.jsonl",
        path=path,
        sha256=fc.sha256_file(path),
        row_count=1,
    )

    series = fc.load_tick_series(record)

    assert series.times_us.tolist() == [1767305100405000]
    assert series.times_us[0] != row["time_msc"] * 1000

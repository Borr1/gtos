"""Same-byte adversaries for the second exit/capture-science falsifier.

Set ``HDF_REPO_ROOT`` to run these exact test bytes against another immutable
repository node.  The tests deliberately derive their expectations without
reading HDC's result or completion receipt.
"""

from __future__ import annotations

import importlib.util
import itertools
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest


REPO = Path(
    os.environ.get("HDF_REPO_ROOT", Path(__file__).resolve().parents[2])
).resolve()
TEST_SOURCE_REPO = Path(__file__).resolve().parents[2]


def _activate_selected_repo():
    """Prevent pytest's external test path from contaminating comparator imports."""

    if REPO == TEST_SOURCE_REPO:
        # Normal suite execution already imports the selected repository. Purging the shared
        # ``src`` namespace here would invalidate module objects held by tests collected
        # before this file and manufacture order-dependent registrar/schema state.
        return
    target = str(REPO)
    foreign = str(TEST_SOURCE_REPO)
    sys.path[:] = [
        target,
        *(
            entry
            for entry in sys.path
            if entry not in {target, foreign}
        ),
    ]
    # ``src`` is a namespace package and can have ``__file__ = None`` while its
    # cached __path__ remains bound to the test-owning worktree.  Purging the
    # complete local namespace is the only reliable cross-worktree isolation.
    for module_name in tuple(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]


_activate_selected_repo()


@pytest.fixture(autouse=True)
def _bind_implementation_imports_to_selected_repo():
    _activate_selected_repo()

def _tool_path(name: str) -> Path:
    """Resolve a relocated tool against the SELECTED repo's layout.

    At HEAD the tools live in src/research_infra/ (A0 relocation); the immutable
    comparator nodes this file can be pointed at via HDF_REPO_ROOT predate the
    relocation and carry them under docs/.../receipts/. Same test bytes, both layouts.
    """
    for candidate in (
        REPO / "src/research_infra" / name,
        REPO / "docs/audits/fable5-vision-audit-20260725/phase19/receipts" / name,
    ):
        if candidate.is_file():
            return candidate
    return REPO / "src/research_infra" / name


FC_SCRIPT = _tool_path("session_fc_exit_overlay.py")
FC_EVIDENCE = REPO / "research/operations/wave19_sol_repair_2026_08_01/exit"
FC_COMPLETE = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
    "SESSION_FC_COMPLETE.json"
)
CS_SCRIPT = _tool_path("cs_breaker_folds.py")


def _load_fc_module():
    name = "session_hdf_fc_comparator_module"
    spec = importlib.util.spec_from_file_location(name, FC_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_cs_module():
    name = "session_hdf_cs_comparator_module"
    spec = importlib.util.spec_from_file_location(name, CS_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _capture_spec(*, windows, hashes, blackout=(("2026-03-01", "2026-03-31"),)):
    from src.research_infra.walkforward.spec import GateSpec

    return GateSpec(
        spec_id="hdf_capture_adversary",
        authored_utc="2026-08-01T00:00:00+00:00",
        reserved_blackout=blackout,
        capture_windows=windows,
        capture_declaration_id="HDF_SYNTHETIC_PROSPECTIVE_PLAN",
        capture_declaration_sha256s=hashes,
    )


def test_implementation_imports_are_bound_to_selected_repository():
    from src.research_infra.walkforward import spec, stats

    for module in (spec, stats):
        assert Path(module.__file__).resolve().is_relative_to(REPO)


def test_duplicate_declaration_digest_is_rejected():
    with pytest.raises(ValueError, match="must not repeat"):
        _capture_spec(
            windows=(("2026-01-01", "2026-01-30"),),
            hashes=("1" * 64, "1" * 64),
        )


def test_capture_authority_is_deeply_immutable_after_construction():
    windows = [
        ["2026-01-01", "2026-01-30"],
        ["2026-04-01", "2026-04-30"],
    ]
    hashes = ["1" * 64, "2" * 64]
    blackout = [["2026-03-01", "2026-03-31"]]
    spec = _capture_spec(windows=windows, hashes=hashes, blackout=blackout)
    original_seal = spec.seal()

    windows[0][0] = "2026-01-02"
    windows.append(["2026-05-01", "2026-05-30"])
    hashes[0] = "3" * 64
    blackout.clear()

    assert spec.capture_windows == (
        ("2026-01-01", "2026-01-30"),
        ("2026-04-01", "2026-04-30"),
    )
    assert spec.capture_declaration_sha256s == ("1" * 64, "2" * 64)
    assert spec.reserved_blackout == (("2026-03-01", "2026-03-31"),)
    assert spec.seal() == original_seal


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.pop("spec_sha256"), "spec seal missing or invalid"),
        (lambda payload: payload.__setitem__("spec_sha256", 0), "spec seal missing or invalid"),
        (lambda payload: payload.__setitem__("schema", "forged.capture.schema"), "schema"),
    ],
)
def test_capture_files_require_exact_schema_and_valid_seal(tmp_path, mutation, message):
    from src.research_infra.walkforward.spec import GateSpec

    spec = _capture_spec(
        windows=(("2026-01-01", "2026-01-30"),),
        hashes=("1" * 64,),
    )
    payload = spec.as_dict()
    mutation(payload)
    path = tmp_path / "capture-spec.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        GateSpec.read(str(path))


def test_capture_date_aliases_are_refused_instead_of_truncated():
    with pytest.raises(ValueError, match="exact ISO date"):
        _capture_spec(
            windows=(("2026-01-01junk", "2026-01-30"),),
            hashes=("1" * 64,),
        )
    with pytest.raises(ValueError, match="exact ISO date"):
        _capture_spec(
            windows=(("2026-01-01", "2026-01-30"),),
            hashes=("1" * 64,),
            blackout=(("2026-03-01T00:00:00", "2026-03-31"),),
        )


def test_capture_authority_refuses_partial_malformed_empty_and_one_day_shapes():
    from src.research_infra.walkforward.spec import GateSpec

    with pytest.raises(ValueError, match="must be set together"):
        GateSpec(
            spec_id="hdf_partial_capture",
            authored_utc="2026-08-01T00:00:00+00:00",
            capture_windows=(("2026-01-01", "2026-01-30"),),
        )
    with pytest.raises(ValueError, match="lowercase full sha256"):
        _capture_spec(
            windows=(("2026-01-01", "2026-01-30"),), hashes=("A" * 64,)
        )
    with pytest.raises(ValueError, match="at least one window"):
        _capture_spec(windows=(), hashes=("1" * 64,))
    with pytest.raises(ValueError, match="at least two calendar days"):
        _capture_spec(
            windows=(("2026-01-01", "2026-01-01"),), hashes=("1" * 64,)
        )


def test_capture_file_symlink_cannot_bypass_the_content_seal(tmp_path):
    from src.research_infra.walkforward.spec import GateSpec

    spec = _capture_spec(
        windows=(("2026-01-01", "2026-01-30"),), hashes=("1" * 64,)
    )
    target = tmp_path / "sealed.json"
    alias = tmp_path / "alias.json"
    spec.write(str(target))
    alias.symlink_to(target)
    assert GateSpec.read(str(alias)).seal() == spec.seal()

    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["capture_windows"][0][0] = "2026-01-02"
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="spec seal mismatch"):
        GateSpec.read(str(alias))


def test_next_day_captures_are_independent_but_shared_endpoints_are_refused():
    adjacent = _capture_spec(
        windows=(
            ("2026-04-01", "2026-04-30"),
            ("2026-05-01", "2026-05-30"),
        ),
        hashes=("1" * 64,),
    )
    assert adjacent.capture_windows[0][1] == "2026-04-30"
    assert adjacent.capture_windows[1][0] == "2026-05-01"

    with pytest.raises(ValueError, match="strictly ordered and non-overlapping"):
        _capture_spec(
            windows=(
                ("2026-04-01", "2026-04-30"),
                ("2026-04-30", "2026-05-30"),
            ),
            hashes=("1" * 64,),
        )


def _anchored_sign_answer(segments, block):
    block_sums = [
        math.fsum(segment[start : start + block])
        for segment in segments
        for start in range(0, len(segment), block)
    ]
    observed = math.fsum(block_sums)
    tail = sum(
        math.fsum(sign * value for sign, value in zip(signs, block_sums))
        >= observed - 1e-12
        for signs in itertools.product((-1.0, 1.0), repeat=len(block_sums))
    )
    return block_sums, tail, 2 ** len(block_sums)


def test_segmented_sign_null_has_capture_start_origin_and_known_exact_answer():
    from src.research_infra.walkforward.stats import block_permutation_p

    segments = (
        (1.0, -0.5, 2.0, 0.25, 1.25),
        (-0.25, 1.5, 0.5, -0.1),
        (0.75, 0.4, -0.2),
    )
    block = 3
    block_sums, tail, states = _anchored_sign_answer(segments, block)
    pooled = [value for segment in segments for value in segment]
    result = block_permutation_p(
        pooled,
        block=block,
        n_perm=10_000,
        seed=7,
        segment_lengths=tuple(map(len, segments)),
    )

    assert block_sums == pytest.approx([2.5, 1.5, 1.75, -0.1, 0.95])
    assert result["phase_policy"] == "none_capture_start_anchored"
    assert result["alignment_policy"] == "first_oos_day_of_each_sealed_capture"
    assert result["n_blocks_by_segment"] == [2, 2, 1]
    assert result["distinct_sign_assignments"] == states == 32
    assert result["n_permutations_evaluated"] == states
    assert result["p_value"] == pytest.approx(tail / states)
    assert result["seed_effective"] is False

    reordered = segments[2], segments[0], segments[1]
    reordered_result = block_permutation_p(
        [value for segment in reordered for value in segment],
        block=block,
        n_perm=10_000,
        seed=999,
        segment_lengths=tuple(map(len, reordered)),
    )
    assert reordered_result["p_value"] == result["p_value"]


def test_exact_sign_tail_retains_mathematically_tied_states():
    from src.research_infra.walkforward.stats import block_permutation_p

    segments = ((0.1, -1.0), (0.1, -0.1))
    block_sums, tail, states = _anchored_sign_answer(segments, block=1)
    assert (tail, states) == (12, 16)

    result = block_permutation_p(
        [value for segment in segments for value in segment],
        block=1,
        n_perm=states,
        segment_lengths=tuple(map(len, segments)),
    )
    assert result["enumeration"] == "exact"
    assert result["p_value"] == pytest.approx(tail / states)


def test_segmented_sign_null_monte_carlo_transition_is_seeded_and_explicit():
    from src.research_infra.walkforward.stats import block_permutation_p

    series = [(-1.0) ** index * (index + 1) / 10 for index in range(20)]
    a = block_permutation_p(
        series, block=1, n_perm=64, seed=19, segment_lengths=(10, 10)
    )
    b = block_permutation_p(
        series, block=1, n_perm=64, seed=19, segment_lengths=(10, 10)
    )
    assert a == b
    assert a["enumeration"] == "monte_carlo_add_one"
    assert a["seed_effective"] is True
    assert a["distinct_sign_assignments"] == 2**20
    assert a["n_permutations_evaluated"] == 64

    for bad in ((), (0, 20), (9, 10), (21,)):
        with pytest.raises(ValueError, match="segment_lengths"):
            block_permutation_p(
                series, block=1, n_perm=64, seed=19, segment_lengths=bad
            )


def test_cs_economics_nulls_and_59_member_bill_reproduce_from_first_principles():
    from src.costs import load_broker_true_costs
    from src.research_infra.walkforward import era_population
    from src.research_infra.walkforward.options import OPTIONS
    from src.research_infra.walkforward.panel import price_trades
    from src.research_infra.walkforward.stats import (
        block_permutation_p,
        day_block_bootstrap_p,
    )

    cs = _load_cs_module()
    january, _ = cs.CQ_GATE._load_repair_trades()
    april, _ = cs._load_cs_trade_records(cs.WINDOWS["april_2026"])
    may, _ = cs._load_cs_trade_records(cs.WINDOWS["may_2026"])
    raw = [*january, *april, *may]
    assert len(raw) == 11_305
    assert all(
        record.entry_utc.month not in (2, 3)
        and record.exit_utc.month not in (2, 3)
        for record in raw
    )

    base = OPTIONS["B_balanced"].with_(
        spec_id="hdf_independent_cs_math",
        account="FTMO",
        cost_artifact_sha256=cs._sha256_file(cs.PHASE17_COSTS),
        spread_band="mid",
    )
    population, priced_spec, mix = era_population.apply(
        "RECORDED",
        {cs.SLEEVE: raw},
        base,
        account="FTMO",
        band="mid",
    )
    assert mix == {"kept": 6536, "dropped": 4769, "unpriceable": 0}
    priced, coverage = price_trades(
        population[cs.SLEEVE],
        priced_spec,
        costs=load_broker_true_costs(cs.PHASE17_COSTS),
    )
    assert len(priced) == 6536
    # Wave-21 (2026-08-10): the artifact-bound slippage authority leaves six of
    # this sleeve's sixteen symbols without reconciled samples on FTMO; the
    # measured restricted-universe coverage replaces the full-universe 1.0.
    assert coverage[cs.SLEEVE].coverage_frac == pytest.approx(
        0.6355569155446756
    )

    segments = []
    segment_dates = []
    for lo, hi in (
        ("2026-01-16", "2026-01-30"),
        ("2026-04-16", "2026-04-30"),
        ("2026-05-16", "2026-05-30"),
    ):
        by_day = defaultdict(list)
        for row in priced:
            day = row.trade.entry_utc.date().isoformat()
            if lo <= day <= hi and row.status == "priced":
                by_day[day].append(row.r_net)
        dates = sorted(by_day)
        segment_dates.append(dates)
        segments.append(
            [math.fsum(by_day[day]) / len(by_day[day]) for day in dates]
        )

    lengths = tuple(map(len, segments))
    fold_means = [math.fsum(segment) / len(segment) for segment in segments]
    pooled_mean = math.fsum(fold_means) / len(fold_means)
    assert lengths == (11, 11, 9)
    assert [dates[0] for dates in segment_dates] == [
        "2026-01-16",
        "2026-04-16",
        "2026-05-18",
    ]
    assert [dates[-1] for dates in segment_dates] == [
        "2026-01-30",
        "2026-04-30",
        "2026-05-29",
    ]
    # Wave-21 restricted universe (10 of 16 symbols carry reconciled slippage
    # samples on FTMO): the full-universe fold means [11.2523, 7.4536, 3.8520]
    # move to the measured values below.
    assert fold_means == pytest.approx(
        [12.24971575505896, 7.666601968036244, 1.710644304185736],
        abs=1e-12,
    )
    assert pooled_mean == pytest.approx(7.20898734242698, abs=1e-12)

    pooled_n = sum(lengths)
    weighted_segments = [
        [
            value * pooled_n / (len(segments) * len(segment))
            for value in segment
        ]
        for segment in segments
    ]
    weighted = [value for segment in weighted_segments for value in segment]
    assert hashlib.sha256(
        json.dumps(
            [round(value, 12) for value in weighted], separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest() == (
        "f79285b9130bd67f04829e5361505a93608bc120b466029c530a7dc9694a65e4"
    )
    assert math.fsum(weighted) / len(weighted) == pytest.approx(
        pooled_mean, abs=1e-12
    )

    block_sums, exact_tail, exact_states = _anchored_sign_answer(
        weighted_segments, block=3
    )
    assert [math.ceil(length / 3) for length in lengths] == [4, 4, 3]
    assert len(block_sums) == 11
    # Restricted-universe series: the exact tail moves 2 -> 11 of 2048.
    assert (exact_tail, exact_states) == (11, 2048)
    raw_p = exact_tail / exact_states
    assert raw_p == pytest.approx(11.0 / 2048.0)
    assert 1 / exact_states == pytest.approx(0.00048828125)

    # Reconstruct the original continuous Monte Carlo sign flip independently.
    rng = np.random.default_rng(20260729)
    signs = rng.choice(
        np.array([-1.0, 1.0]),
        size=(10_000, math.ceil(len(weighted) / 3)),
    )
    expanded = np.repeat(signs, 3, axis=1)[:, : len(weighted)]
    null_means = (expanded * np.asarray(weighted)[None, :]).mean(axis=1)
    continuous_ge = int(
        np.count_nonzero(null_means >= np.asarray(weighted).mean())
    )
    # Restricted-universe series: 80 of 10,000 Monte Carlo sign draws reach the
    # observed mean (full-universe: 25).
    assert continuous_ge == 80
    assert (1 + continuous_ge) / 10_001 == pytest.approx(81.0 / 10_001.0)

    # HC's three common circular phases are not prospectively sealed.  Their
    # mathematical exact tail is 14/6144; HC reported 13/6144 because one tied
    # state fell just below the observation under a different float sum order.
    common_phase_tails = []
    for phase in range(3):
        phase_segments = []
        for segment in weighted_segments:
            offset = phase % min(3, len(segment))
            phase_segments.append(segment[offset:] + segment[:offset])
        _, phase_tail, phase_states = _anchored_sign_answer(
            phase_segments, block=3
        )
        assert phase_states == 2048
        common_phase_tails.append(phase_tail)
    # Restricted-universe series: the three circular-phase exact tails move
    # from [2, 2, 10] to the measured values below.
    assert common_phase_tails == [11, 5, 16]
    assert sum(common_phase_tails) / (3 * 2048) == pytest.approx(
        32.0 / (3 * 2048)
    )

    # Independently reconstruct the segmented centred circular bootstrap.
    values = np.asarray(weighted)
    centred = values - values.mean()
    rng = np.random.default_rng(20260729)
    bootstrap_sums = np.zeros(10_000, dtype=float)
    offset = 0
    for length in lengths:
        segment = centred[offset : offset + length]
        offset += length
        block = min(3, length)
        wrapped = np.concatenate([segment, segment[: block - 1]])
        n_blocks = math.ceil(length / block)
        starts = rng.integers(0, length, size=(10_000, n_blocks))
        indices = (
            starts[:, :, None] + np.arange(block)[None, None, :]
        ).reshape(10_000, n_blocks * block)[:, :length]
        bootstrap_sums += wrapped[indices].sum(axis=1)
    bootstrap_means = bootstrap_sums / len(values)
    bootstrap_ge = int(np.count_nonzero(bootstrap_means >= values.mean()))
    assert bootstrap_ge == 0
    assert (1 + bootstrap_ge) / 10_001 == pytest.approx(
        0.00009999000099990002
    )

    implementation = block_permutation_p(
        weighted,
        block=3,
        n_perm=10_000,
        seed=20260729,
        segment_lengths=lengths,
    )
    bootstrap = day_block_bootstrap_p(
        weighted,
        block=3,
        n_boot=10_000,
        seed=20260729,
        segment_lengths=lengths,
    )
    assert implementation["phase_policy"] == "none_capture_start_anchored"
    assert implementation["p_value"] == pytest.approx(raw_p)
    assert bootstrap["p_value"] == pytest.approx(1 / 10_001)
    assert max(implementation["p_value"], bootstrap["p_value"]) == raw_p

    family_payload = json.loads(cs.V27.read_text(encoding="utf-8"))
    family = family_payload["families"]["CANDIDATE_BOOK_V1"]
    members = family["members"]
    assert family["high_water_size"] == len(members) == 59
    assert family["high_water_looks"] == sum(
        bool(member["look_taken"]) for member in members
    ) == 57
    assert len({member["name"] for member in members}) == 59
    assert [member["name"] for member in members].count(cs.SLEEVE) == 1

    bill = sorted([raw_p, *([1.0] * 58)])
    cs_rank = bill.index(raw_p) + 1
    q_value = min(1.0, raw_p * len(bill) / cs_rank)
    critical = 0.10 * cs_rank / len(bill)
    assert (cs_rank, len(bill)) == (1, 59)
    assert q_value == pytest.approx(0.3169, abs=1e-4)
    assert critical == pytest.approx(0.0016949152542372883)
    # The restricted-universe candidate FAILS the sealed admission bar; the
    # pre-wave-21 full-universe pass is not reproducible at current authority.
    assert raw_p > critical


def _independent_exit_oracle(spec, values, times_us, eligible, *, cost_r):
    """Third implementation of the frozen temporal state machine."""

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
            if spec.partial_fraction:
                partial += spec.partial_fraction * spec.trigger_r
                remaining -= spec.partial_fraction
            if spec.move_stop_to_break_even:
                floor = max(floor, 0.0)

        if value >= spec.hard_target_r and times_us[index] != deadline_time:
            return close(index, "hard_target", spec.hard_target_r)
        if triggered and spec.giveback_gap_r is not None:
            floor = max(floor, mfe - spec.giveback_gap_r)

    return close(len(values) - 1, "horizon_terminal_mark", values[-1])


def _reference_fields(reference):
    return {
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


def _field_mismatches(actual, expected):
    mismatches = []
    for field, wanted in expected.items():
        got = actual[field]
        if isinstance(wanted, float):
            if not math.isclose(float(got), wanted, rel_tol=0.0, abs_tol=1e-10):
                mismatches.append((field, got, wanted))
        elif got != wanted:
            mismatches.append((field, got, wanted))
    return mismatches


def test_all_3200_fast_and_reference_rows_match_the_third_oracle():
    fc = _load_fc_module()
    _, overlays, _ = fc.load_protocol()
    rng = random.Random(3150)
    fast_mismatches = []
    reference_mismatches = []

    for case in range(80):
        level = 0.0
        values_list = []
        for _ in range(120):
            level += rng.uniform(-0.32, 0.34)
            values_list.append(level)
        if case % 4 == 0:
            values_list[9], values_list[19] = 0.55, -0.05
        elif case % 4 == 1:
            values_list[14], values_list[24] = 1.3, 0.7
        elif case % 4 == 2:
            values_list[34] = 2.1
        else:
            values_list[44] = -1.1

        values = np.asarray(values_list, dtype=np.float64)
        times = np.asarray(
            [(index + 1) * fc.MICROSECONDS_PER_MINUTE for index in range(120)],
            dtype=np.int64,
        )
        eligible = np.ones(len(values), dtype=np.bool_)
        path = fc.PathArrays(values, times, eligible, "HDF_THIRD_ORACLE")
        points = tuple(
            fc.ExitPathPoint(int(times[index]), float(value), True, index)
            for index, value in enumerate(values)
        )
        for overlay in overlays:
            oracle = _independent_exit_oracle(
                overlay, values, times, eligible, cost_r=0.137
            )
            reference = fc.replay_signed_path(
                overlay,
                points,
                decision_time_us=0,
                cost_r=0.137,
                source_mode="HDF_THIRD_ORACLE",
            )
            fast = fc.fast_replay_one(
                overlay, path, decision_us=0, cost_r=0.137
            )
            ref_delta = _field_mismatches(_reference_fields(reference), oracle)
            fast_delta = _field_mismatches(
                {field: getattr(fast, field) for field in oracle}, oracle
            )
            if ref_delta:
                reference_mismatches.append((case, overlay.variant_id, ref_delta))
            if fast_delta:
                fast_mismatches.append((case, overlay.variant_id, fast_delta))

    assert not reference_mismatches, (
        f"reference_mismatch_count={len(reference_mismatches)} "
        f"first={reference_mismatches[:2]}"
    )
    assert not fast_mismatches, (
        f"fast_mismatch_count={len(fast_mismatches)} first={fast_mismatches[:2]}"
    )


def test_terminal_observation_completes_trigger_partial_and_ratchet_state():
    fc = _load_fc_module()
    minute = fc.MICROSECONDS_PER_MINUTE

    partial = fc.ExitOverlaySpec.from_protocol_cell(
        {
            "id": "HDF_PARTIAL",
            "kind": "partial_harvest",
            "trigger_r": 0.5,
            "fraction": 0.5,
        }
    )
    identity = fc.ExitOverlaySpec.from_protocol_cell(
        {"id": "HDF_IDENTITY", "kind": "identity"}
    )
    cases = (
        (partial, [0.1, 0.6]),
        (identity, [1.0, 1.5]),
    )

    for overlay, raw_values in cases:
        values = np.asarray(raw_values, dtype=np.float64)
        times = np.asarray([minute, 2 * minute], dtype=np.int64)
        eligible = np.ones(2, dtype=np.bool_)
        oracle = _independent_exit_oracle(
            overlay, values, times, eligible, cost_r=0.0
        )
        reference = fc.replay_signed_path(
            overlay,
            tuple(
                fc.ExitPathPoint(int(times[index]), float(value), True, index)
                for index, value in enumerate(values)
            ),
            decision_time_us=0,
            cost_r=0.0,
            source_mode="HDF_TERMINAL",
        )
        fast = fc.fast_replay_one(
            overlay,
            fc.PathArrays(values, times, eligible, "HDF_TERMINAL"),
            decision_us=0,
            cost_r=0.0,
        )
        assert _field_mismatches(_reference_fields(reference), oracle) == []
        assert _field_mismatches(
            {field: getattr(fast, field) for field in oracle}, oracle
        ) == []

    assert _independent_exit_oracle(
        partial,
        np.asarray([0.1, 0.6]),
        np.asarray([minute, 2 * minute]),
        np.ones(2, dtype=np.bool_),
        cost_r=0.0,
    )["gross_r"] == pytest.approx(0.55)
    assert _independent_exit_oracle(
        identity,
        np.asarray([1.0, 1.5]),
        np.asarray([minute, 2 * minute]),
        np.ones(2, dtype=np.bool_),
        cost_r=0.0,
    )["protective_floor_r"] == pytest.approx(1.1)


def test_historical_fc_family_disposition_and_sealed_artifact_hashes_are_unchanged():
    expected_hashes = {
        "OVERLAY_PROTOCOL.json": (
            "173b6be4dcd7a1e55248cd5f00dfcad4a09ebefd80b1739acc054ee04037f422"
        ),
        "OVERLAY_RESULTS.json": (
            "106b3dfbe8e3e7c66e0c90ab27a81e8cebea973a1fb494e2cdccf38cac17d3ae"
        ),
        "NULL_CONTROLS.json": (
            "07218f01fe33f5efafd502caf8963cbc5710d14f67ad9bbff7ad92d7e8c0b558"
        ),
        "EXECUTED_OVERLAY_REPLAY.json": (
            "7e73e3d16d6f4ebbfec478d61e5cb449f41222ac8fab4defc253c6707a81ccf9"
        ),
        "LOOK_MANIFEST.json": (
            "ca21eb4b58bc4342550542a8ca7d4d2b182c325fb33648c2dfcb34e9331bb147"
        ),
    }
    for name, expected in expected_hashes.items():
        assert hashlib.sha256((FC_EVIDENCE / name).read_bytes()).hexdigest() == expected

    results = json.loads(
        (FC_EVIDENCE / "OVERLAY_RESULTS.json").read_text(encoding="utf-8")
    )
    complete = json.loads(FC_COMPLETE.read_text(encoding="utf-8"))
    cells = results["cells"]
    selected = set(results["top_three_frozen_from_january_train"])
    assert results["family_denominator"] == len(cells) == 40
    assert len(selected) == 3
    assert len(set(cells) - selected) == 37
    assert all(
        not results["gates"][variant]["executed_persistence_gate_passes"]
        and not results["gates"][variant]["residual_persistence_gate_passes"]
        for variant in selected
    )

    surfaces = (
        "january_executed_train",
        "january_executed_holdout",
        "february_executed_attribution",
    )
    assert not [
        variant
        for variant, cell in cells.items()
        if all(cell[surface]["total_net_r"] > 0.0 for surface in surfaces)
    ]
    assert not [
        variant
        for variant, cell in cells.items()
        if cell["january_executed_train"]["total_net_r"]
        + cell["january_executed_holdout"]["total_net_r"]
        > 0.0
    ]
    verified = complete["verified_result"]
    assert verified["family_size"] == 40
    assert verified["executed_persistent_candidates"] == []
    assert verified["residual_persistent_candidates"] == []
    assert verified["implemented_authoritative_candidate"] is None

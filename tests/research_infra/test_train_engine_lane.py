"""Session CD (B2250-B2258) -- the lane-iteration purpose, the repairs, the projection.

Behavioural, in CC's style: every test asserts what the machinery DOES, not what
a source string says. The three properties worth naming up front, because they
are the ones a later session will be tempted to loosen:

1. **The two axes stay two axes.** January 2026 must authorize for
   `LANE_ITERATION` (surface `VAL`) and must refuse for `TRAINING` (role
   `SEALED`). A change that makes both succeed has collapsed the distinction the
   whole lane rests on.
2. **A lane look cannot become a training artifact**, and vice versa, without
   anyone remembering to check.
3. **Every repair has an inert control**, and the control is not merely "the flag
   is off" -- it installs the same wrapper.
"""

from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

from src.research_infra.train_engine import cuts, guard, identity, lane, repairs
from src.research_infra.training_lane import IterationLedger

SEALED_JANUARY = ("2026-01-01", "2026-01-31")


# ---------------------------------------------------------------------------
# the two axes
# ---------------------------------------------------------------------------


def test_sealed_january_iterates_but_does_not_train() -> None:
    """The single fact Session CD exists on top of."""

    ok = guard.authorize_window(
        start=SEALED_JANUARY[0],
        end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    assert ok.dominant_surface == "VAL"
    assert set(ok.roles.values()) == {"SEALED"}
    assert ok.may_emit_iteration_evidence is True
    assert ok.may_emit_training_evidence is False

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start=SEALED_JANUARY[0],
            end=SEALED_JANUARY[1],
            purpose=guard.PURPOSE_TRAINING,
        )


def test_the_authorization_carries_the_used_once_disclosure() -> None:
    """A VAL figure must drag its disclosure without anyone remembering to."""

    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    assert ok.disclosures
    assert any("selection surface" in text for text in ok.disclosures)


@pytest.mark.parametrize("purpose", list(guard.PURPOSES))
def test_the_live_forward_stream_is_refused_under_every_purpose(purpose: str) -> None:
    """TEST has no escape hatch, and adding a purpose must not create one."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-07-29", end="2026-07-30", purpose=purpose)


@pytest.mark.parametrize("purpose", list(guard.PURPOSES))
def test_the_uncovered_gap_is_refused_under_every_purpose(purpose: str) -> None:
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-06-05", end="2026-06-06", purpose=purpose)


@pytest.mark.parametrize("purpose", list(guard.PURPOSES))
def test_march_is_still_refused_under_every_purpose(purpose: str) -> None:
    """CB's invariant, re-asserted because CD added a purpose to the list."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-03-10", end="2026-03-11", purpose=purpose)


def test_a_surface_refusal_is_catchable_as_a_window_refusal() -> None:
    """`SurfaceRefusal` is not a `PartitionRefusal`; re-raising is what makes
    `except WindowRefused` sufficient. This is CB's section-5.1 bug, one
    function later."""

    from src.research_infra.trainer_partitions import PartitionRefusal

    with pytest.raises(PartitionRefusal):
        guard.authorize_window(
            start="2026-07-29", end="2026-07-30",
            purpose=guard.PURPOSE_LANE_ITERATION,
        )


def test_both_axes_are_recorded_per_day_not_just_the_one_that_gated() -> None:
    ok = guard.authorize_window(
        start="2026-01-05", end="2026-01-07", purpose=guard.PURPOSE_LANE_ITERATION,
    )
    payload = ok.as_dict()
    assert set(payload["roles"]) == set(payload["surfaces"])
    assert payload["surface_map_digest"]
    assert payload["surface_checked"] is True


# ---------------------------------------------------------------------------
# the emitters cannot be crossed
# ---------------------------------------------------------------------------


def _economics() -> dict:
    return {
        "counts": {"trade": 1, "order": 1, "scorecard": 0, "missed": 0},
        "trades": [
            {field: 1 for field in identity.TRADE_IDENTITY_FIELDS},
        ],
        "missed_digest": {"rows": 0},
    }


def test_a_reproduction_run_cannot_emit_a_lane_artifact(tmp_path) -> None:
    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_REPRODUCTION,
    )
    with pytest.raises(lane.IterationOutputRefused):
        lane.write_iteration_outputs(
            out_dir=tmp_path, authorization=ok, economics=_economics(),
            run_fingerprint={}, measurements={}, spec={},
        )


def test_a_lane_run_cannot_emit_a_training_artifact(tmp_path) -> None:
    from src.research_infra.train_engine import runner

    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    with pytest.raises(runner.TrainingOutputRefused):
        runner.write_training_outputs(
            out_dir=tmp_path, authorization=ok, economics=_economics(),
            run_fingerprint={}, measurements={},
        )


def test_the_lane_artifact_is_stamped_and_carries_its_disclosure(tmp_path) -> None:
    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    written = lane.write_iteration_outputs(
        out_dir=tmp_path, authorization=ok, economics=_economics(),
        run_fingerprint={"train_engine_version": "x"}, measurements={},
        spec={"arm": "S0R0"},
    )
    header = json.loads(written["trade_table"].read_text().splitlines()[0])
    assert header["evidence_class"] == lane.LANE_EVIDENCE_STAMP
    assert "TRAINING_EVIDENCE" not in header["evidence_class"]
    assert header["disclosures"]
    receipt = json.loads(written["receipt"].read_text())
    assert receipt["spec"]["arm"] == "S0R0"


# ---------------------------------------------------------------------------
# the auto-logged look
# ---------------------------------------------------------------------------


def test_an_arm_logs_exactly_one_unbilled_val_row(tmp_path) -> None:
    ledger = tmp_path / "ITER.jsonl"
    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    spec = lane.run_spec(
        arm="S0R0", authorization=ok, patches=["a"], repairs=["commission_broker_true"]
    )
    row = lane.log_look(
        authorization=ok, spec=spec, session="CD", ledger_path=ledger,
        metric=-0.9, metric_name="pool_mean_r",
    )
    assert row["surface"] == "VAL"
    assert row["billed"] is False
    assert row["surface_stamp"]["test_days"] == []
    assert row["disclosures"]
    assert len(IterationLedger(ledger).rows()) == 1


def test_the_look_is_stamped_over_the_days_the_guard_enumerated(tmp_path) -> None:
    """Passing `days` rather than a span is what stops a caller widening or
    narrowing the recorded window relative to what actually ran."""

    ok = guard.authorize_window(
        start="2026-01-05", end="2026-01-09", purpose=guard.PURPOSE_LANE_ITERATION,
    )
    row = lane.log_look(
        authorization=ok,
        spec=lane.run_spec(arm="S0R0", authorization=ok, patches=[], repairs=[]),
        session="CD", ledger_path=tmp_path / "L.jsonl",
    )
    assert row["surface_stamp"]["n_days"] == 5
    assert row["date_span"] == ["2026-01-05", "2026-01-09"]


def test_the_spec_separates_speed_cuts_from_economic_repairs() -> None:
    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    spec = lane.run_spec(
        arm="S1R1", authorization=ok,
        patches=["gc_during_chunk"], repairs=["swap_horizon_true"],
    )
    assert spec["speed_cuts"] == ["gc_during_chunk"]
    assert spec["repairs"] == ["swap_horizon_true"]
    # Two runs that differ only in the repair set must be different candidates.
    other = lane.run_spec(arm="S1R1", authorization=ok, patches=["gc_during_chunk"], repairs=[])
    from src.research_infra.training_lane.iteration_ledger import spec_digest

    assert spec_digest(spec) != spec_digest(other)


def test_a_lane_registry_requires_an_explicit_window_before_running(tmp_path) -> None:
    """A valid January default must never substitute for a requested virgin window."""

    from src.research_infra.train_engine import runner

    class HistoricalInputs:
        @staticmethod
        def resolve_sealed_january(_root):
            raise AssertionError("no historical input may resolve for a registry run")

    with pytest.raises(ValueError, match="requires_explicit_window"):
        runner._resolve_run_inputs(
            sealed_inputs=HistoricalInputs(),
            lane_input_registry=tmp_path / "registry.json",
            lane_window_id=None,
            purpose=guard.PURPOSE_LANE_ITERATION,
        )


def test_the_explicit_february_window_reaches_the_registry_resolver(
    tmp_path, monkeypatch
) -> None:
    """Exercise the selection behavior without decoding any economic row."""

    from src.research_infra import lane_rematerialization
    from src.research_infra.train_engine import runner

    selected = object()
    calls = []

    class StubRegistry:
        def __init__(self, path: Path):
            calls.append(("init", path))

        def resolve(self, *, window_id: str, purpose: str):
            calls.append(("resolve", window_id, purpose))
            return selected

    monkeypatch.setattr(lane_rematerialization, "LaneInputRegistry", StubRegistry)
    sealed, provider, resolved = runner._resolve_run_inputs(
        sealed_inputs=object(),
        lane_input_registry=tmp_path / "registry.json",
        lane_window_id="february_2026",
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    assert sealed is provider is selected
    assert resolved == "february_2026"
    assert calls[-1] == (
        "resolve",
        "february_2026",
        guard.PURPOSE_LANE_ITERATION,
    )


def test_lane_prefix_is_bound_before_the_engine_receives_the_provider() -> None:
    from src.research_infra.train_engine import runner

    class Provider:
        window_end = "2026-05-31"

        def for_prefix(self, end: str):
            assert end == "2026-05-30"
            return Bounded()

    class Bounded:
        window_end = "2026-05-30"

    original = Provider()
    assert runner._prefix_lane_inputs(
        original,
        effective_end="2026-05-30",
        stop_after_day="2026-05-30",
    ).window_end == "2026-05-30"
    assert runner._prefix_lane_inputs(
        original,
        effective_end="2026-05-31",
        stop_after_day=None,
    ) is original


def test_lane_prefix_plan_is_bound_after_the_effective_scope() -> None:
    from src.research_infra.train_engine import runner

    calls = []

    class Provider:
        window_end = "2026-05-31"

        def for_prefix(self, end: str):
            calls.append(("prefix", end))
            return Bounded()

        def with_canonical_source_plan_digest(self, _digest: str):
            raise AssertionError("the full-window provider must not receive prefix plan")

    class Bounded:
        window_end = "2026-05-30"

        def with_canonical_source_plan_digest(self, digest: str):
            calls.append(("plan", digest))
            return self

    effective = runner._effective_lane_inputs(
        Provider(),
        effective_end="2026-05-30",
        stop_after_day="2026-05-30",
        source_plan_digest="a" * 64,
    )
    assert effective.window_end == "2026-05-30"
    assert calls == [("prefix", "2026-05-30"), ("plan", "a" * 64)]


def test_a_window_selector_is_refused_without_a_lane_registry() -> None:
    from src.research_infra.train_engine import runner

    with pytest.raises(ValueError, match="window_requires_lane_input_registry"):
        runner._resolve_run_inputs(
            sealed_inputs=object(),
            lane_input_registry=None,
            lane_window_id="february_2026",
            purpose=guard.PURPOSE_LANE_ITERATION,
        )


def test_the_lane_cannot_write_a_gate_verdict(tmp_path) -> None:
    """Session CD is the session most tempted to write `rejected`."""

    from src.research_infra.training_lane import IterationLedgerRefusal

    ok = guard.authorize_window(
        start=SEALED_JANUARY[0], end=SEALED_JANUARY[1],
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    for word in ("rejected", "admitted", "graduated"):
        with pytest.raises(IterationLedgerRefusal):
            lane.log_look(
                authorization=ok,
                spec=lane.run_spec(arm="S0R0", authorization=ok, patches=[], repairs=[]),
                session="CD", verdict=word, ledger_path=tmp_path / "L.jsonl",
            )


# ---------------------------------------------------------------------------
# the repairs
# ---------------------------------------------------------------------------


def test_every_live_repair_has_an_inert_control() -> None:
    for live, control in repairs.REPAIR_PAIRS:
        assert live in repairs.REPAIR_IDS
        assert control in repairs.REPAIR_IDS
        assert live != control


def test_repair_ids_are_unique() -> None:
    assert len(repairs.REPAIR_IDS) == len(set(repairs.REPAIR_IDS))
    assert repairs.resolve_repairs("controls") == list(
        dict.fromkeys(repairs.resolve_repairs("controls"))
    )


def test_a_repair_that_does_not_apply_refuses_with_its_reason() -> None:
    """A repair that has no surface must say so with a cite, not fail as unknown."""

    for key in repairs.REPAIRS_THAT_DO_NOT_APPLY:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            repairs.validate_repair_ids([key])
        assert "does not apply" in str(excinfo.value)
        assert len(str(excinfo.value)) > 200  # the reason, not just the refusal


def test_an_unknown_repair_refuses_and_names_the_investigated_set() -> None:
    with pytest.raises(repairs.RepairUnavailable) as excinfo:
        repairs.validate_repair_ids(["make_it_profitable"])
    assert "time_stop_contract" in str(excinfo.value)


def test_the_swap_horizon_numbers_are_derived_not_typed() -> None:
    """AQ's lesson: a horizon constant that is really a conversion ratio."""

    assert repairs.TRUE_SWAP_HORIZON_BARS == (
        repairs.REPLAY_MAX_HOLD_MINUTES / repairs.SWAP_MODEL_MINUTES_PER_BAR
    )
    assert repairs.SEALED_SWAP_HORIZON_BARS > repairs.TRUE_SWAP_HORIZON_BARS


def test_the_commission_pricer_charges_per_trade_not_per_instrument() -> None:
    """`commission_r` scales with 1/stop distance, because the denominator is R."""

    pricer = repairs._CommissionPricer()
    near, reason_near = pricer.commission_r(
        symbol="XAUUSD", entry_price=2000.0, sl_distance=5.0
    )
    far, reason_far = pricer.commission_r(
        symbol="XAUUSD", entry_price=2000.0, sl_distance=10.0
    )
    assert reason_near == reason_far == "broker_true"
    assert near == pytest.approx(2 * far, rel=1e-9)


def test_the_commission_pricer_refuses_rather_than_charging_zero() -> None:
    """Charging a plausible number with no basis IS F38."""

    pricer = repairs._CommissionPricer()
    value, reason = pricer.commission_r(
        symbol="NOT_A_SYMBOL", entry_price=1.0, sl_distance=1.0
    )
    assert value is None
    assert reason.startswith("unpriced_instrument") or reason.startswith("cost_truth")

    value, reason = pricer.commission_r(symbol="XAUUSD", entry_price=2000.0, sl_distance=0.0)
    assert (value, reason) == (None, "no_stop_distance")


def test_all_twenty_four_replay_symbols_price() -> None:
    """AW measured 0 unpriced over the January pool; a regression here would
    silently under-charge the regeneration."""

    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        GTOS_24_SYMBOL_SURFACE,
    )

    pricer = repairs._CommissionPricer()
    unpriced = [
        symbol
        for symbol in GTOS_24_SYMBOL_SURFACE
        if pricer.commission_r(symbol=symbol, entry_price=100.0, sl_distance=1.0)[0]
        is None
    ]
    assert unpriced == []


def test_the_repair_manifest_names_its_artifact_and_its_formula() -> None:
    manifest = repairs.repair_manifest()
    assert "BROKER_TRUE_COSTS_V1.json" in manifest["commission"]["artifact"]
    assert "sl_distance_price" in manifest["commission"]["formula"]
    assert manifest["swap_horizon"]["sealed_bars"] == 32.0
    assert set(manifest["do_not_apply"]) >= {
        "time_stop_contract",
        "spread_geometry_floor_at_generation",
        "broker_clock",
    }


# ---------------------------------------------------------------------------
# the ledger projection
# ---------------------------------------------------------------------------


def test_the_projection_keeps_every_scalar_and_drops_every_container() -> None:
    row = {
        "a": 1, "b": "x", "c": None, "d": True, "e": 1.5,
        "nested": {"k": "v"}, "list": [1, 2], "tup": (1,),
    }
    out = cuts._project_scalar_row(row, frozenset())
    assert {k: v for k, v in out.items() if k != "train_lane_ledger_projection"} == {
        "a": 1, "b": "x", "c": None, "d": True, "e": 1.5,
    }
    assert out["train_lane_ledger_projection"] == cuts.LEDGER_PROJECTION_STAMP


def test_the_projection_can_keep_a_named_container() -> None:
    row = {"a": 1, "keepme": {"x": 1}, "dropme": {"y": 2}}
    out = cuts._project_scalar_row(row, frozenset({"keepme"}))
    assert out["keepme"] == {"x": 1}
    assert "dropme" not in out


def test_the_missed_opportunity_ledger_is_never_projected() -> None:
    """The substrate the lane exists to produce. A future session that adds it
    here has made the lane fast and useless."""

    assert not any(
        "MISSED" in suffix for suffix in cuts.LEDGER_PROJECTIONS
    )
    assert set(cuts.LEDGER_PROJECTIONS) == {
        "_DECISION_LEDGER.jsonl",
        "_SCORECARD_LEDGER.jsonl",
    }


def test_the_projection_preserves_row_count_and_leaves_other_ledgers_alone(tmp_path) -> None:
    """Row COUNTS are what `identity.compare_economics` gates."""

    patch = cuts.make_ledger_projection_patch()
    seen: list[tuple[str, list[dict]]] = []

    class _FakeModule:
        @staticmethod
        def append_jsonl(path, rows):
            materialised = list(rows)
            seen.append((str(path), materialised))
            return len(materialised)

    import src.research_infra.fast_engine.accel as accel

    original_module = accel._module
    accel._module = lambda name: _FakeModule  # type: ignore[assignment]
    try:
        patch.apply()
        rows = [{"a": 1, "big": {"x": [0] * 10}} for _ in range(5)]
        assert _FakeModule.append_jsonl(tmp_path / "P_DECISION_LEDGER.jsonl", iter(rows)) == 5
        assert _FakeModule.append_jsonl(tmp_path / "P_MISSED_OPPORTUNITY_LEDGER.jsonl", iter(rows)) == 5
    finally:
        accel._module = original_module  # type: ignore[assignment]

    decision_rows = seen[0][1]
    missed_rows = seen[1][1]
    assert all("big" not in row for row in decision_rows)
    assert all(row.get("big") == {"x": [0] * 10} for row in missed_rows)


def test_the_safe_set_excludes_every_memo_h_cb_2_measured_dirty() -> None:
    """CB_VERIFY_HCB2.json: `probability_debate_v4._stable_sha256` disagreed on
    100 % of its hits. CG's lean default keeps only MEASURED-CLEAN memos; the
    v2 exact successors are registered but off (net-negative, B2403/B2408)."""

    assert "proof_hash_content_memo" not in cuts.TRAIN_SAFE_SET_PATCHES
    assert "attribution_fields_identity_memo" not in cuts.TRAIN_SAFE_SET_PATCHES
    for dirty_v2 in (
        "selector_hash_content_memo_v2",
        "timewarp_hash_content_memo_v2",
        "probability_hash_content_memo_v2",
        "attribution_fields_content_memo_v2",
    ):
        assert dirty_v2 not in cuts.TRAIN_SAFE_SET_PATCHES, dirty_v2
    assert "authority_hash_content_memo" in cuts.TRAIN_SAFE_SET_PATCHES
    assert cuts.resolve_patches("safe") == list(cuts.TRAIN_SAFE_SET_PATCHES)
    # CD's spellings survive and resolve to the one lean set; the pure compute
    # subset is reachable by its own name.
    assert cuts.resolve_patches("safe+projection") == list(cuts.TRAIN_SAFE_SET_PATCHES)
    assert cuts.resolve_patches("hcb2-safe") == list(cuts.HCB2_COMPUTE_SAFE_PATCHES)


def test_the_projection_default_is_reader_bound_and_never_sealed() -> None:
    """CG promoted the projections to lane default only after deriving the keep
    set from the actual reader chain (B2400-B2401). The disk cut may be default;
    a sealed arm must never get it."""

    assert "ledger_scalar_projection" in cuts.TRAIN_DEFAULT_PATCHES
    assert "ledger_scalar_projection" in cuts.TRAIN_SAFE_SET_PATCHES
    patch = cuts.make_ledger_projection_patch()
    assert patch.default_on is True
    assert patch.sealed_compatible is False


# ---------------------------------------------------------------------------
# the MISSED pool projection -- the one cut that can lose something
# ---------------------------------------------------------------------------


def test_the_missed_keep_list_is_derived_from_the_readers_own_field_list() -> None:
    """Typed-out keep-lists go stale silently. This one cannot."""

    from src.research_infra import b7_5_diagnostic_pool as pool

    keep = cuts._missed_keep_names()
    for field in pool.FEATURE_FIELDS:
        if field.source.startswith("derived:"):
            continue
        assert field.source.split(".", 1)[0] in keep, field.source


def test_the_missed_projection_keeps_every_field_the_pool_aggregate_reads() -> None:
    """`bench._missed_digest` is what `identity.compare_economics` gates."""

    keep = cuts._missed_keep_names()
    for field in (
        "missed_opportunity_r_scoreability_status",
        "missed_opportunity_non_executable_diagnostic_scoreable",
        "opportunity_net_proxy_r",
    ):
        assert field in keep


def test_the_missed_projection_keeps_the_repair_status_columns() -> None:
    """A regenerated arm must be able to prove which repair produced it."""

    keep = cuts._missed_keep_names()
    assert {"commission_r", "commission_r_broker_true_measured",
            "commission_r_repair_status", "swap_horizon_repair_status"} <= keep


def test_the_missed_projection_default_is_reader_complete_and_never_sealed() -> None:
    """CD's field-list cut broke AW's mine on the first scoreable row (B2400).
    The default-on successor derives its keep set from the readers themselves
    and declares itself sealed-incompatible."""

    patch = cuts.make_missed_pool_projection_patch()
    assert patch.default_on is True
    assert patch.sealed_compatible is False
    assert "b7_5_diagnostic_pool" in patch.identity_argument
    assert "bench._missed_digest" in patch.identity_argument
    assert "missed_pool_projection" in cuts.TRAIN_SAFE_SET_PATCHES
    assert "missed_pool_projection" in cuts.TRAIN_DEFAULT_PATCHES
    assert "missed_pool_projection" in cuts.resolve_patches("safe+projection+pool")


# ---------------------------------------------------------------------------
# CD-5's cost-ceiling dial
# ---------------------------------------------------------------------------


def test_the_cost_ceiling_is_a_dial_and_says_so() -> None:
    """It changes admission on purpose and restores no correct value."""

    patch = repairs._make_cost_ceiling_patch(0.25)
    assert patch.patch_id == "cost_ceiling_0p25"
    assert patch.default_on is False
    assert "SEARCH dial, not a repair" in patch.summary
    assert repairs.SEALED_TOTAL_COST_CEILING_R == 0.15
    assert repairs.SEALED_TOTAL_COST_CEILING_R not in repairs.COST_CEILING_CELLS


def test_a_ceiling_cell_composes_with_the_accounting_commission_variant() -> None:
    resolved = repairs.resolve_repairs("ceiling:0.25")
    assert resolved == [
        "commission_broker_true",
        "swap_horizon_true",
        "cost_ceiling_0p25",
    ]
    repairs.validate_repair_ids(resolved)


def test_two_wrappers_that_both_regate_the_same_packet_are_refused() -> None:
    """The receipt could not say which ceiling decided."""

    with pytest.raises(repairs.RepairUnavailable) as excinfo:
        repairs.validate_repair_ids(
            ["commission_broker_true_gated", "cost_ceiling_0p25"]
        )
    assert "cannot compose" in str(excinfo.value)


def test_every_declared_ceiling_cell_builds_a_patch() -> None:
    ids = {patch.patch_id for patch in repairs.build_repairs()}
    for value in repairs.COST_CEILING_CELLS:
        assert repairs._ceiling_id(value) in ids


# ---------------------------------------------------------------------------
# FA-2's neutral-seed replicate dial
# ---------------------------------------------------------------------------

_SEALED_PROTOCOL_SEED = (
    "0c6b87233ad895d981b6ace153e1c355862dde7989e66abd4ca99c93b4edaf3a"
)
_R1_SEED = "cdeae5d82cf877ada87644f0da6373afe384d67147c326d05afa92a0bbfd7cad"
_R2_SEED = "709126af734315332fc988342a3eaf9df43ae39afb24289f173e448a1698f346"


def _canonical_sha256(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _seed_binding(payload_builder):
    """A valid factorial binding shaped like the constructor's return dict."""

    protocol = {
        "denominator": {"initial_equity_cash": 100000.0},
        "matched_risk": {"daily_accepted_risk_pct_cap": 4.0},
    }
    core = {
        "decision_contract_sha256": "c" * 64,
        "common_execution_input_digest_sha256": "d" * 64,
        "arm_id": "S0R0",
        "arm_fingerprint_sha256": "f" * 64,
        "selection_factor": "S0",
        "sizing_factor": "R0",
        "selection_mode": "neutral_hash_hard_eligible",
        "sizing_mode": "fixed_equal_account_risk",
        "neutral_selection_seed_sha256": _SEALED_PROTOCOL_SEED,
        "protocol_economics": protocol,
        "protocol_economics_digest_sha256": "e" * 64,
    }
    payload = payload_builder(**core)
    return {
        "valid": True,
        "status": "sealed_factorial_arm_bound_broker_live_closed",
        **core,
        "binding_payload": payload,
        "binding_payload_sha256": _canonical_sha256(payload),
    }


@pytest.fixture()
def stub_seed_modules(monkeypatch):
    """Stub the two rebound modules, in the cuts-test stub-module pattern."""

    calls: list = []

    def payload_builder(**kwargs):
        return {key: value for key, value in sorted(kwargs.items())}

    def original(args):
        calls.append(args)
        return _seed_binding(payload_builder)

    timewarp = types.ModuleType(repairs.TIMEWARP)
    setattr(
        timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR, _SEALED_PROTOCOL_SEED
    )
    runner = types.ModuleType(repairs.ATTEMPT5)
    runner.selection_sizing_factorial_binding_from_args = original
    runner.selection_sizing_core_binding_payload = payload_builder
    runner.stable_sha256 = _canonical_sha256
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)
    monkeypatch.setitem(sys.modules, repairs.ATTEMPT5, runner)
    return timewarp, runner, original


def test_the_seed_replicate_is_a_dial_and_says_so() -> None:
    """It changes the neutral tiebreak on purpose and restores no correct value."""

    for n in repairs.NEUTRAL_SEED_REPLICATE_CELLS:
        patch = repairs._make_neutral_seed_replicate_patch(n)
        assert patch.patch_id == f"neutral_seed_replicate_r{n}"
        assert patch.default_on is False
        assert "REPLICATE dial, not a repair" in patch.summary
        assert "measurement, not a defect" in patch.identity_argument
        assert patch.patch_id in repairs.REPAIR_IDS


def test_the_replicate_seeds_are_derived_not_typed_and_pinned() -> None:
    """The derivation rule is the artifact; the hex values are its receipts."""

    assert (
        repairs.SEALED_NEUTRAL_SELECTION_SEED_SHA256 == _SEALED_PROTOCOL_SEED
    )
    assert repairs.neutral_seed_replicate_seed(1) == _R1_SEED
    assert repairs.neutral_seed_replicate_seed(2) == _R2_SEED
    for n, expected in ((1, _R1_SEED), (2, _R2_SEED)):
        recomputed = hashlib.sha256(
            (
                f"gtos.train_engine.neutral_seed_replicate:{n}|"
                f"{_SEALED_PROTOCOL_SEED}"
            ).encode("utf-8")
        ).hexdigest()
        assert recomputed == expected
    assert len({_SEALED_PROTOCOL_SEED, _R1_SEED, _R2_SEED}) == 3
    with pytest.raises(repairs.RepairUnavailable):
        repairs.neutral_seed_replicate_seed(3)
    manifest = repairs.repair_manifest()["neutral_seed_replicate_dial"]
    assert manifest["cells"] == {
        "neutral_seed_replicate_r1": _R1_SEED,
        "neutral_seed_replicate_r2": _R2_SEED,
    }
    assert manifest["sealed_protocol_seed_sha256"] == _SEALED_PROTOCOL_SEED


def test_two_replicate_seeds_refuse_to_compose_at_validation() -> None:
    """Exactly one neutral seed ranks the pool; a second could not be named."""

    with pytest.raises(repairs.RepairUnavailable) as excinfo:
        repairs.validate_repair_ids(
            ["neutral_seed_replicate_r1", "neutral_seed_replicate_r2"]
        )
    assert "cannot compose" in str(excinfo.value)


def test_a_replicate_composes_with_the_cj_repair_set() -> None:
    """The seed arms run WITH the repaired stack; disjoint rebind symbols."""

    repairs.validate_repair_ids(
        [
            "commission_broker_true_gated",
            "swap_horizon_true",
            "neutral_seed_replicate_r1",
        ]
    )
    repairs.validate_repair_ids(
        [
            "commission_broker_true",
            "swap_horizon_true",
            "cost_ceiling_0p25",
            "neutral_seed_replicate_r2",
        ]
    )


def test_every_declared_replicate_cell_builds_a_patch() -> None:
    ids = {patch.patch_id for patch in repairs.build_repairs()}
    for n in repairs.NEUTRAL_SEED_REPLICATE_CELLS:
        assert repairs._replicate_id(n) in ids


def test_apply_rebinds_both_sides_and_revert_restores_the_sealed_seed(
    stub_seed_modules,
) -> None:
    """The loop's check constant and the runner's binding must carry the SAME
    variant, or the engine would fail the binding (or worse, silently change
    selection semantics). Revert must return the constant to the sealed seed."""

    timewarp, runner, original = stub_seed_modules
    patch = repairs._make_neutral_seed_replicate_patch(1)
    patch.apply()
    try:
        assert (
            getattr(timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR) == _R1_SEED
        )
        assert (
            runner.selection_sizing_factorial_binding_from_args
            is not original
        )
        binding = runner.selection_sizing_factorial_binding_from_args(
            object()
        )
        assert binding["neutral_selection_seed_sha256"] == _R1_SEED
        assert (
            binding["binding_payload"]["neutral_selection_seed_sha256"]
            == _R1_SEED
        )
        assert binding["binding_payload_sha256"] == _canonical_sha256(
            binding["binding_payload"]
        )
        # The check the loop performs at v4_timewarp:36276-36279: runtime seed
        # against the module constant. Both sides read the variant.
        assert binding["neutral_selection_seed_sha256"] == getattr(
            timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR
        )
        disclosure = binding["neutral_selection_seed_replicate"]
        assert disclosure["dial"] == "neutral_seed_replicate_r1"
        assert (
            disclosure["sealed_protocol_seed_sha256"] == _SEALED_PROTOCOL_SEED
        )
        assert disclosure["variant_seed_sha256"] == _R1_SEED
        assert disclosure["derivation"] == (
            repairs.NEUTRAL_SEED_REPLICATE_DERIVATION
        )
    finally:
        patch.revert()
    assert (
        getattr(timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR)
        == _SEALED_PROTOCOL_SEED
    )
    assert runner.selection_sizing_factorial_binding_from_args is original


def test_a_second_seed_dial_refuses_at_apply_time_even_without_validation(
    stub_seed_modules,
) -> None:
    """`validate_repair_ids` can be bypassed by installing patches directly;
    the apply() guard cannot."""

    timewarp, _runner, _original = stub_seed_modules
    first = repairs._make_neutral_seed_replicate_patch(1)
    second = repairs._make_neutral_seed_replicate_patch(2)
    first.apply()
    try:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            second.apply()
        assert "never compose" in str(excinfo.value)
        # The refusal left the first dial's rebind untouched.
        assert (
            getattr(timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR) == _R1_SEED
        )
    finally:
        first.revert()
    assert (
        getattr(timewarp, repairs.TIMEWARP_SEALED_SEED_ATTR)
        == _SEALED_PROTOCOL_SEED
    )


def test_the_dial_refuses_to_replicate_an_unknown_baseline(
    stub_seed_modules, monkeypatch
) -> None:
    """If the contract's seed is not the sealed one, the declared derivation
    would describe a relationship that does not hold. Refuse, never guess."""

    _timewarp, runner, _original = stub_seed_modules
    foreign = _seed_binding(runner.selection_sizing_core_binding_payload)
    foreign["neutral_selection_seed_sha256"] = "a" * 64
    monkeypatch.setattr(
        runner,
        "selection_sizing_factorial_binding_from_args",
        lambda args: foreign,
    )
    patch = repairs._make_neutral_seed_replicate_patch(2)
    patch.apply()
    try:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            runner.selection_sizing_factorial_binding_from_args(object())
        assert "unknown baseline" in str(excinfo.value)
    finally:
        patch.revert()


def test_the_dial_refuses_when_it_cannot_reproduce_the_original_payload(
    stub_seed_modules, monkeypatch
) -> None:
    """The folded-in control: before rebinding, the wrapper must rebuild the
    ORIGINAL payload byte-for-byte with the sealed seed. An engine API drift
    makes that impossible and must refuse, not emit fabricated provenance."""

    _timewarp, runner, _original = stub_seed_modules
    patch = repairs._make_neutral_seed_replicate_patch(1)
    patch.apply()
    try:

        def drifted(**kwargs):
            payload = {key: value for key, value in sorted(kwargs.items())}
            payload["new_api_field"] = 1
            return payload

        monkeypatch.setattr(
            runner, "selection_sizing_core_binding_payload", drifted
        )
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            runner.selection_sizing_factorial_binding_from_args(object())
        assert "faithful" in str(excinfo.value)
    finally:
        patch.revert()


def test_an_unrequested_factorial_binding_passes_through_as_none(
    stub_seed_modules, monkeypatch
) -> None:
    """A non-factorial run under the dial stays a non-factorial run."""

    _timewarp, runner, _original = stub_seed_modules
    monkeypatch.setattr(
        runner,
        "selection_sizing_factorial_binding_from_args",
        lambda args: None,
    )
    patch = repairs._make_neutral_seed_replicate_patch(1)
    patch.apply()
    try:
        assert (
            runner.selection_sizing_factorial_binding_from_args(object())
            is None
        )
    finally:
        patch.revert()


def test_an_unrebindable_binding_shape_refuses(
    stub_seed_modules, monkeypatch
) -> None:
    for shape in ({}, {"valid": False}, "not-a-mapping"):
        _timewarp, runner, _original = stub_seed_modules
        monkeypatch.setattr(
            runner,
            "selection_sizing_factorial_binding_from_args",
            lambda args, shape=shape: shape,
        )
        patch = repairs._make_neutral_seed_replicate_patch(1)
        patch.apply()
        try:
            with pytest.raises(repairs.RepairUnavailable):
                runner.selection_sizing_factorial_binding_from_args(object())
        finally:
            patch.revert()


# ---------------------------------------------------------------------------
# FA Phase C -- R-COST-TRUTH: spread_input_truth + cost_ruler_harmonize (B5 C3/C4-A)
# ---------------------------------------------------------------------------

_SPREAD_SOURCE = "spread_model_v1_hour_aware"


def _spx_market(*, with_swap: bool) -> dict:
    market = {"point": 1.0, "spread": 10.0}
    if with_swap:
        market.update(
            {
                "swap_mode": 1.0,
                "swap_long": -2.5,
                "swap_short": -1.0,
                "swap_rollover3days": 3,
                "trade_mode": 4.0,
                "trade_tick_value": 1.0,
                "trade_tick_size": 0.25,
            }
        )
    return market


def _spx_quote_kwargs(*, symbol: str = "SPX500", spread_points: float = 10.0) -> dict:
    """kwargs for the REAL `_predecision_tick_for_cost` spec-constant branch."""

    return dict(
        candidate={
            "symbol": symbol,
            "entry_price": 5900.0,
            "stop_loss": 5870.0,
            "side": "LONG",
        },
        path_sources=None,
        asof_utc="2026-01-15T14:30:00+00:00",
        config={
            "instruments": {
                symbol: {"market": {"point": 1.0, "spread": spread_points}}
            },
            "gtos_vnext_runtime": {},
        },
    )


def _spx_packet_kwargs(*, with_swap: bool) -> dict:
    """kwargs for the REAL `broker_calibrated_replay_cost_packet`."""

    return dict(
        candidate={
            "symbol": "SPX500",
            "entry_price": 5900.0,
            "stop_loss": 5870.0,
            "side": "LONG",
            "take_profit_1": 5960.0,
            "risk_reward_ratio": 2.0,
            "candidate_id": "rcosttruth-test",
        },
        config={
            "instruments": {"SPX500": {"market": _spx_market(with_swap=with_swap)}},
            "gtos_vnext_runtime": {
                "selected_cell_default_expected_slippage_r": 0.02
            },
            "market": {"symbol": "SPX500", "mt5_symbol": "US500.cash"},
        },
        path_sources=None,
        risk_pct=0.5,
        asof_utc="2026-01-15T14:30:00+00:00",
    )


def test_spread_truth_and_ruler_are_registered_with_controls() -> None:
    ids = {patch.patch_id for patch in repairs.build_repairs()}
    for name in (
        "spread_input_truth",
        "spread_input_truth_inert_control",
        "cost_ruler_harmonize",
        "cost_ruler_inert_control",
    ):
        assert name in ids
        assert name in repairs.REPAIR_IDS
    pairs = dict(repairs.REPAIR_PAIRS)
    assert pairs["spread_input_truth"] == "spread_input_truth_inert_control"
    assert pairs["cost_ruler_harmonize"] == "cost_ruler_inert_control"
    for patch in repairs.build_repairs():
        if patch.patch_id.startswith(("spread_input", "cost_ruler")):
            assert patch.default_on is False


def test_spread_truth_refuses_its_own_control_and_ruler_refuses_ceiling() -> None:
    for bad in (
        ["spread_input_truth", "spread_input_truth_inert_control"],
        ["cost_ruler_harmonize", "cost_ruler_inert_control"],
        ["cost_ruler_harmonize", "cost_ceiling_0p25"],
    ):
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            repairs.validate_repair_ids(bad)
        assert "cannot compose" in str(excinfo.value)


def test_the_cost_truth_spec_orders_the_ruler_outermost() -> None:
    """Wrappers nest later-outside; the ruler's census must read the ruler the
    pool actually gets, so it installs AFTER the commission wrapper."""

    resolved = repairs.resolve_repairs("cost_truth")
    assert resolved == [
        "spread_input_truth",
        "commission_broker_true_gated",
        "swap_horizon_true",
        "cost_ruler_harmonize",
    ]
    assert resolved.index("commission_broker_true_gated") < resolved.index(
        "cost_ruler_harmonize"
    )
    repairs.validate_repair_ids(resolved)


def test_the_cost_truth_stack_composes_with_the_seed_replicate() -> None:
    repairs.validate_repair_ids(
        repairs.resolve_repairs("cost_truth") + ["neutral_seed_replicate_r1"]
    )


def test_spread_truth_replaces_the_spec_constant_with_the_model_price() -> None:
    """B5 C3's flagship, in its wave-21 NATIVE form. The engine itself now
    prices spread model-first and fail-closed: the per-row constant 10.0
    (16.7x tick truth) can no longer reach a quote AT ALL -- without broker
    identity the row is a source gap, never the constant; with identity it is
    the era/hour-aware model price. The retrofit patch is inert on the native
    engine and must count the row as kept, not replaced."""

    import copy

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    # 1. Without broker identity: fail-closed gap; the spec constant never prices.
    kwargs = _spx_quote_kwargs()
    gap_tick, gap_meta = v4t._predecision_tick_for_cost(**kwargs)
    assert gap_meta["quote_source"] == "spread_model_source_gap"
    assert not gap_tick
    assert "spread_model_unavailable:CostTruthError" in gap_meta["source_gaps"]

    # 2. With broker identity: the model prices natively.
    kwargs = copy.deepcopy(kwargs)
    kwargs["config"]["broker_profile"] = {"server": "FTMO-Server3"}
    tick, meta = v4t._predecision_tick_for_cost(**kwargs)
    assert meta["quote_source"] == _SPREAD_SOURCE
    width = tick["ask"] - tick["bid"]
    # SPX500 is anchored at 0.6 price units (MEASURED, 783,729 ticks); era and
    # hour shaping move it, never back to the 10.0 constant's order of
    # magnitude. Loose band on purpose.
    assert 0.25 <= width <= 1.25
    assert width == pytest.approx(meta["spread_model_spread_price"])
    # |entry-stop| = 30, so the charged spread_r is width / 30.
    assert meta["synthetic_quote_spread_r"] == pytest.approx(width / 30.0)
    assert 0.005 <= meta["synthetic_quote_spread_r"] <= 0.05
    assert meta["spread_model_account"] == "FTMO"
    assert meta["spread_model_band"] == "mid"
    assert meta["spread_model_era"] == "2026Q1"
    assert meta["spread_model_coverage"] == "MEASURED"

    # 3. The retrofit patch is inert on the native engine: same bytes out,
    #    censused as kept, nothing replaced.
    repairs.reset_repair_stats()
    patch = repairs._make_spread_truth_patch(live=True)
    patch.apply()
    try:
        patched = v4t._predecision_tick_for_cost(**kwargs)
    finally:
        patch.revert()
    assert patched == (tick, meta)
    report = repairs.repair_report()["spread_input_truth"]
    assert report["applied"] == 0
    assert report["errors"] == {"kept:" + _SPREAD_SOURCE: 1}

    # Revert restores the native engine byte-for-byte.
    tick_after, meta_after = v4t._predecision_tick_for_cost(**kwargs)
    assert (tick_after, meta_after) == (tick, meta)


def test_spread_truth_replaces_the_floor_table_and_counts_undecidable() -> None:
    """USOIL_cash used to ride TICK_SPREAD_FLOOR_R (0.0270 R, a round-trip
    constant, not a decision-time quote). Wave-21's native model-first engine
    retired that table read: without broker identity the row is a fail-closed
    gap, with identity it is the model price -- and its 2026Q1 era is still
    said to be undecidable instead of hidden."""

    import copy

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = dict(
        candidate={
            "symbol": "USOIL_cash",
            "entry_price": 70.0,
            "stop_loss": 69.5,
            "side": "LONG",
        },
        path_sources=None,
        asof_utc="2026-01-15T14:30:00+00:00",
        config={"instruments": {}, "gtos_vnext_runtime": {}},
    )
    gap_tick, gap_meta = v4t._predecision_tick_for_cost(**kwargs)
    assert gap_meta["quote_source"] == "spread_model_source_gap"
    assert not gap_tick

    kwargs = copy.deepcopy(kwargs)
    kwargs["config"]["broker_profile"] = {"server": "FTMO-Server3"}
    tick, meta = v4t._predecision_tick_for_cost(**kwargs)
    assert meta["quote_source"] == _SPREAD_SOURCE
    assert meta["spread_model_decidable"] is False
    assert meta["spread_model_era"] == "2026Q1"
    assert tick["ask"] - tick["bid"] == pytest.approx(
        meta["spread_model_spread_price"]
    )

    # The retrofit patch is inert on the native engine and censuses the row.
    repairs.reset_repair_stats()
    patch = repairs._make_spread_truth_patch(live=True)
    patch.apply()
    try:
        patched = v4t._predecision_tick_for_cost(**kwargs)
    finally:
        patch.revert()
    assert patched == (tick, meta)
    report = repairs.repair_report()["spread_input_truth"]
    assert report["applied"] == 0
    assert report["errors"]["kept:" + _SPREAD_SOURCE] == 1


def test_spread_truth_keeps_the_real_tick_and_conservative_default_branches(
    monkeypatch,
) -> None:
    """A genuine last-tick quote is more honest than any model, and the
    conservative-default class is a fail-closed refusal the repair must not
    silently delete. Both pass through UNTOUCHED and counted."""

    from datetime import datetime, timezone

    kept_cases = [
        {
            "quote_source": "historical_ftmo_predecision_tick",
            "historical_tick_spread_r": 0.021,
            "measured_tick_spread_floor_used_as_quote_substitute": False,
        },
        {
            "quote_source": "conservative_default_spread_r_no_tick_or_symbol_spec",
            "synthetic_quote_spread_r": 0.10,
        },
    ]
    for frozen_meta in kept_cases:
        frozen_tick = {"bid": 99.0, "ask": 99.05, "time_utc": "t"}

        def boom(**kwargs):
            raise AssertionError("synthesis must not run for a kept branch")

        timewarp = types.ModuleType(repairs.TIMEWARP)
        timewarp._predecision_tick_for_cost = (
            lambda ft=frozen_tick, fm=frozen_meta, **kwargs: (ft, fm)
        )
        timewarp._broker_cost_tick_from_spread_r = boom
        timewarp.parse_utc = lambda value: datetime(
            2026, 1, 15, 14, 30, tzinfo=timezone.utc
        )
        monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

        repairs.reset_repair_stats()
        patch = repairs._make_spread_truth_patch(live=True)
        patch.apply()
        try:
            tick, meta = timewarp._predecision_tick_for_cost(
                candidate={"symbol": "EURUSD", "entry_price": 1.1, "stop_loss": 1.09},
                path_sources=None,
                asof_utc="2026-01-15T14:30:00+00:00",
                config={},
            )
        finally:
            patch.revert()
        assert tick is frozen_tick and meta is frozen_meta
        report = repairs.repair_report()["spread_input_truth"]
        assert report["applied"] == 0 and report["unpriced"] == 0
        assert report["errors"] == {
            "kept:" + frozen_meta["quote_source"]: 1
        }


def test_spread_truth_replaces_the_floor_substitute_inside_the_tick_branch(
    monkeypatch,
) -> None:
    """A crossed/zero-width tick makes the tick branch fall back to the floor
    TABLE while keeping the tick label -- a floor use, replaced as one."""

    from datetime import datetime, timezone

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    frozen_meta = {
        "quote_source": "historical_ftmo_predecision_tick",
        "historical_tick_spread_r": 0.0270,
        "historical_tick_time_utc": "2026-01-15T14:29:12+00:00",
        "measured_tick_spread_floor_used_as_quote_substitute": True,
    }
    frozen_tick = {"bid": 69.99, "ask": 70.01, "time_utc": "t"}
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp._predecision_tick_for_cost = lambda **kwargs: (
        frozen_tick,
        frozen_meta,
    )
    # The real synthesis helper, so the emitted quote shape is the engine's.
    timewarp._broker_cost_tick_from_spread_r = v4t._broker_cost_tick_from_spread_r
    timewarp.parse_utc = lambda value: datetime(
        2026, 1, 15, 14, 30, tzinfo=timezone.utc
    )
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_spread_truth_patch(live=True)
    patch.apply()
    try:
        tick, meta = timewarp._predecision_tick_for_cost(
            candidate={
                "symbol": "USOIL_cash",
                "entry_price": 70.0,
                "stop_loss": 69.5,
            },
            path_sources=None,
            asof_utc="2026-01-15T14:30:00+00:00",
            config={},
        )
    finally:
        patch.revert()
    assert meta["quote_source"] == _SPREAD_SOURCE
    assert meta["pre_repair_quote_class"] == "historical_tick_floor_substitute"
    # The tick branch's own provenance survives the merge.
    assert meta["historical_tick_time_utc"] == "2026-01-15T14:29:12+00:00"
    assert tick["ask"] - tick["bid"] == pytest.approx(
        meta["spread_model_spread_price"]
    )
    report = repairs.repair_report()["spread_input_truth"]
    assert report["errors"]["replaced:historical_tick_floor_substitute"] == 1


def test_spread_truth_unpriced_symbol_keeps_frozen_and_counts() -> None:
    """A symbol the model cannot price must never receive an invented number.
    Pre-wave-21 that meant 'keep the frozen constant and count unpriced'; the
    native engine is stricter: the row is a fail-closed source gap BEFORE any
    patch, the spec constant 7.0 never prices, and the patch keeps the gap."""

    import copy

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = _spx_quote_kwargs(symbol="NOT_A_SYMBOL", spread_points=7.0)
    kwargs = copy.deepcopy(kwargs)
    kwargs["config"]["broker_profile"] = {"server": "FTMO-Server3"}
    frozen = v4t._predecision_tick_for_cost(**kwargs)
    frozen_tick, frozen_meta = frozen
    assert frozen_meta["quote_source"] == "spread_model_source_gap"
    assert not frozen_tick
    repairs.reset_repair_stats()
    patch = repairs._make_spread_truth_patch(live=True)
    patch.apply()
    try:
        result = v4t._predecision_tick_for_cost(**kwargs)
    finally:
        patch.revert()
    assert result == frozen
    report = repairs.repair_report()["spread_input_truth"]
    assert report["applied"] == 0
    assert report["errors"] == {"kept:spread_model_source_gap": 1}


def test_spread_truth_control_is_byte_equal_and_computes_the_same_number() -> None:
    """Live and control are indistinguishable on the wave-21 native engine:
    the model already priced the row, so BOTH arms emit the native bytes,
    BOTH census the identical kept row, and NEITHER replaces anything."""

    import copy

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = _spx_quote_kwargs()
    kwargs = copy.deepcopy(kwargs)
    kwargs["config"]["broker_profile"] = {"server": "FTMO-Server3"}
    frozen = v4t._predecision_tick_for_cost(**kwargs)
    assert frozen[1]["quote_source"] == _SPREAD_SOURCE

    repairs.reset_repair_stats()
    live = repairs._make_spread_truth_patch(live=True)
    live.apply()
    try:
        live_result = v4t._predecision_tick_for_cost(**kwargs)
    finally:
        live.revert()
    live_report = repairs.repair_report()["spread_input_truth"]
    assert live_result == frozen
    assert live_report["applied"] == 0
    assert live_report["errors"] == {"kept:" + _SPREAD_SOURCE: 1}
    assert live_report["per_symbol"] == {}

    repairs.reset_repair_stats()
    control = repairs._make_spread_truth_patch(live=False)
    control.apply()
    try:
        result = v4t._predecision_tick_for_cost(**kwargs)
    finally:
        control.revert()
    assert result == frozen
    report = repairs.repair_report()["spread_input_truth_inert_control"]
    assert report["applied"] == 0
    assert report["errors"] == {"kept:" + _SPREAD_SOURCE: 1}
    assert report["per_symbol"] == {}


def test_spread_truth_extends_and_restores_the_component_source_authority() -> None:
    """Wave-21 made the model source NATIVE: the timewarp itself emits
    `spread_model_v1_hour_aware`, so the base authority table must already
    allow it (pre-wave-21 only the patch extended it). The patch must remain
    apply/revert-safe and must not disturb any other component's set."""

    import src.research_infra.train_engine.decision_semantics as ds

    before = ds._ALLOWED_COMPONENT_SOURCES
    assert _SPREAD_SOURCE in before["spread_r"]
    patch = repairs._make_spread_truth_patch(live=True)
    patch.apply()
    try:
        assert _SPREAD_SOURCE in ds._ALLOWED_COMPONENT_SOURCES["spread_r"]
        # Every other component's authority set is untouched.
        for field in ("expected_slippage_r", "swap_cost_r", "commission_r"):
            assert ds._ALLOWED_COMPONENT_SOURCES[field] == before[field]
    finally:
        patch.revert()
    assert ds._ALLOWED_COMPONENT_SOURCES is before


def test_spread_truth_live_and_control_refuse_to_stack_at_apply_time() -> None:
    live = repairs._make_spread_truth_patch(live=True)
    control = repairs._make_spread_truth_patch(live=False)
    live.apply()
    try:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            control.apply()
        assert "already installed" in str(excinfo.value)
    finally:
        live.revert()


def test_the_ruler_keeps_an_incomplete_flat_override_visibly() -> None:
    """The C4-A shape, after wave-21 retired the flat 0.12 authority fallback:
    an incomplete four-component packet now REFUSES with a nonnumeric total --
    'missing authority remains nonnumeric' -- instead of pricing the flat
    constant. The ruler censuses the refusal and never invents a term."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = _spx_packet_kwargs(with_swap=False)
    frozen = v4t.broker_calibrated_replay_cost_packet(**kwargs)
    assert frozen["status"] == "REFUSED"
    assert frozen["total_cost_r"] is None
    components = frozen["total_cost_components"]
    assert "authority_fallback_total_cost_r" not in components
    assert components["spread_r"] is None
    assert components["commission_r"] is None

    repairs.reset_repair_stats()
    patch = repairs._make_cost_ruler_patch(live=True)
    patch.apply()
    try:
        packet = v4t.broker_calibrated_replay_cost_packet(**kwargs)
    finally:
        patch.revert()
    assert packet["total_cost_r"] is None
    assert packet["cost_ruler_harmonize_status"] == (
        "identity_unevaluable_incomplete_components"
    )
    report = repairs.repair_report()["cost_ruler_harmonize"]
    assert report["errors"]["census:identity_unevaluable"] == 1
    assert report["applied"] == 0


def test_the_ruler_replaces_a_flat_override_with_a_complete_witnessed_sum(
    monkeypatch,
) -> None:
    """The enforcement guarantee: a flat-override total whose four components
    are complete AND witnessed is rebuilt as the sum and re-gated by the
    engine's own refusal check."""

    from src.research_infra.train_engine.decision_semantics import (
        TRUSTED_COMMISSION_REPAIR_SOURCE,
    )

    packet = {
        "status": "CHECKED",
        "symbol": "GER40",
        "total_cost_r": 0.12,
        "max_total_cost_r": 0.15,
        "max_spread_r": 0.10,
        "cost_limit_tolerance_r": 1e-6,
        "spread_r": 0.04,
        "total_cost_components": {
            "spread_r": 0.04,
            "expected_slippage_r": 0.02,
            "swap_cost_r": 0.005,
            "commission_r": 0.003,
            "authority_fallback_total_cost_r": 0.12,
        },
        "tick_cost": {"spread_r": 0.04, "source_status": "captured"},
        "quote_authority": {"quote_source": "historical_ftmo_predecision_tick"},
        "expected_slippage_r": 0.02,
        "expected_slippage_source": "trade_params",
        "swap_cost": {
            "cost_r": 0.005,
            "model_version": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
        },
        "commission_cost": {
            "cost_r": 0.003,
            "repair_source": TRUSTED_COMMISSION_REPAIR_SOURCE,
            "source_status": "captured",
            "included_in_total_cost_r": True,
        },
        "commission_r_broker_true_measured": 0.003,
        "refusal_reasons": ["authority_conservative_broker_default_no_broker_total_cost_r"],
    }
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.broker_calibrated_replay_cost_packet = lambda **kwargs: packet
    timewarp.broker_replay_default_total_cost_r = lambda config: 0.12
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_cost_ruler_patch(live=True)
    patch.apply()
    try:
        out = timewarp.broker_calibrated_replay_cost_packet(
            candidate={"symbol": "GER40"}, config={}
        )
    finally:
        patch.revert()
    assert out["total_cost_r"] == pytest.approx(0.068)
    assert "authority_fallback_total_cost_r" not in out["total_cost_components"]
    assert out["cost_ruler_harmonize_status"] == (
        "flat_override_replaced_with_component_sum"
    )
    assert out["cost_ruler_total_before_r"] == pytest.approx(0.12)
    assert out["cost_ruler_total_after_r"] == pytest.approx(0.068)
    assert out["legacy_emitter_fallback_replaced"] is True
    assert out["cost_component_state"] == "complete"
    # The re-gate is the engine's own check, recomputed on the honest total.
    assert out["status"] in {"PASSED", "REFUSED"}
    assert isinstance(out["refusal_reasons"], list)
    report = repairs.repair_report()["cost_ruler_harmonize"]
    assert report["applied"] == 1
    assert report["charged_r_mean"] == pytest.approx(0.068)
    assert report["baseline_r_mean"] == pytest.approx(0.12)


def test_the_ruler_never_touches_a_non_override_deviation(monkeypatch) -> None:
    """A total != sum with NO flat-override marker is a mechanism the wrapper
    has not identified: counted, stamped, left alone."""

    packet = {
        "status": "CHECKED",
        "symbol": "UKOIL_cash",
        "total_cost_r": 0.30,
        "total_cost_components": {
            "spread_r": 0.04,
            "expected_slippage_r": 0.02,
            "swap_cost_r": 0.005,
            "commission_r": 0.003,
        },
    }
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.broker_calibrated_replay_cost_packet = lambda **kwargs: packet
    timewarp.broker_replay_default_total_cost_r = lambda config: 0.12
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_cost_ruler_patch(live=True)
    patch.apply()
    try:
        out = timewarp.broker_calibrated_replay_cost_packet(
            candidate={"symbol": "UKOIL_cash"}, config={}
        )
    finally:
        patch.revert()
    assert out["total_cost_r"] == pytest.approx(0.30)
    assert out["cost_ruler_harmonize_status"] == "identity_deviates_unrepaired"
    assert out["cost_ruler_identity_delta_r"] == pytest.approx(0.232)
    report = repairs.repair_report()["cost_ruler_harmonize"]
    assert report["errors"]["census:identity_deviates"] == 1
    assert report["errors"]["deviates:UKOIL_cash"] == 1
    assert report["applied"] == 0


def test_the_ruler_control_censuses_but_returns_the_packet_unchanged() -> None:
    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = _spx_packet_kwargs(with_swap=False)
    frozen = v4t.broker_calibrated_replay_cost_packet(**kwargs)

    repairs.reset_repair_stats()
    control = repairs._make_cost_ruler_patch(live=False)
    control.apply()
    try:
        packet = v4t.broker_calibrated_replay_cost_packet(**kwargs)
    finally:
        control.revert()
    assert packet == frozen
    assert "cost_ruler_harmonize_status" not in packet
    report = repairs.repair_report()["cost_ruler_inert_control"]
    # Wave-21 retired the flat-override class: the census the control now
    # records for this incomplete packet is the nonnumeric refusal.
    assert report["errors"]["census:identity_unevaluable"] == 1


def test_the_ruler_live_and_control_refuse_to_stack_at_apply_time() -> None:
    import src.research_infra.v4_timewarp_simulated_live_research_loop  # noqa: F401

    live = repairs._make_cost_ruler_patch(live=True)
    control = repairs._make_cost_ruler_patch(live=False)
    live.apply()
    try:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            control.apply()
        assert "already installed" in str(excinfo.value)
    finally:
        live.revert()


def test_the_composed_cost_truth_stack_heals_the_flat_override_end_to_end() -> None:
    """The C4-A kill shot, on the wave-21 native engine: with broker identity
    the spread is truthed by the model, the composed stack rebuilds the total
    as the exact component sum, the ruler censuses identity_holds -- and the
    flat 0.12 authority fallback is gone from the packet entirely."""

    import copy

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    kwargs = _spx_packet_kwargs(with_swap=True)
    kwargs = copy.deepcopy(kwargs)
    kwargs["config"]["broker_profile"] = {"server": "FTMO-Server3"}
    frozen = v4t.broker_calibrated_replay_cost_packet(**kwargs)
    assert frozen["total_cost_r"] is not None

    repairs.reset_repair_stats()
    patches = {patch.patch_id: patch for patch in repairs.build_repairs()}
    order = repairs.resolve_repairs("cost_truth")
    applied = []
    try:
        for pid in order:
            patches[pid].apply()
            applied.append(pid)
        packet = v4t.broker_calibrated_replay_cost_packet(**kwargs)
    finally:
        for pid in reversed(applied):
            patches[pid].revert()

    components = packet["total_cost_components"]
    component_sum = sum(
        float(components[key])
        for key in ("spread_r", "expected_slippage_r", "swap_cost_r", "commission_r")
    )
    assert packet["total_cost_r"] == pytest.approx(component_sum, abs=1e-9)
    assert "authority_fallback_total_cost_r" not in components
    assert packet["cost_ruler_harmonize_status"] == "identity_holds"
    assert packet["quote_authority"]["quote_source"] == _SPREAD_SOURCE
    assert packet["spread_r"] < 0.05  # truthed, not the 0.3333 constant
    assert packet["swap_horizon_bars_used"] == 8.0
    # Swap resolves through the owner-signed broker-wall rollover semantics:
    # a 2-hour hold crosses zero broker midnights, so the charge is exactly 0.
    assert packet["swap_cost"]["swap_charge_basis"] == (
        "broker_wall_midnight_crossings"
    )
    assert packet["swap_cost"]["rollover_nights_charged"] == 0.0
    # Commission is repair-priced (0.0 witnessed), not broker-captured, so the
    # ruler's own sub-classification stays 'incomplete' while the numeric
    # identity holds -- the honest reading, not a defect.
    assert packet["cost_component_state"] == "incomplete"
    report = repairs.repair_report()
    # The native engine already model-priced the row; the spread patch keeps it.
    assert report["spread_input_truth"]["applied"] == 0
    assert report["spread_input_truth"]["errors"] == {"kept:" + _SPREAD_SOURCE: 1}
    assert report["cost_ruler_harmonize"]["errors"] == {"census:identity_holds": 1}

    # Full revert restores the frozen ruler byte-for-byte.
    assert v4t.broker_calibrated_replay_cost_packet(**kwargs) == frozen


def test_the_manifest_names_the_spread_artifact_and_the_expectation() -> None:
    manifest = repairs.repair_manifest()
    spread = manifest["spread_input_truth"]
    assert "SPREAD_MODEL_V1.json" in spread["artifact"]
    assert spread["account"] == "FTMO" and spread["band"] == "mid"
    assert "0.564 -> ~0.157" in spread["ex_ante_expectation"]
    assert "within-era" in spread["era_note"]
    assert "broker_profile_symbol_spec_spread" in spread["replaced_quote_sources"]
    assert "historical_ftmo_predecision_tick" in spread["kept_quote_sources"]
    ruler = manifest["cost_ruler_harmonize"]
    assert "73.5%" in ruler["finding"]
    assert "v4_timewarp:58929-58938" in ruler["mechanism"]
    assert "engine-file edit" in ruler["documented_remainder"]


def test_repair_stats_carry_the_baseline_channel() -> None:
    stats = repairs._RepairStats()
    stats.applied = 2
    stats.charged_r_sum = 0.4
    stats.baseline_r_sum = 1.0
    stats.per_symbol["X"] = {"n": 2, "sum_r": 0.4, "baseline_sum_r": 1.0}
    out = stats.as_dict()
    assert out["baseline_r_sum"] == 1.0
    assert out["baseline_r_mean"] == 0.5
    assert out["per_symbol"]["X"]["baseline_sum_r"] == 1.0
    # Rows created by repairs that never track a baseline stay readable.
    stats.per_symbol["Y"] = {"n": 1, "sum_r": 0.1}
    assert stats.as_dict()["per_symbol"]["Y"]["baseline_sum_r"] == 0.0


# ---------------------------------------------------------------------------
# R-BELIEF (FA Phase C spec section 3)
# ---------------------------------------------------------------------------

_DEBATE_CFG = {
    "gtos_vnext_runtime": {"probability_debate_team_engine_v4": {"enabled": True}}
}
_BELIEF_LIVE_IDS = (
    "belief_cost_single_charge",
    "belief_hash_term_removal",
    "belief_confidence_constant_retire",
    "belief_ev_walked_contract",
    "belief_fill_probability_deweight",
)


def _belief_candidate(family: str = "current_fvg_fill") -> dict:
    return {
        "candidate_id": "syn-belief-1",
        "symbol": "SPX500",
        "side": "LONG",
        "origin_family": family,
        "route_session": "ny",
        "risk_reward_ratio": 1.5,
        "source_window_complete": True,
        "entry_price": 5000.0,
        "stop_loss": 4990.0,
        "source_fields": {
            "atr14_atr50_ratio": 1.0,
            "lookback50_position": 0.8,
            "trend_state_20": "up",
        },
    }


def test_belief_repairs_are_registered_with_controls() -> None:
    ids = {patch.patch_id for patch in repairs.build_repairs()}
    pairs = dict(repairs.REPAIR_PAIRS)
    for live in _BELIEF_LIVE_IDS:
        control = pairs[live]
        assert live in ids and live in repairs.REPAIR_IDS
        assert control in ids and control in repairs.REPAIR_IDS
    for patch in repairs.build_repairs():
        if patch.patch_id.startswith("belief_"):
            assert patch.default_on is False


def test_belief_context_wire_only_form_is_refused_with_the_b5_reason() -> None:
    """The atomicity rule (spec 9.2): the naive one-key wire double-charges."""

    with pytest.raises(repairs.RepairUnavailable) as excinfo:
        repairs.validate_repair_ids(["belief_cost_context_wire_only"])
    message = str(excinfo.value)
    assert "atomicity" in message
    assert "42.8% -> 57.8%" in message
    assert "belief_cost_single_charge" in message


def test_belief_live_repairs_refuse_their_own_controls() -> None:
    pairs = dict(repairs.REPAIR_PAIRS)
    for live in _BELIEF_LIVE_IDS:
        with pytest.raises(repairs.RepairUnavailable) as excinfo:
            repairs.validate_repair_ids([live, pairs[live]])
        assert "cannot compose" in str(excinfo.value)


def test_belief_bundle_orders_census_inner_and_walked_outer() -> None:
    """Both wrap evaluate_candidate_v4; the charge census must classify the
    debate chain BEFORE the walked-contract repricer overwrites the row."""

    bundle = repairs.resolve_repairs("belief")
    assert bundle == list(repairs.BELIEF_BUNDLE)
    assert bundle.index("belief_cost_single_charge") < bundle.index(
        "belief_ev_walked_contract"
    )
    repairs.validate_repair_ids(bundle)


def test_belief_honesty_is_arm_two_as_one_flag() -> None:
    resolved = repairs.resolve_repairs("belief_honesty")
    assert resolved == repairs.resolve_repairs("cost_truth") + list(
        repairs.BELIEF_BUNDLE
    )
    repairs.validate_repair_ids(resolved)
    repairs.validate_repair_ids(resolved + ["neutral_seed_replicate_r1"])


def test_belief_charge_census_classifier_grid() -> None:
    """Synthetic rows through the census arithmetic: exactly-once passes,
    the double charge and the uncharged row are named, zero-cost rows are
    their own bucket (the three classes coincide at c = 0)."""

    classify = repairs.belief_charge_census_classify
    ev, c = -0.2552, 0.9
    assert classify(ev_charged=ev, debate_cost_r=c, expected_net_r=ev) == "charged_1x"
    assert (
        classify(ev_charged=ev, debate_cost_r=c, expected_net_r=ev - c)
        == "charged_2x"
    )
    assert (
        classify(ev_charged=ev, debate_cost_r=c, expected_net_r=ev + c)
        == "charged_0x"
    )
    assert (
        classify(ev_charged=0.7, debate_cost_r=0.0, expected_net_r=0.7)
        == "zero_cost_row"
    )
    assert (
        classify(ev_charged=None, debate_cost_r=c, expected_net_r=ev)
        == "unclassifiable_missing_fields"
    )
    assert (
        classify(ev_charged=ev, debate_cost_r=c, expected_net_r=ev - 0.5 * c)
        == "unclassifiable_off_grid"
    )


def test_belief_single_charge_holds_exactly_one_charge_through_the_real_chain() -> None:
    """The composed-state identity on the REAL engine chain: context wired
    (cost_r + candidate_direction), the debate charges once (p cost-informed,
    EV able to go negative, the veto able to fire), the probability_thesis
    add-back restores the pre-cost EV, and the frozen downstream subtraction
    (the :67450 arithmetic) nets to the charged EV -- charged_1x."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    cand = _belief_candidate()
    cost = 0.9
    ctx_frozen = v4t.build_probability_context(
        cand, "2026-01-15T14:30:00+00:00", None, cost_r=cost
    )
    assert "cost_r" not in ctx_frozen and "candidate_direction" not in ctx_frozen
    frozen = repairs._side_thesis(
        v4t.evaluate_probability_debate_team_v4(ctx_frozen, _DEBATE_CFG).to_record(),
        "long",
    )

    repairs.reset_repair_stats()
    patch = repairs._make_belief_cost_patch(live=True)
    patch.apply()
    try:
        context = v4t.build_probability_context(
            cand, "2026-01-15T14:30:00+00:00", None, cost_r=cost
        )
        assert context["cost_r"] == cost
        assert context["candidate_direction"] == "LONG"
        record = v4t.evaluate_probability_debate_team_v4(
            context, _DEBATE_CFG
        ).to_record()
        charged = repairs._side_thesis(record, "long")
        restored = v4t.probability_thesis(record, "long")
        expected_net = round(restored["ev_r"] - cost, 12)  # the :67450 line
        verdict = repairs.belief_charge_census_classify(
            ev_charged=charged["ev_r"],
            debate_cost_r=charged["cost_r"],
            expected_net_r=expected_net,
        )
        assert verdict == "charged_1x"
        assert charged["cost_r"] == pytest.approx(cost)
        assert expected_net == pytest.approx(charged["ev_r"], abs=1e-9)
        # The p-channel went live: cost-informed p moved below the frozen p.
        assert charged["probability"] < frozen["probability"]
        # The record keeps the charged truth; the copy carries the restatement.
        assert restored["debate_charged_ev_r"] == pytest.approx(charged["ev_r"])
        assert restored["ev_precost_restored_for_single_charge"] is True
        # The frozen counterfactual is stamped per row.
        block = record["debate_controls"]["belief_cost_single_charge"]
        assert block["pre_repair_probability"] == pytest.approx(
            frozen["probability"]
        )
        assert block["pre_repair_ev_r"] == pytest.approx(frozen["ev_r"])
        # The jury can finally express a loser inside the debate, and the EV
        # veto fires on it (min_trade_ev_r 0.0).
        high = repairs._side_thesis(
            v4t.evaluate_probability_debate_team_v4(
                v4t.build_probability_context(
                    cand, "2026-01-15T14:30:00+00:00", None, cost_r=3.5
                ),
                _DEBATE_CFG,
            ).to_record(),
            "long",
        )
        assert high["ev_r"] <= 0
        assert "EV_below_trade_threshold" in high["vetoes"]
        report = repairs.repair_report()["belief_cost_single_charge"]
        assert report["errors"]["veto_ev_below_trade_threshold_fired"] >= 1
        assert report["errors"]["counterfactual_runs"] >= 2
    finally:
        patch.revert()
    # Revert restores the frozen context builder byte-for-byte.
    assert (
        v4t.build_probability_context(
            cand, "2026-01-15T14:30:00+00:00", None, cost_r=cost
        )
        == ctx_frozen
    )


def test_belief_single_charge_rebaselines_the_p_gates_and_reverts() -> None:
    """Spec 3.1 item 4: 0.58 / 0.70 / 0.85 / 0.80 move DOWN by the declared
    median-cost logit (0.6166 * 0.7), derived not typed; revert is exact."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    assert repairs.P_GATE_LOGIT_SHIFT == pytest.approx(0.6166 * 0.7)
    patch = repairs._make_belief_cost_patch(live=True)
    patch.apply()
    try:
        resolved = v4t._scheduler_config_uncached({"gtos_vnext_runtime": {}})
        assert resolved["dynamic_budget_package_min_probability"] == pytest.approx(
            repairs.rebaselined_p_gate(0.58)
        )
        assert resolved[
            "selector_reduce_risk_numeric_disagreement_min_probability"
        ] == pytest.approx(repairs.rebaselined_p_gate(0.85))
        assert resolved[
            "selector_reduce_risk_new_entry_min_probability"
        ] == pytest.approx(repairs.rebaselined_p_gate(0.80))
        assert v4t.SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY == pytest.approx(
            repairs.rebaselined_p_gate(0.70)
        )
        # The expected_net floors are NOT touched: they were calibrated
        # against a single-charged quantity the add-back preserves.
        assert v4t.SOURCE_BOUND_ROUTER_REFUSAL_MIN_EXPECTED_NET_R == 0.55
        assert v4t.RUNTIME_ROUTER_REFUSAL_MIN_EXPECTED_NET_R == 0.85
    finally:
        patch.revert()
    assert v4t.SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY == 0.70
    resolved = v4t._scheduler_config_uncached({"gtos_vnext_runtime": {}})
    assert resolved["dynamic_budget_package_min_probability"] == 0.58


def test_belief_cost_control_is_outcome_identical_to_frozen() -> None:
    """The control wires cost_r = 0.0, which the debate's own reader
    (_positive_float(... or ..., 0.0)) cannot distinguish from the frozen
    absent key; candidate_direction keeps absent-semantics; p-gates keep
    their original values. Outcome identity attributes every live difference
    to the wired number."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    cand = _belief_candidate()
    frozen = repairs._side_thesis(
        v4t.evaluate_probability_debate_team_v4(
            v4t.build_probability_context(
                cand, "2026-01-15T14:30:00+00:00", None, cost_r=0.9
            ),
            _DEBATE_CFG,
        ).to_record(),
        "long",
    )
    patch = repairs._make_belief_cost_patch(live=False)
    patch.apply()
    try:
        context = v4t.build_probability_context(
            cand, "2026-01-15T14:30:00+00:00", None, cost_r=0.9
        )
        assert context["cost_r"] == 0.0
        assert "candidate_direction" not in context
        control = repairs._side_thesis(
            v4t.evaluate_probability_debate_team_v4(
                context, _DEBATE_CFG
            ).to_record(),
            "long",
        )
        assert control["probability"] == pytest.approx(
            frozen["probability"], abs=1e-12
        )
        assert control["ev_r"] == pytest.approx(frozen["ev_r"], abs=1e-12)
        assert control["vetoes"] == frozen["vetoes"]
        resolved = v4t._scheduler_config_uncached({"gtos_vnext_runtime": {}})
        assert resolved["dynamic_budget_package_min_probability"] == 0.58
        assert v4t.SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY == 0.70
    finally:
        patch.revert()


def test_hash_term_removal_makes_family_name_probability_inert() -> None:
    """B4 Q1's live probe, inverted: two identical candidates differing ONLY
    in origin_family must carry identical follow_strength, identical debate
    probability, and identical rank-key signal after the repair; the
    candidate_id tail of the rank key is the declared content-free tiebreak."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    frozen_a = v4t.candidate_feature_signal(_belief_candidate("current_fvg_fill"), None)
    frozen_b = v4t.candidate_feature_signal(
        _belief_candidate("liquidity_sweep_reclaim"), None
    )
    assert frozen_a["follow_strength"] != frozen_b["follow_strength"]

    repairs.reset_repair_stats()
    patch = repairs._make_hash_removal_patch(live=True)
    patch.apply()
    try:
        signal_a = v4t.candidate_feature_signal(
            _belief_candidate("current_fvg_fill"), None
        )
        signal_b = v4t.candidate_feature_signal(
            _belief_candidate("liquidity_sweep_reclaim"), None
        )
        assert signal_a["follow_strength"] == signal_b["follow_strength"]
        assert signal_a["family_hash_signal"] == 0.0
        assert signal_a["family_hash_term_removed"] is True
        assert signal_a["pre_repair_follow_strength"] == frozen_a["follow_strength"]
        assert signal_a["pre_repair_family_hash_signal"] == pytest.approx(
            frozen_a["family_hash_signal"]
        )
        thesis_a = repairs._side_thesis(
            v4t.evaluate_probability_debate_team_v4(
                v4t.build_probability_context(
                    _belief_candidate("current_fvg_fill"), "t", None, cost_r=0.1
                ),
                _DEBATE_CFG,
            ).to_record(),
            "long",
        )
        thesis_b = repairs._side_thesis(
            v4t.evaluate_probability_debate_team_v4(
                v4t.build_probability_context(
                    _belief_candidate("liquidity_sweep_reclaim"), "t", None, cost_r=0.1
                ),
                _DEBATE_CFG,
            ).to_record(),
            "long",
        )
        assert thesis_a["probability"] == thesis_b["probability"]
        key_a = v4t.candidate_generation_rank_key(
            _belief_candidate("current_fvg_fill"), None
        )
        key_b = v4t.candidate_generation_rank_key(
            _belief_candidate("liquidity_sweep_reclaim"), None
        )
        assert key_a[:4] == key_b[:4]
        assert key_a[4] == "syn-belief-1"  # content-free deterministic tail
        report = repairs.repair_report()["belief_hash_term_removal"]
        assert report["applied"] >= 2
    finally:
        patch.revert()
    assert (
        v4t.candidate_feature_signal(_belief_candidate("current_fvg_fill"), None)
        == frozen_a
    )


def test_hash_removal_control_computes_and_freezes() -> None:
    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    frozen = v4t.candidate_feature_signal(_belief_candidate(), None)
    patch = repairs._make_hash_removal_patch(live=False)
    patch.apply()
    try:
        control = v4t.candidate_feature_signal(_belief_candidate(), None)
        assert control["follow_strength"] == frozen["follow_strength"]
        assert control["family_hash_signal"] == frozen["family_hash_signal"]
        assert control["family_hash_term_removed"] is False
        assert "family_hash_control_would_apply" in control
    finally:
        patch.revert()


def test_hash_removal_keeps_frozen_on_reconstruction_drift(monkeypatch) -> None:
    """If the engine's follow_strength formula ever changes under the wrapper,
    the subtraction would be a guess -- the row keeps the frozen value and the
    drift is counted, never silently applied."""

    drifted = {
        "extreme_strength": 0.6,
        "trend_follow": 1.0,
        "volatility_balance": 1.0,
        "rr_signal": 0.5,
        "family_hash_signal": 0.5,
        "mso_signal": {"follow_ratio": 0.0},
        "follow_strength": 0.999,  # does NOT match the mirrored formula
    }
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.candidate_feature_signal = lambda candidate, mso: dict(drifted)
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_hash_removal_patch(live=True)
    patch.apply()
    try:
        signal = timewarp.candidate_feature_signal({}, None)
    finally:
        patch.revert()
    assert signal["follow_strength"] == 0.999
    assert "family_hash_term_removed" not in signal
    report = repairs.repair_report()["belief_hash_term_removal"]
    assert report["errors"]["reconstruction_drift_kept_frozen"] == 1
    assert report["applied"] == 0


def test_confidence_retire_is_a_uniform_shift_and_rank_invariant() -> None:
    """Spec 3.3: a constant x weight is rank-inert -- PROVEN per row: every
    component equals 0.55*0.20 = 0.11, so removal shifts every score by the
    same amount and ordering is preserved; a nonconstant component is a
    counted FINDING, not a silent repair."""

    import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc

    rows = [
        {"ev_component": 0.40, "confidence_component": 0.11, "cost_penalty": -0.30},
        {"ev_component": 0.90, "confidence_component": 0.11, "cost_penalty": -0.10},
    ]
    frozen = [alloc._sum_scheduler_score_components(dict(row)) for row in rows]
    repairs.reset_repair_stats()
    patch = repairs._make_confidence_retire_patch(live=True)
    patch.apply()
    try:
        stamped = [dict(row) for row in rows]
        live = [alloc._sum_scheduler_score_components(row) for row in stamped]
    finally:
        patch.revert()
    for before, after, row in zip(frozen, live, stamped):
        assert after == pytest.approx(before - 0.11, abs=1e-12)
        assert row["pre_repair_confidence_component"] == 0.11
        assert row["confidence_component"] == 0.0
        assert row["confidence_component_retired"] is True
        assert row["score_without_confidence_component"] == pytest.approx(
            row["score_with_confidence_component"] - 0.11, abs=1e-12
        )
    # Uniform shift -> ordering preserved (rank changes must be 0).
    assert (frozen[0] < frozen[1]) == (live[0] < live[1])
    report = repairs.repair_report()["belief_confidence_constant_retire"]
    assert report["applied"] == 2
    assert "uniform_shift_violation_nonconstant_confidence" not in report["errors"]

    # A nonconstant confidence is a finding, counted and reported.
    repairs.reset_repair_stats()
    patch = repairs._make_confidence_retire_patch(live=True)
    patch.apply()
    try:
        alloc._sum_scheduler_score_components(
            {"ev_component": 0.1, "confidence_component": 0.13}
        )
    finally:
        patch.revert()
    report = repairs.repair_report()["belief_confidence_constant_retire"]
    assert report["errors"]["uniform_shift_violation_nonconstant_confidence"] == 1
    assert alloc._sum_scheduler_score_components(
        {"ev_component": 0.1, "confidence_component": 0.13}
    ) == pytest.approx(0.23)


def test_confidence_control_returns_original_total() -> None:
    """Control design per spec 3.3: keep the term, weight-0.0 counterfactual
    computed and stamped, ORIGINAL total returned -- proving removal equals
    zero-weighting while staying outcome-identical to the frozen engine."""

    import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc

    row = {"ev_component": 0.40, "confidence_component": 0.11}
    frozen = alloc._sum_scheduler_score_components(dict(row))
    patch = repairs._make_confidence_retire_patch(live=False)
    patch.apply()
    try:
        total = alloc._sum_scheduler_score_components(row)
    finally:
        patch.revert()
    assert total == pytest.approx(frozen)
    assert row["confidence_component"] == 0.11  # kept
    assert row["confidence_component_retired"] is False
    assert row["score_without_confidence_component"] == pytest.approx(frozen - 0.11)


def test_fill_deweight_drops_both_additive_terms() -> None:
    """Spec 3.5: the additive fill terms leave both scoring functions --
    the legacy fill_probability_component and _candidate_edge_score's
    weighted term; the multiplier surfaces and the three template-vs-
    threshold gates stay frozen (P1-blocked, labeled not modeled)."""

    import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc

    row = {"ev_component": 0.40, "fill_probability_component": 0.092}
    frozen_sum = alloc._sum_scheduler_score_components(dict(row))
    frozen_edge = alloc._candidate_edge_score(
        ev_r=1.0,
        probability=0.7,
        cost_total=0.2,
        fill_probability=0.9,
        source_completeness=0.9,
        fill_probability_weight=0.10,
    )
    repairs.reset_repair_stats()
    patch = repairs._make_fill_deweight_patch(live=True)
    patch.apply()
    try:
        live_sum = alloc._sum_scheduler_score_components(row)
        live_edge = alloc._candidate_edge_score(
            ev_r=1.0,
            probability=0.7,
            cost_total=0.2,
            fill_probability=0.9,
            source_completeness=0.9,
            fill_probability_weight=0.10,
        )
    finally:
        patch.revert()
    assert live_sum == pytest.approx(frozen_sum - 0.092, abs=1e-12)
    assert row["fill_probability_component"] == 0.0
    assert row["pre_repair_fill_probability_component"] == 0.092
    assert row["fill_probability_component_deweighted"] is True
    assert frozen_edge - live_edge == pytest.approx(0.9 * 0.10, abs=1e-12)
    report = repairs.repair_report()["belief_fill_probability_deweight"]
    assert report["applied"] == 1
    assert report["errors"]["edge_score_calls"] == 1
    # Revert restores both symbols.
    assert alloc._sum_scheduler_score_components(
        {"fill_probability_component": 0.092}
    ) == pytest.approx(0.092)


def test_fill_deweight_control_passes_original_values_through() -> None:
    import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc

    row = {"ev_component": 0.40, "fill_probability_component": 0.092}
    frozen_sum = alloc._sum_scheduler_score_components(dict(row))
    patch = repairs._make_fill_deweight_patch(live=False)
    patch.apply()
    try:
        control_sum = alloc._sum_scheduler_score_components(row)
        control_edge = alloc._candidate_edge_score(
            ev_r=1.0,
            probability=0.7,
            cost_total=0.2,
            fill_probability=0.9,
            source_completeness=0.9,
            fill_probability_weight=0.10,
        )
    finally:
        patch.revert()
    assert control_sum == pytest.approx(frozen_sum)
    assert row["fill_probability_component"] == 0.092  # kept
    assert row["fill_probability_component_deweighted"] is False
    assert control_edge == pytest.approx(
        alloc._candidate_edge_score(
            ev_r=1.0,
            probability=0.7,
            cost_total=0.2,
            fill_probability=0.9,
            source_completeness=0.9,
            fill_probability_weight=0.10,
        )
    )


def _walked_stub_result(**_kwargs) -> dict:
    return {
        "candidate_after_geometry": {
            "symbol": "SPX500",
            "side": "LONG",
            "origin_family": "current_fvg_fill",
            "route_session": "ny",
            "risk_reward_ratio": 2.0,  # the post-rewrite walked contract
        },
        "cost_r": 0.07,
        "candidate_probability": 0.8353,
        "probability": 0.8353,
        "candidate_ev_r": 0.9622,
        "ev_r": 0.9622,
        "expectancy_r": 0.9622,
        "candidate_expected_net_r": 0.8922,
        "expected_net_r": 0.8922,
        "probability_packet": {"theses": []},
    }


def test_ev_walked_contract_prices_negative_and_stamps(monkeypatch) -> None:
    """The stand-down repair: the engine's stamped p 0.8353 / EV +0.96 become
    the January cell's honest p-hat ~0.538 and a NEGATIVE walked-contract EV,
    with p* published and every moved field stamped pre_repair_*. The
    jury-cannot-express-a-loser property dies here, counted."""

    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.evaluate_candidate_v4 = _walked_stub_result
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_ev_walked_patch(live=True)
    patch.apply()
    try:
        row = timewarp.evaluate_candidate_v4()
    finally:
        patch.revert()
    block = row["belief_walked_contract"]
    assert row["belief_walked_contract_status"] == "applied"
    assert block["cell_id"] == "current_fvg_fill|C1|ny"
    assert block["granularity"] == "family_band_session"
    assert block["n"] >= 30
    # BELIEF-RECAL's own cell: p-hat 0.5391 on n=230, shrunk toward the pool
    # gross rate 0.347 with prior mass 1.
    assert block["p_hat_shrunk"] == pytest.approx(0.5383, abs=1e-3)
    assert block["ev_walked_r"] < 0
    assert block["p_star_required"] == pytest.approx(0.6965, abs=1e-3)
    assert block["walked_contract_rr"] == 2.0
    assert row["candidate_ev_r"] == row["expected_net_r"] == block["ev_walked_r"]
    assert row["expectancy_r"] == block["ev_walked_r"]
    assert row["candidate_probability"] == block["p_hat_shrunk"]
    assert row["belief_ev_negative"] is True
    assert row["pre_repair_candidate_ev_r"] == 0.9622
    assert row["pre_repair_expected_net_r"] == 0.8922
    assert row["pre_repair_candidate_probability"] == 0.8353
    report = repairs.repair_report()["belief_ev_walked_contract"]
    assert report["applied"] == 1
    assert report["errors"]["ev_negative_rows"] == 1


def test_ev_walked_control_observes_only(monkeypatch) -> None:
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.evaluate_candidate_v4 = _walked_stub_result
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    patch = repairs._make_ev_walked_patch(live=False)
    patch.apply()
    try:
        row = timewarp.evaluate_candidate_v4()
    finally:
        patch.revert()
    assert row["candidate_ev_r"] == 0.9622 and row["expected_net_r"] == 0.8922
    assert row["candidate_probability"] == 0.8353
    assert row["belief_walked_contract_status"] == "control_observed_only"
    observed = row["belief_walked_contract_observability"]
    assert observed["ev_walked_r"] < 0 and observed["p_star_required"] is not None
    assert "pre_repair_candidate_ev_r" not in row


def test_ev_walked_unpriced_row_keeps_frozen_and_counts(monkeypatch) -> None:
    timewarp = types.ModuleType(repairs.TIMEWARP)
    timewarp.evaluate_candidate_v4 = lambda **kwargs: {
        "cost_r": None,
        "candidate_after_geometry": {},
        "candidate_ev_r": 0.5,
    }
    monkeypatch.setitem(sys.modules, repairs.TIMEWARP, timewarp)

    repairs.reset_repair_stats()
    patch = repairs._make_ev_walked_patch(live=True)
    patch.apply()
    try:
        row = timewarp.evaluate_candidate_v4()
    finally:
        patch.revert()
    assert row["candidate_ev_r"] == 0.5
    assert row["belief_walked_contract_status"] == (
        "unpriced_missing_family_or_cost_frozen_values_kept"
    )
    report = repairs.repair_report()["belief_ev_walked_contract"]
    assert report["errors"]["cell_unpriced_missing_family_or_cost"] == 1
    assert report["applied"] == 0


def test_ev_walked_cell_table_is_sha_pinned(monkeypatch, tmp_path) -> None:
    """An unverified cell table is refused at apply time, by hash."""

    tampered = tmp_path / "BELIEF_RECAL.json"
    tampered.write_text(json.dumps({"cells": []}))
    monkeypatch.setattr(repairs, "BELIEF_CELL_TABLE", tampered)
    table = repairs._BeliefCellTable()
    with pytest.raises(repairs.RepairUnavailable) as excinfo:
        table.load()
    assert "refusing to price beliefs from an unverified table" in str(excinfo.value)


def test_belief_cost_band_thresholds_match_the_declaration() -> None:
    """BELIEF-RECAL section 1.1's fixed absolute thresholds, byte-identical
    across windows: C1 < 0.10 <= C2 < 0.30 <= C3 < 1.00 <= C4."""

    assert repairs.belief_cost_band(0.05) == "C1"
    assert repairs.belief_cost_band(0.10) == "C2"
    assert repairs.belief_cost_band(0.2999) == "C2"
    assert repairs.belief_cost_band(0.30) == "C3"
    assert repairs.belief_cost_band(0.9999) == "C3"
    assert repairs.belief_cost_band(1.00) == "C4"
    assert repairs.belief_cost_band(12.87) == "C4"


def test_belief_bundle_rebind_targets_are_disjoint_from_cost_truth() -> None:
    """Composition claim, measured not asserted: installing the whole belief
    bundle leaves every cost-truth rebind target untouched (and vice versa the
    cost stack never touches the belief symbols -- disjoint by construction)."""

    import src.research_infra.v4_timewarp_simulated_live_research_loop as v4t

    cost_symbols = (
        "broker_calibrated_replay_cost_packet",
        "build_pretrade_cost_packet",
        "_predecision_tick_for_cost",
    )
    frozen = {name: getattr(v4t, name) for name in cost_symbols}
    patches = {patch.patch_id: patch for patch in repairs.build_repairs()}
    applied = []
    try:
        for pid in repairs.resolve_repairs("belief"):
            patches[pid].apply()
            applied.append(pid)
        for name in cost_symbols:
            assert getattr(v4t, name) is frozen[name]
    finally:
        for pid in reversed(applied):
            patches[pid].revert()
    # And the belief symbols are restored exactly after revert.
    assert not getattr(v4t.evaluate_candidate_v4, "_gtos_belief_ev_walked_wrapper", False)
    assert not getattr(
        v4t.build_probability_context, "_gtos_belief_context_wire_wrapper", False
    )


def test_belief_manifest_names_the_charge_point_and_the_stand_down() -> None:
    manifest = repairs.repair_manifest()
    bundle = manifest["belief_bundle"]
    assert bundle["ids"] == list(repairs.BELIEF_BUNDLE)
    assert "debate_live_style" in bundle["charge_point"]
    assert bundle["p_gate_rebaseline"]["logit_shift"] == pytest.approx(0.6166 * 0.7)
    assert bundle["cell_table"]["sha256"] == repairs.BELIEF_CELL_TABLE_SHA256
    assert "STAND DOWN" in bundle["expected_direction"]
    assert "belief_cost_context_wire_only" in manifest["refused_repair_forms"]

"""Session FE's default-off, as-of-safe condition telemetry contract."""

from __future__ import annotations

import copy
import json
import math
import types

from src.components.broader_origin_generators import PREDECISION_FEATURE_KEYS
from src.research_infra.learned_edge_dataset_builder import feature_guard_violations
from src.research_infra.train_engine import cuts


def _complete_block() -> dict[str, object]:
    return {
        key: ("flat" if key == "trend_state_m15" else index / 10.0)
        for index, key in enumerate(cuts.CONDITION_FEATURE_KEYS)
    }


def test_condition_transport_is_exactly_the_existing_asof_safe_feature_contract() -> None:
    assert cuts.CONDITION_FEATURE_KEYS == PREDECISION_FEATURE_KEYS
    learned_names = {f"f_pd_{name}": None for name in cuts.CONDITION_FEATURE_KEYS}
    assert feature_guard_violations(learned_names) == []


def test_condition_projection_copies_a_complete_scalar_block_without_mutation() -> None:
    block = _complete_block()
    row = {"candidate_id": "candidate-1", "predecision_features": block}
    before = copy.deepcopy(row)

    projected = cuts.condition_feature_ledger_fields(row)

    assert row == before
    assert projected["predecision_features"] == block
    assert projected["predecision_features"] is not block
    assert projected["condition_feature_projection_status"] == "complete"
    assert projected["condition_feature_projection_present_count"] == len(block)
    assert projected["condition_feature_projection_missing_count"] == 0
    assert projected["condition_feature_projection_unknown_key_count"] == 0
    assert projected["condition_feature_projection_invalid_value_count"] == 0


def test_condition_projection_drops_unknown_nested_and_nonfinite_values() -> None:
    block = _complete_block()
    block["trigger_bar_range_atr"] = {"future": 9.0}
    block["trigger_bar_body_atr"] = math.nan
    block["opportunity_net_proxy_r"] = 99.0

    projected = cuts.condition_feature_ledger_fields(
        {"predecision_features": block}
    )
    output = projected["predecision_features"]

    assert set(output) == set(cuts.CONDITION_FEATURE_KEYS)
    assert "opportunity_net_proxy_r" not in output
    assert output["trigger_bar_range_atr"] is None
    assert output["trigger_bar_body_atr"] is None
    assert projected["condition_feature_projection_status"] == "invalid_values_dropped"
    assert projected["condition_feature_projection_unknown_key_count"] == 1
    assert projected["condition_feature_projection_invalid_value_count"] == 2
    assert projected["condition_feature_projection_missing_count"] == 2


def test_condition_projection_never_raises_for_missing_or_malformed_input() -> None:
    missing = cuts.condition_feature_ledger_fields({})
    malformed = cuts.condition_feature_ledger_fields(
        {"predecision_features": ["not", "a", "mapping"]}
    )

    assert "predecision_features" not in missing
    assert missing["condition_feature_projection_status"] == "missing"
    assert missing["condition_feature_projection_missing_count"] == len(
        cuts.CONDITION_FEATURE_KEYS
    )
    assert "predecision_features" not in malformed
    assert malformed["condition_feature_projection_status"] == "malformed_not_mapping"
    assert malformed["condition_feature_projection_invalid_value_count"] == 1


def test_condition_patch_is_registered_but_absent_from_every_default_set() -> None:
    patch = cuts.make_condition_feature_propagation_patch()
    installer = cuts.build_installer()

    assert patch.patch_id == "condition_feature_propagation"
    assert patch.default_on is False
    assert patch.sealed_compatible is False
    assert patch.patch_id in installer.registered
    assert patch.patch_id not in cuts.TRAIN_DEFAULT_PATCHES
    assert patch.patch_id not in cuts.TRAIN_SAFE_SET_PATCHES
    assert cuts.resolve_patches("safe+conditions") == list(
        cuts.TRAIN_CONDITION_FEATURE_PATCHES
    )

    installer.install(cuts.resolve_patches("none"))
    assert patch.patch_id not in installer.manifest()["applied"]


def test_condition_patch_adds_only_telemetry_and_reverts_exactly(monkeypatch) -> None:
    calls: list[tuple[object, object, object]] = []

    def original(row, packets=None, *, decision_time_utc=None):
        calls.append((row, packets, decision_time_utc))
        return {
            "candidate_id": row.get("candidate_id"),
            "opportunity_net_proxy_r": row.get("opportunity_net_proxy_r"),
            "commission_r": row.get("commission_r"),
        }

    module = types.SimpleNamespace(ledger_namespace_alias_fields=original)
    monkeypatch.setattr(cuts.accel, "_module", lambda _name: module)
    row = {
        "candidate_id": "candidate-1",
        "opportunity_net_proxy_r": -0.25,
        "commission_r": 0.1,
        "predecision_features": _complete_block(),
    }
    before = copy.deepcopy(row)
    packets = {"selector_packet": {"selected": False}}
    patch = cuts.make_condition_feature_propagation_patch()

    patch.apply()
    try:
        assert module.ledger_namespace_alias_fields is not original
        result = module.ledger_namespace_alias_fields(
            row,
            packets,
            decision_time_utc="2026-01-01T00:00:00+00:00",
        )
    finally:
        patch.revert()

    assert module.ledger_namespace_alias_fields is original
    assert row == before
    assert calls == [(row, packets, "2026-01-01T00:00:00+00:00")]
    assert result["candidate_id"] == before["candidate_id"]
    assert result["opportunity_net_proxy_r"] == before["opportunity_net_proxy_r"]
    assert result["commission_r"] == before["commission_r"]
    assert result["predecision_features"] == before["predecision_features"]
    assert result["condition_feature_projection_status"] == "complete"


def test_missed_pool_projection_preserves_only_the_bounded_condition_surface() -> None:
    row = {
        "candidate_id": "candidate-1",
        "predecision_features": _complete_block(),
        "condition_feature_projection_schema": (
            cuts.CONDITION_FEATURE_PROJECTION_SCHEMA
        ),
        "condition_feature_projection_status": "complete",
        "condition_feature_projection_present_count": len(
            cuts.CONDITION_FEATURE_KEYS
        ),
        "condition_feature_projection_missing_count": 0,
        "condition_feature_projection_unknown_key_count": 0,
        "condition_feature_projection_invalid_value_count": 0,
        "unrelated_nested_envelope": {"large": [1, 2, 3]},
    }

    projected = cuts.project_missed_pool_row(row)

    assert projected["predecision_features"] == row["predecision_features"]
    assert cuts.CONDITION_FEATURE_LEDGER_FIELDS <= set(projected)
    assert "unrelated_nested_envelope" not in projected
    assert projected["train_lane_missed_projection"] == (
        cuts.MISSED_POOL_PROJECTION_STAMP
    )


# ---------------------------------------------------------------------------
# WALK-F1 (Session FA Phase C): the instrument must reach the MISSED pool
# ---------------------------------------------------------------------------


def _stub_modules(monkeypatch):
    """Name-aware accel._module stubs for the timewarp helper AND the
    attempt5 transport compactor the WALK-F1 fix rebinds."""

    def alias_original(row, packets=None, *, decision_time_utc=None):
        return {"candidate_id": row.get("candidate_id")}

    missed_keep = ("candidate_id", "opportunity_net_proxy_r")

    def compact_original(rows):
        # Faithful shape of attempt5's strict keep_fields allowlist: this is
        # exactly the drop WALK-F1 measured (0/8,448 missed rows carried the
        # block while TRADE and ORDER rows did).
        return [
            {key: row.get(key) for key in missed_keep if key in row}
            for row in rows
        ]

    timewarp = types.SimpleNamespace(
        ledger_namespace_alias_fields=alias_original
    )
    runner = types.SimpleNamespace(
        compact_missed_opportunity_rows=compact_original
    )
    modules = {
        "src.research_infra.v4_timewarp_simulated_live_research_loop": timewarp,
        (
            "src.research_infra."
            "replay_acceleration_attempt5_typed_sparse_runner"
        ): runner,
    }
    monkeypatch.setattr(cuts.accel, "_module", lambda name: modules.get(name))
    return timewarp, runner, alias_original, compact_original


def test_condition_patch_carries_fields_through_the_missed_transport_compactor(
    monkeypatch,
) -> None:
    timewarp, runner, alias_original, compact_original = _stub_modules(
        monkeypatch
    )
    patch = cuts.make_condition_feature_propagation_patch()

    patch.apply()
    try:
        assert cuts._CONDITION_FEATURE_PROPAGATION_ACTIVE == 1
        assert runner.compact_missed_opportunity_rows is not compact_original
        # The assembly-time wrapper output rides on the pre-compaction row.
        assembled = {
            "candidate_id": "candidate-1",
            "opportunity_net_proxy_r": -0.25,
            **timewarp.ledger_namespace_alias_fields(
                {
                    "candidate_id": "candidate-1",
                    "predecision_features": _complete_block(),
                }
            ),
        }
        (compacted,) = runner.compact_missed_opportunity_rows([assembled])
        # The allowlist would have dropped every condition field; the carry
        # preserves the assembly-time projection verbatim.
        assert compacted["candidate_id"] == "candidate-1"
        assert compacted["opportunity_net_proxy_r"] == -0.25
        assert compacted["predecision_features"] == _complete_block()
        assert compacted["condition_feature_projection_status"] == "complete"
        assert cuts.CONDITION_FEATURE_LEDGER_FIELDS <= set(compacted)
        # And the missed projection keeps them end to end.
        projected = cuts.project_missed_pool_row(compacted)
        assert projected["predecision_features"] == _complete_block()
        assert projected["condition_feature_projection_status"] == "complete"
    finally:
        patch.revert()

    assert cuts._CONDITION_FEATURE_PROPAGATION_ACTIVE == 0
    assert runner.compact_missed_opportunity_rows is compact_original
    assert timewarp.ledger_namespace_alias_fields is alias_original


def test_condition_patch_stamps_missing_on_rows_that_bypassed_the_helper(
    monkeypatch,
) -> None:
    _, runner, _, _ = _stub_modules(monkeypatch)
    patch = cuts.make_condition_feature_propagation_patch()

    patch.apply()
    try:
        # A pre-compaction row that never passed the instrumented helper has
        # no condition fields; absence must stay distinguishable from
        # instrument-off, so the carry stamps the status block ("missing").
        (compacted,) = runner.compact_missed_opportunity_rows(
            [{"candidate_id": "candidate-2"}]
        )
        assert "predecision_features" not in compacted
        assert compacted["condition_feature_projection_status"] == "missing"
        assert compacted["condition_feature_projection_missing_count"] == len(
            cuts.CONDITION_FEATURE_KEYS
        )
        # Belt: a row reaching the projector with no condition fields while
        # the instrument is armed still stamps "missing" there.
        projected = cuts.project_missed_pool_row(
            {"candidate_id": "candidate-3"}
        )
        assert projected["condition_feature_projection_status"] == "missing"
        assert "predecision_features" not in projected
    finally:
        patch.revert()


def test_missed_projection_is_byte_identical_when_the_instrument_is_off() -> None:
    row = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "opportunity_net_proxy_r": -0.25,
        "terminal_outcome": "stop_reached_before_target",
    }
    assert cuts._CONDITION_FEATURE_PROPAGATION_ACTIVE == 0
    inactive = cuts.project_missed_pool_row(row)
    assert not any(
        key in inactive for key in cuts.CONDITION_FEATURE_LEDGER_FIELDS
    )

    cuts._CONDITION_FEATURE_PROPAGATION_ACTIVE += 1
    try:
        active = cuts.project_missed_pool_row(row)
    finally:
        cuts._CONDITION_FEATURE_PROPAGATION_ACTIVE -= 1

    # The instrument adds ONLY its declared fields; with it off, the
    # projection output is byte-identical to the active output minus them.
    stripped = {
        key: value
        for key, value in active.items()
        if key not in cuts.CONDITION_FEATURE_LEDGER_FIELDS
    }
    assert stripped == inactive
    assert json.dumps(stripped, sort_keys=True, default=str) == json.dumps(
        inactive, sort_keys=True, default=str
    )

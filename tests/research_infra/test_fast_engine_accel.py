"""Behavioural proof that the fast engine's accelerations change no answer.

These are deliberately behavioural, not source-string assertions: each test
runs the frozen implementation and the accelerated one over the same adversarial
payloads and requires identical output. A test that greps for a substring passes
against a wrong implementation.
"""

from __future__ import annotations

import collections.abc as cabc
import json
import math
import types
from types import MappingProxyType

import pytest

from src.research_infra.fast_engine import accel, reproduction


# ---------------------------------------------------------------------------
# adversarial payloads
# ---------------------------------------------------------------------------


class _DictSubclass(dict):
    """Stands in for _FrozenPackageAuthorityPayload, which is dict[str, Any]."""


class _ListSubclass(list):
    """Stands in for _FrozenPackageAuthorityList, which is list[Any]."""


class _CustomMapping(cabc.Mapping):
    """A Mapping that is NOT a dict -- the case that would break the fast path."""

    def __init__(self, data):
        self._data = dict(data)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


ADVERSARIAL_VALUES = [
    {},
    {"a": 1},
    _DictSubclass({"a": 1}),
    [],
    [1, 2],
    _ListSubclass([1]),
    (1, 2),
    "text",
    b"bytes",
    bytearray(b"ba"),
    1,
    1.5,
    True,
    False,
    None,
    float("nan"),
    float("inf"),
    range(3),
    MappingProxyType({"a": 1}),
    _CustomMapping({"a": 1}),
    set(),
]


# ---------------------------------------------------------------------------
# P1: concrete-type isinstance dispatch
# ---------------------------------------------------------------------------


def _fake_module(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.Mapping = cabc.Mapping
    module.MutableMapping = cabc.MutableMapping
    module.Sequence = cabc.Sequence
    return module


def test_mapping_concrete_matches_abc_on_engine_shaped_values(monkeypatch):
    """dict and dict subclasses are the only Mappings the engine builds."""

    engine_shaped = [
        {},
        {"a": 1},
        _DictSubclass({"a": 1}),
        [1],
        _ListSubclass([1]),
        (1,),
        "text",
        b"x",
        1,
        1.0,
        True,
        None,
        float("nan"),
    ]
    for value in engine_shaped:
        assert isinstance(value, cabc.Mapping) == isinstance(value, dict), value


def test_mapping_concrete_diverges_only_on_non_dict_mappings():
    """The fast path's exact failure mode, stated as a test rather than a hope."""

    proxy = MappingProxyType({"a": 1})
    custom = _CustomMapping({"a": 1})
    for value in (proxy, custom):
        assert isinstance(value, cabc.Mapping) is True
        assert isinstance(value, dict) is False


def test_verify_mode_counts_the_divergence_it_is_there_to_find():
    accel.reset_verify_stats()
    module = _fake_module("fake_verify_module")
    patch = accel.make_abc_patch(
        symbols=("Mapping",), modules=("fake_verify_module",), verify=True
    )
    import sys

    sys.modules["fake_verify_module"] = module
    try:
        patch.apply()
        # a dict agrees, a non-dict Mapping does not
        assert isinstance({}, module.Mapping) is True
        assert isinstance(MappingProxyType({}), module.Mapping) is True
        report = accel.verify_report()
        assert report["Mapping"]["checks"] == 2
        assert report["Mapping"]["mismatches"] == 1
        assert report["Mapping"]["mismatch_types"] == {"mappingproxy": 1}
    finally:
        patch.revert()
        sys.modules.pop("fake_verify_module", None)
        accel.reset_verify_stats()


def test_verify_mode_returns_the_abc_answer_not_the_fast_one():
    """Verify mode must never change behaviour while it is measuring."""

    accel.reset_verify_stats()
    import sys

    module = _fake_module("fake_verify_module2")
    sys.modules["fake_verify_module2"] = module
    patch = accel.make_abc_patch(
        symbols=("Mapping",), modules=("fake_verify_module2",), verify=True
    )
    try:
        patch.apply()
        assert isinstance(MappingProxyType({}), module.Mapping) is True
    finally:
        patch.revert()
        sys.modules.pop("fake_verify_module2", None)
        accel.reset_verify_stats()


def test_strict_verify_raises_on_divergence():
    import sys

    accel.reset_verify_stats()
    module = _fake_module("fake_strict_module")
    sys.modules["fake_strict_module"] = module
    patch = accel.make_abc_patch(
        symbols=("Mapping",), modules=("fake_strict_module",), verify=True, strict=True
    )
    try:
        patch.apply()
        with pytest.raises(accel.VerifyMismatch):
            isinstance(MappingProxyType({}), module.Mapping)
    finally:
        patch.revert()
        sys.modules.pop("fake_strict_module", None)
        accel.reset_verify_stats()


def test_patch_reverts_exactly():
    import sys

    module = _fake_module("fake_revert_module")
    sys.modules["fake_revert_module"] = module
    patch = accel.make_abc_patch(
        symbols=("Mapping", "MutableMapping"), modules=("fake_revert_module",)
    )
    try:
        patch.apply()
        assert module.Mapping is dict
        assert module.MutableMapping is dict
        patch.revert()
        assert module.Mapping is cabc.Mapping
        assert module.MutableMapping is cabc.MutableMapping
    finally:
        sys.modules.pop("fake_revert_module", None)


def test_patch_leaves_foreign_rebindings_alone():
    """If something else already rebound the symbol, do not clobber it."""

    import sys

    module = _fake_module("fake_foreign_module")
    module.Mapping = str  # a foreign rebinding
    sys.modules["fake_foreign_module"] = module
    patch = accel.make_abc_patch(symbols=("Mapping",), modules=("fake_foreign_module",))
    try:
        patch.apply()
        assert module.Mapping is str
    finally:
        patch.revert()
        sys.modules.pop("fake_foreign_module", None)


def test_sequence_is_registered_but_off_by_default():
    """str/bytes/range ARE Sequences and are not (list, tuple) -- verify first."""

    assert "Sequence" in accel.ABC_CONCRETE
    assert "Sequence" not in accel.ABC_DEFAULT_SYMBOLS
    real, concrete = accel.ABC_CONCRETE["Sequence"]
    for value in ("text", b"bytes", range(3)):
        assert isinstance(value, real) is True
        assert isinstance(value, concrete) is False


def test_sequence_can_be_opted_into_explicitly():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    patch = accel.make_abc_patch(
        symbols=("Sequence",),
        modules=("src.research.moonshot_scheduler_v4_best_trade_allocator",),
    )
    patch.apply()
    try:
        assert allocator.Sequence == (list, tuple)
    finally:
        patch.revert()
    assert allocator.Sequence is cabc.Sequence


def test_sequence_rebinding_is_output_identical_at_the_hot_call_site():
    """_canonical_hash_payload guards str/bytes/bytearray itself, so the two
    dispatches agree there -- which is the argument for opting in, measured."""

    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payload = {
        "text": "unicode-é",
        "raw": "009",
        "list": [1, "two", (3, "four")],
        "nested": {"deep": ["a", {"b": "c"}]},
    }
    before = json.dumps(
        allocator._canonical_hash_payload(payload), sort_keys=True, default=str
    )
    patch = accel.make_abc_patch(
        symbols=("Mapping", "Sequence"),
        modules=("src.research.moonshot_scheduler_v4_best_trade_allocator",),
    )
    patch.apply()
    try:
        after = json.dumps(
            allocator._canonical_hash_payload(payload), sort_keys=True, default=str
        )
    finally:
        patch.revert()
    assert before == after


def test_dict_supports_the_runtime_subscript_mapping_supported():
    """Mapping[str, Any] must keep evaluating after the rebinding."""

    assert dict[str, int] is not None


def test_installer_manifest_names_every_identity_argument():
    installer = accel.build_installer()
    manifest = installer.manifest()
    assert manifest["available"], "an installer with no patches proves nothing"
    for entry in manifest["available"]:
        assert entry["identity_argument"].strip(), entry["patch_id"]
        assert entry["summary"].strip(), entry["patch_id"]


def test_installer_rejects_unknown_patch_ids():
    installer = accel.build_installer()
    with pytest.raises(ValueError, match="unknown_patch_ids"):
        installer.install(["no_such_patch"])


def test_canonical_hash_payload_is_unchanged_by_the_rebinding():
    """The real hot function, run both ways over adversarial input."""

    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payload = {
        "z": 1,
        "a": {"nested": [1, 2, {"deep": "x"}], "empty": "", "none": None},
        "frozen": _DictSubclass({"k": _ListSubclass([1, 2])}),
        "tuple": (1, 2),
        "float": 1.23456789012345,
        "text": "unicode-é",
        "true": True,
    }
    before = json.dumps(
        allocator._canonical_hash_payload(payload), sort_keys=True, default=str
    )
    patch = accel.make_abc_patch(
        symbols=("Mapping",),
        modules=("src.research.moonshot_scheduler_v4_best_trade_allocator",),
    )
    patch.apply()
    try:
        assert allocator.Mapping is dict
        after = json.dumps(
            allocator._canonical_hash_payload(payload), sort_keys=True, default=str
        )
    finally:
        patch.revert()
    assert allocator.Mapping is cabc.Mapping
    assert before == after


def test_authority_payload_hash_is_unchanged_by_the_rebinding():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payload = {
        "payload_schema": "s",
        "candidate_id": "c-1",
        "decision_time_utc": "2026-01-01T00:00:00Z",
        "nested": {"a": [1, 2], "b": ""},
    }
    before = allocator.package_new_entry_authority_payload_hash_sha256(payload)
    patch = accel.make_abc_patch(
        symbols=("Mapping",),
        modules=("src.research.moonshot_scheduler_v4_best_trade_allocator",),
    )
    patch.apply()
    try:
        after = allocator.package_new_entry_authority_payload_hash_sha256(payload)
    finally:
        patch.revert()
    assert before == after


# ---------------------------------------------------------------------------
# P2: authority payload hash memo
# ---------------------------------------------------------------------------


def _memo_patch(verify: bool = False):
    accel.reset_memo_stats()
    return accel.make_authority_hash_memo_patch(verify=verify)


def test_memo_returns_the_same_digest_as_the_frozen_function():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payloads = [
        {"payload_schema": "s", "candidate_id": f"c-{i}", "nested": {"a": [1, i]}}
        for i in range(5)
    ]
    expected = [
        allocator.package_new_entry_authority_payload_hash_sha256(p) for p in payloads
    ]
    patch = _memo_patch()
    patch.apply()
    try:
        # each payload hashed three times -- the repeat pattern the finalizer has
        for _ in range(3):
            got = [
                allocator.package_new_entry_authority_payload_hash_sha256(p)
                for p in payloads
            ]
            assert got == expected
    finally:
        patch.revert()
    report = accel.memo_report()["authority_payload_hash"]
    assert report["calls"] == 15
    assert report["hits"] == 10, report
    assert report["misses"] == 5, report


def test_memo_patches_every_module_that_imported_the_symbol_by_name():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator
    from src.research_infra import v4_timewarp_simulated_live_research_loop as v4

    original_allocator = allocator.package_new_entry_authority_payload_hash_sha256
    original_v4 = v4.package_new_entry_authority_payload_hash_sha256
    patch = _memo_patch()
    patch.apply()
    try:
        assert allocator.package_new_entry_authority_payload_hash_sha256 is not (
            original_allocator
        )
        assert v4.package_new_entry_authority_payload_hash_sha256 is not original_v4
        # and the two module globals point at the SAME memo, or the caches split
        assert (
            allocator.package_new_entry_authority_payload_hash_sha256
            is v4.package_new_entry_authority_payload_hash_sha256
        )
    finally:
        patch.revert()
    assert allocator.package_new_entry_authority_payload_hash_sha256 is (
        original_allocator
    )
    assert v4.package_new_entry_authority_payload_hash_sha256 is original_v4


def test_memo_verify_mode_catches_in_place_mutation():
    """The one hazard the identity argument rests on, made to actually happen."""

    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payload = {"payload_schema": "s", "candidate_id": "c-1"}
    patch = _memo_patch(verify=True)
    patch.apply()
    try:
        first = allocator.package_new_entry_authority_payload_hash_sha256(payload)
        payload["candidate_id"] = "c-2"  # the forbidden mutation
        second = allocator.package_new_entry_authority_payload_hash_sha256(payload)
    finally:
        patch.revert()
    report = accel.memo_report()["authority_payload_hash"]
    assert report["mismatches"] == 1, report
    # verify mode must return the TRUE digest, not the stale memo
    assert second != first
    assert second == allocator.package_new_entry_authority_payload_hash_sha256(payload)


def test_memo_frozen_payloads_pass_through_to_the_engines_own_cache():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    frozen = allocator.freeze_package_new_entry_authority_payload(
        {"payload_schema": "s", "candidate_id": "c-1"}
    )
    patch = _memo_patch()
    patch.apply()
    try:
        allocator.package_new_entry_authority_payload_hash_sha256(frozen)
        allocator.package_new_entry_authority_payload_hash_sha256(frozen)
    finally:
        patch.revert()
    report = accel.memo_report()["authority_payload_hash"]
    assert report["frozen_passthrough"] == 2
    assert report["hits"] == 0


def test_memo_eviction_is_bounded(monkeypatch):
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    monkeypatch.setattr(accel, "MEMO_MAX_ENTRIES", 4)
    patch = _memo_patch()
    patch.apply()
    try:
        payloads = [{"candidate_id": f"c-{i}"} for i in range(40)]
        digests = [
            allocator.package_new_entry_authority_payload_hash_sha256(p)
            for p in payloads
        ]
    finally:
        patch.revert()
    # every digest still correct despite eviction
    for payload, digest in zip(payloads, digests):
        assert allocator.package_new_entry_authority_payload_hash_sha256(payload) == (
            digest
        )


def test_memo_revert_restores_and_clears():
    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    original = allocator.package_new_entry_authority_payload_hash_sha256
    patch = _memo_patch()
    patch.apply()
    allocator.package_new_entry_authority_payload_hash_sha256({"a": 1})
    patch.revert()
    assert allocator.package_new_entry_authority_payload_hash_sha256 is original


def test_both_patches_together_preserve_the_digest():
    """The combination is what ships, so the combination is what is tested."""

    from src.research import moonshot_scheduler_v4_best_trade_allocator as allocator

    payload = {
        "payload_schema": "s",
        "candidate_id": "c-1",
        "nested": {"list": [1, {"x": "é"}], "empty": "", "none": None},
        "float": 0.1 + 0.2,
    }
    expected = allocator.package_new_entry_authority_payload_hash_sha256(payload)
    accel.reset_memo_stats()
    installer = accel.build_installer()
    installer.install()
    try:
        assert set(installer.applied) == set(accel.DEFAULT_PATCHES)
        for _ in range(3):
            assert (
                allocator.package_new_entry_authority_payload_hash_sha256(payload)
                == expected
            )
    finally:
        installer.revert_all()
    assert allocator.package_new_entry_authority_payload_hash_sha256(payload) == expected


# ---------------------------------------------------------------------------
# P3: attribution-field memo (default-off until a verify run clears it)
# ---------------------------------------------------------------------------


def test_authority_hash_memo_is_off_by_default_on_measured_economics():
    """0.11 % hit rate over 52.0 M calls, +270 MB peak RSS: net cost, not saving."""

    assert "authority_hash_identity_memo" not in accel.DEFAULT_PATCHES
    patch = accel.make_authority_hash_memo_patch()
    assert patch.default_on is False
    # correctness was never the problem, and the record should say so
    assert "0 mismatches" in patch.identity_argument
    assert "0.11" in patch.identity_argument


def test_attribution_memo_is_not_default_on():
    """The mutation hazard is real, so this one must not ship by accident."""

    installer = accel.build_installer()
    installer.install()
    try:
        assert "attribution_fields_identity_memo" not in installer.applied
    finally:
        installer.revert_all()
    assert "attribution_fields_identity_memo" not in accel.DEFAULT_PATCHES


def test_attribution_memo_returns_equal_projections():
    from src.research_infra import v4_timewarp_simulated_live_research_loop as v4

    surface = {
        "package_new_entry_authority_authority_field": "",
        "package_new_entry_authority_payload": {
            "payload_schema": "s",
            "candidate_id": "c-1",
        },
        "package_new_entry_authority_status": "valid",
    }
    expected = v4.package_new_entry_authority_attribution_fields(surface)
    accel.reset_memo_stats()
    patch = accel.make_attribution_fields_memo_patch()
    patch.apply()
    try:
        first = v4.package_new_entry_authority_attribution_fields(surface)
        second = v4.package_new_entry_authority_attribution_fields(surface)
    finally:
        patch.revert()
    assert first == expected
    assert second == expected
    stats = accel.memo_report()["attribution_fields"]
    assert stats["hits"] == 1, stats


def test_attribution_memo_hands_out_a_fresh_outer_dict_each_call():
    """A caller mutating the returned dict must not poison the memo."""

    from src.research_infra import v4_timewarp_simulated_live_research_loop as v4

    surface = {"package_new_entry_authority_payload": {"payload_schema": "s"}}
    accel.reset_memo_stats()
    patch = accel.make_attribution_fields_memo_patch()
    patch.apply()
    try:
        first = v4.package_new_entry_authority_attribution_fields(surface)
        first["injected_by_caller"] = True
        second = v4.package_new_entry_authority_attribution_fields(surface)
        assert "injected_by_caller" not in second
        assert first is not second
    finally:
        patch.revert()


def test_attribution_memo_verify_mode_catches_surface_mutation():
    from src.research_infra import v4_timewarp_simulated_live_research_loop as v4

    surface = {
        "package_new_entry_authority_payload": {
            "payload_schema": "s",
            "candidate_id": "c-1",
        }
    }
    accel.reset_memo_stats()
    patch = accel.make_attribution_fields_memo_patch(verify=True)
    patch.apply()
    try:
        v4.package_new_entry_authority_attribution_fields(surface)
        surface["package_new_entry_authority_status"] = "mutated_after_memo"
        recomputed = v4.package_new_entry_authority_attribution_fields(surface)
    finally:
        patch.revert()
    stats = accel.memo_report()["attribution_fields"]
    assert stats["mismatches"] == 1, stats
    # and verify mode returned the recomputed truth
    assert recomputed == v4.package_new_entry_authority_attribution_fields(surface)


def test_attribution_memo_distinguishes_prefix_and_validation_flag():
    from src.research_infra import v4_timewarp_simulated_live_research_loop as v4

    surface = {"package_new_entry_authority_payload": {"payload_schema": "s"}}
    accel.reset_memo_stats()
    patch = accel.make_attribution_fields_memo_patch()
    patch.apply()
    try:
        plain = v4.package_new_entry_authority_attribution_fields(surface)
        prefixed = v4.package_new_entry_authority_attribution_fields(
            surface, prefix="selected_"
        )
    finally:
        patch.revert()
    stats = accel.memo_report()["attribution_fields"]
    assert stats["hits"] == 0, "different kwargs must not share a memo entry"
    assert set(plain) != set(prefixed) or not plain


# ---------------------------------------------------------------------------
# P4 / the evidence dial
# ---------------------------------------------------------------------------


def test_recertification_skip_returns_the_identical_contract():
    """The whole identity argument, executed rather than asserted."""

    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )

    frozen_contract = attempt5.current_summary_v2_contract_for_rows(())
    patch = accel.make_skip_ledger_recertification_patch()
    patch.apply()
    try:
        rows_that_must_not_be_read = _ExplodingIterable()
        patched_contract = attempt5.current_summary_v2_contract_for_rows(
            rows_that_must_not_be_read
        )
    finally:
        patch.revert()
    assert patched_contract == frozen_contract
    assert not rows_that_must_not_be_read.iterated


class _ExplodingIterable:
    def __init__(self):
        self.iterated = False

    def __iter__(self):
        self.iterated = True
        raise AssertionError("the skipped path must not read the ledgers")


def test_evidence_levels_resolve_to_named_patches():
    assert accel.patches_for(evidence="full") == list(accel.DEFAULT_PATCHES)
    decision = accel.patches_for(evidence="decision")
    assert "skip_post_hoc_ledger_recertification" in decision
    assert set(accel.DEFAULT_PATCHES).issubset(decision)


def test_unknown_evidence_level_is_rejected():
    with pytest.raises(ValueError, match="unknown_evidence_level"):
        accel.patches_for(evidence="whatever")


def test_evidence_full_is_the_frozen_evidence_behaviour():
    """'full' must not silently include an evidence-suppressing patch."""

    assert "skip_post_hoc_ledger_recertification" not in accel.patches_for(
        evidence="full"
    )


# ---------------------------------------------------------------------------
# P5: gc during the chunk -- sealed-incompatible and must announce it
# ---------------------------------------------------------------------------


def test_gc_patch_is_marked_sealed_incompatible_and_default_off():
    patch = accel.make_gc_during_chunk_patch()
    assert patch.sealed_compatible is False
    assert patch.default_on is False
    assert "gc_during_chunk" not in accel.DEFAULT_PATCHES


def test_manifest_flags_a_sealed_incompatible_run():
    installer = accel.build_installer()
    installer.install(["gc_during_chunk"])
    try:
        manifest = installer.manifest()
        assert manifest["sealed_lane_compatible"] is False
        assert manifest["applied_sealed_incompatible"] == ["gc_during_chunk"]
    finally:
        installer.revert_all()


def test_default_run_is_sealed_lane_compatible():
    installer = accel.build_installer()
    installer.install(list(accel.DEFAULT_PATCHES))
    try:
        manifest = installer.manifest()
        assert manifest["sealed_lane_compatible"] is True
        assert manifest["applied_sealed_incompatible"] == []
    finally:
        installer.revert_all()


def test_gc_patch_suppresses_the_in_chunk_disable_and_reverts_thresholds():
    import gc as real_gc

    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )

    original_module_gc = attempt5.gc
    original_threshold = real_gc.get_threshold()
    was_enabled = real_gc.isenabled()
    patch = accel.make_gc_during_chunk_patch(gen0_threshold=12345)
    patch.apply()
    try:
        assert attempt5.gc is not original_module_gc
        assert real_gc.get_threshold()[0] == 12345
        # the engine's own idiom must not turn collection off
        if attempt5.gc.isenabled():
            attempt5.gc.disable()
        assert real_gc.isenabled() is True
        # pass-through still works for everything else
        assert attempt5.gc.collect() >= 0
    finally:
        patch.revert()
        if was_enabled:
            real_gc.enable()
        else:
            real_gc.disable()
    assert attempt5.gc is original_module_gc
    assert real_gc.get_threshold() == original_threshold


# ---------------------------------------------------------------------------
# the comparator
# ---------------------------------------------------------------------------


def test_nan_equals_nan_but_one_sided_nan_is_a_difference():
    nan = float("nan")
    assert reproduction.values_equal(nan, nan) is True
    assert reproduction.values_equal(nan, 1.0) is False
    assert reproduction.values_equal(1.0, nan) is False


def test_inf_comparison_is_signed():
    assert reproduction.values_equal(float("inf"), float("inf")) is True
    assert reproduction.values_equal(float("inf"), float("-inf")) is False


def test_bool_is_not_int_for_the_comparator():
    """True == 1 in Python; an exit_reason flag flipping must not read as equal."""

    assert reproduction.values_equal(True, 1) is False
    assert reproduction.values_equal(0, False) is False


def test_absent_key_is_a_difference_not_a_skip():
    left = {"counts": {"trade": 1}, "trades": [{"exact_r": 1.0, "symbol": "X"}]}
    right = {"counts": {"trade": 1}, "trades": [{"exact_r": 1.0}]}
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "DIVERGENT"
    assert any(d.kind == "absent_on_one_side" for d in result.differences)


def test_empty_both_sides_is_not_identical():
    result = reproduction.compare_economics(
        {"counts": {}, "trades": [], "missed_digest": {"rows": 0}},
        {"counts": {}, "trades": [], "missed_digest": {"rows": 0}},
    )
    assert result.verdict == "EMPTY"
    assert "nothing was proved" in " ".join(result.notes)


def test_identical_economics_reports_r_identical():
    payload = {
        "counts": {"trade": 1, "order": 1},
        "trades": [{"exact_r": -1.0, "net_cash": -100.5, "symbol": "XAUUSD"}],
        "orders": [{"order_id": 1}],
        "scorecards": [],
        "missed_digest": {"rows": 3, "positive_net_r": 1.5, "negative_net_r": -2.5},
    }
    result = reproduction.compare_economics(payload, json.loads(json.dumps(payload)))
    assert result.verdict == "R_IDENTICAL"
    assert result.compared_rows == 2


def test_row_count_divergence_is_caught_before_field_comparison():
    left = {"counts": {"trade": 2}, "trades": [{"exact_r": 1.0}, {"exact_r": 2.0}]}
    right = {"counts": {"trade": 1}, "trades": [{"exact_r": 1.0}]}
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "DIVERGENT"
    assert any(d.kind == "row_count" for d in result.differences)


def test_timing_fields_are_excluded_and_the_exclusion_is_published():
    left = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0, "economic_hot_path_seconds": 10.0}],
        "missed_digest": {"rows": 1},
    }
    right = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0, "economic_hot_path_seconds": 3.0}],
        "missed_digest": {"rows": 1},
    }
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "R_IDENTICAL"
    published = result.as_dict()["excluded_fields"]
    assert "economic_hot_path_seconds" in published


def test_tolerance_downgrades_the_verdict_rather_than_hiding_it():
    left = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0000000001}],
        "missed_digest": {"rows": 1},
    }
    right = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0}],
        "missed_digest": {"rows": 1},
    }
    exact = reproduction.compare_economics(left, right)
    assert exact.verdict == "DIVERGENT"
    toleranced = reproduction.compare_economics(left, right, rel_tol=1e-9)
    assert toleranced.verdict == "ECONOMICALLY_IDENTICAL"
    assert "not bit-for-bit" in " ".join(toleranced.notes)


def _diag(value, **extra):
    row = {
        "missed_opportunity_non_executable_diagnostic_scoreable": True,
        "opportunity_net_proxy_r": value,
    }
    row.update(extra)
    return row


def test_missed_digest_aggregates_signed_pools_separately():
    """Mirrors analyze_b7_5_selection_sizing_matrix.py:742-770 exactly."""

    from src.research_infra.fast_engine import bench

    digest = bench._missed_digest(
        [
            _diag(2.0),
            _diag(-3.0),
            _diag(0.0),
            _diag(1.5),
            {"opportunity_net_proxy_r": 99.0},  # not diagnostic-scoreable
        ]
    )
    assert digest["positive_net_r"] == 3.5
    assert digest["negative_net_r"] == -3.0
    assert digest["positive_rows"] == 2
    assert digest["negative_rows"] == 1
    assert digest["flat_rows"] == 1
    assert digest["diagnostic_scoreable_rows"] == 4
    assert digest["rows"] == 5


def test_missed_digest_honours_the_status_gate_as_well_as_the_boolean():
    from src.research_infra.fast_engine import bench

    digest = bench._missed_digest(
        [
            {
                "missed_opportunity_r_scoreability_status": (
                    "diagnostic_opportunity_r_scoreable"
                ),
                "opportunity_net_proxy_r": 4.0,
            }
        ]
    )
    assert digest["diagnostic_scoreable_rows"] == 1
    assert digest["positive_net_r"] == 4.0


def test_missed_digest_counts_unreadable_proxies_loudly():
    """A silent null here would understate the diagnostic pool."""

    from src.research_infra.fast_engine import bench

    digest = bench._missed_digest([_diag(None), _diag("not-a-number"), _diag(1.0)])
    assert digest["unreadable_proxy_rows"] == 2
    assert digest["diagnostic_scoreable_rows"] == 3
    assert digest["positive_net_r"] == 1.0


def test_ledger_digest_covers_nested_fields_the_pruned_rows_drop():
    from src.research_infra.fast_engine import bench

    left = [{"a": 1, "nested": {"deep": 1}}]
    right = [{"a": 1, "nested": {"deep": 2}}]
    assert bench._prune_row(left[0]) == bench._prune_row(right[0])
    assert bench._ledger_digest(left) != bench._ledger_digest(right)


def test_ledger_digest_ignores_excluded_fields():
    from src.research_infra.fast_engine import bench

    left = [{"a": 1, "economic_hot_path_seconds": 10.0}]
    right = [{"a": 1, "economic_hot_path_seconds": 3.0}]
    assert bench._ledger_digest(left) == bench._ledger_digest(right)


def test_digest_mismatch_alone_makes_the_comparison_divergent():
    """The pruned scalars can agree while a nested field moved."""

    base = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0}],
        "missed_digest": {"rows": 1},
        "ledger_digests": {"trade": "aaa"},
    }
    other = json.loads(json.dumps(base))
    other["ledger_digests"]["trade"] = "bbb"
    result = reproduction.compare_economics(base, other)
    assert result.verdict == "DIVERGENT"
    assert any(d.kind == "ledger_digest" for d in result.differences)


def test_receipt_refuses_to_accept_a_divergent_run():
    from src.research_infra.fast_engine import receipt

    base = {
        "wall_seconds": 100.0,
        "rusage": {"maxrss_bytes": 1000},
        "receipt_counts": {"trade_rows": 5},
        "error": None,
    }
    fast = {
        "wall_seconds": 50.0,
        "rusage": {"maxrss_bytes": 900},
        "receipt_counts": {"trade_rows": 5},
        "error": None,
    }
    built = receipt.build_receipt(
        baseline_report=base,
        fast_report=fast,
        comparison={"verdict": "DIVERGENT"},
    )
    assert built["accepted"] is False
    assert built["delta"]["wall_speedup"] == 2.0


def test_receipt_refuses_to_accept_when_row_counts_differ():
    """A 2x speedup that produced four trades instead of five is not a pass."""

    from src.research_infra.fast_engine import receipt

    built = receipt.build_receipt(
        baseline_report={
            "wall_seconds": 100.0,
            "rusage": {"maxrss_bytes": 1000},
            "receipt_counts": {"trade_rows": 5},
            "error": None,
        },
        fast_report={
            "wall_seconds": 50.0,
            "rusage": {"maxrss_bytes": 900},
            "receipt_counts": {"trade_rows": 4},
            "error": None,
        },
        comparison={"verdict": "R_IDENTICAL"},
    )
    assert built["accepted"] is False


def test_receipt_refuses_to_accept_a_run_that_errored():
    from src.research_infra.fast_engine import receipt

    built = receipt.build_receipt(
        baseline_report={
            "wall_seconds": 100.0,
            "rusage": {"maxrss_bytes": 1000},
            "receipt_counts": {},
            "error": None,
        },
        fast_report={
            "wall_seconds": 50.0,
            "rusage": {"maxrss_bytes": 900},
            "receipt_counts": {},
            "error": "Traceback ...",
        },
        comparison={"verdict": "R_IDENTICAL"},
    )
    assert built["accepted"] is False


def test_receipt_labels_a_bounded_run_as_not_an_arm_of_record():
    from src.research_infra.fast_engine import receipt

    built = receipt.build_receipt(
        baseline_report={
            "wall_seconds": 1.0,
            "rusage": {"maxrss_bytes": 1},
            "receipt_counts": {},
            "error": None,
            "stop_after_day": "2026-01-02",
        },
        fast_report={
            "wall_seconds": 1.0,
            "rusage": {"maxrss_bytes": 1},
            "receipt_counts": {},
            "error": None,
        },
        comparison={"verdict": "R_IDENTICAL"},
    )
    assert built["fixture"]["is_sealed_arm_of_record"] is False
    assert "H5" in built["fixture"]["note"]


def test_run_namespace_is_normalised_out_of_row_values():
    """Two runs cannot share an output namespace, so it must not read as drift."""

    left = {
        "output_prefix": "AX_BASE_D2_B7_5_S1R1",
        "counts": {"trade": 1},
        "trades": [
            {
                "campaign": "ax_base_d2_b7_5_s1r1_repaired_v3",
                "order_id": "ax_base_d2_b7_5_s1r1:order:000001",
                "net_r": -1.09544224,
            }
        ],
        "missed_digest": {"rows": 1},
    }
    right = json.loads(json.dumps(left).replace("base", "fast").replace("BASE", "FAST"))
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "R_IDENTICAL", result.as_dict()["differences"]
    assert any("normalised" in note for note in result.notes)


def test_missing_output_prefix_is_reported_not_silently_skipped():
    payload = {
        "counts": {"trade": 1},
        "trades": [{"net_r": 1.0}],
        "missed_digest": {"rows": 1},
    }
    result = reproduction.compare_economics(payload, json.loads(json.dumps(payload)))
    assert any("were NOT normalised" in note for note in result.notes)


def test_a_short_prefix_is_refused_rather_than_masking_real_differences():
    """`a` is a substring of every hex digest; normalising it would hide drift."""

    left = {
        "output_prefix": "A",
        "counts": {"trade": 1},
        "trades": [{"net_r": -1.0, "packet_sidecar_id": "a" * 64}],
        "missed_digest": {"rows": 1},
    }
    right = json.loads(json.dumps(left))
    right["output_prefix"] = "B"
    right["trades"][0]["packet_sidecar_id"] = "b" * 64
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "PROVENANCE_DIGESTS_ONLY"
    assert any("NOT normalised" in note for note in result.notes)


def test_provenance_digest_only_divergence_gets_its_own_verdict():
    left = {
        "output_prefix": "AX_BASE_D2_B7_5_S1R1",
        "counts": {"trade": 1},
        "trades": [{"net_r": -1.0, "packet_sidecar_id": "a" * 64}],
        "missed_digest": {"rows": 1},
    }
    right = json.loads(json.dumps(left))
    right["output_prefix"] = "AX_FAST_D2_B7_5_S1R1"
    right["trades"][0]["packet_sidecar_id"] = "b" * 64
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "PROVENANCE_DIGESTS_ONLY"
    assert result.as_dict()["quantity_difference_count"] == 0
    assert result.as_dict()["provenance_digest_difference_count"] == 1
    assert "control" in " ".join(result.notes)


def test_one_moved_quantity_beats_any_number_of_digest_differences():
    left = {
        "output_prefix": "A",
        "counts": {"trade": 1},
        "trades": [{"net_r": -1.0, "packet_sidecar_id": "a" * 64}],
        "missed_digest": {"rows": 1},
    }
    right = json.loads(json.dumps(left))
    right["output_prefix"] = "B"
    right["trades"][0]["packet_sidecar_id"] = "b" * 64
    right["trades"][0]["net_r"] = -1.0000001
    result = reproduction.compare_economics(left, right)
    assert result.verdict == "DIVERGENT"
    assert result.as_dict()["quantity_difference_count"] == 1


def test_difference_signature_is_comparable_between_two_comparisons():
    def make(prefix, digest):
        return {
            "output_prefix": f"AX_{prefix}_D2_B7_5_S1R1",
            "counts": {"trade": 1},
            "trades": [{"net_r": -1.0, "packet_sidecar_id": digest}],
            "missed_digest": {"rows": 1},
        }

    control = reproduction.compare_economics(
        make("BASE", "a" * 64), make("CTRL", "b" * 64)
    )
    candidate = reproduction.compare_economics(
        make("BASE", "a" * 64), make("FAST", "c" * 64)
    )
    assert control.signature() == candidate.signature() == {"packet_sidecar_id": 1}


def test_extract_economics_refuses_an_absent_route(tmp_path):
    """An empty extraction is never a valid payload -- it must raise, not return."""

    from src.research_infra.fast_engine import bench

    with pytest.raises(FileNotFoundError, match="economics_route_absent"):
        bench.extract_economics(tmp_path / "gone", "ANY_PREFIX")


def test_ledger_digest_normalises_the_run_namespace():
    from src.research_infra.fast_engine import bench

    left = [{"campaign": "ax_base_x_repaired", "net_r": 1.0}]
    right = [{"campaign": "ax_fast_x_repaired", "net_r": 1.0}]
    assert bench._ledger_digest(left, "ax_base_x") == bench._ledger_digest(
        right, "ax_fast_x"
    )


def test_missing_digests_are_reported_rather_than_assumed_clean():
    base = {
        "counts": {"trade": 1},
        "trades": [{"exact_r": 1.0}],
        "missed_digest": {"rows": 1},
    }
    result = reproduction.compare_economics(base, json.loads(json.dumps(base)))
    assert result.verdict == "R_IDENTICAL"
    assert any("NOT compared" in note for note in result.notes)


# ---------------------------------------------------------------------------
# output cleanup safety
# ---------------------------------------------------------------------------


def test_route_cleanup_refuses_anything_outside_the_attempt5_root(tmp_path):
    """B88: the denominator route has paths that are load-bearing by absence."""

    from src.research_infra.fast_engine import bench

    outside = tmp_path / "not_the_route"
    outside.mkdir()
    (outside / "sentinel").write_text("x")
    removed = bench._remove_route(outside)
    assert removed == []
    assert (outside / "sentinel").is_file()


def test_route_cleanup_refuses_the_namespace_root_itself():
    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )
    from src.research_infra.fast_engine import bench

    # The namespace root is an EMPTY directory, and git does not track empty directories, so
    # it cannot be restored by `git checkout`/`git stash pop` and its absence leaves
    # `git status` clean. Any working-tree clean makes this test fail once and then heal
    # itself, because the sibling test below recreates the root with `parents=True`.
    #
    # That matters more than it sounds: the working agreement MANDATES A/B by copy-back, which
    # is exactly such a clean. Found 2026-07-31 by Session CC (B2231) when its own copy-back
    # produced a single unreproducible failure here — the failure was real, the cause was the
    # harness, and the next session doing an honest A/B would have paid for it again.
    #
    # Making the precondition explicit rather than inherited keeps the assertion below meaning
    # what its name says: does `_remove_route` REFUSE the root? It cannot answer that against a
    # root that is not there.
    attempt5.ATTEMPT5_NAMESPACE_ROOT.mkdir(parents=True, exist_ok=True)

    removed = bench._remove_route(attempt5.ATTEMPT5_NAMESPACE_ROOT)
    assert removed == []
    assert attempt5.ATTEMPT5_NAMESPACE_ROOT.is_dir()


def test_route_cleanup_removes_its_own_namespace_and_the_semantic_sibling():
    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )
    from src.research_infra.fast_engine import bench

    route = attempt5.ATTEMPT5_NAMESPACE_ROOT / "AX_UNIT_CLEANUP_PROBE"
    semantic = attempt5.semantic_diagnostic_root(route)
    route.mkdir(parents=True, exist_ok=False)
    semantic.mkdir(parents=True, exist_ok=False)
    (route / "row.jsonl").write_text("{}\n")
    try:
        removed = bench._remove_route(route)
        assert len(removed) == 2
        assert not route.exists()
        assert not semantic.exists()
    finally:
        for path in (route, semantic):
            if path.exists():
                import shutil

                shutil.rmtree(path)

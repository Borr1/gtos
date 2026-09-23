"""The content memo is the lane's biggest cut. These tests pin what it trusts.

The patch is installed against a STUB module rather than the real 44k-line
allocator: the mechanics under test are "which symbol gets rebound, in which
modules, and does it revert", and a stub makes those observable without a
20-second import. The economic correctness of the memo is not asserted here at
all -- it is measured by `--verify` on the real engine and by the trade-outcome
identity gate, and the result doc carries the numbers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from src.research_infra.train_engine import cuts


# --------------------------------------------------------------------------
# the key
# --------------------------------------------------------------------------


def _engine_key(payload):
    """The allocator's own cheap key, reproduced here as the comparand.

    Kept as an independent copy on purpose: if the engine's key changes, this
    test measures that the memo key is still STRICTLY STRONGER, which is the
    property the identity argument rests on.
    """

    return (
        payload.get("payload_schema"),
        payload.get("payload_contract"),
        payload.get("candidate_id"),
        payload.get("decision_time_utc"),
        payload.get("canonical_replay_candidate_instance_key"),
        payload.get("source_bound_replay_candidate_instance_key"),
        payload.get("target_action_intent"),
        payload.get("scope"),
        payload.get("selector_action"),
        payload.get("selector_reason"),
        payload.get("authority_family"),
        payload.get("authority_source"),
        len(payload),
    )


def test_the_memo_key_supersets_the_engines_own_key() -> None:
    """Every one of the engine's 12 key fields is a top-level scalar, so the
    memo key contains them all -- and separates payloads the engine key
    collides."""

    a = {"candidate_id": "c1", "scope": "open", "risk_pct": 0.25}
    b = {"candidate_id": "c1", "scope": "open", "risk_pct": 0.50}
    assert _engine_key(a) == _engine_key(b)
    assert cuts._content_key(a) != cuts._content_key(b)

    scalars = next(iter(cuts._content_key(a)[1:2]))
    named = {name for name, _type, _value in scalars}
    assert {"candidate_id", "scope"} <= named


def test_the_memo_key_does_not_fold_bool_into_int() -> None:
    assert cuts._content_key({"authority_allowed": True}) != cuts._content_key(
        {"authority_allowed": 1}
    )


def test_the_memo_key_is_order_insensitive() -> None:
    a = {"candidate_id": "c1", "scope": "open", "x": 1}
    b = {"x": 1, "scope": "open", "candidate_id": "c1"}
    assert cuts._content_key(a) == cuts._content_key(b)


def test_the_known_residual_is_a_nested_only_difference_and_it_is_pinned() -> None:
    """THE limit of the trusted key, asserted rather than left in prose.

    Two payloads identical in every top-level scalar AND in every container's
    name/type/length, differing only INSIDE a container, produce the same key.
    That is the exact residual `--verify` exists to measure. If a future change
    makes the key deep, this test fails and the identity argument must be
    rewritten -- which is the point.
    """

    assert cuts._content_key({"candidate_id": "c1", "nested": {"value": 1}}) == (
        cuts._content_key({"candidate_id": "c1", "nested": {"value": 2}})
    )


def test_container_shape_is_in_the_key_so_a_changed_length_separates() -> None:
    assert cuts._content_key({"a": 1, "n": [1, 2]}) != cuts._content_key(
        {"a": 1, "n": [1, 2, 3]}
    )
    assert cuts._content_key({"a": 1, "n": [1, 2]}) != cuts._content_key(
        {"a": 1, "n": (1, 2)}
    )


def test_a_payload_with_containers_but_no_scalar_refuses_rather_than_trusting_shape() -> None:
    """A pure-shape key is not evidence of anything. Refusing costs one frozen
    call; trusting it would be the fast-wrong-engine the commission refuses."""

    assert cuts._content_key({"nested": {"v": 1}}) is cuts.UNKEYABLE
    assert cuts._content_key({"a": [1], "b": {"x": 2}}) is cuts.UNKEYABLE


def test_an_empty_payload_is_keyed_exactly_rather_than_refused() -> None:
    """`{}` has no scalars, but the key determines its content completely.
    Refusing it cost 3,433,381 fallback calls (11.8 % of the authority hash's
    traffic) on the 2-day fixture and bought nothing."""

    assert cuts._content_key({}) is not cuts.UNKEYABLE
    assert cuts._content_key({}) == cuts._content_key({})
    assert cuts._content_key({}) != cuts._content_key({"a": 1})


@pytest.mark.parametrize("payload", [[1, 2, 3], "text", 5, None, (1, 2)])
def test_a_non_mapping_payload_refuses(payload: object) -> None:
    """json.dumps of a scalar or short list is already cheap; a list key would
    be a guess for no gain."""

    assert cuts._content_key(payload) is cuts.UNKEYABLE


def test_the_key_is_hashable_for_realistic_payload_values() -> None:
    payload = {
        "payload_schema": "s",
        "candidate_id": "c1",
        "decision_time_utc": "2026-01-02T07:15:00+00:00",
        "authority_allowed": True,
        "risk_pct": 0.25,
        "nothing": None,
        "unhashable_container": {1, 2, 3},
    }
    hash(cuts._content_key(payload))


def test_exact_content_key_separates_the_nested_differences_hcb2_missed() -> None:
    assert cuts._exact_content_key(
        {"candidate_id": "c1", "nested": {"value": 1}}
    ) != cuts._exact_content_key(
        {"candidate_id": "c1", "nested": {"value": 2}}
    )
    assert cuts._exact_content_key({"rows": [1, 2]}) != cuts._exact_content_key(
        {"rows": [2, 1]}
    )


def test_exact_content_key_is_mapping_order_insensitive_and_type_strict() -> None:
    assert cuts._exact_content_key({"a": 1, "b": [2]}) == cuts._exact_content_key(
        {"b": [2], "a": 1}
    )
    assert cuts._exact_content_key({"x": True}) != cuts._exact_content_key({"x": 1})
    assert cuts._exact_content_key({"x": 0.0}) != cuts._exact_content_key({"x": -0.0})
    # JSON treats tuple/list alike; a stricter key loses a hit but cannot be wrong.
    assert cuts._exact_content_key({"x": [1]}) != cuts._exact_content_key({"x": (1,)})


def test_exact_content_key_canonicalizes_nested_unordered_nodes() -> None:
    expected = cuts._exact_content_key({"outer": {"a": 1, "b": 2}})
    # Rebuild equal mappings and frozensets through different insertion orders. Pickle's
    # native frozenset framing is not canonical and made this exact loop intermittent.
    for keys in (("a", "b"), ("b", "a")):
        inner = {key: {"a": 1, "b": 2}[key] for key in keys}
        assert cuts._exact_content_key({"outer": inner}) == expected

    # Attribution uses `default_str=False`, where set content is semantic and
    # therefore must be canonical (FD-A1: the items are now sorted by their
    # protocol-5 framing at construction, exactly like mapping pairs).
    expected_set = cuts._exact_content_key(
        {"set": frozenset({"x", "y", "z"})}, default_str=False
    )
    for values in (("x", "y", "z"), ("z", "y", "x"), ("y", "x", "z")):
        assert (
            cuts._exact_content_key({"set": frozenset(values)}, default_str=False)
            == expected_set
        )


def test_exact_content_key_refuses_sets_under_default_str_json_semantics() -> None:
    """FD-A1 residual (a2_verify/FD_VERIFY.md new finding 1): `str(set)` renders
    in hash-table iteration order, so keying on it gave EQUAL payloads UNEQUAL
    memo keys under 7 of 64 hash seeds. A canonical key is impossible here --
    the memoised functions hash json.dumps(default=str) material, which is
    itself order-dependent for sets -- so the only stable-and-faithful answer
    is refusal, which the memo wrapper counts as a passthrough."""

    for values in ((("a", 1), ("b", 2)), (("b", 2), ("a", 1))):
        assert (
            cuts._exact_content_key({"x": frozenset(values)}, default_str=True)
            is cuts.UNKEYABLE
        )
        assert (
            cuts._exact_content_key({"x": set(values)}, default_str=True)
            is cuts.UNKEYABLE
        )
    # A set and a frozenset of the same items stay distinct content under the
    # attribution key, and both remain canonical.
    assert cuts._exact_content_key(
        {"x": frozenset({1, 2})}, default_str=False
    ) != cuts._exact_content_key({"x": {1, 2}}, default_str=False)


def test_exact_content_key_set_branch_is_stable_under_fd_a1_failing_seeds() -> None:
    """Behavioral pin of the FD-A1 repair under the exact seeds the a2_verify
    probe measured as failing (MEMO_KEY_PROBE.json: head set-branch unequal
    under {8, 13, 14, 37, 41, 47, 59}); seed 1 is the control."""

    child = (
        "import sys; sys.path.insert(0, '.');\n"
        "from src.research_infra.train_engine import cuts\n"
        "a = cuts._exact_content_key("
        "{'x': frozenset([('a', 1), ('b', 2)])}, default_str=False)\n"
        "b = cuts._exact_content_key("
        "{'x': frozenset([('b', 2), ('a', 1)])}, default_str=False)\n"
        "assert a == b and a is not cuts.UNKEYABLE, 'set keys differ'\n"
        "assert cuts._exact_content_key("
        "{'x': frozenset([('a', 1), ('b', 2)])}) is cuts.UNKEYABLE\n"
        "m1 = cuts._exact_content_key({'a': 1, 'b': [2]})\n"
        "d2 = {}; d2['b'] = [2]; d2['a'] = 1\n"
        "assert m1 == cuts._exact_content_key(d2), 'mapping keys differ'\n"
        "print(a[1].hex())\n"
    )
    digests = set()
    for seed in ("8", "47", "1"):
        result = subprocess.run(
            [sys.executable, "-c", child],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
            env={**os.environ, "PYTHONHASHSEED": seed},
            check=False,
        )
        assert result.returncode == 0, (seed, result.stderr)
        digests.add(result.stdout.strip())
    # The canonical attribution key is identical ACROSS processes and seeds.
    assert len(digests) == 1


def test_exact_content_key_refuses_unknown_attribution_objects() -> None:
    class _Mutable:
        pass

    assert (
        cuts._exact_content_key({"x": _Mutable()}, default_str=False)
        is cuts.UNKEYABLE
    )
    assert cuts._exact_content_key({"x": _Mutable()}, default_str=True) is not cuts.UNKEYABLE


def test_exact_content_key_is_fixed_size_for_a_large_payload() -> None:
    small = cuts._exact_content_key({"rows": [1]})
    large = cuts._exact_content_key({"rows": list(range(10_000))})
    assert small[0] == large[0] == "exact_content_sha256_v1"
    assert len(small[1]) == len(large[1]) == 32


# --------------------------------------------------------------------------
# the patch mechanics
# --------------------------------------------------------------------------


class _Frozen(dict):
    """Stand-in for `_FrozenPackageAuthorityPayload` (the engine caches these)."""


@pytest.fixture()
def stub_allocator(monkeypatch):
    calls: list[dict] = []

    def original(payload):
        calls.append(dict(payload))
        return f"digest-of-{sorted(payload.items(), key=lambda kv: str(kv[0]))}"

    module = types.ModuleType("src.research.moonshot_scheduler_v4_best_trade_allocator")
    module.package_new_entry_authority_payload_hash_sha256 = original
    module._FrozenPackageAuthorityPayload = _Frozen
    module._package_authority_hash_cache_key = _engine_key

    saved = {name: sys.modules.get(name) for name in cuts.HASH_SYMBOL_MODULES}
    monkeypatch.setitem(sys.modules, cuts.HASH_SYMBOL_MODULES[0], module)
    for name in cuts.HASH_SYMBOL_MODULES[1:]:
        sibling = types.ModuleType(name)
        sibling.package_new_entry_authority_payload_hash_sha256 = original
        monkeypatch.setitem(sys.modules, name, sibling)
    yield module, calls, original
    for name, value in saved.items():
        if value is not None:
            sys.modules[name] = value


def test_the_patch_rebinds_every_module_that_binds_the_symbol(stub_allocator) -> None:
    """The hot callers live in the timewarp loop and resolve the name through
    their OWN globals. Rebinding only the allocator would change nothing."""

    module, _calls, original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch()
    patch.apply()
    try:
        for name in cuts.HASH_SYMBOL_MODULES:
            rebound = getattr(sys.modules[name], cuts.HASH_ATTRIBUTE)
            assert rebound is not original, name
    finally:
        patch.revert()
    for name in cuts.HASH_SYMBOL_MODULES:
        assert getattr(sys.modules[name], cuts.HASH_ATTRIBUTE) is original, name


def test_a_repeat_of_a_logically_identical_payload_hits_and_returns_the_same_digest(
    stub_allocator,
) -> None:
    """This is the whole cut: the caller rebuilds the payload as a NEW dict each
    time (which is why AX's identity memo hit 0.11 %), so the memo must key on
    content."""

    module, calls, _original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch()
    patch.apply()
    try:
        memoised = getattr(module, cuts.HASH_ATTRIBUTE)
        first = memoised({"candidate_id": "c1", "scope": "open", "risk_pct": 0.25})
        # A NEW dict with the same content -- not the same object.
        second = memoised({"candidate_id": "c1", "scope": "open", "risk_pct": 0.25})
        assert first == second
        assert len(calls) == 1, "the underlying hash ran more than once"
    finally:
        patch.revert()
    report = cuts.cut_report()["authority_payload_hash_content"]
    assert report["calls"] == 2 and report["hits"] == 1 and report["misses"] == 1


def test_a_different_payload_misses_and_gets_its_own_digest(stub_allocator) -> None:
    module, calls, _original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch()
    patch.apply()
    try:
        memoised = getattr(module, cuts.HASH_ATTRIBUTE)
        first = memoised({"candidate_id": "c1", "risk_pct": 0.25})
        second = memoised({"candidate_id": "c1", "risk_pct": 0.50})
        assert first != second
        assert len(calls) == 2
    finally:
        patch.revert()


def test_frozen_payloads_take_the_engines_own_path_and_are_counted(
    stub_allocator,
) -> None:
    module, calls, _original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch()
    patch.apply()
    try:
        memoised = getattr(module, cuts.HASH_ATTRIBUTE)
        memoised(_Frozen({"candidate_id": "c1"}))
        memoised(_Frozen({"candidate_id": "c1"}))
    finally:
        patch.revert()
    report = cuts.cut_report()["authority_payload_hash_content"]
    assert report["frozen_passthrough"] == 2
    assert report["hits"] == 0
    assert len(calls) == 2


def test_an_unkeyable_payload_passes_through_loudly(stub_allocator) -> None:
    """Never guess. A payload the memo cannot key must take the frozen path and
    SAY so, or "the memo did nothing" becomes invisible."""

    module, calls, _original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch()
    patch.apply()
    try:
        memoised = getattr(module, cuts.HASH_ATTRIBUTE)
        memoised({"only": {"nested": 1}})  # no top-level scalar -> UNKEYABLE
        memoised({"only": {"nested": 2}})
    finally:
        patch.revert()
    report = cuts.cut_report()["authority_payload_hash_content"]
    assert report["calls"] == 2
    assert report["unkeyable_passthrough"] == 2
    assert report["hits"] == 0
    assert len(calls) == 2, "both must have reached the real hash"


def test_verify_mode_recomputes_and_counts_a_disagreement(stub_allocator) -> None:
    """The residual is measured, not argued. Force a collision and check that
    verify mode notices AND returns the true digest rather than the memo's."""

    module, _calls, _original = stub_allocator
    cuts.reset_cut_stats()
    patch = cuts.make_authority_hash_content_memo_patch(verify=True)
    patch.apply()
    try:
        memoised = getattr(module, cuts.HASH_ATTRIBUTE)
        first = memoised({"candidate_id": "c1", "nested": {"v": 1}})
        # Same memo key (nested-only difference), different true digest.
        second = memoised({"candidate_id": "c1", "nested": {"v": 2}})
        assert second != first, "verify mode must return the TRUE digest"
    finally:
        patch.revert()
    report = cuts.cut_report()["authority_payload_hash_content"]
    assert report["verified"] == 1
    assert report["mismatches"] == 1
    assert report["mismatch_examples"]


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------


@pytest.fixture()
def stub_proof_hash_modules(monkeypatch):
    """Stubs for the four `json.dumps` + sha256 proof-hash functions."""

    calls: dict[str, int] = {}
    saved = {name: sys.modules.get(name) for name, _ in cuts.PROOF_HASH_TARGETS}
    modules = {}
    for module_name, attribute in cuts.PROOF_HASH_TARGETS:

        def original(payload, *, _name=f"{module_name}.{attribute}"):
            calls[_name] = calls.get(_name, 0) + 1
            # A digest that depends on the FULL payload, nested content included
            # -- that is what makes a shallow-key collision observable.
            return f"{_name}:{json.dumps(payload, sort_keys=True, default=str)}"

        module = modules.get(module_name) or types.ModuleType(module_name)
        setattr(module, attribute, original)
        modules[module_name] = module
        monkeypatch.setitem(sys.modules, module_name, module)
    yield modules, calls
    for name, value in saved.items():
        if value is not None:
            sys.modules[name] = value


def test_each_proof_hash_gets_its_own_memo_so_digests_never_cross(
    stub_proof_hash_modules,
) -> None:
    """The four bodies are identical today. If one memo served all of them, a
    `_packet_hash` digest could be returned for a `_selector_hash_digest` call
    and nothing would notice."""

    modules, _calls = stub_proof_hash_modules
    cuts.reset_cut_stats()
    patch = cuts.make_proof_hash_content_memo_patch()
    patch.apply()
    try:
        payload = {"candidate_id": "c1", "score": 0.5}
        digests = {
            attribute: getattr(modules[module_name], attribute)(dict(payload))
            for module_name, attribute in cuts.PROOF_HASH_TARGETS
        }
        assert len(set(digests.values())) == len(cuts.PROOF_HASH_TARGETS)
    finally:
        patch.revert()


def test_the_proof_hash_memo_hits_on_a_rebuilt_equal_payload(
    stub_proof_hash_modules,
) -> None:
    modules, calls = stub_proof_hash_modules
    cuts.reset_cut_stats()
    patch = cuts.make_proof_hash_content_memo_patch()
    patch.apply()
    try:
        module_name, attribute = cuts.PROOF_HASH_TARGETS[0]
        fn = getattr(modules[module_name], attribute)
        first = fn({"candidate_id": "c1", "score": 0.5})
        second = fn({"candidate_id": "c1", "score": 0.5})
        assert first == second
        assert calls[f"{module_name}.{attribute}"] == 1
    finally:
        patch.revert()
    report = cuts.cut_report()[f"{module_name.rsplit('.', 1)[-1]}.{attribute}"]
    assert report["hits"] == 1 and report["misses"] == 1


def test_the_proof_hash_memo_refuses_a_payload_with_no_top_level_scalar(
    stub_proof_hash_modules,
) -> None:
    """The exposure is higher here than for the structured authority payload:
    these take arbitrary payloads, so a pure-shape key must refuse."""

    modules, calls = stub_proof_hash_modules
    cuts.reset_cut_stats()
    patch = cuts.make_proof_hash_content_memo_patch()
    patch.apply()
    try:
        module_name, attribute = cuts.PROOF_HASH_TARGETS[0]
        fn = getattr(modules[module_name], attribute)
        first = fn({"nested": {"v": 1}})
        second = fn({"nested": {"v": 2}})
        assert first != second, "a refused key must not serve a stale digest"
        assert calls[f"{module_name}.{attribute}"] == 2
    finally:
        patch.revert()
    report = cuts.cut_report()[f"{module_name.rsplit('.', 1)[-1]}.{attribute}"]
    assert report["unkeyable_passthrough"] == 2


def test_the_proof_hash_memo_reverts_every_target(stub_proof_hash_modules) -> None:
    modules, _calls = stub_proof_hash_modules
    before = {
        (m, a): getattr(modules[m], a) for m, a in cuts.PROOF_HASH_TARGETS
    }
    patch = cuts.make_proof_hash_content_memo_patch()
    patch.apply()
    assert all(
        getattr(modules[m], a) is not before[(m, a)] for m, a in cuts.PROOF_HASH_TARGETS
    )
    patch.revert()
    assert all(
        getattr(modules[m], a) is before[(m, a)] for m, a in cuts.PROOF_HASH_TARGETS
    )


@pytest.mark.parametrize(
    "patch_id",
    [
        "selector_hash_content_memo_v2",
        "timewarp_hash_content_memo_v2",
        "probability_hash_content_memo_v2",
    ],
)
def test_each_v2_hash_memo_hits_equal_nested_content_and_misses_mutation(
    stub_proof_hash_modules, patch_id
) -> None:
    modules, calls = stub_proof_hash_modules
    module_name, attribute, report_name = cuts.SPLIT_HASH_MEMO_TARGETS[patch_id]
    cuts.reset_cut_stats()
    patch = cuts.make_split_hash_content_memo_patch(patch_id, verify=True)
    patch.apply()
    try:
        fn = getattr(modules[module_name], attribute)
        first = fn({"candidate_id": "c1", "nested": {"v": 1}})
        # The key is allowed to be stricter than JSON and lose a hit when map
        # insertion order differs. It must hit identical typed content in the
        # stable producer order and must never hit mutated nested content.
        same = fn({"candidate_id": "c1", "nested": {"v": 1}})
        changed = fn({"candidate_id": "c1", "nested": {"v": 2}})
        assert first == same
        assert changed != first
    finally:
        patch.revert()
    assert calls[f"{module_name}.{attribute}"] == 3  # miss, verified hit, miss
    report = cuts.cut_report()[report_name]
    assert report["verified"] == 1
    assert report["mismatches"] == 0


def test_attribution_v2_key_invalidates_an_in_place_nested_splice(monkeypatch) -> None:
    module_name = "src.research_infra.v4_timewarp_simulated_live_research_loop"
    calls = 0

    def original(*surfaces, prefix="", validate_against_outer_projection=True):
        nonlocal calls
        calls += 1
        return {
            f"{prefix}value": surfaces[0]["nested"]["value"],
            "validated": validate_against_outer_projection,
        }

    module = types.ModuleType(module_name)
    module.package_new_entry_authority_attribution_fields = original
    monkeypatch.setitem(sys.modules, module_name, module)
    cuts.reset_cut_stats()
    patch = cuts.make_attribution_fields_content_memo_patch(verify=True)
    patch.apply()
    surface = {"nested": {"value": 1}}
    try:
        assert module.package_new_entry_authority_attribution_fields(surface)["value"] == 1
        assert module.package_new_entry_authority_attribution_fields(surface)["value"] == 1
        surface["nested"]["value"] = 2
        assert module.package_new_entry_authority_attribution_fields(surface)["value"] == 2
    finally:
        patch.revert()
    assert calls == 3  # miss, verified hit, mutation miss
    report = cuts.cut_report()["attribution_fields_content_memo"]
    assert report["verified"] == 1 and report["mismatches"] == 0


def test_attribution_v2_returns_fresh_nested_output_on_a_hit(monkeypatch) -> None:
    module_name = "src.research_infra.v4_timewarp_simulated_live_research_loop"

    def original(*surfaces, prefix="", validate_against_outer_projection=True):
        del surfaces, prefix, validate_against_outer_projection
        return {"failures": ["original"]}

    module = types.ModuleType(module_name)
    module.package_new_entry_authority_attribution_fields = original
    monkeypatch.setitem(sys.modules, module_name, module)
    cuts.reset_cut_stats()
    patch = cuts.make_attribution_fields_content_memo_patch()
    patch.apply()
    try:
        first = module.package_new_entry_authority_attribution_fields({"value": 1})
        first["failures"].append("caller-mutation")
        second = module.package_new_entry_authority_attribution_fields({"value": 1})
    finally:
        patch.revert()
    assert second == {"failures": ["original"]}


def test_the_installer_carries_ax_patches_plus_this_lanes_cut() -> None:
    installer = cuts.build_installer()
    assert "authority_hash_content_memo" in installer.registered
    assert "proof_hash_content_memo" in installer.registered
    assert "ledger_scalar_projection" in installer.registered
    assert "missed_pool_projection" in installer.registered
    assert "semantic_sidecar_projection" in installer.registered
    assert cuts.HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID in installer.registered
    for patch_id in cuts.SPLIT_HASH_MEMO_TARGETS:
        assert patch_id in installer.registered
    assert "attribution_fields_content_memo_v2" in installer.registered
    for inherited in (
        "abc_concrete_types",
        "attribution_fields_identity_memo",
        "skip_post_hoc_ledger_recertification",
        "gc_during_chunk",
    ):
        assert inherited in installer.registered


def test_an_unknown_cut_id_refuses_rather_than_running_a_silent_baseline() -> None:
    installer = cuts.build_installer()
    with pytest.raises(ValueError):
        installer.install(["not_a_real_cut"])


def test_resolve_patches_distinguishes_default_from_baseline_from_explicit() -> None:
    assert cuts.resolve_patches(None) == list(cuts.TRAIN_DEFAULT_PATCHES)
    assert cuts.resolve_patches("safe") == list(cuts.TRAIN_SAFE_SET_PATCHES)
    assert cuts.resolve_patches("hcb2-safe") == list(cuts.HCB2_COMPUTE_SAFE_PATCHES)
    assert cuts.resolve_patches("safe+hard-eligibility-observability") == [
        *cuts.TRAIN_SAFE_SET_PATCHES,
        cuts.HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID,
    ]
    assert cuts.resolve_patches(
        "hard_eligibility_observability,ledger_scalar_projection"
    ) == [
        "ledger_scalar_projection",
        cuts.HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID,
    ]
    assert cuts.resolve_patches("none") == []
    assert cuts.resolve_patches("") == []
    assert cuts.resolve_patches("abc_concrete_types") == ["abc_concrete_types"]


def test_sequence_is_not_in_the_zero_mismatch_abc_surface() -> None:
    """H-CB-2 measured 47,444,764 wrong string checks under the broad rebind."""

    assert cuts.TRAIN_ABC_SYMBOLS == ("Mapping", "MutableMapping")


# --------------------------------------------------------------------------
# the output projections
# --------------------------------------------------------------------------


def _exercise_append_patch(monkeypatch, patch, path: Path, rows: list[dict]):
    observed: list[dict] = []

    class _Attempt:
        @staticmethod
        def append_jsonl(_path, stream):
            materialized = list(stream)
            observed.extend(materialized)
            return len(materialized)

    original_module = cuts.accel._module
    monkeypatch.setattr(cuts.accel, "_module", lambda _name: _Attempt)
    try:
        patch.apply()
        assert _Attempt.append_jsonl(path, iter(rows)) == len(rows)
        patch.revert()
    finally:
        monkeypatch.setattr(cuts.accel, "_module", original_module)
    return observed


def test_scalar_projection_keeps_scalars_and_named_containers(monkeypatch, tmp_path) -> None:
    rows = [{"scalar": 1, "text": "x", "nested": {"large": [1, 2]}}]
    observed = _exercise_append_patch(
        monkeypatch,
        cuts.make_ledger_projection_patch(),
        tmp_path / "P_DECISION_LEDGER.jsonl",
        rows,
    )
    assert observed == [
        {
            "scalar": 1,
            "text": "x",
            "train_lane_ledger_projection": cuts.LEDGER_PROJECTION_STAMP,
        }
    ]


def test_scalar_projection_leaves_undeclared_ledgers_whole(monkeypatch, tmp_path) -> None:
    row = {"nested": {"must": "remain"}}
    observed = _exercise_append_patch(
        monkeypatch,
        cuts.make_ledger_projection_patch(),
        tmp_path / "P_TRADE_LEDGER.jsonl",
        [row],
    )
    assert observed == [row]


def _factorial_scorecard_row() -> dict:
    instance_keys = [
        "candidate-a@@2026-01-02T08:00:00+00:00",
        "candidate-b@@2026-01-02T08:00:00+00:00",
    ]
    option_rows = [
        {
            "candidate_id": key.split("@@", 1)[0],
            "decision_time_utc": key.split("@@", 1)[1],
            "canonical_replay_candidate_instance_key": key,
            "b7_5_selection_sizing_factorial_hard_eligible": True,
            "b7_5_selection_sizing_factorial_neutral_rank_sha256": char * 64,
            "selected": char == "b",
        }
        for key, char in zip(instance_keys, ("a", "b"))
    ]
    return {
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "b7_5_selection_sizing_factorial_arm_id": "S0R0",
        cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER: {
            "b7_5_selection_sizing_factorial_hard_eligible_pool_count": 2,
            "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256": (
                cuts._hard_eligibility_digest(instance_keys)
            ),
            "b7_5_selection_sizing_factorial_hard_eligible_instance_keys": (
                instance_keys
            ),
            "b7_5_factorial_hard_eligible_option_rows": option_rows,
        },
    }


def test_hard_eligibility_observability_lifts_exact_producer_fields() -> None:
    source = _factorial_scorecard_row()
    projected = cuts.project_hard_eligibility_observability_row(source)
    nested = source[cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER]

    for field in cuts.HARD_ELIGIBILITY_REQUIRED_FIELDS:
        assert projected[field] == nested[field]
    assert projected["train_lane_hard_eligibility_observability"] == (
        cuts.HARD_ELIGIBILITY_OBSERVABILITY_STAMP
    )
    assert projected["train_lane_hard_eligibility_observability_status"] == (
        "EXACT_FACTORIAL_HARD_POOL_EMITTED"
    )
    assert projected[
        "train_lane_hard_eligibility_observability_count_reconciled"
    ] is True
    assert projected[
        "train_lane_hard_eligibility_observability_digest_reconciled"
    ] is True

    nested["b7_5_selection_sizing_factorial_hard_eligible_instance_keys"].append(
        "later-mutation"
    )
    assert len(
        projected["b7_5_selection_sizing_factorial_hard_eligible_instance_keys"]
    ) == 2


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (
            lambda source: source.__setitem__(
                "b7_5_selection_sizing_factorial_hard_eligible_pool_count", 3
            ),
            "count_mismatch",
        ),
        (
            lambda source: source.__setitem__(
                "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256",
                "0" * 64,
            ),
            "digest_mismatch",
        ),
        (
            lambda source: source[
                "b7_5_factorial_hard_eligible_option_rows"
            ][0].__setitem__(
                "canonical_replay_candidate_instance_key",
                "wrong@@2026-01-02T08:00:00+00:00",
            ),
            "option_key_set_mismatch",
        ),
    ],
)
def test_hard_eligibility_observability_fails_closed_on_inconsistent_source(
    mutation, error
) -> None:
    row = _factorial_scorecard_row()
    mutation(row[cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER])
    with pytest.raises(ValueError, match=error):
        cuts.project_hard_eligibility_observability_row(row)


def test_hard_eligibility_observability_distinguishes_nonfactorial_and_missing() -> None:
    nonfactorial = cuts.project_hard_eligibility_observability_row(
        {cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER: {"status": "materialized"}}
    )
    assert nonfactorial[
        "train_lane_hard_eligibility_observability_status"
    ] == "NOT_FACTORIAL_BOUND"
    missing = cuts.project_hard_eligibility_observability_row({"scalar": 1})
    assert missing[
        "train_lane_hard_eligibility_observability_status"
    ] == "SOURCE_CONTAINER_MISSING"
    with pytest.raises(ValueError, match="factorial_source_container_missing"):
        cuts.project_hard_eligibility_observability_row(
            {"b7_5_selection_sizing_factorial_arm_id": "S0R0"}
        )


def _exercise_hard_observability_patch_stack(
    monkeypatch, tmp_path, patch_factories
) -> dict:
    observed: list[dict] = []

    class _Attempt:
        @staticmethod
        def append_jsonl(_path, stream):
            materialized = list(stream)
            observed.extend(materialized)
            return len(materialized)

    patches = [factory() for factory in patch_factories]
    original_module = cuts.accel._module
    monkeypatch.setattr(cuts.accel, "_module", lambda _name: _Attempt)
    try:
        for patch in patches:
            patch.apply()
        assert _Attempt.append_jsonl(
            tmp_path / "P_SCORECARD_LEDGER.jsonl",
            iter([_factorial_scorecard_row()]),
        ) == 1
    finally:
        for patch in reversed(patches):
            patch.revert()
        monkeypatch.setattr(cuts.accel, "_module", original_module)
    assert cuts._HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE == 0
    return observed[0]


@pytest.mark.parametrize(
    "patch_factories",
    [
        (
            cuts.make_ledger_projection_patch,
            cuts.make_hard_eligibility_observability_patch,
        ),
        (
            cuts.make_hard_eligibility_observability_patch,
            cuts.make_ledger_projection_patch,
        ),
    ],
)
def test_hard_observability_composes_with_scalar_projection_in_either_order(
    monkeypatch, tmp_path, patch_factories
) -> None:
    observed = _exercise_hard_observability_patch_stack(
        monkeypatch, tmp_path, patch_factories
    )
    assert cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER not in observed
    assert observed["b7_5_selection_sizing_factorial_hard_eligible_pool_count"] == 2
    assert len(
        observed["b7_5_selection_sizing_factorial_hard_eligible_instance_keys"]
    ) == 2
    assert len(observed["b7_5_factorial_hard_eligible_option_rows"]) == 2
    assert observed["train_lane_ledger_projection"] == cuts.LEDGER_PROJECTION_STAMP
    assert observed["train_lane_hard_eligibility_observability"] == (
        cuts.HARD_ELIGIBILITY_OBSERVABILITY_STAMP
    )


def test_hard_observability_is_default_off_and_scalar_shape_is_unchanged(
    monkeypatch, tmp_path
) -> None:
    patch = cuts.make_hard_eligibility_observability_patch()
    assert patch.default_on is False
    assert patch.sealed_compatible is False
    assert patch.patch_id not in cuts.TRAIN_SAFE_SET_PATCHES
    assert patch.patch_id not in cuts.TRAIN_DEFAULT_PATCHES

    observed = _exercise_append_patch(
        monkeypatch,
        cuts.make_ledger_projection_patch(),
        tmp_path / "P_SCORECARD_LEDGER.jsonl",
        [_factorial_scorecard_row()],
    )[0]
    assert cuts.HARD_ELIGIBILITY_SOURCE_CONTAINER not in observed
    assert all(field not in observed for field in cuts.HARD_ELIGIBILITY_REQUIRED_FIELDS)
    assert "train_lane_hard_eligibility_observability" not in observed


def test_missed_projection_derives_every_aw_reader_field() -> None:
    from src.research_infra import b7_5_diagnostic_pool as pool

    keep = cuts._missed_keep_names()
    for field in (*pool.PROJECTION, *pool.OUTCOME_PROJECTION):
        if not field.source.startswith("derived:"):
            assert field.source.split(".", 1)[0] in keep, field.source
    for fields in cuts.MISSED_POOL_LITERAL_READERS.values():
        assert fields <= keep


def test_missed_projection_repairs_cds_missing_identity_and_outcomes(
    monkeypatch, tmp_path
) -> None:
    row = {
        "canonical_replay_candidate_instance_key": "c@@2026-01-02T00:00:00+00:00",
        "candidate_decision_quality": {"entry_quality_fill_probability": 0.5},
        "opportunity_net_proxy_r": -1.0,
        "opportunity_gross_r": -0.5,
        "opportunity_close_reason": "stop",
        "terminal_outcome": "stop_reached_before_target",
        "counterfactual_order_close_time_utc": "2026-01-02T01:00:00+00:00",
        "missed_opportunity_headline_r_scoreable": False,
        "unused_proof_envelope": {"large": [1, 2, 3]},
    }
    observed = _exercise_append_patch(
        monkeypatch,
        cuts.make_missed_pool_projection_patch(),
        tmp_path / "P_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [row],
    )[0]
    for field in (
        "canonical_replay_candidate_instance_key",
        "candidate_decision_quality",
        "opportunity_net_proxy_r",
        "opportunity_gross_r",
        "opportunity_close_reason",
        "terminal_outcome",
        "counterfactual_order_close_time_utc",
        "missed_opportunity_headline_r_scoreable",
    ):
        assert observed[field] == row[field]
    assert "unused_proof_envelope" not in observed
    assert observed["train_lane_missed_projection"] == cuts.MISSED_POOL_PROJECTION_STAMP


def test_missed_projection_preserves_exact_capture_and_binds_the_authoritative_exit() -> None:
    base = {
        "candidate_id": "candidate-1",
        "counterfactual_order_fill_status": "filled_from_ordered_tick_path",
        "counterfactual_order_fill_time_utc": "2026-01-21T13:01:00+00:00",
        "counterfactual_order_fill_price": 4400.0,
        "counterfactual_order_close_time_utc": "2026-01-21T15:00:00+00:00",
        "opportunity_path_scored": True,
        "opportunity_gross_r": 0.75,
        "opportunity_close_reason": "selected_policy_replay:momentum_exhaustion",
        "terminal_outcome": "momentum_exhaustion",
        "path_source": "tick",
        "path_index_source_path": "/evidence/XAUUSD/ticks.jsonl",
        "path_index_source_sha256": "a" * 64,
        "ordered_tick_truth_satisfied": True,
        "selected_execution_policy_replay_bound": True,
        "selected_execution_policy_replay_exit_time_utc": (
            "2026-01-21T14:15:00+00:00"
        ),
        "profit_harvest_applied_to_terminal": False,
        "unused_transport_envelope": {"large": [1, 2, 3]},
    }
    selected = cuts.project_missed_pool_row(base)
    assert selected["counterfactual_order_fill_status"].startswith("filled")
    assert selected["counterfactual_order_fill_time_utc"].endswith("+00:00")
    assert selected["counterfactual_order_fill_price"] == 4400.0
    assert selected["opportunity_gross_r"] == 0.75
    assert selected["path_index_source_sha256"] == "a" * 64
    assert selected["opportunity_close_time_utc"] == (
        "2026-01-21T14:15:00+00:00"
    )
    assert selected["opportunity_close_time_source"] == "selected_execution_policy"
    assert "unused_transport_envelope" not in selected

    harvested = cuts.project_missed_pool_row(
        {
            **base,
            "profit_harvest_applied_to_terminal": True,
            "profit_harvest_policy_close_time_utc": "2026-01-21T13:45:00+00:00",
        }
    )
    assert harvested["opportunity_close_time_utc"] == "2026-01-21T13:45:00+00:00"
    assert harvested["opportunity_close_time_source"] == "profit_harvest_policy"

    raw = cuts.project_missed_pool_row(
        {
            **base,
            "selected_execution_policy_replay_bound": False,
        }
    )
    assert raw["opportunity_close_time_utc"] == "2026-01-21T15:00:00+00:00"
    assert raw["opportunity_close_time_source"] == "counterfactual_order_path"


def test_semantic_sidecar_projection_keeps_one_disclosed_row_and_zero_fields(
    monkeypatch, tmp_path
) -> None:
    row = {
        "schema": "sealed-semantic-schema",
        "sidecar_payload_canonical_json": "x" * 1000,
        "state_projection": {"huge": [1, 2, 3]},
    }
    observed = _exercise_append_patch(
        monkeypatch,
        cuts.make_semantic_sidecar_projection_patch(),
        tmp_path / "P_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
        [row],
    )
    assert observed == [
        {"train_lane_semantic_projection": cuts.SEMANTIC_SIDECAR_PROJECTION_STAMP}
    ]
    assert all(not fields for fields in cuts.SEMANTIC_SIDECAR_FIELD_READERS.values())


def test_every_default_projection_declares_sealed_incompatibility() -> None:
    for patch in (
        cuts.make_ledger_projection_patch(),
        cuts.make_missed_pool_projection_patch(),
        cuts.make_semantic_sidecar_projection_patch(),
    ):
        assert patch.patch_id in cuts.TRAIN_DEFAULT_PATCHES
        assert patch.default_on is True
        assert patch.sealed_compatible is False


def test_repaired_memos_stay_off_when_the_exact_key_is_net_negative() -> None:
    assert "proof_hash_content_memo" not in cuts.TRAIN_SAFE_SET_PATCHES
    assert "attribution_fields_identity_memo" not in cuts.TRAIN_SAFE_SET_PATCHES
    assert "ultimate_packet_hash_content_memo" in cuts.TRAIN_SAFE_SET_PATCHES
    for patch_id in (
        "selector_hash_content_memo_v2",
        "timewarp_hash_content_memo_v2",
        "attribution_fields_content_memo_v2",
    ):
        assert patch_id not in cuts.TRAIN_SAFE_SET_PATCHES
    # Exact content produced no repeat key on the commissioned fixture.  The
    # old memo's 8,810 apparent hits were therefore collisions, not reusable
    # work; zero mismatches over zero hits cannot license a default-on cut.
    assert "probability_hash_content_memo_v2" not in cuts.TRAIN_SAFE_SET_PATCHES
    assert cuts.TRAIN_DEFAULT_PATCHES == cuts.TRAIN_SAFE_SET_PATCHES

def test_missed_projection_stamps_the_expectancy_ev_alias_and_counts_disagreement() -> None:
    """R-SCHEMA dedup: `expectancy_r` was byte-equal to `candidate_ev_r` on
    8,448/8,448 fence MISSED rows. The field is kept (readers exist); the
    stamp names the alias, and a disagreement is counted in the cut report
    because it would be a finding."""

    stats = cuts.CUT_STATS.setdefault(
        cuts.EXPECTANCY_ALIAS_STATS_NAME, cuts._CutStats()
    )
    calls0, hits0, mismatches0 = stats.calls, stats.hits, stats.mismatches

    equal = cuts.project_missed_pool_row(
        {
            "candidate_id": "candidate-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
            "expectancy_r": 0.7650724,
            "candidate_ev_r": 0.7650724,
        }
    )
    assert equal["expectancy_r_is_candidate_ev_r_alias"] is True
    assert equal["expectancy_r"] == 0.7650724
    assert equal["candidate_ev_r"] == 0.7650724

    unequal = cuts.project_missed_pool_row(
        {
            "candidate_id": "candidate-2",
            "decision_time_utc": "2026-01-02T08:15:00+00:00",
            "expectancy_r": 0.7650724,
            "candidate_ev_r": 0.5,
        }
    )
    assert unequal["expectancy_r_is_candidate_ev_r_alias"] is False

    absent = cuts.project_missed_pool_row(
        {"candidate_id": "candidate-3", "expectancy_r": 0.7650724}
    )
    assert "expectancy_r_is_candidate_ev_r_alias" not in absent

    assert stats.calls == calls0 + 2
    assert stats.hits == hits0 + 1
    assert stats.mismatches == mismatches0 + 1
    assert any(
        example.get("candidate_id") == "candidate-2"
        for example in stats.mismatch_examples
    )

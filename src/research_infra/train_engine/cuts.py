"""CB-2 -- the dataflow cut: compute what a decision reads, and nothing else.

Runtime rebinds into already-imported frozen modules. **No bound file's bytes
change**, so R2's input-binding drift check and the execution-seal digest are
both untouched (CLAUDE.md H1) -- the same discipline `fast_engine.accel`
established, and this module reuses its `Installer` rather than growing a second
patch mechanism.

## The trap, and the way past it

AX measured that the expensive machinery is **called by the decision**:
`finalize_scheduler_risk_admitted_selection` -- the B7.5 selection factor itself
-- reaches `package_new_entry_authority_attribution_fields` (288.4 s, 26.2 % of
wall), which reaches `signed_envelope_failures` (269.0 s), which reaches
`package_new_entry_authority_payload_hash_sha256` (210.4 s, 19.1 %). So "turn
the evidence off" is not available: a decision reads whether that envelope
validated.

Reading the code rather than the profile says what IS available. Both
`signed_envelope_failures` (`v4_timewarp:12072`) and
`package_new_entry_authority_immutable_payload_failures` (`v4_timewarp:16291`)
hash the SAME payload object independently, per surface, per candidate, and
`envelope_surfaces` walks nested surfaces recursively -- 5,902 hashes per
candidate, 52.0 M on a two-day fixture. **The repetition is logical, not
referential**, which is exactly why AX's identity memo hit 0.11 %: the caller
rebuilds the payload as a new dict every time.

So the cut is a **content-addressed** memo, and the content key is the one the
engine already computes for itself and then throws away.
`package_new_entry_authority_payload_hash_sha256`
(`moonshot_scheduler_v4_best_trade_allocator.py:897-937`) computes a cheap
13-field `_package_authority_hash_cache_key`, and then computes
`_stable_sha256_material(payload)` -- the recursive canonicalisation plus
`json.dumps` that IS the expense -- **before** consulting the cache, purely to
validate the hit. Its cache therefore saves the SHA-256 and none of the cost.

AX filed trusting that key as H-AX-0 direction 2: *"at a stated, quantifiable
collision risk. That is a contract-level decision, not an implementation one."*
**In the training lane it is mine to make**, because this lane's acceptance test
is trade-outcome identity rather than provenance identity, and because the risk
is measurable rather than argued: `verify` mode computes the true digest on
every hit and counts disagreements.

The key shipped here is deliberately **stronger than the engine's own**. The
engine's 13 fields plus every top-level scalar item of the payload: a collision
now needs two payloads agreeing on every scalar they carry and differing only
inside a nested container. It is a shallow scan -- no recursion, no sort of
nested structure, no `json.dumps` -- so it stays far below the cost it replaces.

## What this module projects, and why

The missed-opportunity rows stay, but their 670-field transport envelope does
not. The lane keeps the complete declared input surface of AW's reader and the
matrix analyzer, plus repair provenance and the compact executable-capture
contract needed to turn a missed candidate into an exact fill/no-fill record,
and stamps every projected row. The
semantic-diagnostic sidecar has no field-reading lane consumer at all; it keeps
one stamped row per producer row so row-count telemetry stays honest. These are
training-lane projections only and are marked sealed-incompatible. The frozen
producer and every sealed path remain untouched.
"""

from __future__ import annotations

import collections
import copy
from dataclasses import dataclass
import hashlib
import json
import math
import pickle
from typing import Any, Mapping

from src.research_infra.fast_engine import accel
from src.research_infra.train_engine import decision_semantics

#: Modules that bind the hash symbol by name (`rg -l` over `src/`). A rebind has
#: to reach every one: the hot callers live in the timewarp loop and resolve the
#: name through their OWN module globals, not the allocator's.
HASH_SYMBOL_MODULES = (
    "src.research.moonshot_scheduler_v4_best_trade_allocator",
    "src.research_infra.v4_timewarp_simulated_live_research_loop",
    "src.components.selector_v4",
)
HASH_ATTRIBUTE = "package_new_entry_authority_payload_hash_sha256"

#: Unbounded would be a leak; too small and the memo thrashes across the day.
#: 52.0 M calls over 8,812 candidates is ~5,900 per candidate, and a candidate's
#: surfaces are walked within one decision, so the working set is small. 65,536
#: entries of (key -> 64-char digest) is a few tens of MB and comfortably above
#: it. Eviction is LRU, and the counters report evictions so a wrong guess shows
#: up as a falling hit rate instead of as silence.
HASH_MEMO_MAX_ENTRIES = 65_536
EXACT_CONTENT_MEMO_MAX_ENTRIES = 16_384


@dataclass
class _CutStats:
    calls: int = 0
    hits: int = 0
    misses: int = 0
    frozen_passthrough: int = 0
    unkeyable_passthrough: int = 0
    evictions: int = 0
    verified: int = 0
    mismatches: int = 0
    mismatch_examples: tuple = ()


CUT_STATS: dict[str, _CutStats] = {}


def cut_report() -> dict[str, Any]:
    """Counters for every train-lane cut. Always reported, not only under verify.

    The hit rate is the explanation for whatever the wall-clock shows; AX's
    session turned on the fact that a memo can be correct and useless, and the
    only way anyone found out was that it counted itself.
    """

    report = {
        name: {
            "calls": s.calls,
            "hits": s.hits,
            "misses": s.misses,
            "hit_rate": round(s.hits / s.calls, 6) if s.calls else 0.0,
            "frozen_passthrough": s.frozen_passthrough,
            "unkeyable_passthrough": s.unkeyable_passthrough,
            "evictions": s.evictions,
            "verified": s.verified,
            "mismatches": s.mismatches,
            "mismatch_examples": list(s.mismatch_examples),
        }
        for name, s in CUT_STATS.items()
    }
    from src.research_infra.train_engine import resident_event_sink

    report["train_resident_event_sink"] = resident_event_sink.report()
    return report


def reset_cut_stats() -> None:
    CUT_STATS.clear()
    from src.research_infra.train_engine import resident_event_sink

    resident_event_sink.reset_stats()


#: Sentinel: this payload cannot be keyed cheaply and must take the frozen path.
#: Returned rather than raised because "refuse to memo" is a normal outcome that
#: has to be COUNTED, not an error.
UNKEYABLE = object()


def _content_key(payload: Any) -> Any:
    """A shallow content key: every top-level scalar, plus container SHAPE.

    Shallow by construction -- that is what makes it affordable, and it is the
    whole of the residual. Two payloads agreeing on every top-level scalar AND
    on the name/type/length of every top-level container, differing only inside
    a container, produce the same key. `verify` mode measures exactly that.

    `frozenset` rather than a sorted tuple: an O(n) build with no comparison
    sort, and dict keys are unique so nothing is lost. Measured at 1.23 % of
    wall as a sorted tuple on the first train run, which is why it is worth
    doing properly.

    Returns `UNKEYABLE` when the key would be too weak to trust:

    * a payload that carries **containers but no scalar at all** -- the key
      would be pure shape, which is not evidence of anything;
    * a non-mapping payload -- `json.dumps` of a scalar or a short list is
      already cheap, so there is nothing to buy and a list key would be a
      guess.

    A payload with **neither** scalars nor containers (`{}`) is keyed, not
    refused: the key `(0, frozenset(), frozenset())` determines its content
    completely. Refusing it cost 3,433,381 fallback calls -- 11.8 % of the
    authority hash's traffic on the 2-day fixture -- and bought nothing, which
    is exactly the sort of thing a counter finds and an argument does not.

    Refusing is always safe: it costs one frozen call.
    """

    if type(payload) is not dict and not isinstance(payload, Mapping):
        return UNKEYABLE
    scalars: list[tuple[Any, str, Any]] = []
    shapes: list[tuple[Any, str, int]] = []
    for key, value in payload.items():
        # `bool` is an `int` in Python; keep the type name so True and 1 differ.
        if value is None or isinstance(value, (str, int, float, bool)):
            scalars.append((key, type(value).__name__, value))
        else:
            try:
                shapes.append((key, type(value).__name__, len(value)))
            except TypeError:
                shapes.append((key, type(value).__name__, -1))
    if shapes and not scalars:
        return UNKEYABLE
    try:
        return (len(payload), frozenset(scalars), frozenset(shapes))
    except TypeError:  # an unhashable key or scalar; never guess
        return UNKEYABLE


def _exact_content_key(payload: Any, *, default_str: bool = True) -> Any:
    """An exact, recursively immutable content key without JSON materialization.

    Barring a SHA-256 collision, equality of two returned keys implies equality
    of the corresponding typed frozen content and therefore of
    ``json.dumps(..., sort_keys=True, default=str)`` material for the native JSON
    types used by the hash functions. The frozen form is deliberately stricter
    where Python and JSON collapse types (tuple/list, integer/string mapping
    keys), so it can lose hits. Verify mode measures the collision boundary on
    every hit before promotion.

    Unknown leaf objects are keyed by their fully qualified type and ``str``
    only for hash functions, whose frozen serializer uses exactly
    ``default=str``. Attribution-field memoization passes ``default_str=False``
    and refuses such surfaces because that function can inspect Python objects
    rather than their JSON representation.
    """

    active: set[int] = set()

    def freeze(value: Any) -> Any:
        if value is None:
            return ("none",)
        if isinstance(value, bool):
            return ("bool", value)
        if isinstance(value, int):
            return ("int", value)
        if isinstance(value, float):
            # `0.0 == -0.0`, but json.dumps distinguishes them.
            return ("float", repr(value))
        if isinstance(value, str):
            return ("str", value)
        if isinstance(value, bytes):
            if not default_str:
                return ("bytes", value)
            return ("default_str", "builtins.bytes", str(value))

        if isinstance(value, Mapping):
            identity = id(value)
            if identity in active:
                return UNKEYABLE
            active.add(identity)
            try:
                items = []
                for key, item in value.items():
                    frozen_key = freeze(key)
                    frozen_item = freeze(item)
                    if frozen_key is UNKEYABLE or frozen_item is UNKEYABLE:
                        return UNKEYABLE
                    items.append((frozen_key, frozen_item))
                try:
                    # A frozenset compares independent of insertion order, but
                    # its pickle byte order is not canonical.  Because the final
                    # fixed-size key hashes that pickle, equal mappings could
                    # intermittently receive different memo keys.  Sort the
                    # already typed frozen pairs by their protocol-5 framing so
                    # unlike Python values never need to compare directly.
                    content = tuple(
                        sorted(
                            items,
                            key=lambda item: pickle.dumps(item, protocol=5),
                        )
                    )
                except (
                    AttributeError,
                    OverflowError,
                    pickle.PickleError,
                    TypeError,
                    ValueError,
                ):
                    return UNKEYABLE
                # A non-dict Mapping may reach json.dumps.default; including its
                # string makes this key stricter while retaining its content for
                # attribution semantics.
                mapping_tag = (
                    "dict"
                    if isinstance(value, dict)
                    else f"{type(value).__module__}.{type(value).__qualname__}:"
                    f"{str(value)}"
                )
                return ("mapping", mapping_tag, len(value), content)
            finally:
                active.remove(identity)

        if isinstance(value, (list, tuple)):
            identity = id(value)
            if identity in active:
                return UNKEYABLE
            active.add(identity)
            try:
                items = tuple(freeze(item) for item in value)
                if any(item is UNKEYABLE for item in items):
                    return UNKEYABLE
                return (type(value).__name__, items)
            finally:
                active.remove(identity)

        if isinstance(value, (set, frozenset)):
            if default_str:
                # FD-A1 residual fix (a2_verify/FD_VERIFY.md "New findings" #1,
                # measured in a2_verify/MEMO_KEY_PROBE.json): the previous key
                # here was `str(value)`, which renders in hash-table iteration
                # order, so EQUAL set payloads received UNEQUAL memo keys under
                # PYTHONHASHSEED in {8, 13, 14, 37, 41, 47, 59} of 1..64. A
                # canonical key is not available either: the memoised functions
                # hash json.dumps(default=str) material, whose set render is
                # itself iteration-order-dependent, so one key for two renders
                # would return a digest the original function disagrees with.
                # When no key can be both stable and faithful, refuse -- the
                # passthrough is counted, correct, and seed-independent.
                return UNKEYABLE
            identity = id(value)
            if identity in active:
                return UNKEYABLE
            active.add(identity)
            try:
                items = [freeze(item) for item in value]
                if any(item is UNKEYABLE for item in items):
                    return UNKEYABLE
                try:
                    # Same FD-A1 canonicalization as the mapping branch: sort
                    # the typed frozen items by their protocol-5 framing so the
                    # frozen node is order-free at construction rather than
                    # relying on `canonicalize_unordered` at framing time.
                    content = tuple(
                        sorted(
                            items,
                            key=lambda item: pickle.dumps(item, protocol=5),
                        )
                    )
                except (
                    AttributeError,
                    OverflowError,
                    pickle.PickleError,
                    TypeError,
                    ValueError,
                ):
                    return UNKEYABLE
                return (type(value).__name__, content)
            finally:
                active.remove(identity)

        if not default_str:
            return UNKEYABLE
        try:
            rendered = str(value)
        except Exception:
            return UNKEYABLE
        return (
            "default_str",
            f"{type(value).__module__}.{type(value).__qualname__}",
            rendered,
        )

    frozen = freeze(payload)
    if frozen is UNKEYABLE:
        return UNKEYABLE

    def canonicalize_unordered(value: Any) -> Any:
        """Give pickle a stable order without retaining the full payload in the LRU.

        ``freeze`` represents mappings and sets as frozensets so their equality is order
        insensitive.  Pickle, however, writes a frozenset in table-iteration order; two
        equal frozensets can therefore produce different byte streams in the same process.
        That made the content key itself order-sensitive intermittently.  Replace only the
        internal unordered nodes with sorted tuples before framing.  Frozen user containers
        are already type-tagged, so this private marker cannot collide with user content.
        """
        if isinstance(value, tuple):
            return tuple(canonicalize_unordered(item) for item in value)
        if isinstance(value, frozenset):
            items = [canonicalize_unordered(item) for item in value]
            items.sort(key=lambda item: pickle.dumps(item, protocol=5))
            return ("__gtos_canonical_frozenset__", tuple(items))
        return value

    try:
        # Retaining the full recursively frozen payload in a 16k-entry LRU can
        # consume the memory the resident sink just recovered. Pickle is only
        # an internal typed framing here; SHA-256 makes the stored key fixed
        # size. A collision is additionally measured on every verify hit.
        framed = pickle.dumps(canonicalize_unordered(frozen), protocol=5)
    except (AttributeError, OverflowError, pickle.PickleError, TypeError, ValueError):
        return UNKEYABLE
    return ("exact_content_sha256_v1", hashlib.sha256(framed).digest())


def make_authority_hash_content_memo_patch(*, verify: bool = False) -> accel.Patch:
    """Memoise the authority payload hash on payload CONTENT, not identity.

    This is the single largest cut in the lane: it removes the recursive
    canonicalisation plus `json.dumps` from every repeat hash of a logically
    identical payload.
    """

    stats = CUT_STATS.setdefault("authority_payload_hash_content", _CutStats())
    memo: collections.OrderedDict[tuple[Any, ...], str] = collections.OrderedDict()
    saved: dict[str, Any] = {}

    def apply() -> None:
        allocator = accel._module(HASH_SYMBOL_MODULES[0])
        if allocator is None:
            return
        original = getattr(allocator, HASH_ATTRIBUTE)
        frozen_type = getattr(allocator, "_FrozenPackageAuthorityPayload", ())

        def memoised(payload: Any) -> str:
            stats.calls += 1
            if isinstance(payload, frozen_type):
                # The engine caches these ON the object already. Duplicating
                # that here would add a layer and save nothing (AX measured the
                # frozen path at 3.1 % of calls; this session measured 3.3 %).
                stats.frozen_passthrough += 1
                return original(payload)
            key = _content_key(payload)
            if key is UNKEYABLE:
                # Never guess -- take the frozen path and count it, so "the
                # memo did nothing" is visible rather than inferred.
                stats.unkeyable_passthrough += 1
                return original(payload)
            cached = memo.get(key)
            if cached is not None:
                stats.hits += 1
                if verify:
                    stats.verified += 1
                    truth = original(payload)
                    if truth != cached:
                        stats.mismatches += 1
                        if len(stats.mismatch_examples) < 8:
                            stats.mismatch_examples = (
                                *stats.mismatch_examples,
                                {
                                    "candidate_id": payload.get("candidate_id"),
                                    "memo_digest": cached,
                                    "true_digest": truth,
                                },
                            )
                        return truth
                memo.move_to_end(key)
                return cached
            stats.misses += 1
            digest = original(payload)
            memo[key] = digest
            memo.move_to_end(key)
            while len(memo) > HASH_MEMO_MAX_ENTRIES:
                memo.popitem(last=False)
                stats.evictions += 1
            return digest

        for module_name in HASH_SYMBOL_MODULES:
            module = accel._module(module_name)
            if module is None or not hasattr(module, HASH_ATTRIBUTE):
                continue
            saved[module_name] = getattr(module, HASH_ATTRIBUTE)
            setattr(module, HASH_ATTRIBUTE, memoised)

    def revert() -> None:
        for module_name, value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                setattr(module, HASH_ATTRIBUTE, value)
        saved.clear()
        memo.clear()

    return accel.Patch(
        patch_id="authority_hash_content_memo",
        summary=(
            "memoise package_new_entry_authority_payload_hash_sha256 on payload "
            "CONTENT (engine cheap key + every top-level scalar), skipping the "
            "recursive canonicalisation + json.dumps that is 19.1 % of wall"
        ),
        identity_argument=(
            "The function is pure in its payload. The engine itself computes "
            "_package_authority_hash_cache_key as a cheap lookup key and then "
            "computes the full canonical material anyway to validate the hit "
            "(allocator:905-912) -- so its cache saves the sha256 and none of "
            "the cost. This memo trusts a key that SUPERSETS the engine's: every "
            "top-level scalar (typed, so True != 1) plus the name/type/length of "
            "every top-level container. All twelve of the engine's key fields "
            "are top-level scalars, so they are contained in it. A false hit "
            "therefore needs two payloads agreeing on every scalar AND on every "
            "container's shape, differing only inside a container. That residual "
            "is not argued, it is MEASURED: verify mode recomputes the true "
            "digest on every hit and counts disagreements, and the "
            "trade-outcome identity gate is the backstop. NOT sealed-lane "
            "compatible in spirit -- a provenance claim must not rest on a "
            "trusted key -- but it changes no bound byte and no verifier input, "
            "so sealed_compatible stays true and the receipt records the "
            "trusted key explicitly."
        ),
        apply=apply,
        revert=revert,
        default_on=True,
    )


# ---------------------------------------------------------------------------
# the OTHER proof hashes -- found by profiling the first train run, not by
# reading AX's tree
# ---------------------------------------------------------------------------
#
# With the authority hash memoised, the 2-day fixture's residual map put 74.1 s
# (15.8 % of wall) in four MORE hash functions, and all four are the same
# five-line body:
#
#     material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
#                           default=str)
#     return hashlib.sha256(material.encode("utf-8")).hexdigest()
#
# | function | self-time on the 470 s run |
# |---|---:|
# | `selector_v4._selector_hash_digest`                | 24.1 s |
# | `v4_timewarp._stable_sha256_uncached`              | 22.2 s |
# | `probability_debate_v4._stable_sha256`             | 18.4 s |
# | `ultimate_candidate_package._packet_hash`          |  9.4 s |
#
# The exposure here is genuinely higher than for the authority payload: these
# take ARBITRARY payloads rather than a structured signed payload, so a shallow
# key can be weak. That is why `_content_key` refuses (`UNKEYABLE`) rather than
# guessing on a payload with no top-level scalar, and why every one of these is
# counted separately -- a low hit rate on one of them is information, not a
# reason to widen the key.

#: (module, attribute) for each. `v4_timewarp.stable_sha256` is deliberately NOT
#: patched: it dispatches to a campaign cache when one is active and to
#: `_stable_sha256_uncached` otherwise, so patching the leaf covers both routes
#: without stepping on the engine's own cache.
PROOF_HASH_TARGETS = (
    ("src.components.selector_v4", "_selector_hash_digest"),
    ("src.research_infra.v4_timewarp_simulated_live_research_loop", "_stable_sha256_uncached"),
    ("src.components.probability_debate_v4", "_stable_sha256"),
    ("src.components.ultimate_candidate_package", "_packet_hash"),
)


def make_proof_hash_content_memo_patch(*, verify: bool = False) -> accel.Patch:
    """Content-memoise the four remaining `json.dumps` + sha256 proof hashes."""

    saved: dict[tuple[str, str], Any] = {}
    memos: dict[str, collections.OrderedDict[Any, str]] = {}

    def apply() -> None:
        for module_name, attribute in PROOF_HASH_TARGETS:
            module = accel._module(module_name)
            if module is None or not hasattr(module, attribute):
                continue
            original = getattr(module, attribute)
            # One memo and one counter PER function: a digest from
            # `_packet_hash` must never be served to `_selector_hash_digest`,
            # even though their bodies are identical today.
            name = f"{module_name.rsplit('.', 1)[-1]}.{attribute}"
            stats = CUT_STATS.setdefault(name, _CutStats())
            memo: collections.OrderedDict[Any, str] = collections.OrderedDict()
            memos[name] = memo

            def memoised(
                payload: Any,
                *,
                _original: Any = original,
                _memo: Any = memo,
                _stats: Any = stats,
            ) -> str:
                _stats.calls += 1
                key = _content_key(payload)
                if key is UNKEYABLE:
                    _stats.unkeyable_passthrough += 1
                    return _original(payload)
                cached = _memo.get(key)
                if cached is not None:
                    _stats.hits += 1
                    if verify:
                        _stats.verified += 1
                        truth = _original(payload)
                        if truth != cached:
                            _stats.mismatches += 1
                            if len(_stats.mismatch_examples) < 8:
                                _stats.mismatch_examples = (
                                    *_stats.mismatch_examples,
                                    {"memo_digest": cached, "true_digest": truth},
                                )
                            return truth
                    _memo.move_to_end(key)
                    return cached
                _stats.misses += 1
                digest = _original(payload)
                _memo[key] = digest
                _memo.move_to_end(key)
                while len(_memo) > HASH_MEMO_MAX_ENTRIES:
                    _memo.popitem(last=False)
                    _stats.evictions += 1
                return digest

            saved[(module_name, attribute)] = original
            setattr(module, attribute, memoised)

    def revert() -> None:
        for (module_name, attribute), value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                setattr(module, attribute, value)
        saved.clear()
        memos.clear()

    return accel.Patch(
        patch_id="proof_hash_content_memo",
        summary=(
            "content-memoise the four remaining json.dumps+sha256 proof hashes "
            "(_selector_hash_digest, _stable_sha256_uncached, _stable_sha256, "
            "_packet_hash) -- 74.1 s / 15.8 % of the first train run"
        ),
        identity_argument=(
            "All four are pure `json.dumps(sort_keys=True, default=str)` + "
            "sha256 of their single argument, with no state. Each gets its OWN "
            "memo, so an identical body can never serve one function's digest "
            "to another. The key is `_content_key`, which REFUSES (frozen "
            "passthrough, counted) any payload with no top-level scalar rather "
            "than trusting a pure-shape key -- the exposure here is higher than "
            "for the structured authority payload because these take arbitrary "
            "payloads. Residual: two payloads agreeing on every top-level scalar "
            "AND every container's name/type/length, differing only inside a "
            "container. Measured by verify mode; backstopped by the "
            "trade-outcome identity gate."
        ),
        apply=apply,
        revert=revert,
        default_on=True,
    )


# Split successors to the legacy all-four patch. H-CB-2 proved the packet hash
# clean under the shallow key and the other three dirty; independent patch ids
# let the clean member stay while each repaired memo earns promotion separately.
SPLIT_HASH_MEMO_TARGETS: dict[str, tuple[str, str, str]] = {
    "selector_hash_content_memo_v2": (
        "src.components.selector_v4",
        "_selector_hash_digest",
        "selector_v4._selector_hash_digest",
    ),
    "timewarp_hash_content_memo_v2": (
        "src.research_infra.v4_timewarp_simulated_live_research_loop",
        "_stable_sha256_uncached",
        "v4_timewarp_simulated_live_research_loop._stable_sha256_uncached",
    ),
    "probability_hash_content_memo_v2": (
        "src.components.probability_debate_v4",
        "_stable_sha256",
        "probability_debate_v4._stable_sha256",
    ),
    "ultimate_packet_hash_content_memo": (
        "src.components.ultimate_candidate_package",
        "_packet_hash",
        "ultimate_candidate_package._packet_hash",
    ),
}


def make_split_hash_content_memo_patch(
    patch_id: str,
    *,
    verify: bool = False,
) -> accel.Patch:
    module_name, attribute, report_name = SPLIT_HASH_MEMO_TARGETS[patch_id]
    stats = CUT_STATS.setdefault(report_name, _CutStats())
    memo: collections.OrderedDict[Any, str] = collections.OrderedDict()
    saved: dict[str, Any] = {}
    exact = patch_id != "ultimate_packet_hash_content_memo"

    def apply() -> None:
        module = accel._module(module_name)
        if module is None or not hasattr(module, attribute):
            return
        original = getattr(module, attribute)

        def memoised(payload: Any) -> str:
            stats.calls += 1
            key = (
                _exact_content_key(payload, default_str=True)
                if exact
                else _content_key(payload)
            )
            if key is UNKEYABLE:
                stats.unkeyable_passthrough += 1
                return original(payload)
            if key in memo:
                cached = memo[key]
                stats.hits += 1
                if verify:
                    stats.verified += 1
                    truth = original(payload)
                    if truth != cached:
                        stats.mismatches += 1
                        if len(stats.mismatch_examples) < 8:
                            stats.mismatch_examples = (
                                *stats.mismatch_examples,
                                {"memo_digest": cached, "true_digest": truth},
                            )
                        return truth
                memo.move_to_end(key)
                return cached
            stats.misses += 1
            digest = original(payload)
            memo[key] = digest
            memo.move_to_end(key)
            while len(memo) > EXACT_CONTENT_MEMO_MAX_ENTRIES:
                memo.popitem(last=False)
                stats.evictions += 1
            return digest

        saved[attribute] = original
        setattr(module, attribute, memoised)

    def revert() -> None:
        module = accel._module(module_name)
        if module is not None and attribute in saved:
            setattr(module, attribute, saved[attribute])
        saved.clear()
        memo.clear()

    key_description = (
        "recursive exact native-JSON content"
        if exact
        else "CB's shallow content key (H-CB-2: 8,628 verified hits, zero mismatches)"
    )
    return accel.Patch(
        patch_id=patch_id,
        summary=f"memoise {report_name} on {key_description}",
        identity_argument=(
            f"{report_name} is pure json.dumps(sort_keys=True, default=str) plus "
            "sha256. The v2 key recursively freezes mapping content and ordered "
            "sequences, preserves scalar types and -0.0, and uses the frozen "
            "serializer's default=str material for unknown leaves. The typed "
            "form is reduced to a fixed-size SHA-256 key rather than retained in "
            "the LRU; stricter type tags may lose hits, while cryptographic "
            "collision risk is measured again by verify mode, which recomputes "
            "every hit and returns truth on disagreement."
            if exact
            else (
                f"{report_name} is pure; H-CB-2 recomputed all 8,628 shallow-key "
                "hits with zero mismatches. Splitting it from the three dirty "
                "functions retains that measured-clean cut without enabling them."
            )
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


def make_attribution_fields_content_memo_patch(
    *, verify: bool = False
) -> accel.Patch:
    """Replace AX's identity key with the full content of every input surface."""

    stats = CUT_STATS.setdefault("attribution_fields_content_memo", _CutStats())
    memo: collections.OrderedDict[Any, dict[str, Any]] = collections.OrderedDict()
    saved: dict[str, Any] = {}
    module_name = "src.research_infra.v4_timewarp_simulated_live_research_loop"
    attribute = "package_new_entry_authority_attribution_fields"

    def apply() -> None:
        module = accel._module(module_name)
        if module is None or not hasattr(module, attribute):
            return
        original = getattr(module, attribute)

        def memoised(
            *surfaces: Any,
            prefix: str = "",
            validate_against_outer_projection: bool = True,
        ) -> dict[str, Any]:
            stats.calls += 1
            frozen_surfaces = tuple(
                _exact_content_key(surface, default_str=False)
                for surface in surfaces
            )
            if any(key is UNKEYABLE for key in frozen_surfaces):
                stats.unkeyable_passthrough += 1
                return original(
                    *surfaces,
                    prefix=prefix,
                    validate_against_outer_projection=validate_against_outer_projection,
                )
            validation_key = _exact_content_key(
                validate_against_outer_projection,
                default_str=False,
            )
            if validation_key is UNKEYABLE:
                stats.unkeyable_passthrough += 1
                return original(
                    *surfaces,
                    prefix=prefix,
                    validate_against_outer_projection=(
                        validate_against_outer_projection
                    ),
                )
            key = (frozen_surfaces, prefix, validation_key)
            if key in memo:
                cached = memo[key]
                stats.hits += 1
                if verify:
                    stats.verified += 1
                    truth = original(
                        *surfaces,
                        prefix=prefix,
                        validate_against_outer_projection=(
                            validate_against_outer_projection
                        ),
                    )
                    if truth != cached:
                        stats.mismatches += 1
                        if len(stats.mismatch_examples) < 8:
                            stats.mismatch_examples = (
                                *stats.mismatch_examples,
                                {
                                    "surface_count": len(surfaces),
                                    "prefix": prefix,
                                },
                            )
                        return truth
                memo.move_to_end(key)
                # The frozen function constructs fresh nested lists for some
                # attribution fields. A shallow copy would let one caller
                # mutate the memo and corrupt a later hit.
                return copy.deepcopy(cached)
            stats.misses += 1
            value = original(
                *surfaces,
                prefix=prefix,
                validate_against_outer_projection=validate_against_outer_projection,
            )
            memo[key] = copy.deepcopy(value)
            memo.move_to_end(key)
            while len(memo) > EXACT_CONTENT_MEMO_MAX_ENTRIES:
                memo.popitem(last=False)
                stats.evictions += 1
            return copy.deepcopy(value)

        saved[attribute] = original
        setattr(module, attribute, memoised)

    def revert() -> None:
        module = accel._module(module_name)
        if module is not None and attribute in saved:
            setattr(module, attribute, saved[attribute])
        saved.clear()
        memo.clear()

    return accel.Patch(
        patch_id="attribution_fields_content_memo_v2",
        summary=(
            "memoise package_new_entry_authority_attribution_fields on the exact "
            "recursive content of every surface, prefix and validation mode"
        ),
        identity_argument=(
            "AX keyed mutable rows by id and H-CB-2 measured 8,207 wrong hits. "
            "This key recursively freezes every supported surface value, so an "
            "in-place splice changes the key. Unknown Python objects refuse the "
            "memo rather than falling back to identity or str. A fresh outer dict "
            "is returned as in the frozen function; verify recomputes every hit."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# output projections -- training-lane artifacts, never sealed evidence
# ---------------------------------------------------------------------------

# The attempt-5 runner funnels every JSONL write through one function. Runtime
# wrappers here project only explicitly named suffixes and stream one output row
# for every input row. An unknown file therefore fails open on FOOTPRINT (it is
# written whole), while every projected file carries an on-row disclosure.

LEDGER_PROJECTIONS: dict[str, str] = {
    "_DECISION_LEDGER.jsonl": "SCALARS_ONLY",
    "_SCORECARD_LEDGER.jsonl": "SCALARS_ONLY",
}
LEDGER_PROJECTION_KEEP: dict[str, frozenset[str]] = {
    "_DECISION_LEDGER.jsonl": frozenset(),
    "_SCORECARD_LEDGER.jsonl": frozenset(),
}
LEDGER_PROJECTION_STAMP = "train_lane_scalar_projection_v1"

HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID = "hard_eligibility_observability"
HARD_ELIGIBILITY_OBSERVABILITY_STAMP = (
    "train_lane_hard_eligibility_observability_v1"
)
HARD_ELIGIBILITY_SOURCE_CONTAINER = "risk_admitted_scheduler_finalizer"
HARD_ELIGIBILITY_REQUIRED_FIELDS = (
    "b7_5_selection_sizing_factorial_hard_eligible_pool_count",
    "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256",
    "b7_5_selection_sizing_factorial_hard_eligible_instance_keys",
    "b7_5_factorial_hard_eligible_option_rows",
)
HARD_ELIGIBILITY_CONTAINER_FIELDS = frozenset(
    {
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys",
        "b7_5_factorial_hard_eligible_option_rows",
    }
)
_HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE = 0

# WALK-F1 (phase19 forensic walk annex): the condition-feature instrument's
# output reached TRADE (4/4) and ORDER (8/8) rows but 0/8,448 MISSED rows.
# The missed-row assembly DOES splat the wrapped helper (all three
# `ledgers["missed"].append` sites in the frozen timewarp file), but the
# attempt5 transport compactor `compact_missed_opportunity_rows` is a strict
# keep_fields allowlist that stripped the block before `append_jsonl` -- on
# both write paths (the resident sink's append-time projector and the
# write-time iterator funnel through the same module global).  This counter
# follows the `_HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE` precedent so the
# missed projection can distinguish "instrument off" (no fields at all) from
# "instrument on, block absent" (status fields stamped "missing").
_CONDITION_FEATURE_PROPAGATION_ACTIVE = 0

MISSED_LEDGER_SUFFIX = "_MISSED_OPPORTUNITY_LEDGER.jsonl"
MISSED_POOL_PROJECTION_STAMP = "train_lane_missed_pool_projection_v3"

#: R-SCHEMA dedup telemetry name: hits = rows where `expectancy_r ==
#: candidate_ev_r` (the measured 8,448/8,448 alias), mismatches =
#: disagreements (a finding).  Resolved through CUT_STATS.setdefault at each
#: use so `reset_cut_stats()` cannot orphan the counter.
EXPECTANCY_ALIAS_STATS_NAME = "missed_pool_expectancy_r_alias"

# These are the readers, not a hand-maintained bag of convenient fields. The
# first entry is expanded from the reader's own Field_ declarations by
# `_missed_reader_fields`; the remaining entries name the literal reads in the
# two diagnostic aggregators. Keeping this registry beside the cut makes a new
# consumer an explicit schema change rather than a silent dependency.
MISSED_POOL_LITERAL_READERS: dict[str, frozenset[str]] = {
    (
        "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_"
        "2026_07_16/analyze_b7_5_selection_sizing_matrix.py:update_missed"
    ): frozenset(
        {
            "canonical_replay_candidate_instance_key",
            "candidate_instance_parity_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_id",
            "decision_time_utc",
            "decision_time",
            "missed_opportunity_r_scoreability_status",
            "missed_opportunity_non_executable_diagnostic_scoreable",
            "missed_opportunity_headline_r_scoreable",
            "opportunity_net_proxy_r",
        }
    ),
    "src.research_infra.fast_engine.bench:_missed_digest": frozenset(
        {
            "missed_opportunity_r_scoreability_status",
            "missed_opportunity_non_executable_diagnostic_scoreable",
            "opportunity_net_proxy_r",
        }
    ),
}

# Repair provenance is not an economic reader today, but it is the declaration
# that says which generator produced the row. Dropping it would make two repair
# arms observationally indistinguishable to a later audit.
MISSED_POOL_REPAIR_PROVENANCE = frozenset(
    {
        *decision_semantics.REPAIR_PROVENANCE_FIELDS,
        *decision_semantics.SEMANTIC_FIELDS,
    }
)

# Session CR found that the producer had already computed every field needed to
# score an executable missed-candidate population, but the footprint projection
# discarded the fill identity and content-bound path.  Those fields are not a
# large proof envelope: they are the compact behavioral record that distinguishes
# a no-fill from a trade and binds a filled trade's gross R to its exit/path.
#
# Keep both the raw limit-path close and the selected-policy/profit-harvest close.
# `project_missed_pool_row` resolves them into `opportunity_close_time_utc` only
# after checking the corresponding authority flag, so a diagnostic overlay can
# never silently replace the terminal event.
MISSED_EXECUTABLE_CAPTURE_FIELDS = frozenset(
    {
        "counterfactual_order_fill_status",
        "counterfactual_order_terminal_outcome",
        "counterfactual_order_fill_time_utc",
        "counterfactual_order_fill_price",
        "counterfactual_order_close_time_utc",
        "counterfactual_order_close_mark_r",
        "counterfactual_order_close_mark_source",
        "limit_first_fill_status",
        "limit_first_terminal_outcome",
        "limit_first_fill_time_utc",
        "limit_first_entry_price",
        "limit_first_close_time_utc",
        "limit_first_expiry_utc",
        "pending_expiry_minutes",
        "opportunity_path_scored",
        "opportunity_gross_r",
        "opportunity_close_reason",
        "terminal_outcome",
        "entry_fill_executable",
        "fill_realism_class",
        "fill_realism_executable",
        "fill_realism_reason",
        "terminal_r_scoreable",
        "terminal_r_scoreability_status",
        "terminal_r_path_authority",
        "path_source",
        "path_source_timeframe",
        "path_index_timeframe",
        "path_index_source_path",
        "path_index_source_sha256",
        "path_index_rows_returned",
        "path_row_count",
        "path_source_truth_scope",
        "path_source_gaps",
        "source_gaps",
        "ordered_tick_truth_satisfied",
        "ordered_tick_truth_authority_hash_sha256",
        "tick_window_covers_candidate",
        "selected_execution_policy_replay_bound",
        "selected_execution_policy_replay_final_r",
        "selected_execution_policy_replay_exit_reason",
        "selected_execution_policy_replay_exit_time_utc",
        "selected_execution_policy_replay_final_r_authority_status",
        "profit_harvest_applied_to_terminal",
        "profit_harvest_policy_terminal_outcome",
        "profit_harvest_policy_close_time_utc",
        "profit_harvest_policy_close_mark_r",
        "profit_harvest_mfe_capture_replay_exit_final_r_authority",
        "profit_harvest_mfe_capture_replay_exit_final_r_authority_status",
        "exit_composition_terminal_gross_r",
    }
)

# ORDER and TRADE are small terminal ledgers, so semantics can be repaired
# without projecting away any source field.  In particular, the legacy trade
# emitter stored terminal outcomes in ``close_mark_source``.  This capture-only
# patch preserves that value under ``legacy_close_mark_source`` and emits the
# canonical source/outcome pair.  It never touches the bound decision loop.
DECISION_SEMANTICS_LEDGER_KINDS = {
    "_ORDER_LEDGER.jsonl": "order",
    "_TRADE_LEDGER.jsonl": "trade",
}

# Session FE's bounded higher-information surface. These are the exact V2
# as-of-safe fields emitted by broader_origin_generators. They are copied here
# intentionally: the train-lane instrument must have a reviewable, finite
# transport contract rather than inheriting every future nested candidate key.
# A focused test pins byte-for-byte equality with PREDECISION_FEATURE_KEYS.
CONDITION_FEATURE_KEYS: tuple[str, ...] = (
    "atr14_over_atr50",
    "stop_distance_atr",
    "target_distance_atr",
    "close_position_in_lookback_range",
    "trend_state_m15",
    "trend_transition_flag",
    "dist_to_prior_high20_atr",
    "dist_to_prior_low20_atr",
    "trigger_bar_range_atr",
    "trigger_bar_body_atr",
    "compression_ratio_prior_bar",
    "bars_since_session_open",
    "close_to_close_vol_8_over_48",
    "sweep_depth_atr",
    "session_open_range_width_atr",
)
CONDITION_FEATURE_PROJECTION_SCHEMA = "train_lane_condition_features_v1"
CONDITION_FEATURE_LEDGER_FIELDS = frozenset(
    {
        "predecision_features",
        "condition_feature_projection_schema",
        "condition_feature_projection_status",
        "condition_feature_projection_present_count",
        "condition_feature_projection_missing_count",
        "condition_feature_projection_unknown_key_count",
        "condition_feature_projection_invalid_value_count",
    }
)


def condition_feature_ledger_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a bounded, scalar-only copy of as-of-safe condition telemetry.

    This is observation, never candidate authority. Missing or malformed input
    returns status fields and no exception, so enabling the instrument cannot
    suppress candidate generation or change economics.
    """

    raw = row.get("predecision_features")
    base = {
        "condition_feature_projection_schema": CONDITION_FEATURE_PROJECTION_SCHEMA,
        "condition_feature_projection_present_count": 0,
        "condition_feature_projection_missing_count": len(CONDITION_FEATURE_KEYS),
        "condition_feature_projection_unknown_key_count": 0,
        "condition_feature_projection_invalid_value_count": 0,
    }
    if raw is None:
        return {**base, "condition_feature_projection_status": "missing"}
    if not isinstance(raw, Mapping):
        return {
            **base,
            "condition_feature_projection_status": "malformed_not_mapping",
            "condition_feature_projection_invalid_value_count": 1,
        }

    unknown_count = sum(key not in CONDITION_FEATURE_KEYS for key in raw)
    projected: dict[str, Any] = {}
    present_count = 0
    invalid_count = 0
    for key in CONDITION_FEATURE_KEYS:
        if key not in raw:
            projected[key] = None
            continue
        value = raw.get(key)
        scalar_and_finite = (
            value is None
            or isinstance(value, (str, int, bool))
            or (isinstance(value, float) and math.isfinite(value))
        )
        if scalar_and_finite:
            projected[key] = value
            present_count += 1
        else:
            projected[key] = None
            invalid_count += 1

    missing_count = len(CONDITION_FEATURE_KEYS) - present_count
    if invalid_count:
        status = "invalid_values_dropped"
    elif unknown_count:
        status = "unknown_keys_dropped"
    elif missing_count:
        status = "partial"
    else:
        status = "complete"
    return {
        "predecision_features": projected,
        "condition_feature_projection_schema": CONDITION_FEATURE_PROJECTION_SCHEMA,
        "condition_feature_projection_status": status,
        "condition_feature_projection_present_count": present_count,
        "condition_feature_projection_missing_count": missing_count,
        "condition_feature_projection_unknown_key_count": unknown_count,
        "condition_feature_projection_invalid_value_count": invalid_count,
    }


def _missed_reader_fields() -> dict[str, frozenset[str]]:
    """Return raw-ledger fields grouped by the reader that consumes them."""

    from src.research_infra import b7_5_diagnostic_pool as pool

    declared = {
        field.source.split(".", 1)[0]
        for field in (*pool.PROJECTION, *pool.OUTCOME_PROJECTION)
        if not field.source.startswith("derived:")
    }
    return {
        (
            "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
            "aw_separability_mine.py:load_frame -> "
            "src.research_infra.b7_5_diagnostic_pool:iter_arm_rows/project"
        ): frozenset(declared),
        **MISSED_POOL_LITERAL_READERS,
    }


def _missed_keep_names() -> frozenset[str]:
    fields = set(MISSED_POOL_REPAIR_PROVENANCE | CONDITION_FEATURE_LEDGER_FIELDS)
    fields.update(MISSED_EXECUTABLE_CAPTURE_FIELDS)
    for reader_fields in _missed_reader_fields().values():
        fields.update(reader_fields)
    return frozenset(fields)


# No lane reader consumes a semantic-sidecar field. The complete census is:
# attempt5's `semantic_ledger_write_row_counts` consumes the append return value
# (row count, zero fields); `fast_engine.bench.extract_economics` never opens the
# namespace; and AW reads MISSED_OPPORTUNITY, not this sidecar. Sealed semantic
# readers deliberately are not lane readers, so this patch is sealed-incompatible.
SEMANTIC_SIDECAR_PROJECTIONS = frozenset(
    {
        "_SEMANTIC_CANDIDATE_LEDGER.jsonl",
        "_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl",
        "_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
    }
)
SEMANTIC_SIDECAR_FIELD_READERS: dict[str, frozenset[str]] = {
    (
        "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner:"
        "semantic_ledger_write_row_counts"
    ): frozenset(),
    "src.research_infra.fast_engine.bench:extract_economics": frozenset(),
    (
        "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
        "aw_separability_mine.py:load_frame"
    ): frozenset(),
}
SEMANTIC_SIDECAR_PROJECTION_STAMP = "train_lane_unread_semantic_sidecar_v1"


def _hard_eligibility_digest(instance_keys: list[str]) -> str:
    material = json.dumps(
        instance_keys,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def project_hard_eligibility_observability_row(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Lift the exact factorial hard pool before scalar projection drops it.

    The finalizer already computes these values. This projector does not
    reconstruct, infer, or rank anything; it validates and copies the producer's
    exact count, digest, instance keys, and compact option rows to the scorecard
    top level. Non-factorial rows remain distinguishable from broken factorial
    rows through an explicit status.
    """

    out = dict(row)
    if out.get("train_lane_hard_eligibility_observability") == (
        HARD_ELIGIBILITY_OBSERVABILITY_STAMP
    ):
        return out

    source = row.get(HARD_ELIGIBILITY_SOURCE_CONTAINER)
    if not isinstance(source, Mapping):
        if row.get("b7_5_selection_sizing_factorial_arm_id") not in (None, ""):
            raise ValueError(
                "hard_eligibility_observability_factorial_source_container_missing"
            )
        out.update(
            {
                "train_lane_hard_eligibility_observability": (
                    HARD_ELIGIBILITY_OBSERVABILITY_STAMP
                ),
                "train_lane_hard_eligibility_observability_status": (
                    "SOURCE_CONTAINER_MISSING"
                ),
            }
        )
        return out

    present = [field for field in HARD_ELIGIBILITY_REQUIRED_FIELDS if field in source]
    if not present:
        if row.get("b7_5_selection_sizing_factorial_arm_id") not in (None, ""):
            raise ValueError(
                "hard_eligibility_observability_factorial_source_fields_missing"
            )
        out.update(
            {
                "train_lane_hard_eligibility_observability": (
                    HARD_ELIGIBILITY_OBSERVABILITY_STAMP
                ),
                "train_lane_hard_eligibility_observability_status": (
                    "NOT_FACTORIAL_BOUND"
                ),
            }
        )
        return out
    if len(present) != len(HARD_ELIGIBILITY_REQUIRED_FIELDS):
        missing = sorted(set(HARD_ELIGIBILITY_REQUIRED_FIELDS) - set(present))
        raise ValueError(
            "hard_eligibility_observability_partial_source_fields:"
            + ",".join(missing)
        )

    raw_count = source[HARD_ELIGIBILITY_REQUIRED_FIELDS[0]]
    raw_digest = source[HARD_ELIGIBILITY_REQUIRED_FIELDS[1]]
    raw_keys = source[HARD_ELIGIBILITY_REQUIRED_FIELDS[2]]
    raw_rows = source[HARD_ELIGIBILITY_REQUIRED_FIELDS[3]]
    if (
        isinstance(raw_count, bool)
        or not isinstance(raw_count, int)
        or raw_count < 0
    ):
        raise ValueError("hard_eligibility_observability_invalid_count")
    if not isinstance(raw_keys, (list, tuple)):
        raise ValueError("hard_eligibility_observability_invalid_instance_keys")
    if not isinstance(raw_rows, (list, tuple)):
        raise ValueError("hard_eligibility_observability_invalid_option_rows")

    instance_keys = [str(value or "").strip() for value in raw_keys]
    if any(not value for value in instance_keys):
        raise ValueError("hard_eligibility_observability_blank_instance_key")
    if instance_keys != sorted(instance_keys):
        raise ValueError("hard_eligibility_observability_unsorted_instance_keys")
    if len(instance_keys) != len(set(instance_keys)):
        raise ValueError("hard_eligibility_observability_duplicate_instance_key")
    if raw_count != len(instance_keys) or raw_count != len(raw_rows):
        raise ValueError("hard_eligibility_observability_count_mismatch")

    option_rows: list[dict[str, Any]] = []
    option_instance_keys: list[str] = []
    for option in raw_rows:
        if not isinstance(option, Mapping):
            raise ValueError("hard_eligibility_observability_invalid_option_row")
        option_row = copy.deepcopy(dict(option))
        option_key = str(
            option_row.get("canonical_replay_candidate_instance_key") or ""
        ).strip()
        if not option_key:
            raise ValueError("hard_eligibility_observability_option_key_missing")
        option_rows.append(option_row)
        option_instance_keys.append(option_key)
    if sorted(option_instance_keys) != instance_keys:
        raise ValueError("hard_eligibility_observability_option_key_set_mismatch")

    digest = str(raw_digest or "").strip().lower()
    expected_digest = _hard_eligibility_digest(instance_keys)
    if digest != expected_digest:
        raise ValueError("hard_eligibility_observability_digest_mismatch")

    out.update(
        {
            HARD_ELIGIBILITY_REQUIRED_FIELDS[0]: raw_count,
            HARD_ELIGIBILITY_REQUIRED_FIELDS[1]: digest,
            HARD_ELIGIBILITY_REQUIRED_FIELDS[2]: copy.deepcopy(instance_keys),
            HARD_ELIGIBILITY_REQUIRED_FIELDS[3]: option_rows,
            "train_lane_hard_eligibility_observability": (
                HARD_ELIGIBILITY_OBSERVABILITY_STAMP
            ),
            "train_lane_hard_eligibility_observability_status": (
                "EXACT_FACTORIAL_HARD_POOL_EMITTED"
            ),
            "train_lane_hard_eligibility_observability_count_reconciled": True,
            "train_lane_hard_eligibility_observability_digest_reconciled": True,
            "train_lane_hard_eligibility_observability_join_key": (
                "candidate_id+decision_time_utc"
            ),
            "train_lane_hard_eligibility_observability_composite_completion": (
                "join_symbol+side_or_direction_from_candidate_or_missed_ledger"
            ),
        }
    )
    return out


def _project_scalar_row(
    row: Mapping[str, Any],
    keep: frozenset[str],
    *,
    hard_eligibility_observability: bool = False,
) -> dict[str, Any]:
    source_row = row
    if hard_eligibility_observability and _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE:
        source_row = project_hard_eligibility_observability_row(row)
    effective_keep = keep
    if source_row.get("train_lane_hard_eligibility_observability") == (
        HARD_ELIGIBILITY_OBSERVABILITY_STAMP
    ):
        effective_keep = frozenset(
            set(keep) | set(HARD_ELIGIBILITY_CONTAINER_FIELDS)
        )
    out = {
        key: value
        for key, value in source_row.items()
        if not isinstance(value, (dict, list, tuple, set)) or key in effective_keep
    }
    out["train_lane_ledger_projection"] = LEDGER_PROJECTION_STAMP
    return out


def cost_attribution_provenance_fields(
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Project repair provenance from the packet the frozen emitter can see.

    The frozen attribution helper deliberately emits a compact economic set,
    but it predates the train-lane commission/swap repairs and therefore drops
    their statuses.  This projection is additive and contains no decision
    input.  It is split out so the capture contract has a pure regression test.
    """

    out: dict[str, Any] = {}
    scalar_fields = packet.get("scalar_fields")
    scalar_fields = scalar_fields if isinstance(scalar_fields, Mapping) else {}
    for field in decision_semantics.REPAIR_PROVENANCE_FIELDS:
        value = packet.get(field)
        if value in (None, ""):
            value = scalar_fields.get(field)
        if value not in (None, ""):
            out[field] = value
    return out


def _append_projection_patch(
    *,
    patch_id: str,
    summary: str,
    identity_argument: str,
    projector: Any,
    default_on: bool = True,
    sealed_compatible: bool = False,
    on_apply: Any = None,
    on_revert: Any = None,
) -> accel.Patch:
    """Wrap attempt5.append_jsonl with one streaming projection."""

    stats = CUT_STATS.setdefault(patch_id, _CutStats())
    saved: dict[str, Any] = {}
    module_name = (
        "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    )

    def apply() -> None:
        if on_apply is not None:
            on_apply()
        module = accel._module(module_name)
        if module is None or not hasattr(module, "append_jsonl"):
            return
        original = module.append_jsonl

        def projected(path: Any, rows: Any) -> int:
            project = projector(str(getattr(path, "name", path)))
            if project is None:
                stats.frozen_passthrough += 1
                return original(path, rows)

            def stream() -> Any:
                for row in rows:
                    stats.calls += 1
                    if not isinstance(row, Mapping):
                        stats.unkeyable_passthrough += 1
                        yield row
                        continue
                    stats.hits += 1
                    yield project(row)

            return original(path, stream())

        saved[module_name] = original
        module.append_jsonl = projected

    def revert() -> None:
        for name, value in saved.items():
            module = accel._module(name)
            if module is not None:
                module.append_jsonl = value
        saved.clear()
        if on_revert is not None:
            on_revert()

    return accel.Patch(
        patch_id=patch_id,
        summary=summary,
        identity_argument=identity_argument,
        apply=apply,
        revert=revert,
        default_on=default_on,
        sealed_compatible=sealed_compatible,
    )


def make_cost_attribution_provenance_patch() -> accel.Patch:
    module_name = (
        "src.research_infra.v4_timewarp_simulated_live_research_loop"
    )
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(module_name)
        if module is None or not hasattr(module, "pretrade_cost_attribution_fields"):
            return
        original = module.pretrade_cost_attribution_fields

        def enriched(packets: Mapping[str, Any]) -> dict[str, Any]:
            out = dict(original(packets))
            packet = module.normalized_pretrade_cost_packet_from_packets(packets)
            out.update(cost_attribution_provenance_fields(packet))
            return out

        saved[module_name] = original
        module.pretrade_cost_attribution_fields = enriched

    def revert() -> None:
        for name, value in saved.items():
            module = accel._module(name)
            if module is not None:
                module.pretrade_cost_attribution_fields = value
        saved.clear()

    return accel.Patch(
        patch_id="cost_attribution_provenance",
        summary=(
            "carry train-repair status and total-redecode provenance from the "
            "pretrade packet into behavior-ledger attribution fields"
        ),
        identity_argument=(
            "Additive evidence projection only. The original attribution "
            "function computes every economic field and decision first; this "
            "wrapper copies named provenance scalars from that same packet. "
            "No cost, gate, candidate, sizing, order, or outcome can change."
        ),
        apply=apply,
        revert=revert,
        default_on=True,
        sealed_compatible=False,
    )


def make_ledger_projection_patch() -> accel.Patch:
    def choose(name: str) -> Any:
        suffix = next(
            (item for item in LEDGER_PROJECTIONS if name.endswith(item)), None
        )
        if suffix is None:
            return None
        keep = LEDGER_PROJECTION_KEEP.get(suffix, frozenset())
        return lambda row: _project_scalar_row(
            row,
            keep,
            hard_eligibility_observability=(
                suffix == "_SCORECARD_LEDGER.jsonl"
            ),
        )

    return _append_projection_patch(
        patch_id="ledger_scalar_projection",
        summary=(
            "write top-level scalars only to DECISION and SCORECARD; their lane "
            "readers consume no nested field"
        ),
        identity_argument=(
            "bench.extract_economics never opens DECISION and applies _prune_row "
            "to SCORECARD, which already drops dict/list/tuple values. One row is "
            "written per input row; outcome identity is the backstop. The changed "
            "artifact is training-only, so sealed_compatible is false."
        ),
        projector=choose,
    )


def make_missed_pool_projection_patch() -> accel.Patch:
    def choose(name: str) -> Any:
        if not name.endswith(MISSED_LEDGER_SUFFIX):
            return None
        return project_missed_pool_row

    return _append_projection_patch(
        patch_id="missed_pool_projection",
        summary=(
            "write the union of every field read by AW's b7_5_diagnostic_pool "
            "pipeline, the matrix analyzer, bench._missed_digest, and repair "
            "provenance plus the exact executable-capture contract to "
            "MISSED_OPPORTUNITY"
        ),
        identity_argument=(
            "The keep set is derived from b7_5_diagnostic_pool.PROJECTION plus "
            "OUTCOME_PROJECTION, then unioned with the matrix analyzer's exact "
            "identity/scoreability reads, bench._missed_digest, and repair "
            "provenance plus CR's fill/terminal/path contract. This fixes CD's "
            "FEATURE_FIELDS-only cut, which omitted "
            "canonical identity and four AW outcome inputs. One row remains one "
            "row; the full pool digest and trade/order identities are gated at "
            "zero tolerance. The changed artifact is training-only."
        ),
        projector=choose,
    )


def make_semantic_sidecar_projection_patch() -> accel.Patch:
    def choose(name: str) -> Any:
        if not any(name.endswith(suffix) for suffix in SEMANTIC_SIDECAR_PROJECTIONS):
            return None
        return project_semantic_sidecar_row

    return _append_projection_patch(
        patch_id="semantic_sidecar_projection",
        summary=(
            "preserve semantic-sidecar row counts as stamped rows and drop all "
            "fields; the lane has zero field-reading consumers"
        ),
        identity_argument=(
            "The enumerated lane consumers read only append_jsonl's returned row "
            "count or ignore the namespace. Sealed semantic comparison readers "
            "are intentionally out of scope, and the patch declares itself "
            "sealed-incompatible. Outcome identity is gated independently."
        ),
        projector=choose,
    )


def make_decision_semantics_projection_patch() -> accel.Patch:
    def choose(name: str) -> Any:
        suffix = next(
            (
                item
                for item in DECISION_SEMANTICS_LEDGER_KINDS
                if name.endswith(item)
            ),
            None,
        )
        if suffix is None:
            return None
        row_kind = DECISION_SEMANTICS_LEDGER_KINDS[suffix]
        return lambda row: decision_semantics.normalize_evidence_row(
            row, row_kind=row_kind
        )

    return _append_projection_patch(
        patch_id="decision_semantics_projection",
        summary=(
            "repair cost, source/outcome, authority, and heuristic provenance "
            "on the small ORDER and TRADE evidence ledgers"
        ),
        identity_argument=(
            "The patch is additive except where a semantically false legacy "
            "field is copied to legacy_* before canonicalization. It is "
            "training-only, sealed-incompatible, and does not change any "
            "candidate, order instruction, sizing, or outcome."
        ),
        projector=choose,
    )


def make_hard_eligibility_observability_patch() -> accel.Patch:
    """Preserve exact factorial hard-pool evidence in train scorecards only."""

    def choose(name: str) -> Any:
        if not name.endswith("_SCORECARD_LEDGER.jsonl"):
            return None
        return project_hard_eligibility_observability_row

    def activate() -> None:
        global _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE
        _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE += 1

    def deactivate() -> None:
        global _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE
        _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE = max(
            0, _HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE - 1
        )

    return _append_projection_patch(
        patch_id=HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID,
        summary=(
            "lift and validate the exact factorial hard-eligible count, digest, "
            "instance keys, and compact option rows before scorecard scalar "
            "projection"
        ),
        identity_argument=(
            "The patch copies producer-computed fields without reconstructing "
            "eligibility or rank, and fails closed unless count, unique sorted "
            "instance keys, option-row keys, and producer digest reconcile. It "
            "changes only training-lane scorecard observability."
        ),
        projector=choose,
        default_on=False,
        sealed_compatible=False,
        on_apply=activate,
        on_revert=deactivate,
    )


def project_missed_pool_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Public pure projector used by the runtime cut and disk receipt."""

    normalized = decision_semantics.normalize_evidence_row(row)
    keep = _missed_keep_names()
    out = {key: value for key, value in normalized.items() if key in keep}
    if _CONDITION_FEATURE_PROPAGATION_ACTIVE and not any(
        key in out for key in CONDITION_FEATURE_LEDGER_FIELDS
    ):
        # WALK-F1 belt: with the instrument armed, a missed row that reached
        # this projector without any condition telemetry (a writer path that
        # bypassed the wrapped compactor) still stamps the status fields, so
        # "block absent" stays distinguishable from "instrument off".  With
        # the instrument off this branch never runs and the projection output
        # is byte-identical (pinned by test).
        out.update(condition_feature_ledger_fields(normalized))
    expectancy_r = normalized.get("expectancy_r")
    candidate_ev_r = normalized.get("candidate_ev_r")
    if expectancy_r is not None and candidate_ev_r is not None:
        # R-SCHEMA dedup stamp (phase19 PHASE1_OPEN_QUESTIONS cross-cutting
        # item 2): `expectancy_r` was byte-equal to `candidate_ev_r` on
        # 8,448/8,448 fence MISSED rows -- a duplicate field, kept because
        # readers exist.  The stamp names the alias; a disagreement would be
        # a finding, so it is counted in the cut report.
        alias = expectancy_r == candidate_ev_r
        out["expectancy_r_is_candidate_ev_r_alias"] = alias
        alias_stats = CUT_STATS.setdefault(
            EXPECTANCY_ALIAS_STATS_NAME, _CutStats()
        )
        alias_stats.calls += 1
        if alias:
            alias_stats.hits += 1
        else:
            alias_stats.mismatches += 1
            if len(alias_stats.mismatch_examples) < 8:
                alias_stats.mismatch_examples = (
                    *alias_stats.mismatch_examples,
                    {
                        "candidate_id": normalized.get("candidate_id"),
                        "decision_time_utc": normalized.get("decision_time_utc"),
                        "expectancy_r": expectancy_r,
                        "candidate_ev_r": candidate_ev_r,
                    },
                )
    if normalized.get("profit_harvest_applied_to_terminal") is True:
        opportunity_close_time = normalized.get(
            "profit_harvest_policy_close_time_utc"
        )
        opportunity_close_source = "profit_harvest_policy"
    elif normalized.get("selected_execution_policy_replay_bound") is True:
        opportunity_close_time = normalized.get(
            "selected_execution_policy_replay_exit_time_utc"
        )
        opportunity_close_source = "selected_execution_policy"
    else:
        opportunity_close_time = normalized.get(
            "counterfactual_order_close_time_utc"
        )
        opportunity_close_source = "counterfactual_order_path"
    out["opportunity_close_time_utc"] = opportunity_close_time
    out["opportunity_close_time_source"] = opportunity_close_source
    out["train_lane_missed_projection"] = MISSED_POOL_PROJECTION_STAMP
    return out


def project_semantic_sidecar_row(_row: Mapping[str, Any]) -> dict[str, Any]:
    """Public pure projector used by the runtime cut and disk receipt."""

    return {
        "train_lane_semantic_projection": SEMANTIC_SIDECAR_PROJECTION_STAMP
    }


def make_condition_feature_propagation_patch() -> accel.Patch:
    """Expose the existing predecision block to training ledgers, explicitly off.

    The frozen timewarp file is R2-bound, so FE does not edit it. Instead this
    unbound train-lane patch wraps the namespace helper at runtime and adds only
    telemetry to its returned ledger dict. The input candidate is never
    mutated, and revert restores the exact original function object.
    """

    patch_id = "condition_feature_propagation"
    stats = CUT_STATS.setdefault(patch_id, _CutStats())
    saved: list[tuple[str, str, Any]] = []
    module_name = "src.research_infra.v4_timewarp_simulated_live_research_loop"
    attribute = "ledger_namespace_alias_fields"
    runner_module_name = (
        "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    )
    compact_attribute = "compact_missed_opportunity_rows"

    def apply() -> None:
        global _CONDITION_FEATURE_PROPAGATION_ACTIVE
        _CONDITION_FEATURE_PROPAGATION_ACTIVE += 1
        module = accel._module(module_name)
        if module is None or not hasattr(module, attribute):
            return
        original = getattr(module, attribute)

        def instrumented(
            row: Mapping[str, Any],
            packets: Mapping[str, Any] | None = None,
            *,
            decision_time_utc: str | None = None,
        ) -> dict[str, Any]:
            frozen_fields = original(
                row,
                packets,
                decision_time_utc=decision_time_utc,
            )
            stats.calls += 1
            projected = condition_feature_ledger_fields(row)
            status = projected["condition_feature_projection_status"]
            if status == "complete":
                stats.hits += 1
            else:
                stats.unkeyable_passthrough += 1
            return {**frozen_fields, **projected}

        saved.append((module_name, attribute, original))
        setattr(module, attribute, instrumented)

        # WALK-F1 fix: the assembly-time fields above were stripped by the
        # attempt5 transport compactor's keep_fields allowlist before any
        # missed row reached `append_jsonl`, so 0/8,448 walk MISSED rows
        # carried them. Rebinding the module global at runtime covers both
        # consumers -- the resident sink's `project_compact_missed_transport_row`
        # and the write path's `iter_compact_missed_opportunity_rows` resolve
        # it at call time -- without editing the R2-adjacent runner file.
        runner_module = accel._module(runner_module_name)
        if runner_module is None or not hasattr(runner_module, compact_attribute):
            return
        compact_original = getattr(runner_module, compact_attribute)

        def carrying(rows: Any) -> list[dict[str, Any]]:
            raw_rows = list(rows)
            compact_rows = compact_original(raw_rows)
            for raw, compact in zip(raw_rows, compact_rows):
                if not isinstance(raw, Mapping) or not isinstance(compact, dict):
                    continue
                carried = {
                    key: raw[key]
                    for key in CONDITION_FEATURE_LEDGER_FIELDS
                    if key in raw
                }
                if carried:
                    # Carry the assembly-time projection verbatim; it is the
                    # single source of truth (re-projecting a projected block
                    # would count its None placeholders as present).
                    compact.update(carried)
                else:
                    # The row never passed the instrumented helper; stamp so
                    # absence stays distinguishable from instrument-off.
                    compact.update(condition_feature_ledger_fields(raw))
            return compact_rows

        saved.append((runner_module_name, compact_attribute, compact_original))
        setattr(runner_module, compact_attribute, carrying)

    def revert() -> None:
        global _CONDITION_FEATURE_PROPAGATION_ACTIVE
        _CONDITION_FEATURE_PROPAGATION_ACTIVE = max(
            0, _CONDITION_FEATURE_PROPAGATION_ACTIVE - 1
        )
        for name, attr, value in reversed(saved):
            module = accel._module(name)
            if module is not None:
                setattr(module, attr, value)
        saved.clear()

    return accel.Patch(
        patch_id=patch_id,
        summary=(
            "default-off propagation of the existing as-of-safe broader-origin "
            "predecision feature block into train-lane missed-pool telemetry"
        ),
        identity_argument=(
            "The patch adds ledger telemetry after ledger_namespace_alias_fields "
            "has computed its frozen result; it never mutates the candidate, "
            "selector packets, identity, geometry, cost, or outcome. Only the 15 "
            "declared scalar/None fields survive, unknown/nested values are "
            "dropped with status, the patch is absent from every default set, "
            "and the resulting artifact is explicitly sealed-incompatible. "
            "WALK-F1 addendum: it also carries those same additive fields "
            "through the attempt5 missed-row transport compactor (a strict "
            "allowlist that previously stripped them before append_jsonl) and "
            "raises a module counter so project_missed_pool_row can stamp "
            "status='missing' when the block never arrived; every added field "
            "is telemetry-only and no compactor keep_fields value changes."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
        sealed_compatible=False,
    )


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

#: H-CB-2's measured-clean compute set. The two dirty memo patches remain
#: registered so old receipts reproduce, but neither is reachable from `safe`
#: or the lane default until a zero-mismatch verify run promotes its replacement.
HCB2_COMPUTE_SAFE_PATCHES = (
    "authority_hash_content_memo",
    "abc_concrete_types",
    "skip_post_hoc_ledger_recertification",
    "gc_during_chunk",
)

#: The operational lane default: clean compute plus the three reader-bound
#: footprint cuts.  The exact memo successors are registered and verified but
#: remain off: their recursive key made a default-path fixture exceed the full
#: frozen baseline by 1.77x before final serialization.  Correctness is
#: necessary for promotion, not sufficient when a performance cut is slower.
#: All three projections are visibly sealed-incompatible.
TRAIN_SAFE_SET_PATCHES = (
    *HCB2_COMPUTE_SAFE_PATCHES,
    "ultimate_packet_hash_content_memo",
    "train_resident_event_sink",
    "ledger_scalar_projection",
    "cost_attribution_provenance",
    "missed_pool_projection",
    "decision_semantics_projection",
    "semantic_sidecar_projection",
)
TRAIN_DEFAULT_PATCHES = TRAIN_SAFE_SET_PATCHES

#: Explicit higher-information spelling. The condition feature instrument is
#: absent from both the default and safe sets; a caller has to request this
#: exact research-only surface, and the run manifest will record that it is
#: sealed-incompatible.
TRAIN_CONDITION_FEATURE_PATCHES = (
    *TRAIN_SAFE_SET_PATCHES,
    "condition_feature_propagation",
)

#: Symbols rebound to concrete types. H-CB-2 measured Mapping and MutableMapping
#: at zero per-call mismatches. Sequence was wrong on 47,444,764 string checks:
#: `(list, tuple)` is not a replacement for the ABC at the module-wide rebind
#: boundary, even though outcome identity happened to survive one fixture.
TRAIN_ABC_SYMBOLS = ("Mapping", "MutableMapping")


def build_installer(
    *,
    abc_symbols: "tuple[str, ...]" = TRAIN_ABC_SYMBOLS,
    verify: bool = False,
    strict: bool = False,
) -> accel.Installer:
    """AX's registry plus this lane's cuts, in one installer."""

    installer = accel.build_installer(
        abc_symbols=abc_symbols, verify=verify, strict=strict
    )
    installer.register(make_authority_hash_content_memo_patch(verify=verify))
    installer.register(make_proof_hash_content_memo_patch(verify=verify))
    for patch_id in SPLIT_HASH_MEMO_TARGETS:
        installer.register(
            make_split_hash_content_memo_patch(patch_id, verify=verify)
        )
    installer.register(
        make_attribution_fields_content_memo_patch(verify=verify)
    )
    from src.research_infra.train_engine import resident_event_sink

    installer.register(resident_event_sink.make_patch())
    installer.register(make_ledger_projection_patch())
    installer.register(make_cost_attribution_provenance_patch())
    installer.register(make_missed_pool_projection_patch())
    installer.register(make_decision_semantics_projection_patch())
    installer.register(make_semantic_sidecar_projection_patch())
    installer.register(make_condition_feature_propagation_patch())
    installer.register(make_hard_eligibility_observability_patch())
    return installer


def resolve_patches(spec: str | None) -> list[str]:
    """Resolve named lane sets while retaining CD's command spellings."""

    if spec is None:
        return list(TRAIN_DEFAULT_PATCHES)
    text = spec.strip().lower()
    if text in {"none", ""}:
        return []
    if text == "hcb2-safe":
        return list(HCB2_COMPUTE_SAFE_PATCHES)
    if text in {"safe", "safe+projection", "safe+projection+pool"}:
        return list(TRAIN_SAFE_SET_PATCHES)
    if text == "safe+conditions":
        return list(TRAIN_CONDITION_FEATURE_PATCHES)
    if text == "safe+hard-eligibility-observability":
        return [
            *TRAIN_SAFE_SET_PATCHES,
            HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID,
        ]
    selected = [item.strip() for item in spec.split(",") if item.strip()]
    if HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID in selected:
        selected = [
            item
            for item in selected
            if item != HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID
        ] + [HARD_ELIGIBILITY_OBSERVABILITY_PATCH_ID]
    return selected

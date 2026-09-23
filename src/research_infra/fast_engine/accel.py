"""Runtime accelerations for the frozen sealed engine.

Every acceleration in this module is installed at *runtime*, into already
imported modules. No bound file's bytes change, so the R2 input-binding drift
check and the execution-seal digest are both untouched (CLAUDE.md H1).

Each acceleration carries three things, and refuses to be merged without them:

1. an **identity argument** -- why the patched path produces the same value as
   the frozen path;
2. a **verifier** -- a runtime mode that computes both answers and counts
   disagreements, so the identity argument is measured rather than asserted;
3. an **economic backstop** -- the reproduction test in ``reproduction.py``,
   which is what actually decides whether the fast engine ships.

The design rule that fell out of measurement: a metaclass ``__instancecheck__``
surrogate is *slower* than ``abc``'s own C-cached check (126 ns vs 88 ns on this
machine), so the only real win is rebinding to concrete types (17 ns). That
makes exhaustiveness a measurement obligation, not a style choice -- hence
``verify`` mode.
"""

from __future__ import annotations

import collections
import collections.abc as cabc
import sys
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable

# ---------------------------------------------------------------------------
# ABC isinstance dispatch
# ---------------------------------------------------------------------------

# The modules whose isinstance dispatch the sampled profile attributes 80.0 s of
# 1052.8 s self-time to (<frozen abc>:__instancecheck__ 65.8, __subclasscheck__
# 9.9, _collections_abc:__subclasshook__ 4.3).
ABC_HOT_MODULES = (
    "src.research_infra.v4_timewarp_simulated_live_research_loop",
    "src.research.moonshot_scheduler_v4_best_trade_allocator",
    "src.research_infra.replay_compact_event_sink",
    "src.components.selector_v4",
    "src.components.ultimate_candidate_package",
)

# symbol -> (real abc, concrete replacement)
#
# ``Mapping`` -> ``dict``: every mapping the engine builds is a dict or a dict
# subclass (``_FrozenPackageAuthorityPayload`` is ``dict[str, Any]``). ``dict``
# is subscriptable, so a stray runtime ``Mapping[str, Any]`` still evaluates.
#
# ``Sequence`` -> ``(list, tuple)``: NOT equivalent in general -- ``str``,
# ``bytes`` and ``range`` are Sequences and are not in the tuple. At the hot
# call sites the very next clause excludes ``str``/``bytes``/``bytearray``
# anyway, so the outcome is unchanged; ``verify`` mode is what establishes that
# for every site actually exercised, and this symbol is disabled by default
# until a verify run says otherwise.
ABC_CONCRETE = {
    "Mapping": (cabc.Mapping, dict),
    "MutableMapping": (cabc.MutableMapping, dict),
    "Sequence": (cabc.Sequence, (list, tuple)),
}

ABC_DEFAULT_SYMBOLS = ("Mapping", "MutableMapping")


class VerifyMismatch(RuntimeError):
    """A concrete-type replacement disagreed with the abc it replaced."""


@dataclass
class _VerifyStats:
    checks: int = 0
    mismatches: int = 0
    mismatch_types: collections.Counter = field(default_factory=collections.Counter)


VERIFY_STATS: dict[str, _VerifyStats] = {}


def _verifying_type(symbol: str, real: Any, concrete: Any, strict: bool) -> type:
    """Build a check-both-and-compare stand-in used only by ``verify`` mode."""

    stats = VERIFY_STATS.setdefault(symbol, _VerifyStats())

    class _VerifyMeta(type):
        def __instancecheck__(cls, obj: Any) -> bool:
            truth = isinstance(obj, real)
            fast = isinstance(obj, concrete)
            stats.checks += 1
            if truth != fast:
                stats.mismatches += 1
                stats.mismatch_types[type(obj).__name__] += 1
                if strict:
                    raise VerifyMismatch(
                        f"{symbol}: isinstance({type(obj).__name__}) "
                        f"abc={truth} concrete={fast}"
                    )
            return truth

        def __subclasscheck__(cls, sub: type) -> bool:
            return issubclass(sub, real)

        def __getitem__(cls, item: Any) -> Any:
            return real[item]

    return _VerifyMeta(f"Verifying{symbol}", (), {})


# ---------------------------------------------------------------------------
# patch registry
# ---------------------------------------------------------------------------


@dataclass
class Patch:
    """One runtime acceleration, with the evidence obligations it carries."""

    patch_id: str
    summary: str
    identity_argument: str
    apply: Callable[[], None]
    revert: Callable[[], None]
    default_on: bool = True
    # False means: this patch changes something an R2-bound verifier reads, so a
    # run using it can never be presented as satisfying the sealed lane. It may
    # still be perfectly sound as a research instrument -- but the distinction
    # has to be in the receipt, not in a reader's memory.
    sealed_compatible: bool = True


class Installer:
    """Applies and reverts a named set of patches, and reports what it did."""

    def __init__(self) -> None:
        self._patches: dict[str, Patch] = {}
        self._applied: list[str] = []

    def register(self, patch: Patch) -> None:
        if patch.patch_id in self._patches:
            raise ValueError(f"duplicate_patch_id:{patch.patch_id}")
        self._patches[patch.patch_id] = patch

    @property
    def registered(self) -> tuple[str, ...]:
        return tuple(self._patches)

    @property
    def applied(self) -> tuple[str, ...]:
        return tuple(self._applied)

    def install(self, patch_ids: "list[str] | tuple[str, ...] | None" = None) -> list[str]:
        if patch_ids is None:
            selected = [p.patch_id for p in self._patches.values() if p.default_on]
        else:
            selected = list(patch_ids)
        unknown = [p for p in selected if p not in self._patches]
        if unknown:
            raise ValueError(f"unknown_patch_ids:{sorted(unknown)}")
        for patch_id in selected:
            if patch_id in self._applied:
                continue
            self._patches[patch_id].apply()
            self._applied.append(patch_id)
        return list(self._applied)

    def revert_all(self) -> None:
        for patch_id in reversed(self._applied):
            self._patches[patch_id].revert()
        self._applied.clear()

    def manifest(self) -> dict[str, Any]:
        applied_incompatible = [
            p.patch_id
            for p in self._patches.values()
            if p.patch_id in self._applied and not p.sealed_compatible
        ]
        return {
            "applied": list(self._applied),
            "sealed_lane_compatible": not applied_incompatible,
            "applied_sealed_incompatible": applied_incompatible,
            "available": [
                {
                    "patch_id": p.patch_id,
                    "summary": p.summary,
                    "identity_argument": p.identity_argument,
                    "default_on": p.default_on,
                    "sealed_compatible": p.sealed_compatible,
                }
                for p in self._patches.values()
            ],
        }


# ---------------------------------------------------------------------------
# P1 - concrete-type isinstance dispatch
# ---------------------------------------------------------------------------


def _module(name: str) -> ModuleType | None:
    return sys.modules.get(name)


def make_abc_patch(
    *,
    symbols: "tuple[str, ...]" = ABC_DEFAULT_SYMBOLS,
    modules: "tuple[str, ...]" = ABC_HOT_MODULES,
    verify: bool = False,
    strict: bool = False,
) -> Patch:
    """Rebind abc aliases in the hot modules to concrete types (or verifiers).

    The modules all carry ``from __future__ import annotations``, so their
    ``Mapping[str, Any]`` annotations are strings that are never evaluated; the
    rebinding therefore only reaches ``isinstance``/``issubclass`` call sites and
    any runtime subscript, which ``dict`` supports natively.
    """

    saved: dict[tuple[str, str], Any] = {}

    def apply() -> None:
        for module_name in modules:
            module = _module(module_name)
            if module is None:
                continue
            for symbol in symbols:
                if not hasattr(module, symbol):
                    continue
                real, concrete = ABC_CONCRETE[symbol]
                if getattr(module, symbol) is not real:
                    # Someone else already rebound it; leave it alone.
                    continue
                saved[(module_name, symbol)] = real
                replacement = (
                    _verifying_type(symbol, real, concrete, strict)
                    if verify
                    else concrete
                )
                setattr(module, symbol, replacement)

    def revert() -> None:
        for (module_name, symbol), real in saved.items():
            module = _module(module_name)
            if module is not None:
                setattr(module, symbol, real)
        saved.clear()

    mode = "verify" if verify else "concrete"
    return Patch(
        patch_id="abc_concrete_types",
        summary=(
            f"rebind {sorted(symbols)} to concrete types in {len(modules)} hot "
            f"modules ({mode} mode)"
        ),
        identity_argument=(
            "abc.Mapping's only instances in this engine are dict and dict "
            "subclasses; isinstance against a concrete type is 5.2x cheaper "
            "than abc's C-cached __instancecheck__ (17 ns vs 88 ns measured). "
            "verify mode computes both and counts disagreements."
        ),
        apply=apply,
        revert=revert,
    )


def verify_report() -> dict[str, Any]:
    """What ``verify`` mode observed -- the evidence for the identity argument."""

    report: dict[str, Any] = {
        symbol: {
            "checks": stats.checks,
            "mismatches": stats.mismatches,
            "mismatch_types": dict(stats.mismatch_types),
        }
        for symbol, stats in VERIFY_STATS.items()
    }
    if MEMO_STATS:
        report["authority_hash_memo"] = memo_report()
    return report


def reset_verify_stats() -> None:
    VERIFY_STATS.clear()


# ---------------------------------------------------------------------------
# P2 - object-identity memo for the authority payload hash
# ---------------------------------------------------------------------------
#
# The first audit's sampled profile puts 210.4 s of 1102.3 s wall (19.1 %)
# inside `package_new_entry_authority_payload_hash_sha256`, reached from the
# selection finalizer via `signed_envelope_failures` (269.0 s) and
# `package_new_entry_authority_immutable_payload_failures` (238.9 s). Both of
# those validators pull the SAME `package_new_entry_authority_payload` object
# out of the surface and hash it independently, and the finalizer walks a
# candidate's nested envelope surfaces repeatedly.
#
# The engine already caches this hash -- but only for
# `_FrozenPackageAuthorityPayload` instances (on the object) and, for everything
# else, behind a content cache whose key requires canonicalising and
# JSON-encoding the payload first. That is the whole expense, so the existing
# cache saves the sha256 and none of the cost.

MEMO_MAX_ENTRIES = 4096


@dataclass
class _MemoStats:
    calls: int = 0
    hits: int = 0
    misses: int = 0
    frozen_passthrough: int = 0
    unhashable_passthrough: int = 0
    verified: int = 0
    mismatches: int = 0


MEMO_STATS: dict[str, _MemoStats] = {}


def memo_report() -> dict[str, Any]:
    return {
        name: {
            "calls": s.calls,
            "hits": s.hits,
            "misses": s.misses,
            "frozen_passthrough": s.frozen_passthrough,
            "unhashable_passthrough": s.unhashable_passthrough,
            "hit_rate": round(s.hits / s.calls, 4) if s.calls else 0.0,
            "verified": s.verified,
            "mismatches": s.mismatches,
        }
        for name, s in MEMO_STATS.items()
    }


def reset_memo_stats() -> None:
    MEMO_STATS.clear()


def make_authority_hash_memo_patch(*, verify: bool = False) -> Patch:
    """Memoise the authority payload hash on the payload object's identity.

    Correctness rests on two things, and both are enforced rather than assumed:

    * **id reuse is impossible while an entry lives.** The memo holds a strong
      reference to the payload alongside its digest, so CPython cannot recycle
      that ``id()`` for a different object until the entry is evicted. The
      ``entry_payload is payload`` guard is therefore always true on a key hit;
      it stays in as a tripwire rather than as logic.
    * **in-place mutation would poison the memo.** The payload is the engine's
      *immutable* authority payload -- ``_FrozenPackageAuthorityPayload`` raises
      on every mutator, and the plain-dict payloads are built once and read
      thereafter. ``verify`` mode recomputes the digest on every hit and counts
      disagreements, which is what turns that sentence into a measurement.

    Frozen payloads are passed straight through: the engine's own on-object
    cache already handles them, and duplicating it here would only add a layer.
    """

    stats = MEMO_STATS.setdefault("authority_payload_hash", _MemoStats())
    memo: collections.OrderedDict[int, tuple[Any, str]] = collections.OrderedDict()
    saved: dict[tuple[str, str], Any] = {}

    targets = (
        ("src.research.moonshot_scheduler_v4_best_trade_allocator", None),
        ("src.research_infra.v4_timewarp_simulated_live_research_loop", None),
        ("src.components.selector_v4", None),
    )
    attribute = "package_new_entry_authority_payload_hash_sha256"

    def apply() -> None:
        allocator = _module("src.research.moonshot_scheduler_v4_best_trade_allocator")
        if allocator is None:
            return
        original = getattr(allocator, attribute)
        frozen_type = getattr(allocator, "_FrozenPackageAuthorityPayload", ())

        def memoised(payload: Any) -> str:
            stats.calls += 1
            if isinstance(payload, frozen_type):
                stats.frozen_passthrough += 1
                return original(payload)
            try:
                key = id(payload)
            except TypeError:  # pragma: no cover - defensive
                stats.unhashable_passthrough += 1
                return original(payload)
            entry = memo.get(key)
            if entry is not None and entry[0] is payload:
                stats.hits += 1
                if verify:
                    stats.verified += 1
                    recomputed = original(payload)
                    if recomputed != entry[1]:
                        stats.mismatches += 1
                        return recomputed
                memo.move_to_end(key)
                return entry[1]
            stats.misses += 1
            digest = original(payload)
            memo[key] = (payload, digest)
            memo.move_to_end(key)
            while len(memo) > MEMO_MAX_ENTRIES:
                memo.popitem(last=False)
            return digest

        for module_name, _ in targets:
            module = _module(module_name)
            if module is None or not hasattr(module, attribute):
                continue
            saved[(module_name, attribute)] = getattr(module, attribute)
            setattr(module, attribute, memoised)

    def revert() -> None:
        for (module_name, name), value in saved.items():
            module = _module(module_name)
            if module is not None:
                setattr(module, name, value)
        saved.clear()
        memo.clear()

    return Patch(
        patch_id="authority_hash_identity_memo",
        summary=(
            "memoise package_new_entry_authority_payload_hash_sha256 on payload "
            "object identity across the allocator, timewarp loop and selector "
            "-- MEASURED NET NEGATIVE, default-off, see identity_argument"
        ),
        default_on=False,
        identity_argument=(
            "The function is pure. The memo holds a strong reference to each "
            "keyed payload, so id() reuse cannot alias two objects; the only "
            "remaining hazard is in-place mutation of an authority payload, "
            "which the engine's own immutability contract forbids and which "
            "verify mode recomputes and counts. CORRECTNESS HELD (0 mismatches); "
            "the patch was turned off on ECONOMICS: measured hit rate 0.11 % "
            "over 52.0 M calls on the 2-day fixture, because the caller rebuilds "
            "the payload as a NEW dict each time, so an identity key can never "
            "hit. It saved ~0.2 s, cost ~5 s of id() lookups on 52 M calls and "
            "+270 MB of peak RSS."
        ),
        apply=apply,
        revert=revert,
    )


# ---------------------------------------------------------------------------
# P3 - identity memo for the attribution-field builder  (NOT default-on)
# ---------------------------------------------------------------------------
#
# `package_new_entry_authority_attribution_fields` is the single biggest node in
# the first audit's cumulative tree: 288.4 s of 1102.3 s (26.2 %), reached both
# from the selection finalizer (303.4 s) and from
# `execution_fillability_alias_fields` (277.8 s), which calls it per surface.
#
# It is a pure projection of its surfaces -- but its surfaces are candidate rows
# and packets, and rows DO get fields spliced into them during a day. That makes
# the in-place-mutation hazard materially larger than for P2's immutable
# authority payload, so this patch is **off by default** and ships only on a
# verify run that measures zero mismatches. Enabling it without that measurement
# is exactly the "fast wrong engine" the commission refuses.


def make_attribution_fields_memo_patch(*, verify: bool = False) -> Patch:
    """Memoise the attribution-field projection on its surfaces' identities."""

    stats = MEMO_STATS.setdefault("attribution_fields", _MemoStats())
    memo: collections.OrderedDict[tuple[Any, ...], tuple[tuple[Any, ...], dict[str, Any]]] = (
        collections.OrderedDict()
    )
    saved: dict[str, Any] = {}
    module_name = "src.research_infra.v4_timewarp_simulated_live_research_loop"
    attribute = "package_new_entry_authority_attribution_fields"

    def apply() -> None:
        module = _module(module_name)
        if module is None or not hasattr(module, attribute):
            return
        original = getattr(module, attribute)

        def memoised(
            *surfaces: Any,
            prefix: str = "",
            validate_against_outer_projection: bool = True,
        ) -> dict[str, Any]:
            stats.calls += 1
            key = (
                tuple(id(surface) for surface in surfaces),
                prefix,
                validate_against_outer_projection,
            )
            entry = memo.get(key)
            if entry is not None and all(
                held is given for held, given in zip(entry[0], surfaces)
            ):
                stats.hits += 1
                if verify:
                    stats.verified += 1
                    recomputed = original(
                        *surfaces,
                        prefix=prefix,
                        validate_against_outer_projection=(
                            validate_against_outer_projection
                        ),
                    )
                    if recomputed != entry[1]:
                        stats.mismatches += 1
                        return recomputed
                memo.move_to_end(key)
                # A fresh outer dict per call, sharing the same nested objects --
                # exactly what the unmemoised projection returns.
                return dict(entry[1])
            stats.misses += 1
            value = original(
                *surfaces,
                prefix=prefix,
                validate_against_outer_projection=validate_against_outer_projection,
            )
            memo[key] = (surfaces, value)
            memo.move_to_end(key)
            while len(memo) > MEMO_MAX_ENTRIES:
                memo.popitem(last=False)
            return dict(value)

        saved[attribute] = original
        setattr(module, attribute, memoised)

    def revert() -> None:
        module = _module(module_name)
        if module is not None and attribute in saved:
            setattr(module, attribute, saved[attribute])
        saved.clear()
        memo.clear()

    return Patch(
        patch_id="attribution_fields_identity_memo",
        summary=(
            "memoise package_new_entry_authority_attribution_fields on surface "
            "identity (26.2 % of wall in the audit's cumulative tree)"
        ),
        identity_argument=(
            "The projection is pure and the memo returns a fresh outer dict "
            "sharing the same nested objects, which is what the unmemoised call "
            "returns. Strong references to the surfaces make id() aliasing "
            "impossible. The open hazard is in-place mutation of a surface "
            "between calls -- rows ARE spliced during a day -- so this patch is "
            "default-off until a verify run measures zero mismatches."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# P4 - the evidence dial's one honest member
# ---------------------------------------------------------------------------
#
# `current_summary_v2_contract_for_outputs` re-opens every ledger the run has
# just written, JSON-decodes each row and re-certifies it (29.4 s of 1102.3 s in
# the audit's tree). Its RETURN VALUE does not depend on the rows at all --
# `current_summary_v2_contract_for_rows` builds the contract dict from three
# constants before the loop and returns that same dict afterwards, so the loop
# is pure validation that either raises or does nothing.
#
# Skipping it is therefore exactly and only "do not re-prove what the frozen run
# already proved". It is default-off, and any run that uses it must say so --
# which is why it is a named patch in the receipt rather than a silent default.


def make_skip_ledger_recertification_patch() -> Patch:
    """Skip the post-hoc re-read and re-certification of already-written rows."""

    saved: dict[str, Any] = {}
    module_name = "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    attribute = "current_summary_v2_contract_for_rows"

    def apply() -> None:
        module = _module(module_name)
        if module is None or not hasattr(module, attribute):
            return
        original = getattr(module, attribute)

        def certified_without_rereading(rows: Any) -> dict[str, Any]:
            # Consume nothing: the generator is never iterated, so the ledger
            # files are never re-opened. The contract returned is byte-identical
            # to the frozen path's, which builds it from module constants.
            return original(())

        saved[attribute] = original
        setattr(module, attribute, certified_without_rereading)

    def revert() -> None:
        module = _module(module_name)
        if module is not None and attribute in saved:
            setattr(module, attribute, saved[attribute])
        saved.clear()

    return Patch(
        patch_id="skip_post_hoc_ledger_recertification",
        summary=(
            "skip re-reading and re-certifying already-written ledger rows "
            "(29.4 s of 1102.3 s in the audit's cumulative tree)"
        ),
        identity_argument=(
            "current_summary_v2_contract_for_rows builds its return value from "
            "three module constants BEFORE iterating, and returns that same "
            "object after; the loop can only raise. Calling it with an empty "
            "iterable returns the identical contract and skips the re-read. The "
            "only behaviour lost is a second proof of rows the frozen run "
            "already certified."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# P5 - cyclic GC during the day chunk  (SEALED-INCOMPATIBLE, default off)
# ---------------------------------------------------------------------------
#
# The engine disables cyclic GC for the whole chunk
# (`attempt5:16838-16839`) and, with `chunk_size = 1`, a chunk is one replay
# day. That is exactly the window in which THIRD_REVIEW A1 measured the heap
# ramping 0 -> 5.5 GB and then collapsing at the day boundary -- so part of that
# ramp is uncollected cyclic garbage rather than live evidence.
#
# **The sealed lane cannot take this lever.** The R2-bound verifier
# `verify_denominator_to_deployment_execution.py:5161-5167` requires
# `automatic_gc_enabled_before/after_explicit_collection` to be exactly False,
# so a run with GC left on fails the sealed verifier by construction. Any real
# fix to the intra-day ramp is therefore a contract regeneration, not a runtime
# flag -- which is worth knowing before anyone budgets the memory work.
#
# It changes no computed value: cyclic collection alters when unreachable
# objects are freed, never what a reachable object holds.


def make_gc_during_chunk_patch(*, gen0_threshold: int = 50_000) -> Patch:
    """Leave cyclic GC enabled inside the day chunk, at a coarse threshold."""

    saved: dict[str, Any] = {}
    module_name = "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"

    def apply() -> None:
        import gc as real_gc

        module = _module(module_name)
        if module is None:
            return
        saved["gc"] = module.gc
        saved["threshold"] = real_gc.get_threshold()

        class _GcShim:
            """Truthful about state; a no-op only for the in-chunk disable."""

            suppressed_disables = 0

            def __getattr__(self, name: str) -> Any:
                return getattr(real_gc, name)

            def disable(self) -> None:
                _GcShim.suppressed_disables += 1

            def isenabled(self) -> bool:
                return real_gc.isenabled()

        real_gc.enable()
        real_gc.set_threshold(gen0_threshold, 20, 20)
        real_gc.freeze()
        module.gc = _GcShim()

    def revert() -> None:
        import gc as real_gc

        module = _module(module_name)
        if module is not None and "gc" in saved:
            module.gc = saved["gc"]
        if "threshold" in saved:
            real_gc.set_threshold(*saved["threshold"])
        real_gc.unfreeze()
        saved.clear()

    return Patch(
        patch_id="gc_during_chunk",
        summary=(
            f"leave cyclic GC enabled inside the day chunk at gen0="
            f"{gen0_threshold} instead of disabling it for the whole day"
        ),
        identity_argument=(
            "Cyclic collection changes when unreachable objects are freed, "
            "never what a reachable object holds, so no computed value moves. "
            "It DOES flip the two automatic_gc_enabled_* checkpoint fields, "
            "which an R2-bound verifier requires to be False -- hence "
            "sealed_compatible=False."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
        sealed_compatible=False,
    )


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

# `authority_hash_identity_memo` was default-on when the A/B was measured and is
# now off: its hit rate on the 2-day fixture is 0.11 % over 52.0 M calls, so it
# bought ~0.2 s, cost ~5 s of id() lookups, and added +270 MB of peak RSS. The
# 1.061x figure in the receipt was measured WITH it on; P1 alone has not been
# separately benchmarked, but it is bounded below by that measurement because
# everything removed was net cost.
DEFAULT_PATCHES = ("abc_concrete_types",)

# The `--evidence` dial. `full` reproduces the frozen engine's evidence
# behaviour exactly; `decision` keeps everything a decision or a fail-closed
# guard reads and drops the post-hoc re-proof; `off` is `decision` today and is
# the slot the deeper emission redesign lands in.
EVIDENCE_LEVELS = {
    "full": (),
    "decision": ("skip_post_hoc_ledger_recertification",),
    "off": ("skip_post_hoc_ledger_recertification",),
}


def build_installer(
    *,
    abc_symbols: "tuple[str, ...]" = ABC_DEFAULT_SYMBOLS,
    verify: bool = False,
    strict: bool = False,
) -> Installer:
    installer = Installer()
    installer.register(
        make_abc_patch(symbols=abc_symbols, verify=verify, strict=strict)
    )
    installer.register(make_authority_hash_memo_patch(verify=verify))
    installer.register(make_attribution_fields_memo_patch(verify=verify))
    installer.register(make_skip_ledger_recertification_patch())
    installer.register(make_gc_during_chunk_patch())
    return installer


def patches_for(
    *, evidence: str = "full", extra: "tuple[str, ...]" = DEFAULT_PATCHES
) -> list[str]:
    """Resolve an ``--evidence`` level plus an explicit patch set into ids."""

    if evidence not in EVIDENCE_LEVELS:
        raise ValueError(f"unknown_evidence_level:{evidence}")
    resolved = list(extra)
    for patch_id in EVIDENCE_LEVELS[evidence]:
        if patch_id not in resolved:
            resolved.append(patch_id)
    return resolved

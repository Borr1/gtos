"""Locate the sealed January inputs and build the frozen engine's own args.

Read-only. Every path here points at the *producing* worktree, because the
sealed source authority pins absolute paths and rejects byte-identical copies
elsewhere (CLAUDE.md H4, ``fresh_source_authority_path_binding_mismatch``).
This module never writes to any of them.

The argument construction is deliberately the frozen runner's own
``build_standard_args`` -- not a reimplementation -- so the fast engine cannot
drift from the sealed execution surface by accident. A bounded fixture records
three engineering-only deviations: the calendar-month window, the absolute-
path pin neutralisation already used by the audit's profiling harness
(``docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py``),
and serial source prewarming. The last removes ``ProcessPoolExecutor`` lifecycle
from interruptible train-lane probes after Session CK found three orphaned CD
pools. Full-month arms retain the frozen runner's worker count. Every deviation
is recorded so no reader can mistake a bounded fixture for a sealed arm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# The worktree that PRODUCED the sealed January evidence. Its absolute path is
# baked into the source authority; reading from anywhere else fails closed.
PRODUCING_WORKTREE = Path("/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719")

JANUARY_EVIDENCE = (
    PRODUCING_WORKTREE
    / ".hermes/evidence/phase-d/january-post-acceleration-source-20260723T225928Z"
)
JANUARY_SELECTION_RECEIPT = (
    PRODUCING_WORKTREE
    / ".hermes/evidence/task4/source-bundle-selection-refresh-20260722-r5"
    / "CURRENT_SOURCE_SELECTION_RECEIPT.json"
)

ROUTE_RELATIVE = Path(
    "research/operations"
    "/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    "/attempt_5_typed_sparse"
)

# R2 is the contract of record for every forward run (CLAUDE.md H1). R1 stays
# untouched as January's sealed contract of record.
R2_CONTRACT_RELATIVE = Path(
    "research/operations"
    "/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    "/B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
)

ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")

BOUNDED_PREWARM_POLICY = "serial_bounded_fixture_no_process_pool"
SEALED_PREWARM_POLICY = "runner_default_not_overridden"


class SealedInputsUnavailable(RuntimeError):
    """The sealed January inputs are not reachable from this machine."""


@dataclass(frozen=True)
class SealedJanuary:
    """Every read-only input a January arm needs, resolved and existence-checked."""

    evidence_root: Path
    selection_receipt: Path
    seal: dict[str, Any]
    prepared_day_pack_root: Path
    prepared_pack_authority: Path
    contract: Path

    @property
    def window_start(self) -> str:
        return str(self.seal["window_binding"]["start"])

    @property
    def window_end(self) -> str:
        return str(self.seal["window_binding"]["end"])


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SealedInputsUnavailable(message)


def resolve_sealed_january(
    repo_root: Path, *, require_prepared_day_packs: bool = True
) -> SealedJanuary:
    """Resolve the sealed January inputs, or fail with the exact missing path.

    ``require_prepared_day_packs=False`` is for callers that use this only as an
    argument-construction shell and replace ``prepared_day_pack_root`` with their
    own before the value is ever read — the lane arm does exactly that at
    ``lane_rematerialization.py:2475``. January's 20 GB of prepared day packs are
    then a hard dependency on a *parked campaign's* bulk evidence for a run that
    never opens it, which is how a lane arm came to die of
    ``january_prepared_day_pack_root_absent`` on 2026-08-12. The root is still
    resolved and returned so the caller keeps the authority record; only the
    on-disk existence check is relaxed. Every other input stays mandatory.
    """

    evidence = JANUARY_EVIDENCE
    _require(evidence.is_dir(), f"january_evidence_root_absent:{evidence}")
    for name in ("typed-cache", "tick-sparse-cache", "materialization-current"):
        _require((evidence / name).is_dir(), f"january_{name}_absent")
    _require(
        JANUARY_SELECTION_RECEIPT.is_file(),
        f"january_source_selection_absent:{JANUARY_SELECTION_RECEIPT}",
    )

    seal_path = evidence / "JANUARY_EXECUTION_SEAL_R3.json"
    _require(seal_path.is_file(), f"january_execution_seal_absent:{seal_path}")
    seal = json.loads(seal_path.read_text())

    authority = evidence / "JANUARY_PREPARED_PACK_REBIND_AUTHORITY_R3.json"
    _require(authority.is_file(), f"january_pack_authority_absent:{authority}")
    pack_root = Path(json.loads(authority.read_text())["prepared_day_pack_root"])
    if require_prepared_day_packs:
        _require(
            pack_root.is_dir(), f"january_prepared_day_pack_root_absent:{pack_root}"
        )

    contract = repo_root / R2_CONTRACT_RELATIVE
    _require(contract.is_file(), f"r2_decision_contract_absent:{contract}")

    return SealedJanuary(
        evidence_root=evidence,
        selection_receipt=JANUARY_SELECTION_RECEIPT,
        seal=seal,
        prepared_day_pack_root=pack_root,
        prepared_pack_authority=authority,
        contract=contract,
    )


def build_january_args(
    *,
    repo_root: Path,
    arm_id: str,
    output_dir: Path,
    output_prefix: str,
    stop_after_day: str | None = None,
    sealed: SealedJanuary | None = None,
) -> Any:
    """Build the frozen runner's args for a January arm, optionally day-bounded.

    ``stop_after_day`` narrows the run to ``window_start..stop_after_day``. That
    is a FIXTURE, not a sealed arm: the sealed path hardcodes
    ``engineering_stop_after_day = None`` (CLAUDE.md H5), so a bounded run can
    never be presented as a sealed month. Pass ``None`` for the full arm.
    """

    if arm_id not in ARMS:
        raise SealedInputsUnavailable(f"unknown_arm:{arm_id}")

    from src.research_infra import b7_5_post_acceleration_runner as runner

    sealed = sealed or resolve_sealed_january(repo_root)
    src_binding = sealed.seal["source_authority_binding"]

    args = runner.build_standard_args(
        output_dir=output_dir,
        output_prefix=output_prefix,
        window_id="development_january",
        start=sealed.window_start,
        end=sealed.window_end,
        arm_id=arm_id,
        decision_contract_path=sealed.contract,
        source_bundle_dir=sealed.evidence_root / "materialization-current/bundle",
        source_selection_path=sealed.selection_receipt,
        source_authority_path=sealed.evidence_root / "FRESH_CURRENT_BUNDLE_AUTHORITY.json",
        source_authority_file_sha256=src_binding["file_sha256"],
        source_authority_root_sha256=src_binding["authority_root_sha256"],
        source_bundle_root_sha256=src_binding["bundle_root_sha256"],
        source_plan_digest_sha256=src_binding["source_plan_digest_sha256"],
        typed_cache_root=sealed.evidence_root / "typed-cache",
        tick_sparse_cache_root=sealed.evidence_root / "tick-sparse-cache",
        prepared_day_pack_root=sealed.prepared_day_pack_root,
        prepared_pack_authority_path=sealed.prepared_pack_authority,
    )

    if stop_after_day is not None:
        # The prepared pack is sealed for the whole month and the engine
        # requires exact set equality between pack roots and the chunk plan, so
        # a bounded fixture must narrow the declared roots to the days replayed.
        args.engineering_stop_after_day = stop_after_day
        roots = dict(args.expected_prepared_day_pack_roots)
        args.expected_prepared_day_pack_roots = {
            key: value for key, value in roots.items() if str(key[1]) <= stop_after_day
        }
        # Bounded train-lane probes are routinely interrupted while a cut is
        # being evaluated. The frozen runner's ProcessPoolExecutor left three
        # four-worker pools plus resource trackers orphaned after earlier CD
        # probes. This is an execution-topology hardening only: prewarm fills
        # the same immutable source cache and does not decide an outcome. Keep
        # the sealed/full-month path exactly on the runner default.
        args.bounded_prewarm_previous_workers = getattr(
            args, "source_prewarm_workers", None
        )
        args.source_prewarm_workers = 1
        args.bounded_prewarm_policy = BOUNDED_PREWARM_POLICY
    else:
        args.bounded_prewarm_previous_workers = None
        args.bounded_prewarm_policy = SEALED_PREWARM_POLICY
    return args


def prelude(args: Any) -> None:
    """Mirror ``run_sealed_arm``'s prelude, minus the two sub-window bindings."""

    from src.research_infra import b7_5_post_acceleration_runner as runner
    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )

    attempt5.bind_attempt5_finalizer_conflict_key_order()
    attempt5.configure_runtime_evidence_root(attempt5.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    runner.bind_fresh_source(args)
    shared = runner.current_shared_contract(args)
    args.expected_shared_execution_contract_sha256 = shared[
        "shared_execution_contract_digest_sha256"
    ]
    attempt5.configure_output_namespace(Path(args.output_dir))

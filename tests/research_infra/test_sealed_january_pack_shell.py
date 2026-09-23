"""The lane arm must not die of a parked campaign's bulk evidence.

On 2026-08-12 a disk reclamation removed January's `prepared-day-packs/` tree
(31 packs, 20.0 GB raw). Every *lane* arm then failed at
`january_prepared_day_pack_root_absent` — even though the lane replaces
`prepared_day_pack_root` with its own at `lane_rematerialization.py:2475`,
before the value is ever read. January was serving as an argument-construction
shell and nothing more, so the lane was blocked by an artifact it never opens.

These tests pin both halves of the fix: the shell caller may proceed without the
packs, and the sealed-arm caller — for which the pack root IS the authority —
must still fail closed. Behavioural, not source-string.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.fast_engine import sealed_inputs


def _january_pack_root() -> Path:
    authority = (
        sealed_inputs.JANUARY_EVIDENCE
        / "JANUARY_PREPARED_PACK_REBIND_AUTHORITY_R3.json"
    )
    if not authority.is_file():
        pytest.skip("January pack authority absent in this checkout")
    return Path(json.loads(authority.read_text())["prepared_day_pack_root"])


def _repo_root() -> Path:
    from src.research_infra import lane_rematerialization

    return lane_rematerialization.REPO_ROOT


def test_shell_caller_resolves_without_prepared_day_packs() -> None:
    """require_prepared_day_packs=False proceeds when the packs are absent."""
    if _january_pack_root().is_dir():
        pytest.skip("packs present — this asserts behaviour when they are not")

    sealed = sealed_inputs.resolve_sealed_january(
        _repo_root(), require_prepared_day_packs=False
    )
    # The authority record still carries the root; only the existence check relaxed.
    assert sealed.prepared_day_pack_root == _january_pack_root()
    assert sealed.evidence_root.is_dir()
    assert sealed.contract.is_file()


def test_sealed_arm_caller_still_fails_closed_without_packs() -> None:
    """The default must keep refusing: for a sealed arm the packs ARE the authority."""
    if _january_pack_root().is_dir():
        pytest.skip("packs present — this asserts behaviour when they are not")

    with pytest.raises(Exception) as excinfo:
        sealed_inputs.resolve_sealed_january(_repo_root())
    assert "january_prepared_day_pack_root_absent" in str(excinfo.value)


def test_relaxation_does_not_weaken_any_other_input() -> None:
    """Every non-pack January input stays mandatory under the relaxed flag."""
    evidence = sealed_inputs.JANUARY_EVIDENCE
    if not evidence.is_dir():
        pytest.skip("January evidence root absent in this checkout")

    for name in ("typed-cache", "tick-sparse-cache", "materialization-current"):
        assert (evidence / name).is_dir(), f"{name} must still be required"
    assert (evidence / "JANUARY_EXECUTION_SEAL_R3.json").is_file()
    assert (
        evidence / "JANUARY_PREPARED_PACK_REBIND_AUTHORITY_R3.json"
    ).is_file()

    sealed = sealed_inputs.resolve_sealed_january(
        _repo_root(), require_prepared_day_packs=False
    )
    assert sealed.seal, "execution seal must still be loaded, not stubbed"
    assert sealed.selection_receipt.is_file()


def test_lane_build_args_requests_the_shell_relaxation(monkeypatch) -> None:
    """The lane's own call site must not use the strict default.

    Behavioural: we intercept the real resolver and record how the lane called
    it, rather than grepping the source — a source assertion would pass against
    a wrong implementation.
    """
    from src.research_infra import lane_rematerialization

    captured: dict[str, object] = {}
    real = sealed_inputs.resolve_sealed_january

    def spy(repo_root, **kwargs):
        captured.update(kwargs)
        raise _StopAfterResolve

    class _StopAfterResolve(Exception):
        pass

    monkeypatch.setattr(sealed_inputs, "resolve_sealed_january", spy)

    inputs = object.__new__(lane_rematerialization.LaneWindowInputs)
    with pytest.raises(_StopAfterResolve):
        lane_rematerialization.LaneWindowInputs.build_args(
            inputs,
            arm_id="TEST",
            output_dir=Path("/tmp/does-not-matter"),
            output_prefix="TEST",
            stop_after_day=None,
        )

    assert captured.get("require_prepared_day_packs") is False, (
        "the lane must ask for the shell relaxation; without it the lane arm "
        "dies on a parked campaign's 20 GB of prepared day packs it never reads"
    )
    assert sealed_inputs.resolve_sealed_january is spy
    monkeypatch.setattr(sealed_inputs, "resolve_sealed_january", real)

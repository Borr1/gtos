from __future__ import annotations

from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_physical_reference_runner as physical,
)


def test_physical_reference_cli_exposes_only_fresh_output_namespace(
    tmp_path: Path,
) -> None:
    args = physical.parse_args(["--output-dir", str(tmp_path / "reference")])
    assert args.output_dir == tmp_path / "reference"
    with pytest.raises(SystemExit):
        physical.parse_args(
            [
                "--output-dir",
                str(tmp_path / "reference"),
                "--start",
                "2026-01-02",
            ]
        )


def test_physical_reference_args_are_exact_and_cache_free(tmp_path: Path) -> None:
    args = physical.physical_reference_args(tmp_path / "reference")

    assert args.start == replay.ATTEMPT5_START_DAY
    assert args.end == replay.ATTEMPT5_CONTRACT_END_DAY
    assert args.chunk_size == 1
    assert args.profiles == [replay.PROFILE_REPAIRED]
    assert args.symbols is None
    assert args.arm_id == "S0R0"
    assert args.accepted_physical_reference is True
    assert args.physical_reference_checkpoint_after_day == (
        replay.ATTEMPT5_PARITY_DAY
    )
    assert args.parity_gate_after_day is None
    assert args.stop_after_parity_gate is False
    assert args.source_acceleration_cache_root is None
    assert args.tick_sparse_cache_root is None
    assert args.runtime_evidence_root is None
    assert args.source_acceleration_bundle_dir == physical.SOURCE_BUNDLE_DIR
    assert "task8/source-bundle-consumer-rebind-20260723-r5" in str(
        physical.SOURCE_BUNDLE_DIR
    )
    assert "task8/source-bundle-consumer-rebind-20260723-r5" in str(
        physical.SOURCE_REBIND_AUTHORITY
    )
    assert args.expected_source_bundle_root_sha256 == (
        replay.ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256
    )


def test_physical_reference_shared_contract_preserves_economic_digest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args = physical.physical_reference_args(tmp_path / "reference")
    shared = {
        "valid": True,
        "shared_execution_contract_digest_sha256": "a" * 64,
    }
    monkeypatch.setattr(
        replay,
        "selection_sizing_factorial_binding_from_args",
        lambda _args: {"arm_id": "S0R0"},
    )
    monkeypatch.setattr(
        replay,
        "ultimate_package_runtime_input_contract",
        lambda: {"valid": True},
    )
    monkeypatch.setattr(
        replay,
        "requested_replay_symbols",
        lambda _symbols: ("EURUSD",),
    )
    monkeypatch.setattr(
        replay,
        "active_replay_symbol_universe",
        lambda _symbols: ("EURUSD",),
    )
    monkeypatch.setattr(
        replay,
        "broad_replay_execution_options_from_args",
        lambda _args, factorial_arm_binding: {"arm": factorial_arm_binding},
    )
    monkeypatch.setattr(
        replay,
        "broad_replay_shared_execution_contract",
        lambda **_kwargs: shared,
    )
    monkeypatch.setattr(
        physical,
        "split_shared_execution_contract",
        lambda _shared: {
            "economic_execution_contract_digest_sha256": (
                physical.EXPECTED_ECONOMIC_CONTRACT_DIGEST
            )
        },
    )

    assert physical._bind_shared_contract(args) == shared
    assert args.expected_shared_execution_contract_sha256 == "a" * 64

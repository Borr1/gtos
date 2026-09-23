"""Session CK: bounded fixtures cannot leak a multiprocessing prewarm pool."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.research_infra import b7_5_post_acceleration_runner as frozen_runner
from src.research_infra.fast_engine import sealed_inputs


def _sealed(tmp_path: Path) -> sealed_inputs.SealedJanuary:
    return sealed_inputs.SealedJanuary(
        evidence_root=tmp_path / "evidence",
        selection_receipt=tmp_path / "selection.json",
        seal={
            "window_binding": {"start": "2026-01-01", "end": "2026-01-31"},
            "source_authority_binding": {
                "file_sha256": "file",
                "authority_root_sha256": "authority",
                "bundle_root_sha256": "bundle",
                "source_plan_digest_sha256": "plan",
            },
        },
        prepared_day_pack_root=tmp_path / "packs",
        prepared_pack_authority=tmp_path / "pack-authority.json",
        contract=tmp_path / "contract.json",
    )


def _fake_standard_args(**kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(
        **kwargs,
        engineering_stop_after_day=None,
        source_prewarm_workers=4,
        expected_prepared_day_pack_roots={
            ("EURUSD", "2026-01-01"): "a",
            ("EURUSD", "2026-01-12"): "b",
            ("EURUSD", "2026-01-20"): "c",
        },
    )


def test_bounded_fixture_serializes_prewarm_and_records_the_override(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(frozen_runner, "build_standard_args", _fake_standard_args)

    args = sealed_inputs.build_january_args(
        repo_root=tmp_path,
        arm_id="S0R0",
        output_dir=tmp_path / "out",
        output_prefix="CK",
        stop_after_day="2026-01-12",
        sealed=_sealed(tmp_path),
    )

    assert args.engineering_stop_after_day == "2026-01-12"
    assert args.source_prewarm_workers == 1
    assert args.bounded_prewarm_previous_workers == 4
    assert args.bounded_prewarm_policy == sealed_inputs.BOUNDED_PREWARM_POLICY
    assert set(args.expected_prepared_day_pack_roots) == {
        ("EURUSD", "2026-01-01"),
        ("EURUSD", "2026-01-12"),
    }


def test_full_arm_keeps_the_frozen_runner_worker_count(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(frozen_runner, "build_standard_args", _fake_standard_args)

    args = sealed_inputs.build_january_args(
        repo_root=tmp_path,
        arm_id="S0R0",
        output_dir=tmp_path / "out",
        output_prefix="CK",
        sealed=_sealed(tmp_path),
    )

    assert args.engineering_stop_after_day is None
    assert args.source_prewarm_workers == 4
    assert args.bounded_prewarm_previous_workers is None
    assert args.bounded_prewarm_policy == sealed_inputs.SEALED_PREWARM_POLICY
    assert len(args.expected_prepared_day_pack_roots) == 3

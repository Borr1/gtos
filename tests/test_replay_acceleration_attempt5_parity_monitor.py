from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.research_infra import replay_acceleration_attempt5_parity_monitor as monitor


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_gate_request(
    *,
    namespace: Path,
    gate: Path,
    golden: Path,
    amendment: Path,
) -> dict[str, object]:
    verifier = Path(monitor.__file__).with_name(
        "replay_acceleration_real_parity_verifier.py"
    ).resolve()
    authority = {
        "golden_manifest_path": str(golden.resolve()),
        "golden_manifest_file_sha256": _file_sha256(golden),
        "golden_manifest_self_root_sha256": "a" * 64,
        "golden_root_sha256": "b" * 64,
        "opaque_result_surface_root_sha256": "c" * 64,
        "golden_amendment_path": str(amendment.resolve()),
        "golden_amendment_file_sha256": _file_sha256(amendment),
        "golden_amendment_self_root_sha256": "d" * 64,
        "fixed_verifier_module": monitor.VERIFIER_MODULE,
        "fixed_verifier_path": str(verifier),
        "fixed_verifier_file_sha256": _file_sha256(verifier),
    }
    core = {
        "schema": "gtos.replay_acceleration.real_s0r0_gate_request.v1",
        "accelerated_namespace_path": str(namespace.resolve()),
        "prospective_golden_authority": authority,
    }
    request = {
        **core,
        "gate_request_root_sha256": monitor.root(core),
    }
    gate.write_bytes(monitor.canonical_bytes(request) + b"\n")
    return authority


def _monitor_args(
    *,
    namespace: Path,
    gate: Path,
    golden: Path,
    report: Path,
    receipt: Path,
    evidence: Path,
    git_root: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        runner_pid=os.getpid(),
        namespace=namespace,
        git_root=git_root,
        golden_manifest=golden,
        gate_request=gate,
        report_output=report,
        receipt_output=receipt,
        monitor_receipt=evidence,
        timeout_seconds=10,
        poll_seconds=0.01,
    )


def test_monitor_invokes_unchanged_verifier_without_reading_economics(
    tmp_path: Path, monkeypatch
) -> None:
    namespace = tmp_path / "namespace"
    namespace.mkdir()
    gate = namespace / "GATE_REQUEST.json"
    gate.write_text("{}\n", encoding="ascii")
    golden = tmp_path / "golden.json"
    golden.write_text("{}\n", encoding="ascii")
    amendment = tmp_path / "amendment.json"
    amendment.write_text("{}\n", encoding="ascii")
    authority = _write_gate_request(
        namespace=namespace,
        gate=gate,
        golden=golden,
        amendment=amendment,
    )
    report = namespace / "REPORT.json"
    receipt = namespace / "RECEIPT.json"
    evidence = namespace / "MONITOR.json"

    def fake_run(command, *, cwd, check):
        assert command[2] == monitor.VERIFIER_MODULE
        assert cwd == tmp_path
        assert check is False
        report.write_text("{}\n", encoding="ascii")
        receipt.write_text("{}\n", encoding="ascii")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(monitor.subprocess, "run", fake_run)
    result = monitor.run_monitor(
        _monitor_args(
            namespace=namespace,
            gate=gate,
            golden=golden,
            report=report,
            receipt=receipt,
            evidence=evidence,
            git_root=tmp_path,
        )
    )
    persisted = json.loads(evidence.read_text(encoding="ascii"))
    assert result == persisted
    assert result["economic_values_exposed"] is False
    assert result["other_arms_launched"] is False
    assert result["broker_live_authority"] is False
    assert result["golden_manifest_sha256"] == authority[
        "golden_manifest_file_sha256"
    ]
    assert result["golden_amendment_sha256"] == authority[
        "golden_amendment_file_sha256"
    ]
    assert result["fixed_verifier_file_sha256"] == authority[
        "fixed_verifier_file_sha256"
    ]


def test_monitor_rejects_golden_not_bound_by_gate_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = tmp_path / "namespace"
    namespace.mkdir()
    gate = namespace / "GATE_REQUEST.json"
    golden = tmp_path / "golden.json"
    golden.write_text("{}\n", encoding="ascii")
    amendment = tmp_path / "amendment.json"
    amendment.write_text("{}\n", encoding="ascii")
    _write_gate_request(
        namespace=namespace,
        gate=gate,
        golden=golden,
        amendment=amendment,
    )
    unbound_golden = tmp_path / "unbound-golden.json"
    unbound_golden.write_text("{}\n", encoding="ascii")
    args = _monitor_args(
        namespace=namespace,
        gate=gate,
        golden=unbound_golden,
        report=namespace / "REPORT.json",
        receipt=namespace / "RECEIPT.json",
        evidence=namespace / "MONITOR.json",
        git_root=tmp_path,
    )
    monkeypatch.setattr(
        monitor.subprocess,
        "run",
        lambda *unused_args, **unused_kwargs: pytest.fail(
            "verifier must not run for unbound golden authority"
        ),
    )

    with pytest.raises(
        monitor.MonitorRejected,
        match="monitor_gate_request_authority_mismatch",
    ):
        monitor.run_monitor(args)


def test_monitor_rejects_pairwise_output_alias_before_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = tmp_path / "namespace"
    namespace.mkdir()
    gate = namespace / "GATE_REQUEST.json"
    golden = tmp_path / "golden.json"
    golden.write_text("{}\n", encoding="ascii")
    amendment = tmp_path / "amendment.json"
    amendment.write_text("{}\n", encoding="ascii")
    _write_gate_request(
        namespace=namespace,
        gate=gate,
        golden=golden,
        amendment=amendment,
    )
    aliased_output = namespace / "PARITY.json"
    args = _monitor_args(
        namespace=namespace,
        gate=gate,
        golden=golden,
        report=aliased_output,
        receipt=aliased_output,
        evidence=namespace / "MONITOR.json",
        git_root=tmp_path,
    )
    monkeypatch.setattr(
        monitor.subprocess,
        "run",
        lambda *unused_args, **unused_kwargs: pytest.fail(
            "verifier must not run for aliased outputs"
        ),
    )

    with pytest.raises(
        monitor.MonitorRejected,
        match="monitor_evidence_path_collision",
    ):
        monitor.run_monitor(args)


@pytest.mark.parametrize("symlink_role", ("namespace", "golden"))
def test_monitor_rejects_lexical_symlink_components(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    symlink_role: str,
) -> None:
    real_namespace = tmp_path / "real-namespace"
    real_namespace.mkdir()
    namespace = tmp_path / "namespace"
    namespace.symlink_to(real_namespace, target_is_directory=True)
    gate = real_namespace / "GATE_REQUEST.json"
    golden_target = tmp_path / "golden-target.json"
    golden_target.write_text("{}\n", encoding="ascii")
    golden = tmp_path / "golden.json"
    golden.symlink_to(golden_target)
    amendment = tmp_path / "amendment.json"
    amendment.write_text("{}\n", encoding="ascii")
    request_namespace = namespace if symlink_role == "namespace" else real_namespace
    request_golden = golden if symlink_role == "golden" else golden_target
    _write_gate_request(
        namespace=request_namespace,
        gate=gate,
        golden=request_golden,
        amendment=amendment,
    )
    args = _monitor_args(
        namespace=request_namespace,
        gate=gate,
        golden=request_golden,
        report=real_namespace / "REPORT.json",
        receipt=real_namespace / "RECEIPT.json",
        evidence=real_namespace / "MONITOR.json",
        git_root=tmp_path,
    )
    monkeypatch.setattr(
        monitor.subprocess,
        "run",
        lambda *unused_args, **unused_kwargs: pytest.fail(
            "verifier must not run through symlinked authority"
        ),
    )

    with pytest.raises(
        monitor.MonitorRejected,
        match="monitor_symlink_component_forbidden",
    ):
        monitor.run_monitor(args)


def test_monitor_has_no_runner_writer_or_policy_import() -> None:
    source = Path(monitor.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = (
        "replay_acceleration_attempt5_typed_sparse_runner",
        "replay_acceleration_real_parity_verifier",
        "v4_timewarp_simulated_live_research_loop",
    )
    assert not any(any(item in value for item in forbidden) for value in imports)


def test_monitor_rejects_fixed_verifier_change_between_check_and_exec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra.replay_acceleration_fixed_verifier_authority import (
        build_fixed_verifier_code_authority,
    )

    namespace = tmp_path / "namespace"
    namespace.mkdir()
    gate = namespace / "GATE_REQUEST.json"
    golden = tmp_path / "golden.json"
    golden.write_text("{}\n", encoding="ascii")
    amendment = tmp_path / "amendment.json"
    amendment.write_text("{}\n", encoding="ascii")
    authority = _write_gate_request(
        namespace=namespace,
        gate=gate,
        golden=golden,
        amendment=amendment,
    )
    successor = tmp_path / "successor-authority.json"
    successor.write_text("{}\n", encoding="ascii")
    fixed_code_authority, _identities = build_fixed_verifier_code_authority(
        Path(monitor.__file__).parent
    )
    authority.update(
        {
            "successor_authority_path": str(successor.resolve()),
            "successor_authority_file_sha256": _file_sha256(successor),
            "successor_authority_root_sha256": "e" * 64,
            "successor_authority_verification_root_sha256": "f" * 64,
            "economic_execution_contract_digest_sha256": "1" * 64,
            "fixed_verifier_code_authority": fixed_code_authority,
            "fixed_verifier_code_authority_root_sha256": (
                fixed_code_authority["authority_root_sha256"]
            ),
        }
    )
    core = {
        "schema": "gtos.replay_acceleration.real_s0r0_gate_request.v2",
        "accelerated_namespace_path": str(namespace.resolve()),
        "prospective_golden_authority": authority,
    }
    request = {**core, "gate_request_root_sha256": monitor.root(core)}
    gate.write_bytes(monitor.canonical_bytes(request) + b"\n")
    monkeypatch.setattr(
        monitor,
        "verify_successor_authority",
        lambda _path: {
            "authority_file_sha256": authority[
                "successor_authority_file_sha256"
            ],
            "authority_root_sha256": authority[
                "successor_authority_root_sha256"
            ],
            "verification_root_sha256": authority[
                "successor_authority_verification_root_sha256"
            ],
        },
    )
    identity_checks = 0

    def detect_change(_identities: object) -> None:
        nonlocal identity_checks
        identity_checks += 1
        if identity_checks == 2:
            raise monitor.FixedVerifierAuthorityError(
                "fixed_verifier_code_identity_changed"
            )

    monkeypatch.setattr(
        monitor,
        "assert_fixed_verifier_code_identity",
        detect_change,
    )
    report = namespace / "REPORT.json"
    receipt = namespace / "RECEIPT.json"

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        report.write_text("{}\n", encoding="ascii")
        receipt.write_text("{}\n", encoding="ascii")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(monitor.subprocess, "run", fake_run)
    with pytest.raises(
        monitor.MonitorRejected,
        match="monitor_fixed_verifier_changed",
    ):
        monitor.run_monitor(
            _monitor_args(
                namespace=namespace,
                gate=gate,
                golden=golden,
                report=report,
                receipt=receipt,
                evidence=namespace / "MONITOR.json",
                git_root=tmp_path,
            )
        )
    assert identity_checks == 2

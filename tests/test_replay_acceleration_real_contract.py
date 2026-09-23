from __future__ import annotations

import ast
from pathlib import Path

import pytest


def test_real_execution_contract_command_rejects_other_arm() -> None:
    from src.research_infra.replay_acceleration_real_contract_verifier import (
        _verify_command,
    )

    variant = {
        "shared_execution_contract_digest_sha256": "a" * 64,
        "argv": [
            "python3",
            "runner.py",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-31",
            "--chunk-size",
            "1",
            "--output-prefix",
            (
                "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_"
                "S0R0_SOURCE_REPAIRED_R3_CAP_R2"
            ),
            "--profiles",
            "repaired_package_conversion_v3",
            "--source-prewarm-workers",
            "1",
            "--parity-gate-after-day",
            "2026-01-07",
            "--arm-id",
            "S1R0",
            "--expected-shared-execution-contract-sha256",
            "a" * 64,
            "--streaming-proof-archive-root",
            "archive",
            "--stop-after-parity-gate",
            "--omit-candidate-ledger",
            "--omit-candidate-index-ledger",
            "--omit-packet-sidecar-ledger",
            "--compact-missed-ledger",
            "--compact-decision-ledger",
            "--compact-scorecard-ledger",
        ],
    }
    with pytest.raises(ValueError, match="execution_contract_arm_invalid"):
        _verify_command(variant, name="cold_bounded", expected_workers=1)


def test_real_execution_contract_verifier_does_not_import_writer_or_runner() -> None:
    verifier = Path(
        "src/research_infra/replay_acceleration_real_contract_verifier.py"
    )
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = (
        "run_broad_live_as_if_replay_harness",
        "replay_acceleration_real_contract",
    )
    assert not any(any(item in value for item in forbidden) for value in imports)

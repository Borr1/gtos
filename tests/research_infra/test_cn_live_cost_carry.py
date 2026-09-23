"""Session CN carry-package contract: reproducible, ordered, and broker-offline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PKG = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_live_cost_truth"
)


def test_carry_builder_reproduces_every_committed_payload_and_diff():
    result = subprocess.run(
        [sys.executable, str(PKG / "build_carry.py"), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS carry package reproducible" in result.stdout


def test_carry_payload_probe_is_broker_offline_and_behaviour_green():
    result = subprocess.run(
        [sys.executable, str(PKG / "verify_carry.py"), "--check", "payload"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"old": "PASSED"' in result.stdout
    assert '"new": "REFUSED"' in result.stdout
    assert '"unknown": "REFUSED"' in result.stdout
    assert '"v2_readable": true' in result.stdout


def test_manifest_activates_engine_last_and_carries_no_config():
    man = json.loads((PKG / "MANIFEST.json").read_text())
    files = sorted(man["files"], key=lambda row: row["copy_order"])

    assert [row["copy_order"] for row in files] == list(range(1, 8))
    assert files[-1]["repo_path"] == "src/components/broker_net_cost_engine.py"
    assert man["seal_exposure"]["changed_R2_bound_path"] == files[-1]["repo_path"]
    assert not any(row["repo_path"].startswith("config/") for row in files)
    assert man["proving_log_line"]["required_fields"] == {
        "modelled_cost_model_version": "vnext_selected_cell_pretrade_cost_model_v3",
        "modelled_commission_mode": "broker_true_commission_default_v1",
        "modelled_commission_cost_source_status": "captured",
        "modelled_commission_cost_artifact": "BROKER_TRUE_COSTS_V1.json",
        "modelled_cost_excludes": [],
    }

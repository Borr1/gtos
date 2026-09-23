from __future__ import annotations

import tempfile
from pathlib import Path

from src.research_infra import wave4i_integration_partition_gate as wave4i


ROOT = Path(__file__).resolve().parents[1]


def test_wave4i_wave5_launchability_is_exact():
    rows = wave4i.wave5_launchability_rows()
    statuses = {row["wave5_lane"]: row["launch_status"] for row in rows}

    assert statuses["wave5a_dataset_leakage_guard"] == "launchable_now_after_wave4i_commit"
    assert statuses["wave5b_baselines_calibration"] == "blocked_until_wave5a_dataset_hashes_exist"
    assert statuses["wave5c_challengers_local_training"] == "blocked_until_wave5b_baseline_floors_exist"
    assert statuses["wave5d_registry_runtime_packet_gate"] == "blocked_until_wave5a_wave5b_wave5c_outputs_exist"

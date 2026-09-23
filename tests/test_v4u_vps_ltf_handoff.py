import argparse
import json
from pathlib import Path

import pytest

from scripts.build_v4u_vps_ltf_handoff import main as build_handoff_main
from scripts.export_mt5_research_ohlcv import (
    ORDERED_PATH_OVERRIDE_SCOPE,
    add_source_provenance_args,
    source_provenance_from_args,
)
from src.research_infra.v4u_vps_ltf_handoff import build_handoff_package


def test_ftmo_handoff_labels_every_requirement_and_uses_safe_tick_window() -> None:
    package = build_handoff_package(oracle_report=_oracle_report())

    manifest = package.manifest
    assert manifest["source_broker"] == "FTMO"
    assert manifest["source_role"] == "owner_authorized_path_override"
    assert manifest["replaces_missing_frozen_path_source"] is True
    assert manifest["not_redacted_account_native"] is True
    assert manifest["source_truth_scope"] == ORDERED_PATH_OVERRIDE_SCOPE
    assert manifest["source_boundary"] == {
        "ordered_path_truth_only": True,
        "asof_decision_packet_truth_satisfied": False,
        "broker_ticket_order_deal_account_history_truth_satisfied": False,
        "proxy_or_m15_may_satisfy_ordered_path_truth": False,
        "redacted_account_native_truth_claim": False,
    }

    row = package.requirement_rows[0]
    assert row["source_broker"] == "FTMO"
    assert row["source_role"] == "owner_authorized_path_override"
    assert row["replaces_missing_frozen_path_source"] is True
    assert row["not_redacted_account_native"] is True
    assert row["not_broker_order_lifecycle_truth"] is True
    assert row["not_asof_decision_packet_truth"] is True
    assert row["mt5_symbol"] == "NDX100"
    assert set(
        [
            "source_server",
            "source_account_login",
            "row_count",
            "sha256",
            "export_tool",
        ]
    ).issubset(row["required_capture_fields_after_export"])

    tick_command = row["commands"]["tick_probe"]
    tick_window = tick_command[tick_command.index("--window") + 1]
    assert tick_window.startswith(row["requirement_id"] + ":")
    assert ",2022-01-06T00:00:00Z" in tick_window
    assert "+00:00:" not in tick_window
    assert "--source-broker" in tick_command
    assert "FTMO" in tick_command
    assert "--source-role" in tick_command
    assert "owner_authorized_path_override" in tick_command
    assert "--replaces-missing-frozen-path-source" in tick_command
    assert "--not-redacted_account-native" in tick_command
    assert "--require-owner-authorized-path-override" in tick_command

    tick_export_command = row["commands"]["tick_export"]
    tick_export_window = tick_export_command[tick_export_command.index("--window") + 1]
    assert tick_export_command[1] == "scripts/export_mt5_research_ticks.py"
    assert tick_export_window == tick_window
    assert tick_export_command[tick_export_command.index("--label") + 1].endswith("_tick")
    assert row["commands"]["m1_export"][
        row["commands"]["m1_export"].index("--label") + 1
    ].endswith("_m1")
    assert (
        tick_export_command[tick_export_command.index("--label") + 1]
        != row["commands"]["m1_export"][
            row["commands"]["m1_export"].index("--label") + 1
        ]
    )
    assert "--source-broker" in tick_export_command
    assert "--not-redacted_account-native" in tick_export_command
    assert "--require-owner-authorized-path-override" in tick_export_command

    assert "broker_ticket_order_deal_account_history_truth" in row["forbidden_uses"]
    assert "asof_decision_packet_input" in row["forbidden_uses"]
    assert "proxy_m15_ordered_path_truth" in row["forbidden_uses"]


def test_owner_authorized_handoff_rejects_non_ftmo_source() -> None:
    with pytest.raises(ValueError, match="source_broker=FTMO"):
        build_handoff_package(oracle_report=_oracle_report(), source_broker="redacted_account")


def test_owner_authorized_source_provenance_requires_all_override_flags() -> None:
    parser = argparse.ArgumentParser()
    add_source_provenance_args(parser)

    bad_args = parser.parse_args(
        [
            "--source-broker",
            "FTMO",
            "--source-role",
            "owner_authorized_path_override",
            "--source-truth-scope",
            ORDERED_PATH_OVERRIDE_SCOPE,
            "--require-owner-authorized-path-override",
        ]
    )
    with pytest.raises(RuntimeError, match="not_redacted_account_native"):
        source_provenance_from_args(bad_args)

    good_args = parser.parse_args(
        [
            "--source-broker",
            "FTMO",
            "--source-role",
            "owner_authorized_path_override",
            "--source-truth-scope",
            ORDERED_PATH_OVERRIDE_SCOPE,
            "--replaces-missing-frozen-path-source",
            "--not-redacted_account-native",
            "--require-owner-authorized-path-override",
        ]
    )
    provenance = source_provenance_from_args(good_args)
    assert provenance["broker_lifecycle_truth_satisfied"] is False
    assert provenance["asof_decision_truth_satisfied"] is False


def test_cli_writes_manifest_requirements_and_powershell(tmp_path: Path) -> None:
    oracle_report = tmp_path / "oracle.json"
    manifest = tmp_path / "handoff.json"
    requirements = tmp_path / "requirements.jsonl"
    powershell = tmp_path / "commands.ps1"
    oracle_report.write_text(json.dumps(_oracle_report()), encoding="utf-8")

    assert (
        build_handoff_main(
            [
                "--oracle-report",
                str(oracle_report),
                "--output-manifest-json",
                str(manifest),
                "--output-requirements-jsonl",
                str(requirements),
                "--output-powershell",
                str(powershell),
                "--python-executable",
                "python",
            ]
        )
        == 0
    )

    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert manifest_payload["exact_requirement_groups_packaged"] == 1
    assert rows[0]["source_broker"] == "FTMO"
    assert rows[0]["source_truth_scope"] == ORDERED_PATH_OVERRIDE_SCOPE
    assert "--require-owner-authorized-path-override" in powershell.read_text(
        encoding="utf-8"
    )
    assert "scripts/export_mt5_research_ticks.py" in powershell.read_text(
        encoding="utf-8"
    )


def _oracle_report() -> dict:
    return {
        "run_id": "unit_test_oracle",
        "metrics": {
            "ordered_touch_missing_rows": 1,
            "exact_requirement_groups": 1,
        },
        "exact_source_requirements": [
            {
                "symbol": "NAS100",
                "date": "2022-01-05",
                "session": "OFF_KZ_BROAD",
                "candidate_rows": 2,
                "sample_candidate_ids": ["cand_a", "cand_b"],
                "sample_window_ids": ["window_a"],
                "export_command_templates": [
                    {
                        "tool": "scripts/inspect_mt5_tick_availability.py",
                        "read_only": True,
                        "command": (
                            "python3 scripts/inspect_mt5_tick_availability.py "
                            "--window NAS100_2022-01-05:"
                            "2022-01-05T19:15:00+00:00:"
                            "2022-01-06T00:00:00+00:00 "
                            "--symbol NAS100:NDX100 --write-json --yes-live-readonly"
                        ),
                    },
                    {
                        "tool": "scripts/export_mt5_research_ohlcv.py",
                        "read_only": True,
                        "command": (
                            "python3 scripts/export_mt5_research_ohlcv.py "
                            "--start 2022-01-05T19:15:00+00:00 "
                            "--end 2022-01-06T00:00:00+00:00 "
                            "--symbol NAS100:NDX100 --timeframes M1 "
                            "--label v4u_ordered_path_window --yes-live-readonly"
                        ),
                    },
                ],
            }
        ],
    }

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_v4u_broker_lifecycle_capture_contract import (
    REQUIREMENT_JSONL,
    SOURCE_PARTIAL_LEDGER,
    build_audit,
    write_jsonl,
)


def test_broker_lifecycle_capture_contract_audit_counts_rows_and_config(
    tmp_path: Path,
) -> None:
    route_dir = tmp_path / "route"
    route_dir.mkdir()
    write_jsonl(
        route_dir / SOURCE_PARTIAL_LEDGER,
        [
            {
                "source_path": "data/A_M15.csv",
                "source_sha256": "sha-a",
                "source_path_status": "source_path_missing",
                "row_count": 3,
                "symbols": {"XAUUSD": 3},
                "top_source_gaps": {
                    "missing_ticket": 3,
                    "commission": 2,
                    "source_window_incomplete": 3,
                },
            },
            {
                "source_path": "data/B_M15.csv",
                "source_sha256": "sha-b",
                "source_path_status": "source_path_exists",
                "row_count": 2,
                "symbols": {"GBPJPY": 2},
                "top_source_gaps": {"ordered_milestone_clock_required_for_time_to_1.0r": 2},
            },
        ],
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
gtos_vnext_runtime:
  execution_manager_v4_broker_lifecycle_capture_contract_required: true
  broker_order_lifecycle_capture_v4_enabled: true
  broker_order_lifecycle_capture_v4_log_enabled: true
  broker_order_lifecycle_capture_v4_schema: broker_order_lifecycle_capture_v4_packet_v1
  broker_order_lifecycle_capture_v4_log_path: shadow_logs/broker_order_lifecycle_capture_v4.jsonl
""",
        encoding="utf-8",
    )

    audit, requirement_rows = build_audit(route_dir, config_path)

    assert audit["status"] == (
        "active_contract_implemented_historical_rows_remain_capture_required"
    )
    assert audit["source_partial_requirement_groups"] == 2
    assert audit["source_partial_rows_total"] == 5
    assert audit["broker_lifecycle_gap_groups"] == 1
    assert audit["broker_lifecycle_gap_rows"] == 3
    assert audit["top_broker_lifecycle_gap_counts"]["missing_ticket"] == 3
    assert audit["top_broker_lifecycle_gap_counts"]["commission"] == 2
    assert requirement_rows[0]["contract_schema"] == (
        "broker_order_lifecycle_capture_v4_packet_v1"
    )
    assert REQUIREMENT_JSONL == "V4U_BROKER_LIFECYCLE_CAPTURE_REQUIREMENT_LEDGER.jsonl"


def test_broker_lifecycle_capture_contract_audit_writes_parseable_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, [{"a": 1}, {"b": 2}])

    assert [json.loads(line) for line in path.read_text().splitlines()] == [
        {"a": 1},
        {"b": 2},
    ]

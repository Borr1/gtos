from __future__ import annotations

import json
from pathlib import Path

from src.components.pending_limit_lifecycle_logger import record_pending_limit_lifecycle
from src.research_infra.forward_capture import validate_scid_forward_source_capture_row


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_pending_limit_lifecycle_scid_bridge_redacts_broker_ids_and_results(tmp_path):
    lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
    scid_path = tmp_path / "scid_forward_source_capture.jsonl"

    record_pending_limit_lifecycle(
        {
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "side": "LONG",
            "candidate_id": "NAS100_2026-05-04T13:30:00+00:00",
            "trade_id": "lim_NAS100_20260504_133000",
            "decision_time_utc": "2026-05-04T13:30:00+00:00",
            "timestamp_utc": "2026-05-04T13:45:00+00:00",
            "checked_candle_time_utc": "2026-05-04T13:45:00+00:00",
            "intent_after_check": "order_send_success_filled",
            "pending_ticket": "SECRET_PENDING_TICKET",
            "mt5_order_ticket": "SECRET_MT5_ORDER_TICKET",
            "trade_state_ticket": "SECRET_TRADE_STATE_TICKET",
            "actual_r": "SECRET_ACTUAL_R",
            "synthetic_path_r": "SECRET_SYNTHETIC_R",
            "slippage_price": "SECRET_SLIPPAGE",
        },
        log_path=str(lifecycle_path),
    )

    lifecycle_row = _read_rows(lifecycle_path)[0]
    scid_row = _read_rows(scid_path)[0]
    scid_payload = json.dumps(scid_row, sort_keys=True)

    assert lifecycle_row["pending_ticket"] == "SECRET_PENDING_TICKET"
    assert scid_row["field_group"] == "lifecycle_fill_cancel_expiry_source_status"
    assert scid_row["redacted_order_bridge_hash_optional"] is None
    assert validate_scid_forward_source_capture_row(scid_row)["ok"] is True
    assert "SECRET_" not in scid_payload
    assert "pending_ticket" not in scid_payload
    assert "mt5_order_ticket" not in scid_payload
    assert "actual_r" not in scid_payload
    assert scid_row["validation_safe"] is False
    assert scid_row["outcome_review_opened"] is False
    assert scid_row["live_effect"] is False


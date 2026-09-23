from __future__ import annotations

import json
from argparse import Namespace

from scripts import build_broker_r_reconciliation_coverage as mod


def test_summarize_separates_broker_r_from_synthetic():
    payload = mod.summarize(
        trade_records=[
            {"exit": {"actual_r": 1.0}, "execution": {"ticket": 1}},
            {"shadow": {"synthetic_path_r": 1.5}, "execution": None},
        ],
        lifecycle_rows=[{"intent_after_check": "order_send_success_filled"}],
        slippage_rows=[{"ticket": 1}],
        j46_rows=[{"actual_close": {"broker_deal_reconciled": True}}],
        mt5_deal_rows=[{"entry": 1, "magic": 20260401}],
    )

    coverage = payload["coverage"]
    assert coverage["trade_records_with_broker_actual_r"] == 1
    assert coverage["trade_records_with_synthetic_or_path_fields"] == 1
    assert coverage["pending_lifecycle_internal_filled_rows"] == 1
    assert coverage["mt5_deal_history_rows"] == 1
    assert coverage["mt5_close_deal_rows"] == 1
    assert coverage["mt5_agent_magic_deal_rows"] == 1
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_read_trade_records_skips_bad_json(tmp_path):
    root = tmp_path / "records"
    root.mkdir()
    (root / "good.json").write_text(json.dumps({"exit": {"realized_R": 1.0}}), encoding="utf-8")
    (root / "bad.json").write_text("{bad", encoding="utf-8")

    rows = mod.read_trade_records(root)
    assert len(rows) == 1
    assert rows[0]["exit"]["realized_R"] == 1.0


def test_build_payload_reads_inputs(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    (records / "a.json").write_text(json.dumps({"execution": {"ticket": 1}}), encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.jsonl"
    lifecycle.write_text(json.dumps({"intent_after_check": "order_send_success_filled"}) + "\n", encoding="utf-8")
    slippage = tmp_path / "slippage.jsonl"
    slippage.write_text(json.dumps({"ticket": 1}) + "\n", encoding="utf-8")
    j46 = tmp_path / "j46.jsonl"
    j46.write_text("", encoding="utf-8")

    payload = mod.build_payload(
        Namespace(
            trade_records_root=str(records),
            lifecycle_log=str(lifecycle),
            slippage_log=str(slippage),
            j46_log=str(j46),
            mt5_deals_log=str(tmp_path / "missing_mt5.jsonl"),
        )
    )

    assert payload["coverage"]["trade_records_total"] == 1
    assert payload["coverage"]["slippage_rows"] == 1


def test_render_md_contains_join_plan():
    payload = mod.summarize(
        trade_records=[],
        lifecycle_rows=[],
        slippage_rows=[],
        j46_rows=[],
        mt5_deal_rows=[],
    )
    md = mod.render_md(payload)
    assert "Join Plan" in md
    assert "NO_PROMOTION_VERDICT" in md

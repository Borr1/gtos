from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts import audit_orderflow_limit_intent_reconciliation as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def repo_tmp():
    root = Path.cwd() / ".codex_pytest_local" / f"orderflow_limit_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _coverage_row(symbol: str = "XAUUSD") -> dict:
    return {
        "schema_version": "coverage",
        "audit_rows": [
            {
                "symbol": symbol,
                "candle_close_utc": "2026-04-17T13:30:00+00:00",
                "coverage_class": "limit_placed_no_broker_close_in_join",
                "final_outcome": "LIMIT_PLACED",
                "synthetic_outcome": "TP",
                "synthetic_realized_r": 1.5,
                "trade_record_path": f"knowledge_base/trade_records/{symbol}/2026-04-17_ny_1330.json",
            }
        ],
    }


def _candidate_row(symbol: str = "XAUUSD") -> dict:
    return {
        "candidate__symbol": symbol,
        "candidate__candle_close_utc": "2026-04-17T13:30:00+00:00",
        "candidate__direction": "LONG",
        "candidate__synthetic_ohlcv_dir": "data/ohlcv",
    }


def _record_payload(exit_payload=None, execution_payload=None) -> dict:
    return {
        "metadata": {
            "trade_id": "XAUUSD_2026-04-17_ny_1330",
            "candle_time": "2026-04-17T13:30:05+00:00",
        },
        "decision_pipeline": {"final_outcome": "LIMIT_PLACED"},
        "execution": execution_payload,
        "exit": exit_payload,
        "limit_intent": {
            "trade_id": "lim_2026-04-17_1330",
            "limit_price": 4793.86,
            "stop_loss": 4773.73,
            "take_profit_1": 4824.05,
            "expiry_candles": 192,
        },
    }


def _write_m1(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-04-17 13:31:00,4790,4791,4788,4789,10",
                "2026-04-17 15:40:00,4822,4825,4821,4824,10",
            ]
        ),
        encoding="utf-8",
    )


def test_reconciles_discarded_internal_intent_with_counterfactual_tp(repo_tmp):
    _write_json(
        repo_tmp / "knowledge_base/trade_records/XAUUSD/2026-04-17_ny_1330.json",
        _record_payload(),
    )
    log_dir = repo_tmp / "knowledge_base/logs"
    log_dir.mkdir(parents=True)
    (log_dir / "agent_XAUUSD_demo.log").write_text(
        "\n".join(
            [
                "2026-04-17 21:30:26 INFO LIMIT PLACED: lim_2026-04-17_1330 LONG limit=4793.86000 sl=4773.73000 tp=4824.05000",
                "2026-04-17 21:45:05 INFO Processing candle - ny KZ",
                "2026-04-18 08:01:05 INFO Discarding pending_intent placed before today's first KZ (placed=2026-04-17T13:30:26.606481+00:00, first_kz_start=2026-04-18T07:00:00+00:00): lim_2026-04-17_1330 LONG limit=4793.86000",
            ]
        ),
        encoding="utf-8",
    )
    _write_m1(repo_tmp / "data/ohlcv/XAUUSD_M1.csv")

    payload = mod.build_payload(
        _coverage_row(),
        [_candidate_row()],
        project_root=repo_tmp,
        m1_roots=[Path("data/ohlcv")],
    )

    row = payload["reconciliation_rows"][0]
    assert row["reconciliation_class"] == "discarded_internal_intent_but_research_path_would_have_filled"
    assert row["counterfactual_m1_path"]["outcome"] == "TP"
    assert row["log"]["processing_candles_after_placement_before_discard"] == 1


def test_classify_prefers_actual_broker_r(repo_tmp):
    _write_json(
        repo_tmp / "knowledge_base/trade_records/XAUUSD/2026-04-17_ny_1330.json",
        _record_payload(exit_payload={"actual_r": -0.5}, execution_payload={"ticket": 1}),
    )
    (repo_tmp / "knowledge_base/logs").mkdir(parents=True)
    (repo_tmp / "knowledge_base/logs/agent_XAUUSD_demo.log").write_text("", encoding="utf-8")

    payload = mod.build_payload(
        _coverage_row(),
        [_candidate_row()],
        project_root=repo_tmp,
        m1_roots=[Path("data/ohlcv")],
    )

    assert payload["reconciliation_rows"][0]["reconciliation_class"] == "actual_broker_r_present"


def test_log_evidence_detects_limit_fill_variant(repo_tmp):
    log_dir = repo_tmp / "knowledge_base/logs"
    log_dir.mkdir(parents=True)
    (log_dir / "agent_XAUUSD_demo.log").write_text(
        "2026-04-17 INFO LIMIT FILLED: lim_filled_2026-04-17_1330 at 4794.0\n",
        encoding="utf-8",
    )

    out = mod.inspect_log_evidence(
        symbol="XAUUSD",
        trade_id="lim_2026-04-17_1330",
        project_root=repo_tmp,
    )

    assert out["has_limit_filled_log"] is True

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import audit_futures_proxy_expansion_validation as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"futures_proxy_expansion_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _diag(fut: str, mt5: str, corr: float, direction: float, transform: str = "direct") -> dict:
    return {
        "futures_symbol": fut,
        "mt5_symbol": mt5,
        "return_transform": transform,
        "zero_lag_return_corr": corr,
        "directional_agreement": direction,
        "best_lag_minutes": 0,
    }


def _window(window_id: str, shift: int, diags: list[dict], cost: float = 0.01) -> dict:
    return {
        "window_id": window_id,
        "selected_shift_minutes": shift,
        "selected_diagnostics": diags,
        "sidecar": {"estimate": {"cost_usd": cost}},
    }


def test_proxy_expansion_audit_marks_partial_6j_under_strict_floor():
    validation = {
        "inputs": {"pairs": ["SI.v.0:XAGUSD", "6J.v.0:USDJPY:inverse_return"]},
        "windows": [
            _window("w1", -180, [_diag("SI.v.0", "XAGUSD", 0.90, 0.90), _diag("6J.v.0", "USDJPY", 0.91, 0.95, "inverse_return")]),
            _window("w2", -180, [_diag("SI.v.0", "XAGUSD", 0.91, 0.91), _diag("6J.v.0", "USDJPY", 0.83, 0.94, "inverse_return")]),
            _window("w3", -180, [_diag("SI.v.0", "XAGUSD", 0.92, 0.92), _diag("6J.v.0", "USDJPY", 0.89, 0.93, "inverse_return")]),
        ],
    }

    payload = mod.build_payload(validation, input_path="input.json")
    statuses = {row["pair"]: row["status"] for row in payload["pair_audit"]}

    assert statuses["SI.v.0->XAGUSD:direct"] == "STRICT_TRANSFER_PASS"
    assert statuses["6J.v.0->USDJPY:inverse_return"] == "TRANSFER_REVIEW_REQUIRED"
    assert payload["decision_readout"]["gbpjpy_synthetic_cross_status"] == "BLOCKED_BY_6J_USDJPY_REVIEW"
    assert payload["inputs"]["estimated_databento_cost_usd"] == 0.03


def test_proxy_expansion_audit_writes_no_promotion_markdown(tmp_path):
    payload = mod.build_payload(
        {"inputs": {"pairs": []}, "windows": []},
        input_path="input.json",
    )
    out = tmp_path / "audit.md"
    mod.write_markdown(payload, out)
    text = out.read_text(encoding="utf-8")

    assert "NO_PROMOTION_VERDICT" in text
    assert "Ambiguity Ledger" in text
    assert "Next Steps" in text

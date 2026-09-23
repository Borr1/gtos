from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts import analyze_lane6_tail_triage as mod


def test_estimate_rough_vol_hurst_requires_enough_rows():
    result = mod.estimate_rough_vol_hurst(pd.Series([1.0, 1.1, 1.2]))

    assert result["status"] == "insufficient_rows"
    assert result["hurst"] is None


def test_estimate_rough_vol_hurst_returns_numeric_for_long_series():
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0, 0.01, 1000)
    close = pd.Series(100.0 * np.exp(np.cumsum(returns)))

    result = mod.estimate_rough_vol_hurst(close)

    assert result["status"] == "ok"
    assert isinstance(result["hurst"], float)


def test_rough_hurst_inventory_reads_current_symbol_files(tmp_path):
    hist = tmp_path / "data" / "historical_2026"
    hist.mkdir(parents=True)
    times = pd.date_range("2026-01-01", periods=300, freq="15min")
    for idx, file_symbol in enumerate(mod.CURRENT_SYMBOL_FILES.values()):
        path = hist / f"{file_symbol}_M15.csv"
        close = 100.0 + idx + np.linspace(0, 1, len(times)) + np.sin(np.arange(len(times)) / 10.0)
        df = pd.DataFrame(
            {
                "time": times.strftime("%Y-%m-%d %H:%M:%S"),
                "open": close,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": 1,
            }
        )
        df.to_csv(path, index=False)

    inv = mod.rough_hurst_inventory(tmp_path)

    assert inv["symbol_count"] == 7
    assert set(inv["symbols_found"]) == set(mod.CURRENT_SYMBOL_FILES)


def test_build_payload_preserves_no_promotion_and_expected_static_statuses(tmp_path):
    payload = mod.build_payload(tmp_path)
    by_id = {item["id"]: item for item in payload["classifications"]}

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["V-5"]["status"] == "REJECTED_FAILED"
    assert by_id["L-1"]["status"] == "FILED_FOR_APPROVAL"
    assert by_id["RR-1"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["X-5"]["status"] == "BLOCKED_WITH_REASON"
    json.dumps(payload)


def test_render_markdown_contains_hurst_and_classification_sections(tmp_path):
    payload = mod.build_payload(tmp_path)
    md = mod.render_markdown(payload)

    assert "## Rough-Vol Hurst Proxy" in md
    assert "## Classification Matrix" in md
    assert "NO_PROMOTION_VERDICT" in md

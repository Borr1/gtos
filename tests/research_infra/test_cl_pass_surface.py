"""Behavioural controls for Session CL's offline pass-surface receipt."""

from __future__ import annotations

import datetime as dt
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
DRIVER = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17/receipts/cl_pass_surface.py"
)


@pytest.fixture(scope="module")
def cl():
    spec = importlib.util.spec_from_file_location("test_cl_pass_surface_driver", DRIVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _row(day: str, outcome: object) -> dict[str, object]:
    return {
        "sleeve": "fx_jpy",
        "symbol": "USDJPY",
        "symbol_canonical": "USDJPY",
        "decision_day": day,
        "entry_utc": f"{day}T09:00:00+00:00",
        "exit_utc": f"{day}T10:00:00+00:00",
        "direction": 1,
        "sl_distance_price": 1.0,
        "entry_price": 100.0,
        "r_gross": outcome,
    }


def test_estate_reader_checks_protected_and_live_forward_dates_before_outcome(
    cl, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A poisoned outcome proves TEST rows are rejected before outcome conversion."""
    source = tmp_path / "estate.json.gz"
    doc = {
        "trades": {
            "fx_jpy": [
                _row("2025-02-03", 0.25),
                _row("2026-03-10", "MARCH_OUTCOME_MUST_NOT_BE_READ"),
                _row("2026-07-30", "LIVE_FORWARD_OUTCOME_MUST_NOT_BE_READ"),
            ]
        }
    }
    with gzip.open(source, "wt") as fh:
        json.dump(doc, fh)
    monkeypatch.setattr(cl, "ESTATE", source)

    projected, guard = cl.safe_estate_records()

    assert [row["r_gross"] for row in projected["fx_jpy"]] == [0.25]
    assert guard["protected_outcome_fields_accessed"] == 0
    assert guard["rows_dropped"] == {
        "label_or_decision_intersects_protected_month": 1,
        "outside_train_val": 1,
    }


def test_extension_without_own_series_is_not_hidden_by_baseline_days(cl) -> None:
    daily = {"crypto": {"ACTUAL_REALIZED_HOLD": {"2025-02-03": 0.1}}}
    start = dt.date(2025, 1, 1)
    end = dt.date(2025, 12, 31)

    assert cl.has_window_series(daily, "crypto", "ACTUAL_REALIZED_HOLD", start, end)
    assert not cl.has_window_series(
        daily, "vp_euidx_pocgrav", "ACTUAL_REALIZED_HOLD", start, end
    )


@pytest.mark.parametrize("account", ["FTMO", "redacted_account"])
def test_archive_only_vp_never_gets_arming_authority(cl, account: str) -> None:
    disposition = cl.evidence_disposition(account, "vp_euidx_pocgrav", has_series=False)
    assert disposition["decision"] == "DO_NOT_ARM"
    assert "comparability gate" in disposition["reason"]


def test_direct_arming_inventory_is_bounded_to_evidence_supported_extensions(cl) -> None:
    assert set(cl.EXTENSIONS) == {
        "fx_jpy",
        "fx_jpy_ny",
        "fx_jpy_pair",
        "metals_core_downweighted",
        "metals_softband",
        "mx_btcusd_target5",
        "vp_euidx_pocgrav",
    }
    assert cl.EXTENSIONS["metals_core_downweighted"]["weights"] == {
        "metals_core": 0.50
    }
    assert cl.EXTENSIONS["mx_btcusd_target5"]["weights"] == {cl.MX: 0.025}

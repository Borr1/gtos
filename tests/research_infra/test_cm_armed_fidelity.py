from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17/receipts/cm_armed_fidelity.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("cm_armed_fidelity", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_refused_rows_are_classified_before_ohlc_is_parsed(tmp_path):
    cm = _load_module()
    rel = "bars/TEST_H4.csv"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    # Both refused rows carry deliberately non-numeric OHLC.  Loading can succeed only if the
    # timestamp guard runs before any economic field is converted.
    path.write_text(
        "time,open,high,low,close,volume\n"
        "2025-01-02T00:00:00+00:00,1,2,0.5,1.5,10\n"
        "2026-03-02T00:00:00+00:00,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ\n"
        "2026-06-02T00:00:00+00:00,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ,DO_NOT_READ\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    series = cm.load_lane_series(
        tmp_path,
        {
            "lane_relpath": rel,
            "sha256": digest,
            "time_column_basis": "true_utc",
            "symbol": "TEST",
            "timeframe": "H4",
            "row_count": 3,
        },
    )
    assert len(series.bars) == 1
    assert series.times[0] == dt.datetime(2025, 1, 2, tzinfo=dt.timezone.utc)
    assert series.skipped == {
        "day_inside_reserved_blackout": 1,
        "day_outside_every_surface": 1,
    }


def test_causal_span_refuses_test_and_uncovered_days():
    cm = _load_module()
    utc = dt.timezone.utc
    assert cm.span_is_iterable(
        dt.datetime(2024, 12, 1, tzinfo=utc), dt.datetime(2025, 2, 1, tzinfo=utc)
    )
    assert not cm.span_is_iterable(
        dt.datetime(2026, 2, 27, tzinfo=utc), dt.datetime(2026, 4, 2, tzinfo=utc)
    )
    assert not cm.span_is_iterable(
        dt.datetime(2026, 5, 30, tzinfo=utc), dt.datetime(2026, 6, 2, tzinfo=utc)
    )


def _gate_row(mean, folds, *, n=40):
    return {
        "n_trades": n,
        "n_folds_evaluable": len(folds),
        "pooled_oos_mean_r": mean,
        "fold_means": folds,
    }


def test_arm_rule_requires_positive_pooled_recent_and_fold_majority_in_every_band():
    cm = _load_module()
    current = {b: _gate_row(0.10, [0.05, 0.10, 0.15]) for b in cm.BANDS}
    candidate = {b: _gate_row(0.20, [0.06, 0.12, 0.19]) for b in cm.BANDS}
    assert cm.arm_rule("crypto", current, candidate)["eligible"] is True

    candidate["high"] = _gate_row(0.20, [0.06, 0.12, 0.14])
    result = cm.arm_rule("crypto", current, candidate)
    assert result["eligible"] is False
    assert "high_latest_fold_delta_not_positive" in result["reasons"]


def test_energy_extension_floor_and_existing_frontier_contracts_are_exact():
    cm = _load_module()
    current = {b: _gate_row(0.10, [0.05, 0.10, 0.15], n=67) for b in cm.BANDS}
    candidate = {b: _gate_row(0.20, [0.06, 0.12, 0.19], n=67) for b in cm.BANDS}
    result = cm.arm_rule("energy_agri", current, candidate)
    assert result["eligible"] is False
    assert "energy_extension_does_not_exceed_AD_n67" in result["reasons"]

    crypto_current, crypto_candidate = cm.variants_for("crypto")
    assert crypto_current.stop_mult == 1.0
    assert crypto_candidate.stop_mult == 1.5
    assert crypto_candidate.target_mode == "scales_with_stop"

    energy_current, energy_candidate = cm.variants_for("energy_agri")
    assert energy_current.partial_at_r == 2.0
    assert energy_candidate.partial_at_r is None
    assert energy_candidate.target_r == 4.0

    _, xvol_candidate = cm.variants_for("sub_xvol_pullback")
    assert xvol_candidate.target_mode == "fixed_r"
    assert xvol_candidate.target_r == 4.0

    mx_current, mx_candidate = cm.variants_for(cm.MX)
    assert mx_current.target_r == mx_candidate.target_r == 5.0


def test_inventory_keeps_admission_and_fidelity_separate_and_selects_one_account():
    path = SCRIPT.parent / "CM_ARMED_EXIT_INVENTORY_V1.json"
    inv = json.loads(path.read_text(encoding="utf-8"))
    assert inv["historical_sweep"]["AD"]["gated_cells"] == 1631
    assert inv["sleeves"]["crypto"]["historical_best"]["class"] == "fidelity"
    assert inv["sleeves"]["sub_xvol_pullback"]["historical_best"][
        "delta_r_per_day_mid"
    ] == 0.130065
    assert inv["sleeves"]["energy_agri"]["current"]["extension_exceeds_AD_n67"] is False
    assert inv["selected_for_ceremony"] == {
        "FTMO": ["crypto@stop_1p5x_target_scale"],
        "redacted_account": [],
    }
    assert inv["protected_boundaries"] == {
        "march_2026_outcomes_read": False,
        "test_surface_consumed": False,
        "broker_or_vps_contact": False,
        "config_bytes_written": False,
    }


def test_host_carry_is_reproducible_one_file_and_default_off():
    package = SCRIPT.parents[1] / "activation_carry_armed_fidelity"
    subprocess.run(
        [sys.executable, str(package / "build_carry.py"), "--check"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    man = json.loads((package / "MANIFEST.json").read_text(encoding="utf-8"))
    assert len(man["files"]) == 1
    rec = man["files"][0]
    payload = package / "files/execution_packets.py"
    assert rec["repo_path"] == "src/components/ultimate_book/execution_packets.py"
    assert hashlib.sha256(payload.read_bytes()).hexdigest() == rec["sha256_after_carry"]
    assert rec["default_effect"].startswith("INERT until --frontier-exits selects crypto")
    assert man["selection"]["ftmo_frontier_after"].endswith(",crypto")
    assert man["selection"]["redacted_account_frontier_before_and_after"] is None
    assert "MetaTrader5" not in payload.read_text(encoding="utf-8")
    assert "order_send(" not in payload.read_text(encoding="utf-8")


def test_ceremony_preserves_firing_ledger_and_names_full_rollback_order():
    ceremony = (
        SCRIPT.parents[1]
        / "activation_carry_armed_fidelity/ARMED_FIDELITY_CEREMONY.md"
    ).read_text(encoding="utf-8")
    assert "Do not delete either firing ledger" in ceremony
    assert "Restore `run_book_supervisor.ps1` **first**" in ceremony
    assert "--frontier-exits mx_btcusd_d1_donchian_20_breakout,crypto" in ceremony
    assert "redacted_account must contain **neither** frontier line" in ceremony

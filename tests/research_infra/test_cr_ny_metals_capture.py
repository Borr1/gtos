"""Session CR's source boundary, fidelity measurement, and executable-row contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(
    "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
    "cr_ny_metals_capture.py"
).resolve()
SPEC = importlib.util.spec_from_file_location("cr_ny_metals_capture", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CR)


def test_forbidden_days_refuse_before_json_decode(monkeypatch):
    decoded = False

    def _decoder(_line):
        nonlocal decoded
        decoded = True
        raise AssertionError("outcome decoder must not be reached")

    monkeypatch.setattr(CR.json, "loads", _decoder)
    for day, label in (("2026-02-02", "february"), ("2026-03-02", "march")):
        decoded = False
        line = f'{{"decision_time_utc":"{day}T13:00:00+00:00",BROKEN_OUTCOME}}'
        with pytest.raises(CR.CRCaptureRefusal, match=label):
            CR.decode_january_line(line, context="synthetic")
        assert decoded is False


def test_policy_filter_is_exact_and_pretrade_only():
    base = {
        "decision_time_utc": "2026-01-21T13:00:00+00:00",
        "route_session": "ny",
        "symbol": "XAUUSD",
        "side": "LONG",
    }
    assert CR.is_policy_candidate(base)
    assert not CR.is_policy_candidate({**base, "route_session": "london"})
    assert not CR.is_policy_candidate({**base, "symbol": "EURUSD"})
    assert not CR.is_policy_candidate({**base, "side": "SHORT"})
    assert not CR.is_policy_candidate(
        {**base, "decision_time_utc": "2026-01-20T13:00:00+00:00"}
    )


def test_direct_fidelity_compares_unique_candidate_time_identities():
    reference = []
    semantic = []
    for index in range(249):
        minute = index % 60
        hour = 13 + ((index // 60) % 4)
        identity = f"candidate-{index}"
        decision = f"2026-01-21T{hour:02d}:{minute:02d}:00+00:00"
        reference.append(
            {
                "candidate_id": identity,
                "decision_time_utc": decision,
                "route_session": "ny",
                "symbol": "XAUUSD" if index % 2 else "XAGUSD",
                "side": "LONG",
            }
        )
        semantic.append(
            {
                "candidate_id": identity,
                "decision_time_utc": decision,
                "trading_day": "2026-01-21",
            }
        )
    got = CR.measure_generator_fidelity(reference, semantic)
    assert got["agreed"] == 249
    assert got["reference_only"] == 0
    assert got["reference_recall"] == 1.0
    assert got["semantic_holdout_unique_identities"] == 249
    assert got["precision"] is None
    assert got["precision_supported"] is False


def test_executable_capture_requires_terminal_tuple_only_for_fills():
    no_fill = {
        "entry_fill_executable": False,
        "fill_realism_class": "not_filled",
    }
    complete_fill = {
        "entry_fill_executable": True,
        "fill_realism_class": "passive_queue_confirmed",
        "counterfactual_order_fill_time_utc": "2026-01-21T13:01:00+00:00",
        "counterfactual_order_fill_price": 4400.0,
        "opportunity_close_time_utc": "2026-01-21T14:00:00+00:00",
        "opportunity_gross_r": 0.5,
        "opportunity_close_reason": "momentum_exhaustion",
        "path_index_source_path": "ticks/XAUUSD.jsonl",
        "path_index_source_sha256": "a" * 64,
    }
    complete = CR.assess_executable_capture([no_fill, complete_fill])
    assert complete["classification"]["filled"] == 1
    assert complete["classification"]["no_fill"] == 1
    assert complete["row_contract_complete"] is True

    incomplete = CR.assess_executable_capture(
        [{key: value for key, value in complete_fill.items() if key != "opportunity_gross_r"}]
    )
    assert incomplete["row_contract_complete"] is False
    assert incomplete["filled_trade_tuple"]["missing_rows_by_requirement"] == {
        "pre_cost_gross_r": 1
    }


def test_v27_is_the_fixed_59_declared_57_look_tip():
    declaration = CR.verify_declaration(CR.DEFAULT_CP_GATE_RECEIPT, CR.DEFAULT_FAMILY)
    assert declaration["candidate_id"] == CR.CANDIDATE_ID
    assert declaration["candidate_authority"].endswith(
        "CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json"
    )
    assert declaration["family_all_declared"] == 59
    assert declaration["family_looks_taken"] == 57
    assert declaration["candidate_already_billed"] is True
    assert declaration["new_hypothesis_looks"] == 0
    spec = CR.frozen_spec(CR.DEFAULT_FAMILY)
    assert spec["option"] == "B_balanced"
    assert spec["alpha"] == 0.10
    assert spec["band"] == "mid"
    assert spec["population"] == "RECORDED"
    assert spec["declared_family_size"] == 59

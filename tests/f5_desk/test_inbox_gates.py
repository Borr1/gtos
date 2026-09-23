"""Occupancy is SCRIPT. asia_pdl_fade cannot be approved. USDJPY HOLD stays."""
from __future__ import annotations

from scripts.f5_desk.inbox_gates import (
    gate_candidate_verdict,
    is_occupancy_why,
    is_usdjpy_why,
)


def test_occupancy_why_codes_are_script():
    assert is_occupancy_why("occupied_no_second_ticket")
    assert is_occupancy_why("owner_spent_gold_no_remint_tonight")
    assert is_occupancy_why("grok_sit_no_named_mechanism")
    assert is_occupancy_why("chair_sit_no_place_from_seat")
    assert is_occupancy_why("no_named_mechanism_chair_sit")
    assert not is_occupancy_why("usdjpy_scrub")
    assert is_usdjpy_why("usdjpy_scrub")


def test_uk100_asia_pdl_approve_demotes():
    cand = {
        "candidate_id": "W7_BOOK::liquidity_sweep::UK100::2026-08-27::LONG::asia_pdl_fade",
        "sleeve": "asia_pdl_fade",
        "symbol": "UK100",
        "status": "intent",
    }
    row = {
        "candidate_id": cand["candidate_id"],
        "verdict": "approve",
        "mechanism": "",
        "why_code": "isolated_reentry_free_symbol",
        "confidence": 0.55,
    }
    out, tag = gate_candidate_verdict(row, cand)
    assert out["verdict"] == "hold"
    assert out["why_code"] == "hard_off_sleeve"
    assert tag == "hard_off_sleeve_not_approvable"


def test_occupancy_hold_demotes_to_abstain():
    cand = {
        "candidate_id": "LAUNCHER::XAUUSD::dsp_bleed_accept_fresh_20low_second_push::2026-08-28",
        "sleeve": "dsp_bleed_accept_fresh_20low_second_push",
        "symbol": "XAUUSD",
        "status": "intent",
    }
    row = {
        "candidate_id": cand["candidate_id"],
        "verdict": "hold",
        "mechanism": "correlation",
        "why_code": "occupied_no_second_ticket",
        "confidence": 0.8,
    }
    out, tag = gate_candidate_verdict(row, cand)
    assert out["verdict"] == "abstain"
    assert tag == "occupancy_hold_demoted_script"


def test_usdjpy_hold_is_kept():
    cand = {
        "candidate_id": "LAUNCHER::USDJPY::dsp_isolated_spike_high::2026-08-28",
        "sleeve": "dsp_isolated_spike_high",
        "symbol": "USDJPY",
        "status": "intent",
    }
    row = {
        "candidate_id": cand["candidate_id"],
        "verdict": "hold",
        "mechanism": "microstructure",
        "why_code": "usdjpy_scrub",
        "confidence": 0.7,
    }
    out, tag = gate_candidate_verdict(row, cand)
    assert out["verdict"] == "hold"
    assert out["why_code"] == "usdjpy_scrub"
    assert tag is None


def test_high_window_blocks_new_risk_approve():
    cand = {
        "candidate_id": "LAUNCHER::GBPUSD::dsp_isolated_flush_to_20low_snap::2026-08-28",
        "sleeve": "dsp_isolated_flush_to_20low_snap",
        "symbol": "GBPUSD",
        "status": "intent",
        "high_impact_minutes": 1.6,
    }
    row = {
        "candidate_id": cand["candidate_id"],
        "verdict": "approve",
        "mechanism": "",
        "why_code": "tape_live",
        "confidence": 0.5,
    }
    out, tag = gate_candidate_verdict(row, cand)
    # isolated_flush is HARD_OFF first
    assert out["verdict"] == "hold"
    assert out["why_code"] == "hard_off_sleeve"


def test_high_window_on_paying_sleeve():
    cand = {
        "candidate_id": "LAUNCHER::GBPUSD::dsp_bleed_accept_fresh_20low_second_push::2026-08-28",
        "sleeve": "dsp_bleed_accept_fresh_20low_second_push",
        "symbol": "GBPUSD",
        "status": "intent",
        "high_impact_minutes": 1.6,
    }
    row = {
        "candidate_id": cand["candidate_id"],
        "verdict": "approve",
        "mechanism": "",
        "why_code": "tape_live",
        "confidence": 0.5,
    }
    out, tag = gate_candidate_verdict(row, cand)
    assert out["verdict"] == "hold"
    assert out["why_code"] == "named_high_print_window_candidate_symbol"
    assert tag == "high_window_candidate_symbol"

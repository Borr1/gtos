"""Shim round trip — verdict JSON -> flow sidecars -> consumed by the ACTUAL
``judgment_layer`` functions in-process. The book-side seam is not mocked."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from scripts.f5_desk import common, shim
from src.components.ultimate_book.judgment_layer import judgment_flow

from .conftest import MIDDAY_NOW

NS = "operator"

LTC_W7 = "W7_BOOK::liquidity_sweep::LTCUSD::2026-08-24::LONG::asia_pdl_fade"
LTC_LAUNCHER = "LAUNCHER::LTCUSD::asia_pdl_fade::2026-08-24"
EUR_W7 = "W7_BOOK::dsp_c_bleed20low::EURUSD::2026-08-24::LONG::dsp_bleed_accept_fresh_20low_second_push"
EUR_LAUNCHER = "LAUNCHER::EURUSD::dsp_bleed_accept_fresh_20low_second_push::2026-08-24"
XAU_LAUNCHER = "LAUNCHER::XAUUSD::dsp_walked_high_accepted_through::2026-08-24"
FLUSH_W7 = "W7_BOOK::dsp_c_flush::EURUSD::2026-08-24::LONG::dsp_climax_flush_to_96low_then_snap"
FLUSH_LAUNCHER = "LAUNCHER::EURUSD::dsp_climax_flush_to_96low_then_snap::2026-08-24"


def make_slate() -> dict:
    return {
        "schema": "gtos.judgment.slate.v2",
        "namespace": NS,
        "slate_id": "cafe0123deadbeef",
        "candidates": [
            {"candidate_id": LTC_W7, "alias_ids": [LTC_W7, LTC_LAUNCHER],
             "symbol": "LTCUSD", "sleeve": "asia_pdl_fade", "status": "intent"},
            {"candidate_id": EUR_W7, "alias_ids": [EUR_W7, EUR_LAUNCHER],
             "symbol": "EURUSD", "sleeve": "dsp_bleed_accept_fresh_20low_second_push",
             "status": "placed"},
            {"candidate_id": XAU_LAUNCHER, "alias_ids": [XAU_LAUNCHER],
             "symbol": "XAUUSD", "sleeve": "dsp_walked_high_accepted_through",
             "status": "intent"},
            {"candidate_id": FLUSH_W7, "alias_ids": [FLUSH_W7, FLUSH_LAUNCHER],
             "symbol": "EURUSD", "sleeve": "dsp_climax_flush_to_96low_then_snap",
             "status": "intent"},
        ],
        "open_positions": [
            {"ticket": 178351322, "symbol": "EURUSD", "sleeve": "x", "direction": "LONG",
             "entry_price": 1.16657, "stop_now": 1.16605, "take_profit_1": 1.16969,
             "locked_r": -1.0},
            {"ticket": 178058089, "symbol": "EURUSD", "sleeve": "y", "direction": "LONG",
             "entry_price": 1.16740, "stop_now": 1.16691},
        ],
    }


def make_verdict(slate) -> dict:
    return {
        "schema": "gtos.f5.judge.verdict.v1",
        "slate_id": slate["slate_id"],
        "verdicts": [
            {"candidate_id": LTC_W7, "verdict": "hold",
             "mechanism": "microstructure", "why_code": "thin_hour_crypto",
             "confidence": 0.8},
            {"candidate_id": EUR_W7, "verdict": "approve",
             "mechanism": "", "why_code": "conditions_clean", "confidence": 0.7},
            # hold WITHOUT a mechanism -> the shim demotes it to abstain
            {"candidate_id": XAU_LAUNCHER, "verdict": "hold",
             "mechanism": "", "why_code": "vibes", "confidence": 0.9},
            # unknown candidate -> dropped
            {"candidate_id": "LAUNCHER::GBPJPY::fx_jpy::2026-08-24", "verdict": "hold",
             "mechanism": "correlation", "why_code": "not_in_slate", "confidence": 0.9},
        ],
        "manage": [
            {"ticket": 178351322, "action": "tighten_stop", "new_stop": 1.16640,
             "mechanism": "event_proximity", "why_code": "fomc_in_45m"},
            {"ticket": 178058089, "action": "close",
             "mechanism": "weekend_carry", "why_code": "friday_close_window"},
            # NOT risk-reducing for a LONG (below current stop) -> dropped
            {"ticket": 178058089, "action": "tighten_stop", "new_stop": 1.16650,
             "mechanism": "microstructure", "why_code": "bad"},
            # unknown ticket -> dropped
            {"ticket": 999, "action": "close", "mechanism": "microstructure",
             "why_code": "ghost"},
        ],
        "notes": "test slate",
    }


def apply(tmp_path, now=MIDDAY_NOW, verdict=None, slate=None):
    slate = slate or make_slate()
    verdict = verdict if verdict is not None else make_verdict(slate)
    state_dir = tmp_path / "state_ns"
    flow_dir = tmp_path / "flow"
    result = shim.apply_verdict(
        verdict, slate, state_dir=state_dir, flow_dir=flow_dir,
        provider="test", latency_ms=42.0, now=now,
    )
    return result, state_dir, flow_dir, slate


# ---------------------------------------------------------------------------
# the round trip through the REAL consumer
# ---------------------------------------------------------------------------
def test_hold_binds_within_ttl_via_real_judgment_flow(tmp_path):
    result, state_dir, flow_dir, slate = apply(tmp_path)
    assert result["applied"] is True

    later = MIDDAY_NOW + timedelta(seconds=60)
    decision = judgment_flow(
        LTC_W7, later, verdict_dir=flow_dir, namespace=NS,
        extra_ids=[LTC_LAUNCHER], extra_row_dirs=[],
    )
    assert decision["action"] == "HOLD"
    assert decision["verdict"] == "hold"
    assert decision["why_code"] == "hard_off_sleeve"
    assert decision["reason"] == "sidecar"


def test_hold_binds_via_launcher_alias_alone(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)
    decision = judgment_flow(
        LTC_LAUNCHER, MIDDAY_NOW + timedelta(seconds=60),
        verdict_dir=flow_dir, namespace=NS, extra_row_dirs=[],
    )
    assert decision["action"] == "HOLD"


def test_approve_and_abstain_and_absent_all_pass_or_approve(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)
    later = MIDDAY_NOW + timedelta(seconds=60)

    approve = judgment_flow(EUR_W7, later, verdict_dir=flow_dir, namespace=NS,
                            extra_ids=[EUR_LAUNCHER], extra_row_dirs=[])
    assert approve["action"] == "APPROVE"  # no size_mult proposed -> APPROVE, not SIZE

    demoted = judgment_flow(XAU_LAUNCHER, later, verdict_dir=flow_dir, namespace=NS,
                            extra_row_dirs=[])
    assert demoted["action"] == "PASS"      # hold-without-mechanism was demoted to abstain
    assert demoted["verdict"] == "abstain"

    absent = judgment_flow("LAUNCHER::GBPJPY::fx_jpy::2026-08-24", later,
                           verdict_dir=flow_dir, namespace=NS, extra_row_dirs=[])
    assert absent["action"] == "PASS"
    assert absent["reason"] == "no_row"


def test_hold_expires_at_ttl_approve_survives(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)
    past_hold_ttl = MIDDAY_NOW + timedelta(seconds=shim.TTL_HOLD_S + 1)

    stale_hold = judgment_flow(LTC_W7, past_hold_ttl, verdict_dir=flow_dir,
                               namespace=NS, extra_ids=[LTC_LAUNCHER], extra_row_dirs=[])
    assert stale_hold["action"] == "PASS", "a stale HOLD must never veto a live fire"

    approve = judgment_flow(EUR_W7, past_hold_ttl, verdict_dir=flow_dir,
                            namespace=NS, extra_row_dirs=[])
    assert approve["action"] == "APPROVE"  # approve-class ttl is 14400


def test_wrong_namespace_never_binds(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)
    decision = judgment_flow(
        LTC_W7, MIDDAY_NOW + timedelta(seconds=60),
        verdict_dir=flow_dir, namespace="redacted_account_f5_minimal", extra_row_dirs=[],
    )
    assert decision["action"] == "PASS"


def test_both_sidecar_filenames_written_with_alias_keys(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)
    day = MIDDAY_NOW.date().isoformat()
    for stem in ("flow", "consume"):
        path = flow_dir / f"{stem}_{day}.json"
        assert path.is_file()
        data = json.loads(path.read_text())
        assert LTC_W7 in data and LTC_LAUNCHER in data
        entry = data[LTC_W7]
        # both key alias forms the consumer checks
        assert entry["action"] == "HOLD" and entry["verdict"] == "hold"
        assert entry["written_at_utc"] == entry["ts"]
        assert entry["ttl_s"] == shim.TTL_HOLD_S
        assert entry["namespace"] == NS


def test_midnight_dual_write_survives_date_roll(tmp_path):
    near_midnight = datetime(2026, 8, 24, 23, 40, 0, tzinfo=timezone.utc)
    _, _, flow_dir, _ = apply(tmp_path, now=near_midnight)
    assert (flow_dir / "flow_2026-08-24.json").is_file()
    assert (flow_dir / "flow_2026-08-25.json").is_file()

    after_midnight = datetime(2026, 8, 25, 0, 30, 0, tzinfo=timezone.utc)
    decision = judgment_flow(LTC_W7, after_midnight, verdict_dir=flow_dir,
                             namespace=NS, extra_row_dirs=[])
    assert decision["action"] == "HOLD", "a 23:40Z HOLD must still bind at 00:30Z"


def test_midday_write_does_not_dual_write(tmp_path):
    _, _, flow_dir, _ = apply(tmp_path)  # MIDDAY_NOW
    assert (flow_dir / "flow_2026-08-24.json").is_file()
    assert not (flow_dir / "flow_2026-08-25.json").exists()


def test_newer_verdict_replaces_standing_word(tmp_path):
    result, state_dir, flow_dir, slate = apply(tmp_path)
    # HARD_OFF asia_pdl cannot abstain-pass. Lift a paying sleeve instead.
    verdict2 = {
        "schema": "gtos.f5.judge.verdict.v1", "slate_id": slate["slate_id"],
        "verdicts": [{"candidate_id": EUR_W7, "verdict": "abstain",
                      "mechanism": "", "why_code": "spread_normalized", "confidence": 0.6}],
        "manage": [], "notes": "",
    }
    shim.apply_verdict(verdict2, slate, state_dir=state_dir, flow_dir=flow_dir,
                       provider="test", now=MIDDAY_NOW + timedelta(minutes=5))
    decision = judgment_flow(EUR_W7, MIDDAY_NOW + timedelta(minutes=6),
                             verdict_dir=flow_dir, namespace=NS,
                             extra_ids=[EUR_LAUNCHER], extra_row_dirs=[])
    assert decision["action"] == "PASS", "the newer abstain must displace the old approve"


def test_asia_pdl_isolated_reentry_approve_is_hard_off(tmp_path):
    slate = make_slate()
    verdict = {
        "schema": "gtos.f5.judge.verdict.v1", "slate_id": slate["slate_id"],
        "verdicts": [{
            "candidate_id": LTC_W7, "verdict": "approve",
            "mechanism": "", "why_code": "isolated_reentry_free_symbol",
            "confidence": 0.55,
        }],
        "manage": [], "notes": "UK100 shape",
    }
    _, _, flow_dir, _ = apply(tmp_path, verdict=verdict, slate=slate)
    decision = judgment_flow(
        LTC_W7, MIDDAY_NOW + timedelta(seconds=60),
        verdict_dir=flow_dir, namespace=NS, extra_ids=[LTC_LAUNCHER], extra_row_dirs=[],
    )
    assert decision["action"] == "HOLD"
    assert decision["why_code"] == "hard_off_sleeve"


def test_climax_flush_approve_is_hard_off(tmp_path):
    slate = make_slate()
    verdict = {
        "schema": "gtos.f5.judge.verdict.v1", "slate_id": slate["slate_id"],
        "verdicts": [{
            "candidate_id": FLUSH_W7, "verdict": "approve",
            "mechanism": "", "why_code": "isolated_reentry_wanted",
            "confidence": 0.7,
        }],
        "manage": [], "notes": "",
    }
    _, _, flow_dir, _ = apply(tmp_path, verdict=verdict, slate=slate)
    decision = judgment_flow(
        FLUSH_W7, MIDDAY_NOW + timedelta(seconds=60),
        verdict_dir=flow_dir, namespace=NS, extra_ids=[FLUSH_LAUNCHER], extra_row_dirs=[],
    )
    assert decision["action"] == "HOLD"
    assert decision["why_code"] == "hard_off_sleeve"


def test_occupancy_hold_is_script_not_intelligence(tmp_path):
    slate = make_slate()
    verdict = {
        "schema": "gtos.f5.judge.verdict.v1", "slate_id": slate["slate_id"],
        "verdicts": [{
            "candidate_id": XAU_LAUNCHER, "verdict": "hold",
            "mechanism": "correlation", "why_code": "occupied_no_second_ticket",
            "confidence": 0.8,
        }],
        "manage": [], "notes": "",
    }
    _, _, flow_dir, _ = apply(tmp_path, verdict=verdict, slate=slate)
    decision = judgment_flow(
        XAU_LAUNCHER, MIDDAY_NOW + timedelta(seconds=60),
        verdict_dir=flow_dir, namespace=NS, extra_row_dirs=[],
    )
    assert decision["action"] == "PASS"
    assert decision["verdict"] == "abstain"
    assert decision["why_code"] == "occupancy_script_not_intelligence"


# ---------------------------------------------------------------------------
# rejects write NOTHING
# ---------------------------------------------------------------------------
def test_schema_mismatch_writes_nothing_and_counts_breach(tmp_path):
    slate = make_slate()
    bad = {"schema": "not.the.schema", "slate_id": slate["slate_id"], "verdicts": []}
    result, state_dir, flow_dir, _ = apply(tmp_path, verdict=bad, slate=slate)
    assert result["applied"] is False
    assert result["reject_reason"] == "schema_mismatch"
    assert not any(flow_dir.glob("*.json")), "a rejected verdict must write no sidecar"
    assert not any(state_dir.glob("manage_*.json"))
    breach = json.loads(shim.breach_counter_path(state_dir).read_text())
    assert breach["count"] == 1
    journal = (state_dir / f"judge_{MIDDAY_NOW.date().isoformat()}.jsonl").read_text()
    assert "verdict_rejected" in journal


def test_slate_id_mismatch_rejected(tmp_path):
    slate = make_slate()
    verdict = make_verdict(slate)
    verdict["slate_id"] = "0000000000000000"
    result, state_dir, flow_dir, _ = apply(tmp_path, verdict=verdict, slate=slate)
    assert result["applied"] is False
    assert result["reject_reason"] == "slate_id_mismatch"
    assert not any(flow_dir.glob("*.json"))


def test_row_level_defects_drop_not_reject(tmp_path):
    result, state_dir, flow_dir, _ = apply(tmp_path)
    assert result["applied"] is True
    drops = result["drops"]
    assert drops["verdict_unknown_candidate"] == 1
    assert drops["hold_demoted_no_mechanism"] == 1
    assert drops["manage_unknown_ticket"] == 1
    assert drops["manage_tighten_not_risk_reducing"] == 1


def test_journal_and_memory_written(tmp_path):
    result, state_dir, flow_dir, slate = apply(tmp_path)
    day = MIDDAY_NOW.date().isoformat()
    journal_lines = (state_dir / f"judge_{day}.jsonl").read_text().strip().splitlines()
    row = json.loads(journal_lines[-1])
    assert row["kind"] == "slate_judged"
    assert row["slate_id"] == slate["slate_id"]
    assert row["provider"] == "test"
    memory = (state_dir / "JUDGE-MEMORY.md").read_text()
    assert slate["slate_id"] in memory
    assert "a1/h1/x1" in memory  # 1 approve, 1 hold, 1 (demoted) abstain

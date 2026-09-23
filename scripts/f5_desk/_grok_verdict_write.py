from pathlib import Path
import sys
from datetime import datetime, timezone
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common
path = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
payload = {
  "schema": "gtos.f5.judge.verdict.v1",
  "slate_id": "1b20f808c63ab74f",
  "fingerprint": "2a431a1267113ac5",
  "written_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "verdicts": [
    {"candidate_id": "W7_BOOK::dsp_c_isospike::USDJPY::2026-08-28::SHORT::dsp_isolated_spike_high", "verdict": "hold", "mechanism": "microstructure", "why_code": "usdjpy_named_hold", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::dsp_c_walkhigh::USDJPY::2026-08-28::SHORT::dsp_walked_high_accepted_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "usdjpy_named_hold", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::dsp_c_bleed20low::USDJPY::2026-08-27::LONG::dsp_bleed_accept_fresh_20low_second_push", "verdict": "hold", "mechanism": "microstructure", "why_code": "usdjpy_named_hold", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::dsp_c_isospike::XAUUSD::2026-08-28::SHORT::dsp_isolated_spike_high", "verdict": "hold", "mechanism": "microstructure", "why_code": "owner_spent_gold_no_remint_tonight", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::dsp_c_walkhigh::XAUUSD::2026-08-28::SHORT::dsp_walked_high_accepted_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "owner_spent_gold_no_remint_tonight", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::xa_c_huge20::XAUUSD::2026-08-28::LONG::xa_huge_20_extreme", "verdict": "hold", "mechanism": "microstructure", "why_code": "owner_spent_gold_no_remint_tonight", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::xa_c_isoopp::XAUUSD::2026-08-28::LONG::xa_isolated_opposite", "verdict": "hold", "mechanism": "microstructure", "why_code": "owner_spent_gold_no_remint_tonight", "confidence": 0.9},
    {"candidate_id": "W7_BOOK::dsp_c32::GBPUSD::2026-08-28::LONG::dsp_isolated_flush_to_20low_snap", "verdict": "abstain", "mechanism": "", "why_code": "no_place_from_seats", "confidence": 0.4},
    {"candidate_id": "W7_BOOK::dsp_c_bleed20low::GBPUSD::2026-08-28::LONG::dsp_bleed_accept_fresh_20low_second_push", "verdict": "abstain", "mechanism": "", "why_code": "no_place_from_seats", "confidence": 0.4},
    {"candidate_id": "W7_BOOK::dsp_c02::GBPUSD::2026-08-28::LONG::dsp_close_on_20low_not_a_cascade_then_up", "verdict": "abstain", "mechanism": "", "why_code": "no_place_from_seats", "confidence": 0.4},
    {"candidate_id": "W7_BOOK::dsp_c_microbounce::GBPUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "verdict": "abstain", "mechanism": "", "why_code": "no_place_from_seats", "confidence": 0.4},
    {"candidate_id": "W7_BOOK::dsp_c_bleed20low::EURUSD::2026-08-28::LONG::dsp_bleed_accept_fresh_20low_second_push", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c02::EURUSD::2026-08-28::LONG::dsp_close_on_20low_not_a_cascade_then_up", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::fx_reversion::EURUSD::2026-08-28::LONG::asian_fade", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::fx_reversion::EURUSD::2026-08-28::LONG::asian_fade_widen", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c_microbounce::EURUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c_smallsit::EURUSD::2026-08-28::LONG::dsp_small_bar_sit_on_20high_rejects", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c_walkhigh::EURUSD::2026-08-27::SHORT::dsp_walked_high_accepted_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c_walkhigh::US30_cash::2026-08-28::SHORT::dsp_walked_high_accepted_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c_microbounce::US30_cash::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::dsp_c19::US30_cash::2026-08-28::SHORT::dsp_london_two_up_into_20high_reverses", "verdict": "hold", "mechanism": "microstructure", "why_code": "no_second_ticket_occupied", "confidence": 0.8},
    {"candidate_id": "W7_BOOK::crypto::BTCUSD::2026-08-28::SHORT::orb_crypto_london", "verdict": "abstain", "mechanism": "", "why_code": "leave_working_ticket", "confidence": 0.5},
    {"candidate_id": "W7_BOOK::crypto::ETHUSD::2026-08-28::LONG::orb_crypto_london", "verdict": "abstain", "mechanism": "", "why_code": "leave_working_ticket", "confidence": 0.5},
    {"candidate_id": "W7_BOOK::index::GER40::2026-08-28::SHORT::idxrev", "verdict": "abstain", "mechanism": "", "why_code": "leave_working_ticket", "confidence": 0.5}
  ],
  "manage": [],
  "notes": "15:26 ICT leave 5 lives (US30/EUR/GER40/ETH/BTC). HOLD USDJPY+XAU remint. occupied no-second. GBPUSD abstain no place. writer 16640/15552 healthy, close-fail 10011 loop not flatten."
}
common.write_json_atomic(path, payload)
print("wrote", path, payload["written_at_utc"], "n=", len(payload["verdicts"]))

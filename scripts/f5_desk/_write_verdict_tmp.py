from pathlib import Path
import sys
from datetime import datetime, timezone
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
slate_id = "3a3e029ad80f4bd9"
fingerprint = "c6e2f51f9386c700"

# Occupied symbols: no second ticket. USDJPY: named scrub HOLD.
occupied = {"ETHUSD", "EURUSD", "GER40", "UK100", "US30", "US30_cash", "XAUUSD"}
usdjpy_ids = [
    "W7_BOOK::dsp_c_isospike::USDJPY::2026-08-28::SHORT::dsp_isolated_spike_high",
    "W7_BOOK::dsp_c_walkhigh::USDJPY::2026-08-28::SHORT::dsp_walked_high_accepted_through",
    "W7_BOOK::dsp_c_bleed20low::USDJPY::2026-08-27::LONG::dsp_bleed_accept_fresh_20low_second_push",
]
# unique candidate rows we care to word (intents + named)
# Full list of intents from slate parse — HOLD occupied-symbol intents + USDJPY; abstain rest
rows = [
    ("W7_BOOK::dsp_c_walkhigh::US30_cash::2026-08-28::SHORT::dsp_walked_high_accepted_through", "hold", "correlation", "no_second_ticket_us30_live", 0.7),
    ("W7_BOOK::crypto::ETHUSD::2026-08-28::LONG::orb_crypto_london", "abstain", "", "already_live_leave", 0.55),
    ("W7_BOOK::dsp_c_microbounce::XAUUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "abstain", "", "already_live_be_lock_leave", 0.55),
    ("W7_BOOK::dsp_c_bleed20low::EURUSD::2026-08-28::LONG::dsp_bleed_accept_fresh_20low_second_push", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::dsp_c02::EURUSD::2026-08-28::LONG::dsp_close_on_20low_not_a_cascade_then_up", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::dsp_c_bleed20low::GBPUSD::2026-08-28::LONG::dsp_bleed_accept_fresh_20low_second_push", "abstain", "", "no_place_from_seat", 0.45),
    ("W7_BOOK::fx_reversion::EURUSD::2026-08-28::LONG::asian_fade", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::fx_reversion::EURUSD::2026-08-28::LONG::asian_fade_widen", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::dsp_c02::GBPUSD::2026-08-28::LONG::dsp_close_on_20low_not_a_cascade_then_up", "abstain", "", "no_place_from_seat", 0.45),
    ("W7_BOOK::dsp_c_isospike::USDJPY::2026-08-28::SHORT::dsp_isolated_spike_high", "hold", "microstructure", "named_usdjpy_scrub", 0.85),
    ("W7_BOOK::dsp_c_walkhigh::USDJPY::2026-08-28::SHORT::dsp_walked_high_accepted_through", "hold", "microstructure", "named_usdjpy_scrub", 0.85),
    ("W7_BOOK::index::GER40::2026-08-28::SHORT::idxrev", "abstain", "", "already_live_leave", 0.55),
    ("W7_BOOK::dsp_c_microbounce::US30_cash::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "hold", "correlation", "no_second_ticket_us30_live", 0.7),
    ("W7_BOOK::dsp_c32::EURUSD::2026-08-27::LONG::dsp_isolated_flush_to_20low_snap", "abstain", "", "already_live_leave", 0.55),
    ("W7_BOOK::dsp_c_microbounce::EURUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::dsp_c_microbounce::GBPUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through", "abstain", "", "no_place_from_seat", 0.45),
    ("W7_BOOK::dsp_c19::US30_cash::2026-08-28::SHORT::dsp_london_two_up_into_20high_reverses", "hold", "correlation", "no_second_ticket_us30_live", 0.7),
    ("W7_BOOK::dsp_c_smallsit::EURUSD::2026-08-28::LONG::dsp_small_bar_sit_on_20high_rejects", "hold", "correlation", "no_second_ticket_eurusd_live", 0.7),
    ("W7_BOOK::dsp_c_bleed20low::USDJPY::2026-08-27::LONG::dsp_bleed_accept_fresh_20low_second_push", "hold", "microstructure", "named_usdjpy_scrub", 0.85),
    ("W7_BOOK::index::UK100::2026-08-27::LONG::idxrev", "abstain", "", "already_live_leave", 0.55),
    ("W7_BOOK::index::US30_cash::2026-08-27::LONG::idxrev", "abstain", "", "already_live_leave", 0.55),
    ("W7_BOOK::liquidity_sweep::USDCHF::2026-08-27::LONG::asia_pdl_fade", "abstain", "", "no_place_from_seat", 0.4),
]

verdicts = []
seen = set()
for cid, v, mech, why, conf in rows:
    if cid in seen:
        continue
    seen.add(cid)
    verdicts.append({
        "candidate_id": cid,
        "verdict": v,
        "mechanism": mech,
        "why_code": why,
        "confidence": conf,
    })

payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": slate_id,
    "fingerprint": fingerprint,
    "written_at_utc": now,
    "verdicts": verdicts,
    "manage": [],
    "notes": "13:58 ICT sit: 6 lives leave; USDJPY scrub HOLD; no second ticket on occupied; no place; gold BE lock ignore dump R; writer Running pair alive; close 10011 spam not restart.",
}
path = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
common.write_json_atomic(path, payload)
print("wrote", path, "n=", len(verdicts), "at", now)

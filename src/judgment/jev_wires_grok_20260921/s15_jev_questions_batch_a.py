"""DRAFT ONLY — session 15_residual_static_book_owner_batch_a.

Side question pack for residual STATIC book_owner Batch A.
Do not import from live fire path this session.
Do not mutate judgment/astra/JEV_GATE_INVENTORY.json n_fluid=48.
Never place / remint / flatten / order_send.

IDs are for code; instructions carry meaning (TypeSafe System One).
"""
from __future__ import annotations

from typing import Any

PACK_ID = "gtos.judgment.book_owner_batch_a.v0"
MODEL = "jev-1.13.0"


def batch_a_questions() -> dict[str, Any]:
    return {
        "weekend_carry": {
            "type": "score",
            "instructions": (
                "Given weekend.hours_to_boundary, weekend.flatten_before_hours, "
                "identity.sleeve, geometry.horizon if named, and account.firm / "
                "account.phase: how survivable is holding this fire across the "
                "named weekend boundary? Use only named fields. Do not invent a "
                "session calendar or ATR/regime. Empty news_join is STATE_MISSING "
                "and is not 'no HIGH'."
            ),
            "criteria": [
                "Horizon dies in the flatten window or weekend gap",
                "Ordinary Friday hold; mixed or unnamed horizon",
                "Named clock and horizon fit a legal weekend carry for this firm/phase",
            ],
        },
        "weekend_embargo_action": {
            "type": "choice",
            "instructions": (
                "Static code would SKIP this intent as weekend_entry_embargo. "
                "Pick one action over named weekend.* and account.firm/phase. "
                "KEEP_EMBARGO = leave the skip. DELAY = skip this bar, do not "
                "consume a later legal window. SCOPED_ENTRY_OK = the economic "
                "embargo (not a funded-firm flatten rule) should not skip. "
                "Code will still refuse redacted_account funded and same-tick flatten "
                "window regardless of this answer. This is not PLACE. House "
                "kill/halt/breach/token are not this question."
            ),
            "criteria": {
                "KEEP_EMBARGO": "Leave the static weekend skip",
                "SCOPED_ENTRY_OK": "Economic embargo should not skip; firm/phase still gated in code",
                "DELAY": "Skip now; wait for a later bar outside the window",
            },
        },
        "crypto_weekend_grid": {
            "type": "choice",
            "instructions": (
                "Only when identity.sleeve is crypto. Session BA measured BTCUSD "
                "gapped 43.8% of weeks and quoted through 56.2%. CALENDAR = flat "
                "by Saturday 00:00 whatever the instrument does. GRID = exempt "
                "when the named market is still quoting. ABSTAIN if sleeve is not "
                "crypto or named quote-through is missing. Code owns the firm rule."
            ),
            "criteria": {
                "KEEP_CALENDAR": "Keep calendar weekend embargo/flatten for this crypto fire",
                "GRID_EXEMPT": "Treat as 24/7 quote-through; embargo is the wrong reading",
                "ABSTAIN": "Not crypto, or named quote-through state is missing",
            },
        },
        "tape_fresh": {
            "type": "noul",
            "instructions": (
                "Tick is unnamed/missing (tick.present is false). Is this a "
                "transient broker hole that should RETRY the same decision bar, "
                "or is the tape dead / market closed so the bar should be consumed "
                "and not chased on reopen? Use tick.age_s, minutes_since_decision_bar, "
                "session_bucket if named. Do not invent a trading-session calendar. "
                "Yes = transient, retry. No = consume/stand. This cannot authorize PLACE."
            ),
            "criteria": {
                "true": "Transient hole; retry the same decision bar",
                "false": "Tape dead or market closed; consuming the bar avoids a stale chase",
            },
        },
    }


def batch_a_payload(state: dict[str, Any], *, model: str = MODEL) -> dict[str, Any]:
    return {"state": state, "model": model, "questions": batch_a_questions()}

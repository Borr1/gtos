"""Already-live Dig F place/conf consume flags.

Chair confirmed these live on Challenge 0. This module documents
the consume — it does **not** mint new broker / order_send flags.

``CONF_ORDER_CONSUME``, ``PLACE_APPLY``, and ``PLACE_ENSEMBLE`` are
constants, not ``GTOS_*`` env arms. Missing here must not fail-open a
place path.
"""

from __future__ import annotations

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS

# Chair-confirmed already-live consume (Challenge writer only).
CONF_ORDER_CONSUME = True
PLACE_APPLY = True
PLACE_ENSEMBLE = True

ALREADY_LIVE = {
    "CONF_ORDER_CONSUME": CONF_ORDER_CONSUME,
    "PLACE_APPLY": PLACE_APPLY,
    "PLACE_ENSEMBLE": PLACE_ENSEMBLE,
}

#: Explicitly empty — Dig F must not invent a new broker env.
NEW_BROKER_FLAGS: tuple[str, ...] = ()

PACK1B_BEATEN = False

APPLY_CANDIDATES = (
    "option_order_sensitivity",
    "state_evidence_sufficiency",
    "jev_repeatability_probe",
    "noul_vs_choice_shape",
    "od_13",
)

KILL_STANDALONE_APPLY = (
    "order_ensemble_shuffle",
    "od_10_perm_avg_research_router",
    "od_12_yesno_reverse_regression",
)

CHALLENGE_ONLY = {
    "login": CHALLENGE_LOGIN,
    "ns": CHALLENGE_NS,
    "magic": CHALLENGE_MAGIC,
}


def already_live_consume() -> dict[str, object]:
    """Receipt block: confirm consume, no new broker flags."""

    return {
        "schema": "gtos.judgment.dig_f.already_live.v1",
        "already_live": dict(ALREADY_LIVE),
        "new_broker_flags": list(NEW_BROKER_FLAGS),
        "pack1b_beaten": PACK1B_BEATEN,
        "challenge_only": dict(CHALLENGE_ONLY),
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "dig_never_broker_send": True,
        "news_invent": False,
    }

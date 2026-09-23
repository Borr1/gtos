"""DRAFT ONLY — do not land. Place/occupancy questions for symbol_fanout merge.

Add these keys into gold_fanout_questions() / symbol_fanout_questions().
IDs are for code; instructions carry meaning. One POST, independent questions.
"""

PLACE_OCCUPANCY_QUESTIONS = {
    "place_action": {
        "type": "choice",
        "instructions": (
            "Given named occupancy, freshness, cost, place_context, and affinity, "
            "should the writer send this bar, stand (consume, no send), or delay "
            "(retry the same bar)? Do not send when place_context.live_broker_authority "
            "is false. Do not treat empty news_join as 'no HIGH'. House integers "
            "(2-stop COUNT, keep-one default, kill, token, hard-off) are not this answer. "
            "REMINT and FLATTEN_ADD are occupancy labels; code may still HOLD them."
        ),
        "criteria": {
            "PLACE": (
                "Occupancy is clear or isolated-legal; freshness is inside the named "
                "window; cost is not dominating the named stop; named tape still supports sending."
            ),
            "STAND": (
                "Do not send. Consume the bar: occupied without isolated-legal, "
                "restart-late chase, or cost-dominated versus named stop."
            ),
            "DELAY": (
                "Do not send this tick. Leave the bar unconsumed because tick, "
                "position-source, or spread is transient."
            ),
            "REMINT": (
                "Occupancy is hit but named isolated re-entry / remint geometry supports "
                "a new unit. Not a 15m chase of the same orig_stop."
            ),
            "FLATTEN_ADD": (
                "Occupancy is hit; flatten the existing book ticket then add. "
                "Code may refuse this label until flatten hist-prove."
            ),
        },
    },
    "occupancy_action": {
        "type": "choice",
        "instructions": (
            "If named occupancy shows a hold (already_placed_today, sleeve_holds_symbol, "
            "sleeve_holds_symbol_broker, same_broker_symbol_open, cluster_placed_today_other_bar), "
            "pick HOLD, PLACE_ISOLATED, REMINT, FLATTEN_ADD, SWITCH_SLEEVE, or STAND. "
            "If occupancy is clear, pick STAND — this question is idle. "
            "Confirm occupancy.isolated_reentry_legal. Do not call a legal 15m reprint a remint. "
            "2-stop COUNT stays an integer on occupancy.two_stop_exhausted."
        ),
        "criteria": {
            "HOLD": "Keep the existing unit / skip the new fire. Default keep-one.",
            "PLACE_ISOLATED": (
                "Symbol is flat long enough (isolated_reentry_legal) and this is a new fire, "
                "not a remint of the same stop. two_stop_exhausted is false."
            ),
            "REMINT": "Named remint geometry after an orig_stop. Code may still HOLD.",
            "FLATTEN_ADD": "Flatten existing then add. Code may refuse until prove.",
            "SWITCH_SLEEVE": "Label only: another alive sleeve is the better occupant. Do not retag.",
            "STAND": "Occupancy clear (idle) or mixed/unassembled — do not steer.",
        },
    },
    "freshness_action": {
        "type": "choice",
        "instructions": (
            "If freshness.stale_late_entry_after_restart is true, pick PLACE_FRESH, DELAY, or STAND "
            "from named minutes_past_close versus late_frac and geometry. "
            "If bar_iso or tf is missing, this question should not block a timely fire."
        ),
        "criteria": {
            "PLACE_FRESH": "Still inside a named valid window; geometry not a chase.",
            "DELAY": "Restart-late but state is still assembling; retry the bar.",
            "STAND": "Hours-late chase of a close the edge never entered at.",
        },
    },
    "cost_action": {
        "type": "score",
        "instructions": (
            "Does named cost.spread_r versus cost.max_spread_r and named M15 geometry.atr14 "
            "argue skip, trim, or pass? This may STAND a fire. It must not size-up. "
            "Unassembled spread → ordinary/mid so code keeps the static screen. "
            "Existing cost_hurtful Noul stays a size tilt and cannot refuse."
        ),
        "criteria": [
            "COST_DOMINATED — spread eats a material fraction of the named stop; skip",
            "TRIM — ordinary-hurtful; haircut size only",
            "COST_OK — cheap versus named stop and named M15 vol; do not skip on spread",
        ],
    },
}

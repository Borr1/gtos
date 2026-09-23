"""SKETCH only — not for live import. place_action Choice for symbol_fanout_questions.

Fail-closed: Jev dark → DELAY. Envelope hit → STAND. Never order_send.
"""

PLACE_ACTION_QUESTION = {
    "place_action": {
        "type": "choice",
        "instructions": (
            "Given COMPLETE_STATE — occupancy, named news window, cost vs named M15 ATR, "
            "stale_standing, last_refusal_class, corr HOLD draft, envelope integers already "
            "applied by code, and identity.sleeve times symbol affinity — should the WRITER "
            "be authorized to print this candidate now, stand, or delay to the next bar? "
            "This is not will-it-profit. House hard-off / token / 2-stop COUNT / keep-one "
            "are code, not this answer. Empty news spine is not no HIGH. Missing ATR is "
            "not invented vol. If named state is thin, prefer DELAY. "
            "PLACE means envelope is clear AND named tape/cost/occupancy support printing now. "
            "STAND means named state argues do not print this candidate this cycle. "
            "DELAY means wait for the next bar or missing state. "
            "You do not send. You do not remint. You do not flatten."
        ),
        "criteria": {
            "PLACE": "Envelope-clear candidate; named tape/cost/occupancy support printing now",
            "STAND": "Named state argues do not print this candidate this cycle",
            "DELAY": "State thin, stale, or wait-next-bar; do not authorize send",
        },
    }
}

"""Wave-21 forward-shadow lane.

Runs the frozen MARKET-top-choice funnel decision path
(MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1) on LIVE forward data with ZERO broker
mutations, logging every would-be decision.  This package deliberately contains
no order transmission surface of any kind: no ``order_send``, no activation
token, no book interaction.  The read adapter exposes read-only MetaTrader5
calls only and raises on any mutation-shaped attribute.
"""

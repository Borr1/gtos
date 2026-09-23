"""The broker-truth cost layer. One function owns every cost number in GTOS.

    from src.costs import cost_r
    breakdown = cost_r("USDJPY", "FTMO", holding_hours=2.5, sl_distance_price=0.08)
    breakdown.total_r.value        # cost in R
    breakdown.commission_r.coverage  # Coverage.MEASURED

Backed by the versioned ``BROKER_TRUE_COSTS_V1.json``. Every number carries a coverage
class ([MEASURED] / [TRANSFERRED] / [MODELLED]) and the class travels into every result
computed from it -- a total built on a modelled commission is modelled.

Why this layer exists: F38. The validation and the pre-CN live pre-trade engine charged
**zero commission at five independent sites** (`GATE_G1B_RECEIPT.md` §5.2a), while realized
commission and swap were **31.6% of the live W7 loss**. Session CN wired this layer into the
default live packet as the fourth cost term; the old three-term arithmetic now exists only as
an explicitly named offline comparator.
"""

from src.costs.coverage import Coverage, Measure, weakest
from src.costs.model import (
    DEFAULT_ARTIFACT,
    BrokerTrueCosts,
    CostBreakdown,
    CostTruthError,
    account_for,
    commission_usd_per_lot,
    commission_usd_per_lot_for_packet,
    cost_r,
    legacy_class_cost_r,
    load_broker_true_costs,
    rollover_nights,
    swap_price_drag_per_night,
)

__all__ = [
    "Coverage",
    "Measure",
    "weakest",
    "BrokerTrueCosts",
    "CostBreakdown",
    "CostTruthError",
    "cost_r",
    "account_for",
    "commission_usd_per_lot",
    "commission_usd_per_lot_for_packet",
    "legacy_class_cost_r",
    "load_broker_true_costs",
    "rollover_nights",
    "swap_price_drag_per_night",
    "DEFAULT_ARTIFACT",
]

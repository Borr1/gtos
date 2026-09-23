"""KILL fence — standalone ``order_ensemble_shuffle`` APPLY stub.

Subsumed by OD-13 under already-live ``PLACE_APPLY`` / ``PLACE_ENSEMBLE``.
Any APPLY entrypoint here must fail closed. Dig never broker-sends.
"""

from __future__ import annotations

from .od13_ensemble import StandaloneOrderEnsembleError, refuse_standalone_order_ensemble

APPLY_ENABLED = False
STANDALONE_PATH = False
SUBSUMED_BY = "od_13"


def apply_order_ensemble_shuffle(*_args: object, **_kwargs: object) -> None:
    """Dead APPLY stub. Always raises."""

    refuse_standalone_order_ensemble("order_ensemble_shuffle")


def apply_od_10_perm_avg_research_router(*_args: object, **_kwargs: object) -> None:
    refuse_standalone_order_ensemble("od_10_perm_avg_research_router")


def apply_od_12_yesno_reverse_regression(*_args: object, **_kwargs: object) -> None:
    refuse_standalone_order_ensemble("od_12_yesno_reverse_regression")


def apply_order_ensemble(*_args: object, **_kwargs: object) -> None:
    refuse_standalone_order_ensemble("ORDER_ENSEMBLE")


__all__ = [
    "APPLY_ENABLED",
    "STANDALONE_PATH",
    "SUBSUMED_BY",
    "StandaloneOrderEnsembleError",
    "apply_od_10_perm_avg_research_router",
    "apply_od_12_yesno_reverse_regression",
    "apply_order_ensemble",
    "apply_order_ensemble_shuffle",
]

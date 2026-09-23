"""GTOS Feedback Fleet — one relay, N demo PLACE workers, LABEL feedback.

Source login 0. Quarantine 0. PLACE only on Free Trial / demo.
Chair / Jev / run_book.py still never place on observer books.
"""

from .allowlist import FORBIDDEN_LOGINS, PlaceVeto, place_veto_reason
from .common import (
    QUARANTINE_LOGINS,
    SOURCE_LOGIN,
    load_schema,
    miss_type_for_timing,
    normalize_book_row,
    validate_fleet_event,
    validate_fleet_feedback,
)

__all__ = [
    "FORBIDDEN_LOGINS",
    "PlaceVeto",
    "QUARANTINE_LOGINS",
    "SOURCE_LOGIN",
    "load_schema",
    "miss_type_for_timing",
    "normalize_book_row",
    "place_veto_reason",
    "validate_fleet_event",
    "validate_fleet_feedback",
]

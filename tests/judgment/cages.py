"""Helpers so live-path tests follow PLACE_APPLY instead of eternal True."""

from __future__ import annotations

from typing import Mapping

import pytest

from src.judgment.place_apply import action_unlockable, cage_stamp, place_authorized
from src.judgment.veto import JevPlacePathVeto, refuse_broker_action


def assert_live_cages(doc: Mapping[str, object], **kwargs) -> None:
    """Process-level cages follow the owner unlock, not Chair eternal True."""

    expected = cage_stamp(**kwargs)
    assert doc["never_place"] is expected["never_place"]
    if "never_remint" in doc:
        assert doc["never_remint"] is expected["never_remint"]
    if "never_flatten" in doc:
        assert doc["never_flatten"] is expected["never_flatten"]


def assert_refuse_broker(action: str, **kwargs) -> None:
    """Unlockable broker actions raise only while the Challenge cage is locked."""

    if action_unlockable(action) and place_authorized(**kwargs):
        refuse_broker_action(action)
        return
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action(action)

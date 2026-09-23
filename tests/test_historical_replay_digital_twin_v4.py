from __future__ import annotations

from pathlib import Path

import yaml

from src.research.historical_replay_digital_twin_v4 import (
    MATERIAL_SOURCE_SPECS,
    ROUTE_DIR,
    load_source_entries,
    no_api_policy_record,
    time_split_assignments,
    verify_route,
)


def test_historical_replay_digital_twin_no_api_policy_blocks_market_replay():
    decision = no_api_policy_record()

    assert decision["allowed"] is False
    assert decision["action"] == "SKIP_AI_NO_API_REPLAY"
    assert decision["reason"] == "ai_cost_control_no_api_market_replay"



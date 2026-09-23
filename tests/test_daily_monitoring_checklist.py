from __future__ import annotations

import json

from scripts import build_daily_monitoring_checklist as mod
from scripts import build_limitations_to_opportunities_queue_state as lto_mod


def test_extract_python_commands_dedupes_slash_variants():
    text = "\n".join(
        [
            "```powershell",
            "python scripts\\follow_live_candidate_paths.py --max-hours 12",
            "python scripts/follow_live_candidate_paths.py --max-hours 12",
            "python scripts\\verify_shadow_log_integrity.py",
            "```",
        ]
    )

    commands = mod.extract_python_commands(text)

    assert commands == [
        "python scripts\\follow_live_candidate_paths.py --max-hours 12",
        "python scripts\\verify_shadow_log_integrity.py",
    ]



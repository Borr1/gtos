"""In-place Cohort A patches for F5 book_engine.py and execution_packets.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"host-local\redacted_host\repo\src\components\ultimate_book")
ENG = ROOT / "book_engine.py"
EX = ROOT / "execution_packets.py"


def patch_engine() -> str:
    text = ENG.read_text(encoding="utf-8")
    changed = []
    old_imp = "from .sleeves.registry import active_specs"
    new_imp = "from .sleeves.registry import DISPLACEMENT_BUILT, active_specs"
    if new_imp not in text:
        if old_imp not in text:
            raise SystemExit("engine import needle missing")
        text = text.replace(old_imp, new_imp, 1)
        changed.append("import")
    old_f = "        if spec.tag in admitted\n    ]"
    new_f = "        if spec.tag in admitted or spec.tag in DISPLACEMENT_BUILT\n    ]"
    if "spec.tag in DISPLACEMENT_BUILT" not in text:
        if old_f not in text:
            raise SystemExit("engine filter needle missing")
        text = text.replace(old_f, new_f, 1)
        changed.append("filter")
    ENG.write_text(text, encoding="utf-8")
    return ",".join(changed) if changed else "already"


def patch_packets() -> str:
    text = EX.read_text(encoding="utf-8")
    if "dsp_climax_flush_to_96low_then_snap" in text:
        return "already"
    needle = (
        '    "vss_fxcross_london_up_low": dict(policy="time_stop", final_from_intent=True, final_target_r=2.0,\n'
        "                                      time_stop_bars=48),\n"
        "}"
    )
    insert = (
        '    "vss_fxcross_london_up_low": dict(policy="time_stop", final_from_intent=True, final_target_r=2.0,\n'
        "                                      time_stop_bars=48),\n"
        "    # Cohort A: H=32, stop 0.75 ATR, target 6.0 ATR. final_from_intent so\n"
        "    # broker TP is 6.0/0.75 = 8R, not DEFAULT_EXIT_PROFILE's 2R.\n"
        '    "dsp_climax_flush_to_96low_then_snap": dict(\n'
        '        policy="time_stop", final_from_intent=True, time_stop_bars=32),\n'
        '    "dsp_london_two_up_into_20high_reverses": dict(\n'
        '        policy="time_stop", final_from_intent=True, time_stop_bars=32),\n'
        '    "dsp_expanding_up_staircase": dict(\n'
        '        policy="time_stop", final_from_intent=True, time_stop_bars=32),\n'
        "}"
    )
    if needle not in text:
        raise SystemExit("packets needle missing")
    EX.write_text(text.replace(needle, insert, 1), encoding="utf-8")
    return "inserted"


if __name__ == "__main__":
    print("engine", patch_engine())
    print("packets", patch_packets())

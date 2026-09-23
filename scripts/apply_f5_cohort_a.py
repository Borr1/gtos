"""In-place Cohort A patches for F5 admission.py. Idempotent."""
from __future__ import annotations

from pathlib import Path

ADM = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\admission.py")

BLOCK = '''# Cohort A displacement (2026-08-21 Path A). Not in SLEEVE_REGISTRY so --tags ""
# cannot fail-open them. Admission knows them so a later remint cannot
# fail_closed:unknown_sleeve. Distinct cluster ids until T3 Jaccard.
_DSP_FIRST_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30_cash")
DISPLACEMENT_REGISTRY: dict[str, SleeveSpec] = {
    "dsp_climax_flush_to_96low_then_snap": SleeveSpec(
        "dsp_climax_flush_to_96low_then_snap", 0.15, "dsp_c_flush",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 LONG "
        "(geometry.py best_both_halves hold R +0.157); V2 up-rate SHORT was WRONG"),
    "dsp_london_two_up_into_20high_reverses": SleeveSpec(
        "dsp_london_two_up_into_20high_reverses", 0.15, "dsp_c_londonrev",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 SHORT "
        "(geometry.py best_both_halves hold R +0.133); V2 up-rate LONG was WRONG"),
    "dsp_expanding_up_staircase": SleeveSpec(
        "dsp_expanding_up_staircase", 0.15, "dsp_c_stair",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 SHORT "
        "(geometry.py best_both_halves hold R +0.146); V2 up-rate LONG was WRONG"),
}
DISPLACEMENT_NAMES: tuple[str, ...] = tuple(DISPLACEMENT_REGISTRY.keys())

'''

NEEDLE1 = (
    "# Corr-cluster map (KB2_true_corr_mc.md: cross-sleeve corr ~0; same-class same-day = ONE unit)."
)
FULL_LINE = (
    "CLUSTER_OF_SLEEVE_FULL.update({n: s.asset_class for n, s in DISPLACEMENT_REGISTRY.items()})\n"
)
NEEDLE2 = (
    "CLUSTER_OF_SLEEVE_FULL.update({n: s.asset_class for n, s in CLEAN4_REGISTRY.items()})\n"
)
NEEDLE3 = (
    "        market_expansion_sleeves=market_expansion_sleeves,\n"
    "    )\n"
    "    # DROPPING pre-count filters"
)
INSERT3 = (
    "        market_expansion_sleeves=market_expansion_sleeves,\n"
    "    )\n"
    "    # Cohort A: do not enlarge the default live registry. When a tags-gated\n"
    "    # dsp_* intent is actually present, admit it with its own cluster.\n"
    "    dsp_present = {it.sleeve for it in intents if it.sleeve in DISPLACEMENT_REGISTRY}\n"
    "    if dsp_present:\n"
    "        registry = dict(registry)\n"
    "        registry.update({name: DISPLACEMENT_REGISTRY[name] for name in dsp_present})\n"
    "    # DROPPING pre-count filters"
)


def main() -> int:
    text = ADM.read_text(encoding="utf-8")
    changed = []
    if "DISPLACEMENT_REGISTRY: dict[str, SleeveSpec]" not in text:
        if NEEDLE1 not in text:
            raise SystemExit("needle1 missing")
        text = text.replace(NEEDLE1, BLOCK + NEEDLE1, 1)
        changed.append("registry")
    if FULL_LINE not in text:
        if NEEDLE2 not in text:
            raise SystemExit("needle2 missing")
        text = text.replace(NEEDLE2, NEEDLE2 + FULL_LINE, 1)
        changed.append("cluster_full")
    if "dsp_present =" not in text:
        if NEEDLE3 not in text:
            raise SystemExit("needle3 missing")
        text = text.replace(NEEDLE3, INSERT3, 1)
        changed.append("admit")
    ADM.write_text(text, encoding="utf-8")
    print("admission_ok", ",".join(changed) if changed else "already")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

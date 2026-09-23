from pathlib import Path

import yaml

from src.components.ultimate_book.admission import (
    CLEAN3_REGISTRY,
    CLEAN4_REGISTRY,
    SLEEVE_REGISTRY,
    effective_registry,
)
from src.components.ultimate_book.sleeves import metals as MT
from src.components.ultimate_book.sleeves.registry import BUILT


ROOT = Path(__file__).resolve().parents[2]


def _runtime_config() -> dict:
    cfg = yaml.safe_load((ROOT / "config" / "agent_config.yaml").read_text())
    return cfg["gtos_vnext_runtime"]


def test_active_config_effective_registry_is_core8_and_generation_covered():
    # STALE EXPECTATION fixed 2026-08-25: this test pinned the pre-F5 mainline contract
    # (include_clean3 False, effective registry == core8). In THIS tree (f5max-ship, the
    # live F5 book source) the committed contract is the FULL surface:
    # config/agent_config.yaml:1291 "ultimate_book_include_clean3: true  # F5 2026-08-12:
    # full surface for the minimal-size experiment" (CLAUDE.md §4 F5 bullet; authority
    # docs/audits/fable-20260825/OWNER-GRANT-20260825.md). clean_4 remains opt-in-later
    # (:1292). The protections kept: clean4 stays OFF, the active sizing registry is
    # exactly core8 ∪ clean3 (11 sleeves, nothing more), and every active sleeve is
    # generation-covered (present in BUILT).
    cfg = _runtime_config()
    active = effective_registry(
        include_clean3=cfg["ultimate_book_include_clean3"],
        include_clean4=cfg["ultimate_book_include_clean4"],
    )
    core = set(SLEEVE_REGISTRY)
    clean3 = set(CLEAN3_REGISTRY)
    clean4 = set(CLEAN4_REGISTRY)

    assert cfg["ultimate_book_include_clean3"] is True
    assert cfg["ultimate_book_include_clean4"] is False
    assert set(active) == core | clean3
    assert len(core) == 8 and len(clean3) == 3 and len(set(active)) == 11
    assert not (set(active) & clean4)
    assert core <= set(BUILT)
    assert set(active) <= set(BUILT)


def test_metals_softband_low_vol_boost_is_explicit_bounded_and_disjoint():
    assert MT._size_mult_soft(0.0399, 1.0) == 0.0

    for ac in (0.04, 0.06, 0.09, 0.099):
        boosted = MT._size_mult_soft(ac, 1.34)
        neutral_low_edge = MT._size_mult_soft(ac, 1.35)
        neutral_high_edge = MT._size_mult_soft(ac, 1.599)
        reduced = MT._size_mult_soft(ac, 1.60)

        assert boosted == round(neutral_low_edge * 1.15, 4)
        assert neutral_low_edge == neutral_high_edge
        assert reduced == round(neutral_high_edge * 0.90, 4)
        assert boosted <= 1.5
        assert 0.50 * boosted <= 0.75

    assert MT.AC_FLOOR_SB == 0.04
    assert MT.AC_THR == 0.10
    assert MT._size_mult_soft(MT.AC_THR, 1.34) > 0.0

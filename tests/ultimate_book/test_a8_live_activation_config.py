from pathlib import Path

import yaml

from src.components.ultimate_book.admission import (
    GovernorLimits,
    GovernorState,
    TradeIntent,
    admit_and_size,
)
from src.components.ultimate_book.bridge import DEFAULT_CONFIG


ROOT = Path(__file__).resolve().parents[2]


def _runtime_config() -> dict:
    cfg = yaml.safe_load((ROOT / "config" / "agent_config.yaml").read_text())
    return cfg["gtos_vnext_runtime"]


def _metal_intents() -> list[TradeIntent]:
    return [
        TradeIntent(
            "metals_core",
            "XAUUSD",
            1,
            "2026-06-18",
            10.0,
            target_dist=25.0,
            htf_slope_norm=0.5,
            mom_20_atr=0.5,
            fvg_freshness_bars=2,
            atr_ratio=1.0,
            session_hour=3,
        ),
        TradeIntent(
            "metals_core",
            "XAGUSD",
            1,
            "2026-06-18",
            10.0,
            target_dist=25.0,
            htf_slope_norm=-0.5,
            mom_20_atr=-0.5,
            fvg_freshness_bars=99,
            atr_ratio=2.5,
            session_hour=15,
        ),
    ]


def _state() -> GovernorState:
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


def _metals_unit_n(out: dict) -> int:
    for unit in out["units"]:
        if unit["cluster"] == "metals":
            return unit["n_trades"]
    return 0


def test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile():
    # 2026-08-25: these assertions are the TRUE committed contract of this tree (f5max-ship,
    # the live F5 book source): all four ultimate_book gates are armed at
    # config/agent_config.yaml:1266-1269 ("ARMED 2026-08-12 for the F5 minimal-size
    # experiment tree ONLY"; authority docs/audits/fable-20260825/OWNER-GRANT-20260825.md).
    # The Session-AT KEEP-REAL xfail row filed when mainline was disarmed is CLOSED in
    # phase6/TEST_TRIAGE_V1.json per that marker's own close-out instruction. Mainline
    # stays disarmed by design; this tree's config is the one the F5 book runs.
    cfg = _runtime_config()
    assert DEFAULT_CONFIG["ultimate_book_metals_confluence_gate"] is False
    assert cfg["ultimate_book_metals_confluence_gate"] is True
    assert cfg["ultimate_book_enabled"] is True
    assert cfg["ultimate_book_apply_to_execution"] is True
    assert cfg["ultimate_book_live_activation_allowed"] is True
    assert cfg["ultimate_book_profile"] == "clean3_w7_ceiling_nom2p00"
    assert cfg["ultimate_book_derisk_mode"] == "smooth"
    assert cfg["ultimate_book_stress_derisk"] is True


def test_active_a8_gate_is_shrink_only_on_featured_metals_intents():
    cfg = _runtime_config()
    limits = GovernorLimits(derisk_mode=cfg["ultimate_book_derisk_mode"])
    base_kwargs = dict(
        state=_state(),
        profile=cfg["ultimate_book_profile"],
        include_clean3=cfg["ultimate_book_include_clean3"],
        include_clean4=cfg["ultimate_book_include_clean4"],
        kelly_lite=cfg["ultimate_book_kelly_lite"],
        kelly_conservative=cfg["ultimate_book_kelly_conservative"],
        stress_derisk=cfg["ultimate_book_stress_derisk"],
        limits=limits,
    )

    off = admit_and_size(
        _metal_intents(),
        metals_confluence_gate=False,
        **base_kwargs,
    )
    on = admit_and_size(
        _metal_intents(),
        metals_confluence_gate=cfg["ultimate_book_metals_confluence_gate"],
        **base_kwargs,
    )

    assert off["new_entries_allowed"] is True
    assert on["new_entries_allowed"] is True
    assert _metals_unit_n(off) == 2
    assert _metals_unit_n(on) == 1
    assert on["metals_confluence_gate"] is True
    assert on["units"][0]["unit_risk_pct"] <= off["units"][0]["unit_risk_pct"]

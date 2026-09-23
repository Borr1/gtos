#!/usr/bin/env python3
"""Verify the A8 live activation packet without traversing the large route tree."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
A8_RESULT = (
    ROOT
    / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
    / "A8_BOOK_MC_RESULT.json"
)


def _repo_imports():
    sys.path.insert(0, str(ROOT))
    from src.components.ultimate_book.admission import (  # noqa: WPS433
        GovernorLimits,
        GovernorState,
        TradeIntent,
        admit_and_size,
    )
    from src.components.ultimate_book.bridge import DEFAULT_CONFIG  # noqa: WPS433

    return GovernorLimits, GovernorState, TradeIntent, admit_and_size, DEFAULT_CONFIG


def _active_runtime_config() -> dict:
    cfg = yaml.safe_load((ROOT / "config/agent_config.yaml").read_text())
    return cfg["gtos_vnext_runtime"]


def _metal_intents(TradeIntent):
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


def _metals_n(out: dict) -> int:
    for unit in out["units"]:
        if unit["cluster"] == "metals":
            return int(unit["n_trades"])
    return 0


def _check(name: str, passed: bool, detail: dict | None = None) -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    GovernorLimits, GovernorState, TradeIntent, admit_and_size, DEFAULT_CONFIG = _repo_imports()
    runtime = _active_runtime_config()
    a8 = json.loads(A8_RESULT.read_text())

    state = GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )
    limits = GovernorLimits(derisk_mode=runtime["ultimate_book_derisk_mode"])
    common = dict(
        state=state,
        profile=runtime["ultimate_book_profile"],
        include_clean3=runtime["ultimate_book_include_clean3"],
        include_clean4=runtime["ultimate_book_include_clean4"],
        kelly_lite=runtime["ultimate_book_kelly_lite"],
        kelly_conservative=runtime["ultimate_book_kelly_conservative"],
        stress_derisk=runtime["ultimate_book_stress_derisk"],
        limits=limits,
    )
    off = admit_and_size(_metal_intents(TradeIntent), metals_confluence_gate=False, **common)
    on = admit_and_size(
        _metal_intents(TradeIntent),
        metals_confluence_gate=runtime["ultimate_book_metals_confluence_gate"],
        **common,
    )

    checks = [
        _check(
            "bridge_default_remains_fail_safe",
            DEFAULT_CONFIG["ultimate_book_metals_confluence_gate"] is False,
        ),
        _check(
            "active_config_arms_a8",
            runtime.get("ultimate_book_metals_confluence_gate") is True,
        ),
        _check(
            "live_triple_gate_true",
            all(
                runtime.get(k) is True
                for k in (
                    "ultimate_book_enabled",
                    "ultimate_book_apply_to_execution",
                    "ultimate_book_live_activation_allowed",
                )
            ),
        ),
        _check(
            "live_profile_has_smooth_ceiling_guard",
            runtime.get("ultimate_book_profile") == "clean3_w7_ceiling_nom2p00"
            and runtime.get("ultimate_book_derisk_mode") == "smooth"
            and runtime.get("ultimate_book_stress_derisk") is True,
        ),
        _check(
            "a8_evidence_passed_book_gate",
            a8.get("reproduced_rows") is True
            and a8.get("reproduced_column") is True
            and a8.get("every_split_sharpe_gain") is True
            and a8.get("beats_placebo_every_split") is True,
            {
                "kept": a8.get("kept"),
                "n_total": a8.get("n_total"),
                "key_dial": a8.get("key_dial"),
            },
        ),
        _check(
            "a8_improves_mc_tail_and_pass_rate",
            a8["mc_a8"]["p_pass"] > a8["mc_base"]["p_pass"]
            and a8["mc_a8"]["p_fail_dd"] < a8["mc_base"]["p_fail_dd"]
            and a8["mc_a8"]["worst_day_pct"] > a8["mc_base"]["worst_day_pct"],
            {"mc_base": a8["mc_base"], "mc_a8": a8["mc_a8"]},
        ),
        _check(
            "runtime_gate_shrinks_featured_failing_metal",
            off["new_entries_allowed"] is True
            and on["new_entries_allowed"] is True
            and _metals_n(off) == 2
            and _metals_n(on) == 1,
            {"off_metals_trades": _metals_n(off), "on_metals_trades": _metals_n(on)},
        ),
        _check(
            "runtime_gate_does_not_increase_unit_risk",
            bool(on["units"])
            and bool(off["units"])
            and on["units"][0]["unit_risk_pct"] <= off["units"][0]["unit_risk_pct"],
            {
                "off_unit_risk_pct": off["units"][0]["unit_risk_pct"] if off["units"] else None,
                "on_unit_risk_pct": on["units"][0]["unit_risk_pct"] if on["units"] else None,
            },
        ),
    ]
    ok = all(c["passed"] for c in checks)
    result = {
        "ok": ok,
        "decision": "ARM_A8_METALS_CONFLUENCE_GATE_FOR_LIVE_AND_VPS" if ok else "BLOCK_A8_ACTIVATION",
        "active_config": {
            "ultimate_book_metals_confluence_gate": runtime.get("ultimate_book_metals_confluence_gate"),
            "ultimate_book_profile": runtime.get("ultimate_book_profile"),
            "ultimate_book_derisk_mode": runtime.get("ultimate_book_derisk_mode"),
            "ultimate_book_stress_derisk": runtime.get("ultimate_book_stress_derisk"),
            "ultimate_book_include_clean3": runtime.get("ultimate_book_include_clean3"),
        },
        "headline_numbers": {
            "book_sharpe_base": a8["base"]["all"]["sharpe"],
            "book_sharpe_a8": a8["a8"]["all"]["sharpe"],
            "mc_pass_base": a8["mc_base"]["p_pass"],
            "mc_pass_a8": a8["mc_a8"]["p_pass"],
            "p_fail_dd_base": a8["mc_base"]["p_fail_dd"],
            "p_fail_dd_a8": a8["mc_a8"]["p_fail_dd"],
            "worst_day_pct_base": a8["mc_base"]["worst_day_pct"],
            "worst_day_pct_a8": a8["mc_a8"]["worst_day_pct"],
            "key_dial": a8["key_dial"],
            "kept": a8["kept"],
            "n_total": a8["n_total"],
        },
        "checks": checks,
    }
    result_path = ROUTE / "A8_LIVE_ACTIVATION_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n")

    manifest = {
        "route": ROUTE.name,
        "decision": result["decision"],
        "files": [
            "verify_a8_live_activation.py",
            "A8_LIVE_ACTIVATION_PACKET.md",
            "A8_LIVE_ACTIVATION_RESULT.json",
            "A8_LIVE_ACTIVATION_OUTPUT_MANIFEST.json",
            "A8_LIVE_ACTIVATION_COMPLETION_AUDIT.json",
        ],
    }
    (ROUTE / "A8_LIVE_ACTIVATION_OUTPUT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    audit = {
        "ok": ok,
        "result_path": str(result_path.relative_to(ROOT)),
        "issue_count": 0 if ok else sum(1 for c in checks if not c["passed"]),
        "no_broker_or_order_mutation": True,
        "runtime_config_mutation": "config/agent_config.yaml gtos_vnext_runtime.ultimate_book_metals_confluence_gate=true",
    }
    (ROUTE / "A8_LIVE_ACTIVATION_COMPLETION_AUDIT.json").write_text(
        json.dumps(audit, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

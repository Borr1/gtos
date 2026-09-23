#!/usr/bin/env python3
"""DRAFT ONLY — not landed. Challenge 0 conf_gate + regime_gate hist-prove.

Phase 1 can run injected S14/S15 scripts already in _pr41_land.
Phase 2 (live evaluate) is sketched here and must not order_send.

Honesty:
  - S14 tape atr14=1.2/atr50=1.0 is lab_constant, not Module_ATR
  - never merge Dig_3R / Edge_ATR / Module_ATR R
  - numeric conf absent on hist labels until evaluate() harvest
"""

from __future__ import annotations

APPLY_GATE = {
    "wins_preserved": None,
    "n_order_send": 0,
    "n_invented_news": 0,
    "n_invented_atr": 0,
    "module_atr_R_merged": False,
    "atr_source_forbidden_for_apply": "lab_constant",
    "numeric_conf_sidecar": False,
    "GTOS_JEV_CONF_GATE_APPLY": 0,
    "GTOS_JEV_REGIME_GATE_APPLY": 0,
    "GTOS_JEV_SLEEVE_SELECT_APPLY": 0,
    "place": False,
}

KEEP_WIN_TICKETS = ("291816474", "293540988", "291794419")
RESIDUAL_TICKETS = ("291087142", "293128383")

METRICS = (
    "n",
    "n_jev_ok",
    "n_jev_dark",
    "n_yes",
    "n_no",
    "n_unsure",
    "n_regime_tag_pending",
    "n_atr_omitted",
    "fire_rate_shadow",
    "fire_rate_baseline",
    "sumR_challenge",
    "sumR_Module_ATR",
    "maxDD_challenge",
    "wins_preserved",
    "n_order_send",
    "n_invented_news",
    "n_invented_atr",
)


def main() -> int:
    print("DRAFT hist-prove harness — not executable land.")
    print("Use _pr41_land scripts/run_s14_historical_prove.py for Phase 1.")
    print("APPLY_GATE", APPLY_GATE)
    print("KEEP_WIN_TICKETS", KEEP_WIN_TICKETS)
    print("METRICS", METRICS)
    return 2  # refuse APPLY env by convention of p0 hist-prove


if __name__ == "__main__":
    raise SystemExit(main())

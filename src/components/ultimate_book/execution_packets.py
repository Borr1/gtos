"""execution_packets.py — build the FULL V4 trade_params for one sized W7 book unit.

Pure (stdlib + the V4 contract builders). NO MT5 / NO broker / NO order. Produces the dict that
clears all three live fail-closed gates the runtime runs in ExecutionEngine.open_trade:
  1. _vnext_dynamic_policy_support_error  (execution.py:2683-2689 / :1490-1533)
  2. evaluate_execution_manager_v4         (execution.py:2840-2860 / execution_manager_v4.py:617)
  3. _resolve_vnext_production_risk_pct    (execution.py:2804-2813 / :1591-1677)

The pretrade_cost_model is NOT a trade_params key — it is a separate order-send argument the
order router must build from a live tick (execution.py:2833 build_pretrade_cost_packet).

The target multiple and the risk percent written on a live order are the System One
scores for that state (model jev-1.13.0, POST https://api.typesafe.ai/v1/systemone,
Noul / Choice / Score only). An empty answer, a tie, or an error leaves those fields
unset. This module does not send.
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hashlib
import json as _json
from typing import Any, Mapping

from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.prop_firm_headroom_v4 import (
    build_prop_firm_headroom_snapshot_v4_from_account_state,
)

# ---- config-default constants (mirror the FTMO-merged live config; verified [RAN]) -------------
PROFILE_NAMESPACE = "operator_profile"          # operator_profile.yaml

# ---- THE TIME-STOP UNIT, AND THE ONE WAY TO WRITE IT --------------------------------------------
# `time_stop_bars` below is **M15 bars that PRINTED** -- trading bars, so nights, weekends and
# holidays do not count -- for EVERY sleeve, whatever grid the sleeve decides on. The engine that
# consumes it counts M15 stamps and compares the count to this integer:
#     src/components/execution.py:8953-8958   ExecutionEngine._trading_m15_bars_since
#     src/components/execution.py:9010-9014   check_time_stop_and_close
# So an H4 or D1 sleeve MUST declare its horizon pre-scaled, and hand-scaling is exactly where it
# has already gone wrong once: the fourteen `mx_*` D1 sleeves carried **96**, which is
# `M15_BARS_PER["D1"]` -- the conversion RATIO written into the field that wants the converted
# VALUE. Their live time stop was therefore 1 D1 bar against the 80-D1-bar research horizon every
# published economic number for them was measured under: 80x tight, truncating 72-90 % of the
# walked trades (Session AQ, B1400-B1404; measured per symbol in
# `docs/audits/fable5-vision-audit-20260725/phase7/receipts/AD_TIMESTOP_UNITS_V1.json`).
#
# Write `time_stop_m15(n_native_bars, "<grid>")`, never a hand-multiplied literal. The conversion
# is CALENDAR, because a spec is per sleeve while the printed-bar ratio is per symbol (96 on a
# 24/7 symbol, 92 on a session index, 84 on UKOIL). On a session symbol the result therefore runs
# ~4 % PAST the native horizon rather than short of it -- looser than research, never tighter,
# which is the safe direction for a backstop.
def time_stop_m15(n_native_bars: int, grid: str):
    """Native bars of `grid` in M15 prints. The ratio is the score for that grid.

    An empty score leaves the horizon unset.
    """
    try:
        from src.judgment.nineteen import score
        per = score(
            {"grid": str(grid), "native_bars": n_native_bars},
            question_id="m15_bars_per",
            instructions=(
                "The score you return is how many M15 prints one bar of this grid contains. "
                "It may sit between the levels. An empty score leaves the ratio unset. Do not send."
            ),
        )
    except Exception:
        return None
    if per is None:
        return None
    try:
        n = int(n_native_bars)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n * per


#: The horizon every sleeve's published economics are measured under: `maxbars=80` bars of the
#: sleeve's own grid (`AA_ESTATE_TRADES.json.gz` -> `maxbars`, and `ExitPolicy.maxbars`'s default).
#: A sleeve whose time stop is meant to be "the research horizon" declares exactly this.
# ---- PER-SLEEVE EXIT-PROFILE REGISTRY -----------------------------------------------------------
# Each W7 book sleeve carries its OWN validated native exit policy + geometry instead of a single
# forced momentum_exhaustion 2R. `final_from_intent=True` => the broker take-profit R is derived from
# the sleeve's native target_dist/stop_dist (vol-tiered runner / measured-move) rather than a fixed
# R. Resolved per intent in build_book_trade_params; any sleeve not listed falls back to
# DEFAULT_EXIT_PROFILE. Verified [RAN] against the 3 fail-closed gates
# (.tools/probe_per_sleeve_exit_gates.py): all 11 sleeves + the default clear gate1/2/3.
SLEEVE_EXIT_PROFILES: dict[str, dict] = {
    "crypto":            dict(policy="time_stop"),
    "idxrev":            dict(policy="time_stop"),
    "fx_jpy":            dict(policy="time_stop"),
    "fx_jpy_ny":         dict(policy="time_stop"),
    "sub_xvol_pullback": dict(policy="time_stop"),
    "sub_mid_dn_revert": dict(policy="time_stop"),
    "vp_euidx_pocgrav":  dict(policy="time_stop", final_from_intent=True),
    "metals_core":       dict(policy="partial_be_runner", final_from_intent=True),
    "metals_softband":   dict(policy="partial_be_runner", final_from_intent=True),
    "metals_ob_micro":   dict(policy="partial_be_runner", final_from_intent=True),
    # SCALE-OUT REMOVED 2026-08-11 (owner-authorized, swarm-2 lane B7). Was
    # `partial_be_runner`. The target (4R) and the horizon
    # (1280) are UNCHANGED -- the delta is the scale-out alone, which is what makes it measurable.
    # Paired on identical entries, identical bars, identical labeller (n=72, USOIL+UKOIL H4), the
    # live scale-out cost -0.2883 R/trade, t=-2.385, paired CI95 [-0.525, -0.051]. Its mechanism is
    # visible in the exit counts: moving the stop to breakeven on the remainder converts SIX winners
    # into stops (42 -> 48 stop exits). Splitting the two components, the partial costs -0.214 and
    # the breakeven stop a further -0.075. 4R is not the problem: 2R is -0.427 and 3R -0.221 against
    # it, and 6R is indistinguishable (+0.038, n.s.). Third independent instrument to agree in sign,
    # magnitude and mechanism (AD section 6.2 -0.308 R/day; AU +0.2302 R/day restamp error).
    # QUALIFICATION, stated because the lane that proposed this did not: at the (symbol, entry-day)
    # block level -- the correlated unit -- the delta's 95 % interval is [-0.560, +0.0009], i.e. it
    # TOUCHES ZERO, p(delta >= 0) = 0.0254. An independent harness on 67 trades gets -0.2943 with
    # [-0.608, +0.030]. Point estimates agree to three decimals across three harnesses; the
    # intervals do not exclude zero, and at 3.1 trades/month the question needs ~504 weeks to
    # resolve forward. So the sign is well established and the magnitude is not.
    #
    # WHICH IS WHY THE PRIMARY ARGUMENT IS NOT THE DELTA. Every published economic number for this
    # sleeve -- the survivor-book entry, the p_pass, the R/day it was ARMED on -- was measured under
    # the plain 4R exit. `walkforward/exits.py`'s own docstring says AA labelled all four
    # `partial_be_runner` sleeves under plain stop/target/maxbars, making those numbers "about a
    # contract the live book does not run". This makes the sleeve BE the contract that was measured.
    # That holds if the delta is -0.29 and equally if it is 0.00.
    #
    # THE ONE REAL COST, measured rather than asserted: removing the scale-out raises per-trade sd
    # 1.7575 -> 2.3649 (+34.6 %, day-block CI on the ratio [1.278, 1.423] -- MORE certain than the
    # mean effect), the losing-trade fraction 52.8 % -> 62.5 %, and the sleeve's own worst path
    # drawdown -5.51 R -> -9.51 R. Per-trade Sharpe still improves, 0.3276 -> 0.3653. The worst-case
    # SINGLE-TRADE loss is unchanged at -1.00 R in both arms, because the scale-out only arms after
    # +2R is reached -- so this buys nothing at the daily-loss or max-DD wall either way.
    "energy_agri":       dict(policy="time_stop"),
    # Runtime-executable candidate-book v2: fixed-target, capless trailing, and targetless time-stop
    # candidates are represented by their native exit semantics. `broker_take_profit_mode="none"` means the
    # broker request carries no TP; the book-owned runtime manages trail/time-stop from ticket-bound state.
    "vol_compression":   dict(policy="time_stop", final_from_intent=True),
    "asian_fade":        dict(policy="trailing_runner",
                              final_target_r=None, broker_take_profit_mode="none"),
    "ny_crypto_momentum": dict(policy="time_stop", final_target_r=None,
                               broker_take_profit_mode="none"),
    "metal_session_reversion": dict(policy="trailing_runner",
                                    final_target_r=None, broker_take_profit_mode="none"),
    "asia_pdl_fade":     dict(policy="time_stop", final_from_intent=True),
    "orb_crypto_london": dict(policy="time_stop", final_from_intent=True),
    "asian_fade_widen": dict(policy="time_stop", final_from_intent=True),
    "ny_crypto_momentum_widen": dict(policy="time_stop", final_target_r=None,
                                     broker_take_profit_mode="none"),
    "orb_crypto_london_widen": dict(policy="time_stop", final_from_intent=True),
    "liq_asia_up_low_metal": dict(policy="time_stop", final_from_intent=True),
    "kz_london_crypto_low": dict(policy="time_stop", final_target_r=None,
                                 broker_take_profit_mode="none"),
    "vss_fxcross_london_up_low": dict(policy="time_stop", final_from_intent=True),
    # Cohort A: H=32, stop 0.75 ATR, target 6.0 ATR. final_from_intent so
    # broker TP is 6.0/0.75 = 8R, not DEFAULT_EXIT_PROFILE's 2R.
    "dsp_climax_flush_to_96low_then_snap": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_london_two_up_into_20high_reverses": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_expanding_up_staircase": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_huge_down_hold_then_spring": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_already_wide_down_bar_second_wave": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_cascade_last_two_not_yet_four": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_close_on_20low_not_a_cascade_then_up": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_wide_down_then_micro_bounce_then_through": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_isolated_spike_high": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_bleed_accept_fresh_20low_second_push": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_walked_high_accepted_through": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_small_bar_sit_on_20high_rejects": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_session_open_already_live": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_climax_onto_20high_then_fade_london": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_climax_onto_20high_then_fade_cashhole": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_expanding_two_bar_run_tokyo": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_high_vol_doji_after_reclaimed_flush_fx": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_weekend_gap_then_bleed_into_20low": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_overnight_box_failed_floor_probe": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_london_bounce_fails_overnight_midpoint": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_first_cash_bar_spike_and_flush": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_two_open_bars_down_then_cascade": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_isolated_flush_to_20low_snap": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_climax_into_high_then_dump": dict(
        policy="time_stop", final_from_intent=True),
    "dsp_climax_2atr_onto_20high_then_fade": dict(
        policy="time_stop", final_from_intent=True),
    "xa_huge_20_extreme": dict(
        policy="time_stop", final_from_intent=True),
    "xa_isolated_opposite": dict(
        policy="time_stop", final_from_intent=True),
    "xa_prior_huge": dict(
        policy="time_stop", final_from_intent=True),
    "xa_climax_spring": dict(
        policy="time_stop", final_from_intent=True),
    "xa_wide_extreme": dict(
        policy="time_stop", final_from_intent=True),
    "xa_second_leg": dict(
        policy="time_stop", final_from_intent=True),
}

MARKET_EXPANSION_TARGET2_SLEEVES: tuple[str, ...] = (
    "mx_aus200_cash_d1_volume_surge_reversal",
    "mx_avausd_d1_donchian_20_breakout",
    "mx_btcusd_d1_donchian_20_breakout",
    "mx_cadjpy_d1_volume_surge_reversal",
    "mx_ethusd_d1_donchian_20_breakout",
    "mx_eu50_cash_d1_volume_surge_reversal",
    "mx_fra40_cash_d1_volume_surge_reversal",
    "mx_ger40_cash_d1_volume_surge_reversal",
    "mx_jp225_cash_d1_volume_surge_reversal",
    "mx_nzdjpy_d1_donchian_20_breakout",
    "mx_spn35_cash_d1_volume_surge_reversal",
    "mx_us100_cash_d1_atr_mean_reversion",
    "mx_us30_cash_d1_volume_surge_reversal",
    "mx_us500_cash_d1_atr_mean_reversion",
)
#: REPAIRED 2026-07-30 (Session AQ, B1404). This block carried `time_stop_bars=96` -- one D1 bar,
#: because 96 is `M15_BARS_PER["D1"]` and not a horizon. Every published economic number for these
#: sleeves is measured at `maxbars=80` D1 bars with no time stop, so the live book was running an
#: exit contract 80x tighter than the one the evidence describes and truncating 72-90 % of the
#: trades. `vol_compression`, four lines above, had the same D1 horizon written correctly all
#: along; the two now use the same expression so they cannot drift apart again.
#: Nothing armed is in this cohort -- the three live sleeves are H4 -- and the repair moves no
#: other sleeve's integer. Pinned by `tests/ultimate_book/test_time_stop_units.py`.
SLEEVE_EXIT_PROFILES.update({
    sleeve: dict(policy="time_stop", final_from_intent=True)
    for sleeve in MARKET_EXPANSION_TARGET2_SLEEVES
})

# --- C4 staged 20260907: Astra V2_ADDED_EXIT_PROFILES (tag exit map; NEW fires after F5 restart) ---
V2_ADDED_EXIT_PROFILES: dict[str, dict] = {
    'dsp_accepted_20low_then_second_flush': dict(policy="time_stop", final_from_intent=True),
    'dsp_cascade_two_down_bars_then_third': dict(policy="time_stop", final_from_intent=True),
    'dsp_climax_onto_20high_then_fade': dict(policy="time_stop", final_from_intent=True),
    'dsp_descending_lows_accepted': dict(policy="time_stop", final_from_intent=True),
    'dsp_first_crack_failed_reclaim': dict(policy="time_stop", final_from_intent=True),
    'dsp_high_vol_doji_after_reclaimed_flush': dict(policy="time_stop", final_from_intent=True),
    'dsp_isolated_20h_spike_then_fade': dict(policy="time_stop", final_from_intent=True),
    'dsp_london_cascade_into_20low_springs': dict(policy="time_stop", final_from_intent=True),
    'dsp_reclaim_then_giveback': dict(policy="time_stop", final_from_intent=True),
    'dsp_rejection_wick_then_through': dict(policy="time_stop", final_from_intent=True),
    'dsp_shakeout_holds_run_lows': dict(policy="time_stop", final_from_intent=True),
    'dsp_small_bar_on_thrust_high': dict(policy="time_stop", final_from_intent=True),
    'dsp_spring_close_on_20low_through_the_box': dict(policy="time_stop", final_from_intent=True),
    'dsp_spring_first_print_of_range_low': dict(policy="time_stop", final_from_intent=True),
    'dsp_take_of_low_already_falling_continues': dict(policy="time_stop", final_from_intent=True),
    'dsp_three_bar_squeeze_into_high': dict(policy="time_stop", final_from_intent=True),
    'dsp_three_fresh_lower_lows': dict(policy="time_stop", final_from_intent=True),
    'dsp_two_bar_thrust_into_20high_continues': dict(policy="time_stop", final_from_intent=True),
    'dsp_volume_ramp_into_unrepaired_low': dict(policy="time_stop", final_from_intent=True),
    'dsp_wide_bar_takes_both_extremes_then_reverse': dict(policy="time_stop", final_from_intent=True),
    'xa_huge_same_way': dict(policy="time_stop", final_from_intent=True),
    'xa_second_rth': dict(policy="time_stop", final_from_intent=True),
    'xa_wave_two_standing': dict(policy="time_stop", final_from_intent=True),
}

# Registry profile for an unlisted sleeve. The target multiple on a live order is the
# System One score for that state. This number is not that decision.
DEFAULT_EXIT_PROFILE: dict = dict(policy="time_stop")


# ---- THE FRONTIER EXIT CONTRACTS, DEFAULT-OFF AND SELECTABLE PER SLEEVE -------------------------
# Session AU (B1550-B1599). Two exit cells in this estate carry a measured economic verdict that the
# live engine could not run, so their published economics described a contract no book could execute
# -- the defect class Session AQ found on the `mx_*` time stop, one layer up. These wire them.
#
#   `mx_btcusd_d1_donchian_20_breakout` @ target_5R   the estate's ONE standing admission
#       (`phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md`; p 0.0011, admits at two of three cost bands on
#       the ratified RECORDED population). Its evidence is the 5R exit; the spec runs 2R.
#   `sub_xvol_pullback` @ target_4R                   AK's frontier winner, +1.157 R/day against
#       as-walked (`phase8/receipts/AK_*`; AD's estate sweep never covered this sleeve's exits).
#       This sleeve is ARMED and trading real money on both accounts at 3R.
#
# WHY AN OVERRIDE AND NOT AN EDIT TO THE DICT ABOVE. `sub_xvol_pullback` is live on two funded
# accounts. Editing its `final_target_r` in place would change armed-money behaviour the moment the
# VPS carried the code -- no ceremony, no owner decision, no flat book. So the frontier value lives
# in a separate, EMPTY-BY-DEFAULT selection: `resolve_exit_profile(sleeve)` with no selection returns
# the committed profile object for every sleeve, asserted byte-identical by
# `tests/ultimate_book/test_frontier_exit_contracts.py`.
#
# WHY PER SLEEVE AND NOT ONE BOOLEAN. The two sleeves are in opposite live states. `mx_btcusd` is not
# in either account's `--tags`, so wiring its 5R exit is inert; `sub_xvol_pullback` is armed, so
# wiring its 4R exit is a live risk change. One boolean would force the ceremony to change armed
# money in order to make the admission's own contract runnable. The selection is therefore a set of
# sleeve names, parsed by `parse_frontier_exits`, which REFUSES an empty string and REFUSES an
# unknown name -- `--tags ""` is falsy and silently means "all BUILT sleeves" (B359), and an all-typo
# `--tags` stands the book down every tick in silence (`registry.py:144`). Both fail-open shapes are
# closed here rather than inherited.
#
# WHAT EACH OVERRIDE IS, AND THE MEASUREMENT THAT SAYS IT IS THE RESEARCH CELL. Both research cells
# are `ExitPolicy(target_dist=k*stop, trail=None, partial=None, maxbars=80 own bars, time_stop=None)`
# (`phase7/receipts/ad_exit_sweep.py:534-539`, `target_mode="fixed_r"`). The live contract they
# resolve to is: broker SL at -1R, broker TP at k*R, no trail, no partial, and a time stop at the
# sleeve's own 80-bar research horizon -- 7680 M15 bars for the D1 sleeve, 1280 for the H4 one, both
# of which fire on the same bar `maxbars` does, at the same close. So the wiring is not an analogue
# of the cell, it IS the cell, and `phase12/receipts/au_exit_contract_wiring.py` proves it by
# replaying the live-resolved profile against AD's own variant over AA's stored intents and requiring
# R-identity trade by trade.
FRONTIER_EXIT_OVERRIDES: dict[str, dict] = {
    "mx_btcusd_d1_donchian_20_breakout": dict(
        # The spec sets `final_from_intent=True`, so the broker TP tracks the GENERATOR's ratio
        # (`market_expansion_d1.py:225 target_dist=TARGET_R*risk`, measured at exactly 2.0 on all
        # 318 walked trades). A fixed 5R must therefore turn that off, or the override would be
        # silently ignored on every intent that carries a target.
        final_from_intent=False,
        frontier_cell="target_5R",
        frontier_evidence="phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md",
    ),
    "sub_xvol_pullback": dict(
        final_from_intent=False,
        frontier_cell="target_4R",
        frontier_evidence="phase8/receipts/AK_EXIT_FRONTIER_V2.json",
    ),
    # Session CM (B2700-B2749): AD's measured-best stop-width cell, re-read through the
    # production crypto generator on CJ's true-UTC TRAIN/VAL lane. FTMO RECORDED improves by
    # +0.2527 R/day at the mid band, the latest fold remains +0.0355 better, and 4/5 paired
    # folds improve at every cost band. redacted_account's latest fold is negative, so the ceremony
    # selects this name on FTMO only. `build_book_trade_params` applies the multiplier to the
    # resolved risk distance before BOTH broker SL and TP are built; fixed 4R therefore scales
    # the target price with the wider stop, exactly matching AD's `stop_1.5x_tgtscale` cell.
    "crypto": dict(
        frontier_cell="stop_1p5x_target_scale",
        frontier_evidence="phase17/receipts/CM_REVERIFY_V1.json",
    ),
}

# ---- THE DELIBERATE SHORT HORIZONS (Session AU AU-3, B1570) --------------------------------------
# AQ repaired the `mx_*` D1 cohort's `time_stop_bars` from 96 to 7680 -- 96 was `M15_BARS_PER["D1"]`,
# the conversion RATIO written into the field that wants the converted value -- and then measured that
# on FIVE of the ten generating sleeves the accidental one-bar stop was BETTER than the 80-bar research
# horizon. Its own prescription: *"for those five the follow-up is to declare a short horizon
# DELIBERATELY on the evidence rather than inherit one from a bug."*
#
# `phase12/receipts/au_d1_horizons.py` re-gated the horizon ladder {1,2,3,5,10,20,40,80} own D1 bars at
# the RATIFIED rule (RECORDED, `B_balanced` alpha 0.10, band column alongside a flat control, family V5)
# -- AD's existing grid could not answer it, being at the flat band on ALL_ERAS where `mx_btcusd`'s
# delta reads 1.9x smaller. Six sleeves cleared all four pre-declared prescription clauses (best cell
# shorter than 80; better at EVERY cost band; positive R/day; majority-positive chronological folds).
#
# READ THE NUMBER AND THEN READ THE NEXT PARAGRAPH. For four of them the declared value is
# `time_stop_m15(1, "D1") == 96` -- the same integer AQ removed. That is not a revert. AQ's repair was
# a UNIT repair and it was right: a field whose unit is M15 printed bars cannot hold the M15-per-D1
# ratio and mean anything. What changes here is that 96 stops being an accident that nobody could
# defend and becomes `time_stop_m15(1, "D1")`, with a gated measurement behind it, in a map whose
# default is OFF.
#
# AND WHAT THESE ARE NOT. Every one of the eleven cells in the ladder REJECTS at the ratified rule, and
# the min-p over the ladder is what the global null returns 22-92 % of the time (`p_min_over_grid` vs
# `expected_min_p_under_global_null` in the artifact). So these are CONTRACT DECLARATIONS -- they make
# the spec describe the evidence -- and NOT admissions, NOT edges, and NOT a recommendation to arm.
# At h=1 the horizon is also the dominant exit (77-90 % of trades), so the sleeve is a one-day-hold
# contract rather than a geometry that resolves; that is a property to know before arming, not a defect.
# Arming any of them is Borhen's, and nothing in this cohort is armed today.
FRONTIER_EXIT_OVERRIDES.update({
    "mx_us100_cash_d1_atr_mean_reversion": dict(
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_us500_cash_d1_atr_mean_reversion": dict(
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_ger40_cash_d1_volume_surge_reversal": dict(
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_us30_cash_d1_volume_surge_reversal": dict(
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_ethusd_d1_donchian_20_breakout": dict(
        frontier_cell="time_stop_10_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    # The CONTROL sleeve of the ladder, and it is here because the rule prescribed it rather than
    # because the cohort did. `vol_compression`'s 80-bar horizon was declared CORRECTLY all along
    # (it is the sleeve whose right answer proved 96 was wrong), and its ladder is monotone RISING to
    # h=20 with h=1 its worst cell -- the opposite shape to the mis-scaled cohort, which is what makes
    # it a working control. Prescribing 20 for it is an optimisation on a REJECT cell, not a repair.
    "vol_compression": dict(
        frontier_cell="time_stop_20_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
})

# ---- THE SCALE-OUT, AS A PRICED OPTION (Session BD, B2094) ---------------------------------------
# `energy_agri` is ARMED on both funded accounts and its live exit is a `partial_be_runner`: half off
# at +2R, stop to breakeven, the rest to 4R or the horizon. Three instruments now say that scale-out
# COSTS money on this sleeve, and the third is the only one gated at the ratified rule:
#
#   AD §6.2   -0.308  R/day  n=67   "a question, not a recommendation"
#   AU §2     +0.2302 R/day         restamp error at every band, on armed money
#   BD        +0.2302 R/day         GATED: RECORDED, B_balanced alpha 0.10, family V5, four bands
#                                   (`phase13/receipts/BD_PARTIAL_EXIT_V1.json`)
#
# BD reproduces AU's figure to four decimals through an independent driver: at the mid band the live
# contract earns +0.1763 R/day and the plain one +0.4065, and the delta is IDENTICAL at all four
# bands because a cost band shifts both arms equally -- so "at every band" is a structural property
# of the comparison, not four independent confirmations. Read it that way.
#
# AND IT IS NOT AN ADMISSION. Both arms REJECT at all four bands. `p_raw` moves 0.321 -> 0.206
# against an alpha of 0.10, n is 64 trades, and the chronological fold table decays hard under BOTH
# contracts -- LIVE [+0.533, +0.282, -0.287], PLAIN [+0.933, +0.351, -0.064]. The most recent fold is
# NEGATIVE either way, and most of the improvement sits in the earliest. `maxbars_share` is 0.0 on
# both, so this is a contract difference and not a harness-ceiling artifact. `p_min` over the two
# arms is 0.2005 against an expected 0.3608 under the global null.
#
# THE CONTROL IS WHY THIS IS AN OPTION AND NOT A POLICY. All four `partial_be_runner` sleeves rode
# the same grid and the sign runs BOTH ways -- `energy_agri` +0.2302 and `metals_softband` +0.0372
# favour plain; `metals_core` -0.0777 and `metals_ob_micro` -0.0399 favour the scale-out. A harness
# that preferred plain everywhere would be measuring itself. Only `energy_agri` is wired, because it
# is the only one of the four that is armed and the only one with a second and third instrument.
#
# THE DIRECTION OF THIS ENTRY WAS INVERTED 2026-08-11 (owner-authorized, swarm-2 lane B7), and BD's
# recommendation above -- "NOT to arm it on this evidence" -- was overruled by the owner on a fourth
# instrument. The plain contract is now the COMMITTED default (see `SLEEVE_EXIT_PROFILES` above), so
# a `plain_exit_no_partial` override would resolve to exactly the committed dict: an operator could
# select it, see the banner, and change nothing. That silent no-op is the failure shape this whole
# module exists to refuse, so the override now points the OTHER way and restores the scale-out.
#
# What that buys, and it is the reason it is not simply deleted: it makes the previous live contract
# reachable WITHOUT A CODE CARRY. Rolling this decision back is then a launcher argument and a
# supervisor restart, not a file copied onto a funded host. Deleting the entry instead would make
# `--frontier-exits energy_agri` raise at launch (`parse_frontier_exits` refuses unknown names) --
# fail-closed, but it would take a book with it, and it would leave no reverse gear.
#
# Read the residual risk honestly: a STALE `--frontier-exits energy_agri` left in a host launcher now
# RESTORES the scale-out instead of being inert. The direction is safe (it can only reproduce the
# contract the book ran until today, never an unmeasured one) and the carry runbook verifies the
# argument is absent before and after -- the committed launcher carries `frontier=$null` on both
# accounts and the host's own `--frontier-exits` was removed entirely on 2026-08-05.
FRONTIER_EXIT_OVERRIDES.update({
    "energy_agri": dict(
        policy="partial_be_runner",
        # 2.0, not `final_target_r`: this is the scale-out trigger the sleeve ran live from arming
        # until 2026-08-11. The resolved profile must equal the pre-change committed dict exactly,
        # which `tests/ultimate_book/test_b7_live_contract_changes.py` asserts by value.
        frontier_cell="partial_be_runner_restore",
        frontier_evidence="phase13/receipts/BD_PARTIAL_EXIT_V1.json",
    ),
})

#: The declared vocabulary of frontier cells. A cell name outside this set is a typo or an undeclared
#: kind of override, and `tests/ultimate_book/test_frontier_exit_contracts.py` refuses it.
#: `plain_exit_` was added by Session BD for a cell that changes neither the target nor the horizon
#: but removes a management leg. `stop_` was added by Session CM for a measured stop-width cell;
#: unlike a target-only frontier it must rebuild both broker SL and TP from the scaled risk unit.
#: `partial_` was added by lane B7 when the plain exit became `energy_agri`'s committed default and
#: the override inverted to restore the scale-out -- a cell that ADDS a management leg back. It is
#: kept as its own kind rather than folded into `plain_exit_` because the two are opposites and a
#: reader who skims the cell name must not read one as the other.
FRONTIER_CELL_KINDS: tuple[str, ...] = ("target_", "time_stop_", "plain_exit_", "stop_", "partial_")

#: The keys `FRONTIER_EXIT_OVERRIDES` may carry that are PROVENANCE rather than contract. They ride
#: in the placement's `source_event_details` so a ledger row says which contract placed it, and they
#: are stripped before the profile reaches any geometry builder.
_FRONTIER_PROVENANCE_KEYS: tuple[str, ...] = ("frontier_cell", "frontier_evidence")


class FrontierExitSelectionError(ValueError):
    """A frontier-exit selection that cannot be honoured. Raised at launch, never at a tick.

    Fail-closed deliberately: the two shapes this forbids are the two the estate has already
    measured on `--tags`. An empty selection that means "all" is fail-OPEN (B359); an unknown sleeve
    name that is silently dropped leaves the operator believing a contract is armed when it is not.
    """


def parse_frontier_exits(raw) -> tuple[str, ...]:
    """`"a,b"` / `("a",)` / None -> the validated sleeve tuple. Raises on empty or unknown."""
    if raw is None:
        return ()
    items = [s.strip() for s in raw.split(",")] if isinstance(raw, str) else [str(s).strip() for s in raw]
    named = [s for s in items if s]
    if not named:
        raise FrontierExitSelectionError(
            "--frontier-exits was given but names no sleeve. An empty selection is refused rather "
            "than read as 'all': the same shape on --tags means 'every BUILT sleeve' and is the "
            f"fail-open the book already carries. Known frontier sleeves: "
            f"{sorted(FRONTIER_EXIT_OVERRIDES)}"
        )
    unknown = [s for s in named if s not in FRONTIER_EXIT_OVERRIDES]
    if unknown:
        raise FrontierExitSelectionError(
            f"no frontier exit contract is wired for {unknown!r}. A typo must not resolve to "
            f"'no override' in silence -- that is an operator believing a contract is armed when "
            f"the book is running the committed one. Wired: {sorted(FRONTIER_EXIT_OVERRIDES)}"
        )
    return tuple(dict.fromkeys(named))


def describe_frontier_contract(sleeve) -> str:
    """One human clause naming WHAT a wired frontier override changes, for the launch banner.

    B1852. `run_book.py`'s banner rendered `float(_o["final_target_r"])` unconditionally, and SIX of
    the eight wired sleeves are `time_stop_*` cells that carry no such key -- so
    `--frontier-exits vol_compression` (or any of the five `mx_*` short horizons) raised
    `KeyError('final_target_r')` at LAUNCH, after `parse_frontier_exits` had already accepted the
    name. That is the fail shape the whole module exists to avoid, one layer further out: the worker
    dies before `BookLauncher`, the supervisor restarts a missing book forever, and
    `manage_open_positions` never runs on either namespace. The two cells that DO carry the key are
    `mx_btcusd` and `sub_xvol_pullback`, which is why it survived AU's 43 tests.

    Rendering lives here rather than in `run_book.py` so it is testable without a broker and so a
    NEW kind of override cannot reintroduce the crash silently: an override carrying neither key
    renders `"contract override"` and `test_frontier_exit_contracts.py` asserts every wired sleeve
    renders a non-empty clause naming at least one contract key.
    """
    over = FRONTIER_EXIT_OVERRIDES.get(sleeve)
    if not over:
        return "no wired override"
    parts = []
    tgt = over.get("final_target_r")
    if tgt is not None:
        parts.append(f"broker TP {float(tgt):.1f}R")
    bars = over.get("time_stop_bars")
    if bars is not None:
        parts.append(f"time stop {int(bars)} printed M15 bars")
    # The third override kind (Session BD): a POLICY change that removes a management leg
    # rather than moving a target or a horizon. Render it by name, or B1852's fallback
    # ("contract override") reads as a banner that names nothing — the exact shape the
    # launch-banner test refuses.
    pol = over.get("policy")
    if pol is not None:
        parts.append(f"exit policy {pol}")
    stop_mult = over.get("stop_distance_multiplier")
    if stop_mult is not None:
        parts.append(f"stop distance x{float(stop_mult):g} with target scaled")
    if "partial_close_ratio" in over and over.get("partial_close_ratio") is None:
        parts.append("scale-out leg removed")
    return ", ".join(parts) if parts else "contract override"


def resolve_exit_profile(sleeve, *, frontier_exits=(), contract_version=None, profile_namespace=None, **_kwargs) -> dict:
    """Exit profile for sleeve. C4 staged 20260907: V2 overlay for NEW F5 fires; frontier semantics preserved.

    With empty frontier selection returns the committed profile object itself (not a copy), matching
    pre-C4 behavior. V2 tags (e.g. dsp_descending_lows_accepted) resolve from V2_ADDED_EXIT_PROFILES
    with final_from_intent / time_stop_bars=32 instead of DEFAULT 2.0R/1280.
    """
    use_v2 = False
    if contract_version == "f5_gate_v2":
        use_v2 = True
    if profile_namespace == "operator":
        use_v2 = True
    if contract_version is None and profile_namespace is None:
        use_v2 = True

    if use_v2:
        v2_prof = V2_ADDED_EXIT_PROFILES.get(sleeve)
        if v2_prof is not None:
            if not frontier_exits or sleeve not in frontier_exits:
                return v2_prof
            over = FRONTIER_EXIT_OVERRIDES.get(sleeve)
            if over is None:
                return v2_prof
            return {**v2_prof, **over}

    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if not frontier_exits or sleeve not in frontier_exits:
        return prof
    over = FRONTIER_EXIT_OVERRIDES.get(sleeve)
    if over is None:                      # unreachable via parse_frontier_exits; belt and braces
        return prof
    return {**prof, **over}


def frontier_provenance(prof) -> dict:
    """The provenance keys a frontier-overridden profile carries, `{}` for a committed one."""
    return {k: prof[k] for k in _FRONTIER_PROVENANCE_KEYS if isinstance(prof, Mapping) and k in prof}


_MODEL = "jev-1.13.0"
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_LIMIT_KEY_PARTS = ("floor", "baseline", "pass_line")


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _banned_limit_text(value: str) -> bool:
    """A printed floor is not a reason to drop a fact or a score."""
    return False


def _limit_key(name: str) -> bool:
    low = name.strip().lower()
    return any(part in low for part in _LIMIT_KEY_PARTS)


def _scrub_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Facts for one ask. A floor and a baseline are not on the question."""
    out: dict[str, Any] = {}
    for key, value in facts.items():
        name = str(key)
        if _limit_key(name):
            continue
        if isinstance(value, str) and _banned_limit_text(value):
            continue
        number = _finite(value)
        if number is not None and _banned_limit_text(format(number, ".10g")):
            continue
        if number is not None:
            out[name] = number
            continue
        if isinstance(value, (str, bool)) or value is None:
            out[name] = value
    out["model"] = _MODEL
    return out


def _score_questions(specs: tuple[tuple[str, str], ...]) -> dict[str, dict[str, Any]]:
    pack: dict[str, dict[str, Any]] = {}
    for qid, instructions in specs:
        text = str(instructions).strip()
        block: dict[str, Any] = {}
        try:
            from src.judgment.jev_questions import parameter_question

            built = parameter_question(qid, text)
            raw = built.get(qid) if isinstance(built, dict) else None
            if isinstance(raw, dict):
                block = dict(raw)
        except Exception:
            block = {}
        for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
            block.pop(key, None)
        block["type"] = "score"
        block["instructions"] = text
        criteria = block.get("criteria")
        if isinstance(criteria, list):
            kept = [
                str(item)
                for item in criteria
                if not _limit_key(str(item)) and not _banned_limit_text(str(item))
            ]
            if kept:
                block["criteria"] = kept
            else:
                block.pop("criteria", None)
        pack[qid] = block
    return pack


def _tied(block: Mapping[str, Any], unique_highest: Any) -> bool:
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return False
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _finite(value)
        if number is None:
            continue
        numeric[str(key)] = number
    if len(numeric) < 2:
        return False
    try:
        picked = unique_highest(numeric, tuple(numeric))
    except TypeError:
        picked = unique_highest(numeric)
    return picked is None


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from src.judgment.jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]


def _remember(qid: str, value: float | None, state: Mapping[str, Any], error: str | None) -> None:
    try:
        from src.judgment.jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        _LOCAL_OUTCOMES.append({
            "spot": qid,
            "value": value,
            "error": error,
        })


def _order_parameter_scores(
    facts: Mapping[str, Any],
    specs: tuple[tuple[str, str], ...],
) -> dict[str, float | None]:
    """Scores for this state. A miss stays None. Nothing here writes a constant back."""
    unset = {qid: None for qid, _instructions in specs}
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import returned_number, unique_highest
    except Exception:
        return unset
    state = _scrub_facts(facts)
    try:
        questions = _score_questions(specs)
    except Exception:
        return unset
    _attach_priors(state, questions)
    error: str | None = None
    try:
        receipt = evaluate(state, questions=questions, merge_sleeve=False, model=_MODEL)
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the packet
        receipt = {}
        error = type(exc).__name__
    if not isinstance(receipt, dict):
        receipt = {}
        error = error or "evaluate_not_a_dict"
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    if error is None:
        raw_error = receipt.get("error") or receipt.get("skipped")
        error = str(raw_error) if raw_error not in (None, "") else None
    if not answers and error is None:
        error = "empty"
    out: dict[str, float | None] = {}
    for qid, _instructions in specs:
        value: float | None = None
        spot_error = error
        block = answers.get(qid) if isinstance(answers, dict) else None
        if error is None and isinstance(block, (int, float)) and not isinstance(block, bool):
            value = _finite(block)
        elif error is None and isinstance(block, dict) and not block.get("error") and not _tied(block, unique_highest):
            try:
                value = _finite(returned_number(block))
            except Exception:
                value = None
            if value is None:
                value = _finite(block.get("score"))
                if value is None:
                    value = _finite(block.get("value"))
        if value is None and spot_error is None:
            spot_error = "tie" if isinstance(block, dict) and _tied(block, unique_highest) else "score_missing"
        out[qid] = value
        _remember(qid, value, state, None if value is not None else spot_error)
    return out


_TARGET_MULTIPLE_Q = (
    "target_multiple",
    "The score you return is the target multiple for this live order. "
    "It may sit between the levels. "
    "An empty score, a tie, or an error leaves the target multiple unset. "
    "A floor and a baseline are not this question. Do not send.",
)
_RISK_PERCENT_Q = (
    "risk_percent",
    "The score you return is the risk percent for this live order. "
    "It may sit between the levels. "
    "An empty score, a tie, or an error leaves the risk percent unset. "
    "A floor and a baseline are not this question. Do not send.",
)
_ENTRY_PRICE_Q = (
    "entry_price",
    "The score you return is the limit price for this entry. "
    "The entry is a limit order. Bid and ask are facts. "
    "The score may sit between the levels. "
    "An empty score, a tie, or an error leaves the price unset and does not cross the spread. "
    "A floor and a baseline are not this question. Do not send.",
)
_STOP_DISTANCE_Q = (
    "stop_distance_multiplier",
    "The score you return is the stop-distance multiple for this order. "
    "It may sit between the levels. An empty score leaves the distance unscaled. Do not send.",
)
_TRIGGER_R_Q = (
    "trigger_r",
    "The score you return is the trigger multiple for this order. "
    "It may sit between the levels. An empty score leaves the trigger unset. Do not send.",
)
_PARTIAL_CLOSE_Q = (
    "partial_close_ratio",
    "The score you return is the partial-close fraction for this order. "
    "It may sit between the levels. An empty score leaves the fraction unset. Do not send.",
)
_TRAIL_GAP_Q = (
    "trail_gap_r",
    "The score you return is the trail gap for this order. "
    "It may sit between the levels. An empty score leaves the gap unset. Do not send.",
)
_PULLBACK_Q = (
    "pullback_r",
    "The score you return is the pullback for this order. "
    "It may sit between the levels. An empty score leaves the pullback unset. Do not send.",
)
_TIME_STOP_BARS_Q = (
    "time_stop_bars",
    "The score you return is the time-stop bar count for this order. "
    "It may sit between the levels. An empty score leaves the count unset. Do not send.",
)
_DAILY_LOSS_Q = (
    "daily_loss_limit_pct",
    "The score you return is the daily loss percent for this account state. "
    "It may sit between the levels. An empty score leaves the percent unset. "
    "A floor and a baseline are not this question. Do not send.",
)
_OVERALL_LOSS_Q = (
    "overall_loss_limit_pct",
    "The score you return is the overall loss percent for this account state. "
    "It may sit between the levels. An empty score leaves the percent unset. "
    "A floor and a baseline are not this question. Do not send.",
)
_INITIAL_BASELINE_Q = (
    "initial_equity_or_balance_baseline",
    "The score you return is the initial balance baseline for this account state. "
    "It may sit between the levels. An empty score leaves the baseline unset. "
    "A floor and a baseline number planted in code is not this question. Do not send.",
)


def _spine_score(facts: Mapping[str, Any], role: str, instructions: str) -> float | None:
    """One spine score. None does not restore a profile constant."""
    try:
        from src.judgment.nineteen import score

        return score(dict(facts), question_id=role, instructions=instructions)
    except Exception:
        return None


def _proposed_target(prof: Mapping[str, Any], native_target: Any = None, native_stop: Any = None) -> float | None:
    """Intent ratio as a fact. A profile constant is not the multiple."""
    stop = _finite(native_stop)
    target = _finite(native_target)
    if (
        prof.get("final_from_intent")
        and target is not None
        and stop is not None
        and stop > 0
        and target > 0
    ):
        return target / stop
    return None


def native_policy_instrumentation(sleeve, *, frontier_exits=()) -> dict:
    """The per-sleeve NATIVE exit-policy fields (the gtos_vnext_dynamic_* subset of a book trade_params),
    derived from SLEEVE_EXIT_PROFILES. Used to rehydrate an ADOPTED position whose on-disk trade record is
    missing (adopt-missing-record): the sleeve identity (the W7:{sleeve} broker comment) is enough to
    restore the validated time-stop / scale-out / target lifecycle.

    The target multiple on this rehydrate is the System One score for this state.
    An empty answer, a tie, or an error leaves it unset.

    `frontier_exits` MUST be the same selection the placement ran under, and the caller cannot know
    that from this path -- by definition there is no trade record to read it off. So a position placed
    at the committed 3R and adopted-without-record while the 4R contract is selected is rehydrated at
    4R, and with `live_broker_authority` true that MOVES its broker TP. Narrow (adopt-missing-record
    only; every position with a record is rehydrated from the record's own placement values) and
    named rather than silent: the operating rule is FLIP THE SELECTION AT A FLAT BOOK, which is the
    same rule arming a `--tags` change already needs (B365)."""
    prof = resolve_exit_profile(sleeve, frontier_exits=frontier_exits)
    policy = str(prof["policy"])
    no_broker_tp = str(prof.get("broker_take_profit_mode", "final_target")).strip().lower() == "none"
    facts: dict[str, Any] = {
        "role": "native_policy",
        "sleeve": None if sleeve is None else str(sleeve),
        "policy": policy,
        "no_broker_take_profit": no_broker_tp,
    }
    proposed = _proposed_target(prof)
    if proposed is not None:
        facts["proposed_target_multiple"] = proposed
    final_target_r = _order_parameter_scores(facts, (_TARGET_MULTIPLE_Q,))["target_multiple"]
    trigger_r = _spine_score(
        facts,
        "trigger_r",
        "The score you return is the trigger multiple for this sleeve. "
        "It may sit between the levels. An empty score leaves the trigger unset. Do not send.",
    )
    partial_close_ratio = _spine_score(
        facts,
        "partial_close_ratio",
        "The score you return is the partial-close fraction for this sleeve. "
        "It may sit between the levels. An empty score leaves the fraction unset. Do not send.",
    )
    trail_gap_r = _spine_score(
        facts,
        "trail_gap_r",
        "The score you return is the trail gap for this sleeve. "
        "It may sit between the levels. An empty score leaves the gap unset. Do not send.",
    )
    pullback_r = _spine_score(
        facts,
        "pullback_r",
        "The score you return is the pullback for this sleeve. "
        "It may sit between the levels. An empty score leaves the pullback unset. Do not send.",
    )
    time_stop_bars = _spine_score(
        facts,
        "time_stop_bars",
        "The score you return is the time-stop bar count for this sleeve. "
        "It may sit between the levels. An empty score leaves the count unset. Do not send.",
    )
    return {
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_selected": policy,
        "gtos_vnext_execution_policy_id": f"emv4_{policy}_v1",
        "gtos_vnext_dynamic_be_trigger_r": trigger_r,
        "gtos_vnext_dynamic_final_target_r": final_target_r,
        "gtos_vnext_dynamic_broker_take_profit_mode": "none" if no_broker_tp else "final_target",
        "gtos_vnext_dynamic_no_broker_take_profit": no_broker_tp,
        "gtos_vnext_dynamic_momentum_pullback_r": pullback_r,
        "gtos_vnext_dynamic_partial_close_ratio": partial_close_ratio,
        "gtos_vnext_dynamic_trail_gap_r": trail_gap_r,
        "gtos_vnext_dynamic_time_stop_bars": time_stop_bars,
        "gtos_vnext_book_native_exit_management": True,
    }

FTMO_INITIAL_BALANCE = 100000.0                       # agent_config.yaml / profile
FTMO_DAILY_LOSS_PCT = 5.0                             # agent_config.yaml / profile
FTMO_OVERALL_LOSS_PCT = 10.0                          # agent_config.yaml / profile
SOURCE_FILE = "shadow_logs/gtos_vnext_runtime_decisions.jsonl"


def _sha(obj: Any) -> str:
    return _hashlib.sha256(
        _json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _g(geometry: Any, key: str, default: Any = None) -> Any:
    v = geometry.get(key, default) if isinstance(geometry, Mapping) else getattr(geometry, key, default)
    return default if v in (None, "") else v


def build_prop_firm_headroom_snapshot(account_state, *, config=None, now_utc=None,
                                      account_namespace=None) -> dict:
    """Broker-real PropFirmHeadroomSnapshotV4 from a LIVE same-tick account read.

    `account_state` MUST carry the live broker reads:
        current_equity (or equity/account_equity), balance, account_login (login, hash-only),
        day_start_equity_or_balance_baseline (post-FTMO-reset equity), daily_reset_window_id.
    The prop-firm rule constants (initial 100000, daily 5%, overall 10%) are injected when account_state
    omits them (identical for FTMO + FN 100k challenges). account_namespace MUST be passed for the
    correct account so a redacted_account snapshot is NOT mis-stamped with the FTMO namespace (provenance);
    defaults to the FTMO namespace only for back-compat callers. captured_at_utc is stamped NOW at build
    time, so this MUST be built in the same decision tick as the order (<=900s rule).
    """
    facts = dict(account_state)
    facts.setdefault("account_namespace", account_namespace or PROFILE_NAMESPACE)
    if str(facts.get("account_namespace") or "") != "operator":
        facts.setdefault("initial_equity_or_balance_baseline", FTMO_INITIAL_BALANCE)
        facts.setdefault("daily_loss_limit_pct", FTMO_DAILY_LOSS_PCT)
        facts.setdefault("overall_loss_limit_pct", FTMO_OVERALL_LOSS_PCT)
    return build_prop_firm_headroom_snapshot_v4_from_account_state(
        facts, config=config, now_utc=now_utc
    )


def build_book_trade_params(sized_unit, intent, geometry, account_state, *, profile_namespace,
                            frontier_exits=()) -> dict:
    """Assemble the FULL V4 trade_params for one sized W7 book unit (per-sleeve native exit policy).

    sized_unit : SizedUnit. Its risk fraction is a fact on the ask. The risk percent
                 on the order is the System One score for this state.
    intent     : TradeIntent(symbol, direction:int +1/-1, decision_day, stop_dist:PRICE, sleeve,
                 target_dist). The sleeve selects its native exit profile (SLEEVE_EXIT_PROFILES).
                 The target multiple on the order is the score for this state.
    geometry   : Mapping/obj resolved at decision tick; must provide entry_price; may provide
                 stop_loss / risk_distance (else derived from intent). take_profit_1 is the entry
                 plus that returned multiple times the risk distance. A missing score leaves it unset.
    account_state : live broker reads for the prop-firm headroom snapshot (see above).
    frontier_exits : the validated frontier-exit sleeve selection (see FRONTIER_EXIT_OVERRIDES).
                 Empty by default. The target multiple and the risk percent are still the scores.
    """
    symbol = str(intent.symbol)
    direction = "LONG" if int(intent.direction) > 0 else "SHORT"
    sign = 1.0 if direction == "LONG" else -1.0
    challenge = str(profile_namespace) == "operator"
    raw_entry = _g(geometry, "entry_price")
    entry_unset = bool(_g(geometry, "entry_unset", False)) or raw_entry in (None, "")
    if challenge and entry_unset:
        entry_price = None
    else:
        entry_price = float(raw_entry)
    if challenge:
        try:
            base_risk_distance = float(_g(geometry, "risk_distance", intent.stop_dist))
        except (TypeError, ValueError):
            base_risk_distance = None
    else:
        base_risk_distance = float(_g(geometry, "risk_distance", intent.stop_dist))

    # ---- per-sleeve native exit profile (replaces the forced momentum_exhaustion 2R) ----
    prof = resolve_exit_profile(getattr(intent, "sleeve", None), frontier_exits=frontier_exits)
    policy = str(prof["policy"])
    execution_policy_id = f"emv4_{policy}_v1"
    native_target = getattr(intent, "target_dist", None)
    native_stop = getattr(intent, "stop_dist", None)
    broker_take_profit_mode = str(prof.get("broker_take_profit_mode", "final_target")).strip().lower()
    no_broker_take_profit = broker_take_profit_mode == "none"
    order_facts: dict[str, Any] = {
        "role": "book_trade_params",
        "sleeve": None if getattr(intent, "sleeve", None) is None else str(intent.sleeve),
        "symbol": symbol,
        "direction": direction,
        "policy": policy,
        "no_broker_take_profit": no_broker_take_profit,
    }
    proposed_target = _proposed_target(prof, native_target, native_stop)
    if proposed_target is not None:
        order_facts["proposed_target_multiple"] = proposed_target
    proposed_risk = _finite(getattr(sized_unit, "risk_pct_per_trade", None))
    if proposed_risk is not None:
        order_facts["proposed_risk_percent"] = proposed_risk * 100.0
    if challenge and isinstance(account_state, Mapping):
        for fact_key, fact_value in (
            ("bid", _finite(_g(geometry, "bid"))),
            ("ask", _finite(_g(geometry, "ask"))),
            ("balance", _finite(account_state.get("balance"))),
            ("equity", _finite(account_state.get("current_equity"))),
        ):
            if fact_value is not None:
                order_facts[fact_key] = fact_value
    specs = [_TARGET_MULTIPLE_Q, _RISK_PERCENT_Q]
    if challenge:
        specs.extend((
            _STOP_DISTANCE_Q,
            _TRIGGER_R_Q,
            _PARTIAL_CLOSE_Q,
            _TRAIL_GAP_Q,
            _PULLBACK_Q,
            _TIME_STOP_BARS_Q,
            _DAILY_LOSS_Q,
            _OVERALL_LOSS_Q,
            _INITIAL_BASELINE_Q,
        ))
        if entry_price is None:
            specs.append(_ENTRY_PRICE_Q)
    scores = _order_parameter_scores(order_facts, tuple(specs))
    final_target_r = scores["target_multiple"]
    risk_pct = scores["risk_percent"]
    if challenge and entry_price is None:
        hopped_entry = scores.get("entry_price")
        if (
            isinstance(hopped_entry, (int, float))
            and not isinstance(hopped_entry, bool)
            and hopped_entry > 0
        ):
            entry_price = float(hopped_entry)
    if challenge:
        stop_distance_multiplier = scores.get("stop_distance_multiplier")
        trigger_r = scores.get("trigger_r")
        partial_close_ratio = scores.get("partial_close_ratio")
        trail_gap_r = scores.get("trail_gap_r")
        pullback_r = scores.get("pullback_r")
        time_stop_bars = scores.get("time_stop_bars")
    else:
        stop_distance_multiplier = _spine_score(
            order_facts,
            "stop_distance_multiplier",
            _STOP_DISTANCE_Q[1],
        )
        trigger_r = _spine_score(order_facts, "trigger_r", _TRIGGER_R_Q[1])
        partial_close_ratio = _spine_score(
            order_facts,
            "partial_close_ratio",
            _PARTIAL_CLOSE_Q[1],
        )
        trail_gap_r = _spine_score(order_facts, "trail_gap_r", _TRAIL_GAP_Q[1])
        pullback_r = _spine_score(order_facts, "pullback_r", _PULLBACK_Q[1])
        time_stop_bars = _spine_score(order_facts, "time_stop_bars", _TIME_STOP_BARS_Q[1])
    if (
        stop_distance_multiplier is not None
        and stop_distance_multiplier > 0
        and entry_price is not None
        and base_risk_distance is not None
    ):
        risk_distance = base_risk_distance * float(stop_distance_multiplier)
        stop_loss = entry_price - sign * risk_distance
    elif entry_price is not None and base_risk_distance is not None:
        risk_distance = base_risk_distance
        stop_loss = float(_g(geometry, "stop_loss", entry_price - sign * risk_distance))
    else:
        risk_distance = base_risk_distance
        stop_loss = _g(geometry, "stop_loss", None)
    if no_broker_take_profit:
        take_profit_1 = 0.0
    elif final_target_r is None or entry_price is None or risk_distance is None:
        take_profit_1 = None
    else:
        take_profit_1 = entry_price + sign * float(final_target_r) * risk_distance

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    decision_day = getattr(intent, "decision_day", None) or now[:10]
    cluster = str(getattr(sized_unit, "cluster", "book"))
    candidate_id = f"W7_BOOK::{cluster}::{symbol}::{decision_day}::{direction}::{intent.sleeve}"
    cell_id = f"{cluster}::{policy}::{symbol}"

    source_event_details = {
        "book": "W7", "cluster": cluster, "sleeve": intent.sleeve,
        "sleeve_members": list(getattr(sized_unit, "sleeve_members", ())),
        "symbol": symbol, "direction": direction, "decision_day": decision_day,
        "confidence": getattr(sized_unit, "confidence", None),
        "n_trades": getattr(sized_unit, "n_trades", None),
    }
    # Provenance for a frontier-overridden placement, so a ledger row says WHICH exit contract placed
    # it rather than leaving a reader to infer it from a launcher argument nobody recorded. Added ONLY
    # when an override applied: `source_event_details` is hashed, so an unconditional key would move
    # `gtos_vnext_source_event_hash` on every default placement and break byte-identity.
    _frontier = frontier_provenance(prof)
    if _frontier:
        source_event_details["exit_contract"] = {"kind": "frontier_override", **_frontier}
    source_event_hash = _sha(source_event_details)
    selector_proof_hash = _sha([candidate_id, source_event_hash, cell_id])

    headroom_state = account_state
    if challenge and isinstance(account_state, Mapping):
        headroom_state = dict(account_state)
        for key in (
            "daily_loss_limit_pct",
            "overall_loss_limit_pct",
            "initial_equity_or_balance_baseline",
        ):
            value = scores.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                headroom_state[key] = value
    headroom = build_prop_firm_headroom_snapshot(
        headroom_state, account_namespace=profile_namespace
    )

    selector_packet = {
        "schema_version": "selector_v4_packet_v1", "action": "trade",
        "reason": "ultimate_book_admitted", "source_status": "predecision_source_allowed",
        "candidate_id": candidate_id,
    }
    selector_packet["packet_hash_sha256"] = _sha(selector_packet)

    scheduler_packet = {
        "schema_version": "scheduler_v4_packet_v1",
        "decision": {
            "selected_candidate_id": candidate_id, "selected_candidate_ids": [candidate_id],
            "selected_action_class": "execute_now", "runtime_effect_now": True,
        },
        "source_boundary": {"missing_runtime_truth": []},
    }
    scheduler_packet["packet_hash_sha256"] = _sha(scheduler_packet)

    # policy-specific management field ONLY (binds exit_management_contract_status for `policy`)
    mgmt_params: dict[str, Any] = {}
    if pullback_r is not None:
        mgmt_params["gtos_vnext_dynamic_momentum_pullback_r"] = pullback_r
    if partial_close_ratio is not None:
        mgmt_params["gtos_vnext_dynamic_partial_close_ratio"] = partial_close_ratio
    if trail_gap_r is not None:
        mgmt_params["gtos_vnext_dynamic_trail_gap_r"] = trail_gap_r
    if time_stop_bars is not None:
        mgmt_params["gtos_vnext_dynamic_time_stop_bars"] = time_stop_bars
    mgmt_params["gtos_vnext_dynamic_broker_take_profit_mode"] = (
        "none" if no_broker_take_profit else "final_target"
    )
    mgmt_params["gtos_vnext_dynamic_no_broker_take_profit"] = no_broker_take_profit

    if entry_price is None or stop_loss is None or risk_distance is None:
        geometry_packet = None
    else:
        geometry_packet = build_target_stop_geometry_v4_contract(
        config=None,
        selected_policy=policy, execution_policy_id=execution_policy_id,
        source_event={
            "source_mode": "ultimate_book_runtime_trade_params",
            "source_path_feature_status": "runtime_asof_ultimate_book_closed_bar_features",
            "source_window_complete": True,
            "selected_policy_ordered_path_status":
                "asof_runtime_path_ordering_not_required_before_order_send",
            "selected_policy_same_bar_ambiguous": False,
        },
        direction=direction, entry_price=entry_price, stop_loss=stop_loss,
        risk_distance=risk_distance,
        trigger_r=trigger_r,
        final_target_r=None if no_broker_take_profit else final_target_r,
        trade_params=mgmt_params,
    )

    return {
        # plain book candidate
        "symbol": symbol, "direction": direction,
        "entry_price": entry_price, "stop_loss": stop_loss, "take_profit_1": take_profit_1,
        "risk_pct_override": risk_pct,
        # identity / timing
        "candidate_id": candidate_id, "decision_time_utc": now, "asof_utc": now,
        # dynamic policy (per-sleeve native exit policy + geometry)
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_selected": policy,
        "gtos_vnext_execution_policy_id": execution_policy_id,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_be_trigger_r": trigger_r,
        "gtos_vnext_dynamic_final_target_r": final_target_r,
        "gtos_vnext_dynamic_broker_take_profit_mode": (
            "none" if no_broker_take_profit else "final_target"
        ),
        "gtos_vnext_dynamic_no_broker_take_profit": no_broker_take_profit,
        "gtos_vnext_dynamic_momentum_pullback_r": pullback_r,
        "gtos_vnext_dynamic_partial_close_ratio": partial_close_ratio,
        "gtos_vnext_dynamic_trail_gap_r": trail_gap_r,
        "gtos_vnext_dynamic_time_stop_bars": time_stop_bars,
        # book-native exit: broker SL plus either broker TP(final_target_r) or targetless/no-TP
        # ticket-bound trail/time-stop owns the exit; generic orchestrator overlays are neutralized.
        "gtos_vnext_book_native_exit_management": True,
        # source completeness
        "source_file": SOURCE_FILE,
        "gtos_vnext_source_event_hash": source_event_hash,
        "gtos_vnext_source_event_details": source_event_details,
        "gtos_vnext_selector_row_id": candidate_id,
        "gtos_vnext_selector_proof_hash": selector_proof_hash,
        # selected-cell risk (authoritative sizing; must == headroom percent unit and <= max_allowed)
        "gtos_vnext_selected_cell_risk_cell_id": cell_id,
        "gtos_vnext_selected_cell_risk_pct": risk_pct,
        "gtos_vnext_selected_cell_risk_selected_policy": policy,
        "gtos_vnext_selected_cell_risk_policy_identity_status": "exact_selected_policy_risk_match",
        # selector v4
        "gtos_vnext_selector_v4_action": "trade",
        "gtos_vnext_selector_v4_packet": selector_packet,
        "gtos_vnext_selector_v4_packet_hash": selector_packet["packet_hash_sha256"],
        # scheduler v4
        "gtos_vnext_scheduler_v4_packet": scheduler_packet,
        "gtos_vnext_scheduler_v4_packet_hash": scheduler_packet["packet_hash_sha256"],
        "gtos_vnext_scheduler_v4_current_candidate_id": candidate_id,
        "gtos_vnext_scheduler_v4_selected_candidate_id": candidate_id,
        "gtos_vnext_scheduler_v4_selected_candidate_ids": [candidate_id],
        "gtos_vnext_scheduler_v4_selected_action_class": "execute_now",
        # geometry (explicit)
        "gtos_vnext_dynamic_target_stop_geometry_v4": geometry_packet,
        # prop-firm headroom (broker-real, same-tick)
        "gtos_vnext_prop_firm_headroom_snapshot_v4": headroom,
        # commission model status — MUST be one of selected_cell_allowed_commission_model_statuses
        # (agent_config.yaml:723-725); the book sizes net-of-real-cost so commission is included in
        # the selected-cell risk. "broker_commission_modeled" is UNAPPROVED -> cost REFUSED -> emv4 block.
        "gtos_vnext_commission_model_status": "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK",
        # same-symbol lifecycle owner
        "gtos_vnext_same_symbol_lifecycle_action": "open_new",
        "gtos_vnext_lifecycle_action": "open_new",
        "gtos_vnext_same_symbol_lifecycle_v4_packet": {
            "action": "open_new", "permitted_order_intent": True,
            "same_symbol_owner": "same_symbol_same_instrument_lifecycle_v4",
        },
    }

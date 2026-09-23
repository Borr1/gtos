"""execution_packets.py — build the FULL V4 trade_params for one sized W7 book unit.

Pure (stdlib + the V4 contract builders). NO MT5 / NO broker / NO order. Produces the dict that
clears all three live fail-closed gates the runtime runs in ExecutionEngine.open_trade:
  1. _vnext_dynamic_policy_support_error  (execution.py:2683-2689 / :1490-1533)
  2. evaluate_execution_manager_v4         (execution.py:2840-2860 / execution_manager_v4.py:617)
  3. _resolve_vnext_production_risk_pct    (execution.py:2804-2813 / :1591-1677)

The pretrade_cost_model is NOT a trade_params key — it is a separate order-send argument the
order router must build from a live tick (execution.py:2833 build_pretrade_cost_packet).
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
M15_BARS_PER: dict[str, int] = {"M15": 1, "H4": 16, "D1": 96}


def time_stop_m15(n_native_bars: int, grid: str) -> int:
    """`n_native_bars` of `grid` expressed in the M15 printed bars the engine counts."""
    try:
        per = M15_BARS_PER[grid]
    except KeyError:  # pragma: no cover - a typo'd grid must not silently under-scale
        raise ValueError(
            f"unknown decision grid {grid!r}; known: {sorted(M15_BARS_PER)}. A time stop "
            f"declared on an unknown grid would be charged in the wrong unit, which is the "
            f"defect this helper exists to make unwriteable."
        ) from None
    n = int(n_native_bars)
    if n < 1:
        raise ValueError(f"n_native_bars must be >= 1, got {n_native_bars!r}")
    return n * per


#: The horizon every sleeve's published economics are measured under: `maxbars=80` bars of the
#: sleeve's own grid (`AA_ESTATE_TRADES.json.gz` -> `maxbars`, and `ExitPolicy.maxbars`'s default).
#: A sleeve whose time stop is meant to be "the research horizon" declares exactly this.
RESEARCH_HORIZON_NATIVE_BARS = 80

# ---- PER-SLEEVE EXIT-PROFILE REGISTRY -----------------------------------------------------------
# Each W7 book sleeve carries its OWN validated native exit policy + geometry instead of a single
# forced momentum_exhaustion 2R. `final_from_intent=True` => the broker take-profit R is derived from
# the sleeve's native target_dist/stop_dist (vol-tiered runner / measured-move) rather than a fixed
# R. Resolved per intent in build_book_trade_params; any sleeve not listed falls back to
# DEFAULT_EXIT_PROFILE. Verified [RAN] against the 3 fail-closed gates
# (.tools/probe_per_sleeve_exit_gates.py): all 11 sleeves + the default clear gate1/2/3.
SLEEVE_EXIT_PROFILES: dict[str, dict] = {
    "crypto":            dict(policy="time_stop", final_target_r=4.0,  time_stop_bars=1280),
    "idxrev":            dict(policy="time_stop", final_target_r=0.75, time_stop_bars=960),
    "fx_jpy":            dict(policy="time_stop", final_target_r=2.5,  time_stop_bars=48),
    "fx_jpy_ny":         dict(policy="time_stop", final_target_r=2.5,  time_stop_bars=48),
    "sub_xvol_pullback": dict(policy="time_stop", final_target_r=3.0,  time_stop_bars=1280),
    "sub_mid_dn_revert": dict(policy="time_stop", final_target_r=3.0,  time_stop_bars=1280),
    "vp_euidx_pocgrav":  dict(policy="time_stop", final_from_intent=True, time_stop_bars=960),
    "metals_core":       dict(policy="partial_be_runner", trigger_r=2.0, final_from_intent=True,
                              partial_close_ratio=0.5, time_stop_bars=1280),
    "metals_softband":   dict(policy="partial_be_runner", trigger_r=1.5, final_from_intent=True,
                              partial_close_ratio=0.5, time_stop_bars=1280),
    "metals_ob_micro":   dict(policy="partial_be_runner", trigger_r=1.5, final_from_intent=True,
                              partial_close_ratio=0.5, time_stop_bars=1280),
    "energy_agri":       dict(policy="partial_be_runner", trigger_r=2.0, final_target_r=4.0,
                              partial_close_ratio=0.5, time_stop_bars=1280),
    # Runtime-executable candidate-book v2: fixed-target, capless trailing, and targetless time-stop
    # candidates are represented by their native exit semantics. `broker_take_profit_mode="none"` means the
    # broker request carries no TP; the book-owned runtime manages trail/time-stop from ticket-bound state.
    "vol_compression":   dict(policy="time_stop", final_from_intent=True, final_target_r=3.0,
                              # D1 research horizon: 80 D1 bars. Was the literal 7680; the helper
                              # is the same number and makes the unit unmistakable.
                              time_stop_bars=time_stop_m15(RESEARCH_HORIZON_NATIVE_BARS, "D1")),
    "asian_fade":        dict(policy="trailing_runner", trigger_r=0.5, trail_gap_r=0.5,
                              final_target_r=None, broker_take_profit_mode="none", time_stop_bars=48),
    "ny_crypto_momentum": dict(policy="time_stop", final_target_r=None,
                               broker_take_profit_mode="none", time_stop_bars=20),
    "metal_session_reversion": dict(policy="trailing_runner", trigger_r=0.6, trail_gap_r=0.5,
                                    final_target_r=None, broker_take_profit_mode="none", time_stop_bars=24),
    "asia_pdl_fade":     dict(policy="time_stop", final_from_intent=True, final_target_r=3.0,
                              time_stop_bars=32),
    "orb_crypto_london": dict(policy="time_stop", final_from_intent=True, final_target_r=2.0,
                              time_stop_bars=80),
    "liq_asia_up_low_metal": dict(policy="time_stop", final_from_intent=True, final_target_r=3.0,
                                  time_stop_bars=16),
    "kz_london_crypto_low": dict(policy="time_stop", final_target_r=None,
                                 broker_take_profit_mode="none", time_stop_bars=32),
    "vss_fxcross_london_up_low": dict(policy="time_stop", final_from_intent=True, final_target_r=2.0,
                                      time_stop_bars=48),
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
    sleeve: dict(policy="time_stop", final_from_intent=True, final_target_r=2.0,
                 time_stop_bars=time_stop_m15(RESEARCH_HORIZON_NATIVE_BARS, "D1"))
    for sleeve in MARKET_EXPANSION_TARGET2_SLEEVES
})
DEFAULT_EXIT_PROFILE: dict = dict(policy="time_stop", final_target_r=2.0, time_stop_bars=1280)


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
        final_target_r=5.0,
        # The spec sets `final_from_intent=True`, so the broker TP tracks the GENERATOR's ratio
        # (`market_expansion_d1.py:225 target_dist=TARGET_R*risk`, measured at exactly 2.0 on all
        # 318 walked trades). A fixed 5R must therefore turn that off, or the override would be
        # silently ignored on every intent that carries a target.
        final_from_intent=False,
        frontier_cell="target_5R",
        frontier_evidence="phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md",
    ),
    "sub_xvol_pullback": dict(
        final_target_r=4.0,
        final_from_intent=False,
        frontier_cell="target_4R",
        frontier_evidence="phase8/receipts/AK_EXIT_FRONTIER_V2.json",
    ),
    # Session CM (B2700-B2749): AD's measured-best stop-width cell, re-read through the
    # production crypto generator on CJ's true-UTC TRAIN/VAL lane. FTMO RECORDED improves by
    # +0.2527 R/day at the mid band, the latest fold remains +0.0355 better, and 4/5 paired
    # folds improve at every cost band. redacted_account's latest fold is negative, so the ceremony
    # selects this name on FTMO only. The multiplier rebuilds BOTH broker SL and TP from the
    # scaled risk unit, exactly matching AD's stop_1.5x_tgtscale cell.
    "crypto": dict(
        stop_distance_multiplier=1.5,
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
        time_stop_bars=time_stop_m15(1, "D1"),
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_us500_cash_d1_atr_mean_reversion": dict(
        time_stop_bars=time_stop_m15(1, "D1"),
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_ger40_cash_d1_volume_surge_reversal": dict(
        time_stop_bars=time_stop_m15(1, "D1"),
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_us30_cash_d1_volume_surge_reversal": dict(
        time_stop_bars=time_stop_m15(1, "D1"),
        frontier_cell="time_stop_1_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    "mx_ethusd_d1_donchian_20_breakout": dict(
        time_stop_bars=time_stop_m15(10, "D1"),
        frontier_cell="time_stop_10_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
    # The CONTROL sleeve of the ladder, and it is here because the rule prescribed it rather than
    # because the cohort did. `vol_compression`'s 80-bar horizon was declared CORRECTLY all along
    # (it is the sleeve whose right answer proved 96 was wrong), and its ladder is monotone RISING to
    # h=20 with h=1 its worst cell -- the opposite shape to the mis-scaled cohort, which is what makes
    # it a working control. Prescribing 20 for it is an optimisation on a REJECT cell, not a repair.
    "vol_compression": dict(
        time_stop_bars=time_stop_m15(20, "D1"),
        frontier_cell="time_stop_20_d1", frontier_evidence="phase12/receipts/AU_D1_HORIZONS_V1.json"),
})

#: The declared vocabulary of frontier cells. A cell name outside this set is a typo or an undeclared
#: kind of override, and `tests/ultimate_book/test_frontier_exit_contracts.py` refuses it.
#: ``stop_`` is a stop-width contract: both broker SL and TP must be rebuilt from R.
FRONTIER_CELL_KINDS: tuple[str, ...] = ("target_", "time_stop_", "stop_")

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
    stop_mult = over.get("stop_distance_multiplier")
    if stop_mult is not None:
        parts.append(f"stop distance x{float(stop_mult):g} with target scaled")
    return ", ".join(parts) if parts else "contract override"


def resolve_exit_profile(sleeve, *, frontier_exits=()) -> dict:
    """The exit profile the engine runs for `sleeve`, under the frontier selection `frontier_exits`.

    With an empty selection this returns the committed `SLEEVE_EXIT_PROFILES` object itself (not a
    copy), so the default path cannot diverge from the dict by construction. With `sleeve` selected
    it returns a COPY carrying the frontier override.
    """
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


def native_policy_instrumentation(sleeve, *, frontier_exits=()) -> dict:
    """The per-sleeve NATIVE exit-policy fields (the gtos_vnext_dynamic_* subset of a book trade_params),
    derived from SLEEVE_EXIT_PROFILES. Used to rehydrate an ADOPTED position whose on-disk trade record is
    missing (adopt-missing-record): the sleeve identity (the W7:{sleeve} broker comment) is enough to
    restore the validated time-stop / scale-out / target lifecycle, far better than the generic floor.

    NOTE: a `final_from_intent` sleeve (metals) cannot recompute final_target_r without the original intent,
    so it falls back to the profile/DEFAULT final_target_r -- harmless because the BROKER TP was already set
    at placement and bounds the real target; the reconstructable trigger_r / partial_close_ratio / time-stop
    (the parts the engine actually re-drives) are restored exactly.

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
    raw_final_target_r = prof.get("final_target_r", DEFAULT_EXIT_PROFILE["final_target_r"])
    final_target_r = 0.0 if no_broker_tp and raw_final_target_r in (None, "") else float(raw_final_target_r)
    return {
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_selected": policy,
        "gtos_vnext_execution_policy_id": f"emv4_{policy}_v1",
        "gtos_vnext_dynamic_be_trigger_r": float(prof.get("trigger_r", final_target_r)),
        "gtos_vnext_dynamic_final_target_r": final_target_r,
        "gtos_vnext_dynamic_broker_take_profit_mode": "none" if no_broker_tp else "final_target",
        "gtos_vnext_dynamic_no_broker_take_profit": no_broker_tp,
        "gtos_vnext_dynamic_momentum_pullback_r": prof.get("pullback_r"),
        "gtos_vnext_dynamic_partial_close_ratio": prof.get("partial_close_ratio"),
        "gtos_vnext_dynamic_trail_gap_r": prof.get("trail_gap_r"),
        "gtos_vnext_dynamic_time_stop_bars": prof.get("time_stop_bars"),
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
    facts.setdefault("initial_equity_or_balance_baseline", FTMO_INITIAL_BALANCE)
    facts.setdefault("daily_loss_limit_pct", FTMO_DAILY_LOSS_PCT)
    facts.setdefault("overall_loss_limit_pct", FTMO_OVERALL_LOSS_PCT)
    return build_prop_firm_headroom_snapshot_v4_from_account_state(
        facts, config=config, now_utc=now_utc
    )


def build_book_trade_params(sized_unit, intent, geometry, account_state, *, profile_namespace,
                            frontier_exits=()) -> dict:
    """Assemble the FULL V4 trade_params for one sized W7 book unit (per-sleeve native exit policy).

    sized_unit : SizedUnit  (risk_pct_per_trade is a FRACTION -> *100 for percent)
    intent     : TradeIntent(symbol, direction:int +1/-1, decision_day, stop_dist:PRICE, sleeve,
                 target_dist). The sleeve selects its native exit profile (SLEEVE_EXIT_PROFILES); the
                 broker SL=-1R / TP=final_target_r and the policy management fields come from it.
    geometry   : Mapping/obj resolved at decision tick; must provide entry_price; may provide
                 stop_loss / risk_distance (else derived from intent). take_profit_1 is recomputed
                 here from the sleeve's native final_target_r so the broker TP is self-consistent.
    account_state : live broker reads for the prop-firm headroom snapshot (see above).
    frontier_exits : the validated frontier-exit sleeve selection (see FRONTIER_EXIT_OVERRIDES).
                 Empty by default, in which case every key of the returned dict is byte-identical to
                 the pre-B1550 output -- asserted in tests/ultimate_book/test_frontier_exit_contracts.py.
    """
    symbol = str(intent.symbol)
    direction = "LONG" if int(intent.direction) > 0 else "SHORT"
    sign = 1.0 if direction == "LONG" else -1.0
    entry_price = float(_g(geometry, "entry_price"))
    base_risk_distance = float(_g(geometry, "risk_distance", intent.stop_dist))

    # ---- per-sleeve native exit profile (replaces the forced momentum_exhaustion 2R) ----
    prof = resolve_exit_profile(getattr(intent, "sleeve", None), frontier_exits=frontier_exits)
    stop_distance_multiplier = float(prof.get("stop_distance_multiplier", 1.0))
    if stop_distance_multiplier <= 0:
        raise ValueError(
            f"stop_distance_multiplier must be > 0, got {stop_distance_multiplier!r}"
        )
    risk_distance = base_risk_distance * stop_distance_multiplier
    policy = str(prof["policy"])
    execution_policy_id = f"emv4_{policy}_v1"
    native_target = getattr(intent, "target_dist", None)
    native_stop = getattr(intent, "stop_dist", None)
    broker_take_profit_mode = str(prof.get("broker_take_profit_mode", "final_target")).strip().lower()
    no_broker_take_profit = broker_take_profit_mode == "none"
    if (
        prof.get("final_from_intent")
        and native_target not in (None, "")
        and native_stop not in (None, "")
        and float(native_stop) > 0
        and float(native_target) > 0
    ):
        final_target_r = float(native_target) / float(native_stop)
    elif no_broker_take_profit and prof.get("final_target_r") in (None, ""):
        final_target_r = 0.0
    else:
        final_target_r = float(prof.get("final_target_r", DEFAULT_EXIT_PROFILE["final_target_r"]))
    trigger_r = float(prof.get("trigger_r", final_target_r))
    partial_close_ratio = prof.get("partial_close_ratio")
    trail_gap_r = prof.get("trail_gap_r")
    pullback_r = prof.get("pullback_r")
    time_stop_bars = prof.get("time_stop_bars")

    # A selected width cell must rebuild the broker SL from scaled R. With multiplier
    # 1.0 the caller-supplied stop_loss still wins, preserving the exact default path.
    stop_loss = (
        float(_g(geometry, "stop_loss", entry_price - sign * risk_distance))
        if stop_distance_multiplier == 1.0
        else entry_price - sign * risk_distance
    )
    take_profit_1 = 0.0 if no_broker_take_profit else entry_price + sign * final_target_r * risk_distance
    risk_pct = round(float(sized_unit.risk_pct_per_trade) * 100.0, 8)  # FRACTION -> PERCENT

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

    headroom = build_prop_firm_headroom_snapshot(account_state, account_namespace=profile_namespace)

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

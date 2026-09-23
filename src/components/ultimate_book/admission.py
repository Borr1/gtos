"""ultimate_book_live_package.py â€” STANDALONE DEPLOYABLE PACKAGE (default-off).

Self-contained implementation of the FULL Wave-2 validated book (PORTFOLIO_BUILD_W2.md +
KB2_true_corr_mc.md). It is a pure decision/sizing/governor library: it performs NO network,
NO MT5, NO broker, NO order placement. It turns per-sleeve candidate trade intents into
confidence-weighted, correlated-risk-unit-governed, fail-closed sizing decisions, and answers the
FTMO challenge question (size each independent risk unit so the book reaches +8% before -5% daily /
-10% maxDD).

WHY a separate module (not just the integrator): the integrator scripts
(INTEG_portfolio_build_w2.py / INTEG_portfolio_build.py) regenerate the book FROM RAW DATA to PROVE
the edge (research path). This module is the THIN deployable surface that the production engine wires
to: it carries the LOCKED rules as data (sleeve registry + confidence weights + governor limits) and
the leak-free sizing/governor math, with the heavy backtest generators imported only when a caller
explicitly asks to regenerate streams (replay-parity / self-test). Nothing here can place an order;
go-live is gated behind config flags the owner flips (see KB3_live_package.md GO-LIVE CHECKLIST).

DOCTRINE PRESERVED (cite: PORTFOLIO_BUILD_W2.md, KB_architecture_spec.md):
 - Per-sleeve CONFIDENCE weights from data_depth TRAIN/FORWARD evidence (delete nothing; falsified
   sleeves demoted to 0.15, never zero).
 - CORRELATED-RISK-UNIT: same sleeve-class firing on a decision-day = ONE risk unit (correlated);
   cross-class = independent units (the proven ~0 cross-sleeve correlation diversification).
 - SIZE BY CONFIDENCE: per-unit risk% = base_risk * sleeve_conf (* intra-trade size ramp).
 - BOTH ACCOUNTS full 8-sleeve book @ 0.75% (balanced) â€” diversification is WITHIN each account.
 - FAIL-CLOSED governors: soft daily-stop well below the -5% hard limit; max-DD de-risk into the
   wall; portfolio gross-risk cap; any missing/contradictory state -> size 0 for NEW entries
   (existing trades managed by their own structural stops).
 - Outer CIRCUIT BREAKER: a single operator switch (size_cap_override=0) flattens new entries.
 - ALL fills go through geometry_lib.simulate (leak-free pessimistic labeler) â€” never hand-rolled.
   Per-trade R winsorized [-1.3,+5].

This module is import-safe with ZERO heavy deps for the deployable path (registry + sizer +
governor). The backtest generators (used only by regenerate_streams / parity self-test) are imported
lazily so a production process never pulls in pandas/csv data loaders.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Mapping, Sequence, Any

# ===========================================================================================
# 0. WINSORIZE + FTMO CONSTANTS (locked; cite INTEG_portfolio_build.py TARGET/MAXDD/DAILY)
# ===========================================================================================
R_WINSOR_LO = -1.3
R_WINSOR_HI = 5.0
def winsorize_R(r: float) -> float:
    """Clamp R. On Challenge the bounds are the score. Empty leaves that side uncut."""
    value = float(r)
    if not _on_challenge_book():
        return max(R_WINSOR_LO, min(R_WINSOR_HI, value))
    pack = _pack(
        {"r": value, "recorded_lo": R_WINSOR_LO, "recorded_hi": R_WINSOR_HI, "login": 0},
        {
            "winsor_lo": _score_q(
                "The score you return is the low winsor bound for this R. "
                "The recorded low bound is a fact, not the bound. "
                "An empty score leaves the low side unset. Do not send."
            ),
            "winsor_hi": _score_q(
                "The score you return is the high winsor bound for this R. "
                "The recorded high bound is a fact, not the bound. "
                "An empty score leaves the high side unset. Do not send."
            ),
        },
    )
    lo = pack.get("winsor_lo")
    hi = pack.get("winsor_hi")
    if lo is not None:
        value = max(float(lo), value)
    if hi is not None:
        value = min(float(hi), value)
    return value

# FTMO challenge rule constants (the owner objective; INTEG TARGET/MAXDD/DAILY).
FTMO_TARGET = 0.08      # +8% profit target (absorbing pass)
FTMO_MAXDD = 0.10       # -10% overall max drawdown (fail)
FTMO_DAILY = 0.05       # -5% daily loss limit (fail)

# ===========================================================================================
# 0b. WAVE-7 (UNLEASH) TICK-TRUTH EXECUTION FLOORS + sqrt-N WITHIN-SLEEVE POOLING (default-clean).
#     Source: KB7_execution_truth.md (per-symbol bridge tick spread) + KB7_TICK_BOOK_RESTATE.json +
#     KB7_TICK_TRUTH_RESULT.json + KB7_stale_audit.md (sqrt-N concentration pooling).
# ===========================================================================================
# DROPPED illiquid energy legs (real tick spread swamps the 1*ATR stop -> modeled EV is a cost-map
# artifact). These are removed from the energy_agri universe above AND policed defensively here so a
# stale upstream candidate for either symbol fails closed in the live path.
ENERGY_DROPPED_SYMBOLS: frozenset[str] = frozenset({"HEATOIL_c", "NATGAS_cash"})

# Per-symbol TICK SPREAD FLOOR (round-trip cost in R) â€” the MEASURED real bid/ask round-trip the live
# sizer must assume per symbol (a floor: never assume a fill cheaper than this). Measured on the
# siliconmetatrader5 bridge (2023H2-2026 forward-heavy subset; KB7_execution_truth.md per-sleeve tick
# tables + ULTIMATE_TICK_SPREAD_GOLD.json XAU cross-check). The illiquid legs (HEATOIL/NATGAS, and the
# crypto analogue DASH) carry floors that are a LARGE fraction of (or exceed) their stop -> they are
# the dropped/flagged set. Liquid carriers (XAU/crude/BTC/JPY) floor BELOW the old per-class cost map
# (the proxy over-charged them). This is the per-SYMBOL replacement for the single per-class cost map.
TICK_SPREAD_FLOOR_R: dict[str, float] = {
    # metals (KB7_TICK_TRUTH_RESULT per_symbol mean_entry_spread_R; XAU cross-checked GOLD 0.0118 RT)
    "XAUUSD": 0.0118, "XAGUSD": 0.0408,
    # energy crude (liquid; ~half the old 0.0372R class map)
    "USOIL_cash": 0.0270, "UKOIL_cash": 0.0258,
    # energy illiquid (DROPPED â€” floor >> stop; here for the fail-closed guard / audit only)
    "NATGAS_cash": 0.3932, "HEATOIL_c": 0.9763,
    # crypto (BTC fill-robust 0.09 bps ~ 0R on a 2*ATR stop; DASH illiquid 85 bps flagged)
    "BTCUSD": 0.0001, "DASHUSD": 0.0850,
    # jpy fx (London round-trip; NY ~0.068R; both BELOW the 0.1148R class map)
    "USDJPY": 0.0841,
}
# Symbols whose measured tick floor swamps a typical stop -> NOT live-tradeable at the deploy geometry.
TICK_SPREAD_FLOOR_UNTRADEABLE_R: float = 0.20  # >= this round-trip floor => gate the symbol out


def tick_spread_floor_for(symbol: str) -> float | None:
    """Return the MEASURED per-symbol round-trip tick spread floor in R (None if not tick-covered).

    The live sizer/cost path must charge AT LEAST this per round trip for a market fill on `symbol`
    (the per-class cost map is replaced by this per-symbol floor). None => no direct bridge feed; the
    caller transfers the same-class floor (e.g. GBPJPY <- USDJPY, metals_softband/ob_micro <- XAU).
    """
    return TICK_SPREAD_FLOOR_R.get(symbol)


def is_tick_tradeable(symbol: str) -> bool:
    """True unless the symbol is explicitly dropped OR its measured tick floor swamps the stop.

    On Challenge the drop is the tick_untradeable hop. The measured floor and the
    recorded level are facts. An empty answer does not refuse the symbol.
    """
    if not _on_challenge_book():
        if symbol in ENERGY_DROPPED_SYMBOLS:
            return False
        floor = TICK_SPREAD_FLOOR_R.get(symbol)
        if floor is not None and floor >= TICK_SPREAD_FLOOR_UNTRADEABLE_R:
            return False
        return True
    floor = TICK_SPREAD_FLOOR_R.get(symbol)
    block = _spot("tick_untradeable")
    if block is None:
        return True
    pack = _pack(
        {
            "symbol": symbol,
            "measured_floor_r": floor,
            "recorded_untradeable_r": TICK_SPREAD_FLOOR_UNTRADEABLE_R,
            "on_dropped_list": symbol in ENERGY_DROPPED_SYMBOLS,
            "login": 0,
        },
        {"tick_untradeable": block},
    )
    return pack.get("tick_untradeable") != "floor_refuses"


def pool_same_day_sleeve_R(per_trade_R: Sequence[float], *, sqrt_n: bool = False) -> float:
    """Pool same-day SAME-SLEEVE per-trade R into ONE within-sleeve daily contribution.

    DEPLOYED convention (sqrt_n=False) = MEAN pooling (sum/len): same-day same-sleeve trades treated
    as perfectly correlated (corr=1) -> ONE risk unit at the mean R. This matches the locked
    INTEG_portfolio_build_w2.build_matrix (`sum(rs)/len(rs)`) the deploy book + W7 final MC were
    built from.

    WAVE-7 sqrt-N partial pooling (sqrt_n=True; KB7_stale_audit.md (b)) = sum/sqrt(n): same-day
    same-sleeve trades are correlated but NOT identical, so the fair credit is partial (effective
    N = sqrt(n)), not zero. This is a FREE win on the binding vol-matched 1.5x-stress at matched risk
    (+1.9..+2.2pp) or ~27% faster speed-to-target at fixed nominal; daily-breach stays 0% to 2% and
    worst-day inside the -5% wall. CROSS-sleeve diversification is untouched (only the within-sleeve
    same-day corr assumption is relaxed from 1.0 to 1/sqrt(n)). DEFAULT-OFF in the deploy module so
    the live sizing matches the locked W7 MC headline unless the owner opts into the sqrt-N refresh.
    """
    rs = [float(r) for r in per_trade_R]
    n = len(rs)
    if n == 0:
        return 0.0
    if n == 1:
        return rs[0]
    s = sum(rs)
    return s / math.sqrt(n) if sqrt_n else s / n

# ===========================================================================================
# 1. SLEEVE REGISTRY â€” the LOCKED Wave-2 book (PORTFOLIO_BUILD_W2.md Section 1 + 2).
#    confidence weights MUST match INTEG_portfolio_build_w2.SLEEVE_CONF exactly.
#    A self-test (test_ultimate_book_live_package.py) asserts byte-equality against the integrator.
# ===========================================================================================
@dataclass(frozen=True)
class SleeveSpec:
    name: str
    confidence: float           # SLEEVE_CONF â€” the size weight (Wave-2 data_depth-validated)
    asset_class: str            # corr cluster id for the correlated-risk-unit governor
    symbols: tuple[str, ...]    # the live universe for this sleeve
    status: str                 # 'train_validated' | 'forward_only' | 'breadth_falsified'
    note: str

# Wave-2 LOCKED registry. confidence == INTEG_portfolio_build_w2.SLEEVE_CONF.
SLEEVE_REGISTRY: dict[str, SleeveSpec] = {
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr", 0.15, "fx_major",
        ("EURUSD",),
        "forward_only",
        "EURUSD M15 SHORT CHAIR_APPLY_20260920; NEVER alias sub_mid_dn_revert"),

    "metals_core": SleeveSpec(
        "metals_core", 1.00, "metals",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"),
        "train_validated",
        "vol-gated FVG-retest H1->M15 cascade STATE_D exit; causal paired-lift; +1.16R fwd; deepest anchor"),
    "crypto": SleeveSpec(
        "crypto", 0.85, "crypto",
        # KEEP THIS TUPLE EQUAL TO `sleeves.crypto.ON_SURFACE`. It is the SECOND declaration of the
        # same surface and it does NOT gate generation -- `sleeves/registry.py:50` passes
        # `crypto.ON_SURFACE` by reference and `book_engine.py:548` iterates THAT -- so a
        # disagreement here is silent. It WAS silent: this tuple still read ("BTCUSD","DASHUSD")
        # with a comment asserting ETH was excluded, for as long as that was false. It cannot be a
        # reference: `sleeves.crypto` imports `TradeIntent` from this module, so importing it here
        # is a cycle. It is a literal held equal by
        # `tests/ultimate_book/test_b7_live_contract_changes.py` instead.
        ("BTCUSD", "DASHUSD", "ETHUSD"),
        "train_validated",
        # ETHUSD added 2026-08-11 (owner-authorized, swarm-2 lane B7): excluded originally for a
        # broken-H4 DATA reason that no longer holds. Out of the `year>=2025` selection window and
        # at broker-true cost, BTC+ETH is net +0.4270 R/trade (n=243, day-block CI95
        # [+0.122,+0.736]) where the BTC+DASH pair does not clear zero (+0.2268, p 0.132). See
        # `sleeves/crypto.py`'s docstring for the full receipt list.
        "Donchian-20 breakout + ac60>=0.15 persistence + sd=2*ATR + target4; BTC+DASH+ETH"),
    "energy_agri": SleeveSpec(
        "energy_agri", 0.80, "energy",
        # WAVE-7 (UNLEASH) tick-truth: HEATOIL_c + NATGAS_cash DROPPED from the live universe. Real
        # bid/ask round-trip spread (HEATOIL 0.98R, NATGAS 0.39R measured on the bridge) swamps the
        # 1*ATR stop vs the 0.037R cost-map proxy (KB7_execution_truth.md; 6/21 HEATOIL trades stop on
        # spread alone). Their modeled EV was a cost-map artifact: real-fill energy EV is unchanged
        # (+0.349->+0.350R) with far less tail, so dropping them is a strict improvement (map-don't-kill).
        # Also enforced by ENERGY_DROPPED_SYMBOLS + the per-symbol TICK_SPREAD_FLOOR_R guard.
        ("USOIL_cash", "UKOIL_cash", "CORN_c", "COTTON_c"),
        "train_validated",
        "energy FVG cascade STATE_D + supply-shock vr>=2 runR=4; agri continuation; TRAIN +0.433R; "
        "W7 tick-truth: HEATOIL_c+NATGAS_cash dropped (illiquid, spread swamps stop)"),
    "metals_softband": SleeveSpec(
        "metals_softband", 0.50, "metals",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"),
        "train_validated",
        "FVG soft-ramp confidence band 0.04<=ac60<0.10 (freq the hard gate drops); STATE_D exit; disjoint from core"),
    "metals_ob_micro": SleeveSpec(
        "metals_ob_micro", 0.30, "metals",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"),
        "train_validated",
        "OB-retest ac60>=0.20 only, dedup vs FVG; small tail-frequency add"),
    "fx_jpy_ny": SleeveSpec(
        "fx_jpy_ny", 0.15, "jpy",
        ("GBPJPY", "USDJPY"),
        "forward_only",
        "gated NY-open JPY 2nd session (imp>=1.0*ATR + M15 trend20); forward-only window -> tiny breadth"),
    "idxrev": SleeveSpec(
        "idxrev", 0.15, "index",
        ("SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40"),
        "breadth_falsified",
        "failed-breakout fade; data_depth FALSIFIED train (-0.065R, 5 deep idx) -> demoted to breadth, not deleted"),
    "fx_jpy": SleeveSpec(
        "fx_jpy", 0.15, "jpy",
        ("GBPJPY", "USDJPY"),
        "breadth_falsified",
        "London-open momentum; data_depth FALSIFIED train (-0.103R 11.5yr) -> demoted to breadth, not deleted"),
}
SLEEVE_NAMES: tuple[str, ...] = tuple(SLEEVE_REGISTRY.keys())

# ===========================================================================================
# 1b. WAVE-5 clean_3 ADDITIVE SLEEVES (DEFAULT-OFF) â€” the data-chosen deploy upgrade.
#     Source of truth: INTEG_W5_CLEAN3_DEPLOY.json (the LOCKED clean_3 deploy book) +
#     PORTFOLIO_BUILD_W5.md Section 1. These are NOT loaded into the live decision path unless the
#     caller passes include_clean3=True (owner flips the flag at go-live). The deploy-selection MC
#     (INTEG_portfolio_build_w5) chose exactly these three over "add everything": they RAISE Sharpe
#     and hold the 1.5x-stress tail at book level, banking +205 low-corr tr/yr of orthogonal breadth.
#     Confidence weights are parity-checked byte-for-byte against the integrator artifact.
# ===========================================================================================
CLEAN3_REGISTRY: dict[str, SleeveSpec] = {
    "sub_mid_dn_re_proxy_nzdusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_nzdusd_short_m15_atr", 0.15, "fx_major",
        ("NZDUSD",),
        "forward_only",
        "NZDUSD M15 SHORT mid-stretch>=1ATR Module_ATR hist-KEEP 20260920; NOT portable from AUD; Chair APPLY ON_SURFACE"),

    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr", 0.15, "fx_major",
        ("EURUSD",),
        "forward_only",
        "EURUSD M15 SHORT CHAIR_APPLY_20260920; NEVER alias sub_mid_dn_revert"),

    "sub_xvol_pullback": SleeveSpec(
        "sub_xvol_pullback", 0.45, "substrate",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
         "USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c", "CORN_c", "COTTON_c",
         "SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40"),
        "train_validated",
        "substrate xhi-vol uptrend pullback long (vol=xhi persist=rand trend=up mtf=conflict) 1:3R; "
        "metals/energy/index/fx (crypto+jpy dropped); FWD +1.61R n51 both yrs; corr vs book -0.012; "
        "ADDITIVE flagship (lifts Sharpe AND stress tail)"),
    "vp_euidx_pocgrav": SleeveSpec(
        "vp_euidx_pocgrav", 0.30, "volprofile",
        ("GER40", "UK100"),
        "forward_only",
        "GER40+UK100 prior-day volume-profile POC-gravitation (|d_poc|>=2.0 ATR, vr>=1.2); FWD +0.24R "
        "n230 both yrs ~115 tr/yr; corr +0.049; M1-since-2024 -> essentially forward-only (flagged); "
        "the frequency engine of the additive set"),
    "sub_mid_dn_revert": SleeveSpec(
        "sub_mid_dn_revert", 0.20, "substrate",
        # ETHUSD removed (twin of the crypto-sleeve ETH fix): ETH's research H4 was broken so it
        # contributed ZERO rows to the +0.49R/n129 validation, yet it is live-capable on FTMO -> a
        # live ETH substrate fire would be an UNVALIDATED carrier. BTCUSD kept (validated carrier).
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
         "USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c", "CORN_c", "COTTON_c",
         "SPX500", "UK100", "GER40", "BTCUSD",
         "GBPJPY", "USDJPY", "EURJPY", "AUDJPY", "CHFJPY"),
        "train_validated",
        "substrate NY-session mid-vol downtrend reversion long (trend=dn rngpos=mid session=ny) 1:3R; "
        "FWD +0.49R n129 ~64 tr/yr; corr -0.023; repairs the book's NY-session coverage"),
}
CLEAN3_NAMES: tuple[str, ...] = tuple(CLEAN3_REGISTRY.keys())

# vol-matched risk rescale (PORTFOLIO_BUILD_W5.md Section 2 + INTEG_W5_CLEAN3_DEPLOY.json):
# the clean_3 book runs hotter per unit nominal (daily std 0.5997 vs book 0.5686), so the FAIR,
# risk-equivalent deploy multiplies nominal risk by VOL_SCALE to equalize daily std == book-only;
# the diversification then banks as a HIGHER PASS-RATE FLOOR at no tail cost (deploy at 0.71% eff).
CLEAN3_VOL_SCALE = 0.9481

# ===========================================================================================
# 1d. WAVE-6 clean_4 ADDITIVE SLEEVE (DEFAULT-OFF) â€” the ONE confirmed W6 diversifier.
#     Source of truth: KB6_SESSION_STACKS_RESULT.json + PORTFOLIO_BUILD_W6.md Section 1.
#     The Wave-6 re-mine tested three proposed promotions (broad session-leadlag, metals session
#     stack, DXY->FX) on the binding vol-matched 1.5x-stress MC. Exactly ONE folded as a sleeve and
#     had to be REDESIGNED: the GENUINE cross-asset LEAD subset of the session-open lead-lag set
#     (the deep-train JPY-cross legs at 27-31% win were DILUTIVE, -22pts stress; trimming to the
#     null-cleared cross-asset leads turned that into a +2.5pt stress GAIN). The other two are
#     SELECTOR-only (metals_sess_stack = 90%-same-trade double-count of metals_core, corr +0.65;
#     dxy_bias = n=12 fwd filter) and are documented as overlays, NOT folded as sleeves.
# ===========================================================================================
CLEAN4_REGISTRY: dict[str, SleeveSpec] = {
    "session_leadlag_genuine": SleeveSpec(
        "session_leadlag_genuine", 0.15, "leadlag",
        ("GER40", "USDJPY", "AUDJPY", "SPX500", "NAS100"),
        "forward_only",
        "GENUINE cross-asset session-open LEAD subset (US30->GER40/USDJPY/AUDJPY ny_open + "
        "USDJPY->AUDJPY london_ny; null-cleared z3.09-4.66, leader-adds-dR>0.25, both fwd yrs +); "
        "FWD +0.46R n390 36%win ~195 tr/yr; corr +0.053 vs book; ADDITIVE on the vol-matched stress "
        "MC (Sharpe 0.1522->0.1586, stress@1% +2.51 / @1.5% +2.03). M15 index/cross since 2025-06 -> "
        "forward-only (graduate when a 3rd fwd year exists). The broad set (incl JPY-cross legs) was "
        "DILUTIVE (-22pts stress) and is EXCLUDED; this is the trimmed genuine-lead sleeve only."),
}
CLEAN4_NAMES: tuple[str, ...] = tuple(CLEAN4_REGISTRY.keys())

# clean_4 = clean_3 + session_leadlag_genuine, re-vol-matched on the LOCKED W2 MC engine.
# folded_additive in KB6_SESSION_STACKS_RESULT.json: Sharpe 0.1586, vol_scale 0.9873.
CLEAN4_VOL_SCALE = 0.9873

# ===========================================================================================
# 1c. CONFLUENCE OVERLAYS (DEFAULT-OFF) â€” validated SIZE-UP SELECTORS on base sleeves.
#     Source: KB5_FRONTIER.json + KB5_validate_stack.py + PORTFOLIO_BUILD_W5.md Section 4/6.
#     These are NOT separate sleeves (the leader-veto subset has corr +0.79 with sub_xvol_pullback
#     = same population, filtered -> double-count). They raise the size of an EXISTING base-sleeve
#     intent when an INDEPENDENT confluence condition holds. Multipliers are bounded (>=1.0, never
#     widen risk beyond the unit cap) and applied multiplicatively, capped at OVERLAY_SIZEUP_MAX.
# ===========================================================================================
@dataclass(frozen=True)
class ConfluenceOverlay:
    name: str
    base_sleeves: tuple[str, ...]   # which base sleeves this size-up selector applies to
    sizeup: float                   # size-up multiplier when the condition holds (>=1.0)
    note: str

# Leader-impulse VETO (the cross-layer flagship). On a sub_xvol_pullback signal, when NO relevant
# cross-asset leader is impulsing (|z|<1.5 -> ll_impulse=none), size UP (high conviction): base
# FWD +0.71R -> veto cell +1.53R (pooled, perm-p 0.0003, both fwd yrs); the mirror (leader opposed)
# is forward-NEGATIVE -0.35R. Sized conservatively at 1.5x (NOT the raw 2.16x R-ratio) to keep the
# unit within the worst-case risk cap; the un-gated base carries the frequency.
# Session-active stack: an active-session (London open .. NY, H4 hour in {8,12,16}) bar adds a
# modest, independent directional-follow-through edge (KB5 condition family); stacked at 1.15x.
LEADER_IMPULSE_NONE = "none"        # ll_impulse tag value meaning no leader impulsing >=1.5Ïƒ
SESSION_ACTIVE_HOURS: frozenset[int] = frozenset({8, 12, 16})  # H4 server hours: London open .. NY
OVERLAY_SIZEUP_MAX = 1.75           # hard cap on the COMBINED overlay size-up (governor-safe)

CONFLUENCE_OVERLAYS: dict[str, ConfluenceOverlay] = {
    "leader_impulse_veto": ConfluenceOverlay(
        "leader_impulse_veto", ("sub_xvol_pullback",), 1.5,
        "cross-layer flagship: size up xvol pullback long when ll_impulse=none (no relevant leader "
        ">=1.5sigma). base +0.71R -> +1.53R fwd, perm-p 0.0003, 2/2 yrs; mirror (opposed) fwd-neg"),
    "session_active_stack": ConfluenceOverlay(
        "session_active_stack", ("sub_xvol_pullback", "sub_mid_dn_revert"), 1.15,
        "active-session stack: size up when the H4 decision bar hour in {8,12,16} (London open..NY); "
        "independent directional-follow-through family (KB5_condition_families c_session_active)"),
}

# ===========================================================================================
# 1e. WAVE-6 VP-ACCEPTANCE SELECTOR (exit-honest refinement of sub_mid_dn_revert).
#     Source: KB6_confluence_state_d.md Section 7 + KB6_OVERLAY_PASSRATE_RESULT.json (vpacc_replace).
#     Under the DEPLOYED cs.exit_state_d scale-out (NOT fixed 1:3R), the sprawling low-EV
#     sub_mid_dn_revert is refined to its VP-acceptance subset (volume-profile vp_loc=above_va): a
#     16%-retention NOISE-CUT that LIFTS the binding vol-matched stress@1.5% from 69.6% (exit-honest)
#     to 74.8% (best of all overlay tests) at flat 2/2 forward years (2025 +0.56 / 2026 +0.59).
#     This is the STATE_D-honest definition; the clean_3 book scored sub_mid_dn_revert at fixed-3R,
#     which OVERSTATES stress headroom by ~2.5pts. Default-OFF (owner opts in via vp_acceptance=True).
VP_ACCEPTANCE_TAG = "above_va"  # vp_loc tag value: prior-day volume-profile acceptance above value-area
VP_ACCEPTANCE_BASE = "sub_mid_dn_revert"  # the only base sleeve this refinement applies to
# When vp_acceptance is enabled, a sub_mid_dn_revert intent whose vp_loc != above_va is DROPPED
# (noise-cut); the kept above_va subset is the exit-honest definition. Documented stress lift:
# deploy_sd (exit-honest) stress@1.5% 69.59% -> vpacc_replace 74.84% (+5.25pts), Sharpe 0.148->0.151.
VP_ACCEPTANCE_STRESS_1P5_FROM = 0.6959
VP_ACCEPTANCE_STRESS_1P5_TO = 0.74835

# ===========================================================================================
# 1f. WAVE-6 TEMPORAL STRESS-DE-RISK OVERLAY (day-level size multiplier; reactive layer default-on).
#     Source: KB6_stress_hardening.md + KB6_COMBINE_RESULT.json. The binding 1.5x left tail is a
#     TEMPORAL CLUSTERING problem (crypto = 49.4% of worst-day loss mass; runs of -0.93 crypto days),
#     NOT single fat days -> static per-sleeve vol-target NULL (never binds). The fix is a leak-free
#     REACTIVE day-level de-risk multiplier (uses ONLY realized days < t), wired ON TOP of the fixed
#     sleeve confidence weights (sizing-by-confidence preserved). Two tiers:
#       TIER-1 reactive (ladder+coloss) â€” FORWARD-POSITIVE, recommended default-on:
#         stress@1% 80.86->87.48 (+6.6), @1.5% 70.93->77.60 (+6.7), fwd +2.0@1%, Sharpe 0.1522->0.1564
#       TIER-2 regime (full stack regime+ladder+coloss) â€” bigger lift but the regime component is
#         FORWARD-FLAT/slightly-neg alone (full-history optimizer), so it is OPT-IN after first clear:
#         stress@1% ->91.86 (+11.0), @1.5% ->83.09 (+12.2), fwd +1.7@1%, Sharpe 0.1568.
# ===========================================================================================
@dataclass(frozen=True)
class StressDeriskOverlay:
    name: str
    tier: int                       # 1 = reactive forward-clean (default-on); 2 = +regime (opt-in)
    stress_1pct: float              # documented vol-matched stress P(pass) @1% with this overlay
    stress_1p5pct: float
    fwd_delta_1pct: float           # forward-holdout delta @1% (the distrust check)
    sharpe: float
    note: str

# Ladder (after 1/2+ consecutive book-loss days, size next day x0.80 then x0.60; reset on green) AND
# co-loss breaker (trailing-5-day cross-sleeve neg-firing fraction >= 0.57 -> that day x0.60).
LADDER_STEPS: tuple[float, ...] = (1.0, 0.80, 0.60)   # consecutive-loss-day size multipliers
COLOSS_NEG_FRAC: float = 0.57                          # trailing-5d neg-firing fraction trigger
COLOSS_SIZE_MULT: float = 0.60                         # de-risk multiplier when the breaker trips
COLOSS_WINDOW: int = 5
STRESS_DERISK_MIN_MULT: float = 0.60                   # floor: the overlay only EVER shrinks size

STRESS_DERISK_OVERLAYS: dict[str, StressDeriskOverlay] = {
    "reactive_ladder_coloss": StressDeriskOverlay(
        "reactive_ladder_coloss", 1, 0.8748, 0.7760, 0.020, 0.1564,
        "TIER-1 reactive temporal de-risk (3-step daily ladder x coloss breaker); forward-POSITIVE "
        "(+2.0@1%); no fitted regime -> generalizes; RECOMMENDED default-on for the first live cycle"),
    "full_stack_regime_ladder_coloss": StressDeriskOverlay(
        "full_stack_regime_ladder_coloss", 2, 0.9186, 0.8309, 0.017, 0.1568,
        "TIER-2 full stack (W3 breadth+dd regime overlay ON TOP of reactive); biggest stress lift "
        "(+11.0@1%) but regime component is forward-flat ALONE -> opt-in after the reactive layer is "
        "proven live; re-validate regime as the forward window lengthens"),
}
DEFAULT_STRESS_OVERLAY = "reactive_ladder_coloss"  # tier-1, forward-clean


@dataclass
class StressDeriskState:
    """Realized-history facts the runtime feeds the reactive de-risk overlay (leak-free, days < t).

    consecutive_loss_days : count of consecutive prior book-loss days ending yesterday (reset by green).
    trailing_neg_frac     : trailing-COLOSS_WINDOW-day mean cross-sleeve negative-firing fraction.
    """
    consecutive_loss_days: int = 0
    trailing_neg_frac: float = 0.0


def stress_derisk_multiplier(
    st: "StressDeriskState", *, enabled: bool = True, tier: int = 1,
) -> tuple[float | None, tuple[str, ...]]:
    """Day-level size multiplier (<=1.0) from the reactive temporal de-risk overlay (TIER-1).

    Leak-free: uses ONLY realized prior-day facts in `st`. Returns (multiplier, reasons). The
    multiplier ONLY ever shrinks size (floor STRESS_DERISK_MIN_MULT); it never widens risk. TIER-2
    (regime) is a full-history classifier and is NOT applied here (the deployable reactive layer is
    forward-clean); the integrator carries the regime multiplier for the opt-in aggressive profile.
    """
    if not enabled:
        return 1.0, ()
    if _on_challenge_book():
        asked = _scalar(
            "stress_derisk",
            "The score you return is the day-level size multiplier on this live equity. "
            "The ladder steps and the co-loss fraction on this card are facts, not the multiplier. "
            "An empty score leaves the multiplier unset. Do not send.",
            {
                "consecutive_loss_days": int(getattr(st, "consecutive_loss_days", 0) or 0),
                "trailing_neg_frac": float(getattr(st, "trailing_neg_frac", 0.0) or 0.0),
                "recorded_ladder": list(LADDER_STEPS),
                "recorded_coloss_neg_frac": COLOSS_NEG_FRAC,
                "recorded_coloss_mult": COLOSS_SIZE_MULT,
                "recorded_min_mult": STRESS_DERISK_MIN_MULT,
                "login": 0,
            },
        )
        if asked is None:
            return None, ()
        return float(asked), ("stress_score",)
    mult = 1.0
    reasons: list[str] = []
    # 3-step consecutive-loss ladder
    step = min(int(max(st.consecutive_loss_days, 0)), len(LADDER_STEPS) - 1)
    if step > 0:
        mult *= LADDER_STEPS[step]
        reasons.append(f"ladder_step{step}")
    # co-loss circuit breaker
    if st.trailing_neg_frac >= COLOSS_NEG_FRAC:
        mult *= COLOSS_SIZE_MULT
        reasons.append("coloss_breaker")
    return max(mult, STRESS_DERISK_MIN_MULT), tuple(reasons)


def compute_stress_derisk_state(closed_deals, now_utc, *, offset_hours: float = 0.0,
                                window: int = COLOSS_WINDOW) -> "StressDeriskState":
    """Leak-free StressDeriskState from realized closed BOOK deals (PRIOR server-days only; today excluded).

    The reactive de-risk overlay (stress_derisk_multiplier) only ever SHRINKS size, so feeding it real
    history can only reduce risk after losses -- never widen it. Inputs:
      closed_deals : [{sleeve, profit, time}] where `time` is the broker-server deal epoch (server wall
                     clock as a unix ts; utcfromtimestamp -> the server-local datetime).
      now_utc      : current UTC time; offset_hours derives the server-local 'today' so the in-progress
                     day is EXCLUDED (leak-free -- the overlay must use only fully-realized prior days).
    Returns (consecutive_loss_days, trailing_neg_frac). NEVER raises (a bad read -> neutral empty state,
    i.e. no de-risk, the safe-inert fallback).

    Day semantics (documented assumption): a net-loss PRIOR traded day extends the consecutive streak; a
    net>=0 (green/flat) traded day RESETS it; a no-deal day is skipped (the book did not trade that day, so
    it is neither a loss nor a reset). trailing_neg_frac = mean over the trailing `window` TRADED days of
    that day's negative-firing fraction (#sleeves closing net<0 / #sleeves that fired)."""
    import datetime as _dt
    try:
        today = (now_utc.astimezone(_dt.timezone.utc) + _dt.timedelta(hours=float(offset_hours))).date()
        day_net: dict = {}
        day_sleeve: dict = {}
        for d in closed_deals or []:
            t = d.get("time")
            if not t:
                continue
            day = _dt.datetime.fromtimestamp(int(t), _dt.timezone.utc).date()
            if day >= today:                       # leak-free: fully-realized PRIOR days only
                continue
            pnl = float(d.get("profit") or 0.0)
            day_net[day] = day_net.get(day, 0.0) + pnl
            sl = d.get("sleeve")
            if sl:
                day_sleeve.setdefault(day, {})
                day_sleeve[day][sl] = day_sleeve[day].get(sl, 0.0) + pnl
        traded_days = sorted(day_net.keys(), reverse=True)   # most-recent first
        consec = 0
        for day in traded_days:
            if day_net[day] < 0.0:
                consec += 1
            else:
                break                              # a non-loss traded day resets the streak
        span = int(window)
        if _on_challenge_book():
            asked = _scalar(
                "stress_window",
                "The score you return is how many prior traded days this trailing fraction uses. "
                "The recorded window is a fact, not the count. "
                "An empty score leaves the window unset. Do not send.",
                {
                    "traded_days": len(traded_days),
                    "recorded_window": int(window),
                    "login": 0,
                },
            )
            if asked is None:
                span = len(traded_days)
            else:
                span = int(asked)
        fracs: list[float] = []
        for day in traded_days[:span] if span > 0 else []:
            sls = day_sleeve.get(day, {})
            if not sls:
                continue
            neg = sum(1 for v in sls.values() if v < 0.0)
            fracs.append(neg / len(sls))
        neg_frac = (sum(fracs) / len(fracs)) if fracs else 0.0
        return StressDeriskState(consecutive_loss_days=int(consec), trailing_neg_frac=float(neg_frac))
    except Exception:
        return StressDeriskState()

# Cohort A displacement (2026-08-21 Path A). Not in SLEEVE_REGISTRY so --tags ""
# cannot fail-open them. Admission knows them so a later remint cannot
# fail_closed:unknown_sleeve. Distinct cluster ids until T3 Jaccard.
_DSP_FIRST_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")  # US30_cash OFF owner 2026-09-10 0-TP Challenge standdown
DISPLACEMENT_REGISTRY: dict[str, SleeveSpec] = {
    "dsp_climax_flush_to_96low_then_snap": SleeveSpec(
        "dsp_climax_flush_to_96low_then_snap", 0.15, "dsp_c_flush",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 LONG "
        "(geometry.py best_both_halves hold R +0.157); V2 up-rate SHORT was WRONG"),
    "dsp_london_two_up_into_20high_reverses": SleeveSpec(
        "dsp_london_two_up_into_20high_reverses", 0.15, "dsp_c19",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 SHORT "
        "(geometry.py best_both_halves hold R +0.133); V2 up-rate LONG was WRONG"),
    "dsp_expanding_up_staircase": SleeveSpec(
        "dsp_expanding_up_staircase", 0.15, "dsp_c19",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "displacement precondition sweep 2026-08-21; geometry 0.75/6.0 SHORT "
        "(geometry.py best_both_halves hold R +0.146); V2 up-rate LONG was WRONG"),
    "dsp_huge_down_hold_then_spring": SleeveSpec(
        "dsp_huge_down_hold_then_spring", 0.15, "dsp_c_hugespring",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort B 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_already_wide_down_bar_second_wave": SleeveSpec(
        "dsp_already_wide_down_bar_second_wave", 0.15, "dsp_c_wavedown",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort B 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_cascade_last_two_not_yet_four": SleeveSpec(
        "dsp_cascade_last_two_not_yet_four", 0.15, "dsp_c_twonot4",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort B 2026-08-21; geometry 1.0/6.0 SHORT"),
    "dsp_close_on_20low_not_a_cascade_then_up": SleeveSpec(
        "dsp_close_on_20low_not_a_cascade_then_up", 0.15, "dsp_c02",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort E leftover 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_wide_down_then_micro_bounce_then_through": SleeveSpec(
        "dsp_wide_down_then_micro_bounce_then_through", 0.15, "dsp_c_microbounce",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort E leftover 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_isolated_spike_high": SleeveSpec(
        "dsp_isolated_spike_high", 0.15, "dsp_c_isospike",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Cohort E leftover 2026-08-21; geometry 1.0/6.0 SHORT"),
    "dsp_bleed_accept_fresh_20low_second_push": SleeveSpec(
        "dsp_bleed_accept_fresh_20low_second_push", 0.15, "dsp_c_bleed20low",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "DISPREAD 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_walked_high_accepted_through": SleeveSpec(
        "dsp_walked_high_accepted_through", 0.15, "dsp_c_walkhigh",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "DISPREAD 2026-08-21; geometry 1.0/6.0 SHORT"),
    "dsp_small_bar_sit_on_20high_rejects": SleeveSpec(
        "dsp_small_bar_sit_on_20high_rejects", 0.15, "dsp_c_smallsit",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "DISPREAD 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_session_open_already_live": SleeveSpec(
        "dsp_session_open_already_live", 0.15, "dsp_c42",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-B 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_climax_onto_20high_then_fade_london": SleeveSpec(
        "dsp_climax_onto_20high_then_fade_london", 0.15, "dsp_c15",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-B 2026-08-21; geometry 1.0/4.0 LONG"),
    "dsp_climax_onto_20high_then_fade_cashhole": SleeveSpec(
        "dsp_climax_onto_20high_then_fade_cashhole", 0.15, "dsp_c15",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-B 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_expanding_two_bar_run_tokyo": SleeveSpec(
        "dsp_expanding_two_bar_run_tokyo", 0.15, "dsp_c19",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-B 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_high_vol_doji_after_reclaimed_flush_fx": SleeveSpec(
        "dsp_high_vol_doji_after_reclaimed_flush_fx", 0.15, "dsp_c26",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-B 2026-08-21; geometry 1.0/6.0 SHORT"),
    "dsp_weekend_gap_then_bleed_into_20low": SleeveSpec(
        "dsp_weekend_gap_then_bleed_into_20low", 0.15, "dsp_c53",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-A 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_overnight_box_failed_floor_probe": SleeveSpec(
        "dsp_overnight_box_failed_floor_probe", 0.15, "dsp_c38",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-A 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_london_bounce_fails_overnight_midpoint": SleeveSpec(
        "dsp_london_bounce_fails_overnight_midpoint", 0.15, "dsp_c34",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-A 2026-08-21; geometry 1.0/6.0 SHORT"),
    "dsp_first_cash_bar_spike_and_flush": SleeveSpec(
        "dsp_first_cash_bar_spike_and_flush", 0.15, "dsp_c23",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-A 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_two_open_bars_down_then_cascade": SleeveSpec(
        "dsp_two_open_bars_down_then_cascade", 0.15, "dsp_c02",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "UNUSED-A 2026-08-21; geometry 1.0/6.0 LONG"),
    "dsp_isolated_flush_to_20low_snap": SleeveSpec(
        "dsp_isolated_flush_to_20low_snap", 0.15, "dsp_c32",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "weekend leftover 2026-08-22; geometry 1.0/6.0 LONG"),
    "dsp_climax_into_high_then_dump": SleeveSpec(
        "dsp_climax_into_high_then_dump", 0.15, "dsp_c14",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "weekend leftover 2026-08-22; geometry 1.0/6.0 SHORT"),
    "dsp_climax_2atr_onto_20high_then_fade": SleeveSpec(
        "dsp_climax_2atr_onto_20high_then_fade", 0.15, "dsp_c10",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "weekend leftover 2026-08-22; geometry 1.0/6.0 SHORT"),

    # J2B_V2_LEFTOVER_PACK
    "dsp_high_vol_doji_after_reclaimed_flush": SleeveSpec(
        "dsp_high_vol_doji_after_reclaimed_flush", 0.15, "dsp_j2b_high_vol_doji_af",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 1.0/6.0 LONG; hold R +0.078 n 97,528; NOT ARMED"),
    "dsp_two_bar_thrust_into_20high_continues": SleeveSpec(
        "dsp_two_bar_thrust_into_20high_continues", 0.15, "dsp_j2b_two_bar_thrust_i",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.154 n 455,442; NOT ARMED"),
    "dsp_climax_onto_20high_then_fade": SleeveSpec(
        "dsp_climax_onto_20high_then_fade", 0.15, "dsp_j2b_climax_onto_20hi",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.166 n 10,959; NOT ARMED"),
    "dsp_first_crack_failed_reclaim": SleeveSpec(
        "dsp_first_crack_failed_reclaim", 0.15, "dsp_j2b_first_crack_fail",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.103 n 227,002; NOT ARMED"),
    "dsp_three_fresh_lower_lows": SleeveSpec(
        "dsp_three_fresh_lower_lows", 0.15, "dsp_j2b_three_fresh_lowe",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.097 n 1,287,057; NOT ARMED"),
    "dsp_descending_lows_accepted": SleeveSpec(
        "dsp_descending_lows_accepted", 0.15, "dsp_j2b_descending_lows_",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.141 n 954,488; NOT ARMED"),
    "dsp_spring_close_on_20low_through_the_box": SleeveSpec(
        "dsp_spring_close_on_20low_through_the_box", 0.15, "dsp_j2b_spring_close_on_",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.148 n 476,106; NOT ARMED"),
    "dsp_volume_ramp_into_unrepaired_low": SleeveSpec(
        "dsp_volume_ramp_into_unrepaired_low", 0.15, "dsp_j2b_volume_ramp_into",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.087 n 91,056; NOT ARMED"),
    "dsp_small_bar_on_thrust_high": SleeveSpec(
        "dsp_small_bar_on_thrust_high", 0.15, "dsp_j2b_small_bar_on_thr",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.129 n 112,973; NOT ARMED"),
    "dsp_wide_bar_takes_both_extremes_then_reverse": SleeveSpec(
        "dsp_wide_bar_takes_both_extremes_then_reverse", 0.15, "dsp_j2b_wide_bar_takes_b",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.133 n 17,229; NOT ARMED"),
    "dsp_three_bar_squeeze_into_high": SleeveSpec(
        "dsp_three_bar_squeeze_into_high", 0.15, "dsp_j2b_three_bar_squeez",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.119 n 562,152; NOT ARMED"),
    "dsp_isolated_20h_spike_then_fade": SleeveSpec(
        "dsp_isolated_20h_spike_then_fade", 0.15, "dsp_j2b_isolated_20h_spi",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.099 n 106,930; NOT ARMED"),
    "dsp_london_cascade_into_20low_springs": SleeveSpec(
        "dsp_london_cascade_into_20low_springs", 0.15, "dsp_j2b_london_cascade_i",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.101 n 8,652; NOT ARMED"),
    "dsp_rejection_wick_then_through": SleeveSpec(
        "dsp_rejection_wick_then_through", 0.15, "dsp_j2b_rejection_wick_t",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 SHORT; hold R +0.118 n 288,188; NOT ARMED"),
    "dsp_shakeout_holds_run_lows": SleeveSpec(
        "dsp_shakeout_holds_run_lows", 0.15, "dsp_j2b_shakeout_holds_r",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.108 n 94,474; NOT ARMED"),
    "dsp_cascade_two_down_bars_then_third": SleeveSpec(
        "dsp_cascade_two_down_bars_then_third", 0.15, "dsp_j2b_cascade_two_down",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.149 n 29,240; NOT ARMED"),
    "dsp_take_of_low_already_falling_continues": SleeveSpec(
        "dsp_take_of_low_already_falling_continues", 0.15, "dsp_j2b_take_of_low_alre",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.183 n 131,000; NOT ARMED"),
    "dsp_spring_first_print_of_range_low": SleeveSpec(
        "dsp_spring_first_print_of_range_low", 0.15, "dsp_j2b_spring_first_pri",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.085 n 187,864; NOT ARMED"),
    "dsp_reclaim_then_giveback": SleeveSpec(
        "dsp_reclaim_then_giveback", 0.15, "dsp_j2b_reclaim_then_giv",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.153 n 510,938; NOT ARMED"),
    "dsp_accepted_20low_then_second_flush": SleeveSpec(
        "dsp_accepted_20low_then_second_flush", 0.15, "dsp_j2b_accepted_20low_t",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "J2b ALL36 2026-08-21; geometry 0.75/6.0 LONG; hold R +0.167 n 408,059; NOT ARMED"),
    "xa_huge_20_extreme": SleeveSpec(
        "xa_huge_20_extreme", 0.15, "xa_c_huge20",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 LONG"),
    "xa_isolated_opposite": SleeveSpec(
        "xa_isolated_opposite", 0.15, "xa_c_isoopp",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 LONG"),
    "xa_prior_huge": SleeveSpec(
        "xa_prior_huge", 0.15, "xa_c_priorhuge",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 LONG"),
    "xa_climax_spring": SleeveSpec(
        "xa_climax_spring", 0.15, "xa_c_spring20",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 LONG"),
    "xa_wide_extreme": SleeveSpec(
        "xa_wide_extreme", 0.15, "xa_c_wideext",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 SHORT"),
    "xa_second_leg": SleeveSpec(
        "xa_second_leg", 0.15, "xa_c_leg2",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "xasset live generate 2026-08-22; geometry 1.0/6.0 LONG"),
    "xa_huge_same_way": SleeveSpec(
        "xa_huge_same_way", 0.15, "xa_c_hugesame",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Fable M2 2026-09-02 copy; geometry 0.75/6.0 LONG"),
    "xa_second_rth": SleeveSpec(
        "xa_second_rth", 0.15, "xa_c_rth2",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Fable M2 2026-09-02 copy; geometry 0.75/6.0 LONG"),
    "xa_wave_two_standing": SleeveSpec(
        "xa_wave_two_standing", 0.15, "xa_c_wavetwo",
        _DSP_FIRST_SURFACE,
        "forward_only",
        "Fable M2 2026-09-02 copy; geometry 0.75/6.0 LONG"),
}
DISPLACEMENT_NAMES: tuple[str, ...] = tuple(DISPLACEMENT_REGISTRY.keys())

# Corr-cluster map (KB2_true_corr_mc.md: cross-sleeve corr ~0; same-class same-day = ONE unit).
# LOCKED-BOOK map = the 8 core sleeves only (5 cluster ids). The clean_3 sleeves carry NEW
# independent clusters (substrate / volprofile, corr ~0 vs the core per the W5 corr matrix); the
# clean_4 sleeve carries the independent `leadlag` cluster; all resolved via cluster_of(...) from the
# effective registry only when the matching book is enabled.
CLUSTER_OF_SLEEVE: dict[str, str] = {n: s.asset_class for n, s in SLEEVE_REGISTRY.items()}
# Full map including the default-off clean_3 + clean_4 clusters (for the cluster-lookup helper + audit).
CLUSTER_OF_SLEEVE_FULL: dict[str, str] = dict(CLUSTER_OF_SLEEVE)
CLUSTER_OF_SLEEVE_FULL.update({n: s.asset_class for n, s in CLEAN3_REGISTRY.items()})
CLUSTER_OF_SLEEVE_FULL.update({n: s.asset_class for n, s in CLEAN4_REGISTRY.items()})
CLUSTER_OF_SLEEVE_FULL.update({n: s.asset_class for n, s in DISPLACEMENT_REGISTRY.items()})

CANDIDATE_BOOK_PROFILE = "runtime_executable_native_exit_v2"
MARKET_EXPANSION_PROFILE = "default_off_market_expansion_d1_target2_v1"
MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY = "explicit_allowlist"


def candidate_book_registry(candidate_book_sleeves: "Sequence[str] | None" = None) -> dict[str, SleeveSpec]:
    """Default-off runtime-executable candidate sleeves from the research catalog.

    This admits positive-confidence candidates whose native exits are represented by the runtime contract:
    fixed-target, capless no-TP trailing, and targetless no-TP time-stop.
    """
    from .sleeves import candidate_registry as CR
    allowed = {str(s) for s in (candidate_book_sleeves or ()) if str(s)}
    out: dict[str, SleeveSpec] = {}
    for name in CR.RUNTIME_EXECUTABLE_CANDIDATE_NAMES:
        if allowed and name not in allowed:
            continue
        confidence = float(CR.CANDIDATE_CONFIDENCE.get(name, 0.0))
        if confidence <= 0.0:
            continue
        spec = CR.CANDIDATES[name]
        out[name] = SleeveSpec(
            name=name,
            confidence=confidence,
            asset_class=spec.asset_class,
            symbols=tuple(spec.on_surface),
            status=str(CR.CANDIDATE_STATUS.get(name, "promotion_candidate")),
            note=f"{CANDIDATE_BOOK_PROFILE}; {spec.note}",
        )
    return out


WIDEN_ADMISSION_CONFIDENCE: dict[str, float] = {
    "asian_fade_widen": 0.40,          # inherit asian_fade
    "ny_crypto_momentum_widen": 0.35,  # inherit ny_crypto_momentum
    "orb_crypto_london_widen": 0.35,   # inherit orb_crypto_london
}
WIDEN_ADMISSION_CLASS: dict[str, str] = {
    "asian_fade_widen": "fx_reversion",
    "ny_crypto_momentum_widen": "crypto",
    "orb_crypto_london_widen": "crypto",
}
WIDEN_ADMISSION_SYMBOLS: dict[str, tuple[str, ...]] = {
    "asian_fade_widen": ("EURUSD", "GBPUSD"),
    "ny_crypto_momentum_widen": ("BTCUSD", "ETHUSD"),
    "orb_crypto_london_widen": ("BTCUSD", "ETHUSD"),
}


def widen_registry(candidate_book_sleeves: "Sequence[str] | None" = None) -> dict[str, SleeveSpec]:
    """F5 ceremony WIDEN tags. Not in CANDIDATES (MC pin)."""
    allowed = {str(s) for s in (candidate_book_sleeves or ()) if str(s)}
    out: dict[str, SleeveSpec] = {}
    for name, confidence in WIDEN_ADMISSION_CONFIDENCE.items():
        if allowed and name not in allowed:
            continue
        if confidence <= 0.0:
            continue
        out[name] = SleeveSpec(
            name=name,
            confidence=confidence,
            asset_class=WIDEN_ADMISSION_CLASS[name],
            symbols=WIDEN_ADMISSION_SYMBOLS[name],
            status="f5_widen_container_20260825",
            note="F5-only WIDEN beside incumbent; entry identical; OPUS-F5-MAXVALUE section 3",
        )
    return out


def candidate_runtime_blockers() -> dict[str, str]:
    """Positive-confidence candidates still lacking an exact runtime exit contract."""
    from .sleeves import candidate_registry as CR
    return dict(CR.CANDIDATE_RUNTIME_BLOCKERS)


def market_expansion_conditioned_policies() -> dict[str, tuple[str, ...]]:
    """Audited default-off market-expansion policy aliases from the conditioned sizing route."""
    from .sleeves import candidate_registry as CR
    return dict(CR.MARKET_EXPANSION_CONDITIONED_POLICIES)


def market_expansion_conditioned_policy_metadata() -> dict[str, dict[str, object]]:
    """Audited conditioned policy metrics for bridge/config descriptions."""
    from .sleeves import candidate_registry as CR
    return dict(CR.MARKET_EXPANSION_CONDITIONED_POLICY_METADATA)


def resolve_market_expansion_sleeves(
    *,
    policy: str | None,
    explicit_sleeves: "Sequence[str] | None" = None,
) -> "tuple[tuple[str, ...], str | None]":
    """Resolve a market-expansion policy into an exact sleeve allowlist.

    `explicit_allowlist` preserves the original safety contract: include=true with no sleeves fails
    closed. Named conditioned policies are auditable aliases for exact committed allowlists. If an
    operator supplies both a named policy and an explicit list, the list must match the policy set or
    the bridge fails closed instead of guessing.
    """
    raw = tuple(str(s) for s in (explicit_sleeves or ()) if str(s))
    policy_name = str(policy or MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY)
    if policy_name == MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY:
        return raw, None
    policies = market_expansion_conditioned_policies()
    selected = policies.get(policy_name)
    if selected is None:
        return (), f"unknown_market_expansion_policy:{policy_name}"
    if raw and set(raw) != set(selected):
        return (), f"market_expansion_policy_sleeve_mismatch:{policy_name}"
    return tuple(selected), None


def market_expansion_registry(
    market_expansion_sleeves: "Sequence[str] | None" = None,
) -> dict[str, SleeveSpec]:
    """Default-off market-expansion D1 runtime-capable sleeves.

    Unlike the candidate-book registry, market expansion never treats an empty allowlist as "all".
    The bridge also fail-closes include=true with an empty allowlist. This registry-level behavior is
    a second safety layer for internal callers.
    """
    from .sleeves import candidate_registry as CR
    allowed = {str(s) for s in (market_expansion_sleeves or ()) if str(s)}
    if not allowed:
        return {}
    out: dict[str, SleeveSpec] = {}
    for name in sorted(allowed):
        spec = CR.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.get(name)
        if spec is None:
            continue
        if spec.design_status != "default_off_spec_design_ready":
            continue
        if not spec.symbol_collision_winner:
            continue
        confidence = float(spec.candidate_seed_weight)
        if confidence <= 0.0 or spec.activation_weight_now != 0.0:
            continue
        out[name] = SleeveSpec(
            name=name,
            confidence=confidence,
            asset_class=spec.family,
            symbols=(spec.file_symbol,),
            status="default_off_runtime_capable_zero_activation",
            note=f"{MARKET_EXPANSION_PROFILE}; target2 D1 next-open; {spec.note}",
        )
    return out


def cluster_of(sleeve: str, registry: Mapping[str, SleeveSpec] | None = None) -> str | None:
    """Resolve the corr-cluster id for a sleeve; None if unknown."""
    if registry is not None and sleeve in registry:
        return registry[sleeve].asset_class
    if sleeve in CLUSTER_OF_SLEEVE_FULL:
        return CLUSTER_OF_SLEEVE_FULL[sleeve]
    spec = candidate_book_registry().get(sleeve)
    if spec is not None:
        return spec.asset_class
    spec = widen_registry().get(sleeve)
    if spec is not None:
        return spec.asset_class
    from .sleeves import candidate_registry as CR
    expansion_spec = CR.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.get(sleeve)
    return None if expansion_spec is None else expansion_spec.family


def filter_w7_dropped_symbols(
    intents: "Sequence[TradeIntent]", *, enabled: bool = True,
) -> "tuple[list[TradeIntent], tuple[str, ...]]":
    """Drop intents on the WAVE-7 tick-true illiquid symbols (HEATOIL_c, NATGAS_cash).

    The runtime bridge calls this BEFORE sizing so the deployed candidate stream matches the W7 final
    book (whose modeled EV on these two energy legs was a cost-map artifact; real spread swamps the
    stop). Returns (kept_intents, dropped_symbol_tuple). Leak-free, pure-data, no broker work.
    When enabled=False this is a no-op (returns the input unchanged) for the locked pre-W7 book.
    """
    if not enabled:
        return list(intents), ()
    kept: list[TradeIntent] = []
    dropped: list[str] = []
    for it in intents:
        if it.symbol in W7_DROPPED_SYMBOLS and _admission_blocks(
            "w7_dropped_symbol", {"symbol": str(it.symbol)}
        ):
            dropped.append(it.symbol)
        else:
            kept.append(it)
    return kept, tuple(sorted(set(dropped)))


def effective_registry(
    include_clean3: bool = False,
    include_clean4: bool = False,
    include_candidate_book: bool = False,
    candidate_book_sleeves: "Sequence[str] | None" = None,
    include_market_expansion_book: bool = False,
    market_expansion_sleeves: "Sequence[str] | None" = None,
) -> dict[str, SleeveSpec]:
    """Return the active sleeve registry. Default = locked 8-sleeve book (clean_3/clean_4 OFF).

    The owner enables the Wave-5 clean_3 additive sleeves at go-live by passing include_clean3=True,
    and the Wave-6 clean_4 additive sleeve (session_leadlag_genuine) by include_clean4=True (which
    implies clean_3). Candidate-book v1 is a separate default-off runtime-executable promotion layer.
    """
    reg = dict(SLEEVE_REGISTRY)
    # GROK_KEEP_ACTIVATE_20260920: research drafts (EUR+NZD proxies) always admitted when registered
    reg.update(RESEARCH_DRAFT_SLEEVE_REGISTRY)
    if include_clean3 or include_clean4:
        reg.update(CLEAN3_REGISTRY)
    if include_clean4:
        reg.update(CLEAN4_REGISTRY)
    if include_candidate_book:
        reg.update(candidate_book_registry(candidate_book_sleeves))
        reg.update(widen_registry(candidate_book_sleeves))
    if include_market_expansion_book:
        reg.update(market_expansion_registry(market_expansion_sleeves))
    return reg

# ===========================================================================================
# 2. ALLOCATION PROFILES â€” the 2-account live config (PORTFOLIO_BUILD_W2.md Section 7).
# ===========================================================================================
@dataclass(frozen=True)
class AllocationProfile:
    name: str
    risk_per_unit_A: float
    risk_per_unit_B: float
    base_p_both: float          # documented MC P(pass both) base
    fwd_p_both: float
    stress15_p_both: float
    note: str

ALLOCATION_PROFILES: dict[str, AllocationProfile] = {
    # RECOMMENDED live default (PORTFOLIO_BUILD_W2.md Section 7).
    "balanced_0p75": AllocationProfile(
        "balanced_0p75", 0.0075, 0.0075, 0.9993, 1.0000, 0.747,
        "RECOMMENDED live default: both accounts full 8-sleeve book @ 0.75%/unit"),
    # capital-protection variant (most robust on stress).
    "conservative_0p50": AllocationProfile(
        "conservative_0p50", 0.0050, 0.0050, 1.0000, 1.0000, 0.837,
        "capital-protection variant: both accounts @ 0.50%/unit (best stress survivability)"),
    "staggered_1p00_0p50": AllocationProfile(
        "staggered_1p00_0p50", 0.0100, 0.0050, 0.9970, 0.9997, 0.633,
        "staggered A1.00%/B0.50% (offered; strictly dominated on stress by symmetric pairs)"),
    # WAVE-5 clean_3 deploy profile (INTEG_W5_CLEAN3_DEPLOY.json two_account balanced_A0.75_B0.75).
    # Sizes are the VOL-MATCHED EFFECTIVE risk (0.75% nominal x vol_scale 0.948 = 0.711% effective):
    # diversification is banked as a higher pass-rate floor, NOT bigger bets. Use with include_clean3.
    "clean3_balanced_eff0p71": AllocationProfile(
        "clean3_balanced_eff0p71", round(0.0075 * CLEAN3_VOL_SCALE, 6),
        round(0.0075 * CLEAN3_VOL_SCALE, 6), 0.9999, 1.0000, 0.7030,
        "RECOMMENDED clean_3 live default: both accounts full 11-sleeve deploy book at the "
        "vol-matched effective 0.71%/unit (0.75% nominal x vol_scale 0.948); P(both)=99.99% base, "
        "70.30% under adversarial 1.5x stress, 0% daily-breach"),
    "clean3_conservative_eff0p47": AllocationProfile(
        "clean3_conservative_eff0p47", round(0.0050 * CLEAN3_VOL_SCALE, 6),
        round(0.0050 * CLEAN3_VOL_SCALE, 6), 1.0000, 1.0000, 0.7951,
        "clean_3 capital-protection variant: 0.47%/unit effective (max stress safety 79.51% under "
        "1.5x stress); use for the first live challenge cycle, step up to balanced after clearing"),
    # KB7 GROWTH-OPTIMAL clean_3 profiles (KB7_growth_kelly_sizing.md / KB7_GROWTH_KELLY_RESULT.json +
    # KB7_growth_kelly_v2.py hardening). The owner OBJECTIVE on the UNLEASH wave is MAX speed-to-+8%
    # s.t. an ACCEPTABLE P(maxDD-breach), NOT minimal size. Daily-breach is mechanically 0% up to 2.5%
    # eff (worst historical day inside -5%); the BINDING rule is the 1.5x-left-tail stress maxDD-fail.
    # Growth-optimal knee = 1.50% nominal (1.42% eff vol-matched): all-history pass 98.5%, forward
    # 99.3%, ~60-day median pass (HALVES the 0.71%-deploy's ~120d), stress maxDD-fail 29.1% FLAT.
    # PAIR WITH the Kelly-lite conviction multiplier (kelly_lite_conviction_multiplier): at EQUAL vol
    # it cuts stress maxDD-fail 29.1%->16.1% (handset) and 2025/2026 both improve (no single-regime),
    # so 1.5%+Kelly carries the tail of flat ~1.25% with the speed of flat ~1.6%.
    "clean3_growth_eff1p42": AllocationProfile(
        "clean3_growth_eff1p42", round(0.015 * CLEAN3_VOL_SCALE, 6),
        round(0.015 * CLEAN3_VOL_SCALE, 6), 0.987, 0.994, 0.577,
        "KB7 GROWTH-OPTIMAL clean_3 default for max speed-to-target: 1.42%/unit effective (1.50% "
        "nominal x vol_scale 0.948). Single-acct all-history pass 98.5%, forward 99.3%, ~60d median, "
        "stress maxDD-fail 29.1% flat (16.1% with Kelly-lite at equal vol); 2-acct balanced P(both) "
        "base 98.7% / stress 57.7% flat. Enable kelly_lite=True for the confidence-proportional tilt"),
    "clean3_aggressive_eff1p66": AllocationProfile(
        "clean3_aggressive_eff1p66", round(0.0175 * CLEAN3_VOL_SCALE, 6),
        round(0.0175 * CLEAN3_VOL_SCALE, 6), 0.972, 0.985, 0.545,
        "KB7 AGGRESSIVE clean_3 (owner ceiling): 1.66%/unit effective (1.75% nominal). ~51d median "
        "pass single-acct, all-history 97.5%, forward 98.5%; HARD CEILING per account â€” 2.0% trips a "
        "daily-breach on hot conviction days under Kelly-lite. Use only with kelly_lite + stress_derisk"),
    # GO-LIVE FIRST-CYCLE dial (owner-chosen 2026-06-15): 1.25% nominal half-Kelly,
    # the daily-breach-free-even-under-1.5x-stress sweet spot per PORTFOLIO_BUILD_W7_FINAL.md Â§3a/Â§6.
    # 1.25% nominal x vol_scale 0.9481 = 1.185% effective. Single-acct P(pass) 99.36%,
    # P(maxDD) 0.65%, str15 maxDD-fail 20.9%, ~79 median days (vs ~119 at the old 0.75%).
    # PAIR WITH kelly_lite=True, kelly_conservative=True (half-Kelly bins are breach-free
    # even under stress at this dial). Step to clean3_growth_eff1p42 (1.5%) after the
    # first account clears; ceiling clean3_aggressive_eff1p66 capped at 2.0% nominal.
    "clean3_firstcycle_eff1p18": AllocationProfile(
        "clean3_firstcycle_eff1p18", round(0.0125 * CLEAN3_VOL_SCALE, 6),
        round(0.0125 * CLEAN3_VOL_SCALE, 6), 0.9936, 0.9919, 0.637,
        "GO-LIVE FIRST CYCLE (owner dial): 1.185%/unit effective (1.25% nominal x vol_scale "
        "0.948). Single-acct P(pass) 99.36%, P(maxDD) 0.65%, ~79d median; 2-acct balanced "
        "P(both) base 99.28% / stress 63.7%; daily-breach 0% even under 1.5x stress. Use with "
        "kelly_lite=True + kelly_conservative=True (half-Kelly) + stress_derisk=True"),
    # WAVE-6 clean_4 deploy profiles (clean_3 + session_leadlag_genuine, re-vol-matched at
    # vol_scale 0.9873). The +195 tr/yr genuine cross-asset lead sleeve RAISES the stress floor:
    # the folded book lifts stress@1% 80.86%->82.24% and Sharpe 0.1522->0.1586. Effective risk is
    # 0.75% nominal x 0.9873 = 0.74% (vs clean_3's 0.71%) because the extra orthogonal breadth lets
    # the fair vol-match run slightly hotter. Use with include_clean4=True (implies clean_3).
    "clean4_balanced_eff0p74": AllocationProfile(
        "clean4_balanced_eff0p74", round(0.0075 * CLEAN4_VOL_SCALE, 6),
        round(0.0075 * CLEAN4_VOL_SCALE, 6), 0.9998, 1.0000, 0.7234,
        "RECOMMENDED clean_4 live default: full 12-sleeve deploy book (clean_3 + "
        "session_leadlag_genuine) at vol-matched effective 0.74%/unit; the genuine session-lead "
        "sleeve raises the stress floor (book stress@1% 80.86%->82.24%, @1.5% 70.93%->72.06%)"),
    "clean4_conservative_eff0p49": AllocationProfile(
        "clean4_conservative_eff0p49", round(0.0050 * CLEAN4_VOL_SCALE, 6),
        round(0.0050 * CLEAN4_VOL_SCALE, 6), 1.0000, 1.0000, 0.8010,
        "clean_4 capital-protection variant: 0.49%/unit effective; max stress safety; use for the "
        "first live challenge cycle, step up to balanced after clearing"),
    # ===========================================================================================
    # WAVE-7 FINAL DEPLOY DIALS (owner-chosen NOMINAL sizing; clean_3 11-sleeve W7 final book).
    # Source of truth: PORTFOLIO_BUILD_W7_FINAL.md Section 3 + INTEG_W7_FINAL_RESULT.json
    # (two_account_final) + ULTIMATE_GO_LIVE_DOSSIER.md Section 0-W7.
    #
    # CONVENTION DIFFERENCE vs the W5 clean3_* profiles above: the W7 dials carry the OWNER-CHOSEN
    # NOMINAL risk per unit DIRECTLY (0.0125 / 0.015 / 0.020), NOT a pre-multiplied vol-scaled
    # effective. In the W7 final book the volatility reshape is the KELLY-LITE conviction multiplier,
    # which the deployable path applies as a RUNTIME multiplier in size_correlated_units (kelly_lite=
    # True). So: deploy these profiles WITH include_clean3=True AND kelly_lite=True so the realized
    # per-unit risk equals (nominal x sleeve_conf x kelly_mult), matching the locked W7 MC where the
    # Kelly-folded series was vol-matched at VS_final=0.7504. The two-account stats below are the
    # LOCKED INTEG_W7_FINAL_RESULT two_account_final balanced pairs (P(both) base / fwd / 1.5x-stress).
    #
    # FIRST CYCLE (owner): 1.25% nominal + half-Kelly (kelly_conservative=True) -> daily-breach-free
    # even under 1.5x stress, P(pass) 99.4% single / P(both) 99.28% base. STEP after the first account
    # clears: 1.50% nominal + handset Kelly + reactive stress_derisk overlay. HARD CEILING: 2.00%.
    # ===========================================================================================
    "clean3_w7_measured_nom1p25": AllocationProfile(
        "clean3_w7_measured_nom1p25", 0.0125, 0.0125, 0.9928, 0.9919, 0.637,
        "WAVE-7 FIRST-CYCLE dial (owner default): 1.25% NOMINAL per unit, clean_3 11-sleeve W7 final "
        "book. Deploy WITH include_clean3=True + kelly_lite=True + kelly_conservative=True (half-Kelly). "
        "2-acct balanced P(both) base 99.28% / fwd 99.19% / 1.5x-stress 63.7%; daily-breach 0%. Step "
        "to clean3_w7_growth_nom1p50 after the first account clears (ULTIMATE_GO_LIVE_DOSSIER 0-W7)"),
    "clean3_w7_growth_nom1p50": AllocationProfile(
        "clean3_w7_growth_nom1p50", 0.015, 0.015, 0.9852, 0.9837, 0.5971,
        "WAVE-7 GROWTH-OPTIMAL dial: 1.50% NOMINAL per unit, clean_3 W7 final book. Deploy WITH "
        "include_clean3=True + kelly_lite=True (handset) + stress_derisk=True (reactive ladder+coloss). "
        "2-acct balanced P(both) base 98.52% / fwd 98.37% / 1.5x-stress 59.71%; daily-breach 0%; "
        "~66 median days-to-+8% (~1.8x faster than the 0.75% fear-distilled deploy)"),
    "clean3_w7_ceiling_nom2p00": AllocationProfile(
        "clean3_w7_ceiling_nom2p00", 0.020, 0.020, 0.9553, 0.9562, 0.5021,
        "WAVE-7 HARD CEILING dial (owner max-aggression, NOT a default): 2.00% NOMINAL per unit, "
        "clean_3 W7 final book. ONLY with include_clean3=True + kelly_lite=True + stress_derisk=True. "
        "2-acct P(both) base 95.53% / fwd 95.62% / 1.5x-stress 50.21%; daily-breach still 0%; "
        "~49 median days. Do not exceed 2.0%/account (Kelly-lite hot days can graze -5% above this)"),
}
DEFAULT_PROFILE = "balanced_0p75"
# the recommended profile once the owner enables the Wave-5 additive deploy book (include_clean3=True)
CLEAN3_DEFAULT_PROFILE = "clean3_balanced_eff0p71"
# the recommended profile once the owner enables the Wave-6 additive deploy book (include_clean4=True)
CLEAN4_DEFAULT_PROFILE = "clean4_balanced_eff0p74"
# WAVE-7 final-book dials (owner NOMINAL sizing; deploy WITH include_clean3=True + kelly_lite=True).
CLEAN3_W7_FIRST_CYCLE_PROFILE = "clean3_w7_measured_nom1p25"   # 1.25% nominal half-Kelly (owner default)
CLEAN3_W7_GROWTH_PROFILE = "clean3_w7_growth_nom1p50"          # 1.50% nominal handset-Kelly (after clear)
CLEAN3_W7_CEILING_PROFILE = "clean3_w7_ceiling_nom2p00"        # 2.00% nominal hard ceiling
# WAVE-7 tick-true execution: these two illiquid energy legs are DROPPED from candidate generation
# (their modeled EV was a cost-map artifact; real spread swamps the stop). The energy_agri sleeve
# universe above now PHYSICALLY excludes them (USOIL/UKOIL/CORN/COTTON only); the runtime bridge MUST
# also filter intents on these symbols (filter_w7_dropped_symbols) for any other sleeve. Alias of the
# canonical ENERGY_DROPPED_SYMBOLS (section 0b). Source: KB7_execution_truth.md + PORTFOLIO_BUILD_W7_FINAL.md T2.
W7_DROPPED_SYMBOLS: frozenset[str] = ENERGY_DROPPED_SYMBOLS

# Governor limits (KB_architecture_spec.md Section 3.2/3.3 + KB2_true_corr_mc.md Section 4).
@dataclass(frozen=True)
class GovernorLimits:
    soft_daily_stop_pct: float = 0.03      # stop opening NEW units at -3% intraday (hard limit -5%)
    hard_daily_limit_pct: float = FTMO_DAILY
    max_dd_limit_pct: float = FTMO_MAXDD
    # Optional earlier entry-side buffer before the prop-fatal max-DD wall. Defaults to max_dd_limit_pct
    # for backward compatibility; live config sets 0.09 so new entries stop before breach-flatten territory.
    max_dd_entry_block_pct: float = FTMO_MAXDD
    derisk_start_dd_pct: float = 0.07      # begin multiplicative size shrink as DD approaches the wall
    gross_open_risk_cap_pct: float = 0.04  # cap same-day deployed worst-case stop risk (>4x headroom)
    # de-risk shape as equity approaches the -10% wall. "band" = current live (full size to derisk_start_dd,
    # then linear to 0 at the wall). "smooth" = proportional de-risk from dd=0 (risk*=1-dd_frac); research
    # c59/c61 on the REAL W7 book shows smooth holds total-DD-fail ~0 at a higher base -> faster AND safer
    # passes. Opt-in only; DEFAULT_LIMITS reads GTOS_UB_DERISK_MODE (defaults to "band" = no behavior change).
    derisk_mode: str = "band"
    # worst single book-day in 1,598 days is -1.491 unit-R -> at 0.75% that is -1.12% (PORTFOLIO_BUILD_W2 S6)
    # OPS-03 PROFIT-TARGET PROTECT: once equity is >= initial_balance*(1+profit_target_pct) the challenge
    # target is effectively passed; shrink NEW-entry size by profit_target_derisk_mult to LOCK IN the pass
    # while staying in the market (owner policy: de-risk hard, keep trading). 0 disables (no target logic).
    profit_target_pct: float = 0.0
    profit_target_derisk_mult: float = 0.25
DEFAULT_LIMITS = GovernorLimits(derisk_mode=os.environ.get("GTOS_UB_DERISK_MODE", "band"))


# ===========================================================================================
# 3. CONFIDENCE-WEIGHTED CORRELATED-RISK-UNIT SIZER
#    A "candidate" is one sleeve firing on a decision-day for a symbol. Same sleeve-class same day
#    collapse into ONE correlated unit (split equally). Cross-class units are independent.
# ===========================================================================================
@dataclass(frozen=True)
class TradeIntent:
    """A single candidate trade intent emitted by a sleeve generator (no outcome fields).

    Overlay-condition fields are PURE FACTS observed at the decision bar (leak-free, index<=i):
      ll_impulse      : cross-asset leader-impulse tag ('none' if no relevant leader >=1.5sigma).
      decision_hour   : H4 server hour of the decision bar (for the session-active stack).
      vp_loc          : prior-day volume-profile location tag ('above_va' enables the W6 VP-acceptance
                        exit-honest refinement of sub_mid_dn_revert; non-above_va is DROPPED when
                        vp_acceptance=True).
    They are advisory inputs to the confluence SIZE-UP selectors; absent (None) -> no size-up.
    """
    sleeve: str
    symbol: str
    direction: int            # +1 long / -1 short
    decision_day: str         # ISO date string (the decision bar's date)
    stop_dist: float          # PRICE distance to structural stop (R-unit), > 0
    target_dist: float | None = None
    intra_size: float = 1.0   # intra-sleeve confidence ramp (softband / agri conf), default 1.0
    ll_impulse: str | None = None   # leader-impulse tag ('none' enables the leader_impulse_veto size-up)
    decision_hour: int | None = None  # H4 decision-bar server hour (enables session_active_stack size-up)
    vp_loc: str | None = None  # prior-day volume-profile location ('above_va' = W6 VP-acceptance keep)
    # A8 metals entry-quality CONFLUENCE features (leak-free decision-bar facts, all index<=i). Populated
    # by the metals generator when the A8 gate is deployed; None => the gate cannot evaluate this intent
    # and ADMITS it as today (the deploy-phase generator change to populate these is what arms the gate).
    htf_slope_norm: float | None = None    # higher-TF slope (UP_REGIME: >0 with mom_20_atr>0)
    mom_20_atr: float | None = None        # 20-bar momentum / ATR (UP_REGIME)
    fvg_freshness_bars: float | None = None  # bars since the FVG formed (FRESH: <=5)
    atr_ratio: float | None = None         # current/ref ATR (VOL_CAP: <1.8)
    session_hour: int | None = None        # decision-bar session hour (ASIAN: 0..6)
    # WAVE-11 vol-level sizing tilt input (Session AR). The decision bar's `vr` â€” ATR(14) over
    # its own 100-bar mean, `primitives.vol_ratio` / `substrate_engine.compute_state`'s `vr`.
    # Populated by the substrate generator, which already computes it to decide whether to fire
    # at all, so it costs no work and cannot leak (index<=i by construction). None on every
    # other sleeve => the tilt is a no-op there. See VOL_LEVEL_TILT below.
    vr: float | None = None
    # T4 native limit-entry rail (default OFF). None on every existing sleeve => the live
    # DEAL path is byte-identical. `entry_price` is the only switch that arms BUY_LIMIT /
    # SELL_LIMIT via TRADE_ACTION_PENDING. `entry_offset_atr` is reserved for half-two
    # (non-zero offset after a measured fill rate) and is never applied here. `expiry_bars`
    # arms cancel-on-expiry in manage_open_positions; None means no auto-cancel.
    entry_offset_atr: float | None = None
    entry_price: float | None = None
    expiry_bars: int | None = None
    unit_choice: str | None = None


# WAVE-11 vol-LEVEL sizing tilt (Session AR, default-OFF): `vol_level_tilt_for` and the
# VOL_LEVEL_TILT_* constants live at the END of this module, deliberately. They are a
# 60-line block and this file is cited by `file:line` from ~60 places in live code; putting
# a long comment HERE would have shifted every citation below it by 80+ lines. Kept out of
# the middle so an edit to a default-off feature does not invalidate the estate's citations.
_SCORE_CACHE: dict[str, float | None] = {}


def _admit_score(role: str, instructions: str, facts: dict) -> float | None:
    """One score for this role and these facts. The nineteen import stays.

    The same facts reuse the return. An empty score stays empty.
    """
    try:
        key = role + "|" + json.dumps(facts, sort_keys=True, default=str)
    except TypeError:
        key = role + "|" + str(facts)
    if key in _SCORE_CACHE:
        return _SCORE_CACHE[key]
    try:
        from src.judgment.nineteen import score
        number = score(facts, question_id=role, instructions=instructions)
    except Exception:
        number = None
    if number is not None:
        try:
            number = float(number)
        except (TypeError, ValueError):
            number = None
    _SCORE_CACHE[key] = number
    return number


def overlay_sizeup_for(intent: "TradeIntent", *, overlays: bool = True) -> tuple[float, tuple[str, ...]]:
    """Combined size-up. Each multiple and the cap are scores. An empty score does not apply 1.5 or 1.75."""
    if not overlays:
        return 1.0, ()
    mult = 1.0
    applied: list[str] = []
    for name, ov in CONFLUENCE_OVERLAYS.items():
        if intent.sleeve not in ov.base_sleeves:
            continue
        if name == "leader_impulse_veto" and intent.ll_impulse != LEADER_IMPULSE_NONE:
            continue
        if name == "session_active_stack" and intent.decision_hour is None:
            continue
        sizeup = _admit_score(
            "overlay_sizeup",
            "The score you return is the size-up multiple for this overlay. "
            "An empty score leaves this overlay unset. Do not send.",
            {
                "overlay": name,
                "sleeve": intent.sleeve,
                "hour": getattr(intent, "decision_hour", None),
                "ll_impulse": getattr(intent, "ll_impulse", None),
            },
        )
        if sizeup is None:
            continue
        mult *= sizeup
        applied.append(name)
    cap = _admit_score(
        "overlay_sizeup_cap",
        "The score you return is the cap on this combined size-up. "
        "An empty score leaves the product uncapped. Do not send.",
        {"sleeve": intent.sleeve},
    )
    if cap is None:
        return mult, tuple(applied)
    return min(mult, cap), tuple(applied)


# ===========================================================================================
# 1g. KB7 KELLY-LITE CONFIDENCE-PROPORTIONAL DAY-LEVEL MULTIPLIER (default-OFF; UNLEASH wave).
#     Source: KB7_growth_kelly_sizing.md / KB7_GROWTH_KELLY_RESULT.json + KB7_growth_kelly_v2.py.
#     A leak-free per-DAY conviction signal: the COUNT of INDEPENDENT sleeves firing that day
#     (known at decision time, BEFORE sizing). Forward-validated monotone (FWD meanR: n_active=1
#     +0.12R, 2-3 +0.15R, >=4 +0.61R; corr(n_active,R) all +0.279 fwd +0.203; perm-null p=0.0006).
#     This is the textbook confidence-proportional / Kelly-lite rule: bet BIGGER on multi-edge-
#     agreement days, smaller on marginal single-edge days. It is a LEARNED-FREE step function whose
#     bins match the conditional Kelly fraction f*_bucket/f*_base = {0.50, 0.98, 1.48} (the principled
#     derivation), DEPLOYED at the slightly tamer hand-set {0.85, 1.10, 1.60} for a smoother bottom
#     bucket. At EQUAL vol it cuts the binding 1.5x-stress maxDD-fail 29.1%->16.1% @1.5% (both 2025
#     and 2026 improve -> NOT single-regime), for ~+4 days of median pass.
#
#     COMPOSES with the per-sleeve conf, intra_size, the confluence overlays, and the SHRINK-ONLY
#     reactive stress-de-risk overlay; the COMBINED size-up is capped at OVERLAY_SIZEUP_MAX (1.75)
#     so a single risk unit never exceeds the worst-case daily/maxDD cap.
#
#     HONESTY CAVEAT (documented, required): the strongest tier (>=4 -> 1.6) is forward-validated
#     2/2 yrs + null-cleared but TRAIN-THIN (only 3 such days exist <=2024, because fx_jpy_ny /
#     vp_euidx / sub_xvol came online mid-2025). The 2-3 tier IS train-validated (+0.134 train).
#     Treat the top tier as forward-conditional; re-confirm as the forward window grows. The
#     PRINCIPLED-HALF variant (bottom 0.748) is the breach-free conservative form (no daily-breach
#     even at 2x deep-stress); the hand-set top 1.6 can graze the -5% wall on the single worst
#     n_active=7 correlated-loss day when inflated 1.5x (-5.28%) -> the shrink-only stress_derisk
#     overlay + the -3% soft daily stop are the live guards that neutralize it. Default-OFF; the owner
#     enables kelly_lite=True at go-live with the growth profile.
# ===========================================================================================
# Hand-set deploy bins (n_active_lo, n_active_hi) -> day-level size multiplier (matches the validated
# conditional-Kelly monotonicity; capped at OVERLAY_SIZEUP_MAX in the combine step).
KELLY_LITE_BINS: tuple[tuple[int, int, float], ...] = ((1, 1, 0.85), (2, 3, 1.10), (4, 99, 1.60))
# Breach-free conservative (half-Kelly damped) bins for the cautious deploy / first live cycle.
KELLY_LITE_BINS_HALF: tuple[tuple[int, int, float], ...] = ((1, 1, 0.748), (2, 3, 0.991), (4, 99, 1.241))


def kelly_lite_conviction_multiplier(
    n_active_sleeves_today: int, *, enabled: bool = False, conservative: bool = False,
) -> float | None:
    """Leak-free day-level confidence-proportional (Kelly-lite) size multiplier.

    `n_active_sleeves_today` = number of INDEPENDENT deploy sleeves with a firing signal that day,
    KNOWN at decision time before sizing (count of non-zero contributions). Returns a multiplier on
    the day's base risk; >=1.0 on high-conviction multi-edge days, <1.0 on marginal single-edge days.
    DEFAULT-OFF (enabled=False -> 1.0). `conservative=True` uses the breach-free half-Kelly bins.

    The returned value is NOT capped here; it is composed with the confluence overlays in the sizing
    path and the COMBINED size-up is capped at OVERLAY_SIZEUP_MAX so the unit risk stays governor-safe.
    """
    if not enabled:
        return 1.0
    na = int(n_active_sleeves_today)
    if _on_challenge_book():
        asked = _scalar(
            "kelly_lite",
            "The score you return is the day-level size multiplier for this count of firing sleeves. "
            "The recorded bins are facts, not the multiplier. "
            "An empty score leaves the multiplier unset. Do not send.",
            {
                "n_active": na,
                "conservative": bool(conservative),
                "recorded_bins": [list(row) for row in (KELLY_LITE_BINS_HALF if conservative else KELLY_LITE_BINS)],
                "login": 0,
            },
        )
        return None if asked is None else float(asked)
    bins = KELLY_LITE_BINS_HALF if conservative else KELLY_LITE_BINS
    for lo, hi, m in bins:
        if lo <= na <= hi:
            return m
    return 1.0


@dataclass
class SizedUnit:
    cluster: str
    sleeve_members: tuple[str, ...]
    n_trades: int
    confidence: float | None   # effective unit confidence (max over members incl. overlay size-up)
    risk_pct_per_trade: float | None  # equity % risked on each trade in this unit
    unit_risk_pct: float | None       # total worst-case-stop equity % for this correlated unit
    sized: bool
    reason: str
    overlays_applied: tuple[str, ...] = ()  # confluence size-up selectors that fired on this unit


def _is_known_sleeve(name: str, registry: Mapping[str, SleeveSpec] = SLEEVE_REGISTRY) -> bool:
    return name in registry


def confidence_for(sleeve: str, registry: Mapping[str, SleeveSpec] = SLEEVE_REGISTRY) -> float | None:
    """Registry weight off Challenge. On Challenge the score is the weight.

    An empty score does not restore the stored SleeveSpec weight.
    """

    spec = registry.get(sleeve)
    stored = None if spec is None else spec.confidence
    if not _on_challenge_book():
        return 0.0 if stored is None else float(stored)
    return _admit_score(
        "sleeve_confidence",
        "The score you return is this sleeve's confidence weight on this state. "
        "The registry weight is a fact, not the decision. "
        "An empty score leaves the weight unset. Do not send.",
        {"sleeve": sleeve, "registry_confidence": stored},
    )


# ===========================================================================================
# 1h. LEARNING ACTUATOR + A8 CONFLUENCE GATE wiring (both DEFAULT-OFF; owner-armed).
#     learning_rerate: a {sleeve: confidence_multiplier} map from learning_actuator.rerate_book(...)
#       on the deep-history every-split evidence (L1_ADJUDICATION_COMPLETE_RESULT.json). It closes
#       live-limitation L5 â€” the live edge_reconciler only MEASURES + warns (brake-only); this map
#       lets the owner ACTUATE the per-sleeve re-rating: GATE a non-edge (mult 0.0 -> the sleeve's
#       intents are DROPPED), DOWN_WEIGHT a soft-negative (0.5), KEEP/HOLD (1.0), or modest bounded
#       SIZE_UP a validated sleeve (<=LEARNING_RERATE_MAX). Multipliers are clamped defensively to
#       [0, LEARNING_RERATE_MAX] (== the actuator's own MAX_UP). None => no-op (byte-identical to today).
#     metals_confluence_gate: when True, DROP metals_core/metals_softband intents that CARRY the A8
#       confluence features and fail the verified K=3-of-4 (verify_confluence_book_gate.py sleeve-Sharpe
#       Pareto filter). Intents NOT carrying the features are ADMITTED as today â€” populating
#       htf_slope_norm/mom_20_atr/fvg_freshness_bars/atr_ratio/session_hour in the metals generator is
#       the deploy-phase task that ARMS the gate; the full-W7-book MC remains the owner-gated step (c82).
# ===========================================================================================
LEARNING_RERATE_MAX = 1.25  # defensive clamp on a learning per-sleeve confidence multiplier (== actuator MAX_UP)
A8_CONFLUENCE_SLEEVES = frozenset({"metals_core", "metals_softband"})  # the metals sleeves the A8 gate filters


def _metals_confluence_pass(it: "TradeIntent") -> "bool | None":
    """A8 K=3-of-4 confluence verdict for one metals intent. None => features absent (cannot evaluate)."""
    if it.sleeve not in A8_CONFLUENCE_SLEEVES:
        return True   # not an A8-gated metals sleeve -> the gate does not apply (admit)
    feats = (it.htf_slope_norm, it.mom_20_atr, it.fvg_freshness_bars, it.atr_ratio, it.session_hour)
    if any(f is None for f in feats):
        return None   # deploy-phase generator has not populated the features yet -> admit-as-today
    from .metals_confluence_gate import metals_confluence
    return metals_confluence(htf_slope_norm=it.htf_slope_norm, mom_20_atr=it.mom_20_atr,
                             fvg_freshness_bars=it.fvg_freshness_bars, atr_ratio=it.atr_ratio,
                             session_hour=it.session_hour, enabled=True).passed


_LEARNING_MULT: dict[str, float | None] = {}
_LEARNING_DROPPED: set[str] = set()


def _learning_mult(sleeve: str, learning_rerate) -> float | None:
    """Per-sleeve learning multiplier. On Challenge the score is the multiplier.

    An empty score stays unset. It does not become 1 and it does not apply the recorded max.
    """
    if not learning_rerate:
        return 1.0
    if _on_challenge_book():
        if sleeve in _LEARNING_MULT:
            asked = _LEARNING_MULT[sleeve]
            return None if asked is None else float(asked)
        asked = _scalar(
            "learning_mult",
            "The score you return is this sleeve's learning multiplier on this state. "
            "The map value and the recorded max are facts, not the multiplier. "
            "An empty score leaves the multiplier unset. Do not send.",
            {
                "sleeve": sleeve,
                "map_value": learning_rerate.get(sleeve),
                "recorded_max": LEARNING_RERATE_MAX,
                "login": 0,
            },
        )
        _LEARNING_MULT[sleeve] = asked
        return None if asked is None else float(asked)
    return max(0.0, min(LEARNING_RERATE_MAX, float(learning_rerate.get(sleeve, 1.0))))


_LIVE_NAMESPACE = ""


def bind_live_namespace(namespace: str | None) -> None:
    """One process runs one book. precount reads this when the env is empty."""
    global _LIVE_NAMESPACE
    _LIVE_NAMESPACE = str(namespace or "")


def _place_namespace() -> str:
    return str(
        os.environ.get("GTOS_NAMESPACE")
        or os.environ.get("GTOS_BOOK_NAMESPACE")
        or _LIVE_NAMESPACE
        or ""
    )


def _learning_challenge(kept: list, learning_rerate, refuse) -> list:
    """One pack for the learning gate and the multiplier. The map value is a fact."""
    sleeves = sorted({it.sleeve for it in kept})
    gate = _spot("learning_rerate_gate")
    questions: dict[str, Any] = {}
    for sleeve in sleeves:
        if gate is not None:
            questions[f"learning_gate|{sleeve}"] = gate
        questions[f"learning_mult|{sleeve}"] = _score_q(
            "The score you return is this sleeve's learning multiplier on this state. "
            "The map value and the recorded max are facts, not the multiplier. "
            "An empty score leaves the multiplier unset. Do not send."
        )
    pack = _pack(
        {
            "login": 0,
            "recorded_max": LEARNING_RERATE_MAX,
            "map": {sleeve: learning_rerate.get(sleeve) for sleeve in sleeves},
        },
        questions,
    )
    _LEARNING_DROPPED.clear()
    for sleeve in sleeves:
        _LEARNING_MULT[sleeve] = pack.get(f"learning_mult|{sleeve}")
        if pack.get(f"learning_gate|{sleeve}") == "learning_gate_drop":
            _LEARNING_DROPPED.add(sleeve)
    retained = []
    for it in kept:
        if it.sleeve in _LEARNING_DROPPED:
            refuse(it, "learning_rerate_gate_zero")
        else:
            retained.append(it)
    return retained


def _metals_challenge(kept: list, refuse) -> list:
    """The K reading is a fact. The choice drops. Empty does not drop."""
    gate = _spot("metals_confluence")
    if gate is None:
        return list(kept)
    questions: dict[str, Any] = {}
    facts = []
    for index, it in enumerate(kept):
        verdict = _metals_confluence_pass(it)
        if verdict is None:
            continue
        questions[f"metals|{index}"] = gate
        facts.append({
            "index": index,
            "sleeve": it.sleeve,
            "symbol": it.symbol,
            "verdict_failed": verdict is False,
        })
    if not questions:
        return list(kept)
    pack = _pack({"login": 0, "intents": facts}, questions)
    retained = []
    for index, it in enumerate(kept):
        if pack.get(f"metals|{index}") == "confluence_failed":
            refuse(it, "metals_confluence_gate_failed")
        else:
            retained.append(it)
    return retained


def _symbol_challenge(kept: list, metrics, refuse) -> list:
    """The damage multiplier is a fact. Quarantine is the choice. Empty does not drop."""
    from .symbol_damage_guard import symbol_damage_mult

    gate = _spot("symbol_damage")
    if gate is None:
        return list(kept)
    questions: dict[str, Any] = {}
    facts = []
    for index, it in enumerate(kept):
        mult = symbol_damage_mult(it.symbol, metrics, enabled=True)
        questions[f"damage|{index}"] = gate
        facts.append({"index": index, "symbol": it.symbol, "multiplier": mult})
    pack = _pack({"login": 0, "intents": facts}, questions)
    retained = []
    for index, it in enumerate(kept):
        if pack.get(f"damage|{index}") == "quarantine":
            refuse(it, "symbol_damage_quarantine")
        else:
            retained.append(it)
    return retained


def precount_intent_filter(
    intents: "Sequence[TradeIntent]",
    *,
    vp_acceptance: bool = False,
    learning_rerate: "Mapping[str, float] | None" = None,
    metals_confluence_gate: bool = False,
    symbol_damage_guard: bool = False,
    symbol_damage_metrics: "Mapping[str, Mapping] | None" = None,
    candidate_refusal_sink: "list[dict[str, Any]] | None" = None,
) -> list:
    """The ONE definition of the DROPPING pre-count filters, in the ONE order they apply.

    Every filter here removes intents outright, so the set it returns is exactly the set that
    reaches the Kelly-lite ``n_active_by_day`` count in ``size_correlated_units``. Confidence
    *tilts* (learning DOWN_WEIGHT/SIZE_UP, symbol-damage RISK_REDUCE) are NOT applied here â€” they
    change a unit's size, not whether its sleeve is counted.

    D3 (SLEEVE_BOOK_DEFECT_REGISTER): this used to be written twice â€” once here and once in
    ``book_engine._running_conviction_override`` â€” and the two copies drifted. The engine copy
    applied only ``drop_w7`` + ``vp_acceptance``, omitting the three below, of which
    ``metals_confluence_gate`` is ARMED LIVE (``agent_config.yaml:1315``). A sleeve the full-day
    path drops was therefore still entering the persisted running set, and because
    ``na = max(per_cycle, running)`` can only carry a count UPWARD, the running override could push
    ``n_active`` ABOVE the full-day union â€” breaking the bound its own docstring calls
    CORRECTNESS-CRITICAL, in the size-INCREASING direction (na 3->4 is a 25% size increase on every
    unit that day). Both paths now call this function, so they cannot drift again.

    NOT included here: ``filter_w7_dropped_symbols``. It runs one level up in ``admit_and_size``
    (before ``size_correlated_units`` is ever called) and the engine applies it separately, so
    folding it in would apply it twice on one path and change the call order on the other.
    """
    def _refuse(intent: "TradeIntent", reason: str) -> None:
        if candidate_refusal_sink is None:
            return
        candidate_refusal_sink.append({
            "sleeve": intent.sleeve,
            "symbol": intent.symbol,
            "direction": intent.direction,
            "decision_day": intent.decision_day,
            "candidate_disposition": "refused",
            "candidate_disposition_gate": "book_admission_and_sizing",
            "candidate_disposition_reason": reason,
        })

    kept = list(intents)
    # W6 VP-acceptance exit-honest noise-cut: drop non-above_va sub_mid_dn_revert intents.
    if vp_acceptance:
        retained = []
        for it in kept:
            if (
                it.sleeve == VP_ACCEPTANCE_BASE
                and getattr(it, "vp_loc", None) != VP_ACCEPTANCE_TAG
                and _admission_blocks(
                    "vp_acceptance",
                    {"sleeve": it.sleeve, "vp_loc": getattr(it, "vp_loc", None)},
                )
            ):
                _refuse(it, "vp_acceptance_not_above_va")
            else:
                retained.append(it)
        kept = retained
    # L5 learning actuator: the gate drops a sleeve. On Challenge the multiplier is the score.
    if learning_rerate:
        if _on_challenge_book():
            kept = _learning_challenge(kept, learning_rerate, _refuse)
        else:
            retained = []
            for it in kept:
                if _learning_mult(it.sleeve, learning_rerate) <= 0.0 and _admission_blocks(
                    "learning_rerate_gate", {"sleeve": it.sleeve}
                ):
                    _refuse(it, "learning_rerate_gate_zero")
                else:
                    retained.append(it)
            kept = retained
    # Policy C STRIKE_WHEN_RIGHT (Chair 2026-09-20 APPLY): pre-entry stand_down refuse.
    retained = []
    for it in kept:
        try:
            from src.judgment.policy_c_admit import evaluate_policy_c_admit
            _pc = evaluate_policy_c_admit(it)
            if _pc.get("refuse") and _admission_blocks(
                "policy_c_stand_down",
                {"sleeve": getattr(it, "sleeve", None), "symbol": getattr(it, "symbol", None)},
            ):
                _refuse(it, "policy_c_stand_down")
                continue
        except Exception:
            pass

        # Admission, then place. An exception is a fact on that ask.
        _book_ns = _place_namespace()
        if _book_ns == "operator":
            try:
                from src.judgment.admission_place import decide_admission_place
                _adm = decide_admission_place(
                    intent=it,
                    login=0,
                    ns="operator",
                )
                _adm_d = _adm.as_dict() if hasattr(_adm, "as_dict") else {}
                _adm_det = getattr(it, "details", None)
                if not isinstance(_adm_det, dict):
                    try:
                        it.details = {}
                        _adm_det = it.details
                    except Exception:
                        _adm_det = None
                if isinstance(_adm_det, dict):
                    _adm_det["jev_admission_receipt"] = {
                        k: _adm_d.get(k)
                        for k in (
                            "may_place",
                            "reason",
                            "disposition",
                            "admit",
                            "unique_highest",
                            "probability",
                            "skipped",
                            "state_sufficient",
                        )
                    }
                if (
                    getattr(_adm, "unique_highest", False) is True
                    and getattr(_adm, "admit", None) == "not_this_candidate"
                ):
                    _refuse(it, "jev_admission_not_this_candidate")
                    continue
            except Exception as _adm_exc:
                _adm_det = getattr(it, "details", None)
                if isinstance(_adm_det, dict):
                    _adm_det["jev_admission_error"] = type(_adm_exc).__name__

        # OWNER UNLOCK 2026-09-21: unique CALL. PLACE vs STAND vs DELAY this bar.
        # An unanswered admission hop does not restore a refuse.
        try:
            from src.judgment.place_choice import evaluate_place_choice
            _plc = evaluate_place_choice(it)
            _compose = _plc.get("writer_compose") if isinstance(_plc, dict) else None
            if not isinstance(_compose, dict):
                try:
                    from src.judgment.writer_compose_place import compose_writer_intent
                    _compose = compose_writer_intent(_plc if isinstance(_plc, dict) else {})
                except Exception:
                    _compose = {
                        "action": (_plc or {}).get("action") if isinstance(_plc, dict) else "DELAY",
                        "allow_fresh_place": False,
                        "remint_signal": False,
                        "flatten_candidate": False,
                        "refuse_admit": True,
                        "reason": "jev_place_compose_import_fail",
                    }
            _act = str((_compose or {}).get("action") or (_plc or {}).get("action") or "").upper()
            _det = getattr(it, "details", None)
            if not isinstance(_det, dict):
                try:
                    it.details = {}
                    _det = it.details
                except Exception:
                    _det = None
            if isinstance(_det, dict):
                if isinstance(_compose, dict):
                    _det["jev_writer_compose"] = dict(_compose)
                    _det["jev_place_action"] = _act
                if isinstance(_plc, dict):
                    _det["jev_place_receipt"] = {
                        k: _plc.get(k)
                        for k in (
                            "action",
                            "refuse_place",
                            "source",
                            "skipped",
                            "extra_pass",
                            "never_place",
                        )
                        if k in _plc
                    }
                    _det["jev_place_receipt"]["extra_pass"] = False
            if _act in {"STAND", "DELAY", "SKIP_APPLY_OFF"}:
                _refuse(it, "jev_place_choice_" + _act.lower())
                continue
            if isinstance(_plc, dict) and _plc.get("refuse_place") and _act not in {
                "PLACE",
                "REMINT",
                "FLATTEN_CANDIDATE",
                "SKIP_NOT_CHALLENGE",
                "SKIP_JEV_ABSENT",
            }:
                _refuse(it, "jev_place_choice_" + str(_plc.get("action", "stand")).lower())
                continue
            if _act == "REMINT":
                if isinstance(_det, dict):
                    _det["jev_remint_signal"] = True
                _refuse(it, "jev_place_choice_remint")
                continue
            if _act == "FLATTEN_CANDIDATE":
                if isinstance(_det, dict):
                    _det["jev_flatten_candidate"] = True
                _refuse(it, "jev_place_choice_flatten_candidate")
                continue
        except Exception as _plc_exc:
            if _place_namespace() == "operator":
                _err_det = getattr(it, "details", None)
                if isinstance(_err_det, dict):
                    _err_det["jev_place_error"] = type(_plc_exc).__name__
            else:
                _refuse(it, "jev_place_choice_exception")
                continue

        # SCOPED JEV_SLEEVE_SELECT conflicts (Chair Jev-everywhere 2026-09-21)
        try:
            from src.judgment.sleeve_select import (
                should_stand_three_fresh_xau_conflict,
                should_stand_gbpjpy_conflict_tag,
            )
            _tag = str(getattr(it, "sleeve", None) or getattr(it, "tag", None) or getattr(it, "name", None) or "")
            _sym = str(getattr(it, "symbol", None) or getattr(it, "instrument", None) or "")
            _alive_guess = [_tag]
            try:
                _alive_guess += [str(getattr(x, "sleeve", None) or getattr(x, "tag", None) or "") for x in kept]
                _alive_guess += [str(getattr(x, "sleeve", None) or getattr(x, "tag", None) or "") for x in retained]
            except Exception:
                pass
            if "three_fresh" in _tag and should_stand_three_fresh_xau_conflict(_alive_guess, symbol=_sym):
                _refuse(it, "jev_sleeve_select_xau_conflict_stand_three_fresh")
                continue
            if should_stand_gbpjpy_conflict_tag(_tag, _alive_guess, symbol=_sym):
                _refuse(it, "jev_sleeve_select_gbpjpy_conflict_stand")
                continue
        except Exception:
            pass
        retained.append(it)
    kept = retained
    # A8 metals confluence gate. On Challenge the K reading is a fact and the choice drops.
    if metals_confluence_gate:
        if _on_challenge_book():
            kept = _metals_challenge(kept, _refuse)
        else:
            retained = []
            for it in kept:
                if _metals_confluence_pass(it) is False and _admission_blocks(
                    "metals_confluence", {"sleeve": it.sleeve, "symbol": it.symbol}
                ):
                    _refuse(it, "metals_confluence_gate_failed")
                else:
                    retained.append(it)
            kept = retained
    # S1 per-symbol damage memory. On Challenge the multiplier is a fact and quarantine is the choice.
    if symbol_damage_guard and symbol_damage_metrics:
        if _on_challenge_book():
            kept = _symbol_challenge(kept, symbol_damage_metrics, _refuse)
        else:
            from .symbol_damage_guard import symbol_damage_mult
            retained = []
            for it in kept:
                if symbol_damage_mult(it.symbol, symbol_damage_metrics, enabled=True) <= 0.0 and _admission_blocks(
                    "symbol_damage", {"symbol": it.symbol}
                ):
                    _refuse(it, "symbol_damage_quarantine")
                else:
                    retained.append(it)
            kept = retained
    return kept


def _challenge_risk_units(
    pending: list[tuple],
    *,
    registry: Mapping[str, SleeveSpec],
    base_risk: float,
    equity_card: Mapping[str, Any] | None,
    room: float | None,
    sqrt_n_pooling: bool,
    kelly_lite: bool,
    kelly_conservative: bool,
    n_active_by_day: Mapping[str, int],
    stress_derisk: bool,
    stress_state: "StressDeriskState | None",
    overlays: bool,
    learning_rerate: "Mapping[str, float] | None" = None,
) -> list[SizedUnit]:
    """One pack: each unit's risk and its how_many_more side.

    The profile base, the registry weight, and the room are facts.
    An empty risk does not write zero and does not drop the unit.
    An empty side does not shed.
    """
    card = dict(equity_card or {})
    card["recorded_base_risk"] = base_risk
    card["room_pct"] = room
    card["kelly_lite"] = bool(kelly_lite)
    card["kelly_conservative"] = bool(kelly_conservative)
    card["n_active_by_day"] = dict(n_active_by_day)
    card["stress_derisk"] = bool(stress_derisk)
    card["overlays"] = bool(overlays)
    if stress_state is not None:
        card["consecutive_loss_days"] = int(stress_state.consecutive_loss_days)
        card["trailing_neg_frac"] = float(stress_state.trailing_neg_frac)
    described = []
    for day, cluster, group, members, n in pending:
        if learning_rerate and any(_LEARNING_MULT.get(sleeve) is None for sleeve in members):
            continue
        weights = []
        for sleeve in members:
            spec = registry.get(sleeve)
            weights.append(None if spec is None else spec.confidence)
        described.append({
            "day": day,
            "cluster": cluster,
            "n": n,
            "sleeves": list(members),
            "symbols": [g.symbol for g in group],
            "stops": [g.stop_dist for g in group],
            "directions": [g.direction for g in group],
            "intra": [g.intra_size for g in group],
            "ll_impulse": [getattr(g, "ll_impulse", None) for g in group],
            "decision_hour": [getattr(g, "decision_hour", None) for g in group],
            "vr": [getattr(g, "vr", None) for g in group],
            "registry_confidence": weights,
        })
    card["units"] = described
    how = _spot("how_many_more")
    questions: dict[str, Any] = {}
    for row in described:
        tag = f"{row['day']}|{row['cluster']}"
        questions[f"unit_risk|{tag}"] = _score_q(
            "The score you return is this unit's worst-case open risk as a fraction of live equity. "
            f"The unit is {tag}. "
            "The profile base, the registry weights, the room, and the open risk are facts, not the risk. "
            "An empty score leaves this unit's risk unset. Do not write zero. Do not send."
        )
        if how is not None:
            block = dict(how)
            block["instructions"] = str(how.get("instructions") or "") + f" This question is the unit {tag}."
            questions[f"how_many|{tag}"] = block
    pack = _pack(card, questions) if questions else {}
    out: list[SizedUnit] = []
    for day, cluster, group, members, n in pending:
        tag = f"{day}|{cluster}"
        if learning_rerate and any(_LEARNING_MULT.get(sleeve) is None for sleeve in members):
            out.append(SizedUnit(cluster, members, n, None, None, None, False, "learning_unset"))
            continue
        risk = pack.get(f"unit_risk|{tag}")
        if risk is None:
            per_trade = None
            unit_risk = None
        else:
            unit_risk = float(risk)
            per_trade = (unit_risk / n) if n else None
        pool_reason: tuple[str, ...] = ()
        if sqrt_n_pooling and n > 1:
            pool_reason = (f"sqrtN_pool_n{n}",)
        unit = SizedUnit(
            cluster, members, n, None, per_trade, unit_risk, True, "sized", pool_reason,
        )
        if how is not None:
            _note_side(unit, pack.get(f"how_many|{tag}"))
        out.append(unit)
    return out


def size_correlated_units(
    intents: Sequence[TradeIntent],
    *,
    base_risk_per_unit: float,
    limits: GovernorLimits = DEFAULT_LIMITS,
    include_clean3: bool = False,
    include_clean4: bool = False,
    include_candidate_book: bool = False,
    candidate_book_sleeves: "Sequence[str] | None" = None,
    include_market_expansion_book: bool = False,
    market_expansion_sleeves: "Sequence[str] | None" = None,
    overlays: bool = False,
    vp_acceptance: bool = False,
    stress_state: "StressDeriskState | None" = None,
    stress_derisk: bool = False,
    kelly_lite: bool = False,
    kelly_conservative: bool = False,
    sqrt_n_pooling: bool = False,
    n_active_override: "Mapping[str, int] | None" = None,
    n_active_override_authoritative: bool = False,
    learning_rerate: "Mapping[str, float] | None" = None,
    metals_confluence_gate: bool = False,
    symbol_damage_metrics: "Mapping[str, Mapping] | None" = None,
    symbol_damage_guard: bool = False,
    vol_level_tilt: bool = False,
    candidate_refusal_sink: "list[dict[str, Any]] | None" = None,
    equity_card: "Mapping[str, Any] | None" = None,
    room_pct: float | None = None,
) -> list[SizedUnit]:
    """Group same-day intents into correlated risk units and confidence-size each.

    n_active_override (default None): a leak-free RUNNING per-day distinct-firing-sleeve count
    (decision_day -> count) supplied by the live engine to recover the validated full-day Kelly-lite
    convention without lookahead. Normally the Kelly-lite day count is max(per-cycle, running), retaining
    the historical evaluation-slate behavior. ``n_active_override_authoritative=True`` is reserved for the
    final per-candidate routing preview: its count contains only durable accepted placements plus the
    candidate currently at the send boundary, so future or later-refused siblings cannot size it.
    None => the per-cycle count (byte-identical to today).

    FAIL-CLOSED: any intent referencing an unknown sleeve (relative to the ACTIVE registry â€” the
    clean_3 sleeves are unknown unless include_clean3=True, the clean_4 sleeve unless include_clean4),
    non-positive stop, or invalid direction causes its WHOLE cluster-day unit to size to 0 with an
    explicit reason (no silent admission). Per-trade risk% = base_risk_per_unit * sleeve_confidence *
    intra_size, split across the unit's members so the correlated unit's worst-case simultaneous stop
    = base_risk_per_unit * conf.

    When overlays=True, validated confluence SIZE-UP selectors (leader-impulse veto / session-active
    stack) raise the unit's confidence on the matching base sleeves when their leak-free condition
    holds; the combined size-up is capped at OVERLAY_SIZEUP_MAX so the unit risk stays governor-safe.

    When vp_acceptance=True (W6 exit-honest refinement), sub_mid_dn_revert intents whose vp_loc is
    not the acceptance tag ('above_va') are DROPPED before sizing (the 74.8% stress@1.5% noise-cut).

    When stress_derisk=True, the reactive temporal de-risk overlay (TIER-1 ladder+coloss) applies a
    LEAK-FREE day-level size multiplier (<=1.0) from realized prior-day facts in `stress_state` on top
    of the fixed sleeve confidence weights (sizing-by-confidence preserved; it only ever shrinks size).

    WAVE-7 sqrt-N pooling (sqrt_n_pooling=True; KB7_stale_audit.md (b)): the WORST-CASE-STOP semantics
    of a correlated unit are UNCHANGED (the unit's simultaneous-stop risk stays base*conf, the safe
    governor invariant â€” same-day same-sleeve trades are still ONE correlated unit for risk). What
    sqrt-N changes is the within-sleeve same-day EV-CREDIT convention used to combine the n realized
    R's into the daily series (mean sum/n -> sum/sqrt(n)), exposed via pool_same_day_sleeve_R() and
    applied numerically in the return/MC path. Here it is RECORDED as the active pooling convention on
    each multi-trade unit's reasons so the runtime + the replay-parity check know which book is live.
    DEFAULT-OFF so live sizing + the recorded convention match the LOCKED W7 final MC (mean pooling);
    the owner opts into the sqrt-N refresh (a free +1.9..+2.2pp stress / ~27% faster-to-target win).

    WAVE-11 vol-level tilt (vol_level_tilt=True; Session AR, DEFAULT-OFF): a per-intent monotone
    size tilt on the decision bar's `vr`, scoped to VOL_LEVEL_TILT_SLEEVES â€” see the VOL_LEVEL_TILT
    block above for the measurement, the published centre and why it is a tilt rather than a filter.
    ONE SEMANTIC WORTH KNOWING, because it is the existing unit convention and not a tilt choice:
    a unit is sized at the MAX effective confidence over its same-day same-cluster members
    (`:1176-1179`), so on a multi-trade unit the tilt that survives is the LEAST-shrinking member's.
    The tilt is a net de-risk, so that convention under-delivers it rather than over-delivering it,
    which is the safe direction; `AR_VOL_LEVEL_TILT_V1.json.unit_max_convention` measures how often
    it binds on the archive population rather than leaving it as a caveat.
    """
    registry = effective_registry(
        include_clean3=include_clean3,
        include_clean4=include_clean4,
        include_candidate_book=include_candidate_book,
        candidate_book_sleeves=candidate_book_sleeves,
        include_market_expansion_book=include_market_expansion_book,
        market_expansion_sleeves=market_expansion_sleeves,
    )
    # Cohort A: do not enlarge the default live registry. When a tags-gated
    # dsp_* intent is actually present, admit it with its own cluster.
    dsp_present = {it.sleeve for it in intents if it.sleeve in DISPLACEMENT_REGISTRY}
    if dsp_present:
        registry = dict(registry)
        registry.update({name: DISPLACEMENT_REGISTRY[name] for name in dsp_present})
    # DROPPING pre-count filters (W6 VP-acceptance noise-cut, L5 learning GATE, A8 metals confluence,
    # S1 symbol-damage QUARANTINE). Shared with book_engine._running_conviction_override so the running
    # Kelly count can never be taken over a wider intent set than the one sized here â€” see D3 in
    # precount_intent_filter's docstring. Confidence TILTS for the survivors are applied below.
    intents = precount_intent_filter(
        intents,
        vp_acceptance=vp_acceptance,
        learning_rerate=learning_rerate,
        metals_confluence_gate=metals_confluence_gate,
        symbol_damage_guard=symbol_damage_guard,
        symbol_damage_metrics=symbol_damage_metrics,
        candidate_refusal_sink=candidate_refusal_sink,
    )
    # W6 reactive temporal de-risk: leak-free day-level multiplier from realized prior days only.
    derisk_mult, derisk_reasons = (1.0, ())
    challenge = _on_challenge_book()
    if stress_derisk and not challenge:
        derisk_mult, derisk_reasons = stress_derisk_multiplier(
            stress_state or StressDeriskState(), enabled=True, tier=1)
    # KB7 Kelly-lite day-level conviction tilt: leak-free count of DISTINCT firing sleeves TODAY
    # (per decision_day), known before sizing. The multiplier is applied per-unit and COMBINED with
    # the confluence overlay size-up, then capped at OVERLAY_SIZEUP_MAX (governor-safe). This counts
    # distinct sleeves across ALL of today's intents (the independent-edge breadth), not per-cluster.
    n_active_by_day: dict[str, int] = {}
    if kelly_lite or challenge:
        day_sleeves: dict[str, set[str]] = {}
        for it in intents:
            day_sleeves.setdefault(it.decision_day, set()).add(it.sleeve)
        n_active_by_day = {d: len(s) for d, s in day_sleeves.items()}
    # bucket by (decision_day, cluster) â€” the correlated-risk-unit key.
    buckets: dict[tuple[str, str], list[TradeIntent]] = {}
    for it in intents:
        cluster = cluster_of(it.sleeve, registry)
        if cluster is None:
            cluster = "__unknown__"
        buckets.setdefault((it.decision_day, cluster), []).append(it)

    units: list[SizedUnit | None] = []
    pending: list[tuple] = []
    for (day, cluster), group in sorted(buckets.items()):
        members = tuple(sorted(set(g.sleeve for g in group)))
        n = len(group)
        # FAIL-CLOSED validation of every member of the unit.
        bad = None
        for g in group:
            if not _is_known_sleeve(g.sleeve, registry) and _admission_blocks(
                "unknown_sleeve", {"sleeve": g.sleeve}
            ):
                bad = f"unknown_sleeve:{g.sleeve}"; break
            if not (g.direction in (1, -1)) and _admission_blocks(
                "bad_direction", {"sleeve": g.sleeve, "direction": g.direction}
            ):
                bad = f"bad_direction:{g.direction}"; break
            if not (g.stop_dist is not None and g.stop_dist > 0) and _admission_blocks(
                "nonpositive_stop", {"sleeve": g.sleeve, "stop_dist": g.stop_dist}
            ):
                bad = f"nonpositive_stop:{g.stop_dist}"; break
            if not (g.intra_size is not None and g.intra_size >= 0) and _admission_blocks(
                "bad_intra_size", {"sleeve": g.sleeve, "intra_size": g.intra_size}
            ):
                bad = f"bad_intra_size:{g.intra_size}"; break
        if bad is not None:
            if challenge:
                units.append(SizedUnit(cluster, members, n, None, None, None, False, f"fail_closed:{bad}"))
            else:
                units.append(SizedUnit(cluster, members, n, 0.0, 0.0, 0.0, False, f"fail_closed:{bad}"))
            continue
        if challenge:
            pending.append((day, cluster, group, members, n))
            units.append(None)
            continue
        # confidence of the unit: max sleeve confidence among the same-class members firing today,
        # each member's confidence boosted by its own confluence overlay size-up (if it qualifies).
        # (correlated-within-class: the unit is sized at the strongest member's effective confidence;
        #  the weaker same-class members share the unit and do not add independent risk.)
        # KB7 Kelly-lite day-level conviction multiplier for this day (1.0 when disabled).
        kelly_mult = 1.0; kelly_reason: tuple[str, ...] = ()
        if kelly_lite:
            # Ordinary evaluation keeps the historical max(per-cycle, running) floor.  The explicit
            # placement-bound mode makes the override authoritative because it contains only durable
            # accepted sleeves plus the current candidate; future/refused slate members are intentionally
            # absent and must not raise this candidate's Kelly bin.
            na = n_active_by_day.get(day, 0)
            if n_active_override is not None:
                override_na = int(n_active_override.get(day, 0))
                na = max(0, override_na) if n_active_override_authoritative else max(na, override_na)
            if _on_challenge_book():
                asked = _challenge_factor(
                    "kelly",
                    {"n_active": na, "conservative": bool(kelly_conservative)},
                )
                kelly_mult = None if asked is None else asked
            else:
                kelly_mult = kelly_lite_conviction_multiplier(
                    na, enabled=True, conservative=kelly_conservative)
            if kelly_mult is None:
                units.append(SizedUnit(
                    cluster, members, n, None, None, None, False, "kelly_unset",
                ))
                continue
            if kelly_mult != 1.0:
                kelly_reason = (f"kelly_lite_na{na}_x{kelly_mult:g}",)
        applied: list[str] = []
        conf = 0.0
        for g in group:
            su, names = overlay_sizeup_for(g, overlays=overlays)
            # WAVE-11 vol-LEVEL tilt (default-off). It is the only multiplier in this product
            # that can be BELOW 1.0, so it is SPLIT and the two halves compose differently â€”
            # which is not fussiness, it is the difference between a de-risk that is obeyed and
            # one that is merely observed:
            #   * the size-UP half goes INSIDE the cap, so the governor-safe ceiling still binds;
            #   * the SHRINK half applies AFTER the cap, so it can never be absorbed by it.
            # Putting the whole tilt inside the cap DISCARDS the shrink whenever the other terms
            # already reach the ceiling. That state is LATENT and two independent changes away â€”
            # `overlays` is false AND the live generator populates neither field either overlay
            # needs, so `su` is 1.0 structurally (see the VOL_LEVEL_TILT block for the
            # measurement). The split is hardening, not an active repair. Measured, not reasoned:
            # `test_a_shrink_is_not_discarded_by_the_sizeup_cap` drives the other terms to the
            # ceiling, failed on the inside-the-cap version and passes on this one. The pattern is
            # the one `derisk_mult` already uses below â€” a shrink applies outside every cap.
            # Exactly one half is ever != 1.0 because the tilt is a single scalar.
            vlt, vlt_names = vol_level_tilt_for(g, enabled=vol_level_tilt)
            if vlt is None:
                units.append(SizedUnit(
                    cluster, members, n, None, None, None, False, "vol_level_unset",
                ))
                conf = None
                break
            names = tuple(names) + vlt_names
            vlt_up, vlt_dn = max(1.0, vlt), min(1.0, vlt)
            # COMBINED size-up (confluence overlay x Kelly-lite conviction tilt x the tilt's
            # size-up half) is capped together at OVERLAY_SIZEUP_MAX so a single risk unit never
            # exceeds the worst-case daily/maxDD cap; the tilt's shrink half then applies.
            _cap = _admit_score(
                "overlay_sizeup_cap",
                "The score you return is the cap on this unit's combined size-up. "
                "An empty score leaves the product uncapped. Do not send.",
                {"sleeve": g.sleeve, "cluster": cluster},
            )
            _product = su * kelly_mult * vlt_up
            if _cap is not None:
                _product = min(_product, _cap)
            su_combined = _product * vlt_dn
            # L5 learning actuator: bounded per-sleeve confidence tilt (DOWN_WEIGHT/SIZE_UP); GATE (0.0)
            # already dropped above. 1.0 when learning_rerate is None (no-op). S1 symbol-damage RISK_REDUCE
            # (0.5) applies per-symbol (QUARANTINE 0.0 already dropped above); 1.0 when disabled (no-op).
            sd_mult = 1.0
            if symbol_damage_guard and symbol_damage_metrics:
                from .symbol_damage_guard import symbol_damage_mult
                sd_mult = symbol_damage_mult(g.symbol, symbol_damage_metrics, enabled=True)
            weight = confidence_for(g.sleeve, registry)
            if weight is None:
                continue
            learn = _learning_mult(g.sleeve, learning_rerate)
            if learn is None:
                units.append(SizedUnit(
                    cluster, members, n, None, None, None, False, "learning_unset",
                ))
                conf = None
                break
            eff = (float(weight) * float(g.intra_size) * su_combined
                   * learn * sd_mult)
            if eff > conf:
                conf = eff; applied = list(names)
        if conf is None:
            continue
        # reactive temporal de-risk is a DAY-LEVEL multiplier on the whole-unit risk (<=1.0).
        unit_risk = base_risk_per_unit * conf * derisk_mult
        per_trade = unit_risk / n if n else 0.0
        # WAVE-7 sqrt-N pooling: worst-case-stop risk is UNCHANGED (correlated cap = base*conf, the
        # safe invariant); we only RECORD the active EV-credit pooling convention on multi-trade units
        # so the runtime/parity know whether the live book uses mean (locked W7 MC) or sqrt-N pooling.
        pool_reason: tuple[str, ...] = ()
        if sqrt_n_pooling and n > 1:
            pool_reason = (f"sqrtN_pool_n{n}",)
        units.append(SizedUnit(cluster, members, n, round(conf * derisk_mult, 6),
                               round(per_trade, 8), round(unit_risk, 8), True, "sized",
                               tuple(applied) + kelly_reason + derisk_reasons + pool_reason))
    if pending:
        finished = _challenge_risk_units(
            pending,
            registry=registry,
            base_risk=base_risk_per_unit,
            equity_card=equity_card,
            room=room_pct,
            sqrt_n_pooling=sqrt_n_pooling,
            kelly_lite=kelly_lite,
            kelly_conservative=kelly_conservative,
            n_active_by_day=n_active_by_day,
            stress_derisk=stress_derisk,
            stress_state=stress_state,
            overlays=overlays,
            learning_rerate=learning_rerate,
        )
        step = 0
        filled: list[SizedUnit] = []
        for item in units:
            if item is None:
                filled.append(finished[step])
                step += 1
            else:
                filled.append(item)
        return filled
    return [item for item in units if item is not None]


# ===========================================================================================
# 4. FAIL-CLOSED DAILY-BREACH / MAX-DD GOVERNOR (runtime invariant, KB_architecture_spec S3.3)
# ===========================================================================================
@dataclass
class GovernorState:
    """Live equity/intraday state passed in by the runtime (no outcome leakage; current facts only)."""
    equity: float                 # current account equity
    high_water: float             # peak equity since challenge start (sanity invariant only; >= equity)
    realized_today_pct: float     # realized intraday P&L as fraction of start-of-day equity (<=0 if loss)
    open_risk_pct: float          # sum of worst-case-stop equity% across currently open units
    operator_circuit_breaker: bool = False  # outer kill switch: True => flatten new entries
    max_dd_reference_equity: float = 0.0     # STATIC max-DD basis = initial balance (FTMO/FN floor is
    #                                          initial-10% = a FIXED 90k for 100k, NOT trailing). 0 =>
    #                                          fall back to trailing high_water (back-compat).


@dataclass
class GovernorDecision:
    allow_new_entries: bool
    size_cap_multiplier: float    # multiply base_risk_per_unit (de-risk into the wall; never widen)
    available_gross_risk_pct: float | None
    reason: str



def _on_challenge_book() -> bool:
    """Live Challenge writer or an explicit Challenge namespace. Friends stay on the old branch."""
    ns = str(os.environ.get("GTOS_NAMESPACE") or os.environ.get("GTOS_BOOK_NAMESPACE") or "").strip()
    if ns == "operator":
        return True
    import sys
    argv = " ".join(sys.argv).replace("\\", "/").lower()
    return "operator" in argv and "run_book" in argv


def _challenge_factor(spot: str, facts: dict) -> float | None:
    """Score multiplier on Challenge. None does not apply a table or a haircut."""
    if not _on_challenge_book():
        return None
    try:
        from src.judgment.no_fear import factor
        return factor(spot, facts)
    except Exception:
        return None


def _admission_blocks(spot: str, facts: dict | None = None) -> bool:
    """Old branch off Challenge. On Challenge, only when that side is the unique highest."""
    if not _on_challenge_book():
        return True
    try:
        from src.judgment.admission_choices import withholds
        return bool(withholds(spot, facts))
    except Exception:
        return False


def _how_many_more(facts: dict) -> str | None:
    """Unique side of the how_many_more hop.

    count_caps sheds. another_can_send keeps. None does not shed and does not
    zero the room.
    """
    try:
        from src.judgment.admission_choices import unique_side
        picked = unique_side("how_many_more", facts)
    except Exception:
        return None
    if picked in {"count_caps", "another_can_send"}:
        return picked
    return None


_MISSING = object()
_UNIT_SIDE: dict[int, str | None] = {}
_UNIT_ASKED: set[int] = set()


def _score_q(text: str) -> dict[str, str]:
    return {"type": "score", "instructions": text}


def _spot(name: str) -> dict | None:
    try:
        from src.judgment.admission_choices import spot_block
        return spot_block(name)
    except Exception:
        return None


def _pack(facts: dict, questions: dict) -> dict:
    """One ask for this card. Empty questions are not a call."""
    if not questions:
        return {}
    try:
        from src.judgment.admission_choices import ask_pack
        got = ask_pack(facts, questions)
    except Exception:
        return {}
    return got if isinstance(got, dict) else {}


def _scalar(role: str, instructions: str, facts: dict) -> float | None:
    number = _pack(facts, {role: _score_q(instructions)}).get(role)
    if number is None:
        return None
    try:
        return float(number)
    except (TypeError, ValueError):
        return None


def _note_side(unit: SizedUnit, side: str | None) -> None:
    _UNIT_ASKED.add(id(unit))
    _UNIT_SIDE[id(unit)] = side if side in {"count_caps", "another_can_send"} else None


def _read_side(unit: SizedUnit):
    if id(unit) not in _UNIT_ASKED:
        return _MISSING
    return _UNIT_SIDE.get(id(unit))


def _equity_card(state: GovernorState, limits: GovernorLimits, **extra) -> dict:
    """Live equity readings. Recorded limits are facts on the card."""
    dd_ref = state.max_dd_reference_equity if state.max_dd_reference_equity > 0 else state.high_water
    dd = None
    gain = None
    try:
        if dd_ref:
            dd = (float(dd_ref) - float(state.equity)) / float(dd_ref)
            gain = (float(state.equity) - float(dd_ref)) / float(dd_ref)
    except (TypeError, ValueError, ZeroDivisionError):
        dd = None
        gain = None
    card = {
        "equity": state.equity,
        "high_water": state.high_water,
        "realized_today_pct": state.realized_today_pct,
        "open_risk_pct": state.open_risk_pct,
        "max_dd_reference_equity": state.max_dd_reference_equity,
        "dd": dd,
        "gain": gain,
        "login": 0,
        "ns": "operator",
        "recorded_soft_daily_stop_pct": getattr(limits, "soft_daily_stop_pct", None),
        "recorded_hard_daily_limit_pct": getattr(limits, "hard_daily_limit_pct", None),
        "recorded_max_dd_limit_pct": getattr(limits, "max_dd_limit_pct", None),
        "recorded_max_dd_entry_block_pct": getattr(limits, "max_dd_entry_block_pct", None),
        "recorded_derisk_start_dd_pct": getattr(limits, "derisk_start_dd_pct", None),
        "recorded_gross_open_risk_cap_pct": getattr(limits, "gross_open_risk_cap_pct", None),
        "recorded_profit_target_pct": getattr(limits, "profit_target_pct", None),
        "recorded_profit_target_derisk_mult": getattr(limits, "profit_target_derisk_mult", None),
        "derisk_mode": getattr(limits, "derisk_mode", None),
    }
    card.update(extra)
    return card


def _challenge_governor(
    state: GovernorState,
    limits: GovernorLimits,
    *,
    base_risk: float | None = None,
) -> GovernorDecision:
    """Room, caps, and the block choices are one pack on the live equity card.

    An empty score does not restore a recorded cap and does not write the room as zero.
    An empty choice does not block.
    """
    card = _equity_card(state, limits)
    if base_risk is not None:
        card["base_risk"] = base_risk
    questions: dict[str, Any] = {
        "gross_open_risk_room": _score_q(
            "The score you return is the gross open-risk room on this live equity, "
            "as a fraction of equity still open for new risk. "
            "The recorded cap is a fact, not the room. "
            "An empty score leaves the room unset. Do not write zero. Do not send."
        ),
        "soft_daily_stop_pct": _score_q(
            "The score you return is the soft daily stop for this live equity, as a fraction of equity. "
            "The recorded stop is a fact, not the stop. "
            "An empty score leaves the stop unset. Do not send."
        ),
        "max_dd_limit_pct": _score_q(
            "The score you return is the max-drawdown limit for this live equity, as a fraction of equity. "
            "The recorded limit is a fact, not the limit. "
            "An empty score leaves the limit unset. Do not send."
        ),
        "max_dd_entry_block_pct": _score_q(
            "The score you return is the entry-buffer drawdown for this live equity, as a fraction of equity. "
            "The recorded buffer is a fact, not the buffer. "
            "An empty score leaves the buffer unset. Do not send."
        ),
        "hard_daily_limit_pct": _score_q(
            "The score you return is the hard daily limit for this live equity, as a fraction of equity. "
            "The recorded limit is a fact, not the limit. "
            "An empty score leaves the limit unset. Do not send."
        ),
        "size_cap_multiplier": _score_q(
            "The score you return is the size-cap multiplier on this live equity. "
            "The drawdown and the recorded de-risk shape are facts, not the multiplier. "
            "An empty score leaves the size uncut. Do not send."
        ),
        "profit_target_mult": _score_q(
            "The score you return is the profit-target size multiplier on this live equity. "
            "The recorded target and the recorded shrink are facts, not the multiplier. "
            "An empty score leaves the size uncut. Do not send."
        ),
    }
    for name in ("soft_daily_stop", "max_dd_limit", "max_dd_entry_buffer", "ceiling_smooth"):
        block = _spot(name)
        if block is not None:
            questions[name] = block
    pack = _pack(card, questions)
    if pack.get("ceiling_smooth") == "ceiling_refuses":
        return GovernorDecision(False, 0.0, None, "ceiling_profile_requires_smooth_ddefense")
    if pack.get("soft_daily_stop") == "soft_stop_reached":
        return GovernorDecision(False, 0.0, None, "soft_daily_stop_reached")
    if pack.get("max_dd_limit") == "max_dd_reached":
        return GovernorDecision(False, 0.0, None, "max_dd_limit_reached")
    if pack.get("max_dd_entry_buffer") == "entry_buffer_reached":
        return GovernorDecision(False, 0.0, None, "max_dd_entry_buffer_reached")
    room = pack.get("gross_open_risk_room")
    room_out = None if room is None else round(float(room), 6)
    cap = pack.get("size_cap_multiplier")
    cap_mult = 1.0 if cap is None else float(cap)
    profit = pack.get("profit_target_mult")
    reason = "ok" if cap_mult == 1.0 else "derisking_into_maxdd_wall"
    if profit is not None:
        cap_mult *= float(profit)
        reason = "profit_target_protect_derisk"
    return GovernorDecision(True, round(cap_mult, 6), room_out, reason)


def evaluate_governor(
    state: GovernorState,
    *,
    limits: GovernorLimits = DEFAULT_LIMITS,
    base_risk: float | None = None,
) -> GovernorDecision:
    """Fail-closed governor. Returns whether NEW entries are allowed and a size-cap multiplier.

    Order of fail-closed checks (any trip -> block new entries; existing managed by structural stops):
      1. operator circuit breaker (outer kill switch)
      2. invalid/contradictory state (NaN, equity<=0, high_water<equity-epsilon)
      3. soft daily stop reached (-3% intraday)
      4. gross open risk cap exhausted
      5. max-DD de-risk band (shrink size as equity approaches -10%)
    """
    eps = 1e-9
    # 1. outer circuit breaker
    if state.operator_circuit_breaker and _admission_blocks(
        "circuit_breaker_open", {"operator_circuit_breaker": True}
    ):
        return GovernorDecision(False, 0.0, 0.0, "circuit_breaker_open")
    # 2. invalid/contradictory state -> fail closed
    vals = [state.equity, state.high_water, state.realized_today_pct, state.open_risk_pct]
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals) and _admission_blocks(
        "nan_state", {"nan_state": True}
    ):
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:nan_state")
    if (state.equity <= 0 or state.high_water <= 0) and _admission_blocks(
        "nonpositive_equity",
        {"equity": state.equity, "high_water": state.high_water},
    ):
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:nonpositive_equity")
    if state.high_water + eps < state.equity and _admission_blocks(
        "high_water_below_equity",
        {"equity": state.equity, "high_water": state.high_water},
    ):
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:high_water_below_equity")
    if state.open_risk_pct < -eps and _admission_blocks(
        "negative_open_risk", {"open_risk_pct": state.open_risk_pct}
    ):
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:negative_open_risk")
    if _on_challenge_book():
        return _challenge_governor(state, limits, base_risk=base_risk)
    # 3. soft daily stop (block opening NEW units below -3% intraday; -5% hard never approached)
    if state.realized_today_pct <= -limits.soft_daily_stop_pct and _admission_blocks(
        "soft_daily_stop", {"realized_today_pct": state.realized_today_pct}
    ):
        return GovernorDecision(False, 0.0, 0.0, "soft_daily_stop_reached")
    # Drawdown for the max-DD wall + de-risk band. The FTMO/FN max-DD floor is STATIC = initial-10%
    # (a FIXED 90k for a 100k account; it does NOT trail up with profit), so measure DD from the static
    # initial-balance reference when supplied. Fall back to trailing high_water only for back-compat
    # callers that pass no reference. When equity is ABOVE the reference (in profit) dd is negative ->
    # full size, no de-risk, and the wall stays pinned at reference*(1-max_dd) regardless of the peak.
    dd_ref = state.max_dd_reference_equity if state.max_dd_reference_equity > 0 else state.high_water
    dd = (dd_ref - state.equity) / dd_ref
    if dd >= limits.max_dd_limit_pct and _admission_blocks(
        "max_dd_limit", {"dd": dd}
    ):
        return GovernorDecision(False, 0.0, 0.0, "max_dd_limit_reached")
    entry_block_pct = max(0.0, min(float(limits.max_dd_entry_block_pct), float(limits.max_dd_limit_pct)))
    if entry_block_pct > 0 and dd >= entry_block_pct and _admission_blocks(
        "max_dd_entry_buffer", {"dd": dd, "entry_block_pct": entry_block_pct}
    ):
        return GovernorDecision(False, 0.0, 0.0, "max_dd_entry_buffer_reached")
    # 4. gross open-risk arithmetic. On Challenge it is a fact, not a gate.
    available = limits.gross_open_risk_cap_pct - state.open_risk_pct
    if not _on_challenge_book() and available <= 0 and _admission_blocks(
        "gross_risk_cap", {"available": available}
    ):
        return GovernorDecision(False, 0.0, max(0.0, available), "gross_risk_cap_exhausted")
    # 5. max-DD de-risk: shrink size as equity approaches the -10% wall. Two modes (limits.derisk_mode):
    #   "band" (default == current live behavior): full size until derisk_start_dd, then linear to 0 at wall.
    #   "smooth": de-risk PROPORTIONALLY from dd=0 (cap_mult = 1 - dd_frac). On the REAL W7 book (research
    #     c59/c61) this holds total-DD-fail ~0 at a HIGHER base -> the binding constraint becomes the -5%
    #     daily fat tail, not the -10% wall; faster passes AND safer. Opt-in via GTOS_UB_DERISK_MODE=smooth.
    if limits.derisk_mode == "smooth":
        computed_cap = max(0.0, 1.0 - dd / max(eps, limits.max_dd_limit_pct)) if dd > 0 else 1.0
    elif dd <= limits.derisk_start_dd_pct:
        computed_cap = 1.0
    else:
        span = max(eps, limits.max_dd_limit_pct - limits.derisk_start_dd_pct)
        computed_cap = max(0.0, 1.0 - (dd - limits.derisk_start_dd_pct) / span)
    # The formula is a reading. On Challenge the multiplier is the score.
    # An empty answer or a tie leaves the cap uncut and does not restore the shrink.
    if _on_challenge_book():
        cap_mult = 1.0
        if dd > 0:
            asked = _challenge_factor(
                "size_cap",
                {"dd": dd, "derisk_mode": str(limits.derisk_mode)},
            )
            if asked is not None:
                cap_mult = asked
    elif computed_cap < 1.0 - 1e-12 and _admission_blocks(
        "derisk",
        {
            "dd": dd,
            "derisk_mode": limits.derisk_mode,
            "computed_cap": computed_cap,
        },
    ):
        cap_mult = computed_cap
    else:
        cap_mult = computed_cap
    # OPS-03 profit-target protect: once the challenge target is reached (gain vs the STATIC initial-balance
    # reference, the same basis as the max-DD wall), shrink NEW-entry size to lock in the pass while staying
    # in the market. Combines multiplicatively with the max-DD de-risk (whichever is smaller dominates).
    reason = "ok" if cap_mult == 1.0 else "derisking_into_maxdd_wall"
    if limits.profit_target_pct > 0 and dd_ref > 0:
        gain = (state.equity - dd_ref) / dd_ref
        if gain >= limits.profit_target_pct and _on_challenge_book():
            asked = _challenge_factor("profit_target", {"gain": gain})
            if asked is not None:
                cap_mult *= asked
                reason = "profit_target_protect_derisk"
        elif gain >= limits.profit_target_pct and _admission_blocks(
            "profit_target_protect", {"gain": gain}
        ):
            cap_mult *= max(0.0, min(1.0, limits.profit_target_derisk_mult))
            reason = "profit_target_protect_derisk"
    return GovernorDecision(True, round(cap_mult, 6), round(available, 6), reason)


def _enforce_gross_open_risk_cap(units: "Sequence[SizedUnit]", available_gross_risk_pct: float | None) -> list:
    """Drop sized units that would exceed the remaining gross-open-risk headroom, considering units in
    DESCENDING-CONVICTION order. Returns asdict() dicts in the ORIGINAL unit order. Inert until the cap
    actually binds (normal-day gross << 4%).

    WHAT THIS GUARANTEES: the highest-conviction unit is tested against the FULL headroom, so
    metals_core is admitted whenever its own risk fits. That is the property the prior
    natural/alphabetical-cluster order broke (a known W7_LIVE_ENGINE_BUILD_PLAN hazard) and it is the
    strongest guarantee any shed policy can give.

    WHAT THIS DOES **NOT** GUARANTEE â€” corrected 2026-07-27, D1 in SLEEVE_BOOK_DEFECT_REGISTER.md.
    This docstring used to claim the cap "sheds the LOWEST-conviction units first". IT DOES NOT. The
    algorithm is a FIRST-FIT-DESCENDING greedy: each unit is admitted iff it fits the REMAINING
    headroom, so the cap sheds by FIT, not by conviction. At 0.0400 headroom with four clusters firing
    it admits metals (1.241) and index (0.15 conf), and sheds crypto and energy â€” i.e. it sheds the
    second- and third-strongest while admitting the weakest. [MEASURED] Over 4,000 random cluster sets
    drawn from the live 13-cluster confidence map, FFD can leave 28.6% of deployable risk unused
    (headroom 0.031: FFD deploys 0.021718 where the optimal subset deploys 0.030404).

    Latent, not realized: in the recorded W7 fortnight the cap NEVER bound â€” all 668 distinct recorded
    units carry reason "sized", zero carry "gross_risk_cap_would_exceed" [MEASURED].

    Changing the shed policy (D1 proposes proportional scaling) redistributes risk across sleeves and
    is therefore the OWNER's decision, not a hygiene fix. Only the false claim is repaired here."""
    available = available_gross_risk_pct
    order = sorted(range(len(units)), key=lambda i: -(units[i].confidence or 0.0))
    kept: dict[int, Any] = {}
    for i in order:
        u = units[i]
        if not u.sized:
            kept[i] = u
            continue
        if _on_challenge_book():
            # The fit comparison is not the shed. how_many_more is.
            primed = _read_side(u)
            if primed is _MISSING:
                side = _how_many_more(
                    {
                        "cluster": u.cluster,
                        "unit_risk_pct": u.unit_risk_pct,
                        "room_pct": available,
                    }
                )
            else:
                side = primed
            if side == "count_caps":
                kept[i] = SizedUnit(
                    u.cluster, u.sleeve_members, u.n_trades, u.confidence,
                    u.risk_pct_per_trade, u.unit_risk_pct, False, "how_many_more",
                    u.overlays_applied,
                )
            elif side == "another_can_send":
                if available is not None and u.unit_risk_pct is not None:
                    available = float(available) - float(u.unit_risk_pct)
                kept[i] = u
            else:
                kept[i] = u
            continue
        if u.unit_risk_pct <= available + 1e-9:
            available -= u.unit_risk_pct
            kept[i] = u
        elif _admission_blocks(
            "gross_cap_shed",
            {
                "cluster": u.cluster,
                "unit_risk_pct": u.unit_risk_pct,
                "available": available,
            },
        ):
            # D5: carry overlays_applied through the rebuild. Omitting it dropped the kelly_lite_naN_xM
            # / ladder_stepK / coloss_breaker tags from every shed unit, so a shed unit kept its
            # confidence but lost the record of WHY it had that confidence â€” exactly the forensics D1
            # needs to reconstruct whether the cap shed a top-bin Kelly day or a bottom-bin one.
            kept[i] = SizedUnit(u.cluster, u.sleeve_members, u.n_trades, u.confidence,
                                0.0, 0.0, False, "gross_risk_cap_would_exceed",
                                u.overlays_applied)
        else:
            available -= u.unit_risk_pct
            kept[i] = u
    return [asdict(kept[i]) for i in range(len(units))]


def admit_and_size(
    intents: Sequence[TradeIntent],
    state: GovernorState,
    *,
    profile: str = DEFAULT_PROFILE,
    account: str = "A",
    limits: GovernorLimits = DEFAULT_LIMITS,
    include_clean3: bool = False,
    include_clean4: bool = False,
    include_candidate_book: bool = False,
    candidate_book_sleeves: "Sequence[str] | None" = None,
    include_market_expansion_book: bool = False,
    market_expansion_sleeves: "Sequence[str] | None" = None,
    overlays: bool = False,
    vp_acceptance: bool = False,
    stress_state: "StressDeriskState | None" = None,
    stress_derisk: bool = False,
    kelly_lite: bool = False,
    kelly_conservative: bool = False,
    sqrt_n_pooling: bool = False,
    drop_w7_symbols: bool = False,
    n_active_override: "Mapping[str, int] | None" = None,
    n_active_override_authoritative: bool = False,
    learning_rerate: "Mapping[str, float] | None" = None,
    metals_confluence_gate: bool = False,
    symbol_damage_metrics: "Mapping[str, Mapping] | None" = None,
    symbol_damage_guard: bool = False,
    vol_level_tilt: bool = False,
    candidate_refusal_sink: "list[dict[str, Any]] | None" = None,
) -> dict[str, Any]:
    """Top-level deployable decision: governor gate -> confidence-weighted correlated-unit sizing.

    Returns a structured decision (JSON-serializable). When new entries are blocked, ALL units size 0
    (existing positions are NOT touched here â€” they are managed by their own structural stops upstream).

    All upgrade flags default OFF (locked 8-sleeve book). The owner enables, at go-live:
      include_clean3   -> Wave-5 additive deploy book (3 substrate/volprofile sleeves)
      include_clean4   -> + Wave-6 session_leadlag_genuine sleeve (implies clean_3)
      include_candidate_book -> runtime-executable fixed-target candidate promotions (default-off)
      include_market_expansion_book -> market-expansion D1 target2 candidates (default-off and
                          explicit non-empty allowlist only)
      overlays         -> confluence size-up selectors (leader veto / session stack)
      vp_acceptance    -> W6 exit-honest noise-cut of sub_mid_dn_revert (above_va only)
      stress_derisk    -> W6 reactive temporal de-risk multiplier (TIER-1 ladder+coloss, default-on
                          recommended; pass stress_state with realized prior-day facts)
      kelly_lite       -> KB7 day-level conviction tilt (handset; kelly_conservative=half-Kelly)
      sqrt_n_pooling   -> KB7 within-sleeve same-day sqrt-N EV-credit convention (recorded; default-off
                          to match the locked W7 final MC mean-pooling)
      drop_w7_symbols  -> W7 tick-true fail-closed filter of HEATOIL_c/NATGAS_cash intents
      learning_rerate  -> L5 learning-actuator per-sleeve confidence map (GATE 0.0 drops; bounded tilt
                          otherwise). Produced by learning_actuator.rerate_book on deep-history evidence;
                          None => no-op (the live edge_reconciler stays brake-only unless the owner arms this)
      metals_confluence_gate -> A8 K=3-of-4 entry-quality filter on metals intents that carry the
                          confluence features (deploy-phase generator change arms it; featureless = admit)
      vol_level_tilt   -> WAVE-11 per-intent vol-LEVEL size tilt on the decision bar's `vr`, scoped
                          to VOL_LEVEL_TILT_SLEEVES (Session AR; net DE-RISK, mean multiplier 0.925
                          on the archive population). Reached from `run_book.py --vol-level-tilt`,
                          NOT from a config byte -- `agent_config.yaml` and `profiles/redacted_account.yaml`
                          are both hashed into a live activation token's config digest.
    For the clean_3/clean_4 path pass the matching profile (CLEAN3_/CLEAN4_/W7 dial) so sizing uses the
    intended risk; the W7 nominal dials expect include_clean3=True + kelly_lite=True.
    """
    prof = ALLOCATION_PROFILES.get(profile)
    if prof is None:
        if _admission_blocks("unknown_profile", {"profile": str(profile)}):
            return {"ok": False, "reason": f"unknown_profile:{profile}", "units": [], "governor": None}
        return {"ok": False, "reason": "admission_unset:unknown_profile", "units": [], "governor": None}
    base_risk = prof.risk_per_unit_A if account.upper() == "A" else prof.risk_per_unit_B
    # SAFETY INTERLOCK (research c61): the >=2.0% ceiling nominal is only certified RUIN-SAFE
    # (total-DD-fail = 0) WITH smooth DD-defense. On band-defense the real fat left tail (-3.225R) leaks
    # total-DD failures, so the un-certified pairing is refused: fail closed (size 0 new entries) unless
    # smooth defense is active. The aggressive dial can therefore NEVER run on the un-certified band shape.
    # The LIVE dial is the 2.0% ceiling (clean3_w7_ceiling_nom2p00), which this interlock REQUIRES smooth
    # defense for (band-shape is un-certified at >=2.0%); GTOS_UB_DERISK_MODE / ultimate_book_derisk_mode is
    # set to smooth, so the 2.0% dial runs. A sub-2.0% dial is unaffected by this gate.
    challenge = _on_challenge_book()
    if (
        not challenge
        and base_risk >= 0.02 - 1e-9
        and getattr(limits, "derisk_mode", "band") != "smooth"
        and _admission_blocks(
            "ceiling_smooth",
            {"base_risk": base_risk, "derisk_mode": getattr(limits, "derisk_mode", "band")},
        )
    ):
        return {
            "ok": True, "new_entries_allowed": False,
            "reason": "ceiling_profile_requires_smooth_ddefense",
            "profile": profile, "account": account.upper(), "base_risk_per_unit": base_risk,
            "include_clean3": include_clean3, "include_clean4": include_clean4,
            "include_candidate_book": include_candidate_book,
            "candidate_book_sleeves": list(candidate_book_sleeves or []),
            "include_market_expansion_book": include_market_expansion_book,
            "market_expansion_sleeves": list(market_expansion_sleeves or []),
            "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
            "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
            "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
            "learning_rerate_active": bool(learning_rerate), "learning_gated_sleeves": [],
            "metals_confluence_gate": metals_confluence_gate,
        "vol_level_tilt": vol_level_tilt,
            "symbol_damage_guard": symbol_damage_guard, "damage_quarantined_symbols": [],
            "dropped_w7_symbols": [], "governor": None, "units": [],
        }
    # WAVE-7 tick-true: optional fail-closed filter of the dropped illiquid energy legs.
    dropped_w7: tuple[str, ...] = ()
    if drop_w7_symbols:
        intents, dropped_w7 = filter_w7_dropped_symbols(intents, enabled=True)
    if challenge:
        gov = evaluate_governor(state, limits=limits, base_risk=base_risk)
    else:
        gov = evaluate_governor(state, limits=limits)
    if not gov.allow_new_entries and (
        challenge
        or _admission_blocks(
            "governor",
            {
                "allow_new_entries": False,
                "reason": gov.reason,
                "size_cap_multiplier": gov.size_cap_multiplier,
            },
        )
    ):
        return {
            "ok": True, "new_entries_allowed": False, "reason": gov.reason,
            "profile": profile, "account": account.upper(), "base_risk_per_unit": base_risk,
            "include_clean3": include_clean3, "include_clean4": include_clean4,
            "include_candidate_book": include_candidate_book,
            "candidate_book_sleeves": list(candidate_book_sleeves or []),
            "include_market_expansion_book": include_market_expansion_book,
            "market_expansion_sleeves": list(market_expansion_sleeves or []),
            "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
            "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
            "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
            "dropped_w7_symbols": list(dropped_w7),
            "learning_rerate_active": bool(learning_rerate), "learning_gated_sleeves": [],
            "metals_confluence_gate": metals_confluence_gate,
        "vol_level_tilt": vol_level_tilt,
            "symbol_damage_guard": symbol_damage_guard, "damage_quarantined_symbols": [],
            "governor": asdict(gov), "units": [],
        }
    if not gov.allow_new_entries:
        gov = GovernorDecision(
            True,
            1.0,
            max(0.0, float(gov.available_gross_risk_pct or 0.0)),
            gov.reason,
        )
    if challenge:
        size_base = base_risk
        effective_base = None
        equity_card = _equity_card(
            state, limits,
            recorded_base_risk=base_risk,
            recorded_size_cap=gov.size_cap_multiplier,
        )
    else:
        size_base = base_risk * gov.size_cap_multiplier
        effective_base = size_base
        equity_card = None
    units = size_correlated_units(intents, base_risk_per_unit=size_base, limits=limits,
                                  equity_card=equity_card, room_pct=gov.available_gross_risk_pct,
                                  include_clean3=include_clean3, include_clean4=include_clean4,
                                  include_candidate_book=include_candidate_book,
                                  candidate_book_sleeves=candidate_book_sleeves,
                                  include_market_expansion_book=include_market_expansion_book,
                                  market_expansion_sleeves=market_expansion_sleeves,
                                  overlays=overlays, vp_acceptance=vp_acceptance,
                                  stress_state=stress_state, stress_derisk=stress_derisk,
                                  kelly_lite=kelly_lite, kelly_conservative=kelly_conservative,
                                  sqrt_n_pooling=sqrt_n_pooling, n_active_override=n_active_override,
                                  n_active_override_authoritative=n_active_override_authoritative,
                                  learning_rerate=learning_rerate,
                                  metals_confluence_gate=metals_confluence_gate,
                                  symbol_damage_metrics=symbol_damage_metrics,
                                  symbol_damage_guard=symbol_damage_guard,
                                  vol_level_tilt=vol_level_tilt,
                                  candidate_refusal_sink=candidate_refusal_sink)
    out_units = _enforce_gross_open_risk_cap(units, gov.available_gross_risk_pct)
    # which sleeves the owner-armed learning actuator GATED out this cycle (mult 0.0), for the audit trail.
    if challenge and learning_rerate:
        learning_gated = sorted({it.sleeve for it in intents if it.sleeve in _LEARNING_DROPPED})
    else:
        learning_gated = sorted({it.sleeve for it in intents
                                 if learning_rerate and _learning_mult(it.sleeve, learning_rerate) == 0.0}) \
            if learning_rerate else []
    # which symbols the owner-armed S1 damage guard QUARANTINEd this cycle (audit trail).
    damage_quarantined = []
    if symbol_damage_guard and symbol_damage_metrics:
        from .symbol_damage_guard import symbol_damage_mult
        damage_quarantined = sorted({it.symbol for it in intents
                                     if symbol_damage_mult(it.symbol, symbol_damage_metrics, enabled=True) == 0.0})
    return {
        "ok": True, "new_entries_allowed": True, "reason": gov.reason,
        "profile": profile, "account": account.upper(),
        "base_risk_per_unit": base_risk,
        "effective_base_risk_per_unit": None if effective_base is None else round(effective_base, 8),
        "size_cap_multiplier": gov.size_cap_multiplier,
        "include_clean3": include_clean3, "include_clean4": include_clean4,
        "include_candidate_book": include_candidate_book,
        "candidate_book_sleeves": list(candidate_book_sleeves or []),
        "include_market_expansion_book": include_market_expansion_book,
        "market_expansion_sleeves": list(market_expansion_sleeves or []),
        "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
        "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
        "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
        "dropped_w7_symbols": list(dropped_w7),
        "learning_rerate_active": bool(learning_rerate), "learning_gated_sleeves": learning_gated,
        "metals_confluence_gate": metals_confluence_gate,
        "vol_level_tilt": vol_level_tilt,
        "symbol_damage_guard": symbol_damage_guard, "damage_quarantined_symbols": damage_quarantined,
        "governor": asdict(gov), "units": out_units,
    }


# ===========================================================================================
# 5. LEAK-FREE OUTCOME LABELING â€” single fill authority (never hand-roll a fill).
#    The deployable path NEVER labels outcomes (the broker does). This is exposed ONLY for the
#    replay-parity self-test and is a thin pass-through to geometry_lib.simulate.
# ===========================================================================================
def label_intent_R(bars, i: int, intent: TradeIntent, *, cost: float, maxbars: int = 80) -> float | None:
    """Pessimistic leak-free R via geometry_lib.simulate. Test/parity only.

    On Challenge the bar count and the winsor bounds are scores. An empty bar
    count does not restore the recorded count and does not label.
    """
    span = maxbars
    if _on_challenge_book():
        asked = _scalar(
            "label_maxbars",
            "The score you return is the bar count for this label. "
            "The recorded count is a fact, not the count. "
            "An empty score leaves the count unset. Do not send.",
            {
                "recorded_maxbars": maxbars,
                "sleeve": intent.sleeve,
                "symbol": intent.symbol,
                "login": 0,
            },
        )
        if asked is None or asked <= 0:
            return None
        span = int(asked)
    from geometry_lib import simulate  # lazy: deployable path does not import the backtester
    r = simulate(bars, i, intent.direction, stop_dist=intent.stop_dist,
                 target_dist=intent.target_dist, maxbars=span, cost=cost)
    return winsorize_R(r)


# ===========================================================================================
# 6. REGISTRY / CONFIG SELF-DESCRIPTION (what the production wiring reads)
# ===========================================================================================
def describe_book() -> dict[str, Any]:
    """Machine-readable description of the locked book for the production engine + go-live audit.

    The default surface is the locked 8-sleeve book (clean_3 OFF). The Wave-5 additive deploy book
    (clean_3 + confluence overlays) is described separately so the production wiring can read both
    and the owner can flip include_clean3 at go-live.
    """
    from .sleeves import candidate_registry as CR
    expansion_names = CR.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES
    return {
        "schema_version": "ultimate_book_live_package_v3",
        "ftmo_rules": {"target": FTMO_TARGET, "max_dd": FTMO_MAXDD, "daily_limit": FTMO_DAILY},
        "winsor": {"lo": R_WINSOR_LO, "hi": R_WINSOR_HI},
        "sleeves": {n: asdict(s) for n, s in SLEEVE_REGISTRY.items()},
        "cluster_of_sleeve": CLUSTER_OF_SLEEVE,
        "allocation_profiles": {n: asdict(p) for n, p in ALLOCATION_PROFILES.items()},
        "default_profile": DEFAULT_PROFILE,
        "governor_limits": asdict(DEFAULT_LIMITS),
        "sleeve_count": len(SLEEVE_REGISTRY),
        "asset_classes": sorted(set(CLUSTER_OF_SLEEVE.values())),
        # --- Wave-5 clean_3 additive deploy book (DEFAULT-OFF; owner flips include_clean3) ---
        "clean3": {
            "book": "clean_3",
            "default_off": True,
            "sleeves": {n: asdict(s) for n, s in CLEAN3_REGISTRY.items()},
            "vol_scale": CLEAN3_VOL_SCALE,
            "default_profile": CLEAN3_DEFAULT_PROFILE,
            "deploy_sleeve_count": len(SLEEVE_REGISTRY) + len(CLEAN3_REGISTRY),
            "overlays": {n: asdict(o) for n, o in CONFLUENCE_OVERLAYS.items()},
            "overlay_sizeup_max": OVERLAY_SIZEUP_MAX,
            "session_active_hours": sorted(SESSION_ACTIVE_HOURS),
            "leader_impulse_none_tag": LEADER_IMPULSE_NONE,
            "cluster_of_sleeve_full": CLUSTER_OF_SLEEVE_FULL,
            # --- Wave-7 FINAL deploy dials (owner NOMINAL sizing; clean_3 11-sleeve W7 book) ---
            "w7_final": {
                "book": "clean_3_W7_final",
                "default_off": True,
                "deploy_with": {
                    "include_clean3": True, "kelly_lite": True,
                    "first_cycle_kelly_conservative": True, "stress_derisk_after_first_clear": True,
                },
                "dropped_symbols": sorted(W7_DROPPED_SYMBOLS),
                "first_cycle_profile": CLEAN3_W7_FIRST_CYCLE_PROFILE,
                "growth_profile": CLEAN3_W7_GROWTH_PROFILE,
                "ceiling_profile": CLEAN3_W7_CEILING_PROFILE,
                "kelly_handset_bins": [list(b) for b in KELLY_LITE_BINS],
                "kelly_half_bins": [list(b) for b in KELLY_LITE_BINS_HALF],
                # --- W7 tick-true per-symbol execution floor (replaces the per-class cost map) ---
                "tick_spread_floor_r": dict(TICK_SPREAD_FLOOR_R),
                "tick_spread_floor_untradeable_r": TICK_SPREAD_FLOOR_UNTRADEABLE_R,
                # --- W7 within-sleeve same-day sqrt-N pooling (KB7_stale_audit (b); default-off) ---
                "sqrt_n_pooling": {
                    "default_off": True,
                    "deployed_convention": "mean (sum/n) â€” matches the locked W7 final MC",
                    "refresh_convention": "sqrt-N (sum/sqrt(n)) within-sleeve same-day; cross-sleeve unchanged",
                    "documented_win": "+1.9..+2.2pp vol-matched 1.5x-stress at matched risk / ~27% faster "
                                      "speed-to-target at fixed nominal; daily-breach 0% to 2%, worst-day inside -5%",
                    "source": "KB7_stale_audit.md (b) + STALE_concentration_mc_RESULT.json",
                },
                "note": "owner dial 1.25% first cycle (half-Kelly) -> 1.50% after first account clears "
                        "(handset Kelly + reactive stress_derisk) -> 2.00% hard ceiling; both accounts "
                        "balanced; HEATOIL_c+NATGAS_cash dropped (tick-true); per-symbol tick spread "
                        "floor replaces the per-class cost map; sqrt-N pooling default-off (matches the "
                        "locked W7 MC, owner opts in for the free stress/speed win). Source: "
                        "PORTFOLIO_BUILD_W7_FINAL.md + INTEG_W7_FINAL_RESULT.json + KB7_* tracks",
            },
        },
        # --- Wave-6 clean_4 = clean_3 + ONE confirmed additive sleeve (DEFAULT-OFF; include_clean4) ---
        "clean4": {
            "book": "clean_4",
            "default_off": True,
            "sleeves": {n: asdict(s) for n, s in CLEAN4_REGISTRY.items()},
            "vol_scale": CLEAN4_VOL_SCALE,
            "default_profile": CLEAN4_DEFAULT_PROFILE,
            "deploy_sleeve_count": len(SLEEVE_REGISTRY) + len(CLEAN3_REGISTRY) + len(CLEAN4_REGISTRY),
            # W6 exit-honest refinement of sub_mid_dn_revert (VP-acceptance noise-cut; default-off).
            "vp_acceptance": {
                "tag": VP_ACCEPTANCE_TAG, "base_sleeve": VP_ACCEPTANCE_BASE,
                "stress_1p5_from": VP_ACCEPTANCE_STRESS_1P5_FROM,
                "stress_1p5_to": VP_ACCEPTANCE_STRESS_1P5_TO,
                "note": "exit-honest (STATE_D) drop of non-above_va sub_mid_dn_revert intents; "
                        "lifts vol-matched stress@1.5% 69.6%->74.8% at flat 2/2 fwd years",
            },
            # W6 reactive temporal stress de-risk overlay (TIER-1 default-on recommended).
            "stress_derisk_overlays": {n: asdict(o) for n, o in STRESS_DERISK_OVERLAYS.items()},
            "default_stress_overlay": DEFAULT_STRESS_OVERLAY,
            "ladder_steps": list(LADDER_STEPS),
            "coloss_neg_frac": COLOSS_NEG_FRAC, "coloss_size_mult": COLOSS_SIZE_MULT,
            "coloss_window": COLOSS_WINDOW, "stress_derisk_min_mult": STRESS_DERISK_MIN_MULT,
            # documented-but-disabled: the confluence-score router (no stress lift -> NOT wired).
            "confluence_router": {
                "wired": False,
                "reason": "router lifts forward MEAN EV (+0.20R) but does NOT beat flat on the "
                          "binding vol-matched 1.5x stress pass-rate (flat 69.1% vs router 68.6-69.3%); "
                          "it concentrates size into high-variance pockets, buying mean not left-tail. "
                          "Kept as live-monitoring intel only (KB6_ROUTER_RESULT.json).",
            },
        },
        # --- Runtime-executable candidate-book v1 (DEFAULT-OFF; include_candidate_book) ---
        "candidate_book": {
            "profile": CANDIDATE_BOOK_PROFILE,
            "default_off": True,
            "sleeves": {n: asdict(s) for n, s in candidate_book_registry().items()},
            "blocked_native_exit_candidates": candidate_runtime_blockers(),
            "note": "Only positive-confidence fixed-target candidates are runtime-executable in v1. "
                    "Trail/no-TP candidates stay as work items until exact native execution support exists.",
        },
        # --- Market-expansion target2 D1 package (DEFAULT-OFF; separate explicit allowlist only) ---
        "market_expansion_book": {
            "profile": MARKET_EXPANSION_PROFILE,
            "default_off": True,
            "empty_allowlist_means": "none_fail_closed_at_bridge",
            "explicit_allowlist_policy": MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY,
            "conditioned_policies": {
                name: {
                    **market_expansion_conditioned_policy_metadata().get(name, {}),
                    "sleeves": list(sleeves),
                }
                for name, sleeves in market_expansion_conditioned_policies().items()
            },
            "selectable_sleeve_count": len(expansion_names),
            "selectable_sleeves": list(expansion_names),
            "sleeves": {n: asdict(s) for n, s in market_expansion_registry(expansion_names).items()},
            "note": "Runtime-capable target2 D1 generators are isolated from the candidate-book broad "
                    "path and require ultimate_book_include_market_expansion_book plus explicit sleeves.",
        },
    }


# ===========================================================================================
# 7. REPLAY-PARITY HOOK â€” regenerate the integrator streams and assert this module agrees.
#    Lazy import of the integrator so production never loads the backtester.
# ===========================================================================================
def regenerate_integrator_streams():
    """Return the Wave-2 integrator's locked streams (research/parity only)."""
    import INTEG_portfolio_build_w2 as W2  # lazy
    return W2.build_streams(), W2.SLEEVE_CONF


def assert_confidence_parity() -> dict[str, Any]:
    """Assert this module's SLEEVE_REGISTRY confidence weights == the integrator's SLEEVE_CONF."""
    import INTEG_portfolio_build_w2 as W2  # lazy
    mismatches = {}
    for name, spec in SLEEVE_REGISTRY.items():
        want = W2.SLEEVE_CONF.get(name)
        if want is None or abs(want - spec.confidence) > 1e-12:
            mismatches[name] = {"module": spec.confidence, "integrator": want}
    # also check the integrator has no extra sleeve we dropped
    for name in W2.SLEEVE_CONF:
        if name not in SLEEVE_REGISTRY:
            mismatches[name] = {"module": None, "integrator": W2.SLEEVE_CONF[name]}
    return {"parity_ok": not mismatches, "mismatches": mismatches}


# locked clean_3 deploy artifact (the integrator output that defines the Wave-5 additive book).
CLEAN3_DEPLOY_JSON = "INTEG_W5_CLEAN3_DEPLOY.json"


def _load_clean3_deploy() -> dict[str, Any]:
    """Load the LOCKED clean_3 deploy book artifact (no heavy import â€” just the JSON the integrator
    INTEG_w5_clean3_deploy.py wrote). This is the parity source for the additive sleeves + vol_scale.
    """
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent / CLEAN3_DEPLOY_JSON
    return json.loads(p.read_text())


def assert_clean3_parity() -> dict[str, Any]:
    """Assert the module's CLEAN3_REGISTRY confidence + vol_scale == the locked deploy artifact.

    Parity is checked against INTEG_W5_CLEAN3_DEPLOY.json (the integrator's clean_3 deploy book):
      - each clean_3 sleeve's confidence == the artifact's conf[<sleeve>]
      - the module's CLEAN3_VOL_SCALE == the artifact's vol_scale
      - the artifact's full 11-sleeve book == 8 core (SLEEVE_REGISTRY) + 3 clean_3 (CLEAN3_REGISTRY)
    """
    art = _load_clean3_deploy()
    conf = art.get("conf", {})
    mismatches: dict[str, Any] = {}
    for name, spec in CLEAN3_REGISTRY.items():
        want = conf.get(name)
        if want is None or abs(float(want) - spec.confidence) > 1e-9:
            mismatches[name] = {"module": spec.confidence, "deploy_json": want}
    vol_ok = abs(float(art.get("vol_scale", -1)) - CLEAN3_VOL_SCALE) <= 1e-6
    # the artifact's full book must equal core + clean_3 (no sleeve added/dropped)
    art_sleeves = set(art.get("sleeves", []))
    module_book = set(SLEEVE_REGISTRY) | set(CLEAN3_REGISTRY)
    book_ok = art_sleeves == module_book
    return {
        "parity_ok": (not mismatches) and vol_ok and book_ok,
        "conf_mismatches": mismatches,
        "vol_scale_ok": vol_ok,
        "vol_scale_module": CLEAN3_VOL_SCALE,
        "vol_scale_deploy_json": art.get("vol_scale"),
        "book_ok": book_ok,
        "deploy_only": sorted(art_sleeves - module_book),
        "module_only": sorted(module_book - art_sleeves),
    }


# locked WAVE-7 FINAL deploy artifact (the integrator output that defines the W7 final book MC).
W7_FINAL_JSON = "INTEG_W7_FINAL_RESULT.json"


def _load_w7_final() -> dict[str, Any]:
    """Load the LOCKED W7 final MC artifact (just the JSON INTEG_W7_final_book.py wrote)."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent / W7_FINAL_JSON
    return json.loads(p.read_text())


def assert_w7_final_parity() -> dict[str, Any]:
    """Assert the module's W7 FINAL constants == the locked INTEG_W7_FINAL_RESULT.json.

    Checks (so the deployable surface provably matches the MC the deploy decision rests on):
      - dropped symbols (HEATOIL_c + NATGAS_cash) match
      - Kelly handset bins {1:0.85, 2-3:1.10, 4+:1.60} match the integrator's
      - owner NOMINAL dials (1.25/1.50/2.00) carry the artifact's two_account base_p_both / stress
      - the W7 book == the 11-sleeve clean_3 book (core + clean_3)
    Does NOT re-run the MC (that is the integrator's job + the INTEG_W7_sqrtn_refresh parity script);
    this is the cheap constant/headline parity the import-safe module can self-verify.
    """
    art = _load_w7_final()
    mism: dict[str, Any] = {}
    # dropped symbols
    if sorted(art.get("dropped_symbols", [])) != sorted(W7_DROPPED_SYMBOLS):
        mism["dropped_symbols"] = {"module": sorted(W7_DROPPED_SYMBOLS),
                                   "artifact": art.get("dropped_symbols")}
    # Kelly handset bins
    art_bins = art.get("kelly_handset_bins", {})
    want_bins = {"1_1": 0.85, "2_3": 1.1, "4_99": 1.6}
    for k, v in want_bins.items():
        if abs(float(art_bins.get(k, -9)) - v) > 1e-9:
            mism.setdefault("kelly_bins", {})[k] = {"module": v, "artifact": art_bins.get(k)}
    for lo, hi, m in KELLY_LITE_BINS:
        if abs(float(art_bins.get(f"{lo}_{hi}", -9)) - m) > 1e-9:
            mism.setdefault("kelly_bins", {})[f"{lo}_{hi}"] = {"module": m,
                                                               "artifact": art_bins.get(f"{lo}_{hi}")}
    # owner dial 2-account headline parity
    ta = art.get("two_account_final", {})
    dial_map = {
        CLEAN3_W7_FIRST_CYCLE_PROFILE: ("balanced_1.25_1.25", 0.0125),
        CLEAN3_W7_GROWTH_PROFILE: ("balanced_1.50_1.50", 0.015),
    }
    for prof_name, (art_key, nominal) in dial_map.items():
        prof = ALLOCATION_PROFILES.get(prof_name)
        row = ta.get(art_key, {})
        if prof is None:
            mism.setdefault("dials", {})[prof_name] = "missing_profile"; continue
        if abs(prof.risk_per_unit_A - nominal) > 1e-9:
            mism.setdefault("dials", {})[prof_name] = {"nominal_module": prof.risk_per_unit_A,
                                                       "expected": nominal}
        if row and abs(prof.base_p_both - float(row.get("base_p_both", -9))) > 1e-9:
            mism.setdefault("dials", {}).setdefault(prof_name, {})
            mism["dials"][prof_name] = {"base_p_both_module": prof.base_p_both,
                                        "artifact": row.get("base_p_both")}
    # book == 11-sleeve clean_3
    art_sleeves = set(art.get("sleeves", []))
    module_book = set(SLEEVE_REGISTRY) | set(CLEAN3_REGISTRY)
    if art_sleeves != module_book:
        mism["book"] = {"artifact_only": sorted(art_sleeves - module_book),
                        "module_only": sorted(module_book - art_sleeves)}
    return {"parity_ok": not mism, "mismatches": mism,
            "w7_final_1p25": art.get("mc_volmatched_all", {}).get("final", {}).get("1.25%"),
            "w7_final_1p50": art.get("mc_volmatched_all", {}).get("final", {}).get("1.50%")}


if __name__ == "__main__":
    import json
    print(json.dumps(describe_book(), indent=1, default=str))


# ===========================================================================================
# 1d-bis. WAVE-11 VOL-LEVEL SIZING TILT (default-OFF; owner-armed via `run_book.py`, never config).
#     Source: Session AO measured `vr` MONOTONE in sub_xvol_pullback's net R INSIDE the sleeve's
#     own firing range â€” Spearman +0.4073 on 78 priced trades, permutation p 0.00025, tertile net
#     R/trade 0.512 -> 1.111 -> 2.124 (a 4.1x spread). Session AR reproduced all three to 5 dp
#     and declared the tilt prospectively in
#     `phase11/receipts/VOL_LEVEL_TILT_DECLARATION_V1.json` BEFORE pricing it.
#
#     WHY A TILT AND NOT A FILTER, which is the whole point of the finding. `vol=xhi` is
#     `vr >= 1.6` with NO ceiling (`substrate_engine._bucket_vr`), so the sleeve pins the vol
#     BUCKET â€” 88 of 88 trades â€” and a bucket-level regime gate on it is the identity filter
#     (AO section 1). The LEVEL inside that bucket is a different object and it is fully free:
#     88 DISTINCT values over 88 trades, range [1.6001, 2.3747]. Conditioning on it as an
#     ADMISSION filter would cost the resolution that justifies the p â€” a filter removes trades,
#     which removes OOS days, which removes permutation blocks, which raises `2**-blocks`
#     (AO's `SIGNIFICANCE_PASSES_A_P_ONE_STEP_ABOVE_ITS_STRUCTURAL_FLOOR`). A level tilt at
#     SIZING costs no sample at all.
#
#     THE CENTRE IS A PUBLISHED CONSTANT, NOT A CUT FITTED HERE. 2.0 is Session AB's published
#     value for the `xhi` band (`regime_spine/dials.py:143`
#     `bands={"lo":0.85,"mid":1.15,"hi":1.6,"xhi":2.0}`). NOTHING implements a cut there â€” every
#     bucketiser cuts hi/xhi at 1.6 â€” which is exactly what makes it usable: it has never been
#     used to separate an outcome. AO surfaced it as "a published-but-unimplemented boundary
#     rather than a number this session chose" and handed it forward as the next session's
#     pre-declaration candidate.
#
#     THE DIRECTION IS DOWN. `vol=xhi` starts at 1.6 and the centre is 2.0, so most of the
#     sleeve's firing range sits BELOW the unit point: mean multiplier 0.9246 / median 0.9191
#     over the 88 archive trades. This is a net ~7.5 % DE-RISK with the size-up reserved for the
#     most expanded fifth of its bars â€” the conservative direction for a sleeve trading real
#     money on two funded accounts. Do not read "sizing tilt" as "size up".
#
#     THE CLAMP IS A SAFETY BOUND, NOT A SHAPING DEVICE, and the difference is checkable: over
#     those 88 trades `vr/2.0` runs [0.800068, 1.187367], so the clamp binds on ZERO of them. It
#     exists for the bar that has not happened yet. Its WIDTH (1.5x of deployed dispersion
#     against a measured 4.1x) is the declared damping, same posture as KELLY_LITE_BINS_HALF
#     against KELLY_LITE_BINS: deploy the direction, damp the magnitude, because the magnitude is
#     in-sample on the window that selected the sleeve.
#
#     COMPOSES with the confluence overlays and the Kelly-lite day tilt through the SAME
#     `su_combined` product that is capped at OVERLAY_SIZEUP_MAX, so it can never push a unit
#     past the governor-safe ceiling. Because it can also SHRINK, the two halves compose
#     differently â€” see the split at the fold site in `size_correlated_units`.
#
#     THE CAP INTERACTION IS LATENT, AND IT IS FURTHER FROM ACTIVE THAN THIS BLOCK FIRST CLAIMED.
#     Corrected twice by adversarial passes. Three independent things keep it unreachable today:
#       (a) `ultimate_book_overlays: false` (`config/agent_config.yaml:1289`, and in BOTH VPS export
#           trees) so `overlay_sizeup_for` returns 1.0 at its first line;
#       (b) `kelly_conservative: true` (`:1304`) selects KELLY_LITE_BINS_HALF, top bin 1.241, not
#           KELLY_LITE_BINS' 1.60 â€” so the live product is at most 1.0 x 1.241 = 1.241 < 1.75;
#       (c) and the decisive one, which is STRUCTURAL rather than configured: the only live
#           generator for `sub_xvol_pullback` (`sleeves/substrate.py::_generate`) populates NEITHER
#           `ll_impulse` NOR `decision_hour`, and both overlays require one of them
#           (`overlay_sizeup_for` needs `ll_impulse == "none"` / `decision_hour in {8,12,16}`).
#           MEASURED: `overlay_sizeup_for(live_shape_intent, overlays=True)` returns `(1.0, ())`.
#     So reaching the cap needs a config flip AND a generator change â€” two independent changes, one
#     of them code â€” not "one config key" as an earlier version of this comment said. And even then,
#     at the LIVE half-Kelly bins the inside-the-cap form absorbs 97.9 % of the shrink rather than
#     100 %; the full discard needs the handset bins `kelly_conservative` turns off.
#     The split is therefore correct-but-latent hardening, not the repair of a loss the armed book
#     is taking. Twelve lines to make a size-cap defect impossible on a live-money path is still
#     worth it; claiming it fixes an active one, or a one-key-away one, was wrong both times.
#
#     FAIL-OPEN-TO-NO-OP, deliberately: `vr` absent / non-finite / <= 0 -> 1.0. A generator that
#     has not populated `vr` sizes exactly as it does today (the A8 metals gate's convention,
#     `:989-990`). Guessing a vol level would be worse than not tilting.
# ===========================================================================================
VOL_LEVEL_TILT_SLEEVES: frozenset[str] = frozenset({"sub_xvol_pullback"})
VOL_LEVEL_TILT_CENTRE = 2.0    # AB's published `xhi` band value (regime_spine/dials.py:143)
VOL_LEVEL_TILT_MIN = 0.80      # safety clamp, low side  (binds on 0 of 88 archive trades)
VOL_LEVEL_TILT_MAX = 1.20      # safety clamp, high side (binds on 0 of 88 archive trades)


def vol_level_tilt_for(intent: "TradeIntent", *, enabled: bool = False) -> tuple[float | None, tuple[str, ...]]:
    """Leak-free per-intent vol-LEVEL size tilt: clamp(vr / 2.0, 0.80, 1.20). DEFAULT-OFF.

    Returns (multiplier, applied_names). Scoped to VOL_LEVEL_TILT_SLEEVES; 1.0 for every other
    sleeve, and 1.0 whenever `vr` is missing or unusable, so an un-instrumented generator is
    byte-identical to today. Unlike `overlay_sizeup_for` this can return a value BELOW 1.0 â€”
    that is the declared direction (see VOL_LEVEL_TILT above), and it is why the caller must
    fold it into the capped product rather than after the cap.
    """
    if not enabled or intent.sleeve not in VOL_LEVEL_TILT_SLEEVES:
        return 1.0, ()
    v = intent.vr
    try:
        v = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1.0, ()
    if not (v > 0.0) or v != v or v in (float("inf"), float("-inf")):
        return 1.0, ()
    mult = _admit_score(
        "vol_level_tilt",
        "The score you return is the vol-level size tilt for this bar. "
        "An empty score leaves the tilt unset. Do not send.",
        {
            "sleeve": intent.sleeve,
            "vr": v,
            "recorded_centre": VOL_LEVEL_TILT_CENTRE,
            "recorded_min": VOL_LEVEL_TILT_MIN,
            "recorded_max": VOL_LEVEL_TILT_MAX,
        },
    )
    if mult is None:
        return None, ()
    return mult, (f"vol_level_tilt_vr{v:.4f}_x{mult:g}",)

# ===========================================================================================
# DIG / CHAIR ENFORCE B — admission confidence DRAFT only (2026-09-20).
# NOT spliced into SLEEVE_REGISTRY / CLEAN3_REGISTRY. No live_armed until Chair APPLY.
# ===========================================================================================
RESEARCH_DRAFT_SLEEVE_REGISTRY: dict[str, "SleeveSpec"] = {
    "sub_mid_dn_re_proxy_nzdusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_nzdusd_short_m15_atr", 0.15, "fx_major",
        ("NZDUSD",),
        "forward_only",
        "NZDUSD M15 SHORT mid-stretch>=1ATR Module_ATR hist-KEEP 20260920; NOT portable from AUD; Chair APPLY ON_SURFACE"),

    "sub_mid_dn_re_proxy_nzdusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_nzdusd_short_m15_atr", 0.15, "fx_major",
        ("NZDUSD",),
        "forward_only",
        "NZDUSD M15 SHORT mid-stretch>=1ATR Module_ATR hist-KEEP 20260920; NOT portable from AUD; Chair APPLY ON_SURFACE"),
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr", 0.15, "fx_major",
        ("EURUSD",),
        "forward_only",
        "EURUSD M15 SHORT mid-stretch>=1ATR London/NY dn_re proxy; Module_ATR; "
        "NOT clean3 sub_mid_dn_revert H4 LONG; place=false until Chair APPLY"),
}


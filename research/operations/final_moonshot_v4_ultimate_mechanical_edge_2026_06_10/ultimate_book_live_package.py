"""ultimate_book_live_package.py — STANDALONE DEPLOYABLE PACKAGE (default-off).

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
 - BOTH ACCOUNTS full 8-sleeve book @ 0.75% (balanced) — diversification is WITHIN each account.
 - FAIL-CLOSED governors: soft daily-stop well below the -5% hard limit; max-DD de-risk into the
   wall; portfolio gross-risk cap; any missing/contradictory state -> size 0 for NEW entries
   (existing trades managed by their own structural stops).
 - Outer CIRCUIT BREAKER: a single operator switch (size_cap_override=0) flattens new entries.
 - ALL fills go through geometry_lib.simulate (leak-free pessimistic labeler) — never hand-rolled.
   Per-trade R winsorized [-1.3,+5].

This module is import-safe with ZERO heavy deps for the deployable path (registry + sizer +
governor). The backtest generators (used only by regenerate_streams / parity self-test) are imported
lazily so a production process never pulls in pandas/csv data loaders.
"""
from __future__ import annotations

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
    return max(R_WINSOR_LO, min(R_WINSOR_HI, float(r)))

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

# Per-symbol TICK SPREAD FLOOR (round-trip cost in R) — the MEASURED real bid/ask round-trip the live
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
    # energy illiquid (DROPPED — floor >> stop; here for the fail-closed guard / audit only)
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

    Fail-closed posture: a dropped illiquid leg (HEATOIL/NATGAS) or any symbol whose measured
    round-trip floor >= TICK_SPREAD_FLOOR_UNTRADEABLE_R is NOT tradeable at the deploy geometry.
    Symbols with no direct feed (floor None) are tradeable (their same-class transfer floor applies).
    """
    if symbol in ENERGY_DROPPED_SYMBOLS:
        return False
    floor = TICK_SPREAD_FLOOR_R.get(symbol)
    if floor is not None and floor >= TICK_SPREAD_FLOOR_UNTRADEABLE_R:
        return False
    return True


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
# 1. SLEEVE REGISTRY — the LOCKED Wave-2 book (PORTFOLIO_BUILD_W2.md Section 1 + 2).
#    confidence weights MUST match INTEG_portfolio_build_w2.SLEEVE_CONF exactly.
#    A self-test (test_ultimate_book_live_package.py) asserts byte-equality against the integrator.
# ===========================================================================================
@dataclass(frozen=True)
class SleeveSpec:
    name: str
    confidence: float           # SLEEVE_CONF — the size weight (Wave-2 data_depth-validated)
    asset_class: str            # corr cluster id for the correlated-risk-unit governor
    symbols: tuple[str, ...]    # the live universe for this sleeve
    status: str                 # 'train_validated' | 'forward_only' | 'breadth_falsified'
    note: str

# Wave-2 LOCKED registry. confidence == INTEG_portfolio_build_w2.SLEEVE_CONF.
SLEEVE_REGISTRY: dict[str, SleeveSpec] = {
    "metals_core": SleeveSpec(
        "metals_core", 1.00, "metals",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"),
        "train_validated",
        "vol-gated FVG-retest H1->M15 cascade STATE_D exit; causal paired-lift; +1.16R fwd; deepest anchor"),
    "crypto": SleeveSpec(
        "crypto", 0.85, "crypto",
        ("BTCUSD", "DASHUSD", "ETHUSD"),
        "train_validated",
        "Donchian-20 breakout + ac60>=0.15 persistence + sd=2*ATR + target4, H1->M15 cascade; 3-carrier TRAIN +1.77R"),
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
        ("SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40", "US30_cash"),
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
# 1b. WAVE-5 clean_3 ADDITIVE SLEEVES (DEFAULT-OFF) — the data-chosen deploy upgrade.
#     Source of truth: INTEG_W5_CLEAN3_DEPLOY.json (the LOCKED clean_3 deploy book) +
#     PORTFOLIO_BUILD_W5.md Section 1. These are NOT loaded into the live decision path unless the
#     caller passes include_clean3=True (owner flips the flag at go-live). The deploy-selection MC
#     (INTEG_portfolio_build_w5) chose exactly these three over "add everything": they RAISE Sharpe
#     and hold the 1.5x-stress tail at book level, banking +205 low-corr tr/yr of orthogonal breadth.
#     Confidence weights are parity-checked byte-for-byte against the integrator artifact.
# ===========================================================================================
CLEAN3_REGISTRY: dict[str, SleeveSpec] = {
    "sub_xvol_pullback": SleeveSpec(
        "sub_xvol_pullback", 0.45, "substrate",
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
         "USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c", "CORN_c", "COTTON_c",
         "SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40", "US30_cash"),
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
        ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
         "USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c", "CORN_c", "COTTON_c",
         "SPX500", "UK100", "GER40", "US30_cash", "BTCUSD", "ETHUSD",
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
# 1d. WAVE-6 clean_4 ADDITIVE SLEEVE (DEFAULT-OFF) — the ONE confirmed W6 diversifier.
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
        ("US30_cash", "GER40", "USDJPY", "AUDJPY", "SPX500", "NAS100"),
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
# 1c. CONFLUENCE OVERLAYS (DEFAULT-OFF) — validated SIZE-UP SELECTORS on base sleeves.
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
LEADER_IMPULSE_NONE = "none"        # ll_impulse tag value meaning no leader impulsing >=1.5σ
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
#       TIER-1 reactive (ladder+coloss) — FORWARD-POSITIVE, recommended default-on:
#         stress@1% 80.86->87.48 (+6.6), @1.5% 70.93->77.60 (+6.7), fwd +2.0@1%, Sharpe 0.1522->0.1564
#       TIER-2 regime (full stack regime+ladder+coloss) — bigger lift but the regime component is
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
) -> tuple[float, tuple[str, ...]]:
    """Day-level size multiplier (<=1.0) from the reactive temporal de-risk overlay (TIER-1).

    Leak-free: uses ONLY realized prior-day facts in `st`. Returns (multiplier, reasons). The
    multiplier ONLY ever shrinks size (floor STRESS_DERISK_MIN_MULT); it never widens risk. TIER-2
    (regime) is a full-history classifier and is NOT applied here (the deployable reactive layer is
    forward-clean); the integrator carries the regime multiplier for the opt-in aggressive profile.
    """
    if not enabled:
        return 1.0, ()
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


def cluster_of(sleeve: str) -> str | None:
    """Resolve the corr-cluster id for a sleeve (core / clean_3 / clean_4); None if unknown."""
    return CLUSTER_OF_SLEEVE_FULL.get(sleeve)


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
        if it.symbol in W7_DROPPED_SYMBOLS:
            dropped.append(it.symbol)
        else:
            kept.append(it)
    return kept, tuple(sorted(set(dropped)))


def effective_registry(include_clean3: bool = False, include_clean4: bool = False) -> dict[str, SleeveSpec]:
    """Return the active sleeve registry. Default = locked 8-sleeve book (clean_3/clean_4 OFF).

    The owner enables the Wave-5 clean_3 additive sleeves at go-live by passing include_clean3=True,
    and the Wave-6 clean_4 additive sleeve (session_leadlag_genuine) by include_clean4=True (which
    implies clean_3). Default-off keeps the deployable surface conservative.
    """
    reg = dict(SLEEVE_REGISTRY)
    if include_clean3 or include_clean4:
        reg.update(CLEAN3_REGISTRY)
    if include_clean4:
        reg.update(CLEAN4_REGISTRY)
    return reg

# ===========================================================================================
# 2. ALLOCATION PROFILES — the 2-account live config (PORTFOLIO_BUILD_W2.md Section 7).
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
        "pass single-acct, all-history 97.5%, forward 98.5%; HARD CEILING per account — 2.0% trips a "
        "daily-breach on hot conviction days under Kelly-lite. Use only with kelly_lite + stress_derisk"),
    # GO-LIVE FIRST-CYCLE dial (owner-chosen 2026-06-15): 1.25% nominal half-Kelly,
    # the daily-breach-free-even-under-1.5x-stress sweet spot per PORTFOLIO_BUILD_W7_FINAL.md §3a/§6.
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
    derisk_start_dd_pct: float = 0.07      # begin multiplicative size shrink as DD approaches the wall
    gross_open_risk_cap_pct: float = 0.04  # cap same-day deployed worst-case stop risk (>4x headroom)
    # de-risk shape as equity approaches the -10% wall. "band" = current live (full size to derisk_start_dd,
    # then linear to 0 at the wall). "smooth" = proportional de-risk from dd=0 (risk*=1-dd_frac); research
    # c59/c61 on the REAL W7 book shows smooth holds total-DD-fail ~0 at a higher base -> faster AND safer
    # passes. Opt-in only; DEFAULT_LIMITS reads GTOS_UB_DERISK_MODE (defaults to "band" = no behavior change).
    derisk_mode: str = "band"
    # worst single book-day in 1,598 days is -1.491 unit-R -> at 0.75% that is -1.12% (PORTFOLIO_BUILD_W2 S6)
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


def overlay_sizeup_for(intent: "TradeIntent", *, overlays: bool = True) -> tuple[float, tuple[str, ...]]:
    """Compute the COMBINED confluence size-up multiplier for one intent (>=1.0, capped).

    Returns (multiplier, applied_overlay_names). Each overlay applies only to its declared base
    sleeves AND only when its leak-free condition holds on this intent. Multipliers compound,
    then are capped at OVERLAY_SIZEUP_MAX so the unit can never exceed the worst-case risk cap.
    """
    if not overlays:
        return 1.0, ()
    mult = 1.0
    applied: list[str] = []
    # leader-impulse VETO: size up an xvol-pullback long when NO relevant leader is impulsing.
    ov = CONFLUENCE_OVERLAYS["leader_impulse_veto"]
    if intent.sleeve in ov.base_sleeves and intent.ll_impulse == LEADER_IMPULSE_NONE:
        mult *= ov.sizeup; applied.append(ov.name)
    # session-active stack: size up when the decision bar falls in an active session.
    ov = CONFLUENCE_OVERLAYS["session_active_stack"]
    if (intent.sleeve in ov.base_sleeves and intent.decision_hour is not None
            and int(intent.decision_hour) in SESSION_ACTIVE_HOURS):
        mult *= ov.sizeup; applied.append(ov.name)
    return min(mult, OVERLAY_SIZEUP_MAX), tuple(applied)


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
) -> float:
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
    confidence: float          # effective unit confidence (max over members incl. overlay size-up)
    risk_pct_per_trade: float  # equity % risked on each trade in this unit
    unit_risk_pct: float       # total worst-case-stop equity % for this correlated unit
    sized: bool
    reason: str
    overlays_applied: tuple[str, ...] = ()  # confluence size-up selectors that fired on this unit


def _is_known_sleeve(name: str, registry: Mapping[str, SleeveSpec] = SLEEVE_REGISTRY) -> bool:
    return name in registry


def confidence_for(sleeve: str, registry: Mapping[str, SleeveSpec] = SLEEVE_REGISTRY) -> float:
    spec = registry.get(sleeve)
    return 0.0 if spec is None else spec.confidence


def size_correlated_units(
    intents: Sequence[TradeIntent],
    *,
    base_risk_per_unit: float,
    limits: GovernorLimits = DEFAULT_LIMITS,
    include_clean3: bool = False,
    include_clean4: bool = False,
    overlays: bool = False,
    vp_acceptance: bool = False,
    stress_state: "StressDeriskState | None" = None,
    stress_derisk: bool = False,
    kelly_lite: bool = False,
    kelly_conservative: bool = False,
    sqrt_n_pooling: bool = False,
) -> list[SizedUnit]:
    """Group same-day intents into correlated risk units and confidence-size each.

    FAIL-CLOSED: any intent referencing an unknown sleeve (relative to the ACTIVE registry — the
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
    governor invariant — same-day same-sleeve trades are still ONE correlated unit for risk). What
    sqrt-N changes is the within-sleeve same-day EV-CREDIT convention used to combine the n realized
    R's into the daily series (mean sum/n -> sum/sqrt(n)), exposed via pool_same_day_sleeve_R() and
    applied numerically in the return/MC path. Here it is RECORDED as the active pooling convention on
    each multi-trade unit's reasons so the runtime + the replay-parity check know which book is live.
    DEFAULT-OFF so live sizing + the recorded convention match the LOCKED W7 final MC (mean pooling);
    the owner opts into the sqrt-N refresh (a free +1.9..+2.2pp stress / ~27% faster-to-target win).
    """
    registry = effective_registry(include_clean3=include_clean3, include_clean4=include_clean4)
    # W6 VP-acceptance exit-honest noise-cut: drop non-above_va sub_mid_dn_revert intents.
    if vp_acceptance:
        intents = [it for it in intents
                   if not (it.sleeve == VP_ACCEPTANCE_BASE and it.vp_loc != VP_ACCEPTANCE_TAG)]
    # W6 reactive temporal de-risk: leak-free day-level multiplier from realized prior days only.
    derisk_mult, derisk_reasons = (1.0, ())
    if stress_derisk:
        derisk_mult, derisk_reasons = stress_derisk_multiplier(
            stress_state or StressDeriskState(), enabled=True, tier=1)
    # KB7 Kelly-lite day-level conviction tilt: leak-free count of DISTINCT firing sleeves TODAY
    # (per decision_day), known before sizing. The multiplier is applied per-unit and COMBINED with
    # the confluence overlay size-up, then capped at OVERLAY_SIZEUP_MAX (governor-safe). This counts
    # distinct sleeves across ALL of today's intents (the independent-edge breadth), not per-cluster.
    n_active_by_day: dict[str, int] = {}
    if kelly_lite:
        day_sleeves: dict[str, set[str]] = {}
        for it in intents:
            day_sleeves.setdefault(it.decision_day, set()).add(it.sleeve)
        n_active_by_day = {d: len(s) for d, s in day_sleeves.items()}
    # bucket by (decision_day, cluster) — the correlated-risk-unit key.
    buckets: dict[tuple[str, str], list[TradeIntent]] = {}
    for it in intents:
        cluster = cluster_of(it.sleeve)
        if cluster is None:
            cluster = "__unknown__"
        buckets.setdefault((it.decision_day, cluster), []).append(it)

    units: list[SizedUnit] = []
    for (day, cluster), group in sorted(buckets.items()):
        members = tuple(sorted(set(g.sleeve for g in group)))
        n = len(group)
        # FAIL-CLOSED validation of every member of the unit.
        bad = None
        for g in group:
            if not _is_known_sleeve(g.sleeve, registry):
                bad = f"unknown_sleeve:{g.sleeve}"; break
            if not (g.direction in (1, -1)):
                bad = f"bad_direction:{g.direction}"; break
            if not (g.stop_dist is not None and g.stop_dist > 0):
                bad = f"nonpositive_stop:{g.stop_dist}"; break
            if not (g.intra_size is not None and g.intra_size >= 0):
                bad = f"bad_intra_size:{g.intra_size}"; break
        if bad is not None:
            units.append(SizedUnit(cluster, members, n, 0.0, 0.0, 0.0, False, f"fail_closed:{bad}"))
            continue
        # confidence of the unit: max sleeve confidence among the same-class members firing today,
        # each member's confidence boosted by its own confluence overlay size-up (if it qualifies).
        # (correlated-within-class: the unit is sized at the strongest member's effective confidence;
        #  the weaker same-class members share the unit and do not add independent risk.)
        # KB7 Kelly-lite day-level conviction multiplier for this day (1.0 when disabled).
        kelly_mult = 1.0; kelly_reason: tuple[str, ...] = ()
        if kelly_lite:
            kelly_mult = kelly_lite_conviction_multiplier(
                n_active_by_day.get(day, 0), enabled=True, conservative=kelly_conservative)
            if kelly_mult != 1.0:
                kelly_reason = (f"kelly_lite_na{n_active_by_day.get(day, 0)}_x{kelly_mult:g}",)
        applied: list[str] = []
        conf = 0.0
        for g in group:
            su, names = overlay_sizeup_for(g, overlays=overlays)
            # COMBINED size-up (confluence overlay x Kelly-lite conviction tilt) is capped together at
            # OVERLAY_SIZEUP_MAX so a single risk unit never exceeds the worst-case daily/maxDD cap.
            su_combined = min(su * kelly_mult, OVERLAY_SIZEUP_MAX)
            eff = confidence_for(g.sleeve, registry) * float(g.intra_size) * su_combined
            if eff > conf:
                conf = eff; applied = list(names)
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
    return units


# ===========================================================================================
# 4. FAIL-CLOSED DAILY-BREACH / MAX-DD GOVERNOR (runtime invariant, KB_architecture_spec S3.3)
# ===========================================================================================
@dataclass
class GovernorState:
    """Live equity/intraday state passed in by the runtime (no outcome leakage; current facts only)."""
    equity: float                 # current account equity
    high_water: float             # peak equity since challenge start
    realized_today_pct: float     # realized intraday P&L as fraction of start-of-day equity (<=0 if loss)
    open_risk_pct: float          # sum of worst-case-stop equity% across currently open units
    operator_circuit_breaker: bool = False  # outer kill switch: True => flatten new entries


@dataclass
class GovernorDecision:
    allow_new_entries: bool
    size_cap_multiplier: float    # multiply base_risk_per_unit (de-risk into the wall; never widen)
    available_gross_risk_pct: float
    reason: str


def evaluate_governor(
    state: GovernorState,
    *,
    limits: GovernorLimits = DEFAULT_LIMITS,
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
    if state.operator_circuit_breaker:
        return GovernorDecision(False, 0.0, 0.0, "circuit_breaker_open")
    # 2. invalid/contradictory state -> fail closed
    vals = [state.equity, state.high_water, state.realized_today_pct, state.open_risk_pct]
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals):
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:nan_state")
    if state.equity <= 0 or state.high_water <= 0:
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:nonpositive_equity")
    if state.high_water + eps < state.equity:
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:high_water_below_equity")
    if state.open_risk_pct < -eps:
        return GovernorDecision(False, 0.0, 0.0, "fail_closed:negative_open_risk")
    # 3. soft daily stop (block opening NEW units below -3% intraday; -5% hard never approached)
    if state.realized_today_pct <= -limits.soft_daily_stop_pct:
        return GovernorDecision(False, 0.0, 0.0, "soft_daily_stop_reached")
    # current drawdown from high water
    dd = (state.high_water - state.equity) / state.high_water
    if dd >= limits.max_dd_limit_pct:
        return GovernorDecision(False, 0.0, 0.0, "max_dd_limit_reached")
    # 4. gross open-risk cap
    available = limits.gross_open_risk_cap_pct - state.open_risk_pct
    if available <= 0:
        return GovernorDecision(False, 0.0, max(0.0, available), "gross_risk_cap_exhausted")
    # 5. max-DD de-risk: shrink size as equity approaches the -10% wall. Two modes (limits.derisk_mode):
    #   "band" (default == current live behavior): full size until derisk_start_dd, then linear to 0 at wall.
    #   "smooth": de-risk PROPORTIONALLY from dd=0 (cap_mult = 1 - dd_frac). On the REAL W7 book (research
    #     c59/c61) this holds total-DD-fail ~0 at a HIGHER base -> the binding constraint becomes the -5%
    #     daily fat tail, not the -10% wall; faster passes AND safer. Opt-in via GTOS_UB_DERISK_MODE=smooth.
    if limits.derisk_mode == "smooth":
        cap_mult = max(0.0, 1.0 - dd / max(eps, limits.max_dd_limit_pct)) if dd > 0 else 1.0
    elif dd <= limits.derisk_start_dd_pct:
        cap_mult = 1.0
    else:
        span = max(eps, limits.max_dd_limit_pct - limits.derisk_start_dd_pct)
        cap_mult = max(0.0, 1.0 - (dd - limits.derisk_start_dd_pct) / span)
    return GovernorDecision(True, round(cap_mult, 6), round(available, 6),
                            "ok" if cap_mult == 1.0 else "derisking_into_maxdd_wall")


def admit_and_size(
    intents: Sequence[TradeIntent],
    state: GovernorState,
    *,
    profile: str = DEFAULT_PROFILE,
    account: str = "A",
    limits: GovernorLimits = DEFAULT_LIMITS,
    include_clean3: bool = False,
    include_clean4: bool = False,
    overlays: bool = False,
    vp_acceptance: bool = False,
    stress_state: "StressDeriskState | None" = None,
    stress_derisk: bool = False,
    kelly_lite: bool = False,
    kelly_conservative: bool = False,
    sqrt_n_pooling: bool = False,
    drop_w7_symbols: bool = False,
) -> dict[str, Any]:
    """Top-level deployable decision: governor gate -> confidence-weighted correlated-unit sizing.

    Returns a structured decision (JSON-serializable). When new entries are blocked, ALL units size 0
    (existing positions are NOT touched here — they are managed by their own structural stops upstream).

    All upgrade flags default OFF (locked 8-sleeve book). The owner enables, at go-live:
      include_clean3   -> Wave-5 additive deploy book (3 substrate/volprofile sleeves)
      include_clean4   -> + Wave-6 session_leadlag_genuine sleeve (implies clean_3)
      overlays         -> confluence size-up selectors (leader veto / session stack)
      vp_acceptance    -> W6 exit-honest noise-cut of sub_mid_dn_revert (above_va only)
      stress_derisk    -> W6 reactive temporal de-risk multiplier (TIER-1 ladder+coloss, default-on
                          recommended; pass stress_state with realized prior-day facts)
      kelly_lite       -> KB7 day-level conviction tilt (handset; kelly_conservative=half-Kelly)
      sqrt_n_pooling   -> KB7 within-sleeve same-day sqrt-N EV-credit convention (recorded; default-off
                          to match the locked W7 final MC mean-pooling)
      drop_w7_symbols  -> W7 tick-true fail-closed filter of HEATOIL_c/NATGAS_cash intents
    For the clean_3/clean_4 path pass the matching profile (CLEAN3_/CLEAN4_/W7 dial) so sizing uses the
    intended risk; the W7 nominal dials expect include_clean3=True + kelly_lite=True.
    """
    prof = ALLOCATION_PROFILES.get(profile)
    if prof is None:
        return {"ok": False, "reason": f"unknown_profile:{profile}", "units": [], "governor": None}
    base_risk = prof.risk_per_unit_A if account.upper() == "A" else prof.risk_per_unit_B
    # SAFETY INTERLOCK (research c61): the >=2.0% ceiling nominal is only certified RUIN-SAFE
    # (total-DD-fail = 0) WITH smooth DD-defense. On band-defense the real fat left tail (-3.225R) leaks
    # total-DD failures, so the un-certified pairing is refused: fail closed (size 0 new entries) unless
    # smooth defense is active. The aggressive dial can therefore NEVER run on the un-certified band shape.
    # No effect on the live 1.25%/1.50% dials. Activate smooth via env GTOS_UB_DERISK_MODE=smooth (restart).
    if base_risk >= 0.02 - 1e-9 and getattr(limits, "derisk_mode", "band") != "smooth":
        return {
            "ok": True, "new_entries_allowed": False,
            "reason": "ceiling_profile_requires_smooth_ddefense",
            "profile": profile, "account": account.upper(), "base_risk_per_unit": base_risk,
            "include_clean3": include_clean3, "include_clean4": include_clean4,
            "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
            "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
            "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
            "dropped_w7_symbols": [], "governor": None, "units": [],
        }
    # WAVE-7 tick-true: optional fail-closed filter of the dropped illiquid energy legs.
    dropped_w7: tuple[str, ...] = ()
    if drop_w7_symbols:
        intents, dropped_w7 = filter_w7_dropped_symbols(intents, enabled=True)
    gov = evaluate_governor(state, limits=limits)
    if not gov.allow_new_entries:
        return {
            "ok": True, "new_entries_allowed": False, "reason": gov.reason,
            "profile": profile, "account": account.upper(), "base_risk_per_unit": base_risk,
            "include_clean3": include_clean3, "include_clean4": include_clean4,
            "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
            "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
            "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
            "dropped_w7_symbols": list(dropped_w7),
            "governor": asdict(gov), "units": [],
        }
    effective_base = base_risk * gov.size_cap_multiplier
    units = size_correlated_units(intents, base_risk_per_unit=effective_base, limits=limits,
                                  include_clean3=include_clean3, include_clean4=include_clean4,
                                  overlays=overlays, vp_acceptance=vp_acceptance,
                                  stress_state=stress_state, stress_derisk=stress_derisk,
                                  kelly_lite=kelly_lite, kelly_conservative=kelly_conservative,
                                  sqrt_n_pooling=sqrt_n_pooling)
    # Enforce the gross open-risk cap. Decide drops in DESCENDING-CONVICTION order so when the cap binds
    # it sheds the LOWEST-conviction units first and NEVER starves the highest-conviction metals_core
    # (the prior natural/alphabetical-cluster order did — a known hazard). Emit in the ORIGINAL order.
    # Kept byte-parallel with src admission._enforce_gross_open_risk_cap (tests/ultimate_book parity).
    available = gov.available_gross_risk_pct
    _order = sorted(range(len(units)), key=lambda i: -(units[i].confidence or 0.0))
    _kept = {}
    for i in _order:
        u = units[i]
        if not u.sized:
            _kept[i] = u
            continue
        if u.unit_risk_pct <= available + 1e-9:
            available -= u.unit_risk_pct
            _kept[i] = u
        else:
            _kept[i] = SizedUnit(u.cluster, u.sleeve_members, u.n_trades, u.confidence,
                                 0.0, 0.0, False, "gross_risk_cap_would_exceed")
    out_units = [asdict(_kept[i]) for i in range(len(units))]
    return {
        "ok": True, "new_entries_allowed": True, "reason": gov.reason,
        "profile": profile, "account": account.upper(),
        "base_risk_per_unit": base_risk, "effective_base_risk_per_unit": round(effective_base, 8),
        "size_cap_multiplier": gov.size_cap_multiplier,
        "include_clean3": include_clean3, "include_clean4": include_clean4,
        "overlays": overlays, "vp_acceptance": vp_acceptance, "stress_derisk": stress_derisk,
        "kelly_lite": kelly_lite, "kelly_conservative": kelly_conservative,
        "sqrt_n_pooling": sqrt_n_pooling, "drop_w7_symbols": drop_w7_symbols,
        "dropped_w7_symbols": list(dropped_w7),
        "governor": asdict(gov), "units": out_units,
    }


# ===========================================================================================
# 5. LEAK-FREE OUTCOME LABELING — single fill authority (never hand-roll a fill).
#    The deployable path NEVER labels outcomes (the broker does). This is exposed ONLY for the
#    replay-parity self-test and is a thin pass-through to geometry_lib.simulate.
# ===========================================================================================
def label_intent_R(bars, i: int, intent: TradeIntent, *, cost: float, maxbars: int = 80) -> float:
    """Pessimistic leak-free R via geometry_lib.simulate. Winsorized [-1.3,+5]. Test/parity only."""
    from geometry_lib import simulate  # lazy: deployable path does not import the backtester
    r = simulate(bars, i, intent.direction, stop_dist=intent.stop_dist,
                 target_dist=intent.target_dist, maxbars=maxbars, cost=cost)
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
                    "deployed_convention": "mean (sum/n) — matches the locked W7 final MC",
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
    }


# ===========================================================================================
# 7. REPLAY-PARITY HOOK — regenerate the integrator streams and assert this module agrees.
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
    """Load the LOCKED clean_3 deploy book artifact (no heavy import — just the JSON the integrator
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

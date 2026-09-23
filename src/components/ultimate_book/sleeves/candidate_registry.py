"""candidate_registry.py — default-off candidate sleeve catalog.

These conditional sleeves were built during the 2026-06-17 north-star session. They are NOT in the default
live registry; wiring any into generation/sizing is controlled by an explicit candidate-book flag. This
module is the single place the ultimate-system assembly enumerates the default-off candidate inventory,
current book-confidence policy, quarantine status, runtime-execution status, and next challenger queue for
orthogonality / book-MC / activation decisions.

Each was validated on the binding bar (NOT a blended-average / must-work-everywhere rule — the ultimate system
is CONDITIONAL): pooled EVERY-SPLIT positive (train<=2021 / oos<=2024 / sealed2025+) at real cost + beats the
CORRECT random-entry-SAME-EXIT null (NOT the sign-flip placebo) + (for momentum) beats the random-LONG drift null
+ balanced-or-justified direction + leak-free generator that reproduces the research candidate trade-for-trade.
Per-trade validation is not enough for promotion: the 2026-06-17 principal audit added a daily-risk-unit and
unified-book gate. A candidate can remain in this inventory with zero book confidence when its idea is useful
for redesign but its current daily-unit contribution is a drag.

EXIT POLICY differs per sleeve (the deployable TradeIntent carries stop_dist + optional fixed target_dist; the
trail / time-stop exits are declared here + as module constants and handled by the live execution path):
  - vol_squeeze / vol_compression : FIXED target (target_dist = TARGET_R * stop_dist).
  - asian_fade                    : TRAIL (arm/gap in stop-units; target_dist None).
  - ny_crypto_momentum            : TIME-STOP hold-to-session-close (MAXBARS) + stop; target_dist None.
    Refined to NOT-LOW vol-state (mid/high) after the daily-unit audit; this is a replacement, not additive.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..bar_provider import TF_H4, TF_M15, TF_D1
from . import (vol_squeeze, vol_compression, asian_fade, ny_crypto_momentum, ny_index_momentum,
               structural_retest, metal_session_reversion, asia_pdl_fade, orb_crypto_london,
               liq_asia_up_low_metal, kz_london_crypto_low, vss_fxcross_london_up_low)


@dataclass(frozen=True)
class CandidateSpec:
    tag: str
    generator: object
    timeframe: int
    asset_class: str               # corr-cluster id for the governor when/if wired
    on_surface: tuple[str, ...]
    exit_policy: str               # 'fixed_target' | 'trail' | 'time_stop'
    every_split: tuple[float, float, float]   # (train, oos, sealed) pooled meanR at real cost
    correct_null_p: float          # random-entry-same-exit p (entry adds edge if < 0.05)
    note: str


# The default-off candidate sleeves (live wiring owner-gated).
CANDIDATES: dict[str, CandidateSpec] = {
    "vol_squeeze": CandidateSpec(
        "vol_squeeze", vol_squeeze.generate, TF_H4, "index", vol_squeeze.ON_SURFACE, "fixed_target",
        (0.243, 0.129, 0.227), 0.003,
        "indices H4 vol-squeeze->trend-gated expansion (GER40/UK100/SPX500/NAS100/US30_cash); neg-control NULL "
        "(edge IS the vol-state); corr_book ~-0.11..-0.14. US30 = US-beta breadth, not net-new diversification."),
    "vol_compression": CandidateSpec(
        "vol_compression", vol_compression.generate, TF_D1, "crypto", vol_compression.ON_SURFACE, "fixed_target",
        (0.242, 0.246, 0.369), 0.0033,
        "crypto D1 compression->range-breakout (BTC/ETH/XTZ); ac60-gate KILLS it => vol-STATE not momentum; "
        "corr_book -0.028 (orthogonal)."),
    "asian_fade": CandidateSpec(
        "asian_fade", asian_fade.generate, TF_M15, "fx_reversion", asian_fade.ON_SURFACE, "trail",
        (0.142, 0.241, 0.228), 0.0,
        "EUR/GBP M15 Asian-range break faded during London/NY with TRAIL exit; NON-momentum reversion, "
        "orthogonal to the momentum book; EURUSD positive EVERY YEAR 2014-2026; entry beats random by 6-8 SD."),
    "ny_crypto_momentum": CandidateSpec(
        "ny_crypto_momentum", ny_crypto_momentum.generate, TF_M15, "crypto", ny_crypto_momentum.ON_SURFACE,
        "time_stop", (0.102, 0.273, 0.310), 0.0007,
        "BTC/ETH M15 NY-killzone momentum-CONTINUATION refined to NOT-LOW vol-state (mid/high only): "
        "|de|>=0.50 -> ride to session close. This folds kz_ny_crypto_notlow into the existing sleeve as a "
        "replacement, not additive double-counting. Refined pooled n=1702 +0.2017, balanced L/S "
        "(880 long +0.259 / 822 short +0.141), beats drift null p=0.0033. LOW-vol subset is excluded."),
    "ny_index_momentum": CandidateSpec(
        "ny_index_momentum", ny_index_momentum.generate, TF_M15, "index", ny_index_momentum.ON_SURFACE,
        "time_stop", (0.178, 0.175, 0.257), 0.0,
        "indices M15 NY-killzone momentum-CONTINUATION, MID-VOL only (|de|>=0.50 + ATR mid-percentile -> ride to "
        "session close); pooled n=863, balanced L/S both positive (L+0.221/S+0.162), correct-null p=0.000, "
        "drift-null p=0.005. SPX500/US30/GER40 strong; UK100 the weak member; 1 neg year (2023). CONDITIONAL "
        "(mid-vol regime). From the correct-null sweep wf_77c9d7db; principal-re-derived (verify_ny_index_momentum)."),
    "structural_retest": CandidateSpec(
        "structural_retest", structural_retest.generate, TF_M15, "structural",
        structural_retest.ON_SURFACE, "fixed_target", (0.09, 0.07, 0.20), 0.0425,
        "GENERAL M15 break-and-retest (OB/BRK/DISP/SWP/FVG), direction=HTF-regime, fired only in VERIFIED "
        "(class,session,regime,high-vol) whitelist cells, fixed 2R + 32-bar time-stop. 3 cells (all every-split+, "
        "beat the CORRECT regime-fixed null): crypto-SHORT NY|dn (n=5957, +0.057/+0.055/+0.073, p=0.043 — the "
        "system's first dedicated SHORT) + metal-SHORT London|dn (n=2017, +0.143/+0.075/+0.283, 9 metals+, p=0.043) "
        "+ index-LONG Asian|up (n=1291, +0.057/+0.091/+0.188, US30/SPX/NAS+, p=0.010). Supersedes the earlier "
        "single-cell structural prototype. wf_77c9d7db; principal-re-derived (verify_structural_retest, 1215/1215 identical)."),
    "metal_session_reversion": CandidateSpec(
        "metal_session_reversion", metal_session_reversion.generate, TF_M15, "metal_reversion",
        metal_session_reversion.ON_SURFACE, "trail", (0.066, 0.076, 0.151), 0.0,
        "XAU/XAG M15 NY-session anchor-REVERSION (fade >=1.6*ATR extension from the session-open, dn/range regime "
        "only) with trail exit. A metals REVERSION sleeve, distinct from the deployed metals MOMENTUM core. "
        "n=4458, every-split+ & INCREASING, balanced L/S, XAU+0.095/XAG+0.058 both deep+positive, correct "
        "random-entry-same-trail null p=0.000. Leak-free (dropped the gen's full-day look-ahead bar-count gate; "
        "edge unchanged). wf_77c9d7db; principal-re-derived (verify_metal_session_reversion)."),
    "asia_pdl_fade": CandidateSpec(
        "asia_pdl_fade", asia_pdl_fade.generate, TF_M15, "liquidity_sweep", asia_pdl_fade.ON_SURFACE,
        "fixed_target", (0.110, 0.015, 0.164), 0.0033,
        "BROADEST deployable sleeve (30 symbols after NATGAS split): Asian-session prior-day-LOW sweep+reclaim "
        "-> LONG fade, fixed 3R + 32-bar time-stop. Ex-NATGAS n=7524, every-split+ but OOS THIN "
        "(+0.015, 2023 negative), sealed improves after NATGAS removal (+0.164). NATGAS_cash had only 18 trades, "
        "no train sample, and sealed damage; bridge/tick-spread proof keeps it as a research-revival lane, not a "
        "deployable carrier. Correct random-entry null p=0.0033 + drift null p=0.0025. Leak-free (M15-only, PDL "
        "from prior completed day; dropped the gen's D1-regime-exists gate)."),
    "liq_asia_up_low_metal": CandidateSpec(
        "liq_asia_up_low_metal", liq_asia_up_low_metal.generate, TF_M15, "metal_liquidity_reversion",
        liq_asia_up_low_metal.ON_SURFACE, "fixed_target", (0.113, 0.142, 0.168), 0.004,
        "XAU/XAG/XPT/XPD M15 Asian-session liquidity-sweep REVERSION in D1-up + LOW intraday-vol state: "
        "PDH sweep+reclaim -> SHORT and PDL sweep+reclaim -> LONG, fixed 3R + 16-bar time-stop. "
        "Pooled n=496, every-split+ and rising (train+0.113/oos+0.142/sealed+0.168), daily meanR +0.17098 "
        "with daily split +0.149/+0.155/+0.254, correct random-entry-same-exit null p=0.004 and drift null "
        "p=0.008. HONEST: narrow 4-metal surface; PDH-short carries most edge while PDL-long is weak but "
        "recent-diversifying. Canonical module applied from the daily-pass challenger queue."),
    "kz_london_crypto_low": CandidateSpec(
        "kz_london_crypto_low", kz_london_crypto_low.generate, TF_M15, "crypto",
        kz_london_crypto_low.ON_SURFACE, "time_stop", (0.260, 0.154, 0.424), 0.026,
        "BTC/ETH M15 London-killzone momentum-CONTINUATION, LOW-vol only: server 12:00 decision, "
        "|de|>=0.50 over the 09:00-12:00 window, 1.3*ATR stop, hold-to-session-close time-stop. "
        "Pooled n=813, train/oos/sealed +0.2599/+0.1543/+0.4239; daily n=627, split "
        "+0.115631/+0.133007/+0.243072; random-entry same-exit null p=0.026. HONEST: same-direction "
        "drift null is only marginal (p~0.085) and old 0.25 confidence was weak additive, so this is "
        "canonical only at low book-watch confidence after tuned unified-MC."),
    "vss_fxcross_london_up_low": CandidateSpec(
        "vss_fxcross_london_up_low", vss_fxcross_london_up_low.generate, TF_M15,
        "fxcross_vol_state_squeeze", vss_fxcross_london_up_low.ON_SURFACE, "fixed_target",
        (0.077, 0.070, 0.329), 0.0017,
        "EURJPY/GBPJPY/CHFJPY/AUDJPY/EURGBP M15 box-width-in-ATR squeeze breakout in London, gated by "
        "mandatory prior-D1 up regime and M15 LOW-vol state. Stop=1*ATR, target=2*ATR, 48-bar time stop. "
        "Pooled n=860, train/oos/sealed +0.077/+0.0695/+0.3285; daily n=518, split "
        "+0.112171/+0.001194/+0.391658; random-entry and drift null p~0.0017. HONEST: OOS daily "
        "mean is thin and 2024 weak, so status remains OOS-decay-watch even after book promotion."),
    "orb_crypto_london": CandidateSpec(
        "orb_crypto_london", orb_crypto_london.generate, TF_M15, "crypto", orb_crypto_london.ON_SURFACE,
        "fixed_target", (0.150, 0.098, 0.058), 0.0,
        "BTC/ETH M15 London opening-range-breakout CONTINUATION (07:00 OR, first 08-11 close beyond edge), "
        "vol-LOW + TRENDING regime, edge-stop + 2R + 80-bar time-stop. Distinct from the killzone mechanic. "
        "n=2706 leak-free (trailing vol-state), every-split+ (train+0.150/oos+0.098/sealed+0.058), balanced L/S, "
        "BTC+0.083/ETH+0.146, correct random-entry-same-exit null p=0.000. principal-re-derived "
        "(verify_orb_crypto_london, generate 160/160 identical)."),
}
CANDIDATE_NAMES: tuple[str, ...] = tuple(CANDIDATES.keys())

# ---------------------------------------------------------------------------------------------------------------
# VPS HANDOFF: this catalog is the COMPLETE default-off spec the VPS would read for any future owner-gated live
# wiring. This Mac is RESEARCH/BUILD ONLY; it does NOT wire for live, configure for live, or turn anything on.
# The VPS owns live wiring/config/turning-on/linking and parity across live + VPS environments.
#
# Confidence here = BOOK-CONTRIBUTION, not per-trade expectancy. Zero confidence is a quarantine state, not
# deletion: the idea remains in the inventory for redesign, but it must not receive book risk until a new
# daily-unit/unified-MC proof repairs it.
#
# Corrected principal audit, 2026-06-17:
# - deployed baseline Sharpe 0.144597; MC pass/fail-DD 0.9843/0.0157; median days 66; monthly 2.590%.
# - pre-quarantine nonzero drag policy Sharpe 0.251492; pass/fail-DD 0.9995/0.0005; median days 37; monthly 4.504%.
# - current registry after not-low crypto fold + LIQ/KZ/VSS promotion Sharpe 0.274137; pass/fail-DD
#   0.9996/0.0004; median days 33; monthly 4.910%.
# - robust KZ/VSS promotion target uses kz_london_crypto_low 0.10 + vss_fxcross_london_up_low 0.12:
#   selected to avoid overweighting VSS's thin OOS daily-unit split; higher VSS weights remain diagnostic only.
# See research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json.
#
# PROVENANCE WARNING, measured 2026-08-07 (wave-20 lane p4). THE FILE NAMED ON THE LINE ABOVE HAS
# NEVER EXISTED. Over all 9,004 commits reachable from every ref, `git log --all --diff-filter=A`
# records zero additions of CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, zero of its sibling
# CORRECTED_CANDIDATE_DAILY_SERIES_AUDIT.json, and zero of ANY path under
# research/operations/final_moonshot_principal_full_system_audit_2026_06_17/. The directory is phantom.
#
# What survives, and what does not:
#   * The VALUES are safe. `UNIFIED_BOOK_MC_RESULT.json -> conf` in
#     research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ is byte-equal to
#     CANDIDATE_CONFIDENCE below and is pinned by tests/ultimate_book/test_candidate_book_consistency.py:73.
#   * The DERIVATION is not recoverable. That artifact restates these weights as INPUTS to all
#     eleven MC scenarios and never derives them, and they are not a function of anything it
#     publishes: Spearman(confidence, R/day per fireday) = -0.1111 (n=9), vs matched_days +0.2992,
#     vs firedays +0.2821. kz_london_crypto_low has the second-HIGHEST per-day expectancy (0.337)
#     and the LOWEST nonzero weight (0.10); metal_session_reversion has the lowest (0.073) and the
#     highest weight (0.40). No published statistic orders them.
#
# Scope, so this is not read as bigger than it is: NONE of these sleeves is armed. The armed set is
# crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback (src/safety/armed_set.py), whose
# confidences come from admission.SLEEVE_REGISTRY and admission.CLEAN3_REGISTRY, whose own
# provenance artifacts DO exist and are tracked (INTEG_portfolio_build_w2.py, INTEG_W5_CLEAN3_DEPLOY.json,
# PORTFOLIO_BUILD_W5.md). These weights size nothing live today. They become load-bearing the moment
# any name below enters `run_book.py --tags`, and at that point the derivation must be rebuilt first.
# Register: docs/audits/fable5-vision-audit-20260725/phase20/forward/SUPERSEDED_CLAIMS_V1.json
CANDIDATE_CONFIDENCE: dict[str, float] = {
    "vol_squeeze": 0.0, "vol_compression": 0.40, "asian_fade": 0.40, "metal_session_reversion": 0.40,
    "ny_crypto_momentum": 0.35, "ny_index_momentum": 0.0, "structural_retest": 0.0, "asia_pdl_fade": 0.25,
    "orb_crypto_london": 0.35, "liq_asia_up_low_metal": 0.25, "kz_london_crypto_low": 0.10,
    "vss_fxcross_london_up_low": 0.12,
}

CANDIDATE_STATUS: dict[str, str] = {
    "vol_squeeze": "quarantined_daily_unit_drag",
    "vol_compression": "promotion_candidate",
    "asian_fade": "promotion_candidate",
    "ny_crypto_momentum": "promotion_candidate_notlow_replacement_applied",
    "ny_index_momentum": "quarantined_book_drag_redesign_required",
    "structural_retest": "quarantined_daily_unit_failure",
    "metal_session_reversion": "promotion_candidate",
    "asia_pdl_fade": "promotion_candidate_recency_oos_watch_natgas_split_applied",
    "liq_asia_up_low_metal": "promotion_candidate_narrow_surface_watch",
    "kz_london_crypto_low": "promotion_candidate_low_weight_book_watch",
    "vss_fxcross_london_up_low": "promotion_candidate_oos_decay_watch_aux_required",
    "orb_crypto_london": "promotion_candidate",
}

CANDIDATE_DECISION: dict[str, dict[str, object]] = {
    "ny_crypto_momentum": {
        "decision": "fold_kz_ny_crypto_notlow_into_existing_sleeve",
        "reason": (
            "same mechanic/session/symbols as existing ny_crypto_momentum; daily-unit audit and refinement "
            "work show low-vol exclusion is the robust replacement, not an additive sleeve"
        ),
    },
    "liq_asia_up_low_metal": {
        "decision": "promote_daily_pass_challenger_to_default_off_candidate_catalog",
        "reason": (
            "orthogonal metals liquidity-reversion mechanism with positive per-trade and daily train/oos/sealed "
            "splits; narrow surface and side asymmetry keep confidence at provisional 0.25 pending broader rebuild"
        ),
    },
    "kz_london_crypto_low": {
        "decision": "promote_daily_pass_challenger_at_tuned_low_book_confidence",
        "reason": (
            "real London crypto low-vol momentum edge with exact parity and positive daily splits, but old 0.25 "
            "weight was weak additive; tuned unified-MC selects 0.10 in the current book"
        ),
    },
    "vss_fxcross_london_up_low": {
        "decision": "promote_daily_pass_challenger_with_oos_decay_watch",
        "reason": (
            "portfolio-orthogonal FX-cross squeeze edge improves the current book, but OOS daily mean is thin "
            "and the D1-aux gate is mandatory; confidence remains 0.12 while higher tuned weights stay diagnostic"
        ),
    },
    "vol_squeeze": {
        "decision": "zero_book_confidence_until_daily_unit_redesign",
        "reason": "per-trade valid, but same-day correlated index risk-unit contribution was a book drag",
    },
    "ny_index_momentum": {
        "decision": "zero_book_confidence_until_market_state_or_surface_redesign",
        "reason": "corrected unified-book leave-one-out improved when dropped",
    },
    "structural_retest": {
        "decision": "zero_book_confidence_until_cell_level_rebuild",
        "reason": (
            "full three-cell daily-unit audit failed: meanR -0.071032 and train/oos/sealed meanR "
            "-0.053274/-0.082925/-0.086833"
        ),
    },
}

PROVISIONAL_CHALLENGER_QUEUE: dict[str, dict[str, object]] = {
    "kz_ny_crypto_notlow": {
        "relationship": "replacement_candidate_for_ny_crypto_momentum",
        "daily_meanR": 0.185503,
        "daily_split_meanR": (0.126159, 0.215613, 0.289136),
        "status": "canonical_refinement_applied_to_ny_crypto_momentum",
    },
    "kz_london_crypto_low": {
        "relationship": "new_crypto_killzone_candidate",
        "daily_meanR": 0.148179,
        "daily_split_meanR": (0.115631, 0.133007, 0.243072),
        "status": "canonical_module_applied_to_default_off_registry_at_0.10_book_watch",
    },
    "liq_asia_up_low_metal": {
        "relationship": "new_metal_liquidity_candidate",
        "daily_meanR": 0.170980,
        "daily_split_meanR": (0.149025, 0.155433, 0.254366),
        "status": "canonical_module_applied_to_default_off_registry",
    },
    "vss_fxcross_london_up_low": {
        "relationship": "new_fxcross_vol_state_candidate",
        "daily_meanR": 0.143559,
        "daily_split_meanR": (0.112171, 0.001194, 0.391658),
        "status": "canonical_module_applied_to_default_off_registry_at_0.12_oos_decay_watch",
    },
}

BOOK_PROMOTION_READY_CANDIDATE_NAMES: tuple[str, ...] = tuple(
    name for name, confidence in CANDIDATE_CONFIDENCE.items() if confidence > 0.0
)

# Runtime-executable v2 admits every positive-confidence candidate whose native exit can now be represented
# exactly by the V4 execution contract: fixed broker TP plus time-stop, capless trailing with no broker TP, and
# targetless hold-to-close time-stop with no broker TP. Zero-confidence candidates remain quarantined inventory.
RUNTIME_EXECUTABLE_CANDIDATE_NAMES: tuple[str, ...] = tuple(
    name for name in BOOK_PROMOTION_READY_CANDIDATE_NAMES
    if CANDIDATES[name].exit_policy in {"fixed_target", "trail", "time_stop"}
)

CANDIDATE_RUNTIME_BLOCKERS: dict[str, str] = {
    name: (
        "native_exit_contract_pending:"
        + ("capless_trailing_runner" if CANDIDATES[name].exit_policy == "trail" else "targetless_time_stop")
    )
    for name in BOOK_PROMOTION_READY_CANDIDATE_NAMES
    if CANDIDATES[name].exit_policy not in {"fixed_target", "trail", "time_stop"}
}


def candidate_specs() -> list[CandidateSpec]:
    """All default-off candidate sleeve specs (the VPS-handoff catalog; the VPS wires + activates for live)."""
    return list(CANDIDATES.values())


@dataclass(frozen=True)
class MarketExpansionDefaultOffSpec:
    """Metadata-only market-expansion candidate design.

    These rows are NOT runtime generators and carry zero activation weight. They preserve the G12/default-off
    design package as code-readable inventory for the next implementation lane without changing live behavior.
    """

    tag: str
    file_symbol: str
    broker_symbol: str
    family: str
    mechanism: str
    design_status: str
    candidate_seed_weight: float
    candidate_weight_ceiling: float
    activation_weight_now: float
    symbol_collision_winner: bool
    target2_exact_m1_event_count: int
    target2_m15_proxy_event_count: int
    target2_ordered_mean_r: float
    full_book_delta_sharpe: float
    evidence_route: str
    note: str


MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE = (
    "research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18"
)
MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE = (
    "research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18"
)


MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES: dict[str, MarketExpansionDefaultOffSpec] = {
    "mx_aus200_cash_d1_atr_mean_reversion": MarketExpansionDefaultOffSpec(
        "mx_aus200_cash_d1_atr_mean_reversion", "AUS200_cash", "AUS200.cash", "indices_context",
        "d1_atr_mean_reversion", "default_off_spec_design_ready", 0.0, 0.05, 0.0, False,
        45, 54, 0.150821, 0.00016, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; loses AUS200 collision to volume-surge repaired full-book delta"),
    "mx_aus200_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_aus200_cash_d1_volume_surge_reversal", "AUS200_cash", "AUS200.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        74, 91, 0.073095, 0.000192, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; wins AUS200 collision by repaired full-book delta"),
    "mx_avausd_d1_donchian_20_breakout": MarketExpansionDefaultOffSpec(
        "mx_avausd_d1_donchian_20_breakout", "AVAUSD", "AVAUSD", "crypto_alt_or_major",
        "d1_donchian_20_breakout", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        50, 148, 0.176133, 0.000261, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "exact-M1-supported default-off design; still requires broker cost/spec/deployment proof"),
    "mx_btcusd_d1_donchian_20_breakout": MarketExpansionDefaultOffSpec(
        "mx_btcusd_d1_donchian_20_breakout", "BTCUSD", "BTCUSD", "crypto_alt_or_major",
        "d1_donchian_20_breakout", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        79, 282, 0.085068, 0.000054, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_cadjpy_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_cadjpy_d1_volume_surge_reversal", "CADJPY", "CADJPY", "jpy_fx",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        29, 196, 0.059455, 0.000286, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "exact-M1-supported default-off design; still requires broker cost/spec/deployment proof"),
    "mx_ethusd_d1_donchian_20_breakout": MarketExpansionDefaultOffSpec(
        "mx_ethusd_d1_donchian_20_breakout", "ETHUSD", "ETHUSD", "crypto_alt_or_major",
        "d1_donchian_20_breakout", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        72, 280, 0.152397, 0.000108, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_eu50_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_eu50_cash_d1_volume_surge_reversal", "EU50_cash", "EU50.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        100, 36, 0.238981, 0.000521, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_fra40_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_fra40_cash_d1_volume_surge_reversal", "FRA40_cash", "FRA40.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        82, 34, 0.163668, 0.000234, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_ger40_cash_d1_atr_mean_reversion": MarketExpansionDefaultOffSpec(
        "mx_ger40_cash_d1_atr_mean_reversion", "GER40_cash", "GER40.cash", "indices_context",
        "d1_atr_mean_reversion", "transformed_context_or_veto_after_exact_m1_repair", 0.0, 0.05, 0.0, False,
        43, 49, -0.0005, 0.00001, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1 repair negated the candidate claim; preserve as GER40 context/veto intelligence"),
    "mx_ger40_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_ger40_cash_d1_volume_surge_reversal", "GER40_cash", "GER40.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        65, 63, 0.096851, 0.000063, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; wins GER40 collision after ATR transforms to context/veto"),
    "mx_jp225_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_jp225_cash_d1_volume_surge_reversal", "JP225_cash", "JP225.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        80, 46, 0.096101, 0.000153, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_nzdjpy_d1_donchian_20_breakout": MarketExpansionDefaultOffSpec(
        "mx_nzdjpy_d1_donchian_20_breakout", "NZDJPY", "NZDJPY", "jpy_fx",
        "d1_donchian_20_breakout", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        32, 341, 0.06149, 0.000625, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "exact-M1-supported default-off design; still requires broker cost/spec/deployment proof"),
    "mx_spn35_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_spn35_cash_d1_volume_surge_reversal", "SPN35_cash", "SPN35.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        24, 88, 0.131326, 0.000269, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "near-miss row accepted only as exact-M1-supported default-off design"),
    "mx_us100_cash_d1_atr_mean_reversion": MarketExpansionDefaultOffSpec(
        "mx_us100_cash_d1_atr_mean_reversion", "US100_cash", "US100.cash", "indices_context",
        "d1_atr_mean_reversion", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        22, 60, 0.121194, 0.000262, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "exact-M1-supported default-off design; still requires broker cost/spec/deployment proof"),
    "mx_us30_cash_d1_volume_surge_reversal": MarketExpansionDefaultOffSpec(
        "mx_us30_cash_d1_volume_surge_reversal", "US30_cash", "US30.cash", "indices_context",
        "d1_volume_surge_reversal", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        52, 90, 0.236683, 0.000163, MARKET_EXPANSION_PROXY_M1_REPAIR_EVIDENCE_ROUTE,
        "exact-M1-repaired default-off design; still requires broker cost/spec/deployment proof"),
    "mx_us500_cash_d1_atr_mean_reversion": MarketExpansionDefaultOffSpec(
        "mx_us500_cash_d1_atr_mean_reversion", "US500_cash", "US500.cash", "indices_context",
        "d1_atr_mean_reversion", "default_off_spec_design_ready", 0.025, 0.05, 0.0, True,
        22, 56, 0.199876, 0.000391, MARKET_EXPANSION_DEFAULT_OFF_EVIDENCE_ROUTE,
        "exact-M1-supported default-off design; still requires broker cost/spec/deployment proof"),
}

MARKET_EXPANSION_DEFAULT_OFF_NAMES: tuple[str, ...] = tuple(MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.keys())
MARKET_EXPANSION_DEFAULT_OFF_M1_SUPPORTED_NAMES: tuple[str, ...] = tuple(
    name for name, spec in MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
    if spec.design_status == "default_off_spec_design_ready"
)
MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES: tuple[str, ...] = tuple(
    name for name, spec in MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
    if spec.design_status == "repair_gated_default_off_spec_only"
)
MARKET_EXPANSION_DEFAULT_OFF_TRANSFORMED_NAMES: tuple[str, ...] = tuple(
    name for name, spec in MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
    if spec.design_status.startswith("transformed_")
)
MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES: tuple[str, ...] = tuple(
    name for name, spec in MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
    if spec.activation_weight_now > 0.0
)
MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES: tuple[str, ...] = tuple(
    name for name, spec in MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
    if spec.symbol_collision_winner
)

MARKET_EXPANSION_CONDITIONED_SIZING_EVIDENCE_ROUTE = (
    "research/operations/final_moonshot_market_expansion_conditioned_sizing_refinement_2026_06_18"
)

MARKET_EXPANSION_CONDITIONED_POLICIES: dict[str, tuple[str, ...]] = {
    "all14_swap_adjusted": MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES,
    "positive_weighted12_after_swap": (
        "mx_avausd_d1_donchian_20_breakout",
        "mx_btcusd_d1_donchian_20_breakout",
        "mx_cadjpy_d1_volume_surge_reversal",
        "mx_ethusd_d1_donchian_20_breakout",
        "mx_eu50_cash_d1_volume_surge_reversal",
        "mx_fra40_cash_d1_volume_surge_reversal",
        "mx_ger40_cash_d1_volume_surge_reversal",
        "mx_jp225_cash_d1_volume_surge_reversal",
        "mx_nzdjpy_d1_donchian_20_breakout",
        "mx_us100_cash_d1_atr_mean_reversion",
        "mx_us30_cash_d1_volume_surge_reversal",
        "mx_us500_cash_d1_atr_mean_reversion",
    ),
    "robust6_every_split_positive": (
        "mx_btcusd_d1_donchian_20_breakout",
        "mx_ethusd_d1_donchian_20_breakout",
        "mx_eu50_cash_d1_volume_surge_reversal",
        "mx_fra40_cash_d1_volume_surge_reversal",
        "mx_ger40_cash_d1_volume_surge_reversal",
        "mx_us500_cash_d1_atr_mean_reversion",
    ),
}

MARKET_EXPANSION_CONDITIONED_POLICY_METADATA: dict[str, dict[str, object]] = {
    "all14_swap_adjusted": {
        "status": "flat_all_sleeve_reference_not_preferred",
        "monthly_pct": 4.991,
        "sharpe": 0.278675,
        "maxDD_R": None,
        "selected_tag_count": 14,
        "evidence_route": MARKET_EXPANSION_CONDITIONED_SIZING_EVIDENCE_ROUTE,
    },
    "positive_weighted12_after_swap": {
        "status": "best_monthly_and_sharpe_default_off_policy",
        "monthly_pct": 5.09,
        "sharpe": 0.28419,
        "maxDD_R": 8.842614,
        "selected_tag_count": 12,
        "evidence_route": MARKET_EXPANSION_CONDITIONED_SIZING_EVIDENCE_ROUTE,
    },
    "robust6_every_split_positive": {
        "status": "best_drawdown_default_off_policy",
        "monthly_pct": 5.052,
        "sharpe": 0.282076,
        "maxDD_R": 7.956872,
        "selected_tag_count": 6,
        "evidence_route": MARKET_EXPANSION_CONDITIONED_SIZING_EVIDENCE_ROUTE,
    },
}


def market_expansion_default_off_specs() -> list[MarketExpansionDefaultOffSpec]:
    """Metadata-only market-expansion design rows; never active runtime sleeves by themselves."""
    return list(MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.values())

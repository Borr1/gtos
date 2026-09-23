"""Sleeve decision `if`s as a hierarchical TypeSafe question tree.

Founder brief (Diogo / Appendix 3): nested labels + log(n) tree search,
Score include-depth (hide / short / long / full), not linear binary
keep/drop. One completeness Noul on *this* gold_state object — not a
Noul per sleeve, per bar, or per tick because Jev is cheap.

Code owns workflow (which generator ran, ON_SURFACE, warmup, ATR<=0,
``--tags``, include_* flags, named hard-off, digest, 2-stop count, prop
wall, frontier-exits selection). TypeSafe owns the semantic call that
used to be a sleeve fire / size / exit cliff.

Subtree questions live here. The stacked gold POST folds
``sleeve_subtree_questions(..., standalone=False)`` in
``jev_questions.systemone_payload`` so this fire's schema rides the same
System One call (``ask_together``). Do not add a second LLM hop.

Pin model ``jev-1.13.0``. Challenge book ``0``.

Every decision this module returns, including every parameter, is the
System One value for that state. ``decide_sleeve`` posts this fire's
subtree once through ``jev_client.evaluate`` (model ``jev-1.13.0``,
``merge_sleeve=False``, POST https://api.typesafe.ai/v1/systemone).
A return is a Noul, a Choice, or a Score. A Score may sit between the
levels. Prior outcomes ride that ask. An empty answer, a tie, or an
error leaves the return unset and does not restore a constant. Floor
and baseline are not a question. The tree stays hierarchical. This
module does not send.
"""

from __future__ import annotations

from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS
from .family import family_class_for, hard_off_family
from .jev_questions import MODEL

INCLUDE_DEPTH_LEVELS = ("hide", "short", "long", "full")
INCLUDE_DEPTH_CRITERIA = [
    "Hide this chunk — not needed for this fire's query",
    "Short summary of the named fields in this chunk",
    "Longer summary of the named fields in this chunk",
    "Include the whole named chunk",
]

# Family nodes are the first hop of the tree. Leaves are named sleeves.
# Do not flatten this into a 48-way keep/drop.
FAMILY_LEAVES: dict[str, tuple[str, ...]] = {
    "metals": (
        "metals_core",
        "metals_softband",
        "metals_ob_micro",
        "metal_session_reversion",
    ),
    "crypto": (
        "crypto",
        "ny_crypto_momentum",
        "orb_crypto_london",
        "kz_london_crypto_low",
        "vol_compression",
    ),
    "energy": ("energy_agri",),
    "jpy": ("fx_jpy", "fx_jpy_ny"),
    "substrate": ("sub_xvol_pullback", "sub_mid_dn_revert"),
    "volprofile": ("vp_euidx_pocgrav",),
    "index": ("idxrev", "ny_index_momentum", "vol_squeeze"),
    "fx_reversion": ("asian_fade",),
    "liquidity": ("asia_pdl_fade", "liq_asia_up_low_metal"),
    "structural": ("structural_retest",),
    "leadlag": ("session_leadlag_genuine",),
    "vss": ("vss_fxcross_london_up_low",),
    "mx": (),  # filled from prefix mx_
    "house_keep": (),  # F5 spring / vss prefixes — code routes
    "a_plus": (),
    "study": (),
    "other": (),
}

# Per-sleeve chunk override when the family default would dump an unused series
# (founder: query-aware include, not a family-wide catalog). Session hour that
# is a clock *fact* is not an include-depth chunk.
SLEEVE_CHUNKS: dict[str, tuple[str, ...]] = {
    "vol_compression": ("squeeze",),
    "ny_crypto_momentum": ("vol", "de"),
    "ny_index_momentum": ("vol", "de"),
    "orb_crypto_london": ("vol", "regime"),
    "liq_asia_up_low_metal": ("vol", "regime", "pdl"),
    "kz_london_crypto_low": ("vol", "de"),
    "vss_fxcross_london_up_low": ("vol", "squeeze", "d1"),
    "metal_session_reversion": ("regime", "extension"),
    "vol_squeeze": ("squeeze", "regime"),
    "asia_pdl_fade": ("pdl",),
    "asian_fade": ("range",),
    "structural_retest": ("cell", "vol"),
    "session_leadlag_genuine": ("leader",),
}

# Joint family Scores already cover these — do not add a second generic vol hop.
_NO_GENERIC_VOL_NODES = frozenset({"energy"})
_NO_GENERIC_VOL_SLEEVES = frozenset({"vol_compression", "vol_squeeze", "energy_agri"})

# Query-aware chunks. Only the family's used chunks enter the question set.
FAMILY_CHUNKS: dict[str, tuple[str, ...]] = {
    "metals": ("ac60", "session", "a8", "levels"),
    "crypto": ("donchian", "ac60"),
    "energy": ("vol", "slope"),
    "jpy": ("session", "impulse"),
    "substrate": ("cell", "session"),
    "volprofile": ("poc", "vol"),
    "index": ("wick",),
    "fx_reversion": ("session", "range"),
    "liquidity": ("session", "pdl"),
    "structural": ("cell",),
    "leadlag": ("leader",),
    "vss": ("session",),
    "mx": ("donchian", "surge"),
    "house_keep": ("session", "geometry"),
    "a_plus": ("session", "geometry"),
    "study": ("session", "geometry"),
    "other": ("session",),
}

_SNIPPETS: dict[str, str] = {
    "metals_core": "H4 FVG-retest; persistence is a range on ac60, not ac60>=0.10",
    "metals_softband": "same FVG; softband 0.04–0.10 is already a size range",
    "metals_ob_micro": "OB-retest tail; ac60 range not 0.20 cliff; same-bar FVG is a fact",
    "crypto": "H4 Donchian-20 break; ac60 is a range 0.05–0.25, not 0.15",
    "energy_agri": "same FVG; ignition is vr×slope jointly, not vr>=2 OR |slope|<0.05",
    "idxrev": "wick-fade of prior-16 range; quality Score, not wick-or-not",
    "fx_jpy": "London 4th session bar is a COUNT; fitness is Score",
    "fx_jpy_ny": "NY hour/impulse/trend are facts + fitness Score",
    "sub_xvol_pullback": "xhi/rand/up/conflict cell fitness as a range, not AND of four cliffs",
    "sub_mid_dn_revert": "NY mid-vol revert cell fitness as a range; session hour is a clock fact",
    "vp_euidx_pocgrav": "POC gravitation vs VA as a range, not |d_poc|>=2 and vr>=1.2",
    "vol_compression": "ATR squeeze then range-break; no ac60 gate (that kills it)",
    "asian_fade": "Asian range then London/NY wick fade; session clock is a fact",
    "ny_crypto_momentum": "NY 17:00 bar is a clock fact; |de| and vol-state are Scores",
    "metal_session_reversion": "NY anchor extension fade; HTF-not-up is Score not a ban",
    "asia_pdl_fade": "Asia PDL sweep+reclaim; PDL presence is a fact, quality is Score",
    "orb_crypto_london": "London ORB crypto; named F5 hard-off stays integer",
    "liq_asia_up_low_metal": "Asia up-low metal liquidity; session clock is a fact",
    "kz_london_crypto_low": "London killzone crypto low-vol; hour is a fact",
    "vss_fxcross_london_up_low": "VSS FX-cross London; session clock is a fact",
    "vol_squeeze": "index ATR-squeeze expansion; vol-state Score, not a shape cliff",
    "ny_index_momentum": "NY killzone index continuation; mid-vol Score",
    "structural_retest": "whitelist cell fitness as Score; cell membership is a fact",
    "session_leadlag_genuine": "leader impulse is a fact when the feed exists; quality is Score",
}

INTEGER_FACTS: tuple[str, ...] = (
    "tags_intersection",
    "include_clean3",
    "include_clean4",
    "include_candidate_book",
    "include_market_expansion_book",
    "on_surface_membership",
    "warmup_bar_count",
    "atr_nonpositive",
    "named_hard_off",
    "token_digest_match",
    "two_stop_count",
    "prop_wall",
    "frontier_exits_selection",
    "fourth_session_bar_count",
    "same_bar_fvg_presence",
    "operator_flatten_flag",
    "kelly_bin_count",
    "a8_k_of_4_count",
    "candidate_confidence_zero",
    "first_break_of_day",
    "or_bar_count",
    "metals_confluence_gate_enabled",
)


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def family_node_for(sleeve: str, *, symbol: str = "", origin: str = "") -> str:
    """Name the subtree to ask. The family decision is the Choice on the ask."""
    sl = _norm(sleeve)
    origin_n = _norm(origin)
    if sl.startswith("mx_"):
        return "mx"
    if sl.startswith(("aplus_", "a_plus_")) or origin_n == "aplus_research":
        return "a_plus"
    # F5 keep (dsp_spring / non-fxcross vss) before the dsp_ study prefix.
    # dsp_spring is house_keep, not study. vss_fxcross stays the W7 VSS node.
    if sl.startswith("dsp_spring") or (
        sl.startswith("vss") and not sl.startswith("vss_fxcross")
    ):
        return "house_keep"
    if sl.startswith("dsp_"):
        return "study"
    for node, leaves in FAMILY_LEAVES.items():
        if sl in leaves:
            return node
    if sl.startswith("metals_") or sl.startswith("metal_"):
        return "metals"
    if "crypto" in sl or sl.startswith("kz_london"):
        return "crypto"
    if sl.startswith("sub_"):
        return "substrate"
    if sl.startswith("fx_jpy"):
        return "jpy"
    if sl:
        return "other"
    return "other"


def used_chunks(sleeve: str, node: str | None = None) -> tuple[str, ...]:
    """Query-aware chunks for THIS sleeve. Not the family catalog."""
    sl = _norm(sleeve)
    node = node or family_node_for(sl)
    if sl in SLEEVE_CHUNKS:
        return SLEEVE_CHUNKS[sl]
    if sl.startswith("mx_"):
        if "donchian" in sl:
            return ("donchian",)
        if "volume_surge" in sl:
            return ("surge",)
        if "atr_mean" in sl:
            return ("excursion",)
        return FAMILY_CHUNKS["mx"]
    return FAMILY_CHUNKS.get(node, ("session",))


def directional_snippet(sleeve: str) -> str:
    """Two-layer catalog: a short line so a model can *suggest* the sleeve exists.

    Full schema loads only when this fire's subtree is the query. Do not dump
    the sleeve catalog into one prompt.
    """
    sl = _norm(sleeve)
    if sl in _SNIPPETS:
        return _SNIPPETS[sl]
    if sl.startswith("mx_") and "donchian" in sl:
        return "D1 Donchian-20 breakout family; break quality is Score, window length is a fact"
    if sl.startswith("mx_") and "volume_surge" in sl:
        return "D1 volume-surge reversal family; surge quality is Score, z-threshold is a fact"
    if sl.startswith("mx_") and "atr_mean" in sl:
        return "D1 ATR mean-reversion family; excursion quality is Score"
    if sl:
        return f"named sleeve {sl}; directional only — load subtree schema on this fire"
    return "unnamed sleeve — integer emit stays None"


def hierarchical_labels(
    state: Mapping[str, Any] | None = None,
    *,
    sleeve: str | None = None,
    symbol: str | None = None,
    origin: str | None = None,
    branch: str = "fire",
) -> dict[str, Any]:
    """Nested labels so a later tree-search can find this object. Not a transcript."""
    identity = dict((state or {}).get("identity") or {})
    clock = dict((state or {}).get("clock") or {})
    sl = sleeve if sleeve is not None else identity.get("sleeve")
    sy = symbol if symbol is not None else identity.get("symbol")
    origin_s = origin if origin is not None else identity.get("origin_organism") or "f5_challenge"
    node = family_node_for(str(sl or ""), symbol=str(sy or ""), origin=str(origin_s))
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "origin": origin_s,
        "family_class": identity.get("family_class")
        or family_class_for(str(sl or ""), symbol=str(sy or ""), origin=str(origin_s)),
        "family_node": node,
        "sleeve": sl,
        "symbol": sy,
        "side": identity.get("side"),
        "branch": branch,
        "clock.as_of_utc": clock.get("as_of_utc"),
        "decision_day": identity.get("decision_day"),
        "ticket": identity.get("candidate_id") or identity.get("ticket"),
        "hard_off_family": hard_off_family(str(sl or ""), str(sy or "")),
        "subgoal": f"sleeve:{node}:{_norm(sl)}:{branch}",
    }


def integer_facts() -> tuple[str, ...]:
    return INTEGER_FACTS


def converted_ifs() -> tuple[dict[str, str], ...]:
    """Every sleeve fire / size / exit `if` this seat converts.

    ``still_integer`` is the fact code still computes. ``now`` is the TypeSafe
    shape. Gold: do not re-encode ac60>=0.10. Session and vol stay separate.
    """
    rows = [
        {
            "site": "UB-GEN-METALS-CORE",
            "sleeve": "metals_core",
            "was": "if ac is None or ac < 0.10: return None",
            "now": "persistence Score is the returned parameter, with metals_band_depth; a missing score stays unset",
            "still_integer": "ON_SURFACE, warmup, ATR<=0, FVG detector emit",
        },
        {
            "site": "UB-GEN-METALS-SOFT",
            "sleeve": "metals_softband",
            "was": "if ac >= 0.10 or ac < 0.04: return None; _size_mult_soft linear",
            "now": "same persistence Score; sleeve_size_depth is the returned size parameter",
            "still_integer": "ON_SURFACE, FVG emit, intra_size field presence",
        },
        {
            "site": "UB-GEN-METALS-MICRO",
            "sleeve": "metals_ob_micro",
            "was": "if ac < 0.20: return None; same-bar FVG dedup",
            "now": "persistence Score on the tail; FVG same-bar presence stays a fact",
            "still_integer": "same_bar_fvg_presence, warmup>=200, ON_SURFACE",
        },
        {
            "site": "UB-GEN-CRYPTO",
            "sleeve": "crypto",
            "was": "Donchian-20 close break and ac60>=0.15",
            "now": "donchian_break_quality and crypto_persistence are the returned parameters",
            "still_integer": "ON_SURFACE BTC+DASH, ATR<=0, lookback count",
        },
        {
            "site": "UB-GEN-ENERGY",
            "sleeve": "energy_agri",
            "was": "energy_gate: vr>=2.0 OR |slope|<0.05",
            "now": "energy_ignition Score on vr×slope jointly; session×vol stay separate",
            "still_integer": "ON_SURFACE, FVG emit, ATR<=0",
        },
        {
            "site": "UB-GEN-IDXREV",
            "sleeve": "idxrev",
            "was": "wick beyond prior-16 then close back in",
            "now": "wick_fade_quality Score",
            "still_integer": "ON_SURFACE, named F5 hard-off idxrev, ATR<=0",
        },
        {
            "site": "UB-GEN-JPY-LDN",
            "sleeve": "fx_jpy",
            "was": "server hour>=8 and 4th session bar",
            "now": "session_fitness Score; 4th-bar COUNT stays integer",
            "still_integer": "bar_times present, warmup, hour clock, fourth_session_bar_count",
        },
        {
            "site": "UB-GEN-JPY-NY",
            "sleeve": "fx_jpy_ny",
            "was": "hour>=15 and |impulse|>=1.0 ATR and trend20 align",
            "now": "jpy_impulse_fit Score; hour clock stays a fact",
            "still_integer": "session hour, warmup, bar_times",
        },
        {
            "site": "UB-GEN-XVOL",
            "sleeve": "sub_xvol_pullback",
            "was": "AND of vol=xhi persist=rand trend=up mtf=conflict",
            "now": "cell_fitness Score on named coords as a range",
            "still_integer": "include_clean3, ON_SURFACE, warmup 210, ATR<=0, cell_matches emit",
        },
        {
            "site": "UB-GEN-MIDDN",
            "sleeve": "sub_mid_dn_revert",
            "was": "AND of seven cell buckets including session=ny hour>=16",
            "now": "cell_fitness Score; NY hour is a clock fact",
            "still_integer": "include_clean3, bar_time present, server hour, warmup",
        },
        {
            "site": "UB-GEN-VP",
            "sleeve": "vp_euidx_pocgrav",
            "was": "if abs(dpoc)<2 or in_va or vr<1.2 or rr<0.8: continue",
            "now": "poc_gravitation Score + vp_vol Score",
            "still_integer": "aux M1 present, prior-day profile present, ON_SURFACE",
        },
        {
            "site": "UB-GEN-VOLCOMP",
            "sleeve": "vol_compression",
            "was": "if a > squeeze quantile: return None; then Donchian break",
            "now": "squeeze_quality Score; do not add an ac60 cliff (that kills this sleeve)",
            "still_integer": "include_candidate_book, ON_SURFACE, HIST_LB count",
        },
        {
            "site": "UB-GEN-ASIANFADE",
            "sleeve": "asian_fade",
            "was": "hour 8..21 and first break of Asian range with rejection wick",
            "now": "range_fade_quality Score; session window is a clock fact",
            "still_integer": "bar_times, MIN_ASIAN_BARS, ON_SURFACE",
        },
        {
            "site": "UB-GEN-NYCRYPTO",
            "sleeve": "ny_crypto_momentum",
            "was": "hour==17 and |de|>=0.50 and vol not-low",
            "now": "directional_efficiency + vol_state as ranges plus ny_continuation_quality; 17:00 is a clock fact",
            "still_integer": "decision hour/minute, WINDOW length",
        },
        {
            "site": "UB-GEN-METALREV",
            "sleeve": "metal_session_reversion",
            "was": "NY extension >=Z ATR and HTF not-up then fade",
            "now": "anchor_extension_quality Score; NY hours are a clock fact",
            "still_integer": "session hours 14..21, warmup",
        },
        {
            "site": "UB-GEN-ASIAPDL",
            "sleeve": "asia_pdl_fade",
            "was": "Asia hour 0..6 sweep+reclaim of prior-day low",
            "now": "pdl_reclaim_quality Score; PDL assembled-or-not is a fact",
            "still_integer": "Asia hour clock, prior-day complete",
        },
        {
            "site": "UB-GEN-ORB",
            "sleeve": "orb_crypto_london",
            "was": "if not _low_vol or regime==range: return None; first close beyond OR edge",
            "now": "vol_state and htf_regime are returned parameters, plus orb_quality; F5 named hard-off stays integer",
            "still_integer": "named_hard_off, OR hour-7 bar COUNT, break-window clock 8..11, first_break_of_day",
        },
        {
            "site": "UB-GEN-LIQASIA",
            "sleeve": "liq_asia_up_low_metal",
            "was": "D1-up AND ATR-percentile low AND PDH/PDL sweep+reclaim",
            "now": "htf_regime + vol_state as ranges plus liq_sweep_quality; Asia hour is a clock fact",
            "still_integer": "Asia hour clock, ON_SURFACE, prior-day HL assembled",
        },
        {
            "site": "UB-GEN-KZLDN",
            "sleeve": "kz_london_crypto_low",
            "was": "hour==12 and |de|>=0.50 and ATR rank < 0.34",
            "now": "directional_efficiency + vol_state as ranges plus kz_quality; 12:00 is a clock fact",
            "still_integer": "killzone clock, WINDOW length",
        },
        {
            "site": "UB-GEN-VSS",
            "sleeve": "vss_fxcross_london_up_low",
            "was": "London hour AND D1 sma20>sma50 AND squeeze pctl AND ATR rank < 0.33",
            "now": "htf_regime + vol_state as ranges plus vss_squeeze_quality; London hour is a clock fact",
            "still_integer": "aux D1 present, London hour clock, box length",
        },
        {
            "site": "UB-GEN-VOLSQ",
            "sleeve": "vol_squeeze",
            "was": "if htf_trend==0: return None; ATR quantile squeeze AND expansion body",
            "now": "htf_regime as a range plus squeeze_expansion_quality; not trend==0 as a ban",
            "still_integer": "ON_SURFACE, lookback counts",
        },
        {
            "site": "UB-GEN-NYIDX",
            "sleeve": "ny_index_momentum",
            "was": "hour==17 and |de|>=0.50 and ATR rank in [0.34, 0.67)",
            "now": "directional_efficiency + vol_state as ranges (not the mid-band cliff); 17:00 is a clock fact",
            "still_integer": "decision clock",
        },
        {
            "site": "UB-GEN-STRUCT",
            "sleeve": "structural_retest",
            "was": "fire only in verified (class, session, regime, vol) cells",
            "now": "cell_fitness Score; whitelist membership is a fact",
            "still_integer": "whitelist membership, HTF completed bars",
        },
        {
            "site": "UB-GEN-LEADLAG",
            "sleeve": "session_leadlag_genuine",
            "was": "leader z-impulse ifs; None when leader feed absent",
            "now": "leadlag_quality Score; missing leader feed is integer fail-closed",
            "still_integer": "include_clean4, leader feed present",
        },
        {
            "site": "UB-GEN-MX",
            "sleeve": "mx_*",
            "was": "D1 Donchian / volume-surge / ATR-reversion cliffs",
            "now": "mx_mechanism_quality Score on the named rule; window lengths are facts",
            "still_integer": "include_market_expansion allowlist, mx_us30 named hard-off",
        },
        {
            "site": "UB-SIZE-KELLY",
            "sleeve": "*",
            "was": "Kelly-lite bins as dead numbers",
            "now": "sleeve_size_depth Score tilts; bin COUNT stays integer",
            "still_integer": "kelly_bin_count, conviction ledger union",
        },
        {
            "site": "UB-SIZE-VOLTILT",
            "sleeve": "sub_*",
            "was": "VOL_LEVEL_TILT vr buckets as a boolean overlay",
            "now": "sleeve_size_depth reads named vr as a range; overlay flag stays integer",
            "still_integer": "VOL_LEVEL_TILT default-off flag",
        },
        {
            "site": "UB-EXIT-PROFILE",
            "sleeve": "*",
            "was": "SLEEVE_EXIT_PROFILES[sleeve] dict pick",
            "now": "exit_profile_fit Score vs named tape; resolve_exit_profile still code",
            "still_integer": "profile dict, time_stop_bars unit, frontier_exits_selection",
        },
        {
            "site": "UB-EXIT-FRONTIER",
            "sleeve": "frontier named",
            "was": "FRONTIER_EXIT_OVERRIDES if selected",
            "now": "frontier_cell_fit Score; selection ceremony stays integer",
            "still_integer": "frontier_exits_selection, unknown-name refuse at launch",
        },
        {
            "site": "UB-ADM-SLEEVE-SELECT",
            "sleeve": "unit",
            "was": "which sleeve wins a multi-member unit",
            "now": "sleeve_select Choice among siblings of this family node",
            "still_integer": "unit occupancy keep-one, named surface",
        },
        {
            "site": "UB-REG-TAGS",
            "sleeve": "*",
            "was": "--tags / include_clean3 / include_candidate_book ifs",
            "now": "not converted — registry flags stay facts",
            "still_integer": "tags_intersection, include_* flags",
        },
        {
            "site": "UB-REG-CONF-ZERO",
            "sleeve": "quarantined candidates",
            "was": "if confidence<=0.0: continue",
            "now": "not converted — zero-confidence quarantine stays a fact",
            "still_integer": "candidate_confidence_zero",
        },
        {
            "site": "UB-ADM-A8",
            "sleeve": "metals_core, metals_softband",
            "was": "if metals_confluence_gate and K<3: drop",
            "now": "gold a8_quality Score may move K; integer K=3-of-4 still computes. Not re-asked on this subtree (merge reuses gold ID)",
            "still_integer": "metals_confluence_gate_enabled, a8_k_of_4_count",
        },
        {
            "site": "UB-F5-KEEP",
            "sleeve": "dsp_spring_*, vss_* (not vss_fxcross)",
            "was": "F5 keep-family tag ifs",
            "now": "house_keep_quality Score; named hard-off families stay integer",
            "still_integer": "named_hard_off, keep_family routing",
        },
        {
            "site": "UB-F5-APLUS",
            "sleeve": "aplus_*",
            "was": "A+ pack ready ifs",
            "now": "aplus_ready Score as a range; pack integer facts stay computed",
            "still_integer": "pack field presence, origin_organism",
        },
        {
            "site": "UB-F5-STUDY",
            "sleeve": "dsp_* (not spring)",
            "was": "DSP study-prefix fire ifs",
            "now": "dsp_study_quality Score; starve/hard-off stay integer",
            "still_integer": "STUDY_PREFIXES membership",
        },
        {
            "site": "UB-SCHEMA-HOP",
            "sleeve": "*",
            "was": "dump fire+size+exit schema on every sleeve tick",
            "now": "hierarchical branch: fire asks fire+size_depth; exit asks exit_profile_fit. Not a Noul per tick",
            "still_integer": "branch name is code",
        },
    ]
    return tuple(rows)


def ignore_if(question_id: str, state: Mapping[str, Any] | None) -> bool:
    """Query-aware compression: skip a question when its named chunk is unassembled."""
    state = state or {}
    news = dict(state.get("news") or {})
    levels = dict(state.get("levels") or {})
    feats = dict(state.get("sleeve_features") or {})
    sessions = dict(state.get("sessions") or {})
    qid = _norm(question_id)
    if qid in {"event_proximity", "event_size", "calendar_honest"}:
        return bool(news.get("spine_empty"))
    if qid in {"level_respect", "include_levels", "pdl_reclaim_quality"}:
        return _norm(levels.get("source")) == "unassembled"
    if qid in {"persistence", "crypto_persistence", "metals_band_depth", "include_ac60", "ac60_size"}:
        return feats.get("ac60") is None
    if qid in {"a8_quality", "a8_agrees", "include_a8"}:
        sleeve = _norm((state.get("identity") or {}).get("sleeve"))
        return not sleeve.startswith("metals_")
    if qid in {"session_fitness", "include_session", "jpy_impulse_fit"}:
        return _norm(sessions.get("source")) == "unassembled"
    if qid in {"vol_state", "include_vol"}:
        vol_bucket = _norm((state.get("regime") or {}).get("vol_bucket"))
        return feats.get("vol_ratio") is None and vol_bucket in {"", "unassembled"}
    if qid in {"htf_regime", "include_regime", "include_d1"}:
        return feats.get("htf_slope_norm") is None and feats.get("d1_regime") is None
    if qid in {"directional_efficiency", "include_de"}:
        return feats.get("de") is None and feats.get("directional_efficiency") is None
    if qid == "frontier_cell_fit":
        return not bool((state.get("exit") or {}).get("frontier_selected"))
    if qid == "leadlag_quality":
        return not bool(feats.get("leader_feed_present"))
    return False


def _score_q(instructions: str, criteria: list[str]) -> dict[str, Any]:
    text = str(instructions).strip()
    if "empty score leaves" not in text.lower():
        text = (
            text
            + " The score you return is that parameter. It may sit between the levels."
            + " An empty score leaves the parameter unset."
        )
    return {"type": "score", "instructions": text, "criteria": list(criteria)}


def _choice_q(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = str(instructions).strip()
    if "tie leaves" not in text.lower():
        text = (
            text
            + " The unique highest probability is the decision."
            + " An empty answer or a tie leaves the choice unset."
        )
    kept = {
        str(key): str(value)
        for key, value in criteria.items()
        if "floor" not in str(key).lower() and "baseline" not in str(key).lower()
    }
    return {"type": "choice", "instructions": text, "criteria": kept}


def _noul_q(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = str(instructions).strip()
    if "empty answer leaves" not in text.lower():
        text = text + " An empty answer leaves this unset."
    return {"type": "noul", "instructions": text, "criteria": dict(criteria)}


def _size_depth_q() -> dict[str, Any]:
    return _score_q(
        (
            "How much size does this named sleeve deserve versus named tape? "
            "The score you return is that size parameter. It may sit between the levels. "
            "An empty score leaves the parameter unset. A missing score does not zero a fire. "
            "Kelly bin count is an integer fact."
        ),
        [
            "Size is light versus named tape",
            "Ordinary size versus named tape",
            "Named tape supports more size",
        ],
    )


def _include_q(chunk: str) -> dict[str, Any]:
    return _score_q(
        (
            f"For this fire's query, how much of the named `{chunk}` chunk of gold_state "
            "should be in context? hide / short / long / full. This is include-depth, "
            "not keep/drop of the sleeve. Unused chunks are not asked."
        ),
        list(INCLUDE_DEPTH_CRITERIA),
        )


def _chunk_quality_questions(chunks: tuple[str, ...], node: str, sleeve: str) -> dict[str, dict[str, Any]]:
    """Hop 2: one quality Score per used chunk. Not a Noul per sleeve tick."""
    sl = _norm(sleeve)
    out: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        if (
            chunk == "vol"
            and node not in _NO_GENERIC_VOL_NODES
            and sl not in _NO_GENERIC_VOL_SLEEVES
        ):
            out["vol_state"] = _score_q(
                (
                    "Named vol-state as a range for THIS sleeve. "
                    "A printed vol cliff is not this score. "
                    "Session fitness is a different question — do not AND them here."
                ),
                [
                    "Vol-state fights this sleeve fire",
                    "Ordinary / mixed vol",
                    "Named vol-state fits this sleeve",
                ],
            )
        elif chunk in {"regime", "d1"}:
            out["htf_regime"] = _score_q(
                (
                    "HTF / prior-D1 regime as a range for THIS sleeve. "
                    "A printed slope cliff or a ban list is not this score. "
                    "Clock hour is a fact."
                ),
                [
                    "Named HTF/D1 regime fights this fire",
                    "Ordinary / mixed regime",
                    "Named regime fits this sleeve",
                ],
            )
        elif chunk == "de":
            out["directional_efficiency"] = _score_q(
                (
                    "Window directional-efficiency as a range. A printed efficiency cliff is not this score. "
                    "Vol-state is a different Score. Decision hour/minute is a clock fact."
                ),
                [
                    "Move is a coin / chase versus named tape",
                    "Ordinary directional efficiency",
                    "Clean one-way move fits this sleeve",
                ],
            )
    return out


def _family_fire_questions(node: str, sleeve: str) -> dict[str, dict[str, Any]]:
    """Second hop: schema for this family subtree only."""
    sl = _norm(sleeve)
    out: dict[str, dict[str, Any]] = {}
    if node == "metals" and sl != "metal_session_reversion":
        out["metals_band_depth"] = _score_q(
            (
                "Given sleeve_features.ac60 and identity.sleeve "
                "(core / softband / micro) plus flow_stance in this request, how well "
                "does persistence fit THIS named metals sleeve? "
                "A printed persistence cliff is not this score."
            ),
            [
                "Named ac60 fights this metals sleeve / side",
                "Ordinary / mixed persistence",
                "Persistence fits this named metals sleeve given flow",
            ],
        )
    if sl == "crypto":
        out["donchian_break_quality"] = _score_q(
            (
                "Is the close-vs-prior-window break a range versus named tape, "
                "not a boolean c>hh? Window length is a fact."
            ),
            [
                "Break is noise versus named vol",
                "Ordinary channel break",
                "Break fits named vol and side",
            ],
        )
        out["crypto_persistence"] = _score_q(
            (
                "ac60 as a range for this crypto fire. "
                "A printed persistence cliff is not this score. "
                "vol_compression must not gain an ac60 gate."
            ),
            [
                "Persistence fights this crypto fire",
                "Ordinary / mixed",
                "Persistence supports the named break",
            ],
        )
    if node == "energy":
        out["energy_ignition"] = _score_q(
            (
                "Joint vr and slope ignition as a range. A printed vol or slope cliff is not this score. "
                "Session fitness is a different question — do not AND them here."
            ),
            [
                "Neither vol shock nor flat continuation",
                "Mixed / ordinary energy state",
                "Named tape shows ignition or flat continuation",
            ],
        )
    if node == "jpy":
        out["jpy_impulse_fit"] = _score_q(
            (
                "Opening impulse versus ATR as a range for this JPY session sleeve. "
                "Hour clock and 4th-bar COUNT are facts, not this Score."
            ),
            [
                "Impulse fights the session fire",
                "Ordinary impulse",
                "Impulse fits the named session sleeve",
            ],
        )
    if node in {"substrate", "structural"}:
        out["cell_fitness"] = _score_q(
            (
                "Do named cell coords fit this sleeve's cell as a range, not an AND of "
                "bucket cliffs? Integer still computes cell_matches for emit."
            ),
            [
                "Named coords fight the cell",
                "Mixed / partial cell fit",
                "Named coords fit the cell",
            ],
        )
    if node == "volprofile":
        out["poc_gravitation"] = _score_q(
            "POC distance versus value-area as a range. A printed distance cliff is not this score.",
            [
                "Inside value or too close to POC",
                "Ordinary distance",
                "Far-from-POC gravitation fits",
            ],
        )
        out["vp_vol"] = _score_q(
            "Named vr as a range for POC-gravitation. A printed vol cliff is not this score. Separate from session.",
            [
                "Vol fights the gravitation fire",
                "Ordinary vol",
                "Vol supports the named fire",
            ],
        )
    if node == "index" and sl == "idxrev":
        out["wick_fade_quality"] = _score_q(
            "Wick-beyond then close-back-in as a range versus named vol, not wick-or-not.",
            [
                "Wick is noise / stop likely dies",
                "Ordinary fade",
                "Fade fits named tape",
            ],
        )
    if node == "fx_reversion":
        out["range_fade_quality"] = _score_q(
            "Asian-range break + rejection wick as a range. Session window is a clock fact.",
            [
                "Break/wick fights a fade",
                "Ordinary fade",
                "Fade fits the named range",
            ],
        )
    if node == "liquidity":
        out["pdl_reclaim_quality"] = _score_q(
            "PDL sweep+reclaim quality. Unassembled PDL → ignore-if. Asia hour is a fact.",
            [
                "Sweep/reclaim fights a long fade",
                "Ordinary reclaim",
                "Reclaim holds a named PDL",
            ],
        )
    if sl in {"ny_crypto_momentum", "ny_index_momentum"}:
        out["ny_continuation_quality"] = _score_q(
            (
                "NY killzone continuation as a range on directional efficiency and vol-state. "
                "17:00 / session clock is a fact. Session and vol are separate Scores."
            ),
            [
                "Continuation is a chase / low-vol coin",
                "Ordinary continuation",
                "Clean NY continuation on named vol",
            ],
        )
    if sl == "metal_session_reversion":
        out["anchor_extension_quality"] = _score_q(
            "NY anchor extension fade as a range. HTF-not-up is this Score, not a ban list.",
            [
                "Extension fights a fade (or HTF is a strong up)",
                "Ordinary extension",
                "Extension fits a named fade",
            ],
        )
    if sl == "vol_compression":
        out["squeeze_quality"] = _score_q(
            "ATR compression then range-break as a range. Do not add ac60. Session is separate.",
            [
                "Not compressed / break is noise",
                "Ordinary squeeze-break",
                "Compression-break fits named vol",
            ],
        )
    if sl == "vol_squeeze":
        out["squeeze_expansion_quality"] = _score_q(
            "ATR-percentile squeeze + expansion body as a range. Vol-state is the edge, not bar shape.",
            [
                "No squeeze / expansion fights HTF",
                "Ordinary squeeze-expansion",
                "Vol-state expansion fits HTF",
            ],
        )
    if sl == "orb_crypto_london":
        out["orb_quality"] = _score_q(
            "London ORB quality as a range. Named F5 hard-off is integer, not this Score.",
            [
                "ORB fights the fire",
                "Ordinary ORB",
                "ORB fits named tape",
            ],
        )
    if sl == "liq_asia_up_low_metal":
        out["liq_sweep_quality"] = _score_q(
            "Asia up-low metal liquidity sweep as a range. Session clock is a fact.",
            [
                "Sweep fights the fire",
                "Ordinary sweep",
                "Sweep fits named levels",
            ],
        )
    if sl == "kz_london_crypto_low":
        out["kz_quality"] = _score_q(
            "London killzone crypto quality. Hour is a fact. Vol-state is this Score, separate from session.",
            [
                "Killzone fire is a coin on this vol",
                "Ordinary killzone",
                "Killzone fits named low-vol tape",
            ],
        )
    if sl == "vss_fxcross_london_up_low":
        out["vss_squeeze_quality"] = _score_q(
            "VSS FX-cross London squeeze as a range. Session clock is a fact.",
            [
                "Squeeze fights the fire",
                "Ordinary VSS",
                "Squeeze fits the named cross",
            ],
        )
    if sl == "session_leadlag_genuine":
        out["leadlag_quality"] = _score_q(
            "Leader-follower impulse quality. Missing leader feed is ignore-if, not 'no impulse'.",
            [
                "Leader impulse fights the follower fire",
                "Ordinary lead-lag",
                "Named leader supports the follower",
            ],
        )
    if node == "mx":
        out["mx_mechanism_quality"] = _score_q(
            (
                "Named D1 mechanism (Donchian-20 / volume-surge / ATR-reversion) as a range. "
                "Window length and allowlist are facts. mx_us30 named hard-off is integer."
            ),
            [
                "Mechanism fights this D1 fire",
                "Ordinary D1 mechanism",
                "Mechanism fits named tape",
            ],
        )
    if node == "house_keep":
        out["house_keep_quality"] = _score_q(
            (
                "F5 keep-family (dsp_spring / vss) quality as a range. "
                "Named hard-off families stay integer. Not a keep/drop of every F5 tag."
            ),
            [
                "Keep-family fire fights named tape",
                "Ordinary keep-family",
                "Keep-family fits named Challenge tape",
            ],
        )
    if node == "a_plus":
        out["aplus_ready"] = _score_q(
            (
                "A+ study sleeve readiness as a range. Pack integer facts stay computed. "
                "Not a linear keep/drop of every aplus_ tag."
            ),
            [
                "A+ setup is not ready on this tape",
                "Ordinary / mixed A+",
                "A+ setup fits named Challenge tape",
            ],
        )
    if node == "study":
        out["dsp_study_quality"] = _score_q(
            "DSP study-prefix quality as a range. Starve/hard-off are integer facts.",
            [
                "Study fire fights named tape",
                "Ordinary study",
                "Study fire fits named tape",
            ],
        )
    return out


def sleeve_subtree_questions(
    state: Mapping[str, Any] | None,
    *,
    standalone: bool = True,
    branch: str = "fire",
) -> dict[str, dict[str, Any]]:
    """Fan-out for THIS sleeve's subtree only. Speculative, ask_together.

    Not a Noul over the catalog. Completeness Noul is included only when
    ``standalone`` (this payload is the request). When merging into the gold
    POST, pass ``standalone=False`` and reuse gold ``state_sufficient``.
    """
    state = state or {}
    identity = dict(state.get("identity") or {})
    sleeve = str(identity.get("sleeve") or "")
    symbol = str(identity.get("symbol") or "")
    origin = str(identity.get("origin_organism") or "f5_challenge")
    node = family_node_for(sleeve, symbol=symbol, origin=origin)
    questions: dict[str, dict[str, Any]] = {}
    if standalone:
        questions["sleeve_state_sufficient"] = _noul_q(
            (
                "Is THIS gold_state object complete enough to judge this named sleeve "
                "fire as-of clock.as_of_utc? One Noul on this object — not a scan of "
                "every sleeve, field, bar, or tick. Empty news spine is not 'no HIGH'."
            ),
            {
                "true": "Named sleeve blocks are present enough to judge this fire",
                "false": "A required named block for this sleeve is missing",
            },
        )
    questions["sleeve_family_node"] = _choice_q(
        (
            "Confirm the family tree node for identity.sleeve. This is hierarchical "
            "routing, not a keep/drop of every sleeve. Code already named the sleeve; "
            "do not rediscover bleed as a Noul."
        ),
        {
            "metals": "Metals FVG / OB / session-reversion family",
            "crypto": "Crypto Donchian / killzone / compression family",
            "energy": "Energy FVG ignition family",
            "jpy": "JPY session-momentum family",
            "substrate": "Substrate cell family",
            "volprofile": "EU index POC-gravitation",
            "index": "Index fade / squeeze family",
            "fx_reversion": "FX Asian-fade family",
            "liquidity": "PDL sweep family",
            "structural": "Structural retest whitelist",
            "leadlag": "Session lead-lag",
            "vss": "VSS FX-cross",
            "mx": "Market-expansion D1 family",
            "house_keep": "F5 keep family",
            "a_plus": "A+ study family",
            "study": "DSP study family",
            "other": "Named other / unknown",
        },
    )
    chunks = used_chunks(sleeve, node)
    if branch in {"fire", "size"}:
        for chunk in chunks:
            questions[f"include_{chunk}"] = _include_q(chunk)
        questions.update(_chunk_quality_questions(chunks, node, sleeve))
    if branch == "fire":
        questions.update(_family_fire_questions(node, sleeve))
        questions["sleeve_size_depth"] = _size_depth_q()
        members = list(identity.get("sleeve_members") or [])
        members = [str(m) for m in members if str(m).strip()]
        if len(members) > 1:
            criteria = {m: f"Sibling {m} wins the unit" for m in members}
            criteria["no_clear_winner"] = "Siblings are mixed; code occupancy stays"
            questions["sleeve_select"] = _choice_q(
                (
                    "Which sibling of this family node deserves remaining headroom? "
                    "Tree-search among siblings, not a linear scan of the book. "
                    "Does not invent headroom."
                ),
                criteria,
            )
    elif branch == "size":
        questions["sleeve_size_depth"] = _size_depth_q()
        if node == "metals":
            fire_q = _family_fire_questions(node, sleeve)
            if "metals_band_depth" in fire_q:
                questions["metals_band_depth"] = fire_q["metals_band_depth"]
    elif branch == "exit":
        questions["exit_profile_fit"] = _score_q(
            (
                "Does the named SLEEVE_EXIT_PROFILES policy (time_stop / "
                "partial_be_runner / trailing_runner) fit this tape? Code still "
                "resolves the profile. time_stop is first-class. Do not wrap "
                "resolve_exit_profile."
            ),
            [
                "Named exit policy fights this tape",
                "Ordinary house exit",
                "Named exit policy fits this tape",
            ],
        )
        if (state.get("exit") or {}).get("frontier_selected"):
            questions["frontier_cell_fit"] = _score_q(
                "Does the selected frontier cell fit this tape? Selection is integer.",
                [
                    "Frontier cell fights this tape",
                    "Ordinary / unused",
                    "Frontier cell fits this tape",
                ],
            )
    # Drop ignore-if questions — query-aware compression. One subtree, not a flat catalog.
    return {
        qid: spec
        for qid, spec in questions.items()
        if not ignore_if(qid, state) and not _asks_limit(qid, spec)
    }


def noul_question_ids(questions: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(qid for qid, spec in questions.items() if isinstance(spec, dict) and spec.get("type") == "noul")


def asked_include_chunks(questions: Mapping[str, Any]) -> tuple[str, ...]:
    out = []
    for qid in questions:
        if qid.startswith("include_"):
            out.append(qid[len("include_") :])
    return tuple(out)


_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe and probe in compact:
            return True
    return False


def _question_blob(qid: str, spec: Mapping[str, Any]) -> str:
    parts = [str(qid), str(spec.get("instructions") or "")]
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, value in criteria.items():
            parts.append(str(key))
            parts.append(str(value))
    elif isinstance(criteria, (list, tuple)) and not isinstance(criteria, (str, bytes)):
        parts.extend(str(item) for item in criteria)
    return " ".join(parts)


def _asks_limit(qid: str, spec: Mapping[str, Any]) -> bool:
    """Floor and baseline are not a question. Only Noul, Choice, or Score are asked."""
    if not isinstance(spec, Mapping):
        return True
    if str(spec.get("type") or "") not in {"noul", "choice", "score"}:
        return True
    blob = _question_blob(qid, spec).lower()
    if "floor" in blob or "baseline" in blob:
        return True
    return _banned_text(blob)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar text from the ask copy."""
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(str(key)):
                continue
            out[str(key)] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return [_scrub(item) for item in value]
    if isinstance(value, str) and _banned_text(value):
        return ""
    return value


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


def _unique_choice(block: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label stays unset."""
    if not isinstance(block, Mapping) or not order:
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(val)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = None
        best: str | None = None
        best_p: float | None = None
        tied = False
        for name in order:
            if name not in numeric:
                continue
            prob = numeric[name]
            if best_p is None or prob > best_p + 1e-12:
                best = name
                best_p = prob
                tied = False
            elif abs(prob - best_p) <= 1e-12:
                tied = True
        if not tied:
            picked = best
    if picked is None or str(picked) not in set(order):
        return None
    return str(picked)


def _score_of(block: Any) -> float | None:
    """The parameter is the returned score. A miss does not restore a constant."""
    if not isinstance(block, Mapping):
        return None
    number: Any = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _finite(number)
    if parsed is not None:
        return parsed
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _finite(raw)


def _noul_of(block: Any) -> bool | float | None:
    if not isinstance(block, Mapping) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _remember(state: Mapping[str, Any], qid: str, value: Any, error: str | None) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        return


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []


def _post(state: dict[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    """One System One evaluate for this subtree. Empty and error leave answers unset."""
    _attach_priors(state, questions)
    state["model"] = MODEL
    try:
        from .jev_client import evaluate
    except Exception:
        return {}, "import_failed"
    try:
        receipt = evaluate(
            state,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        ) or {}
    except Exception as exc:  # noqa: BLE001 — the subtree ask must not raise
        return {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict"
    if not receipt.get("ok"):
        err = receipt.get("error") or receipt.get("skipped") or "error"
        return {}, str(err)
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        return {}, str(err)
    return answers, None


def decide_sleeve(
    state: Mapping[str, Any] | None = None,
    *,
    branch: str = "fire",
    standalone: bool = True,
) -> dict[str, Any]:
    """Ask this fire's subtree once. Each decision and parameter is that return.

    The tree stays one hierarchical piece. An empty answer, a tie, or an error
    leaves that return unset. This function does not send.
    """
    cleaned = _scrub(dict(state or {}))
    if not isinstance(cleaned, dict):
        cleaned = {}
    questions = sleeve_subtree_questions(cleaned, standalone=standalone, branch=branch)
    questions = {
        str(qid): spec
        for qid, spec in questions.items()
        if isinstance(spec, dict) and not _asks_limit(str(qid), spec)
    }
    answers, error = _post(cleaned, questions)
    decisions: dict[str, Any] = {}
    parameters: dict[str, float | None] = {}
    for qid, spec in questions.items():
        kind = str(spec.get("type") or "")
        block = answers.get(qid) if error is None else None
        value: Any = None
        miss: str | None = error
        if error is None and kind == "noul":
            value = _noul_of(block)
            miss = None if value is not None else "noul_missing"
        elif error is None and kind == "choice":
            criteria = spec.get("criteria")
            order = tuple(str(key) for key in criteria) if isinstance(criteria, Mapping) else ()
            value = _unique_choice(block, order)
            miss = None if value is not None else "tie_or_empty"
        elif error is None and kind == "score":
            value = _score_of(block)
            miss = None if value is not None else "score_missing"
        elif error is None:
            miss = "unset"
        decisions[qid] = value
        if kind == "score":
            parameters[qid] = value if _finite(value) is not None else None
        _remember(cleaned, qid, value, miss)
    return {
        "model": MODEL,
        "branch": branch,
        "asked": tuple(questions),
        "decisions": decisions,
        "parameters": parameters,
        "error": error,
        "may_send": False,
    }

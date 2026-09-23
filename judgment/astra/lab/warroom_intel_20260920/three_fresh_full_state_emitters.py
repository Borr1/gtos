#!/usr/bin/env python3
"""Three-fresh full-state SHADOW emitters (apply=false).

Chair LOCK — three_fresh_status=RESEARCH_OPEN_DUAL_LENS
  Dig_3R  = monitor (hold+ train− honesty); WR floor = monitor not kill
  Edge_ATR = research exit candidate (do NOT claim Dig 13/13)
  KEEP_WIN_SUBTYPE long only · promote=false · place=false
  NEVER fade shorts / NEVER port dsp_three_fresh_lower_lows shorts

Writers (capture-intelligence, not promote):
  1) inventory.alive_sleeves_for_symbol — Dig compose:
       build_slots ∩ armed ∩ inventory
       armed = RESEARCH overlay (research_armed_tags), NOT live_armed_set mutation
       Stamp armed_source=research_armed_tags vs live_armed
  2) regime_tag — S14 hydrate-when-present; null OK; never invent
  3) fanout Choice/Score/Noul — KEEP|STAND|REVIEW (long-path only)
  4) exit_model_tag — Dig_3R | Edge_ATR (dual-lens honesty; two stamp variants)

FORBIDDEN: place · NEWS invent · cost kill · live promote · merge Dig/Edge R
           · fade shorts · mutate live_armed_set.json
Affinity: XAUUSD × dsp_three_fresh
Reuse: expanding_full_state_emitters.py + THREE_FRESH_DEEPEN_20260920.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# Local Dig helpers (war_room path)
import sys as _sys_boot
if str(Path(__file__).resolve().parent) not in _sys_boot.path:
    _sys_boot.path.insert(0, str(Path(__file__).resolve().parent))
from sleeve_on_surface_loader import load_sleeve_module  # noqa: E402

_BOX = Path("/workspace/gtos/close_loop/war_room_20260920")
_GTOS = Path("/workspace/gtos")
_SWARM_SRC = _GTOS / "_swarm_land_tip/extract/src"
_SWARM_SLEEVES = _SWARM_SRC / "components/ultimate_book/sleeves"
_ARMED_JSON = _GTOS / "_swarm_land_tip/extract/config/live_armed_set.json"
_FABLE_REG = _GTOS / "redacted_host/parked/sleeves/registry.py"
_WARROOM_SRC = _GTOS / "judgment/warroom_shadow"
_DIG_JSON = _BOX / "ALIVE_SLEEVES_FOR_SYMBOL_POINTERS_DIG_20260920.json"
_DEEPEN = _BOX / "THREE_FRESH_DEEPEN_20260920.json"
_DIG_BLOTTER = (
    _GTOS / "research/warroom_20260920/multiyear/blotter_PRIMARY_XAUUSD_dsp_three_fresh.jsonl"
)
_EDGE_LOSER = Path(
    "/workspace/instrument-edge/packs/XAU_THREE_FRESH_2022_LOSER_SAMPLES_PLAIN_20260920.json"
)
_STAMP_DIR = _BOX / "shadow_stamps_three_fresh_full_state"
_LEARNING = _GTOS / "close_loop/learning_rows.jsonl"

AFFINITY_SYMBOL = "XAUUSD"
AFFINITY_SLEEVE = "dsp_three_fresh_lower_lows"  # full module TAG (alias: dsp_three_fresh)
AFFINITY_ALIASES: Tuple[str, ...] = ("dsp_three_fresh", "dsp_three_fresh_lower_lows")
SCHEMA = "gtos.warroom_shadow.three_fresh_full_state_stamp.v1"
THREE_FRESH_STATUS = "RESEARCH_OPEN_DUAL_LENS"

_OVERLAY_JSON = _BOX / "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"
_MODULE_ATR_BLOTTER = _BOX / "blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl"
_MODULE_ATR_YEARFOLD = _BOX / "THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.json"
_VOTER_STAMP_JSONL = _BOX / "shadow_stamps_three_fresh_full_state" / "THREE_FRESH_MODULE_ATR_JEV_VOTER_STAMPS_20260920.jsonl"

# Chair NAME research overlay — SHADOW only. Never write live_armed_set.json.
# Prefer overlay JSON full module TAGs; fallback aliases kept for Dig blotter honesty.
def _load_research_armed_tags() -> Tuple[str, ...]:
    if _OVERLAY_JSON.exists():
        body = json.loads(_OVERLAY_JSON.read_text())
        tags = body.get("research_armed_tags") or []
        if tags:
            return tuple(str(t) for t in tags)
    return (
        "dsp_three_fresh_lower_lows",
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_expanding_up_staircase",
    )

RESEARCH_ARMED_TAGS: Tuple[str, ...] = _load_research_armed_tags()
# Dual-lens + Module_ATR third lens (NEVER merge R universes)
EXIT_MODEL_TAGS: Tuple[str, ...] = ("Dig_3R", "Edge_ATR", "Module_ATR")

# Mapping honesty (sketch verbs → REAL menu). B_SIZE_HALF / E_KEEP_CAP unused here.
CHOICE_VERB_TO_MENU = {
    "KEEP": "D_FULL",
    "STAND": "A_STAND_DOWN",
    "REVIEW": "C_SIZE_TRIM",
}
REAL_MENU = ("A_STAND_DOWN", "B_SIZE_HALF", "C_SIZE_TRIM", "D_FULL", "E_KEEP_CAP")
MAPPING_HONESTY = (
    "KEEP→D_FULL; STAND→A_STAND_DOWN; REVIEW→C_SIZE_TRIM; "
    "B_SIZE_HALF/E_KEEP_CAP unused in three_fresh sketch (STRIKE_WHEN_RIGHT may emit E_KEEP_CAP)"
)

# Fade / short nouns — NEVER KEEP. Do NOT treat affinity TAG substring as fade.
_FADE_SHORT_MARKERS = (
    "fade_short",
    "three_bar_squeeze",
    "NEGCTRL",
)


@dataclass(frozen=True)
class _Spec:
    tag: str
    on_surface: tuple


def _ict_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M ICT")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Armed: live (read-only) vs research overlay (inject; never mutate live)
# ---------------------------------------------------------------------------

def load_live_armed_sleeves(account: Optional[str] = None) -> Tuple[frozenset, Dict[str, Any]]:
    """Read-only live_armed_set.json. Never mutate."""
    meta: Dict[str, Any] = {
        "source": None,
        "path": str(_ARMED_JSON),
        "mutated": False,
    }
    if _ARMED_JSON.exists():
        body = json.loads(_ARMED_JSON.read_text())
        accounts = body.get("accounts") or {}
        out: set = set()
        if account and account in accounts:
            out |= set(accounts[account].get("armed_sleeves") or [])
            meta["account"] = account
        else:
            for row in accounts.values():
                out |= set(row.get("armed_sleeves") or [])
            meta["account"] = "union"
        meta["source"] = "live_armed_set.json"
        return frozenset(out), meta
    meta["source"] = "unavailable"
    return frozenset(), meta


def research_armed_overlay(
    *,
    account: Optional[str] = None,
    extra_tags: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Chair research overlay. Does NOT write live_armed_set."""
    live, live_meta = load_live_armed_sleeves(account)
    research = list(RESEARCH_ARMED_TAGS)
    if extra_tags:
        for t in extra_tags:
            if t not in research:
                research.append(str(t))
    return {
        "armed_source": "research_armed_tags",
        "research_armed_tags": research,
        "live_armed_tags": sorted(live),
        "live_armed_meta": live_meta,
        "live_armed_set_mutated": False,
        "note": "SHADOW research overlay for XAUUSD affinity — do not mutate live_armed_set.json",
    }


# ---------------------------------------------------------------------------
# Dig compose ingredients (same recipe as expanding)
# ---------------------------------------------------------------------------

def _import_build_slots():
    if str(_SWARM_SRC) not in sys.path:
        sys.path.insert(0, str(_SWARM_SRC))
    from components.ultimate_book.symbol_resolution_watch import build_slots  # type: ignore
    return build_slots


def _parse_on_surface_tuple(text: str, name: str) -> Optional[tuple]:
    import re
    # Support ON_SURFACE = (...) and ON_SURFACE: tuple[str, ...] = (...)
    pat = rf"(?:^|\n){name}\s*(?::[^=\n]+)?\s*=\s*\((.*?)\)"
    m = re.search(pat, text, re.S)
    if not m:
        # legacy colon-only form ON_SURFACE: ("A",)
        pat2 = rf"(?:^|\n){name}\s*:\s*\((.*?)\)"
        m = re.search(pat2, text, re.S)
    if not m:
        return None
    inner = m.group(1)
    syms = re.findall(r'["\']([A-Za-z0-9_\.]+)["\']', inner)
    return tuple(syms) if syms else tuple()


def load_on_surface_specs_from_disk() -> Tuple[List[_Spec], Dict[str, Any]]:
    """Build SleeveSpec-like list. Never invent ON_SURFACE for missing modules."""
    notes: Dict[str, Any] = {
        "swarm_sleeves_dir": str(_SWARM_SLEEVES),
        "missing_on_surface_modules": [],
        "loaded_tags": [],
    }
    known = {
        "metals_core": ("metals", "ON_SURFACE"),
        "metals_softband": ("metals", "ON_SURFACE"),
        "crypto": ("crypto", "ON_SURFACE"),
        "energy_agri": ("energy_agri", "ON_SURFACE"),
        "idxrev": ("index_jpy", "IDXREV_ON_SURFACE"),
        "metals_ob_micro": ("metals_ob_micro", "ON_SURFACE"),
        "fx_jpy": ("fx_jpy", "ON_SURFACE"),
        "fx_jpy_ny": ("fx_jpy", "ON_SURFACE"),
        "vol_compression": ("vol_compression", "ON_SURFACE"),
        "asian_fade": ("asian_fade", "ON_SURFACE"),
        "ny_crypto_momentum": ("ny_crypto_momentum", "ON_SURFACE"),
        "metal_session_reversion": ("metal_session_reversion", "ON_SURFACE"),
        "asia_pdl_fade": ("asia_pdl_fade", "ON_SURFACE"),
        "orb_crypto_london": ("orb_crypto_london", "ON_SURFACE"),
        "liq_asia_up_low_metal": ("liq_asia_up_low_metal", "ON_SURFACE"),
        "kz_london_crypto_low": ("kz_london_crypto_low", "ON_SURFACE"),
        "vss_fxcross_london_up_low": ("vss_fxcross_london_up_low", "ON_SURFACE"),
    }
    displacement_tags = []
    if _FABLE_REG.exists():
        import re
        displacement_tags = re.findall(
            r'"(dsp_[^"]+|xa_[^"]+)"\s*:\s*SleeveSpec',
            _FABLE_REG.read_text(encoding="utf-8", errors="replace"),
        )
        notes["displacement_tags_named_in_registry"] = sorted(set(displacement_tags))

    specs: List[_Spec] = []
    seen = set()

    def _add(tag: str, surface: tuple) -> None:
        if tag in seen:
            return
        seen.add(tag)
        specs.append(_Spec(tag=tag, on_surface=tuple(surface)))
        notes["loaded_tags"].append(tag)

    for tag, (stem, attr) in known.items():
        path = _SWARM_SLEEVES / f"{stem}.py"
        if not path.exists():
            notes["missing_on_surface_modules"].append({"tag": tag, "path": str(path)})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        surface = _parse_on_surface_tuple(text, attr)
        if surface is None:
            notes["missing_on_surface_modules"].append(
                {"tag": tag, "path": str(path), "attr": attr}
            )
            continue
        _add(tag, surface)

    parked = _GTOS / "redacted_host/parked/sleeves"
    recovered = _GTOS / "research/codila_absorb/war_room/recovered"
    # Prefer sleeve_on_surface_loader (alias→full TAG + recovered/parked paths)
    research_tags = set(RESEARCH_ARMED_TAGS) | set(AFFINITY_ALIASES) | set(displacement_tags)
    for tag in sorted(research_tags):
        loaded = load_sleeve_module(tag)
        if loaded.get("status") == "LOADED_FROM_RECOVERY" and loaded.get("ON_SURFACE"):
            full_tag = loaded.get("TAG") or tag
            surface = tuple(loaded["ON_SURFACE"])
            _add(full_tag, surface)
            # Also register blotter alias if different
            if tag != full_tag:
                _add(tag, surface)
            notes.setdefault("on_surface_sources", {})[full_tag] = {
                "path": loaded.get("path"),
                "ON_SURFACE": list(surface),
                "status": loaded.get("status"),
                "loader": "sleeve_on_surface_loader",
                "alias_requested": tag,
            }
            continue
        # Fallback: direct parked/recovered file for tag string
        candidates = [parked / f"{tag}.py", recovered / f"{tag}.py"]
        path = next((pp for pp in candidates if pp.exists()), None)
        if path is None:
            notes["missing_on_surface_modules"].append(
                {
                    "tag": tag,
                    "path": str(parked / f"{tag}.py"),
                    "reason": "generator_module_missing_on_dig",
                }
            )
            continue
        mod_text = path.read_text(encoding="utf-8", errors="replace")
        surface = _parse_on_surface_tuple(mod_text, "ON_SURFACE")
        if surface is None:
            notes["missing_on_surface_modules"].append(
                {"tag": tag, "path": str(path), "reason": "ON_SURFACE_not_found"}
            )
            continue
        _add(tag, surface)
        notes.setdefault("on_surface_sources", {})[tag] = {
            "path": str(path),
            "ON_SURFACE": list(surface),
        }

    for tag in RESEARCH_ARMED_TAGS:
        if tag not in seen and _normalize_sleeve(tag) not in seen:
            # defer _normalize_sleeve — may not be defined yet at function def time;
            # check aliases manually
            aliases = {
                "dsp_three_fresh": "dsp_three_fresh_lower_lows",
                "dsp_spring_close": "dsp_spring_close_on_20low_through_the_box",
            }
            resolved = aliases.get(tag, tag)
            if resolved not in seen and tag not in seen:
                notes.setdefault("research_overlay_missing_on_surface", []).append(
                    {
                        "tag": tag,
                        "status": "MISSING_MODULE",
                        "note": f"{tag}.py absent on Dig — refuse to invent on_surface",
                    }
                )
    return specs, notes


def collect_warroom_inventory_sleeves(armed: Iterable[str]) -> Tuple[tuple, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    sleeves = list(armed)
    try:
        if str(_WARROOM_SRC) not in sys.path:
            sys.path.insert(0, str(_WARROOM_SRC))
        from src.judgment.inventory import collect_live_inventory  # type: ignore
        from src.judgment.challenge import (  # type: ignore
            CHALLENGE_KEEP_FAMILIES,
            CHALLENGE_HARD_OFF_FAMILIES,
        )

        inv = collect_live_inventory(
            sleeves=list(sleeves) + list(CHALLENGE_KEEP_FAMILIES),
            include_w7_armed=False,
            include_launcher_workers=False,
            include_challenge_keep=False,
        )
        meta["source"] = "collect_live_inventory"
        meta["notes"] = list(inv.notes)
        meta["fingerprint"] = inv.fingerprint
        meta["blocked_sleeves"] = list(inv.blocked_sleeves)
        meta["challenge_keep_families"] = list(CHALLENGE_KEEP_FAMILIES)
        meta["hard_off"] = list(CHALLENGE_HARD_OFF_FAMILIES)
        return inv.sleeves, meta
    except Exception as exc:
        hard_off = {"bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30"}
        keep = ("spring", "vss")
        live = tuple(sorted({s for s in list(sleeves) + list(keep) if s not in hard_off}))
        meta["source"] = "fallback_no_warroom_import"
        meta["error"] = f"{type(exc).__name__}:{exc}"
        meta["hard_off"] = list(hard_off)
        return live, meta


def compose_alive_sleeves_for_symbol(
    symbol: str,
    *,
    account: Optional[str] = None,
    use_research_overlay: bool = True,
) -> Dict[str, Any]:
    """COMPOSE alive — Dig recipe with optional research_armed_tags overlay.

    Dig-honest: build_slots ∩ research_armed ∩ inventory (hard-off blocked).
    Does NOT invent ON_SURFACE for missing generator modules.
    Does NOT mutate live_armed_set.
    """
    build_slots = _import_build_slots()
    overlay = research_armed_overlay(account=account)
    live_armed = frozenset(overlay["live_armed_tags"])

    if use_research_overlay:
        armed = frozenset(overlay["research_armed_tags"])
        armed_source = "research_armed_tags"
    else:
        armed = live_armed
        armed_source = "live_armed"

    specs, spec_notes = load_on_surface_specs_from_disk()
    inv_sleeves, inv_meta = collect_warroom_inventory_sleeves(armed)

    slots = build_slots(specs, lambda c: str(c), armed_tags=list(armed))
    by_sym: Dict[str, List[str]] = defaultdict(list)
    for sl in slots:
        if not sl.armed:
            continue
        keys = {sl.canonical}
        if sl.broker:
            keys.add(sl.broker)
        for k in keys:
            by_sym[k].append(sl.sleeve)

    inv_set = set(inv_sleeves)
    raw = sorted(set(by_sym.get(symbol, [])))
    hard_off = set(inv_meta.get("hard_off") or [])
    alive_final = sorted({t for t in raw if not any(h in t for h in hard_off)})
    alive_strict = sorted(set(raw) & inv_set) if inv_set else list(raw)

    return {
        "field": "inventory.alive_sleeves_for_symbol",
        "symbol": symbol,
        "alive_sleeves_for_symbol": alive_final,
        "armed_source": armed_source,
        "research_armed_tags": overlay["research_armed_tags"],
        "live_armed_tags": overlay["live_armed_tags"],
        "live_armed_set_mutated": False,
        "candidate_research_armed": bool(
            set(AFFINITY_ALIASES) & set(overlay["research_armed_tags"])
            or AFFINITY_SLEEVE in set(overlay["research_armed_tags"])
        ),
        "compose": {
            "recipe": (
                "build_slots(active_specs/on_surface) ∩ research_armed_tags "
                "∩ collect_live_inventory (hard-off blocked)"
                if use_research_overlay
                else "build_slots ∩ live_armed ∩ collect_live_inventory"
            ),
            "named_function_exists": False,
            "dig_pointer": str(_DIG_JSON),
            "armed_source": armed_source,
            "armed_tags": sorted(armed),
            "live_armed_meta": overlay["live_armed_meta"],
            "inventory": inv_meta,
            "inventory_sleeves": list(inv_sleeves),
            "specs": spec_notes,
            "n_slots": len(slots),
            "n_armed_slots_for_symbol": len(raw),
            "alive_strict_inventory_intersect": alive_strict,
        },
        "apply": False,
    }


# ---------------------------------------------------------------------------
# S14 regime_tag — null OK, never invent
# ---------------------------------------------------------------------------

def hydrate_regime_tag(row: Mapping[str, Any]) -> Dict[str, Any]:
    esk = row.get("entry_state_keys") if isinstance(row.get("entry_state_keys"), dict) else {}
    candidates = [
        row.get("regime_tag"),
        esk.get("regime_tag") if isinstance(esk, dict) else None,
        (row.get("s14") or {}).get("regime_tag") if isinstance(row.get("s14"), dict) else None,
        row.get("h4_regime_descriptive_only"),  # Edge pack descriptive — only if present
    ]
    tag = None
    for c in candidates:
        if c is not None and c != "" and c != "regime_unknown":
            tag = c
            break
        if c == "regime_unknown":
            tag = None
    return {
        "field": "regime_tag",
        "regime_tag": tag,
        "hydrate": "when_present",
        "invented": False,
        "s14_status": "HYDRATED" if tag is not None else "NULL_OK_AWAITING_S14",
        "apply": False,
    }


def occupancy_corr_honest_null() -> Dict[str, Any]:
    return {
        "occupancy": None,
        "occupancy_status": "MISSING",
        "corr_cluster": None,
        "corr_hold": None,
        "corr_status": "MISSING",
        "note": "No existing hydrate writers — leave honest null; do not invent",
    }


# ---------------------------------------------------------------------------
# Fanout — KEEP|STAND|REVIEW · long-path only · NEVER fade shorts
# ---------------------------------------------------------------------------

def _fanout_from_verb(verb: str) -> str:
    """Map sketch verb → REAL menu id (mapping honesty)."""
    return CHOICE_VERB_TO_MENU.get(verb, "C_SIZE_TRIM")


def _normalize_sleeve(sleeve: str) -> str:
    s = str(sleeve or "")
    if s in ("dsp_three_fresh", "dsp_three_fresh_lower_lows"):
        return AFFINITY_SLEEVE
    if s in ("dsp_spring_close", "dsp_spring_close_on_20low_through_the_box"):
        return "dsp_spring_close_on_20low_through_the_box"
    return s


def _is_affinity_three_fresh(sleeve: str, symbol: str) -> bool:
    return (
        str(symbol) == AFFINITY_SYMBOL
        and _normalize_sleeve(sleeve) == AFFINITY_SLEEVE
    )


def _is_fade_or_short(row: Mapping[str, Any], sleeve: str) -> bool:
    """SHORT/fade NEVER KEEP. Affinity TAG dsp_three_fresh_lower_lows is LONG — not fade."""
    side = str(row.get("side") or row.get("dir") or "LONG").upper()
    if side in ("SHORT", "SELL", "S"):
        return True
    # Affinity LONG module: ignore TAG substring traps (lower_lows in name)
    if _is_affinity_three_fresh(sleeve, str(row.get("symbol") or AFFINITY_SYMBOL)):
        if side in ("LONG", "BUY", "B", ""):
            return False
    blob = " ".join(
        str(x)
        for x in (
            sleeve,
            row.get("sleeve"),
            row.get("family"),
            row.get("role"),
            row.get("affinity"),
        )
        if x
    ).lower()
    if "fade" in blob and "short" in blob:
        return True
    return any(m.lower() in blob for m in _FADE_SHORT_MARKERS)


def emit_choice_score_noul(
    row: Mapping[str, Any],
    *,
    alive_sleeves: Sequence[str],
    regime: Optional[str],
    research_armed: bool,
    exit_model_tag: str,
) -> Dict[str, Any]:
    """Shadow fanout. Long KEEP_WIN_SUBTYPE only. apply=false."""
    symbol = row.get("symbol") or AFFINITY_SYMBOL
    sleeve = str(row.get("sleeve") or AFFINITY_SLEEVE)
    miss = row.get("miss") or row.get("miss_type")
    session = row.get("session_ict") or row.get("session")
    dig_alive = (
        sleeve in set(alive_sleeves)
        or _normalize_sleeve(sleeve) in set(alive_sleeves)
        or any(_normalize_sleeve(a) == _normalize_sleeve(sleeve) for a in alive_sleeves)
    )
    footnotes: List[str] = []

    if _is_fade_or_short(row, sleeve):
        verb = "STAND"
        reason = "never_fade_shorts_KEEP_WIN_SUBTYPE_long_only"
        footnotes.append("FORBIDDEN fade/short path — STAND; Dig NEGCTRL toxic on XAU")
    elif not _is_affinity_three_fresh(sleeve, str(symbol)):
        verb = "STAND"
        reason = "outside_affinity_XAUUSD_x_dsp_three_fresh_lower_lows"
        footnotes.append(
            "affinity gate — research emitters scoped to XAUUSD×dsp_three_fresh_lower_lows"
        )
    elif not research_armed and not dig_alive:
        verb = "STAND"
        reason = "not_research_armed_and_dig_alive_false"
        footnotes.append("neither research overlay nor Dig compose alive — STAND")
    elif miss == "event_gap":
        verb = "REVIEW"
        reason = "event_gap_trim_not_stand_down"
        footnotes.append("Dig pocket: event_gap → REVIEW/trim never A_STAND_DOWN")
    elif research_armed and not dig_alive:
        # RESEARCH_OPEN_DUAL_LENS: Dig module missing but Chair research overlay arms tag
        verb = "KEEP"
        reason = "research_armed_KEEP_WIN_SUBTYPE_monitor_dig_alive_stub"
        footnotes.append(
            "Dig compose alive empty (module MISSING / not invented); "
            "research_armed_tags overlay → KEEP monitor; promote=false"
        )
        footnotes.append("WR floor = monitor not kill; Dig hold+ train− honesty")
    else:
        verb = "KEEP"
        reason = "keep_win_subtype_long_research_open_dual_lens"
        footnotes.append("KEEP_WIN_SUBTYPE long reclaim — apply=false place=false")

    if verb == "KEEP" and regime is None:
        footnotes.append("regime_tag null — full-state Score haircut; still KEEP with REVIEW footnote")

    if exit_model_tag == "Dig_3R":
        footnotes.append("exit_model_tag=Dig_3R monitor (hold+ train−); do NOT merge Edge/Module R")
    elif exit_model_tag == "Edge_ATR":
        footnotes.append(
            "exit_model_tag=Edge_ATR research exit candidate; do NOT claim Dig 13/13; "
            "cite Edge packs only"
        )
    elif exit_model_tag == "Module_ATR":
        footnotes.append(
            "exit_model_tag=Module_ATR third lens file stop0.75/tgt6.0; "
            "never merge Dig_3R or Edge_ATR R"
        )

    score = 0.50
    if research_armed:
        score += 0.12
    if dig_alive:
        score += 0.10
    if regime is not None:
        score += 0.08
    if verb == "STAND":
        score = min(score, 0.35)
    if verb == "REVIEW":
        score = min(max(score, 0.40), 0.60)
    if verb == "KEEP" and not dig_alive:
        score = min(score, 0.58)  # haircut for Dig stub
    if exit_model_tag == "Edge_ATR" and verb == "KEEP":
        score = min(score, 0.60)  # research-exit candidate, not Dig claim
    score = round(min(1.0, max(0.0, score)), 4)

    noul = [
        f"symbol:{symbol}",
        f"sleeve:{sleeve}",
        f"choice_verb:{verb}",
        f"alive_dig:{str(dig_alive).lower()}",
        f"research_armed:{str(research_armed).lower()}",
        f"regime:{regime if regime is not None else 'null'}",
        f"exit_model_tag:{exit_model_tag}",
        "mode:shadow_apply_false",
        f"three_fresh_status:{THREE_FRESH_STATUS}",
        "keep_win_subtype:LONG_only",
        "never_fade_shorts:true",
        "cf:PAUSED",
        "promote:false",
        "place:false",
        "affinity:XAUUSD_x_dsp_three_fresh",
        "armed_source:research_armed_tags",
    ]
    if session:
        noul.append(f"session:{session}")
    if miss:
        noul.append(f"miss:{miss}")
    for fn in footnotes:
        noul.append(f"footnote:{fn[:100]}")

    return {
        "shadow.jev.Choice": _fanout_from_verb(verb),
        "shadow.jev.Choice_verb": verb,
        "shadow.jev.Choice_menu_map": dict(CHOICE_VERB_TO_MENU),
        "shadow.jev.mapping_honesty": MAPPING_HONESTY,
        "shadow.jev.real_menu": list(REAL_MENU),
        "shadow.jev.choice_reason": reason,
        "shadow.jev.choice_footnotes": footnotes,
        "shadow.jev.Score": score,
        "shadow.jev.Noul_tags": noul,
        "shadow.jev.stand_down": verb == "STAND",
        "shadow.jev.apply": False,
        "v2_advisory_on_Challenge": False,
        "v3": "NO_LOCKED",
        "cf_variants": "PAUSED",
        "place": False,
        "promote": False,
        "LonNY_harden": False,
        "cost_kill": False,
        "news_invented": False,
        "fade_shorts": False,
    }


# ---------------------------------------------------------------------------
# Dual-lens exit_model_tag
# ---------------------------------------------------------------------------

def exit_model_pack(exit_model_tag: str) -> Dict[str, Any]:
    if exit_model_tag not in EXIT_MODEL_TAGS:
        raise ValueError(f"exit_model_tag must be one of {EXIT_MODEL_TAGS}, got {exit_model_tag}")
    if exit_model_tag == "Dig_3R":
        return {
            "exit_model_tag": "Dig_3R",
            "exit_model_role": "monitor",
            "r_universe": "Dig_PRIMARY_geometry_3R",
            "claim_dig_13_of_13": False,
            "claim_edge_13_of_13_as_dig": False,
            "wr_floor": "monitor_not_kill",
            "honesty": "hold+ train− under 3R geometry; never merge Edge ATR-R or Module_ATR",
            "blotter": str(_DIG_BLOTTER),
            "deepen": str(_DEEPEN),
        }
    if exit_model_tag == "Module_ATR":
        return {
            "exit_model_tag": "Module_ATR",
            "exit_model_role": "third_lens_file_exit_shape",
            "r_universe": "Module_file_ATR_stop0.75_tgt6.0",
            "claim_dig_13_of_13": False,
            "claim_edge_13_of_13_as_dig": False,
            "wr_floor": "monitor_not_kill",
            "honesty": (
                "geometry_proxy_ohlc_touch Module_ATR — NEVER merge with Dig_3R or Edge_ATR R; "
                "fill ≠ broker / ≠ module-exact runtime"
            ),
            "blotter": str(_MODULE_ATR_BLOTTER),
            "yearfold": str(_MODULE_ATR_YEARFOLD),
            "exit_shape_from_file": "stop0.75_tgt6.0_ATR",
            "module_tag": AFFINITY_SLEEVE,
        }
    return {
        "exit_model_tag": "Edge_ATR",
        "exit_model_role": "research_exit_candidate",
        "r_universe": "Instrument_Edge_ATR14_ONLY",
        "claim_dig_13_of_13": False,
        "claim_edge_13_of_13_as_dig": False,
        "note": "Edge 13/13 ATR-positive is SEPARATE — do not stamp as Dig claim",
        "wr_floor": "monitor_not_kill",
        "honesty": "cite Edge packs only in Edge_ATR lens; never add/compare sumR to Dig or Module",
        "edge_loser_pack": str(_EDGE_LOSER),
        "deepen": str(_DEEPEN),
    }


# ---------------------------------------------------------------------------
# Full stamp (one exit_model_tag per call)
# ---------------------------------------------------------------------------

def emit_three_fresh_full_state_stamp(
    row: Mapping[str, Any],
    *,
    exit_model_tag: str,
    account: Optional[str] = None,
) -> Dict[str, Any]:
    symbol = str(row.get("symbol") or AFFINITY_SYMBOL)
    sleeve = str(row.get("sleeve") or AFFINITY_SLEEVE)
    alive_pack = compose_alive_sleeves_for_symbol(
        symbol, account=account, use_research_overlay=True
    )
    regime_pack = hydrate_regime_tag(row)
    occ = occupancy_corr_honest_null()
    em = exit_model_pack(exit_model_tag)
    fanout = emit_choice_score_noul(
        row,
        alive_sleeves=alive_pack["alive_sleeves_for_symbol"],
        regime=regime_pack["regime_tag"],
        research_armed=bool(alive_pack.get("candidate_research_armed")),
        exit_model_tag=exit_model_tag,
    )

    # R field: keep lens-local; never merge Dig / Edge / Module R universes
    if exit_model_tag == "Dig_3R":
        is_dig_row = (
            row.get("lens") != "Module_ATR"
            and bool(row.get("fill_model") or row.get("bars_source") or row.get("R") is not None)
            and row.get("R_raw") is None
            and row.get("exit_shape") != "stop0.75_tgt6.0_ATR"
        )
        # Dig blotter rows carry Dig geometry R; Module_ATR blotter must not feed Dig lens
        if row.get("lens") == "Module_ATR":
            R = None
            r_note = "Dig_lens_null_on_Module_ATR_row_never_merge"
        else:
            R = (row.get("R") or row.get("realised_r_unit150") or row.get("tape_R"))
            r_note = "Dig_PRIMARY_R_only"
    elif exit_model_tag == "Module_ATR":
        if row.get("lens") == "Module_ATR" or row.get("exit_shape") == "stop0.75_tgt6.0_ATR":
            R = row.get("R_ATR") if row.get("R_ATR") is not None else row.get("R")
            r_note = "Module_ATR_R_only_do_not_merge_with_Dig_or_Edge"
        else:
            R = None
            r_note = "Module_ATR_lens_null_unless_module_row"
    else:  # Edge_ATR
        if row.get("lens") == "Module_ATR":
            R = None
            r_note = "Edge_lens_null_on_Module_ATR_row_never_merge"
        elif row.get("R_raw") is not None:
            R = row.get("R_raw")
            r_note = "Edge_ATR_R_only_do_not_merge_with_Dig"
        elif row.get("R_ATR") is not None and row.get("lens") != "Module_ATR":
            R = row.get("R_ATR")
            r_note = "Edge_ATR_R_only_do_not_merge_with_Dig"
        else:
            R = None
            r_note = "Edge_ATR_R_only_do_not_merge_with_Dig"

    stamp = {
        "schema": SCHEMA,
        "ts_ict": _ict_now(),
        "ts_utc": _utc_now(),
        "mode": "SHADOW_LOG_ONLY",
        "apply": False,
        "place": False,
        "promote": False,
        "cf_variants": "PAUSED",
        "three_fresh_status": THREE_FRESH_STATUS,
        "affinity": f"{AFFINITY_SYMBOL}×{AFFINITY_SLEEVE}",
        "module_tag": AFFINITY_SLEEVE,
        "research_blotter_alias": "dsp_three_fresh",
        "mapping_honesty": MAPPING_HONESTY,
        "real_menu": list(REAL_MENU),
        "keep_win_subtype": "LONG_only",
        "ticket": row.get("ticket") or row.get("i") or row.get("entry_time"),
        "symbol": symbol,
        "sleeve": sleeve,
        "side": row.get("side") or "LONG",
        "asset_class": row.get("asset_class") or "XAU",
        "session_ict": row.get("session_ict") or row.get("session"),
        "miss": row.get("miss") or row.get("miss_type"),
        "exit": row.get("exit") or row.get("exit_class"),
        "R": R,
        "R_note": r_note,
        "split": row.get("split"),
        "entry_time": row.get("entry_time") or row.get("signal_time"),
        # --- dual-lens stamp ---
        "exit_model_tag": em["exit_model_tag"],
        "exit_model": em,
        # --- Dig compose + research overlay ---
        "inventory.alive_sleeves_for_symbol": alive_pack["alive_sleeves_for_symbol"],
        "inventory.candidate_sleeve_alive": (
            sleeve in set(alive_pack["alive_sleeves_for_symbol"])
            or _normalize_sleeve(sleeve) in set(alive_pack["alive_sleeves_for_symbol"])
            or any(
                _normalize_sleeve(a) == _normalize_sleeve(sleeve)
                for a in alive_pack["alive_sleeves_for_symbol"]
            )
        ),
        "inventory.candidate_research_armed": alive_pack.get("candidate_research_armed"),
        "inventory.compose": alive_pack["compose"],
        "armed_source": alive_pack["armed_source"],
        "research_armed_tags": alive_pack["research_armed_tags"],
        "live_armed_tags": alive_pack["live_armed_tags"],
        "live_armed_set_mutated": False,
        # --- S14 ---
        "regime_tag": regime_pack["regime_tag"],
        "regime_tag_meta": {k: regime_pack[k] for k in ("hydrate", "invented", "s14_status")},
        # --- occupancy/corr ---
        "occupancy": occ["occupancy"],
        "occupancy_status": occ["occupancy_status"],
        "corr_cluster": occ["corr_cluster"],
        "corr_hold": occ["corr_hold"],
        "corr_status": occ["corr_status"],
        "occupancy_corr_note": occ["note"],
        **fanout,
        "forbidden_respected": {
            "place": False,
            "promote": False,
            "news_invent": False,
            "cost_kill": False,
            "live_armed_set_mutate": False,
            "merge_dig_edge_R": False,
            "fade_shorts": False,
            "claim_dig_13_of_13": False,
            "occupancy_corr_invent": False,
            "LonNY_promote": False,
            "v3": False,
        },
        "paths": {
            "emitter": str(_BOX / "three_fresh_full_state_emitters.py"),
            "dig_pointer": str(_DIG_JSON),
            "deepen": str(_DEEPEN),
            "expanding_pattern": str(_BOX / "expanding_full_state_emitters.py"),
            "build_slots": str(
                _SWARM_SRC / "components/ultimate_book/symbol_resolution_watch.py"
            ),
            "armed_set_readonly": str(_ARMED_JSON),
            "warroom_inventory": str(_WARROOM_SRC / "src/judgment/inventory.py"),
            "dig_blotter": str(_DIG_BLOTTER),
            "edge_loser_pack": str(_EDGE_LOSER),
        },
        "note": (
            "three_fresh writers = capture-intelligence not promote; "
            "RESEARCH_OPEN_DUAL_LENS; Dig_3R monitor vs Edge_ATR research-exit; "
            "research_armed_tags overlay — live_armed_set untouched"
        ),
    }
    return stamp


def emit_dual_lens_stamps(
    row: Mapping[str, Any],
    *,
    account: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Emit both Dig_3R and Edge_ATR stamp variants for dual-lens honesty."""
    return [
        emit_three_fresh_full_state_stamp(row, exit_model_tag="Dig_3R", account=account),
        emit_three_fresh_full_state_stamp(row, exit_model_tag="Edge_ATR", account=account),
    ]


def write_stamp(stamp: Mapping[str, Any], path: Optional[Path] = None) -> Path:
    _STAMP_DIR.mkdir(parents=True, exist_ok=True)
    ticket = stamp.get("ticket") or "unknown"
    tag = stamp.get("exit_model_tag") or "unknown"
    safe = str(ticket).replace(" ", "_").replace(":", "")
    path = path or (_STAMP_DIR / f"three_fresh_full_state_stamp_{tag}_{safe}.json")
    path.write_text(json.dumps(stamp, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def append_learning_row(stamp: Mapping[str, Any], stamp_path: Path) -> None:
    row = {
        "schema": "gtos.close_loop.learning_row.v1",
        "ts_ict": stamp.get("ts_ict") or _ict_now(),
        "event": "THREE_FRESH_FULL_STATE_EMITTERS",
        "place": False,
        "apply": False,
        "promote": False,
        "cf_variants": "PAUSED",
        "three_fresh_status": THREE_FRESH_STATUS,
        "affinity_law": True,
        "owner_law_cost_never_issue": True,
        "no_LonNY_promote": True,
        "no_cost_kill": True,
        "no_NEWS_invent": True,
        "no_fade_shorts": True,
        "no_merge_dig_edge_R": True,
        "live_armed_set_mutated": False,
        "armed_source": stamp.get("armed_source"),
        "research_armed_tags": stamp.get("research_armed_tags"),
        "live_armed_tags": stamp.get("live_armed_tags"),
        "exit_model_tag": stamp.get("exit_model_tag"),
        "keep_win_subtype": "LONG_only",
        "sleeve": stamp.get("sleeve"),
        "symbol": stamp.get("symbol"),
        "ticket": stamp.get("ticket"),
        "alive_sleeves_for_symbol": stamp.get("inventory.alive_sleeves_for_symbol"),
        "candidate_sleeve_alive": stamp.get("inventory.candidate_sleeve_alive"),
        "candidate_research_armed": stamp.get("inventory.candidate_research_armed"),
        "regime_tag": stamp.get("regime_tag"),
        "Choice_verb": stamp.get("shadow.jev.Choice_verb"),
        "Choice_fanout": stamp.get("shadow.jev.Choice"),
        "Score": stamp.get("shadow.jev.Score"),
        "occupancy_status": "MISSING",
        "corr_status": "MISSING",
        "forbidden_respected": stamp.get("forbidden_respected"),
        "paths": {
            "emitter": stamp.get("paths", {}).get("emitter"),
            "stamp": str(stamp_path),
            "md": str(_BOX / "THREE_FRESH_FULL_STATE_EMITTERS_20260920.md"),
            "json": str(_BOX / "THREE_FRESH_FULL_STATE_EMITTERS_20260920.json"),
            "deepen": str(_DEEPEN),
            "dig_pointer": str(_DIG_JSON),
        },
        "note": (
            "Shadow three_fresh emitters; RESEARCH_OPEN_DUAL_LENS; "
            "exit_model_tag Dig_3R|Edge_ATR; research_armed_tags overlay; apply=false"
        ),
    }
    with _LEARNING.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_dig_sample() -> Dict[str, Any]:
    """Hold +3R Dig PRIMARY sample for Dig_3R lens."""
    for line in _DIG_BLOTTER.open():
        r = json.loads(line)
        if r.get("exit") == "orig_tp" and r.get("split") == "hold" and r.get("side") == "LONG":
            r = dict(r)
            r["ticket"] = f"DIG_{r['entry_time']}"
            r["miss"] = "ok_win"
            return r
    raise RuntimeError("no Dig hold orig_tp sample")


def _load_edge_sample() -> Dict[str, Any]:
    """Edge ATR loser sample (flush_continues) for Edge_ATR lens."""
    body = json.loads(_EDGE_LOSER.read_text())
    s = dict(body["samples"][0])
    s["symbol"] = AFFINITY_SYMBOL
    s["sleeve"] = AFFINITY_SLEEVE
    s["side"] = "LONG"
    s["ticket"] = f"EDGE_{s.get('signal_time')}"
    s["session"] = s.get("session")
    s["regime_tag"] = None  # descriptive h4 is separate; S14 never invent — hydrate uses h4 only if we allow
    # Keep h4_regime_descriptive_only for hydrate (present on Edge pack — OK, not invented)
    s["miss"] = "flush_continues"
    return s



def emit_compact_module_atr_voter_stamp(
    row: Mapping[str, Any],
    *,
    alive_sleeves: Sequence[str],
    research_armed: bool,
    armed_source: str,
    research_armed_tags: Sequence[str],
    live_armed_tags: Sequence[str],
) -> Dict[str, Any]:
    """Compact Module_ATR Jev voter stamp (jsonl row). apply=false."""
    regime_pack = hydrate_regime_tag(row)
    fanout = emit_choice_score_noul(
        row,
        alive_sleeves=alive_sleeves,
        regime=regime_pack["regime_tag"],
        research_armed=research_armed,
        exit_model_tag="Module_ATR",
    )
    sleeve = str(row.get("sleeve") or AFFINITY_SLEEVE)
    return {
        "schema": "gtos.warroom_shadow.three_fresh_module_atr_jev_voter_stamp.v1",
        "mode": "SHADOW_LOG_ONLY",
        "apply": False,
        "place": False,
        "promote": False,
        "exit_model_tag": "Module_ATR",
        "module_tag": AFFINITY_SLEEVE,
        "research_blotter_alias": "dsp_three_fresh",
        "lens": "Module_ATR",
        "ticket": row.get("entry_time"),
        "symbol": row.get("symbol") or AFFINITY_SYMBOL,
        "sleeve": sleeve,
        "side": row.get("side") or "LONG",
        "year": row.get("year"),
        "split": row.get("split"),
        "exit": row.get("exit"),
        "R_Module_ATR": row.get("R_ATR") if row.get("R_ATR") is not None else row.get("R"),
        "R_note": "Module_ATR_only_never_merge",
        "exit_shape": row.get("exit_shape") or "stop0.75_tgt6.0_ATR",
        "fill_model": row.get("fill_model"),
        "inventory.alive_sleeves_for_symbol": list(alive_sleeves),
        "inventory.candidate_sleeve_alive": (
            sleeve in set(alive_sleeves)
            or _normalize_sleeve(sleeve) in set(alive_sleeves)
            or any(_normalize_sleeve(a) == _normalize_sleeve(sleeve) for a in alive_sleeves)
        ),
        "inventory.candidate_research_armed": research_armed,
        "armed_source": armed_source,
        "research_armed_tags": list(research_armed_tags),
        "live_armed_tags": list(live_armed_tags),
        "live_armed_set_mutated": False,
        "regime_tag": regime_pack["regime_tag"],
        "regime_tag_meta": {
            "hydrate": regime_pack["hydrate"],
            "invented": False,
            "s14_status": regime_pack["s14_status"],
            "null_ok": True,
        },
        "shadow.jev.Choice_verb": fanout["shadow.jev.Choice_verb"],
        "shadow.jev.Choice": fanout["shadow.jev.Choice"],
        "shadow.jev.Score": fanout["shadow.jev.Score"],
        "shadow.jev.choice_reason": fanout["shadow.jev.choice_reason"],
        "shadow.jev.mapping_honesty": MAPPING_HONESTY,
        "shadow.jev.real_menu": list(REAL_MENU),
        "shadow.jev.apply": False,
        "occupancy": None,
        "occupancy_status": "MISSING",
        "corr_status": "MISSING",
        "doctrine": "STRIKE_WHEN_RIGHT",
        "static_fail_policy": "research_suspicion_only_under_STRIKE_WHEN_RIGHT",
        "score0_parked_untouched": True,
        "forbidden_respected": {
            "place": False,
            "promote": False,
            "news_invent": False,
            "cost_kill": False,
            "live_armed_set_mutate": False,
            "merge_R_lenses": False,
            "LonNY_promote": False,
            "v3": False,
        },
    }


def stamp_module_atr_jev_voters(*, limit: Optional[int] = None) -> Dict[str, Any]:
    """Stamp all Module_ATR multiyear blotter candidates (compact jsonl). apply=false."""
    from collections import Counter

    if not _MODULE_ATR_BLOTTER.exists():
        raise FileNotFoundError(str(_MODULE_ATR_BLOTTER))

    alive_pack = compose_alive_sleeves_for_symbol(AFFINITY_SYMBOL, use_research_overlay=True)
    alive = alive_pack["alive_sleeves_for_symbol"]
    research_armed = bool(alive_pack.get("candidate_research_armed"))
    armed_source = alive_pack["armed_source"]
    research_tags = alive_pack["research_armed_tags"]
    live_tags = alive_pack["live_armed_tags"]

    _VOTER_STAMP_JSONL.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    choice_hist: Counter = Counter()
    verb_hist: Counter = Counter()
    null_regime = 0
    by_year: Counter = Counter()
    by_split: Counter = Counter()

    with _MODULE_ATR_BLOTTER.open() as fin, _VOTER_STAMP_JSONL.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            stamp = emit_compact_module_atr_voter_stamp(
                row,
                alive_sleeves=alive,
                research_armed=research_armed,
                armed_source=armed_source,
                research_armed_tags=research_tags,
                live_armed_tags=live_tags,
            )
            fout.write(json.dumps(stamp, ensure_ascii=False) + "\n")
            n += 1
            choice_hist[stamp["shadow.jev.Choice"]] += 1
            verb_hist[stamp["shadow.jev.Choice_verb"]] += 1
            if stamp["regime_tag"] is None:
                null_regime += 1
            by_year[stamp.get("year")] += 1
            by_split[stamp.get("split")] += 1
            if limit is not None and n >= limit:
                break

    # Also emit one full-state sample Module_ATR stamp (first hold orig_tp if any)
    sample_path = None
    with _MODULE_ATR_BLOTTER.open() as fin:
        for line in fin:
            r = json.loads(line)
            if r.get("split") == "hold" and r.get("exit") == "orig_tp":
                full = emit_three_fresh_full_state_stamp(r, exit_model_tag="Module_ATR")
                sample_path = write_stamp(full)
                break

    report = {
        "schema": "gtos.close_loop.three_fresh_full_state_voter_stamp.v1",
        "ts_ict": _ict_now(),
        "place": False,
        "apply": False,
        "promote": False,
        "affinity": f"{AFFINITY_SYMBOL}×{AFFINITY_SLEEVE}",
        "module_tag": AFFINITY_SLEEVE,
        "exit_model_tag": "Module_ATR",
        "n_candidates_stamped": n,
        "Choice_histogram": dict(choice_hist),
        "Choice_verb_histogram": dict(verb_hist),
        "null_regime_count": null_regime,
        "null_regime_ok": True,
        "regime_invented": False,
        "alive_source": "research_armed_tags",
        "armed_source": armed_source,
        "alive_sleeves_for_symbol_XAUUSD": alive,
        "candidate_research_armed": research_armed,
        "candidate_sleeve_alive": (
            AFFINITY_SLEEVE in set(alive)
            or any(_normalize_sleeve(a) == AFFINITY_SLEEVE for a in alive)
        ),
        "research_armed_tags": research_tags,
        "live_armed_tags": live_tags,
        "live_armed_set_mutated": False,
        "mapping_honesty": MAPPING_HONESTY,
        "real_menu": list(REAL_MENU),
        "by_year": {str(k): v for k, v in sorted(by_year.items(), key=lambda x: (x[0] is None, x[0]))},
        "by_split": dict(by_split),
        "paths": {
            "blotter": str(_MODULE_ATR_BLOTTER),
            "yearfold": str(_MODULE_ATR_YEARFOLD),
            "voter_stamps_jsonl": str(_VOTER_STAMP_JSONL),
            "emitter": str(_BOX / "three_fresh_full_state_emitters.py"),
            "overlay": str(_OVERLAY_JSON),
            "sample_full_stamp": str(sample_path) if sample_path else None,
        },
        "doctrine": "STRIKE_WHEN_RIGHT",
        "static_fail_policy": "research_suspicion_only_under_STRIKE_WHEN_RIGHT",
        "score0_parked_untouched": True,
        "forbidden_respected": {
            "place": False,
            "promote": False,
            "news_invent": False,
            "cost_kill": False,
            "live_armed_set_mutate": False,
            "merge_R_lenses": False,
            "LonNY_promote": False,
            "v3": False,
        },
    }
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    if "--module-atr-voters" in argv:
        limit = None
        if "--limit" in argv:
            i = argv.index("--limit")
            limit = int(argv[i + 1])
        report = stamp_module_atr_jev_voters(limit=limit)
        out_json = _BOX / "THREE_FRESH_FULL_STATE_VOTER_STAMP_20260920.json"
        out_md = _BOX / "THREE_FRESH_FULL_STATE_VOTER_STAMP_20260920.md"
        out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md = [
            f"# THREE_FRESH full-state Jev voter stamp — Module_ATR — {report['ts_ict']}",
            "",
            f"**Affinity:** `{report['affinity']}` · **lens:** Module_ATR · **apply=false** · **place=false**",
            f"**Doctrine:** STRIKE_WHEN_RIGHT · static fails = research suspicion only",
            "",
            "## Counts",
            "",
            f"| metric | value |",
            f"|---|---:|",
            f"| n candidates stamped | **{report['n_candidates_stamped']}** |",
            f"| null regime_tag | {report['null_regime_count']} (null-ok, never invent) |",
            f"| alive_source | `{report['alive_source']}` |",
            f"| candidate_sleeve_alive | {report['candidate_sleeve_alive']} |",
            f"| live_armed_set_mutated | {report['live_armed_set_mutated']} |",
            "",
            "## Choice histogram (REAL menu)",
            "",
            "| Choice | n |",
            "|---|---:|",
        ]
        for k, v in sorted(report["Choice_histogram"].items()):
            md.append(f"| {k} | {v} |")
        md += [
            "",
            "## Choice_verb histogram",
            "",
            "| verb | n |",
            "|---|---:|",
        ]
        for k, v in sorted(report["Choice_verb_histogram"].items()):
            md.append(f"| {k} | {v} |")
        md += [
            "",
            f"**mapping_honesty:** {report['mapping_honesty']}",
            "",
            f"**alive_sleeves_for_symbol(XAUUSD):** `{report['alive_sleeves_for_symbol_XAUUSD']}`",
            "",
            "## Paths",
            f"- voter jsonl: `{report['paths']['voter_stamps_jsonl']}`",
            f"- report json: `{out_json}`",
            f"- blotter: `{report['paths']['blotter']}`",
            f"- emitter: `{report['paths']['emitter']}`",
            "",
            "## Forbidden respected",
            "place/promote/NEWS invent/cost kill/live_armed mutate/merge R/Lon+NY/V3 = false",
            "",
            "score0 PARKED untouched.",
            "",
        ]
        out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "n": report["n_candidates_stamped"], "json": str(out_json), "md": str(out_md), "jsonl": report["paths"]["voter_stamps_jsonl"]}, indent=2))
        return 0

    dig_row = _load_dig_sample()
    edge_row = _load_edge_sample()

    # Dual-lens on Dig sample + Edge sample (4 stamps: each row × Dig_3R/Edge_ATR)
    # Primary deliverable: Dig row stamped Dig_3R + Edge row stamped Edge_ATR,
    # plus cross-stamp variants for honesty (same row both tags).
    written: List[Dict[str, Any]] = []

    # Dig blotter row → both tags
    for stamp in emit_dual_lens_stamps(dig_row):
        path = write_stamp(stamp)
        append_learning_row(stamp, path)
        written.append(
            {
                "path": str(path),
                "exit_model_tag": stamp["exit_model_tag"],
                "ticket": stamp["ticket"],
                "Choice_verb": stamp.get("shadow.jev.Choice_verb"),
                "armed_source": stamp.get("armed_source"),
                "apply": False,
            }
        )

    # Edge pack row → both tags
    for stamp in emit_dual_lens_stamps(edge_row):
        path = write_stamp(stamp)
        append_learning_row(stamp, path)
        written.append(
            {
                "path": str(path),
                "exit_model_tag": stamp["exit_model_tag"],
                "ticket": stamp["ticket"],
                "Choice_verb": stamp.get("shadow.jev.Choice_verb"),
                "armed_source": stamp.get("armed_source"),
                "apply": False,
            }
        )

    summary = {
        "three_fresh_status": THREE_FRESH_STATUS,
        "apply": False,
        "place": False,
        "promote": False,
        "armed_source": "research_armed_tags",
        "research_armed_tags": list(RESEARCH_ARMED_TAGS),
        "live_armed_set_mutated": False,
        "exit_model_tag_values": list(EXIT_MODEL_TAGS),
        "stamps": written,
        "stamp_dir": str(_STAMP_DIR),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

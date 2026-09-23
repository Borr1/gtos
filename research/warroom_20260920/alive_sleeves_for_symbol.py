#!/usr/bin/env python3
"""JEV_SLEEVE_SELECT compose writer — alive_sleeves_for_symbol(symbol).

Chair NAME 2026-09-20: context→strategy pick inventory.

Recipe:
  alive = build_slots(active/research specs) ∩ armed ∩ ON_SURFACE(symbol)
  hard-off families:
    default → excluded from alive (silent drop of hard-off from alive list)
    RELAX_TO_JEV=True → NOT silent: emitted as blocked_escape[{tag, escape:BLOCKED}]

SHADOW: place=false · apply=false · never mutate live_armed_set.
No invent NEWS / occupancy / corr.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ICT = timezone(timedelta(hours=7))
_HERE = Path(__file__).resolve().parent
_GTOS = Path("/workspace/gtos")
_SWARM_SRC = _GTOS / "_swarm_land_tip/extract/src"
_WARROOM_SRC = _GTOS / "judgment/warroom_shadow"
_CL = _GTOS / "close_loop/war_room_20260920"
_DIG_WAR = _GTOS / "research/codila_absorb/war_room"
_RECOVERED = _DIG_WAR / "recovered"
_ARMED_JSON = _GTOS / "_swarm_land_tip/extract/config/live_armed_set.json"
_OVERLAY = _CL / "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_CL) not in sys.path:
    sys.path.insert(0, str(_CL))

try:
    from sleeve_on_surface_loader import load_sleeve_module  # type: ignore
except Exception:  # noqa: BLE001
    load_sleeve_module = None  # type: ignore

# House hard-off prefixes (code surface). Dig does not invent new cages.
DEFAULT_HARD_OFF_FAMILIES = (
    "bleed",
    "orb_crypto",
    "idxrev",
    "xa_huge",
    "mx_us30",
)


def _ict_now() -> str:
    return datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00")


def relax_to_jev_enabled(flag: Optional[bool] = None) -> bool:
    if flag is not None:
        return bool(flag)
    env = os.environ.get("GTOS_RELAX_TO_JEV", "").strip().lower()
    return env in ("1", "true", "yes", "on")


def load_live_armed_tags(account: Optional[str] = None) -> Tuple[List[str], Dict[str, Any]]:
    meta: Dict[str, Any] = {"path": str(_ARMED_JSON), "mutated": False, "source": None}
    if not _ARMED_JSON.exists():
        # VPS fallback
        vps_guess = Path("C:host-local/redacted_host/repo/config/live_armed_set.json")
        if vps_guess.exists():
            meta["path"] = str(vps_guess)
            body = json.loads(vps_guess.read_text(encoding="utf-8"))
        else:
            meta["source"] = "unavailable"
            return [], meta
    else:
        body = json.loads(_ARMED_JSON.read_text(encoding="utf-8"))
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
    return sorted(out), meta


def load_research_armed_tags() -> Tuple[List[str], Dict[str, Any]]:
    """Base overlay + ADD_* fragments under close_loop war_room."""
    meta: Dict[str, Any] = {"path": str(_OVERLAY), "fragments": [], "source": None}
    tags: set = set()
    if _OVERLAY.exists():
        body = json.loads(_OVERLAY.read_text(encoding="utf-8"))
        tags |= {str(t) for t in (body.get("research_armed_tags") or [])}
        meta["source"] = "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"
    for frag in sorted(_CL.glob("RESEARCH_ARMED_TAGS_OVERLAY_ADD_*.json")):
        try:
            raw = frag.read_text(encoding="utf-8")
            # tolerate accidental trailing junk
            d = json.loads(raw.split("\n{")[0] + ("\n{" if False else "")) if False else None
        except Exception:
            d = None
        try:
            d = json.loads(frag.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # take first JSON object only
            txt = frag.read_text(encoding="utf-8")
            end = txt.find("\n}")
            if end > 0:
                d = json.loads(txt[: end + 2])
            else:
                meta["fragments"].append({"file": frag.name, "error": "JSONDecodeError"})
                continue
        add = d.get("research_armed_tags_add") or d.get("research_armed_tags") or []
        tags |= {str(t) for t in add}
        meta["fragments"].append({"file": frag.name, "added": list(add)})
    if not tags and meta["source"] is None:
        meta["source"] = "unavailable"
    return sorted(tags), meta


def hard_off_families() -> Tuple[set, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    try:
        if str(_WARROOM_SRC) not in sys.path:
            sys.path.insert(0, str(_WARROOM_SRC))
        from src.judgment.challenge import CHALLENGE_HARD_OFF_FAMILIES  # type: ignore

        fam = set(CHALLENGE_HARD_OFF_FAMILIES)
        meta["source"] = "challenge.CHALLENGE_HARD_OFF_FAMILIES"
        meta["hard_off"] = sorted(fam)
        return fam, meta
    except Exception as exc:  # noqa: BLE001
        fam = set(DEFAULT_HARD_OFF_FAMILIES)
        meta["source"] = "DEFAULT_HARD_OFF_FAMILIES"
        meta["error"] = f"{type(exc).__name__}:{exc}"
        meta["hard_off"] = sorted(fam)
        return fam, meta


class _Spec:
    def __init__(self, tag: str, on_surface: tuple):
        self.tag = tag
        self.on_surface = on_surface


def _import_build_slots():
    if str(_SWARM_SRC) not in sys.path:
        sys.path.insert(0, str(_SWARM_SRC))
    from components.ultimate_book.symbol_resolution_watch import build_slots  # type: ignore

    return build_slots


def _load_on_surface_from_recovered(tag: str) -> Optional[Tuple[str, tuple]]:
    if load_sleeve_module is None:
        return None
    loaded = load_sleeve_module(tag)
    if loaded.get("status") == "LOADED_FROM_RECOVERY" and loaded.get("ON_SURFACE"):
        return str(loaded.get("TAG") or tag), tuple(loaded["ON_SURFACE"])
    return None


def load_on_surface_specs(tags: Sequence[str]) -> Tuple[List[_Spec], Dict[str, Any]]:
    notes: Dict[str, Any] = {"loaded": {}, "missing": []}
    specs: List[_Spec] = []
    seen = set()
    for tag in tags:
        got = _load_on_surface_from_recovered(tag)
        if got:
            full, surface = got
            if full not in seen:
                specs.append(_Spec(full, surface))
                seen.add(full)
            if tag != full and tag not in seen:
                specs.append(_Spec(tag, surface))
                seen.add(tag)
            notes["loaded"][full] = {"ON_SURFACE": list(surface), "alias_requested": tag}
        else:
            notes["missing"].append({"tag": tag, "note": "refuse invent ON_SURFACE"})
    return specs, notes


def _is_hard_off(tag: str, families: set) -> Optional[str]:
    t = tag.lower()
    for h in families:
        if h.lower() in t:
            return h
    return None


def alive_sleeves_for_symbol(
    symbol: str,
    *,
    account: Optional[str] = None,
    use_research_overlay: bool = True,
    relax_to_jev: Optional[bool] = None,
) -> Dict[str, Any]:
    """Compose alive sleeve tags for symbol.

    When relax_to_jev: hard-off matches become blocked_escape (BLOCKED), not silent drop.
    """
    symbol = str(symbol).upper()
    relax = relax_to_jev_enabled(relax_to_jev)
    live_tags, live_meta = load_live_armed_tags(account)
    research_tags, research_meta = load_research_armed_tags()

    if use_research_overlay and research_tags:
        armed = list(research_tags)
        armed_source = "research_armed_tags"
    else:
        armed = list(live_tags)
        armed_source = "live_armed"

    specs, spec_notes = load_on_surface_specs(armed)
    hard_off, inv_meta = hard_off_families()
    build_slots = _import_build_slots()
    slots = build_slots(specs, lambda c: str(c), armed_tags=list(armed))

    by_sym: Dict[str, List[str]] = defaultdict(list)
    for sl in slots:
        if not getattr(sl, "armed", False):
            continue
        sleeve = getattr(sl, "sleeve", None) or getattr(sl, "tag", None)
        if sleeve is None:
            continue
        keys = {getattr(sl, "canonical", None)}
        broker = getattr(sl, "broker", None)
        if broker:
            keys.add(broker)
        for k in keys:
            if k:
                by_sym[str(k).upper()].append(str(sleeve))

    raw = sorted(set(by_sym.get(symbol, [])))
    alive: List[str] = []
    blocked_escape: List[Dict[str, Any]] = []
    silently_dropped: List[str] = []

    for t in raw:
        hit = _is_hard_off(t, hard_off)
        if hit is None:
            alive.append(t)
        elif relax:
            blocked_escape.append(
                {
                    "tag": t,
                    "hard_off_family": hit,
                    "escape": "BLOCKED",
                    "note": "RELAX_TO_JEV — hard-off is BLOCKED Choice escape, not silent drop",
                }
            )
        else:
            silently_dropped.append(t)

    alive = sorted(set(alive))

    return {
        "schema": "gtos.dig.jev_sleeve_select.alive_sleeves_for_symbol.v1",
        "ts_ict": _ict_now(),
        "field": "inventory.alive_sleeves_for_symbol",
        "chair": "JEV_SLEEVE_SELECT",
        "symbol": symbol,
        "alive_sleeves_for_symbol": alive,
        "blocked_escape": blocked_escape,
        "hard_off_silently_dropped": silently_dropped if not relax else [],
        "relax_to_jev": relax,
        "armed_source": armed_source,
        "research_armed_tags": research_tags,
        "live_armed_tags": live_tags,
        "live_armed_set_mutated": False,
        "named_function_exists": True,
        "compose": {
            "recipe": "build_slots(specs) ∩ armed ∩ ON_SURFACE(symbol); hard-off→BLOCKED if RELAX_TO_JEV else drop from alive",
            "n_slots": len(slots),
            "n_raw_for_symbol": len(raw),
            "specs": spec_notes,
            "hard_off_meta": inv_meta,
            "live_armed_meta": live_meta,
            "research_armed_meta": research_meta,
            "occupancy_invented": False,
            "corr_invented": False,
            "news_invented": False,
        },
        "apply": False,
        "place": False,
        "promote": False,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    symbol = "EURUSD"
    if "--symbol" in argv:
        symbol = argv[argv.index("--symbol") + 1]
    elif argv and not argv[0].startswith("-"):
        symbol = argv[0]
    relax = "--relax-to-jev" in argv
    use_research = "--live-armed" not in argv

    pack = alive_sleeves_for_symbol(symbol, use_research_overlay=use_research, relax_to_jev=relax)
    demos = {
        s: alive_sleeves_for_symbol(s, use_research_overlay=True, relax_to_jev=relax)
        for s in ("XAUUSD", "EURUSD", "GBPUSD", "USDJPY")
    }

    out_json = _HERE / "JEV_SLEEVE_SELECT_ALIVE_SLEEVES_20260920.json"
    out_md = _HERE / "JEV_SLEEVE_SELECT_ALIVE_SLEEVES_20260920.md"
    report = {
        "schema": "gtos.dig.jev_sleeve_select.writer_report.v1",
        "ts_ict": _ict_now(),
        "writer": str(_HERE / "alive_sleeves_for_symbol.py"),
        "named_function": "alive_sleeves_for_symbol",
        "place": False,
        "apply": False,
        "live_armed_set_mutated": False,
        "primary": pack,
        "demos": {
            s: {
                "alive": d["alive_sleeves_for_symbol"],
                "blocked_escape": d["blocked_escape"],
                "relax_to_jev": d["relax_to_jev"],
                "n_alive": len(d["alive_sleeves_for_symbol"]),
            }
            for s, d in demos.items()
        },
        "paths": {
            "writer": str(_HERE / "alive_sleeves_for_symbol.py"),
            "pointers": str(_DIG_WAR / "ALIVE_SLEEVES_FOR_SYMBOL_POINTERS_20260920.md"),
            "build_slots": str(_SWARM_SRC / "components/ultimate_book/symbol_resolution_watch.py"),
            "overlay": str(_OVERLAY),
        },
    }
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# JEV_SLEEVE_SELECT — alive_sleeves_for_symbol — {report['ts_ict']}",
        "",
        "**place=false** · **apply=false** · live_armed untouched",
        "",
        f"**Writer:** `{report['writer']}`",
        "",
        "## Recipe",
        "`build_slots ∩ armed ∩ ON_SURFACE(symbol)`; hard-off → BLOCKED escape when RELAX_TO_JEV",
        "",
        f"Primary `{pack['symbol']}` alive=`{pack['alive_sleeves_for_symbol']}` relax={pack['relax_to_jev']}",
        f"blocked_escape=`{pack['blocked_escape']}`",
        "",
        "| symbol | n | alive | blocked_escape |",
        "|---|---:|---|---|",
    ]
    for s, d in report["demos"].items():
        lines.append(f"| {s} | {d['n_alive']} | `{d['alive']}` | `{d['blocked_escape']}` |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "symbol": symbol, "alive": pack["alive_sleeves_for_symbol"], "blocked": pack["blocked_escape"], "json": str(out_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""alive_sleeves_for_symbol writer — Dig compose + research_armed_tags overlay.

SHADOW only: apply=false · place=false · never mutate live_armed_set.

Compose recipe (Dig pointers):
  alive = build_slots(ON_SURFACE specs) ∩ research_armed_tags ∩ inventory(hard-off blocked)
  armed_source stamped separately: research_armed_tags vs live_armed

Pointers:
  ALIVE_SLEEVES_FOR_SYMBOL_POINTERS_DIG_20260920.json
  SYSTEM_ONE_INFRA_POINTERS_DIG_20260920.json
  RESEARCH_ARMED_TAGS_OVERLAY_20260920.json
  symbol_resolution_watch.build_slots
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_BOX = Path(__file__).resolve().parent
_GTOS = Path("/workspace/gtos")
_SWARM_SRC = _GTOS / "_swarm_land_tip/extract/src"
_ARMED_JSON = _GTOS / "_swarm_land_tip/extract/config/live_armed_set.json"
_OVERLAY = _BOX / "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"
_DIG_PTR = _BOX / "ALIVE_SLEEVES_FOR_SYMBOL_POINTERS_DIG_20260920.json"
_SYS1 = _BOX / "SYSTEM_ONE_INFRA_POINTERS_DIG_20260920.json"
_WARROOM_SRC = _GTOS / "judgment/warroom_shadow"

if str(_BOX) not in sys.path:
    sys.path.insert(0, str(_BOX))
from sleeve_on_surface_loader import load_sleeve_module  # noqa: E402


def _ict_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M ICT")


def load_live_armed_tags(account: Optional[str] = None) -> Tuple[List[str], Dict[str, Any]]:
    """Read-only live_armed_set.json. Never mutate."""
    meta: Dict[str, Any] = {"path": str(_ARMED_JSON), "mutated": False, "source": None}
    if not _ARMED_JSON.exists():
        meta["source"] = "unavailable"
        return [], meta
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
    return sorted(out), meta


def load_research_armed_tags() -> Tuple[List[str], Dict[str, Any]]:
    meta: Dict[str, Any] = {"path": str(_OVERLAY), "source": None}
    if not _OVERLAY.exists():
        meta["source"] = "unavailable"
        return [], meta
    body = json.loads(_OVERLAY.read_text())
    tags = [str(t) for t in (body.get("research_armed_tags") or [])]
    meta["source"] = "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"
    meta["alias_to_module_tag"] = body.get("alias_to_module_tag") or {}
    meta["modules"] = {
        k: {"ON_SURFACE": (v or {}).get("ON_SURFACE"), "status": (v or {}).get("status")}
        for k, v in (body.get("modules") or {}).items()
    }
    return tags, meta


class _Spec:
    def __init__(self, tag: str, on_surface: tuple):
        self.tag = tag
        self.on_surface = on_surface


def _import_build_slots():
    if str(_SWARM_SRC) not in sys.path:
        sys.path.insert(0, str(_SWARM_SRC))
    from components.ultimate_book.symbol_resolution_watch import build_slots  # type: ignore
    return build_slots


def load_on_surface_specs(tags: Sequence[str]) -> Tuple[List[_Spec], Dict[str, Any]]:
    """Parse ON_SURFACE from recovered modules. Never invent."""
    notes: Dict[str, Any] = {"loaded": {}, "missing": []}
    specs: List[_Spec] = []
    seen = set()
    for tag in tags:
        loaded = load_sleeve_module(tag)
        if loaded.get("status") == "LOADED_FROM_RECOVERY" and loaded.get("ON_SURFACE"):
            full = loaded.get("TAG") or tag
            surface = tuple(loaded["ON_SURFACE"])
            if full not in seen:
                specs.append(_Spec(full, surface))
                seen.add(full)
            if tag != full and tag not in seen:
                specs.append(_Spec(tag, surface))
                seen.add(tag)
            notes["loaded"][full] = {
                "path": loaded.get("path"),
                "ON_SURFACE": list(surface),
                "status": loaded.get("status"),
                "alias_requested": tag,
            }
        else:
            notes["missing"].append(
                {
                    "tag": tag,
                    "status": loaded.get("status") or "MISSING_MODULE",
                    "note": "refuse invent ON_SURFACE",
                }
            )
    return specs, notes


def collect_inventory_hard_off(armed: Sequence[str]) -> Tuple[set, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    try:
        if str(_WARROOM_SRC) not in sys.path:
            sys.path.insert(0, str(_WARROOM_SRC))
        from src.judgment.inventory import collect_live_inventory  # type: ignore
        from src.judgment.challenge import (  # type: ignore
            CHALLENGE_KEEP_FAMILIES,
            CHALLENGE_HARD_OFF_FAMILIES,
        )

        inv = collect_live_inventory(
            sleeves=list(armed) + list(CHALLENGE_KEEP_FAMILIES),
            include_w7_armed=False,
            include_launcher_workers=False,
            include_challenge_keep=False,
        )
        meta["source"] = "collect_live_inventory"
        meta["hard_off"] = list(CHALLENGE_HARD_OFF_FAMILIES)
        meta["fingerprint"] = inv.fingerprint
        return set(CHALLENGE_HARD_OFF_FAMILIES), meta
    except Exception as exc:
        hard_off = {"bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30"}
        meta["source"] = "fallback_hard_off"
        meta["error"] = f"{type(exc).__name__}:{exc}"
        meta["hard_off"] = list(hard_off)
        return hard_off, meta


def alive_sleeves_for_symbol(
    symbol: str,
    *,
    account: Optional[str] = None,
    use_research_overlay: bool = True,
) -> Dict[str, Any]:
    """Return alive sleeve tags for research (research_armed ∩ ON_SURFACE ∩ compose).

    Does NOT invent occupancy/corr. Does NOT mutate live_armed.
    """
    symbol = str(symbol).upper()
    live_tags, live_meta = load_live_armed_tags(account)
    research_tags, research_meta = load_research_armed_tags()

    if use_research_overlay and research_tags:
        armed = list(research_tags)
        armed_source = "research_armed_tags"
    else:
        armed = list(live_tags)
        armed_source = "live_armed"

    specs, spec_notes = load_on_surface_specs(armed)
    hard_off, inv_meta = collect_inventory_hard_off(armed)
    build_slots = _import_build_slots()
    slots = build_slots(specs, lambda c: str(c), armed_tags=list(armed))

    by_sym: Dict[str, List[str]] = defaultdict(list)
    for sl in slots:
        if not sl.armed:
            continue
        keys = {sl.canonical}
        if sl.broker:
            keys.add(sl.broker)
        for k in keys:
            by_sym[str(k).upper()].append(sl.sleeve)

    raw = sorted(set(by_sym.get(symbol, [])))
    alive = sorted({t for t in raw if not any(h in t for h in hard_off)})

    # Dual stamp: what live_armed would yield (contrast only)
    live_alive: List[str] = []
    if live_tags:
        live_specs, _ = load_on_surface_specs(live_tags)
        live_slots = build_slots(live_specs, lambda c: str(c), armed_tags=list(live_tags))
        live_by: Dict[str, List[str]] = defaultdict(list)
        for sl in live_slots:
            if not sl.armed:
                continue
            keys = {sl.canonical}
            if sl.broker:
                keys.add(sl.broker)
            for k in keys:
                live_by[str(k).upper()].append(sl.sleeve)
        live_alive = sorted(
            {t for t in set(live_by.get(symbol, [])) if not any(h in t for h in hard_off)}
        )

    return {
        "schema": "gtos.close_loop.alive_sleeves_for_symbol.v1",
        "ts_ict": _ict_now(),
        "field": "inventory.alive_sleeves_for_symbol",
        "symbol": symbol,
        "alive_sleeves_for_symbol": alive,
        "armed_source": armed_source,
        "research_armed_tags": research_tags,
        "live_armed_tags": live_tags,
        "live_armed_alive_sleeves_for_symbol": live_alive,
        "live_armed_set_mutated": False,
        "named_function_exists": True,
        "writer": str(_BOX / "alive_sleeves_for_symbol.py"),
        "compose": {
            "recipe": (
                "build_slots(ON_SURFACE from sleeve_on_surface_loader) "
                "∩ research_armed_tags ∩ hard-off blocked"
                if armed_source == "research_armed_tags"
                else "build_slots ∩ live_armed ∩ hard-off blocked"
            ),
            "dig_pointer": str(_DIG_PTR),
            "system_one_pointer": str(_SYS1),
            "best_match_helper": "symbol_resolution_watch.build_slots",
            "n_slots": len(slots),
            "n_armed_slots_for_symbol": len(raw),
            "specs": spec_notes,
            "inventory": inv_meta,
            "live_armed_meta": live_meta,
            "research_armed_meta": research_meta,
            "occupancy_invented": False,
            "corr_invented": False,
        },
        "apply": False,
        "place": False,
        "promote": False,
        "note": "SHADOW research writer — never mutates live_armed_set.json",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    symbol = "XAUUSD"
    if "--symbol" in argv:
        symbol = argv[argv.index("--symbol") + 1]
    elif argv and not argv[0].startswith("-"):
        symbol = argv[0]

    use_research = "--live-armed" not in argv
    pack = alive_sleeves_for_symbol(symbol, use_research_overlay=use_research)

    out_json = _BOX / "ALIVE_SLEEVES_FOR_SYMBOL_WRITER_20260920.json"
    out_md = _BOX / "ALIVE_SLEEVES_FOR_SYMBOL_WRITER_20260920.md"

    # Demo multi-symbol snapshot for report
    demos = {}
    for sym in ("XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"):
        demos[sym] = alive_sleeves_for_symbol(sym, use_research_overlay=True)

    report = {
        "schema": "gtos.close_loop.alive_sleeves_for_symbol_writer.v1",
        "ts_ict": _ict_now(),
        "writer": str(_BOX / "alive_sleeves_for_symbol.py"),
        "named_function": "alive_sleeves_for_symbol",
        "named_function_exists": True,
        "apply": False,
        "place": False,
        "promote": False,
        "live_armed_set_mutated": False,
        "armed_source_default": "research_armed_tags",
        "primary_symbol": symbol,
        "primary": pack,
        "demos": {
            s: {
                "alive_sleeves_for_symbol": d["alive_sleeves_for_symbol"],
                "armed_source": d["armed_source"],
                "live_armed_alive_sleeves_for_symbol": d["live_armed_alive_sleeves_for_symbol"],
                "n_alive": len(d["alive_sleeves_for_symbol"]),
            }
            for s, d in demos.items()
        },
        "research_armed_tags": pack["research_armed_tags"],
        "live_armed_tags": pack["live_armed_tags"],
        "paths": {
            "writer": str(_BOX / "alive_sleeves_for_symbol.py"),
            "dig_pointer": str(_DIG_PTR),
            "system_one_pointer": str(_SYS1),
            "overlay": str(_OVERLAY),
            "build_slots": str(
                _SWARM_SRC / "components/ultimate_book/symbol_resolution_watch.py"
            ),
            "live_armed_readonly": str(_ARMED_JSON),
        },
        "forbidden_respected": {
            "place": False,
            "promote": False,
            "news_invent": False,
            "live_armed_set_mutate": False,
            "occupancy_corr_invent": False,
            "v3": False,
        },
    }
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# alive_sleeves_for_symbol writer — {report['ts_ict']}",
        "",
        "**Mode:** SHADOW · apply=false · place=false · live_armed untouched",
        "",
        f"**Writer:** `{report['writer']}`",
        f"**Named function:** `alive_sleeves_for_symbol(symbol)` — **exists=true**",
        "",
        "## Compose recipe",
        "",
        "`build_slots(ON_SURFACE) ∩ research_armed_tags ∩ hard-off blocked`",
        "",
        f"- armed_source default: `{report['armed_source_default']}`",
        f"- Dig pointer: `{_DIG_PTR.name}`",
        f"- Overlay: `{_OVERLAY.name}`",
        f"- Helper: `symbol_resolution_watch.build_slots` (compose, no invent occupancy/corr)",
        "",
        "## Primary",
        "",
        f"| field | value |",
        f"|---|---|",
        f"| symbol | {pack['symbol']} |",
        f"| alive | `{pack['alive_sleeves_for_symbol']}` |",
        f"| armed_source | `{pack['armed_source']}` |",
        f"| live_armed contrast alive | `{pack['live_armed_alive_sleeves_for_symbol']}` |",
        f"| live_armed_set_mutated | false |",
        "",
        "## Demo by symbol (research_armed overlay)",
        "",
        "| symbol | n | alive | live_armed contrast |",
        "|---|---:|---|---|",
    ]
    for s, d in report["demos"].items():
        md.append(
            f"| {s} | {d['n_alive']} | `{d['alive_sleeves_for_symbol']}` | `{d['live_armed_alive_sleeves_for_symbol']}` |"
        )
    md += [
        "",
        "## Forbidden respected",
        "place / promote / NEWS invent / mutate live_armed / invent occupancy·corr / V3 = false",
        "",
        f"Report JSON: `{out_json}`",
        "",
    ]
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "symbol": symbol,
                "alive": pack["alive_sleeves_for_symbol"],
                "armed_source": pack["armed_source"],
                "json": str(out_json),
                "md": str(out_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

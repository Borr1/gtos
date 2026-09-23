#!/usr/bin/env python3
"""LIVE-BOOK INTEGRITY Task 1 - symbol-universe ground truth, STRICTLY READ-ONLY.

MT5 calls used: initialize / symbol_info / symbols_get / symbol_info_tick / terminal_info /
account_info / shutdown.  There is no order_send, order_check, order_calc_* or any other
mutating or margin-reserving call in this file.  Nothing is written inside the live tree.

For each live account it reproduces the engine's own symbol resolution
(apply_profile_overrides -> build_broker_symbol_resolver -> active_specs) and then asks the
BROKER whether each canonical slot exists, so a profile-config omission can be told apart
from a genuine broker limitation.
"""
import os
import sys
import json
import datetime as dt

REPO = r"C:\Users\MSI\Documents\ai-trading-agent"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"host-local\lbi_20260811"
os.makedirs(OUT, exist_ok=True)
os.chdir(REPO)
sys.path.insert(0, REPO)

import yaml  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402
from src.utils.config import apply_profile_overrides  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.admission import cluster_of  # noqa: E402

# exactly the live command lines (Get-CimInstance Win32_Process, 2026-08-11T10:21Z)
ARMED_TAGS = ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"]
ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", "operator_profile"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", "redacted_account"),
]

SYM_FIELDS = ("name", "path", "trade_mode", "visible", "select", "digits", "point",
              "trade_contract_size", "volume_min", "volume_max", "volume_step",
              "spread", "spread_float", "trade_stops_level", "swap_long", "swap_short",
              "swap_mode", "currency_base", "currency_profit", "currency_margin")

TRADE_MODE_NAMES = {0: "DISABLED", 1: "LONGONLY", 2: "SHORTONLY", 3: "CLOSEONLY", 4: "FULL"}

base_cfg = yaml.safe_load(open(os.path.join(REPO, "config", "agent_config.yaml"), encoding="utf-8"))

result = {
    "schema": "gtos.live_book_integrity.symbol_universe.v1",
    "as_of_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "armed_tags": ARMED_TAGS,
    "host_repo": REPO,
    "accounts": {},
}

# ---- 1. resolve each account's declared universe from the live config, per the engine ----
per_account_slots = {}
for label, term, profile in ACCOUNTS:
    merged = apply_profile_overrides(dict(base_cfg), profile)
    rt = merged.get("gtos_vnext_runtime", merged)
    resolver = build_broker_symbol_resolver(merged)
    supports = getattr(resolver, "supports")

    include_c3 = bool(rt.get("ultimate_book_include_clean3", False))
    include_cb = bool(rt.get("ultimate_book_include_candidate_book", False))
    include_me = bool(rt.get("ultimate_book_include_market_expansion_book", False))
    cand = rt.get("ultimate_book_candidate_book_sleeves") or None
    expa = rt.get("ultimate_book_market_expansion_sleeves") or None

    specs = list(active_specs(ARMED_TAGS,
                             include_candidate_book=include_cb,
                             candidate_book_sleeves=cand,
                             include_market_expansion_book=include_me,
                             market_expansion_sleeves=expa))
    slots = []
    for spec in specs:
        for sym in spec.on_surface:
            slots.append({
                "canonical": sym,
                "sleeve": spec.tag,
                "cluster": getattr(spec, "cluster", None),
                "cluster_of": cluster_of(spec.tag),
                "timeframe": getattr(spec, "timeframe", None),
                "profile_supported": bool(supports(sym)),
                "broker_name": resolver(sym),
            })
    per_account_slots[label] = slots
    result["accounts"][label] = {
        "profile": profile,
        "terminal": term,
        "include_clean3": include_c3,
        "include_candidate_book": include_cb,
        "include_market_expansion_book": include_me,
        "spec_count": len(specs),
        "spec_tags": sorted({s.tag for s in specs}),
        "active_symbol_slot_count": len(slots),
        "profile_supported_slot_count": sum(1 for s in slots if s["profile_supported"]),
        "profile_unsupported_slot_count": sum(1 for s in slots if not s["profile_supported"]),
        "profile_instrument_count": len((merged.get("instruments") or {})),
        "slots": slots,
    }

# every canonical name any account wants, plus common broker aliases to test for a
# naming mismatch masquerading as an absence
union_canonical = sorted({s["canonical"] for v in per_account_slots.values() for s in v})
ALIAS_PROBE = {
    "XAUEUR": ["XAUEUR", "XAUEUR.", "GOLDEUR", "XAUEUR_c", "XAUEURm"],
    "XAGEUR": ["XAGEUR", "SILVEREUR", "XAGEUR_c"],
    "XAUAUD": ["XAUAUD", "GOLDAUD", "XAUAUD_c"],
    "XAGAUD": ["XAGAUD", "SILVERAUD", "XAGAUD_c"],
    "CORN_c": ["CORN_c", "CORN", "CORN.cash", "CORNUSD", "ZC"],
    "COTTON_c": ["COTTON_c", "COTTON", "COTTON.cash", "COTTONUSD", "CT"],
    "DASHUSD": ["DASHUSD", "DASH", "DSHUSD", "DASHUSD.", "DASHUSDm"],
    "AVAUSD": ["AVAUSD", "AVAXUSD", "AVAUSD."],
    "XPDUSD": ["XPDUSD", "PALLADIUM", "XPDUSD."],
    "XTZUSD": ["XTZUSD", "XTZUSD.", "TEZOSUSD"],
}

# ---- 2. ask each BROKER directly ----
for label, term, profile in ACCOUNTS:
    if not mt5.initialize(path=term):
        result["accounts"][label]["broker_error"] = str(mt5.last_error())
        continue
    ti = mt5.terminal_info()
    ai = mt5.account_info()
    acct = result["accounts"][label]
    acct["broker_server"] = getattr(ai, "server", None)
    acct["broker_company"] = getattr(ai, "company", None)
    acct["broker_trade_allowed"] = getattr(ai, "trade_allowed", None)
    acct["terminal_connected"] = getattr(ti, "connected", None)
    acct["terminal_trade_allowed"] = getattr(ti, "trade_allowed", None)

    all_syms = mt5.symbols_get()
    all_names = sorted({s.name for s in (all_syms or [])})
    acct["broker_total_symbol_count"] = len(all_names)

    probe = {}
    for canon in union_canonical:
        merged = apply_profile_overrides(dict(base_cfg), profile)
        resolver = build_broker_symbol_resolver(merged)
        bname = resolver(canon)
        info = mt5.symbol_info(bname)
        row = {"canonical": canon, "probed_broker_name": bname,
               "exists_on_broker": info is not None}
        if info is not None:
            for f in SYM_FIELDS:
                v = getattr(info, f, None)
                if v is not None:
                    row[f] = v
            row["trade_mode_name"] = TRADE_MODE_NAMES.get(row.get("trade_mode"), "?")
        else:
            # not found under the resolved name -> is the instrument on this broker at all?
            aliases = ALIAS_PROBE.get(canon, [canon])
            found = []
            for a in aliases:
                if mt5.symbol_info(a) is not None:
                    found.append(a)
            # broad substring sweep over the broker's whole tradable list
            stem = canon.replace("_c", "").replace("_cash", "").upper()
            near = [n for n in all_names if stem and stem in n.upper()][:12]
            row["alias_hits"] = found
            row["substring_matches_on_broker"] = near
        probe[canon] = row
    acct["broker_probe"] = probe
    mt5.shutdown()

# ---- 3. reconcile: which slots are unreachable, and why ----
for label in result["accounts"]:
    acct = result["accounts"][label]
    probe = acct.get("broker_probe", {})
    unreachable = []
    for s in acct["slots"]:
        c = s["canonical"]
        pr = probe.get(c, {})
        if not s["profile_supported"]:
            cause = ("PROFILE_OMISSION_BROKER_HAS_IT" if pr.get("exists_on_broker")
                     else ("PROFILE_OMISSION_ALIAS_EXISTS" if pr.get("alias_hits")
                           else "BROKER_DOES_NOT_LIST_IT"))
            unreachable.append({**s, "cause": cause,
                                "broker_alias_hits": pr.get("alias_hits"),
                                "broker_substring_matches": pr.get("substring_matches_on_broker")})
        elif not pr.get("exists_on_broker"):
            unreachable.append({**s, "cause": "PROFILE_DECLARES_BUT_BROKER_MISSING",
                                "broker_alias_hits": pr.get("alias_hits")})
        elif pr.get("trade_mode") not in (4, None):
            unreachable.append({**s, "cause": "BROKER_TRADE_MODE_" + str(pr.get("trade_mode_name"))})
    acct["unreachable_slots"] = unreachable
    acct["unreachable_slot_count"] = len(unreachable)
    acct["unreachable_symbols"] = sorted({u["canonical"] for u in unreachable})
    by_sleeve = {}
    for u in unreachable:
        by_sleeve.setdefault(u["sleeve"], []).append(u["canonical"])
    tot_by_sleeve = {}
    for s in acct["slots"]:
        tot_by_sleeve[s["sleeve"]] = tot_by_sleeve.get(s["sleeve"], 0) + 1
    acct["unreachable_by_sleeve"] = {
        k: {"lost": sorted(set(v)), "lost_slots": len(v),
            "total_slots": tot_by_sleeve.get(k, 0),
            "surviving_slots": tot_by_sleeve.get(k, 0) - len(v)}
        for k, v in sorted(by_sleeve.items())
    }

out = os.path.join(OUT, "SYMBOL_UNIVERSE_V1.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=1, sort_keys=False)
print("WROTE", out)
for label, acct in result["accounts"].items():
    print(label, "slots", acct["active_symbol_slot_count"],
          "profile_supported", acct["profile_supported_slot_count"],
          "unreachable", acct.get("unreachable_slot_count"),
          "brokersyms", acct.get("broker_total_symbol_count"))
    print("   lost:", acct.get("unreachable_symbols"))
    print("   by sleeve:", json.dumps(acct.get("unreachable_by_sleeve", {})))

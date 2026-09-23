"""B5 step 2 (a) — which of the 166 archive symbols are TRADEABLE on the two live accounts.

Read-only. Four independent authorities, in decreasing order of strength:
  A1  broker symbol list, FTMO        vps-export .../09_mt5_api/ftmo_symbols_get.jsonl        (167)
  A2  broker symbol list, redacted_account  vps-export .../09_mt5_api/redacted_account_symbols_get.jsonl  (76)
  A3  GTOS instrument config          config/profiles/{operator_profile,redacted_account}.yaml
  A4  cross-broker spec comparison    vps-export .../09_mt5_api/BROKER_SYMBOL_SPEC_COMPARISON.json

A1/A2 say "the broker lists it and it is trade_mode FULL".
A3 says "GTOS can size it" — without an `instruments` entry the live book skips the symbol
(the known redacted_account gap: 13 symbol/sleeve pairs silently skipped on missing instrument config).
So TRADEABLE_NOW = A1/A2 AND A3.  TRADEABLE_AFTER_CONFIG = A1/A2 only.  RESEARCH_ONLY = neither.

Writes <OUT>/B5_TRADEABILITY_V1.json
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
OUT = os.path.join(HERE, "..", "b5_receipts")
EXP = "/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api"
COSTS = os.path.join(REPO, "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json")

# MT5 SYMBOL_TRADE_MODE: 0 disabled, 1 longonly, 2 shortonly, 3 closeonly, 4 full
TRADE_MODE_FULL = 4


# The three naming systems: archive (`US500_cash`, `BRK_B`, `COCOA_c`), FTMO broker
# (`US500.cash`, `BRK.B`, `COCOA.C`) and redacted_account broker (`SPX500`, `GER30`, `UKOUSD`).
# Canonical key = uppercase, drop the CFD suffix, drop separators. Then one explicit
# alias table for the instruments redacted_account genuinely names differently
# (BROKER_SYMBOL_SPEC_COMPARISON.json `alias_map`, inverted, extended by inspection).
BROKER_ALIAS = {
    "NDX100": "US100", "SPX500": "US500", "GER30": "GER40", "EUSTX50": "EU50",
    "NTH25": "N25", "UKOUSD": "UKOIL", "USOUSD": "USOIL",
}


def norm(s):
    k = s.upper()
    for suf in (".CASH", "_CASH", ".C", "_C"):
        if k.endswith(suf):
            k = k[: -len(suf)]
            break
    k = k.replace(".", "").replace("_", "")
    return BROKER_ALIAS.get(k, k)


FN_ALIAS = {}


def load_symbols_jsonl(path):
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out[norm(d["name"])] = {
                "broker_name": d["name"], "path": d.get("path"),
                "trade_mode": d.get("trade_mode"), "visible": d.get("visible"),
                "spread_points_snapshot": d.get("spread"),
                "point": d.get("point"), "digits": d.get("digits"),
                "contract_size": d.get("trade_contract_size"),
                "volume_min": d.get("volume_min"), "volume_max": d.get("volume_max"),
                "trade_stops_level": d.get("trade_stops_level"),
                "trade_freeze_level": d.get("trade_freeze_level"),
                "swap_long": d.get("swap_long"), "swap_short": d.get("swap_short"),
                "bid": d.get("bid"), "ask": d.get("ask"),
            }
    return out


def load_profile_instruments(path):
    """Minimal YAML read of just the top-level `instruments:` keys, no yaml dep issues."""
    import yaml
    d = yaml.safe_load(open(path))
    ins = d.get("instruments") or {}
    return {norm(k): k for k in ins}


def main():
    inv = json.load(open(os.path.join(OUT, "B5_UNIVERSE_INVENTORY_V1.json")))
    syms = inv["symbols"]

    ftmo = load_symbols_jsonl(os.path.join(EXP, "ftmo_symbols_get.jsonl"))
    fn = load_symbols_jsonl(os.path.join(EXP, "redacted_account_symbols_get.jsonl"))
    cfg_ftmo = load_profile_instruments(os.path.join(REPO, "config/profiles/operator_profile.yaml"))
    cfg_fn = load_profile_instruments(os.path.join(REPO, "config/profiles/redacted_account.yaml"))
    cmp_json = json.load(open(os.path.join(EXP, "BROKER_SYMBOL_SPEC_COMPARISON.json")))
    costs = json.load(open(COSTS))
    cost_ftmo = {norm(k): v for k, v in costs["accounts"]["FTMO"]["instruments"].items()}
    cost_fn = {norm(k): v for k, v in costs["accounts"]["redacted_account"]["instruments"].items()}

    rec = {}
    for s, meta in syms.items():
        k = norm(s)
        fk = FN_ALIAS.get(k, k)
        fnk = norm(fk)
        f = ftmo.get(k)
        n = fn.get(fnk)
        cf = cost_ftmo.get(k)
        cn = cost_fn.get(fnk)
        ftmo_listed = f is not None and f["trade_mode"] == TRADE_MODE_FULL
        fn_listed = n is not None and n["trade_mode"] == TRADE_MODE_FULL
        ftmo_cfg = k in cfg_ftmo
        fn_cfg = fnk in cfg_fn or k in cfg_fn
        if ftmo_listed or fn_listed:
            status = "TRADEABLE_NOW" if (ftmo_cfg or fn_cfg) else "TRADEABLE_AFTER_CONFIG"
        else:
            status = "RESEARCH_ONLY"
        rec[s] = {
            "class": meta["class"], "n_d1": meta["n"], "first": meta["first"][:10], "last": meta["last"][:10],
            "span_years": meta["span_years"],
            "status": status,
            "ftmo_listed": ftmo_listed, "redacted_account_listed": fn_listed,
            "ftmo_instrument_config": ftmo_cfg, "redacted_account_instrument_config": fn_cfg,
            "ftmo_broker_name": f["broker_name"] if f else None,
            "redacted_account_broker_name": n["broker_name"] if n else None,
            "ftmo_trade_mode": f["trade_mode"] if f else None,
            "redacted_account_trade_mode": n["trade_mode"] if n else None,
            "ftmo_broker_path": (cf or {}).get("broker_path") if cf else (f or {}).get("path"),
            "ftmo_spread_points_snapshot": f["spread_points_snapshot"] if f else None,
            "ftmo_point": f["point"] if f else None,
            "ftmo_mid_snapshot": (0.5 * (f["bid"] + f["ask"]) if f and f.get("bid") and f.get("ask") else None),
            "ftmo_trade_stops_level": f["trade_stops_level"] if f else None,
            "ftmo_volume_min": f["volume_min"] if f else None,
            "ftmo_contract_size": f["contract_size"] if f else None,
            "ftmo_swap_long": f["swap_long"] if f else None,
            "ftmo_swap_short": f["swap_short"] if f else None,
            "cost_layer_class_ftmo": (cf or {}).get("instrument_class"),
            "cost_commission_coverage_ftmo": ((cf or {}).get("commission") or {}).get("coverage"),
            "cost_spread_coverage_ftmo": "MEASURED" if (cf or {}).get("spread_price") else "ABSENT",
        }

    # rollups
    from collections import Counter, defaultdict
    by_status = Counter(v["status"] for v in rec.values())
    by_status_class = defaultdict(Counter)
    for v in rec.values():
        by_status_class[v["class"]][v["status"]] += 1
    both = [s for s, v in rec.items() if v["ftmo_listed"] and v["redacted_account_listed"]]
    ftmo_only = [s for s, v in rec.items() if v["ftmo_listed"] and not v["redacted_account_listed"]]
    neither = [s for s, v in rec.items() if not v["ftmo_listed"] and not v["redacted_account_listed"]]
    cfg_any = [s for s, v in rec.items() if v["ftmo_instrument_config"] or v["redacted_account_instrument_config"]]

    # what the archive is NOT: broker symbols absent from the archive
    arch_keys = {norm(s) for s in syms}
    ftmo_not_in_archive = sorted(k for k in ftmo if k not in arch_keys)
    fn_not_in_archive = sorted(k for k in fn if k not in arch_keys and FN_ALIAS.get(k, k) not in arch_keys)

    roll = {
        "n_archive_symbols": len(rec),
        "n_ftmo_broker_symbols": len(ftmo),
        "n_redacted_account_broker_symbols": len(fn),
        "n_ftmo_instrument_config": len(cfg_ftmo),
        "n_redacted_account_instrument_config": len(cfg_fn),
        "by_status": dict(by_status),
        "by_class_status": {c: dict(v) for c, v in by_status_class.items()},
        "listed_on_both_brokers": len(both),
        "listed_ftmo_only": len(ftmo_only),
        "listed_on_neither": len(neither),
        "n_with_gtos_instrument_config": len(cfg_any),
        "gtos_configured_symbols": sorted(cfg_any),
        "ftmo_broker_symbols_absent_from_archive": ftmo_not_in_archive,
        "redacted_account_broker_symbols_absent_from_archive": fn_not_in_archive,
        "archive_is_ftmo_symbol_list": len(neither) == 0,
        "note_live_surface": "the estate's live/replay surface is 24 symbols (GTOS_24_SYMBOL_SURFACE); "
                             "GTOS instrument config covers %d of the archive; the FTMO broker lists %d." % (len(cfg_any), len(both) + len(ftmo_only)),
        "sources": {
            "ftmo_symbols_get": os.path.join(EXP, "ftmo_symbols_get.jsonl"),
            "redacted_account_symbols_get": os.path.join(EXP, "redacted_account_symbols_get.jsonl"),
            "spec_comparison": os.path.join(EXP, "BROKER_SYMBOL_SPEC_COMPARISON.json"),
            "spec_comparison_note": cmp_json["note"],
            "spec_comparison_alias_map": cmp_json["alias_map"],
            "spec_comparison_fn_only": cmp_json["symbols_only_on_redacted_account"],
            "broker_true_costs": COSTS,
            "profiles": ["config/profiles/operator_profile.yaml", "config/profiles/redacted_account.yaml"],
        },
    }
    json.dump({"rollup": roll, "symbols": rec}, open(os.path.join(OUT, "B5_TRADEABILITY_V1.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in roll.items() if k not in ("gtos_configured_symbols", "sources")}, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""SLEEVE PULL (sub_mid_dn_revert) - resolver + broker verification. STRICTLY READ-ONLY.

MT5 calls: initialize / account_info / positions_get / terminal_info / shutdown.
There is NO order_send, order_check or order_calc_* in this file. The placement proof is
`activation_token.authorize_broker_mutation`, the pure decision function behind
`RealMT5.order_send`'s choke point: it classifies and answers allow/deny WITHOUT transmitting.

It resolves the sleeve set through the ENGINE'S OWN path -- active_specs(tags, include-flags)
intersected with effective_registry (book_engine._active_sleeve_names, the DF-1 filter) -- for
(a) the tags the running worker actually carries, and (b) the proposed tags. Never by eye.
"""
import os, sys, json, re, datetime as dt

REPO = r"C:\Users\MSI\Documents\ai-trading-agent"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"host-local\smdr_20260811"
PHASE = sys.argv[2] if len(sys.argv) > 2 else "PRE"
os.makedirs(OUT, exist_ok=True)
os.chdir(REPO); sys.path.insert(0, REPO)

import yaml
import MetaTrader5 as mt5
from src.utils.config import apply_profile_overrides
from src.components.ultimate_book.bridge import config_bool_value
from src.components.ultimate_book.sleeves.registry import active_specs
from src.components.ultimate_book.admission import effective_registry
from src.safety.activation_token import (
    authorize_broker_mutation, account_digest, config_digest_for, token_dir,
    strict_positions_provider, PositionsUnavailable,
)

PROPOSED = ["crypto", "energy_agri", "sub_xvol_pullback"]
PULLED = "sub_mid_dn_revert"
ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", "operator_profile", "operator_profile"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", "redacted_account", "redacted_account_live_bee34003"),
]

def live_argv():
    """The tags each RUNNING worker actually carries -- the ground truth, not the file."""
    import subprocess
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object { $_.CommandLine -like '*run_book*' } | "
          "ForEach-Object { $_.ProcessId.ToString() + '|' + $_.CommandLine }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True)
    rows = []
    for line in r.stdout.splitlines():
        if "|" not in line: continue
        pid, cmd = line.split("|", 1)
        ns = re.search(r"--namespace\s+(\S+)", cmd)
        tg = re.search(r"--tags\s+(\S+)", cmd)
        fl = re.search(r"--spread-geometry-floor\s+(\S+)", cmd)
        fr = re.search(r"--frontier-exits\s+(\S+)", cmd)
        rows.append({"pid": int(pid.strip()), "namespace": ns.group(1) if ns else None,
                     "tags_raw": tg.group(1) if tg else None,
                     "tags_present": bool(tg),
                     "spread_geometry_floor": fl.group(1) if fl else None,
                     "frontier_exits": fr.group(1) if fr else None,
                     "cmdline": cmd.strip()})
    return rows

def resolve(rt, tags):
    """book_engine._generate_intents' resolution, reproduced exactly:
    active_specs(tags, include-flags) filtered by `spec.tag not in _active_sleeve_names()`."""
    def cb(key, dflt):
        return config_bool_value(rt.get(key, dflt), dflt)
    inc3 = cb("ultimate_book_include_clean3", True)
    inc4 = cb("ultimate_book_include_clean4", False)
    inc_c = cb("ultimate_book_include_candidate_book", False)
    inc_m = cb("ultimate_book_include_market_expansion_book", False)
    cand = rt.get("ultimate_book_candidate_book_sleeves") or None
    expa = rt.get("ultimate_book_market_expansion_sleeves") or None
    active_names = set(effective_registry(
        include_clean3=inc3, include_clean4=inc4, include_candidate_book=inc_c,
        candidate_book_sleeves=cand, include_market_expansion_book=inc_m,
        market_expansion_sleeves=expa).keys())
    specs = active_specs(tags, include_candidate_book=inc_c, candidate_book_sleeves=cand,
                         include_market_expansion_book=inc_m, market_expansion_sleeves=expa)
    generating = sorted({s.tag for s in specs if s.tag in active_names})
    slots = sum(len(getattr(s, "symbols", ()) or ()) for s in specs if s.tag in active_names)
    return {"tags_requested": (list(tags) if tags is not None else None),
            "tags_is_none_FAIL_OPEN": tags is None,
            "generating_sleeves": generating, "generating_count": len(generating),
            "symbol_slots": slots,
            "dropped_unknown_tags": (sorted(set(tags) - {s.tag for s in specs})
                                     if tags is not None else []),
            "include_flags": {"clean3": inc3, "clean4": inc4, "candidate_book": inc_c,
                              "market_expansion": inc_m},
            "effective_registry_size": len(active_names)}

base = yaml.safe_load(open(os.path.join(REPO, "config", "agent_config.yaml"), encoding="utf-8"))
argv_rows = live_argv()
res = {"schema": "gtos.sleeve_pull.sub_mid_dn_revert.verify.v1", "phase": PHASE,
       "as_of_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "pulled_sleeve": PULLED, "proposed_tags": PROPOSED,
       "token_dir": str(token_dir()), "live_argv": argv_rows, "accounts": {}}

for label, term, profile, ns in ACCOUNTS:
    merged = apply_profile_overrides(dict(base), profile)
    rt = merged.get("gtos_vnext_runtime", merged)
    digest = config_digest_for("config/agent_config.yaml", profile, repo_root=REPO)
    mine = [r for r in argv_rows if r["namespace"] == ns]
    live_tags = None
    if mine and mine[0]["tags_present"] and mine[0]["tags_raw"]:
        live_tags = [t.strip() for t in mine[0]["tags_raw"].split(",") if t.strip()]
    row = {"profile": profile, "namespace": ns, "config_digest_sha256": digest,
           "worker_pids": [r["pid"] for r in mine],
           "live_tags_from_argv": live_tags,
           "gates": {k: rt.get(k) for k in ("ultimate_book_apply_to_execution",
                                            "ultimate_book_live_activation_allowed",
                                            "ultimate_book_live_broker_authority",
                                            "ultimate_book_include_clean3")},
           "resolved_LIVE_ARGV": resolve(rt, live_tags),
           "resolved_PROPOSED": resolve(rt, PROPOSED)}
    row["pulled_sleeve_generates_under_live_argv"] = (
        PULLED in row["resolved_LIVE_ARGV"]["generating_sleeves"])
    row["pulled_sleeve_generates_under_proposed"] = (
        PULLED in row["resolved_PROPOSED"]["generating_sleeves"])

    if not mt5.initialize(path=term):
        row["broker_error"] = str(mt5.last_error()); res["accounts"][label] = row; continue
    ai, ti = mt5.account_info(), mt5.terminal_info()
    ld = account_digest(getattr(ai, "login", None)) if ai is not None else None
    positions = mt5.positions_get()
    pos_rows = []
    for p in (positions or ()):
        pos_rows.append({"ticket": getattr(p, "ticket", None), "symbol": getattr(p, "symbol", None),
                         "volume": getattr(p, "volume", None), "comment": getattr(p, "comment", None),
                         "magic": getattr(p, "magic", None), "profit": getattr(p, "profit", None)})
    row["broker"] = {"server": getattr(ai, "server", None),
                     "login_sha256_redacted": "redacted:" + (ld or "")[:12],
                     "trade_allowed": getattr(ai, "trade_allowed", None),
                     "terminal_connected": getattr(ti, "connected", None),
                     "balance": getattr(ai, "balance", None), "equity": getattr(ai, "equity", None),
                     "open_positions": (len(positions) if positions is not None else None),
                     "positions": pos_rows}
    row["open_positions_naming_pulled_sleeve"] = [
        p for p in pos_rows if PULLED in str(p.get("comment") or "")]

    @strict_positions_provider
    def provider(symbol, _p=positions):
        if _p is None: raise PositionsUnavailable("positions_get returned None")
        return _p

    req = {"action": int(mt5.TRADE_ACTION_DEAL), "symbol": "XAUUSD",
           "type": int(mt5.ORDER_TYPE_BUY), "volume": 0.01,
           "comment": "GTOS_SLEEVE_PULL_DRILL_NO_TRANSMIT"}
    d = authorize_broker_mutation(req, account_login_sha256=ld, positions_provider=provider,
                                  namespace=ns, config_digest_sha256=digest, audit=True)
    row["placement_drill"] = {"transmitted_to_broker": False, "allowed": bool(d.allowed),
                              "reason": d.reason, "risk_direction": d.risk_direction,
                              "classification": d.classification,
                              "positions_verified": d.positions_verified}
    close = dict(req); close.update({"type": int(mt5.ORDER_TYPE_SELL), "position": 1})
    d2 = authorize_broker_mutation(close, account_login_sha256=ld, positions_provider=provider,
                                   namespace=ns, config_digest_sha256=digest, audit=True)
    row["reducing_control"] = {"allowed": bool(d2.allowed), "reason": d2.reason,
                               "risk_direction": d2.risk_direction}
    d3 = authorize_broker_mutation(req, account_login_sha256=ld, positions_provider=provider,
                                   namespace=ns, config_digest_sha256="0" * 64, audit=False)
    row["stale_digest_negative_control"] = {"allowed": bool(d3.allowed), "reason": d3.reason}
    mt5.shutdown()
    res["accounts"][label] = row

p = os.path.join(OUT, f"SLEEVE_PULL_VERIFY_{PHASE}.json")
json.dump(res, open(p, "w", encoding="utf-8"), indent=1)
print("WROTE", p)
for k, v in res["accounts"].items():
    print(f"\n== {k} [{v['namespace']}] digest={str(v['config_digest_sha256'])[:12]} pids={v['worker_pids']}")
    print(f"   live argv tags   : {v['live_tags_from_argv']}")
    print(f"   resolved LIVE    : {v['resolved_LIVE_ARGV']['generating_sleeves']} "
          f"(slots={v['resolved_LIVE_ARGV']['symbol_slots']}, dropped={v['resolved_LIVE_ARGV']['dropped_unknown_tags']})")
    print(f"   resolved PROPOSED: {v['resolved_PROPOSED']['generating_sleeves']} "
          f"(slots={v['resolved_PROPOSED']['symbol_slots']}, dropped={v['resolved_PROPOSED']['dropped_unknown_tags']})")
    print(f"   {PULLED}: live={v['pulled_sleeve_generates_under_live_argv']} proposed={v['pulled_sleeve_generates_under_proposed']}")
    print(f"   gates={v['gates']}")
    print(f"   broker={ {kk: vv for kk, vv in v.get('broker', {}).items() if kk != 'positions'} }")
    print(f"   positions naming pulled sleeve: {v.get('open_positions_naming_pulled_sleeve')}")
    print(f"   DRILL increasing allowed={v['placement_drill']['allowed']} reason={v['placement_drill']['reason']} dir={v['placement_drill']['risk_direction']}")
    print(f"   reducing control allowed={v['reducing_control']['allowed']} reason={v['reducing_control']['reason']}")
    print(f"   stale-digest control allowed={v['stale_digest_negative_control']['allowed']} reason={v['stale_digest_negative_control']['reason']}")

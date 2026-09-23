#!/usr/bin/env python3
"""Session AZ (B1855) — measure the carry rather than reason about it.

Three things, all against a materialised reconstruction of the host's own tree:

  --stage states     every one of the 2^4 subsets of {execution_packets, order_router,
                     book_owner, run_book}: does the tree import, does the owner construct,
                     does a PLACEMENT succeed, does the ADOPT path survive? The state space
                     deliberately includes the placement probe, because Session AC's own
                     lesson is that a probe narrower than the claim finds half the fatal
                     states -- and this carry's characteristic failure (`order_router`
                     without `execution_packets`) is invisible to import AND to construct,
                     landing only when a trade tries to place.

  --stage blast      the exit profile, the adopt instrumentation and the full placement dict
                     for EVERY sleeve the host's registry resolves, before and after the
                     carry, with no frontier selection. This is what says "nothing armed
                     moves"; AQ's time-stop repair rides `execution_packets.py` and must be
                     priced on THIS host rather than inherited.

  --stage identity   the activation itself: `mx_btcusd @ target_5R` through the real
                     `build_book_trade_params` on the carried tree, and the adopt-rehydration
                     path through the HOST's own `ExecutionEngine`.

Writes `AZ_CARRY_PROBE_V1.json`. Never touches a broker: `MetaTrader5` is shadowed with an
empty module in every child, exactly as `verify_carry.py` does.
"""

from __future__ import annotations

import argparse
import itertools
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = HERE.parents[5]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
LINEAGE = "redacted_host"
OUT = HERE / "AZ_CARRY_PROBE_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"

#: The host's bytes for the paths two earlier carries already landed (verified at after-hashes
#: on the running host 2026-07-30, `phase8/receipts/VPS_CEREMONY_COMPLETED.md`).
HOST_OVERLAY = {
    "src/utils/broker_clock.py": "phase5/activation_carry/files/broker_clock.py",
    "src/components/ultimate_book/governor_state.py": "phase5/activation_carry/files/governor_state.py",
    "src/components/ultimate_book/book_engine.py": "phase5/activation_carry/files/book_engine.py",
    "src/components/execution.py": "phase5/activation_carry/files/execution.py",
    "src/components/ultimate_book/book_owner.py": "phase4/packet_carry/files/book_owner.py",
    "src/components/ultimate_book/runtime_learning_packet.py": "phase4/packet_carry/files/runtime_learning_packet.py",
    "src/components/ultimate_book/packet_economics.py": "phase4/packet_carry/files/packet_economics.py",
    "src/components/ultimate_book/packet_guard.py": "phase4/packet_carry/files/packet_guard.py",
}
#: The Stage-0 token carry's five files, at the wave-3 integration state — the primary
#: `accepted_before_state` in MANIFEST.json.
HOST_STAGE0_COMMIT = "dcb54cbab"
HOST_STAGE0 = ["run_book.py", "src/safety/activation_token.py", "src/mt5/mt5_real.py",
               "src/mt5/mt5_interface.py", "scripts/gtos_activation_token.py",
               "src/safety/notification_authorization.py"]

#: name -> (destination in the tree, payload in this package)
CARRY = {
    "EP": ("src/components/ultimate_book/execution_packets.py", "files/execution_packets.py"),
    "OR": ("src/components/ultimate_book/order_router.py", "files/order_router.py"),
    "BO": ("src/components/ultimate_book/book_owner.py", "files/book_owner.py"),
    "RB": ("run_book.py", "files/run_book.py"),
}


def materialise(dest: Path, applied: tuple[str, ...]) -> None:
    """The host tree, with `applied` of the carry landed on top."""
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(f"git archive {LINEAGE} src scripts config run_book.py | tar -x -C {dest}",
                   shell=True, cwd=REPO, check=True)
    for repo_path, src in HOST_OVERLAY.items():
        shutil.copyfile(AUDIT / src, dest / repo_path)
    for repo_path in HOST_STAGE0:
        blob = subprocess.run(["git", "show", f"{HOST_STAGE0_COMMIT}:{repo_path}"],
                              cwd=REPO, capture_output=True, check=True).stdout
        (dest / repo_path).write_bytes(blob)
    for key in applied:
        repo_path, payload = CARRY[key]
        shutil.copyfile(PKG / payload, dest / repo_path)


PROBE = r'''
import json, sys, types, tempfile, traceback
ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
out = {}

def step(name, fn):
    try:
        out[name] = {"ok": True, "value": fn()}
    except BaseException as exc:
        out[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

# ---- 1. every module run_book.py imports at module top ----
def _imports():
    import importlib
    for dotted in ["src.security", "src.utils.config", "src.utils.broker_profile",
                   "src.mt5.mt5_real", "src.components.ultimate_book.book_owner",
                   "src.components.ultimate_book.bridge",
                   "src.components.ultimate_book.symbol_map",
                   "src.components.ultimate_book.launcher"]:
        importlib.import_module(dotted)
    return "all 8 module-top imports resolve"
step("imports", _imports)

# ---- 1b. EVERY import run_book.py performs, including the DEFERRED ones inside main() ----
# A module-top probe is blind to exactly the failure this carry introduces: the carried
# `run_book.py` imports `parse_frontier_exits` from inside `main()`, unconditionally, so a tree
# with run_book carried and execution_packets not carried imports perfectly and then dies at
# startup on BOTH namespaces. Session AC's grid found half its fatal states by carrying the
# probe past import; this one is the same lesson one level deeper, and it is derived from the
# tree's OWN run_book.py by AST so it cannot drift away from what the file does.
def _deferred_imports():
    import ast, importlib, os
    src = open(os.path.join(ROOT, "run_book.py"), encoding="utf-8").read()
    dotted = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src."):
            dotted.append((node.module, [a.name for a in node.names]))
        elif isinstance(node, ast.Import):
            dotted += [(a.name, []) for a in node.names if a.name.startswith("src.")]
    for mod, names in dotted:
        m = importlib.import_module(mod)
        for n in names:
            if hasattr(m, n):
                continue
            # `from src.utils import notification_queue` binds a SUBMODULE, which is not an
            # attribute of the package until it is imported. A `hasattr`-only check reported
            # every state fatal, including the fully carried one -- the wipeout shape AU filed.
            try:
                importlib.import_module(f"{mod}.{n}")
            except ImportError:
                raise ImportError(f"cannot import name {n!r} from {mod!r}") from None
    return f"{len(dotted)} `src.` imports in run_book.py (module-top AND deferred) all resolve"
step("run_book_all_imports", _deferred_imports)

class _StubMT5:
    _mt5 = None
    def get_broker_offset_seconds(self): return 3 * 3600

CFG = {"gtos_vnext_runtime": {"prop_safe_selector_daily_reset_timezone": "Europe/Prague"}}

# ---- 2. construct the owner the way run_book.py does, with and without a selection ----
def _construct_default():
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    UltimateBookOwner(CFG, _StubMT5(), tempfile.mkdtemp(prefix="az_"), namespace="az_probe")
    return "UltimateBookOwner(...) constructs"
step("construct_default", _construct_default)

def _construct_frontier():
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    from src.components.ultimate_book.execution_packets import parse_frontier_exits
    sel = parse_frontier_exits("mx_btcusd_d1_donchian_20_breakout")
    UltimateBookOwner(CFG, _StubMT5(), tempfile.mkdtemp(prefix="az_"), namespace="az_probe",
                      frontier_exits=sel)
    return "UltimateBookOwner(..., frontier_exits=(mx_btcusd,)) constructs"
step("construct_frontier", _construct_frontier)

# ---- 3. THE PLACEMENT PATH, through the router the owner actually holds ----
def _sized(sleeve):
    from src.components.ultimate_book.admission import SizedUnit, TradeIntent
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=10.0, target_dist=20.0)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": 3000.0, "risk_distance": 10.0, "stop_loss": 2990.0,
            "take_profit_1": 3020.0}
    return su, intent, geom, acct

def _place_default():
    """What a PLACEMENT does with no selection -- the state an un-activated host is in."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    o = UltimateBookOwner(CFG, _StubMT5(), tempfile.mkdtemp(prefix="az_"), namespace="az_probe")
    su, intent, geom, acct = _sized("crypto")
    import src.components.ultimate_book.execution_packets as EP
    tp = EP.build_book_trade_params(su, intent, geom, acct,
                                    profile_namespace="operator_profile",
                                    **({"frontier_exits": o.router.frontier_exits}
                                       if hasattr(o.router, "frontier_exits") else {}))
    return {"take_profit_1": tp["take_profit_1"],
            "final_target_r": tp["gtos_vnext_dynamic_final_target_r"]}
step("place_default", _place_default)

def _place_via_router():
    """The router's own path -- this is the one that dies when OR lands without EP."""
    from src.components.ultimate_book.order_router import UltimateBookOrderRouter
    import src.components.ultimate_book.execution_packets as EP
    su, intent, geom, acct = _sized("crypto")
    r = UltimateBookOrderRouter(CFG, namespace="operator_profile")
    tp = EP.build_book_trade_params(su, intent, geom, acct,
                                    profile_namespace=r.namespace,
                                    **({"frontier_exits": r.frontier_exits}
                                       if hasattr(r, "frontier_exits") else {}))
    return {"take_profit_1": tp["take_profit_1"]}
step("place_via_router", _place_via_router)

def _place_through_router_place():
    """THE REAL CONSEQUENCE, not the raw one.

    `UltimateBookOrderRouter.place` wraps its whole body in `except Exception` and returns
    `{"placed": False, "reason": f"router_exception:{e!r}"}` -- *"the book NEVER breaks the
    live path"*. So an `order_router` carried without `execution_packets` does NOT crash the
    book: it returns a soft refusal on every single placement while the process stays up, the
    heartbeat stays healthy, and exit management keeps running. That is a SILENT TOTAL
    PLACEMENT OUTAGE, which is a different (and in one way worse) failure than a crash, and
    the first version of this probe called `build_book_trade_params` directly and therefore
    measured the exception rather than the outcome.
    """
    from src.components.ultimate_book.order_router import UltimateBookOrderRouter
    su, intent, geom, acct = _sized("crypto")
    class _Tick:
        bid = 2999.0; ask = 3001.0
    class _Engine:
        _last_open_trade_block_reason = None
        _last_order_send_diagnostic = None
        def open_trade(self, tp, bal, risk_pct_override=None, trigger=None):
            return type("TS", (), {"ticket": 4242})()
    r = UltimateBookOrderRouter(CFG, namespace="operator_profile")
    out = r.place(_Engine(), su, intent, _Tick(), acct, 100000.0)
    return {"placed": bool(out.get("placed")), "reason": str(out.get("reason"))[:140]}
step("place_through_router_place", _place_through_router_place)

# ---- 4. THE ADOPT PATH, on this tree's own ExecutionEngine ----
def _adopt(sleeve, selection=()):
    import src.components.ultimate_book.execution_packets as EP
    from src.components.execution import ExecutionEngine
    kw = {"frontier_exits": selection} if selection else {}
    try:
        inst = EP.native_policy_instrumentation(sleeve, **kw)
    except TypeError as exc:
        raise TypeError(f"native_policy_instrumentation rejected the selection: {exc}") from None
    rec = {"instrumentation": inst, "execution": {"ticket": 1}, "sleeve": sleeve,
           "symbol": "XAUUSD", "reconstructed_from_sleeve_identity": True}
    # The REAL TradeState, not a stub: this probe exists to establish that the host's own
    # rehydration reaches its end on a `time_stop` record, and a stub thin enough to hide a
    # KeyError behind an AttributeError would answer a different question.
    from src.components.execution import TradeState
    eng = ExecutionEngine.__new__(ExecutionEngine)
    eng.config = {}
    eng.active_trade = TradeState(
        ticket=1, direction="LONG", entry_price=3000.0, stop_loss=2990.0,
        take_profit_1=3020.0, take_profit_2=0.0, take_profit_3=0.0,
        initial_volume=0.10, current_volume=0.10, sl_distance=10.0)
    eng.active_trade.trade_id = "az_probe"
    eng.active_trade.symbol = "XAUUSD"
    eng.active_trade.entry_time = "2026-06-15T00:00:00+00:00"
    ok = ExecutionEngine.hydrate_vnext_dynamic_policy_from_record(eng, rec, modify_broker_tp=False)
    t = eng.active_trade
    return {"hydrated": bool(ok),
            "policy": inst.get("gtos_vnext_dynamic_policy_selected"),
            "be_trigger_r": getattr(t, "gtos_vnext_dynamic_be_trigger_r", None),
            "final_target_r": getattr(t, "gtos_vnext_dynamic_final_target_r", None),
            "take_profit_1": getattr(t, "take_profit_1", None),
            "time_stop_bars": getattr(t, "gtos_vnext_dynamic_time_stop_bars", None)}

step("adopt_time_stop_sleeve", lambda: _adopt("crypto"))
step("adopt_mx_btcusd_default", lambda: _adopt(BTC := "mx_btcusd_d1_donchian_20_breakout"))
step("adopt_mx_btcusd_frontier",
     lambda: _adopt("mx_btcusd_d1_donchian_20_breakout",
                    ("mx_btcusd_d1_donchian_20_breakout",)))

print("@@AZJSON@@" + json.dumps(out))
'''

BLAST = r'''
import json, sys, types
ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
import src.components.ultimate_book.execution_packets as EP
from src.components.ultimate_book.admission import (
    SizedUnit, TradeIntent, effective_registry, resolve_market_expansion_sleeves)

mx, err = resolve_market_expansion_sleeves(policy="positive_weighted12_after_swap",
                                           explicit_sleeves=[])
assert not err, err
reg = effective_registry(include_candidate_book=True, include_clean3=True,
                         include_market_expansion_book=True, market_expansion_sleeves=mx)

_WALL = ("decision_time_utc", "asof_utc", "gtos_vnext_prop_firm_headroom_snapshot_v4",
         "gtos_vnext_dynamic_target_stop_geometry_v4")

def place(sleeve):
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=10.0, target_dist=20.0)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": 3000.0, "risk_distance": 10.0, "stop_loss": 2990.0,
            "take_profit_1": 3020.0}
    tp = EP.build_book_trade_params(su, intent, geom, acct,
                                    profile_namespace="operator_profile")
    return {k: v for k, v in tp.items() if k not in _WALL}

out = {"registry_size": len(reg), "market_expansion_allowlist": list(mx), "sleeves": {}}
for sleeve in sorted(set(list(reg) + list(EP.SLEEVE_EXIT_PROFILES))):
    row = {"in_registry": sleeve in reg,
           "profile": {k: v for k, v in EP.SLEEVE_EXIT_PROFILES.get(sleeve, {}).items()},
           "instrumentation": EP.native_policy_instrumentation(sleeve)}
    try:
        row["placement"] = place(sleeve)
    except BaseException as exc:
        row["placement"] = {"__error__": f"{type(exc).__name__}: {exc}"}
    out["sleeves"][sleeve] = row
print("@@AZJSON@@" + json.dumps(out, default=str))
'''


def run(script: str, root: Path) -> dict:
    r = subprocess.run([sys.executable, "-c", script, str(root)],
                       capture_output=True, text=True, cwd=root)
    for line in r.stdout.splitlines():
        if line.startswith("@@AZJSON@@"):
            return json.loads(line[len("@@AZJSON@@"):])
    return {"__fatal__": {"ok": False, "error": (r.stderr or r.stdout).strip()[-1200:]}}


def stage_states(tmp: Path) -> dict:
    keys = list(CARRY)
    rows = []
    for n in range(len(keys) + 1):
        for applied in itertools.combinations(keys, n):
            root = tmp / ("state_" + ("_".join(applied) or "none"))
            materialise(root, applied)
            res = run(PROBE, root)
            rows.append({"applied": list(applied), "n_applied": len(applied), "probe": res})
            shutil.rmtree(root, ignore_errors=True)
    return {"n_states": len(rows), "states": rows}


def stage_blast(tmp: Path) -> dict:
    before_root, after_root = tmp / "blast_before", tmp / "blast_after"
    materialise(before_root, ())
    materialise(after_root, tuple(CARRY))
    before, after = run(BLAST, before_root), run(BLAST, after_root)
    moved, unchanged = {}, []
    for sleeve, arow in (after.get("sleeves") or {}).items():
        brow = (before.get("sleeves") or {}).get(sleeve)
        if brow is None:
            moved[sleeve] = {"reason": "sleeve absent before the carry"}
        elif brow != arow:
            deltas = {}
            for section in ("profile", "instrumentation", "placement"):
                b, a = brow.get(section) or {}, arow.get(section) or {}
                d = {k: {"before": b.get(k), "after": a.get(k)}
                     for k in sorted(set(b) | set(a)) if b.get(k) != a.get(k)}
                if d:
                    deltas[section] = d
            moved[sleeve] = deltas
        else:
            unchanged.append(sleeve)
    return {"registry_size_before": before.get("registry_size"),
            "registry_size_after": after.get("registry_size"),
            "n_sleeves_compared": len(after.get("sleeves") or {}),
            "n_unchanged": len(unchanged), "unchanged": sorted(unchanged), "moved": moved}


def stage_identity(tmp: Path) -> dict:
    root = tmp / "identity"
    materialise(root, tuple(CARRY))
    script = r'''
import json, sys, types
ROOT = sys.argv[1]; sys.path.insert(0, ROOT)
sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
import src.components.ultimate_book.execution_packets as EP
from src.components.ultimate_book.admission import SizedUnit, TradeIntent
from src.components.ultimate_book.book_owner import UltimateBookOwner
BTC = "mx_btcusd_d1_donchian_20_breakout"
ENTRY, STOP = 3000.0, 10.0
def place(sel):
    su = SizedUnit(cluster="book", sleeve_members=[BTC], n_trades=1, confidence=0.025,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    it = TradeIntent(sleeve=BTC, symbol="BTCUSD", direction=1, decision_day="2026-06-15",
                     stop_dist=STOP, target_dist=2.0 * STOP)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": ENTRY, "risk_distance": STOP, "stop_loss": ENTRY - STOP,
            "take_profit_1": ENTRY + 2.0 * STOP}
    return EP.build_book_trade_params(su, it, geom, acct,
                                      profile_namespace="operator_profile",
                                      frontier_exits=sel)
off, on = place(()), place((BTC,))
res = {
  "committed": {"final_target_r": off["gtos_vnext_dynamic_final_target_r"],
                "take_profit_1": off["take_profit_1"], "stop_loss": off["stop_loss"],
                "time_stop_bars": off.get("gtos_vnext_dynamic_time_stop_bars"),
                "exit_contract": off["gtos_vnext_source_event_details"].get("exit_contract")},
  "frontier":  {"final_target_r": on["gtos_vnext_dynamic_final_target_r"],
                "take_profit_1": on["take_profit_1"], "stop_loss": on["stop_loss"],
                "time_stop_bars": on.get("gtos_vnext_dynamic_time_stop_bars"),
                "exit_contract": on["gtos_vnext_source_event_details"].get("exit_contract")},
  "risk_unit_unmoved": off["stop_loss"] == on["stop_loss"],
  "tp_is_entry_plus_5R": abs(on["take_profit_1"] - (ENTRY + 5.0 * STOP)) < 1e-9,
  "committed_tp_is_entry_plus_2R": abs(off["take_profit_1"] - (ENTRY + 2.0 * STOP)) < 1e-9,
  "source_event_hash_moves": off["gtos_vnext_source_event_hash"] != on["gtos_vnext_source_event_hash"],
  "time_stop_is_80_D1_bars": off.get("gtos_vnext_dynamic_time_stop_bars") == EP.time_stop_m15(80, "D1"),
  "only_the_named_sleeve_moves": all(
      EP.resolve_exit_profile(s, frontier_exits=(BTC,)) is EP.SLEEVE_EXIT_PROFILES[s]
      for s in EP.SLEEVE_EXIT_PROFILES if s != BTC),
  "banner_renders_for_every_wired_sleeve": {
      s: EP.describe_frontier_contract(s) for s in sorted(EP.FRONTIER_EXIT_OVERRIDES)},
}
# and the owner really carries the selection to the router it holds
o = UltimateBookOwner({"gtos_vnext_runtime": {}}, type("M", (), {"_mt5": None,
    "get_broker_offset_seconds": lambda self: 10800})(), ROOT, namespace="az",
    frontier_exits=(BTC,))
res["owner_router_selection"] = list(o.router.frontier_exits)
res["owner_field"] = list(o._frontier_exits)
print("@@AZJSON@@" + json.dumps(res, default=str))
'''
    return run(script, root)


#: Mainline's replacement for the host's `selected_policy == "time_stop"` rehydration branch.
#: Applied here as an anchored edit purely as a CONTROL: the manifest declares `execution.py`
#: not-carried, and a not-carried decision that rests on reading two files deserves the same
#: standard of proof as a carried one.
AS_HUNK_BEFORE = '''        if selected_policy == "time_stop":
            # Targetless time-stop records intentionally carry no trigger leg and
            # may have final_target_r=0 when broker TP is disabled. Rehydration
            # must still restore the policy clock so adopted positions cannot
            # degrade into passive monitoring after a restart.
            trigger_r = 0.0
            final_target_r = float(params.get("final_target_r") or 0.0)
        else:
            trigger_r = float(params["trigger_r"])
            final_target_r = float(params["final_target_r"])
        trade.gtos_vnext_dynamic_be_trigger_r = trigger_r
        trade.gtos_vnext_dynamic_final_target_r = final_target_r
'''
AS_HUNK_AFTER = '''        trigger_r = params.get("trigger_r")
        if trigger_r is None:
            trigger_r = payload.get("gtos_vnext_dynamic_be_trigger_r")
        if trigger_r in (None, ""):
            trigger_r = params.get("final_target_r") or 0.0
        trade.gtos_vnext_dynamic_be_trigger_r = float(trigger_r)
        trade.gtos_vnext_dynamic_final_target_r = float(params["final_target_r"])
'''
AS_TP1_BEFORE = '''        trade.take_profit_1 = (
            0.0
            if selected_policy == "time_stop"
            else trade.gtos_vnext_dynamic_be_trigger_price
        )
'''
AS_TP1_AFTER = '''        trade.take_profit_1 = (
            0.0
            if no_broker_tp and selected_policy == "time_stop"
            else trade.gtos_vnext_dynamic_be_trigger_price
        )
'''


def stage_as_control(tmp: Path) -> dict:
    """What Session AS's mainline `execution.py` hunk would DO on this host, if carried."""
    root = tmp / "as_control"
    materialise(root, tuple(CARRY))
    baseline = run(PROBE, root)
    target = root / "src/components/execution.py"
    text = target.read_text(encoding="utf-8")
    counts = {"rehydration_branch": text.count(AS_HUNK_BEFORE),
              "take_profit_1_branch": text.count(AS_TP1_BEFORE)}
    if counts["rehydration_branch"] != 1 or counts["take_profit_1_branch"] != 1:
        return {"__error__": "the host's execution.py no longer carries the branches this "
                             "control replaces", "counts": counts}
    target.write_text(text.replace(AS_HUNK_BEFORE, AS_HUNK_AFTER)
                          .replace(AS_TP1_BEFORE, AS_TP1_AFTER), encoding="utf-8")
    after = run(PROBE, root)
    keys = ["adopt_time_stop_sleeve", "adopt_mx_btcusd_default", "adopt_mx_btcusd_frontier"]
    deltas = {}
    for k in keys:
        b, a = baseline.get(k, {}), after.get(k, {})
        if b != a:
            deltas[k] = {"host_today": b, "with_AS_hunk": a}
    return {
        "claim": "Session AS's KeyError('trigger_r') defect is UNREACHABLE on this host, and "
                 "carrying the mainline hunk would change live adopt behaviour instead of "
                 "fixing anything.",
        "host_branch_present": counts,
        "lineage_commit_that_added_it": "b36d9ab92 (ancestor of redacted_host, NOT of main)",
        "adopt_probes_that_move_if_the_hunk_is_carried": deltas,
        "n_moved": len(deltas),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["states", "blast", "identity", "as-control", "all"],
                    default="all")
    args = ap.parse_args()
    # MERGE rather than clobber. A `--stage states` re-run used to write a receipt containing
    # only `states`, silently deleting `blast_radius` and `as_fix_control` -- and the tests that
    # read them then failed for a reason that had nothing to do with what they assert. A partial
    # run must not be able to publish an artifact that reads as a complete one.
    out: dict = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
    out.update({"schema": "gtos.phase13.az_carry_probe.v1", "session": "AZ",
                "host_base": LINEAGE, "stage0_state": HOST_STAGE0_COMMIT})
    with tempfile.TemporaryDirectory(prefix="az_probe_") as td:
        tmp = Path(td)
        if args.stage in ("states", "all"):
            out["states"] = stage_states(tmp)
        if args.stage in ("blast", "all"):
            out["blast_radius"] = stage_blast(tmp)
        if args.stage in ("identity", "all"):
            out["identity"] = stage_identity(tmp)
        if args.stage in ("as-control", "all"):
            out["as_fix_control"] = stage_as_control(tmp)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

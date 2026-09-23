#!/usr/bin/env python3
"""gtos_mt5_mcp_readonly.py — the READ-ONLY MT5 tool contract, prototyped against exported state.

This is the Stage-1 half of the MT5-MCP design in
`docs/audits/fable5-vision-audit-20260725/phase13/MT5_MCP_INTEGRATION_DESIGN.md`: the exact tool
surface a GTOS-owned MCP server would expose, implemented against a **read-only VPS export** so the
contract can be exercised, tested and reviewed before anything is pointed at a terminal.

Two properties are structural rather than promised, and both are pinned by tests:

1. **There is no mutating code path.** The module imports no `MetaTrader5`, holds no connection, and
   the only backend implemented reads files. `call_tool` resolves names through an allow-list; a
   name outside it raises, and every known-mutating name raises a distinct, louder error so that a
   caller asking for `create_order` gets a refusal that names the reason rather than a generic
   "unknown tool".

2. **The refusal is on the SERVER side, not in a prompt.** The design doc's §5 argument in one
   sentence: a model instructed not to trade is a policy; a server with no order code is a
   mechanism, and only the second one survives a prompt injection carried in a symbol comment.

Why a GTOS-owned server at all, rather than the terminal's native MCP (build 6060+):
`RealMT5.order_send` (`src/mt5/mt5_real.py:475-497`) is GTOS's activation choke point, and it runs
**inside the GTOS Python process**. An order placed by the terminal's own AI never passes through
it, and neither does one placed by a third-party MCP server that imports `MetaTrader5` in its own
process. The activation token — the estate's primary brake since 2026-07-26 — is structurally blind
to both. A GTOS-owned read-only server is the only shape that adds oversight without adding a
second, unguarded order path. See the design doc §4.

    python3 scripts/gtos_mt5_mcp_readonly.py --export-root <export> --list
    python3 scripts/gtos_mt5_mcp_readonly.py --export-root <export> --call get_account \\
        --arg account=FTMO
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_sibling(name: str):
    """Import a module from `scripts/` by path. `scripts/` never goes on sys.path.

    `scripts/research/` is a REGULAR package and the repo root's `research/` is a NAMESPACE one, so
    a regular package wins regardless of sys.path order — putting `scripts/` on the path at all
    breaks `import research.operations...` process-wide. See the long note in
    `gtos_command_center.py`.
    """
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


cc = _load_sibling("gtos_command_center")
ACCOUNTS, Export, read_json = cc.ACCOUNTS, cc.Export, cc.read_json


class MutatingToolRefused(PermissionError):
    """Raised for any tool that would change broker state. Never caught inside this module."""


class UnknownTool(KeyError):
    pass


#: Names that exist in the third-party MT5 MCP servers and in the terminal's native surface. They
#: are enumerated HERE, refused explicitly, and never implemented — so a caller that asks for one
#: gets a refusal naming the reason, not a lookup failure it might retry under another spelling.
#:
#: Enumerating them is the point. A deny-list that only says "unknown tool" teaches a caller to go
#: looking for the right name; one that says "refused, and here is why" ends the conversation.
MUTATING_TOOLS = {
    "create_order": "place a market/limit/stop order",
    "order_send": "call the raw MT5 mutation primitive",
    "modify_order": "adjust a pending order",
    "close_position": "close a position in whole or in part",
    "cancel_order": "cancel a pending order",
    "modify_position": "move SL/TP on an open position",
    "position_modify": "move SL/TP on an open position",
    "order_check": "pre-validate a mutation (it does not mutate, but it exists only to serve one)",
}

_REFUSAL = (
    "REFUSED: {name} would {what}. This server is read-only by construction — it contains no "
    "order-sending code at all, so this is a missing mechanism and not a disabled feature. "
    "Broker mutation in GTOS has exactly one authorised path: the engine's own "
    "RealMT5.order_send, behind the activation token (src/safety/activation_token.py). An MCP "
    "server that could place orders would be a SECOND path outside that brake, which is the one "
    "thing the design forbids."
)


def _fmt_account(name):
    if name not in ACCOUNTS:
        raise ValueError(f"unknown account {name!r}; expected one of {list(ACCOUNTS)}")
    return name


# ---------------------------------------------------------------------------
# the read-only tool surface
# ---------------------------------------------------------------------------
def get_account(export: Export, account: str) -> dict:
    """Balance, equity, margin and the broker's own account identity."""
    info = export.account_info(_fmt_account(account))
    if info is None:
        return {"available": False, "reason": "no account_info in this export"}
    keep = ("login", "server", "company", "name", "currency", "balance", "equity", "profit",
            "margin", "margin_free", "margin_level", "leverage", "trade_allowed", "trade_expert")
    return {"available": True, "account": account, **{k: info.get(k) for k in keep}}


def get_terminal(export: Export, account: str) -> dict:
    """Terminal build, connection state and trade permission.

    `build` is on the read-only surface deliberately: it is the field that tells an operator whether
    the host has taken the update that adds a native, terminal-side AI order path (6060+). Nothing
    else in the estate watches it, and it cannot be prevented from changing — MT5's Live Update
    cannot be disabled.
    """
    info = export.terminal_info(_fmt_account(account))
    if info is None:
        return {"available": False, "reason": "no terminal_info in this export"}
    keep = ("build", "connected", "trade_allowed", "tradeapi_disabled", "dlls_allowed", "mqid",
            "ping_last", "maxbars", "path", "company", "name")
    return {"available": True, "account": account, **{k: info.get(k) for k in keep}}


def get_positions(export: Export, account: str) -> dict:
    """Open positions, with the fields an oversight reader needs and nothing more."""
    rows = export.positions(_fmt_account(account))
    keep = ("ticket", "symbol", "volume", "type", "price_open", "price_current", "sl", "tp",
            "profit", "swap", "magic", "comment", "time")
    return {"available": True, "account": account, "n": len(rows),
            "positions": [{k: r.get(k) for k in keep} for r in rows]}


def get_pending_orders(export: Export, account: str) -> dict:
    rows = export.pending(_fmt_account(account))
    keep = ("ticket", "symbol", "volume_current", "type", "price_open", "sl", "tp", "magic",
            "comment", "time_setup")
    return {"available": True, "account": account, "n": len(rows),
            "orders": [{k: r.get(k) for k in keep} for r in rows]}


def get_history_deals(export: Export, account: str, limit: int = 50) -> dict:
    """Most recent closed deals. `time` is a BROKER-CLOCK epoch — never read it as UTC."""
    rows = export.deals(_fmt_account(account))
    rows = sorted(rows, key=lambda r: r.get("time_msc") or r.get("time") or 0)
    keep = ("ticket", "order", "position_id", "time", "type", "entry", "symbol", "volume", "price",
            "commission", "swap", "profit", "fee", "magic", "comment")
    tail = rows[-int(limit):] if limit else rows
    return {"available": True, "account": account, "n_total": len(rows), "n_returned": len(tail),
            "time_field_semantics": "broker-clock epoch; convert with "
                                    "src.utils.broker_clock.broker_epoch_to_utc, never with "
                                    "utcfromtimestamp",
            "deals": [{k: r.get(k) for k in keep} for r in tail]}


def get_symbol_info(export: Export, account: str, symbol: str) -> dict:
    """Contract spec for one symbol. The two brokers disagree on 18 of 19 shared symbols."""
    _fmt_account(account)
    specs = read_json(export.path("09_mt5_api",
                                  f"{cc.EXPORT_KEY[account]}_symbol_specs_traded.json"))
    if not specs:
        return {"available": False, "reason": "no symbol specs in this export"}
    # The export writes a dict keyed by symbol; tolerate a list of rows too, because the two MT5
    # pull scripts in this estate do not agree on the shape and a reader that knows only one of
    # them reports a present symbol as absent.
    if isinstance(specs, dict) and symbol in specs:
        return {"available": True, "account": account, "symbol": symbol, "spec": specs[symbol]}
    rows = specs if isinstance(specs, list) else (specs.get("symbols") or [])
    for r in rows:
        if isinstance(r, dict) and str(r.get("name") or r.get("symbol")) == symbol:
            return {"available": True, "account": account, "symbol": symbol, "spec": r}
    known = sorted(specs) if isinstance(specs, dict) else []
    return {"available": False, "account": account, "symbol": symbol,
            "reason": "symbol not in this export's traded-symbol specs",
            "known_symbols": known[:40]}


def get_authority_state(export: Export) -> dict:
    """The gates, the effective sleeve set and the heartbeat — the oversight question, in one call.

    Not an MT5 primitive: this is the GTOS-specific tool that makes an MCP server worth having at
    all. An agent asking "is the book armed and what is it trading" should get one authoritative
    answer derived the way `gtos_command_center` derives it (union over a window, never a single
    launcher record), rather than assembling it from raw reads and re-inventing the trap.
    """
    rows = cc.read_jsonl(export.launcher_log())
    # `now=None` disables the cutoff, so the union spans the WHOLE log rather than a trailing
    # window. That is the right choice for an export-backed read — the export has no live clock,
    # and a window anchored on the reader's wall time would silently exclude everything when the
    # export is a few days old. The span is reported so the caller can see what it covers.
    by_ns = cc._armed_set_from_launcher(rows, 0.0, None)
    out = {"available": bool(rows), "union_basis": "the whole launcher log in this export",
           "per_account": {}}
    for ns, account in cc.NAMESPACE_ACCOUNT.items():
        blk = by_ns.get(ns) or {}
        bridge = None
        for r in reversed(rows):
            if r.get("namespace") == ns and r.get("action") == "cycle" and r.get("bridge"):
                bridge = r["bridge"]
                break
        out["per_account"][account] = {
            "namespace": ns,
            "effective_sleeves_union": blk.get("union_window"),
            "n_effective_sleeves": blk.get("n_union_window"),
            "union_is_complete": blk.get("union_is_complete"),
            "union_span_utc": [blk.get("first_cycle_utc"), blk.get("last_cycle_utc")],
            "last_cycle_utc": blk.get("last_cycle_utc"),
            "last_single_record_would_have_said": blk.get("last_record_tag_count"),
            "gates": None if bridge is None else {
                "enabled": bridge.get("enabled"),
                "apply_to_execution": bridge.get("apply_to_execution"),
                "live_activation_allowed": bridge.get("live_activation_allowed_by_config"),
                "live_broker_authority": bridge.get("live_broker_authority"),
                "profile": bridge.get("profile"),
            },
            "caveat": "the sleeve union is PRE-DF-1 and is a lower bound unless "
                      "union_is_complete is true; see gtos_command_center's module docstring",
        }
    return out


TOOLS = {
    "get_account": (get_account, "balance, equity, margin, and account identity"),
    "get_terminal": (get_terminal, "terminal build, connection and trade permission"),
    "get_positions": (get_positions, "open positions"),
    "get_pending_orders": (get_pending_orders, "pending orders"),
    "get_history_deals": (get_history_deals, "recent closed deals"),
    "get_symbol_info": (get_symbol_info, "contract spec for one symbol"),
    "get_authority_state": (get_authority_state, "gates, effective sleeve set and heartbeat"),
}


def call_tool(name: str, export: Export, **kwargs):
    """The single entry point. Allow-list first, explicit refusal second, dispatch last."""
    if name in MUTATING_TOOLS:
        raise MutatingToolRefused(_REFUSAL.format(name=name, what=MUTATING_TOOLS[name]))
    if name not in TOOLS:
        raise UnknownTool(
            f"{name!r} is not a tool on this server. Available: {sorted(TOOLS)}. "
            f"Refused by design: {sorted(MUTATING_TOOLS)}.")
    fn, _ = TOOLS[name]
    return fn(export, **kwargs)


def describe() -> dict:
    """The manifest an MCP client would receive at initialise."""
    return {
        "schema": "gtos.mt5_mcp.readonly_contract.v1",
        "server": "gtos-mt5-readonly",
        "transport_when_deployed": "stdio, launched by the client; no listening socket",
        "backend_in_this_prototype": "a read-only VPS export directory",
        "tools": [{"name": n, "description": d} for n, (_, d) in sorted(TOOLS.items())],
        "refused_by_design": [{"name": n, "reason": w} for n, w in sorted(MUTATING_TOOLS.items())],
        "guarantee": "this server contains no order-sending code. Broker mutation in GTOS has one "
                     "authorised path — RealMT5.order_send behind the activation token — and this "
                     "server is deliberately not a second one.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export-root", required=False, default=None)
    ap.add_argument("--list", action="store_true", help="print the tool manifest and exit")
    ap.add_argument("--call", default=None, help="tool name to invoke")
    ap.add_argument("--arg", action="append", default=[], metavar="K=V")
    args = ap.parse_args()

    if args.list or not args.call:
        print(json.dumps(describe(), indent=1))
        return 0

    kwargs = {}
    for item in args.arg:
        k, _, v = item.partition("=")
        kwargs[k] = int(v) if v.isdigit() else v
    export = Export(Path(args.export_root) if args.export_root else None)
    try:
        print(json.dumps(call_tool(args.call, export, **kwargs), indent=1, default=str))
    except MutatingToolRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (UnknownTool, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

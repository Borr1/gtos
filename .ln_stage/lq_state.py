#!/usr/bin/env python3
"""Session LQ read-only state fence: books, tokens, configs, gates, positions.

Places nothing, mutates nothing. Run before and after the restart; the two
outputs are the fence for the labelling-fix deployment.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TOKEN_DIR = pathlib.Path(r"host-local\.gtos\activation")
BOOKS = {
    "ftmo": {"terminal": r"C:\MT5\FTMO\terminal64.exe",
             "profile": "operator_profile", "namespace": "operator_profile"},
    "fn": {"terminal": r"C:\MT5\redacted_account\terminal64.exe",
           "profile": "redacted_account", "namespace": "redacted_account_live_bee34003"},
}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "state"
    print(f"===== LQ {label} @ {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")

    print("\n-- code bytes --")
    for rel in ("src/components/execution.py",
                "src/components/ultimate_book/book_owner.py",
                "config/agent_config.yaml",
                "config/profiles/redacted_account.yaml",
                "config/profiles/operator_profile.yaml"):
        p = REPO / rel
        mt = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")
        print(f"  {rel:<48} {sha(p)[:16]}  mtime={mt}")
    exec_src = (REPO / "src/components/execution.py").read_text(encoding="utf-8", errors="replace")
    print(f"  fix marker '_last_order_send_refusal' occurrences: {exec_src.count('_last_order_send_refusal')}")

    print("\n-- activation tokens on disk --")
    for f in sorted(TOKEN_DIR.glob("*.token.json")):
        tok = json.loads(f.read_text(encoding="utf-8"))
        print(f"  {f.name[:16]}...  sha={sha(f)[:16]}  ns={tok.get('namespace')!r}  "
              f"expires={tok.get('expires_utc')}  cfg={str(tok.get('config_digest_sha256'))[:12]}")
    key = TOKEN_DIR / "signing.key"
    if key.exists():
        print(f"  signing.key sha={sha(key)[:16]}")

    print("\n-- runtime config digests (recomputed) + gates --")
    import yaml

    from src.safety.activation_token import config_digest_for
    from src.utils.config import apply_profile_overrides

    base = yaml.safe_load((REPO / "config/agent_config.yaml").read_text(encoding="utf-8"))
    gates = ("ultimate_book_enabled", "ultimate_book_apply_to_execution",
             "ultimate_book_live_activation_allowed", "ultimate_book_live_broker_authority")
    for book, meta in BOOKS.items():
        dg = config_digest_for("config/agent_config.yaml", meta["profile"])
        merged = apply_profile_overrides(json.loads(json.dumps(base)), meta["profile"])
        rt = (merged.get("gtos_vnext_runtime") or {})
        print(f"  {book:<5} profile={meta['profile']:<24} digest={dg[:12]}")
        for k in gates:
            print(f"          {k:<44} {rt.get(k)}")

    print("\n-- kill / halt flags --")
    for rel in ("pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag",
                "pipeline_state/ULTIMATE_BOOK_KILL_fn.flag",
                "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag",
                "pipeline_state/RESEARCH_RUNTIME_HALT.flag"):
        print(f"  {rel:<52} {'PRESENT' if (REPO / rel).exists() else 'absent'}")

    print("\n-- broker state (read-only) --")
    import MetaTrader5 as mt5

    def _refuse(*a, **k):
        raise RuntimeError("order_send disabled in LQ state fence")

    mt5.order_send = _refuse
    for book, meta in BOOKS.items():
        if not mt5.initialize(path=meta["terminal"]):
            print(f"  {book:<5} initialize FAILED {mt5.last_error()}")
            continue
        try:
            ai = mt5.account_info()
            pos = mt5.positions_get() or []
            orders = mt5.orders_get() or []
            print(f"  {book:<5} login={ai.login} equity={ai.equity:.2f} balance={ai.balance:.2f} "
                  f"positions={len(pos)} pending_orders={len(orders)} "
                  f"connected={mt5.terminal_info().connected} trade_allowed={mt5.terminal_info().trade_allowed}")
            for p in pos:
                print(f"        POSITION {p.symbol} vol={p.volume} ticket={p.ticket} magic={p.magic} comment={p.comment!r}")
            for o in orders:
                print(f"        ORDER    {o.symbol} vol={o.volume_current} ticket={o.ticket}")
        finally:
            mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())

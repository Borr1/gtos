#!/usr/bin/env python3
"""Post-ceremony verification. STRICTLY READ-ONLY at the broker.

MT5 calls: initialize / account_info / positions_get / terminal_info / shutdown.
There is NO order_send, order_check or order_calc_* in this file. The placement
proof is `activation_token.authorize_broker_mutation`, the pure decision function
that sits behind `RealMT5.order_send`'s choke point: it classifies the request and
answers allow/deny WITHOUT transmitting anything to the broker.
"""
import os
import sys
import json
import datetime as dt

REPO = r"C:\Users\MSI\Documents\ai-trading-agent"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"host-local\lbi_20260811"
os.chdir(REPO)
sys.path.insert(0, REPO)

import yaml  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402
from src.utils.config import apply_profile_overrides  # noqa: E402
from src.components.ultimate_book.bridge import config_bool_value  # noqa: E402
from src.safety.activation_token import (  # noqa: E402
    authorize_broker_mutation, account_digest, config_digest_for, token_dir,
    strict_positions_provider, PositionsUnavailable,
)

ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", "operator_profile", "operator_profile"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", "redacted_account", "redacted_account_live_bee34003"),
]

base = yaml.safe_load(open(os.path.join(REPO, "config", "agent_config.yaml"), encoding="utf-8"))
res = {"schema": "gtos.live_book_integrity.post_ceremony_verify.v1",
       "as_of_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "token_dir": str(token_dir()), "accounts": {}}

for label, term, profile, ns in ACCOUNTS:
    merged = apply_profile_overrides(dict(base), profile)
    rt = merged.get("gtos_vnext_runtime", merged)
    # the EXACT resolution book_owner.py:269-276 performs
    try:
        cap_on = config_bool_value(rt.get("ultimate_book_one_unit_per_cluster_per_day", True), True)
    except (TypeError, ValueError):
        cap_on = True
    exempt = rt.get("ultimate_book_cluster_cap_exempt_clusters", ["jpy"])
    digest = config_digest_for("config/agent_config.yaml", profile, repo_root=REPO)

    row = {
        "profile": profile, "namespace": ns,
        "cluster_cap_on_resolved": bool(cap_on),
        "cluster_cap_exempt": list(exempt) if isinstance(exempt, (list, tuple, set)) else exempt,
        "gates": {k: rt.get(k) for k in ("ultimate_book_apply_to_execution",
                                         "ultimate_book_live_activation_allowed",
                                         "ultimate_book_live_broker_authority",
                                         "ultimate_book_include_clean3")},
        "config_digest_sha256": digest,
    }

    if not mt5.initialize(path=term):
        row["broker_error"] = str(mt5.last_error())
        res["accounts"][label] = row
        continue
    ai = mt5.account_info()
    ti = mt5.terminal_info()
    login_digest = account_digest(getattr(ai, "login", None)) if ai is not None else None
    positions = mt5.positions_get()
    row["broker"] = {
        "server": getattr(ai, "server", None),
        "login_sha256_redacted": "redacted:" + (login_digest or "")[:12],
        "trade_allowed": getattr(ai, "trade_allowed", None),
        "terminal_connected": getattr(ti, "connected", None),
        "balance": getattr(ai, "balance", None),
        "equity": getattr(ai, "equity", None),
        "open_positions": (len(positions) if positions is not None else None),
    }

    @strict_positions_provider
    def provider(symbol, _p=positions):
        if _p is None:
            raise PositionsUnavailable("positions_get returned None")
        return _p

    # An EXPOSURE-INCREASING request shape: TRADE_ACTION_DEAL, ORDER_TYPE_BUY, no `position`.
    # Decided, never transmitted.
    probe_symbol = "XAUUSD"
    request = {"action": int(mt5.TRADE_ACTION_DEAL), "symbol": probe_symbol,
               "type": int(mt5.ORDER_TYPE_BUY), "volume": 0.01,
               "comment": "GTOS_LIVE_BOOK_INTEGRITY_DRILL_NO_TRANSMIT"}
    d = authorize_broker_mutation(
        request, account_login_sha256=login_digest, positions_provider=provider,
        namespace=ns, config_digest_sha256=digest, audit=True)
    row["placement_drill"] = {
        "request": {k: request[k] for k in ("action", "symbol", "type", "volume")},
        "transmitted_to_broker": False,
        "allowed": bool(d.allowed), "reason": d.reason,
        "risk_direction": d.risk_direction, "classification": d.classification,
        "positions_verified": d.positions_verified, "detail": d.detail,
    }
    # control: a risk-REDUCING request must pass without needing the token at all
    close_req = {"action": int(mt5.TRADE_ACTION_DEAL), "symbol": probe_symbol,
                 "type": int(mt5.ORDER_TYPE_SELL), "volume": 0.01, "position": 1,
                 "comment": "GTOS_LIVE_BOOK_INTEGRITY_DRILL_NO_TRANSMIT"}
    d2 = authorize_broker_mutation(
        close_req, account_login_sha256=login_digest, positions_provider=provider,
        namespace=ns, config_digest_sha256=digest, audit=True)
    row["reducing_control"] = {"allowed": bool(d2.allowed), "reason": d2.reason,
                               "risk_direction": d2.risk_direction}
    # negative control: the PREVIOUS digest must now be REFUSED (proves the binding is live)
    d3 = authorize_broker_mutation(
        request, account_login_sha256=login_digest, positions_provider=provider,
        namespace=ns, config_digest_sha256="0" * 64, audit=False)
    row["stale_digest_negative_control"] = {"allowed": bool(d3.allowed), "reason": d3.reason}
    mt5.shutdown()
    res["accounts"][label] = row

p = os.path.join(OUT, "POST_CEREMONY_VERIFY_V1.json")
json.dump(res, open(p, "w", encoding="utf-8"), indent=1)
print("WROTE", p)
for k, v in res["accounts"].items():
    print(f"{k}: cap_on={v['cluster_cap_on_resolved']} gates={v['gates']} digest={str(v['config_digest_sha256'])[:12]}")
    print(f"   broker={v.get('broker')}")
    print(f"   DRILL allowed={v['placement_drill']['allowed']} reason={v['placement_drill']['reason']} dir={v['placement_drill']['risk_direction']}")
    print(f"   reducing control allowed={v['reducing_control']['allowed']} reason={v['reducing_control']['reason']}")
    print(f"   stale-digest negative control allowed={v['stale_digest_negative_control']['allowed']} reason={v['stale_digest_negative_control']['reason']}")

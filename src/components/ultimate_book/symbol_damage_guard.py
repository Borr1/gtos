"""symbol_damage_guard.py — per-symbol/-session DAMAGE-MEMORY kill switch (default-off, owner-armed).

THE GAP THIS FILLS (verified 2026-06-17, wf_a90db6e5 harvest + preflight: the deployed ultimate_book has only
an ACCOUNT-level breach-flatten + smooth DD-defense; it has NO per-SYMBOL circuit-breaker — yet the hard-halt
was a per-symbol/runtime damage event and the "recent-damage kill switch" decision appeared 25x in Wave-2). This
ports the VERIFIED classifier from src/components/market_whiteboard_v2._classify_symbol_health VERBATIM as a
clean, deployable, default-off guard: a symbol that has done real damage over a window of realized PRIOR trades
is QUARANTINE'd (drop new entries) or RISK_REDUCE'd (half size).

DISCIPLINE: leak-free (only fully-realized PRIOR closed deals); DEFAULT-OFF (enabled=False => never acts);
broker-real metrics only (the runtime feeds realized closed deals from the broker account history). Pure; no IO.
Thresholds are config-overridable and identical to the verified market_whiteboard_v2 source.
"""
from __future__ import annotations
import datetime as _dt
from typing import Any, Mapping, Optional

# VERBATIM from market_whiteboard_v2._classify_symbol_health (the verified source).
SYMBOL_HARD_MIN_TRADES = 6
SYMBOL_HARD_MAX_WIN_RATE = 0.35
SYMBOL_HARD_MAX_NET_CASH = -500.0
SYMBOL_HARD_MIN_LOSSES = 4
SYMBOL_REDUCE_MAX_NET_CASH = -100.0
SYMBOL_REDUCE_MAX_WIN_RATE = 0.45

QUARANTINE = "hard_quarantine"
RISK_REDUCE = "risk_reduce"
HEALTHY = "healthy_or_unproven"


def classify_symbol_health(trades: int, losses: int, net: float, win_rate: float,
                           cfg: Optional[Mapping[str, Any]] = None) -> str:
    """VERBATIM verified logic: hard_quarantine if trades>=6 AND (net<=-500 OR wr<=0.35 OR losses>=4);
    risk_reduce if trades>0 AND (net<=-100 OR wr<=0.45); else healthy_or_unproven."""
    cfg = cfg or {}
    min_trades = int(cfg.get("symbol_hard_min_trades", SYMBOL_HARD_MIN_TRADES))
    max_wr = float(cfg.get("symbol_hard_max_win_rate", SYMBOL_HARD_MAX_WIN_RATE))
    max_net = float(cfg.get("symbol_hard_max_net_cash", SYMBOL_HARD_MAX_NET_CASH))
    min_losses = int(cfg.get("symbol_hard_min_losses", SYMBOL_HARD_MIN_LOSSES))
    reduce_net = float(cfg.get("symbol_reduce_max_net_cash", SYMBOL_REDUCE_MAX_NET_CASH))
    reduce_wr = float(cfg.get("symbol_reduce_max_win_rate", SYMBOL_REDUCE_MAX_WIN_RATE))
    if trades >= min_trades and (net <= max_net or win_rate <= max_wr or losses >= min_losses):
        return QUARANTINE
    if trades > 0 and (net <= reduce_net or win_rate <= reduce_wr):
        return RISK_REDUCE
    return HEALTHY


def damage_multiplier(verdict: str, *, enabled: bool = False) -> float:
    """Confidence multiplier from the verdict. DEFAULT-OFF (enabled=False => 1.0, no-op).
    QUARANTINE -> 0.0 (drop new entries), RISK_REDUCE -> 0.5 (half size), HEALTHY -> 1.0."""
    if not enabled:
        return 1.0
    if verdict == QUARANTINE:
        return 0.0
    if verdict == RISK_REDUCE:
        return 0.5
    return 1.0


def compute_symbol_metrics(closed_deals, now_utc, *, offset_hours: float = 0.0,
                           window_days: int = 5) -> dict:
    """Leak-free per-symbol metrics from realized PRIOR closed deals (today excluded). NEVER raises (a bad
    read -> empty metrics = HEALTHY, the safe-inert fallback). Returns {symbol: {trades,losses,net,win_rate}}.

      closed_deals : [{symbol, profit, time}] where time = broker-server deal epoch (unix ts).
      window_days  : trailing fully-realized server-days to aggregate (default 5)."""
    try:
        today = (now_utc.astimezone(_dt.timezone.utc) + _dt.timedelta(hours=float(offset_hours))).date()
        cutoff = today - _dt.timedelta(days=int(window_days))
        agg: dict = {}
        for d in closed_deals or []:
            t = d.get("time"); sym = d.get("symbol")
            if not t or not sym:
                continue
            day = _dt.datetime.fromtimestamp(int(t), _dt.timezone.utc).date()
            if day >= today or day < cutoff:        # fully-realized PRIOR days within the window only
                continue
            pnl = float(d.get("profit") or 0.0)
            a = agg.setdefault(sym, {"trades": 0, "losses": 0, "net": 0.0, "wins": 0})
            a["trades"] += 1
            a["net"] += pnl
            if pnl < 0:
                a["losses"] += 1
            elif pnl > 0:
                a["wins"] += 1
        out = {}
        for sym, a in agg.items():
            wr = (a["wins"] / a["trades"]) if a["trades"] else 1.0
            out[sym] = {"trades": a["trades"], "losses": a["losses"], "net": round(a["net"], 2),
                        "win_rate": round(wr, 4)}
        return out
    except Exception:
        return {}


def symbol_damage_mult(symbol: str, metrics_by_symbol: Optional[Mapping[str, Mapping]],
                       *, enabled: bool = False, cfg: Optional[Mapping[str, Any]] = None) -> float:
    """End-to-end per-symbol damage confidence multiplier for the admission path. DEFAULT-OFF => 1.0.
    metrics_by_symbol = compute_symbol_metrics(...) output; absent symbol -> HEALTHY -> 1.0."""
    if not enabled or not metrics_by_symbol:
        return 1.0
    m = metrics_by_symbol.get(symbol)
    if not m:
        return 1.0
    verdict = classify_symbol_health(int(m.get("trades", 0)), int(m.get("losses", 0)),
                                     float(m.get("net", 0.0)), float(m.get("win_rate", 1.0)), cfg)
    return damage_multiplier(verdict, enabled=True)

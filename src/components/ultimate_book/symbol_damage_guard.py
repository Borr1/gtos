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

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scores(
    cache_key: tuple,
    facts: dict,
    questions: dict[str, str],
    anchors: dict | None = None,
) -> dict[str, float | None]:
    """One nineteen.score per question. Fewer than two anchors does not post."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    levels = anchors if isinstance(anchors, dict) else {}
    out = {str(qid): None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[str(qid)] = _finite(
                    ask(
                        payload,
                        question_id=str(qid),
                        instructions=str(text),
                        anchors=levels.get(str(qid)),
                    )
                )
            except Exception:
                out[str(qid)] = None
    _HOP[cache_key] = dict(out)
    return out

QUARANTINE = "hard_quarantine"
RISK_REDUCE = "risk_reduce"
HEALTHY = "healthy_or_unproven"


def classify_symbol_health(trades: int, losses: int, net: float, win_rate: float,
                           cfg: Optional[Mapping[str, Any]] = None) -> str:
    """Quarantine, reduce, or leave the symbol. An empty bound does not quarantine.

    A caller-supplied cfg value is that call's fact. Anything the cfg does not
    name is one Score for this trade state. An empty score does not restore a
    planted trade count, win rate, or cash level.
    """
    cfg = dict(cfg or {})
    facts = {
        "trades": trades,
        "losses": losses,
        "net": net,
        "win_rate": win_rate,
    }
    questions = {
        "symbol_hard_min_trades": (
            "The score you return is how many closed trades this state needs before a hard quarantine. "
            "An empty score leaves that count unset. Do not send."
        ),
        "symbol_hard_max_win_rate": (
            "The score you return is the win rate at or below which this state quarantines. "
            "An empty score leaves that rate unset. Do not send."
        ),
        "symbol_hard_max_net_cash": (
            "The score you return is the net cash at or below which this state quarantines. "
            "An empty score leaves that cash unset. Do not send."
        ),
        "symbol_hard_min_losses": (
            "The score you return is how many losses this state needs before a hard quarantine. "
            "An empty score leaves that count unset. Do not send."
        ),
        "symbol_reduce_max_net_cash": (
            "The score you return is the net cash at or below which this state reduces risk. "
            "An empty score leaves that cash unset. Do not send."
        ),
        "symbol_reduce_max_win_rate": (
            "The score you return is the win rate at or below which this state reduces risk. "
            "An empty score leaves that rate unset. Do not send."
        ),
    }
    needed = {name: text for name, text in questions.items() if name not in cfg}
    trades_n = _finite(trades)
    losses_n = _finite(losses)
    net_n = _finite(net)
    win_n = _finite(win_rate)
    loss_rate = None
    if trades_n is not None and trades_n > 0 and losses_n is not None:
        loss_rate = losses_n / trades_n
    count_levels = []
    if trades_n is not None:
        count_levels.append(("closed trades on this state", trades_n))
    if losses_n is not None:
        count_levels.append(("losses on this state", losses_n))
    rate_levels = []
    if win_n is not None:
        rate_levels.append(("the win rate on this state", win_n))
    if loss_rate is not None:
        rate_levels.append(("the loss rate on this state", loss_rate))
    cash_levels = []
    if net_n is not None:
        cash_levels.append(("the net cash on this state", net_n))
    level_for = {
        "symbol_hard_min_trades": count_levels,
        "symbol_hard_min_losses": count_levels,
        "symbol_hard_max_win_rate": rate_levels,
        "symbol_reduce_max_win_rate": rate_levels,
        "symbol_hard_max_net_cash": cash_levels,
        "symbol_reduce_max_net_cash": cash_levels,
    }
    bounds = (
        _scores(
            ("symbol_damage", trades, losses, round(float(net), 4), round(float(win_rate), 4), tuple(sorted(needed))),
            facts,
            needed,
            {name: level_for.get(name, []) for name in needed},
        )
        if needed
        else {}
    )

    def pick(name: str) -> float | None:
        if name in cfg:
            return _finite(cfg.get(name))
        return bounds.get(name)

    min_trades = pick("symbol_hard_min_trades")
    max_wr = pick("symbol_hard_max_win_rate")
    max_net = pick("symbol_hard_max_net_cash")
    min_losses = pick("symbol_hard_min_losses")
    reduce_net = pick("symbol_reduce_max_net_cash")
    reduce_wr = pick("symbol_reduce_max_win_rate")
    # A missing bound is not a quarantine. Only a bound that returned can fire.
    if min_trades is not None and trades >= min_trades:
        hard = False
        if max_net is not None and net <= max_net:
            hard = True
        if max_wr is not None and win_rate <= max_wr:
            hard = True
        if min_losses is not None and losses >= min_losses:
            hard = True
        if hard:
            return QUARANTINE
    if trades > 0 and (
        (reduce_net is not None and net <= reduce_net)
        or (reduce_wr is not None and win_rate <= reduce_wr)
    ):
        return RISK_REDUCE
    return HEALTHY


def damage_multiplier(verdict: str, *, enabled: bool = False) -> float:
    """Confidence multiplier from the verdict. DEFAULT-OFF (enabled=False => 1.0, no-op).
    QUARANTINE -> 0.0. An empty reduce score stays 1.0 and does not drop the entry."""
    if not enabled:
        return 1.0
    if verdict == QUARANTINE:
        return 0.0
    if verdict == RISK_REDUCE:
        mult = _scores(
            ("symbol_reduce_mult", verdict),
            {"verdict": verdict},
            {
                "reduce_multiplier": (
                    "The score you return is the size multiplier for a symbol this state reduces. "
                    "An empty score leaves that size unset. Do not send."
                ),
            },
            {"reduce_multiplier": []},
        ).get("reduce_multiplier")
        if mult is None or mult < 0:
            return 1.0
        return float(mult)
    return 1.0


def compute_symbol_metrics(closed_deals, now_utc, *, offset_hours: float = 0.0,
                           window_days: int | None = None) -> dict:
    """Leak-free per-symbol metrics from realized PRIOR closed deals (today excluded). NEVER raises (a bad
    read -> empty metrics = HEALTHY, the safe-inert fallback). Returns {symbol: {trades,losses,net,win_rate}}.

      closed_deals : [{symbol, profit, time}] where time = broker-server deal epoch (unix ts).
      window_days  : trailing fully-realized server-days. Unset asks. An empty score keeps every prior day."""
    try:
        today = (now_utc.astimezone(_dt.timezone.utc) + _dt.timedelta(hours=float(offset_hours))).date()
        span = _finite(window_days)
        if span is None:
            span = _scores(
                ("symbol_window", today.isoformat(), round(float(offset_hours), 6)),
                {"day": today.isoformat(), "offset_hours": offset_hours},
                {
                    "window_days": (
                        "The score you return is how many prior server-days of closed deals this state still counts. "
                        "An empty score does not cut the window. Do not send."
                    ),
                },
                {"window_days": []},
            ).get("window_days")
        cutoff = None if span is None else today - _dt.timedelta(days=int(span))
        agg: dict = {}
        for d in closed_deals or []:
            t = d.get("time"); sym = d.get("symbol")
            if not t or not sym:
                continue
            day = _dt.datetime.fromtimestamp(int(t), _dt.timezone.utc).date()
            if day >= today or (cutoff is not None and day < cutoff):
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

"""Book edge reconciliation — the closed loop the open-loop pipeline was missing (SYNTH-1 / MACRO-EDGE-01).

The W7 book runs a fixed offline edge feed-forward: market -> candidate -> size -> place -> manage, with
NOTHING that reality produces flowing back into a decision. If a sleeve's edge decays or inverts, sizing
keeps full conviction weight indefinitely (the prior live system degraded into the -$859/77-trade hard
halt precisely because no loop noticed the realized edge rolling over).

This is the per-namespace feedback sibling to monitor_books: each closed BOOK deal's realized P&L is
folded into a persisted per-sleeve expectancy, and a sleeve whose trailing-window realized expectancy
turns negative over a minimum sample raises a decay alarm (deduped, re-armed on recovery). State is a
plain JSON file per namespace; processing is keyed on the close-deal ticket so a deal is never
double-counted across runs. No order path; never raises into the caller.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional


class BookEdgeReconciler:
    def __init__(self, repo_root: str, namespace: str, *, min_sample: int = 12, window: int = 25):
        self._dir = os.path.join(repo_root, "pipeline_state", "ultimate_book", namespace)
        self._path = os.path.join(self._dir, "edge_state.json")
        self._min_sample = int(min_sample)
        self._window = int(window)
        self._state = self._load()

    # ---- persistence (best-effort; a read/write fault never blocks reconciliation) ----
    def _load(self) -> dict:
        try:
            with open(self._path, encoding="utf-8") as f:
                s = json.load(f)
                if isinstance(s, dict) and isinstance(s.get("sleeves"), dict):
                    return s
        except (OSError, ValueError):
            pass
        return {"sleeves": {}, "seen_tickets": []}

    def _save(self) -> None:
        try:
            os.makedirs(self._dir, exist_ok=True)
            import uuid
            tmp = f"{self._path}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._state, f)
            os.replace(tmp, self._path)
        except OSError:
            pass

    # ---- ingest ----
    def ingest(self, closed_deals: list[dict]) -> list[str]:
        """Fold NEW closed book deals into per-sleeve expectancy; return decay alarm strings (deduped).

        closed_deals: dicts with keys {ticket, sleeve, profit, time}. A deal already processed (its ticket
        in seen_tickets) is skipped, so calling repeatedly with an overlapping window is safe + idempotent.
        """
        seen = set(self._state.get("seen_tickets") or [])
        sleeves = self._state.setdefault("sleeves", {})
        alarms: list[str] = []
        # process in time order so the trailing window reflects chronology
        new = [d for d in closed_deals if d.get("ticket") not in seen and d.get("sleeve")]
        new.sort(key=lambda d: (d.get("time") or 0, d.get("ticket") or 0))
        for d in new:
            tkt, sl, pnl = d.get("ticket"), str(d.get("sleeve")), float(d.get("profit") or 0.0)
            seen.add(tkt)
            st = sleeves.setdefault(sl, {"n": 0, "wins": 0, "sum_profit": 0.0, "recent": [], "alarmed": False})
            st["n"] += 1
            st["wins"] += 1 if pnl > 0 else 0
            st["sum_profit"] += pnl
            rec = st.setdefault("recent", [])
            rec.append(round(pnl, 2))
            if len(rec) > self._window:
                del rec[0:len(rec) - self._window]
            # decay verdict on the trailing window: enough sample AND the window is net-losing on average
            win_mean = sum(rec) / len(rec) if rec else 0.0
            decayed = len(rec) >= self._min_sample and win_mean < 0.0 and sum(rec) < 0.0
            if decayed and not st.get("alarmed"):
                st["alarmed"] = True
                alarms.append(f"{sl}: edge DECAY — last {len(rec)} trades mean ${win_mean:+.1f}/trade "
                              f"(net ${sum(rec):+.0f}), lifetime n={st['n']} win%={100.0*st['wins']/st['n']:.0f}")
            elif not decayed and st.get("alarmed") and win_mean > 0.0:
                st["alarmed"] = False   # re-arm once the window recovers to positive
        # bound the seen-ticket list (keep recent tail; tickets only grow)
        seen_list = sorted(seen)
        self._state["seen_tickets"] = seen_list[-5000:]
        self._state["sleeves"] = sleeves
        if new:
            self._save()
        return alarms

    def summary(self) -> dict[str, Any]:
        out = {}
        for sl, st in (self._state.get("sleeves") or {}).items():
            n = st.get("n", 0)
            rec = st.get("recent") or []
            out[sl] = {
                "n": n,
                "win_pct": round(100.0 * st.get("wins", 0) / n, 1) if n else 0.0,
                "mean_profit": round(st.get("sum_profit", 0.0) / n, 2) if n else 0.0,
                "recent_mean": round(sum(rec) / len(rec), 2) if rec else 0.0,
                "alarmed": bool(st.get("alarmed")),
            }
        return out


def closed_book_deals(mt5_module, now, hours: int = 168) -> list[dict]:
    """Read recent CLOSED book positions from MT5 history as {ticket, sleeve, profit, time}.

    A CLOSE deal (entry==1 = DEAL_ENTRY_OUT) carries the CLOSE-request comment (e.g. 'owner_flatten' /
    'close_...'), NOT the W7:<sleeve> tag — that lives on the OPEN deal (entry==0). So map close->sleeve by
    position_id via the open deal's W7: comment, and take realized P&L from the close deal(s). The upper
    bound is padded +13h (server ahead of UTC) so a just-closed position is captured. ticket = the close
    deal's ticket (unique, for idempotent dedup). Returns [] on error. mt5_module = raw MetaTrader5 module."""
    import datetime as _dt
    try:
        deals = mt5_module.history_deals_get(now - _dt.timedelta(hours=hours),
                                              now + _dt.timedelta(hours=13))
    except Exception:
        return []
    deals = deals or []
    sleeve_of: dict[int, str] = {}
    for d in deals:
        try:
            if int(getattr(d, "entry", 0)) == 0:                 # OPEN deal carries the sleeve tag
                cmt = str(getattr(d, "comment", "") or "")
                if cmt.startswith("W7:"):
                    sleeve_of[int(getattr(d, "position_id", 0) or 0)] = cmt[3:]
        except Exception:
            continue
    out = []
    for d in deals:
        try:
            if int(getattr(d, "entry", 0)) != 1:                 # only CLOSE deals
                continue
            sl = sleeve_of.get(int(getattr(d, "position_id", 0) or 0))
            if not sl:                                           # close of a non-book / out-of-window-open position
                continue
            out.append({"ticket": int(getattr(d, "ticket", 0) or 0), "sleeve": sl,
                        "profit": float(getattr(d, "profit", 0.0) or 0.0)
                        + float(getattr(d, "swap", 0.0) or 0.0) + float(getattr(d, "commission", 0.0) or 0.0),
                        "time": int(getattr(d, "time", 0) or 0)})
        except Exception:
            continue
    return out

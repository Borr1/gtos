"""The B10 hour-surface repair as a B8 treatment arm.

`spread_model.intraweek_mult` (`src/costs/spread_model.py:396`) reads ONLY
`by_class_hour_of_week`. `SPREAD_MODEL_V1.json` also carries `by_symbol_hour_of_week` for 36
FTMO broker symbols; no code in the tree reads it, and B10 validated it against 300,538,915
ticks at a median 0.64 % disagreement. This arm applies the repair as an external multiplier
on the spread the shipped model returns, so every other term -- tick anchor, era ratio, band
construction, damping -- is untouched and cancels inside the pair.

Deliberately NOT a patch to `spread_model.py`: that file is reachable from the live cost path
and this is a proposal, not a landing.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from b8_paired_shadow.arms import Arm, ArmUnavailable, COST_BAND_INFO, published_policy
from b8_paired_shadow.substrate import MAXBARS, Intent, Substrate
from src.components.ultimate_book.admission import winsorize_R
from src.costs.spread_model import load_spread_model, spread_price
from src.research_infra.walkforward.exits import replay
from src.research_infra.walkforward.quote_side import BarQuote, replay_anchor
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

ACCOUNT = "FTMO"
SERVER = "FTMO-Server3"
BAND = "mid"


class _Surface:
    def __init__(self) -> None:
        m = load_spread_model()
        shape = (m.doc.get("intraweek") or {}).get(ACCOUNT) or {}
        self.by_symbol: dict[str, dict[str, float]] = shape.get("by_symbol_hour_of_week") or {}
        self.by_class: dict[str, dict[str, float]] = shape.get("by_class_hour_of_week") or {}
        self.model = m
        self.rule = resolve_rule(SERVER)
        self._meta: dict[str, tuple[str, str | None]] = {}

    def _resolve(self, symbol: str) -> tuple[str, str | None]:
        if symbol not in self._meta:
            try:
                rec = self.model.record(symbol, ACCOUNT)
                self._meta[symbol] = (str(rec.get("broker_symbol") or symbol),
                                      rec.get("instrument_class"))
            except Exception:
                self._meta[symbol] = (symbol, None)
        return self._meta[symbol]

    def ratio(self, symbol: str, at_utc: dt.datetime) -> float:
        wall = utc_to_broker_naive(at_utc, self.rule)
        how = str(wall.weekday() * 24 + wall.hour)
        bs, kl = self._resolve(symbol)
        sym = None
        for k in (symbol, bs):
            cell = self.by_symbol.get(k)
            if cell is not None and how in cell:
                sym = float(cell[how])
                break
        if sym is None:
            return 1.0
        cls = float(((self.by_class.get(kl) or {}).get(how)) or 1.0)
        return (sym / cls) if cls > 0 else 1.0


_SURFACE: _Surface | None = None


def symbol_hour_exit_arm(name: str, *, declared_at: str) -> Arm:
    def _fn(it: Intent, sub: Substrate) -> Any:
        global _SURFACE
        if _SURFACE is None:
            _SURFACE = _Surface()
        got = sub.resolve(it)
        if got is None:
            raise ArmUnavailable(f"no bars for {it.symbol} @ {it.decision_bar_iso}")
        s, i = got
        at = sub.entry_instant(it)
        try:
            sp = float(spread_price(it.symbol, ACCOUNT, at, band=BAND).spread_price)
        except Exception as exc:
            raise ArmUnavailable(f"no spread for {it.symbol}: {exc}") from None
        if not (sp > 0):
            raise ArmUnavailable(f"non-positive spread for {it.symbol}")
        sp *= _SURFACE.ratio(it.symbol, at)
        pol = published_policy(it, maxbars=MAXBARS)
        res = replay(s.bars, i, it.direction, stop_dist=it.stop_dist, policy=pol,
                     entry_price=replay_anchor(s.bars[i].c, it.direction, sp, BarQuote.BID))
        from b8_paired_shadow.arms import Outcome
        return Outcome(admitted=True, r=winsorize_R(res.r_gross), exit_reason=res.exit_reason,
                       grid=it.tf_name, entry_utc=at.isoformat(),
                       detail={"spread": sp, "policy": pol.label})

    return Arm(name=name, dimension="cost_geometry",
               rationale="by_symbol_hour_of_week substituted for by_class_hour_of_week "
                         "(B10: the symbol table is in the shipped artifact and no code "
                         "reads it; tape-validated to a median 0.64 %)",
               declared_at=declared_at, fn=_fn, information_set=COST_BAND_INFO)

"""G2-M1 — restate the SLEEVE ESTATE at corrected geometry.

Two corrections landed 2026-08-12 and **no published sleeve-estate figure carries either**:

1. **The hour surface is symbol-shaped, and the shipped model reads the class table.**
   `src/costs/spread_model.py:396` (`intraweek_mult`) reads **only** `by_class_hour_of_week`.
   The same artifact `SPREAD_MODEL_V1.json` also carries `by_symbol_hour_of_week` for 36 FTMO
   broker symbols and **no code in the tree reads it** (B10 §0). B10 validated that dead table
   against 300,538,915 ticks: median disagreement **0.64 %** across the 24 surface symbols,
   against a class table that averages UK100's genuine 8.9x hour cycle with instruments that
   are hour-flat and prints 1.30x.
   B10 priced that defect on the **sealed funnel record** (282 trades) and on the **candidate
   pool** (146,745 fills). It never priced it on the **sleeve estate** — the 22,354-decision,
   29-sleeve, 2000-2026 store every published sleeve number is measured on. That is this file.

2. **Slippage is barrier-conditional and the estate charges it flat.**
   `config/agent_config.yaml:740` `selected_cell_default_expected_slippage_r: 0.02`.
   `RECON_SLIPPAGE_ADJUDICATION_V1` measured the legs on 18,978 tick-matched rows:
   entry +0.00663, stop exit +0.03932, target exit 0.00000 (favourable, not banked, correct by
   design), time-stop exit +0.00141. The flat constant is right *at the sealed window's barrier
   mix* (52.0 % stops) to within 4 %. **Sleeve barrier mixes are nothing like that mix** and the
   correction therefore has a per-sleeve sign.

WHAT IS HELD, AND WHY THAT MAKES THIS A RESTATEMENT RATHER THAN A BACKTEST
--------------------------------------------------------------------------
Every decision tuple (sleeve, symbol, timeframe, decision bar, direction, stop distance,
target distance) is the estate's own and is **not varied**. Only the charged cost moves. The
fill authority is `walkforward.exits.replay`, the sanctioned labeller. The control arm is the
estate's own published economic convention (`r_new_mid`: entry anchored at
`close + direction * spread`, spread from the shipped model at band `mid`).

NO WRITES OUTSIDE THIS DIRECTORY. No `src/` edit, no config byte, no broker, no VPS, no git.
The symbol-hour repair is applied as an **external multiplier on the returned spread**,
deliberately not as a patch to `spread_model.py` — that file is reachable from the live cost
path and the repair is a proposal, not a landing.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[9]
B8 = REPO / ("docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
             "outcome_authority/swarm2/breakthrough")
for p in (str(REPO), str(B8)):
    if p not in sys.path:
        sys.path.insert(0, p)

from b8_paired_shadow.arms import published_policy  # noqa: E402
from b8_paired_shadow.substrate import MAXBARS, Substrate  # noqa: E402
from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.costs.spread_model import load_spread_model, spread_price  # noqa: E402
from src.research_infra.walkforward.exits import replay  # noqa: E402
from src.research_infra.walkforward.quote_side import BarQuote, replay_anchor  # noqa: E402
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

OUT = Path(__file__).resolve().parent / "receipts"
ACCOUNT = "FTMO"
SERVER = "FTMO-Server3"
BAND = "mid"

# ---- RECON_SLIPPAGE_ADJUDICATION_V1 §0, the adjudicated legs (original risk units) --------
RECON_ENTRY_LEG = 0.00663          # unconditional, n=18,978, CI [+0.0047, +0.0084]
RECON_STOP_LEG = 0.03932           # conditional on a stop, n=9,543, CI [+0.0364, +0.0431]
RECON_TARGET_LEG = 0.0             # favourable (-0.03968) but not bankable; 0 by design
RECON_TIMESTOP_LEG = 0.00141       # conditional, n=5,482, CI [-0.0001, +0.0029]
CHARGED_FLAT = 0.02                # config/agent_config.yaml:740

#: `trail` is a stop order crossing a moving stop level, so it takes the stop leg. A sleeve
#: whose result turns on this gets a sensitivity in the receipt rather than a footnote.
EXIT_LEG = {"stop": RECON_STOP_LEG, "trail": RECON_STOP_LEG, "target": RECON_TARGET_LEG,
            "time_stop": RECON_TIMESTOP_LEG, "maxbars": RECON_TIMESTOP_LEG,
            "rollover_flat": RECON_TIMESTOP_LEG}


class HourSurface:
    """The symbol-hour repair, as a ratio applied to the shipped spread.

    `intraweek_mult` returns `by_class_hour_of_week[class][how]`. The repair is to prefer
    `by_symbol_hour_of_week[symbol][how]` when the artifact carries that cell. Applied as
    `spread * (symbol_mult / class_mult)` so every other term of the model -- tick anchor,
    era ratio, band construction, damping -- is untouched and cancels in the pair.
    """

    def __init__(self) -> None:
        m = load_spread_model()
        shape = (m.doc.get("intraweek") or {}).get(ACCOUNT) or {}
        self.by_symbol: dict[str, dict[str, float]] = shape.get("by_symbol_hour_of_week") or {}
        self.by_class: dict[str, dict[str, float]] = shape.get("by_class_hour_of_week") or {}
        self.model = m
        self.rule = resolve_rule(SERVER)
        self._cls: dict[str, str | None] = {}
        self.stats: dict[str, int] = defaultdict(int)

    def broker_symbol(self, symbol: str) -> str:
        rec = self.model.record(symbol, ACCOUNT)
        return str(rec.get("broker_symbol") or rec.get("symbol") or symbol)

    def klass(self, symbol: str) -> str | None:
        if symbol not in self._cls:
            try:
                self._cls[symbol] = self.model.record(symbol, ACCOUNT).get("instrument_class")
            except Exception:
                self._cls[symbol] = None
        return self._cls[symbol]

    def ratio(self, symbol: str, at_utc: dt.datetime) -> tuple[float, str]:
        """(multiplier on the shipped spread, why). 1.0 means the repair is a no-op here."""
        wall = utc_to_broker_naive(at_utc, self.rule)
        how = str(wall.weekday() * 24 + wall.hour)
        keys = [symbol]
        try:
            bs = self.broker_symbol(symbol)
            if bs != symbol:
                keys.append(bs)
        except Exception:
            pass
        sym_mult = None
        for k in keys:
            cell = self.by_symbol.get(k)
            if cell is not None and how in cell:
                sym_mult = float(cell[how])
                break
        if sym_mult is None:
            self.stats["no_symbol_cell"] += 1
            return 1.0, "no_symbol_cell"
        kl = self.klass(symbol)
        cls_mult = float(((self.by_class.get(kl) or {}).get(how)) or 1.0)
        if cls_mult <= 0:
            self.stats["bad_class_mult"] += 1
            return 1.0, "bad_class_mult"
        self.stats["repaired"] += 1
        return sym_mult / cls_mult, "repaired"


def main(limit: int | None = None) -> dict[str, Any]:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    sub = Substrate.load(verbose=False)
    hs = HourSurface()

    rows: list[dict[str, Any]] = []
    drops: dict[str, int] = defaultdict(int)
    spread_cache: dict[tuple[str, str], float] = {}

    intents = sub.intents if limit is None else sub.intents[:limit]
    for it in intents:
        got = sub.resolve(it)
        if got is None:
            drops["no_bars"] += 1
            continue
        s, i = got
        at = sub.entry_instant(it)
        ck = (it.symbol, it.entry_utc)
        if ck in spread_cache:
            sp = spread_cache[ck]
        else:
            try:
                sp = float(spread_price(it.symbol, ACCOUNT, at, band=BAND).spread_price)
            except Exception:
                drops["no_spread"] += 1
                spread_cache[ck] = -1.0
                continue
            spread_cache[ck] = sp
        if sp <= 0:
            drops["no_spread"] += 1
            continue

        ratio, why = hs.ratio(it.symbol, at)
        pol = published_policy(it, maxbars=MAXBARS)
        close = s.bars[i].c

        r_ctl = replay(s.bars, i, it.direction, stop_dist=it.stop_dist, policy=pol,
                       entry_price=replay_anchor(close, it.direction, sp, BarQuote.BID))
        r_tap = replay(s.bars, i, it.direction, stop_dist=it.stop_dist, policy=pol,
                       entry_price=replay_anchor(close, it.direction, sp * ratio, BarQuote.BID))

        rows.append({
            "sleeve": it.sleeve, "symbol": it.symbol, "day": it.decision_day,
            "year": it.entry_utc[:4],
            "r_ship": winsorize_R(r_ctl.r_gross), "r_tape": winsorize_R(r_tap.r_gross),
            "exit_ship": r_ctl.exit_reason, "exit_tape": r_tap.exit_reason,
            "spread_ship": sp, "spread_tape": sp * ratio, "ratio": ratio, "why": why,
            "stop_dist": it.stop_dist,
        })

    res = {
        "measurement": "G2-M1 sleeve-estate restatement at corrected geometry",
        "n_rows": len(rows), "drops": dict(drops),
        "hour_repair_coverage": dict(hs.stats),
        "seconds": round(time.time() - t0, 1),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (OUT / "G2_M1_ROWS.json").write_text(json.dumps(rows))
    (OUT / "G2_M1_META.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)

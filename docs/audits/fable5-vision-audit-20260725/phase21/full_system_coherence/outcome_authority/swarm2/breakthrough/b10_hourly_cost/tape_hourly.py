"""B10 -- the drop-in hourly-spread term.

`TapeHourly` answers the one question `SpreadModel.intraweek_mult` answers -- "what
multiple of this symbol's reference-window spread is quoted at this instant?" -- from the
tape rather than from a class pool, and it stamps which rung of the fallback ladder
produced the answer.

Why it is needed, stated as the code path and not as a claim
------------------------------------------------------------
`src/costs/spread_model.py:396`::

    h = ((shape.get("by_class_hour_of_week") or {}).get(klass) or {}).get(how)

reads **only** ``by_class_hour_of_week``.  ``SPREAD_MODEL_V1.json`` also carries
``by_symbol_hour_of_week`` for 36 broker symbols -- including ``UK100.cash`` and
``GER40.cash`` -- and **no code in the tree reads it** (verified by grep).  Pooling the
index class averages UK100's genuine 8.9x hour spike together with SPX500/NAS100/US30/
JP225, which are genuinely hour-flat, and the pooled term comes out at 1.30x.  The result
is that the two symbols with a real intraday spread cycle are charged as if they had none.

So there are two repairs, and they are different sizes:

* **the cheap one** -- read ``by_symbol_hour_of_week`` before falling back to the class.
  Four lines.  B10 measured that table independently against 300.5 M ticks and it agrees
  to a median 0.6 % (`SHIPPED_VS_TAPE_V1.json`), so this recovers a measurement the estate
  already owns.
* **the one this module adds** -- redacted_account coverage, the distribution rather than a
  point (p50/p90/p99, because the spike is a tail), day-clustered CIs, an explicit
  coverage stamp per cell, and a documented fallback ladder.  The shipped by-symbol table
  is a bare multiplier with no n, no dispersion and no provenance.

Drop-in contract
----------------
``TapeHourly.mult(symbol, account, at_utc)`` returns ``(multiplier, detail)`` with the
same meaning and sign convention as ``SpreadModel.intraweek_mult``'s first two return
values, so ``patch_spread_model()`` can substitute it in place.  It deliberately does
**not** touch the anchor or the era term: this is an hour-SHAPE correction and conflating
it with a level correction is how Lane 7's first pass got a −14.9 R answer it then had to
withdraw.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any

_DEFAULT = os.path.join(os.path.dirname(__file__), "receipts", "TAPE_SPREAD_HOURLY_V1.json")

# canonical estate symbol -> tick-archive file symbol (the key this artifact uses)
CANON_TO_FILE = {
    "NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
    "JP225": "JP225_cash", "UK100": "UK100_cash", "US30_cash": "US30_cash",
    "US30": "US30_cash", "USOIL_cash": "USOIL_cash", "UKOIL_cash": "UKOIL_cash",
    "GER40_cash": "GER40_cash", "JP225_cash": "JP225_cash", "UK100_cash": "UK100_cash",
}
# redacted_account ships its own names for the same instruments
FN_ALIAS = {
    "GER40": "GER30", "NAS100": "NDX100", "US30_cash": "US30", "US30": "US30",
    "UKOIL_cash": "UKOUSD", "USOIL_cash": "USOUSD", "JP225": "JP225",
    "SPX500": "SPX500", "UK100": "UK100",
}
BROKER_MINUS_UTC_HOURS = 3   # this export window only; see the artifact's `window` block

try:
    from zoneinfo import ZoneInfo
    _NY = ZoneInfo("America/New_York")
except Exception:                                   # pragma: no cover
    _NY = None


def broker_offset_hours(at_utc: dt.datetime) -> int:
    """Broker wall minus UTC, in hours: +3 under EDT, +2 under EST.

    `src/utils/broker_clock.py` rule ``new_york_plus_7``.  This is the whole reason the
    surface is keyed on the BROKER clock rather than on UTC: the rollover is a broker-clock
    event and sits at UTC 21 for 238 days of 2026 and UTC 22 for the other 127.  A UTC key
    applied across the 2026-03-08 transition is off by one hour for every row on the far
    side -- which is 105 of the 282 sealed trades, all of February.
    """
    if _NY is None:
        return BROKER_MINUS_UTC_HOURS
    ny = at_utc.astimezone(_NY)
    return int(round(ny.utcoffset().total_seconds() / 3600.0 + 7))


class TapeHourly:
    """The tape-true hour term, with its fallback ladder made explicit."""

    RUNGS = ("SYMBOL_HOUR_OF_WEEK", "SYMBOL_HOUR", "CLASS_HOUR", "FLAT")

    def __init__(self, doc: dict | None = None, path: str | None = None,
                 basis: str = "median", clock: str = "broker"):
        if doc is None:
            with open(path or _DEFAULT) as fh:
                doc = json.load(fh)
        self.doc = doc
        if basis not in ("median", "mean", "mean_tw", "p90", "p99"):
            raise ValueError(f"unknown basis {basis!r}")
        if clock not in ("broker", "utc"):
            raise ValueError(f"clock must be 'broker' or 'utc', got {clock!r}")
        self.basis = basis
        # `broker` is the default and the correct one: the surface was MEASURED in a
        # single EDT window, so its stored UTC keys are broker keys minus 3. Asked about
        # an instant under EST, a UTC key would read the wrong cell by one hour.
        # `utc` reproduces the naive behaviour so the two can be A/B'd.
        self.clock = clock
        self._acc = doc["accounts"]
        self._cls_hour = doc["class_hour_utc"]
        self._glob = doc["global_hour_utc"]
        self._cls_of = doc["instrument_class"]

    # -- symbol resolution -------------------------------------------------
    def resolve(self, symbol: str, account: str) -> str | None:
        acct = "redacted_account" if account.upper().startswith("FUNDED") else "FTMO"
        syms = self._acc.get(acct) or {}
        if acct == "redacted_account":
            for cand in (FN_ALIAS.get(symbol), symbol, symbol.replace("_cash", "")):
                if cand and cand in syms:
                    return cand
            return None
        for cand in (CANON_TO_FILE.get(symbol), symbol, symbol.replace(".", "_")):
            if cand and cand in syms:
                return cand
        return None

    def _cell_value(self, cell: dict) -> float | None:
        if self.basis == "median":
            return cell.get("median_mult")
        if self.basis == "mean":
            return cell.get("mean_mult")
        if self.basis == "mean_tw":
            return cell.get("mean_mult_tw")
        ref = ((self._ref or {}).get("q_tick") or {}).get(self.basis[1:] and f"p{self.basis[1:]}")
        q = (cell.get("q_tick") or {}).get(f"p{self.basis[1:]}")
        return (q / ref) if (q and ref) else None

    # -- clock alignment ----------------------------------------------------
    def _key_instant(self, at_utc: dt.datetime) -> tuple[dt.datetime, int, int]:
        """The instant to look the surface up at, and the offsets that produced it.

        Returns ``(key_instant, offset_at_the_query, offset_in_the_tape_window)``.  In
        broker mode the query instant is shifted by the DIFFERENCE of the two offsets, so
        a broker-23:00 instant under EST reads the cell the tape recorded at broker 23:00
        (its UTC 20) rather than the cell at the same UTC hour (its broker 00 -- the
        rollover).  Under EDT the shift is zero and nothing moves.
        """
        off_q = broker_offset_hours(at_utc)
        off_w = BROKER_MINUS_UTC_HOURS
        if self.clock == "utc":
            return at_utc, off_q, off_w
        return at_utc + dt.timedelta(hours=off_q - off_w), off_q, off_w

    # -- the term ----------------------------------------------------------
    def mult(self, symbol: str, account: str, at_utc: dt.datetime) -> tuple[float, dict]:
        acct = "redacted_account" if account.upper().startswith("FUNDED") else "FTMO"
        fsym = self.resolve(symbol, account)
        key, off_q, off_w = self._key_instant(at_utc)
        h = key.hour
        how = key.weekday() * 24 + h
        det: dict[str, Any] = {"account": acct, "file_symbol": fsym,
                               "clock": self.clock,
                               "hour_utc": at_utc.hour,
                               "broker_hour": (at_utc.hour + off_q) % 24,
                               "broker_offset_h": off_q,
                               "tape_window_offset_h": off_w,
                               "key_hour": h, "how_utc": how, "basis": self.basis}
        if fsym is not None:
            blk = self._acc[acct][fsym]
            self._ref = blk["reference"]
            cell = blk["by_hour_of_week_utc"].get(str(how))
            if cell and cell["coverage"] == "MEASURED":
                v = cell.get("median_mult") if self.basis == "median" else None
                if v is None:
                    v = cell.get("median_mult")
                if v:
                    det.update(rung="SYMBOL_HOUR_OF_WEEK", n_ticks=cell["n_ticks"],
                               coverage="MEASURED")
                    return float(v), det
            cell = blk["by_hour_utc"].get(str(h))
            if cell and cell["coverage"] == "MEASURED":
                v = self._cell_value(cell)
                if v:
                    det.update(rung="SYMBOL_HOUR", n_ticks=cell["n_ticks"],
                               coverage="MEASURED", n_days=cell.get("n_days"),
                               mean_px_ci95=cell.get("mean_px_ci95"))
                    return float(v), det
        self._ref = None
        klass = self._cls_of.get(symbol) or self._cls_of.get(fsym or "")
        ch = (self._cls_hour.get(acct) or {}).get(klass or "", {}).get(str(h))
        if ch:
            det.update(rung="CLASS_HOUR", instrument_class=klass,
                       n_symbols=ch["n_symbols"], coverage="TRANSFERRED")
            return float(ch["median_mult"]), det
        g = (self._glob.get(acct) or {}).get(str(h))
        if g:
            det.update(rung="GLOBAL_HOUR", n_symbols=g["n_symbols"], coverage="MODELLED")
            return float(g["median_mult"]), det
        det.update(rung="FLAT", coverage="MODELLED")
        return 1.0, det

    # -- distributional accessors (what a mean cannot say) ------------------
    def hour_cell_at(self, symbol: str, account: str, at_utc: dt.datetime) -> dict | None:
        """The hour cell for a real instant, clock-aligned. Prefer this over `hour_cell`
        whenever the instant can fall on either side of a DST boundary."""
        key, _, _ = self._key_instant(at_utc)
        return self.hour_cell(symbol, account, key.hour)

    def hour_cell(self, symbol: str, account: str, hour_utc: int) -> dict | None:
        fsym = self.resolve(symbol, account)
        if fsym is None:
            return None
        acct = "redacted_account" if account.upper().startswith("FUNDED") else "FTMO"
        return self._acc[acct][fsym]["by_hour_utc"].get(str(hour_utc))

    def reference(self, symbol: str, account: str) -> dict | None:
        fsym = self.resolve(symbol, account)
        if fsym is None:
            return None
        acct = "redacted_account" if account.upper().startswith("FUNDED") else "FTMO"
        return self._acc[acct][fsym]["reference"]


def patch_spread_model(model, tape: "TapeHourly"):
    """Substitute the tape hour term into a live ``SpreadModel`` instance.

    The shipped model composes ``anchor x era_ratio x intraweek``; only the third factor
    is replaced.  The volatility-state sub-term is preserved -- it is a different axis and
    B10 measured nothing that bears on it.  Returns the original bound method so a caller
    can A/B without reconstructing the model.
    """
    original = model.intraweek_mult

    def patched(account, klass, at_utc, vol_state=None, vol_kind="trailing"):
        base, detail = original(account, klass, at_utc, vol_state, vol_kind)
        sym = getattr(model, "_b10_symbol", None)
        if sym is None or at_utc is None:
            return base, {**detail, "b10": "no symbol in scope; class term left in place"}
        h, d = tape.mult(sym, account, at_utc)
        v = detail.get("vol_mult")
        return h * float(v or 1.0), {**detail, "b10": d, "b10_hour_mult": h,
                                     "class_hour_mult": detail.get("hour_mult")}

    model.intraweek_mult = patched
    return original

"""KB7 tick-execution-truth library.

Loads ACTUAL bid/ask ticks (siliconmetatrader5 bridge, on-demand + cached) and replays the
already-decided trade entries/exits at TICK resolution to measure the TRUE execution erosion,
replacing the M1-bar approximation (next-M1-OPEN entry + 0.5*cost stop buffer) and the original
half-spread PROXY.

What tick measures that M1 cannot:
  (1) ENTRY slip: at the H4-signal-close instant, a market BUY fills at the ASK, a SELL at the BID
      of the first tick after close -> the true spread-paid entry vs the modeled close and the M1
      next-bar OPEN (which ignored spread entirely on entry, relying on the cost map for it).
  (2) STOP fill: a long's protective stop is a SELL that fills at the BID once BID<=stop_px; a
      short's at the ASK once ASK>=stop_px. The true fill = first crossing quote (which already
      embeds gap + spread), NOT level + a 0.5*cost guess.
  (3) LIMIT (scale/runner target) fill: a long's take-profit SELL fills at BID>=level; touch is
      measured on the correct quote side, not the mid/HTF-bar.

NO LOOKAHEAD: entries are unchanged (decided at H4 close). Tick only re-prices the fills.
Pessimism preserved within ambiguity: when a single tick is not enough to disambiguate, adverse
(stop) is resolved before favorable, same as the bar engines.

Costs: the modeled book R is ALREADY net of round-trip cost via w1.cost_for (spread+commission).
To avoid double-counting, the TICK measurement charges the REAL spread it observes at entry/exit
and then we report erosion = tick_R_gross_of_modelcost - modeled_R, where tick_R uses the SAME
cost subtraction as the model for the parts the cost map covers EXCEPT we replace the spread-driven
components with what ticks actually show. Concretely we compute two numbers per trade:
  tick_R_costmap : tick fills, then subtract the model cost map (apples-to-apples vs modeled R).
  tick_R_realspread : tick fills with the REAL observed spread charged on entry+exit, NO cost map
                      spread (commission-only residual added back) -> the honest live number.
"""
from __future__ import annotations
import sys, os, json, gzip, bisect, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

DATA = str(ROOT) + "/data/mt5_research_exports"
MICRO_DIR = DATA + "/bridge_ftmo_ticks_micro_2025_2026/ticks"
CACHE_DIR = HERE / "KB7_tick_cache"
CACHE_DIR.mkdir(exist_ok=True)

# file_symbol (underscore) -> bridge symbol (.cash/.c) for on-demand pulls
BRIDGE_SYM = {
    "USOIL_cash": "USOIL.cash", "UKOIL_cash": "UKOIL.cash",
    "NATGAS_cash": "NATGAS.cash", "HEATOIL_c": "HEATOIL.c",
    "XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD",
    "BTCUSD": "BTCUSD", "DASHUSD": "DASHUSD",
}

# -----------------------------------------------------------------------------
# Tick = (epoch_ms, bid, ask)
# -----------------------------------------------------------------------------
class TickStream:
    __slots__ = ("ms", "bid", "ask")
    def __init__(self, ms, bid, ask):
        self.ms = ms; self.bid = bid; self.ask = ask
    def __len__(self):
        return len(self.ms)
    def first_at_or_after(self, ts_ms):
        i = bisect.bisect_left(self.ms, ts_ms)
        return i if i < len(self.ms) else None


def _load_micro(file_sym):
    """Load the pre-exported microstructure tick jsonl(.gz) for a symbol. Returns TickStream
    or None. These cover XAUUSD/XAGUSD/EURUSD/USDJPY 2025-10-01..2026-04-30."""
    base = os.path.join(MICRO_DIR, file_sym, "microstructure_ticks.jsonl")
    paths = [base, base + ".gz"]
    p = next((x for x in paths if os.path.exists(x)), None)
    if p is None:
        return None
    op = gzip.open if p.endswith(".gz") else open
    ms = []; bid = []; ask = []
    with op(p, "rt") as f:
        for line in f:
            try:
                r = json.loads(line)
                tmsc = r.get("time_msc")
                b = r.get("bid"); a = r.get("ask")
                if tmsc is None or b is None or a is None:
                    continue
                ms.append(int(tmsc)); bid.append(float(b)); ask.append(float(a))
            except Exception:
                continue
    if not ms:
        return None
    return TickStream(ms, bid, ask)


_BRIDGE = None
def _bridge():
    global _BRIDGE
    if _BRIDGE is None:
        from siliconmetatrader5 import MetaTrader5
        c = MetaTrader5(host="localhost", port=8001, keepalive=True)
        c.initialize()
        _BRIDGE = c
    return _BRIDGE


def pull_ticks_window(file_sym, start_dt, end_dt, *, max_seconds=120):
    """On-demand bridge pull for [start,end] UTC. Caches per (sym,start,end) to disk.
    Returns list of (ms,bid,ask) rows or [] if none/unavailable. Bounded by max_seconds."""
    bsym = BRIDGE_SYM.get(file_sym, file_sym)
    key = f"{file_sym}_{int(start_dt.timestamp())}_{int(end_dt.timestamp())}.json"
    cpath = CACHE_DIR / key
    if cpath.exists():
        try:
            return json.loads(cpath.read_text())
        except Exception:
            pass
    c = _bridge()
    try:
        c.symbol_select(bsym, True)
        flags = c.COPY_TICKS_ALL
        t0 = time.time()
        ticks = c.copy_ticks_range(bsym, start_dt, end_dt, flags)
        if time.time() - t0 > max_seconds and (ticks is None or len(ticks) == 0):
            return []
        rows = []
        if ticks is not None:
            for t in ticks:
                try:
                    tmsc = int(t["time_msc"]); b = float(t["bid"]); a = float(t["ask"])
                    if b > 0 and a > 0:
                        rows.append((tmsc, b, a))
                except Exception:
                    continue
        rows.sort(key=lambda r: r[0])
        cpath.write_text(json.dumps(rows))
        return rows
    except Exception:
        return []


# Symbols whose on-disk micro export is huge (multi-GB) AND fully bridge-serviceable on its date
# range. For these we pull the BOUNDED window from the bridge first (fast, KBs of RAM) and only
# fall back to the full-file micro load when the bridge returns nothing. Loading the 6.6GB XAGUSD /
# 511MB XAUUSD micro just to slice a 13-day window stalls the run for minutes and ~2GB+ RAM.
PREFER_BRIDGE = {"XAUUSD", "XAGUSD", "USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c",
                 "BTCUSD", "DASHUSD"}


def load_window_stream(file_sym, start_dt, end_dt):
    """Return a TickStream for [start,end]. For PREFER_BRIDGE symbols pull the bounded window from
    the bridge first (no giant-file load); else use the on-disk micro export; else bridge. None if
    no coverage."""
    if file_sym in PREFER_BRIDGE:
        rows = pull_ticks_window(file_sym, start_dt, end_dt)
        if len(rows) >= 5:
            return TickStream([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])
        # bridge empty (e.g. pre-2024) -> try micro fallback below
    micro = _load_micro_cached(file_sym)
    if micro is not None:
        s_ms = int(start_dt.timestamp() * 1000); e_ms = int(end_dt.timestamp() * 1000)
        lo = bisect.bisect_left(micro.ms, s_ms); hi = bisect.bisect_right(micro.ms, e_ms)
        if hi - lo >= 5:
            return TickStream(micro.ms[lo:hi], micro.bid[lo:hi], micro.ask[lo:hi])
    rows = pull_ticks_window(file_sym, start_dt, end_dt)
    if len(rows) < 5:
        return None
    return TickStream([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])


_MICRO_CACHE = {}
def _load_micro_cached(file_sym):
    if file_sym not in _MICRO_CACHE:
        _MICRO_CACHE[file_sym] = _load_micro(file_sym)
    return _MICRO_CACHE[file_sym]


def micro_coverage(file_sym):
    m = _load_micro_cached(file_sym)
    if m is None:
        return None
    return (datetime.fromtimestamp(m.ms[0] / 1000, tz=timezone.utc),
            datetime.fromtimestamp(m.ms[-1] / 1000, tz=timezone.utc), len(m))


# -----------------------------------------------------------------------------
# Tick-resolution exit. Mirrors EXEC_REALISM_m1_lib.realistic_exit but on QUOTES:
#   long  : favorable = BID rising to TP level; adverse = BID falling to stop.
#           entry fills at ASK; TP/scale SELL fills at BID; stop SELL fills at BID.
#   short : favorable = ASK falling to TP; adverse = ASK rising to stop.
#           entry fills at BID; TP BUY fills at ASK; stop BUY fills at ASK.
# This is the live OCO semantics: protective stop and TP are exit (closing) orders, which trade
# at the opposite quote from a market entry. R is measured in price/sd from the ACTUAL entry fill.
# Pessimism: within the scan, the stop (adverse) is tested before the TP (favorable) on each tick.
# -----------------------------------------------------------------------------
def tick_exit(ts: "TickStream", start_i, entry_px, d, sd, *, ladder, be_after_first, runner_R,
              end_ms):
    if sd <= 0 or len(ts) == 0:
        return dict(R=0.0, reason="bad_sd", n_legs=0, exit_i=start_i, mfe=0.0)
    legs = list(ladder)
    pos = 1.0; booked = 0.0
    runner_stop_R = -1.0
    n_legs = 0; mfe = 0.0; reason = "open"
    n = len(ts)
    j = start_i + 1
    while j < n and ts.ms[j] <= end_ms:
        bid = ts.bid[j]; ask = ts.ask[j]
        # exit (closing) quote: long sells at BID, short buys at ASK
        close_q = bid if d > 0 else ask
        fav = d * (close_q - entry_px) / sd
        adv = fav  # for a closing position the same quote governs both stop and TP
        if fav > mfe:
            mfe = fav
        stop_px = entry_px + d * runner_stop_R * sd
        # ---- adverse (stop) FIRST (pessimistic) ----
        crossed_stop = (close_q <= stop_px) if d > 0 else (close_q >= stop_px)
        if crossed_stop or adv <= runner_stop_R:
            fill = close_q   # real quote at/through the stop already embeds gap+spread
            r = d * (fill - entry_px) / sd
            booked += pos * r; pos = 0.0
            reason = ("stop" if n_legs == 0 else
                      ("be_scratch" if abs(runner_stop_R) < 1e-9 else "runner_stop"))
            return dict(R=booked, reason=reason, n_legs=n_legs, exit_i=j, mfe=mfe)
        # ---- ladder TP legs (limit SELL/BUY at level on the closing quote) ----
        while legs and fav >= legs[0][0]:
            lvl, frac = legs.pop(0)
            f = min(frac, pos)
            booked += f * lvl; pos -= f; n_legs += 1
            if n_legs == 1:
                runner_stop_R = be_after_first
        if pos <= 1e-9:
            return dict(R=booked, reason="ladder_complete", n_legs=n_legs, exit_i=j, mfe=mfe)
        # ---- runner fixed target ----
        if runner_R is not None and fav >= runner_R:
            booked += pos * runner_R; pos = 0.0
            return dict(R=booked, reason="runner_target", n_legs=n_legs, exit_i=j, mfe=mfe)
        j += 1
    # horizon close at last closing quote
    last = min(j, n - 1)
    close_q = ts.bid[last] if d > 0 else ts.ask[last]
    booked += pos * d * (close_q - entry_px) / sd
    return dict(R=booked, reason="market_close", n_legs=n_legs, exit_i=last, mfe=mfe)


def entry_fill(ts: "TickStream", start_i, d):
    """Market entry at first tick >= signal close: long fills at ASK, short at BID. Returns
    (entry_px, half_spread_price)."""
    bid = ts.bid[start_i]; ask = ts.ask[start_i]
    px = ask if d > 0 else bid
    return px, (ask - bid) / 2.0

#!/usr/bin/env python3
"""Build the F5 decision->fill->outcome ledger: one JSONL row per candidate_id.

One artifact, three consumers (judgment scoring, atlas candidate labels, banana table).

IN-REPO COPY (scripts/f5_harvest/, 2026-08-25): extends the f5-harvest original
with (1) broker-deals authority join (deals_f5_*.json from dump_f5_deals.py:
per-ticket broker entry/exit price/time/commission/swap, entry-price + initial-
stop fallback for tickets whose trade-record JSON never reached this machine),
(2) per-day broker-vs-ledger reconciliation written to
<root>/f5_broker_reconciliation.json, (3) multi-dir BarStore (bars-aug-extension
+ bars_f5 dumps merged per symbol) so excursion survives a stale tape,
(4) fill-event dedupe by ticket (earliest wins; re-emissions and dual sleeve
attributions become join_quality flags, never extra rows), and (5) a top-level
``era`` field (f5_intended_risk_usd: 10 vs 75) on every row.

Usage:
    build_f5_outcome_ledger.py <dated-harvest-dir> [--date YYYY-MM-DD]
        [--records-dir DIR] [--bars-dir DIR ...] [--out-cumulative PATH]
    build_f5_outcome_ledger.py --vps-live --out-ticket-ledger PATH
        [--ticket-since YYYY-MM-DD]

Reads (all read-only). Mac harvest copies live under dated dirs; on the VPS the
same files sit in pipeline_state / shadow_logs. --vps-live (and the fallbacks
below) open those live paths instead of stamping fill_event=false /
placement_ledger=false when the dated copies are absent.

  <root>/<day>/execution_manager_v4_decisions.jsonl   exec-manager decision rows
  <root>/<day>/events.jsonl                           F5 event stream:
                                                      f5_fill / f5_trade_closed / f5_stop_move /
                                                      f5_refusal_quote / f5_slate
  shadow_logs/f5_minimal/operator/events.jsonl live VPS events (fallback)
  <root>/<day>/slippage_runtime.jsonl                 requested-vs-filled per order_send
  <root>/trade_records/*.json                         per-ticket broker-truth records
                                                      (host-local)
  <root>/trade_records/placed_decisions.jsonl         Mac harvest copy of placement ledger
  <records-dir>/../placed_decisions.jsonl             live VPS placement ledger (sibling of
                                                      trade_records/, NOT inside it)
  <root>/trade_records/f5_notional_ledger.json        notional/real-PnL state (cross-check)
  --bars-dir/<SYM>_M15.csv                            FTMO M15 OHLC for MFE/MAE (broker wall clock)

Also merges events/decisions rows found in EVERY other dated dir under the root
(dedup by exact content), so a future VPS-side log rotation cannot lose history.

Writes:
  <dated-dir>/outbox/f5_outcome_ledger_<date>.jsonl   rows with activity on <date>
  <root>/f5_outcome_ledger_cumulative.jsonl           all rows, sorted by row_key_time_utc
  --out-ticket-ledger PATH                            gtos.f5.outcome_ledger.vps_ticket.v1
                                                      (one row per integer position ticket)
  (each with a sibling .sha256)

UNITS DOCTRINE (binding, from CLAUDE.md section 7): dollars are broker-true USD on the
FTMO account (basis named per block); R appears only with its denominator named -- the
trade's own initial stop distance. At F5's fixed $10 intended risk, R is faithful for
money and treacherous for movement.

HINDSIGHT DOCTRINE: rows are keyed by decision time. Everything known only later lives
under "later_known" with an explicit _note; consumers building decision-time features
must never read inside "later_known".

CONSUMERS -- regenerate the week/banana trade table from the cumulative ledger with:

    import json
    rows = [json.loads(l) for l in open(
        "/Users/borr/GTOSActive/f5-harvest/f5_outcome_ledger_cumulative.jsonl")]
    filled = sorted((r for r in rows if r["outcome_class"] == "FILLED_CLOSED"),
                    key=lambda r: r["later_known"]["fill"]["broker_fill_time_utc"])
    total = sum(r["later_known"]["lifecycle"]["dollars"]["net_usd"] for r in filled)
    # total MUST reconcile with trade_records/f5_notional_ledger.json
    # (real_pnl_usd_cumulative); the build prints the same check as
    # notional_ledger_check.reconciles.

Stdlib only; compatible with macOS system python3 (3.9).
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

SCHEMA = "gtos.f5.outcome_ledger.v1"
TICKET_SCHEMA = "gtos.f5.outcome_ledger.vps_ticket.v1"
TICKET_JOIN_KEY = "integer_position_ticket"

LATER_KNOWN_NOTE = ("OUTCOME DATA -- unknown at decision time. Never use anything under "
                    "later_known as a decision-time feature.")
TICKET_LATER_NOTE = ("OUTCOME DATA -- unknown at decision time. Do not use as a "
                     "decision-time feature.")

R_DENOMINATOR_NOTE = ("R = dollars / trade's own initial stop distance risk. Faithful for money "
                      "at F5's fixed $10 intended risk; treacherous for movement across trades "
                      "(the stop is our choice, not the market's).")


# ----------------------------------------------------------------- small utils
def read_jsonl(path):
    rows, bad = [], 0
    if not os.path.isfile(path):
        return rows, bad, False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad, True


def read_jsonl_multi(paths):
    """Merge JSONL rows across files, deduping by exact canonical content."""
    seen = set()
    out = []
    bad = 0
    used = []
    for p in paths:
        rows, b, ok = read_jsonl(p)
        bad += b
        if not ok:
            continue
        used.append(p)
        for r in rows:
            key = hashlib.sha256(
                json.dumps(r, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
    return out, bad, used


def parse_iso(ts):
    if not ts:
        return None
    ts = str(ts)
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        d = datetime.fromisoformat(ts)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def iso_offset(dt):
    """Aware UTC datetime -> explicit +00:00 stamp (ticket-ledger contract)."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def locked_r_from_stop(stop_now, entry, initial_sl, direction):
    """Direction-signed locked R vs the trade's own initial stop distance.

    Convention (LOCKEDR-FIX / OPUS-F5-MAXVALUE §2.2):
      locked_r = dir_sign * (stop_now - entry) / |entry - initial_sl|
      dir_sign = +1 LONG, -1 SHORT
    Denominator is the initial risk (entry vs initial SL) and does not
    change when the trail arms. Untouched initial stop => -1.0R (nothing
    locked; the full 1R of open risk remains). Positive = profit locked.
    Event-stream locked_r is not used: it is unsigned on SHORT and
    re-denominates by the previous lock after the trail arms.
    """
    if not (is_num(stop_now) and is_num(entry) and is_num(initial_sl)):
        return None
    d = str(direction or "").upper()
    if d == "LONG":
        sign = 1.0
    elif d == "SHORT":
        sign = -1.0
    else:
        return None
    denom = abs(entry - initial_sl)
    if denom == 0:
        return None
    return sign * (stop_now - entry) / denom


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------- broker clock (FTMO)
# Measured rule (CLAUDE.md section 4 + src/utils/broker_clock.py): FTMO-Server3 wall clock
# == America/New_York + 7 h, i.e. UTC+3 under US DST, UTC+2 otherwise. Inversion by
# candidate check, pre-transition offset (+3) tried first, mirroring broker_clock.py's
# fold=0 behaviour for the repeated autumn hour.
try:
    from zoneinfo import ZoneInfo
    _NY = ZoneInfo("America/New_York")
except Exception:                                    # pragma: no cover
    _NY = None


def broker_naive_to_utc(naive):
    """Broker wall-clock naive datetime -> aware UTC datetime."""
    for cand_hours in (3, 2):
        utc = (naive - timedelta(hours=cand_hours)).replace(tzinfo=timezone.utc)
        if _NY is None:
            return utc                               # degraded: assume summer (+3)
        ny = utc.astimezone(_NY)
        offset = 7 - (ny.utcoffset().total_seconds() / 3600.0 + 5)  # +3 if DST else +2
        if int(offset) + 2 == cand_hours or (ny.replace(tzinfo=None)
                                             + timedelta(hours=7)) == naive:
            return utc
    return (naive - timedelta(hours=3)).replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------ M15 bars
class BarStore(object):
    """Lazy per-symbol M15 OHLC store. Times converted broker wall clock -> UTC.

    Accepts ONE dir (str, backward-compatible) or a LIST of dirs. Bars for a
    symbol are merged across every dir that has a matching file, deduped by
    bar-open time (first source wins on collision), so a fresh bars_f5 dump
    extends a stale bars-aug-extension tape instead of replacing it.
    """

    def __init__(self, bars_dir):
        if bars_dir is None:
            dirs = []
        elif isinstance(bars_dir, (list, tuple)):
            dirs = [d for d in bars_dir if d and os.path.isdir(d)]
        else:
            dirs = [bars_dir] if os.path.isdir(bars_dir) else []
        self.bars_dirs = dirs
        self.bars_dir = dirs[0] if dirs else None   # back-compat attribute
        self._cache = {}
        self.manifest = None
        for d in dirs:
            mp = os.path.join(d, "manifest.json")
            if os.path.isfile(mp):
                try:
                    self.manifest = json.load(open(mp, encoding="utf-8"))
                except Exception:
                    self.manifest = None
                break

    def _candidates(self, symbol, broker_symbol):
        names = []
        if broker_symbol:
            names.append(str(broker_symbol) + "_M15.csv")  # dot form (aug-extension: US500.cash_M15.csv)
            names.append(str(broker_symbol).replace(".", "_") + "_M15.csv")
        if symbol:
            names.append(str(symbol) + "_M15.csv")
            names.append(str(symbol).replace(".", "_") + "_M15.csv")
            names.append(str(symbol) + "_cash_M15.csv")
        out, seen = [], set()
        for n in names:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out

    def _read_file(self, path):
        """Read one CSV -> list of (utc_open, high, low), honouring the timebase law."""
        rows = []
        # Timebase law: a CSV with a .timebase.json sidecar declaring
        # time_column_basis == "true_utc" is ALREADY UTC — converting it as
        # broker-wall shifts every window 3-7h (the exact misread that made
        # LIFECYCLE-DAY3 see a tape ending 01:45Z when it reached 04:45Z).
        is_true_utc = False
        try:
            with open(path + ".timebase.json", encoding="utf-8") as tb:
                is_true_utc = json.load(tb).get("time_column_basis") == "true_utc"
        except Exception:
            pass
        with open(path, newline="", encoding="utf-8", errors="replace") as fh:
            for rec in csv.DictReader(fh):
                try:
                    naive = datetime.strptime(rec["time"], "%Y-%m-%d %H:%M:%S")
                    ts = naive.replace(tzinfo=timezone.utc) if is_true_utc else broker_naive_to_utc(naive)
                    rows.append((ts, float(rec["high"]), float(rec["low"])))
                except Exception:
                    continue
        return rows

    def bars(self, symbol, broker_symbol):
        """Return (list of (utc_open, high, low), source_names) or (None, reason).

        Merges every matching file across every configured dir; first source
        wins per bar-open time. Sorted ascending by time.
        """
        if not self.bars_dirs:
            return None, "no_bars_dir"
        key = (symbol, broker_symbol)
        if key in self._cache:
            return self._cache[key]
        merged = {}
        used = []
        errors = []
        for d in self.bars_dirs:
            for name in self._candidates(symbol, broker_symbol):
                path = os.path.join(d, name)
                if not os.path.isfile(path):
                    continue
                try:
                    rows = self._read_file(path)
                except Exception as exc:
                    errors.append("read_error:%s:%r" % (name, exc))
                    continue
                if not rows:
                    continue
                used.append(name)
                for (ts, h, l) in rows:
                    merged.setdefault(ts, (ts, h, l))
                break     # one file per dir; other dirs may extend coverage
        if not merged:
            reason = errors[0] if errors else (
                "no_file:%s" % ",".join(self._candidates(symbol, broker_symbol)))
            result = (None, reason)
        else:
            result = (sorted(merged.values(), key=lambda x: x[0]), "+".join(used))
        self._cache[key] = result
        return result


def excursion(store, symbol, broker_symbol, direction, entry_price, stop_distance,
              actual_risk_usd, t_fill, t_exit):
    """MFE/MAE over M15 bars from fill to exit, inclusive of boundary bars.

    Basis (named): FTMO-Server3 M15 OHLC (MT5 bid-basis bars), broker wall clock
    converted to UTC by the measured NY+7h rule; bar granularity, so the fill bar's
    pre-fill range and the exit bar's post-exit range contaminate the extremes
    (conservative overstatement both ways). Dollars via the risk-linear identity
    usd = price_excursion / stop_distance * f5_actual_risk_usd.
    """
    if t_fill is None or t_exit is None:
        return {"status": "no_fill_or_exit_time"}
    bars, src = store.bars(symbol, broker_symbol)
    if bars is None:
        return {"status": "bars_unavailable", "reason": src}
    lo_bound = t_fill - timedelta(minutes=15)
    window = [(t, h, l) for (t, h, l) in bars if lo_bound < t <= t_exit]
    if not window:
        return {"status": "bars_not_covering_window", "reason": src}
    # W9A amendment (LIFECYCLE-DAY3): a tape whose last bar ends before the exit
    # bar yields a prefix, not a fill-to-exit excursion. Require the newest
    # covered bar to open within one bar-interval of t_exit, else refuse.
    last_covered = max(t for (t, _, _) in window)
    if t_exit - last_covered > timedelta(minutes=30):
        return {"status": "window_truncated", "reason": src,
                "last_bar_utc": last_covered.isoformat(),
                "exit_utc": t_exit.isoformat(),
                "n_bars_prefix": len(window)}
    hi = max(h for _, h, _ in window)
    lo = min(l for _, _, l in window)
    if direction == "LONG":
        mfe_price, mae_price = hi - entry_price, entry_price - lo
    else:
        mfe_price, mae_price = entry_price - lo, hi - entry_price
    out = {
        "status": "ok",
        "basis": ("FTMO M15 OHLC (bid-basis bars, broker wall clock -> UTC via NY+7h rule); "
                  "boundary bars included whole, so extremes can overstate; "
                  "usd = price / initial_stop_distance * f5_actual_risk_usd"),
        "source_file": src,
        "n_bars": len(window),
        "mfe_price": round(mfe_price, 10),
        "mae_price": round(mae_price, 10),
    }
    if is_num(stop_distance) and stop_distance > 0:
        out["mfe_r"] = round(mfe_price / stop_distance, 6)
        out["mae_r"] = round(mae_price / stop_distance, 6)
        if is_num(actual_risk_usd):
            out["mfe_usd"] = round(mfe_price / stop_distance * actual_risk_usd, 4)
            out["mae_usd"] = round(mae_price / stop_distance * actual_risk_usd, 4)
    return out


# ----------------------------------------------------- launcher skip mining
# The launcher slate rows are the ONLY refusal evidence before the frozen-intent
# deploy (f5_refusal_quote exists from 2026-08-17). A dict entry in `skipped`
# carries symbol/sleeve/decision_bar_iso/reason. Kinds:
#   row-creating refusals (signal was due and was turned away):
LAUNCHER_REFUSAL_KINDS = {
    "cost_screen_spread_r", "pretrade_cost", "model_input_invalid_stop",
    "stale_late_entry_after_restart", "stale_tick_market_closed",
    "chase_stop_fraction", "hard_expiry_seconds", "order_rejected",
    "exec_mgr_v4", "runtime_halt_blocked",
}
#   attach-only idempotency guards (never create a row):
LAUNCHER_ATTACH_ONLY_KINDS = {
    "already_placed_this_bar", "already_placed_today", "sleeve_already_holds_symbol",
}
#   dropped as scheduling noise (bar not yet due), counted only:
LAUNCHER_NOISE_KINDS = {"future_decision_bar_time"}


def load_launcher_skips(paths):
    """Extract deduped dict-skips from launcher slate files (full pulls + 256k tails).

    Returns (skips, n_noise, n_bare) where skips is a list of
    {ts, symbol, sleeve, decision_bar_iso, reason, kind}.
    """
    seen = set()
    out = []
    n_noise = n_bare = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue   # 256k tails may start mid-line; that partial is in the full pull
                ts = str(r.get("ts", ""))
                for s in r.get("skipped") or []:
                    if not isinstance(s, dict):
                        n_bare += 1
                        continue
                    reason = str(s.get("reason", ""))
                    kind = reason.split(":", 1)[0]
                    if kind in LAUNCHER_NOISE_KINDS:
                        n_noise += 1
                        continue
                    key = (ts, s.get("symbol"), s.get("sleeve"),
                           str(s.get("decision_bar_iso")), reason)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"ts": ts, "symbol": s.get("symbol"),
                                "sleeve": s.get("sleeve"),
                                "decision_bar_iso": s.get("decision_bar_iso"),
                                "reason": reason, "kind": kind})
    out.sort(key=lambda x: x["ts"])
    return out, n_noise, n_bare


# -------------------------------------------------------------- field pulls
def candidate_direction(candidate_id):
    for part in str(candidate_id or "").split("::"):
        if part in ("LONG", "SHORT"):
            return part
    return None


def short_reasons(reason_lists):
    out = []
    for reasons in reason_lists:
        for r in reasons or []:
            head = str(r).split(" (", 1)[0]
            if head not in out:
                out.append(head)
    return out


def dec_identity(row):
    return row.get("identity") or {}


def load_trade_records(records_dir):
    recs = {}
    for path in sorted(glob.glob(os.path.join(records_dir, "[0-9]*.json"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        if not stem.isdigit():
            continue          # skip 123.pre_sit_repair.json backups; never overwrite live
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        t = ((d.get("execution") or {}).get("ticket")) or d.get("ticket") or stem
        try:
            recs[int(t)] = d
        except Exception:
            continue
    return recs


# ------------------------------------------------------ broker deals authority
# dump_f5_deals.py (VPS, read-only) writes deals_f5_<stamp>.json: every deal +
# history order with magic 0, raw broker-epoch times (broker wall clock,
# NOT UTC — CLAUDE.md section 4). This is the broker-truth spine: it exists for
# every ticket the account ever traded, including tickets whose per-ticket
# trade-record JSON never reached this machine.
DEAL_ENTRY_IN = 0        # MT5 DEAL_ENTRY_IN
DEAL_ENTRY_OUT = 1       # DEAL_ENTRY_OUT
DEAL_ENTRY_INOUT = 2     # reversal
DEAL_ENTRY_OUT_BY = 3    # close-by
_TRADE_DEAL_TYPES = (0, 1)   # DEAL_TYPE_BUY / DEAL_TYPE_SELL only


def _deal_epoch_wall_naive(epoch):
    """Raw MT5 epoch as naive broker-wall datetime (dump_f5_deals time_broker_iso)."""
    if not is_num(epoch) or epoch <= 0:
        return None
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).replace(tzinfo=None)


def _deal_epoch_to_utc(epoch):
    """Broker-basis MT5 epoch -> aware UTC datetime (never trust it as UTC)."""
    naive = _deal_epoch_wall_naive(epoch)
    if naive is None:
        return None
    return broker_naive_to_utc(naive)


def _deal_wall_stamp(deal):
    if not deal:
        return None
    iso_s = deal.get("time_broker_iso")
    if iso_s:
        return str(iso_s)
    naive = _deal_epoch_wall_naive(deal.get("time"))
    return naive.strftime("%Y-%m-%d %H:%M:%S") if naive else None


def load_broker_deals(paths):
    """Merge deals_f5_*.json dumps -> (positions, meta).

    positions: {position_id: {symbol, entry_price, entry_time_utc, entry_volume,
                              exit_price, exit_time_utc, n_entry_deals,
                              n_exit_deals, gross_profit_usd, commission_usd,
                              swap_usd, fee_usd, net_usd, sl, tp,
                              stop_distance_price, deal_tickets}}
    meta: {"files": [...], "n_deals": int, "n_orders": int,
           "window_utc": [min_iso, max_iso]}
    Deals are deduped across files by deal ticket; orders by order ticket.
    """
    deals = {}
    orders = {}
    files = []
    for p in paths:
        if not os.path.isfile(p):
            continue
        try:
            doc = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        files.append(os.path.basename(p))
        for d in doc.get("deals") or []:
            t = d.get("ticket")
            if t is not None:
                deals.setdefault(int(t), d)
        for o in doc.get("orders") or []:
            t = o.get("ticket")
            if t is not None:
                orders.setdefault(int(t), o)
    positions = {}
    times = []
    by_pos = {}
    for d in deals.values():
        if d.get("type") not in _TRADE_DEAL_TYPES:
            continue          # balance/credit ops are not trades
        pid = d.get("position_id")
        if pid is None:
            continue
        by_pos.setdefault(int(pid), []).append(d)
    orders_by_pos = {}
    for o in orders.values():
        pid = o.get("position_id")
        if pid is not None:
            orders_by_pos.setdefault(int(pid), []).append(o)
    for pid, ds in by_pos.items():
        ds.sort(key=lambda d: (d.get("time") or 0, d.get("ticket") or 0))
        entries = [d for d in ds if d.get("entry") == DEAL_ENTRY_IN]
        exits = [d for d in ds if d.get("entry") in (
            DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY)]
        first_in = entries[0] if entries else None
        last_out = exits[-1] if exits else None

        def _sum(field):
            return round(sum(float(d.get(field) or 0.0) for d in ds), 4)

        sl = tp = None
        for o in sorted(orders_by_pos.get(pid, []),
                        key=lambda o: (o.get("time_setup") or 0)):
            if sl is None and is_num(o.get("sl")) and o.get("sl"):
                sl = o.get("sl")
            if tp is None and is_num(o.get("tp")) and o.get("tp"):
                tp = o.get("tp")
        entry_price = (first_in or {}).get("price")
        stop_dist = None
        if is_num(entry_price) and is_num(sl) and sl:
            stop_dist = abs(entry_price - sl)
        t_in = _deal_epoch_to_utc((first_in or {}).get("time"))
        t_out = _deal_epoch_to_utc((last_out or {}).get("time"))
        for t in (t_in, t_out):
            if t:
                times.append(t)
        positions[pid] = {
            "basis": ("broker deals dump (dump_f5_deals.py, magic-filtered); "
                      "times broker wall clock -> UTC via NY+7h rule; dollars "
                      "are broker USD per deal fields"),
            "time_column_basis": "true_utc",
            "broker_clock_rule": "new_york_plus_7",
            "symbol": (first_in or (ds[0] if ds else {})).get("symbol"),
            "entry_price": entry_price,
            "entry_time_utc": iso(t_in),
            "entry_time_broker_wall": _deal_wall_stamp(first_in),
            "entry_volume_lots": (first_in or {}).get("volume"),
            "exit_price": (last_out or {}).get("price"),
            "exit_time_utc": iso(t_out),
            "exit_time_broker_wall": _deal_wall_stamp(last_out),
            "n_entry_deals": len(entries),
            "n_exit_deals": len(exits),
            "gross_profit_usd": _sum("profit"),
            "commission_usd": _sum("commission"),
            "swap_usd": _sum("swap"),
            "fee_usd": _sum("fee"),
            "net_usd": round(_sum("profit") + _sum("commission")
                             + _sum("swap") + _sum("fee"), 4),
            "sl": sl,
            "tp": tp,
            "stop_distance_price": stop_dist,
            "deal_tickets": [d.get("ticket") for d in ds],
        }
    meta = {"files": files, "n_deals": len(deals), "n_orders": len(orders),
            "window_utc": [iso(min(times)) if times else None,
                           iso(max(times)) if times else None]}
    return positions, meta


def era_label(v):
    """f5_intended_risk_usd -> stratum label ('$10' / '$75' / 'unknown').
    Shared convention with summarize_f5_daily.era_key."""
    if is_num(v):
        if abs(v - 75.0) < 0.5:
            return "$75"
        if abs(v - 10.0) < 0.5:
            return "$10"
        return "$%g" % v
    return "unknown"


def broker_reconciliation(positions, rows, day_tolerance_usd=0.01,
                          window_utc=None):
    """Per-day, era-stratified sum(broker deal net) vs sum(ledger net).

    A day is reconcilable only when it lies inside the deals-dump window
    (``window_utc`` = [min_iso, max_iso] from load_broker_deals meta) — outside
    it the broker side is absent by construction, status NOT_COVERED_BY_DUMP.
    Day attribution: broker side by exit_time_utc day of each closed position;
    ledger side by lifecycle.broker_exit_time_utc day (fallback close-event day
    already folded into that field by build_rows).
    """
    ledger_by_ticket = {}
    for r in rows:
        lk = r.get("later_known") or {}
        f = lk.get("fill") or {}
        if f.get("ticket") is not None:
            ledger_by_ticket[int(f["ticket"])] = r

    days = {}

    def _day_slot(day):
        return days.setdefault(day, {
            "broker_net_usd": 0.0, "broker_n": 0,
            "ledger_net_usd": 0.0, "ledger_n": 0,
            "broker_net_by_era": {}, "ledger_net_by_era": {},
            "tickets_broker_only": [], "tickets_ledger_only": []})

    for pid, pos in positions.items():
        if not pos.get("exit_time_utc") or pos.get("n_exit_deals", 0) == 0:
            continue     # still open at dump time: nothing to reconcile yet
        day = str(pos["exit_time_utc"])[:10]
        slot = _day_slot(day)
        net = pos.get("net_usd") or 0.0
        slot["broker_net_usd"] += net
        slot["broker_n"] += 1
        lrow = ledger_by_ticket.get(pid)
        if lrow is not None:
            era = era_label(lrow.get("era"))
        else:
            era = "unknown"
            slot["tickets_broker_only"].append(pid)
        slot["broker_net_by_era"][era] = round(
            slot["broker_net_by_era"].get(era, 0.0) + net, 4)
    for t, r in ledger_by_ticket.items():
        lk = r.get("later_known") or {}
        lc = lk.get("lifecycle") or {}
        if lc.get("status") != "CLOSED":
            continue
        exit_day = str(lc.get("broker_exit_time_utc") or "")[:10]
        if not exit_day:
            continue
        slot = _day_slot(exit_day)
        net = ((lc.get("dollars") or {}).get("net_usd"))
        if is_num(net):
            slot["ledger_net_usd"] += net
            slot["ledger_n"] += 1
            era = era_label(r.get("era"))
            slot["ledger_net_by_era"][era] = round(
                slot["ledger_net_by_era"].get(era, 0.0) + net, 4)
        if t not in positions:
            slot["tickets_ledger_only"].append(t)

    lo = str((window_utc or [None, None])[0] or "")[:10] or None
    hi = str((window_utc or [None, None])[1] or "")[:10] or None
    out = OrderedDict()
    for day in sorted(days):
        slot = days[day]
        # a ledger day OUTSIDE the dump window is not a failure — the broker
        # side simply was not dumped for it.
        in_window = (slot["broker_n"] > 0
                     or (lo is not None and hi is not None and lo <= day <= hi))
        diff = round(slot["broker_net_usd"] - slot["ledger_net_usd"], 4)
        out[day] = {
            "broker_net_usd": round(slot["broker_net_usd"], 4),
            "broker_n_closed": slot["broker_n"],
            "ledger_net_usd": round(slot["ledger_net_usd"], 4),
            "ledger_n_closed": slot["ledger_n"],
            "diff_usd": diff,
            "broker_net_by_era": slot["broker_net_by_era"],
            "ledger_net_by_era": slot["ledger_net_by_era"],
            "tickets_broker_only": sorted(slot["tickets_broker_only"]),
            "tickets_ledger_only": sorted(slot["tickets_ledger_only"]),
            "status": ("NOT_COVERED_BY_DUMP" if not in_window else
                       ("RECONCILED" if abs(diff) <= day_tolerance_usd
                        else "FAILED")),
        }
    return out


# ------------------------------------------------------------------- build
def _bar_norm(bar):
    d = parse_iso(bar)
    return iso(d) if d else str(bar or "")


def build_rows(dec_rows, events, slip_rows, placed_rows, trade_records, store,
               launcher_skips=None, broker_deals=None):
    fills = [e for e in events if e.get("event") == "f5_fill"]
    closes = [e for e in events if e.get("event") == "f5_trade_closed"]
    moves = [e for e in events if e.get("event") == "f5_stop_move"]
    refs = [e for e in events if e.get("event") == "f5_refusal_quote"]

    # --- join maps -------------------------------------------------------
    ticket_to_cand = OrderedDict()
    cand_to_tickets = OrderedDict()
    placed_by_ticket = {}
    for p in placed_rows:
        t, c = p.get("ticket"), p.get("candidate_id")
        if t is None:
            continue
        placed_by_ticket[int(t)] = p
        if c:
            ticket_to_cand.setdefault(int(t), c)
            cand_to_tickets.setdefault(c, []).append(int(t))
    for e in fills:
        t, c = e.get("ticket"), e.get("candidate_id")
        if t is None or not c:
            continue
        prev = ticket_to_cand.get(int(t))
        if prev and prev != c:
            pass  # flagged later
        ticket_to_cand.setdefault(int(t), c)
        if int(t) not in (cand_to_tickets.get(c) or []):
            cand_to_tickets.setdefault(c, []).append(int(t))
    for t, rec in trade_records.items():
        c = rec.get("candidate_id")
        if c:
            ticket_to_cand.setdefault(t, c)
            if t not in (cand_to_tickets.get(c) or []):
                cand_to_tickets.setdefault(c, []).append(t)

    # ---- fill-event dedupe: ONE ticket == ONE economic row -----------------
    # Two duplication modes measured on the live stream (2026-08-24):
    #   (a) dual sleeve attribution — the engine emitted two f5_fill rows for
    #       one ticket in the same millisecond with different `sleeve` fields
    #       (178065119, 178147925: dsp_isolated_flush_to_20low_snap vs
    #       dsp_isolated_spike_high; candidate_id identical);
    #   (b) restart re-emission — the fill row re-appears days later on book
    #       restart (177951277 fills at 08-23T22:00 and again 08-24T04:13 and
    #       08-24T06:16), which put one ticket in two day-lists.
    # Policy: keep the EARLIEST fill event; when sleeves conflict prefer the
    # one matching the candidate_id's own sleeve tail (the placement-ledger
    # sleeve wins at row level regardless); record both modes in join_quality.
    fill_by_ticket = {}
    fill_dup_flags = {}    # ticket -> set of flags
    for e in sorted(fills, key=lambda x: str(x.get("ts_utc", ""))):
        if e.get("ticket") is None:
            continue
        t = int(e["ticket"])
        prev = fill_by_ticket.get(t)
        if prev is None:
            fill_by_ticket[t] = e
            continue
        flags_t = fill_dup_flags.setdefault(t, set())
        if str(e.get("ts_utc", ""))[:10] != str(prev.get("ts_utc", ""))[:10]:
            flags_t.add("fill_event_reemitted_on_later_day")
        else:
            flags_t.add("duplicate_fill_event_same_day")
        if e.get("sleeve") != prev.get("sleeve"):
            flags_t.add("duplicate_sleeve_attribution_fill_events")
            # prefer the event whose sleeve matches the candidate's own tail
            cand_tail = str(prev.get("candidate_id") or "").split("::")[-1]
            if e.get("sleeve") == cand_tail and prev.get("sleeve") != cand_tail:
                e2 = dict(e)
                e2["ts_utc"] = prev.get("ts_utc")   # keep earliest time
                fill_by_ticket[t] = e2
    close_by_ticket = {}
    for e in sorted(closes, key=lambda x: str(x.get("ts_utc", ""))):
        if e.get("ticket") is not None:
            close_by_ticket.setdefault(int(e["ticket"]), e)
    moves_by_ticket = {}
    for e in moves:
        if e.get("ticket") is not None:
            moves_by_ticket.setdefault(int(e["ticket"]), []).append(e)
    slip_by_ticket = {}
    for s in slip_rows:
        t = s.get("ticket") or s.get("order_ticket")
        if t:
            slip_by_ticket.setdefault(int(t), []).append(s)

    # --- candidate spine ---------------------------------------------------
    spine = OrderedDict()   # cid -> dict of source rows

    def slot(cid):
        return spine.setdefault(cid, {"dec": [], "refs": [], "tickets": []})

    for r in sorted(dec_rows, key=lambda x: str(x.get("generated_at_utc", ""))):
        cid = dec_identity(r).get("candidate_id")
        if cid:
            slot(cid)["dec"].append(r)
    for e in sorted(refs, key=lambda x: str(x.get("ts_utc", ""))):
        cid = e.get("candidate_id")
        if not cid:
            cid = "UNIDENTIFIED::%s::%s::%s" % (
                e.get("symbol"), e.get("sleeve"), e.get("decision_bar_iso"))
        slot(cid)["refs"].append(e)
    for cid, tickets in cand_to_tickets.items():
        slot(cid)["tickets"] = sorted(set(tickets))

    # --- launcher skip attachment ------------------------------------------
    # Match a skip to a candidate by (symbol, sleeve, bar-date == cid decision_day);
    # unmatched refusal-kind skips become their own rows (pre-exec refusals that
    # produced no exec-manager row and no f5_refusal_quote event -- the pre-08-17 world).
    def _cid_parts(cid):
        p = str(cid).split("::")
        return {"cluster": p[1] if len(p) > 1 else None,
                "symbol": p[2] if len(p) > 2 else None,
                "day": p[3] if len(p) > 3 else None,
                "sleeve": p[-1] if len(p) > 5 else None}

    sig_index = {}
    for cid in list(spine.keys()):
        if cid.startswith(("UNIDENTIFIED::", "LAUNCHER::")):
            continue
        cp = _cid_parts(cid)
        if cp["symbol"] and cp["sleeve"] and cp["day"]:
            sig_index.setdefault((cp["symbol"], cp["sleeve"], cp["day"]), []).append(cid)

    for sk in (launcher_skips or []):
        bar = _bar_norm(sk.get("decision_bar_iso"))
        bar_day = bar[:10]
        key = (sk.get("symbol"), sk.get("sleeve"), bar_day)
        cids = sig_index.get(key) or []
        if len(cids) == 1:
            target = cids[0]
        elif cids:
            target = cids[0]           # same signal twice a day would land here; flag it
            slot(target).setdefault("skip_flags", set()).add(
                "launcher_skip_matched_ambiguous_candidates")
        elif sk.get("kind") in LAUNCHER_REFUSAL_KINDS:
            # Group by decision DAY, matching W7 candidate identity
            # (cluster::symbol::day::direction::sleeve): fx_jpy-style catch-up bars
            # are the same signal, so one row per (symbol, sleeve, day).
            target = "LAUNCHER::%s::%s::%s" % (sk.get("symbol"), sk.get("sleeve"), bar_day)
        else:
            continue                    # attach-only kind with no candidate: drop
        slot(target).setdefault("skips", []).append(sk)

    out = []
    for cid, src in spine.items():
        dec = src["dec"]
        refs_c = src["refs"]
        tickets = src["tickets"]
        skips = src.get("skips") or []
        flags = sorted(src.get("skip_flags") or [])
        if cid.startswith("UNIDENTIFIED::"):
            flags.append("candidate_id_null_on_refusal_rows")
        if cid.startswith("LAUNCHER::"):
            flags.append("synthetic_id_from_launcher_skip_only")

        # ---- identity ----------------------------------------------------
        first_dec = dec[0] if dec else None
        ident = dec_identity(first_dec) if first_dec else {}
        symbol = (ident.get("symbol")
                  or (refs_c[0].get("symbol") if refs_c else None)
                  or (fill_by_ticket.get(tickets[0], {}).get("symbol") if tickets else None)
                  or (skips[0].get("symbol") if skips else None))
        broker_symbol = ident.get("broker_symbol")
        sleeve = cluster = decision_bar = decision_day = None
        if tickets and tickets[0] in placed_by_ticket:
            p = placed_by_ticket[tickets[0]]
            sleeve, cluster = p.get("sleeve"), p.get("cluster")
            decision_bar, decision_day = p.get("decision_bar_iso"), p.get("decision_day")
        if sleeve is None and refs_c:
            sleeve = refs_c[0].get("sleeve")
        if sleeve is None and tickets and tickets[0] in fill_by_ticket:
            sleeve = fill_by_ticket[tickets[0]].get("sleeve")
        if sleeve is None and skips:
            sleeve = skips[0].get("sleeve")
        if sleeve is None and not cid.startswith(("UNIDENTIFIED::", "LAUNCHER::")):
            sleeve = cid.split("::")[-1]
        if decision_bar is None:
            if refs_c:
                decision_bar = refs_c[0].get("decision_bar_iso")
            elif tickets and tickets[0] in fill_by_ticket:
                decision_bar = fill_by_ticket[tickets[0]].get("decision_bar_iso")
            elif skips:
                decision_bar = skips[0].get("decision_bar_iso")
        if decision_day is None:
            if refs_c:
                decision_day = refs_c[0].get("decision_day")
            elif not cid.startswith(("UNIDENTIFIED::", "LAUNCHER::")):
                parts = cid.split("::")
                decision_day = parts[3] if len(parts) > 3 else None
            elif decision_bar:
                decision_day = _bar_norm(decision_bar)[:10]
        if cluster is None and not cid.startswith(("UNIDENTIFIED::", "LAUNCHER::")):
            cluster = cid.split("::")[1] if len(cid.split("::")) > 1 else None

        # ---- decision block (decision-time knowable) ----------------------
        exec_attempts = []
        spread_at_decision = None
        max_spread_r = None
        packet_hash = None
        final_action = None
        fatal = None
        for r in dec:
            cc = r.get("cost_context") or {}
            if spread_at_decision is None and is_num(cc.get("spread_r")):
                spread_at_decision = cc.get("spread_r")
            if max_spread_r is None and is_num(cc.get("max_spread_r")):
                max_spread_r = cc.get("max_spread_r")
            if packet_hash is None:
                packet_hash = (r.get("broker_order_lifecycle_capture_v4") or {}).get(
                    "packet_hash_sha256")
            final_action = r.get("action")
            if r.get("action") == "block":
                fatal = r.get("fatal_reasons") or []
            exec_attempts.append({
                "time_utc": r.get("generated_at_utc"),
                "action": r.get("action"),
                "spread_r": cc.get("spread_r"),
                "pretrade_cost_model_status": cc.get("pretrade_cost_model_status"),
                "fatal_reasons": r.get("fatal_reasons") or [],
            })
        decision_block = {
            "n_exec_rows": len(dec),
            "first_exec_time_utc": dec[0].get("generated_at_utc") if dec else None,
            "last_exec_time_utc": dec[-1].get("generated_at_utc") if dec else None,
            "final_action": final_action,
            "fatal_reasons_last_block": fatal,
            "spread_r_at_decision": spread_at_decision,
            "max_spread_r": max_spread_r,
            "packet_hash_sha256": packet_hash,
            "exec_attempts": exec_attempts,
        } if dec else None

        # ---- launcher pre-exec refusals / guard skips (decision-time facts) --
        pre_exec = None
        if skips:
            refusal_sk = [s for s in skips if s["kind"] in LAUNCHER_REFUSAL_KINDS]
            guard_sk = [s for s in skips if s["kind"] in LAUNCHER_ATTACH_ONLY_KINDS]
            bars_seen = []
            for s in skips:
                b = _bar_norm(s.get("decision_bar_iso"))
                if b and b not in bars_seen:
                    bars_seen.append(b)
            pre_exec = {
                "source": "ultimate_book_launcher.jsonl skipped[] (the only refusal "
                          "evidence before the 2026-08-17 frozen-intent deploy)",
                "n_refusal_skips": len(refusal_sk),
                "n_guard_skips": len(guard_sk),
                "first_ts_utc": skips[0]["ts"],
                "last_ts_utc": skips[-1]["ts"],
                "decision_bars": bars_seen,
                "refusals": [{"ts": s["ts"], "reason": s["reason"]} for s in refusal_sk],
                "guards": sorted({s["kind"] for s in guard_sk}),
            }

        # ---- frozen-intent episodes ---------------------------------------
        fi_block = None
        if refs_c:
            episodes = OrderedDict()
            for e in refs_c:
                episodes.setdefault(str(e.get("decision_bar_iso")), []).append(e)
            ep_rows = []
            for bar, rows in episodes.items():
                statuses = []
                for e in rows:
                    s = str(e.get("frozen_price_intent_status"))
                    if s not in statuses:
                        statuses.append(s)
                last = rows[-1]
                sprs = [e.get("spread_r") for e in rows if is_num(e.get("spread_r"))]
                lag = last.get("first_clear_lag_s")
                killed = [s for s in statuses if s.startswith("killed")]
                if killed:
                    terminal = killed[-1]
                elif isinstance(lag, str) and lag == "never":
                    terminal = "never_cleared"
                elif is_num(lag) and lag > 0:
                    terminal = "cleared_after_%ds" % int(lag)
                else:
                    terminal = statuses[-1] if statuses else None
                ep_rows.append({
                    "decision_bar_iso": bar,
                    "statuses": statuses,
                    "refusal_reasons": short_reasons(e.get("refusal_reasons") for e in rows),
                    "spread_r_min": min(sprs) if sprs else None,
                    "spread_r_max": max(sprs) if sprs else None,
                    "first_clear_lag_s": lag,
                    "chase_at_first_clear_r": last.get("chase_at_first_clear"),
                    "n_quote_rows": len(rows),
                    "terminal_status": terminal,
                })
            fi_block = {
                "n_quote_rows": len(refs_c),
                "n_episodes": len(ep_rows),
                "episodes": ep_rows,
                "terminal_status": ep_rows[-1]["terminal_status"] if ep_rows else None,
            }

        # ---- later-known: fill + lifecycle + trail + excursion -------------
        later = None
        if len(tickets) > 1:
            flags.append("multiple_tickets_for_candidate")
        if tickets:
            ticket = tickets[0]
            f_ev = fill_by_ticket.get(ticket)
            rec = trade_records.get(ticket)
            recx = (rec or {}).get("execution") or {}
            bd = (broker_deals or {}).get(ticket)
            placed = placed_by_ticket.get(ticket) or {}
            c_ev = close_by_ticket.get(ticket)
            slips = [s for s in slip_by_ticket.get(ticket, [])
                     if s.get("slippage_event_type") in (None, "entry")]
            slip = slips[0] if slips else None
            flags.extend(sorted(fill_dup_flags.get(ticket) or ()))
            if f_ev is None:
                flags.append("fill_event_missing_for_ticket")
            if rec is None:
                flags.append("trade_record_missing_for_ticket")
            if slip is None:
                flags.append("slippage_row_missing_for_ticket")
            if not dec:
                flags.append("no_exec_decision_row_for_filled_candidate")
            if rec and rec.get("candidate_id") and rec.get("candidate_id") != cid:
                flags.append("trade_record_candidate_id_mismatch")

            # entry/stop/time inputs: trade record first (engine truth), then
            # the broker deals dump (broker truth — exists even when the record
            # never reached this machine), then the event stream (detection
            # times; seconds-late, fine at M15 bar granularity).
            entry_price = recx.get("broker_entry_price")
            if not is_num(entry_price) and bd:
                entry_price = bd.get("entry_price")
                if is_num(entry_price):
                    flags.append("entry_price_from_broker_deals")
            planned_stop = recx.get("broker_position_planned_stop_loss")
            if not is_num(planned_stop) and bd and is_num(bd.get("sl")):
                planned_stop = bd.get("sl")
                flags.append("planned_stop_from_broker_deals")
            stop_dist = None
            if is_num(entry_price) and is_num(planned_stop):
                stop_dist = abs(entry_price - planned_stop)
            if stop_dist is None and bd and is_num(bd.get("stop_distance_price")):
                stop_dist = bd.get("stop_distance_price")
            direction = candidate_direction(cid)
            t_fill = parse_iso(recx.get("broker_fill_time_utc"))
            if t_fill is None and bd:
                t_fill = parse_iso(bd.get("entry_time_utc"))
            if t_fill is None and f_ev is not None:
                t_fill = parse_iso(f_ev.get("ts_utc"))
                if t_fill is not None:
                    flags.append("fill_time_from_event_stream")
            t_exit = parse_iso(recx.get("broker_exit_time_utc"))
            if t_exit is None and bd:
                t_exit = parse_iso(bd.get("exit_time_utc"))
            if t_exit is None and c_ev is not None:
                t_exit = parse_iso(c_ev.get("ts_utc"))
                if t_exit is not None:
                    flags.append("exit_time_from_event_stream")

            fill_block = {
                "ticket": ticket,
                "placed_at_utc": placed.get("ts") or recx.get("placed_at_utc"),
                "broker_fill_time_utc": recx.get("broker_fill_time_utc"),
                "broker_entry_price": entry_price,
                "requested_price": (slip or {}).get("requested_price"),
                "fill_price": (slip or {}).get("fill_price"),
                "slippage_price": (slip or {}).get("slippage_price"),
                "slippage_directional": (slip or {}).get("slippage_directional"),
                "slippage_r": (slip or {}).get("slippage_r"),
                "entry_commission_usd": recx.get("broker_entry_commission"),
                "planned_stop": planned_stop,
                "planned_take_profit": recx.get("broker_position_planned_take_profit"),
                "initial_stop_distance_price": stop_dist,
                "f5_intended_risk_usd": (f_ev or {}).get("f5_intended_risk_usd"),
                "f5_actual_risk_usd": (f_ev or {}).get("f5_actual_risk_usd"),
                "f5_nominal_risk_usd": (f_ev or {}).get("f5_nominal_risk_usd"),
                "dollar_basis": "ftmo_broker_usd_account",
            }

            lifecycle = None
            closed = ((rec or {}).get("trade_lifecycle_status") == "closed"
                      or c_ev is not None
                      or bool(bd and bd.get("n_exit_deals")))
            if closed:
                hold_s = None
                if t_fill and t_exit:
                    hold_s = int((t_exit - t_fill).total_seconds())
                net = recx.get("broker_realized_pnl")
                if net is None and c_ev:
                    net = c_ev.get("broker_net_pnl_usd")
                if net is None and bd:
                    net = bd.get("net_usd")
                    if is_num(net):
                        flags.append("net_usd_from_broker_deals")
                if (c_ev and is_num(net) and is_num(c_ev.get("broker_net_pnl_usd"))
                        and abs(net - c_ev["broker_net_pnl_usd"]) > 0.005):
                    flags.append("net_pnl_mismatch_record_vs_close_event")
                if (bd and is_num(net) and is_num(bd.get("net_usd"))
                        and abs(net - bd["net_usd"]) > 0.005):
                    flags.append("net_pnl_mismatch_ledger_vs_broker_deals")
                realised_r = (c_ev or {}).get("realised_r")
                if realised_r is None:
                    fc = recx.get("f5_close") or {}
                    realised_r = fc.get("realised_r")
                dollars = {
                    "basis": ("ftmo_broker_usd_account; position aggregate includes entry+exit "
                              "deal commissions, swap, fees; gross is price PnL only"),
                    "gross_profit_usd": recx.get("broker_position_aggregate_profit"),
                    "commission_usd": recx.get("broker_position_aggregate_commission"),
                    "swap_usd": recx.get("broker_position_aggregate_swap"),
                    "fee_usd": recx.get("broker_position_aggregate_fee"),
                    "net_usd": net,
                }
                if bd:
                    for src_k, dst_k in (("gross_profit_usd", "gross_profit_usd"),
                                         ("commission_usd", "commission_usd"),
                                         ("swap_usd", "swap_usd"),
                                         ("fee_usd", "fee_usd")):
                        if not is_num(dollars.get(dst_k)) and is_num(bd.get(src_k)):
                            dollars[dst_k] = bd.get(src_k)
                lifecycle = {
                    "status": "CLOSED",
                    "close_action": (rec or {}).get("close_action"),
                    "broker_exit_time_utc": (recx.get("broker_exit_time_utc")
                                             or (bd or {}).get("exit_time_utc")
                                             or iso(t_exit)),
                    "broker_exit_price": (recx.get("broker_exit_price")
                                          if is_num(recx.get("broker_exit_price"))
                                          else (bd or {}).get("exit_price")),
                    "hold_seconds_fill_to_exit": hold_s,
                    "dollars": dollars,
                    "realised_r": realised_r,
                    "r_denominator_note": R_DENOMINATOR_NOTE,
                    "notional_pnl_usd": (c_ev or {}).get("notional_pnl_usd"),
                    "notional_equity_after": (c_ev or {}).get("notional_equity_after"),
                    "real_pnl_usd_cumulative_after": (c_ev or {}).get("real_pnl_usd_cumulative"),
                }
                if c_ev is None:
                    flags.append("close_event_missing_for_closed_record")
            else:
                lifecycle = {"status": "OPEN_OR_UNKNOWN"}
                flags.append("position_not_confirmed_closed")

            trail = None
            mv = sorted(moves_by_ticket.get(ticket, []),
                        key=lambda e: str(e.get("ts_utc", "")))
            if mv:
                initial_sl = planned_stop
                if not is_num(initial_sl):
                    for e in mv:
                        if is_num(e.get("stop_now")):
                            initial_sl = e.get("stop_now")
                            break
                entry_for_lock = entry_price
                if not is_num(entry_for_lock):
                    for e in mv:
                        if is_num(e.get("entry_price")):
                            entry_for_lock = e.get("entry_price")
                            break
                locked = []
                for e in mv:
                    lr = locked_r_from_stop(
                        e.get("stop_now"), entry_for_lock, initial_sl, direction)
                    if lr is not None:
                        locked.append(lr)
                trail = {
                    "n_stop_moves": len(mv),
                    "first_move_utc": mv[0].get("ts_utc"),
                    "last_move_utc": mv[-1].get("ts_utc"),
                    "max_locked_r": max(locked) if locked else None,
                    "basis": ("stop-trail reconstruction: locked_r = dir_sign*"
                              "(stop_now-entry)/|entry-initial_sl|; dir_sign=+1 LONG "
                              "/ -1 SHORT; denom is the trade's own initial stop "
                              "distance (never the previous lock); untouched initial "
                              "stop = -1.0R; a LOWER BOUND on favourable excursion "
                              "in R of the initial stop; not quote data"),
                }

            exc = excursion(store, symbol, broker_symbol or recx.get("broker_symbol"),
                            direction, entry_price, stop_dist,
                            fill_block.get("f5_actual_risk_usd"), t_fill, t_exit) \
                if closed and is_num(entry_price) else {"status": "not_computed"}

            later = {"_note": LATER_KNOWN_NOTE, "fill": fill_block,
                     "lifecycle": lifecycle, "trail": trail, "excursion": exc,
                     "broker_truth": bd}
        else:
            # No ticket: attach any orphan order attempts (order_send with no fill --
            # slippage rows carry ticket 0 on IOC timeout/reject) by symbol + time window.
            attempts = []
            if dec:
                t_lo = parse_iso(dec[0].get("generated_at_utc"))
                t_hi = parse_iso(dec[-1].get("generated_at_utc"))
                if t_lo and t_hi:
                    t_lo -= timedelta(seconds=120)
                    t_hi += timedelta(seconds=900)
                    for s in slip_rows:
                        st = s.get("ticket") or s.get("order_ticket")
                        if st:
                            continue
                        if s.get("symbol") != symbol:
                            continue
                        t_send = parse_iso(s.get("order_send_time_utc") or s.get("ts"))
                        if t_send and t_lo <= t_send <= t_hi:
                            attempts.append({
                                "order_send_time_utc": s.get("order_send_time_utc"),
                                "requested_price": s.get("requested_price"),
                                "order_outcome_status": s.get("order_outcome_status"),
                                "notes": s.get("notes"),
                                "reject_or_fill_latency_ms": s.get("reject_or_fill_latency_ms"),
                                "spread_at_request": s.get("spread_at_request"),
                            })
            later = {"_note": LATER_KNOWN_NOTE, "fill": None,
                     "lifecycle": {"status": "NO_ORDER"},
                     "order_attempts_no_fill": attempts or None,
                     "trail": None,
                     "excursion": {"status": "not_applicable_no_fill"}}
            if attempts:
                later["lifecycle"] = {"status": "ORDER_SENT_NO_FILL"}

        # ---- outcome class: deepest funnel stage reached --------------------
        any_allow = any(r.get("action") == "allow" for r in dec)
        any_block = any(r.get("action") == "block" for r in dec)
        if tickets:
            outcome_class = "FILLED_CLOSED" if later["lifecycle"].get("status") == "CLOSED" \
                else "FILLED_OPEN"
        elif any_allow:
            outcome_class = "ALLOWED_NO_FILL"
        elif any_block:
            outcome_class = "BLOCKED_COST"
        elif refs_c or any(s["kind"] in LAUNCHER_REFUSAL_KINDS for s in skips):
            outcome_class = "REFUSED_PRE_EXEC"
        else:
            outcome_class = "UNKNOWN"

        key_times = [parse_iso(x) for x in (
            (dec[0].get("generated_at_utc") if dec else None),
            (refs_c[0].get("ts_utc") if refs_c else None),
            (skips[0]["ts"] if skips else None),
            (placed_by_ticket.get(tickets[0], {}).get("ts") if tickets else None))]
        key_times = [t for t in key_times if t]
        row_key = min(key_times) if key_times else None

        joined = bool(tickets) and not any(
            f in flags for f in ("fill_event_missing_for_ticket",
                                 "trade_record_missing_for_ticket",
                                 "no_exec_decision_row_for_filled_candidate",
                                 "trade_record_candidate_id_mismatch"))

        # era: the $10 vs $75 experiment epoch, from the fill event's own
        # f5_intended_risk_usd. None for never-filled rows.
        era_val = None
        if tickets:
            _fev = fill_by_ticket.get(tickets[0])
            if _fev is not None:
                era_val = _fev.get("f5_intended_risk_usd")

        out.append(OrderedDict([
            ("schema", SCHEMA),
            ("candidate_id", cid),
            ("row_key_time_utc", iso(row_key)),
            ("namespace", "operator"),
            ("symbol", symbol),
            ("broker_symbol", broker_symbol),
            ("sleeve", sleeve),
            ("cluster", cluster),
            ("direction", candidate_direction(cid)),
            ("decision_bar_iso", decision_bar),
            ("decision_day", decision_day),
            ("outcome_class", outcome_class),
            ("era", era_val),
            ("decision", decision_block),
            ("pre_exec_refusals", pre_exec),
            ("frozen_intent", fi_block),
            ("later_known", later),
            ("join_quality", {
                "flags": flags,
                "joined_end_to_end": joined,
                "sources_present": {
                    "exec_decision_rows": len(dec),
                    "refusal_quote_rows": len(refs_c),
                    "launcher_skip_rows": len(skips),
                    "placement_ledger": bool(tickets and tickets[0] in placed_by_ticket),
                    "fill_event": bool(tickets and tickets[0] in fill_by_ticket),
                    "trade_record": bool(tickets and tickets[0] in trade_records),
                    "close_event": bool(tickets and tickets[0] in close_by_ticket),
                    "broker_deals": bool(tickets and (broker_deals or {}).get(tickets[0])),
                    "slippage_rows": len(slip_by_ticket.get(tickets[0], [])) if tickets else 0,
                    "stop_move_rows": len(moves_by_ticket.get(tickets[0], [])) if tickets else 0,
                },
            }),
        ]))

    out.sort(key=lambda r: (r.get("row_key_time_utc") or "9999", r.get("candidate_id") or ""))
    return out


def row_active_on(row, day):
    """True if the row shows any decision/refusal/fill/close activity on UTC day."""
    cands = [row.get("row_key_time_utc"), row.get("decision_day")]
    d = row.get("decision") or {}
    cands += [d.get("first_exec_time_utc"), d.get("last_exec_time_utc")]
    lk = row.get("later_known") or {}
    f = lk.get("fill") or {}
    cands += [f.get("placed_at_utc"), f.get("broker_fill_time_utc")]
    lc = lk.get("lifecycle") or {}
    cands += [lc.get("broker_exit_time_utc")]
    fi = row.get("frozen_intent") or {}
    for ep in fi.get("episodes") or []:
        cands.append(ep.get("decision_bar_iso"))
    pe = row.get("pre_exec_refusals") or {}
    cands += [pe.get("first_ts_utc"), pe.get("last_ts_utc")]
    return any(str(c or "")[:10] == day for c in cands)


def script_repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", ".."))


def vps_live_layout(repo_root=None):
    """On-disk VPS locations. Used when dated Mac-harvest copies are absent."""
    root = repo_root or script_repo_root()
    book = os.path.join(root, "pipeline_state", "ultimate_book", "operator")
    shadow = os.path.join(root, "shadow_logs")
    grok_bars = os.path.join(r"C:\Users\trader\gtos\grok-jobs", "bars", "aug-extension", "M15")
    return {
        "repo_root": root,
        "book": book,
        "records_dir": os.path.join(book, "trade_records"),
        "placed": os.path.join(book, "placed_decisions.jsonl"),
        "events": os.path.join(shadow, "f5_minimal", "operator", "events.jsonl"),
        "slippage": os.path.join(shadow, "slippage_runtime.jsonl"),
        "decisions": os.path.join(shadow, "execution_manager_v4_decisions.jsonl"),
        "deals_dir": book,
        "bars_dirs": [os.path.join(book, "bars_f5"), grok_bars],
        "notional": os.path.join(book, "f5_notional_ledger.json"),
    }


def existing_files(paths):
    out, seen = [], set()
    for p in paths:
        if not p:
            continue
        ap = os.path.abspath(p)
        if ap in seen:
            continue
        seen.add(ap)
        if os.path.isfile(ap):
            out.append(ap)
    return out


def resolve_harvest_paths(dest=None, records_dir=None, events=None, placed=None,
                          slippage=None, decisions=None, deals_dirs=None,
                          vps_live=False, repo_root=None):
    """Resolve events / placed_decisions / deals from dated copies OR live VPS files.

    Live placement ledger is a *sibling* of trade_records/, not inside it. The
    inbox harvest join was stamping placement_ledger=false because it only
    looked at <records-dir>/placed_decisions.jsonl.
    """
    live = vps_live_layout(repo_root)
    if records_dir:
        records_dir = os.path.abspath(records_dir)
    elif vps_live or not dest:
        records_dir = live["records_dir"]
    else:
        records_dir = os.path.join(os.path.dirname(os.path.abspath(dest)), "trade_records")
    book_dir = os.path.dirname(records_dir)
    dated_dirs = []
    if dest and os.path.isdir(dest):
        root = os.path.dirname(os.path.abspath(dest))
        dated_dirs = sorted(
            d for d in glob.glob(os.path.join(root, "20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]"))
            if os.path.isdir(d))
        adest = os.path.abspath(dest)
        if adest not in dated_dirs:
            dated_dirs.append(adest)

    def dated(name):
        return [os.path.join(d, name) for d in dated_dirs]

    ev = list(events or []) + dated("events.jsonl")
    pl = list(placed or []) + [
        os.path.join(records_dir, "placed_decisions.jsonl"),
        os.path.join(book_dir, "placed_decisions.jsonl"),
    ]
    sl = list(slippage or []) + dated("slippage_runtime.jsonl")
    de = list(decisions or []) + dated("execution_manager_v4_decisions.jsonl")
    if vps_live or not existing_files(ev):
        ev.append(live["events"])
    if vps_live or not existing_files(pl):
        pl.append(live["placed"])
    if vps_live or not existing_files(sl):
        sl.append(live["slippage"])
    if vps_live or not existing_files(de):
        de.append(live["decisions"])

    deal_files = []
    for d in list(deals_dirs or []) + [records_dir, book_dir] + dated_dirs:
        deal_files += sorted(glob.glob(os.path.join(d, "deals_f5_*.json")))
    if vps_live or not existing_files(deal_files):
        deal_files += sorted(glob.glob(os.path.join(live["deals_dir"], "deals_f5_*.json")))
    return {
        "records_dir": records_dir,
        "book_dir": book_dir,
        "dated_dirs": dated_dirs,
        "events": existing_files(ev),
        "placed": existing_files(pl),
        "slippage": existing_files(sl),
        "decisions": existing_files(de),
        "deals": existing_files(deal_files),
        "live": live,
    }


def write_jsonl_rows(path, rows, compact=False):
    seps = (",", ":") if compact else (",", ": ")
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=False, separators=seps) + "\n")
    digest = sha256_file(path)
    with open(path + ".sha256", "w", encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (digest, os.path.basename(path)))
    return digest


def _record_fill_time(rec):
    recx = (rec or {}).get("execution") or {}
    return parse_iso(recx.get("broker_fill_time_utc") or (rec or {}).get("broker_fill_time_utc"))


def _record_has_entry(rec):
    if rec is None:
        return False
    if _record_fill_time(rec):
        return True
    recx = rec.get("execution") or {}
    n = recx.get("broker_position_entry_deal_count") or rec.get("broker_position_entry_deal_count")
    try:
        return int(n or 0) > 0
    except (TypeError, ValueError):
        return False


def _pick_num(*vals):
    for v in vals:
        if is_num(v):
            return v
    return None


def build_vps_ticket_rows(dec_rows, events, slip_rows, placed_rows, trade_records,
                          broker_deals=None, since=None):
    """One gtos.f5.outcome_ledger.vps_ticket.v1 row per filled position ticket.

    Joins placed_decisions.jsonl, f5_fill events, exec-manager rows, slippage,
    trade_records, and deals_f5 dumps. broker_truth.entry_time_utc is true UTC
    (NY+7 conversion); broker wall is stored separately as entry_time_broker_wall.
    """
    fills = [e for e in events if e.get("event") == "f5_fill"]
    closes = [e for e in events if e.get("event") == "f5_trade_closed"]
    placed_by_ticket = {}
    for p in placed_rows:
        if p.get("ticket") is None:
            continue
        placed_by_ticket[int(p["ticket"])] = p
    fill_by_ticket = {}
    fill_dup_flags = {}
    for e in sorted(fills, key=lambda x: str(x.get("ts_utc", ""))):
        if e.get("ticket") is None:
            continue
        t = int(e["ticket"])
        prev = fill_by_ticket.get(t)
        if prev is None:
            fill_by_ticket[t] = e
            continue
        flags_t = fill_dup_flags.setdefault(t, set())
        if str(e.get("ts_utc", ""))[:10] != str(prev.get("ts_utc", ""))[:10]:
            flags_t.add("fill_event_reemitted_on_later_day")
        else:
            flags_t.add("duplicate_fill_event_same_day")
        if e.get("sleeve") != prev.get("sleeve"):
            flags_t.add("duplicate_sleeve_attribution_fill_events")
    close_by_ticket = {}
    for e in sorted(closes, key=lambda x: str(x.get("ts_utc", ""))):
        if e.get("ticket") is not None:
            close_by_ticket.setdefault(int(e["ticket"]), e)
    slip_by_ticket = {}
    for s in slip_rows:
        t = s.get("ticket") or s.get("order_ticket")
        if t:
            slip_by_ticket.setdefault(int(t), []).append(s)
    dec_by_cid = {}
    for r in dec_rows:
        cid = dec_identity(r).get("candidate_id")
        if cid:
            dec_by_cid.setdefault(cid, []).append(r)

    tickets = set()
    tickets.update(placed_by_ticket)
    tickets.update(fill_by_ticket)
    for t, rec in (trade_records or {}).items():
        if _record_has_entry(rec):
            tickets.add(int(t))
    for t, bd in (broker_deals or {}).items():
        if bd.get("n_entry_deals"):
            tickets.add(int(t))

    out = []
    for ticket in tickets:
        placed = placed_by_ticket.get(ticket) or {}
        f_ev = fill_by_ticket.get(ticket)
        rec = (trade_records or {}).get(ticket)
        recx = (rec or {}).get("execution") or {}
        bd = (broker_deals or {}).get(ticket)
        c_ev = close_by_ticket.get(ticket)
        if not (f_ev or _record_has_entry(rec) or (bd and bd.get("n_entry_deals"))):
            continue
        cid = (placed.get("candidate_id")
               or (f_ev or {}).get("candidate_id")
               or (rec or {}).get("candidate_id"))
        t_fill = _record_fill_time(rec)
        if t_fill is None and bd:
            t_fill = parse_iso(bd.get("entry_time_utc"))
        if t_fill is None and f_ev is not None:
            t_fill = parse_iso(f_ev.get("ts_utc"))
        if since and t_fill and str(iso_offset(t_fill) or "")[:10] < since:
            continue
        if since and t_fill is None:
            continue
        t_exit = parse_iso(recx.get("broker_exit_time_utc") or (rec or {}).get("broker_exit_time_utc"))
        if t_exit is None and bd:
            t_exit = parse_iso(bd.get("exit_time_utc"))
        if t_exit is None and c_ev is not None:
            t_exit = parse_iso(c_ev.get("ts_utc"))

        sleeve = (placed.get("sleeve") or (f_ev or {}).get("sleeve")
                  or (rec or {}).get("sleeve")
                  or (str(cid).split("::")[-1] if cid else None))
        cluster = (placed.get("cluster") or (rec or {}).get("cluster")
                   or (str(cid).split("::")[1] if cid and len(str(cid).split("::")) > 1 else None))
        symbol = (placed.get("symbol") or (f_ev or {}).get("symbol")
                  or (rec or {}).get("symbol") or (bd or {}).get("symbol"))
        broker_symbol = (recx.get("broker_symbol") or (rec or {}).get("broker_symbol")
                         or dec_identity((dec_by_cid.get(cid) or [{}])[0]).get("broker_symbol"))
        decision_bar = (placed.get("decision_bar_iso") or (f_ev or {}).get("decision_bar_iso")
                        or (rec or {}).get("decision_bar_iso"))
        decision_day = (placed.get("decision_day") or (f_ev or {}).get("decision_day")
                        or (rec or {}).get("decision_day")
                        or (str(cid).split("::")[3] if cid and len(str(cid).split("::")) > 3 else None))
        direction = candidate_direction(cid)

        flags = sorted(fill_dup_flags.get(ticket) or ())
        if f_ev is None:
            flags.append("fill_event_missing_for_ticket")
        if rec is None:
            flags.append("trade_record_missing_for_ticket")
        if ticket not in placed_by_ticket:
            flags.append("placement_ledger_missing_for_ticket")
        dec = dec_by_cid.get(cid) or []
        if cid and not dec:
            flags.append("no_exec_decision_row_for_filled_candidate")

        all_slips = slip_by_ticket.get(ticket, [])
        entry_slips = [s for s in all_slips
                       if s.get("slippage_event_type") in (None, "entry")]
        slip = entry_slips[0] if entry_slips else None
        if slip is None:
            flags.append("slippage_row_missing_for_ticket")
            slip_block = {
                "status": "missing_calc",
                "requested_price": "missing_calc",
                "fill_price": "missing_calc",
                "slippage_price": "missing_calc",
                "slippage_directional": "missing_calc",
                "slippage_r": "missing_calc",
                "note": "no entry slippage_runtime row for this position ticket; not invented",
            }
        else:
            slip_block = {
                "status": "joined",
                "requested_price": slip.get("requested_price"),
                "fill_price": slip.get("fill_price"),
                "slippage_price": slip.get("slippage_price"),
                "slippage_directional": slip.get("slippage_directional"),
                "slippage_r": slip.get("slippage_r"),
                "spread_at_request": slip.get("spread_at_request"),
                "order_send_time_utc": slip.get("order_send_time_utc"),
                "slippage_event_type": slip.get("slippage_event_type") or "entry",
            }

        entry_price = _pick_num(recx.get("broker_entry_price"),
                                (rec or {}).get("broker_entry_price"),
                                (bd or {}).get("entry_price"))
        planned_stop = _pick_num(recx.get("broker_position_planned_stop_loss"),
                                 (rec or {}).get("broker_position_planned_stop_loss"),
                                 (bd or {}).get("sl"))
        stop_dist = None
        if is_num(entry_price) and is_num(planned_stop):
            stop_dist = abs(entry_price - planned_stop)
        if stop_dist is None and bd and is_num(bd.get("stop_distance_price")):
            stop_dist = bd.get("stop_distance_price")
        intended = (f_ev or {}).get("f5_intended_risk_usd")
        if intended is None:
            intended = "missing_calc"
        fill_block = {
            "ticket": ticket,
            "placed_at_utc": placed.get("ts") or recx.get("placed_at_utc"),
            "broker_fill_time_utc": (recx.get("broker_fill_time_utc")
                                     or iso_offset(t_fill)),
            "broker_entry_price": entry_price,
            "requested_price": slip.get("requested_price") if slip else "missing_calc",
            "fill_price": slip.get("fill_price") if slip else "missing_calc",
            "slippage_price": slip.get("slippage_price") if slip else "missing_calc",
            "slippage_directional": slip.get("slippage_directional") if slip else "missing_calc",
            "slippage_r": slip.get("slippage_r") if slip else "missing_calc",
            "entry_commission_usd": recx.get("broker_entry_commission"),
            "planned_stop": planned_stop,
            "planned_take_profit": recx.get("broker_position_planned_take_profit"),
            "initial_stop_distance_price": stop_dist,
            "f5_intended_risk_usd": intended,
            "f5_actual_risk_usd": (f_ev or {}).get("f5_actual_risk_usd"),
            "dollar_basis": "ftmo_broker_usd_account",
        }

        closed = (
            (rec or {}).get("trade_lifecycle_status") == "closed"
            or c_ev is not None
            or bool(bd and bd.get("n_exit_deals"))
        )
        if closed:
            hold_s = None
            if t_fill and t_exit:
                hold_s = int((t_exit - t_fill).total_seconds())
            net = _pick_num((rec or {}).get("broker_realized_pnl"),
                            recx.get("broker_realized_pnl"),
                            (rec or {}).get("broker_position_realized_pnl"),
                            (c_ev or {}).get("broker_net_pnl_usd"),
                            (bd or {}).get("net_usd"))
            dollars = {
                "basis": "ftmo_broker_usd_account; trade_record first, deals fallback",
                "gross_profit_usd": _pick_num(
                    (rec or {}).get("broker_position_aggregate_profit"),
                    recx.get("broker_position_aggregate_profit"),
                    (bd or {}).get("gross_profit_usd")),
                "commission_usd": _pick_num(
                    (rec or {}).get("broker_position_aggregate_commission"),
                    recx.get("broker_position_aggregate_commission"),
                    (bd or {}).get("commission_usd")),
                "swap_usd": _pick_num(
                    (rec or {}).get("broker_position_aggregate_swap"),
                    recx.get("broker_position_aggregate_swap"),
                    (bd or {}).get("swap_usd")),
                "fee_usd": _pick_num(
                    (rec or {}).get("broker_position_aggregate_fee"),
                    recx.get("broker_position_aggregate_fee"),
                    (bd or {}).get("fee_usd")),
                "net_usd": net,
            }
            lifecycle = {
                "status": "CLOSED",
                "close_action": (rec or {}).get("close_action"),
                "broker_exit_time_utc": (recx.get("broker_exit_time_utc")
                                         or (rec or {}).get("broker_exit_time_utc")
                                         or iso_offset(t_exit)),
                "broker_exit_price": _pick_num(
                    recx.get("broker_exit_price"),
                    (rec or {}).get("broker_exit_price"),
                    (bd or {}).get("exit_price")),
                "hold_seconds_fill_to_exit": hold_s,
                "dollars": dollars,
            }
            outcome_class = "FILLED_CLOSED"
        else:
            lifecycle = {"status": "OPEN_OR_UNKNOWN"}
            flags.append("position_not_confirmed_closed")
            outcome_class = "FILLED_OPEN"

        bt = None
        if bd:
            bt = {
                "basis": "deals_f5 dump, magic 0, position_id = ticket",
                "time_column_basis": "true_utc",
                "broker_clock_rule": "new_york_plus_7",
                "entry_time_utc": iso_offset(parse_iso(bd.get("entry_time_utc"))),
                "exit_time_utc": iso_offset(parse_iso(bd.get("exit_time_utc"))),
                "entry_time_broker_wall": bd.get("entry_time_broker_wall"),
                "exit_time_broker_wall": bd.get("exit_time_broker_wall"),
                "entry_price": bd.get("entry_price"),
                "exit_price": bd.get("exit_price"),
                "net_usd": bd.get("net_usd"),
                "n_entry_deals": bd.get("n_entry_deals"),
                "n_exit_deals": bd.get("n_exit_deals"),
            }

        src_fill = ticket in fill_by_ticket
        src_placed = ticket in placed_by_ticket
        joined_end = bool(rec) and src_fill and src_placed
        later = {
            "_note": TICKET_LATER_NOTE,
            "fill": fill_block,
            "lifecycle": lifecycle,
            "slippage": slip_block,
            "broker_truth": bt,
        }
        out.append(OrderedDict([
            ("schema", TICKET_SCHEMA),
            ("ticket", ticket),
            ("join_key", TICKET_JOIN_KEY),
            ("row_key_time_utc", recx.get("broker_fill_time_utc") or iso_offset(t_fill)),
            ("namespace", "operator"),
            ("symbol", symbol),
            ("broker_symbol", broker_symbol),
            ("sleeve", sleeve),
            ("cluster", cluster),
            ("direction", direction),
            ("candidate_id", cid),
            ("decision_bar_iso", decision_bar),
            ("decision_day", decision_day),
            ("entry_day_utc", (iso_offset(t_fill) or "")[:10] or None),
            ("outcome_class", outcome_class),
            ("later_known", later),
            ("join_quality", {
                "flags": flags,
                "joined_trade_record": rec is not None,
                "joined_slippage": slip is not None,
                "joined_end_to_end": joined_end,
                "sources_present": {
                    "trade_record": rec is not None,
                    "broker_deals": bd is not None,
                    "slippage_rows": len(entry_slips),
                    "slippage_rows_any": len(all_slips),
                    "exec_decision_rows": len(dec),
                    "placement_ledger": src_placed,
                    "fill_event": src_fill,
                },
            }),
        ]))
    out.sort(key=lambda r: (r.get("row_key_time_utc") or "9999", r.get("ticket") or 0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dest", nargs="?", default=None, help="dated harvest directory")
    ap.add_argument("--date", default=None, help="UTC day YYYY-MM-DD (default: dir name)")
    ap.add_argument("--records-dir", default=None,
                    help="trade-records dir (default: <root>/trade_records or VPS live)")
    ap.add_argument("--bars-dir", action="append", default=None,
                    help="M15 OHLC dir for MFE/MAE; repeatable — bars merge per "
                         "symbol across dirs (missing => rows flagged, never "
                         "fatal). Default: <root>/bars-aug-extension/M15 + "
                         "<root>/bars_f5 + every <dated>/bars_f5")
    ap.add_argument("--out-cumulative", default=None,
                    help="cumulative ledger path (default: <root>/f5_outcome_ledger_cumulative.jsonl)")
    ap.add_argument("--vps-live", action="store_true",
                    help="Read live VPS placed_decisions.jsonl + events.jsonl "
                         "from pipeline_state/shadow_logs")
    ap.add_argument("--out-ticket-ledger", default=None,
                    help="Write gtos.f5.outcome_ledger.vps_ticket.v1 JSONL")
    ap.add_argument("--ticket-since", default=None,
                    help="UTC day YYYY-MM-DD inclusive lower bound on ticket fill time")
    ap.add_argument("--events", action="append", default=None)
    ap.add_argument("--placed", action="append", default=None)
    ap.add_argument("--slippage", action="append", default=None)
    ap.add_argument("--decisions", action="append", default=None)
    ap.add_argument("--deals-dir", action="append", default=None)
    args = ap.parse_args(argv)
    if not args.dest and not args.vps_live:
        ap.error("dest is required unless --vps-live")

    dest = os.path.abspath(args.dest) if args.dest else None
    root = os.path.dirname(dest) if dest else None
    day = args.date or (os.path.basename(dest) if dest else None)
    paths = resolve_harvest_paths(
        dest=dest,
        records_dir=args.records_dir,
        events=args.events,
        placed=args.placed,
        slippage=args.slippage,
        decisions=args.decisions,
        deals_dirs=args.deals_dir,
        vps_live=args.vps_live,
    )
    records_dir = paths["records_dir"]
    dated_dirs = paths["dated_dirs"]

    dec_rows, dec_bad, dec_files = read_jsonl_multi(paths["decisions"])
    events, ev_bad, ev_files = read_jsonl_multi(paths["events"])
    slip_rows, slip_bad, _ = read_jsonl_multi(paths["slippage"])
    placed_rows, placed_bad, placed_files = read_jsonl_multi(paths["placed"])
    trade_records = load_trade_records(records_dir)
    bars_dirs = list(args.bars_dir or [])
    if not bars_dirs:
        live_bars = paths["live"]["bars_dirs"]
        bars_dirs = live_bars[:] if args.vps_live else []
        if root:
            bars_dirs += [os.path.join(root, "bars-aug-extension", "M15"),
                          os.path.join(root, "bars_f5"),
                          os.path.join(records_dir, "bars_f5")]
        bars_dirs += [os.path.join(d, "bars_f5") for d in dated_dirs]
        if args.vps_live:
            bars_dirs += live_bars
    store = BarStore([d for d in bars_dirs if os.path.isdir(d)] or None)

    broker_deals, deals_meta = load_broker_deals(paths["deals"])

    launcher_files = sorted(glob.glob(os.path.join(records_dir, "ultimate_book_launcher.full.*.jsonl")))
    for d in dated_dirs:
        launcher_files.append(os.path.join(d, "ultimate_book_launcher.tailday.jsonl"))
        launcher_files.append(os.path.join(d, "ultimate_book_launcher.tail256k.jsonl"))
    launcher_skips, n_noise, n_bare = load_launcher_skips(launcher_files)

    rows = []
    if dest or args.out_cumulative:
        rows = build_rows(dec_rows, events, slip_rows, placed_rows, trade_records, store,
                          launcher_skips=launcher_skips, broker_deals=broker_deals)

    since = args.ticket_since
    if since is None and args.vps_live:
        since = "2026-08-21"
    ticket_rows = []
    if args.out_ticket_ledger:
        ticket_rows = build_vps_ticket_rows(
            dec_rows, events, slip_rows, placed_rows, trade_records,
            broker_deals=broker_deals, since=since)

    checks = {}
    ledger_path = os.path.join(records_dir, "f5_notional_ledger.json")
    if rows and os.path.isfile(ledger_path):
        try:
            led = json.load(open(ledger_path, encoding="utf-8"))
            closed = [r for r in rows if r["outcome_class"] == "FILLED_CLOSED"]
            net = sum((r["later_known"]["lifecycle"]["dollars"]["net_usd"] or 0.0)
                      for r in closed
                      if r["later_known"]["lifecycle"].get("dollars"))
            checks = {
                "ledger_trades_recorded": led.get("trades_recorded"),
                "ledger_real_pnl_usd_cumulative": led.get("real_pnl_usd_cumulative"),
                "rows_filled_closed": len(closed),
                "rows_net_usd_sum": round(net, 2),
                "reconciles": (led.get("trades_recorded") == len(closed)
                               and abs((led.get("real_pnl_usd_cumulative") or 0.0) - net) < 0.01),
            }
        except Exception as exc:
            checks = {"error": repr(exc)}

    outputs = {}
    day_rows = []
    if dest:
        outbox = os.path.join(dest, "outbox")
        os.makedirs(outbox, exist_ok=True)
        day_path = os.path.join(outbox, "f5_outcome_ledger_%s.jsonl" % (day or "live"))
        day_rows = [r for r in rows if row_active_on(r, day)] if day else list(rows)
        outputs[os.path.basename(day_path)] = write_jsonl_rows(day_path, day_rows)
        out_cum = args.out_cumulative or os.path.join(root, "f5_outcome_ledger_cumulative.jsonl")
        outputs[os.path.basename(out_cum)] = write_jsonl_rows(out_cum, rows)
    elif args.out_cumulative and rows:
        outputs[os.path.basename(args.out_cumulative)] = write_jsonl_rows(
            args.out_cumulative, rows)

    if args.out_ticket_ledger:
        outputs[os.path.basename(args.out_ticket_ledger)] = write_jsonl_rows(
            args.out_ticket_ledger, ticket_rows, compact=True)

    recon = OrderedDict()
    recon_doc = {"n_failed": 0}
    live_book = os.path.abspath(paths["live"]["book"])
    write_recon = (
        broker_deals and dest and rows and not args.vps_live
        and os.path.abspath(root) != live_book
    )
    if rows and broker_deals:
        recon = broker_reconciliation(broker_deals, rows,
                                      window_utc=deals_meta.get("window_utc"))
        recon_doc = {
            "schema": "gtos.f5.broker_reconciliation.v1",
            "generated_for_day": day,
            "deals_meta": deals_meta,
            "days": recon,
            "n_failed": sum(1 for v in recon.values() if v["status"] == "FAILED"),
        }
        if write_recon:
            recon_path = os.path.join(root, "f5_broker_reconciliation.json")
            with open(recon_path, "w", encoding="utf-8") as fh:
                json.dump(recon_doc, fh, indent=1)

    def _src_count(key, pred):
        n = 0
        for r in ticket_rows:
            sp = ((r.get("join_quality") or {}).get("sources_present") or {})
            if pred(sp.get(key)):
                n += 1
        return n

    summary = {
        "day": day,
        "vps_live": bool(args.vps_live),
        "rows_total": len(rows),
        "rows_today": len(day_rows),
        "ticket_rows": len(ticket_rows),
        "ticket_since": since,
        "ticket_fill_event_true": _src_count("fill_event", lambda v: v is True),
        "ticket_placement_ledger_true": _src_count("placement_ledger", lambda v: v is True),
        "ticket_exec_decision_rows_gt0": _src_count("exec_decision_rows", lambda v: (v or 0) > 0),
        "by_outcome_class": {},
        "joined_end_to_end": sum(1 for r in rows if r["join_quality"]["joined_end_to_end"]),
        "notional_ledger_check": checks,
        "broker_deals": {"positions": len(broker_deals),
                         "files": deals_meta.get("files"),
                         "reconciliation_days": len(recon),
                         "reconciliation_failed_days": recon_doc["n_failed"]},
        "inputs": {"decision_files": len(dec_files), "event_files": len(ev_files),
                   "placed_files": placed_files,
                   "decision_rows": len(dec_rows), "event_rows": len(events),
                   "placed_rows": len(placed_rows),
                   "parse_errors": dec_bad + ev_bad + slip_bad + placed_bad,
                   "trade_records": len(trade_records),
                   "launcher_skips_used": len(launcher_skips),
                   "launcher_skips_noise_dropped": n_noise,
                   "launcher_bare_string_skips": n_bare},
        "outputs": outputs,
    }
    for r in (ticket_rows or rows):
        summary["by_outcome_class"][r["outcome_class"]] = \
            summary["by_outcome_class"].get(r["outcome_class"], 0) + 1
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

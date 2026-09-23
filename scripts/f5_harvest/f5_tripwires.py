#!/usr/bin/env python3
"""F5 tripwires — pages the desk when the $75 experiment book crosses a line.

Runs on BOTH hosts, every 10 minutes:
  VPS (prod venv, MetaTrader5 present):
      python scripts\\f5_harvest\\f5_tripwires.py --repo-root C:\\Users\\Administrator\\redacted_host\\repo
  Mac (harvest, no MT5):
      python3 scripts/f5_harvest/f5_tripwires.py --harvest-root /Users/borr/GTOSActive/f5-harvest

Five wires (each fires at most one page per day per condition — the alert_id is
deterministic and the notification queue dedupes):

  (a) day_net      F5 day net (magic 0) < −$1,000. Source order: live
                   MT5 deals > deals_f5_*.json dump > f5_trade_closed events >
                   outcome ledger. Dollars are broker USD.
  (b) dd_distance  remaining distance to the SHARED FTMO daily-loss limit
                   < $2,000. Firm rule (reused from
                   src/components/ultimate_book/governor_state.py, B56):
                   limit = 5% of the INITIAL balance; the window resets at
                   00:00 CE(S)T (Europe/Prague — NOT server midnight; FTMO's
                   MT5 server runs the US DST calendar); day baseline =
                   max(day-start balance, day-start equity), day-start balance
                   reconstructed as balance_now − Σ trade-deal cash delta since
                   the boundary (profit+commission+swap+fee of BUY/SELL deals,
                   mirroring src/utils/broker_accounting.trade_deal_cash_delta).
                   Needs MT5 — without it the wire reports
                   account_data_unavailable and never fires.
  (c) judgment_dark  candidates flowed in the launcher stream (cycle rows with
                   n_intents > 0) for 2+ cycles with no judge_<day>.jsonl
                   append since. Tolerates the judge files not existing yet.
  (d) hold_breach  a fill happened while an in-TTL HOLD (judge row verdict
                   veto/hold, or judgment/flow_<day>.json sidecar entry) stood
                   for that candidate. TTL default 600 s
                   (judgment_layer.DEFAULT_TTL_S).
  (e) adapter_breach  the breach counter grew since the last run: count of
                   f5_fill_deviation_breach events plus any *adapter_breach*
                   counter file. State in --state.

DELIVERY (reused, never rebuilt): alerts are ENQUEUED to the persistent
Telegram notification queue (src/utils/notification_queue.py enqueue-row
schema). Producers only append; the authorized long-lived worker
(`python -m src.utils.notification_queue --worker`, watchdog.ps1) delivers.
Delivery is process-authorized by design (src/safety/notification_authorization
.py) — this script never needs credentials and never prints them. If the repo
module imports, it is used (dedup + daemon fallback); otherwise the enqueue row
is appended directly to the queue JSONL, which the worker drains identically.

Pure stdlib; MetaTrader5 import guarded; repo imports guarded. Exit code 0
always when the wires evaluated (fired or not); 1 only on an internal error.
"""
import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

F5_MAGIC = 0
F5_NAMESPACE = "operator"
DAY_NET_LIMIT_USD = -1000.0
DD_DISTANCE_LIMIT_USD = 2000.0
FTMO_DAILY_LOSS_PCT = 5.0          # % of INITIAL balance (profile: maximum_daily_loss_pct)
DEFAULT_INITIAL_BALANCE = 100000.0
HOLD_TTL_S = 600.0                 # judgment_layer.DEFAULT_TTL_S
_TRADE_DEAL_TYPES = (0, 1)         # broker_accounting.TRADE_DEAL_TYPES (BUY/SELL)


# ------------------------------------------------------------------ utilities
def utcnow():
    return datetime.now(timezone.utc)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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


def read_jsonl(path, max_bytes=None):
    rows = []
    if not path or not os.path.isfile(path):
        return rows
    try:
        with open(path, "rb") as fh:
            if max_bytes is not None:
                size = os.fstat(fh.fileno()).st_size
                if size > max_bytes:
                    fh.seek(size - max_bytes)
                    fh.readline()          # drop the partial first line
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rows.append(json.loads(raw.decode("utf-8", "replace")))
                except Exception:
                    continue
    except OSError:
        pass
    return rows


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def fmt_money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "?"
    return ("-$%.2f" % abs(v)) if v < 0 else ("$%.2f" % v)


# ------------------------------------------------- broker wall clock -> UTC
# FTMO-Server3 wall clock == America/New_York + 7 h (measured;
# src/utils/broker_clock.py NEW_YORK_PLUS_7). Deal epochs are broker-basis.
try:
    from zoneinfo import ZoneInfo
    _NY = ZoneInfo("America/New_York")
    _PRAGUE = ZoneInfo("Europe/Prague")
except Exception:                                   # pragma: no cover
    _NY = _PRAGUE = None


def broker_epoch_to_utc(epoch):
    if not is_num(epoch) or epoch <= 0:
        return None
    naive = datetime.fromtimestamp(float(epoch), tz=timezone.utc).replace(tzinfo=None)
    for cand_hours in (3, 2):
        utc = (naive - timedelta(hours=cand_hours)).replace(tzinfo=timezone.utc)
        if _NY is None:
            return utc
        ny = utc.astimezone(_NY)
        if (ny.replace(tzinfo=None) + timedelta(hours=7)) == naive:
            return utc
    return (naive - timedelta(hours=3)).replace(tzinfo=timezone.utc)


def ftmo_daily_reset_boundary_utc(now_utc):
    """UTC instant when FTMO's daily-loss window began: 00:00 Europe/Prague.

    The firm rule (governor_state.py B56; broker_clock europe_prague): FTMO
    resets at CE(S)T midnight, NOT its MT5 server midnight. Reuses the repo's
    broker_clock when importable; else zoneinfo Europe/Prague; else a fixed
    UTC+2 (declared degraded — off by 1 h in EU summer).
    """
    try:
        from src.utils.broker_clock import daily_reset_offset_hours
        off = daily_reset_offset_hours(now_utc, "europe_prague")
        if off is not None:
            local = now_utc + timedelta(hours=float(off))
            local_mid = local.replace(hour=0, minute=0, second=0, microsecond=0)
            start = local_mid - timedelta(hours=float(off))
            off2 = daily_reset_offset_hours(start, "europe_prague")
            if off2 is not None and off2 != off:
                start = local_mid - timedelta(hours=float(off2))
            return start, "src.utils.broker_clock:europe_prague"
    except Exception:
        pass
    if _PRAGUE is not None:
        local = now_utc.astimezone(_PRAGUE)
        local_mid = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return local_mid.astimezone(timezone.utc), "zoneinfo:Europe/Prague"
    fixed = now_utc + timedelta(hours=2)
    mid = fixed.replace(hour=0, minute=0, second=0, microsecond=0)
    return mid - timedelta(hours=2), "degraded_fixed_utc_plus_2"


def profile_daily_loss_params(repo_root):
    """(initial_balance, daily_loss_pct) from the live FTMO profile YAML.

    Naive line parse (stdlib-only; PyYAML may be absent on the Mac cron).
    Falls back to the firm constants recorded in
    src/components/ultimate_book/execution_packets.py (FTMO_DAILY_LOSS_PCT=5.0)
    and the $100k account.
    """
    bal, pct = DEFAULT_INITIAL_BALANCE, FTMO_DAILY_LOSS_PCT
    path = os.path.join(repo_root or "", "config", "profiles",
                        "operator_profile.yaml")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if s.startswith("prop_safe_selector_initial_balance:"):
                    try:
                        bal = float(s.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif s.startswith("maximum_daily_loss_pct:"):
                    try:
                        pct = float(s.split(":", 1)[1].strip())
                    except ValueError:
                        pass
    except OSError:
        pass
    return bal, pct


# ------------------------------------------------------------------- inputs
def newest(paths):
    best = None
    for p in paths:
        if os.path.isfile(p):
            if best is None or os.path.getmtime(p) > os.path.getmtime(best):
                best = p
    return best


def locate_inputs(args, day):
    """Resolve every input path for whichever host we are on."""
    repo = args.repo_root
    hr = args.harvest_root
    dated = os.path.join(hr, day) if hr else None
    ns_state = os.path.join(repo, "pipeline_state", "ultimate_book",
                            F5_NAMESPACE) if repo else None
    events = newest([p for p in [
        os.path.join(repo, "shadow_logs", "f5_minimal", F5_NAMESPACE,
                     "events.jsonl") if repo else None,
        os.path.join(dated, "events.jsonl") if dated else None,
    ] if p])
    launcher = newest([p for p in [
        os.path.join(repo, "shadow_logs", "ultimate_book_launcher.jsonl")
        if repo else None,
        os.path.join(dated, "ultimate_book_launcher.tailday.jsonl") if dated else None,
        os.path.join(dated, "ultimate_book_launcher.tail256k.jsonl") if dated else None,
    ] if p])
    deal_globs = []
    for base in (ns_state, os.path.join(hr, "trade_records") if hr else None,
                 dated, hr):
        if base:
            deal_globs += sorted(glob.glob(os.path.join(base, "deals_f5_*.json")))
    judge_files = []
    for base in ([os.path.join(repo, "judgment")] if repo else []) + \
                ([os.path.join(dated, "judgment"), dated] if dated else []):
        if base:
            judge_files.append(os.path.join(base, "judge_%s.jsonl" % day))
    sidecars = []
    for base in ([os.path.join(repo, "judgment")] if repo else []) + \
                ([os.path.join(dated, "judgment")] if dated else []):
        if base:
            sidecars.append(os.path.join(base, "flow_%s.json" % day))
            sidecars.append(os.path.join(base, "consume_%s.json" % day))
    breach_counter_files = []
    for base in (ns_state, dated):
        if base:
            breach_counter_files += sorted(
                glob.glob(os.path.join(base, "*adapter_breach*.json")))
    ledger = newest([p for p in [
        os.path.join(hr, "f5_outcome_ledger_cumulative.jsonl") if hr else None,
    ] if p])
    return {"events": events, "launcher": launcher, "deal_dumps": deal_globs,
            "judge_files": judge_files, "sidecars": sidecars,
            "breach_counter_files": breach_counter_files, "ledger": ledger}


def mt5_connect(terminal_path):
    """Guarded MetaTrader5 import + initialize. Returns module or None."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None
    try:
        if mt5.initialize(path=terminal_path, portable=True) or mt5.initialize():
            return mt5
    except Exception:
        pass
    return None


# ------------------------------------------------------------------ wires
def wire_day_net(day, inputs, mt5, limit_usd):
    """(a) F5 day net by magic; source order MT5 > dump > events > ledger."""
    source = None
    net = None
    n = 0
    if mt5 is not None:
        try:
            now = utcnow()
            deals = mt5.history_deals_get(now - timedelta(days=3),
                                          now + timedelta(days=1))
            if deals is not None:
                net = 0.0
                for d in deals:
                    if getattr(d, "magic", None) != F5_MAGIC:
                        continue
                    if int(getattr(d, "type", -1)) not in _TRADE_DEAL_TYPES:
                        continue
                    t = broker_epoch_to_utc(getattr(d, "time", None))
                    if t is None or t.strftime("%Y-%m-%d") != day:
                        continue
                    net += (float(getattr(d, "profit", 0) or 0)
                            + float(getattr(d, "commission", 0) or 0)
                            + float(getattr(d, "swap", 0) or 0)
                            + float(getattr(d, "fee", 0) or 0))
                    n += 1
                source = "mt5_live_deals"
        except Exception:
            net = None
    if net is None and inputs["deal_dumps"]:
        doc = read_json(inputs["deal_dumps"][-1])
        if doc:
            net = 0.0
            for d in doc.get("deals") or []:
                if d.get("magic") != F5_MAGIC or d.get("type") not in _TRADE_DEAL_TYPES:
                    continue
                t = broker_epoch_to_utc(d.get("time"))
                if t is None or t.strftime("%Y-%m-%d") != day:
                    continue
                net += sum(float(d.get(k) or 0)
                           for k in ("profit", "commission", "swap", "fee"))
                n += 1
            source = "deals_dump:%s" % os.path.basename(inputs["deal_dumps"][-1])
    if net is None and inputs["events"]:
        rows = read_jsonl(inputs["events"])
        closes = [r for r in rows if r.get("event") == "f5_trade_closed"
                  and str(r.get("ts_utc", ""))[:10] == day]
        if closes:
            net = sum(float(r.get("broker_net_pnl_usd") or 0) for r in closes)
            n = len(closes)
            source = "f5_trade_closed_events"
    if net is None and inputs["ledger"]:
        rows = read_jsonl(inputs["ledger"])
        net = 0.0
        for r in rows:
            if r.get("outcome_class") != "FILLED_CLOSED":
                continue
            lc = ((r.get("later_known") or {}).get("lifecycle") or {})
            if str(lc.get("broker_exit_time_utc") or "")[:10] != day:
                continue
            v = (lc.get("dollars") or {}).get("net_usd")
            if is_num(v):
                net += v
                n += 1
        source = "outcome_ledger"
    if net is None:
        return {"wire": "day_net", "status": "no_data", "fired": False}
    fired = net < limit_usd
    return {"wire": "day_net", "status": "ok", "fired": fired,
            "day_net_usd": round(net, 2), "n_deals_or_trades": n,
            "limit_usd": limit_usd, "source": source,
            "message": ("F5 TRIPWIRE day_net: %s on %s (< %s), source %s"
                        % (fmt_money(net), day, fmt_money(limit_usd), source))}


def wire_dd_distance(inputs, mt5, repo_root, limit_usd, state, now_utc=None):
    """(b) remaining distance to the shared FTMO daily-loss wall.

    ``now_utc`` is injectable for tests; production passes nothing."""
    if mt5 is None:
        return {"wire": "dd_distance", "status": "account_data_unavailable",
                "fired": False,
                "note": ("needs MetaTrader5 (whole-account equity+deals); the "
                         "F5 ledger alone cannot see production's share of the "
                         "shared daily budget")}
    try:
        acct = mt5.account_info()
        if acct is None:
            return {"wire": "dd_distance", "status": "no_account_info", "fired": False}
        balance = float(acct.balance)
        equity = float(acct.equity)
        now = now_utc or utcnow()
        boundary, boundary_src = ftmo_daily_reset_boundary_utc(now)
        deals = mt5.history_deals_get(boundary - timedelta(hours=1),
                                      now + timedelta(hours=1))
        if deals is None:
            return {"wire": "dd_distance", "status": "no_deal_history", "fired": False}
        realized = 0.0
        for d in deals:
            if int(getattr(d, "type", -1)) not in _TRADE_DEAL_TYPES:
                continue      # balance ops are not trading cash delta
            t = broker_epoch_to_utc(getattr(d, "time", None))
            if t is None or t < boundary:
                continue
            realized += (float(getattr(d, "profit", 0) or 0)
                         + float(getattr(d, "commission", 0) or 0)
                         + float(getattr(d, "swap", 0) or 0)
                         + float(getattr(d, "fee", 0) or 0))
        day_start_balance = balance - realized
        # anchor persistence mirrors governor_state._balance_anchor:
        # max(day_start_balance, day-start equity); never trust a stale-LOW
        # stored anchor (higher reference = stricter measure = SAFE).
        anchor_date = (boundary.strftime("%Y-%m-%d"))
        st = state.setdefault("dd_anchor", {})
        if st.get("date") == anchor_date:
            baseline = max(float(st.get("baseline") or 0.0), day_start_balance)
        else:
            baseline = max(day_start_balance, equity)
        state["dd_anchor"] = {"date": anchor_date, "baseline": baseline}
        init_bal, pct = profile_daily_loss_params(repo_root)
        limit = init_bal * pct / 100.0
        loss_today = max(0.0, baseline - equity)
        remaining = limit - loss_today
        fired = remaining < limit_usd
        return {"wire": "dd_distance", "status": "ok", "fired": fired,
                "daily_limit_usd": round(limit, 2),
                "loss_today_usd": round(loss_today, 2),
                "remaining_usd": round(remaining, 2),
                "baseline_usd": round(baseline, 2),
                "equity_usd": round(equity, 2),
                "boundary_utc": boundary.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "boundary_source": boundary_src,
                "message": ("F5 TRIPWIRE dd_distance: %s left of the shared FTMO "
                            "daily-loss limit %s (loss so far %s; threshold %s)"
                            % (fmt_money(remaining), fmt_money(limit),
                               fmt_money(loss_today), fmt_money(limit_usd)))}
    except Exception as exc:
        return {"wire": "dd_distance", "status": "error:%r" % exc, "fired": False}


def wire_judgment_dark(day, inputs):
    """(c) candidates flowed 2+ cycles with no judge_<day>.jsonl append."""
    if not inputs["launcher"]:
        return {"wire": "judgment_dark", "status": "no_launcher_stream", "fired": False}
    rows = read_jsonl(inputs["launcher"], max_bytes=4 * 1024 * 1024)
    cand_cycles = []
    for r in rows:
        if str(r.get("ts", ""))[:10] != day:
            continue
        if r.get("action") == "cycle":
            try:
                if int(r.get("n_intents") or 0) > 0:
                    cand_cycles.append(str(r.get("ts")))
            except (TypeError, ValueError):
                continue
    judge_path = None
    judge_rows = []
    for p in inputs["judge_files"]:
        if os.path.isfile(p):
            judge_path = p
            judge_rows = read_jsonl(p)
            break
    last_judge_ts = None
    for r in judge_rows:
        ts = parse_iso(r.get("written_at_utc") or r.get("ts") or r.get("ts_utc"))
        if ts and (last_judge_ts is None or ts > last_judge_ts):
            last_judge_ts = ts
    dark_cycles = []
    for ts in cand_cycles:
        t = parse_iso(ts)
        if t is None:
            continue
        if last_judge_ts is None or t > last_judge_ts:
            dark_cycles.append(ts)
    fired = len(dark_cycles) >= 2
    return {"wire": "judgment_dark", "status": "ok", "fired": fired,
            "candidate_cycles_today": len(cand_cycles),
            "cycles_since_last_judge_row": len(dark_cycles),
            "judge_file": judge_path,
            "last_judge_row_utc": (last_judge_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
                                   if last_judge_ts else None),
            "message": ("F5 TRIPWIRE judgment_dark: %d candidate cycle(s) with no "
                        "judge_%s.jsonl append (judge file: %s)"
                        % (len(dark_cycles), day, judge_path or "absent"))}


def _hold_entries(day, inputs):
    """Collect HOLD verdicts with (candidate, written_at, ttl_s)."""
    holds = []
    for p in inputs["sidecars"]:
        doc = read_json(p)
        if not isinstance(doc, dict):
            continue
        for cid, entry in doc.items():
            if not isinstance(entry, dict):
                continue
            action = str(entry.get("action") or "").upper()
            verdict = str(entry.get("verdict") or "").lower()
            if action == "HOLD" or verdict in ("veto", "hold"):
                holds.append({
                    "candidate_id": cid,
                    "written_at": parse_iso(entry.get("written_at_utc") or entry.get("ts")),
                    "ttl_s": float(entry.get("ttl_s") or HOLD_TTL_S),
                    "source": os.path.basename(p)})
    for p in inputs["judge_files"]:
        for r in read_jsonl(p):
            verdict = str(r.get("verdict") or "").lower()
            if verdict not in ("veto", "hold"):
                continue
            cid = str(r.get("join_key") or r.get("candidate_id") or "")
            if not cid:
                continue
            holds.append({
                "candidate_id": cid,
                "written_at": parse_iso(r.get("written_at_utc") or r.get("ts")),
                "ttl_s": float(r.get("ttl_s") or HOLD_TTL_S),
                "source": os.path.basename(p)})
    return holds


def wire_hold_breach(day, inputs):
    """(d) a fill despite an in-TTL HOLD for that candidate."""
    holds = _hold_entries(day, inputs)
    if not holds:
        return {"wire": "hold_breach", "status": "no_holds_on_record", "fired": False}
    fills = []
    for r in read_jsonl(inputs["events"]):
        if r.get("event") != "f5_fill" or str(r.get("ts_utc", ""))[:10] != day:
            continue
        fills.append(r)
    breaches = []
    for f in fills:
        cid = str(f.get("candidate_id") or "")
        t_fill = parse_iso(f.get("ts_utc"))
        if not cid or t_fill is None:
            continue
        for h in holds:
            if h["candidate_id"] != cid or h["written_at"] is None:
                continue
            if h["written_at"] <= t_fill <= h["written_at"] + timedelta(seconds=h["ttl_s"]):
                breaches.append({"ticket": f.get("ticket"), "candidate_id": cid,
                                 "fill_utc": f.get("ts_utc"),
                                 "hold_written_utc": h["written_at"].strftime(
                                     "%Y-%m-%dT%H:%M:%SZ"),
                                 "hold_source": h["source"]})
    fired = bool(breaches)
    return {"wire": "hold_breach", "status": "ok", "fired": fired,
            "n_holds": len(holds), "breaches": breaches,
            "message": ("F5 TRIPWIRE hold_breach: %d fill(s) despite an in-TTL "
                        "HOLD: %s" % (len(breaches),
                                      "; ".join("ticket %s (%s)"
                                                % (b["ticket"], b["candidate_id"])
                                                for b in breaches)))}


def wire_adapter_breach(day, inputs, state):
    """(e) the deviation/adapter breach counter grew since the last run."""
    count = 0
    sources = []
    ev_rows = read_jsonl(inputs["events"])
    n_ev = sum(1 for r in ev_rows if r.get("event") == "f5_fill_deviation_breach")
    if n_ev:
        sources.append("f5_fill_deviation_breach_events:%d" % n_ev)
    count += n_ev
    for p in inputs["breach_counter_files"]:
        doc = read_json(p)
        v = None
        if isinstance(doc, dict):
            for k in ("count", "breaches", "n_breaches", "total"):
                if is_num(doc.get(k)):
                    v = int(doc[k])
                    break
        elif is_num(doc):
            v = int(doc)
        if v is not None:
            count += v
            sources.append("%s:%d" % (os.path.basename(p), v))
    last = state.get("adapter_breach_count")
    state["adapter_breach_count"] = count
    grew = is_num(last) and count > last
    first_nonzero = last is None and count > 0
    fired = bool(grew or first_nonzero)
    return {"wire": "adapter_breach", "status": "ok", "fired": fired,
            "count": count, "previous": last, "sources": sources,
            "message": ("F5 TRIPWIRE adapter_breach: counter %s -> %d (%s)"
                        % (last, count, ", ".join(sources) or "no sources"))}


# ---------------------------------------------------------------- delivery
def deliver(alerts, queue_path, repo_root, dry_run):
    """Enqueue pages on the persistent notification queue (reuse, no rebuild).

    Path 1: import src.utils.notification_queue and call send() — dedup +
    in-process fallback drain for long-lived callers. Path 2 (import fails —
    e.g. Mac cron without the repo venv): append the enqueue row directly to
    the queue JSONL; the authorized worker drains it identically. Path 3: no
    queue path resolvable — print to stderr, exit nonzero handled by caller.
    """
    results = []
    for a in alerts:
        msg = a["message"]
        # one page per (wire, UTC day): deterministic id, queue dedupes.
        aid = hashlib.sha256(("f5_tripwire|%s|%s" % (
            a["wire"], utcnow().strftime("%Y-%m-%d"))).encode()).hexdigest()
        if dry_run:
            results.append({"wire": a["wire"], "delivery": "dry_run", "alert_id": aid})
            continue
        delivered = False
        if repo_root:
            try:
                sys.path.insert(0, repo_root)
                from src.utils.notification_queue import send, Level
                send(msg, level=Level.CRITICAL, alert_id=aid)
                delivered = True
                results.append({"wire": a["wire"], "delivery": "notification_queue.send",
                                "alert_id": aid})
            except Exception:
                pass
        if not delivered and queue_path:
            try:
                os.makedirs(os.path.dirname(queue_path) or ".", exist_ok=True)
                row = {"alert_id": aid,
                       "ts_utc": utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "level": "CRITICAL", "message": msg,
                       "retry_count": 0, "last_attempt_utc": None}
                with open(queue_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
                delivered = True
                results.append({"wire": a["wire"], "delivery": "queue_row_append",
                                "alert_id": aid, "queue": queue_path})
            except OSError as exc:
                results.append({"wire": a["wire"],
                                "delivery": "FAILED:%r" % exc, "alert_id": aid})
        if not delivered and not any(r.get("alert_id") == aid and
                                     "FAILED" in str(r.get("delivery"))
                                     for r in results):
            print("UNDELIVERED PAGE: %s" % msg, file=sys.stderr)
            results.append({"wire": a["wire"], "delivery": "stderr_only",
                            "alert_id": aid})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="F5 tripwires (see module docstring)")
    ap.add_argument("--repo-root", default=None,
                    help="repo root (VPS: the live tree; enables shadow_logs/"
                         "pipeline_state/judgment inputs + queue import)")
    ap.add_argument("--harvest-root", default=None,
                    help="Mac harvest root (/Users/borr/GTOSActive/f5-harvest)")
    ap.add_argument("--day", default=None, help="UTC day (default today)")
    ap.add_argument("--state", default=None,
                    help="state JSON for growth wires (default: "
                         "<repo pipeline_state|harvest root>/f5_tripwire_state.json)")
    ap.add_argument("--queue", default=None,
                    help="notification queue JSONL (default: "
                         "$GTOS_NOTIFICATION_QUEUE_PATH, else "
                         "<repo>/pipeline_state/notification_queue.jsonl)")
    ap.add_argument("--terminal", default=r"C:\MT5\FTMO\terminal64.exe",
                    help="MT5 terminal path (VPS)")
    ap.add_argument("--day-net-limit", type=float, default=DAY_NET_LIMIT_USD)
    ap.add_argument("--dd-distance-limit", type=float, default=DD_DISTANCE_LIMIT_USD)
    ap.add_argument("--no-mt5", action="store_true",
                    help="never import MetaTrader5 (tests / Mac)")
    ap.add_argument("--dry-run", action="store_true",
                    help="compute + print; enqueue nothing")
    args = ap.parse_args(argv)

    if not args.repo_root and not args.harvest_root:
        # sensible defaults per host
        if os.name == "nt":
            args.repo_root = r"host-local\redacted_host\repo"
        else:
            args.harvest_root = "/Users/borr/GTOSActive/f5-harvest"
    day = args.day or utcnow().strftime("%Y-%m-%d")
    inputs = locate_inputs(args, day)

    state_path = args.state or os.path.join(
        (os.path.join(args.repo_root, "pipeline_state") if args.repo_root
         else args.harvest_root or "."), "f5_tripwire_state.json")
    state = read_json(state_path) or {}

    mt5 = None if args.no_mt5 else mt5_connect(args.terminal)
    try:
        wires = [
            wire_day_net(day, inputs, mt5, args.day_net_limit),
            wire_dd_distance(inputs, mt5, args.repo_root,
                             args.dd_distance_limit, state),
            wire_judgment_dark(day, inputs),
            wire_hold_breach(day, inputs),
            wire_adapter_breach(day, inputs, state),
        ]
    finally:
        if mt5 is not None:
            try:
                mt5.shutdown()
            except Exception:
                pass

    try:
        tmp = state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, state_path)
    except OSError as exc:
        print("WARN state not persisted: %r" % exc, file=sys.stderr)

    fired = [w for w in wires if w.get("fired")]
    queue_path = args.queue or os.environ.get("GTOS_NOTIFICATION_QUEUE_PATH") or (
        os.path.join(args.repo_root, "pipeline_state", "notification_queue.jsonl")
        if args.repo_root else None)
    delivery = deliver(fired, queue_path, args.repo_root, args.dry_run)

    print(json.dumps({"day": day, "fired": [w["wire"] for w in fired],
                      "wires": wires, "delivery": delivery,
                      "state_path": state_path}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

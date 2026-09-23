"""Live monitoring for BOTH account books (FTMO primary + redacted_account follower).

One-shot snapshot (default) or a continuous daemon (--loop SECONDS) that watches both accounts and
sends a Telegram alert the moment anything crosses a risk threshold (approaching the -3% soft stop /
-5% daily / max-DD floor, gross-risk cap, or a book process going down) — plus a periodic heartbeat.
Read-only (each account queried in its own short-lived MT5 session). NO orders, NO modify.

    python .tools/monitor_books.py                 # one snapshot
    python .tools/monitor_books.py --loop 300       # daemon: sweep + alert every 5 min
"""
import re
import sys
import time
import json
import os
import datetime as dt
# load Telegram creds (TELEGRAM_BOT_TOKEN/CHAT_ID) from .env BEFORE importing the notifier, else alerts
# are silently dropped (the book processes do this via run_book.py; the daemon must too).
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)
except Exception:
    pass
import MetaTrader5 as mt5

ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", 531325516, "operator_profile"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", 0, "redacted_account_live_bee34003"),
]
DAILY_SOFT, DAILY_HARD, MAXDD, INIT_BAL = 0.03, 0.05, 0.10, 100000.0
GROSS_CAP = 0.04
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
    resolve_rule,
)

# Struck 2026-07-29 (B56 carry): `SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)`.
# It was wrong in two independent ways, and both of them move the daily-loss alert in the
# SAME dangerous direction -- the monitor believes the day has reset while the firm is
# still counting.
#
#  1. The label was wrong and the number is dated. Both servers are MEASURED to run the
#     **US** DST calendar (America/New_York + 7 h; 81 weekly session boundaries per broker),
#     not EET/EEST. They drop to +2 on **2026-11-01** while a hardcoded 3 would not, so from
#     that date the window would open a further hour early, every night, silently.
#  2. The server clock is not FTMO's reset rule at all. FTMO resets at 00:00 CE(S)T
#     (config/profiles/operator_profile.yaml:104); redacted_account resets at 00:00 server
#     time. Server midnight is therefore 1 h before FTMO's real reset normally, and 2 h
#     before it for the ~4 weeks a year the US and EU calendars disagree.
#
# The window is now computed as an INSTANT rather than a date, because the two rules do not
# share a calendar and comparing a CE(S)T date against a broker-wall date would be a type
# error wearing a fix. Deal times are raw broker epochs, so they are converted with the
# server rule before the comparison -- never by decoding them as UTC.
DAILY_RESET_RULE_BY_LABEL = {
    "FTMO": "Europe/Prague",   # 00:00 CE(S)T, academy.ftmo.com/lesson/maximum-daily-loss/
    "redacted_account": None,        # 00:00 server time, help.redacted_account.com/en/articles/8394309
}
MT5_SERVER_BY_LABEL = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}


def server_offset_hours(label, now_utc):
    """The MT5 server's own offset from UTC, measured, DST-correct."""
    return offset_seconds_at_utc(now_utc, resolve_rule(MT5_SERVER_BY_LABEL[label])) / 3600.0


def daily_reset_window_start_utc(label, now_utc):
    """UTC instant at which THIS FIRM'S current daily-loss window began.

    Raises rather than guessing: an unregistered label or server comes out of ``broker_clock``
    as ``UnknownBrokerClockError``. A wrong window is invisible until it costs an account, and a
    guessed one is exactly the defect this replaces.

    Be clear about what that costs, because an earlier draft of this docstring claimed
    containment that does not exist: ``snap`` has no ``except`` and its caller does not wrap it,
    so a raise here kills the monitor loop. The supervisor restarts it within ~30 s, so the blast
    radius is a crash loop rather than silent wrong alerting -- the right direction, but it is a
    crash, not a graceful degradation. Both server strings and both rules resolve today.
    """
    hours = daily_reset_offset_hours(now_utc, DAILY_RESET_RULE_BY_LABEL[label])
    if hours is None:
        hours = server_offset_hours(label, now_utc)
    local_now = now_utc + dt.timedelta(hours=hours)
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight - dt.timedelta(hours=hours)
MONITOR_HEARTBEAT_PATH = os.path.join(REPO_ROOT, "pipeline_state", "monitor_books", "heartbeat.json")


def write_monitor_heartbeat(status, **extra):
    """Machine-readable monitor daemon liveness for the supervisor."""
    try:
        os.makedirs(os.path.dirname(MONITOR_HEARTBEAT_PATH), exist_ok=True)
        rec = {
            "schema": "gtos.monitor_books.heartbeat.v1",
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "pid": os.getpid(),
            "status": status,
            **extra,
        }
        tmp = f"{MONITOR_HEARTBEAT_PATH}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(rec, handle, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, MONITOR_HEARTBEAT_PATH)
    except Exception:
        pass


def snap(label, path, login):
    """Return a metrics dict for one account (and print a human line). {} on failure."""
    if not mt5.initialize(path=path, portable=True):
        print(f"[{label}] CONNECT FAIL {mt5.last_error()}"); return {}
    try:
        info = mt5.account_info()
        if not info:
            return {}
        eq, bal = float(info.equity), float(info.balance)
        floating = eq - bal
        now = dt.datetime.now(dt.timezone.utc)
        window_start = daily_reset_window_start_utc(label, now)
        srv_rule = resolve_rule(MT5_SERVER_BY_LABEL[label])
        # 30 h back, not 24. The window itself is always < 24 h old (max measured 23.50 h), but
        # history_deals_get's bounds are interpreted as BROKER wall clock, so passing UTC shifts
        # the requested range by the server offset (~3 h). 24 h of window plus a 3 h shift does
        # not fit in a 24 h request. The filter below is exact, so over-fetching costs nothing
        # and under-fetching would silently drop realized loss out of the daily-limit alert.
        deals = mt5.history_deals_get(now - dt.timedelta(hours=30), now + dt.timedelta(hours=13)) or []
        realized_today = sum(float(d.profit) + float(getattr(d, "swap", 0)) + float(getattr(d, "commission", 0))
                             for d in deals if getattr(d, "entry", 0) == 1
                             and broker_epoch_to_utc(d.time, srv_rule) >= window_start)
        day_eq_start = bal - realized_today
        daily_pl_pct = (eq - day_eq_start) / day_eq_start if day_eq_start else 0.0
        maxdd_floor = INIT_BAL * (1 - MAXDD)
        pos = mt5.positions_get() or []
        # gross open risk (distance entry->SL in account currency) as % of equity
        gross = 0.0
        for p in pos:
            if p.sl and p.price_open:
                si = mt5.symbol_info(p.symbol)
                vpp = (si.trade_tick_value / si.trade_tick_size) if (si and si.trade_tick_size) else 0
                gross += p.volume * abs(p.price_open - p.sl) * vpp
        gross_pct = gross / eq if eq else 0.0
        # accrued overnight SWAP on the still-OPEN positions (invisible until rollover; the multi-day
        # index shorts accrue financing each 21:00-UTC server rollover). p.profit excludes swap.
        accrued_swap = sum(float(getattr(p, "swap", 0) or 0) for p in pos)
        m = dict(label=label, eq=eq, bal=bal, floating=floating, realized=realized_today,
                 daily_pl_pct=daily_pl_pct, daily_pl_usd=eq - day_eq_start,
                 dd_headroom=eq - maxdd_floor, gross_pct=gross_pct,
                 n_pos=len(pos), pos=pos, accrued_swap=accrued_swap)
        swap_str = f" | swap ${accrued_swap:+,.1f}" if pos else ""
        print(f"[{label}] eq ${eq:,.0f} | daily {daily_pl_pct*100:+.2f}% | realized today ${realized_today:+,.0f} "
              f"| floating ${floating:+,.0f} | gross {gross_pct*100:.2f}% | DD headroom ${m['dd_headroom']:+,.0f}"
              f"{swap_str} | {len(pos)} pos")
        for p in pos:
            sw = float(getattr(p, "swap", 0) or 0)
            print(f"     {p.symbol:11s} {'S' if p.type==1 else 'L'} {p.volume} ${p.profit:+,.0f} "
                  f"swap ${sw:+,.1f} {p.comment}")
        return m
    finally:
        mt5.shutdown()


def live_namespaces():
    """Set of namespaces with a running run_book.py process (best-effort, Windows). None if unknown."""
    import subprocess
    try:
        out = subprocess.run(["powershell", "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -like '*run_book.py*' } | ForEach-Object "
            "{ if ($_.CommandLine -match '--namespace (\\S+)') { $matches[1] } }"],
            capture_output=True, text=True, timeout=20).stdout
        return set(out.split())
    except Exception:
        return None


def book_down(live=None):
    """Namespaces with NO running run_book.py process."""
    if live is None:
        live = live_namespaces()
    if live is None:
        return []
    return [ns for (_l, _p, _lg, ns) in ACCOUNTS if ns not in live]


def _pid_alive(pid):
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        return True   # cannot check -> assume alive (never SUPPRESS a real hang)


def _another_monitor_running():
    """PID of another monitor_books.py --loop process (excluding self), else None — single-instance guard
    so two daemons don't both alert (duplicate Telegram spam, divergent dedup state)."""
    try:
        import psutil
        me = psutil.Process()
        my_pid = me.pid
        # The venv `Scripts\python.exe` is a thin LAUNCHER that re-execs the real interpreter as a CHILD,
        # so the daemon runs as a shim->child pair that SHARE our `monitor_books.py --loop` command line
        # (same create_time). Without excluding our own launcher-parent and children, the child's guard
        # sees its own shim-parent as a "senior" monitor and instantly defers to it -> the child exits ->
        # the shim exits -> NO monitor survives (a self-defeating single-instance check). Exclude our own
        # process lineage so only a GENUINELY separate daemon counts as a rival.
        my_ppid = me.ppid()
        # TOTAL-ORDER identity key = (start_time, pid). Strictly less => the OTHER is senior and we yield.
        # Using a tuple (not start_time alone) breaks an exact create_time tie deterministically by PID, so
        # two monitors started within the same clock tick still resolve to exactly one survivor (a bare
        # `<` on start_time alone would let BOTH survive on a tie -> the double-monitor bug we're fixing).
        my_key = (me.create_time(), my_pid)
        for p in psutil.process_iter(["pid", "name", "ppid", "create_time", "cmdline"]):
            pid = p.info["pid"]
            if pid == my_pid:
                continue
            if pid == my_ppid or p.info.get("ppid") == my_pid:
                continue   # our own venv-launcher shim parent / spawned child — same lineage, not a rival
            # only a real PYTHON monitor process — NOT a powershell/shell that merely mentions the script
            # + --loop in its command line (that false-match would make the daemon exit on startup).
            if "python" not in (p.info.get("name") or "").lower():
                continue
            cl = " ".join(p.info.get("cmdline") or [])
            if "monitor_books.py" in cl and "--loop" in cl:
                # Yield ONLY to a SENIOR (lower (start_time, pid)) monitor. Otherwise two near-simultaneous
                # starts would each detect the other and BOTH exit (a mutual-exclusion race that leaves NO
                # monitor). The junior defers; the senior survives.
                other_key = (p.info.get("create_time") or 0.0, pid)
                if other_key < my_key:
                    return pid
    except Exception:
        return None
    return None


def book_hung(live=None, max_age_s=240):
    """Namespaces whose run_book.py PID is ALIVE but whose heartbeat.json is stale (the worker is blocked
    inside a broker call -> not ticking -> not placing or managing exits, yet the PID still exists so
    BOOK DOWN never fires). Returns [(namespace, age_seconds), ...]. The book writes the heartbeat at the
    top of every ~60s tick, so a >4-min-old heartbeat = several missed ticks = hung."""
    import json
    if live is None:
        live = live_namespaces()
    if live is None:
        return []
    hung = []
    now = dt.datetime.now(dt.timezone.utc)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for (_l, _p, _lg, ns) in ACCOUNTS:
        if ns not in live:
            continue   # DOWN (handled by book_down), not HUNG
        hb = os.path.join(repo, "pipeline_state", "ultimate_book", ns, "heartbeat.json")
        try:
            with open(hb, encoding="utf-8") as f:
                rec = json.load(f)
            ts = dt.datetime.fromisoformat(rec["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            age = (now - ts).total_seconds()
            if age > max_age_s:
                # Only HUNG if the heartbeat's OWN pid is still alive. A stale heartbeat left by a
                # just-killed worker (a restart in progress: the supervisor's new worker hasn't written
                # its first heartbeat yet) is NOT a hang — don't false-alarm during the restart window.
                hb_pid = rec.get("pid")
                if hb_pid and not _pid_alive(hb_pid):
                    continue
                hung.append((ns, age))
        except FileNotFoundError:
            pass   # process may be mid-startup before its first heartbeat; don't false-alarm
        except Exception:
            pass
    return hung


def book_broker_blind(live=None, max_age_s=240):
    """Namespaces whose worker is ALIVE + ticking (FRESH heartbeat) but reports healthy=False — terminal up
    yet the broker/trade-server link is down, so orders + fresh data are impossible (COMP-4). The worker
    self-alerts too, but this INDEPENDENT monitor flag catches a broker-blind worker even if the worker's
    own alert path is down. A stale heartbeat is handled by book_hung, not here."""
    import json
    if live is None:
        live = live_namespaces()
    if live is None:
        return []
    blind = []
    now = dt.datetime.now(dt.timezone.utc)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for (_l, _p, _lg, ns) in ACCOUNTS:
        if ns not in live:
            continue
        hb = os.path.join(repo, "pipeline_state", "ultimate_book", ns, "heartbeat.json")
        try:
            with open(hb, encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("healthy") is not False:
                continue                      # healthy (or an older heartbeat with no health field)
            ts = dt.datetime.fromisoformat(rec["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            if (now - ts).total_seconds() <= max_age_s:   # only a FRESH unhealthy heartbeat = live + blind
                blind.append(ns)
        except Exception:
            pass
    return blind


def alerts(metrics, down, hung=None):
    out = []
    for m in metrics:
        if not m:
            continue
        L = m["label"]
        if m["daily_pl_pct"] <= -0.045:
            out.append(f"🚨 {L}: daily P&L {m['daily_pl_pct']*100:.2f}% — NEAR -5% HARD LIMIT")
        elif m["daily_pl_pct"] <= -0.025:
            out.append(f"⚠️ {L}: daily P&L {m['daily_pl_pct']*100:.2f}% — approaching -3% soft stop")
        if m["gross_pct"] >= 0.035:
            out.append(f"⚠️ {L}: gross open risk {m['gross_pct']*100:.2f}% — near 4% cap")
        if m["dd_headroom"] <= 0.01 * INIT_BAL:
            out.append(f"🚨 {L}: only ${m['dd_headroom']:,.0f} above the max-DD floor")
    for ns in down:
        out.append(f"🚨 BOOK DOWN: {ns} has no running process (supervisor should restart it)")
    for ns, age in (hung or []):
        out.append(f"🚨 BOOK HUNG: {ns} PID alive but no tick for {age/60:.1f} min "
                   f"(blocked — not placing/managing; investigate or restart)")
    return out


def send(msg):
    try:
        from src.utils.notification_queue import Level, send as _q
        _q(msg, level=Level.HIGH)
    except Exception:
        try:
            from src.notifications import _send_async; _send_async(msg)
        except Exception:
            pass


def disk_space_alert(min_free_mb=500):
    """Alert on low free disk (MACRO-RES-07): a full/failing disk silently degrades the EXACT mechanisms
    that protect against double-placement (PlacementLedger), correct exit policy after restart (trade
    records), and operator awareness (alert queue) — all at once, with no other symptom. Best-effort."""
    try:
        import shutil
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        free_mb = shutil.disk_usage(repo).free / (1024.0 * 1024.0)
        if free_mb < min_free_mb:
            return [f"🚨 LOW DISK: {free_mb:.0f} MB free on the book drive — the placement ledger, trade "
                    f"records, and alert queue can fail SILENTLY (double-place / lost-exit-policy / "
                    f"missed-alert risk). Free space now."]
    except Exception:
        pass
    return []


def firm_and_foreign_alerts(metrics):
    """Two firm-level awareness signals the per-account view misses:
      (1) FOREIGN/UNMANAGED legs — any open position NOT tagged W7:* (a legacy/manual trade the book
          neither manages nor counts in its gross cap; e.g. the GoldAgent_OBRete GER40 orphan). Deduped.
      (2) CROSS-ACCOUNT directional concentration — the same (symbol, direction) open on BOTH accounts =
          one correlated firm-level bet (P(both pass) rests on a correlation premise nothing else surfaces).
    Returns alert strings (the caller dedups via `fired`)."""
    out = []
    ms = [m for m in metrics if m]
    for m in ms:
        for p in (m.get("pos") or []):
            cmt = (getattr(p, "comment", "") or "")
            if not cmt.startswith("W7:"):
                out.append(f"⚠️ FOREIGN POSITION [{m['label']}]: {p.symbol} "
                           f"{'SELL' if p.type == 1 else 'BUY'} {p.volume} '{cmt}' — not a W7 book trade "
                           f"(unmanaged by the book, outside its gross-risk cap)")
    if len(ms) >= 2:
        from collections import defaultdict
        legs = defaultdict(set)
        for m in ms:
            for p in (m.get("pos") or []):
                if (getattr(p, "comment", "") or "").startswith("W7:"):
                    legs[(p.symbol, p.type)].add(m["label"])
        conc = [f"{s} {'S' if d == 1 else 'L'}" for (s, d), accts in legs.items() if len(accts) >= 2]
        if conc:
            out.append(f"⚠️ FIRM CONCENTRATION: same directional leg on BOTH accounts — {', '.join(conc)} "
                       f"(one correlated firm-level bet; a bad correlated day hits both)")
    return out


def edge_reconcile_all(now=None):
    """Closed loop (SYNTH-1 / MACRO-EDGE-01): per account, fold newly-CLOSED book deals into the persisted
    per-sleeve edge reconciler and return any per-sleeve decay alerts. Own short MT5 session per account
    (read-only history). Best-effort; never raises."""
    import datetime as _dt
    try:
        from src.components.ultimate_book.edge_reconciler import BookEdgeReconciler, closed_book_deals
    except Exception:
        return []
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = []
    for (label, path, _login, ns) in ACCOUNTS:
        if not mt5.initialize(path=path, portable=True):
            continue
        try:
            deals = closed_book_deals(mt5, now)
            for a in BookEdgeReconciler(repo, ns).ingest(deals):
                out.append(f"📉 EDGE [{label}] {a} — sizing keeps full weight; review the sleeve")
        except Exception:
            pass
        finally:
            mt5.shutdown()
    return out


def main():
    # line-buffer stdout so the redirected daemon log is not block-buffered (0-byte / liveness-blind):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    loop = None
    if "--loop" in sys.argv:
        loop = float(sys.argv[sys.argv.index("--loop") + 1])
    daemon_mode = loop is not None
    # SINGLE-INSTANCE guard (daemon mode): a second --loop monitor = duplicate Telegram alerts + divergent
    # dedup state. If another is already running, exit (the supervisor only ensures >=1, not exactly 1).
    if daemon_mode:
        _other = _another_monitor_running()
        if _other:
            print(f"another monitor_books --loop is already running (pid {_other}); single-instance exit")
            return
    fired = set()   # dedup: alert once per condition until it clears
    hb = 0
    while True:
        if daemon_mode:
            write_monitor_heartbeat("running", cycle=hb, loop_seconds=loop)
        print(f"=== MONITOR {dt.datetime.now(dt.timezone.utc).isoformat()} ===")
        metrics = [snap(l, p, lg) for (l, p, lg, ns) in ACCOUNTS]
        live = live_namespaces()
        # live-namespaces-failure-false-all-clear: when the process enumeration FAILS (live is None),
        # book_down/book_hung/book_broker_blind all return [] -> a SILENT all-clear that hides a real
        # monitoring outage. Surface it as a distinct alert instead of reporting healthy.
        monitoring_degraded = live is None
        down = book_down(live)
        hung = book_hung(live)
        blind = book_broker_blind(live)
        al = alerts(metrics, down, hung)
        if monitoring_degraded:
            al.append("🚨 MONITOR DEGRADED: cannot enumerate book processes this cycle (Win32_Process "
                      "query failed) — book up/down/hung/broker-blind status is UNVERIFIABLE, NOT all-clear")
        for ns in blind:
            al.append(f"🚨 BOOK BROKER-BLIND: {ns} worker is ticking but its broker/trade-server link is "
                      f"DOWN — orders/data impossible (investigate the terminal's connection)")
        # closed-loop edge reconciliation ~every 30 min (slow signal; bounds extra MT5 sessions)
        if (not loop) or (hb % 6 == 0):
            try:
                al.extend(edge_reconcile_all())
            except Exception:
                pass
        try:
            al.extend(firm_and_foreign_alerts(metrics))   # foreign legs + cross-account concentration
        except Exception:
            pass
        try:
            al.extend(disk_space_alert())                 # low-disk = silent persistence/alert failure
        except Exception:
            pass
        # CONNECT-FAIL = RISK BLIND: snap() returns {} when MT5 connect / account_info fails. Previously
        # that was only printed (alerts() skips empty metrics) -> the monitor was silently blind on that
        # account. Alert it (deduped via `fired`).
        for (_l, _p, _lg, _ns), _m in zip(ACCOUNTS, metrics):
            if not _m:
                al.append(f"🚨 MONITOR: cannot read {_l} (MT5 connect/account_info failed) — RISK BLIND on {_l}")
        # monitor-dedup-volatile-key: dedup on a STABLE key (the alert TYPE + account, with the volatile
        # numbers normalized out) so a condition alerts ONCE until it clears -- instead of re-firing every
        # cycle when a %/$/age value drifts a hundredth (-4.50% -> -4.51% was spamming the phone).
        def _dedup_key(a):
            return re.sub(r'[-+]?\d[\d,.:]*', '#', a)
        cur = {_dedup_key(a) for a in al}
        for a in al:
            if _dedup_key(a) not in fired:
                send(a)
        fired = cur
        if daemon_mode and (hb % 12 == 0):   # heartbeat summary ~hourly at 5-min cadence
            # show the EQUITY-based daily $ (matches the equity-based %); the old code paired the equity %
            # with realized-only $, which read "+0.20% $0" whenever nothing had closed yet (confusing).
            _ms = [m for m in metrics if m]
            ok = " | ".join(f"{m['label']} {m['daily_pl_pct']*100:+.2f}% ${m['daily_pl_usd']:+,.0f}" for m in _ms)
            firm = ""
            if len(_ms) >= 2:   # FIRM-LEVEL view (the two accounts are one correlated book)
                ceq = sum(m['eq'] for m in _ms)
                firm = (f" || FIRM eq ${ceq:,.0f} day ${sum(m['daily_pl_usd'] for m in _ms):+,.0f} "
                        f"gross {100.0 * sum(m['gross_pct'] * m['eq'] for m in _ms) / ceq:.2f}%" if ceq else "")
            send(f"📊 Book heartbeat: {ok}{firm}" + (f" | DOWN: {down}" if down else "")
                 + (f" | HUNG: {[h[0] for h in hung]}" if hung else ""))
        if daemon_mode:
            write_monitor_heartbeat(
                "completed",
                cycle=hb,
                loop_seconds=loop,
                monitoring_degraded=monitoring_degraded,
                alert_count=len(al),
                down=down,
                hung=[h[0] for h in hung],
                blind=blind,
            )
        if not daemon_mode:
            break
        hb += 1
        time.sleep(loop)


if __name__ == "__main__":
    main()

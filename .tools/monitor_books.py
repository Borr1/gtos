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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:                      # this file lives in .tools/, not on the path
    sys.path.insert(0, REPO_ROOT)
from src.utils.broker_clock import (  # noqa: E402
    NEW_YORK_PLUS_7,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
)

# (label, terminal, login, namespace, daily_reset_rule)
# The reset rule is THE FIRM'S, and the two firms differ -- see _reset_offset_h below.
ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", 531325516, "operator_profile", "Europe/Prague"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", 0, "redacted_account_live_bee34003", None),
]
DAILY_SOFT, DAILY_HARD, MAXDD, INIT_BAL = 0.03, 0.05, 0.10, 100000.0
GROSS_CAP = 0.04


def _reset_offset_h(now_utc, reset_rule=None):
    """Hours to add to UTC so that midnight of the result is THIS ACCOUNT'S daily reset.

    Replaces a hardcoded ``SRV_OFFSET_H = 3`` commented "FTMO/FN server = UTC+3 (EEST)",
    which was wrong three separate ways and this monitor drives the daily-loss alerts:

    1. **It was fixed at +3.** Both servers drop to +2 on the 1st Sunday of November, so
       from **2026-11-01** the constant would have mis-dated every deal in the 21:00-22:00
       UTC hour, under- or over-counting `realized_today` against the daily limit.
    2. **"EEST" names the wrong calendar.** Measured on the VPS over 81 weekly session
       boundaries per broker (2025-01-01..2026-07-26): both servers switch on the **US**
       DST dates -- 2025-03-09, 2025-11-02, 2026-03-08 -- and on none of the EU dates.
    3. **It applied one clock to both accounts.** FTMO's daily loss is measured
       "00:00:00 to 23:59:59 CE(S)T" (FTMO's own trading-objectives page, captured under
       research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/),
       which is NOT its server clock. redacted_account resets at server midnight and so takes
       no rule here.
    """
    if reset_rule:
        hours = daily_reset_offset_hours(now_utc, reset_rule)
        if hours is not None:
            return hours
    return offset_seconds_at_utc(now_utc, NEW_YORK_PLUS_7) / 3600.0


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


def snap(label, path, login, reset_rule=None):
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
        # The account's OWN daily-reset day, not a fixed +3 -- see _reset_offset_h.
        srv_today = (now + dt.timedelta(hours=_reset_offset_h(now, reset_rule))).date()
        deals = mt5.history_deals_get(now - dt.timedelta(hours=24), now + dt.timedelta(hours=13)) or []
        realized_today = sum(float(d.profit) + float(getattr(d, "swap", 0)) + float(getattr(d, "commission", 0))
                             for d in deals if getattr(d, "entry", 0) == 1
                             and dt.datetime.fromtimestamp(d.time, dt.timezone.utc).date() == srv_today)
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
    return [ns for (_l, _p, _lg, ns, _rr) in ACCOUNTS if ns not in live]


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
    for (_l, _p, _lg, ns, _rr) in ACCOUNTS:
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
    for (_l, _p, _lg, ns, _rr) in ACCOUNTS:
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


# ---------------------------------------------------------------------------
# Authority-gate tripwire
# ---------------------------------------------------------------------------
#
# The entire brake between this host and live orders is a small set of config
# booleans, and until now NOTHING watched them. A deliberate or mistaken edit
# would not have been detected by anything on the machine — the 2026-07-26 VPS
# inspection found no flag file, no terminal block and no scheduler stop, so
# there was no second line of defence and no observer either.
#
# The expected state is pinned HERE rather than in `config/agent_config.yaml`
# because that file is R2-decision-contract-bound (H1): editing it costs a
# re-seal plus ~16.5 machine-hours per affected window. A tripwire whose
# baseline lives in the file it is watching would also be self-defeating.
#
# Two independent questions are asked, because they fail at different times:
#   (1) what the config files say RIGHT NOW  -> catches an edit immediately,
#       before any restart makes it take effect. This is the early signal.
#   (2) what each RUNNING book resolved at startup -> catches a process that is
#       live-authorised while the file on disk says it should not be.
# Disagreement between the two is itself the alert: it means a flip happened
# and the books have not been restarted yet, or were restarted and then the
# file was put back.
EXPECTED_GATES = {
    # key -> expected value. `None` means "must be absent or false".
    "ultimate_book_enabled": True,             # master on; the book is meant to run in shadow
    "ultimate_book_apply_to_execution": True,  # may influence execution; still shadow without the two below
    "ultimate_book_live_activation_allowed": False,
    "ultimate_book_live_broker_authority": None,   # never present in any committed config
}
# Un-digested environment overrides. `config_digest_for` hashes only the base
# config plus the profile overlay, so every one of these can change live
# behaviour without invalidating an activation token. Reporting their resolved
# values is what makes that drift observable at all.
WATCHED_ENV = (
    "GTOS_UB_DERISK_MODE",          # overrides the derisk shape; see the >=2.0% interlock
    "GTOS_ACTIVATION_TOKEN_DIR",    # relocates the activation brake itself
    "GTOS_PROFILE",                 # replaces the whole risk contract
    "GTOS_MT5_TERMINAL_PATH",       # redirects which account receives orders
)


def _resolved_gates_from_disk(profile=None):
    """Resolve the four gate keys from the config files AS THEY ARE ON DISK NOW.

    Returns ``(gates, error)``. Deliberately re-reads rather than trusting a
    cached value: the whole point is to see an edit the running processes have
    not picked up yet.
    """
    try:
        import yaml
        from src.utils.config import apply_profile_overrides
        with open(os.path.join(REPO_ROOT, "config", "agent_config.yaml"), encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        if profile:
            cfg = apply_profile_overrides(cfg, profile)
        rt = cfg.get("gtos_vnext_runtime", cfg) or {}
        return {k: rt.get(k, None) for k in EXPECTED_GATES}, None
    except Exception as exc:
        return None, repr(exc)


def _gate_value_ok(key, value):
    expected = EXPECTED_GATES[key]
    if expected is None:
        return value is None or value is False
    return value is expected


def gate_tripwire():
    """Alert if the live-authority gates differ from their pinned expected state.

    Returns a list of alert strings. **Never returns [] for an unanswerable
    question** — an unreadable config, a heartbeat with no gate fields, or a
    gate key that has appeared from nowhere all produce an explicit
    UNVERIFIABLE alert, because a tripwire that reports all-clear when it
    cannot see is worse than none.
    """
    out = []

    # (1) the files on disk, per live profile
    for (label, _p, _lg, ns, _rr) in ACCOUNTS:
        gates, err = _resolved_gates_from_disk(ns)
        if gates is None:
            out.append(f"🚨 GATE STATE UNVERIFIABLE ({label}): cannot resolve the authority gates from "
                       f"config on disk ({err}) — this is NOT all-clear")
            continue
        for key, value in gates.items():
            if not _gate_value_ok(key, value):
                out.append(f"🚨 AUTHORITY GATE CHANGED ON DISK ({label}): {key}={value!r}, expected "
                           f"{EXPECTED_GATES[key]!r} — the live-order brake has been edited. If this was "
                           f"not you, treat it as an incident.")

    # (2) what each running book actually resolved
    repo = REPO_ROOT
    for (label, _p, _lg, ns, _rr) in ACCOUNTS:
        hb = os.path.join(repo, "pipeline_state", "ultimate_book", ns, "heartbeat.json")
        try:
            with open(hb, encoding="utf-8") as fh:
                rec = json.load(fh)
        except FileNotFoundError:
            continue          # book not started; book_down/book_hung own that signal
        except Exception as exc:
            out.append(f"🚨 GATE STATE UNVERIFIABLE ({label}): heartbeat unreadable ({exc!r})")
            continue
        # Only judge a heartbeat we can date; a stale one is book_hung's signal, not ours.
        try:
            ts = dt.datetime.fromisoformat(rec["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            if (dt.datetime.now(dt.timezone.utc) - ts).total_seconds() > 240:
                continue
        except Exception:
            continue
        running = rec.get("gates")
        if not isinstance(running, dict):
            out.append(f"🚨 GATE STATE UNVERIFIABLE ({label}): the running book publishes no gate state "
                       f"(pre-tripwire build) — restart it on a build that does, or the flip detector "
                       f"is blind to what this process actually resolved")
            continue
        for key in EXPECTED_GATES:
            if not _gate_value_ok(key, running.get(key)):
                out.append(f"🚨 RUNNING BOOK IS AUTHORISED ({label}): the live process resolved "
                           f"{key}={running.get(key)!r}, expected {EXPECTED_GATES[key]!r} — this worker "
                           f"can send real orders. Stop it now unless this is an intended activation.")
        if rec.get("runtime_effect_now") is True:
            out.append(f"🚨 LIVE ORDER AUTHORITY ACTIVE ({label}): runtime_effect_now=True — the book is "
                       f"NOT in shadow.")
        # Un-digested env drift: report a CHANGE against what the process started with.
        env_now = {k: os.environ.get(k) for k in WATCHED_ENV}
        env_book = rec.get("env") if isinstance(rec.get("env"), dict) else None
        if env_book is not None:
            for k in WATCHED_ENV:
                if env_book.get(k) != env_now.get(k):
                    out.append(f"⚠️ UN-DIGESTED ENV DRIFT ({label}): {k} is {env_now.get(k)!r} in the "
                               f"monitor but {env_book.get(k)!r} in the running book. This variable is "
                               f"outside the activation token's config digest, so it changes behaviour "
                               f"without invalidating the token.")

        # GTOS_UB_DERISK_MODE overrides the YAML at book_engine.py:580 -- env FIRST -- while the
        # token's config digest hashes only the two config FILES. So the env var is the one way to
        # make the effective derisk shape disagree with the config an activation token certifies,
        # and nothing recorded that it had. Two distinct failures, and they point opposite ways.
        effective = rec.get("derisk_mode_effective")
        declared = rec.get("derisk_mode_yaml")
        if effective is not None and declared is not None and effective != declared:
            out.append(f"⚠️ DERISK MODE OVERRIDDEN ({label}): running with {effective!r} while the config "
                       f"the activation token binds says {declared!r}. GTOS_UB_DERISK_MODE wins over YAML "
                       f"and is outside the config digest, so the token still validates.")
        if effective is not None and effective != "smooth" and _dial_requires_smooth(rec.get("profile")):
            out.append(f"🚨 BOOK IS SILENTLY FLAT ({label}): dial {rec.get('profile')!r} is >=2.0% and "
                       f"derisk mode is {effective!r}, not 'smooth' — admit_and_size fails closed and "
                       f"NO new entry will be admitted. The book looks healthy and takes no trades.")
    return out


def _dial_requires_smooth(profile_name):
    """True if this allocation dial is >=2.0%, where the ruin-safety interlock refuses any
    non-smooth drawdown shape (admission.py:1367). Returns False when the dial cannot be
    resolved -- the caller already alerts separately on unverifiable state, and guessing
    'yes' here would fire on every unknown profile name."""
    try:
        from src.components.ultimate_book.admission import ALLOCATION_PROFILES
        prof = ALLOCATION_PROFILES.get(profile_name)
        return prof is not None and float(prof.risk_per_unit_A) >= 0.02 - 1e-9
    except Exception:
        return False


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
    for (label, path, _login, ns, _rr) in ACCOUNTS:
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
    # Operator-delivery grant. Session M inverted notification delivery to presence-of-authorization
    # (`src/safety/notification_authorization.py`) and granted every producer it knew about — but this
    # file is `.tools/`, not `scripts/*_monitor.py`, and was missed. Without the grant EVERY alert this
    # daemon raises is refused by the transport, retried five times, marked FAILED and DROPPED, while
    # `write_monitor_heartbeat("completed")` keeps reporting the monitor healthy: the exact
    # healthy-process/zero-alerts shape B105 had just fixed. It silences BOOK DOWN, BOOK HUNG,
    # RISK BLIND, the soft-stop and max-DD warnings, LOW DISK, foreign legs, SILENTLY FLAT — and
    # `gate_tripwire()`, which per CLAUDE.md §4 is the only thing anywhere that would notice the live
    # authority gate being flipped on a funded, connected host. Found at wave-3 integration (B186);
    # neither branch is wrong alone. See `phase3/WAVE3_INTEGRATION.md` §4.4.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(reason=".tools/monitor_books.py alert daemon")
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
        metrics = [snap(l, p, lg, rr) for (l, p, lg, ns, rr) in ACCOUNTS]
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
        # NOTE the 5-tuple. B58 widened ACCOUNTS with `daily_reset_rule` and updated five of the six
        # unpack sites; this one was missed, and it is NOT inside a try -- so the daemon raised
        # `ValueError: too many values to unpack (expected 4, got 5)` on cycle 0, before any send(),
        # while write_monitor_heartbeat("running") had already fired so the supervisor saw it as
        # healthy and respawned it every 30 s into the same crash. The only alerting process in the
        # system was silent. See B105.
        for (_l, _p, _lg, _ns, _rr), _m in zip(ACCOUNTS, metrics):
            if not _m:
                al.append(f"🚨 MONITOR: cannot read {_l} (MT5 connect/account_info failed) — RISK BLIND on {_l}")
        try:
            al.extend(gate_tripwire())                    # authority-gate flip / un-digested env drift
        except Exception as _gt_e:                        # never let the tripwire's own failure be silence
            al.append(f"🚨 GATE TRIPWIRE FAILED ({_gt_e!r}) — authority-gate state is UNVERIFIABLE this "
                      f"cycle, NOT all-clear")
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

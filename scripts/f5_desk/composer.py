"""F5 slate composer — one ``gtos.judgment.slate.v2`` JSON per cycle.

Reads the streams the live book already writes (nothing new is asked of the tick
path), by byte cursor with rotation tolerance, and folds them into a durable
composer state so a crash/restart rediscovers nothing:

  * launcher tail stream  ``shadow_logs/ultimate_book_launcher.jsonl``
      action=cycle  -> candidates placed[], skipped[] (+reasons), n_intents
      action=manage -> adopted[] (ticket seeds for open-position reconstruction)
  * minimal-size events   ``shadow_logs/f5_minimal/<ns>/events.jsonl``
      f5_slate         -> standing intents (symbol/sleeve/decision_day),
                          sleeve->cluster map, governor descriptives
      f5_fill          -> open position born (ticket + candidate_id)
      f5_stop_move     -> entry/stop/target/locked_r/volume enrichment
      f5_trade_closed  -> open position retired
      f5_refusal_quote -> refusal context rows
  * flow sidecar dir      ``<repo_root>/judgment/`` (the book's consume seam) —
      existing verdict state echoed back so the Judge sees its standing words
  * live HIGH             ``f5_high_calendar.json`` + ``official_high_spine.json``
      (NFP 4 Sep live). Frozen ``data/news_calendar.json`` is gated on
      mtime/updated_at/valid_until and is never live HIGH.
  * clock/session block   UTC now, broker wall clock via src/utils/broker_clock
      (fail-open: unresolvable server -> offset absent), session name, minutes
      into session, day-of-week, weekend proximity

EX-POST EXCLUSION IS STRUCTURAL: candidate/refusal/skip sections pass through a
recursive scrub that drops every P&L-shaped key; the open-position block is
built by WHITELIST and carries entry/stop/target/age/locked_r only. A judge that
cannot see outcomes cannot be trained into outcome-chasing by its own context.

The slate is sha-pinned (content hash in the filename) and archived under
``pipeline_state/ultimate_book/<ns>/judgment/slates/``.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

_REPO_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_IMPORT))

from scripts.f5_desk import common

_log = logging.getLogger("f5_desk.composer")

SLATE_SCHEMA = "gtos.judgment.slate.v2"
PACKET_CONTRACT = "v2"

# P&L-shaped keys that must never reach a candidate/refusal/skip section.
EXPOST_KEYS = frozenset({
    "pnl", "profit", "realized_pnl", "realised_r", "realized_r",
    "broker_net_pnl_usd", "notional_pnl_usd", "real_pnl_usd_cumulative",
    "notional_equity_after", "equity", "realized_today_pct", "after",
    "floating_notional_pnl_usd", "broker_entry_swap", "broker_entry_commission",
})

# Open-position block: WHITELIST (the contract: entry/stop/target/age/locked_r
# plus identity + the risk taken at entry — the risk contract is not ex-post).
OPEN_POSITION_FIELDS = (
    "ticket", "symbol", "sleeve", "cluster", "direction", "candidate_id",
    "decision_day", "decision_bar_iso", "opened_utc", "age_minutes",
    "entry_price", "stop_now", "stop_prev", "take_profit_1", "locked_r",
    "current_volume", "intended_risk_usd", "actual_risk_usd", "last_checked_utc",
)

MAX_CANDIDATES = 40
MAX_REFUSALS = 30
MAX_SKIP_EXAMPLES = 10
MAX_CALENDAR = 40
CANDIDATE_STALE_H = 26.0  # keep today + yesterday's standing intents

INDEX_CCY = {
    "UK100": "GBP", "GER40": "EUR", "EU50": "EUR", "FRA40": "EUR",
    "US30": "USD", "US100": "USD", "US500": "USD", "NAS100": "USD",
    "SPX500": "USD", "JP225": "JPY", "AUS200": "AUD", "HK50": "HKD",
}
_CCY_CODES = frozenset({
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "CNH", "SGD",
    "XAU", "XAG", "XPT", "XPD", "HKD", "NOK", "SEK", "MXN", "ZAR", "PLN",
})
_CRYPTO_BASES = frozenset({
    "BTC", "ETH", "LTC", "XRP", "ADA", "SOL", "DOG", "DOGE", "XTZ", "AVA",
    "AVAX", "DOT", "BCH", "LNK", "LINK", "UNI", "EOS", "XLM", "TRX",
})


def symbol_currencies(symbol: str) -> list[str]:
    """Calendar-relevant currencies for one broker symbol. Best effort, never raises."""
    sym = str(symbol or "").upper().replace(".CASH", "").replace(".C", "").strip()
    if not sym:
        return []
    out: list[str] = []
    if sym in INDEX_CCY:
        out.append(INDEX_CCY[sym])
    elif sym.startswith(("UKOIL", "USOIL", "XBR", "XTI", "WTI", "BRENT", "NGAS", "XNG")):
        out.append("USD")
    elif len(sym) >= 6:
        base, quote = sym[:3], sym[3:6]
        if base in _CRYPTO_BASES or sym[:4] in _CRYPTO_BASES:
            out.append("USD")  # crypto quoted in USD: USD calendar is what moves it
        else:
            if base in _CCY_CODES:
                out.append(base)
            if quote in _CCY_CODES and quote not in out:
                out.append(quote)
    if not out and sym[-3:] in _CCY_CODES:
        out.append(sym[-3:])
    return out


def _direction_from_candidate_id(cid: str) -> Optional[str]:
    parts = str(cid or "").split("::")
    for token in parts:
        if token in ("LONG", "SHORT"):
            return token
    return None


def _direction_from_geometry(entry: Any, stop: Any) -> Optional[str]:
    try:
        e, s = float(entry), float(stop)
    except (TypeError, ValueError):
        return None
    if e > s:
        return "LONG"
    if e < s:
        return "SHORT"
    return None


def launcher_alias(symbol: str, sleeve: str, day: str) -> str:
    """The deterministic alias the book always queries (book_owner.py:6289)."""
    return f"LAUNCHER::{symbol}::{sleeve}::{str(day)[:10]}"


def w7_alias(cluster: str, symbol: str, day: str, direction: str, sleeve: str) -> str:
    return f"W7_BOOK::{cluster}::{symbol}::{str(day)[:10]}::{direction}::{sleeve}"


def strip_expost(obj: Any) -> Any:
    """Recursively drop P&L-shaped keys. Applied to every candidate-facing section."""
    if isinstance(obj, dict):
        return {
            k: strip_expost(v)
            for k, v in obj.items()
            if str(k).lower() not in EXPOST_KEYS
        }
    if isinstance(obj, list):
        return [strip_expost(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
@dataclass
class ComposerConfig:
    repo_root: Path = field(default_factory=common.repo_root_default)
    namespace: str = common.NAMESPACE
    broker_server: str = "FTMO-Server3"
    events_path: Optional[Path] = None
    launcher_path: Optional[Path] = None
    calendar_path: Optional[Path] = None
    high_spine_path: Optional[Path] = None
    news_brief_path: Optional[Path] = None
    f5_high_calendar_path: Optional[Path] = None
    state_dir: Optional[Path] = None
    flow_dir: Optional[Path] = None
    calendar_window_h: float = 12.0

    def __post_init__(self) -> None:
        self.repo_root = Path(self.repo_root)
        if self.events_path is None:
            self.events_path = self.repo_root / common.EVENTS_REL.format(ns=self.namespace)
        if self.launcher_path is None:
            self.launcher_path = self.repo_root / common.LAUNCHER_REL
        if self.calendar_path is None:
            self.calendar_path = self.repo_root / common.CALENDAR_REL
        if self.high_spine_path is None:
            self.high_spine_path = self.repo_root / "data" / "official_high_spine.json"
        if self.news_brief_path is None:
            self.news_brief_path = self.repo_root / "data" / "news_brief.json"
        if self.state_dir is None:
            self.state_dir = common.judgment_state_dir(self.repo_root, self.namespace)
        if self.flow_dir is None:
            self.flow_dir = common.flow_dir(self.repo_root)
        if self.f5_high_calendar_path is None:
            self.f5_high_calendar_path = (
                Path(self.state_dir) / "state" / "f5_high_calendar.json"
            )
        self.events_path = Path(self.events_path)
        self.launcher_path = Path(self.launcher_path)
        self.calendar_path = Path(self.calendar_path)
        self.high_spine_path = Path(self.high_spine_path)
        self.news_brief_path = Path(self.news_brief_path)
        self.f5_high_calendar_path = Path(self.f5_high_calendar_path)
        self.state_dir = Path(self.state_dir)
        self.flow_dir = Path(self.flow_dir)

    @property
    def slates_dir(self) -> Path:
        return self.state_dir / "slates"

    @property
    def internal_state_dir(self) -> Path:
        return self.state_dir / "state"

    @property
    def composer_state_path(self) -> Path:
        return self.internal_state_dir / "composer_state.json"

    @property
    def briefs_dir(self) -> Path:
        return self.state_dir / "briefs"


# ---------------------------------------------------------------------------
# clock / session block
# ---------------------------------------------------------------------------
_SESSIONS_UTC = (
    # (name, start_hour_utc, end_hour_utc) — end exclusive; asia wraps midnight.
    ("asia", 21, 7),
    ("london", 7, 12),
    ("newyork", 12, 21),
)


def _session_of(now: datetime) -> tuple[str, int]:
    """(session_name, minutes_into_session) from UTC wall clock. Deterministic."""
    hour = now.hour + now.minute / 60.0
    for name, start, end in _SESSIONS_UTC:
        if start < end:
            if start <= hour < end:
                return name, int((hour - start) * 60)
        else:  # wraps midnight
            if hour >= start:
                return name, int((hour - start) * 60)
            if hour < end:
                return name, int((hour + 24 - start) * 60)
    return "unknown", 0


def build_clock_block(now: datetime, broker_server: str) -> dict:
    session, minutes_in = _session_of(now)
    block: dict[str, Any] = {
        "now_utc": common.iso_utc(now),
        "utc_day": now.date().isoformat(),
        "day_of_week": now.strftime("%A"),
        "session": session,
        "minutes_into_session": minutes_in,
        "is_weekend_utc": now.weekday() >= 5,
        "in_dead_window": now.hour >= 21,
        "past_friday_new_risk_cutoff": (
            now.weekday() == 4 and (now.hour, now.minute) >= (16, 0)
        ),
    }
    # Broker wall clock via the measured rule; fail-open to absent on any error.
    try:
        from src.utils.broker_clock import resolve_rule, utc_to_broker_naive, offset_seconds_at_utc

        rule = resolve_rule(broker_server)
        broker_wall = utc_to_broker_naive(now, rule)
        offset_s = offset_seconds_at_utc(now, rule)
        block["broker_server"] = broker_server
        block["broker_wall_time"] = broker_wall.isoformat()
        block["broker_utc_offset_hours"] = offset_s / 3600.0
        # FX weekend closes at broker-wall Saturday 00:00 (= 17:00 New York Friday).
        wd = broker_wall.weekday()  # Mon=0 .. Sun=6
        days_to_sat = (5 - wd) % 7
        close_wall = (broker_wall + timedelta(days=days_to_sat)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if days_to_sat == 0 and broker_wall >= close_wall:
            close_wall += timedelta(days=7)
        minutes_to_close = (close_wall - broker_wall).total_seconds() / 60.0
        block["minutes_to_friday_close"] = round(minutes_to_close, 1)
        block["in_friday_close_window"] = 0 <= minutes_to_close <= 240 and wd == 4
        block["is_broker_weekend"] = wd >= 5
    except Exception as exc:
        block["broker_clock_error"] = f"{type(exc).__name__}"
        _log.info("composer: broker clock unresolved (%r) — clock block degrades to UTC-only", exc)
    return block


# ---------------------------------------------------------------------------
# stream ingest into durable composer state
# ---------------------------------------------------------------------------
def _blank_state() -> dict:
    return {
        "schema": "gtos.f5.composer_state.v1",
        "cursors": {},
        "open_positions": {},   # ticket(str) -> record
        "candidates": {},       # launcher_alias -> record
        "sleeve_cluster": {},   # sleeve -> cluster
        "governor": {},
        "refusals": [],
        "skips": [],
        "counters": {
            "events_lines": 0, "launcher_lines": 0, "parse_failures": 0,
            "fills_seen": 0, "closes_seen": 0, "unknown_close_tickets": 0,
        },
        "last_built_at_utc": None,
    }


def _load_state(cfg: ComposerConfig) -> dict:
    state = common.read_json(cfg.composer_state_path, default=None)
    if not isinstance(state, dict) or state.get("schema") != "gtos.f5.composer_state.v1":
        return _blank_state()
    base = _blank_state()
    base.update(state)
    for key in ("cursors", "open_positions", "candidates", "sleeve_cluster", "governor", "counters"):
        if not isinstance(base.get(key), dict):
            base[key] = {}
    for key in ("refusals", "skips"):
        if not isinstance(base.get(key), list):
            base[key] = []
    return base


def _candidate_record(state: dict, symbol: str, sleeve: str, day: str) -> dict:
    key = launcher_alias(symbol, sleeve, day)
    rec = state["candidates"].get(key)
    if not isinstance(rec, dict):
        rec = {
            "launcher_id": key,
            "symbol": symbol,
            "sleeve": sleeve,
            "decision_day": str(day)[:10],
            "status": "intent",
            "first_seen_utc": None,
            "last_seen_utc": None,
        }
        state["candidates"][key] = rec
    return rec


def _ingest_event(state: dict, obj: dict) -> None:
    kind = obj.get("event")
    ts = obj.get("ts_utc")
    if kind == "f5_slate":
        for unit in (obj.get("realized_units") or []) + (obj.get("would_units") or []):
            if not isinstance(unit, dict):
                continue
            cluster = unit.get("cluster")
            for slv in unit.get("sleeve_members") or []:
                if cluster and slv:
                    state["sleeve_cluster"][str(slv)] = str(cluster)
        gov = obj.get("governor")
        if isinstance(gov, dict):
            # Descriptive only, and never P&L: realized_today_pct/equity stay out.
            state["governor"] = {
                "allow": gov.get("allow"),
                "cap_mult": gov.get("cap_mult"),
                "open_risk_pct": gov.get("open_risk_pct"),
                "reason": gov.get("reason"),
                "as_of_utc": ts,
            }
        for intent in obj.get("intents") or []:
            if not isinstance(intent, dict):
                continue
            symbol = str(intent.get("symbol") or "")
            sleeve = str(intent.get("sleeve") or "")
            day = str(intent.get("decision_day") or "")[:10]
            if not (symbol and sleeve and day):
                continue
            rec = _candidate_record(state, symbol, sleeve, day)
            rec.setdefault("first_seen_utc", ts)
            rec["first_seen_utc"] = rec.get("first_seen_utc") or ts
            rec["last_seen_utc"] = ts
            # f5_slate now carries direction/geometry so the judge can HOLD
            # before fill. Older rows without these keys stay geometry-less.
            direction = (
                intent.get("direction")
                or _direction_from_candidate_id(str(intent.get("candidate_id") or ""))
                or _direction_from_geometry(intent.get("entry"), intent.get("stop"))
            )
            if direction:
                rec["direction"] = direction
            geometry = {
                key: intent.get(key)
                for key in ("entry", "stop", "target")
                if intent.get(key) is not None
            }
            if geometry:
                rec["geometry"] = geometry
            if intent.get("candidate_id"):
                rec["candidate_id"] = intent["candidate_id"]
            if intent.get("cluster"):
                rec["cluster"] = intent["cluster"]
                state["sleeve_cluster"][sleeve] = str(intent["cluster"])
            if intent.get("decision_bar_iso"):
                rec["decision_bar_iso"] = intent["decision_bar_iso"]
            if intent.get("stop_dist") is not None and "geometry" not in rec:
                rec["stop_dist"] = intent["stop_dist"]
    elif kind == "f5_fill":
        ticket = obj.get("ticket")
        if ticket is None:
            return
        state["counters"]["fills_seen"] += 1
        cid = str(obj.get("candidate_id") or "")
        rec = {
            "ticket": int(ticket),
            "symbol": obj.get("symbol"),
            "sleeve": obj.get("sleeve"),
            "candidate_id": cid or None,
            "direction": _direction_from_candidate_id(cid),
            "decision_day": obj.get("decision_day"),
            "decision_bar_iso": obj.get("decision_bar_iso"),
            "opened_utc": ts,
            "intended_risk_usd": obj.get("f5_intended_risk_usd"),
            "actual_risk_usd": obj.get("f5_actual_risk_usd"),
        }
        held = state["open_positions"].get(str(ticket))
        if isinstance(held, dict):
            held.update({k: v for k, v in rec.items() if v is not None})
        else:
            state["open_positions"][str(ticket)] = rec
        # the candidate is now a position — mark, so the Judge sees it moved
        if obj.get("symbol") and obj.get("sleeve") and obj.get("decision_day"):
            cand = _candidate_record(
                state, str(obj["symbol"]), str(obj["sleeve"]), str(obj["decision_day"])
            )
            cand["status"] = "filled"
            cand["ticket"] = int(ticket)
            cand["last_seen_utc"] = ts
            if cid:
                cand["candidate_id"] = cid
    elif kind == "f5_stop_move":
        ticket = obj.get("ticket")
        if ticket is None:
            return
        held = state["open_positions"].get(str(ticket))
        if not isinstance(held, dict):
            held = {"ticket": int(ticket), "symbol": obj.get("symbol"), "sleeve": obj.get("sleeve")}
            state["open_positions"][str(ticket)] = held
        held.update({
            "entry_price": obj.get("entry_price"),
            "stop_now": obj.get("stop_now"),
            "stop_prev": obj.get("stop_prev"),
            "take_profit_1": obj.get("take_profit_1"),
            "locked_r": obj.get("locked_r"),
            "current_volume": obj.get("current_volume"),
            "last_checked_utc": obj.get("checked_at_utc") or ts,
        })
        if not held.get("direction"):
            held["direction"] = _direction_from_geometry(obj.get("entry_price"), obj.get("stop_now"))
    elif kind == "f5_trade_closed":
        ticket = obj.get("ticket")
        if ticket is None:
            return
        state["counters"]["closes_seen"] += 1
        if state["open_positions"].pop(str(ticket), None) is None:
            state["counters"]["unknown_close_tickets"] += 1
    elif kind == "f5_refusal_quote":
        row = {
            "candidate_id": obj.get("candidate_id"),
            "symbol": obj.get("symbol"),
            "sleeve": obj.get("sleeve"),
            "decision_day": obj.get("decision_day"),
            "side": obj.get("side") or _direction_from_candidate_id(str(obj.get("candidate_id") or "")),
            "packet_class": obj.get("packet_class"),
            "refusal_reasons": (obj.get("refusal_reasons") or [])[:2],
            "frozen_price_intent_status": obj.get("frozen_price_intent_status"),
            "spread_price": obj.get("spread_price"),
            "spread_r_of_stop": obj.get("spread_r"),  # R denominator = this candidate's stop
            "stop_dist_price": obj.get("stop_dist"),
            "frozen_entry": obj.get("frozen_entry"),
            "quote_at_utc": obj.get("quote_at_utc") or ts,
            "ts_utc": ts,
        }
        state["refusals"].append(row)
        # refusal context also lands on the candidate record when identifiable
        if obj.get("symbol") and obj.get("sleeve") and obj.get("decision_day"):
            cand = _candidate_record(
                state, str(obj["symbol"]), str(obj["sleeve"]), str(obj["decision_day"])
            )
            if cand.get("status") not in ("filled", "placed"):
                cand["status"] = "refused"
            cand["last_refusal_class"] = obj.get("packet_class")
            cand["last_seen_utc"] = ts


def _ingest_launcher(state: dict, obj: dict, namespace: str) -> None:
    if str(obj.get("namespace") or "") != namespace:
        return
    action = obj.get("action")
    ts = obj.get("ts")
    if action == "cycle":
        for sk in obj.get("skipped") or []:
            if not isinstance(sk, dict):
                continue
            state["skips"].append({
                "symbol": sk.get("symbol"),
                "sleeve": sk.get("sleeve"),
                "reason": sk.get("reason"),
                "decision_bar_iso": sk.get("decision_bar_iso"),
                "ts_utc": ts,
            })
        for pl in obj.get("placed") or []:
            if not isinstance(pl, dict):
                continue
            symbol = str(pl.get("symbol") or "")
            sleeve = str(pl.get("sleeve") or "")
            day = str(pl.get("decision_day") or "")[:10]
            if not (symbol and sleeve and day):
                continue
            cand = _candidate_record(state, symbol, sleeve, day)
            cand["status"] = "placed" if cand.get("status") != "filled" else "filled"
            cand["candidate_id"] = pl.get("candidate_id") or cand.get("candidate_id")
            cand["cluster"] = pl.get("cluster") or cand.get("cluster")
            cand["direction"] = pl.get("direction") or cand.get("direction")
            cand["decision_bar_iso"] = pl.get("decision_bar_iso") or cand.get("decision_bar_iso")
            geometry = {
                "entry": pl.get("entry_price"),
                "stop": pl.get("stop_loss"),
                "target": pl.get("take_profit_1"),
            }
            if any(v is not None for v in geometry.values()):
                cand["geometry"] = geometry
            cand["last_seen_utc"] = ts
            if pl.get("cluster") and sleeve:
                state["sleeve_cluster"][sleeve] = str(pl["cluster"])
    elif action == "manage":
        for ad in obj.get("adopted") or []:
            if not isinstance(ad, dict) or ad.get("ticket") is None:
                continue
            ticket = str(ad["ticket"])
            held = state["open_positions"].get(ticket)
            if not isinstance(held, dict):
                state["open_positions"][ticket] = {
                    "ticket": int(ad["ticket"]),
                    "symbol": ad.get("symbol"),
                    "sleeve": ad.get("sleeve"),
                    "adopted": True,
                    "opened_utc": ts,
                }


def _prune_state(state: dict, now: datetime) -> None:
    cutoff = now - timedelta(hours=CANDIDATE_STALE_H)
    keep: dict[str, dict] = {}
    for key, rec in state["candidates"].items():
        seen = common.parse_utc(rec.get("last_seen_utc")) or common.parse_utc(rec.get("first_seen_utc"))
        day = str(rec.get("decision_day") or "")
        day_ok = day >= (now - timedelta(days=1)).date().isoformat()
        if day_ok and (seen is None or seen >= cutoff):
            keep[key] = rec
    state["candidates"] = keep
    today = now.date().isoformat()

    def _fresh(rows: list, field_name: str) -> list:
        out = []
        for row in rows[-200:]:
            ts = common.parse_utc(row.get(field_name))
            if ts is not None and ts.date().isoformat() == today:
                out.append(row)
        return out

    state["refusals"] = _fresh(state["refusals"], "ts_utc")[-MAX_REFUSALS * 2:]
    state["skips"] = _fresh(state["skips"], "ts_utc")[-200:]


# ---------------------------------------------------------------------------
# calendar
# ---------------------------------------------------------------------------
def _calendar_event_time(ev: dict) -> Optional[datetime]:
    sched = common.parse_utc(ev.get("scheduled_utc"))
    if sched is not None:
        return sched
    sched = common.parse_utc(ev.get("time_utc"))
    if sched is not None:
        return sched
    date = str(ev.get("date") or "").strip()
    clock = str(ev.get("time_utc") or "").strip()
    if date and clock:
        if len(clock) == 5:
            clock = clock + ":00"
        return common.parse_utc(f"{date}T{clock}Z")
    return None


# Frozen Mac-spine dump (data/news_calendar.json) is not a live HIGH source.
# 21 Aug 2026 mtime/updated_at must never fold as live. Spine + f5_high do.
CALENDAR_DUMP_LIVE_MAX_AGE_H = 48.0


def _calendar_dump_stamp(doc: object, path: Path) -> Optional[datetime]:
    if isinstance(doc, dict):
        for key in ("updated_at", "updated_utc", "as_of_utc", "calendar_updated_at"):
            stamp = common.parse_utc(doc.get(key))
            if stamp is not None:
                return stamp
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def _calendar_dump_is_live(path: Path, doc: object, now: datetime) -> tuple[bool, str]:
    """Gate news_calendar.json. Spine / f5_high_calendar are not gated here."""
    if isinstance(doc, dict) and doc.get("live") is False:
        return False, "live_false"
    if isinstance(doc, dict):
        vu = common.parse_utc(doc.get("valid_until_utc") or doc.get("valid_until"))
        if vu is not None and vu < now:
            return False, "valid_until_expired:" + common.iso_utc(vu)
    stamp = _calendar_dump_stamp(doc, path)
    if stamp is None:
        return False, "no_stamp"
    age_h = (now - stamp).total_seconds() / 3600.0
    if age_h > CALENDAR_DUMP_LIVE_MAX_AGE_H:
        return False, "stamp_stale:" + common.iso_utc(stamp) + f":{age_h:.1f}h"
    return True, "stamp_fresh:" + common.iso_utc(stamp)


def _fold_calendar_docs(
    cfg: ComposerConfig, now: Optional[datetime] = None,
) -> tuple[list[dict], dict]:
    """f5_high + spine + news_brief, then news_calendar only if the dump is live.

    Frozen 21-Aug ``data/news_calendar.json`` cannot be live HIGH. news_tape is
    not a source. Extra paths stay repo-relative so tests remain isolated.
    """
    now = now or common.now_utc()
    paths = [
        ("f5_high_calendar", cfg.f5_high_calendar_path, False),
        ("official_high_spine", cfg.high_spine_path, False),
        ("news_brief", cfg.news_brief_path, False),
        ("news_calendar", cfg.calendar_path, True),
    ]
    rows: list[dict] = []
    seen: set[tuple] = set()
    used: list[dict] = []
    skipped: list[dict] = []
    for label, path, is_dump in paths:
        if path is None:
            continue
        doc = common.read_json(path, default=None)
        if doc is None:
            skipped.append({"name": label, "path": str(path), "reason": "absent"})
            continue
        if is_dump:
            live, reason = _calendar_dump_is_live(path, doc, now)
            if not live:
                skipped.append({"name": label, "path": str(path), "reason": reason})
                continue
        if isinstance(doc, dict):
            batches = []
            for key in ("events", "calendar", "rows", "data", "absent_next_48h"):
                val = doc.get(key)
                if isinstance(val, list):
                    batches.extend(val)
        elif isinstance(doc, list):
            batches = doc
        else:
            skipped.append({"name": label, "path": str(path), "reason": "unreadable"})
            continue
        kept = 0
        for ev in batches:
            if not isinstance(ev, dict):
                continue
            name = str(ev.get("event") or ev.get("name") or ev.get("what") or "")
            sched = _calendar_event_time(ev)
            if sched is None or not name:
                continue
            ident = (name.lower(), common.iso_utc(sched))
            if ident in seen:
                continue
            seen.add(ident)
            row = dict(ev)
            row["event"] = name
            row["scheduled_utc"] = common.iso_utc(sched)
            imp = str(row.get("impact") or "")
            if imp.lower() == "high":
                row["impact"] = "HIGH"
            if not row.get("impact") and (
                row.get("official_high")
                or "nfp" in str(row.get("what") or "").lower()
                or "nfp" in name.lower()
            ):
                row["impact"] = "HIGH"
            rows.append(row)
            kept += 1
        used.append({"name": label, "path": str(path), "events_kept": kept})
    report = {"used": used, "skipped": skipped}
    return rows, report


def calendar_window(cfg: ComposerConfig, now: datetime, symbols: list[str],
                    fold_report: Optional[dict] = None) -> list[dict]:
    """Events within +/-window hours, tagged with the slate symbols they touch."""
    try:
        events, report = _fold_calendar_docs(cfg, now=now)
        if fold_report is not None:
            fold_report.clear()
            fold_report.update(report)
        if not events:
            return []
        relevant_ccy: dict[str, list[str]] = {}
        for sym in symbols:
            relevant_ccy[sym] = symbol_currencies(sym)
        lo = now - timedelta(hours=cfg.calendar_window_h)
        hi = now + timedelta(hours=cfg.calendar_window_h)
        out = []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            sched = _calendar_event_time(ev)
            if sched is None or not (lo <= sched <= hi):
                continue
            ccy = str(ev.get("currency") or "")
            tickets = [
                str(s).upper().replace(".CASH", "").replace("_CASH", "").replace(".", "")
                for s in (ev.get("tickets") or ev.get("symbols") or [])
                if s
            ]
            touches = [
                sym for sym, ccys in relevant_ccy.items()
                if ccy == "ALL" or ccy in ccys or str(sym).upper() in tickets
            ]
            out.append({
                "event": ev.get("event"),
                "impact": ev.get("impact"),
                "currency": ccy,
                "event_type": ev.get("event_type"),
                "role": ev.get("role"),
                "scheduled_utc": common.iso_utc(sched),
                "minutes_from_now": round((sched - now).total_seconds() / 60.0, 1),
                "touches_symbols": touches,
            })
        impact_rank = {"HIGH": 0, "high": 0, "MEDIUM": 1, "LOW": 2}
        out.sort(key=lambda e: (impact_rank.get(str(e.get("impact")), 3),
                                abs(e.get("minutes_from_now") or 0.0)))
        return out[:MAX_CALENDAR]
    except Exception as exc:
        _log.warning("composer: calendar window failed (%r) -> []", exc)
        return []


# ---------------------------------------------------------------------------
# flow sidecar echo (the Judge's standing words, as the book would read them)
# ---------------------------------------------------------------------------
def flow_state_echo(cfg: ComposerConfig, now: datetime, candidate_ids: list[str]) -> dict:
    try:
        day = now.date().isoformat()
        echo: dict[str, Any] = {"entries": {}, "other_entries": 0, "files_read": []}
        for name in (f"flow_{day}.json", f"consume_{day}.json", f"verdicts_{day}.json"):
            path = cfg.flow_dir / name
            data = common.read_json(path, default=None)
            if not isinstance(data, dict):
                continue
            echo["files_read"].append(name)
            for cid, entry in data.items():
                if not isinstance(entry, dict):
                    continue
                if cid in candidate_ids:
                    if cid not in echo["entries"]:
                        written = common.parse_utc(entry.get("written_at_utc") or entry.get("ts"))
                        age_s = (now - written).total_seconds() if written else None
                        try:
                            ttl = float(entry.get("ttl_s"))
                        except (TypeError, ValueError):
                            ttl = None
                        echo["entries"][cid] = {
                            "action": entry.get("action"),
                            "verdict": entry.get("verdict"),
                            "why_code": entry.get("why_code"),
                            "written_at_utc": entry.get("written_at_utc") or entry.get("ts"),
                            "ttl_s": entry.get("ttl_s"),
                            "age_s": round(age_s, 1) if age_s is not None else None,
                            "fresh_now": bool(
                                written is not None and ttl and age_s is not None and age_s <= ttl
                            ),
                            "source_file": name,
                        }
                else:
                    echo["other_entries"] += 1
        return echo
    except Exception as exc:
        _log.warning("composer: flow echo failed (%r) -> {}", exc)
        return {"entries": {}, "other_entries": 0, "files_read": []}


# ---------------------------------------------------------------------------
# slate assembly
# ---------------------------------------------------------------------------
def _candidate_view(state: dict, rec: dict, now: datetime, calendar: list[dict]) -> dict:
    symbol = str(rec.get("symbol") or "")
    sleeve = str(rec.get("sleeve") or "")
    day = str(rec.get("decision_day") or "")[:10]
    cluster = rec.get("cluster") or state["sleeve_cluster"].get(sleeve)
    direction = rec.get("direction") or _direction_from_candidate_id(str(rec.get("candidate_id") or ""))
    if not direction and isinstance(rec.get("geometry"), dict):
        direction = _direction_from_geometry(rec["geometry"].get("entry"), rec["geometry"].get("stop"))
    alias_ids = [rec["launcher_id"]]
    cid = rec.get("candidate_id")
    if cid and cid not in alias_ids:
        alias_ids.insert(0, str(cid))
    elif cluster and direction:
        w7 = w7_alias(str(cluster), symbol, day, str(direction), sleeve)
        if w7 not in alias_ids:
            alias_ids.insert(0, w7)
    high_min = None
    high_signed = None
    ccys = set(symbol_currencies(symbol))
    try:
        from src.components.ultimate_book.minimal_size import (
            F5_HIGH_POST_MIN as _HIGH_POST,
            F5_HIGH_PRE_MIN as _HIGH_PRE,
        )
    except Exception:
        _HIGH_PRE, _HIGH_POST = 15.0, 60.0
    for ev in calendar:
        if str(ev.get("impact")) != "HIGH":
            continue
        if ev.get("currency") == "ALL" or ev.get("currency") in ccys:
            try:
                signed = float(ev.get("minutes_from_now") or 0.0)
            except (TypeError, ValueError):
                continue
            m = abs(signed)
            if high_min is None or m < high_min:
                high_min = m
            in_window = -float(_HIGH_POST) <= signed <= float(_HIGH_PRE)
            if in_window and (high_signed is None or abs(signed) < abs(high_signed)):
                high_signed = signed
    view = {
        "candidate_id": alias_ids[0],
        "alias_ids": alias_ids,
        "status": rec.get("status") or "intent",
        "symbol": symbol,
        "sleeve": sleeve,
        "cluster": cluster,
        "direction": direction,
        "decision_day": day,
        "decision_bar_iso": rec.get("decision_bar_iso"),
        "geometry": rec.get("geometry"),
        "last_refusal_class": rec.get("last_refusal_class"),
        "first_seen_utc": rec.get("first_seen_utc"),
        "last_seen_utc": rec.get("last_seen_utc"),
        "minutes_to_nearest_high_impact": high_min,
        "high_impact_minutes": high_signed,
        "stop_dist": rec.get("stop_dist"),
    }
    return {k: v for k, v in view.items() if v is not None}


OPEN_ROW_STALE_H = 48.0
OPEN_ROW_FRESH_FILL_MIN = 30.0


def _open_row_is_live(rec: dict, now: datetime) -> bool:
    """Drop pre-desk phantoms: rows whose broker close the packet stream never
    saw (closes during book downtime, pre-desk eras). A REAL open position is
    re-observed at latest on the first manage pass after every book restart
    (``f5_stop_move`` emits on first observation per process), so it always has
    ``stop_now`` plus a ``last_checked_utc``/``opened_utc`` newer than the last
    restart. Clauses: (a) geometry known and checked/opened within 48 h, or
    (b) filled within the last 30 min (manage pass may not have run yet).
    Residual known miss: a close during downtime stays visible up to 48 h."""
    checked = common.parse_utc(rec.get("last_checked_utc"))
    opened = common.parse_utc(rec.get("opened_utc"))
    if rec.get("stop_now") is not None:
        newest = max((t for t in (checked, opened) if t is not None), default=None)
        if newest is not None and (now - newest).total_seconds() <= OPEN_ROW_STALE_H * 3600.0:
            return True
    if opened is not None and (now - opened).total_seconds() <= OPEN_ROW_FRESH_FILL_MIN * 60.0:
        return True
    return False


def _open_position_view(rec: dict, state: dict, now: datetime) -> dict:
    view = {k: rec.get(k) for k in OPEN_POSITION_FIELDS if rec.get(k) is not None}
    sleeve = str(rec.get("sleeve") or "")
    if "cluster" not in view and sleeve:
        cluster = state["sleeve_cluster"].get(sleeve)
        if cluster:
            view["cluster"] = cluster
    opened = common.parse_utc(rec.get("opened_utc"))
    if opened is not None:
        view["age_minutes"] = round((now - opened).total_seconds() / 60.0, 1)
    if not view.get("direction"):
        d = _direction_from_geometry(rec.get("entry_price"), rec.get("stop_now"))
        if d:
            view["direction"] = d
    return view


def slate_fingerprint(slate: dict) -> str:
    """Judge-relevance fingerprint: the candidate set (id+status) and the open
    set (ticket+direction). Quote churn and clock movement do NOT change it."""
    cands = sorted(
        f"{c.get('candidate_id')}|{c.get('status')}"
        for c in slate.get("candidates") or []
    )
    opens = sorted(
        f"{p.get('ticket')}|{p.get('direction')}"
        for p in slate.get("open_positions") or []
    )
    return common.sha256_hex(common.canonical_json({"c": cands, "o": opens}))[:16]


def build_slate(cfg: ComposerConfig, now_utc: Optional[datetime] = None,
                persist: bool = True) -> tuple[dict, Optional[Path]]:
    """Tail streams, fold state, emit one sha-pinned slate. Never raises.

    Returns ``(slate_dict, archived_path_or_None)``.
    """
    now = now_utc or common.now_utc()
    state = _load_state(cfg)

    ev_lines, ev_cur = common.tail_new_lines(cfg.events_path, state["cursors"].get("events"))
    la_lines, la_cur = common.tail_new_lines(cfg.launcher_path, state["cursors"].get("launcher"))
    state["cursors"]["events"] = ev_cur
    state["cursors"]["launcher"] = la_cur

    parsed = 0
    for obj in common.iter_json_lines(ev_lines):
        parsed += 1
        try:
            _ingest_event(state, obj)
        except Exception as exc:
            state["counters"]["parse_failures"] += 1
            _log.warning("composer: event ingest failed (%r) — line skipped", exc)
    for obj in common.iter_json_lines(la_lines):
        parsed += 1
        try:
            _ingest_launcher(state, obj, cfg.namespace)
        except Exception as exc:
            state["counters"]["parse_failures"] += 1
            _log.warning("composer: launcher ingest failed (%r) — line skipped", exc)
    state["counters"]["events_lines"] += len(ev_lines)
    state["counters"]["launcher_lines"] += len(la_lines)
    state["counters"]["parse_failures"] += (len(ev_lines) + len(la_lines)) - parsed

    _prune_state(state, now)

    # ---- sections -------------------------------------------------------
    candidates_raw = sorted(
        state["candidates"].values(),
        key=lambda r: str(r.get("last_seen_utc") or ""), reverse=True,
    )[:MAX_CANDIDATES]

    symbols = sorted({
        str(r.get("symbol") or "") for r in candidates_raw if r.get("symbol")
    } | {
        str(p.get("symbol") or "") for p in state["open_positions"].values() if p.get("symbol")
    })
    fold_report: dict = {}
    calendar = calendar_window(cfg, now, symbols, fold_report=fold_report)

    candidates = [strip_expost(_candidate_view(state, r, now, calendar)) for r in candidates_raw]

    open_rows = sorted(state["open_positions"].values(), key=lambda r: r.get("ticket") or 0)
    live_rows = [rec for rec in open_rows if _open_row_is_live(rec, now)]
    state["counters"]["stale_open_rows_hidden"] = len(open_rows) - len(live_rows)
    open_positions = [_open_position_view(rec, state, now) for rec in live_rows]

    refusals = strip_expost(state["refusals"][-MAX_REFUSALS:])

    skip_counts: dict[str, int] = {}
    for sk in state["skips"]:
        reason = str(sk.get("reason") or "unknown")
        skip_counts[reason] = skip_counts.get(reason, 0) + 1
    skips = strip_expost({
        "counts_today": skip_counts,
        "recent": state["skips"][-MAX_SKIP_EXAMPLES:],
    })

    all_ids: list[str] = []
    for cand in candidates:
        for cid in cand.get("alias_ids") or []:
            if cid not in all_ids:
                all_ids.append(cid)

    slate = {
        "schema": SLATE_SCHEMA,
        "packet_contract": PACKET_CONTRACT,
        "namespace": cfg.namespace,
        "built_at_utc": common.iso_utc(now),
        "clock": build_clock_block(now, cfg.broker_server),
        "governor": dict(state.get("governor") or {}),
        "candidates": candidates,
        "open_positions": open_positions,
        "refusals": refusals,
        "skips": skips,
        "flow_state": flow_state_echo(cfg, now, all_ids),
        "calendar": calendar,
        "calendar_fold": fold_report,
        "counters": dict(state["counters"]),
    }
    body = {k: v for k, v in slate.items() if k != "built_at_utc"}
    slate["slate_id"] = common.sha256_hex(common.canonical_json(body))[:16]
    slate["fingerprint"] = slate_fingerprint(slate)
    try:
        from scripts.f5_desk.chair_briefs import fold_desk_briefs
        slate["desk_briefs"] = fold_desk_briefs(cfg.briefs_dir, now)
    except Exception as exc:  # noqa: BLE001 — briefs never block a slate
        slate["desk_briefs"] = {"present": False, "error": str(exc)[:120]}

    archived: Optional[Path] = None
    if persist:
        state["last_built_at_utc"] = slate["built_at_utc"]
        common.write_json_atomic(cfg.composer_state_path, state)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        archived = cfg.slates_dir / f"slate_{stamp}_{slate['slate_id']}.json"
        if not common.write_json_atomic(archived, slate):
            archived = None
        common.write_json_atomic(cfg.internal_state_dir / "latest_slate.json", {
            "slate_id": slate["slate_id"],
            "fingerprint": slate["fingerprint"],
            "path": str(archived) if archived else None,
            "built_at_utc": slate["built_at_utc"],
        })
    return slate, archived


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build one F5 judgment slate from the live streams.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--namespace", default=common.NAMESPACE)
    parser.add_argument("--no-persist", action="store_true",
                        help="build and print only; do not advance cursors or archive")
    args = parser.parse_args(argv)
    common.setup_logging()
    cfg = ComposerConfig(
        repo_root=Path(args.repo_root) if args.repo_root else common.repo_root_default(),
        namespace=args.namespace,
    )
    slate, path = build_slate(cfg, persist=not args.no_persist)
    print(json.dumps({
        "slate_id": slate["slate_id"],
        "fingerprint": slate["fingerprint"],
        "candidates": len(slate["candidates"]),
        "open_positions": len(slate["open_positions"]),
        "refusals": len(slate["refusals"]),
        "calendar": len(slate["calendar"]),
        "archived": str(path) if path else None,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

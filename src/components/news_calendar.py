"""News calendar component for FTMO-grade event blocking.

Provides tighter pre/post event windows (15min/2min default) compared to the
development-grade economic_calendar utility (120min/30min).

Calendar source priority:
1. MT5 calendar API (Windows only — mt5.calendar_country_by_id)
2. JSON file (data/news_calendar.json) — operator updates weekly
3. CSV fallback (data/economic_calendar.csv) — existing system

When news_filter.enabled is true, this component REPLACES the
economic_calendar blocking in the orchestrator pipeline.

Usage:
    cal = NewsCalendar(config)
    blocked, reason = cal.should_skip("XAUUSD", current_time_utc)
    if blocked:
        log("SKIP_NEWS_EVENT", reason)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Currency map: which currencies affect which instruments
_DEFAULT_CURRENCY_MAP = {
    "XAUUSD": ["USD"],
    "GBPUSD": ["USD", "GBP"],
    "EURUSD": ["USD", "EUR"],
    "USDJPY": ["USD", "JPY"],
    "GBPJPY": ["GBP", "JPY"],
    "NZDUSD": ["USD", "NZD"],
    "US30_cash": ["USD"],
    "NAS100": ["USD"],
    "XAGUSD": ["USD"],
}


class NewsCalendar:
    """FTMO-grade news event filter.

    Blocks trade evaluation when a HIGH-impact event is imminent.
    Designed for funded account risk management.
    """

    def __init__(self, config: dict):
        self._config = config.get("news_filter", {})
        self._enabled = self._config.get("enabled", False)
        self._pre_block = self._config.get("pre_event_block_minutes", 15)
        self._post_block = self._config.get("post_event_block_minutes", 2)
        self._impact_levels = {
            lvl.upper() for lvl in self._config.get("impact_levels", ["HIGH"])
        }
        self._affected_currencies = {
            c.upper() for c in self._config.get("affected_currencies", ["USD"])
        }
        self._currency_map = config.get(
            "economic_calendar", {}
        ).get("currency_map", _DEFAULT_CURRENCY_MAP)

        self._events: list[dict] = []

        if self._enabled:
            self._events = self._load_events()
            if self._events:
                upcoming = sum(
                    1 for e in self._events
                    if e["datetime_utc"] > datetime.now(timezone.utc)
                )
                logger.info(
                    "NewsCalendar loaded %d events (%d upcoming), "
                    "blocking %dmin pre / %dmin post for %s impact",
                    len(self._events), upcoming,
                    self._pre_block, self._post_block,
                    ",".join(sorted(self._impact_levels)),
                )
            else:
                logger.warning(
                    "NewsCalendar enabled but NO events loaded — "
                    "all trades will proceed without event awareness"
                )
        else:
            logger.info("NewsCalendar disabled in config (news_filter.enabled=false)")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def events(self) -> list[dict]:
        return self._events

    def should_skip(
        self,
        symbol: str,
        current_time: datetime,
    ) -> tuple[bool, Optional[str]]:
        """Check if trading should be skipped for the given symbol.

        Returns:
            (should_skip, reason)
            reason example: "SKIP_NEWS_EVENT: NFP in 12 minutes"
        """
        if not self._enabled or not self._events:
            return False, None

        # Get currencies that affect this instrument
        relevant_currencies = set(
            c.upper() for c in self._currency_map.get(symbol.upper(), ["USD"])
        )
        # Intersect with configured affected currencies
        check_currencies = relevant_currencies & self._affected_currencies
        if not check_currencies:
            return False, None

        window_start = current_time - timedelta(minutes=self._post_block)
        window_end = current_time + timedelta(minutes=self._pre_block)

        blocking = []
        for event in self._events:
            if event["impact"] not in self._impact_levels:
                continue
            if event["currency"] not in check_currencies:
                continue
            if window_start <= event["datetime_utc"] <= window_end:
                blocking.append(event)

        if not blocking:
            return False, None

        # Pick closest event for the reason string
        closest = min(
            blocking,
            key=lambda e: abs((e["datetime_utc"] - current_time).total_seconds()),
        )
        delta_seconds = (closest["datetime_utc"] - current_time).total_seconds()
        delta_minutes = int(delta_seconds / 60)

        if delta_minutes > 0:
            reason = f"SKIP_NEWS_EVENT: {closest['event']} in {delta_minutes}min"
        elif delta_minutes == 0:
            reason = f"SKIP_NEWS_EVENT: {closest['event']} NOW"
        else:
            reason = f"SKIP_NEWS_EVENT: {closest['event']} was {abs(delta_minutes)}min ago"

        return True, reason

    def get_next_event(
        self,
        symbol: str,
        current_time: datetime,
    ) -> Optional[dict]:
        """Get the next upcoming event affecting this symbol (for logging)."""
        relevant_currencies = set(
            c.upper() for c in self._currency_map.get(symbol.upper(), ["USD"])
        )
        check_currencies = relevant_currencies & self._affected_currencies

        future_events = [
            e for e in self._events
            if e["datetime_utc"] > current_time
            and e["impact"] in self._impact_levels
            and e["currency"] in check_currencies
        ]
        if not future_events:
            return None
        return min(future_events, key=lambda e: e["datetime_utc"])

    # ── Loading ──────────────────────────────────────────────

    def _load_events(self) -> list[dict]:
        """Load events using priority: MT5 → JSON → CSV."""
        source = self._config.get("calendar_source", "json")

        # Try MT5 first if configured
        if source == "mt5":
            events = self._load_from_mt5()
            if events:
                return events
            logger.warning("MT5 calendar unavailable, falling back to JSON/CSV")

        # Try JSON
        if source in ("mt5", "json"):
            json_path = self._config.get(
                "json_calendar_file", "data/news_calendar.json"
            )
            events = self._load_from_json(json_path)
            if events:
                return events
            if source == "json":
                logger.warning("JSON calendar empty/missing, falling back to CSV")

        # CSV fallback
        csv_path = self._config.get(
            "csv_calendar_file", "data/economic_calendar.csv"
        )
        return self._load_from_csv(csv_path)

    @staticmethod
    def _load_from_mt5() -> list[dict]:
        """Try to load events from MT5 calendar API (Windows only)."""
        try:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("MetaTrader5 package not available")
            return []

        if not mt5.initialize():
            logger.debug("MT5 initialize() failed")
            return []

        try:
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=1)
            end = now + timedelta(days=14)

            # MT5 calendar functions vary by terminal version
            raw_events = None
            for currency in ["USD", "GBP", "EUR", "JPY", "NZD"]:
                try:
                    batch = mt5.calendar_country_by_id(0)  # Try generic
                    if batch:
                        raw_events = batch
                        break
                except Exception:
                    pass

            if not raw_events:
                # Try the direct function if available
                try:
                    raw_events = mt5.calendar_get("USD", start, end)
                except Exception:
                    pass

            if not raw_events:
                return []

            events = []
            for e in raw_events:
                try:
                    impact = getattr(e, "importance", 0)
                    # MT5 importance: 0=none, 1=low, 2=medium, 3=high
                    if impact < 3:
                        continue
                    events.append({
                        "datetime_utc": datetime.fromtimestamp(
                            e.time, tz=timezone.utc
                        ),
                        "event": getattr(e, "name", "Unknown"),
                        "impact": "HIGH",
                        "currency": getattr(e, "currency", "USD").upper(),
                        "source": "mt5",
                    })
                except Exception:
                    continue

            logger.info("Loaded %d HIGH-impact events from MT5 calendar", len(events))
            return events

        except Exception as e:
            logger.warning("MT5 calendar read failed: %s", e)
            return []
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass

    @staticmethod
    def _load_from_json(filepath: str) -> list[dict]:
        """Load events from JSON file.

        Expected format:
        {
          "week_of": "2026-04-07",
          "updated_at": "2026-04-06T18:00:00Z",
          "events": [
            {
              "date": "2026-04-08",
              "time_utc": "12:30",
              "event": "US CPI",
              "impact": "HIGH",
              "currency": "USD"
            }
          ]
        }
        """
        path = Path(filepath)
        if not path.exists():
            logger.debug("JSON calendar not found at %s", filepath)
            return []

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read JSON calendar %s: %s", filepath, e)
            return []

        raw_events = data.get("events", [])
        if not raw_events:
            logger.warning("JSON calendar at %s has no events", filepath)
            return []

        # Warn if stale
        updated_at = data.get("updated_at")
        if updated_at:
            try:
                updated_dt = datetime.fromisoformat(
                    updated_at.replace("Z", "+00:00")
                )
                age_days = (datetime.now(timezone.utc) - updated_dt).days
                if age_days > 7:
                    logger.warning(
                        "JSON calendar is %d days old — update from ForexFactory",
                        age_days,
                    )
            except (ValueError, TypeError):
                pass

        events = []
        for row in raw_events:
            try:
                dt = datetime.strptime(
                    f"{row['date']} {row['time_utc']}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=timezone.utc)
                events.append({
                    "datetime_utc": dt,
                    "event": row.get("event", "Unknown"),
                    "impact": row.get("impact", "HIGH").upper(),
                    "currency": row.get("currency", "USD").upper(),
                    "source": "json",
                })
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed JSON event: %s (%s)", row, e)

        logger.info("Loaded %d events from JSON calendar %s", len(events), filepath)
        return events

    @staticmethod
    def _load_from_csv(filepath: str) -> list[dict]:
        """Load events from CSV (reuses existing economic_calendar format)."""
        import csv as csv_mod

        path = Path(filepath)
        if not path.exists():
            logger.warning("CSV calendar not found at %s", filepath)
            return []

        events = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv_mod.DictReader(f)
                for row in reader:
                    try:
                        dt = datetime.strptime(
                            f"{row['date'].strip()} {row['time_utc'].strip()}",
                            "%Y-%m-%d %H:%M",
                        ).replace(tzinfo=timezone.utc)
                        events.append({
                            "datetime_utc": dt,
                            "event": row.get("event", "").strip(),
                            "impact": row.get("impact", "").strip().upper(),
                            "currency": row.get("currency", "").strip().upper(),
                            "source": "csv",
                        })
                    except (KeyError, ValueError):
                        continue
        except Exception as e:
            logger.warning("Failed to read CSV calendar %s: %s", filepath, e)

        if events:
            logger.info("Loaded %d events from CSV calendar %s", len(events), filepath)
        return events

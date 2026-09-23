#!/usr/bin/env python3
"""Fetch the official ForexFactory *this-week* calendar. Do not invent events.

Writes a dated snapshot under data/news/. Never overwrites data/news_calendar.json
(the June 2026-05-31 operator week of record).

If the fetch fails, exit 2 with spine_empty honesty — do not hand-write HIGH rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "news"


def fetch(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "gtos-judgment-news-repair/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if getattr(resp, "status", 200) != 200:
            raise RuntimeError(f"http_{resp.status}")
        return resp.read()


def to_gtos_high(rows: list[dict]) -> list[dict]:
    high = []
    for row in rows:
        impact = str(row.get("impact") or "").strip().lower()
        if impact != "high":
            continue
        date = str(row.get("date") or "")
        dt = date
        # FF dates look like 2026-09-17T08:30:00-04:00
        try:
            parsed = datetime.fromisoformat(dt)
            utc = parsed.astimezone(timezone.utc)
            date_s = utc.date().isoformat()
            time_s = utc.strftime("%H:%M")
            datetime_utc = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
        country = str(row.get("country") or "").strip()
        currency = {
            "United States": "USD",
            "US": "USD",
            "United Kingdom": "GBP",
            "UK": "GBP",
            "Euro Zone": "EUR",
            "EMU": "EUR",
            "Japan": "JPY",
            "Australia": "AUD",
            "Canada": "CAD",
            "New Zealand": "NZD",
            "Switzerland": "CHF",
            "China": "CNY",
        }.get(country, country[:3].upper() if country else "")
        high.append(
            {
                "date": date_s,
                "time_utc": time_s,
                "datetime_utc": datetime_utc,
                "event": str(row.get("title") or "").strip(),
                "impact": "HIGH",
                "currency": currency,
                "country": country,
                "forecast": row.get("forecast"),
                "previous": row.get("previous"),
            }
        )
    return high


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=FF_URL)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    try:
        raw = fetch(args.url, args.timeout)
    except Exception as exc:
        print(f"FETCH_FAIL spine_empty remains: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        print(f"PARSE_FAIL: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, list):
        print("PARSE_FAIL: expected a JSON list", file=sys.stderr)
        return 2
    high = to_gtos_high(payload)
    digest = hashlib.sha256(raw).hexdigest()
    snapshot = {
        "schema": "gtos.news.ff_thisweek_snapshot.v0",
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": args.url,
        "source_sha256": digest,
        "n_raw": len(payload),
        "n_high": len(high),
        "notes": [
            "Official ForexFactory this-week export. Not invented.",
            "Does not overwrite data/news_calendar.json (2026-06-01..05 week of record).",
            "Challenge dates before this week's first event remain uncovered.",
        ],
        "events": high,
    }
    raw_out = OUT_DIR / f"ff_thisweek_raw_{stamp}.json"
    high_out = OUT_DIR / f"high_spine_ff_thisweek_{stamp}.json"
    print(f"raw={len(payload)} high={len(high)} sha256={digest}")
    if args.dry_run:
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_out.write_bytes(raw)
    high_out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {raw_out.relative_to(REPO)}")
    print(f"wrote {high_out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

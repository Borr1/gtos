"""Cross-analysis helper for EURUSD T7 sim.
Loads the 2280-record JSON, exposes per-decision collections with parsed
raw_response data. Used by A/B/C/D/E/F agent scripts to share parsing logic.

Usage (ad hoc via python -c or interactive):
    from eurusd_extract import load_results, SIM_JSON, M15_CSV, D1_CSV
    rs = load_results()
"""

from __future__ import annotations
import json, re, os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SIM_JSON = os.path.join(ROOT, "research", "t7_live_simulation", "EURUSD_t7_simulation.json")
M15_CSV = os.path.join(ROOT, "data", "historical_2026", "EURUSD_M15.csv")
D1_CSV = os.path.join(ROOT, "data", "historical_2026", "EURUSD_D1.csv")


def _parse_raw_response(raw: str) -> dict | None:
    """Strip optional ```json fences and parse JSON. Returns None if unparseable."""
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def load_results() -> list[dict[str, Any]]:
    with open(SIM_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data["results"]
    # Attach parsed raw_response inline for convenience
    for r in results:
        parsed = _parse_raw_response(r.get("raw_response", ""))
        r["_parsed"] = parsed
    return results


def decision_hist(results) -> Counter:
    return Counter(r["decision"] for r in results)


def no_trade_funnel(results) -> dict:
    """Break NO_TRADE into prescreen/ob_proximity/ai buckets."""
    out = Counter()
    for r in results:
        if r["decision"] != "NO_TRADE":
            continue
        reason = (r.get("no_trade_reason") or "")
        if reason.startswith("prescreen:"):
            out["prescreen"] += 1
        elif reason.startswith("ob_proximity"):
            out["ob_proximity"] += 1
        else:
            out["ai_no_trade"] += 1
    return dict(out)


def iso_week(candle_time: str) -> str:
    dt = datetime.fromisoformat(candle_time.replace("Z", "+00:00"))
    return dt.strftime("%G-W%V")

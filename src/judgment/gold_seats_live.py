"""Load unique gold APPLY seats into the live judgment package.

Imported from ``src.judgment.__init__``. Does **not** edit ``book_owner``.
Does **not** call decide / compose APPLY functions, so Chair place,
size, and manage stay the pre-existing graph. Persist pin is G-FULL
**0.00** (``gold_priors.GATE_COMPOSITE_WEIGHTS``). Missing Jev → no extra
PASS. Do not leftover-ship. Do not remint. Do not copy PR #77 persist 0.10.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import admission_place as _admission_place
from . import compose as _compose
from . import exec_gov_news as _exec_gov_news
from . import exec_gov_news_ifs as _exec_gov_news_ifs
from . import followthrough as _followthrough
from . import followthrough_ifs as _followthrough_ifs
from . import gold_entry as _gold_entry
from . import gold_entry_jev as _gold_entry_jev
from . import gold_exit_geometries as _gold_exit_geometries
from . import gold_priors as _gold_priors
from . import gold_sleeve_ifs as _gold_sleeve_ifs
from . import host_sites as _host_sites
from . import jev_client as _jev_client
from . import jev_questions as _jev_questions
from . import remaining_seats as _remaining_seats
from . import size_exit as _size_exit
from . import sleeve_ifs as _sleeve_ifs
from . import sleeve_jev as _sleeve_jev

UNIQUE_SEAT_MODULES: tuple[str, ...] = (
    "admission_place",
    "compose",
    "exec_gov_news",
    "exec_gov_news_ifs",
    "followthrough",
    "followthrough_ifs",
    "gold_entry",
    "gold_entry_jev",
    "gold_exit_geometries",
    "gold_priors",
    "gold_sleeve_ifs",
    "host_sites",
    "jev_client",
    "jev_questions",
    "remaining_seats",
    "size_exit",
    "sleeve_ifs",
    "sleeve_jev",
)

_LOADED = {
    "admission_place": _admission_place,
    "compose": _compose,
    "exec_gov_news": _exec_gov_news,
    "exec_gov_news_ifs": _exec_gov_news_ifs,
    "followthrough": _followthrough,
    "followthrough_ifs": _followthrough_ifs,
    "gold_entry": _gold_entry,
    "gold_entry_jev": _gold_entry_jev,
    "gold_exit_geometries": _gold_exit_geometries,
    "gold_priors": _gold_priors,
    "gold_sleeve_ifs": _gold_sleeve_ifs,
    "host_sites": _host_sites,
    "jev_client": _jev_client,
    "jev_questions": _jev_questions,
    "remaining_seats": _remaining_seats,
    "size_exit": _size_exit,
    "sleeve_ifs": _sleeve_ifs,
    "sleeve_jev": _sleeve_jev,
}

PERSIST = float(_gold_priors.GATE_COMPOSITE_WEIGHTS["persistence"])
PIN_WINDOW = str(_gold_priors.PIN_WINDOW)
GOLD_SEATS_PERSIST = PERSIST
GOLD_SEATS_PIN_WINDOW = PIN_WINDOW

if PERSIST != 0.0:
    raise RuntimeError(
        "gold seats refuse persist != 0.00 (would be PR #77 overlay); "
        f"got {PERSIST!r} pin={PIN_WINDOW!r}"
    )

GOLD_PIN = _gold_priors.assert_gold_pin()


def _sha12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _hit(name: str, mod: Any) -> dict[str, Any]:
    path = Path(getattr(mod, "__file__", "") or "")
    bytes_n = path.stat().st_size if path.is_file() else 0
    return {
        "module": name,
        "file": str(path),
        "bytes": bytes_n,
        "sha12": _sha12(path) if path.is_file() else "",
        "hits": 1,
    }


GOLD_SEATS_HITS: dict[str, dict[str, Any]] = {
    name: _hit(name, mod) for name, mod in _LOADED.items()
}
GOLD_SEATS_LOADED: tuple[str, ...] = tuple(GOLD_SEATS_HITS)
GOLD_SEATS_HIT_COUNT = sum(int(row["hits"]) for row in GOLD_SEATS_HITS.values())

STAMP_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "lab"
    / "a1"
    / "gold_seats_live.json"
)

_STAMP: dict[str, Any] = {
    "schema": "gtos.judgment.gold_seats_live.v0",
    "utc": datetime.now(timezone.utc).isoformat(),
    "pid": os.getpid(),
    "persist": PERSIST,
    "pin_window": PIN_WINDOW,
    "hit_count": GOLD_SEATS_HIT_COUNT,
    "loaded": list(GOLD_SEATS_LOADED),
    "hits": GOLD_SEATS_HITS,
    "gold_pin": GOLD_PIN,
    "book_owner_untouched": True,
    "decide_functions_not_called": True,
    "copied_077_persist_010": False,
}


def _write_stamp() -> None:
    try:
        STAMP_PATH.parent.mkdir(parents=True, exist_ok=True)
        STAMP_PATH.write_text(json.dumps(_STAMP, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        return


_write_stamp()

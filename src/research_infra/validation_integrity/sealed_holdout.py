"""Sealed go-forward holdout registry (North-Star A2 residual / L1b / N6 capstone).

The whole session's "sealed" confirmations used 2025-26 data that is PARTLY contaminated (it was the W7
selection surface — that is precisely the ~3x magnitude inflation the cycle-1 gauntlet quantified). The
ONLY genuinely-virgin confirmation surface is data AFTER a hash-stamped cutoff that NO selection has ever
touched. This module makes that a hard, enforced contract rather than a hope:

  - register_sealed_cutoff(cutoff_iso, reason) records a hash-stamped, append-only registry entry.
  - assert_selection_clean(dates_used_for_selection, cutoff_iso) RAISES if any selection/tuning touched a
    date strictly after the cutoff — the edge_factory (and any future miner) calls this before trusting a
    "sealed" confirmation, so a contaminated confirmation fails loud instead of silently inflating.
  - is_sealed(date_iso, cutoff_iso) classifies a bar as virgin-sealed vs selectable.

The live VPS forward is the canonical virgin sealed slice: every live trade after the cutoff is data no
backtest selection could have seen. This registry stamps the cutoff so future cycles confirm against it.
Pure stdlib.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Iterable, List, Optional


def _stamp(cutoff_iso: str, reason: str) -> str:
    return hashlib.sha256(f"{cutoff_iso}|{reason}".encode()).hexdigest()[:16]


def register_sealed_cutoff(cutoff_iso: str, reason: str, registry_path: str,
                           created_at_iso: Optional[str] = None) -> dict:
    """Append a hash-stamped sealed-cutoff entry. created_at_iso passed in (no wall-clock here)."""
    entry = {"cutoff": cutoff_iso, "reason": reason, "stamp": _stamp(cutoff_iso, reason),
             "created_at": created_at_iso, "schema": "gtos.sealed_holdout.v1"}
    reg: List[dict] = []
    if os.path.exists(registry_path):
        try:
            reg = json.load(open(registry_path))
        except Exception:
            reg = []
    reg.append(entry)
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    json.dump(reg, open(registry_path, "w"), indent=1)
    return entry


def is_sealed(date_iso: str, cutoff_iso: str) -> bool:
    """A bar is virgin-sealed iff its date is strictly after the cutoff."""
    return str(date_iso)[:10] > str(cutoff_iso)[:10]


def assert_selection_clean(dates_used_for_selection: Iterable[str], cutoff_iso: str) -> None:
    """Raise if ANY selection/tuning date is after the cutoff (i.e. it peeked at the sealed slice)."""
    leaked = sorted({str(d)[:10] for d in dates_used_for_selection if is_sealed(d, cutoff_iso)})
    if leaked:
        raise ValueError(
            f"SEALED-HOLDOUT VIOLATION: selection used {len(leaked)} date(s) after the sealed cutoff "
            f"{cutoff_iso} (e.g. {leaked[:5]}). A confirmation on data you selected on is not a "
            f"confirmation. Re-select only on dates <= {cutoff_iso}.")


def sealed_slice_summary(all_dates: Iterable[str], cutoff_iso: str) -> dict:
    ds = sorted(str(d)[:10] for d in all_dates)
    sealed = [d for d in ds if is_sealed(d, cutoff_iso)]
    return {"cutoff": cutoff_iso, "n_total": len(ds), "n_sealed_virgin": len(sealed),
            "n_selectable": len(ds) - len(sealed),
            "sealed_span": (sealed[0], sealed[-1]) if sealed else None}

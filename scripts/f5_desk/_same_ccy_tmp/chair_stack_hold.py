"""Mechanical HOLD overlay: USDJPY + occupied + same-direction EUR/GBP dsp.

Writer now owns ``f5_standing_hold_reason``. This overlay keeps the slate
honest between sits. Isolated EUR vs GBP opposite is not a stack. Isolated
re-entry after a symbol is flat is not a hold. Fade extras stay a separate
law. Provider is ``grok-chair``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.f5_desk import chair_card as card
from scripts.f5_desk import common, shim

PROVIDER = "grok-chair"
NS = common.NAMESPACE


def occupied_from_snapshot(positions: Iterable[dict], orders: Iterable[dict]) -> set[str]:
    out: set[str] = set()
    for row in list(positions) + list(orders):
        sym = card.norm_symbol(row.get("symbol"))
        if sym:
            out.add(sym)
    out.add("USDJPY")
    return out


def occupied_book_from_snapshot(positions: Iterable[dict], orders: Iterable[dict]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in positions:
        rows.append({
            "symbol": row.get("symbol"),
            "direction": row.get("side") or row.get("direction"),
            "family": row.get("sleeve") or row.get("comment") or "",
        })
    for row in orders:
        tname = str(row.get("type_name") or "")
        if row.get("side"):
            direction = row.get("side")
        elif "BUY" in tname:
            direction = "LONG"
        elif "SELL" in tname:
            direction = "SHORT"
        else:
            direction = None
        rows.append({
            "symbol": row.get("symbol"),
            "direction": direction,
            "family": row.get("sleeve") or row.get("comment") or "",
        })
    return rows


def hold_verdicts(
    slate: dict,
    occupied: Iterable[str],
    occupied_book: Iterable[dict] | None = None,
) -> list[dict[str, Any]]:
    occ = {card.norm_symbol(s) for s in occupied if card.norm_symbol(s)}
    occ.add("USDJPY")
    book = list(occupied_book or [])
    verdicts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cand in slate.get("candidates") or []:
        cid = str(cand.get("candidate_id") or "")
        if not cid or cid in seen:
            continue
        reason = card.standing_hold_reason(
            NS,
            cand.get("symbol"),
            occ,
            direction=cand.get("direction") or cand.get("side"),
            family=cand.get("sleeve") or cand.get("candidate_id"),
            occupied_book=book,
        )
        if not reason:
            sleeve = str(cand.get("sleeve") or "")
            sym = card.norm_symbol(cand.get("symbol"))
            other = {"EURUSD": "GBPUSD", "GBPUSD": "EURUSD"}.get(sym)
            if (
                sleeve in ("asian_fade", "asian_fade_widen")
                and other
                and other in occ
            ):
                reason = "same_currency_fade_stack_hold"
            else:
                continue
        seen.add(cid)
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "correlation",
            "why_code": reason,
            "confidence": 0.8,
        })
    return verdicts


def apply_holds(
    slate: dict,
    occupied: Iterable[str],
    *,
    state_dir: Path,
    flow_dir: Path,
    occupied_book: Iterable[dict] | None = None,
) -> dict[str, Any]:
    verdicts = hold_verdicts(slate, occupied, occupied_book=occupied_book)
    payload = {
        "schema": "gtos.f5.judge.verdict.v1",
        "slate_id": slate.get("slate_id"),
        "verdicts": verdicts,
        "manage": [],
        "notes": "chair: mechanical HOLD USDJPY + occupied + same-ccy dsp + fade extras",
    }
    if not verdicts:
        return {"applied": False, "verdicts": 0}
    res = shim.apply_verdict(
        payload,
        slate,
        state_dir=state_dir,
        flow_dir=flow_dir,
        provider=PROVIDER,
        latency_ms=0,
        raw_text_sha="grok-chair-stack-hold",
    )
    return {"applied": True, "verdicts": len(verdicts), "result": res, "ids": [
        v["candidate_id"] for v in verdicts
    ]}


def latest_slate(repo_root: Path) -> dict[str, Any] | None:
    state = common.judgment_state_dir(repo_root, NS)
    latest = common.read_json(state / "state" / "latest_slate.json", default=None)
    if not isinstance(latest, dict) or not latest.get("path"):
        return None
    slate = common.read_json(latest["path"], default=None)
    return slate if isinstance(slate, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chair_stack_hold")
    parser.add_argument("--repo-root", type=Path, default=_REPO)
    parser.add_argument("--snapshot", type=Path, default=None)
    args = parser.parse_args(argv)
    repo = Path(args.repo_root)
    slate = latest_slate(repo)
    if slate is None:
        print("chair_stack_hold: no latest slate", file=sys.stderr)
        return 2
    if args.snapshot:
        snap = json.loads(args.snapshot.read_text(encoding="utf-8"))
    else:
        from scripts.f5_desk import chair_mt5
        snap = chair_mt5.snapshot()
    positions = snap.get("positions") or []
    orders = snap.get("orders") or []
    occ = occupied_from_snapshot(positions, orders)
    book = occupied_book_from_snapshot(positions, orders)
    out = apply_holds(
        slate,
        occ,
        state_dir=common.judgment_state_dir(repo, NS),
        flow_dir=common.flow_dir(repo),
        occupied_book=book,
    )
    print(json.dumps({"occupied": sorted(occ), **{k: v for k, v in out.items() if k != "result"}}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

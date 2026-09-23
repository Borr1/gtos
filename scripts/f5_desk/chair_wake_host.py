"""Durable F5 chair wake host. Lives on the VPS. Does not judge.

Boot + 5-minute relaunch via GTOS_F5_CHAIR_WAKE. Inner loop 15 s. Lock file
makes extra starts inert. This process:

  * snapshots MT5 (retry INIT_FAIL; never restart books)
  * persists original stops and the 22:00 baseline
  * writes chair_wake.json when the chair should sit
  * occupancy overlay DISABLED 2026-08-30 (writer keep-ones; do not reapply chair_stack_hold)
  * never takes, never tightens, never calls a model

Judgment is the Grok Bot chair reading the wake card.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.f5_desk import chair_card as card
from scripts.f5_desk import chair_ledger, chair_observe, common

LOCK_NAME = "chair_wake.lock"
LOCK_STALE_S = 90.0
CYCLE_S = 15.0
DUP_S = 90.0


def _second_of_bar(now: datetime) -> float:
    return (now.minute % 15) * 60.0 + now.second + now.microsecond / 1e6


def session_open(now: datetime) -> bool:
    """First three minutes of London 07:00Z or NY 12:00Z."""
    now = now.astimezone(timezone.utc)
    for hour in (7, 12):
        start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        age = (now - start).total_seconds()
        if 0 <= age < 180:
            return True
    return False


def day_reset_window(now: datetime) -> bool:
    now = now.astimezone(timezone.utc)
    start = now.replace(hour=22, minute=0, second=0, microsecond=0)
    return 0 <= (now - start).total_seconds() < 180


def wake_fingerprint(reasons: list[str], book: dict[str, Any]) -> str:
    tickets = sorted(str(p.get("ticket")) for p in book.get("positions") or [])
    pending = sorted(str(o.get("ticket")) for o in book.get("pending") or [])
    return common.sha256_hex(common.canonical_json({
        "r": sorted(reasons), "t": tickets, "p": pending,
    }))[:16]


def decide_wake(
    *,
    now: datetime,
    book: dict[str, Any],
    last_sit_unix: float | None,
    last_ids: set[str],
    last_pending: set[str],
    last_tapes: dict[str, str],
    last_fp: str | None,
    last_wake_unix: float | None,
) -> tuple[list[str], str]:
    now_unix = now.timestamp()
    ids = {str(p.get("ticket")) for p in book.get("positions") or []}
    pending = {str(o.get("ticket")) for o in book.get("pending") or []}
    tapes = {
        str(p.get("ticket")): str(p.get("tape") or "")
        for p in book.get("positions") or []
    }
    unfroze = any(
        last_tapes.get(tid) == "frozen_or_stale" and tapes.get(tid) == "live"
        for tid in ids
    )
    reasons = card.wake_reasons(
        second_of_bar=_second_of_bar(now),
        seconds_since_sit=(now_unix - last_sit_unix) if last_sit_unix else 10_000,
        fast_family_live=bool(book.get("fast_family_live")),
        new_deal=bool(ids - last_ids),
        new_pending=bool(pending - last_pending),
        new_intent_on_flat=False,
        tape_unfroze=unfroze,
        day_reset=day_reset_window(now),
    )
    if session_open(now):
        reasons.append("session_open")
    fp = wake_fingerprint(reasons, book)
    if not reasons:
        return [], fp
    if last_fp == fp and last_wake_unix and (now_unix - last_wake_unix) < DUP_S:
        return [], fp
    return reasons, fp


def render_wake(book: dict[str, Any], reasons: list[str], now: datetime) -> str:
    lines = [
        f"WAKE {common.iso_utc(now)} reasons={','.join(reasons)}",
        f"login {book.get('login')} bal {book.get('balance')} eq {book.get('equity')}",
        f"day_net {book.get('day_net')} to_pass {book.get('to_pass')}",
        f"occupied {book.get('occupied')} fast_live {book.get('fast_family_live')}",
    ]
    for p in book.get("positions") or []:
        lines.append(
            "PATH {ticket} {symbol} {sleeve} {side} lots={lots} "
            "entry={entry} orig_sl={orig_sl} live_sl={live_sl} tp={tp} "
            "mark={mark} pnl={profit_usd} R_orig={r_orig} R_to_tp={r_to_tp} "
            "locked_r={locked_r} tape={tape} age={tick_age_s}".format(
                **{k: p.get(k) for k in (
                    "ticket", "symbol", "sleeve", "side", "lots", "entry",
                    "orig_sl", "live_sl", "tp", "mark", "profit_usd",
                    "r_orig", "r_to_tp", "locked_r", "tape", "tick_age_s",
                )}
            )
        )
    for o in book.get("pending") or []:
        lines.append(
            f"ORD {o.get('ticket')} {card.norm_symbol(o.get('symbol'))} "
            f"type={o.get('type')} price={o.get('price')}"
        )
    return "\n".join(lines) + "\n"


class WakeHost:
    def __init__(self, repo_root: Path):
        self.repo = Path(repo_root)
        self.state = chair_ledger.state_dir(self.repo)
        self.state.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.state / LOCK_NAME
        self.wake_path = self.state / chair_ledger.WAKE_NAME
        self.last_sit_path = self.state / chair_ledger.LAST_SIT_NAME
        self.health_path = self.state / chair_ledger.HEALTH_NAME
        self.orig_path = chair_ledger.orig_path(self.repo)
        self.base_path = chair_ledger.baseline_path(self.repo)
        self.last_ids: set[str] = set()
        self.last_pending: set[str] = set()
        self.last_tapes: dict[str, str] = {}
        self.last_fp: str | None = None
        self.last_wake_unix: float | None = None

    def acquire_lock(self) -> bool:
        now_ts = time.time()
        try:
            if self.lock_path.is_file():
                age = now_ts - self.lock_path.stat().st_mtime
                if age < LOCK_STALE_S:
                    return False
            common.write_json_atomic(self.lock_path, {
                "pid": os.getpid(), "started_at_utc": common.iso_utc(),
            })
            return True
        except Exception:
            return False

    def heartbeat(self) -> None:
        try:
            os.utime(self.lock_path, None)
        except Exception:
            common.write_json_atomic(self.lock_path, {
                "pid": os.getpid(), "hb_at_utc": common.iso_utc(),
            })

    def release_lock(self) -> None:
        try:
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass

    def _snapshot(self) -> dict[str, Any] | None:
        from scripts.f5_desk import chair_mt5
        last_err = None
        for _ in range(3):
            try:
                return chair_mt5.snapshot(orig_ledger=chair_ledger.load_orig_ledger(self.orig_path))
            except Exception as exc:  # INIT_FAIL etc — do not restart books
                last_err = exc
                time.sleep(2)
        common.write_json_atomic(self.health_path, {
            "ok": False, "error": str(last_err)[:200], "at_utc": common.iso_utc(),
        })
        return None

    def tick(self, now: datetime | None = None, snap: dict[str, Any] | None = None) -> dict[str, Any]:
        now = now or common.now_utc()
        if snap is None:
            snap = self._snapshot()
        if snap is None:
            return {"ok": False, "wake": False}
        chair_ledger.persist_positions(self.orig_path, snap.get("positions") or [])
        orig = chair_ledger.load_orig_ledger(self.orig_path)
        for ticket, sl in orig.items():
            try:
                chair_ledger.write_trade_record_orig(self.repo, int(ticket), sl)
            except (TypeError, ValueError):
                pass
        acct = snap.get("account") or {}
        try:
            bal = float(acct.get("balance"))
            baseline = chair_ledger.maybe_roll_baseline(self.base_path, bal, now)
        except (TypeError, ValueError):
            baseline = chair_ledger.load_baseline(self.base_path)
        book = chair_observe.book_card(
            acct,
            snap.get("positions") or [],
            baseline=baseline,
            ticks=snap.get("ticks") or {},
            orig_ledger=orig,
            now_unix=snap.get("now_unix") or now.timestamp(),
            orders=snap.get("orders") or [],
        )
        last_sit = common.read_json(self.last_sit_path, default={}) or {}
        last_sit_unix = None
        try:
            last_sit_unix = float((last_sit or {}).get("unix"))
        except (TypeError, ValueError, AttributeError):
            last_sit_unix = None
        reasons, fp = decide_wake(
            now=now,
            book=book,
            last_sit_unix=last_sit_unix,
            last_ids=self.last_ids,
            last_pending=self.last_pending,
            last_tapes=self.last_tapes,
            last_fp=self.last_fp,
            last_wake_unix=self.last_wake_unix,
        )
        self.last_ids = {str(p.get("ticket")) for p in book.get("positions") or []}
        self.last_pending = {str(o.get("ticket")) for o in book.get("pending") or []}
        self.last_tapes = {
            str(p.get("ticket")): str(p.get("tape") or "")
            for p in book.get("positions") or []
        }
        woke = False
        if reasons:
            text = render_wake(book, reasons, now)
            common.write_json_atomic(self.wake_path, {
                "at_utc": common.iso_utc(now),
                "unix": now.timestamp(),
                "reasons": reasons,
                "fingerprint": fp,
                "book": book,
                "proof": text,
            })
            proof = self.state / "chair_wake_proof.txt"
            try:
                proof.write_text(text, encoding="ascii", errors="replace")
            except Exception:
                pass
            self.last_fp = fp
            self.last_wake_unix = now.timestamp()
            woke = True
        # STOP-STACK-HOLD 2026-08-30: do not reapply chair_stack_hold occupancy overlay.
        # Writer already keep-ones. Overlay was a duplicate that fed UNPRICED occupancy cycles.
        # Wake host still snapshots, persists orig stops/baseline, and writes chair_wake.json.
        occupancy_cycles = 0
        common.write_json_atomic(self.health_path, {
            "ok": True,
            "at_utc": common.iso_utc(now),
            "wake": woke,
            "reasons": reasons,
            "occupied": book.get("occupied"),
            "positions": len(book.get("positions") or []),
            "pending": len(book.get("pending") or []),
            "day_net": book.get("day_net"),
            "stack_hold_overlay": "disabled",
            "occupancy_cycles": occupancy_cycles,
        })
        return {"ok": True, "wake": woke, "reasons": reasons, "book": book}

    def run(self, once: bool = False) -> int:
        if not self.acquire_lock():
            return 0
        try:
            while True:
                self.heartbeat()
                try:
                    self.tick()
                except Exception as exc:  # noqa: BLE001 — host must not die
                    common.write_json_atomic(self.health_path, {
                        "ok": False, "error": str(exc)[:200], "at_utc": common.iso_utc(),
                    })
                if once:
                    return 0
                time.sleep(CYCLE_S)
        finally:
            self.release_lock()


def mark_sat(repo_root: Path, now: datetime | None = None) -> None:
    now = now or common.now_utc()
    common.write_json_atomic(chair_ledger.state_dir(repo_root) / chair_ledger.LAST_SIT_NAME, {
        "at_utc": common.iso_utc(now),
        "unix": now.timestamp(),
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chair_wake_host")
    parser.add_argument("--repo-root", type=Path, default=_REPO)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    return WakeHost(args.repo_root).run(once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())

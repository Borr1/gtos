"""The shim — the ONLY writer of envelopes. The model writes judgment content;
this module owns every byte the book can consume.

From one parsed ``gtos.f5.judge.verdict.v1`` object + the slate it judged:

(a) flow sidecar entries in EXACTLY the format ``judgment_layer.judgment_flow``
    consumes (verified against src/components/ultimate_book/judgment_layer.py in
    this tree): files ``flow_<day>.json`` AND ``consume_<day>.json`` (both
    FLOW_SIDECAR_NAMES), entries keyed under EVERY alias id of the candidate
    (W7_BOOK::... engine id and LAUNCHER::... alias — book_owner queries both),
    with both timestamp key forms (``written_at_utc`` + ``ts``) and both verb
    key forms (``action`` + ``verdict``). HOLD ttl_s=3600; approve/abstain
    ttl_s=14400 (never 0, never 86400). Within 90 minutes of UTC midnight the
    same entries are dual-written into tomorrow's files so a standing word
    survives the date roll.
(b) ``manage_<day>.json`` per gtos.judgment.manage.v1 — close / tighten_stop
    rows, ONLY for tickets present in the judged slate's open-position block,
    pre-filtered to be risk-reducing where the slate knows stop+direction.
(c) ``judge_<day>.jsonl`` journal append (slate_id, provider, latency, verdict
    mix, raw response sha — never the prompt, never P&L).
(d) ``JUDGE-MEMORY.md`` append — one compact line per judged slate.

A verdict that fails validation writes NOTHING (seam fail-open) and increments
the breach counter file the tripwires read.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

_REPO_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_IMPORT))

from scripts.f5_desk import common

_log = logging.getLogger("f5_desk.shim")

VERDICT_SCHEMA = "gtos.f5.judge.verdict.v1"
MANAGE_SCHEMA = "gtos.judgment.manage.v1"

VERDICT_ENUM = ("approve", "hold", "abstain")
MANAGE_ACTIONS = ("close", "tighten_stop")

TTL_HOLD_S = 3600
TTL_APPROVE_S = 14400
TTL_MANAGE_DEFAULT_S = 1800
TTL_MANAGE_MIN_S = 60
TTL_MANAGE_MAX_S = 14400
MIDNIGHT_DUAL_WRITE_MIN = 90

_SNAKE = re.compile(r"[^a-z0-9_]+")


def _snake(text: Any) -> str:
    return _SNAKE.sub("_", str(text or "").strip().lower()).strip("_") or "unspecified"


def breach_counter_path(state_dir: Path) -> Path:
    return Path(state_dir) / "state" / "breach_counter.json"


def record_breach(state_dir: Path, reason: str, now: Optional[datetime] = None) -> int:
    """Increment the parser-breach counter the tripwires read. Never raises."""
    now = now or common.now_utc()
    return common.bump_day_counter(
        breach_counter_path(state_dir),
        day=common.utc_day(now),
        extra={"last_reason": str(reason)[:200], "last_at_utc": common.iso_utc(now)},
    )


# ---------------------------------------------------------------------------
# validation — strict envelope, tolerant content
# ---------------------------------------------------------------------------
def _slate_candidate_index(slate: dict) -> dict[str, dict]:
    """Every alias id -> its candidate view."""
    index: dict[str, dict] = {}
    for cand in slate.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        for cid in cand.get("alias_ids") or [cand.get("candidate_id")]:
            if cid:
                index[str(cid)] = cand
    return index


def _slate_positions(slate: dict) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for pos in slate.get("open_positions") or []:
        if isinstance(pos, dict):
            try:
                out[int(pos.get("ticket"))] = pos
            except (TypeError, ValueError):
                continue
    return out


def validate_verdict(raw: Any, slate: dict) -> tuple[Optional[dict], str, dict]:
    """(clean, reject_reason, drop_counts).

    ``clean`` is None on a WHOLE-verdict reject (breach); per-row defects are
    dropped/demoted and counted, never fatal. A HOLD with no named mechanism is
    demoted to abstain — the charter's law, enforced in code.
    """
    drops: dict[str, int] = {}

    def _drop(reason: str) -> None:
        drops[reason] = drops.get(reason, 0) + 1

    if not isinstance(raw, dict):
        return None, "not_a_mapping", drops
    if raw.get("schema") != VERDICT_SCHEMA:
        return None, "schema_mismatch", drops
    slate_id = str(raw.get("slate_id") or "")
    want = str(slate.get("slate_id") or "")
    if want and slate_id != want:
        return None, "slate_id_mismatch", drops
    verdicts_raw = raw.get("verdicts")
    manage_raw = raw.get("manage")
    if verdicts_raw is None:
        verdicts_raw = []
    if manage_raw is None:
        manage_raw = []
    if not isinstance(verdicts_raw, list) or not isinstance(manage_raw, list):
        return None, "verdicts_or_manage_not_list", drops

    index = _slate_candidate_index(slate)
    positions = _slate_positions(slate)

    clean_verdicts: list[dict] = []
    seen_candidates: set[str] = set()
    for row in verdicts_raw:
        if not isinstance(row, dict):
            _drop("verdict_row_not_mapping")
            continue
        cid = str(row.get("candidate_id") or "").strip()
        if not cid:
            _drop("verdict_missing_candidate_id")
            continue
        cand = index.get(cid)
        if cand is None:
            _drop("verdict_unknown_candidate")
            continue
        verdict = str(row.get("verdict") or "").strip().lower()
        if verdict not in VERDICT_ENUM:
            _drop("verdict_outside_enum")
            continue
        mechanism = str(row.get("mechanism") or "").strip()
        if verdict == "hold" and not mechanism:
            verdict = "abstain"
            _drop("hold_demoted_no_mechanism")
        try:
            confidence = float(row.get("confidence"))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = min(1.0, max(0.0, confidence))
        canonical = str(cand.get("candidate_id") or cid)
        if canonical in seen_candidates:
            _drop("verdict_duplicate_candidate")
            continue
        seen_candidates.add(canonical)
        gated = {
            "candidate_id": canonical,
            "alias_ids": list(cand.get("alias_ids") or [canonical]),
            "verdict": verdict,
            "mechanism": mechanism,
            "why_code": _snake(row.get("why_code")),
            "confidence": confidence,
        }
        try:
            from scripts.f5_desk.inbox_gates import gate_candidate_verdict
            gated, demote = gate_candidate_verdict(gated, cand)
            if demote:
                _drop(demote)
        except Exception:
            pass
        clean_verdicts.append(gated)

    clean_manage: list[dict] = []
    seen_manage: set[tuple[int, str]] = set()
    for row in manage_raw:
        if not isinstance(row, dict):
            _drop("manage_row_not_mapping")
            continue
        try:
            ticket = int(row.get("ticket"))
        except (TypeError, ValueError):
            _drop("manage_bad_ticket")
            continue
        pos = positions.get(ticket)
        if pos is None:
            _drop("manage_unknown_ticket")
            continue
        action = str(row.get("action") or "").strip().lower()
        if action not in MANAGE_ACTIONS:
            _drop("manage_action_outside_enum")
            continue
        new_stop: Optional[float] = None
        if action == "tighten_stop":
            try:
                new_stop = float(row.get("new_stop"))
            except (TypeError, ValueError):
                _drop("manage_tighten_missing_new_stop")
                continue
            direction = str(pos.get("direction") or "").upper()
            current = pos.get("stop_now")
            try:
                current_f = float(current)
            except (TypeError, ValueError):
                current_f = None
            if direction not in ("LONG", "SHORT"):
                _drop("manage_direction_unknown")
                continue
            if current_f is not None:
                reducing = new_stop > current_f if direction == "LONG" else new_stop < current_f
                if not reducing:
                    _drop("manage_tighten_not_risk_reducing")
                    continue
            # "not beyond current price" is enforced by the consumer against the
            # live quote; the slate carries no quote, deliberately.
        if (ticket, action) in seen_manage:
            _drop("manage_duplicate_row")
            continue
        seen_manage.add((ticket, action))
        raw_ttl = row.get("ttl_s")
        if raw_ttl is None:
            ttl_s = TTL_MANAGE_DEFAULT_S
        else:
            try:
                ttl_s = int(float(raw_ttl))
            except (TypeError, ValueError):
                ttl_s = TTL_MANAGE_DEFAULT_S
        ttl_s = int(min(TTL_MANAGE_MAX_S, max(TTL_MANAGE_MIN_S, ttl_s)))
        clean_manage.append({
            "ticket": ticket,
            "action": action,
            "new_stop": new_stop,
            "mechanism": str(row.get("mechanism") or "").strip() or "unspecified",
            "why_code": _snake(row.get("why_code")),
            "ttl_s": ttl_s,
        })

    clean = {
        "slate_id": slate_id or want,
        "verdicts": clean_verdicts,
        "manage": clean_manage,
        "notes": str(raw.get("notes") or "")[:2000],
    }
    return clean, "", drops


# ---------------------------------------------------------------------------
# (a) flow sidecars
# ---------------------------------------------------------------------------
_FLOW_BY_VERDICT = {
    "approve": ("APPROVE", TTL_APPROVE_S),
    "hold": ("HOLD", TTL_HOLD_S),
    "abstain": ("PASS", TTL_APPROVE_S),
}


def _sidecar_days(now: datetime) -> list[str]:
    days = [now.date().isoformat()]
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    if (next_midnight - now) <= timedelta(minutes=MIDNIGHT_DUAL_WRITE_MIN):
        days.append((now + timedelta(days=1)).date().isoformat())
    return days


def _merge_sidecar(path: Path, entries: dict[str, dict], now: datetime) -> int:
    """Merge entries into one sidecar file; prune entries stale past ttl+1h.
    A corrupt existing file is set aside (never fed back to the consumer)."""
    existing = common.read_json(path, default=None)
    if existing is None and path.is_file():
        try:
            aside = path.with_name(path.name + f".corrupt-{now.strftime('%Y%m%dT%H%M%SZ')}")
            path.replace(aside)
            _log.warning("shim: corrupt sidecar %s set aside as %s", path, aside.name)
        except Exception:
            pass
        existing = {}
    if not isinstance(existing, dict):
        existing = {}
    merged = dict(existing)
    merged.update(entries)
    pruned: dict[str, dict] = {}
    for cid, entry in merged.items():
        if not isinstance(entry, dict):
            continue
        written = common.parse_utc(entry.get("written_at_utc") or entry.get("ts"))
        try:
            ttl = float(entry.get("ttl_s"))
        except (TypeError, ValueError):
            ttl = TTL_APPROVE_S
        if written is not None and (now - written).total_seconds() > ttl + 3600.0:
            continue
        pruned[cid] = entry
    common.write_json_atomic(path, pruned)
    return len(entries)


def write_flow(clean: dict, slate: dict, flow_dir: Path,
               now: Optional[datetime] = None) -> dict:
    """Write flow sidecar entries for every judged candidate under every alias id.
    Returns {"entries": n, "files": [...]}. Never raises."""
    now = now or common.now_utc()
    entries: dict[str, dict] = {}
    written_iso = common.iso_utc(now)
    for row in clean.get("verdicts") or []:
        action, ttl = _FLOW_BY_VERDICT.get(row["verdict"], ("PASS", TTL_APPROVE_S))
        entry = {
            "action": action,
            "verdict": row["verdict"],
            "role": "JUDGMENT",
            "why_code": row["why_code"],
            "mechanism": row["mechanism"],
            "confidence": row["confidence"],
            "written_at_utc": written_iso,
            "ts": written_iso,
            "ttl_s": ttl,
            "namespace": str(slate.get("namespace") or common.NAMESPACE),
            "slate_id": clean.get("slate_id"),
        }
        for cid in row.get("alias_ids") or [row["candidate_id"]]:
            entries[str(cid)] = entry
    files: list[str] = []
    if entries:
        flow_dir = Path(flow_dir)
        for day in _sidecar_days(now):
            for stem in ("flow", "consume"):
                path = flow_dir / f"{stem}_{day}.json"
                try:
                    _merge_sidecar(path, entries, now)
                    files.append(path.name)
                except Exception as exc:
                    _log.warning("shim: sidecar write failed %s (%r)", path, exc)
    return {"entries": len(entries), "files": files}


# ---------------------------------------------------------------------------
# (b) manage file — gtos.judgment.manage.v1
# ---------------------------------------------------------------------------
def manage_path(state_dir: Path, day: str) -> Path:
    return Path(state_dir) / f"manage_{day}.json"


def write_manage(clean: dict, slate: dict, state_dir: Path,
                 now: Optional[datetime] = None,
                 ttl_s: int = TTL_MANAGE_DEFAULT_S) -> dict:
    """Merge validated manage rows into today's manage_<day>.json. Rows are
    keyed (ticket, action): a newer word replaces the older; expired rows are
    dropped at rewrite. Returns {"rows": n, "path": str|None}. Never raises."""
    now = now or common.now_utc()
    rows_in = clean.get("manage") or []
    if not rows_in:
        # Still prune: an expired row left in the day file re-emits one 'expired'
        # rejection per BOOK RESTART (the consumer's terminal memo is process-scoped
        # — measured on ticket 178427810, 2026-08-25). Rewriting the file without it
        # ends that; a missing/empty file is a no-op.
        day = common.utc_day(now)
        path = manage_path(state_dir, day)
        doc = common.read_json(path, default=None)
        if (isinstance(doc, dict) and doc.get("schema") == MANAGE_SCHEMA
                and isinstance(doc.get("rows"), list)):
            kept = []
            for row in doc["rows"]:
                if not isinstance(row, dict):
                    continue
                written = common.parse_utc(row.get("written_at_utc"))
                try:
                    row_ttl = float(row.get("ttl_s"))
                except (TypeError, ValueError):
                    row_ttl = 0.0
                if written is not None and (now - written).total_seconds() <= row_ttl:
                    kept.append(row)
            if len(kept) != len(doc["rows"]):
                common.write_json_atomic(path, {"schema": MANAGE_SCHEMA, "rows": kept})
        return {"rows": 0, "path": None}
    ttl = int(min(TTL_MANAGE_MAX_S, max(TTL_MANAGE_MIN_S, int(ttl_s))))
    day = common.utc_day(now)
    path = manage_path(state_dir, day)
    doc = common.read_json(path, default=None)
    existing_rows = []
    if isinstance(doc, dict) and doc.get("schema") == MANAGE_SCHEMA and isinstance(doc.get("rows"), list):
        existing_rows = [r for r in doc["rows"] if isinstance(r, dict)]
    merged: dict[tuple[int, str], dict] = {}
    for row in existing_rows:
        try:
            key = (int(row.get("ticket")), str(row.get("action")))
        except (TypeError, ValueError):
            continue
        written = common.parse_utc(row.get("written_at_utc"))
        try:
            row_ttl = float(row.get("ttl_s"))
        except (TypeError, ValueError):
            row_ttl = 0.0
        if written is None or (now - written).total_seconds() > row_ttl:
            continue  # expired or unordered — gone at rewrite
        merged[key] = row
    written_iso = common.iso_utc(now)
    for row in rows_in:
        row_ttl = row.get("ttl_s")
        try:
            use_ttl = int(row_ttl) if row_ttl is not None else int(ttl)
        except (TypeError, ValueError):
            use_ttl = int(ttl)
        use_ttl = int(min(TTL_MANAGE_MAX_S, max(TTL_MANAGE_MIN_S, use_ttl)))
        out = {
            "ticket": row["ticket"],
            "action": row["action"],
            "mechanism": row["mechanism"],
            "why_code": row["why_code"],
            "written_at_utc": written_iso,
            "ttl_s": use_ttl,
        }
        if row["action"] == "tighten_stop":
            out["new_stop"] = float(row["new_stop"])
        merged[(row["ticket"], row["action"])] = out
    payload = {
        "schema": MANAGE_SCHEMA,
        "rows": sorted(merged.values(), key=lambda r: (r.get("ticket") or 0, r.get("action") or "")),
    }
    ok = common.write_json_atomic(path, payload)
    return {"rows": len(rows_in), "path": str(path) if ok else None}


# ---------------------------------------------------------------------------
# (c) journal + (d) memory
# ---------------------------------------------------------------------------
def journal_path(state_dir: Path, day: str) -> Path:
    return Path(state_dir) / f"judge_{day}.jsonl"


def memory_path(state_dir: Path) -> Path:
    return Path(state_dir) / "JUDGE-MEMORY.md"


def append_journal(state_dir: Path, record: dict, now: Optional[datetime] = None) -> bool:
    now = now or common.now_utc()
    return common.append_jsonl(journal_path(state_dir, common.utc_day(now)), record)


def _verdict_mix(clean: dict) -> str:
    counts = {"approve": 0, "hold": 0, "abstain": 0}
    for row in clean.get("verdicts") or []:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return f"a{counts['approve']}/h{counts['hold']}/x{counts['abstain']}"


def append_memory_line(state_dir: Path, clean: dict, provider: Optional[str],
                       now: Optional[datetime] = None) -> bool:
    now = now or common.now_utc()
    holds = [r for r in clean.get("verdicts") or [] if r["verdict"] == "hold"]
    hold_note = ""
    if holds:
        hold_note = " holds=" + ",".join(
            f"{r['candidate_id'].split('::')[2] if r['candidate_id'].count('::') >= 2 else r['candidate_id']}"
            f":{r['why_code']}" for r in holds[:4]
        )
    manage_note = ""
    if clean.get("manage"):
        manage_note = " manage=" + ",".join(
            f"{r['ticket']}:{r['action']}" for r in clean["manage"][:4]
        )
    notes = str(clean.get("notes") or "").strip().replace("\n", " ")[:160]
    line = (
        f"- {common.iso_utc(now)} slate={clean.get('slate_id')} provider={provider or '?'} "
        f"verdicts={_verdict_mix(clean)}{hold_note}{manage_note}"
        + (f" note={notes}" if notes else "")
        + "\n"
    )
    return common.append_text(memory_path(state_dir), line)


# ---------------------------------------------------------------------------
# orchestration — one verdict in, all four writes out (or none)
# ---------------------------------------------------------------------------
def apply_verdict(raw: Any, slate: dict, *, state_dir: Path, flow_dir: Path,
                  provider: Optional[str] = None, latency_ms: Any = None,
                  raw_text_sha: Optional[str] = None,
                  now: Optional[datetime] = None) -> dict:
    """Validate then write (a)-(d). A rejected verdict writes NOTHING except the
    breach counter + one journal reject line. Never raises."""
    now = now or common.now_utc()
    state_dir = Path(state_dir)
    flow_dir = Path(flow_dir)
    try:
        clean, reject, drops = validate_verdict(raw, slate)
        if clean is None:
            breaches = record_breach(state_dir, reject, now)
            append_journal(state_dir, {
                "kind": "verdict_rejected",
                "at_utc": common.iso_utc(now),
                "slate_id": slate.get("slate_id"),
                "provider": provider,
                "reject_reason": reject,
                "breach_count_today": breaches,
                "raw_response_sha": raw_text_sha,
            }, now)
            _log.warning("shim: verdict REJECTED (%s) — nothing written (breach #%d)",
                         reject, breaches)
            return {"applied": False, "reject_reason": reject, "drops": drops}
        flow_summary = write_flow(clean, slate, flow_dir, now)
        manage_summary = write_manage(clean, slate, state_dir, now)
        append_journal(state_dir, {
            "kind": "slate_judged",
            "at_utc": common.iso_utc(now),
            "slate_id": clean.get("slate_id"),
            "provider": provider,
            "latency_ms": latency_ms,
            "verdict_mix": _verdict_mix(clean),
            "verdicts": clean.get("verdicts"),
            "manage": clean.get("manage"),
            "drops": drops,
            "flow": flow_summary,
            "manage_file": manage_summary,
            "raw_response_sha": raw_text_sha,
        }, now)
        append_memory_line(state_dir, clean, provider, now)
        return {
            "applied": True,
            "reject_reason": "",
            "drops": drops,
            "flow": flow_summary,
            "manage": manage_summary,
            "verdicts": len(clean.get("verdicts") or []),
        }
    except Exception as exc:
        # Fail open: a shim defect must never take the daemon down mid-cycle.
        _log.warning("shim: apply_verdict failed (%r) — nothing written", exc)
        try:
            record_breach(state_dir, f"shim_error_{type(exc).__name__}", now)
        except Exception:
            pass
        return {"applied": False, "reject_reason": f"shim_error_{type(exc).__name__}", "drops": {}}

"""Judgment layer — machine rows, deterministic reducer, one-lookup consume seam.

Contract: docs/audits/fable-20260816/JUDGMENT-LOCK.md §4/§6 (audit tree). Three parts,
one home:

1. **Rows.** Judgment bots write per-role JSONL rows all day. The envelope is fixed
   (`ROW_ENVELOPE_FIELDS`); ``join_key`` is the engine's ``candidate_id`` verbatim.
   **No P&L field exists in the schema. Deliberately.**
2. **Reducer.** Plain Python, no model. Folds the latest ELIGIBLE row per
   (join_key, role) into one daily verdict file
   ``judgment/verdicts_<YYYY-MM-DD>.json`` mapping
   ``candidate_id -> {verdict, role, why_code, written_at_utc, ttl_s, ...}``.
   Only Cost-role rows with verdict=true on a code-refused candidate produce RESCUE.
   VETO rows are recorded but NOT consumed yet (log-only downstream).
3. **Lookup.** ``judgment_verdict(candidate_id, now_utc) -> RESCUE | VETO | ABSENT``.
   Stale (past TTL), missing file, unreadable file, wrong book, malformed entry —
   every failure is ABSENT plus one log line, never an exception. ABSENT means
   code-only behavior; a dead bot changes nothing.

4. **LIVE fire-path consume (2026-08-22).** ``judgment_flow(...) -> APPROVE | SIZE | HOLD | PASS``.
   Reads the latest eligible hedge-fund JUDGMENT row (sidecar or judgment jsonl).
   No row / unreadable / stale / abstain → PASS (existing $75 fire continues).
   HOLD only when a real judged row says veto. SIZE annotates; never applies size_mult.
   Machinery COST/RISK/ALIGNMENT/STATE rows are not a fire veto. Never calls place().

Fold semantics, pinned here because the two obvious readings differ: rows fold
latest-per-(join_key, ROLE), not latest-per-join_key across roles. Roles are
independent judges (the lock forbids in-flight cross-talk), so a later State or
Geometry row must not displace the Cost role's standing word on a candidate. RESCUE
and VETO cannot collide on one candidate: RESCUE requires a code-refused row and
VETO a code-accepted one.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date as _date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

_log = logging.getLogger(__name__)

SCHEMA_VERSION = "gtos.judgment.row.v1"

ROLE_STATE = "STATE"
ROLE_GEOMETRY = "GEOMETRY"
ROLE_COST = "COST"
ROLE_RISK = "RISK"
ROLE_ALIGNMENT = "ALIGNMENT"
ROLES = (ROLE_STATE, ROLE_GEOMETRY, ROLE_COST, ROLE_RISK, ROLE_ALIGNMENT)

VERDICT_TRUE = "true"
VERDICT_FALSE = "false"
VERDICT_UNJUDGEABLE = "UNJUDGEABLE"
ROW_VERDICTS = (VERDICT_TRUE, VERDICT_FALSE, VERDICT_UNJUDGEABLE)

VERDICT_RESCUE = "RESCUE"
VERDICT_VETO = "VETO"
VERDICT_ABSENT = "ABSENT"

CODE_ACTION_ALLOW = "allow"
CODE_ACTION_BLOCK = "block"

VERDICT_DIR_NAME = "judgment"
_MS_PER_S = 1000.0

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _consume_bounds(now: Optional[datetime], namespace: Any) -> dict[str, float | None]:
    """Latency budget, fallback ttl, and scan age for this consume day. One post."""
    day = ""
    if isinstance(now, datetime):
        day = now.astimezone(timezone.utc).date().isoformat()
    key = ("consume", str(namespace or ""), day)
    if key in _HOP:
        return dict(_HOP[key])
    payload = {
        "namespace": None if namespace is None else str(namespace),
        "consume_day": day,
    }
    questions = {
        "latency_budget_s": (
            "The score you return is the latency budget in seconds for a judgment row on this day. "
            "An empty score leaves that budget unset. Do not send."
        ),
        "consume_ttl_s": (
            "The score you return is how many seconds a judgment row with no ttl of its own stays current. "
            "An empty score leaves that ttl unset. Do not send."
        ),
        "row_scan_max_age_s": (
            "The score you return is the oldest row file, in seconds, this consume will open. "
            "An empty score leaves that age unset. Do not send."
        ),
    }
    out = {qid: None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[qid] = _finite(
                    ask(
                        payload,
                        question_id=qid,
                        instructions=text,
                        anchors=None,
                    )
                )
            except Exception:
                out[qid] = None
    _HOP[key] = dict(out)
    return out

ROW_ENVELOPE_FIELDS = (
    "schema_version",
    "role",
    "model_id",
    "prompt_sha",
    "written_at_utc",
    "latency_ms",
    "namespace",
    "symbol",
    "sleeve",
    "join_key",
    "code_verdict",
    "verdict",
    "why_code",
    "why_text",
    "evidence",
    "would_flip",
    "assumes",
    "disagree",
    "input_packet_sha",
)


# ---------------------------------------------------------------------------
# shared parsing
# ---------------------------------------------------------------------------
def parse_utc(value: Any) -> Optional[datetime]:
    """ISO-8601 (or datetime) to aware UTC. None on anything unparseable."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_verdict(value: Any) -> Optional[str]:
    """Row verdict to its canonical enum value; None when outside the enum.

    ``UNJUDGEABLE(missing_fact=...)`` normalizes to ``UNJUDGEABLE`` — the missing
    fact stays in why_text/would_flip.
    """
    if value is True:
        return VERDICT_TRUE
    if value is False:
        return VERDICT_FALSE
    text = str(value or "").strip()
    if not text:
        return None
    if text.lower() == VERDICT_TRUE:
        return VERDICT_TRUE
    if text.lower() == VERDICT_FALSE:
        return VERDICT_FALSE
    if text.upper().startswith(VERDICT_UNJUDGEABLE):
        return VERDICT_UNJUDGEABLE
    return None


def code_action(code_verdict: Any) -> Optional[str]:
    """Extract the code's own action ('allow' | 'block') from a row's code_verdict.

    code_verdict is "action + fatal_reasons as-logged + packet_hash_sha256 when
    present" — either a mapping with an ``action`` key or a string leading with the
    action token. Unparseable action means the row can prove neither a refusal nor
    an accept, so it can map to neither RESCUE nor VETO.
    """
    if isinstance(code_verdict, Mapping):
        raw = str(code_verdict.get("action") or "")
    else:
        raw = str(code_verdict or "")
        if "action=" in raw:
            raw = raw.split("action=", 1)[1]
    raw = raw.strip().lower()
    if not raw:
        return None
    token = raw.split(None, 1)[0]
    for sep in (":", ";", ","):
        token = token.split(sep, 1)[0]
    if token.startswith(CODE_ACTION_BLOCK):
        return CODE_ACTION_BLOCK
    if token.startswith(CODE_ACTION_ALLOW):
        return CODE_ACTION_ALLOW
    return None


# ---------------------------------------------------------------------------
# 1. rows
# ---------------------------------------------------------------------------
def build_judgment_row(
    *,
    role: str,
    model_id: str,
    prompt_sha: str,
    written_at_utc: Any,
    latency_ms: Any,
    namespace: str,
    symbol: str,
    sleeve: Any,
    join_key: str,
    code_verdict: Any,
    verdict: Any,
    why_code: str,
    why_text: str,
    evidence: Optional[Mapping[str, Any]] = None,
    would_flip: str = "",
    assumes: str = "",
    input_packet_sha: str = "",
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    """One machine row. Strict on the writer side; the reducer is the tolerant side.

    ``disagree`` is derived (verdict contradicts code_verdict), never author-set.
    """
    role_canon = str(role or "").strip().upper()
    if role_canon not in ROLES:
        raise ValueError(f"unknown judgment role: {role!r} (roles: {ROLES})")
    verdict_canon = normalize_verdict(verdict)
    if verdict_canon is None:
        raise ValueError(f"verdict outside enum true|false|UNJUDGEABLE: {verdict!r}")
    if not str(join_key or "").strip():
        raise ValueError("join_key is required (candidate_id verbatim)")
    written = parse_utc(written_at_utc)
    if written is None:
        raise ValueError(f"written_at_utc unparseable: {written_at_utc!r}")
    latency = None
    if latency_ms not in (None, ""):
        latency = float(latency_ms)
    action = code_action(code_verdict)
    disagree = (
        (action == CODE_ACTION_ALLOW and verdict_canon == VERDICT_FALSE)
        or (action == CODE_ACTION_BLOCK and verdict_canon == VERDICT_TRUE)
    )
    return {
        "schema_version": str(schema_version),
        "role": role_canon,
        "model_id": str(model_id or ""),
        "prompt_sha": str(prompt_sha or ""),
        "written_at_utc": written.isoformat(),
        "latency_ms": latency,
        "namespace": str(namespace or ""),
        "symbol": str(symbol or ""),
        "sleeve": (str(sleeve) if sleeve not in (None, "") else None),
        "join_key": str(join_key),
        "code_verdict": code_verdict,
        "verdict": verdict_canon,
        "why_code": str(why_code or ""),
        "why_text": str(why_text or ""),
        "evidence": dict(evidence or {}),
        "would_flip": str(would_flip or ""),
        "assumes": str(assumes or ""),
        "disagree": bool(disagree),
        "input_packet_sha": str(input_packet_sha or ""),
    }


def append_judgment_row(path: Any, row: Mapping[str, Any]) -> None:
    """Append one row to a per-role JSONL file (single write + fsync)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(row), sort_keys=True, separators=(",", ":"), default=str)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


# ---------------------------------------------------------------------------
# 2. reducer (plain Python, no model)
# ---------------------------------------------------------------------------
def verdict_filename(day: Any) -> str:
    if isinstance(day, datetime):
        day = day.astimezone(timezone.utc).date()
    if isinstance(day, _date):
        return f"verdicts_{day.isoformat()}.json"
    return f"verdicts_{str(day).strip()}.json"


def _iter_rows(row_paths: Iterable[Any]) -> Iterable[tuple[Optional[dict], str]]:
    """Yield (row_dict | None, source) per JSONL line. None marks a parse failure."""
    for raw_path in row_paths:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            yield None, f"{path}:unreadable"
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                yield None, f"{path}:{lineno}"
                continue
            if not isinstance(row, dict):
                yield None, f"{path}:{lineno}"
                continue
            yield row, f"{path}:{lineno}"


def row_ineligibility(row: Mapping[str, Any], *, latency_budget_s: float | None) -> Optional[str]:
    """The task-locked eligibility rule. None == eligible.

    Eligible iff: join_key present, latency_ms inside the returned budget, why_code non-empty,
    verdict in the enum. A row whose written_at_utc cannot be parsed is also
    ineligible — "latest" needs an order and the TTL law needs a timestamp, so an
    unordered row could never be consumed anyway.
    """
    if not str(row.get("join_key") or "").strip():
        return "missing_join_key"
    latency = row.get("latency_ms")
    try:
        latency_f = float(latency)
    except (TypeError, ValueError):
        return "latency_ms_unparseable"
    budget = _finite(latency_budget_s)
    if budget is not None and latency_f > budget * _MS_PER_S:
        return "latency_over_budget"
    if not str(row.get("why_code") or "").strip():
        return "missing_why_code"
    if normalize_verdict(row.get("verdict")) is None:
        return "verdict_outside_enum"
    if parse_utc(row.get("written_at_utc")) is None:
        return "written_at_unparseable"
    return None


def reduce_verdicts(
    row_paths: Iterable[Any],
    *,
    out_dir: Any,
    day: Any,
    latency_budget_s: float | None = None,
    ttl_s: float | None = None,
    write: bool = True,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Fold role JSONL rows into the one daily verdict mapping. Deterministic.

    Returns ``(verdicts, stats)`` and (when ``write``) atomically writes
    ``<out_dir>/verdicts_<day>.json`` whose top level IS the mapping
    ``candidate_id -> {verdict, role, why_code, written_at_utc, ttl_s, namespace,
    symbol, sleeve}``.

    RESCUE: the COST role's latest eligible row has verdict true on a code-refused
    (action=block) candidate. VETO: the latest eligible row (any role) with verdict
    false on a code-accepted (action=allow) candidate — recorded, consumed by
    nothing yet. UNJUDGEABLE folds like any latest row and maps to no entry: a
    role's current word "cannot judge" displaces its own earlier verdict.
    """
    bounds = _consume_bounds(datetime.now(timezone.utc), None)
    if latency_budget_s is None:
        latency_budget_s = bounds.get("latency_budget_s")
    if ttl_s is None:
        ttl_s = bounds.get("consume_ttl_s")
    stats: dict[str, Any] = {
        "rows_total": 0,
        "rows_parse_failed": 0,
        "rows_ineligible": {},
        "rows_eligible": 0,
    }
    # (join_key, role) -> (written_at, seq, row); later (written_at, seq) wins.
    latest: dict[tuple[str, str], tuple[datetime, int, dict]] = {}
    seq = 0
    for row, _source in _iter_rows(row_paths):
        seq += 1
        stats["rows_total"] += 1
        if row is None:
            stats["rows_parse_failed"] += 1
            continue
        reason = row_ineligibility(row, latency_budget_s=latency_budget_s)
        if reason is not None:
            stats["rows_ineligible"][reason] = stats["rows_ineligible"].get(reason, 0) + 1
            continue
        stats["rows_eligible"] += 1
        join_key = str(row.get("join_key")).strip()
        role = str(row.get("role") or "").strip().upper()
        written = parse_utc(row.get("written_at_utc"))
        key = (join_key, role)
        held = latest.get(key)
        if held is None or (written, seq) >= (held[0], held[1]):
            latest[key] = (written, seq, row)

    verdicts: dict[str, dict[str, Any]] = {}
    by_candidate: dict[str, list[tuple[datetime, int, str, dict]]] = {}
    for (join_key, role), (written, order, row) in latest.items():
        by_candidate.setdefault(join_key, []).append((written, order, role, row))

    def _entry(verdict: str, role: str, written: datetime, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "verdict": verdict,
            "role": role,
            "why_code": str(row.get("why_code") or ""),
            "written_at_utc": written.isoformat(),
            "ttl_s": _finite(ttl_s),
            "namespace": str(row.get("namespace") or ""),
            "symbol": str(row.get("symbol") or ""),
            "sleeve": row.get("sleeve"),
        }

    for join_key, held_rows in by_candidate.items():
        rescue = None
        for written, order, role, row in held_rows:
            if role != ROLE_COST:
                continue
            if normalize_verdict(row.get("verdict")) != VERDICT_TRUE:
                continue
            if code_action(row.get("code_verdict")) != CODE_ACTION_BLOCK:
                continue
            rescue = _entry(VERDICT_RESCUE, role, written, row)
        if rescue is not None:
            verdicts[join_key] = rescue
            continue
        veto = None
        veto_order: tuple[datetime, int] | None = None
        for written, order, role, row in held_rows:
            if normalize_verdict(row.get("verdict")) != VERDICT_FALSE:
                continue
            if code_action(row.get("code_verdict")) != CODE_ACTION_ALLOW:
                continue
            if veto_order is None or (written, order) >= veto_order:
                veto = _entry(VERDICT_VETO, role, written, row)
                veto_order = (written, order)
        if veto is not None:
            verdicts[join_key] = veto

    stats["candidates"] = len(by_candidate)
    stats["rescues"] = sum(1 for e in verdicts.values() if e["verdict"] == VERDICT_RESCUE)
    stats["vetoes"] = sum(1 for e in verdicts.values() if e["verdict"] == VERDICT_VETO)

    if write:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / verdict_filename(day)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(
            json.dumps(verdicts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(tmp, target)
        stats["out_path"] = str(target)
    return verdicts, stats


# ---------------------------------------------------------------------------
# 3. the consume seam — one lookup, one enum, TTL, fail-to-absent
# ---------------------------------------------------------------------------
def judgment_verdict(
    candidate_id: Any,
    now_utc: Any,
    *,
    verdict_dir: Any = None,
    namespace: Any = None,
    default_ttl_s: float | None = None,
) -> str:
    """``RESCUE | VETO | ABSENT`` for one candidate at one instant. NEVER raises.

    ABSENT == code-only behavior. Every failure path — missing file, unreadable
    file, malformed entry, wrong book (``namespace`` mismatch), unparseable
    written_at, stale past TTL — returns ABSENT and logs exactly one line. The
    book must never block or crash on this layer.
    """
    try:
        cid = str(candidate_id or "").strip()
        if not cid:
            _log.info("judgment: no candidate_id -> ABSENT")
            return VERDICT_ABSENT
        now = parse_utc(now_utc)
        if now is None:
            _log.warning("judgment[%s]: unparseable now_utc %r -> ABSENT", cid, now_utc)
            return VERDICT_ABSENT
        directory = Path(verdict_dir) if verdict_dir is not None else _default_verdict_dir()
        # Today then yesterday: a verdict written before UTC midnight must stay consumable
        # into the new day for the remainder of its TTL (the TTL check below still binds).
        entry = None
        for day in _consume_days(now):
            path = directory / verdict_filename(day)
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                _log.warning("judgment[%s]: unreadable %s (%r) -> skipped", cid, path, exc)
                continue
            if not isinstance(data, dict):
                _log.warning("judgment[%s]: %s top level is not a mapping -> skipped", cid, path)
                continue
            found = data.get(cid)
            if found is not None:
                entry = found
                break
        if entry is None:
            _log.info("judgment[%s]: no verdict entry (today or yesterday) -> ABSENT", cid)
            return VERDICT_ABSENT
        if not isinstance(entry, dict):
            _log.warning("judgment[%s]: entry is not a mapping -> ABSENT", cid)
            return VERDICT_ABSENT
        if namespace is not None:
            entry_ns = str(entry.get("namespace") or "")
            if not entry_ns or entry_ns != str(namespace):
                _log.warning(
                    "judgment[%s]: wrong book (entry namespace %r, this book %r) -> ABSENT",
                    cid, entry_ns, str(namespace),
                )
                return VERDICT_ABSENT
        verdict = str(entry.get("verdict") or "").strip().upper()
        if verdict not in (VERDICT_RESCUE, VERDICT_VETO):
            _log.warning("judgment[%s]: verdict %r outside enum -> ABSENT", cid, entry.get("verdict"))
            return VERDICT_ABSENT
        written = parse_utc(entry.get("written_at_utc"))
        if written is None:
            _log.warning(
                "judgment[%s]: written_at_utc %r unparseable -> ABSENT",
                cid, entry.get("written_at_utc"),
            )
            return VERDICT_ABSENT
        if default_ttl_s is None:
            default_ttl_s = _consume_bounds(now, namespace).get("consume_ttl_s")
        try:
            ttl = float(entry.get("ttl_s"))
        except (TypeError, ValueError):
            ttl = _finite(default_ttl_s)
        from math import isfinite
        age_s = (now - written).total_seconds()
        fresh = ttl is not None and isfinite(ttl) and ttl > 0 and 0 <= age_s <= ttl
        if not fresh:
            _log.info(
                "judgment[%s]: %s stale (age %.1fs ttl %s) -> ABSENT",
                cid, verdict, age_s, "unset" if ttl is None else f"{ttl:.1f}",
            )
            return VERDICT_ABSENT
        return verdict
    except Exception as exc:  # the book never blocks on this layer
        _log.warning("judgment[%r]: lookup failed (%r) -> ABSENT", candidate_id, exc)
        return VERDICT_ABSENT


# ---------------------------------------------------------------------------
# 4. LIVE fire-path consume — APPROVE | SIZE | HOLD | PASS
# ---------------------------------------------------------------------------
FLOW_APPROVE = "APPROVE"
FLOW_SIZE = "SIZE"
FLOW_HOLD = "HOLD"
FLOW_PASS = "PASS"
ROLE_JUDGMENT = "JUDGMENT"
HEDGE_FUND_VERDICTS = frozenset({"approve", "veto", "abstain", "hold"})
FLOW_SIDECAR_NAMES = ("flow_{day}.json", "consume_{day}.json")
DEFAULT_EXTRA_ROW_DIRS = (
    Path(r"C:\Users\trader\gtos\grok-jobs\outbox\debate\judgment"),
    Path("/Users/borr/Documents/gtos/grok-jobs/outbox/debate/judgment"),
)


def _unwrap_size(value):
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def proposed_size_mult_of(row: Mapping[str, Any]) -> Optional[float]:
    evidence = row.get("evidence")
    containers: list[Any] = []
    if isinstance(evidence, Mapping):
        containers.append(evidence)
    containers.append(row)
    for container in containers:
        if not isinstance(container, Mapping):
            continue
        for name in ("PROPOSED_SIZE_MULT", "proposed_size_mult"):
            if name not in container:
                continue
            parsed = _unwrap_size(container[name])
            if parsed is not None:
                return parsed
    return None


def _is_hedge_fund_row(row: Mapping[str, Any]) -> bool:
    role = str(row.get("role") or row.get("element") or "").strip().upper()
    if role == ROLE_JUDGMENT:
        return True
    verdict = str(row.get("verdict") or "").strip().lower()
    schema = str(row.get("schema_version") or "")
    if schema in ("gtos.debate.judgment.v1", "gtos.judgment.row.v1") and verdict in HEDGE_FUND_VERDICTS:
        # Official role rows use true|false|UNJUDGEABLE — those are not hedge-fund fire verbs.
        if verdict in ("true", "false") or str(row.get("verdict") or "").upper().startswith("UNJUDGEABLE"):
            return False
        return verdict in HEDGE_FUND_VERDICTS
    return verdict in HEDGE_FUND_VERDICTS and role in ("", ROLE_JUDGMENT)


def _hedge_row_ineligible(row: Mapping[str, Any], budget_s: float | None = None) -> Optional[str]:
    if not isinstance(row, Mapping):
        return "not_mapping"
    if not str(row.get("join_key") or row.get("candidate_id") or "").strip():
        return "missing_join_key"
    if not str(row.get("verdict") or "").strip():
        return "missing_verdict"
    if not _is_hedge_fund_row(row):
        return "not_hedge_fund_judgment"
    # No P&L field is allowed on a consume-eligible row (lock §6).
    for key in ("pnl", "after", "realized_pnl", "equity", "realized_today_pct"):
        if key in row:
            return "pnl_present"
    latency = row.get("latency_ms")
    if latency not in (None, ""):
        try:
            latency_f = float(latency)
        except (TypeError, ValueError):
            return "latency_ms_unparseable"
        budget = _finite(budget_s)
        if budget is not None and latency_f > budget * _MS_PER_S:
            return "latency_over_budget"
    return None


def _flow_action_from_verdict(verdict: Any, size_mult: Optional[float]) -> str:
    text = str(verdict or "").strip().lower()
    if text in ("veto", "hold") or text == VERDICT_VETO.lower():
        return FLOW_HOLD
    if text in ("abstain", "pass", "absent") or text.upper().startswith(VERDICT_UNJUDGEABLE):
        return FLOW_PASS
    if text in ("approve", "true"):
        # SIZE is in-flow annotation only. Caller must not multiply lots.
        if size_mult is not None:
            return FLOW_SIZE
        return FLOW_APPROVE
    return FLOW_PASS


def _entry_fresh(entry: Mapping[str, Any], now: datetime, default_ttl_s: float | None) -> bool:
    """False unless the entry carries a parseable timestamp inside a positive TTL.

    FAIL-CLOSED ON MALFORMED TIME, deliberately (2026-08-25 seam fix): the previous
    shape returned True for an absent/unparseable ``written_at_utc`` and True for
    ``ttl_s <= 0``, so a malformed HOLD row bound the fire path FOREVER -- a bot bug
    became a standing veto no TTL could clear. A row without a valid clock cannot
    prove it is current, and the consume law is that only a CURRENT judged row may
    override code-only behavior.
    """
    written = parse_utc(entry.get("written_at_utc") or entry.get("ts"))
    if written is None:
        return False
    try:
        ttl = float(entry.get("ttl_s"))
    except (TypeError, ValueError):
        ttl = _finite(default_ttl_s)
    from math import isfinite
    if ttl is None or not isfinite(ttl) or ttl <= 0:
        return False
    return 0 <= (now - written).total_seconds() <= ttl


def _consume_days(now: datetime) -> list[str]:
    """Today then yesterday (UTC). A row written at 23:58 must survive the midnight
    filename roll: reads keyed on the consume date alone lost every row for up to its
    whole TTL at 00:00 UTC. TTL still binds -- yesterday's file is READ, its rows are
    consumed only while fresh."""
    from datetime import timedelta

    return [
        now.date().isoformat(),
        (now - timedelta(days=1)).date().isoformat(),
    ]


def _default_verdict_dir() -> Path:
    """`judgment/` anchored on the REPO ROOT, never the process cwd.

    The live book passes `verdict_dir` explicitly; this default exists for direct
    calls and the CLI, where a cwd-relative `Path("judgment")` silently resolved
    against wherever the process happened to start (a supervisor's working dir, a
    scheduler's home) and read an empty directory with a healthy log.
    """
    return Path(__file__).resolve().parents[3] / VERDICT_DIR_NAME


def _sidecar_decision(
    candidate_ids: list[str],
    now: datetime,
    directory: Path,
    namespace: Any,
    default_ttl_s: float | None,
) -> Optional[dict[str, Any]]:
    paths = [
        directory / name.format(day=day)
        for day in _consume_days(now)
        for name in FLOW_SIDECAR_NAMES
    ]
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _log.warning("judgment_flow: unreadable sidecar %s (%r) -> PASS", path, exc)
            continue
        if not isinstance(data, dict):
            continue
        for cid in candidate_ids:
            entry = data.get(cid)
            if not isinstance(entry, dict):
                continue
            if namespace is not None:
                entry_ns = str(entry.get("namespace") or "")
                if entry_ns and entry_ns != str(namespace):
                    continue
            if not _entry_fresh(entry, now, default_ttl_s):
                _log.info("judgment_flow[%s]: sidecar stale -> PASS", cid)
                continue
            verdict = entry.get("verdict") or entry.get("action")
            size = proposed_size_mult_of(entry)
            action = str(entry.get("action") or "").strip().upper()
            if action not in (FLOW_APPROVE, FLOW_SIZE, FLOW_HOLD, FLOW_PASS):
                action = _flow_action_from_verdict(verdict, size)
            return {
                "action": action,
                "verdict": str(entry.get("verdict") or "").strip() or None,
                "role": str(entry.get("role") or ROLE_JUDGMENT),
                "why_code": str(entry.get("why_code") or ""),
                "proposed_size_mult": size,
                "source": str(path),
                "join_key": cid,
                "reason": "sidecar",
            }
    return None


def _latest_hedge_row(
    candidate_ids: list[str],
    row_dirs: list[Path],
    now: Optional[datetime] = None,
    budget_s: float | None = None,
    max_age_s: float | None = None,
) -> Optional[dict[str, Any]]:
    wanted = {str(x) for x in candidate_ids if str(x).strip()}
    age_bound = _finite(max_age_s)
    if not wanted:
        return None
    best: Optional[tuple[datetime, int, dict[str, Any], str]] = None
    seq = 0
    for directory in row_dirs:
        if not directory.is_dir():
            continue
        paths = sorted(directory.glob("*.jsonl"))
        for path in paths:
            name = path.name.lower()
            # Skip machinery role dumps. Consume hedge-fund JUDGMENT only.
            if name.startswith(("cost_", "risk_", "alignment_", "state_", "geometry_")):
                continue
            # DATE BOUND (2026-08-25 seam fix): these directories accumulate one jsonl per
            # bot per day forever; reading every byte of every historical file on every fire
            # is an unbounded walk that grows with the age of the deployment. A file whose
            # mtime is older than the scan bound cannot contain a consumable row (TTL law).
            # Skipping on a failed stat is fail-open toward code: the row is simply not
            # consumed, and PASS is code-only behavior.
            if now is not None:
                try:
                    mtime = path.stat().st_mtime
                    if age_bound is not None:
                        if (now.timestamp() - mtime) > age_bound:
                            continue
                    else:
                        stamped = datetime.fromtimestamp(mtime, timezone.utc)
                        if stamped.date() != now.astimezone(timezone.utc).date():
                            continue
                except OSError:
                    continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                if not line.strip():
                    continue
                seq += 1
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict):
                    continue
                if _hedge_row_ineligible(row, budget_s) is not None:
                    continue
                key = str(row.get("join_key") or row.get("candidate_id") or "").strip()
                if key not in wanted:
                    continue
                written = parse_utc(row.get("written_at_utc") or row.get("ts")) or datetime.min.replace(
                    tzinfo=timezone.utc
                )
                cand = (written, seq, row, str(path))
                if best is None or cand[:2] >= best[:2]:
                    best = cand
    if best is None:
        return None
    _written, _seq, row, source = best
    key = str(row.get("join_key") or row.get("candidate_id") or "").strip()
    size = proposed_size_mult_of(row)
    verdict = row.get("verdict")
    return {
        "action": _flow_action_from_verdict(verdict, size),
        "verdict": str(verdict or "").strip() or None,
        "role": str(row.get("role") or row.get("element") or ROLE_JUDGMENT),
        "why_code": str(row.get("why_code") or ""),
        "proposed_size_mult": size,
        "source": source,
        "join_key": key,
        "reason": "latest_eligible_row",
        "written_at_utc": str(row.get("written_at_utc") or row.get("ts") or ""),
        # Carried so the HOLD freshness law reads the ROW's OWN TTL: without this the
        # synthesized decision fell back to the default TTL and a row's ttl_s (0 included)
        # was silently ignored on the flow path.
        "ttl_s": row.get("ttl_s"),
    }


def judgment_flow(
    candidate_id: Any,
    now_utc: Any,
    *,
    verdict_dir: Any = None,
    namespace: Any = None,
    extra_ids: Optional[Iterable[Any]] = None,
    extra_row_dirs: Optional[Iterable[Any]] = None,
    default_ttl_s: float | None = None,
) -> dict[str, Any]:
    """LIVE consume for the $75 fire path. NEVER raises. NEVER applies size_mult.

    Returns ``{action, verdict, role, why_code, proposed_size_mult, source, join_key, reason}``.
    ``action`` is APPROVE | SIZE | HOLD | PASS.

    Fail-closed-no-row is PASS, not HOLD: a missing sidecar, empty day, or unmatched
    join_key must not invent a veto that kills every fire. Abstain is PASS.
    HOLD only when a real eligible hedge-fund JUDGMENT row (or sidecar) says veto.
    """
    absent = {
        "action": FLOW_PASS,
        "verdict": None,
        "role": ROLE_JUDGMENT,
        "why_code": "",
        "proposed_size_mult": None,
        "source": None,
        "join_key": None,
        "reason": "no_row",
    }
    try:
        ids: list[str] = []
        for raw in (candidate_id, *(list(extra_ids) if extra_ids is not None else [])):
            text = str(raw or "").strip()
            if text and text not in ids:
                ids.append(text)
        if not ids:
            absent["reason"] = "no_candidate_id"
            _log.info("judgment_flow: no candidate_id -> PASS")
            return dict(absent)
        now = parse_utc(now_utc)
        if now is None:
            _log.warning("judgment_flow: unparseable now_utc %r -> PASS", now_utc)
            absent["reason"] = "unparseable_now"
            return dict(absent)
        directory = Path(verdict_dir) if verdict_dir is not None else _default_verdict_dir()
        bounds = _consume_bounds(now, namespace)
        if default_ttl_s is None:
            default_ttl_s = bounds.get("consume_ttl_s")
        sidecar = _sidecar_decision(ids, now, directory, namespace, default_ttl_s)
        if sidecar is not None:
            return sidecar
        row_dirs = [directory / "rows", directory]
        if extra_row_dirs is None:
            extra_row_dirs = DEFAULT_EXTRA_ROW_DIRS
        for extra in extra_row_dirs:
            if extra is None:
                continue
            row_dirs.append(Path(extra))
        row = _latest_hedge_row(
            ids, row_dirs, now, bounds.get("latency_budget_s"), bounds.get("row_scan_max_age_s"),
        )
        if row is None:
            _log.info("judgment_flow[%s]: no eligible row -> PASS", ids[0])
            absent["join_key"] = ids[0]
            return dict(absent)
        # A HOLD may bind only while provably fresh. `_entry_fresh` is False for an absent or
        # unparseable written_at_utc and for ttl_s <= 0 (2026-08-25 seam fix) -- a malformed
        # HOLD row used to bind forever; now it degrades to PASS with the reason on the row.
        if row["action"] == FLOW_HOLD and not _entry_fresh(row, now, default_ttl_s):
            _log.info(
                "judgment_flow[%s]: HOLD row stale/unclocked -> PASS (will not invent a live veto)",
                row.get("join_key"),
            )
            absent["join_key"] = row.get("join_key")
            absent["reason"] = "stale_hold_row"
            absent["verdict"] = row.get("verdict")
            return dict(absent)
        return row
    except Exception as exc:
        _log.warning("judgment_flow[%r]: lookup failed (%r) -> PASS", candidate_id, exc)
        absent["reason"] = "lookup_failed"
        return dict(absent)


# ---------------------------------------------------------------------------
# reducer CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic judgment reducer: role JSONL rows -> one daily verdict file.")
    parser.add_argument("--rows", nargs="+", required=True,
                        help="Role JSONL files, or directories scanned for *.jsonl (sorted).")
    parser.add_argument("--out-dir", default=VERDICT_DIR_NAME,
                        help="Directory for verdicts_<date>.json (default: judgment/).")
    parser.add_argument("--date", default=None,
                        help="YYYY-MM-DD verdict day (default: today UTC).")
    parser.add_argument("--latency-budget-s", type=float, default=None)
    parser.add_argument("--ttl-s", type=float, default=None)
    args = parser.parse_args(argv)

    paths: list[Path] = []
    for raw in args.rows:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.jsonl")))
        else:
            paths.append(p)
    day = args.date or datetime.now(timezone.utc).date().isoformat()
    verdicts, stats = reduce_verdicts(
        paths,
        out_dir=args.out_dir,
        day=day,
        latency_budget_s=args.latency_budget_s,
        ttl_s=args.ttl_s,
    )
    print(json.dumps({"day": day, "verdicts": len(verdicts), **stats}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

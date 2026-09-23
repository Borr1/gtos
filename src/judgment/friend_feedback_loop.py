"""FRIEND_FEEDBACK_LOOP_V0 — Chair LABEL on autonomous friend copies.

Unique file. Default-OFF. Recommendation-only. Fail-closed if missing.

Challenge ``0`` is the printer. friend_a / redacted_account / redacted_account are an
autonomous in-system copy of that printer (same lots, same SL, same TP) plus
this feedback learning loop. They are **not** accounts a Cursor agent places
into. redacted_account stays idle. Verification ``0`` is quarantined.

This file does four things and nothing else:

1. Score friend fills against the Challenge printer copy-contract.
2. Persist friend outcomes (feature + label store) for Chair.
3. Emit KEEP/STUDY/STARVE/HARD_OFF/WATCH as Chair LABEL from friend closes
   when present — never from frozen Verification ``f5_study``.
4. When the live rung calls with no sit, ask one hop on the open Challenge
   fill. The learning decision is the Choice option with the highest
   probability on that copied fill. No boolean skips the hop. An unanswered
   hop writes nothing. The Choice does not send.

It does **not** agent-place, invent a 0.01 lot floor, remint, flatten,
leftover-ship ``book_owner``, bounce Challenge, recycle FN, sit Verification,
or move APPLY persist off 0.00.

Host hook (observer, env-gate BEFORE import, never refuse a fire):

    if os.environ.get("GTOS_JEV_FRIEND_FEEDBACK", "").strip().lower() in {"1", "true", "yes"}:
        from src.judgment.friend_feedback_loop import maybe_run_friend_feedback
        maybe_run_friend_feedback(sit_path=sit_json)

Absence of the env is off. Do not copy this onto the host with #77.
Do not bounce Challenge ``11792→5852`` to load it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .challenge import (
    CHALLENGE_KEEP_FAMILIES,
    CHALLENGE_LOGIN,
    VERIFICATION_QUARANTINED,
    account_surface,
)
from .family import family_class_for, hard_off_family, keep_family
from .friend_copy_contract import (
    AGENT_PLACE_MIN_LOT_TICKETS,
    CHAIR_NAMED_CLOSED_NO_TOUCH,
    CHAIR_NAMED_OPEN_TICKETS,
    FRIEND_BOOKS,
    FRIEND_LOGINS,
    FRIEND_NAMESPACES,
    redacted_account_IDLE,
    redacted_account_NS,
    LEAVE_ORIG_TICKETS,
    PRINTER_LOGIN,
    PRINTER_NAMED_FILLS,
    PRINTER_NS,
    identity_surface,
    is_friend_login,
    is_printer_login,
    note_copy_bounds,
    score_copy,
)
from .friend_copy_contract import _lots, _price, _side

MappingLike = Mapping[str, Any]

SCHEMA = "gtos.judgment.friend_feedback_loop.v0"
LABEL_STORE_SCHEMA = "gtos.judgment.friend_label_store.v0"
FEATURE_STORE_SCHEMA = "gtos.judgment.friend_history_features.v0"
LEARNING_SCHEMA = "gtos.judgment.friend_learning_row.v0"
FRIEND_FEEDBACK_ENV = "GTOS_JEV_FRIEND_FEEDBACK"
FRIEND_FEEDBACK_PATH_ENV = "GTOS_JEV_FRIEND_FEEDBACK_PATH"
FRIEND_FEEDBACK_RECORDS_ENV = "GTOS_JEV_FRIEND_FEEDBACK_RECORDS"

# Learning decision is this Choice. No Noul in front of it.
COPY_RECORD_OPTIONS = ("record", "hold", "not_a_copy")


def _fill_named(fill: MappingLike) -> str:
    return (
        f"ticket {fill.get('ticket')} {fill.get('symbol')} {fill.get('side')} "
        f"lots {fill.get('lots')} stop {fill.get('sl')} target {fill.get('tp')} "
        f"lifecycle {fill.get('lifecycle')}"
    )


def friend_learn_questions(fill: MappingLike) -> dict[str, dict[str, Any]]:
    """Choice on this copied fill, then how much of that fill to keep."""

    named = _fill_named(fill)
    return {
        "copy_record": {
            "type": "choice",
            "instructions": (
                f"Learning decision for this copied fill only: {named}. "
                "Friends copy the same lots, stop, and target. Do not send."
            ),
            "criteria": {
                "record": f"Record a learning row for {named}. Do not send.",
                "hold": f"{named} stays open. Record that it is open. Do not send.",
                "not_a_copy": (
                    f"Lots or protection on {named} are not an in-system copy. Do not send."
                ),
            },
        },
        "include_depth": {
            "type": "score",
            "instructions": (
                f"For copied fill {named}, how much of that fill belongs in the "
                "learning record? hide / short / long / full."
            ),
            "criteria": [
                "Hide this fill",
                "Short summary of lots, stop, and target",
                "Longer summary including sleeve and lifecycle",
                "Whole fill object",
            ],
        },
    }


def highest_probability_choice(block: Any) -> dict[str, Any]:
    """The learning decision is the Choice option with the highest probability."""

    empty: dict[str, Any] = {
        "choice": None,
        "probability": None,
        "probabilities": {},
        "tie": False,
    }
    if not isinstance(block, Mapping):
        return empty
    probs_in = block.get("probabilities")
    probs: dict[str, float] = {}
    if isinstance(probs_in, Mapping):
        for key, val in probs_in.items():
            name = str(key)
            if name not in COPY_RECORD_OPTIONS:
                continue
            try:
                probs[name] = float(val)
            except (TypeError, ValueError):
                continue
    if not probs:
        return empty
    top = max(probs.values())
    winners = [name for name, value in probs.items() if value == top]
    if len(winners) != 1:
        return {"choice": None, "probability": top, "probabilities": probs, "tie": True}
    return {
        "choice": winners[0],
        "probability": top,
        "probabilities": probs,
        "tie": False,
    }

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "friend_feedback_loop" / "fixtures"
)
DEFAULT_STORE = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "friend_feedback_loop" / "store.jsonl"
)

W7_ARMED_TAGS = frozenset({"crypto", "energy_agri", "sub_xvol_pullback"})
STUDY_PREFIXES = ("dsp_three_fre", "dsp_three_fresh")
DSP_PREFIX = "dsp_"
QUIET_STUDY_ONLY = STUDY_PREFIXES

PIN_WINDOW_REQUIRED = "G-FULL"
OVERLAY_77_WINDOW = "Y2025"

# The block noul for this persist fact. Empty does not write a block.
_BLOCK_FACT: str | None = None
_BLOCK: bool | None = None


def _returned_persist() -> float | None:
    """The persist score already returned. A miss stays unset."""

    try:
        from .gold_priors import applied_persistence_weight
    except Exception:
        return None
    try:
        weight = applied_persistence_weight()
    except Exception:
        return None
    if isinstance(weight, bool) or weight is None:
        return None
    try:
        number = float(weight)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _persist_fact() -> str:
    return f"{PIN_WINDOW_REQUIRED}|{_returned_persist()}"


def _note_persist_block(blocks: bool | None, fact: str) -> None:
    global _BLOCK_FACT, _BLOCK
    if _BLOCK_FACT != fact:
        _BLOCK_FACT = fact
        _BLOCK = None
    if blocks is True or blocks is False:
        _BLOCK = blocks


def _finite_score(block: Any) -> float | None:
    if not isinstance(block, Mapping):
        return None
    if block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        raw = returned_number(block)
    except Exception:
        raw = block.get("score", block.get("value"))
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _block_noul(block: Any) -> bool | None:
    if block is True or block is False:
        return block
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return None

_TRUTHY = frozenset({"1", "true", "yes", "on"})

ACTIONS = ("KEEP", "STUDY", "STARVE", "HARD_OFF", "WATCH")
COPY_ACTIONS = ("COPY_OK", "AGENT_PLACE", "MISSING_COPY", "SL_TP_MISS", "LOTS_MISMATCH")


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def friend_feedback_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default-OFF. Unset / empty / 0 is off."""

    return _env_on(FRIEND_FEEDBACK_ENV, environ)


def default_store_path() -> Path:
    override = (os.environ.get(FRIEND_FEEDBACK_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_STORE


def _login_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()


def _fail(
    reason: str,
    *,
    enabled: bool,
    extra: MappingLike | None = None,
    fail_closed: bool | None = None,
) -> dict[str, Any]:
    closed = enabled if fail_closed is None else fail_closed
    skipped = None if enabled else f"{FRIEND_FEEDBACK_ENV}_off"
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "printer": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "friends": sorted(FRIEND_LOGINS),
        "enabled": enabled,
        "skipped": skipped,
        "fail_closed": closed,
        "fail_closed_reason": reason if closed else skipped,
        "extra_pass": False,
        "recommendation_emitted": False,
        "apply": False,
        "silent_apply": False,
        "never_place": True,
        "never_agent_place": True,
        "never_invent_min_lot": True,
        "never_flatten": True,
        "never_remint": True,
        "never_bounce_challenge": True,
        "never_recycle_fn": True,
        "persist_weight": _returned_persist(),
        "pin_window": PIN_WINDOW_REQUIRED,
        "overlay_77_copied": False,
        "invented_min_lot": None,
        "do_not_flatten_tickets": sorted(LEAVE_ORIG_TICKETS | AGENT_PLACE_MIN_LOT_TICKETS),
        "copies": [],
        "features": [],
        "copies": [],
        "features": [],
        "copy_recommendations": [],
        "recommendations": [],
        "label_store": None,
        "learning_row": None,
        "proved": False,
        "write": False,
        "decision": (
            "No extra PASS. Friends copy Challenge fills in-system. "
            "Agents do not place. persist stays 0.00."
        ),
        "surface": identity_surface(),
    }
    if extra:
        row.update(dict(extra))
    return row


def persist_pin_ok() -> tuple[bool, str, dict[str, Any]]:
    """The block noul decides. A miss does not close the loop."""

    weight = _returned_persist()
    meta: dict[str, Any] = {"pin_window": None, "persist_weight": weight}
    try:
        from .gold_priors import PIN_WINDOW, assert_gold_pin
    except ImportError:
        return False, "gold_priors_missing", meta
    pin = str(PIN_WINDOW or "")
    meta["pin_window"] = pin
    meta["overlay_window"] = pin == OVERLAY_77_WINDOW
    try:
        assert_gold_pin()
    except Exception as exc:  # noqa: BLE001 — a broken pin file is an error
        return False, f"gold_pin_failed:{exc}", meta
    fact = _persist_fact()
    if _BLOCK_FACT == fact and _BLOCK is True:
        return False, "persist_blocks", meta
    return True, "persist_open", meta


def identity_ok(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    heartbeat: MappingLike | None = None,
    sit: MappingLike | None = None,
) -> tuple[bool, str]:
    """Friends + Challenge printer only. FN / Verification / W7 fail closed."""

    hb = dict(heartbeat or {})
    sit_doc = dict(sit or {})
    sit_login = _login_text(sit_doc.get("login") or sit_doc.get("account"))
    sit_ns = str(sit_doc.get("namespace") or "").strip()
    ns = str(namespace or hb.get("namespace") or sit_ns or "").strip()
    raw_login = sit_login or _login_text(login) or _login_text(
        hb.get("login") or hb.get("account")
    )
    tag_set = {str(t).strip() for t in (tags or hb.get("tags") or sit_doc.get("tags") or []) if str(t).strip()}

    # Sit organism is senior to CLI --login / --namespace. Observer defaults
    # 0 / operator must not launder Verification or FN.
    if (
        sit_login == VERIFICATION_QUARANTINED
        or sit_ns in {"f5_study", "verification"}
        or raw_login == VERIFICATION_QUARANTINED
        or ns in {"f5_study", "verification"}
    ):
        return False, "verification_quarantined"
    if (
        sit_login == redacted_account_IDLE
        or sit_ns in {redacted_account_NS, "redacted_account"}
        or raw_login == redacted_account_IDLE
        or ns in {redacted_account_NS, "redacted_account"}
    ):
        return False, "redacted_account_idle"
    hb_ns = str(hb.get("namespace") or "").strip()
    hb_tags = {str(t).strip() for t in (hb.get("tags") or []) if str(t).strip()}
    if hb_tags and hb_tags <= W7_ARMED_TAGS and hb_ns not in FRIEND_NAMESPACES | {PRINTER_NS, ""}:
        return False, "w7_other_organism"
    if tag_set and tag_set <= W7_ARMED_TAGS and ns not in FRIEND_NAMESPACES | {PRINTER_NS}:
        return False, "w7_other_organism"
    if raw_login and is_printer_login(raw_login) and ns and ns not in FRIEND_NAMESPACES | {PRINTER_NS, ""}:
        return False, "namespace_not_fleet"
    if raw_login and not (is_printer_login(raw_login) or is_friend_login(raw_login)):
        return False, "login_not_fleet"
    if ns and ns not in FRIEND_NAMESPACES | {PRINTER_NS, ""}:
        if ns in {redacted_account_NS, "redacted_account"}:
            return False, "redacted_account_idle"
        return False, "namespace_not_fleet"
    return True, "fleet_challenge_plus_friends"


def load_json(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.is_file():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def quiet_action(sleeve: str, *, symbol: str = "") -> str:
    """Quiet-book law. Recommendation only — does not lift a live cut."""

    sl = (sleeve or "").strip().lower()
    if keep_family(sl) or any(sl.startswith(k) for k in CHALLENGE_KEEP_FAMILIES):
        return "KEEP"
    if hard_off_family(sl, symbol):
        return "HARD_OFF"
    if any(sl.startswith(p) for p in QUIET_STUDY_ONLY):
        return "STUDY"
    if sl.startswith(DSP_PREFIX):
        return "STARVE"
    klass = family_class_for(sl, symbol=symbol, origin="f5_challenge")
    if klass == "house_keep":
        return "KEEP"
    if klass == "house_hard_off":
        return "HARD_OFF"
    if klass == "starve_watch":
        return "STARVE"
    if klass == "a_plus_study":
        return "WATCH"
    return "WATCH"


def _printer_by_ticket(sit: MappingLike) -> dict[Any, dict[str, Any]]:
    by_ticket: dict[Any, dict[str, Any]] = {}
    for raw in sit.get("printer_fills") or sit.get("challenge_fills") or []:
        if not isinstance(raw, dict):
            continue
        ticket = raw.get("ticket")
        if ticket is None:
            continue
        by_ticket[ticket] = dict(raw)
        try:
            by_ticket[int(ticket)] = dict(raw)
        except (TypeError, ValueError):
            pass
    for ticket, named in PRINTER_NAMED_FILLS.items():
        by_ticket.setdefault(ticket, {"ticket": ticket, **named})
        by_ticket.setdefault(str(ticket), {"ticket": ticket, **named})
    return by_ticket


def _friend_fills(sit: MappingLike) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in sit.get("friend_fills") or sit.get("copies") or []:
        if isinstance(raw, dict):
            rows.append(dict(raw))
    books = sit.get("books") or {}
    if isinstance(books, dict):
        for login, book in books.items():
            if not isinstance(book, dict):
                continue
            for pos in book.get("positions") or book.get("fills") or []:
                if not isinstance(pos, dict):
                    continue
                row = dict(pos)
                row.setdefault("login", login)
                rows.append(row)
    return rows


def score_sit_copies(sit: MappingLike) -> list[dict[str, Any]]:
    printers = _printer_by_ticket(sit)
    scored: list[dict[str, Any]] = []
    for fill in _friend_fills(sit):
        src_ticket = fill.get("source_ticket")
        comment = str(fill.get("comment") or "")
        printer = None
        if src_ticket in printers:
            printer = printers[src_ticket]
        else:
            try:
                printer = printers.get(int(src_ticket)) if src_ticket is not None else None
            except (TypeError, ValueError):
                printer = None
        if printer is None:
            for ticket in PRINTER_NAMED_FILLS:
                if f"fleet:{ticket}" in comment:
                    printer = printers.get(ticket)
                    fill = {**fill, "source_ticket": ticket}
                    break
        scored.append(score_copy(printer, fill))
    return scored


def feature_rows(copies: Iterable[MappingLike], *, as_of: str | None = None) -> list[dict[str, Any]]:
    stamped = as_of or datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for copy in copies:
        rows.append(
            {
                "schema": FEATURE_STORE_SCHEMA,
                "as_of_utc": stamped,
                "printer_login": PRINTER_LOGIN,
                "friend_login": copy.get("friend_login"),
                "friend_name": copy.get("friend_name"),
                "printer_ticket": copy.get("printer_ticket"),
                "friend_ticket": copy.get("friend_ticket"),
                "kind": copy.get("kind"),
                "is_copy": copy.get("is_copy"),
                "agent_place": copy.get("agent_place"),
                "invented_min_lot": copy.get("invented_min_lot"),
                "lots_match": copy.get("lots_match"),
                "sl_match": copy.get("sl_match"),
                "tp_match": copy.get("tp_match"),
                "side_match": copy.get("side_match"),
                "symbol_match": copy.get("symbol_match"),
                "friend_lots": copy.get("friend_lots"),
                "printer_lots": copy.get("printer_lots"),
                "feature_store_exclusion": "labels_and_copy_fidelity_only",
                "apply": False,
                "persist_weight": _returned_persist(),
            }
        )
    return rows


def recommend_copies(copies: Iterable[MappingLike]) -> list[dict[str, Any]]:
    """One Chair LABEL row per friend book. Never place. Never flatten."""

    by_login: dict[str, dict[str, Any]] = {
        login: {
            "login": login,
            "name": book["name"],
            "ns": book["ns"],
            "action": "MISSING_COPY",
            "n_copies": 0,
            "n_agent_place": 0,
            "n_ok": 0,
            "chair": "LABEL",
            "size_up": False,
            "apply": False,
            "silent_apply": False,
            "flatten": False,
            "agent_place": False,
        }
        for login, book in FRIEND_BOOKS.items()
    }
    for copy in copies:
        login = _login_text(copy.get("friend_login"))
        slot = by_login.get(login)
        if slot is None:
            continue
        kind = str(copy.get("kind") or "")
        if kind == "in_system_copy":
            slot["n_ok"] += 1
            slot["n_copies"] += 1
        elif kind == "agent_place_min_lot":
            slot["n_agent_place"] += 1
            slot["agent_place"] = True
        elif kind == "missing_sl_tp":
            slot["n_copies"] += 1
            if slot["action"] == "MISSING_COPY":
                slot["action"] = "SL_TP_MISS"
        elif kind == "lots_mismatch":
            slot["n_copies"] += 1
            if slot["action"] == "MISSING_COPY":
                slot["action"] = "LOTS_MISMATCH"
        else:
            slot["n_copies"] += 1
    recs = []
    for slot in by_login.values():
        if slot["n_agent_place"]:
            slot["action"] = "AGENT_PLACE"
        elif slot["n_ok"] and slot["n_ok"] == slot["n_copies"]:
            slot["action"] = "COPY_OK"
        recs.append(slot)
    recs.sort(key=lambda r: r["name"])
    return recs


def recommend_sleeves(sit: MappingLike) -> list[dict[str, Any]]:
    """Quiet-book LABEL from friend close outcomes. Never size-up."""

    by_sleeve: dict[str, dict[str, Any]] = {}
    for raw in sit.get("friend_closes") or sit.get("closes") or []:
        if not isinstance(raw, dict):
            continue
        sleeve = str(raw.get("sleeve") or "unknown")
        symbol = str(raw.get("symbol") or "")
        action = quiet_action(sleeve, symbol=symbol)
        existing = by_sleeve.get(sleeve)
        if existing is None:
            by_sleeve[sleeve] = {
                "sleeve": sleeve,
                "symbol": symbol,
                "family_class": family_class_for(
                    sleeve, symbol=symbol, origin="f5_challenge"
                ),
                "action": action,
                "n_closes": 1,
                "size_up": False,
                "apply": False,
                "silent_apply": False,
                "flatten": False,
                "chair": "LABEL",
            }
        else:
            existing["n_closes"] += 1
    recs = list(by_sleeve.values())
    recs.sort(
        key=lambda r: (ACTIONS.index(r["action"]) if r["action"] in ACTIONS else len(ACTIONS), r["sleeve"])
    )
    return recs


class LabelStore:
    """Append-only JSONL. Duplicate day+id is a no-op."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def append(self, row: MappingLike) -> dict[str, Any]:
        day = str(row.get("utc_day") or "")
        slate_id = str(row.get("slate_id") or "")
        for existing in self.load():
            if existing.get("utc_day") == day and existing.get("slate_id") == slate_id:
                return {**dict(row), "appended": False, "duplicate": True}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
        return {**dict(row), "appended": True, "duplicate": False}


def label_row(
    sit: MappingLike,
    copies: Iterable[MappingLike],
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    copy_list = [dict(c) for c in copies]
    utc_day = str((sit.get("clock") or {}).get("utc_day") or "")
    if not utc_day:
        built = str(sit.get("as_of_utc") or sit.get("built_at_utc") or as_of or "")
        utc_day = built[:10]
    return {
        "schema": LABEL_STORE_SCHEMA,
        "printer": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "friends": sorted(FRIEND_LOGINS),
        "utc_day": utc_day,
        "slate_id": sit.get("slate_id") or sit.get("sit_id") or "friend_feedback",
        "n_friend_fills": len(copy_list),
        "n_in_system_copy": sum(1 for c in copy_list if c.get("kind") == "in_system_copy"),
        "n_agent_place": sum(1 for c in copy_list if c.get("agent_place")),
        "friend_tickets": [c.get("friend_ticket") for c in copy_list],
        "printer_tickets": sorted({c.get("printer_ticket") for c in copy_list if c.get("printer_ticket")}),
        "persist_weight": _returned_persist(),
        "apply": False,
        "never_agent_place": True,
        "as_of_utc": as_of or datetime.now(timezone.utc).isoformat(),
    }


def trade_records_dir() -> Path | None:
    override = (os.environ.get(FRIEND_FEEDBACK_RECORDS_ENV) or "").strip()
    if override:
        target = Path(override)
        return target if target.is_dir() else None
    candidate = REPO_ROOT / "pipeline_state" / "ultimate_book" / PRINTER_NS / "trade_records"
    return candidate if candidate.is_dir() else None


def _nested(doc: MappingLike, *keys: str) -> Any:
    cur: Any = doc
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def fill_from_trade_record(doc: MappingLike, path: Path) -> dict[str, Any] | None:
    """Facts from a Challenge trade record. Does not invent lots."""

    execution = doc.get("execution") if isinstance(doc.get("execution"), Mapping) else {}
    instrumentation = (
        doc.get("instrumentation") if isinstance(doc.get("instrumentation"), Mapping) else {}
    )
    ticket = execution.get("ticket") or doc.get("ticket")
    if ticket is None:
        return None
    flow_lots = _nested(doc, "instrumentation", "gtos_live_flow_execution", "lots_placed")
    result = execution.get("result") if isinstance(execution.get("result"), Mapping) else {}
    lots = _lots(flow_lots if flow_lots is not None else result.get("volume"))
    sl = _price(execution.get("broker_position_sl"))
    tp = _price(execution.get("broker_position_tp"))
    side = _side(instrumentation.get("direction") or doc.get("side"))
    symbol = str(doc.get("symbol") or execution.get("broker_symbol") or "").strip()
    lifecycle = str(doc.get("trade_lifecycle_status") or "").strip().lower()
    opened = str(doc.get("opened_at_utc") or "")
    return {
        "ticket": int(ticket) if str(ticket).isdigit() else ticket,
        "symbol": symbol,
        "side": side,
        "lots": lots,
        "sl": sl,
        "tp": tp,
        "sleeve": str(doc.get("sleeve") or ""),
        "lifecycle": lifecycle or "unknown",
        "opened_at_utc": opened,
        "closed_at_utc": doc.get("closed_at_utc"),
        "broker_exit_profit": doc.get("broker_exit_profit"),
        "source_name": path.name,
        "source_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def select_printer_fill(records: Path) -> tuple[dict[str, Any] | None, str]:
    """One object: the open printer fill, else the newest record."""

    newest: tuple[float, dict[str, Any]] | None = None
    newest_open: tuple[float, dict[str, Any]] | None = None
    for path in records.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        fill = fill_from_trade_record(payload, path)
        if fill is None or fill.get("lots") is None:
            continue
        stamp = path.stat().st_mtime
        if newest is None or stamp >= newest[0]:
            newest = (stamp, fill)
        if fill.get("lifecycle") == "open" and (newest_open is None or stamp >= newest_open[0]):
            newest_open = (stamp, fill)
    if newest_open is not None:
        return newest_open[1], "open_fill"
    if newest is not None:
        return newest[1], "newest_fill"
    return None, "no_trade_record_with_lots"


def friend_learn_state(fill: MappingLike) -> dict[str, Any]:
    return {
        "labels": {
            "book": "challenge",
            "fire": "friend_copy",
            "when": fill.get("lifecycle"),
            "ticket": str(fill.get("ticket")),
        },
        "copied_fill": {
            "ticket": fill.get("ticket"),
            "symbol": fill.get("symbol"),
            "side": fill.get("side"),
            "lots": fill.get("lots"),
            "sl": fill.get("sl"),
            "tp": fill.get("tp"),
            "sleeve": fill.get("sleeve"),
            "lifecycle": fill.get("lifecycle"),
            "login": PRINTER_LOGIN,
        },
        "copy_rule": "friends copy the same lots, stop, and target; this loop does not send",
        "persist_weight": _returned_persist(),
        "friend_broker_tickets": "not_read",
    }


def post_friend_learn_hop(fill: MappingLike) -> dict[str, Any]:
    """One hop on this fill. No boolean in front of the post."""

    from .jev_client import evaluate

    return evaluate(
        friend_learn_state(fill),
        questions=friend_learn_questions(fill),
        merge_sleeve=False,
    )


def learning_store_path(store: LabelStore) -> Path:
    return Path(store.path).with_name("friend_learning.jsonl")


def _learning_row(
    fill: MappingLike,
    hop: MappingLike,
    picked: MappingLike,
    *,
    as_of: str,
) -> dict[str, Any]:
    opened = str(fill.get("opened_at_utc") or as_of)
    utc_day = opened[:10] if len(opened) >= 10 else as_of[:10]
    ticket = fill.get("ticket")
    lifecycle = str(fill.get("lifecycle") or "unknown")
    answers = hop.get("answers") if isinstance(hop.get("answers"), Mapping) else {}
    return {
        "schema": LEARNING_SCHEMA,
        "utc_day": utc_day,
        "slate_id": f"fill:{ticket}:{lifecycle}",
        "printer": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "printer_ticket": ticket,
        "symbol": fill.get("symbol"),
        "side": fill.get("side"),
        "lots": fill.get("lots"),
        "sl": fill.get("sl"),
        "tp": fill.get("tp"),
        "sleeve": fill.get("sleeve"),
        "lifecycle": lifecycle,
        "broker_exit_profit": fill.get("broker_exit_profit"),
        "source_name": fill.get("source_name"),
        "source_mtime_utc": fill.get("source_mtime_utc"),
        "selected_as": fill.get("selected_as"),
        "hop_questions": list(friend_learn_questions(fill)),
        "model": hop.get("model"),
        "http_status": hop.get("http_status"),
        "answers": dict(answers),
        "decision_choice": picked.get("choice"),
        "decision_probability": picked.get("probability"),
        "decision_probabilities": dict(picked.get("probabilities") or {}),
        "sends": False,
        "never_place": True,
        "apply": False,
        "extra_pass": False,
        "persist_weight": _returned_persist(),
        "label_only": False,
        "chair": "RECORD",
        "as_of_utc": as_of,
    }


def record_open_fill(
    *,
    login: Any,
    namespace: Any,
    heartbeat: MappingLike | None,
    store: LabelStore,
    as_of: str,
    pin_meta: MappingLike,
) -> dict[str, Any]:
    """Record one real printer fill through the hop. No sit JSON required."""

    ok, ident_reason = identity_ok(login=login, namespace=namespace, heartbeat=heartbeat)
    if not ok:
        return _fail(ident_reason, enabled=True, extra=pin_meta)
    records = trade_records_dir()
    if records is None:
        override = (os.environ.get(FRIEND_FEEDBACK_RECORDS_ENV) or "").strip()
        return _fail(
            "missing_fill",
            enabled=True,
            extra={
                **dict(pin_meta),
                "missing_fill": override or "pipeline_state trade_records",
            },
        )
    fill, how = select_printer_fill(records)
    if fill is None:
        return _fail(
            "missing_fill",
            enabled=True,
            extra={**dict(pin_meta), "missing_fill": how, "records_dir": str(records)},
        )
    fill = {**fill, "selected_as": how}
    hop = post_friend_learn_hop(fill)
    answers = hop.get("answers") if isinstance(hop.get("answers"), Mapping) else {}
    picked = highest_probability_choice(answers.get("copy_record"))
    if not hop.get("ok") or picked.get("choice") is None:
        return _fail(
            "hop_not_recorded",
            enabled=True,
            extra={
                **dict(pin_meta),
                "hop_status": (
                    "choice_tie"
                    if picked.get("tie")
                    else hop.get("skipped") or hop.get("error") or "no_choice"
                ),
                "http_status": hop.get("http_status"),
                "printer_ticket": fill.get("ticket"),
            },
        )
    stamped = as_of
    row = _learning_row(fill, hop, picked, as_of=stamped)
    stored = LabelStore(learning_store_path(store)).append(row)
    return {
        "schema": SCHEMA,
        "printer": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "friends": sorted(FRIEND_LOGINS),
        "surface": identity_surface(),
        "enabled": True,
        "skipped": None,
        "fail_closed": False,
        "fail_closed_reason": None,
        "identity": ident_reason,
        "extra_pass": False,
        "recommendation_emitted": True,
        "apply": False,
        "silent_apply": False,
        "never_place": True,
        "never_agent_place": True,
        "never_invent_min_lot": True,
        "never_flatten": True,
        "never_remint": True,
        "never_bounce_challenge": True,
        "never_recycle_fn": True,
        "persist_weight": _returned_persist(),
        "pin_window": pin_meta.get("pin_window") or PIN_WINDOW_REQUIRED,
        "overlay_77_copied": False,
        "invented_min_lot": None,
        "do_not_flatten_tickets": sorted(LEAVE_ORIG_TICKETS | {fill["ticket"]} if str(fill["ticket"]).isdigit() else LEAVE_ORIG_TICKETS),
        "copies": [],
        "n_copies": 0,
        "n_in_system_copy": 0,
        "n_agent_place": 0,
        "features": [],
        "n_features": 0,
        "copy_recommendations": [],
        "recommendations": [],
        "n_recommendations": 0,
        "by_action": {action: 0 for action in ACTIONS},
        "by_copy_action": {action: 0 for action in COPY_ACTIONS},
        "label_store": None,
        "learning_row": {
            "path": str(learning_store_path(store)),
            "schema": LEARNING_SCHEMA,
            "printer_ticket": stored.get("printer_ticket"),
            "lots": stored.get("lots"),
            "sl": stored.get("sl"),
            "tp": stored.get("tp"),
            "symbol": stored.get("symbol"),
            "side": stored.get("side"),
            "lifecycle": stored.get("lifecycle"),
            "slate_id": stored.get("slate_id"),
            "answers": stored.get("answers"),
            "model": stored.get("model"),
            "http_status": stored.get("http_status"),
            "decision_choice": stored.get("decision_choice"),
            "decision_probability": stored.get("decision_probability"),
            "appended": stored.get("appended"),
            "duplicate": stored.get("duplicate"),
            "label_only": False,
            "chair": "RECORD",
            "sends": False,
        },
        "proved": True,
        "write": bool(stored.get("appended") or stored.get("duplicate")),
        "gold_pin": "persist_0.00",
        "decision": (
            f"Learning decision is Choice {picked['choice']} "
            f"at probability {picked['probability']} on copied fill {fill.get('ticket')}. "
            "Friends copy the same lots, stop, and target. This loop does not send. "
            "persist stays 0.00."
        ),
    }


def run_friend_feedback(
    *,
    sit_path: Path | str | None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    store: LabelStore | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Enabled path. Callers that need default-off use ``maybe_run_friend_feedback``."""

    enabled = True
    pin_ok, pin_reason, pin_meta = persist_pin_ok()
    if not pin_ok:
        return _fail(pin_reason, enabled=enabled, extra=pin_meta)

    heartbeat = load_json(heartbeat_path) if heartbeat_path is not None else None
    if sit_path is None:
        return record_open_fill(
            login=login,
            namespace=namespace,
            heartbeat=heartbeat,
            store=store or LabelStore(default_store_path()),
            as_of=as_of or datetime.now(timezone.utc).isoformat(),
            pin_meta=pin_meta,
        )
    sit = load_json(sit_path)
    if sit is None:
        return _fail("missing_sit", enabled=enabled, extra=pin_meta)

    ns = namespace
    if ns is None and heartbeat:
        ns = heartbeat.get("namespace")
    if ns is None:
        ns = sit.get("namespace")
    ok, ident_reason = identity_ok(
        login=login or sit.get("login") or sit.get("printer_login"),
        namespace=ns,
        heartbeat=heartbeat,
        sit=sit,
    )
    if not ok:
        return _fail(ident_reason, enabled=enabled, extra=pin_meta)

    copies = score_sit_copies(sit)
    features = feature_rows(copies, as_of=as_of)
    copy_recs = recommend_copies(copies)
    sleeve_recs = recommend_sleeves(sit)
    tickets = sorted(
        set(LEAVE_ORIG_TICKETS)
        | set(AGENT_PLACE_MIN_LOT_TICKETS)
        | {
            int(t)
            for t in (
                [c.get("friend_ticket") for c in copies]
                + [c.get("printer_ticket") for c in copies]
            )
            if t is not None
            and str(t).isdigit()
        }
    )
    store = store or LabelStore(default_store_path())
    stored = store.append(label_row(sit, copies, as_of=as_of))
    return {
        "schema": SCHEMA,
        "printer": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "friends": sorted(FRIEND_LOGINS),
        "surface": {**identity_surface(), **account_surface()},
        "enabled": True,
        "skipped": None,
        "fail_closed": False,
        "fail_closed_reason": None,
        "identity": ident_reason,
        "extra_pass": False,
        "recommendation_emitted": True,
        "apply": False,
        "silent_apply": False,
        "never_place": True,
        "never_agent_place": True,
        "never_invent_min_lot": True,
        "never_flatten": True,
        "never_remint": True,
        "never_bounce_challenge": True,
        "never_recycle_fn": True,
        "persist_weight": _returned_persist(),
        "pin_window": pin_meta.get("pin_window") or PIN_WINDOW_REQUIRED,
        "overlay_77_copied": False,
        "invented_min_lot": None,
        "do_not_flatten_tickets": tickets,
        "copies": copies,
        "n_copies": len(copies),
        "n_in_system_copy": sum(1 for c in copies if c.get("kind") == "in_system_copy"),
        "n_agent_place": sum(1 for c in copies if c.get("agent_place")),
        "features": features,
        "n_features": len(features),
        "copy_recommendations": copy_recs,
        "recommendations": sleeve_recs,
        "n_recommendations": len(sleeve_recs),
        "by_action": {
            action: sum(1 for r in sleeve_recs if r["action"] == action) for action in ACTIONS
        },
        "by_copy_action": {
            action: sum(1 for r in copy_recs if r["action"] == action) for action in COPY_ACTIONS
        },
        "label_store": {
            "path": str(store.path),
            "utc_day": stored.get("utc_day"),
            "slate_id": stored.get("slate_id"),
            "n_friend_fills": stored.get("n_friend_fills"),
            "n_in_system_copy": stored.get("n_in_system_copy"),
            "n_agent_place": stored.get("n_agent_place"),
            "appended": stored.get("appended"),
            "duplicate": stored.get("duplicate"),
        },
        "learning_row": None,
        "gold_pin": pin_reason,
        "named_open": sorted(CHAIR_NAMED_OPEN_TICKETS),
        "named_closed_leave": sorted(CHAIR_NAMED_CLOSED_NO_TOUCH),
        "decision": (
            "Chair LABEL only. Friends are an autonomous copy of Challenge "
            "0 plus this feedback store. Agents do not place. "
            "0.01 on a 0.87/1.75 printer fill is agent_place_min_lot, not a copy. "
            "Does not change place, size, flatten, remint, Challenge PIDs, or persist 0.00."
        ),
    }


def maybe_run_friend_feedback(
    *,
    sit_path: Path | str | None = None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    store: LabelStore | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Host-safe observer. Default off. Never places. Never flattens. Never agent-places."""

    if not friend_feedback_enabled(environ=environ):
        return _fail(
            f"{FRIEND_FEEDBACK_ENV}_off",
            enabled=False,
            extra={"skipped": f"{FRIEND_FEEDBACK_ENV}_off"},
        )
    return run_friend_feedback(
        sit_path=sit_path,
        login=login,
        namespace=namespace,
        heartbeat_path=heartbeat_path,
        store=store,
        as_of=as_of,
        environ=environ,
    )

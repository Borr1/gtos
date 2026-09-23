"""Read-only funnel from the first Challenge fact through the fill.

One cycle, one screen: each hop's count, its error types, one example row,
and the Jev transport errors on that hop. This process only reads files.
It does not import a broker library, attach a terminal, send an order, or
write the tree it is reading.

Paths come from the command line or a host-local JSON file. The repository
copy has no account identifier and no machine path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


TRANSPORT_NAMES = (
    "WriteError",
    "LocalProtocolError",
    "ReadError",
    "JSONDecodeError",
    "timeout",
)
PIPELINE_QUESTIONS = ("last_bar", "closed_series", "placement_brake")
BOOK_INCLUDE = (
    "include_clean3",
    "include_clean4",
    "include_candidate_book",
    "include_market_expansion",
)
MANAGE_ACTS = ("move_sl", "move_tp", "close")
INTENT_FIELDS = {
    "side": ("direction", "side"),
    "limit": ("entry_price", "limit", "limit_price", "entry"),
    "stop": ("stop", "stop_price", "stop_dist", "sl"),
    "target": ("target", "target_dist", "target_price", "tp"),
    "lot": ("lot", "lots", "volume"),
}
HIDDEN_KEYS = {
    "login",
    "account",
    "account_login",
    "account_login_sha256",
    "token",
    "token_path",
    "signature",
    "api_key",
    "authorization",
    "password",
    "secret",
    "question_text",
    "instructions",
    "facts",
    "request_summary",
}
FILL_WORD = re.compile(r"(?<![A-Za-z])fill(?:ed|s)?(?![A-Za-z])", re.IGNORECASE)
RETCODE_WORD = re.compile(
    r"retcode(?:_external)?[\"']?\s*[:=]\s*(-?\d+)",
    re.IGNORECASE,
)
TERMINALS = re.compile(
    r"terminals:([A-Za-z0-9_]+=\d+(?:,[A-Za-z0-9_]+=\d+)*)"
)
LONG_DIGITS = re.compile(r"(?<![\d.])\d{8,}(?![\d.])")
TIMEOUT_WORD = re.compile(r"Timeout|timed out|jev_call_timeout")


@dataclass
class Paths:
    namespace: str
    state_dir: Path
    writer_log: Path
    launcher_log: Path
    events: Path
    activation_audit: Path

    @property
    def judgment(self) -> Path:
        return self.state_dir / "judgment"

    def record(self, name: str) -> Path:
        return self.judgment / name


@dataclass
class Hop:
    name: str
    count: int = 0
    errors: Counter = field(default_factory=Counter)
    transport: Counter = field(default_factory=lambda: Counter({name: 0 for name in TRANSPORT_NAMES}))
    example: Any = None
    notes: list[str] = field(default_factory=list)

    def add_error_name(self, name: str | None) -> None:
        kind, label = classify_error(name)
        if kind == "transport" and label is not None:
            self.transport[label] += 1
        elif kind == "error" and label is not None:
            self.errors[label] += 1

    def consider_example(self, row: Any, *, failed: bool) -> None:
        if self.example is None or (failed and not getattr(self, "_example_failed", False)):
            self.example = row
            self._example_failed = failed


def classify_error(name: str | None) -> tuple[str | None, str | None]:
    if name is None:
        return None, None
    text = str(name).strip()
    if not text or text in {"None", "null"}:
        return None, None
    if "JSONDecodeError" in text:
        return "transport", "JSONDecodeError"
    for label in ("WriteError", "LocalProtocolError", "ReadError"):
        if label in text:
            return "transport", label
    if TIMEOUT_WORD.search(text):
        return "transport", "timeout"
    return "error", text


def parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text[0].isalpha():
        return None
    matched = re.match(
        r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:[.,](\d+))?(Z|[+-]\d{2}:\d{2})?",
        text,
    )
    if matched is None:
        return None
    fraction = (matched.group(3) or "0")[:6].ljust(6, "0")
    zone = matched.group(4) or "Z"
    if zone == "Z":
        zone = "+00:00"
    try:
        return datetime.fromisoformat(
            f"{matched.group(1)}T{matched.group(2)}.{fraction}{zone}"
        ).astimezone(timezone.utc)
    except ValueError:
        return None


def scrub(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "..."
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key) in HIDDEN_KEYS:
                continue
            out[str(key)] = scrub(item, depth + 1)
        return out
    if isinstance(value, list):
        head = [scrub(item, depth + 1) for item in value[:4]]
        if len(value) > 4:
            head.append({"_more": len(value) - 4})
        return head
    if isinstance(value, str):
        return LONG_DIGITS.sub("#", value)[:240]
    return value


def dump_example(row: Any) -> str:
    if row is None:
        return "-"
    if isinstance(row, str):
        return LONG_DIGITS.sub("#", row)[:420]
    try:
        text = json.dumps(scrub(row), default=str, sort_keys=True, separators=(",", ":"))
    except TypeError:
        text = str(row)
    text = LONG_DIGITS.sub("#", text)
    if len(text) > 420:
        return text[:417] + "..."
    return text


def format_counter(counter: Counter, *, required: tuple[str, ...] = ()) -> str:
    names = list(required) + [name for name in counter if name not in required and counter[name]]
    if not names:
        return "-"
    return " ".join(f"{name}={counter[name]}" for name in names)


def render_hop(hop: Hop) -> str:
    lines = [
        f"[{hop.name}]",
        f"count={hop.count}",
        f"errors={format_counter(hop.errors)}",
        f"transport={format_counter(hop.transport, required=TRANSPORT_NAMES)}",
    ]
    for note in hop.notes:
        lines.append(note)
    lines.append(f"example={dump_example(hop.example)}")
    return "\n".join(lines)


def date_needles(start: datetime, end: datetime | None) -> list[bytes]:
    stop = end or (datetime.now(timezone.utc) + timedelta(days=1))
    day = start.date()
    last = stop.date()
    needles = []
    while day <= last:
        needles.append(day.isoformat().encode("ascii"))
        day += timedelta(days=1)
        if len(needles) > 14:
            break
    return needles


def iter_jsonl(
    path: Path,
    start: datetime,
    end: datetime | None,
    time_keys: tuple[str, ...],
) -> Iterator[tuple[datetime, dict]]:
    if not path.is_file():
        return
    needles = date_needles(start, end)
    with path.open("rb") as handle:
        for raw in handle:
            if needles and not any(needle in raw for needle in needles):
                continue
            line = raw.replace(b"\x00", b"").decode("utf-8", "replace").strip()
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            moment = None
            for key in time_keys:
                moment = parse_ts(row.get(key))
                if moment is not None:
                    break
            if moment is None or moment < start:
                continue
            if end is not None and moment >= end:
                continue
            yield moment, row


def load_cycles(path: Path, namespace: str, tail_bytes: int) -> list[tuple[datetime, dict]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    start_at = 0 if tail_bytes <= 0 else max(0, size - tail_bytes)
    found: list[tuple[datetime, dict]] = []
    needle = namespace.encode("utf-8")
    with path.open("rb") as handle:
        handle.seek(start_at)
        if start_at:
            handle.readline()
        for raw in handle:
            if needle not in raw or b'"cycle"' not in raw:
                continue
            line = raw.replace(b"\x00", b"").decode("utf-8", "replace").strip()
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            if row.get("namespace") != namespace or row.get("action") != "cycle":
                continue
            moment = parse_ts(row.get("ts"))
            if moment is None:
                continue
            found.append((moment, row))
    found.sort(key=lambda item: item[0])
    return found


def with_until(
    cycles: list[tuple[datetime, dict]],
    selected: list[tuple[datetime, dict]],
) -> list[tuple[datetime, dict]]:
    starts = [moment for moment, _row in cycles]
    out = []
    for moment, row in selected:
        later = [item for item in starts if item > moment]
        stamped = dict(row)
        stamped["_until"] = later[0] if later else None
        out.append((moment, stamped))
    return out


def iter_log(path: Path, start: datetime, end: datetime | None) -> Iterator[tuple[datetime, str]]:
    if not path.is_file():
        return
    data = path.read_bytes().replace(b"\x00", b"")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    elif data.startswith((b"\xff\xfe", b"\xfe\xff")):
        data = data[2:]
    for line in data.decode("utf-8", "replace").splitlines():
        if not line or line[0].isalpha():
            continue
        moment = parse_ts(line)
        if moment is None or moment < start:
            continue
        if end is not None and moment >= end:
            continue
        yield moment, line


def retcodes_of(text: str) -> list[str]:
    return RETCODE_WORD.findall(text)


def note_transport_text(hop: Hop, text: str) -> None:
    for name in ("WriteError", "LocalProtocolError", "ReadError", "JSONDecodeError"):
        hop.transport[name] += text.count(name)
    if TIMEOUT_WORD.search(text):
        hop.transport["timeout"] += 1


def field_present(row: dict, keys: tuple[str, ...]) -> bool:
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value is None or value == "" or value == []:
            continue
        return True
    return False


def intent_objects(cycle: dict, events: list[dict]) -> list[dict]:
    found: list[dict] = []
    for item in cycle.get("placed") or []:
        if isinstance(item, dict):
            found.append(item)
    for row in events:
        if str(row.get("event") or "") == "f5_slate":
            intents = row.get("intents")
            if isinstance(intents, list):
                found.extend(item for item in intents if isinstance(item, dict))
            continue
        if not isinstance(row, dict):
            continue
        if row.get("sleeve") and (
            row.get("direction") is not None or row.get("entry_price") is not None
        ):
            found.append(row)
    return found


def terminal_counts(reason: Any) -> dict[str, int]:
    matched = TERMINALS.search(str(reason or ""))
    if matched is None:
        return {}
    counts = {}
    for part in matched.group(1).split(","):
        name, _, raw = part.partition("=")
        try:
            counts[name] = int(raw)
        except ValueError:
            continue
    return counts


def verdicts(value: Any) -> Counter:
    found: Counter = Counter()

    def walk(node: Any, depth: int) -> None:
        if depth > 6:
            return
        if isinstance(node, dict):
            for key, item in node.items():
                if str(key) in HIDDEN_KEYS:
                    continue
                walk(item, depth + 1)
        elif isinstance(node, list):
            for item in node[:80]:
                walk(item, depth + 1)
        elif isinstance(node, str) and node.strip().upper() in {"KEEP", "KILL"}:
            found[node.strip().upper()] += 1

    walk(value, 0)
    return found


def question_hop(name: str, rows: list[dict], *, missing: str | None = None) -> Hop:
    hop = Hop(name)
    if missing:
        hop.notes.append(f"source={missing}")
    hop.count = len(rows)
    for row in rows:
        error = row.get("error")
        hop.add_error_name(None if error in (None, "") else str(error))
        hop.consider_example(
            {
                "logged_at_utc": row.get("logged_at_utc") or row.get("at_utc"),
                "question": row.get("question"),
                "choice": row.get("choice"),
                "error": row.get("error"),
                "spot": row.get("spot"),
                "symbol": row.get("symbol"),
                "decision_emitted": row.get("decision_emitted"),
            },
            failed=bool(error),
        )
    return hop


def build_report(
    paths: Paths,
    cycles: list[tuple[datetime, dict, datetime | None]],
    *,
    elapsed_s: float,
) -> str:
    blocks = [
        f"namespace={paths.namespace}",
        f"cycles={len(cycles)}",
        f"elapsed_s={elapsed_s:.3f}",
    ]
    if not cycles:
        blocks.append("no cycle in the scanned launcher tail")
        return "\n".join(blocks)
    for start, cycle, end in cycles:
        blocks.append("")
        blocks.append(render_cycle(paths, start, end, cycle))
    return "\n".join(blocks)


def render_cycle(paths: Paths, start: datetime, end: datetime | None, cycle: dict) -> str:
    pipeline = bucket(paths.record("pipeline_choices.jsonl"), start, end, ("logged_at_utc",))
    book = bucket(paths.record("book_engine_choices.jsonl"), start, end, ("logged_at_utc",))
    execution = bucket(paths.record("execution_choices.jsonl"), start, end, ("logged_at_utc",))
    manage = bucket(paths.record("manage_choices.jsonl"), start, end, ("logged_at_utc",))
    place_path = bucket(paths.record("place_path_choices.jsonl"), start, end, ("at_utc", "logged_at_utc"))
    events = [row for _moment, row in iter_jsonl(paths.events, start, end, ("ts_utc", "ts_cycle_utc", "logged_at_utc"))]
    audit = [
        row
        for _moment, row in iter_jsonl(
            paths.activation_audit, start, end, ("decided_at_utc", "logged_at_utc")
        )
        if not row.get("namespace") or row.get("namespace") == paths.namespace
    ]
    log_lines = [line for _moment, line in iter_log(paths.writer_log, start, end)]
    hops = [
        *pipeline_hops(pipeline, paths.record("pipeline_choices.jsonl")),
        *book_hops(book, paths.record("book_engine_choices.jsonl")),
        sleeve_hop(cycle, book),
        intent_hop(cycle, events),
        admission_hop(cycle),
        place_hop(cycle, place_path, paths.record("place_path_choices.jsonl")),
        execution_hop(cycle, execution, paths.record("execution_choices.jsonl")),
        *broker_hops(log_lines, execution, events, audit, paths),
        *manage_hops(manage, paths.record("manage_choices.jsonl")),
    ]
    until = end.isoformat() if end is not None else "open"
    header = f"cycle={start.isoformat()} until={until}"
    return "\n".join([header, *[render_hop(hop) for hop in hops]])


def bucket(path: Path, start: datetime, end: datetime | None, keys: tuple[str, ...]) -> list[dict]:
    return [row for _moment, row in iter_jsonl(path, start, end, keys)]


def pipeline_hops(rows: list[dict], path: Path) -> list[Hop]:
    missing = None if path.is_file() else str(path.name)
    hops = []
    for question in PIPELINE_QUESTIONS:
        chosen = [row for row in rows if row.get("question") == question]
        hops.append(question_hop(f"pipeline {question}", chosen, missing=missing))
    return hops


def book_hops(rows: list[dict], path: Path) -> list[Hop]:
    missing = None if path.is_file() else str(path.name)
    names = list(BOOK_INCLUDE) + ["last_bar", "unit"]
    extra = sorted({str(row.get("question")) for row in rows if row.get("question")} - set(names))
    hops = []
    for question in names + extra:
        chosen = [row for row in rows if row.get("question") == question]
        if question in extra and not chosen:
            continue
        label = f"book {question}"
        hops.append(question_hop(label, chosen, missing=missing))
    return hops


def sleeve_hop(cycle: dict, book_rows: list[dict]) -> Hop:
    hop = Hop("sleeves")
    counts = terminal_counts(cycle.get("reason"))
    unit_rows = [row for row in book_rows if row.get("question") == "unit"]
    if counts:
        fired = counts.get("candidate_emitted", 0)
        not_fired = sum(value for name, value in counts.items() if name != "candidate_emitted")
        hop.notes.append(
            "terminals=" + " ".join(f"{name}={value}" for name, value in sorted(counts.items()))
        )
    else:
        fired = sum(1 for row in unit_rows if row.get("choice") in {"unit_long", "unit_short"})
        not_fired = sum(1 for row in unit_rows if row.get("choice") not in {"unit_long", "unit_short"})
        hop.notes.append("terminals=absent")
    hop.count = fired + not_fired
    hop.notes.append(f"fired={fired}")
    hop.notes.append(f"not_fired={not_fired}")
    choices = Counter(str(row.get("choice")) for row in unit_rows)
    if choices:
        hop.notes.append("unit_choice=" + format_counter(choices))
    for row in unit_rows:
        hop.add_error_name(None if not row.get("error") else str(row.get("error")))
        hop.consider_example(
            {
                "question": "unit",
                "choice": row.get("choice"),
                "error": row.get("error"),
                "spot": row.get("spot"),
                "logged_at_utc": row.get("logged_at_utc"),
            },
            failed=bool(row.get("error")),
        )
    if hop.example is None:
        hop.consider_example({"reason": cycle.get("reason"), "n_intents": cycle.get("n_intents")}, failed=False)
    return hop


def intent_hop(cycle: dict, events: list[dict]) -> Hop:
    hop = Hop("intents")
    objects = intent_objects(cycle, events)
    try:
        declared = int(cycle.get("n_intents") or 0)
    except (TypeError, ValueError):
        declared = 0
    hop.count = max(declared, len(objects))
    hop.notes.append(f"n_intents={declared}")
    hop.notes.append(f"stored={len(objects)}")
    for label, keys in INTENT_FIELDS.items():
        if not objects:
            hop.notes.append(f"{label}=unset")
            continue
        present = sum(1 for row in objects if field_present(row, keys))
        hop.notes.append(f"{label}=present:{present} unset:{len(objects) - present}")
    example = objects[0] if objects else {"n_intents": declared, "stored": 0}
    hop.consider_example(example, failed=False)
    return hop


def admission_hop(cycle: dict) -> Hop:
    hop = Hop("admission")
    bridge = cycle.get("bridge") if isinstance(cycle.get("bridge"), dict) else {}
    if not bridge:
        hop.notes.append("bridge=absent")
        hop.consider_example({"reason": cycle.get("reason")}, failed=False)
        return hop
    found = verdicts(bridge)
    units = [item for item in (bridge.get("would_units") or []) if isinstance(item, dict)]
    realized = [item for item in (bridge.get("realized_units") or []) if isinstance(item, dict)]
    sized_rows = units or realized
    sized = sum(1 for item in sized_rows if item.get("sized") is True or item.get("reason") == "sized")
    status = str(bridge.get("decision_status") or "")
    kill = found["KILL"]
    held = 1 if found["KEEP"] or status == "blocked_by_governor" else 0
    hop.count = max(1, held + kill + sized + len(units))
    hop.notes.append(f"KEEP={found['KEEP']}")
    hop.notes.append(f"KILL={kill}")
    hop.notes.append(f"sized={sized}")
    hop.notes.append(f"held={held}")
    hop.notes.append(f"decision_status={status or '-'}")
    if status.startswith("fail_closed"):
        hop.errors[status] += 1
    governor = bridge.get("governor") if isinstance(bridge.get("governor"), dict) else {}
    if "allow" in governor:
        governor_allow = governor.get("allow")
    elif "allow_new_entries" in governor:
        governor_allow = governor.get("allow_new_entries")
    else:
        governor_allow = None
    hop.consider_example(
        {
            "decision_status": status,
            "reason": bridge.get("reason"),
            "would_new_entries_allowed": bridge.get("would_new_entries_allowed"),
            "governor_allow": governor_allow,
            "governor_reason": governor.get("reason"),
            "n_would_units": len(units),
            "n_realized_units": len(realized),
        },
        failed=status.startswith("fail_closed") or status == "blocked_by_governor",
    )
    return hop


def place_hop(cycle: dict, place_rows: list[dict], path: Path) -> Hop:
    hop = Hop("place")
    if not path.is_file():
        hop.notes.append(f"source={path.name} missing")
    skipped = [item for item in (cycle.get("skipped") or []) if isinstance(item, dict)]
    placed = [item for item in (cycle.get("placed") or []) if isinstance(item, dict)]
    hop.count = len(skipped) + len(placed) + len(place_rows)
    reasons = Counter(str(item.get("reason") or item.get("skip_reason") or "unset") for item in skipped)
    if reasons:
        hop.notes.append("skip_reasons=" + format_counter(reasons))
    hop.notes.append(f"placed={len(placed)}")
    for reason, count in reasons.items():
        kind, label = classify_error(reason)
        if kind == "transport" and label is not None:
            hop.transport[label] += count
        elif kind == "error" and label is not None:
            hop.errors[label] += count
    for item in skipped:
        hop.consider_example(
            {
                "symbol": item.get("symbol"),
                "sleeve": item.get("sleeve"),
                "decision_bar_iso": item.get("decision_bar_iso"),
                "reason": item.get("reason"),
            },
            failed=True,
        )
    for row in place_rows:
        hop.add_error_name(None if not row.get("error") else str(row.get("error")))
        hop.consider_example(
            {
                "at_utc": row.get("at_utc"),
                "continues": row.get("continues"),
                "send": row.get("send"),
                "reason": row.get("reason"),
                "error": row.get("error"),
            },
            failed=bool(row.get("error")),
        )
    for item in placed:
        hop.consider_example(item, failed=False)
    return hop


def execution_hop(cycle: dict, rows: list[dict], path: Path) -> Hop:
    hop = Hop("execution")
    if not path.is_file():
        hop.notes.append(f"source={path.name} missing")
    hop.count = len(rows)
    bridge = cycle.get("bridge") if isinstance(cycle.get("bridge"), dict) else {}
    risks = []
    for item in (bridge.get("would_units") or []) + (bridge.get("realized_units") or []):
        if not isinstance(item, dict):
            continue
        value = item.get("risk_pct_per_trade")
        if value is not None:
            risks.append(value)
        reason = str(item.get("reason") or "")
        if "fail" in reason.lower():
            hop.errors[reason] += 1
    if risks:
        shown = ",".join(str(item) for item in risks[:8])
        hop.notes.append(f"risk_pct_per_trade={shown}")
    else:
        hop.notes.append("risk_pct_per_trade=unset")
    if "would_total_risk_pct" in bridge:
        hop.notes.append(f"would_total_risk_pct={bridge.get('would_total_risk_pct')}")
    status = str(bridge.get("decision_status") or "")
    if status.startswith("fail_closed"):
        hop.errors[status] += 1
        hop.notes.append(f"fail_closed={status}")
    else:
        closed = [name for name in hop.errors if "fail" in name.lower()]
        hop.notes.append("fail_closed=" + (",".join(closed) if closed else "-"))
    for row in rows:
        hop.add_error_name(None if not row.get("error") else str(row.get("error")))
        choice = str(row.get("choice") or "")
        if choice in {"block", "withhold"}:
            hop.errors[f"choice:{choice}"] += 1
        hop.consider_example(
            {
                "logged_at_utc": row.get("logged_at_utc"),
                "question": row.get("question"),
                "choice": row.get("choice"),
                "parameter": row.get("parameter"),
                "score": row.get("score"),
                "error": row.get("error"),
                "symbol": row.get("symbol"),
                "reason": row.get("reason"),
            },
            failed=bool(row.get("error")) or choice in {"block", "withhold"},
        )
    return hop


def broker_hops(
    log_lines: list[str],
    execution: list[dict],
    events: list[dict],
    audit: list[dict],
    paths: Paths,
) -> list[Hop]:
    check = Hop("order_check")
    send = Hop("order_send")
    fills = Hop("fills")
    if not paths.writer_log.is_file():
        check.notes.append("writer_log=missing")
        send.notes.append("writer_log=missing")
    if not paths.activation_audit.is_file():
        send.notes.append("activation_audit=missing")
    check_codes: list[str] = []
    send_codes: list[str] = []
    for line in log_lines:
        lowered = line.lower()
        if "order_check" in lowered:
            check.count += 1
            codes = retcodes_of(line)
            check_codes.extend(codes)
            note_transport_text(check, line)
            check.consider_example(line.strip(), failed=bool(codes) or "error" in lowered)
        if "order_send" in lowered:
            send.count += 1
            codes = retcodes_of(line)
            send_codes.extend(codes)
            note_transport_text(send, line)
            send.consider_example(line.strip(), failed=True)
        if FILL_WORD.search(line) and ("retcode" in lowered or "deal" in lowered):
            fills.count += 1
            note_transport_text(fills, line)
            fills.consider_example(line.strip(), failed=False)
    for row in execution:
        if row.get("question") == "fill":
            fills.count += 1
            fills.add_error_name(None if not row.get("error") else str(row.get("error")))
            fills.consider_example(
                {
                    "question": "fill",
                    "choice": row.get("choice"),
                    "error": row.get("error"),
                    "symbol": row.get("symbol"),
                    "logged_at_utc": row.get("logged_at_utc"),
                },
                failed=bool(row.get("error")),
            )
    for row in events:
        event = str(row.get("event") or "")
        if FILL_WORD.search(event):
            fills.count += 1
            fills.add_error_name(None if not row.get("error") else str(row.get("error")))
            fills.consider_example(
                {"event": event, "symbol": row.get("symbol"), "sleeve": row.get("sleeve"), "ts_utc": row.get("ts_utc")},
                failed=bool(row.get("error")),
            )
    increasing = []
    for row in audit:
        blob = " ".join(
            str(row.get(key) or "")
            for key in ("risk_direction", "reason", "classification")
        ).lower()
        if "increas" not in blob:
            continue
        increasing.append(row)
        send.count += 1
        if row.get("allowed") is False:
            send.add_error_name(str(row.get("reason") or "audit_denied"))
        send.consider_example(
            {
                "decided_at_utc": row.get("decided_at_utc"),
                "allowed": row.get("allowed"),
                "reason": row.get("reason"),
                "risk_direction": row.get("risk_direction"),
                "classification": row.get("classification"),
                "symbol": (row.get("request_summary") or {}).get("symbol")
                if isinstance(row.get("request_summary"), dict)
                else None,
            },
            failed=row.get("allowed") is False,
        )
    check.notes.append("retcodes=" + (",".join(check_codes) if check_codes else "-"))
    send.notes.append("retcodes=" + (",".join(send_codes) if send_codes else "-"))
    send.notes.append(f"audit_increasing={len(increasing)}")
    return [check, send, fills]


def manage_hops(rows: list[dict], path: Path) -> list[Hop]:
    missing = None if path.is_file() else str(path.name)
    names = list(MANAGE_ACTS)
    extra = sorted({str(row.get("act") or row.get("choice") or "") for row in rows} - set(names) - {""})
    hops = []
    for act in names + extra:
        chosen = [row for row in rows if (row.get("act") or row.get("choice")) == act]
        hop = Hop(f"management {act}")
        if missing:
            hop.notes.append(f"source={path.name} missing")
        hop.count = len(chosen)
        sent = sum(1 for row in chosen if row.get("send") is True or row.get("agent_order_send") is True)
        hop.notes.append(f"send={sent}")
        for row in chosen:
            hop.add_error_name(None if not row.get("error") else str(row.get("error")))
            hop.consider_example(
                {
                    "logged_at_utc": row.get("logged_at_utc"),
                    "act": row.get("act"),
                    "choice": row.get("choice"),
                    "send": row.get("send"),
                    "symbol": row.get("symbol"),
                    "error": row.get("error"),
                },
                failed=bool(row.get("error")),
            )
        hops.append(hop)
    return hops


def host_paths_file() -> Path | None:
    candidates = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "gtos" / "flow_trace.paths.json")
    candidates.append(Path.home() / ".gtos" / "flow_trace.paths.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_paths_file(path: Path) -> dict:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"paths file unreadable: {path} ({exc})") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"paths file must be a JSON object: {path}")
    return loaded


def resolve_paths(args: argparse.Namespace) -> Paths:
    file_values: dict[str, Any] = {}
    if args.paths:
        file_values = load_paths_file(Path(args.paths))
    elif args.paths is None:
        found = host_paths_file()
        if found is not None:
            file_values = load_paths_file(found)
    repo = args.repo or file_values.get("repo")
    namespace = args.namespace or file_values.get("namespace")
    if repo and not namespace:
        root = Path(repo)
        books = [
            child.name
            for child in (root / "pipeline_state" / "ultimate_book").iterdir()
            if (child / "judgment" / "pipeline_choices.jsonl").is_file()
        ] if (root / "pipeline_state" / "ultimate_book").is_dir() else []
        if len(books) == 1:
            namespace = books[0]
    if not namespace:
        raise SystemExit("namespace is required (argument or host-local paths file)")

    def pick(name: str, default: Path | None) -> Path:
        raw = getattr(args, name, None) or file_values.get(name)
        if raw:
            return Path(raw)
        if default is None:
            raise SystemExit(f"{name} is required (argument or host-local paths file)")
        return default

    state_default = None
    log_default = None
    launcher_default = None
    events_default = None
    if repo:
        root = Path(repo)
        state_default = root / "pipeline_state" / "ultimate_book" / str(namespace)
        log_default = root / "shadow_logs" / "f5_verification.log"
        launcher_default = root / "shadow_logs" / "ultimate_book_launcher.jsonl"
        events_default = root / "shadow_logs" / "f5_minimal" / str(namespace) / "events.jsonl"
    audit_default = Path.home() / ".gtos" / "activation" / "activation_audit.jsonl"
    return Paths(
        namespace=str(namespace),
        state_dir=pick("state_dir", state_default),
        writer_log=pick("writer_log", log_default),
        launcher_log=pick("launcher_log", launcher_default),
        events=pick("events", events_default),
        activation_audit=pick("activation_audit", audit_default),
    )


def trace(paths: Paths, args: argparse.Namespace) -> str:
    started = time.perf_counter()
    cycles = load_cycles(paths.launcher_log, paths.namespace, int(args.tail_bytes))
    since = parse_ts(args.since) if args.since else None
    chosen_start = parse_ts(args.cycle_start) if args.cycle_start else None
    if args.cycle_start and chosen_start is None:
        raise SystemExit(f"cycle start is not a timestamp: {args.cycle_start}")
    if args.since and since is None:
        raise SystemExit(f"since is not a timestamp: {args.since}")
    if chosen_start is not None:
        selected = [
            item
            for item in cycles
            if item[0] == chosen_start
            or item[0].replace(microsecond=0) == chosen_start.replace(microsecond=0)
        ]
    elif since is not None:
        selected = [item for item in cycles if item[0] >= since]
    elif cycles:
        selected = [cycles[-1]]
    else:
        selected = []
    bounded = with_until(cycles, selected)
    rendered_cycles = []
    for moment, row in bounded:
        end = row.get("_until")
        if not isinstance(end, datetime):
            end = None
        rendered_cycles.append((moment, row, end))
    elapsed = time.perf_counter() - started
    # elapsed covers the launcher scan only; the per-cycle reads add to the
    # clock printed after the hops are built.
    text_started = time.perf_counter()
    text = build_report(paths, rendered_cycles, elapsed_s=0)
    total = elapsed + (time.perf_counter() - text_started)
    return text.replace("elapsed_s=0.000", f"elapsed_s={total:.3f}", 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print the Challenge funnel for one cycle. Read-only."
    )
    parser.add_argument("--paths", help="Host-local JSON file of paths. Not a repo file.")
    parser.add_argument("--repo", help="Checkout whose pipeline_state and shadow_logs are read.")
    parser.add_argument("--namespace", help="Book directory name under ultimate_book.")
    parser.add_argument("--state-dir", dest="state_dir")
    parser.add_argument("--writer-log", dest="writer_log")
    parser.add_argument("--launcher-log", dest="launcher_log")
    parser.add_argument("--events")
    parser.add_argument("--activation-audit", dest="activation_audit")
    parser.add_argument("--cycle-start", dest="cycle_start", help="Cycle start timestamp.")
    parser.add_argument("--since", help="Print every cycle that starts at or after this time.")
    parser.add_argument(
        "--tail-bytes",
        dest="tail_bytes",
        type=int,
        default=64 * 1024 * 1024,
        help="Bytes of the launcher log to read from the end. 0 reads the whole file.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    paths = resolve_paths(args)
    try:
        text = trace(paths, args)
    except FileNotFoundError as exc:
        sys.stderr.write(f"missing {exc}\n")
        return 1
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    if "no cycle in the scanned launcher tail" in text:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

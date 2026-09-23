"""Read research bar exports in true UTC, whatever clock they were written in.

The view layer for F7. The research archive is terabytes of CSVs whose ``time``
column is the broker server's wall clock labelled UTC, and 53 of the 96 files the
April bundle binds are evicted iCloud placeholders. Re-exporting is therefore both
expensive and partly blocked --- and it would not help anyway, because the sealed
campaign must keep reading the bytes it was sealed against.

So: **declare, don't rewrite.** Not one data byte changes. Each export directory
gains a ``<file>.timebase.json`` sidecar stating what clock its ``time`` column is
in and on what evidence, and this module is the reader that honours it. A consumer
that wants true UTC calls :func:`read_bars`; a consumer that wants the raw bytes
keeps getting them.

That is only legitimate because the offset is *deterministic*, which this programme
measured rather than assumed --- see :mod:`src.utils.broker_clock`. It is
``America/New_York + 7h``, the US DST calendar, not the EET/EEST calendar the audits
asserted. Had it turned out to be non-deterministic (a broker moving its clock
mid-history, or two brokers disagreeing) a view layer would have been unsound and
re-export would have been mandatory.

Fail-closed contract
--------------------
A file with no sidecar and no registry entry raises :class:`UndeclaredTimeBaseError`.
It does **not** default to UTC. Defaulting to UTC is precisely how F7 happened, and
a reader that silently guesses reintroduces the defect one layer up.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterator

from src.utils.broker_clock import (
    BrokerClockRule,
    NEW_YORK_PLUS_7,
    broker_naive_to_utc,
    resolve_rule,
)

__all__ = [
    "TimeBase",
    "UndeclaredTimeBaseError",
    "TimeBaseOutOfDeclaredRangeError",
    "LEGACY_DECLARATIONS",
    "SIDECAR_SUFFIX",
    "BASES",
    "timebase_for",
    "to_true_utc",
    "read_bars",
    "sidecar_path",
    "write_sidecar",
    "in_us_eu_dst_disagreement",
]

SIDECAR_SUFFIX = ".timebase.json"

TRUE_UTC = "true_utc"
BROKER_LOCAL = "broker_server_local"
#: Stamps that are broker wall clock with a EUROPEAN-calendar offset already subtracted.
#: Such a file is true UTC outside a US/EU DST disagreement window and exactly one hour
#: fast inside one, because the broker runs on the US calendar (NY+7) while the correction
#: assumed EET/EEST. It is F7's own arithmetic applied one layer up: the timestamps were
#: corrected, with the wrong calendar, rather than left raw.
#:
#: Measured on `data/historical/` 2026-07-30 (Session AV, B1600-B1612) by
#: `docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py`, which
#: tests it as a falsifiable hypothesis beside the other two rather than inferring it from
#: a residual. `research_timebase`'s own LEGACY_DECLARATIONS note used to attribute this
#: defect to the VPS copy only; this repository's copy carries it too.
BROKER_LOCAL_EU_CORRECTED = "broker_server_local_eu_calendar_corrected"

BASES = (TRUE_UTC, BROKER_LOCAL, BROKER_LOCAL_EU_CORRECTED)

_EU_ZONE = "Europe/Berlin"
_US_ZONE = "America/New_York"


class UndeclaredTimeBaseError(LookupError):
    """Raised for a data file whose time base is neither declared nor registered."""


class TimeBaseOutOfDeclaredRangeError(UndeclaredTimeBaseError):
    """Raised for a row outside the window its sidecar declares itself valid over.

    Subclasses :class:`UndeclaredTimeBaseError` deliberately: a caller that already
    fails closed on an undeclared basis keeps failing closed on a declared-but-unbounded
    row, which is the same class of ignorance about the same column.
    """


def in_us_eu_dst_disagreement(day: date) -> bool:
    """True when the US and EU DST calendars disagree on ``day``.

    Computed from the two zones, never tabulated: a hardcoded transition table is a
    calendar claim that goes stale, and this programme has already paid for one of those.
    Berlin is normally 6 h ahead of New York; in a disagreement window it is 5 h ahead.
    """
    from zoneinfo import ZoneInfo

    noon = datetime.combine(day, time(12, 0))
    ny = noon.replace(tzinfo=ZoneInfo(_US_ZONE)).utcoffset()
    eu = noon.replace(tzinfo=ZoneInfo(_EU_ZONE)).utcoffset()
    assert ny is not None and eu is not None
    return round((eu - ny).total_seconds() / 3600.0) != 6


@dataclass(frozen=True)
class TimeBase:
    """What clock a data file's timestamp column is in, and over what span."""

    basis: str  # one of BASES
    rule: BrokerClockRule | None
    source: str  # "sidecar" | "legacy_registry"
    evidence: str
    #: Inclusive bounds, in the file's OWN stamps, over which the basis was measured.
    #: ``None`` means unbounded. A file spliced from two captures --- which
    #: ``data/historical/`` is, measured --- is only honest with a bound.
    valid_from: date | None = None
    valid_through: date | None = None

    @property
    def needs_correction(self) -> bool:
        return self.basis in (BROKER_LOCAL, BROKER_LOCAL_EU_CORRECTED)

    def check_in_range(self, stamp: datetime, *, where: str = "") -> None:
        day = stamp.date()
        if self.valid_from is not None and day < self.valid_from:
            raise TimeBaseOutOfDeclaredRangeError(
                f"{where or 'stamp'} {stamp.isoformat()} precedes the declared validity start "
                f"{self.valid_from.isoformat()} for this file's time base; the bytes before it "
                "were NOT measured and reading them under this basis would be an assumption."
            )
        if self.valid_through is not None and day > self.valid_through:
            raise TimeBaseOutOfDeclaredRangeError(
                f"{where or 'stamp'} {stamp.isoformat()} is past the declared validity end "
                f"{self.valid_through.isoformat()} for this file's time base; the tail is a "
                "different capture and its clock was not established."
            )


# Directories written before the 2026-07-26 repair, with no metadata of their own.
# Keyed by the directory name as it appears in the path. Each entry is a *declaration
# about bytes already on disk*, so it carries the measurement that established it
# rather than an assumption --- run scripts/declare_research_timebase.py to re-measure
# and to write per-file sidecars, which take precedence over anything here.
LEGACY_DECLARATIONS: dict[str, tuple[str, str, str]] = {
    # dir name: (basis, server-or-empty, evidence)
    "historical_2026": (
        BROKER_LOCAL,
        "FTMO-Server3",
        "Written by scripts/export_mt5_historical.py:109,113 (fromtimestamp(ts, tz=utc), no offset). "
        "FTMO by symbol naming (GER40.cash/UK100.cash/US30.cash). Offset measured directly from the "
        "files: scripts/measure_broker_clock_offset.py --data-dir data/historical_2026 --check "
        "FTMO-Server3 reports 99.3% over 146 days, with both measured transitions falling on the US DST dates (the tool gates on the transition dates, not on the percentage).",
    ),
    # NOTE: "historical" is deliberately NOT registered. Copies of that tree disagree
    # with each other: this repo's data/historical/ is ALREADY corrected (its NYSE open
    # sits at 14:30 UTC), and the VPS copy carries an EU-CALENDAR correction that is an
    # hour wrong in every disagreement window. A blanket declaration would make
    # read_bars apply a SECOND 2-3 h shift to an already-corrected file. Leaving it
    # unregistered makes it raise, which is the correct answer for a directory whose
    # time base varies by copy: verify the specific copy with
    # scripts/measure_broker_clock_offset.py and write it a sidecar.
    "historical_2022_2023": (
        BROKER_LOCAL,
        "FTMO-Server3",
        "Written by scripts/research/extract_ohlcv_2022_2023.py:102, which copied the historical_2026 "
        "schema and its defect.",
    ),
    "multi_instrument": (
        BROKER_LOCAL,
        "FTMO-Server3",
        "Raw broker epochs. Verified over 4.25 years (2022-01-06..2026-04-03, 99,999 bars): the NYSE "
        "open sits at broker stamp 16:30 in all nine EU/US DST disagreement windows, which is the "
        "US-calendar signature and refutes the EU-calendar reading.",
    ),
}


def sidecar_path(data_path: Path | str) -> Path:
    p = Path(data_path)
    return p.with_suffix(p.suffix + SIDECAR_SUFFIX)


def _parse_day(value: object) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


def _rule_from_payload(payload: dict) -> BrokerClockRule | None:
    server = payload.get("broker_clock_server")
    if server:
        return resolve_rule(str(server))
    name = payload.get("broker_clock_rule")
    if name == NEW_YORK_PLUS_7.name:
        return NEW_YORK_PLUS_7
    return None


def timebase_for(data_path: Path | str) -> TimeBase:
    """Resolve a file's time base: sidecar first, then the legacy registry, then fail.

    Never guesses. A file this cannot resolve is a file whose timestamps mean nothing
    definite, and saying so is the whole point.
    """
    path = Path(data_path)
    side = sidecar_path(path)
    if side.is_file():
        payload = json.loads(side.read_text(encoding="utf-8"))
        basis = str(payload.get("time_column_basis") or "")
        if basis not in BASES:
            raise UndeclaredTimeBaseError(
                f"{side} declares an unrecognised time_column_basis {basis!r}; expected one of "
                f"{BASES!r}."
            )
        rule = _rule_from_payload(payload) if basis == BROKER_LOCAL else None
        if basis == BROKER_LOCAL and rule is None:
            raise UndeclaredTimeBaseError(
                f"{side} says the column is broker-local but names no resolvable clock rule; "
                "cannot correct it without one."
            )
        return TimeBase(
            basis=basis,
            rule=rule,
            source="sidecar",
            evidence=str(payload.get("broker_clock_evidence") or f"declared by {side}"),
            valid_from=_parse_day(payload.get("valid_from")),
            valid_through=_parse_day(payload.get("valid_through")),
        )

    for part in reversed(path.parts[:-1]):
        entry = LEGACY_DECLARATIONS.get(part)
        if entry is None:
            continue
        basis, server, evidence = entry
        rule = resolve_rule(server) if (basis == BROKER_LOCAL and server) else None
        return TimeBase(basis=basis, rule=rule, source="legacy_registry", evidence=evidence)

    raise UndeclaredTimeBaseError(
        f"no time base declared for {path}: no {SIDECAR_SUFFIX} sidecar beside it and no "
        f"LEGACY_DECLARATIONS entry for any parent directory. Write one with "
        f"scripts/declare_research_timebase.py. This does NOT default to UTC --- assuming UTC is "
        f"finding F7."
    )


def to_true_utc(stamp: datetime, timebase: TimeBase) -> datetime:
    """Convert one timestamp read out of a file into a true-UTC aware datetime."""
    if timebase.basis == BROKER_LOCAL_EU_CORRECTED:
        # Already corrected, with the wrong calendar. Outside a disagreement window the
        # assumed EET/EEST offset and the actual NY+7 offset coincide and the stamp is
        # already UTC; inside one the broker is at +3 while +2 was assumed, so the stamp
        # runs exactly one hour fast. Both transitions land on a Sunday morning (US
        # 07:00 UTC, EU 01:00 UTC) and spot markets are shut then, so evaluating the
        # window on the stamp's own DATE is exact for every bar that exists --- which
        # av_timebase_verify.py asserts per file rather than assuming.
        aware = stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        if in_us_eu_dst_disagreement(aware.date()):
            aware = aware - timedelta(hours=1)
        return aware.astimezone(timezone.utc)
    if not timebase.needs_correction:
        return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
    assert timebase.rule is not None  # guaranteed by timebase_for
    return broker_naive_to_utc(stamp, timebase.rule)


def read_bars(
    data_path: Path | str,
    *,
    time_column: str = "time",
    time_format: str = "%Y-%m-%d %H:%M:%S",
    timebase: TimeBase | None = None,
) -> Iterator[dict]:
    """Yield rows of a bar CSV with the timestamp corrected to true UTC.

    Each row gains two keys and keeps everything else untouched:

    ``time_utc``
        aware ``datetime`` in true UTC --- the one to compute with.
    ``time_broker_local``
        the naive broker stamp exactly as it appears in the file, so a caller can
        still reconcile against the raw bytes, a sealed receipt, or an MT5 chart.
        **None** for a file already declared ``true_utc`` --- there is no broker
        stamp in it, and returning the UTC value under that name would invite the
        reconciliation to be done against the wrong clock.

    The original ``time_column`` string is left in place. Nothing is rewritten.
    """
    path = Path(data_path)
    base = timebase or timebase_for(path)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = row.get(time_column)
            if not raw:
                continue
            try:
                stamp = datetime.strptime(raw, time_format)
            except ValueError:
                # Some exports carry ISO stamps, sometimes with an explicit offset.
                # A "+00:00"/"Z" suffix is NOT evidence of true UTC --- it is exactly
                # what `fromtimestamp(broker_epoch, tz=utc).isoformat()` emits, i.e.
                # F7's own output. The declared time base wins over the suffix; a
                # measured example is 25_data/raw/XAUUSD_M15.csv, whose Z-suffixed
                # stamps are broker time.
                stamp = datetime.fromisoformat(raw).replace(tzinfo=None)
            base.check_in_range(stamp, where=str(path))
            row["time_broker_local"] = stamp if base.needs_correction else None
            row["time_utc"] = to_true_utc(stamp, base)
            yield row


def write_sidecar(
    data_path: Path | str,
    *,
    basis: str,
    rule: BrokerClockRule | None,
    evidence: str,
    extra: dict | None = None,
    server: str | None = None,
    valid_from: date | None = None,
    valid_through: date | None = None,
) -> Path:
    """Write a ``.timebase.json`` beside a data file and return its path."""
    path = Path(data_path)
    if basis not in BASES:
        raise ValueError(f"unrecognised time_column_basis {basis!r}; expected one of {BASES!r}")
    payload: dict[str, object] = {
        "schema_version": "gtos_timebase_sidecar_v1",
        "time_column": "time",
        "time_column_basis": basis,
        "declares": path.name,
    }
    if rule is not None:
        payload.update(rule.provenance())
    # The caller's evidence wins: it is the one that records what was verified about
    # THIS directory, including "verification skipped". Applying rule.provenance()
    # afterwards used to clobber it with the rule's generic text.
    payload["broker_clock_evidence"] = evidence
    if server:
        payload["broker_clock_server"] = server
    if valid_from is not None:
        payload["valid_from"] = valid_from.isoformat()
    if valid_through is not None:
        payload["valid_through"] = valid_through.isoformat()
    if extra:
        payload.update(extra)
    out = sidecar_path(path)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out

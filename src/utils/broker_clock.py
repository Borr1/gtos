"""Broker server clock -> true UTC, with declared provenance.

Why this exists
---------------
MT5 reports bar and tick timestamps in the **broker server's wall clock**, not in
UTC. ``datetime.fromtimestamp(rec["time"], tz=timezone.utc)`` therefore produces a
datetime that *claims* to be UTC and is not: it is the broker's local clock wearing
a UTC label. That is finding F7, and it is what
``scripts/export_mt5_research_ohlcv.py`` and ``scripts/export_mt5_historical.py``
did for the whole research bar archive.

The live path already corrects this by **detecting** the offset from a fresh tick
(``src/mt5/mt5_real.py`` ``_detect_offset_from_tick`` / ``_broker_epoch_to_utc``).
Offline correction of *historical* data cannot detect from a live tick, because the
offset at the time of a 2024 bar is not the offset now. It needs a **calendar rule**.

The calendar rule, measured
---------------------------
The rule is NOT the EET/EEST (European) calendar, which is what
``SECOND_AUDIT.md`` F7, ``FULL_VISION_PLAN.md`` item 5 and
``scripts/session_volatility_monitor.py`` all assume. FTMO-Server3 keeps its
midnight pinned to the FX close (17:00 New York) year-round, so its UTC offset
switches on the **US** DST dates, not the European ones:

    broker server wall clock == America/New_York wall clock + 7 hours

which yields UTC+2 while New York is on EST and UTC+3 while New York is on EDT.
The two calendars disagree for ~3 weeks each spring (US springs forward first) and
~1 week each autumn (EU falls back first). Applying the European calendar puts
those windows off by exactly one hour --- and the spring window
2026-03-08..2026-03-28 lies inside the sealed March challenge month.

Measured on exchange-anchored instruments in ``data/historical_2026/``, whose cash
opens are fixed points in *their own* exchange's calendar, so the broker stamp of
an exchange open reads the broker offset directly:

============  ===========================  =====================================
Instrument    Anchor                       Observed broker stamp of the open
============  ===========================  =====================================
JP225         Tokyo 09:00 JST (no DST)     02:00 through 2026-03-06;
                                           03:00 from 2026-03-09 onward
GER40/UK100   Frankfurt 09:00 / London     10:00 when EU and US seasons agree;
              08:00 (European DST)         11:00 during both disagreement windows
                                           (2025-10-27..31, 2026-03-09..27)
SPX500/US30   NYSE 09:30 New York          16:30 year-round, across both
NAS100        (US DST)                     transitions --- i.e. it never moves
                                           relative to New York
============  ===========================  =====================================

Every one of those observations is reproduced exactly by ``NEW_YORK_PLUS_7``.
``scripts/measure_broker_clock_offset.py`` re-runs the measurement from the data.

Conventions
-----------
* ``fold``/ambiguity: both US transitions occur at 02:00 New York on a Sunday,
  inside the FX weekend (Friday 17:00 NY -> Sunday 17:00 NY), so **for FX, metals
  and index CFDs** no bar or tick can land in a repeated or skipped hour. That is
  NOT true for crypto: BTCUSD and ETHUSD are in the 24-symbol surface and trade
  through the weekend, so the repeated broker hour is genuinely reachable for them
  (measured: ``data/historical_2026/BTCUSD_M15.csv`` carries Sunday bars). The
  functions below are total and reproduce ``fold=0``: a repeated wall time resolves
  to its first, pre-transition occurrence. Note the separate consequence for the
  exporters --- MT5 hands back the same broker epoch twice in that hour, so the
  ``by_time`` dedup keeps one of the two. That is a property of broker-epoch data,
  not of this module, and it is why ``ts_msc``/raw epochs are preserved alongside
  the corrected stamps.
* Unknown servers **fail closed**. Guessing a clock is how this defect was
  introduced; an undeclared offset is the same defect wearing a correction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

__all__ = [
    "BrokerClockRule",
    "UnknownBrokerClockError",
    "UnsupportedBrokerClockDateError",
    "UsDstAnchor",
    "NEW_YORK_PLUS_7",
    "SERVER_CLOCK_RULES",
    "resolve_rule",
    "offset_seconds_at_broker_time",
    "offset_seconds_at_utc",
    "broker_naive_to_utc",
    "broker_epoch_to_utc",
    "utc_to_broker_naive",
    "daily_reset_instant_utc",
    "fixed_offset_rule",
]


# ---------------------------------------------------------------------------
# The US DST calendar, arithmetically --- deliberately NOT via zoneinfo.
# ---------------------------------------------------------------------------
#
# An earlier draft of this module used ``ZoneInfo("America/New_York")``. That is
# correct on this Mac and a LIVE HAZARD on the production host: Windows ships no IANA
# tz database, so ZoneInfo needs the ``tzdata`` PyPI package, which is not in
# requirements.txt and is no longer a transitive pandas dependency. On the VPS the live
# ``fx_jpy`` sleeve would then raise on every bar, and ``fx_jpy`` fails closed to no-trade;
# ``metals.py:154-161`` instead swallows the exception into ``session_hour = None``.
#
# CORRECTED 2026-07-26 at integration review. An earlier version of this comment said a
# missing package would have *loosened* the A8 gate, quoting ``metals.py:146``'s docstring
# ("the gate then admits-as-today for the missing condition"). That docstring is
# misleading and the direction is backwards: ``metals_confluence_gate.py:51`` evaluates
# ``asian = (session_hour is not None and 0 <= session_hour <= 6)``, so ``None`` scores
# the condition FALSE, lowering the confluence score. Measured: a 3/4 admit becomes a 2/4
# reject at the ``K_REQUIRED = 3`` boundary. It TIGHTENS the gate, and today it changes
# nothing at all because the gate ships ``enabled=False``. The dependency still had to go
# --- an exception on every bar is its own outage --- but the severity was overstated.
#
# The rule is four lines of arithmetic and has been stable since the Energy Policy Act
# of 2005 took effect in 2007, so it is computed directly here. ``tests/
# test_broker_clock_truth.py`` cross-checks every hour of 2022-2028 against zoneinfo
# when tzdata happens to be available, so the two can never silently diverge.


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The ``n``-th ``weekday`` (Mon=0 .. Sun=6) of a month."""
    day = date(year, month, 1)
    day += timedelta(days=(weekday - day.weekday()) % 7)
    return day + timedelta(weeks=n - 1)


def _us_dst_window_utc(year: int) -> tuple[datetime, datetime]:
    """UTC instants at which US daylight time starts and ends in ``year``.

    The Energy Policy Act rule applies from 2007: 2nd Sunday in March through the
    1st Sunday in November.  The Uniform Time Act rule in force for the historical
    archive from 1987 through 2006 used the 1st Sunday in April through the last
    Sunday in October.  Both changes occur at 02:00 New York local time, hence
    07:00 UTC on entry (standard, UTC-5) and 06:00 UTC on exit (daylight, UTC-4).

    Earlier dates deliberately refuse.  The United States used multiple earlier
    rule regimes and the repository has no broker measurement authorising one of
    them for this server.  Applying either later calendar before 1987 would turn an
    unknown into a precise-looking, wrong timestamp.
    """
    if year < 1987:
        raise UnsupportedBrokerClockDateError(
            f"America/New_York broker-clock conversion is unsupported before 1987 "
            f"(requested {year}); no source-backed historic rule is registered."
        )
    if year >= 2007:
        start = _nth_weekday(year, 3, 6, 2)
        end = _nth_weekday(year, 11, 6, 1)
    else:
        start = _nth_weekday(year, 4, 6, 1)
        end = _last_weekday(year, 10, 6)
    return (
        datetime(start.year, start.month, start.day, 7, tzinfo=timezone.utc),
        datetime(end.year, end.month, end.day, 6, tzinfo=timezone.utc),
    )


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """The last ``weekday`` (Mon=0 .. Sun=6) of a month."""
    day = date(year, month, 1) + timedelta(days=32)
    day = date(day.year, day.month, 1) - timedelta(days=1)          # last day of `month`
    return day - timedelta(days=(day.weekday() - weekday) % 7)


def _eu_dst_window_utc(year: int) -> tuple[datetime, datetime]:
    """UTC instants at which EU summer time starts and ends in ``year``.

    The EU rule is defined directly in UTC: 01:00 UTC on the last Sunday of March to 01:00
    UTC on the last Sunday of October, so unlike the US rule it needs no local-offset step.

    This is a DIFFERENT calendar from the US one above, and the difference is the whole
    reason both exist here. They disagree for ~3 weeks each spring (the US springs forward
    first) and ~1 week each autumn (the EU falls back first). FTMO's MT5 **server** follows
    the US calendar (measured, see :data:`NEW_YORK_PLUS_7`) while FTMO's **daily-loss reset
    rule** is stated in CE(S)T, which follows this one. Conflating them is a 1-2 h error in
    the reset window every night.
    """
    start = _last_weekday(year, 3, 6)
    end = _last_weekday(year, 10, 6)
    return (
        datetime(start.year, start.month, start.day, 1, tzinfo=timezone.utc),
        datetime(end.year, end.month, end.day, 1, tzinfo=timezone.utc),
    )


class EuDstAnchor:
    """Central-European offset arithmetic (CET/CEST), with no external data dependency."""

    @staticmethod
    def is_summer(instant_utc: datetime) -> bool:
        start, end = _eu_dst_window_utc(instant_utc.year)
        return start <= instant_utc < end


class UsDstAnchor:
    """New-York-anchored offset arithmetic, with no external data dependency."""

    @staticmethod
    def is_daylight(instant_utc: datetime) -> bool:
        start, end = _us_dst_window_utc(instant_utc.year)
        return start <= instant_utc < end


class UnknownBrokerClockError(LookupError):
    """Raised when a server name has no measured clock rule.

    Deliberately fatal. The caller must either register a measured rule or pass an
    explicit :func:`fixed_offset_rule`; silently assuming an offset is the defect
    this module exists to remove.
    """


class UnsupportedBrokerClockDateError(UnknownBrokerClockError):
    """A registered rule has no source-backed calendar for the requested date."""


@dataclass(frozen=True)
class BrokerClockRule:
    """How one broker server's wall clock relates to UTC.

    Two kinds are supported:

    ``anchor``
        The server tracks another timezone at a constant displacement. This is the
        common MT5 convention: pin server midnight to the FX close so the daily bar
        boundary never moves relative to the market. ``anchor_zone`` +
        ``anchor_offset_hours`` fully determine the offset for every instant,
        including across that anchor zone's DST transitions.

    ``fixed``
        A constant UTC offset with no DST at all (some brokers, and useful for
        tests and for an operator override).
    """

    name: str
    kind: str  # "anchor" | "fixed"
    evidence: str
    anchor_zone: str | None = None
    anchor_offset_hours: float | None = None
    fixed_offset_hours: float | None = None
    aliases: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if self.kind == "anchor":
            if not self.anchor_zone or self.anchor_offset_hours is None:
                raise ValueError(f"{self.name}: anchor rule needs anchor_zone and anchor_offset_hours")
        elif self.kind == "fixed":
            if self.fixed_offset_hours is None:
                raise ValueError(f"{self.name}: fixed rule needs fixed_offset_hours")
        else:
            raise ValueError(f"{self.name}: unknown kind {self.kind!r}")

    def provenance(self) -> dict[str, object]:
        """The block an exporter writes into its manifest.

        An export that carries this is self-describing: a reader a year from now can
        tell what was applied and on what evidence, without reading this source.
        """
        payload: dict[str, object] = {
            "broker_clock_rule": self.name,
            "broker_clock_kind": self.kind,
            "broker_clock_evidence": self.evidence,
        }
        if self.kind == "anchor":
            payload["broker_clock_anchor_zone"] = self.anchor_zone
            payload["broker_clock_anchor_offset_hours"] = self.anchor_offset_hours
        else:
            payload["broker_clock_fixed_offset_hours"] = self.fixed_offset_hours
        return payload


NEW_YORK_PLUS_7 = BrokerClockRule(
    name="new_york_plus_7",
    kind="anchor",
    anchor_zone="America/New_York",
    anchor_offset_hours=7.0,
    evidence=(
        "Measured 2026-07-26 on three independent exchange calendars plus two non-broker "
        "references. Exchange-anchored step probe: the winter/disagree/summer signature is "
        "02:00/03:00/03:00 for JP225 (Tokyo, no DST) and 10:00/11:00/10:00 for GER40+UK100, "
        "while NYSE-anchored SPX500/US30_cash/NAS100 never move -- non-monotone, which "
        "refutes the EU calendar and a broker-fixed artifact simultaneously. Over 4.25 years "
        "of raw broker stamps (2022-01..2026-04, 99,999 bars) all NINE transitions fall on "
        "the US DST date and none on an EU date. Confirmed against UTC-native Sierra Chart "
        "CME/COMEX futures by return cross-correlation (+3.00 h inside 2026-03-09..27, five "
        "instrument pairs) and against a second broker's EU-calendar archive (FTMO leads it "
        "by exactly 1 h in exactly the disagreement windows). Reproduce with "
        "scripts/measure_broker_clock_offset.py. NOT the EET/EEST calendar asserted by "
        "SECOND_AUDIT.md F7, FULL_VISION_PLAN.md item 5, and "
        "scripts/session_volatility_monitor.py:39-44."
    ),
    aliases=(
        "FTMO-Server3", "FTMO-Server", "FTMO-Demo", "FTMO",
        # redacted_account registered 2026-07-26 on VPS measurement. Session B deliberately REFUSED to
        # resolve it, because its calendar was unmeasured and no redacted_account-attributed data spanned
        # a disagreement window -- refusing was right then. It has since been measured on the VPS
        # from 81 weekly session boundaries per broker (M15, 2025-01-01..2026-07-26, EURUSD and
        # USDJPY): redacted_account-Server 2 and FTMO-Server3 are IDENTICAL across all 81 weeks and all
        # three transitions (2025-03-09, 2025-11-02, 2026-03-08), every one a US DST date and none
        # an EU one. Both stamp the week open at Monday 00:00:00 broker time in every week of the
        # sample, which is the signature of a server pinned to the 17:00 New York FX close.
        # Live-tick cross-check: FTMO +3.00000 h measured directly; redacted_account's live tick is
        # INVALID for this purpose (its BTCUSD stops quoting at the weekend), so its +3 comes from
        # the session-boundary calendar, which needs no fresh tick.
        # NOTE: this is the SERVER clock only. redacted_account's DAILY-RESET rule is server midnight,
        # which is a different question -- see DAILY_RESET_RULES and EUROPE_PRAGUE.
        "redacted_account-Server 2", "redacted_account-Server2", "redacted_account-Server", "redacted_account",
    ),
)


EUROPE_PRAGUE = BrokerClockRule(
    name="europe_prague",
    kind="anchor",
    anchor_zone="Europe/Prague",
    anchor_offset_hours=0.0,
    evidence=(
        "CET/CEST. NOT a broker server clock -- this is the calendar FTMO states its "
        "DAILY-LOSS RESET rule in: 'the Maximum Daily Loss resets every midnight CE(S)T' "
        "(academy.ftmo.com/lesson/maximum-daily-loss/, and recorded in this repo at "
        "config/profiles/ftmo.yaml:102 as daily_reset_time: 00:00 CE(S)T). FTMO's MT5 "
        "server runs the US calendar instead (NEW_YORK_PLUS_7), so the reset instant and "
        "the bar clock are 1 h apart normally and 2 h apart during the ~4 weeks a year the "
        "US and EU calendars disagree. redacted_account is different again and resets at 00:00 "
        "SERVER time (help.redacted_account.com/en/articles/8394309), i.e. it needs no rule here."
    ),
    aliases=("Europe/Prague", "CET", "CEST", "CE(S)T"),
)


# Daily-reset calendars, keyed by the profile's declared rule name. This is deliberately a
# SEPARATE registry from SERVER_CLOCK_RULES: a prop firm's reset rule and its MT5 server clock
# are different things and this programme already conflated them once.
DAILY_RESET_RULES: dict[str, BrokerClockRule] = {
    alias.lower(): EUROPE_PRAGUE
    for alias in (EUROPE_PRAGUE.name, *EUROPE_PRAGUE.aliases)
}


def daily_reset_offset_hours(instant_utc: datetime, rule_name: str | None) -> float | None:
    """Offset from UTC, in hours, of the daily-reset calendar named by ``rule_name``.

    Returns ``None`` when ``rule_name`` is falsy or names the broker's own server clock -- the
    caller should then use the live-detected server offset, which is what redacted_account's rule
    ("00:00 server time") actually requires. Raises for an unrecognised name rather than
    silently falling back, because a wrong reset window is invisible until it costs money.
    """
    if not rule_name:
        return None
    key = str(rule_name).strip().lower()
    if key in {"server", "broker_server", "server_time", "mt5_server"}:
        return None
    rule = DAILY_RESET_RULES.get(key)
    if rule is None:
        raise UnknownBrokerClockError(
            f"no daily-reset calendar named {rule_name!r}. Known: "
            f"{sorted(DAILY_RESET_RULES)}, plus 'server' for brokers that reset at server "
            "midnight. Register the rule with the firm's own documentation as evidence; "
            "do not guess a reset window."
        )
    return offset_seconds_at_utc(instant_utc, rule) / 3600.0


# Keyed by MT5 ``account_info().server`` / ``terminal_info()`` server string, and by
# the coarse broker name. Lookup is case-insensitive. Add an entry only with the
# measurement that established it, in ``evidence``.
SERVER_CLOCK_RULES: dict[str, BrokerClockRule] = {
    alias.lower(): NEW_YORK_PLUS_7 for alias in NEW_YORK_PLUS_7.aliases
}


def fixed_offset_rule(hours: float, *, evidence: str) -> BrokerClockRule:
    """Build an explicit constant-offset rule (operator override, or a test double)."""
    return BrokerClockRule(
        name=f"fixed_utc_plus_{hours:g}".replace("-", "minus_"),
        kind="fixed",
        fixed_offset_hours=hours,
        evidence=evidence,
    )


def resolve_rule(server: str | None) -> BrokerClockRule:
    """Look up the measured clock rule for an MT5 server name.

    Raises :class:`UnknownBrokerClockError` for anything unmeasured. Fail closed is
    the point: a wrong offset is silent and survives every existing test.
    """
    if not server:
        raise UnknownBrokerClockError(
            "no broker server name supplied; cannot resolve a clock rule. Pass the MT5 "
            "account_info().server string, or an explicit fixed_offset_rule()."
        )
    rule = SERVER_CLOCK_RULES.get(str(server).strip().lower())
    if rule is None:
        known = sorted(SERVER_CLOCK_RULES)
        raise UnknownBrokerClockError(
            f"no measured broker clock rule for server {server!r}. Known: {known}. "
            "Measure it with scripts/measure_broker_clock_offset.py and register it, or "
            "pass an explicit fixed_offset_rule(); do not guess."
        )
    return rule


def _anchor_offset_hours_at_utc(instant_utc: datetime, rule: BrokerClockRule) -> float:
    """The broker's offset from UTC, in hours, at a true-UTC instant."""
    assert rule.anchor_offset_hours is not None
    if rule.anchor_zone == "America/New_York":
        base, summer = -5.0, UsDstAnchor.is_daylight(instant_utc)
    elif rule.anchor_zone == "Europe/Prague":
        base, summer = 1.0, EuDstAnchor.is_summer(instant_utc)
    else:  # pragma: no cover - only the two registered zones
        raise UnknownBrokerClockError(
            f"{rule.name}: no arithmetic DST rule for anchor zone {rule.anchor_zone!r}. "
            "Add one here rather than reaching for zoneinfo --- the live host has no IANA "
            "tz database (see the module header)."
        )
    return rule.anchor_offset_hours + base + (1.0 if summer else 0.0)


def broker_naive_to_utc(broker_wall: datetime, rule: BrokerClockRule) -> datetime:
    """Convert a broker wall-clock datetime to a true-UTC aware datetime.

    ``broker_wall`` is what MT5 hands you once decoded --- naive, or bearing a
    (wrong) UTC tzinfo from ``fromtimestamp(..., tz=utc)``. Either is accepted; any
    tzinfo present is discarded, because it is exactly the mislabel being repaired.

    Inversion is by candidate check. For the **repeated** wall time (autumn fall-back)
    this reproduces ``fold=0`` exactly: it validates under both offsets and the first
    tried --- ``+3``, the pre-transition one --- wins. Repeated hours ARE reachable:
    BTCUSD/ETHUSD trade through the weekend the transition falls in. See the module header.

    A **non-existent** wall time (the spring-forward gap, broker wall 09:00-09:59 on the
    US transition Sunday) validates under neither candidate and falls through to ``+3``.
    NOTE, corrected 2026-07-26: that is the *post*-transition offset, so such an input maps
    BACKWARD into the pre-gap hour rather than forward past it, which is the opposite of
    what ``fold=0`` does for a non-existent local time. It is left as-is deliberately: MT5
    never emits a wall time its own clock skipped, so the branch is unreachable from broker
    data and only a synthetic caller can hit it. Do not rely on this case.
    """
    naive = broker_wall.replace(tzinfo=None)
    if rule.kind == "fixed":
        assert rule.fixed_offset_hours is not None
        return (naive - timedelta(hours=rule.fixed_offset_hours)).replace(tzinfo=timezone.utc)
    # Candidates in pre-transition-first order so ties resolve like fold=0.
    for candidate in (3.0, 2.0):
        instant = (naive - timedelta(hours=candidate)).replace(tzinfo=timezone.utc)
        if _anchor_offset_hours_at_utc(instant, rule) == candidate:
            return instant
    return (naive - timedelta(hours=3.0)).replace(tzinfo=timezone.utc)


def broker_epoch_to_utc(broker_epoch: float, rule: BrokerClockRule) -> datetime:
    """Convert a raw MT5 epoch (``rec["time"]``, ``tick.time_msc / 1000``) to true UTC.

    MT5's epoch is constructed so that decoding it *as UTC* yields the broker's wall
    clock. So: decode as UTC, then treat the result as a wall clock.
    """
    wall = datetime.fromtimestamp(broker_epoch, tz=timezone.utc).replace(tzinfo=None)
    return broker_naive_to_utc(wall, rule)


def utc_to_broker_naive(instant: datetime, rule: BrokerClockRule) -> datetime:
    """Inverse of :func:`broker_naive_to_utc`: true UTC -> broker wall clock.

    Needed to build request windows: ``copy_rates_range`` bounds are compared
    against broker-localized bar epochs, so a true-UTC window must be translated
    before it is sent, or the exported range is silently shifted by the offset.
    """
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    instant = instant.astimezone(timezone.utc)
    if rule.kind == "fixed":
        assert rule.fixed_offset_hours is not None
        return (instant + timedelta(hours=rule.fixed_offset_hours)).replace(tzinfo=None)
    hours = _anchor_offset_hours_at_utc(instant, rule)
    return (instant + timedelta(hours=hours)).replace(tzinfo=None)


def offset_seconds_at_utc(instant: datetime, rule: BrokerClockRule) -> int:
    """Broker offset in seconds (broker wall clock minus UTC) at a true-UTC instant.

    Unambiguous: a UTC instant always has exactly one offset. Prefer this over
    :func:`offset_seconds_at_broker_time` whenever you hold a true-UTC value, because
    the broker-wall-clock form is ambiguous in the repeated autumn hour.
    """
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    instant = instant.astimezone(timezone.utc)
    if rule.kind == "fixed":
        assert rule.fixed_offset_hours is not None
        return int(round(rule.fixed_offset_hours * 3600))
    return int(round(_anchor_offset_hours_at_utc(instant, rule) * 3600))


def daily_reset_instant_utc(
    now: datetime,
    rule_name: str | None,
    server_offset_hours: float | None = None,
) -> datetime | None:
    """UTC instant at which this account's current daily-loss day began.

    ``rule_name`` is the account's own reset calendar. FTMO's profile names
    Europe/Prague (00:00 CE(S)T). redacted_account names the server clock: pass no
    calendar and supply the live server offset. A missing rule does not guess
    an hour.
    """

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    try:
        offset = daily_reset_offset_hours(now, rule_name)
    except UnknownBrokerClockError:
        return None
    if offset is None:
        if server_offset_hours is None:
            return None
        try:
            offset = float(server_offset_hours)
        except (TypeError, ValueError):
            return None
        if offset != offset or offset in (float("inf"), float("-inf")):
            return None
    local_now = now + timedelta(hours=float(offset))
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = local_midnight - timedelta(hours=float(offset))
    try:
        offset_at_start = daily_reset_offset_hours(start, rule_name)
    except UnknownBrokerClockError:
        return None
    if offset_at_start is None:
        offset_at_start = offset
    if offset_at_start != offset:
        start = local_midnight - timedelta(hours=float(offset_at_start))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return start.astimezone(timezone.utc)


def offset_seconds_at_broker_time(broker_wall: datetime, rule: BrokerClockRule) -> int:
    """Broker offset in seconds, given a broker wall-clock datetime.

    This is the form an exporter needs: it holds broker stamps, not UTC instants.
    """
    true_utc = broker_naive_to_utc(broker_wall, rule)
    return int(round((broker_wall.replace(tzinfo=None) - true_utc.replace(tzinfo=None)).total_seconds()))

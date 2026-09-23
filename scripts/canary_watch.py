#!/usr/bin/env python3
"""The canary page: one command, one page, five questions.

**Read-only and broker-free.** Imports no MT5 module, opens no connection, and
writes only the report file it is asked to write. It reads config, the packet
stream, a fills file and an account-state file, and prints a page.

Designed for how the owner actually works: a terminal, over SSH, no dashboard
server, no browser. `python3 scripts/canary_watch.py` prints the page; `-o FILE`
also writes it; `--json FILE` writes the machine-readable version.

The five questions
------------------
1. **Is it armed?**   the four authority gates AND the activation token, with
   `ABSENT` reported as its own state rather than folded into `false`.
2. **Did it trade?**  fills, and — separately — whether the book is still alive.
3. **Cost vs predicted?**  every fill priced against `BROKER_TRUE_COSTS_V1.json`.
4. **Drawdown headroom?**  to the static floor and to today's daily limit, on
   each firm's own reset calendar.
5. **Still exactly three sleeves?**  resolved through the live resolvers.

Question 5 is not paranoia and it is not hypothetical. Measured 2026-07-29:
`config/agent_config.yaml` at HEAD resolves to **29** sleeves, and so does the
VPS-exported config of 2026-07-25. Among the 26 extras are `idxrev`, `fx_jpy`
and `fx_jpy_ny` — the sleeves measured as dead. No confidence floor exists
anywhere in this repository.

Every alert this page can raise is pre-registered in
`docs/audits/fable5-vision-audit-20260725/phase4/CANARY_STOP_CONDITIONS_V1.json`,
committed before the first live fill. None of them halts anything: the owner
declined automatic stop conditions and follows it himself, so each resolves to a
message addressed to him.

Provenance is printed for every number. A figure this tool was *told* is marked
`[input]`; a figure it computed from a file is marked `[measured]`. The
distinction matters: several of the balance figures in circulation are claims,
not measurements, and a page that renders both in the same typeface invites the
reader to trust the wrong one.

Exit codes: 0 = no alert; 1 = at least one alert; 2 = cannot evaluate.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SPEC_PATH = (REPO / "docs/audits/fable5-vision-audit-20260725/phase4"
             / "CANARY_STOP_CONDITIONS_V1.json")
DEFAULT_CONFIG = REPO / "config" / "agent_config.yaml"
DEFAULT_PACKETS = REPO / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"

CRITICAL, HIGH, MEDIUM, INFO = "CRITICAL", "HIGH", "MEDIUM", "INFO"
_RANK = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, INFO: 3}

GATE_KEYS = (
    "ultimate_book_enabled",
    "ultimate_book_apply_to_execution",
    "ultimate_book_live_activation_allowed",
    "ultimate_book_live_broker_authority",
)


class Alert:
    __slots__ = ("condition", "severity", "headline", "detail")

    def __init__(self, condition, severity, headline, detail=""):
        self.condition, self.severity = condition, severity
        self.headline, self.detail = headline, detail

    def to_dict(self):
        return {"condition": self.condition, "severity": self.severity,
                "headline": self.headline, "detail": self.detail}


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def condition(spec: dict, cid: str) -> dict:
    for c in spec["conditions"]:
        if c["id"] == cid:
            return c
    raise KeyError(f"condition {cid} is not in the pre-registered spec")


def _open(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open(
        "r", encoding="utf-8")


def read_jsonl(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    rows = []
    with _open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def parse_utc(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def runtime_block(config_path: Path) -> tuple[dict, str | None]:
    """The config sub-dict carrying the ultimate_book keys, whatever its nesting."""

    import yaml
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"

    def find(node):
        if isinstance(node, dict):
            if "ultimate_book_enabled" in node:
                return node
            for value in node.values():
                found = find(value)
                if found is not None:
                    return found
        return None

    block = find(loaded)
    if block is None:
        return {}, "no ultimate_book_enabled key anywhere in this config"
    return block, None


# --------------------------------------------------------------------------
# Q1 — is it armed?
# --------------------------------------------------------------------------


def check_arming(spec, cfg, cfg_error, account_digest, token_dir, now):
    """Gates + token. `ABSENT` is reported as its own state, never as `false`.

    The distinction is load-bearing here. `ultimate_book_live_broker_authority`
    is **absent** from mainline `config/agent_config.yaml` and **explicitly
    false** in the VPS export. CLAUDE.md section 4 describes the brake as "three
    false YAML booleans"; on mainline only one of the three is false, one is
    true, and one does not exist. Rendering absence as false would make a fresh
    clone look like the VPS.
    """

    from src.safety import activation_token as at

    report = {"config_error": cfg_error, "gates": {}, "token": None, "armed": None}
    alerts = []

    if cfg_error:
        alerts.append(Alert("C5", CRITICAL, "Gate state UNVERIFIABLE — this is not all-clear",
                            f"config could not be read: {cfg_error}"))
        return report, alerts

    for key in GATE_KEYS:
        report["gates"][key] = "ABSENT" if key not in cfg else cfg[key]

    try:
        state = at.describe_activation_state(account_digest, directory=token_dir, now=now)
    except Exception as exc:  # noqa: BLE001
        state = {"error": f"{type(exc).__name__}: {exc}", "tokens": []}
    report["token"] = state

    valid = [t for t in state.get("tokens", [])
             if t.get("account_login_sha256") == account_digest and t.get("valid")]
    report["token_valid_for_armed_account"] = bool(valid)
    report["token_expires_utc"] = valid[0].get("expires_utc") if valid else None

    live_allowed = cfg.get("ultimate_book_live_activation_allowed") is True
    broker_authority = cfg.get("ultimate_book_live_broker_authority") is True
    report["armed"] = bool(live_allowed and broker_authority and valid)

    # An armed book with no token trades nothing and will look broken at 3 a.m.
    if (live_allowed or broker_authority) and not valid:
        alerts.append(Alert(
            "C5", CRITICAL,
            "Authority gates are LIVE but no valid activation token exists for this account",
            f"token_dir={state.get('token_dir')}; nothing exposure-increasing can be sent. "
            "This is fail-closed, but it is also indistinguishable from a dead book unless "
            "you read this line."))
    if valid and not (live_allowed and broker_authority):
        expires = report["token_expires_utc"]
        alerts.append(Alert(
            "C5", HIGH,
            "A valid activation token exists while the authority gates are NOT live",
            f"token expires {expires}. Harmless — the gates are the outer brake — but a "
            "standing authorization nobody is using is one config edit away from being used."))

    # The gate tripwire's own question, asked here so it does not live only in a daemon.
    if report["armed"]:
        expected = spec and condition(spec, "C5")["expected_gates_when_armed"]
    else:
        expected = spec and condition(spec, "C5")["expected_gates_when_not_armed"]
    for key, want in (expected or {}).items():
        got = report["gates"].get(key, "ABSENT")
        if got != want:
            alerts.append(Alert(
                "C5", CRITICAL, f"Authority gate {key} is {got!r}, pre-registered {want!r}",
                "If this was not you, treat it as an incident."))
    return report, alerts


# --------------------------------------------------------------------------
# Q5 — is the book still exactly three sleeves?
# --------------------------------------------------------------------------


DEAD_SLEEVES = ("idxrev", "fx_jpy", "fx_jpy_ny")


def check_book_composition(spec, cfg, cfg_error, launch_tags=None):
    """Which sleeves can actually put an order on the account?

    **Answering this by reading the include flags is wrong, and answering it from
    `active_specs` alone is also wrong.** The live chain is three steps, and the
    first version of this check modelled only the middle one:

    1. `active_specs(tags, ...)` builds the raw spec list — **32** at HEAD.
    2. `book_engine.py:426` computes `_active_sleeve_names()`, which is
       `admission.effective_registry(...)` called with **all six** parameters,
       and `:452-453` drops every spec not in it. The comment there names the
       reason (DF-1): a sleeve dropped from the book must not generate, or its
       phantom firing inflates the Kelly-lite conviction count and over-sizes the
       real units. That filter removes 3, leaving **29**.
    3. `run_book.py --tags` narrows step 1's input, and is the only thing that
       can express a book smaller than the registry.

    Two mistakes the first version made, both found by an adversarial refuter and
    both shipped as CRITICAL/HIGH alerts before they were caught:

    * it passed the **raw** `market_expansion_sleeves` (`[]` -> `None`) to
      `active_specs`, while both live callers resolve the named policy first
      (`launcher.py:99-102`, `book_engine.py:435`/`:450`). That silently dropped
      all **12** `mx_*` sleeves from the operator's list of what is armed — the
      half of the book he would least expect and most want to see.
    * it never applied step 2, so it reported "20 sleeves can generate orders"
      when the true figure is 29, and raised a **false** HIGH claiming three
      clean_3 sleeves generate without a sizing weight. They cannot generate at
      all; `:452` drops them first.

    After step 2 the generating set and the sizing set are **identical**. That is
    a property worth checking rather than assuming — if they ever diverge, one of
    the two resolvers has drifted, and the page should say so.
    """

    preregistered = list(condition(spec, "C4")["canary_book"])
    # Compare against WHAT IS BEING LAUNCHED, falling back to the pre-registration.
    #
    # Amended 2026-07-29 at wave-4 integration (B367). The spec pre-registers three sleeves, which
    # was right when it was written: `sub_xvol_pullback` is an FTMO survivor that the committed
    # config cannot generate. Borhen has since approved arming the full four-sleeve FTMO survivor
    # book. With the pre-registration as the sole basis, `--launch-tags` naming those four made
    # `unexpected_sleeves` non-empty and fired C4 CRITICAL on day one — on a page that tells the
    # operator "nothing else means anything if this is red". A stop condition that cries wolf on the
    # approved configuration is worse than no stop condition.
    #
    # The pre-registration is NOT rewritten. Rewriting a pre-registered threshold after seeing the
    # decision is the exact failure it exists to prevent. It is kept, reported, and any divergence
    # from it is raised on its own — so the operator is told "you are running a different book than
    # the one every threshold on this page was derived for", which is true and is the thing worth
    # saying, rather than "the book has drifted", which is not.
    canary = list(launch_tags) if launch_tags else list(preregistered)
    report = {"canary_book": canary, "preregistered_canary_book": preregistered,
              "sizing": None, "generation": None,
              "launch_tags": list(launch_tags) if launch_tags else None,
              "resolution_error": None}
    if cfg_error:
        return report, [Alert("C4", CRITICAL, "Book composition UNVERIFIABLE",
                              f"config unreadable: {cfg_error}")]

    alerts = []
    try:
        from src.components.ultimate_book import admission as P
        from src.components.ultimate_book import book_engine as BE
        from src.components.ultimate_book.sleeves.registry import active_specs

        # The engine's own resolvers, not a reimplementation of them. Reproducing
        # the merge in a second place is how the two silently drift apart.
        candidate_sleeves = BE._candidate_book_sleeves(cfg)
        expansion_sleeves = BE._market_expansion_sleeves(cfg)
        include_candidate = bool(cfg.get("ultimate_book_include_candidate_book"))
        include_expansion = bool(cfg.get("ultimate_book_include_market_expansion_book"))

        registry = P.effective_registry(
            include_clean3=bool(cfg.get("ultimate_book_include_clean3")),
            include_clean4=bool(cfg.get("ultimate_book_include_clean4")),
            include_candidate_book=include_candidate,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=include_expansion,
            market_expansion_sleeves=expansion_sleeves or None)

        raw_specs = active_specs(
            tuple(launch_tags) if launch_tags else None,
            include_candidate_book=include_candidate,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=include_expansion,
            market_expansion_sleeves=expansion_sleeves or None)
    except Exception as exc:  # noqa: BLE001
        report["resolution_error"] = f"{type(exc).__name__}: {exc}"
        return report, [Alert("C4", CRITICAL, "Book composition UNVERIFIABLE",
                              report["resolution_error"])]

    sizing = sorted(registry)
    raw = sorted(s.tag for s in raw_specs)
    generation = sorted(t for t in raw if t in registry)      # book_engine.py:452-453

    report["sizing"] = sizing
    report["n_sizing"] = len(sizing)
    report["raw_specs"] = raw
    report["n_raw_specs"] = len(raw)
    report["generation"] = generation
    report["n_generation"] = len(generation)
    report["dropped_by_engine_filter"] = sorted(set(raw) - set(registry))
    report["sizing_without_generation"] = sorted(set(sizing) - set(generation))
    report["confidences"] = {name: getattr(registry[name], "confidence", None) for name in sizing}

    report["unexpected_sleeves"] = sorted(set(generation) - set(canary))
    # "Missing" is measured against launched OR pre-registered, deliberately the union. A sleeve
    # that either the operator asked for or the spec expects, and that cannot put an order on the
    # account, is the CRITICAL case in both directions: `--tags` quietly losing a sleeve, and the
    # config being unable to generate one the owner approved. Taking only the launched set would
    # make a dropped sleeve invisible, because you cannot miss what you did not ask for.
    report["missing_sleeves"] = sorted((set(canary) | set(preregistered)) - set(generation))
    report["diverges_from_preregistration"] = sorted(set(canary) ^ set(preregistered))

    if report["diverges_from_preregistration"]:
        alerts.append(Alert(
            "C4", HIGH,
            f"the launched book is not the pre-registered one "
            f"({len(canary)} sleeves, not {len(preregistered)})",
            f"launched: {', '.join(sorted(canary))}; pre-registered: "
            f"{', '.join(sorted(preregistered))}. Not a fault — the owner may have changed the "
            "book, and this is how you would find out if he had not. But every threshold on this "
            "page was derived for the pre-registered set: C7's silence horizon is the product of "
            "three per-sleeve rates and there is no rate for a fourth sleeve, and the published "
            "P(pass) figures are four-sleeve numbers. Read them as approximate for this book."))

    if report["missing_sleeves"]:
        alerts.append(Alert("C4", CRITICAL,
                            f"{len(report['missing_sleeves'])} armed sleeve(s) cannot generate "
                            f"an order at all",
                            ", ".join(report["missing_sleeves"])))
    if report["unexpected_sleeves"]:
        dead = [s for s in report["unexpected_sleeves"] if s in DEAD_SLEEVES]
        expansion = [s for s in report["unexpected_sleeves"] if s.startswith("mx_")]
        alerts.append(Alert(
            "C4", CRITICAL,
            f"{len(generation)} sleeves can generate orders, not {len(canary)}",
            f"{len(report['unexpected_sleeves'])} beyond the canary book"
            + (f", including {len(dead)} measured as dead ({', '.join(dead)})" if dead else "")
            + (f" and {len(expansion)} market-expansion sleeves" if expansion else "")
            + ". The canary book is expressed by `run_book.py --tags`, NOT by config: no "
              "combination of the config flags can resolve below core-8, and the committed "
              "scripts/run_book_supervisor.ps1:108-109 passes no --tags at all. If the live "
              "host is not passing them either, it is trading a different portfolio than the "
              "one every number on this page assumes."))
    # Only a drift signal when --tags is NOT what caused the difference. With tags
    # passed, sizing legitimately exceeds generation — that is what tags are for,
    # and alerting on it would fire on every correctly-configured canary run.
    if report["sizing_without_generation"] and not launch_tags:
        alerts.append(Alert(
            "C4", HIGH,
            f"{len(report['sizing_without_generation'])} sleeve(s) carry a sizing weight but "
            f"cannot generate",
            ", ".join(report["sizing_without_generation"])
            + " — with no --tags in play the two resolvers should agree exactly after "
              "book_engine.py:452, so a difference here means one changed without the other."))
    return report, alerts


# --------------------------------------------------------------------------
# Q2 — did it trade, and is it alive?
# --------------------------------------------------------------------------


def check_liveness(spec, packets_path, expected_namespaces, now):
    threshold = condition(spec, "C6")["trigger"]["packet_gap_seconds_above"]
    report = {"packets_path": str(packets_path) if packets_path else None,
              "threshold_seconds": threshold, "namespaces": {}, "evaluated": False}
    alerts = []

    rows = read_jsonl(packets_path)
    if not rows:
        report["note"] = ("no packet stream on this machine — liveness UNEVALUATED. "
                          "This is the expected state on the research laptop: the stream "
                          "is written on the VPS.")
        alerts.append(Alert("C6", INFO, "Book liveness not evaluated (no packet stream here)",
                            "Point --packets at an export to evaluate it."))
        return report, alerts

    report["evaluated"] = True
    stamps = defaultdict(list)
    for row in rows:
        instant = parse_utc(row.get("created_at_utc"))
        if instant is not None:
            stamps[str(row.get("namespace") or "unattributed")].append(instant)

    for namespace, series in sorted(stamps.items()):
        series.sort()
        gaps = [(b - a).total_seconds() for a, b in zip(series, series[1:])]
        breaches = [g for g in gaps if g > threshold]
        age = (now - series[-1]).total_seconds()
        report["namespaces"][namespace] = {
            "packets": len(series), "last_packet_utc": series[-1].isoformat(),
            "seconds_since_last_packet": round(age, 1),
            "gap_p90_seconds": round(sorted(gaps)[int(0.9 * len(gaps))], 1) if gaps else None,
            "silence_breaches": len(breaches)}
        if age > threshold:
            alerts.append(Alert("C6", HIGH, f"{namespace}: no packet for {age / 60:.0f} minutes",
                                f"threshold {threshold / 60:.0f} min, calibrated on the live "
                                f"export (p90 60.4 s, p99 909.6 s)"))

    for namespace in sorted(set(expected_namespaces) - set(stamps)):
        alerts.append(Alert("C6", CRITICAL, f"DEAD: {namespace} emitted no packets at all",
                            "A book that died completely emits nothing and so can never appear "
                            "in an observed set — only this set-difference can catch it."))
    return report, alerts


def check_fills(spec, fills, armed_utc, now):
    """Fills, and the calibrated expectation for silence.

    The tension the prompt names is resolved by refusing to conflate two
    questions. `check_liveness` owns *dead*. This owns *quiet*, and it states
    the calibrated expectation on every page whether or not it has triggered —
    because an alert that only ever appears when something is wrong teaches the
    reader nothing about what normal looks like.
    """

    spec_c7 = condition(spec, "C7")
    horizon = spec_c7["trigger"]["calendar_days_of_complete_silence_above"]
    p_zero = spec_c7["derived_from"]["per_sleeve_p_zero_in_38_days"]

    report = {"n_fills": len(fills), "horizon_days": horizon,
              "per_sleeve_p_zero_in_38_days": p_zero}
    alerts = []

    if armed_utc is None:
        report["note"] = "no --armed-utc supplied; silence cannot be aged"
        return report, alerts

    days = (now - armed_utc).total_seconds() / 86400.0
    report["days_since_armed"] = round(days, 2)
    if days < 0:
        # A future arming instant is a typo, not a state. Saying so beats
        # rendering P(silence) = 1.009, which is what the first version did.
        report["note"] = "--armed-utc is in the FUTURE; silence cannot be aged"
        alerts.append(Alert("C7", INFO, "--armed-utc is in the future",
                            f"{armed_utc.isoformat()} > now {now.isoformat()}"))
        return report, alerts

    # P(all three silent for this many days), independence lower bound.
    joint_38 = 1.0
    for value in p_zero.values():
        joint_38 *= float(value)
    per_day = joint_38 ** (1.0 / 38.0)
    p_silence = per_day ** days
    report["p_silence_independence_lower_bound"] = round(p_silence, 4)
    report["joint_p_zero_in_38_days_independence"] = round(joint_38, 4)

    if fills:
        report["first_fill_utc"] = min(
            (r for r in (parse_utc(f.get("entry_time_utc")) for f in fills) if r),
            default=None)
        if report["first_fill_utc"]:
            report["first_fill_utc"] = report["first_fill_utc"].isoformat()
        return report, alerts

    if days > horizon:
        alerts.append(Alert(
            "C7", MEDIUM,
            f"{days:.0f} calendar days armed with zero fills across all three sleeves",
            f"P(this much silence at the sleeves' natural frequency) is "
            f"{p_silence:.3f} under an independence LOWER bound; the sleeves are "
            f"positively dependent, so the true probability is higher and this is the "
            f"earliest defensible point to mention it. Not evidence of breakage — the "
            f"same three fired zero times across the whole 38-day live window."))
    return report, alerts


# --------------------------------------------------------------------------
# Q3 — cost versus predicted
# --------------------------------------------------------------------------


ACCOUNT_KEY = {"ftmo": "FTMO", "redacted_account": "redacted_account"}


def check_costs(spec, fills):
    """Price every fill against the truth table and compare to what was charged.

    This is the hard direction on purpose: `cost_r` never sees the trade's
    realized commission. It gets symbol, account and stop distance, and must
    reproduce what the broker charged.
    """

    c1, c2 = condition(spec, "C1"), condition(spec, "C2")
    report = {"n_priced": 0, "skipped": {}, "per_fill": [], "baseline": c1["derived_from"]}
    alerts = []
    if not fills:
        report["note"] = "no fills yet — nothing to price"
        return report, alerts

    try:
        from src.costs import CostTruthError, cost_r, load_broker_true_costs
        truth = load_broker_true_costs()
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report, [Alert("C1", HIGH, "Cost layer UNAVAILABLE — deviation UNEVALUATED",
                              report["error"])]

    skipped: dict[str, int] = defaultdict(int)
    for row in fills:
        account = ACCOUNT_KEY.get(str(row.get("account") or "").lower())
        symbol = row.get("broker_symbol")
        risk = row.get("risk_at_entry_usd")
        realized = row.get("commission")
        stop = row.get("risk_distance_price")
        if not (account and symbol and risk and stop is not None and realized is not None):
            skipped["missing_fields"] += 1
            continue
        if float(stop) <= 0:
            skipped["nonpositive_stop"] += 1
            continue
        try:
            # entry_utc is required since the wave-21 cost layer: cash-per-lot
            # commissions in a non-USD profit currency convert at the ENTRY
            # instant's historical FX rate, and swap charges at broker-wall
            # midnight crossings from the entry instant.
            priced = cost_r(symbol, account,
                            holding_hours=float(row.get("holding_seconds") or 0) / 3600.0,
                            sl_distance_price=float(stop), entry_price=row.get("entry_price"),
                            side="SHORT" if str(row.get("side", "")).lower() == "short" else "LONG",
                            entry_utc=parse_utc(row.get("entry_time_utc")),
                            costs=truth)
        except CostTruthError as exc:
            skipped[f"unpriceable:{exc.__class__.__name__}"] += 1
            continue
        actual = -float(realized) / float(risk)          # positive = cost
        modelled = priced.commission_r.value
        swap_actual = -float(row.get("swap") or 0.0) / float(risk)
        swap_modelled = getattr(getattr(priced, "swap_r", None), "value", None)
        report["per_fill"].append({
            "symbol": symbol, "account": account,
            "sleeve": row.get("sleeve_id") or row.get("sleeve_tag") or row.get("sleeve_family"),
            "entry_time_utc": row.get("entry_time_utc"),
            "commission_modelled_r": modelled, "commission_actual_r": actual,
            "commission_abs_error_r": abs(modelled - actual),
            "swap_actual_r": swap_actual, "swap_modelled_r": swap_modelled,
            "swap_abs_error_r": (abs(swap_modelled - swap_actual)
                                 if swap_modelled is not None else None),
            "holding_hours": float(row.get("holding_seconds") or 0) / 3600.0,
            "coverage": priced.commission_r.coverage.value})
    report["skipped"] = dict(skipped)
    report["n_priced"] = len(report["per_fill"])
    if not report["per_fill"]:
        # Fills exist but the layer refused every one. Per this tool's own
        # premise -- an alert that does not fire is indistinguishable from
        # all-clear -- an unevaluated C1 must be RED, never a silent note.
        report["note"] = "no fill could be priced"
        return report, [Alert(
            "C1", HIGH,
            "Cost layer refused EVERY fill — deviation UNEVALUATED",
            f"{len(fills)} fill(s), 0 priced; refusals: {dict(skipped)}")]

    errors = [f["commission_abs_error_r"] for f in report["per_fill"]]
    report["mean_abs_error_r"] = statistics.fmean(errors)
    report["worst_abs_error_r"] = max(errors)
    report["pooled_actual_commission_r"] = statistics.fmean(
        f["commission_actual_r"] for f in report["per_fill"])
    report["median_holding_hours"] = statistics.median(
        f["holding_hours"] for f in report["per_fill"])

    window = int(c1["trigger_rolling"]["window_fills"])
    rolling = errors[-window:]
    report["rolling_window_fills"] = window
    report["rolling_mean_abs_error_r"] = statistics.fmean(rolling)

    minimum = int(c1.get("n_fills_before_first_evaluation", 3))
    if len(errors) >= minimum:
        limit = float(c1["trigger_rolling"]["mean_abs_error_r_above"])
        if len(rolling) >= min(window, len(errors)) and report["rolling_mean_abs_error_r"] > limit:
            alerts.append(Alert(
                "C1", HIGH,
                f"Cost model deviating: last {len(rolling)} fills mean |error| "
                f"{report['rolling_mean_abs_error_r']:.4f} R (pre-registered {limit} R)",
                f"baseline was {c1['derived_from']['baseline_mean_abs_error_r']} R over "
                f"{c1['derived_from']['baseline_n_fills']} fills. The activation case rests "
                f"on this table being right."))
    single = float(c1["trigger_single_fill"]["abs_error_r_above"])
    for fill in report["per_fill"]:
        if fill["commission_abs_error_r"] > single:
            alerts.append(Alert(
                "C1", HIGH,
                f"Single fill outside anything ever measured: {fill['symbol']} "
                f"|error| {fill['commission_abs_error_r']:.4f} R (pre-registered {single} R)",
                f"worst of the 175-fill baseline was "
                f"{c1['derived_from']['baseline_worst_single_fill_r']} R"))

    swap_errors = [f["swap_abs_error_r"] for f in report["per_fill"]
                   if f["swap_abs_error_r"] is not None]
    if swap_errors:
        report["swap_mean_abs_error_r"] = statistics.fmean(swap_errors)
        report["swap_worst_abs_error_r"] = max(swap_errors)
        # The band here is an order of magnitude wider than C1's, and that width is
        # measured rather than chosen. The swap model's baseline mean |error| is
        # 0.010324 R against commission's 0.000535 R — 19x — and its coverage is
        # MODELLED, not MEASURED. A first draft copied C1's 0.01 R threshold across
        # and would have fired on 22.8 % of rolling windows in the baseline corpus
        # itself (B336).
        swap_limit = float(c2["trigger_swap"]["mean_abs_error_r_above"])
        recent = swap_errors[-int(c2["trigger_swap"]["window_fills"]):]
        report["swap_rolling_mean_abs_error_r"] = statistics.fmean(recent)
        if len(swap_errors) >= minimum and statistics.fmean(recent) > swap_limit:
            alerts.append(Alert(
                "C2", HIGH,
                f"Swap deviating: last {len(recent)} fills mean |error| "
                f"{statistics.fmean(recent):.4f} R (pre-registered {swap_limit} R)",
                "Swap is the largest single broker cost for eight of eleven sleeves and "
                "holding time is what OD-3 now waits on. The pre-registered band is wide "
                "because the swap model is measurably 19x less accurate than the "
                "commission model; exceeding it is therefore a strong signal."))
        single_swap = float(c2.get("trigger_swap_single_fill", {}).get(
            "abs_error_r_above", float("inf")))
        for fill in report["per_fill"]:
            if fill["swap_abs_error_r"] is not None and fill["swap_abs_error_r"] > single_swap:
                alerts.append(Alert(
                    "C2", HIGH,
                    f"Single fill swap outside anything measured: {fill['symbol']} "
                    f"|error| {fill['swap_abs_error_r']:.4f} R "
                    f"(pre-registered {single_swap} R)",
                    "worst of the 175-fill baseline was 0.1951 R"))
    else:
        report["swap_note"] = ("the cost layer exposes no swap_r for these fills; swap "
                               "deviation UNEVALUATED")

    live_median = float(c2["derived_from"]["live_broker_true_median_holding_hours"])
    multiple = float(c2["trigger_holding"]["sleeve_median_holding_hours_above_multiple_of_live_median"])
    by_sleeve = defaultdict(list)
    for fill in report["per_fill"]:
        by_sleeve[fill["sleeve"] or "unattributed"].append(fill["holding_hours"])
    report["holding_hours_by_sleeve"] = {
        name: {"n": len(v), "median": statistics.median(v)} for name, v in sorted(by_sleeve.items())}
    for name, block in report["holding_hours_by_sleeve"].items():
        if block["n"] >= 3 and block["median"] > live_median * multiple:
            alerts.append(Alert(
                "C2", HIGH,
                f"{name}: median hold {block['median']:.2f} h is over {multiple:g}x the "
                f"live broker-true median ({live_median} h)",
                "Carry is the OD-3 blocker. Longer holds move every CARRY_CONDITIONAL "
                "sleeve toward its break-even."))
    return report, alerts


# --------------------------------------------------------------------------
# C3 — sleeve-level tripwires
# --------------------------------------------------------------------------


def check_sleeves(spec, fills):
    c3 = condition(spec, "C3")
    report = {"per_sleeve": {}}
    alerts = []
    if not fills:
        report["note"] = "no fills yet"
        return report, alerts

    by_sleeve = defaultdict(lambda: {"n": 0, "gross_r": 0.0, "net_r": 0.0})
    for row in fills:
        name = row.get("sleeve_id") or row.get("sleeve_tag") or row.get("sleeve_family") or "unattributed"
        block = by_sleeve[name]
        block["n"] += 1
        block["gross_r"] += float(row.get("gross_r") or 0.0)
        block["net_r"] += float(row.get("realized_r") or 0.0)
    report["per_sleeve"] = {k: dict(v) for k, v in sorted(by_sleeve.items())}

    total_loss = sum(-v["net_r"] for v in by_sleeve.values() if v["net_r"] < 0)
    total_fills = sum(v["n"] for v in by_sleeve.values())
    report["total_fills"] = total_fills
    report["total_net_loss_r"] = total_loss

    min_fills = int(c3["trigger_gross_negative"]["min_fills"])
    for name, block in report["per_sleeve"].items():
        if block["n"] >= min_fills and block["gross_r"] < float(
                c3["trigger_gross_negative"]["cumulative_gross_r_below"]):
            alerts.append(Alert(
                "C3", HIGH,
                f"{name}: negative GROSS over {block['n']} fills "
                f"({block['gross_r']:+.3f} R before any cost)",
                "A sleeve losing before any cost is charged cannot be rescued by a better "
                "cost model. That is exactly what separated the two dead JPY sleeves from "
                "the nine that survived re-costing. Six fills cannot establish an edge and "
                "this does not claim to — it surfaces the shape that took a fortnight to see."))

    if total_fills >= int(c3["trigger_loss_concentration"]["min_total_fills"]) and total_loss > 0:
        share_limit = float(c3["trigger_loss_concentration"]["single_sleeve_share_of_net_loss_above"])
        for name, block in report["per_sleeve"].items():
            if block["net_r"] >= 0:
                continue
            share = -block["net_r"] / total_loss
            report["per_sleeve"][name]["share_of_net_loss"] = round(share, 4)
            if share > share_limit:
                alerts.append(Alert(
                    "C3", HIGH,
                    f"{name}: {share * 100:.0f}% of total net loss over {block['n']} fills",
                    f"pre-registered at {share_limit * 100:.0f}%. The JPY cluster was 37.4% "
                    f"and it took a fortnight and a forensic session to see."))
    return report, alerts


# --------------------------------------------------------------------------
# Q4 — drawdown headroom
# --------------------------------------------------------------------------


def check_headroom(spec, account_state, now):
    """Headroom to the static floor and to today's daily limit, per firm.

    The two firms' rules differ in KIND. FTMO's daily loss is 5 % of **initial
    capital** and resets at 00:00 CE(S)T; redacted_account's is 5 % of **initial
    balance plus today's realized profit** and resets at 00:00 **server** time.
    A firm's reset rule is not its MT5 server clock, and the server clock is
    `America/New_York + 7 h` on the **US** DST calendar. Neither is hardcoded
    here; both come from `src/utils/broker_clock.py`, which fails closed.
    """

    from src.utils.broker_clock import (UnknownBrokerClockError, daily_reset_offset_hours,
                                        offset_seconds_at_utc, resolve_rule)

    c8 = condition(spec, "C8")
    report = {"accounts": {}, "firm_rules": c8["firm_rules"]}
    alerts = []
    if not account_state:
        report["note"] = ("no --account-state supplied. Balance, equity and high-water are "
                          "INPUTS to this tool, never measurements it can make — it holds no "
                          "broker connection. Headroom UNEVALUATED.")
        alerts.append(Alert("C8", INFO, "Drawdown headroom not evaluated (no account state)",
                            "Supply --account-state with balance/equity/day-start equity."))
        return report, alerts

    for name, block in account_state.items():
        entry: dict = {"provenance": block.get("provenance", "[input] unverified — supplied to "
                                                             "this tool, not measured by it")}
        balance = block.get("balance")
        equity = block.get("equity", balance)
        floor = block.get("static_dd_floor")
        initial = block.get("initial_capital")
        day_start = block.get("day_start_equity")
        entry.update({"balance": balance, "equity": equity, "static_dd_floor": floor,
                      "initial_capital": initial, "day_start_equity": day_start})

        if equity is not None and floor is not None:
            headroom = float(equity) - float(floor)
            entry["static_headroom_usd"] = headroom
            limit = float(c8["trigger_static"]["headroom_usd_below"])
            if headroom < limit:
                alerts.append(Alert("C8", HIGH,
                                    f"{name}: ${headroom:,.0f} above the static max-DD floor",
                                    f"pre-registered alert below ${limit:,.0f}"))

        rule_name = block.get("daily_reset_rule")
        try:
            offset = daily_reset_offset_hours(now, rule_name)
            if offset is None:
                server = block.get("broker_server")
                offset = (offset_seconds_at_utc(now, resolve_rule(server)) / 3600.0
                          if server else None)
                entry["reset_calendar"] = f"server clock ({server})"
            else:
                entry["reset_calendar"] = rule_name
            if offset is not None:
                local = now + timedelta(hours=offset)
                next_reset_local = (local + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0)
                entry["reset_offset_hours_now"] = offset
                entry["hours_to_daily_reset"] = round(
                    (next_reset_local - local).total_seconds() / 3600.0, 2)
        except UnknownBrokerClockError as exc:
            entry["reset_error"] = str(exc)
            alerts.append(Alert("C8", HIGH, f"{name}: daily-reset window UNKNOWN",
                                "broker_clock fails closed rather than guessing; a wrong "
                                "reset window is invisible until it costs money"))

        allowance = None
        if initial is not None and str(block.get("daily_loss_basis", "")).lower() == "initial_capital":
            allowance = 0.05 * float(initial)
        elif initial is not None:
            realized = float(block.get("today_realized_profit") or 0.0)
            allowance = 0.05 * (float(initial) + max(0.0, realized))
        if allowance is not None and day_start is not None and equity is not None:
            used = max(0.0, float(day_start) - float(equity))
            entry["daily_allowance_usd"] = allowance
            entry["daily_used_usd"] = used
            entry["daily_fraction_consumed"] = used / allowance if allowance else None
            limit = float(c8["trigger_daily"]["fraction_of_daily_allowance_consumed_above"])
            if allowance and used / allowance > limit:
                alerts.append(Alert(
                    "C8", HIGH,
                    f"{name}: {used / allowance * 100:.0f}% of today's daily-loss allowance used",
                    f"${used:,.0f} of ${allowance:,.0f}; pre-registered at {limit * 100:.0f}%"))
        report["accounts"][name] = entry
    return report, alerts


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _fmt_gate(value):
    if value == "ABSENT":
        return "ABSENT (key not present)"
    return repr(value)


def render(page: dict) -> str:
    out: list[str] = []
    add = out.append
    alerts = page["alerts"]

    add("=" * 78)
    add(f"  GTOS CANARY  —  {page['generated_utc']}")
    add("=" * 78)

    if not alerts:
        add("  NO ALERTS")
    else:
        for alert in sorted(alerts, key=lambda a: _RANK.get(a["severity"], 9)):
            add(f"  [{alert['severity']}] {alert['condition']}: {alert['headline']}")
            if alert["detail"]:
                for line in _wrap(alert["detail"], 72):
                    add(f"        {line}")
    add("")

    arming = page["arming"]
    add("-- 1. IS IT ARMED? ----------------------------------------------------------")
    add(f"   config: {page['config_path']}")
    for key in GATE_KEYS:
        add(f"     {key:<44} {_fmt_gate(arming['gates'].get(key, 'ABSENT'))}")
    token = arming.get("token") or {}
    add(f"     activation token dir                         {token.get('token_dir')}")
    add(f"     valid token for the armed account            "
        f"{arming.get('token_valid_for_armed_account')}"
        + (f"  (expires {arming['token_expires_utc']})" if arming.get("token_expires_utc") else ""))
    add(f"   => ARMED: {arming.get('armed')}")
    add("")

    book = page["book"]
    add("-- 5. IS THE BOOK STILL EXACTLY THREE SLEEVES? ------------------------------")
    add(f"   pre-registered canary book : {', '.join(book['canary_book'])}")
    if book.get("generation") is None:
        add(f"   RESOLUTION FAILED          : {book.get('resolution_error')}")
    else:
        add(f"   CAN GENERATE ORDERS        : {book['n_generation']} sleeves"
            f"   (run_book --tags: {book['launch_tags'] or 'NONE PASSED — all BUILT'})")
        add(f"     specs built                {book['n_raw_specs']}"
            f"  -> engine filter drops {len(book['dropped_by_engine_filter'])}"
            f"  -> {book['n_generation']} can trade")
        add(f"   carry a sizing weight      : {book['n_sizing']} sleeves")
        if book["unexpected_sleeves"]:
            add(f"   BEYOND THE CANARY BOOK     : {len(book['unexpected_sleeves'])}")
            for line in _wrap(", ".join(book["unexpected_sleeves"]), 68):
                add(f"       {line}")
        if book["missing_sleeves"]:
            add(f"   CANNOT GENERATE AT ALL     : {', '.join(book['missing_sleeves'])}")
        if book.get("sizing_without_generation"):
            add(f"   weighted but cannot trade  : {', '.join(book['sizing_without_generation'])}")
    add("")

    add("-- 2. DID IT TRADE? ---------------------------------------------------------")
    fills, live = page["fills"], page["liveness"]
    add(f"   fills recorded             : {fills['n_fills']}")
    if "days_since_armed" in fills:
        add(f"   days since armed           : {fills['days_since_armed']}")
        add(f"   P(this silence | natural frequency), independence lower bound: "
            f"{fills.get('p_silence_independence_lower_bound')}")
        add(f"   alert horizon              : {fills['horizon_days']} calendar days "
            f"of complete silence")
    if fills.get("first_fill_utc"):
        add(f"   first fill                 : {fills['first_fill_utc']}")
    add(f"   book alive (packet stream) : "
        + ("not evaluated — " + str(live.get("note", "")).split("—")[0].strip()
           if not live.get("evaluated") else "evaluated"))
    for namespace, block in (live.get("namespaces") or {}).items():
        add(f"       {namespace:<32} {block['packets']} packets, last "
            f"{block['seconds_since_last_packet'] / 60:.0f} min ago")
    add("")

    add("-- 3. WHAT DID IT COST vs WHAT WE PREDICTED? --------------------------------")
    costs = page["costs"]
    if costs.get("note") or costs.get("error"):
        add(f"   {costs.get('error') or costs['note']}")
        base = costs.get("baseline", {})
        add(f"   baseline to beat           : mean |error| "
            f"{base.get('baseline_mean_abs_error_r')} R over "
            f"{base.get('baseline_n_fills')} fills")
        add(f"   the model this replaced    : {base.get('null_control_shipped_model_error_r')} R "
            f"(it charges zero commission)")
    else:
        add(f"   fills priced               : {costs['n_priced']}"
            + (f"   skipped {costs['skipped']}" if costs.get("skipped") else ""))
        add(f"   mean |commission error|    : {costs['mean_abs_error_r']:.6f} R   "
            f"(baseline {costs['baseline']['baseline_mean_abs_error_r']} R)")
        add(f"   worst single fill          : {costs['worst_abs_error_r']:.6f} R   "
            f"(baseline worst {costs['baseline']['baseline_worst_single_fill_r']} R)")
        add(f"   rolling mean over last {costs['rolling_window_fills']}   : "
            f"{costs['rolling_mean_abs_error_r']:.6f} R")
        if "swap_mean_abs_error_r" in costs:
            add(f"   mean |swap error|          : {costs['swap_mean_abs_error_r']:.6f} R")
        elif costs.get("swap_note"):
            add(f"   swap                       : {costs['swap_note']}")
        add(f"   median holding hours       : {costs['median_holding_hours']:.3f} h   "
            f"(live broker-true median 1.2603 h)")
    add("")

    sleeves = page["sleeves"]
    if sleeves.get("per_sleeve"):
        add("-- SLEEVE TRIPWIRES ---------------------------------------------------------")
        add(f"   {'sleeve':<28} {'n':>4} {'gross R':>10} {'net R':>10}")
        for name, block in sleeves["per_sleeve"].items():
            add(f"   {name:<28} {block['n']:>4} {block['gross_r']:>10.3f} {block['net_r']:>10.3f}")
        add("")

    add("-- 4. HOW MUCH DRAWDOWN HEADROOM IS LEFT? -----------------------------------")
    head = page["headroom"]
    if head.get("note"):
        for line in _wrap(head["note"], 72):
            add(f"   {line}")
    for name, block in (head.get("accounts") or {}).items():
        add(f"   {name}")
        add(f"       provenance             {block['provenance']}")
        if block.get("equity") is not None:
            add(f"       equity                 ${block['equity']:,.0f}")
        if block.get("static_headroom_usd") is not None:
            add(f"       above the static floor ${block['static_headroom_usd']:,.0f} "
                f"(floor ${block['static_dd_floor']:,.0f})")
        if block.get("daily_allowance_usd") is not None:
            add(f"       today's daily budget   ${block['daily_used_usd']:,.0f} used of "
                f"${block['daily_allowance_usd']:,.0f} "
                f"({block['daily_fraction_consumed'] * 100:.0f}%)")
        if block.get("hours_to_daily_reset") is not None:
            add(f"       daily reset in         {block['hours_to_daily_reset']:.1f} h "
                f"({block['reset_calendar']})")
        if block.get("reset_error"):
            add(f"       RESET WINDOW UNKNOWN   {block['reset_error'][:120]}")
    add("")
    add("-" * 78)
    add(f"  Every alert above is pre-registered in {SPEC_PATH.name}.")
    add("  None of them halts anything. You decide when to stop.")
    add("-" * 78)
    return "\n".join(out) + "\n"


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = str(text).split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


# --------------------------------------------------------------------------


def build_page(args, now) -> dict:
    from src.safety.activation_token import account_digest

    spec = load_spec()
    cfg, cfg_error = runtime_block(args.config)
    digest = args.account_digest or account_digest(args.account_login)

    fills = read_jsonl(args.fills)
    if args.fills and args.stack_era:
        fills = [f for f in fills if f.get("stack_era") == args.stack_era]

    account_state = {}
    if args.account_state and args.account_state.is_file():
        account_state = json.loads(args.account_state.read_text(encoding="utf-8"))

    alerts: list[Alert] = []
    arming, a = check_arming(spec, cfg, cfg_error, digest, args.token_dir, now); alerts += a
    book, a = check_book_composition(spec, cfg, cfg_error, args.launch_tags); alerts += a
    liveness, a = check_liveness(spec, args.packets, args.expect_namespace, now); alerts += a
    fills_report, a = check_fills(spec, fills, parse_utc(args.armed_utc), now); alerts += a
    costs, a = check_costs(spec, fills); alerts += a
    sleeves, a = check_sleeves(spec, fills); alerts += a
    headroom, a = check_headroom(spec, account_state, now); alerts += a

    return {
        "schema": "gtos.canary.page.v1",
        "generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spec": str(SPEC_PATH.relative_to(REPO)),
        "config_path": str(args.config),
        "account_login_sha256": digest,
        "arming": arming, "book": book, "liveness": liveness, "fills": fills_report,
        "costs": costs, "sleeves": sleeves, "headroom": headroom,
        "alerts": [x.to_dict() for x in alerts],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                    help="the config whose book and gates to resolve")
    ap.add_argument("--packets", type=Path, default=DEFAULT_PACKETS,
                    help="runtime learning packet JSONL (.gz accepted)")
    ap.add_argument("--fills", type=Path, default=None,
                    help="live fills, gtos.live_divergence_row.v1 shape")
    ap.add_argument("--stack-era", default=None, help="filter fills to one stack_era")
    ap.add_argument("--account-state", type=Path, default=None,
                    help="JSON of balance/equity/floor per account")
    ap.add_argument("--account-login", default="531325516",
                    help="the armed account's login (digested, never transmitted)")
    ap.add_argument("--account-digest", default=None, help="use this digest directly")
    ap.add_argument("--token-dir", default=None, help="override the activation directory")
    ap.add_argument("--launch-tags", default=None,
                    type=lambda s: [t.strip() for t in s.split(",") if t.strip()],
                    help="the --tags the live run_book.py is started with. THIS is what "
                         "expresses a three-sleeve book; config cannot. Omit to check the "
                         "committed supervisor's behaviour, which passes none.")
    ap.add_argument("--armed-utc", default=None,
                    help="when the book was armed, ISO-8601; enables the silence calibration")
    ap.add_argument("--expect-namespace", action="append", default=[],
                    dest="expect_namespace", help="a namespace that MUST be emitting")
    ap.add_argument("--now", default=None, help="evaluate as of this UTC instant (testing)")
    ap.add_argument("-o", "--output", type=Path, default=None, help="write the page here")
    ap.add_argument("--json", type=Path, default=None, help="write the JSON page here")
    args = ap.parse_args()

    now = parse_utc(args.now) or datetime.now(timezone.utc)
    try:
        page = build_page(args, now)
    except Exception as exc:  # noqa: BLE001
        print(f"CANNOT EVALUATE: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    text = render(page)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(page, indent=2, sort_keys=True, default=str) + "\n",
                             encoding="utf-8")
    return exit_code(page)


def exit_code(page: dict) -> int:
    """0 clean, 1 an alert at MEDIUM or above, 3 clean but something unevaluated.

    Three codes rather than two, because collapsing "nothing is wrong" into
    "nothing could be checked" is the exact failure the prompt names: an alert
    that does not fire is indistinguishable from all-clear. On this laptop the
    packet stream and the account state are genuinely absent, so a two-code tool
    would either cry wolf on every run or go quietly green while seeing nothing.
    """

    severities = {a["severity"] for a in page["alerts"]}
    if severities & {CRITICAL, HIGH, MEDIUM}:
        return 1
    return 3 if severities else 0


if __name__ == "__main__":
    raise SystemExit(main())

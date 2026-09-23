"""Challenge 0 admission KEEP/KILL integers after hist S28–S33.

Dig B STATIC remaining board is authority and supersedes the earlier
CHAIR_CONSUME_STale S29 KILL. Consume stays stale — do not re-score it.
Do not invent NEWS.

KEEP (APPLY_CANDIDATE_KEEP): house static integer stays fail-closed.
Choice is wired for LABEL only. ``ADMISSION_APPLY`` stays 0 even when
``GTOS_JEV_ADMISSION_APPLY=1``, ``GTOS_JEV_APPLY_LIVE=1``, or
``GTOS_JEV_FLUID_GATES_APPLY=1``.

KILL: dead Jev / soft path. No Choice. No resting SHADOW.

Envelope walls (ENV-DD / ENV-KILL / token / H8 / 2-stop COUNT / US30 /
occupancy / dead window) stay integers. This module never places,
remints, flattens, or broker-sends. ``pack1b_beaten`` is always False.

Challenge-only: login ``0`` / ns ``operator``.
Do not edit ``src/components/ultimate_book/admission.py`` from here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from .apply_size import is_challenge_account
from .challenge import CHALLENGE_LOGIN, CHALLENGE_NS, VERIFICATION_QUARANTINED
from .process_lock import ENVELOPE_WALL_IDS, stamp_lock
from .veto import InventedNewsProtocolVeto, refuse_broker_action, refuse_invented_news_protocol

SCHEMA = "gtos.judgment.admission_keep_integers.v1"
STEAL = "ADMISSION_KEEP_INTEGERS_S28_S33"
PACK1B_BEATEN = False

# Hardcoded. Env cannot open APPLY. KEEP is the static integer + Choice.
ADMISSION_APPLY = 0

APPLY_ENV = "GTOS_JEV_ADMISSION_APPLY"
CHOICE_ENV = "GTOS_JEV_ADMISSION_CHOICE"
KEEP_ENV = "GTOS_JEV_ADMISSION_KEEP"
APPLY_LIVE_ENV = "GTOS_JEV_APPLY_LIVE"
FLUID_APPLY_ENV = "GTOS_JEV_FLUID_GATES_APPLY"

KEEP = "KEEP"
KILL = "KILL"
APPLY_CANDIDATE_KEEP = "APPLY_CANDIDATE_KEEP"

# House spelling is ``ddefense`` (smooth DD-defense). Do not "fix" the reason.
CEILING_REASON = "ceiling_profile_requires_smooth_ddefense"

KEEP_CHOICE_ANSWERS = ("KEEP_INTEGER", "ABSTAIN", "ESCALATE_CHAIR")

REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "ADMISSION_KEEP_INTEGERS_S28_S33.json"
)
RECEIPT_MD_PATH = RECEIPT_PATH.with_suffix(".md")
ENV_DOC_PATH = REPO_ROOT / "judgment" / "ADMISSION_KEEP_INTEGERS.md"

#: Hist authority — Dig B STATIC remaining board (S29 supersedes consume).
HIST_SOURCE = "DIG_B_STATIC_REMAINING"
HIST_SOURCE_PRIOR = "CHAIR_CONSUME_STale"
SOFT_2PCT_N = 1

HIST_ROWS: tuple[dict[str, Any], ...] = (
    {
        "sid": "S28",
        "name": "circuit_breaker_open",
        "kind": "governor_reason",
        "hist": APPLY_CANDIDATE_KEEP,
        "verdict": KEEP,
        "choice": True,
        "apply": 0,
        "integer_stays_fail_closed": True,
        "note": (
            "Operator circuit breaker stays the house integer. "
            "ADMISSION_APPLY stays 0. Choice labels only."
        ),
    },
    {
        "sid": "S29",
        "name": "soft_daily_stop_reached",
        "kind": "governor_reason",
        "hist": APPLY_CANDIDATE_KEEP,
        "verdict": KEEP,
        "choice": True,
        "apply": 0,
        "integer_stays_fail_closed": True,
        "envelope_untouched": "ENV-DD",
        "supersedes": "CHAIR_CONSUME_STale S29 KILL",
        "evidence": "Challenge soft_2pct n=1",
        "note": (
            "Dig B STATIC remaining board: APPLY_CANDIDATE_KEEP "
            "(Challenge soft_2pct n=1). House soft daily stop stays the "
            "fail-closed integer. ADMISSION_APPLY stays 0. Choice labels "
            "only. ENV-DD hard floor untouched."
        ),
    },
    {
        "sid": "S30",
        "name": "derisking_into_maxdd_wall",
        "kind": "governor_reason",
        "hist": APPLY_CANDIDATE_KEEP,
        "verdict": KEEP,
        "choice": True,
        "apply": 0,
        "integer_stays_fail_closed": True,
        "note": (
            "Max-DD de-risk cap_mult stays the house integer. "
            "Choice labels the haircut; cannot widen."
        ),
    },
    {
        "sid": "S31",
        "name": "profit_target_protect_derisk",
        "kind": "governor_reason",
        "hist": KILL,
        "verdict": KILL,
        "choice": False,
        "apply": 0,
        "dead_soft_path": True,
        "note": (
            "Optional profit-target derisk (default pct 0) is a dead Jev path. "
            "No Choice. House default stays off."
        ),
    },
    {
        "sid": "S32",
        "name": CEILING_REASON,
        "kind": "admit_reason",
        "hist": APPLY_CANDIDATE_KEEP,
        "verdict": KEEP,
        "choice": True,
        "apply": 0,
        "integer_stays_fail_closed": True,
        "note": (
            "Ceiling profile × band-defense interlock stays fail-closed. "
            "House reason spelling is ddefense. Choice labels only."
        ),
    },
    {
        "sid": "S33",
        "name": "leader_impulse_veto",
        "kind": "overlay",
        "hist": KILL,
        "verdict": KILL,
        "choice": False,
        "apply": 0,
        "dead_soft_path": True,
        "overlay_sizeup_allowed": False,
        "note": (
            "Confluence size-up overlay is a dead Jev path on Challenge. "
            "overlay_sizeup_allowed stays False. Do not enable overlays=True."
        ),
    },
)

HIST_BY_NAME: dict[str, dict[str, Any]] = {str(row["name"]): dict(row) for row in HIST_ROWS}
KEEP_NAMES = frozenset(row["name"] for row in HIST_ROWS if row["verdict"] == KEEP)
KILL_NAMES = frozenset(row["name"] for row in HIST_ROWS if row["verdict"] == KILL)

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def _env_flag(name: str, *, default: bool, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(name, "")).strip().lower()
    if raw == "":
        return default
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    return default


def admission_apply_open(
    *,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Always False. Reserved env and sibling APPLY flags cannot open this."""

    del login, ns, environ
    return False


def admission_apply_int(
    *,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    del login, ns, environ
    return ADMISSION_APPLY


def admission_keep_stamp_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default on. ``GTOS_JEV_ADMISSION_KEEP=0`` skips the Challenge stamp."""

    return _env_flag(KEEP_ENV, default=True, environ=environ)


def admission_choice_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default on. Choice still only wires on hist KEEP rows."""

    return _env_flag(CHOICE_ENV, default=True, environ=environ)


def env_flag_contract() -> dict[str, Any]:
    """Documented flags. APPLY stays 0 regardless of these values."""

    return {
        APPLY_ENV: {
            "default": "unset / ignored",
            "effect": "reserved; ADMISSION_APPLY stays 0",
            "can_open_apply": False,
        },
        CHOICE_ENV: {
            "default": "1 (missing counts as on)",
            "effect": "wires LABEL Choice on hist KEEP rows only",
            "can_open_apply": False,
        },
        KEEP_ENV: {
            "default": "1 (missing counts as on)",
            "effect": "stamps KEEP integers on Challenge host_occupancy_governor",
            "can_open_apply": False,
        },
        APPLY_LIVE_ENV: {
            "default": "off",
            "effect": "physical Challenge size haircut only; does not open admission APPLY",
            "can_open_apply": False,
        },
        FLUID_APPLY_ENV: {
            "default": "off",
            "effect": "fluid LABEL drafts only; does not open admission APPLY",
            "can_open_apply": False,
        },
        "ADMISSION_APPLY": ADMISSION_APPLY,
        "pack1b_beaten": PACK1B_BEATEN,
        "note": (
            "Sibling APPLY flags cannot open admission APPLY. "
            "Envelope walls stay integers. Dig never broker-sends."
        ),
    }


def hist_row(name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    return HIST_BY_NAME.get(str(name).strip())


def verdict_for(name: str | None) -> str | None:
    row = hist_row(name)
    return str(row["verdict"]) if row else None


def is_keep(name: str | None) -> bool:
    return verdict_for(name) == KEEP


def is_kill(name: str | None) -> bool:
    return verdict_for(name) == KILL


def overlay_sizeup_allowed_on_challenge(name: str | None) -> bool:
    """S33 KILL: leader_impulse_veto never size-ups on Challenge."""

    if not name:
        return False
    row = hist_row(name)
    if row and row.get("kind") == "overlay":
        return bool(row.get("overlay_sizeup_allowed", False))
    return False


def envelope_wall_name(name: str | None) -> bool:
    if not name:
        return False
    return str(name) in ENVELOPE_WALL_IDS


def choice_path_open(
    name: str | None,
    *,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Choice only where hist proved KEEP, on Challenge, flag default-on."""

    if admission_apply_open(login=login, ns=ns, environ=environ):
        return False
    if envelope_wall_name(name):
        return False
    if not is_challenge_account(login=login, ns=ns):
        return False
    if not admission_choice_enabled(environ=environ):
        return False
    return is_keep(name)


def _choice_payload(name: str) -> dict[str, Any]:
    return {
        "id": f"ADMISSION_{name}",
        "role": "Choice",
        "choice": "KEEP_INTEGER",
        "allowed": list(KEEP_CHOICE_ANSWERS),
        "apply": False,
        "integer_stays_fail_closed": True,
        "note": "LABEL only. Cannot lift, widen, place, remint, or flatten.",
    }


def evaluate_candidate(
    name: str | None,
    *,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """One named hist path. Unknown names are not SHADOW."""

    refuse_invented_news_protocol((name,) if name else None)
    if name and str(name).strip().lower() in {"place", "order_send", "flatten", "remint"}:
        refuse_broker_action(str(name))

    raw = str(name or "").strip()
    challenge = is_challenge_account(login=login, ns=ns)
    base = {
        "name": raw or None,
        "login": CHALLENGE_LOGIN if challenge else (None if login is None else str(login)),
        "ns": CHALLENGE_NS if challenge else (None if ns is None else str(ns)),
        "challenge_only": True,
        "challenge": challenge,
        "apply": ADMISSION_APPLY,
        "apply_open": False,
        "status": None,
        "shadow": False,
        "pack1b_beaten": PACK1B_BEATEN,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_broker_send": True,
        "no_news_invent": True,
        "envelope_walls_stay_integers": True,
    }
    if not challenge:
        return {
            **base,
            "ok": False,
            "refuse": "not_challenge",
            "choice": None,
            "choice_wired": False,
            "verdict": None,
            "in_hist_table": raw in HIST_BY_NAME,
        }
    if envelope_wall_name(raw):
        return {
            **base,
            "ok": True,
            "refuse": "envelope_wall_stays_integer",
            "choice": None,
            "choice_wired": False,
            "verdict": None,
            "in_hist_table": False,
            "status": "INTEGER",
            "envelope": raw,
        }
    row = hist_row(raw)
    if row is None:
        return {
            **base,
            "ok": True,
            "refuse": None,
            "choice": None,
            "choice_wired": False,
            "verdict": None,
            "in_hist_table": False,
            "status": "NOT_CANDIDATE",
            "note": "Not a hist S28–S33 path. Not SHADOW.",
        }

    verdict = str(row["verdict"])
    wired = choice_path_open(raw, login=login, ns=ns, environ=environ)
    choice = _choice_payload(raw) if wired else None
    status = verdict  # KEEP or KILL — never SHADOW
    return {
        **base,
        "ok": True,
        "sid": row["sid"],
        "kind": row["kind"],
        "hist": row["hist"],
        "verdict": verdict,
        "in_hist_table": True,
        "choice": choice,
        "choice_wired": wired,
        "status": status,
        "shadow": False,
        "integer_stays_fail_closed": bool(row.get("integer_stays_fail_closed")),
        "dead_soft_path": bool(row.get("dead_soft_path")),
        "overlay_sizeup_allowed": row.get("overlay_sizeup_allowed"),
        "envelope_untouched": row.get("envelope_untouched"),
        "note": row.get("note"),
    }


def _iter_names(
    *,
    reason: str | None,
    overlay: str | None,
    overlays_applied: Iterable[str] | None,
) -> list[str]:
    names: list[str] = []
    if reason and str(reason).strip() not in {"", "ok"}:
        names.append(str(reason).strip())
    if overlay:
        names.append(str(overlay).strip())
    for item in overlays_applied or ():
        raw = str(item or "").strip()
        if raw:
            names.append(raw)
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def stamp_admission(
    governor: Mapping[str, Any] | None = None,
    *,
    reason: str | None = None,
    overlay: str | None = None,
    overlays_applied: Iterable[str] | None = None,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Chair stamp for host_occupancy_governor. Never mutates the book."""

    gov = dict(governor) if isinstance(governor, Mapping) else {}
    reason_here = reason if reason is not None else gov.get("reason")
    names = _iter_names(
        reason=None if reason_here in (None, "") else str(reason_here),
        overlay=overlay,
        overlays_applied=overlays_applied,
    )
    challenge = is_challenge_account(login=login, ns=ns)
    keep_on = admission_keep_stamp_enabled(environ=environ)
    rows = [
        evaluate_candidate(name, login=login, ns=ns, environ=environ) for name in names
    ]
    if not keep_on:
        for row in rows:
            if row.get("verdict") == KEEP:
                row["choice"] = None
                row["choice_wired"] = False
                row["stamp_skipped"] = "GTOS_JEV_ADMISSION_KEEP_off"
    n_keep = sum(1 for row in rows if row.get("verdict") == KEEP)
    n_kill = sum(1 for row in rows if row.get("verdict") == KILL)
    n_shadow = sum(1 for row in rows if row.get("shadow") or row.get("status") == "SHADOW")
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        "ok": challenge,
        "challenge": challenge,
        "login": CHALLENGE_LOGIN if challenge else None,
        "ns": CHALLENGE_NS if challenge else (str(ns) if ns is not None else None),
        "verification_quarantined": VERIFICATION_QUARANTINED,
        "apply": ADMISSION_APPLY,
        "apply_open": False,
        "pack1b_beaten": PACK1B_BEATEN,
        "hist_source": HIST_SOURCE,
        "n_keep": n_keep,
        "n_kill": n_kill,
        "n_shadow": n_shadow,
        "n_choice_wired": sum(1 for row in rows if row.get("choice_wired")),
        "rows": rows,
        "governor_reason": reason_here,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_broker_send": True,
        "no_news_invent": True,
        "envelope_walls_stay_integers": True,
        "resting_shadow_forbidden": True,
        "env_flags": env_flag_contract(),
    }


def receipt_payload(*, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Frozen hist table + Challenge contract. No consume re-score."""

    login = CHALLENGE_LOGIN
    ns = CHALLENGE_NS
    rows = [
        evaluate_candidate(row["name"], login=login, ns=ns, environ=environ) for row in HIST_ROWS
    ]
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        **stamp_lock(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "hist_source": HIST_SOURCE,
        "hist_source_prior": HIST_SOURCE_PRIOR,
        "s29_superseded_from": "KILL",
        "s29_evidence": "Challenge soft_2pct n=1",
        "consume_stale": True,
        "do_not_rescore_consume": True,
        "pack1b_beaten": PACK1B_BEATEN,
        "admission_apply": ADMISSION_APPLY,
        "apply_open": False,
        "n_keep": sum(1 for row in rows if row["verdict"] == KEEP),
        "n_kill": sum(1 for row in rows if row["verdict"] == KILL),
        "n_shadow": 0,
        "n_choice_wired": sum(1 for row in rows if row["choice_wired"]),
        "keep_names": sorted(KEEP_NAMES),
        "kill_names": sorted(KILL_NAMES),
        "ceiling_reason_house_spelling": CEILING_REASON,
        "rows": rows,
        "hist_table": [dict(row) for row in HIST_ROWS],
        "env_flags": env_flag_contract(),
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_broker_send": True,
        "no_news_invent": True,
        "envelope_walls_stay_integers": True,
        "resting_shadow_forbidden": True,
        "do_not_edit_ultimate_book_admission": True,
        "hook": "src.judgment.host_occupancy.host_occupancy_governor → admission stamp",
        "note": (
            "KEEP = house integer + Choice LABEL. APPLY stays 0. "
            "KILL = dead soft/Jev path, no Choice, no SHADOW. "
            "ENV-DD stays the hard floor. Dig never order_send."
        ),
    }


def write_receipt(
    payload: dict[str, Any] | None = None,
    *,
    dest: Path | None = None,
    md_dest: Path | None = None,
    env_dest: Path | None = None,
) -> dict[str, Any]:
    receipt = payload or receipt_payload()
    out = dest or RECEIPT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    md = md_dest or RECEIPT_MD_PATH
    md.write_text(_markdown(receipt), encoding="utf-8")
    env_md = env_dest or ENV_DOC_PATH
    env_md.write_text(_env_markdown(receipt), encoding="utf-8")
    receipt["out"] = str(out)
    receipt["md_out"] = str(md)
    receipt["env_out"] = str(env_md)
    return receipt


def _markdown(receipt: Mapping[str, Any]) -> str:
    lines = [
        "# Admission KEEP/KILL integers — Challenge 0",
        "",
        "Hist authority: **Dig B STATIC remaining board** "
        "(supersedes CHAIR_CONSUME_STale S29 KILL; consume is stale; do not re-score).",
        "",
        f"- login `{receipt.get('login')}` / ns `{receipt.get('ns')}`",
        f"- `ADMISSION_APPLY={receipt.get('admission_apply')}` (hardcoded 0)",
        f"- `pack1b_beaten={receipt.get('pack1b_beaten')}`",
        f"- Choice wired: `{receipt.get('n_choice_wired')}` KEEP rows",
        f"- resting SHADOW: `{receipt.get('n_shadow')}`",
        "- Envelope walls stay integers. Never place / remint / flatten / order_send.",
        "",
        "## Hist table S28–S33",
        "",
        "| sid | name | hist | verdict | Choice | APPLY |",
        "|---|---|---|---|---|---|",
    ]
    for row in receipt.get("rows") or []:
        lines.append(
            f"| {row.get('sid')} | `{row.get('name')}` | {row.get('hist')} | "
            f"**{row.get('verdict')}** | {row.get('choice_wired')} | {row.get('apply')} |"
        )
    lines.extend(
        [
            "",
            "## Env flags",
            "",
            "See [`judgment/ADMISSION_KEEP_INTEGERS.md`](../../ADMISSION_KEEP_INTEGERS.md).",
            "",
            "- `GTOS_JEV_ADMISSION_APPLY` — reserved; ignored; APPLY stays 0",
            "- `GTOS_JEV_ADMISSION_CHOICE` — default on; KEEP-only Choice",
            "- `GTOS_JEV_ADMISSION_KEEP` — default on; Challenge stamp",
            "- `GTOS_JEV_APPLY_LIVE` / `GTOS_JEV_FLUID_GATES_APPLY` do **not** open admission APPLY",
            "",
            receipt.get("note") or "",
            "",
        ]
    )
    return "\n".join(lines)


def _env_markdown(receipt: Mapping[str, Any]) -> str:
    flags = receipt.get("env_flags") or env_flag_contract()
    lines = [
        "# Admission KEEP integers — env flags",
        "",
        "Challenge `0` / `operator` only. "
        "These flags cannot open broker send, remint, flatten, or envelope walls.",
        "",
        f"`ADMISSION_APPLY` is hardcoded `{ADMISSION_APPLY}`. "
        f"`pack1b_beaten` is `{PACK1B_BEATEN}`.",
        "",
        "| flag | default | effect | opens APPLY? |",
        "|---|---|---|---|",
    ]
    for key in (APPLY_ENV, CHOICE_ENV, KEEP_ENV, APPLY_LIVE_ENV, FLUID_APPLY_ENV):
        spec = flags.get(key) or {}
        lines.append(
            f"| `{key}` | {spec.get('default')} | {spec.get('effect')} | "
            f"{spec.get('can_open_apply')} |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- KEEP (S28 / S29 / S30 / S32): house integer stays fail-closed; Choice LABEL only.",
            "- KILL (S31 / S33): dead soft path; no Choice; no SHADOW rest.",
            "- Soft daily stop KEEP (Dig B STATIC, Challenge soft_2pct n=1) does not lift `ENV-DD`.",
            "- `leader_impulse_veto` KILL: `overlay_sizeup_allowed=false` on Challenge.",
            "- Dig / Jev never `order_send`.",
            "- Do not invent `NEWS_PROTOCOL`.",
            "",
        ]
    )
    return "\n".join(lines)


def refuse_news_invent(names: Iterable[str] | None = None) -> None:
    refuse_invented_news_protocol(names)


def refuse_dig_broker_send(action: str = "order_send") -> None:
    refuse_broker_action(action)


# Re-export so a bad `from src.judgment.admission import admit_and_size` fails loud.
def admit_and_size(*_a: Any, **_k: Any) -> None:
    raise RuntimeError(
        "src.judgment.admission is Challenge KEEP/KILL integers; "
        "do not call ultimate_book.admission.admit_and_size from here"
    )

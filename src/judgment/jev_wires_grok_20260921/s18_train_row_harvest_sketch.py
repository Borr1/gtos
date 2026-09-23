"""OUT-ONLY sketch — paired win/lose train-row harvest from Challenge closes.

Not landed. Not imported by live writer. Never order_send / place / remint / flatten.

Chair land target (later): src/judgment/train_row_harvest.py
Session: 18_jev_train_row_harvest  2026-09-21

Fail-closed if Jev dark. Module_ATR honesty: never merge R lenses.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

# --- env (draft) ---
HARVEST_SHADOW_ENV = "GTOS_JEV_TRAIN_HARVEST_SHADOW"
HARVEST_CALL_ENV = "GTOS_JEV_TRAIN_HARVEST_CALL"
HARVEST_APPLY_ENV = "GTOS_JEV_TRAIN_HARVEST_APPLY"
HARVEST_PATH_ENV = "GTOS_JEV_TRAIN_HARVEST_PATH"

SCHEMA_ROW = "gtos.jev.train_row_harvest.row.v1"
SCHEMA_PAIR = "gtos.jev.train_row_harvest.pair.v1"
SCHEMA_RUN = "gtos.jev.train_row_harvest.run.v1"

CHALLENGE_LOGIN = 0
QUARANTINE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

LENSES = ("Challenge_book", "Module_ATR", "Dig_3R", "Edge_ATR")
MENU_STRIKE = ("A_STAND_DOWN", "B_SIZE_HALF", "C_SIZE_TRIM", "D_FULL", "E_KEEP_CAP")
PAIR_KINDS = (
    "ticket_twin",
    "sleeve_twin_asset_split",
    "year_twin_module_atr",
    "module_keep_vs_challenge_stand",
    "unpaired",
)
KEEP_FAMS = ("spring", "vss_fxcross", "vss", "sub_mid")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def harvest_enabled() -> bool:
    return _env_on(HARVEST_SHADOW_ENV)


def harvest_call_enabled() -> bool:
    return harvest_enabled() and _env_on(HARVEST_CALL_ENV)


def harvest_apply_enabled() -> bool:
    """Harvest never APPLY this session. Later: env AND hist receipt AND non-broker effect."""
    return False


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _login_ok(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    raw = row.get("login") or CHALLENGE_LOGIN
    try:
        login = int(raw)
    except (TypeError, ValueError):
        return False, "login_unparseable"
    if login == QUARANTINE_LOGIN:
        return False, "quarantine_login_0"
    if login != CHALLENGE_LOGIN:
        return False, f"not_challenge_login_{login}"
    return True, None


def keep_signature(sleeve: str | None, family: str | None = None) -> bool:
    sl = (sleeve or "").lower()
    fam = (family or "").lower()
    if fam in KEEP_FAMS:
        return True
    return any(k in sl for k in ("spring", "vss_fxcross", "vss", "sub_mid"))


def harvest_questions() -> dict[str, Any]:
    """Extra TypeSafe questions. IDs for code; meaning in instructions."""
    return {
        "harvest_strike": {
            "type": "choice",
            "instructions": (
                "STRIKE_WHEN_RIGHT over ENTRY-legal complete state only. "
                "Ignore outcome_only_do_not_use_as_live_input (miss_type, realized R, exit_class). "
                "Geometry print alone is not a strike. alive/regime_tag/conf_band/session_fit may be "
                "PENDING or null (null_ok for regime — do not invent S14). "
                "KEEP surface residual structure doubt → E_KEEP_CAP not hard-off. "
                "full_state_dark → A_STAND_DOWN. Many incomplete voters → C_SIZE_TRIM. "
                "Do not use Lon+NY as a cage. Do not invent NEWS."
            ),
            "criteria": {
                "A_STAND_DOWN": "Stand down — do not admit",
                "B_SIZE_HALF": "Admit but size ×0.5",
                "C_SIZE_TRIM": "Admit size ×0.75 (session trim)",
                "D_FULL": "Admit full size",
                "E_KEEP_CAP": "KEEP surface: full size, max_concurrent=1, no boost",
            },
        },
        "harvest_pair_role": {
            "type": "choice",
            "instructions": (
                "Given the enumerated pair (same lens unless cite-kind), is this card "
                "WIN_LIKE, LOSE_LIKE, RELATIVE_WEAK (soft KEEP year, not invented loss), "
                "UNPAIRED, or ABSTAIN (insufficient state)?"
            ),
            "criteria": {
                "WIN_LIKE": "Named twin is the valid/strong side",
                "LOSE_LIKE": "Named twin is the fail/trap side",
                "RELATIVE_WEAK": "Still KEEP / positive but soft vs the strong twin — not an invented loss",
                "UNPAIRED": "No honest twin",
                "ABSTAIN": "Insufficient named state",
            },
        },
        "harvest_pair_kind": {
            "type": "choice",
            "instructions": "Choose among CODE-enumerated legal pair kinds. Do not invent a kind.",
            "criteria": {k: k for k in PAIR_KINDS},
        },
        "harvest_pair_quality": {
            "type": "score",
            "instructions": "How structurally similar is the enumerated twin? Cross-lens without cite-kind is 0.",
            "criteria": [
                "Unmatched or illegal cross-lens merge",
                "Weak similarity (session or conf only)",
                "Structural twin (symbol×sleeve_family×session×side×lens)",
            ],
        },
        "harvest_lens_honest": {
            "type": "noul",
            "instructions": (
                "Is exactly one of R_Challenge_book / R_Module_ATR / R_Dig_3R / R_Edge_ATR "
                "filled, matching `lens`? Two filled columns is dishonest merge."
            ),
            "criteria": {
                "true": "Sole R column matches lens",
                "false": "Merged, mis-tagged, or missing required R",
            },
        },
        "harvest_geometry_alone_neq_strike": {
            "type": "noul",
            "instructions": "Is a geometry print being treated as strike while voters are PENDING/null/dark?",
            "criteria": {
                "true": "Geometry-only — not a strike",
                "false": "Voters named enough that geometry is not alone",
            },
        },
        "harvest_alive_before_keep": {
            "type": "noul",
            "instructions": "Is alive_sleeves_for_symbol named and true? PENDING/false → do not KEEP.",
            "criteria": {
                "true": "Alive named and true",
                "false": "PENDING, false, or missing",
            },
        },
        "harvest_regime_null_ok": {
            "type": "noul",
            "instructions": "regime_tag is null/PENDING. Must NOT force STAND. Never invent S14.",
            "criteria": {
                "true": "Null regime is honest and must not force STAND",
                "false": "Named regime fights the fire",
            },
        },
        "harvest_place_would_have": {
            "type": "choice",
            "instructions": (
                "LABEL only. Retrospective: given ENTRY-legal complete state, would a place "
                "Choice have been PLACE, STAND, or DELAY? This does not send. apply=false. "
                "Writer/broker still owns prints. Default-off until Challenge hist-prove."
            ),
            "criteria": {
                "PLACE": "Named state would authorize place after hist-prove",
                "STAND": "Named state would stand",
                "DELAY": "Named state would delay",
            },
        },
    }


def r_by_lens(*, lens: str, r_value: float | None) -> dict[str, float | None]:
    if lens not in LENSES:
        raise ValueError(f"unknown lens {lens!r}")
    out = {f"R_{k}": None for k in LENSES}
    out[f"R_{lens}"] = r_value
    return out


def lens_honest(r_cols: Mapping[str, Any], lens: str) -> bool:
    filled = [k for k in LENSES if r_cols.get(f"R_{k}") is not None]
    return filled == [lens]


def split_entry_vs_expost(state: Mapping[str, Any]) -> dict[str, Any]:
    """Copy state; move EXPOST under outcome_only so strike/admit cannot see it at top-level."""
    expost_keys = (
        "miss_type",
        "exit_class",
        "close_reason",
        "R",
        "realized_r",
        "broker_net",
        "profit",
        "mfe",
        "mae",
        "won",
        "why_lost",
        "why_lost_text",
    )
    entry = json.loads(json.dumps(state, default=str))
    outcome = dict(entry.pop("outcome_only_do_not_use_as_live_input", {}) or {})
    for key in expost_keys:
        if key in entry and entry[key] is not None:
            outcome[key] = entry.pop(key)
    entry["outcome_only_do_not_use_as_live_input"] = outcome
    entry.setdefault("as_of_clock", "as_of_open_study")
    return entry


def evaluate_harvest_row(state: Mapping[str, Any]) -> dict[str, Any]:
    """POST TypeSafe. Fail-closed. Never place. Sketch — import jev_client at land time."""
    payload_state = split_entry_vs_expost(dict(state))
    if not harvest_call_enabled():
        return {
            "ok": False,
            "jev_dark": True,
            "skipped": "GTOS_JEV_TRAIN_HARVEST_CALL_off",
            "answers": {},
            "apply": False,
            "place": False,
            "source": "fail_closed",
        }
    try:
        from src.judgment.jev_client import evaluate  # type: ignore
    except Exception:
        return {
            "ok": False,
            "jev_dark": True,
            "skipped": "jev_client_import_unavailable_sketch",
            "answers": {},
            "apply": False,
            "place": False,
            "source": "fail_closed",
        }
    rec = evaluate(payload_state)
    if not rec.get("ok") or rec.get("skipped") or rec.get("error"):
        return {
            "ok": False,
            "jev_dark": True,
            "skipped": rec.get("skipped") or rec.get("error") or "jev_dark",
            "answers": {},
            "apply": False,
            "place": False,
            "source": "fail_closed",
            "jev": {k: rec.get(k) for k in ("ok", "skipped", "error", "model", "usage")},
        }
    return {**rec, "jev_dark": False, "apply": False, "place": False, "source": "jev"}


def candidate_twins(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Enumerate legal twins. Does not invent tickets or Module_ATR losses."""
    by_key: dict[tuple, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        lens = str(row.get("lens") or "Challenge_book")
        key = (
            lens,
            str(row.get("symbol") or ""),
            str(row.get("sleeve_family") or ""),
            str(row.get("session_bucket") or row.get("session") or ""),
            str(row.get("side") or "").lower(),
        )
        by_key[key].append(row)

    pairs: list[dict[str, Any]] = []
    used_lose: dict[str, int] = defaultdict(int)

    for key, group in by_key.items():
        lens, symbol, fam, session, side = key
        if lens != "Challenge_book":
            continue
        wins = [r for r in group if (_f(r.get("R")) or 0) > 0]
        losses = [r for r in group if (_f(r.get("R")) or 0) <= 0]
        for win in wins:
            if not losses:
                pairs.append(_unpaired(win, "ticket_twin"))
                continue
            lose = losses[0]
            ticket = str(lose.get("ticket"))
            used_lose[ticket] += 1
            pairs.append(
                {
                    "schema": SCHEMA_PAIR,
                    "pair_kind": "ticket_twin",
                    "pair_id": f"T_{win.get('ticket')}_{lose.get('ticket')}",
                    "lens": lens,
                    "symbols": [symbol],
                    "win_ref": win.get("ticket"),
                    "lose_ref": lose.get("ticket"),
                    "R_win": _f(win.get("R")),
                    "R_lose": _f(lose.get("R")),
                    "same_lens": True,
                    "loser_reused": used_lose[ticket] > 1,
                    "similarity": "symbol×sleeve_family×session×side×Challenge_book",
                    "place": False,
                    "apply": False,
                }
            )
    return pairs


def _unpaired(row: Mapping[str, Any], attempted: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA_PAIR,
        "pair_kind": "unpaired",
        "pair_id": f"U_{row.get('ticket')}",
        "lens": row.get("lens") or "Challenge_book",
        "win_ref": row.get("ticket") if (_f(row.get("R")) or 0) > 0 else None,
        "lose_ref": row.get("ticket") if (_f(row.get("R")) or 0) <= 0 else None,
        "same_lens": True,
        "loser_reused": False,
        "attempted_kind": attempted,
        "place": False,
        "apply": False,
    }


def emit_harvest_row(
    close: Mapping[str, Any],
    *,
    pair: Mapping[str, Any] | None = None,
    books: Any = None,
    spines: Any = None,
    store_path: Path | None = None,
) -> dict[str, Any]:
    """One Challenge close → harvest row. Never places."""
    ok, reason = _login_ok(close)
    if not ok:
        return {
            "schema": SCHEMA_ROW,
            "skipped": reason,
            "apply": False,
            "place": False,
            "never_broker_place": True,
        }
    if close.get("still_open"):
        return {
            "schema": SCHEMA_ROW,
            "skipped": "still_open",
            "ticket": close.get("ticket"),
            "apply": False,
            "place": False,
        }

    lens = str(close.get("lens") or "Challenge_book")
    if lens not in LENSES:
        return {"schema": SCHEMA_ROW, "skipped": "unknown_lens", "apply": False, "place": False}

    r_cols = r_by_lens(lens=lens, r_value=_f(close.get("R")))
    if not lens_honest(r_cols, lens):
        return {
            "schema": SCHEMA_ROW,
            "skipped": "lens_R_dishonest",
            "apply": False,
            "place": False,
        }

    sleeve = str(close.get("sleeve") or "")
    state = {
        "schema": "gtos.jev.complete_state.harvest.v1",
        "as_of_clock": "as_of_open_study",
        "identity": {
            "symbol": close.get("symbol"),
            "sleeve": sleeve,
            "sleeve_family": close.get("sleeve_family") or close.get("jev_sleeve_family"),
            "side": close.get("side"),
            "ticket": close.get("ticket"),
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "keep_surface": keep_signature(sleeve, close.get("sleeve_family")),
            "asset_class": close.get("asset_class") or close.get("asset"),
        },
        "clock": {
            "session_bucket": close.get("session") or close.get("session_ict"),
        },
        "alive_sleeves": close.get("alive_sleeves") or "PENDING",
        "regime_tag": close.get("regime_tag"),  # null_ok
        "conf_band": close.get("conf_band") or close.get("jev_conf_gate_band") or "PENDING",
        "session_fit": close.get("session_fit") or close.get("session") or "PENDING",
        "full_state_dark": close.get("full_state_dark", True),
        "n_incomplete": close.get("n_incomplete"),
        "news_join": close.get("news_join") or "STATE_MISSING",
        "occupancy": "STATE_MISSING",
        "corr_cluster": None,
        "lens": lens,
        **r_cols,
        "outcome_only_do_not_use_as_live_input": {
            "exit_class": close.get("exit_class") or close.get("exit"),
            "miss_type": close.get("miss_type") or close.get("miss"),
            "R": _f(close.get("R")),
            "r_source": close.get("r_source"),
        },
        "harvest_questions": list(harvest_questions()),
        "place": False,
        "apply": False,
    }

    jev = evaluate_harvest_row(state) if harvest_call_enabled() else {
        "ok": False,
        "jev_dark": True,
        "skipped": "GTOS_JEV_TRAIN_HARVEST_CALL_off",
        "answers": {},
        "apply": False,
        "place": False,
        "source": "fail_closed",
    }

    row = {
        "schema": SCHEMA_ROW,
        "ts_ict": None,
        "logged_at_utc": _now_utc(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "ticket": close.get("ticket"),
        "symbol": close.get("symbol"),
        "sleeve": sleeve,
        "lens": lens,
        "pair": dict(pair or {"pair_kind": "unpaired", "pair_id": None}),
        "complete_state": split_entry_vs_expost(state),
        "r_by_lens": r_cols,
        "lens_honest": lens_honest(r_cols, lens),
        "answers": jev.get("answers") or {},
        "jev": {k: jev.get(k) for k in ("ok", "skipped", "error", "model", "usage", "jev_dark", "source")},
        "jev_dark": bool(jev.get("jev_dark")),
        "apply": False,
        "place": False,
        "order_send": False,
        "news_protocol_invent": False,
        "never_merge_R": True,
        "never_broker_place": True,
        "harvest_apply_env_forced_off": True,
    }
    if store_path is not None and harvest_enabled():
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, default=str) + "\n")
        row["appended"] = True
    return row


def run_paired_harvest(
    closes: Iterable[Mapping[str, Any]],
    *,
    store_path: Path | None = None,
) -> dict[str, Any]:
    packed = [dict(c) for c in closes]
    pairs = candidate_twins(packed)
    by_ticket = {str(c.get("ticket")): c for c in packed if c.get("ticket") is not None}
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        for ref_key, role in (("win_ref", "WIN_LIKE"), ("lose_ref", "LOSE_LIKE")):
            ref = pair.get(ref_key)
            if ref is None:
                continue
            close = by_ticket.get(str(ref))
            if not close:
                continue
            tagged = dict(close)
            tagged.setdefault("lens", pair.get("lens") or "Challenge_book")
            rec = emit_harvest_row(tagged, pair={**pair, "role": role}, store_path=store_path)
            rows.append(rec)
    n_dark = sum(1 for r in rows if r.get("jev_dark"))
    return {
        "schema": SCHEMA_RUN,
        "n_closes": len(packed),
        "n_pairs": len(pairs),
        "n_rows": len(rows),
        "n_jev_dark": n_dark,
        "apply": False,
        "place": False,
        "never_broker_place": True,
        "never_merge_R": True,
        "pairs": pairs,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps({
        "sketch": True,
        "landed": False,
        "place": False,
        "apply": harvest_apply_enabled(),
        "questions": list(harvest_questions()),
        "note": "OUT-only. Do not import from writer.",
    }, indent=2))

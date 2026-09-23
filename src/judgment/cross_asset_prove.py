"""Offline CROSS_ASSET prove harness on the Challenge shadow pack.

Never places. Never reads April ``data/historical*`` as Challenge-true.
Physical size stays flow × cost — these wires are LABEL until a named
APPLY. Frozen bars match fluid label: 20 decidable / 5 non-default / 2 distinct.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .bars import (
    CHALLENGE_BAR_DIR,
    admit_challenge_peer_csv,
    challenge_search_dirs,
    challenge_tape_present,
    copy_multi_csvs_if_present,
    landed_challenge_symbols,
    normalize_symbol,
    resolve_challenge_tf,
)
from .challenge_shadow import ACCOUNT, challenge_as_of
from .cross_asset import local_cross_asset_answers
from .occupancy import corr_cluster, occupancy_book_at, trades_from_dicts
from .process_lock import LOCK_ID, PROVE_BARS_FLUID_LABEL, stamp_lock
from .world_state import assemble_world_state_v0, load_peer_books

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK = CHALLENGE_BAR_DIR / "shadow.jsonl"
DEFAULT_DEALS = CHALLENGE_BAR_DIR / "deals_since_20260909.jsonl"
DEFAULT_SLATE = CHALLENGE_BAR_DIR / "slate_20260917T104105Z_bddc8ff9fad4a254.json"
DEFAULT_SURVEY = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "CROSS_ASSET_SURVEY_V0.json"
DEFAULT_PROVE = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "CROSS_ASSET_PROVE_V0.json"

PROVE_TARGETS = (
    {
        "id": "CA-OCC-001",
        "question": "occupancy_world",
        "effect": "label",
        "needs": "deal_tape",
        "can_prove_without_peer_bars": True,
    },
    {
        "id": "CA-LIQ-001",
        "question": "session_liquidity",
        "effect": "label",
        "needs": "clock",
        "can_prove_without_peer_bars": True,
    },
    {
        "id": "CA-EVT-001",
        "question": "event_join",
        "effect": "label",
        "needs": "news_spine",
        "can_prove_without_peer_bars": True,
    },
    {
        "id": "CA-USD-001",
        "question": "usd_proxy",
        "effect": "label",
        "needs": "fx_majors_m15",
        "can_prove_without_peer_bars": False,
    },
    {
        "id": "CA-CORR-001",
        "question": "gold_usd_comove",
        "effect": "label",
        "needs": "fx_majors_m15",
        "can_prove_without_peer_bars": False,
    },
    {
        "id": "CA-RSK-001",
        "question": "risk_on_funding",
        "effect": "label",
        "needs": "us30_and_usdjpy_m15",
        "can_prove_without_peer_bars": False,
    },
    {
        "id": "CA-IDX-001",
        "question": "gold_index_comove",
        "effect": "label",
        "needs": "us30_m15",
        "can_prove_without_peer_bars": False,
    },
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def survey_challenge_surface() -> dict[str, Any]:
    """Disk survey. Challenge-true vs historical-only. Never invents bars."""
    landed = landed_challenge_symbols()
    wanted = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US30", "UK100", "EURGBP"]
    present = {sym: challenge_tape_present(sym) for sym in wanted}
    search = []
    for directory in challenge_search_dirs():
        search.append(
            {
                "path": str(directory),
                "exists": directory.is_dir(),
                "m15": sorted(p.name for p in directory.glob("*_M15.csv")) if directory.is_dir() else [],
            }
        )
    deals_path = DEFAULT_DEALS
    deal_syms: Counter[str] = Counter()
    deal_clusters: Counter[str] = Counter()
    n_deals = 0
    if deals_path.is_file():
        for rec in _iter_jsonl(deals_path):
            if not isinstance(rec, dict):
                continue
            n_deals += 1
            sym = normalize_symbol(str(rec.get("symbol") or ""))
            if not sym:
                continue
            deal_syms[sym] += 1
            deal_clusters[corr_cluster(sym) or "none"] += 1
    slate_syms: Counter[str] = Counter()
    if DEFAULT_SLATE.is_file():
        slate = json.loads(DEFAULT_SLATE.read_text(encoding="utf-8"))
        for rec in slate.get("candidates") or []:
            if isinstance(rec, dict) and rec.get("symbol"):
                slate_syms[normalize_symbol(str(rec["symbol"]))] += 1
    peer_admit: dict[str, Any] = {}
    for sym in ("EURUSD", "GBPUSD", "USDJPY", "US30"):
        path = resolve_challenge_tf(sym, "M15")
        if not path.is_file():
            continue
        admit = admit_challenge_peer_csv(path)
        peer_admit[sym] = {
            "ok": admit.get("ok"),
            "n": admit.get("n"),
            "first_utc": admit.get("first_utc"),
            "last_utc": admit.get("last_utc"),
            "path": path.name,
            "offset_ok": admit.get("offset_ok"),
        }
    return {
        "schema": "gtos.judgment.cross_asset_survey.v0",
        "account_surface": ACCOUNT,
        "landed_challenge_symbols": landed,
        "wanted_challenge_m15": present,
        "n_landed": len(landed),
        "multi_dir_present": any(d["exists"] and any("EURUSD" in n or "GBPUSD" in n for n in d["m15"]) for d in search),
        "search_dirs": search,
        "deal_symbols": dict(deal_syms),
        "deal_clusters": dict(deal_clusters),
        "n_deal_rows": n_deals,
        "slate_candidate_symbols": dict(slate_syms),
        "april_historical_is_not_challenge": True,
        "dxy_is_not_challenge": True,
        "dxy_path": "data/DXY_D1.csv",
        "historical_packs_exist_but_not_used": [
            "exports/multi_instrument/EURUSD_M15.csv",
            "exports/multi_instrument/GBPUSD_M15.csv",
            "exports/multi_instrument/USDJPY_M15.csv",
            "exports/multi_instrument/US30_cash_M15.csv",
        ],
        "chair_vps_claim_20260918": {
            "EURUSD": {"claimed": True, "through": "2026-09-18T03:00Z", "hydrated_here": bool(present.get("EURUSD"))},
            "GBPUSD": {"claimed": True, "through": "2026-09-18T03:00Z", "hydrated_here": bool(present.get("GBPUSD"))},
            "USDJPY": {"claimed": True, "through": "2026-09-18T03:00Z", "hydrated_here": bool(present.get("USDJPY"))},
            "US30": {
                # First VPS pass failed symbol resolve. Chair zip 2026-09-18
                # landed US30.cash / US30_cash / US30 aliases — claimed once on disk.
                "claimed": bool(present.get("US30")),
                "through": "2026-09-18T03:00Z" if present.get("US30") else None,
                "hydrated_here": bool(present.get("US30")),
                "first_pass": "ftmo_symbol_resolve_failed",
                "aliases_on_disk": (
                    ["US30.cash", "US30_cash", "US30"] if present.get("US30") else []
                ),
                "source": "chair_zip_peer_multi_20260918" if present.get("US30") else None,
                "reason": None if present.get("US30") else "ftmo_symbol_resolve_failed",
            },
        },
        "chair_pull_still_open": [
            sym
            for sym in ("EURUSD", "GBPUSD", "USDJPY", "US30")
            if not present.get(sym)
        ],
        "this_vm_hydrated_from_vps": bool(
            present.get("EURUSD") and present.get("GBPUSD") and present.get("USDJPY")
        ),
        "hydrate_channel": (
            "chair_attached_zip"
            if present.get("EURUSD") and present.get("GBPUSD") and present.get("USDJPY")
            else None
        ),
        "peer_admit": peer_admit,
        "never_place": True,
    }


def _row_as_of(row: dict[str, Any]) -> datetime | None:
    clock = (row.get("state") or {}).get("clock") or {}
    raw = clock.get("as_of_utc") or (row.get("state") or {}).get("identity", {}).get("decision_bar_iso")
    if raw:
        text = str(raw).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    pos = {
        "open_time_utc": row.get("open_time_utc") or ((row.get("sit") or {}).get("sit_utc")),
        "open_time_server": row.get("open_time_server"),
    }
    try:
        return challenge_as_of(pos)
    except Exception:
        return None


def _value_for_target(target: dict[str, Any], world: dict[str, Any], answers: dict[str, Any]) -> Any:
    qid = target["question"]
    if qid == "usd_proxy":
        named = (world.get("usd_proxy") or {}).get("named")
        return named if named not in {None, "unassembled"} else None
    if qid == "event_join":
        ev = world.get("event_join") or {}
        if ev.get("spine_empty"):
            return None
        return bool(
            ev.get("usd_high_in_window")
            or ev.get("gbp_high_in_window")
            or ev.get("jpy_high_in_window")
            or ev.get("eur_high_in_window")
        )
    block = answers.get(qid) or {}
    if block.get("choice") is not None:
        return block.get("choice")
    return block.get("score")


def prove_target(rows: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    bars = PROVE_BARS_FLUID_LABEL
    decidable: list[Any] = []
    moved: list[Any] = []
    values: list[Any] = []
    for rec in rows:
        world = rec.get("world") or {}
        answers = rec.get("answers") or {}
        value = _value_for_target(target, world, answers)
        qid = target["question"]
        if qid in answers:
            ok = bool((answers.get(qid) or {}).get("decidable"))
        elif qid == "usd_proxy":
            ok = value is not None
        elif qid == "event_join":
            ok = (world.get("event_join") or {}).get("spine_empty") is False
        else:
            ok = value is not None
        if not ok:
            continue
        decidable.append(rec)
        values.append(value)
        default = 1.0 if qid in {"session_liquidity", "occupancy_world"} else None
        if value not in {None, default, "unassembled", "no_clear"}:
            moved.append(rec)
    distinct = {json.dumps(v, default=str) for v in values}
    reasons: list[str] = []
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(f"decidable {len(decidable)} < {bars['min_decidable']}")
    if len(moved) < int(bars["min_non_default"]):
        reasons.append(f"non_default {len(moved)} < {bars['min_non_default']}")
    if len(distinct) < int(bars["min_distinct"]) and len(decidable) >= int(bars["min_decidable"]):
        reasons.append(f"distinct {len(distinct)} < {bars['min_distinct']} — constant_on_this_tape")
    if not target["can_prove_without_peer_bars"]:
        n_peers = max((r.get("world") or {}).get("n_peers_present") or 0 for r in rows) if rows else 0
        if n_peers == 0:
            reasons.append("peer Challenge M15 not landed — do not wear April historical")
    verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    return {
        "id": target["id"],
        "question": target["question"],
        "effect": "label",
        "needs": target["needs"],
        "verdict": verdict,
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_distinct": len(distinct),
        "vals": dict(Counter(json.dumps(v, default=str) for v in values)),
        "reasons": reasons,
        "apply": False,
        "physical_size_stays_flow_x_cost": True,
        "research_only": True,
    }


def score_pack_rows(
    pack_path: Path | None = None,
    *,
    deals_path: Path | None = None,
) -> list[dict[str, Any]]:
    pack = pack_path or DEFAULT_PACK
    deals = list(_iter_jsonl(deals_path or DEFAULT_DEALS))
    tape = trades_from_dicts(deals, stamp=challenge_as_of) if deals else None
    peers = load_peer_books()
    rows: list[dict[str, Any]] = []
    if pack.is_file():
        source_rows = list(_iter_jsonl(pack))
    else:
        source_rows = []
    for rec in source_rows:
        as_of = _row_as_of(rec)
        if as_of is None:
            continue
        state = rec.get("state") or {}
        identity = state.get("identity") or {}
        news = state.get("news") or {}
        clock = state.get("clock") or {}
        world = assemble_world_state_v0(
            as_of_utc=as_of,
            symbol=str(identity.get("symbol") or "XAUUSD"),
            side=identity.get("side"),
            peer_books=peers,
            xau_books=peers.get("XAUUSD"),
            trades=tape,
            news=news,
            utc_hour=clock.get("utc_hour") or as_of.hour,
            is_friday=bool(clock.get("is_friday")),
            origin_organism="f5_challenge",
            this_ticket=rec.get("ticket") or identity.get("candidate_id"),
        )
        compose = rec.get("compose") or {}
        rows.append(
            {
                "ticket": rec.get("ticket"),
                "kind": rec.get("kind"),
                "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "side": identity.get("side"),
                "symbol": identity.get("symbol") or "XAUUSD",
                "state": {
                    "identity": identity,
                    "completeness": state.get("completeness") or {},
                    "news": news,
                    "cost": state.get("cost") or {},
                    "occupancy": state.get("occupancy") or {},
                    "timeframes": state.get("timeframes") or {},
                    "clock": clock,
                },
                "world": world,
                "answers": local_cross_asset_answers(world),
                "combined_live_tilt": compose.get("combined_live_tilt"),
                "live_size_tilt": compose.get("live_size_tilt"),
                "live_cost_tilt": compose.get("live_cost_tilt"),
            }
        )
    return rows


def run_prove(
    *,
    pack_path: Path | None = None,
    deals_path: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    copy_result = copy_multi_csvs_if_present()
    prior_verdicts: dict[str, str] = {}
    prior_doc: dict[str, Any] = {}
    if DEFAULT_PROVE.is_file():
        try:
            prior_doc = json.loads(DEFAULT_PROVE.read_text(encoding="utf-8"))
            prior_verdicts = {t["id"]: t["verdict"] for t in prior_doc.get("targets") or [] if t.get("id")}
        except (OSError, json.JSONDecodeError, TypeError):
            prior_verdicts = {}
            prior_doc = {}
    survey = survey_challenge_surface()
    rows = score_pack_rows(pack_path, deals_path=deals_path)
    results = [prove_target(rows, t) for t in PROVE_TARGETS]
    flips = []
    for rec in results:
        old = prior_verdicts.get(rec["id"])
        if old and old != rec["verdict"]:
            flips.append({"id": rec["id"], "from": old, "to": rec["verdict"]})
    if flips:
        hydrate_event = {
            "id": "chair_zip_peer_multi_20260918",
            "channel": survey.get("hydrate_channel") or "chair_attached_zip",
            "flips": flips,
            "landed": survey["landed_challenge_symbols"],
            "apply_stays_false": True,
            "new_size_axis_applied": False,
        }
    else:
        hydrate_event = prior_doc.get("hydrate_event") or None
        if hydrate_event is None and prior_doc.get("flips_vs_prior"):
            hydrate_event = {
                "id": "chair_zip_peer_multi_20260918",
                "channel": survey.get("hydrate_channel") or "chair_attached_zip",
                "flips": list(prior_doc.get("flips_vs_prior") or []),
                "landed": survey["landed_challenge_symbols"],
                "apply_stays_false": True,
                "new_size_axis_applied": False,
            }
    tilts = [r.get("combined_live_tilt") for r in rows if r.get("combined_live_tilt") is not None]
    lock = stamp_lock()
    payload = {
        "schema": "gtos.judgment.cross_asset_prove.v0",
        **lock,
        "process_lock": LOCK_ID,
        "n_rows": len(rows),
        "survey": {
            "landed_challenge_symbols": survey["landed_challenge_symbols"],
            "wanted_challenge_m15": survey["wanted_challenge_m15"],
            "deal_clusters": survey["deal_clusters"],
            "april_historical_is_not_challenge": True,
            "dxy_is_not_challenge": True,
            "chair_vps_claim_20260918": survey.get("chair_vps_claim_20260918"),
            "this_vm_hydrated_from_vps": survey.get("this_vm_hydrated_from_vps"),
            "hydrate_channel": survey.get("hydrate_channel"),
            "peer_admit": survey.get("peer_admit"),
        },
        "bars": dict(PROVE_BARS_FLUID_LABEL),
        "targets": results,
        "n_proved_shadow": sum(1 for r in results if r["verdict"] == "PROVED_SHADOW"),
        "n_not_proved": sum(1 for r in results if r["verdict"] == "NOT_PROVED"),
        "hydrate": {
            "copy": {
                "src": copy_result.get("src"),
                "n_copied": copy_result.get("n_copied"),
                "n_rejected": copy_result.get("n_rejected"),
                "rejected": copy_result.get("rejected"),
                "april_historical_used": False,
            },
            "this_vm_hydrated_from_vps": survey.get("this_vm_hydrated_from_vps"),
            "hydrate_channel": survey.get("hydrate_channel"),
            "chair_vps_claim_20260918": survey.get("chair_vps_claim_20260918"),
            "peer_admit": survey.get("peer_admit"),
        },
        "flips_vs_prior": flips,
        "hydrate_event": hydrate_event,
        "physical_size": {
            "stays_flow_x_cost": True,
            "n_rows_with_combined_tilt": len(tilts),
            "new_size_axis_applied": False,
            "spoken": "Cross-asset answers are LABEL. They do not multiply live_flow × live_cost.",
        },
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "envelope_walls_stay_integers": True,
        "next_prove_targets": [
            t["id"] for t in results if t["verdict"] == "NOT_PROVED"
        ],
        "no_ca_apply_flip": True,
        "apply_any": any(bool(t.get("apply")) for t in results),
    }
    if write:
        DEFAULT_SURVEY.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_SURVEY.write_text(json.dumps(survey, indent=2) + "\n", encoding="utf-8")
        DEFAULT_PROVE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payload["survey_path"] = str(DEFAULT_SURVEY.relative_to(REPO_ROOT))
        payload["prove_path"] = str(DEFAULT_PROVE.relative_to(REPO_ROOT))
    return payload

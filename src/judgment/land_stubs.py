"""Dig D land stubs — APPLY_CONSUME vs KILL for closed Dig F/E/C recipes.

Challenge login ``0`` / ns ``operator`` only. This module
never places, remints, flattens, or invents ``NEWS_PROTOCOL``.
``pack1b_beaten`` stays False. redacted_account / W7 books are out of scope.

Chair board ``DIG_LAND_D_LANE_EMPTY_20260921`` already emptied the
implement-stub lane. Dig D lands those dispositions in code:

* APPLY_CONSUME: Dig C 0-8 + Dig F five + A1 observe
* KILL: ``ORDER_ENSEMBLE_SHUFFLE`` / ``OD-10`` / ``OD-12``
* resting SHADOW = 0 under judgment / warroom implement-stub paths

This module never flips live broker APPLY env (``GTOS_JEV_APPLY_LIVE``,
``GTOS_JEV_FLUID_GATES_APPLY``).
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .a1_log import maybe_observe_ub_auth_010, maybe_observe_ub_plc_017
from .a1_log import observe as a1_observe_row
from .a1_log import observe_fluid_inventory, observe_sel_v4_002
from .apply_size import CHALLENGE_LOGIN as APPLY_LOGIN
from .apply_size import CHALLENGE_NS as APPLY_NS
from .apply_size import apply_live_env, honor_f5_scaler_risk
from .challenge import CHALLENGE_LOGIN, CHALLENGE_NS
from .flags import APPLY_ENV, CHALLENGE_PROVE_ONLY_DUAL_FLAGS, EVERYWHERE_ENV, SHADOW_ENV
from .host_occupancy import host_occupancy_governor
from .host_sites import vps_land_plan
from .process_lock import APPLIED_WIRES, ENVELOPE_WALL_IDS, WIRE_CA_SIZE, WIRE_COST, WIRE_FLOW
from .s16_flags import APPLY_ENV as DIG_APPLY_ENV
from .s16_flags import SHADOW_ENV as DIG_SHADOW_ENV
from .s16_flags import s16_apply_enabled

SCHEMA = "gtos.judgment.dig_d_land_stubs.v1"
STEAL = "DIG_D_LAND_STUBS"
LOGIN = CHALLENGE_LOGIN
NAMESPACE = "gtos.astra.jev_trial.dig_d_land_stubs.v1"
CHAIR_BOARD = "DIG_LAND_D_LANE_EMPTY_20260921"

REPO_ROOT = Path(__file__).resolve().parents[2]
STUBS_PATH = REPO_ROOT / "judgment" / "astra" / "dig_d_land_stubs.json"
APPLIED_NAMED_PATH = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "APPLIED_NAMED.json"
P0_STUBS_PATH = REPO_ROOT / "judgment" / "astra" / "p0_unwired_shadow_hook_stubs.json"
S16_MAP_PATH = REPO_ROOT / "judgment" / "astra" / "s16_guard_map.json"
BOARD_PATH = REPO_ROOT / "research" / "warroom" / "DIG_LAND_D_LANE_EMPTY_20260921.md"

CLOSED_LIVE = frozenset({"APPLY_CONSUME", "APPLY", "APPLIED_NAMED"})
CLOSED_DEAD = frozenset({"KILL"})
RESTING = frozenset({"SHADOW", "IN_PROVE", "APPLY_CANDIDATE"})

# Chair-live consume flags already on Challenge. Not new broker flags.
CHAIR_LIVE_FLAGS = {
    "CONF_ORDER_CONSUME": "1",
    "PLACE_APPLY": "1",
    "PLACE_ENSEMBLE": "1",
}

BROKER_APPLY_ENVS = ("GTOS_JEV_APPLY_LIVE", "GTOS_JEV_FLUID_GATES_APPLY")

DIG_C_WIRES = (WIRE_FLOW, WIRE_COST, WIRE_CA_SIZE)

DIG_F_FIVE = (
    "option_order_sensitivity",
    "state_evidence_sufficiency",
    "jev_repeatability_probe",
    "noul_vs_choice_shape",
    "od_13",
)
KILL_ORDER = (
    "order_ensemble_shuffle",
    "od_10_perm_avg_research_router",
    "od_12_yesno_reverse_regression",
)
DIG_C_0_8 = (
    "dig_c_0_admit_observe",
    "dig_c_1_cost_screen_observe",
    "dig_c_2_named_size_tilts",
    "dig_c_3_physical_lot_gate",
    "dig_c_4_occupancy_governor",
    "dig_c_5_prove_c_stamp_fix",
    "dig_c_6_fluid_inventory_observe",
    "dig_c_7_sel_v4_002_research_only",
    "dig_c_8_envelope_walls",
)
A1_OBSERVE = "a1_observe"
DIG_E_APPLY = ("EVERYWHERE_SHADOW", "TRAIN_HARVEST")
DIG_E_KILL = ("DIG_MULTI_STAGE_GUARD",)

DIG_C_ALIASES = {
    "f5_xau_flow_alignment_size_tilt": "dig_c_2_named_size_tilts",
    "F5-JEV-004": "dig_c_2_named_size_tilts",
    "ca_cross_asset_size_tilt": "dig_c_2_named_size_tilts",
    "HOST_PROVE_C_STAMP_FIX": "dig_c_5_prove_c_stamp_fix",
    "ORDER_ENSEMBLE_SHUFFLE": "order_ensemble_shuffle",
    "OD-10": "od_10_perm_avg_research_router",
    "OD-12": "od_12_yesno_reverse_regression",
    "od_10": "od_10_perm_avg_research_router",
    "od_12": "od_12_yesno_reverse_regression",
}

class KilledLandStubError(RuntimeError):
    """Raised when a KILL recipe is invoked on the live path."""


class _DummyIntent:
    stop_dist = 0.0
    symbol = "XAUUSD"
    sleeve = "crypto"


class _DummyTick:
    bid = 0.0
    ask = 0.0


def pack1b_beaten() -> bool:
    """Lane constraint: pack1b is not beaten. Never invent a True."""

    return False


def apply_env_untouched(*, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Read broker APPLY envs. Dig D never writes them."""

    env = environ if environ is not None else os.environ
    return {
        "flipped": False,
        "broker_apply_env_set_by_dig_d": False,
        "reads": {name: str(env.get(name, "") or "") for name in BROKER_APPLY_ENVS},
        "never_place": True,
    }


def load_land_stubs(path: Path | str | None = None) -> dict[str, Any]:
    target = Path(path) if path is not None else STUBS_PATH
    doc = json.loads(target.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"unexpected land-stub schema: {doc.get('schema')}")
    if str(doc.get("login")) != LOGIN:
        raise ValueError("land stubs bind Challenge 0 only")
    if doc.get("pack1b_beaten") is not False:
        raise ValueError("pack1b_beaten must stay false")
    if doc.get("redacted_account") is not False:
        raise ValueError("redacted_account is out of scope")
    if doc.get("never_place") is not True:
        raise ValueError("land stubs must never place")
    if doc.get("news_invent") is not False:
        raise ValueError("NEWS invent is forbidden")
    if doc.get("chair_board") != CHAIR_BOARD:
        raise ValueError(f"chair board must be {CHAIR_BOARD}")
    if int(doc.get("resting_shadow", -1)) != 0:
        raise ValueError("resting_shadow must be 0")
    return doc


def recipes(doc: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    packed = doc if doc is not None else load_land_stubs()
    rows = packed.get("recipes")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _canonical(recipe_id: str) -> str:
    return DIG_C_ALIASES.get(recipe_id, recipe_id)


def lookup(recipe_id: str, *, doc: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    want = _canonical(recipe_id)
    packed = doc if doc is not None else load_land_stubs()
    for row in recipes(packed):
        if row.get("id") == want or row.get("id") == recipe_id:
            return row
        aliases = row.get("aliases") or []
        if recipe_id in aliases or want in aliases:
            return row
    return None


def flip_table(doc: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every closed-recipe flip Dig D stamped."""

    out = []
    for row in recipes(doc):
        out.append(
            {
                "id": row["id"],
                "board": row.get("board"),
                "board_name": row.get("board_name"),
                "prior_status": row.get("prior_status"),
                "status": row.get("status"),
                "live_path": bool(row.get("live_path")),
                "flags": list(row.get("flags") or []),
            }
        )
    return out


def live_path_stubs(doc: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Stubs still on the Challenge live path. KILL is excluded."""

    return [row for row in recipes(doc) if row.get("status") in CLOSED_LIVE and row.get("live_path") is True]


def killed_stubs(doc: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    return [row for row in recipes(doc) if row.get("status") == "KILL"]


def resting_closed_recipes(doc: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Closed Dig F/E/C recipes that still rest as SHADOW / IN_PROVE / APPLY_CANDIDATE."""

    return [row for row in recipes(doc) if row.get("status") in RESTING]


def assert_no_resting_shadow(doc: Mapping[str, Any] | None = None) -> None:
    leftover = resting_closed_recipes(doc)
    if leftover:
        ids = [row.get("id") for row in leftover]
        raise AssertionError(f"resting SHADOW/IN_PROVE stubs remain for closed recipes: {ids}")


def scan_implement_stub_resting() -> list[str]:
    """Resting SHADOW/IN_PROVE/APPLY_CANDIDATE on implement-stub paths only.

    Fluid-gate inventories stay out of this scan. P0 warroom hooks are
    apply=false PARKED, not implement stubs.
    """

    hits: list[str] = []
    packed = load_land_stubs()
    for row in resting_closed_recipes(packed):
        hits.append(f"judgment/astra/dig_d_land_stubs.json:{row.get('id')}:{row.get('status')}")
    scoped = packed.get("out_of_scope") or {}
    if isinstance(scoped, Mapping):
        for name, row in scoped.items():
            if isinstance(row, Mapping) and row.get("status") in RESTING:
                hits.append(f"judgment/astra/dig_d_land_stubs.json:out_of_scope.{name}:{row.get('status')}")
    if int(packed.get("resting_shadow", -1)) != 0:
        hits.append("judgment/astra/dig_d_land_stubs.json:resting_shadow")
    for stub in sorted((REPO_ROOT / "judgment" / "astra").glob("*stub*")):
        if stub.name == "dig_d_land_stubs.json" or not stub.is_file() or stub.suffix != ".json":
            continue
        try:
            payload = json.loads(stub.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("status") in RESTING and payload.get("implement_stub") is not False:
            hits.append(f"judgment/astra/{stub.name}:{payload.get('status')}")
        for row in payload.get("recipes") or []:
            if isinstance(row, Mapping) and row.get("status") in RESTING:
                hits.append(f"judgment/astra/{stub.name}:{row.get('id')}:{row.get('status')}")
    warroom = REPO_ROOT / "research" / "warroom"
    if warroom.is_dir():
        for path in sorted(warroom.glob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                for row in payload.get("recipes") or []:
                    if isinstance(row, Mapping) and row.get("status") in RESTING:
                        hits.append(f"{path.relative_to(REPO_ROOT)}:{row.get('id')}:{row.get('status')}")
    return hits


def _base_receipt(recipe_id: str, *, status: str, enabled: bool, live_path: bool, **extra: Any) -> dict[str, Any]:
    row = {
        "id": recipe_id,
        "enabled": enabled,
        "status": status,
        "live_path": live_path,
        "broker_effect": False,
        "never_place": True,
        "never_order_send": True,
        "news_invent": False,
        "pack1b_beaten": False,
        "redacted_account": False,
        "apply_env_flipped": False,
        "login": LOGIN,
        "ns": CHALLENGE_NS,
        "chair_board": CHAIR_BOARD,
    }
    row.update(extra)
    return row


def consume(recipe_id: str, *, doc: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Consume a closed stub. KILL is disabled. APPLY_CONSUME never places."""

    canonical = _canonical(recipe_id)
    row = lookup(canonical, doc=doc)
    if row is None:
        raise KeyError(recipe_id)
    status = str(row.get("status") or "")
    if status == "KILL":
        return _base_receipt(
            canonical,
            status="KILL",
            enabled=False,
            live_path=False,
            note=row.get("kill_reason") or "disabled_from_live_path",
        )
    if status not in CLOSED_LIVE:
        raise ValueError(f"{recipe_id} is not APPLY_CONSUME/KILL closed: {status}")
    if canonical == A1_OBSERVE:
        return consume_a1_observe(doc=doc)
    if canonical in DIG_C_0_8:
        return consume_dig_c(DIG_C_0_8.index(canonical), doc=doc)
    if canonical in DIG_F_FIVE:
        return consume_dig_f(canonical, doc=doc)
    return _base_receipt(
        canonical,
        status=status,
        enabled=True,
        live_path=True,
        flags=list(row.get("flags") or []),
        wire=row.get("wire") or "wired",
    )


def consume_dig_f(recipe_id: str, *, doc: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """APPLY_CONSUME the five Dig F MAX_POTENTIAL recipes. No broker APPLY env."""

    row = lookup(recipe_id, doc=doc)
    if row is None or row.get("status") != "APPLY_CONSUME":
        raise ValueError(f"{recipe_id} is not Dig F APPLY_CONSUME")
    extra: dict[str, Any] = {
        "flags": list(row.get("flags") or []),
        "wire": "wired",
        "place_choice_importable": False,
        "note": "consume stamp; hash-path lives in Dig F place_choice when merged",
    }
    try:
        from . import place_choice as _place_choice  # type: ignore

        extra["place_choice_importable"] = hasattr(_place_choice, "stamp_place_choice")
        extra["note"] = "place_choice consume wired"
    except ImportError:
        pass
    return _base_receipt(recipe_id, status="APPLY_CONSUME", enabled=True, live_path=True, **extra)


def consume_a1_observe(*, doc: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """APPLY_CONSUME A1 observe. Never flips APPLY env. Never places."""

    del doc
    row = a1_observe_row(
        "A1-OBS-CONSUME",
        {"login": LOGIN, "ns": CHALLENGE_NS},
        extra={"land": "DIG_D", "chair_board": CHAIR_BOARD, "observe_only": True},
    )
    return _base_receipt(
        A1_OBSERVE,
        status="APPLY_CONSUME",
        enabled=True,
        live_path=True,
        flags=["GTOS_JEV_A1_LOG", "GTOS_JEV_ALIVE_SHADOW"],
        wire="wired",
        observe=True,
        apply=False,
        observed=not bool(row.get("skipped")),
        skipped=row.get("skipped"),
        shadow_log_only=True,
        note="observe only; do not flip GTOS_JEV_APPLY_LIVE",
    )


def consume_dig_c(index: int, *, doc: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """APPLY_CONSUME one Dig C land-order site (0-8). Invokes live code."""

    if index < 0 or index > 8:
        raise ValueError("Dig C index must be 0-8")
    recipe_id = DIG_C_0_8[index]
    row = lookup(recipe_id, doc=doc)
    if row is None:
        raise KeyError(recipe_id)
    land = vps_land_plan()
    invoked: dict[str, Any] = {"index": index, "land_order": land["land_order"][index]}
    if index == 0:
        maybe_observe_ub_auth_010({"status": "observe_only", "realized": []})
        invoked["fn"] = "maybe_observe_ub_auth_010"
    elif index == 1:
        maybe_observe_ub_plc_017(_DummyIntent(), _DummyTick(), None)
        invoked["fn"] = "maybe_observe_ub_plc_017"
        invoked["must_not_mutate_cost_skip"] = True
    elif index == 2:
        check = verify_dig_c_live_flags()
        invoked["fn"] = "verify_dig_c_live_flags"
        invoked["wires"] = list(check.get("wires") or [])
        invoked["ok"] = check.get("ok")
    elif index == 3:
        invoked["fn"] = "apply_live_env"
        invoked["apply_live_env_read"] = apply_live_env()
        invoked["apply_env_flipped"] = False
        invoked["note"] = "physical gate already live; Dig D does not set GTOS_JEV_APPLY_LIVE"
    elif index == 4:
        pack = host_occupancy_governor(
            symbol="XAUUSD",
            as_of=None,
            sleeve="crypto",
            opens=[],
            closed_doc={"trades": []},
        )
        invoked["fn"] = "host_occupancy_governor"
        invoked["has_occupancy"] = "occupancy" in pack
        invoked["has_governor"] = "governor" in pack
    elif index == 5:
        honored, stamp = honor_f5_scaler_risk(
            150.0,
            login=LOGIN,
            ns=CHALLENGE_NS,
            trade_params={"jev_combined_live_tilt": 1.0},
        )
        invoked["fn"] = "honor_f5_scaler_risk"
        invoked["honored"] = honored
        invoked["scaler_honor"] = stamp.get("f5_scaler_honor")
    elif index == 6:
        fluid = observe_fluid_inventory(
            {"login": LOGIN, "ns": CHALLENGE_NS},
            extra={"land": "DIG_D", "site": "dig_c_6"},
        )
        invoked["fn"] = "observe_fluid_inventory"
        invoked["skipped"] = fluid.get("skipped")
        invoked["n_fluid"] = fluid.get("n_fluid")
    elif index == 7:
        sel = observe_sel_v4_002({"research_only": True})
        invoked["fn"] = "observe_sel_v4_002"
        invoked["gate_id"] = sel.get("gate_id")
        invoked["not_imported_from_selector_v4"] = True
    elif index == 8:
        invoked["fn"] = "ENVELOPE_WALL_IDS"
        invoked["walls"] = sorted(ENVELOPE_WALL_IDS)
        invoked["stay_integers"] = True
    return _base_receipt(
        recipe_id,
        status="APPLY_CONSUME",
        enabled=True,
        live_path=True,
        flags=list(row.get("flags") or []),
        wire="wired",
        invoked=invoked,
    )


def refuse_killed(recipe_id: str) -> None:
    """KILL recipes are deleted from the live path."""

    canonical = _canonical(recipe_id)
    if canonical not in KILL_ORDER:
        raise KeyError(recipe_id)
    raise KilledLandStubError(f"{canonical} KILL — disabled from live path")


def apply_order_ensemble_shuffle(*_args: Any, **_kwargs: Any) -> None:
    refuse_killed("order_ensemble_shuffle")


def apply_od_10_perm_avg_research_router(*_args: Any, **_kwargs: Any) -> None:
    refuse_killed("od_10_perm_avg_research_router")


def apply_od_12_yesno_reverse_regression(*_args: Any, **_kwargs: Any) -> None:
    refuse_killed("od_12_yesno_reverse_regression")


def apply_order_ensemble(*_args: Any, **_kwargs: Any) -> None:
    refuse_killed("ORDER_ENSEMBLE_SHUFFLE")


def sidecar_stamp(*, doc: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Admit-sidecar stamp. Resting SHADOW is 0. Never places."""

    packed = doc if doc is not None else load_land_stubs()
    leftover = resting_closed_recipes(packed)
    if leftover:
        raise AssertionError(f"resting SHADOW stubs on land board: {[r.get('id') for r in leftover]}")
    apply_ids = [row["id"] for row in recipes(packed) if row.get("status") == "APPLY_CONSUME"]
    kill_ids = [row["id"] for row in killed_stubs(packed)]
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        "chair_board": CHAIR_BOARD,
        "login": LOGIN,
        "ns": CHALLENGE_NS,
        "status": "LANE_EMPTY",
        "apply_consume": apply_ids,
        "kill": kill_ids,
        "dig_c_0_8": list(DIG_C_0_8),
        "dig_f_five": list(DIG_F_FIVE),
        "a1_observe": A1_OBSERVE,
        "kill_order": list(KILL_ORDER),
        "resting_shadow": 0,
        "broker_effect": False,
        "never_place": True,
        "never_order_send": True,
        "news_invent": False,
        "pack1b_beaten": False,
        "redacted_account": False,
        "apply_env_flipped": False,
        "apply_env": apply_env_untouched(),
    }


def verify_dig_c_live_flags(
    *,
    applied_path: Path | str | None = None,
    p0_path: Path | str | None = None,
) -> dict[str, Any]:
    """Dig C already-APPLY stubs must match live named-wire + physical flags."""

    applied = json.loads(
        Path(applied_path or APPLIED_NAMED_PATH).read_text(encoding="utf-8")
    )
    p0 = json.loads(Path(p0_path or P0_STUBS_PATH).read_text(encoding="utf-8"))
    mismatches: list[str] = []

    named = list(applied.get("applied_wires") or [])
    if set(named) != set(APPLIED_WIRES):
        mismatches.append(f"applied_wires {named} != process_lock {list(APPLIED_WIRES)}")
    if set(APPLIED_WIRES) != set(DIG_C_WIRES):
        mismatches.append(f"APPLIED_WIRES drifted from Dig C set {list(DIG_C_WIRES)}")
    if applied.get("verdict") != "APPLIED_NAMED":
        mismatches.append("APPLIED_NAMED verdict missing")
    if applied.get("wire_apply") is not True:
        mismatches.append("wire_apply is not true")

    gate = applied.get("physical_lot_gate") or {}
    if str(gate.get("env") or "") != "GTOS_JEV_APPLY_LIVE=1":
        mismatches.append("physical gate env is not GTOS_JEV_APPLY_LIVE=1")
    try:
        login_ok = int(gate.get("login")) == int(APPLY_LOGIN) == int(LOGIN)
    except (TypeError, ValueError):
        login_ok = False
    if not login_ok:
        mismatches.append("physical gate login is not 0")
    if str(gate.get("ns") or "") != APPLY_NS or APPLY_NS != CHALLENGE_NS:
        mismatches.append("physical gate ns is not operator")
    if gate.get("w7_armed_books") != "never":
        mismatches.append("W7 armed books must stay never")

    if p0.get("apply") is not False:
        mismatches.append("P0 warroom_shadow stubs must stay apply=false")
    hooks = p0.get("hooks") if isinstance(p0.get("hooks"), Mapping) else {}
    for name, hook in hooks.items():
        if isinstance(hook, Mapping) and hook.get("apply") is not False:
            mismatches.append(f"P0 hook {name} apply is not false")

    return {
        "ok": not mismatches,
        "mismatches": mismatches,
        "status": "APPLY_CONSUME",
        "wires": named,
        "physical_env": "GTOS_JEV_APPLY_LIVE",
        "login": LOGIN,
        "ns": CHALLENGE_NS,
        "p0_warroom_shadow_apply": False,
        "never_place": True,
        "apply_env_flipped": False,
    }


def challenge_prove_track() -> dict[str, Any]:
    """Dig E: S16 dual flags are off the Challenge prove-only track."""

    return {
        "dual_flags": sorted(CHALLENGE_PROVE_ONLY_DUAL_FLAGS),
        "includes_fluid_shadow": SHADOW_ENV in CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
        "includes_fluid_apply": APPLY_ENV in CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
        "includes_everywhere_alias": EVERYWHERE_ENV in CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
        "includes_s16_shadow": DIG_SHADOW_ENV in CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
        "includes_s16_apply": DIG_APPLY_ENV in CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
        "s16_apply_enabled": s16_apply_enabled(),
        "s16_apply_enabled_force": s16_apply_enabled(force=True),
    }


def land_module_has_order_send() -> int:
    """AST count. Must stay 0 — Dig D never broker-sends."""

    path = Path(__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    count = 0
    banned = {"order_send", "open_trade"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in banned:
                count += 1
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            if "mt5" in mod or "book_owner" in mod or "redacted_account" in mod:
                count += 1
    return count

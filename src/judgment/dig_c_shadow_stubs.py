"""Dig C SHADOW stub registry — stubs 1–5 + 8 only.

Chair WORD 2026-09-21: Merge Dig C SHADOW stubs 1–5 + 8 into warroom_shadow.
Skip 0/6/7 (already live on Challenge). Chair APPLY via GTOS_JEV_DIG_C_APPLY=1. Dig never broker-sends.
Dig does not broker-send. No NEWS invent. Default-off via GTOS_JEV_DIG_C_SHADOW=1.

FANOUT_DEDUP is observe-path note only — does NOT change a1_log live behavior
unless a safe no-op flag already exists. policy_c / usage_router / automode /
ablation: registry + payload stamp only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, MutableMapping

# Merge set only (skip 0 conf / 6 place_choice / 7 SimpleJev VETO — live on Challenge)
STUB_IDS: dict[int, str] = {
    1: "SHADOW_DIG_C_FANOUT_ONE_POST",
    2: "SHADOW_DIG_C_HARVEST_EMITTER",
    3: "SHADOW_DIG_C_POLICY_C_SHADOW_EVALUATE",
    4: "SHADOW_DIG_C_USAGE_ROUTER_LABEL",
    5: "SHADOW_DIG_C_AUTOMODE_GATE_DECISION_POINTS",
    8: "SHADOW_DIG_C_ABLATION_BEFORE_APPLY",
}

SHORT_IDS: dict[int, str] = {
    1: "fanout_one_post",
    2: "harvest_emitter",
    3: "policy_c_shadow_evaluate",
    4: "usage_router_label",
    5: "automode_gate_decision_points",
    8: "ablation_before_apply",
}

ENV_ENABLE = "GTOS_JEV_DIG_C_SHADOW"
ENV_APPLY = "GTOS_JEV_DIG_C_APPLY"


def dig_c_apply_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Chair flip: Dig C stubs leave resting SHADOW when APPLY=1."""
    env = environ if environ is not None else os.environ
    return str(env.get(ENV_APPLY, "")).strip().lower() in {"1", "true", "yes", "on"}


# Observe-path note for stub 1 — do not mutate a1_log unless safe no-op exists.
FANOUT_DEDUP_NOTE = (
    "FANOUT_DEDUP observe path only; GTOS_JEV_FANOUT_DEDUP=1 is label/env for Dig merge. "
    "Does not change a1_log live POST behavior from this shadow registry."
)

_PLACEHOLDER_HASH = "0" * 16


def _astra_search_roots() -> list[Path]:
    here = Path(__file__).resolve()
    # judgment/warroom_shadow/src/judgment/this.py → parents[2]=warroom_shadow, [3]=judgment
    candidates = [
        here.parents[2] / "judgment" / "astra",  # warroom_shadow/judgment/astra
        here.parents[3] / "astra",  # judgment/astra (live host)
        Path("/workspace/gtos/judgment/warroom_shadow/judgment/astra"),
        Path("/workspace/gtos/judgment/astra"),
        Path(
            "/workspace/gtos/research/warroom_20260920/judgment/"
            "warroom_shadow/judgment/astra"
        ),
        Path("/workspace/gtos/research/codila_absorb/war_room"),
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def dig_c_shadow_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(ENV_ENABLE, "")).strip() == "1"


def list_stub_ids() -> list[int]:
    return sorted(STUB_IDS.keys())


def stub_full_id(stub_id: int) -> str:
    if stub_id not in STUB_IDS:
        raise KeyError(f"stub_id {stub_id} not in Dig C merge set {list(STUB_IDS)}")
    return STUB_IDS[stub_id]


def stub_short_id(stub_id: int) -> str:
    if stub_id not in SHORT_IDS:
        raise KeyError(f"stub_id {stub_id} not in Dig C merge set {list(SHORT_IDS)}")
    return SHORT_IDS[stub_id]


def load_stub_payload(stub_id: int) -> dict[str, Any]:
    """Load stub artifact JSON from astra (recipes blob or typed row)."""
    full = stub_full_id(stub_id)
    for root in _astra_search_roots():
        path = root / f"{full}.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            recipes = data.get("recipes") if isinstance(data, dict) else None
            if isinstance(recipes, dict) and full in recipes:
                row = dict(recipes[full])
            else:
                row = dict(data) if isinstance(data, dict) else {"raw": data}
            row["_artifact_path"] = str(path)
            return row
    return {
        "stub_id": full,
        "id": stub_short_id(stub_id),
        "missing_artifact": True,
        "place": False,
        "apply": bool(apply_on),
        "APPLY_proposed": bool(apply_on),
    }


def _typed_shadow_row(
    stub_id: int,
    *,
    active: bool,
    apply_on: bool = False,
    payload: Mapping[str, Any] | None = None,
    artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    short = stub_short_id(stub_id)
    full = stub_full_id(stub_id)
    menu_hash = _PLACEHOLDER_HASH
    option_order_hash = _PLACEHOLDER_HASH
    state_hash = _PLACEHOLDER_HASH
    model_id = ""
    run_id = ""
    if payload:
        menu_hash = str(payload.get("menu_hash") or menu_hash)
        option_order_hash = str(payload.get("option_order_hash") or option_order_hash)
        state_hash = str(payload.get("state_hash") or state_hash)
        model_id = str(payload.get("model_id") or model_id)
        run_id = str(payload.get("run_id") or run_id)
    art = artifact or {}
    row: dict[str, Any] = {
        "stub_id": full,
        "short_id": short,
        "priority_rank": stub_id,
        "disposition": ("APPLY" if apply_on else "SHADOW"),
        "shadow_active": bool(active),
        "place": False,
        "apply": bool(apply_on),
        "APPLY_proposed": bool(apply_on),
        "pack1b_beaten": False,
        "menu_hash": menu_hash,
        "option_order_hash": option_order_hash,
        "state_hash": state_hash,
        "model_id": model_id,
        "run_id": run_id,
        "env_gate": ENV_ENABLE,
        "dig_c_spec_id": art.get("dig_c_spec_id") or art.get("id") or short,
        "intent": art.get("intent"),
        "wire_into": list(art.get("wire_into") or []),
    }
    if stub_id == 1:
        row["fanout_dedup_note"] = FANOUT_DEDUP_NOTE
        row["observe_only"] = True
    if stub_id == 2:
        row["harvest_env"] = "GTOS_JEV_TRAIN_HARVEST_SHADOW"
        row["never_broker"] = True
    if stub_id == 3:
        row["policy_c_live_untouched"] = True
        row["note"] = "SHADOW emit only; do NOT change live policy_c APPLY"
    return row


def emit_shadow_jev_dig_c(
    payload: MutableMapping[str, Any] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    stub_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Stamp payload['shadow_jev_dig_c'][short_id] for merge stubs 1–5+8.

    Always writes present rows. When GTOS_JEV_DIG_C_SHADOW!=1, rows are
    present-but-inactive (shadow_active=False). Never place/apply.
    """
    if payload is None:
        payload = {}
    active = dig_c_shadow_enabled(environ)
    apply_on = dig_c_apply_enabled(environ)
    if apply_on:
        active = True
    bucket = payload.setdefault("shadow_jev_dig_c", {})
    if not isinstance(bucket, dict):
        bucket = {}
        payload["shadow_jev_dig_c"] = bucket
    ids = stub_ids if stub_ids is not None else list_stub_ids()
    for sid in ids:
        if sid not in STUB_IDS:
            continue
        art = load_stub_payload(sid)
        row = _typed_shadow_row(sid, active=active, payload=payload, artifact=art)
        bucket[stub_short_id(sid)] = row
    # Hard invariants on the bucket itself
    payload["shadow_jev_dig_c"] = bucket
    payload.setdefault("shadow.jev.dig_c.place", False)
    payload.setdefault("shadow.jev.dig_c.apply", False)
    payload.setdefault("shadow.jev.dig_c.APPLY_proposed", False)
    payload["shadow.jev.dig_c.enabled"] = active
    payload["shadow.jev.dig_c.stub_ids"] = list(ids)
    return payload


def smoke() -> dict[str, Any]:
    out = emit_shadow_jev_dig_c({})
    bucket = out["shadow_jev_dig_c"]
    expected = [SHORT_IDS[i] for i in list_stub_ids()]
    missing = [k for k in expected if k not in bucket]
    assert not missing, f"missing keys: {missing}"
    for k, row in bucket.items():
        assert row.get("place") is False, k
        assert row.get("apply") is False, k
        assert row.get("APPLY_proposed") is False, k
    # 0/6/7 must NOT be required in emit set
    for banned in (
        "conf_high_trust_order_block",
        "place_choice_chair",
        "veto_simplejev",
    ):
        assert banned not in bucket
    return {
        "ok": True,
        "keys": sorted(bucket.keys()),
        "enabled": out.get("shadow.jev.dig_c.enabled"),
        "place": False,
        "apply": False,
    }


if __name__ == "__main__":
    print(json.dumps(smoke(), indent=2))

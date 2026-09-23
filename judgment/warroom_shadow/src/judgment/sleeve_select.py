"""JEV_SLEEVE_SELECT — symbol-scoped AliveMenu for System One / shadow Choice.

build_sleeve_select_menu(symbol, state) → AliveMenu-like criteria:
  alive_sleeves_for_symbol ∩ affinity KEEP priors, ordered by φ prior (higher first),
  always includes escapes HOLD/ABSTAIN/ESCALATE_CHAIR/BLOCKED. Cap 255.

SHADOW default when fluid shadow on. APPLY stays 0 until hist-prove (Chair flip).
Jev never places. place=writer only. never_alias Package B → sub_mid_dn_revert.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .alive_menu import AliveMenu, Criterion, ESCAPE_CRITERIA
from .inventory import ESCAPE_HATCHES, MAX_CHOICE_OPTIONS

QUESTION_ID = "JEV_SLEEVE_SELECT"
SLEEVE_SELECT_SHADOW_ENV = "GTOS_JEV_SLEEVE_SELECT_SHADOW"
SLEEVE_SELECT_APPLY_ENV = "GTOS_JEV_SLEEVE_SELECT_APPLY"
FLUID_SHADOW_ENV = "GTOS_JEV_FLUID_GATES_SHADOW"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

# F5 / affinity KEEP priors — must appear for named symbols (EURUSD→asian_fade F5 armed).
F5_AFFINITY_KEEP_PRIORS: dict[str, tuple[str, ...]] = {
    "EURUSD": (
        "asian_fade",
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr",
    ),
    "XAUUSD": (
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_three_fresh_lower_lows",
        "dsp_expanding_up_staircase",
    ),
    # PR40 Edge KEEP deepen (SHADOW) — Dig extend 2026-09-20
    "GBPJPY": (
        "vss_fxcross_london_up_low",
        "sub_mid_dn_revert",  # tape KEEP on GBPJPY only; never Package B SHORT alias
    ),
    "XAGUSD": (
        "sub_xvol_pullback",
        "metals_core",
        "metal_session_reversion",
    ),
}

# Soft-relax documentation (do NOT silently delete hard-offs without receipt).
SOFT_RELAX_HOUSE_LAW = ("mx_us30", "idxrev")  # US30/idxrev stay writer house-law
SOFT_RELAX_STAY_HOUSE_UNTIL_KEEP_PROOF = ("bleed", "xa_huge")
SOFT_RELAX_MAY_BECOME_JEV_BLOCKED: tuple[str, ...] = ()  # Chair fills after KEEP proof

_PHI_CANDIDATE_PATHS = (
    Path("/workspace/gtos/judgment/astra/lab/warroom_intel_20260920/PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
    Path(__file__).resolve().parents[2]
    / "astra"
    / "lab"
    / "warroom_intel_20260920"
    / "PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json",
    Path("/workspace/instrument-edge/packs/PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
    Path(r"host-local\redacted_host\repo\judgment\astra\lab\warroom_intel_20260920\PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
)


def _env_on(name: str, environ: Mapping[str, str] | None = None, *, default: bool = False) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(name, "")).strip().lower()
    if not raw:
        return default
    return raw in _TRUTHY


def sleeve_select_shadow_enabled(
    *,
    environ: Mapping[str, str] | None = None,
    fluid_shadow_on: bool | None = None,
) -> bool:
    """Default ON when fluid shadow is on; explicit 0/false turns off."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(SLEEVE_SELECT_SHADOW_ENV, "")).strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in _TRUTHY:
        return True
    if fluid_shadow_on is not None:
        return bool(fluid_shadow_on)
    return _env_on(FLUID_SHADOW_ENV, env, default=False)


def sleeve_select_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """APPLY stays 0 until Chair hist-prove + flip. Default False."""
    return _env_on(SLEEVE_SELECT_APPLY_ENV, environ, default=False)


def soft_relax_map() -> dict[str, Any]:
    return {
        "house_law_stay_writer": list(SOFT_RELAX_HOUSE_LAW),
        "stay_house_until_keep_proof": list(SOFT_RELAX_STAY_HOUSE_UNTIL_KEEP_PROOF),
        "may_become_jev_blocked": list(SOFT_RELAX_MAY_BECOME_JEV_BLOCKED),
        "note": (
            "US30/idxrev stay house-law; bleed/xa_huge stay house-law until KEEP proof. "
            "Do not silently delete hard-offs without receipt. RELAX_TO_JEV emits BLOCKED escapes."
        ),
        "receipt_required_to_move": True,
    }


def load_phi_prior(path: Path | str | None = None) -> dict[str, Any]:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    candidates.extend(_PHI_CANDIDATE_PATHS)
    for p in candidates:
        try:
            if p.is_file():
                doc = json.loads(p.read_text(encoding="utf-8"))
                doc["_loaded_from"] = str(p)
                return doc
        except Exception:  # noqa: BLE001
            continue
    return {
        "schema": "missing",
        "candidates": [],
        "menu_ranking": [],
        "apply": False,
        "place": False,
        "_loaded_from": None,
    }


def phi_score_for_tag(tag: str, symbol: str, prior: Mapping[str, Any] | None) -> float:
    if not prior:
        return 0.0
    sym = str(symbol).upper()
    tag_l = str(tag).lower()
    best = 0.0
    for row in prior.get("candidates") or []:
        if not isinstance(row, Mapping) or not row.get("menu_eligible", True):
            continue
        inst = str(row.get("instrument") or "").upper()
        if inst and inst != sym:
            if not (inst.startswith("XAU") and sym.startswith("XAU")):
                continue
        row_tag = str(row.get("tag") or "").lower()
        row_sleeve = str(row.get("sleeve") or "").lower()
        if tag_l == row_tag or tag_l == row_sleeve or (row_tag and row_tag in tag_l) or (row_sleeve and row_sleeve in tag_l):
            cap = row.get("capability") if isinstance(row.get("capability"), Mapping) else {}
            phi = float(cap.get("phi", row.get("phi", 0.0)) or 0.0)
            if phi > best:
                best = phi
    return best


def _escape_criterion(name: str) -> Criterion:
    spec = ESCAPE_CRITERIA[name]
    return Criterion(
        id=name,
        what=spec["what"],
        not_for=spec["not_for"],
        examples=tuple(spec["examples"]),
    )


def _sleeve_criterion(name: str, *, phi: float = 0.0, prior_note: str = "") -> Criterion:
    bits = []
    if phi:
        bits.append(f"φ={phi:.4f}")
    if prior_note:
        bits.append(prior_note)
    suffix = (" " + "; ".join(bits)) if bits else ""
    return Criterion(
        id=f"sleeve:{name}",
        what=f"Select alive+affinity sleeve {name} for this symbol's JEV_SLEEVE_SELECT.{suffix}",
        not_for=(
            "Hard-off / US30 house-law without RELAX receipt; "
            "Package B never aliases sub_mid_dn_revert; cost never kill."
        ),
        examples=(name, QUESTION_ID),
    )


@dataclass(frozen=True)
class SleeveSelectMenu:
    """Symbol-scoped Choice menu (AliveMenu-compatible)."""

    cycle_id: str
    symbol: str
    inventory_fingerprint: str
    criteria: tuple[Criterion, ...]
    rebuilt: bool
    prior_fingerprint: str | None
    inventory_changed: bool
    question_id: str = QUESTION_ID
    phi_ordered: bool = True
    apply: bool = False
    place: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)
    selected_sleeve_advisory: str | None = None
    alive_pack: dict[str, Any] = field(default_factory=dict)
    soft_relax: dict[str, Any] = field(default_factory=dict)

    @property
    def option_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    def as_dict(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "cycle_id": self.cycle_id,
            "symbol": self.symbol,
            "inventory_fingerprint": self.inventory_fingerprint,
            "criteria": [c.as_dict() for c in self.criteria],
            "rebuilt": self.rebuilt,
            "prior_fingerprint": self.prior_fingerprint,
            "inventory_changed": self.inventory_changed,
            "notes": list(self.notes),
            "option_ids": list(self.option_ids),
            "phi_ordered": self.phi_ordered,
            "apply": False,
            "place": False,
            "selected_sleeve_advisory": self.selected_sleeve_advisory,
            "alive_pack_summary": {
                "alive": list((self.alive_pack or {}).get("alive_sleeves_for_symbol") or []),
                "armed_source": (self.alive_pack or {}).get("armed_source"),
                "relax_to_jev": (self.alive_pack or {}).get("relax_to_jev"),
                "blocked_escape_n": len((self.alive_pack or {}).get("blocked_escape") or []),
                "fail_closed": (self.alive_pack or {}).get("fail_closed", False),
            },
            "soft_relax": self.soft_relax,
        }

    def as_alive_menu(self) -> AliveMenu:
        return AliveMenu(
            cycle_id=self.cycle_id,
            inventory_fingerprint=self.inventory_fingerprint,
            criteria=self.criteria,
            rebuilt=self.rebuilt,
            prior_fingerprint=self.prior_fingerprint,
            inventory_changed=self.inventory_changed,
            notes=self.notes + ("sleeve_select_as_alive_menu",),
        )


def _collect_alive_tags(symbol: str, state: Mapping[str, Any] | None) -> tuple[list[str], dict[str, Any], list[str]]:
    """Compose alive tags; fail-closed notes if deps missing. Always union F5 KEEP priors."""
    notes: list[str] = []
    pack: dict[str, Any] = {}
    alive: list[str] = []
    try:
        from .alive_sleeves_for_symbol import alive_sleeves_for_symbol

        pack = alive_sleeves_for_symbol(symbol, use_research_overlay=True)
        alive = list(pack.get("alive_sleeves_for_symbol") or [])
        notes.append("alive_sleeves_for_symbol_ok")
    except Exception as exc:  # noqa: BLE001
        pack = {
            "fail_closed": True,
            "error": f"{type(exc).__name__}:{exc}",
            "alive_sleeves_for_symbol": [],
            "apply": False,
            "place": False,
        }
        notes.append(f"alive_sleeves_fail_closed:{type(exc).__name__}")

    sym = str(symbol).upper()
    priors = list(F5_AFFINITY_KEEP_PRIORS.get(sym, ()))
    # state may inject extra KEEP priors
    if state:
        extra = state.get("affinity_keep_priors") or state.get("f5_keep_priors") or ()
        for x in extra:
            if x and str(x) not in priors:
                priors.append(str(x))
    for p in priors:
        if p not in alive:
            alive.append(p)
            notes.append(f"f5_keep_prior_injected:{p}")
    # EURUSD must include asian_fade
    if sym == "EURUSD" and "asian_fade" not in alive:
        alive.insert(0, "asian_fade")
        notes.append("eurusd_asian_fade_forced")
    return alive, pack, notes


def build_sleeve_select_menu(
    symbol: str,
    state: Mapping[str, Any] | None = None,
    *,
    selected_advisory: str | None = None,
    phi_prior: Mapping[str, Any] | None = None,
    prior_menu: SleeveSelectMenu | None = None,
) -> SleeveSelectMenu:
    """Build symbol-scoped Choice criteria. Escapes always present. Cap 255."""
    sym = str(symbol or (state or {}).get("symbol") or (state or {}).get("instrument") or "UNKNOWN").upper()
    alive, pack, notes = _collect_alive_tags(sym, state)
    prior = dict(phi_prior) if phi_prior is not None else load_phi_prior()
    if prior.get("_loaded_from"):
        notes.append(f"phi_prior:{prior['_loaded_from']}")
    else:
        notes.append("phi_prior_missing_fail_closed_order_alpha")

    # φ descending, then alpha for ties
    scored = [(phi_score_for_tag(t, sym, prior), t) for t in alive]
    scored.sort(key=lambda x: (-x[0], x[1]))
    notes.append("phi_ordered_desc")

    criteria: list[Criterion] = [_escape_criterion(n) for n in ESCAPE_HATCHES]
    for phi, tag in scored:
        # never present live sub_mid_dn_revert as Package B alias on EURUSD;
        # GBPJPY F5 KEEP prior may show sub_mid_dn_revert (PR40 tape KEEP) — not Package B SHORT
        if tag == "sub_mid_dn_revert" and tag not in F5_AFFINITY_KEEP_PRIORS.get(sym, ()):
            notes.append("refused_alias_package_b_to_sub_mid_dn_revert")
            continue
        if tag == "sub_mid_dn_re_proxy_eurusd_short_m15_atr" and sym != "EURUSD":
            notes.append("package_b_short_eurusd_only")
            continue
        prior_note = "f5_keep" if tag in F5_AFFINITY_KEEP_PRIORS.get(sym, ()) else ""
        criteria.append(_sleeve_criterion(tag, phi=phi, prior_note=prior_note))

    # blocked_escape from relax → already have BLOCKED hatch; annotate
    for be in pack.get("blocked_escape") or []:
        notes.append(f"blocked_escape:{be.get('tag')}")

    if len(criteria) > MAX_CHOICE_OPTIONS:
        notes.append("capped_at_255")
        head = [c for c in criteria if c.id in ESCAPE_HATCHES]
        rest = [c for c in criteria if c.id not in ESCAPE_HATCHES]
        budget = MAX_CHOICE_OPTIONS - len(head)
        criteria = head + rest[:budget]

    fp_src = {"symbol": sym, "sleeves": [c.id for c in criteria if c.id.startswith("sleeve:")]}
    import hashlib

    fp = hashlib.sha256(json.dumps(fp_src, sort_keys=True).encode()).hexdigest()
    prior_fp = prior_menu.inventory_fingerprint if prior_menu else None
    changed = bool(prior_fp and prior_fp != fp)

    # advisory selection from state if present (APPLY=0 → advisory only)
    advisory = selected_advisory
    if advisory is None and state:
        advisory = state.get("selected_sleeve") or state.get("jev_sleeve_select") or None
        if isinstance(advisory, Mapping):
            advisory = advisory.get("id") or advisory.get("sleeve")

    return SleeveSelectMenu(
        cycle_id=uuid.uuid4().hex,
        symbol=sym,
        inventory_fingerprint=fp,
        criteria=tuple(criteria),
        rebuilt=True,
        prior_fingerprint=prior_fp,
        inventory_changed=changed,
        question_id=QUESTION_ID,
        phi_ordered=True,
        apply=False,
        place=False,
        notes=tuple(notes),
        selected_sleeve_advisory=str(advisory) if advisory else None,
        alive_pack=pack,
        soft_relax=soft_relax_map(),
    )


def emit_sleeve_select_shadow_payload(
    menu: SleeveSelectMenu,
    *,
    state: Mapping[str, Any] | None = None,
    apply_flag: bool = False,
) -> dict[str, Any]:
    """Shadow Choice payload for warroom jsonl. APPLY never enables place."""
    apply_on = bool(apply_flag) and sleeve_select_apply_enabled()
    # this pass: force apply false unless Chair already flipped env AND hist-prove exists —
    # we do NOT enable APPLY=1 this pass.
    apply_on = False
    return {
        "schema": "gtos.jev.sleeve_select.shadow.v1",
        "question_id": QUESTION_ID,
        "type": "Choice",
        "symbol": menu.symbol,
        "options": list(menu.option_ids),
        "criteria": [c.as_dict() for c in menu.criteria],
        "state_keys": sorted(list((state or {}).keys())),
        "selected_sleeve_advisory": menu.selected_sleeve_advisory,
        "phi_ordered": menu.phi_ordered,
        "apply": apply_on,
        "place": False,
        "never_place": True,
        "cost_never_kill": True,
        "never_alias_package_b_to_sub_mid_dn_revert": True,
        "soft_relax": menu.soft_relax,
        "menu": menu.as_dict(),
        "disposition": "advisory_only" if not apply_on else "admit_filter",
    }


def append_warroom_shadow_jsonl(payload: Mapping[str, Any], log_dir: Path | str | None = None) -> Path:
    """Append one shadow line under judgment/live/jev_sidecar/sleeve_select/."""
    from datetime import datetime, timezone

    if log_dir is None:
        override = os.environ.get("GTOS_JEV_FLUID_GATES_LOG_DIR", "").strip()
        root = Path(override) if override else Path(__file__).resolve().parents[2] / "judgment" / "live" / "jev_sidecar"
    else:
        root = Path(log_dir)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = root / "sleeve_select" / f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(payload), sort_keys=True) + "\n")
    return path

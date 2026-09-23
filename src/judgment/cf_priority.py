"""Chair CF priority SHADOW labels for Jev-everywhere.

Challenge 0 historical CF (n=60, 2026-09-20) ranked:

1. ``jev_sleeve_allow_spring_vss_sub_expand`` +8.7013 R (best)
2. ``jev_size_x_conf_shadow`` Δ +28.299 R
3. ``jev_cost_band`` / ``jev_conf_gate_shadow_trim`` Δ +25.413 R

``LEGACY_religion_index_crypto_xa_0`` is **revoked** — do not encode
INDEX / CRYPTO / xa size0 as research religion. Writer house locks
(bleed / orb_crypto / idxrev / xa_huge / mx_us30) stay. ``regime_unknown``
is honest until assembled regime features exist — do not invent.

Labels only. Never place / order_send / remint / flatten.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .chair_enforce import is_keep_family
from .challenge import CHALLENGE_HARD_OFF_FAMILIES

STEAL = "JEV_EVERYWHERE_CF"
SCHEMA = "gtos.judgment.cf_priority.v1"

#: Chair 2026-09-20 — do not encode. Always false.
RELIGION_INDEX_CRYPTO_XA_SIZE0_REVOKED = True
RELIGION_INDEX_CRYPTO_XA_SIZE0 = False

#: Best CF policy families (spring / vss / sub / expand).
SLEEVE_ALLOW_FAMILIES = frozenset(
    {"spring", "vss_fxcross", "sub_mid", "sub", "dsp_expand"}
)

SLEEVE_FAMILIES = (
    "spring",
    "dsp_expand",
    "sub_mid",
    "sub",
    "vss_fxcross",
    "dsp_wide",
    "dsp_shakeout",
    "dsp_two",
    "dsp_reject",
    "orb_crypto",
    "index_rev_bleed",
    "other",
    "unknown",
)

SIZE_CF_LABELS = (
    "SIZE_FULL_KEEP_WIN",
    "SIZE_FULL_DEFAULT",
    "SIZE_SESSION_TRIM",
    "SIZE_FULL_KEEP_LOSS",
    "SIZE_HALF_FS",
)

CONF_SHADOW_LABELS = (
    "CONF_GATE_ALLOW",
    "CONF_GATE_KEEP",
    "CONF_GATE_REVIEW",
    "CONF_GATE_SESSION",
    "CONF_GATE_EVENT",
    "CONF_GATE_STRICT",
)

COST_BAND_LABELS = (
    "COST_WIN",
    "COST_REVIEW",
    "COST_SESSION",
    "COST_EVENT",
    "COST_FS",
)

SIZE_X_CONF_POLICIES = (
    "SIZE_X_CONF_KEEP",
    "SIZE_X_CONF_ALLOW",
    "SIZE_X_CONF_SESSION",
    "SIZE_X_CONF_STRICT",
    "SIZE_X_CONF_REVIEW",
    "SIZE_X_CONF_EVENT",
    "SIZE_X_CONF_SHADOW",
)

LOSS_SUBCLASSES = frozenset(
    {
        "fs_half_still_losing",
        "session_cut_loss",
        "event_gap_shadow",
        "full_size_loss",
        "review_keep_offhours_false_structure",
    }
)

_PREFIX_FAMILY: tuple[tuple[str, str], ...] = (
    ("orb_crypto", "orb_crypto"),
    ("idxrev", "index_rev_bleed"),
    ("index_rev", "index_rev_bleed"),
    ("dsp_expand", "dsp_expand"),
    ("dsp_spring", "spring"),
    ("dsp_wide", "dsp_wide"),
    ("dsp_shake", "dsp_shakeout"),
    ("dsp_two", "dsp_two"),
    ("dsp_2", "dsp_two"),
    ("dsp_reject", "dsp_reject"),
    ("vss_fxcross", "vss_fxcross"),
    ("sub_mid", "sub_mid"),
)


def religion_index_crypto_xa_size0(*, sleeve: str | None = None, symbol: str | None = None) -> bool:
    """Chair-revoked. Never returns True. Arguments are ignored on purpose."""

    _ = sleeve, symbol
    return RELIGION_INDEX_CRYPTO_XA_SIZE0


def classify_sleeve_family(sleeve: str | None) -> str:
    """Map a sleeve noun onto the CF family axis. Unknown stays unknown."""

    raw = str(sleeve or "").strip().lower()
    if not raw:
        return "unknown"
    tokens = tuple(part for part in raw.replace("-", "_").split("_") if part)
    if not tokens:
        return "unknown"
    if raw == "spring" or tokens[0] == "spring":
        return "spring"
    if tokens[0] == "vss":
        return "vss_fxcross"
    if tokens[0] == "sub":
        return "sub_mid" if "mid" in tokens else "sub"
    if "expand" in tokens and tokens[0] in {"dsp", "expand"}:
        return "dsp_expand"
    if raw == "expand":
        return "dsp_expand"
    for prefix, family in _PREFIX_FAMILY:
        if raw == prefix or raw.startswith(prefix + "_") or raw.startswith(prefix):
            return family
    if tokens[0] == "bleed" or "bleed" in tokens:
        return "other"
    return "other" if tokens[0] in {
        "metals",
        "crypto",
        "energy",
        "dsp",
        "mx",
        "xa",
        "unknown",
    } or raw in {"metals_core", "crypto", "energy_agri", "unknown_sleeve"} else "unknown"


def sleeve_allow(family: str) -> bool:
    return family in SLEEVE_ALLOW_FAMILIES


def _subclass_of(gold_state: Mapping[str, Any] | None, subclass: str | None) -> str | None:
    if subclass:
        return str(subclass)
    if not gold_state:
        return None
    ident = gold_state.get("identity")
    if isinstance(ident, Mapping):
        raw = ident.get("s15_subclass")
        if raw:
            return str(raw)
    return None


def _sleeve_of(gold_state: Mapping[str, Any] | None, sleeve: str | None) -> str | None:
    if sleeve:
        return str(sleeve)
    if not gold_state:
        return None
    ident = gold_state.get("identity")
    if isinstance(ident, Mapping) and ident.get("sleeve"):
        return str(ident.get("sleeve"))
    return None


def classify_size_cf(
    *,
    subclass: str | None,
    sleeve: str | None,
    family: str,
    allow: bool,
) -> str:
    """CF size label. Never INDEX/CRYPTO/xa size0 — that religion is revoked."""

    assert religion_index_crypto_xa_size0(sleeve=sleeve) is False
    sub = str(subclass or "")
    keep = is_keep_family(sleeve)
    if sub == "fs_half_still_losing":
        return "SIZE_HALF_FS"
    if sub == "session_cut_loss":
        return "SIZE_SESSION_TRIM"
    if sub == "full_size_loss":
        return "SIZE_FULL_KEEP_LOSS"
    if allow or keep:
        if sub == "review_keep_offhours_false_structure":
            return "SIZE_FULL_KEEP_WIN"
        if sub == "cost_avoided_by_reject":
            return "SIZE_FULL_DEFAULT"
        if sub in LOSS_SUBCLASSES:
            return "SIZE_FULL_DEFAULT"
        return "SIZE_FULL_KEEP_WIN"
    return "SIZE_FULL_DEFAULT"


def classify_conf_shadow(
    *,
    subclass: str | None,
    sleeve: str | None,
    allow: bool,
    s15_band: str | None = None,
) -> str | None:
    """CF CONF_GATE_* SHADOW label. ALLOW/KEEP are CF, not S15 APPLY."""

    sub = str(subclass or "")
    keep = is_keep_family(sleeve)
    if sub == "fs_half_still_losing":
        return "CONF_GATE_STRICT"
    if sub == "session_cut_loss":
        return "CONF_GATE_SESSION"
    if sub == "event_gap_shadow":
        return "CONF_GATE_EVENT"
    if sub == "full_size_loss":
        return "CONF_GATE_REVIEW"
    if keep:
        return "CONF_GATE_KEEP"
    if allow:
        return "CONF_GATE_ALLOW"
    if s15_band in CONF_SHADOW_LABELS:
        return s15_band
    return None


def classify_cost_band(
    *,
    subclass: str | None,
    allow: bool,
    sleeve: str | None,
) -> str | None:
    """CF cost_band SHADOW label. None when the tape has no cost fact."""

    sub = str(subclass or "")
    if sub == "fs_half_still_losing":
        return "COST_FS"
    if sub == "session_cut_loss":
        return "COST_SESSION"
    if sub == "event_gap_shadow":
        return "COST_EVENT"
    if sub in {"full_size_loss", "review_keep_offhours_false_structure"}:
        return "COST_REVIEW"
    if allow or is_keep_family(sleeve):
        return "COST_WIN"
    return None


def compose_size_x_conf(size_cf: str | None, conf_shadow: str | None) -> tuple[str, str | None]:
    """Compose size × conf_shadow. Label only — never APPLY."""

    if not size_cf and not conf_shadow:
        return "SIZE_X_CONF_SHADOW", None
    joined = "×".join(part for part in (size_cf, conf_shadow) if part)
    if size_cf == "SIZE_FULL_KEEP_WIN" and conf_shadow in {"CONF_GATE_KEEP", "CONF_GATE_ALLOW"}:
        return "SIZE_X_CONF_KEEP", joined
    if size_cf == "SIZE_FULL_DEFAULT" and conf_shadow in {"CONF_GATE_ALLOW", "CONF_GATE_KEEP"}:
        return "SIZE_X_CONF_ALLOW", joined
    if size_cf == "SIZE_SESSION_TRIM" or conf_shadow == "CONF_GATE_SESSION":
        return "SIZE_X_CONF_SESSION", joined
    if size_cf == "SIZE_HALF_FS" or conf_shadow == "CONF_GATE_STRICT":
        return "SIZE_X_CONF_STRICT", joined
    if size_cf == "SIZE_FULL_KEEP_LOSS" or conf_shadow == "CONF_GATE_REVIEW":
        return "SIZE_X_CONF_REVIEW", joined
    if conf_shadow == "CONF_GATE_EVENT":
        return "SIZE_X_CONF_EVENT", joined
    return "SIZE_X_CONF_SHADOW", joined or None


def regime_features_exist(gold_state: Mapping[str, Any] | None) -> bool:
    """True only when an assembled regime feature pack is present.

    Bucket-only gold_state with ``source=unassembled`` is not features.
    Do not invent a regime type from that.
    """

    if not gold_state:
        return False
    pack = gold_state.get("regime_features")
    if isinstance(pack, Mapping) and pack.get("assembled") is True:
        return True
    sessions = gold_state.get("sessions")
    levels = gold_state.get("levels")
    sess_src = sessions.get("source") if isinstance(sessions, Mapping) else None
    lvl_src = levels.get("source") if isinstance(levels, Mapping) else None
    if sess_src == "unassembled" or lvl_src == "unassembled":
        return False
    if sess_src == "assembled" and lvl_src == "assembled":
        return True
    return False


def honest_regime_label(gold_state: Mapping[str, Any] | None) -> str:
    if regime_features_exist(gold_state):
        return "regime_features_present"
    return "regime_unknown"


@dataclass(frozen=True)
class CfPriorityLabels:
    """Chair CF priority SHADOW pack. ``broker_effect`` is always False."""

    family: str
    sleeve_allow: bool
    sleeve_policy: str
    size_cf: str
    conf_shadow: str | None
    cost_band: str | None
    size_x_conf: str
    size_x_conf_join: str | None
    regime_honest: str
    religion_index_crypto_xa_size0: bool
    broker_effect: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "steal": STEAL,
            "family": self.family,
            "sleeve_allow": self.sleeve_allow,
            "sleeve_policy": self.sleeve_policy,
            "size_cf": self.size_cf,
            "conf_shadow": self.conf_shadow,
            "cost_band": self.cost_band,
            "size_x_conf": self.size_x_conf,
            "size_x_conf_join": self.size_x_conf_join,
            "regime_honest": self.regime_honest,
            "religion_index_crypto_xa_size0": False,
            "religion_index_crypto_xa_size0_revoked": True,
            "hard_off_families_untouched": list(CHALLENGE_HARD_OFF_FAMILIES),
            "label_only": True,
            "never_place": True,
            "broker_effect": False,
        }


def label_cf_priority(
    *,
    gold_state: Mapping[str, Any] | None = None,
    sleeve: str | None = None,
    subclass: str | None = None,
    s15_band: str | None = None,
) -> CfPriorityLabels:
    resolved_sleeve = _sleeve_of(gold_state, sleeve)
    resolved_sub = _subclass_of(gold_state, subclass)
    family = classify_sleeve_family(resolved_sleeve)
    allow = sleeve_allow(family)
    size_cf = classify_size_cf(
        subclass=resolved_sub, sleeve=resolved_sleeve, family=family, allow=allow
    )
    conf_shadow = classify_conf_shadow(
        subclass=resolved_sub,
        sleeve=resolved_sleeve,
        allow=allow,
        s15_band=s15_band,
    )
    cost_band = classify_cost_band(
        subclass=resolved_sub, allow=allow, sleeve=resolved_sleeve
    )
    policy, joined = compose_size_x_conf(size_cf, conf_shadow)
    return CfPriorityLabels(
        family=family,
        sleeve_allow=allow,
        sleeve_policy="SLEEVE_ALLOW" if allow else "SLEEVE_SHADOW",
        size_cf=size_cf,
        conf_shadow=conf_shadow,
        cost_band=cost_band,
        size_x_conf=policy,
        size_x_conf_join=joined,
        regime_honest=honest_regime_label(gold_state),
        religion_index_crypto_xa_size0=False,
    )

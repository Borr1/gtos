"""S16 MULTI_STAGE_GUARD — Dig/Chair MCP / tool-policy screens.

Five stages: input → tool-pre → observation → response → claim-verify.
CODE maps Jev verdicts to ``allow | review | block`` (+ ``support`` escalate).

Parallel to the Challenge admit sidecar (PR29 / S14 / S15). This module
does **not** import ``cycle`` / ``conf_gate`` / ``regime_*``. It composes
with :mod:`src.judgment.done_outside` for the claim-verify twin.

Place is an infinity VETO. ``broker_effect`` is always false. Confidence
is never permission. Heuristics never override a Jev block. Write/send
``failMode`` is ``closed`` or ``review`` — never ``open``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .done_outside import VerifyResult, completion_truth, verify_artifact
from .s16_flags import default_s16_log_dir, s16_apply_enabled, s16_shadow_enabled
from .s16_heuristics import (
    LOW_CONF,
    classify_action_locally,
    classify_input_locally,
    classify_observation_locally,
    empty_news_fields,
    is_destructive_tool,
    is_read_only_tool,
    is_write_send_tool,
)
from .veto import (
    JevPlacePathVeto,
    is_broker_or_payout_action,
    refuse_broker_action,
    refuse_invented_news_protocol,
)

STEAL = "S16"
SCHEMA = "gtos.chair.s16.shadow_row.v1"
NAMESPACE = "gtos.chair.s16.multi_stage_guard.v1"

POLICY_ACTIONS = ("allow", "review", "block", "support")
POLICY_PRECEDENCE = ("support", "block", "review", "allow")
CLAIM_VERDICTS = ("supported", "contradicted", "insufficient", "fabricated")
STAGES = ("input", "tool_pre", "observation", "response", "claim_verify")
STAGE_API = {
    "input": "screenInput",
    "tool_pre": "assessAction",
    "observation": "screenObservation",
    "response": "screenOutput",
    "claim_verify": "verifyClaim",
}

FORBIDDEN_DIG_TOKENS = frozenset(
    {
        "order_send",
        "mt5",
        "place",
        "remint",
        "flatten",
        "broker",
        "open_trade",
        "mint_token",
        "move_sl",
    }
)

S11_DENY_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "s11_hard_deny.json"
)

DIG_PACK_PATHS = (
    "research/codila_absorb/war_room/s16_multi_stage_guard/SHADOW_WIRE_SPEC.md",
    "research/codila_absorb/war_room/s16_multi_stage_guard/guard_map.json",
    "research/codila_absorb/war_room/s16_multi_stage_guard/compose_pseudocode.md",
    "research/codila_absorb/war_room/s16_multi_stage_guard/PROVE_PLAN.md",
    "research/codila_absorb/war_room/s16_multi_stage_guard/PROVE_FIXTURES.md",
    "research/codila_absorb/war_room/s16_multi_stage_guard/PR29_S16_COMPOSE.md",
    "research/codila_absorb/war_room/s16_multi_stage_guard/prove_fixtures/",
)

CHAIR_DISPOSITION = {
    ("input", "block"): "refuse_run",
    ("input", "review"): "ask_chair",
    ("input", "allow"): "continue",
    ("input", "support"): "escalate_care",
    ("tool_pre", "block"): "refuse_tool",
    ("tool_pre", "review"): "ask_chair",
    ("tool_pre", "allow"): "run_tool",
    ("tool_pre", "support"): "escalate_refuse_write",
    ("observation", "block"): "data_only",
    ("observation", "review"): "redact_or_ask",
    ("observation", "allow"): "use_text",
    ("observation", "support"): "escalate_care",
    ("response", "block"): "hold_send",
    ("response", "review"): "ask_before_outbound",
    ("response", "allow"): "send",
    ("response", "support"): "escalate_care",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_policy_action(raw: object) -> str:
    name = str(raw or "").strip().lower()
    if name in ("deny", "denied", "blocked", "refuse", "veto"):
        return "block"
    if name in POLICY_ACTIONS:
        return name
    return "review"


def fail_mode_for(*, write_send: bool, requested: str | None = None) -> str:
    """Write/send may be ``closed`` or ``review`` — never ``open``."""

    want = str(requested or "").strip().lower()
    if write_send:
        if want == "open":
            return "closed"
        if want in {"closed", "review"}:
            return want
        return "closed"
    if want == "open":
        return "review"
    if want in {"closed", "review"}:
        return want
    return "review"


def is_forbidden_dig_tool(name: str | None) -> bool:
    raw = str(name or "").strip().lower()
    if not raw:
        return False
    if "aplus_" in raw or raw.startswith("aplus"):
        return True
    if is_broker_or_payout_action(raw):
        return True
    tokens = set(re.split(r"[^a-z0-9_]+", raw))
    return bool(tokens & FORBIDDEN_DIG_TOKENS) or any(tok in raw for tok in ("order_send", "open_trade"))


def assert_dig_inventory(tools: Sequence[str] | None) -> tuple[str, ...]:
    """Stage 0: Dig/Chair inventory must not carry place / broker tools."""

    found: list[str] = []
    for raw in tools or ():
        name = str(raw or "").strip()
        if is_forbidden_dig_tool(name):
            found.append(name)
    if found:
        raise JevPlacePathVeto(
            "VETO PLACE_PATH: Dig inventory must not carry "
            + ", ".join(sorted(found))
        )
    return tuple(str(t) for t in (tools or ()) if str(t).strip())


def load_s11_hard_deny(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else S11_DENY_PATH
    if not target.is_file():
        return {
            "schema": "gtos.chair.s11.hard_deny.v1",
            "deny_tools": sorted(FORBIDDEN_DIG_TOKENS),
            "deny_prefixes": ["aplus_"],
            "deny_patterns": [r"rm\s+-rf\s+/", r"curl\b[^|\n]*\|\s*(ba)?sh"],
        }
    return json.loads(target.read_text(encoding="utf-8"))


def s11_hard_deny(action: Mapping[str, object] | None, *, doc: Mapping[str, Any] | None = None) -> str | None:
    payload = dict(action or {})
    name = str(payload.get("name") or payload.get("tool") or "")
    command = str(payload.get("command") or "")
    if isinstance(payload.get("args"), Mapping):
        command = command or str(payload["args"].get("command") or "")
    packed = load_s11_hard_deny() if doc is None else dict(doc)
    low = name.lower()
    for tool in packed.get("deny_tools") or ():
        if low == str(tool).lower() or str(tool).lower() in low:
            return "S11_DENY"
    for prefix in packed.get("deny_prefixes") or ():
        if prefix and prefix.lower() in low:
            return "S11_DENY"
    blob = f"{name} {command}"
    for pattern in packed.get("deny_patterns") or ():
        if pattern and re.search(str(pattern), blob, re.I):
            return "S11_DENY"
    if is_forbidden_dig_tool(name):
        return "S11_DENY"
    return None


@dataclass(frozen=True)
class GuardAction:
    """One Dig/Chair tool or screen payload. Never a broker send."""

    name: str
    command: str = ""
    mutates: bool = False
    sends_external: bool = False
    grant: bool = False
    confidence: float | None = None
    args: dict[str, object] = field(default_factory=dict)
    text: str = ""

    def as_mapping(self) -> dict[str, object]:
        return {
            "name": self.name,
            "tool": self.name,
            "command": self.command,
            "mutates": self.mutates,
            "sends_external": self.sends_external,
            "grant": self.grant,
            "confidence": self.confidence,
            "args": dict(self.args),
            "text": self.text,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object] | None) -> "GuardAction":
        payload = dict(raw or {})
        args = payload.get("args") if isinstance(payload.get("args"), Mapping) else {}
        command = str(payload.get("command") or args.get("command") or args.get("cmd") or "")
        name = str(payload.get("name") or payload.get("tool") or "")
        conf = payload.get("confidence")
        try:
            confidence = float(conf) if conf is not None else None
        except (TypeError, ValueError):
            confidence = None
        return cls(
            name=name,
            command=command,
            mutates=bool(payload.get("mutates")),
            sends_external=bool(payload.get("sends_external")),
            grant=bool(payload.get("grant")),
            confidence=confidence,
            args=dict(args),
            text=str(payload.get("text") or payload.get("prompt") or ""),
        )


@dataclass(frozen=True)
class GuardResult:
    """CODE disposition for one S16 screen. Never a place authorization."""

    steal: str = STEAL
    schema: str = SCHEMA
    stage: str = "tool_pre"
    api: str = "assessAction"
    tool: str | None = None
    action: str = "review"
    fail_mode: str = "review"
    heuristics_hit: bool = False
    heuristics_action: str | None = None
    jev_action: str | None = None
    jev_block_honored: bool = True
    claim_verdict: str | None = None
    completion: str | None = None
    chair_disposition: str = "ask_chair"
    data_only: bool = False
    invented_news: bool = False
    news_headlines: tuple[str, ...] = ()
    news_events: tuple[str, ...] = ()
    news_protocol: None = None
    broker_effect: bool = False
    never_place: bool = True
    never_remint: bool = True
    never_flatten: bool = True
    off_challenge_place_scoreboard: bool = True
    mode: str = "shadow_log_only"
    confidence: float | None = None
    confidence_as_permission: bool = False
    fail_mode_open: bool = False
    grant: bool = False
    reason: str = ""
    skipped: bool = False
    enforced: bool = False
    artifact_ok: bool | None = None
    done_outside_twin: str | None = None
    outbound_executed: bool = False
    tool_executed_external: bool = False
    fixture_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "steal": self.steal,
            "schema": self.schema,
            "namespace": NAMESPACE,
            "stage": self.stage,
            "api": self.api,
            "tool": self.tool,
            "action": self.action,
            "fail_mode": self.fail_mode,
            "heuristics_hit": self.heuristics_hit,
            "heuristics_action": self.heuristics_action,
            "jev_action": self.jev_action,
            "jev_block_honored": self.jev_block_honored,
            "claim_verdict": self.claim_verdict,
            "completion": self.completion,
            "chair_disposition": self.chair_disposition,
            "data_only": self.data_only,
            "invented_news": self.invented_news,
            "news_headlines": list(self.news_headlines),
            "news_events": list(self.news_events),
            "news_protocol": self.news_protocol,
            "broker_effect": False,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
            "never_host-mesh": True,
            "off_challenge_place_scoreboard": True,
            "mode": "shadow_log_only",
            "confidence": self.confidence,
            "confidence_as_permission": False,
            "fail_mode_open": False,
            "grant": self.grant,
            "reason": self.reason,
            "skipped": self.skipped,
            "enforced": self.enforced,
            "artifact_ok": self.artifact_ok,
            "done_outside_twin": self.done_outside_twin,
            "outbound_executed": False,
            "tool_executed_external": False,
            "fixture_id": self.fixture_id,
        }


def _confidence(raw: object) -> float | None:
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0.0 or value > 1.0:
        return None
    return value


def _jev_from_mocks(mocks: Mapping[str, object] | None) -> dict[str, object]:
    payload = dict(mocks or {})
    jev = payload.get("jev")
    if isinstance(jev, Mapping):
        return dict(jev)
    return {}


def _result(
    *,
    stage: str,
    action: str,
    reason: str,
    fail_mode: str,
    tool: str | None = None,
    heuristics_hit: bool = False,
    heuristics_action: str | None = None,
    jev_action: str | None = None,
    jev_block_honored: bool = True,
    claim_verdict: str | None = None,
    completion: str | None = None,
    data_only: bool = False,
    confidence: float | None = None,
    grant: bool = False,
    skipped: bool = False,
    enforced: bool = False,
    artifact_ok: bool | None = None,
    done_outside_twin: str | None = None,
    fixture_id: str | None = None,
) -> GuardResult:
    final = normalize_policy_action(action)
    if stage == "claim_verify":
        chair = completion or "REVIEW"
    else:
        chair = CHAIR_DISPOSITION.get((stage, final), "ask_chair")
    news = empty_news_fields()
    return GuardResult(
        stage=stage,
        api=STAGE_API[stage],
        tool=tool,
        action=final,
        fail_mode=fail_mode if fail_mode != "open" else ("closed" if stage == "tool_pre" else "review"),
        heuristics_hit=heuristics_hit,
        heuristics_action=heuristics_action,
        jev_action=jev_action,
        jev_block_honored=jev_block_honored,
        claim_verdict=claim_verdict,
        completion=completion,
        chair_disposition=chair,
        data_only=data_only or (stage == "observation" and final == "block"),
        invented_news=False,
        news_headlines=tuple(news["news_headlines"]),  # type: ignore[arg-type]
        news_events=tuple(news["news_events"]),  # type: ignore[arg-type]
        news_protocol=None,
        confidence=confidence,
        grant=grant,
        reason=reason,
        skipped=skipped,
        enforced=enforced,
        artifact_ok=artifact_ok,
        done_outside_twin=done_outside_twin,
        fixture_id=fixture_id,
    )


def screen_input(
    prompt: str,
    *,
    fail_mode: str = "closed",
    mocks: Mapping[str, object] | None = None,
    fixture_id: str | None = None,
) -> GuardResult:
    refuse_invented_news_protocol(())
    mode = fail_mode_for(write_send=False, requested=fail_mode)
    local, local_reason = classify_input_locally(prompt)
    jev = _jev_from_mocks(mocks)
    jev_action = normalize_policy_action(jev["action"]) if jev.get("action") is not None else None
    if local == "support" or jev_action == "support":
        action = "support"
        reason = local_reason if local == "support" else "jev_support"
    elif jev_action == "block" or local == "block":
        action = "block"
        reason = "jev_block" if jev_action == "block" else local_reason
    elif jev_action:
        action = jev_action
        reason = f"jev_{jev_action}"
    elif local:
        action = local
        reason = local_reason
    else:
        action = "review"
        reason = "input_fail_closed_review"
    return _result(
        stage="input",
        action=action,
        reason=reason,
        fail_mode=mode,
        heuristics_hit=local is not None,
        heuristics_action=local,
        jev_action=jev_action,
        jev_block_honored=jev_action != "block" or action == "block",
        confidence=_confidence(jev.get("confidence")),
        fixture_id=fixture_id,
    )


def assess_action(
    action: Mapping[str, object] | GuardAction | None,
    *,
    fail_mode: str | None = None,
    heuristics: bool = True,
    mocks: Mapping[str, object] | None = None,
    s11_doc: Mapping[str, Any] | None = None,
    fixture_id: str | None = None,
    inventory: Sequence[str] | None = None,
) -> GuardResult:
    payload = action.as_mapping() if isinstance(action, GuardAction) else dict(action or {})
    parsed = GuardAction.from_mapping(payload)
    refuse_broker_action(parsed.name or "assess")
    if is_forbidden_dig_tool(parsed.name):
        raise JevPlacePathVeto(f"VETO PLACE_PATH: Dig must not assessAction {parsed.name}")
    if inventory is not None:
        assert_dig_inventory(inventory)

    write_send = is_write_send_tool(
        parsed.name,
        command=parsed.command,
        mutates=parsed.mutates,
        sends_external=parsed.sends_external,
    )
    mode = fail_mode_for(write_send=write_send, requested=fail_mode)
    deny = s11_hard_deny(parsed.as_mapping(), doc=s11_doc)
    mock_payload = dict(mocks or {})
    if mock_payload.get("s11_deny") is True:
        deny = deny or "S11_DENY"
    if deny:
        return _result(
            stage="tool_pre",
            action="block",
            reason=deny,
            fail_mode=mode,
            tool=parsed.name or None,
            grant=parsed.grant,
            confidence=parsed.confidence,
            fixture_id=fixture_id,
        )

    h_forced = mock_payload.get("heuristics")
    if isinstance(h_forced, Mapping) and h_forced.get("action"):
        h_action = normalize_policy_action(h_forced.get("action"))
        if h_action == "review":
            h_action = "ambiguous"
        h_reason = str(h_forced.get("reason") or f"heuristic_{h_action}")
    else:
        h_action, h_reason = classify_action_locally(parsed.as_mapping(), enabled=heuristics)

    if h_action == "block":
        return _result(
            stage="tool_pre",
            action="block",
            reason=h_reason,
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=True,
            heuristics_action="block",
            jev_block_honored=True,
            grant=parsed.grant,
            confidence=parsed.confidence,
            fixture_id=fixture_id,
        )

    jev = _jev_from_mocks(mock_payload)
    jev_action = normalize_policy_action(jev["action"]) if jev.get("action") is not None else None
    jev_conf = _confidence(jev.get("confidence") if jev.get("confidence") is not None else parsed.confidence)

    # Jev block / deny is hard. Heuristic allow cannot clear it.
    if jev_action == "block":
        return _result(
            stage="tool_pre",
            action="block",
            reason="jev_block_honored",
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action="block",
            jev_block_honored=True,
            grant=parsed.grant,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    if write_send and not parsed.grant:
        return _result(
            stage="tool_pre",
            action="block",
            reason="write_send_without_grant",
            fail_mode="closed",
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action=jev_action,
            jev_block_honored=True,
            grant=False,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    if jev_action == "support":
        return _result(
            stage="tool_pre",
            action="support",
            reason="jev_support_escalate_refuse_write" if write_send else "jev_support",
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action="support",
            grant=parsed.grant,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    if jev_action == "review":
        return _result(
            stage="tool_pre",
            action="review",
            reason="jev_review",
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action="review",
            grant=parsed.grant,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    destructive = is_destructive_tool(parsed.name, parsed.command)
    if destructive and (jev_conf is None or jev_conf < LOW_CONF):
        return _result(
            stage="tool_pre",
            action="review",
            reason="low_conf_destructive_never_allow",
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action=jev_action,
            grant=parsed.grant,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    if jev_action == "allow" or (h_action == "allow" and jev_action is None and is_read_only_tool(parsed.name, parsed.command)):
        return _result(
            stage="tool_pre",
            action="allow",
            reason="jev_allow" if jev_action == "allow" else h_reason,
            fail_mode=mode,
            tool=parsed.name or None,
            heuristics_hit=h_action != "ambiguous",
            heuristics_action=h_action,
            jev_action=jev_action,
            grant=parsed.grant,
            confidence=jev_conf,
            fixture_id=fixture_id,
        )

    return _result(
        stage="tool_pre",
        action="review",
        reason="tool_pre_fail_closed_review",
        fail_mode=mode,
        tool=parsed.name or None,
        heuristics_hit=h_action != "ambiguous",
        heuristics_action=h_action,
        jev_action=jev_action,
        grant=parsed.grant,
        confidence=jev_conf,
        fixture_id=fixture_id,
    )


def screen_observation(
    text: str,
    *,
    fail_mode: str = "closed",
    mocks: Mapping[str, object] | None = None,
    fixture_id: str | None = None,
) -> GuardResult:
    refuse_invented_news_protocol((str((mocks or {}).get("news_protocol") or ""),))
    mode = fail_mode_for(write_send=False, requested=fail_mode)
    local, local_reason = classify_observation_locally(text)
    jev = _jev_from_mocks(mocks)
    jev_action = normalize_policy_action(jev["action"]) if jev.get("action") is not None else None
    if jev_action == "block" or local == "block":
        action = "block"
        reason = "jev_block" if jev_action == "block" else local_reason
    elif jev_action == "support" or local == "support":
        action = "support"
        reason = "jev_support" if jev_action == "support" else local_reason
    elif jev_action:
        action = jev_action
        reason = f"jev_{jev_action}"
    elif local:
        action = local
        reason = local_reason
    else:
        action = "review"
        reason = "observation_fail_closed_review"
    return _result(
        stage="observation",
        action=action,
        reason=reason,
        fail_mode=mode,
        heuristics_hit=local is not None,
        heuristics_action=local,
        jev_action=jev_action,
        jev_block_honored=jev_action != "block" or action == "block",
        data_only=action == "block",
        confidence=_confidence(jev.get("confidence")),
        fixture_id=fixture_id,
    )


def screen_output(
    reply: str,
    *,
    fail_mode: str = "closed",
    mocks: Mapping[str, object] | None = None,
    fixture_id: str | None = None,
) -> GuardResult:
    mode = fail_mode_for(write_send=True, requested=fail_mode)
    local, local_reason = classify_input_locally(reply)
    jev = _jev_from_mocks(mocks)
    jev_action = normalize_policy_action(jev["action"]) if jev.get("action") is not None else None
    if local == "block" or jev_action == "block":
        action = "block"
        reason = local_reason if local == "block" else "jev_block_hold_send"
    elif local == "support" or jev_action == "support":
        action = "support"
        reason = "escalate_care"
    elif jev_action:
        action = jev_action
        reason = f"jev_{jev_action}"
    else:
        action = "review"
        reason = "output_fail_closed_review"
    return _result(
        stage="response",
        action=action,
        reason=reason,
        fail_mode=mode,
        heuristics_hit=local is not None,
        heuristics_action=local,
        jev_action=jev_action,
        jev_block_honored=jev_action != "block" or action == "block",
        confidence=_confidence(jev.get("confidence")),
        fixture_id=fixture_id,
    )


def _artifact_from_mocks(mocks: Mapping[str, object] | None, *, tmp: Path | None = None) -> tuple[Path | None, bool]:
    payload = dict(mocks or {})
    art = payload.get("artifact")
    if art is None:
        return None, True
    if isinstance(art, Mapping):
        present = bool(art.get("present"))
        raw_path = art.get("path")
        if not present:
            return Path(str(raw_path)) if raw_path else None, True
        if raw_path:
            return Path(str(raw_path)), False
        if tmp is not None:
            path = tmp / "s16_evidence.json"
            content = art.get("content") if isinstance(art.get("content"), Mapping) else {"ok": True, "schema": "s16_evidence"}
            path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
            return path, False
        return None, False
    return None, True


def verify_claim(
    claim: str,
    *,
    evidence: str | None = None,
    quote: str | None = None,
    mocks: Mapping[str, object] | None = None,
    artifact_path: Path | str | None = None,
    required_keys: Sequence[str] = (),
    required_consts: Mapping[str, object] | None = None,
    tmp: Path | None = None,
    fixture_id: str | None = None,
) -> GuardResult:
    """DONE_OUTSIDE twin. Confidence / Jev DONE never prove a write/send/place."""

    del evidence, quote, claim  # quoted for the screen; CODE owns the artifact
    refuse_invented_news_protocol(())
    jev = _jev_from_mocks(mocks)
    verdict_raw = str(jev.get("verdict") or jev.get("claim_verdict") or "").strip().lower()
    if verdict_raw not in CLAIM_VERDICTS:
        verdict_raw = "insufficient"
    jev_choice = str(jev.get("choice") or jev.get("jev_choice") or "")
    confidence = _confidence(jev.get("confidence"))

    path = artifact_path
    missing_forced = False
    if path is None:
        path, missing_forced = _artifact_from_mocks(mocks, tmp=tmp)
    verify = verify_artifact(
        path,
        required_keys=required_keys,
        required_consts=required_consts,
    )
    artifact_missing = (not verify.ok) and verify.reason in {
        "artifact_path_missing",
        "artifact_missing",
    }
    if missing_forced:
        artifact_missing = True
        verify = VerifyResult(False, "artifact_missing", None if path is None else str(path))

    twin = completion_truth(jev_choice=jev_choice, verify=verify)
    if artifact_missing:
        completion = "NOT_DONE_JEV_ADVISORY_ONLY"
        action = "review"
        reason = "missing_artifact_jev_advisory_only"
    elif verdict_raw in {"contradicted", "fabricated"}:
        completion = "NOT_DONE"
        action = "block"
        reason = f"claim_{verdict_raw}"
    elif verdict_raw == "insufficient":
        completion = "REVIEW"
        action = "review"
        reason = "claim_insufficient"
    elif verdict_raw == "supported" and verify.ok:
        completion = "DONE_OK"
        action = "allow"
        reason = "supported_plus_evidence"
    else:
        completion = "REVIEW"
        action = "review"
        reason = "claim_needs_chair"

    # CONF_GATE law: HIGH confidence never flips missing/bad evidence to DONE_OK.
    if completion != "DONE_OK":
        confidence_note = "confidence_neq_permission"
        if reason == "supported_plus_evidence":
            reason = confidence_note
        elif confidence is not None and confidence >= 0.85:
            reason = f"{reason}+{confidence_note}"

    return _result(
        stage="claim_verify",
        action=action,
        reason=reason,
        fail_mode="closed",
        claim_verdict=verdict_raw,
        completion=completion,
        confidence=confidence,
        artifact_ok=verify.ok,
        done_outside_twin=twin,
        fixture_id=fixture_id,
    )


@dataclass
class InMemoryToolAdapter:
    """Records intended tool use. Never executes MCP / shell / send / place."""

    attempts: list[dict[str, object]] = field(default_factory=list)

    def apply(self, result: GuardResult, action: GuardAction) -> dict[str, object]:
        if is_forbidden_dig_tool(action.name):
            raise JevPlacePathVeto(f"VETO PLACE_PATH: adapter refused {action.name}")
        write_send = is_write_send_tool(
            action.name,
            command=action.command,
            mutates=action.mutates,
            sends_external=action.sends_external,
        )
        if result.action == "allow" and not write_send:
            recorded = "read_recorded"
        elif result.action == "allow" and write_send:
            recorded = "write_recorded_not_executed"
        elif result.action == "review":
            recorded = "review_held"
        elif result.action == "support":
            recorded = "support_escalated"
        else:
            recorded = "block_refused"
        row = {
            "tool": action.name,
            "recorded": recorded,
            "executed_external": False,
            "place": False,
            "broker_effect": False,
            "action": result.action,
        }
        self.attempts.append(row)
        return row


def maybe_write_shadow_row(
    result: GuardResult,
    *,
    log_dir: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
    force: bool = False,
) -> Path | None:
    """Unset SHADOW → no write (no S16 side effects). Observe-only: never raise.

    Dig E KILL: APPLY + forbidden tool used to raise ``JevPlacePathVeto``
    here. That could abort Challenge place if this helper were imported on
    the writer path. Shadow write is skipped; place is not blocked.
    APPLY still never place — the raise moved off this observe harness.
    """

    if not s16_shadow_enabled(environ=environ, force=force):
        return None
    if s16_apply_enabled(environ=environ) and is_forbidden_dig_tool(result.tool):
        return None
    root = Path(log_dir) if log_dir is not None else default_s16_log_dir()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    directory = root / day
    directory.mkdir(parents=True, exist_ok=True)
    name = result.fixture_id or result.stage
    path = directory / f"{name}-{uuid4().hex[:8]}.json"
    doc = result.as_dict()
    doc["logged_at_utc"] = _now_utc()
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_screen(
    stage: str,
    request: Mapping[str, object],
    *,
    mocks: Mapping[str, object] | None = None,
    fail_mode: str | None = None,
    heuristics: bool = True,
    tmp: Path | None = None,
    fixture_id: str | None = None,
    inventory: Sequence[str] | None = None,
) -> GuardResult:
    name = str(stage or "").strip()
    if name == "input":
        return screen_input(
            str(request.get("prompt") or request.get("text") or ""),
            fail_mode=fail_mode or "closed",
            mocks=mocks,
            fixture_id=fixture_id,
        )
    if name == "tool_pre":
        action = request.get("action") if isinstance(request.get("action"), Mapping) else request
        return assess_action(
            action,
            fail_mode=fail_mode,
            heuristics=heuristics,
            mocks=mocks,
            fixture_id=fixture_id,
            inventory=inventory,
        )
    if name == "observation":
        return screen_observation(
            str(request.get("text") or request.get("observation") or request.get("body") or ""),
            fail_mode=fail_mode or "closed",
            mocks=mocks,
            fixture_id=fixture_id,
        )
    if name == "response":
        return screen_output(
            str(request.get("reply") or request.get("text") or ""),
            fail_mode=fail_mode or "closed",
            mocks=mocks,
            fixture_id=fixture_id,
        )
    if name == "claim_verify":
        return verify_claim(
            str(request.get("claim") or ""),
            evidence=str(request.get("evidence") or "") or None,
            quote=str(request.get("quote") or "") or None,
            mocks=mocks,
            tmp=tmp,
            fixture_id=fixture_id,
        )
    raise ValueError(f"unknown_s16_stage:{stage}")

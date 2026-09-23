"""Local S16 heuristics — fast-path only.

Law from jev-guardrails / Dig pack:

* Local **allow**: routine read-only (``ls``, ``git status``, list/search/get).
* Local **block**: catastrophe (``rm -rf /``, ``curl|bash``, disk wipe).
* Ambiguous → Jev ``assessAction``.
* A local heuristic **never** overrides a Jev ``block``.
* Observation path never invents ``NEWS_PROTOCOL``.
"""

from __future__ import annotations

import re
from typing import Mapping

from .veto import INVENTED_NEWS_PROTOCOL, refuse_invented_news_protocol

HeuristicAction = str  # allow | block | ambiguous

READ_ONLY_TOOLS = frozenset(
    {
        "gmail.search_threads",
        "gmail.get_thread",
        "gmail.get_message",
        "gmail.list_drafts",
        "slack.slack_read_channel",
        "slack.slack_search_public",
        "slack.slack_read_thread",
        "github.get_file_contents",
        "github.list_commits",
        "github.list_pull_requests",
        "github.search_code",
        "google-drive.search_files",
        "google-drive.get_file_metadata",
        "google-drive.read_file_content",
        "atlassian.getjiraissue",
        "atlassian.searchjiraissuesusingjql",
    }
)

READ_ONLY_TOOL_PREFIXES = (
    "list_",
    "search_",
    "get_",
    "read_",
    "fetch_",
)

READ_ONLY_COMMANDS = (
    re.compile(r"^ls(\s|$)"),
    re.compile(r"^git\s+status(\s|$)"),
    re.compile(r"^git\s+(diff|log|show|rev-parse|branch)(\s|$)"),
    re.compile(r"^pwd(\s|$)"),
    re.compile(r"^cat\s+\S+$"),
    re.compile(r"^head(\s|$)"),
    re.compile(r"^tail(\s+[^\-|]|$)"),
)

CATASTROPHE_COMMANDS = (
    re.compile(r"rm\s+-rf\s+(/|\*|~|/home|/var|/usr)(?:\b|$)"),
    re.compile(r"curl\b[^|\n]*\|\s*(ba)?sh"),
    re.compile(r"wget\b[^|\n]*\|\s*(ba)?sh"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"\bmkfs\."),
    re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:"),
    re.compile(r"chmod\s+-r\s+777\s+/"),
    re.compile(r"diskutil\s+erase"),
)

WRITE_SEND_MARKERS = (
    "send_message",
    "slack_send_message",
    "create_or_update_file",
    "create_deployment",
    "trash_file",
    "transitionjiraissue",
    "push_files",
    "merge_pull_request",
    "create_release",
    "forward",
    ".reply",
    "buy_domain",
    "edit_project_env",
)

DESTRUCTIVE_MARKERS = (
    "trash",
    "delete",
    "destroy",
    "wipe",
    "drop_table",
    "rm -",
    "chmod",
    "mkfs",
    "flatten",
)

JAILBREAK_PATTERNS = (
    re.compile(r"ignore (all |any )?(previous|prior|above) instructions", re.I),
    re.compile(r"\byou are now (dan|jailbroken)\b", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"developer mode", re.I),
    re.compile(r"do anything now", re.I),
)

SELF_HARM_PATTERNS = (
    re.compile(r"\b(kill|hurt|harm) myself\b", re.I),
    re.compile(r"suicid", re.I),
    re.compile(r"\bwant to die\b", re.I),
    re.compile(r"end my life", re.I),
)

INJECTION_PATTERNS = (
    re.compile(r"ignore (all |any )?(previous|prior|above) instructions", re.I),
    re.compile(r"exfiltrat", re.I),
    re.compile(r"<script\b", re.I),
    re.compile(r"hidden.{0,40}instruction", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"send (all )?(secrets|api keys|tokens) to", re.I),
)

LOW_CONF = 0.50


def _norm_tool(name: str | None) -> str:
    return str(name or "").strip().lower()


def tool_leaf(name: str | None) -> str:
    raw = _norm_tool(name)
    if "." in raw:
        return raw.rsplit(".", 1)[-1]
    return raw


def is_read_only_tool(name: str | None, command: str | None = None) -> bool:
    full = _norm_tool(name)
    leaf = tool_leaf(name)
    if full in READ_ONLY_TOOLS or leaf in READ_ONLY_TOOLS:
        return True
    if any(leaf.startswith(prefix) for prefix in READ_ONLY_TOOL_PREFIXES):
        if not any(marker in leaf for marker in ("send", "create", "update", "delete", "trash", "push")):
            return True
    cmd = str(command or "").strip()
    if cmd and any(pat.search(cmd) for pat in READ_ONLY_COMMANDS):
        return True
    return False


def is_write_send_tool(
    name: str | None,
    *,
    command: str | None = None,
    mutates: bool = False,
    sends_external: bool = False,
) -> bool:
    if mutates or sends_external:
        return True
    full = _norm_tool(name)
    if any(marker in full for marker in WRITE_SEND_MARKERS):
        return True
    cmd = str(command or "")
    if any(pat.search(cmd) for pat in CATASTROPHE_COMMANDS):
        return True
    if re.search(r"\b(rm|mv|chmod|chown|unlink)\b", cmd):
        return True
    return False


def is_destructive_tool(name: str | None, command: str | None = None) -> bool:
    blob = f"{_norm_tool(name)} {command or ''}".lower()
    return any(marker in blob for marker in DESTRUCTIVE_MARKERS) or any(
        pat.search(str(command or "")) for pat in CATASTROPHE_COMMANDS
    )


def classify_action_locally(
    action: Mapping[str, object] | None,
    *,
    enabled: bool = True,
) -> tuple[HeuristicAction, str]:
    """Return ``(allow|block|ambiguous, reason)``.

    Disable only for fixture tests via ``enabled=False``.
    """

    if not enabled:
        return "ambiguous", "heuristics_disabled"
    payload = dict(action or {})
    name = str(payload.get("name") or payload.get("tool") or "")
    command = str(payload.get("command") or payload.get("args", {}).get("command") or "")
    if isinstance(payload.get("args"), Mapping):
        command = command or str(payload["args"].get("command") or payload["args"].get("cmd") or "")
    if any(pat.search(command) for pat in CATASTROPHE_COMMANDS):
        return "block", "heuristic_catastrophe"
    if is_read_only_tool(name, command):
        return "allow", "heuristic_readonly"
    return "ambiguous", "heuristic_ambiguous"


def classify_input_locally(prompt: str) -> tuple[str | None, str]:
    text = str(prompt or "")
    if any(pat.search(text) for pat in SELF_HARM_PATTERNS):
        return "support", "self_harm_escalate"
    if any(pat.search(text) for pat in JAILBREAK_PATTERNS):
        return "block", "jailbreak_or_harmful_input"
    return None, "input_unclassified"


def classify_observation_locally(text: str) -> tuple[str | None, str]:
    raw = str(text or "")
    if not raw.strip():
        return "review", "empty_untrusted_observation"
    if any(pat.search(raw) for pat in INJECTION_PATTERNS):
        return "block", "injection_or_exfil"
    return None, "observation_unclassified"


def empty_news_fields() -> dict[str, object]:
    """Observation path never invents NEWS. Always empty."""

    refuse_invented_news_protocol(())
    return {
        "invented_news": False,
        "news_headlines": [],
        "news_events": [],
        "news_protocol": None,
        INVENTED_NEWS_PROTOCOL: None,
    }

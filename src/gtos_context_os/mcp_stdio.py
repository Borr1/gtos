"""Read-only MCP stdio wrapper for Context OS.

This module intentionally stays dependency-free.  It supports the real MCP
JSON-RPC handshake used by Codex/Claude clients while preserving the older
internal JSON-lines request shape used by tests and lightweight scripts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from src.gtos_context_os.catalog import DEFAULT_DB_PATH, catalog_stats, search_catalog
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.pack import build_context_pack
from src.gtos_context_os.resume import build_resume_bundle
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.second_brain import DEFAULT_SECOND_BRAIN_ROOT, search_second_brain, second_brain_status
from src.gtos_context_os.session import list_session_capsules, session_capsule_status
from src.gtos_context_os.session_state import load_active_session_state, load_continuation_cursor
from src.gtos_context_os.symbols import search_symbols

MCP_PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {
    "name": "gtos-context-os",
    "title": "GTOS Context OS",
    "version": "1.0.0",
}


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


MCP_TO_INTERNAL_METHOD = {
    "gtos_context_stats": "stats",
    "gtos_context_health": "health",
    "gtos_context_search": "search",
    "gtos_route_overview": "route",
    "gtos_memory_search": "memory",
    "gtos_second_brain_status": "second_brain_status",
    "gtos_second_brain_search": "second_brain_search",
    "gtos_second_brain_read": "second_brain_read",
    "gtos_context_read_file": "read_file",
    "gtos_session_capsule_status": "session_capsule_status",
    "gtos_session_capsules": "session_capsules",
    "gtos_active_session_state": "active_state",
    "gtos_continuation_cursor": "cursor",
    "gtos_code_symbol_search": "symbols",
    "gtos_resume_bundle": "resume",
    "gtos_context_pack": "pack",
    "gtos_context_fast_pack": "fast_pack",
}


MCP_TOOLS = [
    {
        "name": "gtos_context_pack",
        "title": "Build GTOS Context Pack",
        "description": (
            "Build a compact GTOS task pack from current repo context, optional "
            "Codex memory, and optional Obsidian second-brain retrieval."
        ),
        "inputSchema": _schema(
            {
                "task": {"type": "string", "description": "Current task or question."},
                "profile": {
                    "type": "string",
                    "description": "Pack profile such as ultimate, replay-repair, selector-scheduler, cost-order.",
                },
                "route": {"type": "string", "description": "Optional route name."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "include_memory": {"type": "boolean"},
                "include_second_brain": {"type": "boolean"},
                "second_brain_query": {"type": "string"},
                "include_health": {"type": "boolean"},
                "section_timeout_seconds": {"type": "number", "minimum": 1, "maximum": 60},
                "auto_rebuild_stale": {"type": "boolean"},
            },
            ["task"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_context_fast_pack",
        "title": "Build Fast GTOS Context Pack",
        "description": (
            "Build a bounded context pack optimized for MCP reliability. "
            "Health is skipped by default and each optional section has a short local timeout."
        ),
        "inputSchema": _schema(
            {
                "task": {"type": "string", "description": "Current task or question."},
                "profile": {"type": "string"},
                "route": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "include_memory": {"type": "boolean"},
                "include_second_brain": {"type": "boolean"},
                "second_brain_query": {"type": "string"},
                "section_timeout_seconds": {"type": "number", "minimum": 1, "maximum": 30},
                "allow_stale": {"type": "boolean"},
            },
            ["task"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_second_brain_search",
        "title": "Search GTOS Second Brain",
        "description": "Search distilled Obsidian second-brain notes without bulk-loading the vault.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "include_raw": {"type": "boolean"},
                "root": {"type": "string", "description": "Optional second-brain vault root override."},
            },
            ["query"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_context_search",
        "title": "Search GTOS Context Catalog",
        "description": "Search the Context OS catalog over current repo context and route summaries.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            ["query"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_context_health",
        "title": "GTOS Context Health",
        "description": "Return context catalog freshness, second-brain status, session capsules, and process hints.",
        "inputSchema": _schema(
            {
                "second_brain_root": {"type": "string"},
                "session_capsule_limit": {"type": "integer", "minimum": 1, "maximum": 20},
            }
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_context_stats",
        "title": "GTOS Context Catalog Stats",
        "description": "Return Context OS catalog counts by authority tier and evidence class.",
        "inputSchema": _schema(),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_route_overview",
        "title": "GTOS Route Overview",
        "description": "Summarize route-owned artifacts and read-first files from the Context OS catalog.",
        "inputSchema": _schema(
            {
                "route": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            ["route"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_memory_search",
        "title": "Search Codex Memory",
        "description": "Search controlled Codex memory registry files as recall, not current authority.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "memory_root": {"type": "string"},
            },
            ["query"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_second_brain_status",
        "title": "GTOS Second Brain Status",
        "description": "Return Obsidian second-brain vault counts and raw distillation queue.",
        "inputSchema": _schema({"root": {"type": "string"}}),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_second_brain_read",
        "title": "Read GTOS Second Brain Note",
        "description": "Read one exact Obsidian second-brain note returned by search, bounded to the vault.",
        "inputSchema": _schema(
            {
                "path": {
                    "type": "string",
                    "description": "Vault-relative path such as conversation-intelligence/Component_Root_Issue_Atlas.md.",
                },
                "root": {"type": "string", "description": "Optional second-brain vault root override."},
                "max_chars": {"type": "integer", "minimum": 1000, "maximum": 100000},
            },
            ["path"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_context_read_file",
        "title": "Read GTOS Repo File",
        "description": "Read one repo-relative file path, bounded to the configured GTOS repo root.",
        "inputSchema": _schema(
            {
                "path": {
                    "type": "string",
                    "description": "Repo-relative path. Use search or route tools first for exact paths.",
                },
                "max_chars": {"type": "integer", "minimum": 1000, "maximum": 100000},
            },
            ["path"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_session_capsule_status",
        "title": "GTOS Session Capsule Status",
        "description": "Return recent Context OS continuity capsule status.",
        "inputSchema": _schema({"limit": {"type": "integer", "minimum": 1, "maximum": 20}}),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_session_capsules",
        "title": "List GTOS Session Capsules",
        "description": "List recent local continuity capsules for restart/compaction recovery.",
        "inputSchema": _schema(
            {
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                "task_query": {"type": "string"},
            }
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_active_session_state",
        "title": "Read GTOS Active Session State",
        "description": (
            "Read compact current active-state/root-cause checkpoint files. "
            "This is continuity intelligence and must be verified against current disk."
        ),
        "inputSchema": _schema(),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_continuation_cursor",
        "title": "Read GTOS Continuation Cursor",
        "description": (
            "Read the compact short-lived cursor for the last observation, current hypothesis, "
            "and next atomic step after restart or compaction."
        ),
        "inputSchema": _schema(),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_code_symbol_search",
        "title": "Search GTOS Live Code Symbols",
        "description": (
            "Search live Python symbols by name/path/docstring for exact source navigation. "
            "Use before opening code; verify source before claims."
        ),
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "roots": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional repo-relative roots. Defaults to src, scripts, tests.",
                },
                "max_files": {"type": "integer", "minimum": 1, "maximum": 20000},
                "max_file_bytes": {"type": "integer", "minimum": 1, "maximum": 10000000},
                "max_elapsed_seconds": {"type": "number", "minimum": 0.25, "maximum": 30},
            },
            ["query"],
        ),
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "gtos_resume_bundle",
        "title": "Build GTOS Resume Bundle",
        "description": "Build a one-stop read-only resume bundle after restart or compaction.",
        "inputSchema": _schema(
            {
                "task": {"type": "string"},
                "profile": {"type": "string"},
                "route": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "include_memory": {"type": "boolean"},
                "include_second_brain": {"type": "boolean"},
                "second_brain_root": {"type": "string"},
                "write_capsule": {"type": "boolean", "description": "Defaults false for MCP read-only use."},
            },
            ["task"],
        ),
        "annotations": {"readOnlyHint": True},
    },
]


def serve_stdio(*, repo: Path | str = ".", db_path: Path | str = DEFAULT_DB_PATH) -> int:
    for line in sys.stdin:
        request: dict[str, Any] | None = None
        try:
            request = json.loads(line)
            response = handle_wire_request(request, repo=repo, db_path=db_path)
        except Exception as exc:  # pragma: no cover - defensive server loop
            if isinstance(request, dict) and request.get("jsonrpc") == "2.0":
                response = mcp_error(request.get("id"), -32603, str(exc))
            else:
                response = {"ok": False, "error": str(exc)}
        if response is not None:
            print(json.dumps(response, sort_keys=True), flush=True)
    return 0


def handle_wire_request(
    request: dict[str, Any],
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> dict[str, Any] | None:
    if request.get("jsonrpc") == "2.0":
        return handle_mcp_request(request, repo=repo, db_path=db_path)
    return handle_stdio_request(request, repo=repo, db_path=db_path)


def handle_mcp_request(
    request: dict[str, Any],
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> dict[str, Any] | None:
    method = str(request.get("method") or "")
    request_id = request.get("id")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        requested_version = str(params.get("protocolVersion") or MCP_PROTOCOL_VERSION)
        return mcp_result(
            request_id,
            {
                "protocolVersion": requested_version if requested_version else MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": (
                    "Read-only GTOS Context OS. Use gtos_context_pack and "
                    "gtos_second_brain_search for targeted retrieval; do not "
                    "bulk-load raw vault or route ledgers."
                ),
            },
        )
    if method == "ping":
        return mcp_result(request_id, {})
    if method == "tools/list":
        return mcp_result(request_id, {"tools": MCP_TOOLS})
    if method == "tools/call":
        tool_name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if tool_name not in MCP_TO_INTERNAL_METHOD:
            return mcp_error(request_id, -32602, f"Unknown tool: {tool_name}")
        tool_result = call_mcp_tool(tool_name, arguments, repo=repo, db_path=db_path)
        return mcp_result(request_id, tool_result)
    return mcp_error(request_id, -32601, f"Method not found: {method}")


def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    try:
        response = handle_stdio_request(
            {"method": MCP_TO_INTERNAL_METHOD[tool_name], "params": arguments},
            repo=repo,
            db_path=db_path,
        )
    except Exception as exc:
        response = {"ok": False, "error": str(exc)}
    is_error = not bool(response.get("ok"))
    payload = response.get("result") if not is_error else {"error": response.get("error", "tool_failed")}
    text = json.dumps(payload, indent=2, sort_keys=True)
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }
    if isinstance(payload, dict):
        result["structuredContent"] = payload
    return result


def mcp_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def mcp_error(request_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def handle_stdio_request(
    request: dict[str, Any],
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    method = str(request.get("method") or "")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}
    if method == "stats":
        return {"ok": True, "result": catalog_stats(db_path=db_path, repo=repo)}
    if method == "health":
        return {
            "ok": True,
            "result": context_intelligence_health(
                repo=repo,
                db_path=db_path,
                second_brain_root=params.get("second_brain_root"),
                session_capsule_limit=int(params.get("session_capsule_limit") or 5),
            ),
        }
    if method == "search":
        return {
            "ok": True,
            "result": search_catalog(str(params.get("query") or ""), db_path=db_path, repo=repo, limit=int(params.get("limit") or 12)),
        }
    if method == "route":
        return {
            "ok": True,
            "result": route_overview(str(params.get("route") or ""), db_path=db_path, repo=repo, limit=int(params.get("limit") or 25)),
        }
    if method == "memory":
        return {
            "ok": True,
            "result": search_memory(str(params.get("query") or ""), memory_root=params.get("memory_root"), limit=int(params.get("limit") or 8)),
        }
    if method == "second_brain_status":
        return {"ok": True, "result": second_brain_status(root=params.get("root"))}
    if method == "second_brain_search":
        return {
            "ok": True,
            "result": search_second_brain(
                str(params.get("query") or ""),
                root=params.get("root"),
                limit=int(params.get("limit") or 10),
                include_raw=bool(params.get("include_raw")),
            ),
        }
    if method == "second_brain_read":
        return {
            "ok": True,
            "result": read_bounded_text(
                root=Path(params.get("root") or DEFAULT_SECOND_BRAIN_ROOT),
                rel_path=str(params.get("path") or ""),
                max_chars=int(params.get("max_chars") or 20000),
                root_label="second_brain",
            ),
        }
    if method == "read_file":
        return {
            "ok": True,
            "result": read_bounded_text(
                root=Path(repo),
                rel_path=str(params.get("path") or ""),
                max_chars=int(params.get("max_chars") or 20000),
                root_label="repo",
            ),
        }
    if method == "session_capsule_status":
        return {
            "ok": True,
            "result": session_capsule_status(repo=repo, limit=int(params.get("limit") or 5)),
        }
    if method == "session_capsules":
        return {
            "ok": True,
            "result": list_session_capsules(
                repo=repo,
                limit=int(params.get("limit") or 5),
                task_query=params.get("task_query"),
            ),
        }
    if method == "active_state":
        return {
            "ok": True,
            "result": load_active_session_state(repo=repo),
        }
    if method == "cursor":
        return {
            "ok": True,
            "result": load_continuation_cursor(repo=repo),
        }
    if method == "symbols":
        roots_value = params.get("roots")
        if isinstance(roots_value, list):
            roots = tuple(str(item) for item in roots_value if str(item).strip())
        elif isinstance(roots_value, str) and roots_value.strip():
            roots = tuple(part.strip() for part in roots_value.split(",") if part.strip())
        else:
            roots = ("src", "scripts", "tests")
        return {
            "ok": True,
            "result": search_symbols(
                str(params.get("query") or ""),
                repo=repo,
                roots=roots,
                limit=int(params.get("limit") or 20),
                max_files=int(params.get("max_files") or 5000),
                max_file_bytes=int(params.get("max_file_bytes") or 750_000),
                max_elapsed_seconds=float(params.get("max_elapsed_seconds") or 5.0),
            ),
        }
    if method == "resume":
        return {
            "ok": True,
            "result": build_resume_bundle(
                str(params.get("task") or ""),
                repo=repo,
                db_path=db_path,
                limit=int(params.get("limit") or 10),
                profile=str(params.get("profile") or "ultimate"),
                route=params.get("route"),
                include_memory=_bool_param(params, "include_memory", True),
                include_second_brain=_bool_param(params, "include_second_brain", True),
                second_brain_root=params.get("second_brain_root"),
                write_capsule=_bool_param(params, "write_capsule", False),
            ),
        }
    if method == "pack":
        return {
            "ok": True,
            "result": build_context_pack(
                str(params.get("task") or ""),
                repo=repo,
                db_path=db_path,
                limit=int(params.get("limit") or 10),
                profile=str(params.get("profile") or "standard"),
                route=params.get("route"),
                include_memory=_bool_param(params, "include_memory", False),
                memory_root=params.get("memory_root"),
                include_second_brain=_bool_param(params, "include_second_brain", False),
                second_brain_root=params.get("second_brain_root"),
                second_brain_query=params.get("second_brain_query"),
                include_health=_bool_param(params, "include_health", True),
                section_timeout_seconds=float(params.get("section_timeout_seconds") or 8.0),
                auto_rebuild_stale=_bool_param(params, "auto_rebuild_stale", False),
            ),
        }
    if method == "fast_pack":
        return {
            "ok": True,
            "result": build_context_pack(
                str(params.get("task") or ""),
                repo=repo,
                db_path=db_path,
                limit=int(params.get("limit") or 8),
                profile=str(params.get("profile") or "ultimate"),
                route=params.get("route"),
                include_memory=_bool_param(params, "include_memory", True),
                memory_root=params.get("memory_root"),
                include_second_brain=_bool_param(params, "include_second_brain", False),
                second_brain_root=params.get("second_brain_root"),
                second_brain_query=params.get("second_brain_query"),
                include_health=False,
                include_recent_capsules=True,
                section_timeout_seconds=float(params.get("section_timeout_seconds") or 3.0),
                allow_stale=_bool_param(params, "allow_stale", True),
                auto_rebuild_stale=False,
                auto_build=False,
            ),
        }
    return {"ok": False, "error": f"unknown_method:{method}"}


def _bool_param(params: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in params:
        return default
    value = params.get(key)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return default


def read_bounded_text(
    *,
    root: Path,
    rel_path: str,
    max_chars: int = 20000,
    root_label: str,
) -> dict[str, Any]:
    if not rel_path or rel_path.startswith("/"):
        raise ValueError("path must be a non-empty relative path")
    root_resolved = root.expanduser().resolve()
    target = (root_resolved / rel_path).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f"path escapes {root_label} root")
    if not target.exists():
        raise FileNotFoundError(target.as_posix())
    if not target.is_file():
        raise ValueError("path is not a file")
    max_chars = max(1000, min(int(max_chars), 100000))
    text = target.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]
    return {
        "root_label": root_label,
        "root": root_resolved.as_posix(),
        "path": target.relative_to(root_resolved).as_posix(),
        "abs_path": target.as_posix(),
        "size_bytes": target.stat().st_size,
        "max_chars": max_chars,
        "truncated": truncated,
        "text": text,
    }

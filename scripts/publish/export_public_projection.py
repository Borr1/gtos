#!/usr/bin/env python3
"""Deterministic public projection of an Origin GTOS checkout.

Pattern redaction only. Live account literals are stripped by
scrub_private.py, which stays off this tree. The overlay directory wins
over redacted files. ORIGIN_SHA is the exact source commit.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXCLUDE_GLOBS = (
    ".git",
    ".git/**",
    "**/.env",
    "**/.env.*",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/*id_rsa*",
    "**/*.pid",
    "**/*.bak",
    "**/*.bak_*",
    "**/*.bak-*",
    "**/*bak-*",
    "*bak_*",
    "*bak-*",
    "**/*bak_*",
    "**/*bak-*",
    "**/*credential*",
    "**/*secret*",
    "judgment/live/**",
    "pipeline_state/**",
    "shadow_logs/**",
    "sot/SECRET_SCAN_*",
    "config/profiles/ftmo_sh*",
    "config/profiles/ftmo_gatous*",
    "config/profiles/ftmo_aracna*",
    "config/profiles/fundednext.yaml",
    "config/profiles/*verification*",
    "gtos-spreadfloor-backup-*",
    "gtos-spreadfloor-backup-*/**",
    "_carry_backup*",
    "_carry_backup*/**",
    "knowledge_base_backtest_jan27_mar21_backup/**",
    "tmp/**",
    "podcast_pipeline/transcripts/**",
    "podcast_pipeline/**",
    "**/*.html",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.token.json",
    "._*",
    "**/._*",
)

# Root scratch written against a live desk. The runnable entrypoints stay.
ROOT_SCRATCH = re.compile(r"^_[^/]+$")

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
EMAIL_SKIP = {"example.com", "example.org", "example.net", "localhost", "test.com"}
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
TOKEN_RES = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9\-_]{16,}\b"),
    re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bcrsr_[A-Za-z0-9]{16,}\b"),
    re.compile(r"(?<!\d)\d{8,12}:[A-Za-z0-9_\-]{30,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{16,}"),
    re.compile(r"\b[a-z][a-z0-9+\-.]*://[^/\s:@]+:[^/\s@]+@"),
)
LOGIN_ASSIGN_RE = re.compile(
    r"(?i)(\b(?:login|account(?:_number|_id)?|mt5_login|chat_id|telegram_chat)\b\s*[:=]\s*['\"]?)\d{5,12}"
)
LOGIN_SHA_RE = re.compile(r"(?i)(login_sha256\s*[:=]\s*['\"]?)[a-fA-F0-9]{64}")
PASSWORD_RE = re.compile(
    r"(?i)(?<![\"'])(\b(?:password|passwd|pwd|api[_-]?key|access[_-]?token|auth[_-]?token|bot[_-]?token)\b\s*[:=]\s*)(['\"]).*?\2"
)
PASSWORD_BARE_RE = re.compile(
    r"(?i)(\b(?:password|passwd|pwd)\b\s*[:=]\s*)([^\s#'\"]{4,})"
)
PHONE_RE = re.compile(r"(?<!\w)\+\d{10,15}(?!\d)")
VPS_PAREN_RE = re.compile(r"\(VPS\s+[^)]+\)")
FINGERPRINT_RE = re.compile(r"(sha256\[:8\]=)[0-9a-fA-F]{8}")
TS_NET_RE = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9.-]*\.ts\.net\b")
ADMIN_PATH_RE = re.compile(r"(?i)[A-Za-z]:\\Users\\Administrator|/[Uu]sers/Administrator")
WINRM_URL_RE = re.compile(r"(?i)\bhttps?://[^\s'\"]+:598[56]\b")


def excluded(rel: str) -> bool:
    path = rel.replace("\\", "/")
    if ROOT_SCRATCH.match(path):
        return True
    folded = path.casefold()
    for pattern in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(folded, pattern.casefold()):
            return True
    return False


def _ip_kind(ip: str) -> str | None:
    parts = [int(p) for p in ip.split(".")]
    if parts[0] in (0, 127) or ip == "255.255.255.255":
        return None
    if parts[0] == 10 or (parts[0] == 192 and parts[1] == 168):
        return "lan"
    if parts[0] == 172 and 16 <= parts[1] <= 31:
        return "lan"
    if parts[0] == 100 and 64 <= parts[1] <= 127:
        return "cgnat"
    if parts[0] == 169 and parts[1] == 254:
        return None
    if all(p < 10 for p in parts):
        return None
    return "public"


def redact_text(text: str) -> str:
    text = VPS_PAREN_RE.sub("(host-local)", text)
    text = FINGERPRINT_RE.sub(lambda match: match.group(1) + ("0" * 8), text)
    text = TS_NET_RE.sub("redacted-host.ts.net", text)
    text = re.sub(r"(?i)tailscale", "host-mesh", text)
    text = re.sub(r"(?i)\bwinrm\b", "host-admin", text)
    text = ADMIN_PATH_RE.sub("host-local", text)
    text = WINRM_URL_RE.sub("redacted-winrm", text)
    for cre in TOKEN_RES:
        text = cre.sub("redacted", text)
    def _login_sha(match: re.Match[str]) -> str:
        prefix = match.group(1)
        zeros = "0" * 64
        if prefix.rstrip().endswith(("'", '"')):
            return prefix + zeros
        return prefix + '"' + zeros + '"'

    text = LOGIN_SHA_RE.sub(_login_sha, text)
    text = LOGIN_ASSIGN_RE.sub(r"\g<1>0", text)
    text = PASSWORD_RE.sub(r"\1\2redacted\2", text)
    text = PASSWORD_BARE_RE.sub(r"\1redacted", text)
    text = PHONE_RE.sub("+00000000000", text)

    def email_sub(match: re.Match[str]) -> str:
        domain = match.group(0).split("@", 1)[1].lower()
        if domain in EMAIL_SKIP:
            return match.group(0)
        return "redacted@example.com"

    text = EMAIL_RE.sub(email_sub, text)

    def ip_sub(match: re.Match[str]) -> str:
        if _ip_kind(match.group(0)) is None:
            return match.group(0)
        return "0.0.0.0"

    return IPV4_RE.sub(ip_sub, text)


def tracked_files(source: Path) -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=source)
    return [p.decode() for p in out.split(b"\0") if p]


def sha(source: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()


def copy_overlay(overlay: Path, dest: Path) -> None:
    if not overlay.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(overlay):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        rel_dir = Path(dirpath).relative_to(overlay)
        target_dir = dest / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            src = Path(dirpath) / name
            dst = target_dir / name
            shutil.copy2(src, dst)


def project(source: Path, dest: Path, overlay: Path | None) -> str:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    origin = sha(source)
    copied = 0
    dropped = 0
    for rel in tracked_files(source):
        if excluded(rel):
            dropped += 1
            continue
        src = source / rel
        if not src.is_file():
            continue
        data = src.read_bytes()
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if b"\0" in data[:8192]:
            target.write_bytes(data)
        else:
            text = data.decode("utf-8", errors="surrogateescape")
            target.write_bytes(redact_text(text).encode("utf-8", errors="surrogateescape"))
        copied += 1
    if overlay is not None:
        copy_overlay(overlay, dest)
    (dest / "ORIGIN_SHA").write_text(origin + "\n", encoding="utf-8")
    manifest = hashlib.sha256()
    for path in sorted(p for p in dest.rglob("*") if p.is_file() and ".git" not in p.parts):
        rel = path.relative_to(dest).as_posix()
        manifest.update(rel.encode())
        manifest.update(b"\0")
        manifest.update(path.read_bytes())
        manifest.update(b"\0")
    (dest / ".projection-manifest.sha256").write_text(manifest.hexdigest() + "\n", encoding="utf-8")
    print(f"origin {origin}")
    print(f"copied {copied}")
    print(f"dropped {dropped}")
    print(f"manifest {manifest.hexdigest()}")
    return origin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args()
    project(args.source, args.dest, args.overlay)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Session LN — host-admin transport helper for the GTOS VPS.

Design rules, each of which exists because a prior session paid for it:

* **PowerShell is passed as a FILE, never as an inline string.** ``run_ps`` on a long
  inline script is the documented mangling hazard. ``run_file`` uploads the script and
  executes it with ``-File``.
* **Uploads are chunked base64 with a host-side SHA-256 check.** The chunk cap matches the
  ceremony packages' documented <=2,800-character base64 method.
* **The password is read from ``~/.gtos/vps.env`` and never printed, logged, returned or
  written.** It exists only inside the ``host-admin.Session`` object.
* Every call returns ``(rc, stdout, stderr)`` decoded as UTF-8 with replacement, so a
  stray byte can never crash a ceremony step.

Usage as a library::

    from vps import VPS
    v = VPS()
    rc, out, err = v.run_file("local.ps1")
    v.put_file("local/payload.py", r"C:\\...\\dest.py")   # hash-verified
"""
from __future__ import annotations

import base64
import hashlib
import os
import pathlib
import sys
import time

import host-admin

ENV_PATH = pathlib.Path.home() / ".gtos" / "vps.env"
# Base64 chunk cap. The ceremony packages document "<=2,800-character base64-chunk";
# we stay under it so an ``Add-Content`` line never approaches a command-line limit.
CHUNK = 2400


def _load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, val = line.partition("=")
        env[k.strip()] = val.strip().strip('"').strip("'")
    return env


class VPS:
    def __init__(self) -> None:
        env = _load_env()
        self.host = env["VPS_HOST"]
        self.name = env.get("VPS_NAME", "")
        self.user = env["VPS_USER"]
        port = env.get("VPS_WINRM_PORT", "5985")
        transport = env.get("VPS_WINRM_TRANSPORT", "ntlm")
        # NOTE: the password enters the Session and is never retained on self.
        self._s = host-admin.Session(
            f"http://{self.host}:{port}/wsman",
            auth=(self.user, env["VPS_PASSWORD"]),
            transport=transport,
            read_timeout_sec=600,
            operation_timeout_sec=540,
        )

    # ---------------------------------------------------------------- exec ---
    def _ps(self, script: str):
        r = self._s.run_ps(script)
        return (
            r.status_code,
            r.std_out.decode("utf-8", "replace"),
            r.std_err.decode("utf-8", "replace"),
        )

    def ps_short(self, script: str):
        """Run a SHORT inline snippet. Only for one-liners with no quoting risk."""
        return self._ps(script)

    def run_file(self, local_ps1: str, *, remote_dir: str = r"C:\Users\trader\ln20260806"):
        """Upload a local .ps1 and execute it with ``powershell -File``.

        This is the only sanctioned way to run a multi-line script on the host.
        """
        local = pathlib.Path(local_ps1)
        remote = f"{remote_dir}\\{local.name}"
        self.put_file(str(local), remote, quiet=True)
        return self._ps(
            f"& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass "
            f"-File '{remote}' 2>&1 | Out-String -Width 4096"
        )

    # ---------------------------------------------------------------- copy ---
    def put_file(self, local_path: str, remote_path: str, *, quiet: bool = False) -> str:
        """Chunked base64 upload with a host-side SHA-256 equality proof.

        Returns the host-computed SHA-256 (uppercase). Raises on mismatch, so a
        partially transferred payload can never be installed.
        """
        data = pathlib.Path(local_path).read_bytes()
        want = hashlib.sha256(data).hexdigest()
        b64 = base64.b64encode(data).decode("ascii")
        tmp = remote_path + ".b64.part"

        parent = remote_path.rsplit("\\", 1)[0]
        rc, out, err = self._ps(
            f"New-Item -ItemType Directory -Force -Path '{parent}' | Out-Null; "
            f"if (Test-Path '{tmp}') {{ Remove-Item -Force '{tmp}' }}; 'ready'"
        )
        if rc != 0:
            raise RuntimeError(f"put_file prep failed rc={rc}: {err[:400]}")

        chunks = [b64[i : i + CHUNK] for i in range(0, len(b64), CHUNK)]
        for n, c in enumerate(chunks):
            rc, out, err = self._ps(f"Add-Content -Path '{tmp}' -Value '{c}' -NoNewline -Encoding Ascii")
            if rc != 0:
                raise RuntimeError(f"put_file chunk {n}/{len(chunks)} failed rc={rc}: {err[:400]}")
            if not quiet and (n % 25 == 0 or n == len(chunks) - 1):
                print(f"    chunk {n + 1}/{len(chunks)}", file=sys.stderr, flush=True)

        # Decode base64 -> bytes with byte-exact IO. LM's session lost 10 KB to Windows
        # text-mode newline translation; [IO.File]::WriteAllBytes cannot do that.
        rc, out, err = self._ps(
            f"$b = [Convert]::FromBase64String((Get-Content -Raw '{tmp}')); "
            f"[IO.File]::WriteAllBytes('{remote_path}', $b); "
            f"Remove-Item -Force '{tmp}'; "
            f"(Get-FileHash -Algorithm SHA256 '{remote_path}').Hash + ' ' + "
            f"(Get-Item '{remote_path}').Length"
        )
        if rc != 0:
            raise RuntimeError(f"put_file decode failed rc={rc}: {err[:400]}")
        got, _, length = out.strip().partition(" ")
        if got.lower() != want:
            raise RuntimeError(
                f"put_file HASH MISMATCH for {remote_path}: host {got.lower()} != local {want}"
            )
        if not quiet:
            print(f"    uploaded {remote_path}  {got.lower()[:12]}  {length.strip()} B", file=sys.stderr)
        return got


def main() -> int:
    v = VPS()
    if len(sys.argv) >= 3 and sys.argv[1] == "put":
        v.put_file(sys.argv[2], sys.argv[3])
        return 0
    if len(sys.argv) >= 2 and sys.argv[1].endswith(".ps1"):
        t0 = time.time()
        rc, out, err = v.run_file(sys.argv[1])
        sys.stdout.write(out)
        if err.strip():
            sys.stderr.write("\n--- STDERR ---\n" + err)
        print(f"\n[rc={rc}  {time.time() - t0:.1f}s]", file=sys.stderr)
        return rc
    rc, out, err = v.ps_short("hostname; whoami; (Get-Date).ToUniversalTime().ToString('s') + 'Z'")
    sys.stdout.write(out)
    sys.stderr.write(err)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

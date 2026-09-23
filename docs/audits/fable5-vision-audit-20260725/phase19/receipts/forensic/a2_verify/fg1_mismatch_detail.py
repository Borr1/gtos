#!/usr/bin/env python3
"""For each of the 8 patch-id-mismatched cherry-pick pairs, compare per-file
patches and report exactly which files' hunks differ between source commit and
integrated commit."""
import subprocess, json

WT = "/Users/borr/GTOSActive/worktrees/wave19-sol-integration-20260801"
PAIRS = [
    ("CR", "47139bc35", "4b54c9550"),
    ("CS", "7f9ab73c2", "01b7975a6"),
    ("FB", "33ea0413e", "a3f15587b"),
    ("FC", "4dd71e566", "33181552a"),
    ("FD", "08b7ea41a", "a23505600"),
    ("FE-telemetry", "a86976b14", "23ddb448b"),
    ("FE-close", "2573afddb", "b946b0969"),
    ("FF", "d52e48b2d", "41ebaf260"),
]

def run(*args, inp=None):
    r = subprocess.run(["git", "-C", WT] + list(args), capture_output=True, text=True, input=inp)
    if r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr[:300]}")
    return r.stdout

def files_of(sha):
    return [f for f in run("show", "--name-only", "--format=", sha).splitlines() if f]

def file_patch_id(sha, path):
    patch = run("show", sha, "--", path)
    if not patch.strip():
        return "NOPATCH"
    r = subprocess.run(["git", "-C", WT, "patch-id", "--stable"], capture_output=True, text=True, input=patch)
    return r.stdout.split()[0] if r.stdout.strip() else "EMPTY"

out = []
for label, src, integ in PAIRS:
    fs, fi = set(files_of(src)), set(files_of(integ))
    entry = {"pair": label, "src": src, "integ": integ,
             "files_only_in_src": sorted(fs - fi),
             "files_only_in_integ": sorted(fi - fs),
             "files_with_differing_patch": []}
    for f in sorted(fs & fi):
        if file_patch_id(src, f) != file_patch_id(integ, f):
            entry["files_with_differing_patch"].append(f)
    out.append(entry)

print(json.dumps(out, indent=1))

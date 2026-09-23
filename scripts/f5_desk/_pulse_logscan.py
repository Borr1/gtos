from pathlib import Path
p = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
text = p.read_text(encoding="utf-16")
needles = [
    "reconciliation FAILED",
    "immutable_entry_risk_unavailable",
    "governor_ready false",
    "governor_ready=False",
    "governor_ready: False",
]
for n in needles:
    print(n, text.lower().count(n.lower()))
# last 2 real lines
lines = [ln for ln in text.splitlines() if ln.strip()]
print("LAST", lines[-1][:260])
print("HAS_frozen", "frozen" in text.lower())
# last governor mention
gov = [ln for ln in lines if "governor_ready" in ln]
print("GOV_N", len(gov), "LAST", (gov[-1][:200] if gov else "none"))
recon = [ln for ln in lines if "FAILED" in ln and "reconcil" in ln.lower()]
print("RECON_FAIL_N", len(recon), "LAST", (recon[-1][:200] if recon else "none"))

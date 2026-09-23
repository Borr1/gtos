from pathlib import Path
text = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log").read_text(encoding="utf-16")
lines = text.splitlines()
recon = [ln for ln in lines if "reconciliation FAILED" in ln or "immutable_entry_risk_unavailable" in ln]
print("N", len(recon))
print("FIRST", recon[0][:220] if recon else None)
print("---LAST5---")
for ln in recon[-5:]:
    print(ln[:260])
# after 10:00Z today
late = [ln for ln in recon if ln.startswith("2026-08-27 10:")]
print("AFTER_10Z", len(late))
if late:
    print("LATE_LAST", late[-1][:260])

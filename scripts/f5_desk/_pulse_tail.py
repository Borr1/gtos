from pathlib import Path
p = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
keys = ("reconciliation FAILED", "immutable_entry_risk_unavailable", "governor_ready false", "179380936", "closed by broker")
print("N", len(lines))
print("LAST", lines[-1][:240] if lines else "empty")
hits = [ln for ln in lines if any(k in ln for k in keys)]
print("HITS", len(hits))
for ln in hits[-12:]:
    print(ln[:240])

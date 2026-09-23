"""Component 7 — Minimal FastAPI Dashboard (Phase 1).

Diagnostic JSON endpoints for monitoring agent state.
Run standalone:  uvicorn src.components.dashboard:app --port 8080
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from src.components.knowledge_base import KnowledgeBase
from src.components.monitoring import AlertSystem
from src.utils.file_io import load_json, load_yaml
import datetime
from datetime import timezone
import json
import os

# Check for psutil availability
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


app = FastAPI(title="Gold Agent Dashboard", version="0.1.0")

# ── Shared state (configured at startup or by tests) ─────────────────

_kb: Optional[KnowledgeBase] = None
_alerts: Optional[AlertSystem] = None
_kb_base: str = "knowledge_base"


def configure(kb_base: str = "knowledge_base") -> None:
    """Set the knowledge base path and initialise shared objects."""
    global _kb, _alerts, _kb_base
    _kb_base = kb_base
    _kb = KnowledgeBase(base_path=kb_base)
    _alerts = AlertSystem(kb_base=kb_base)


def _get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        configure(_kb_base)
    return _kb


def _get_alerts() -> AlertSystem:
    global _alerts
    if _alerts is None:
        configure(_kb_base)
    return _alerts


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    """Simple HTML page with links to diagnostic endpoints."""
    return """<!DOCTYPE html>
<html><head><title>Gold Agent Dashboard</title>
<style>
body{font-family:monospace;max-width:600px;margin:40px auto;padding:0 20px}
a{display:block;margin:8px 0;font-size:16px}
</style></head><body>
<h1>Gold Agent — Dashboard</h1>
<a href="/status">/status — Current session state</a>
<a href="/trades">/trades — Trade history</a>
<a href="/stats">/stats — Rolling statistics</a>
<a href="/alerts">/alerts — Recent alerts</a>
<a href="/health">/health — System health</a>
</body></html>"""


@app.get("/status")
def status():
    """Current session state (latest session manifest)."""
    kb = _get_kb()
    sessions_dir = kb.base / "sessions"
    if not sessions_dir.exists():
        return {"status": "no active session", "sessions_found": 0}

    files = sorted(sessions_dir.glob("*_session.json"), reverse=True)
    if not files:
        return {"status": "no active session", "sessions_found": 0}

    latest = load_json(files[0])
    return {"status": "ok", "latest_session": latest}


@app.get("/trades")
def trades():
    """List all trades from the trade index, most recent first."""
    kb = _get_kb()
    index = load_json(kb.base / "index" / "_trade_index.json")
    trade_list = index.get("trades", [])
    return {"count": len(trade_list), "trades": list(reversed(trade_list))}


@app.get("/trades/{trade_id}")
def trade_detail(trade_id: str):
    """Full trade record as JSON."""
    kb = _get_kb()
    trade = kb.load_trade(trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
    return trade.model_dump(mode="json")


@app.get("/stats")
def stats():
    """Rolling statistics."""
    kb = _get_kb()
    return kb.load_rolling_stats()


@app.get("/alerts")
def alerts():
    """Last 50 alerts, most recent first."""
    alert_sys = _get_alerts()
    items = alert_sys.get_recent(50)
    return {"count": len(items), "alerts": items}


@app.get("/health")
def health():
    """System health check."""
    kb = _get_kb()
    checks: dict = {}

    # Config exists
    config_path = Path("config/agent_config.yaml")
    checks["config_exists"] = config_path.exists()

    # KB directories
    checks["kb_base_exists"] = kb.base.exists()
    checks["trades_dir_exists"] = (kb.base / "trades").exists()
    checks["sessions_dir_exists"] = (kb.base / "sessions").exists()
    checks["vectordb_dir_exists"] = (kb.base / "vectordb").exists()

    # LanceDB accessible
    try:
        import lancedb
        db = lancedb.connect(str(kb.base / "vectordb"))
        tables = list(db.table_names())
        checks["lancedb_accessible"] = True
        checks["lancedb_tables"] = tables
    except Exception as exc:
        checks["lancedb_accessible"] = False
        checks["lancedb_error"] = str(exc)

    # Rolling stats file
    stats_path = kb.base / "statistics" / "rolling_stats.json"
    checks["rolling_stats_exists"] = stats_path.exists()

    # Alerts file
    alerts_path = kb.base / "meta" / "alerts.jsonl"
    checks["alerts_file_exists"] = alerts_path.exists()

    all_ok = all(
        v for k, v in checks.items()
        if k.endswith("_exists") or k == "lancedb_accessible"
    )
    return {"healthy": all_ok, "checks": checks}


# ═══════════════════════════════════════════════════════════════════════
# ENHANCED DASHBOARD (Category A Infrastructure Improvements)  
# ═══════════════════════════════════════════════════════════════════════

from src.components.monitoring import shadow_collector, security_monitor, performance_monitor


@app.get("/monitoring", response_class=HTMLResponse)
def monitoring_dashboard():
    """Enhanced monitoring dashboard with real-time metrics."""
    return """<!DOCTYPE html>
<html><head>
<title>Gold Agent - Enhanced Monitoring</title>
<meta charset="utf-8">
<style>
body{font-family:monospace;max-width:1200px;margin:20px auto;padding:0 20px;background:#f5f5f5}
.header{background:#333;color:#fff;padding:15px;border-radius:5px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:15px}
.card{background:#fff;border:1px solid #ddd;border-radius:5px;padding:15px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.metric{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee}
.metric:last-child{border-bottom:none}
.value{font-weight:bold;color:#007acc}
.critical{color:#d32f2f}
.warning{color:#f57c00}
.ok{color:#388e3c}
.refresh{background:#007acc;color:#fff;border:none;padding:10px 20px;border-radius:3px;cursor:pointer}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{text-align:left;padding:8px;border-bottom:1px solid #ddd}
th{background:#f0f0f0}
.timestamp{font-size:0.8em;color:#666}
</style>
<script>
function refreshPage(){location.reload()}
setInterval(refreshPage, 30000); // Auto-refresh every 30s
</script>
</head><body>

<div class="header">
    <h1>Gold Agent - Enhanced Monitoring Dashboard</h1>
    <button class="refresh" onclick="refreshPage()">Refresh Now</button>
    <div class="timestamp">Auto-refresh every 30 seconds</div>
</div>

<div class="grid">
    <div class="card">
        <h3>System Health</h3>
        <div id="health-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>Recent Alerts</h3>
        <div id="alerts-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>Performance Metrics</h3>
        <div id="performance-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>Security Events</h3>
        <div id="security-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>Trading Status</h3>
        <div id="trading-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>Component Status</h3>
        <div id="component-status">Loading...</div>
    </div>
</div>

<script>
// Fetch and update all sections
async function updateDashboard() {
    try {
        // Health check
        const health = await fetch('/health').then(r => r.json());
        document.getElementById('health-status').innerHTML = renderHealth(health);
        
        // Recent alerts
        const alerts = await fetch('/alerts').then(r => r.json());
        document.getElementById('alerts-status').innerHTML = renderAlerts(alerts);
        
        // Performance
        const perf = await fetch('/monitoring/performance').then(r => r.json());
        document.getElementById('performance-status').innerHTML = renderPerformance(perf);
        
        // Security
        const security = await fetch('/monitoring/security').then(r => r.json());
        document.getElementById('security-status').innerHTML = renderSecurity(security);
        
        // Trading status
        const trading = await fetch('/status').then(r => r.json());
        document.getElementById('trading-status').innerHTML = renderTrading(trading);
        
        // Component status
        const components = await fetch('/monitoring/components').then(r => r.json());
        document.getElementById('component-status').innerHTML = renderComponents(components);
        
    } catch (e) {
        console.error('Dashboard update failed:', e);
    }
}

function renderHealth(health) {
    const status = health.healthy ? 'OK' : 'ISSUES';
    const cssClass = health.healthy ? 'ok' : 'critical';
    let html = `<div class="metric"><span>Overall Status</span><span class="${cssClass}">${status}</span></div>`;
    
    for (const [key, value] of Object.entries(health.checks)) {
        if (key.endsWith('_exists') || key === 'lancedb_accessible') {
            const status = value ? 'OK' : 'FAIL';
            const cssClass = value ? 'ok' : 'critical';
            html += `<div class="metric"><span>${key}</span><span class="${cssClass}">${status}</span></div>`;
        }
    }
    return html;
}

function renderAlerts(alerts) {
    if (alerts.count === 0) return '<div class="metric"><span>No recent alerts</span><span class="ok">OK</span></div>';
    
    let html = `<div class="metric"><span>Alert Count</span><span class="value">${alerts.count}</span></div>`;
    
    const recent = alerts.alerts.slice(0, 5);
    for (const alert of recent) {
        const cssClass = alert.level === 'CRITICAL' ? 'critical' : alert.level === 'WARNING' ? 'warning' : 'value';
        const time = new Date(alert.timestamp).toLocaleTimeString();
        html += `<div class="metric"><small>${alert.alert_type} (${time})</small><span class="${cssClass}">${alert.level}</span></div>`;
    }
    return html;
}

function renderPerformance(perf) {
    if (!perf.slow_operations_last_hour) return '<div class="metric"><span>Performance</span><span class="ok">Good</span></div>';
    
    const slowCount = perf.slow_operations_last_hour.length;
    const cssClass = slowCount > 5 ? 'critical' : slowCount > 0 ? 'warning' : 'ok';
    
    let html = `<div class="metric"><span>Slow Operations (1h)</span><span class="${cssClass}">${slowCount}</span></div>`;
    
    if (perf.cpu_usage) html += `<div class="metric"><span>CPU Usage</span><span class="value">${perf.cpu_usage.toFixed(1)}%</span></div>`;
    if (perf.memory_usage) html += `<div class="metric"><span>Memory Usage</span><span class="value">${perf.memory_usage.toFixed(1)}%</span></div>`;
    
    return html;
}

function renderSecurity(security) {
    let html = '<div class="metric"><span>Security Status</span><span class="ok">Monitoring</span></div>';
    
    if (security.failed_auth_attempts > 0) {
        html += `<div class="metric"><span>Failed Auth Attempts</span><span class="warning">${security.failed_auth_attempts}</span></div>`;
    }
    
    if (security.rate_limit_hits > 0) {
        html += `<div class="metric"><span>Rate Limit Hits</span><span class="warning">${security.rate_limit_hits}</span></div>`;
    }
    
    return html;
}

function renderTrading(trading) {
    if (trading.status === 'no active session') {
        return '<div class="metric"><span>Session Status</span><span class="warning">No Active Session</span></div>';
    }
    
    const session = trading.latest_session;
    let html = `<div class="metric"><span>Session Date</span><span class="value">${session.date}</span></div>`;
    html += `<div class="metric"><span>Day of Week</span><span class="value">${session.day_of_week}</span></div>`;
    
    if (session.trade_summary) {
        const traded = session.trade_summary.trade_taken;
        html += `<div class="metric"><span>Trade Taken</span><span class="${traded ? 'ok' : 'value'}">${traded ? 'Yes' : 'No'}</span></div>`;
    }
    
    return html;
}

function renderComponents(components) {
    let html = '';
    for (const [component, status] of Object.entries(components)) {
        const cssClass = status === 'healthy' ? 'ok' : status === 'degraded' ? 'warning' : 'critical';
        html += `<div class="metric"><span>${component}</span><span class="${cssClass}">${status}</span></div>`;
    }
    return html || '<div class="metric"><span>Components</span><span class="ok">All Healthy</span></div>';
}

// Initial load
updateDashboard();
</script>

</body></html>"""


@app.get("/monitoring/performance")
def monitoring_performance():
    """Performance monitoring endpoint."""
    try:
        summary = performance_monitor.get_performance_summary()
        
        # Add system metrics if available
        if PSUTIL_AVAILABLE:
            try:
                summary.update({
                    "cpu_usage": psutil.cpu_percent(interval=0.1),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent
                })
            except Exception:
                pass
        else:
            pass
            
        return summary
    except Exception as e:
        return {"error": str(e)}


@app.get("/monitoring/security")
def monitoring_security():
    """Security monitoring endpoint."""
    try:
        # Get recent security events from the last hour
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        security_file = security_monitor._security_dir / f"audit_{today}.jsonl"
        
        failed_auth = 0
        rate_limits = 0
        
        if security_file.exists():
            cutoff = datetime.now(timezone.utc) - datetime.timedelta(hours=1)
            
            with open(security_file) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        if event_time > cutoff:
                            if event["event_type"] == "AUTH_FAILURE":
                                failed_auth += 1
                            elif event["event_type"] == "RATE_LIMIT":
                                rate_limits += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        
        return {
            "failed_auth_attempts": failed_auth,
            "rate_limit_hits": rate_limits,
            "monitoring_active": True
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/monitoring/components")
def monitoring_components():
    """Component health status."""
    try:
        # Check various component health
        components = {}
        
        # Knowledge base health
        try:
            kb = _get_kb()
            if kb.base.exists() and (kb.base / "trades").exists():
                components["KnowledgeBase"] = "healthy"
            else:
                components["KnowledgeBase"] = "degraded"
        except Exception:
            components["KnowledgeBase"] = "critical"
        
        # Alert system health
        try:
            alerts = _get_alerts()
            alerts_file = alerts._alerts_file
            if alerts_file.exists():
                components["AlertSystem"] = "healthy"
            else:
                components["AlertSystem"] = "degraded"
        except Exception:
            components["AlertSystem"] = "critical"
        
        # Shadow collector health
        try:
            if shadow_collector._running:
                components["ShadowCollector"] = "healthy"
            else:
                components["ShadowCollector"] = "degraded"
        except Exception:
            components["ShadowCollector"] = "critical"
            
        return components
    except Exception as e:
        return {"error": str(e)}


@app.get("/monitoring/shadow-data")
def get_shadow_data(date: str = None):
    """Get shadow data for a specific date."""
    try:
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
        shadow_file = shadow_collector._shadow_dir / f"metrics_{date}.jsonl"
        
        if not shadow_file.exists():
            return {"date": date, "metrics": [], "count": 0}
        
        metrics = []
        with open(shadow_file) as f:
            for line in f:
                try:
                    metric = json.loads(line.strip())
                    metrics.append(metric)
                except json.JSONDecodeError:
                    continue
        
        return {
            "date": date,
            "metrics": metrics[-100:],  # Last 100 metrics
            "count": len(metrics)
        }
    except Exception as e:
        return {"error": str(e)}


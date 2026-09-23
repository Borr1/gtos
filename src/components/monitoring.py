"""Component 7 — Monitoring & Alerting (Phase 1).

AlertSystem:  append-only JSONL alerts to knowledge_base/meta/alerts.jsonl.
SessionLogger: structured daily log files under knowledge_base/meta/logs/.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal, Optional

import os
import queue
import threading
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Callable

# Optional imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

AlertLevel = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]


class AlertSystem:
    """Append-only alert log.

    Writes one JSON object per line to ``<kb_base>/meta/alerts.jsonl``.
    CRITICAL alerts are also printed to stderr.
    """

    def __init__(self, kb_base: str | Path = "knowledge_base") -> None:
        self.base = Path(kb_base)
        self._alerts_dir = self.base / "meta"
        self._alerts_dir.mkdir(parents=True, exist_ok=True)
        self._alerts_file = self._alerts_dir / "alerts.jsonl"

    def log_alert(
        self,
        level: AlertLevel,
        alert_type: str,
        message: str,
        details: Optional[dict] = None,
    ) -> dict:
        """Append an alert entry and return it."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "alert_type": alert_type,
            "message": message,
            "details": details or {},
        }

        with open(self._alerts_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        if level == "CRITICAL":
            print(f"CRITICAL ALERT [{alert_type}]: {message}", file=sys.stderr)

        logger.log(
            getattr(logging, level, logging.INFO),
            "[%s] %s: %s",
            level,
            alert_type,
            message,
        )
        return entry

    def get_recent(self, n: int = 50) -> list[dict]:
        """Return the last *n* alerts (most recent first)."""
        if not self._alerts_file.exists():
            return []
        lines: list[str] = []
        with open(self._alerts_file) as f:
            lines = f.readlines()
        alerts = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    alerts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return list(reversed(alerts[-n:]))


class SessionLogger:
    """Structured daily log writer.

    Each day gets its own file: ``<kb_base>/meta/logs/YYYY-MM-DD.log``.
    Lines are ``TIMESTAMP | COMPONENT | EVENT | JSON_DATA``.
    """

    def __init__(self, kb_base: str | Path = "knowledge_base") -> None:
        self.base = Path(kb_base)
        self._logs_dir = self.base / "meta" / "logs"
        self._logs_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, date_str: Optional[str] = None) -> Path:
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self._logs_dir / f"{date_str}.log"

    def _write(self, component: str, event: str, data: dict) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        line = f"{ts} | {component} | {event} | {json.dumps(data)}\n"
        path = self._log_path()
        with open(path, "a") as f:
            f.write(line)
        return line.rstrip()

    # ── Convenience log methods ───────────────────────────────────────

    def log_candle_evaluation(
        self,
        candle_time: str,
        decision: str,
        reason: Optional[str] = None,
        confidence: Optional[int] = None,
    ) -> str:
        return self._write("PRIMARY_ANALYZER", "CANDLE_EVAL", {
            "candle_time": candle_time,
            "decision": decision,
            "reason": reason,
            "confidence": confidence,
        })

    def log_debate(
        self,
        bull_strength: int,
        bear_strength: int,
        verdict: str,
        confidence: int,
    ) -> str:
        return self._write("DEBATE", "VERDICT", {
            "bull_strength": bull_strength,
            "bear_strength": bear_strength,
            "verdict": verdict,
            "confidence": confidence,
        })

    def log_trade_executed(
        self,
        trade_id: str,
        direction: str,
        entry: float,
        sl: float,
        tp1: float,
    ) -> str:
        return self._write("EXECUTION", "TRADE_OPEN", {
            "trade_id": trade_id,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
        })

    def log_trade_closed(
        self,
        trade_id: str,
        outcome: str,
        r_multiple: float,
    ) -> str:
        return self._write("EXECUTION", "TRADE_CLOSE", {
            "trade_id": trade_id,
            "outcome": outcome,
            "r_multiple": r_multiple,
        })

    def log_error(
        self,
        component: str,
        error_type: str,
        details: Optional[dict] = None,
    ) -> str:
        return self._write(component, "ERROR", {
            "error_type": error_type,
            "details": details or {},
        })

    def read_log(self, date_str: Optional[str] = None) -> list[str]:
        """Return all lines from the log file for a given date."""
        path = self._log_path(date_str)
        if not path.exists():
            return []
        with open(path) as f:
            return [line.rstrip() for line in f if line.strip()]


# ═══════════════════════════════════════════════════════════════════════
# ENHANCED MONITORING SYSTEM (Category A Infrastructure Improvements)
# ═══════════════════════════════════════════════════════════════════════

import threading
import queue
# Handled above with try/except
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Callable


@dataclass
class MetricSnapshot:
    """Single point-in-time system metric."""
    timestamp: str
    metric_type: str
    value: float
    component: str
    details: Dict[str, Any]


class ShadowDataCollector:
    """Background data collection without affecting trading logic.
    
    Collects performance metrics, system resources, and trading patterns
    for analysis without impacting real-time operations.
    """
    
    def __init__(self, kb_base: str | Path = "knowledge_base"):
        self.base = Path(kb_base)
        self._shadow_dir = self.base / "meta" / "shadow_data"
        self._shadow_dir.mkdir(parents=True, exist_ok=True)
        self._running = False
        self._collector_thread = None
        self._metrics_queue = queue.Queue(maxsize=1000)
        self._session_logger = SessionLogger(kb_base)
        
    def start_collection(self):
        """Start background data collection."""
        if self._running:
            return
            
        self._running = True
        self._collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collector_thread.start()
        logger.info("Shadow data collection started")
        
    def stop_collection(self):
        """Stop background data collection."""
        self._running = False
        if self._collector_thread:
            self._collector_thread.join(timeout=5)
        logger.info("Shadow data collection stopped")
        
    def collect_metric(self, metric_type: str, value: float, component: str, **details):
        """Thread-safe metric collection."""
        try:
            metric = MetricSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                metric_type=metric_type,
                value=value,
                component=component,
                details=details
            )
            self._metrics_queue.put_nowait(metric)
        except queue.Full:
            # Log warning but don't block trading operations
            logger.warning("Shadow data queue full, dropping metric")
    
    def _collection_loop(self):
        """Background collection loop."""
        while self._running:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Process queued application metrics
                self._process_metric_queue()
                
                # Sleep to avoid CPU overhead
                time.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in shadow collection loop: {e}")
                time.sleep(30)  # Back off on error
    
    def _collect_system_metrics(self):
        """Collect system performance metrics."""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.collect_metric("cpu_usage", cpu_percent, "SYSTEM")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.collect_metric("memory_usage_percent", memory.percent, "SYSTEM")
            self.collect_metric("memory_available_gb", memory.available / (1024**3), "SYSTEM")
            
            # Disk usage
            disk = psutil.disk_usage("/")
            self.collect_metric("disk_usage_percent", (disk.used / disk.total) * 100, "SYSTEM")
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def _process_metric_queue(self):
        """Process queued metrics and persist to shadow data."""
        metrics_to_write = []
        
        # Drain the queue (non-blocking)
        while True:
            try:
                metric = self._metrics_queue.get_nowait()
                metrics_to_write.append(metric)
            except queue.Empty:
                break
        
        if metrics_to_write:
            self._persist_metrics(metrics_to_write)
    
    def _persist_metrics(self, metrics: List[MetricSnapshot]):
        """Write metrics to shadow data files."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            shadow_file = self._shadow_dir / f"metrics_{today}.jsonl"
            
            with open(shadow_file, "a") as f:
                for metric in metrics:
                    data = {
                        "timestamp": metric.timestamp,
                        "type": metric.metric_type,
                        "value": metric.value,
                        "component": metric.component,
                        "details": metric.details
                    }
                    f.write(json.dumps(data) + "\n")
                    
        except Exception as e:
            logger.error(f"Failed to persist shadow metrics: {e}")


class SecurityEventMonitor:
    """Enhanced alert system for security events."""
    
    def __init__(self, kb_base: str | Path = "knowledge_base"):
        self.alert_system = AlertSystem(kb_base)
        self.base = Path(kb_base)
        self._security_dir = self.base / "meta" / "security"
        self._security_dir.mkdir(parents=True, exist_ok=True)
        self._failed_attempts = {}
        self._rate_limits = {}
        
    def log_auth_attempt(self, component: str, user_id: str, success: bool, source_ip: str = None):
        """Log authentication attempts and detect suspicious patterns."""
        key = f"{component}:{user_id}"
        timestamp = datetime.now(timezone.utc)
        
        if not success:
            # Track failed attempts
            if key not in self._failed_attempts:
                self._failed_attempts[key] = []
            self._failed_attempts[key].append(timestamp)
            
            # Clean old attempts (older than 1 hour)
            cutoff = timestamp - timedelta(hours=1)
            self._failed_attempts[key] = [
                t for t in self._failed_attempts[key] if t > cutoff
            ]
            
            # Alert on excessive failures
            if len(self._failed_attempts[key]) >= 5:
                self.alert_system.log_alert(
                    "CRITICAL",
                    "EXCESSIVE_AUTH_FAILURES",
                    f"5+ authentication failures for {user_id} in {component}",
                    {
                        "component": component,
                        "user_id": user_id,
                        "source_ip": source_ip,
                        "failure_count": len(self._failed_attempts[key])
                    }
                )
        else:
            # Clear failed attempts on successful auth
            if key in self._failed_attempts:
                del self._failed_attempts[key]
    
    def log_rate_limit_hit(self, component: str, endpoint: str, source: str):
        """Log rate limiting events and escalate if persistent."""
        key = f"{component}:{endpoint}:{source}"
        timestamp = datetime.now(timezone.utc)
        
        if key not in self._rate_limits:
            self._rate_limits[key] = []
        self._rate_limits[key].append(timestamp)
        
        # Clean old events (older than 1 hour)
        cutoff = timestamp - timedelta(hours=1)
        self._rate_limits[key] = [t for t in self._rate_limits[key] if t > cutoff]
        
        # Alert on persistent rate limiting
        if len(self._rate_limits[key]) >= 10:
            self.alert_system.log_alert(
                "WARNING",
                "PERSISTENT_RATE_LIMITING",
                f"Persistent rate limiting on {endpoint} from {source}",
                {
                    "component": component,
                    "endpoint": endpoint,
                    "source": source,
                    "hit_count": len(self._rate_limits[key])
                }
            )
    
    def log_data_access(self, component: str, resource: str, user_id: str, operation: str):
        """Log sensitive data access for audit trail."""
        self._write_security_log("DATA_ACCESS", {
            "component": component,
            "resource": resource,
            "user_id": user_id,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def log_config_change(self, component: str, setting: str, old_value: str, new_value: str, user_id: str):
        """Log configuration changes."""
        self.alert_system.log_alert(
            "WARNING",
            "CONFIG_CHANGE",
            f"Configuration changed: {setting} in {component}",
            {
                "component": component,
                "setting": setting,
                "old_value": old_value[:100] if old_value else None,  # Truncate for security
                "new_value": new_value[:100] if new_value else None,
                "user_id": user_id
            }
        )
        
        self._write_security_log("CONFIG_CHANGE", {
            "component": component,
            "setting": setting,
            "old_value": old_value,
            "new_value": new_value,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _write_security_log(self, event_type: str, data: Dict[str, Any]):
        """Write to security audit log."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            security_file = self._security_dir / f"audit_{today}.jsonl"
            
            entry = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data
            }
            
            with open(security_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write security log: {e}")


class PerformanceMonitor:
    """Monitor component performance and detect anomalies."""
    
    def __init__(self, kb_base: str | Path = "knowledge_base"):
        self.alert_system = AlertSystem(kb_base)
        self.shadow_collector = ShadowDataCollector(kb_base)
        self._component_timings = {}
        self._slow_operations = []
    
    def time_operation(self, component: str, operation: str):
        """Context manager for timing operations."""
        return _OperationTimer(self, component, operation)
    
    def record_timing(self, component: str, operation: str, duration_ms: float):
        """Record operation timing."""
        self.shadow_collector.collect_metric(
            "operation_duration_ms", duration_ms, component, 
            operation=operation
        )
        
        # Track slow operations
        if duration_ms > 5000:  # 5+ seconds
            self._slow_operations.append({
                "component": component,
                "operation": operation,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Alert on very slow operations
            if duration_ms > 30000:  # 30+ seconds
                self.alert_system.log_alert(
                    "WARNING",
                    "SLOW_OPERATION",
                    f"Slow operation: {operation} in {component} took {duration_ms:.1f}ms",
                    {
                        "component": component,
                        "operation": operation,
                        "duration_ms": duration_ms
                    }
                )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get recent performance summary."""
        return {
            "slow_operations_last_hour": [
                op for op in self._slow_operations 
                if datetime.fromisoformat(op["timestamp"]) > 
                datetime.now(timezone.utc) - timedelta(hours=1)
            ]
        }


class _OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, component: str, operation: str):
        self.monitor = monitor
        self.component = component
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.monitor.record_timing(self.component, self.operation, duration_ms)


class YouTubeRateLimiter:
    """Rate limiter specifically for YouTube API calls to prevent 429 errors."""
    
    def __init__(self):
        self._last_request_time = 0
        self._request_count = 0
        self._block_until = 0
        self._block_count = 0
        self._lock = threading.Lock()
    
    def wait_for_rate_limit(self):
        """Wait for rate limit before making YouTube request."""
        with self._lock:
            current_time = time.time()
            
            # Check if we're in a block period
            if current_time < self._block_until:
                wait_time = self._block_until - current_time
                logger.warning(f"YouTube rate limited, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                return
            
            # Normal rate limiting: 10-12 seconds between requests
            time_since_last = current_time - self._last_request_time
            if time_since_last < 10:
                sleep_time = 10 + (time.time() % 2)  # 10-12 seconds
                logger.info(f"YouTube rate limit: waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
            self._request_count += 1
            
            # Extra pause every 5 requests
            if self._request_count % 5 == 0:
                logger.info("YouTube rate limit: 5-request pause")
                time.sleep(60)
    
    def handle_429_error(self):
        """Handle YouTube 429 error with exponential backoff."""
        with self._lock:
            self._block_count += 1
            
            # Exponential backoff: 90s * block_count (max 10 minutes)
            backoff_seconds = min(90 * self._block_count, 600)
            self._block_until = time.time() + backoff_seconds
            
            logger.error(
                f"YouTube 429 error (block #{self._block_count}), "
                f"backing off for {backoff_seconds}s"
            )
    
    def reset_on_success(self):
        """Reset block state on successful request."""
        with self._lock:
            if self._block_count > 0:
                logger.info("YouTube requests recovered, resetting block count")
                self._block_count = 0
                self._block_until = 0


# Global instances for easy access
shadow_collector = ShadowDataCollector()
security_monitor = SecurityEventMonitor()
performance_monitor = PerformanceMonitor()
youtube_limiter = YouTubeRateLimiter()



# ═══════════════════════════════════════════════════════════════════════
# ENHANCED SESSION LOGGING (Category A Infrastructure Improvements)
# ═══════════════════════════════════════════════════════════════════════

class EnhancedSessionLogger(SessionLogger):
    """Extended session logger with enhanced audit trail capabilities."""
    
    def __init__(self, kb_base: str | Path = "knowledge_base"):
        super().__init__(kb_base)
        self._audit_dir = self.base / "meta" / "audit"
        self._audit_dir.mkdir(parents=True, exist_ok=True)
        
    def log_component_start(self, component: str, version: str = None, config: Dict[str, Any] = None):
        """Log component initialization with configuration."""
        return self._write("LIFECYCLE", "COMPONENT_START", {
            "component": component,
            "version": version,
            "config": config or {},
            "process_id": os.getpid()
        })
    
    def log_component_stop(self, component: str, exit_code: int = 0, reason: str = None):
        """Log component shutdown."""
        return self._write("LIFECYCLE", "COMPONENT_STOP", {
            "component": component,
            "exit_code": exit_code,
            "reason": reason,
            "process_id": os.getpid()
        })
    
    def log_data_source_access(self, source: str, operation: str, records_affected: int = None):
        """Log data source access for audit trail."""
        return self._write("DATA_ACCESS", "SOURCE_OPERATION", {
            "source": source,
            "operation": operation,
            "records_affected": records_affected,
            "user_context": self._get_user_context()
        })
    
    def log_model_prediction(self, model: str, input_hash: str, prediction: str, confidence: float):
        """Log AI model predictions for reproducibility."""
        return self._write("AI_MODEL", "PREDICTION", {
            "model": model,
            "input_hash": input_hash,
            "prediction": prediction,
            "confidence": confidence
        })
    
    def log_external_api_call(self, api: str, endpoint: str, status_code: int, duration_ms: float):
        """Log external API calls."""
        return self._write("EXTERNAL_API", "REQUEST", {
            "api": api,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "success": 200 <= status_code < 300
        })
    
    def log_file_operation(self, operation: str, file_path: str, size_bytes: int = None):
        """Log file system operations."""
        return self._write("FILE_SYSTEM", "OPERATION", {
            "operation": operation,
            "file_path": str(file_path),
            "size_bytes": size_bytes,
            "user_context": self._get_user_context()
        })
    
    def log_configuration_change(self, component: str, setting: str, old_value: Any, new_value: Any):
        """Log configuration changes with full audit trail."""
        entry = self._write("CONFIG", "CHANGE", {
            "component": component,
            "setting": setting,
            "old_value": str(old_value)[:500],  # Truncate long values
            "new_value": str(new_value)[:500],
            "user_context": self._get_user_context()
        })
        
        # Also write to dedicated audit log
        self._write_audit_log("CONFIG_CHANGE", {
            "component": component,
            "setting": setting,
            "old_value": old_value,
            "new_value": new_value
        })
        
        return entry
    
    def log_trading_decision_chain(self, decision_id: str, steps: List[Dict[str, Any]]):
        """Log complete decision-making chain for trading decisions."""
        return self._write("TRADING", "DECISION_CHAIN", {
            "decision_id": decision_id,
            "steps": steps,
            "total_steps": len(steps),
            "final_decision": steps[-1] if steps else None
        })
    
    def log_risk_calculation(self, calculation_type: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """Log risk calculations for compliance."""
        return self._write("RISK", "CALCULATION", {
            "calculation_type": calculation_type,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def create_session_snapshot(self) -> str:
        """Create a comprehensive snapshot of current session state."""
        snapshot_id = f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_info": self._get_system_info(),
            "component_states": self._get_component_states(),
            "recent_logs": self._get_recent_logs(50),
            "performance_metrics": self._get_performance_snapshot()
        }
        
        snapshot_file = self._audit_dir / f"{snapshot_id}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        self._write("AUDIT", "SNAPSHOT_CREATED", {"snapshot_id": snapshot_id})
        return snapshot_id
    
    def _get_user_context(self) -> Dict[str, str]:
        """Get current user/execution context."""
        return {
            "process_id": str(os.getpid()),
            "user": os.environ.get("USER", "unknown"),
            "hostname": os.environ.get("HOSTNAME", "unknown")
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            import platform
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            }
        except Exception:
            return {"error": "Could not collect system info"}
    
    def _get_component_states(self) -> Dict[str, str]:
        """Get current state of system components."""
        states = {}
        
        # Shadow collector state
        try:
            states["shadow_collector"] = "running" if shadow_collector._running else "stopped"
        except Exception:
            states["shadow_collector"] = "unknown"
        
        # Knowledge base state
        try:
            kb_health = "healthy" if self.base.exists() else "missing"
            states["knowledge_base"] = kb_health
        except Exception:
            states["knowledge_base"] = "unknown"
            
        return states
    
    def _get_recent_logs(self, count: int) -> List[str]:
        """Get recent log entries."""
        try:
            logs = self.read_log()
            return logs[-count:] if logs else []
        except Exception:
            return ["Error reading recent logs"]
    
    def _get_performance_snapshot(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            return performance_monitor.get_performance_summary()
        except Exception:
            return {"error": "Could not collect performance metrics"}
    
    def _write_audit_log(self, event_type: str, data: Dict[str, Any]):
        """Write to dedicated audit log for compliance."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            audit_file = self._audit_dir / f"audit_{today}.jsonl"
            
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "data": data,
                "user_context": self._get_user_context()
            }
            
            with open(audit_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Global enhanced logger instance  
enhanced_logger = EnhancedSessionLogger()


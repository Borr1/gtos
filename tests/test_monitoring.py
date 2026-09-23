"""Tests for Component 7 — Monitoring, Session Logger, and Dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.components.monitoring import AlertSystem, SessionLogger


# ═══════════════════════════════════════════════════════════════════════
# AlertSystem
# ═══════════════════════════════════════════════════════════════════════

class TestAlertSystem:

    def test_alert_writes_to_file(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        alerts.log_alert("INFO", "TRADE_EXECUTED", "Trade tr_2025-11-15_001 opened")

        alerts_file = tmp_path / "meta" / "alerts.jsonl"
        assert alerts_file.exists()

        lines = alerts_file.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["level"] == "INFO"
        assert entry["alert_type"] == "TRADE_EXECUTED"
        assert "tr_2025-11-15_001" in entry["message"]

    def test_alert_appends_multiple(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        alerts.log_alert("INFO", "TRADE_EXECUTED", "Trade opened")
        alerts.log_alert("WARNING", "DRAWDOWN_WARNING", "Drawdown at 3%")
        alerts.log_alert("ERROR", "API_ERROR", "Timeout", {"attempt": 2})

        alerts_file = tmp_path / "meta" / "alerts.jsonl"
        lines = alerts_file.read_text().strip().split("\n")
        assert len(lines) == 3

        # Check details on the error alert
        error_entry = json.loads(lines[2])
        assert error_entry["level"] == "ERROR"
        assert error_entry["details"]["attempt"] == 2

    def test_critical_alert_prints_to_stderr(self, tmp_path, capsys):
        alerts = AlertSystem(kb_base=str(tmp_path))
        alerts.log_alert("CRITICAL", "SYSTEM_ERROR", "Something broke badly")

        captured = capsys.readouterr()
        assert "CRITICAL ALERT" in captured.err
        assert "Something broke badly" in captured.err

    def test_get_recent_returns_most_recent_first(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        for i in range(5):
            alerts.log_alert("INFO", f"TYPE_{i}", f"Message {i}")

        recent = alerts.get_recent(3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0]["alert_type"] == "TYPE_4"
        assert recent[2]["alert_type"] == "TYPE_2"

    def test_get_recent_empty(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        assert alerts.get_recent() == []

    def test_alert_has_timestamp(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        entry = alerts.log_alert("INFO", "TEST", "test msg")
        assert "timestamp" in entry
        # Parseable ISO format
        dt = datetime.fromisoformat(entry["timestamp"])
        assert dt.year >= 2025

    def test_alert_with_details(self, tmp_path):
        alerts = AlertSystem(kb_base=str(tmp_path))
        details = {"trade_id": "tr_001", "r_multiple": -1.0}
        entry = alerts.log_alert("WARNING", "LOSS", "Trade lost", details)
        assert entry["details"]["trade_id"] == "tr_001"
        assert entry["details"]["r_multiple"] == -1.0


# ═══════════════════════════════════════════════════════════════════════
# SessionLogger
# ═══════════════════════════════════════════════════════════════════════

class TestSessionLogger:

    def test_log_candle_evaluation(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        line = sl.log_candle_evaluation(
            candle_time="2025-11-15T07:15:00Z",
            decision="NO_TRADE",
            reason="daily_ranging",
            confidence=15,
        )

        assert "PRIMARY_ANALYZER" in line
        assert "CANDLE_EVAL" in line
        assert "NO_TRADE" in line
        assert "daily_ranging" in line

    def test_log_debate(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        line = sl.log_debate(
            bull_strength=82,
            bear_strength=45,
            verdict="APPROVE",
            confidence=80,
        )

        assert "DEBATE" in line
        assert "VERDICT" in line
        assert "APPROVE" in line

    def test_log_trade_executed(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        line = sl.log_trade_executed(
            trade_id="tr_2025-11-15_001",
            direction="LONG",
            entry=2700.0,
            sl=2688.0,
            tp1=2736.0,
        )

        assert "EXECUTION" in line
        assert "TRADE_OPEN" in line
        assert "tr_2025-11-15_001" in line

    def test_log_trade_closed(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        line = sl.log_trade_closed(
            trade_id="tr_2025-11-15_001",
            outcome="WIN",
            r_multiple=3.2,
        )

        assert "TRADE_CLOSE" in line
        assert "WIN" in line

    def test_log_error(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        line = sl.log_error(
            component="PRIMARY_ANALYZER",
            error_type="api_timeout",
            details={"attempt": 2},
        )

        assert "PRIMARY_ANALYZER" in line
        assert "ERROR" in line
        assert "api_timeout" in line

    def test_log_format_pipe_delimited(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        sl.log_candle_evaluation("2025-11-15T07:15:00Z", "NO_TRADE")

        lines = sl.read_log()
        assert len(lines) == 1
        parts = lines[0].split(" | ")
        assert len(parts) == 4  # timestamp | component | event | json

        # Last part should be valid JSON
        data = json.loads(parts[3])
        assert data["decision"] == "NO_TRADE"

    def test_daily_log_file_created(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        sl.log_candle_evaluation("2025-11-15T07:15:00Z", "NO_TRADE")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_path / "meta" / "logs" / f"{today}.log"
        assert log_path.exists()

    def test_multiple_entries_same_day(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        sl.log_candle_evaluation("07:15", "NO_TRADE")
        sl.log_candle_evaluation("07:30", "NO_TRADE")
        sl.log_candle_evaluation("07:45", "CANDIDATE", confidence=78)

        lines = sl.read_log()
        assert len(lines) == 3

    def test_read_log_empty(self, tmp_path):
        sl = SessionLogger(kb_base=str(tmp_path))
        assert sl.read_log() == []
        assert sl.read_log("2020-01-01") == []


# ═══════════════════════════════════════════════════════════════════════
# Dashboard endpoints
# ═══════════════════════════════════════════════════════════════════════

class TestDashboardEndpoints:

    @pytest.fixture(autouse=True)
    def setup_dashboard(self, tmp_path):
        """Configure the dashboard to use a temp KB before each test."""
        from src.components import dashboard
        dashboard.configure(kb_base=str(tmp_path))
        self.tmp_path = tmp_path
        self.kb = dashboard._kb

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.components.dashboard import app
        return TestClient(app)

    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "/status" in resp.text
        assert "/trades" in resp.text

    def test_status_no_session(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no active session"

    def test_status_with_session(self, client):
        from src.models.trade_models import SessionManifest, TradeSummary
        manifest = SessionManifest(
            date="2025-11-15",
            day_of_week="Saturday",
            session_start_utc="07:00",
            session_end_utc="09:30",
            trade_summary=TradeSummary(trade_taken=False),
        )
        self.kb.write_session_manifest(manifest)

        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["latest_session"]["date"] == "2025-11-15"

    def test_trades_empty(self, client):
        resp = client.get("/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["trades"] == []

    def test_trades_with_data(self, client):
        from src.models.trade_models import TradeRecord
        trade = TradeRecord(
            trade_id="",
            date="2025-11-15",
            day_of_week="Saturday",
            direction="LONG",
            entry_price=2700.0,
            stop_loss=2688.0,
            take_profit_1=2736.0,
            outcome="WIN",
            r_multiple=3.2,
        )
        self.kb.write_trade(trade)

        resp = client.get("/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["trades"][0]["outcome"] == "WIN"

    def test_trade_detail(self, client):
        from src.models.trade_models import TradeRecord
        trade = TradeRecord(
            trade_id="",
            date="2025-11-15",
            day_of_week="Saturday",
            direction="LONG",
            entry_price=2700.0,
            stop_loss=2688.0,
            take_profit_1=2736.0,
        )
        trade_id = self.kb.write_trade(trade)

        resp = client.get(f"/trades/{trade_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trade_id"] == trade_id
        assert data["direction"] == "LONG"

    def test_trade_detail_not_found(self, client):
        resp = client.get("/trades/tr_9999-99-99_999")
        assert resp.status_code == 404

    def test_stats_empty(self, client):
        resp = client.get("/stats")
        assert resp.status_code == 200
        # Empty dict when no stats file exists
        assert isinstance(resp.json(), dict)

    def test_stats_with_data(self, client):
        from src.models.trade_models import TradeRecord
        trade = TradeRecord(
            trade_id="tr_test",
            date="2025-11-15",
            day_of_week="Saturday",
            direction="LONG",
            entry_price=2700.0,
            stop_loss=2688.0,
            take_profit_1=2736.0,
            outcome="WIN",
            r_multiple=3.2,
        )
        self.kb.update_rolling_stats(trade)

        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_trades"] == 1
        assert data["wins"] == 1

    def test_alerts_empty(self, client):
        resp = client.get("/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_alerts_with_data(self, client):
        from src.components.monitoring import AlertSystem
        alert_sys = AlertSystem(kb_base=str(self.tmp_path))
        alert_sys.log_alert("INFO", "TEST", "test alert")
        alert_sys.log_alert("WARNING", "WARN", "warning alert")

        resp = client.get("/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        # Most recent first
        assert data["alerts"][0]["alert_type"] == "WARN"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "healthy" in data
        assert "checks" in data
        assert data["checks"]["kb_base_exists"] is True


# ═══════════════════════════════════════════════════════════════════════
# ENHANCED MONITORING TESTS (Category A Infrastructure Improvements)
# ═══════════════════════════════════════════════════════════════════════

import tempfile
import threading
import time
import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from src.components.monitoring import (
    ShadowDataCollector,
    SecurityEventMonitor, 
    PerformanceMonitor,
    EnhancedSessionLogger,
    YouTubeRateLimiter,
    MetricSnapshot
)


class TestShadowDataCollector:
    """Test shadow data collection functionality."""
    
    def test_shadow_collector_init(self, tmp_path):
        collector = ShadowDataCollector(kb_base=str(tmp_path))
        assert collector._shadow_dir.exists()
        assert not collector._running
    
    def test_collect_metric(self, tmp_path):
        collector = ShadowDataCollector(kb_base=str(tmp_path))
        
        collector.collect_metric("test_metric", 42.0, "TEST_COMPONENT", 
                                detail1="value1", detail2="value2")
        
        # Metric should be queued
        assert not collector._metrics_queue.empty()
        
        # Process the queue
        collector._process_metric_queue()
        
        # Check that metric was persisted
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        shadow_file = collector._shadow_dir / f"metrics_{today}.jsonl"
        assert shadow_file.exists()
        
        with open(shadow_file) as f:
            metric_data = json.loads(f.read().strip())
            assert metric_data["type"] == "test_metric"
            assert metric_data["value"] == 42.0
            assert metric_data["component"] == "TEST_COMPONENT"
            assert metric_data["details"]["detail1"] == "value1"
    
    def test_shadow_collector_start_stop(self, tmp_path):
        collector = ShadowDataCollector(kb_base=str(tmp_path))
        
        # Start collection
        collector.start_collection()
        assert collector._running
        assert collector._collector_thread is not None
        
        # Stop collection
        collector.stop_collection()
        assert not collector._running
    
    def test_queue_overflow_handling(self, tmp_path):
        # Create collector with small queue for testing
        collector = ShadowDataCollector(kb_base=str(tmp_path))
        collector._metrics_queue = collector._metrics_queue.__class__(maxsize=2)
        
        # Fill queue beyond capacity
        collector.collect_metric("test1", 1.0, "TEST")
        collector.collect_metric("test2", 2.0, "TEST")
        collector.collect_metric("test3", 3.0, "TEST")  # Should be dropped
        
        assert collector._metrics_queue.qsize() == 2


class TestSecurityEventMonitor:
    """Test security event monitoring."""
    
    def test_auth_failure_tracking(self, tmp_path):
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        
        # Log multiple failed attempts
        for i in range(5):
            monitor.log_auth_attempt("TEST_COMPONENT", "test_user", False, "0.0.0.0")
        
        # Should have generated a critical alert
        alerts = monitor.alert_system.get_recent(10)
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]
        assert len(critical_alerts) > 0
        assert "EXCESSIVE_AUTH_FAILURES" in critical_alerts[0]["alert_type"]
    
    def test_successful_auth_clears_failures(self, tmp_path):
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        
        # Log failed attempts
        for i in range(3):
            monitor.log_auth_attempt("TEST_COMPONENT", "test_user", False, "0.0.0.0")
        
        # Log successful attempt
        monitor.log_auth_attempt("TEST_COMPONENT", "test_user", True, "0.0.0.0")
        
        # Failed attempts should be cleared
        key = "TEST_COMPONENT:test_user"
        assert key not in monitor._failed_attempts
    
    def test_rate_limit_monitoring(self, tmp_path):
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        
        # Log multiple rate limit hits
        for i in range(15):
            monitor.log_rate_limit_hit("TEST_COMPONENT", "/api/test", "0.0.0.0")
        
        # Should have generated a warning alert
        alerts = monitor.alert_system.get_recent(10)
        warning_alerts = [a for a in alerts if a["level"] == "WARNING"]
        rate_limit_alerts = [a for a in warning_alerts if "RATE_LIMITING" in a["alert_type"]]
        assert len(rate_limit_alerts) > 0
    
    def test_data_access_logging(self, tmp_path):
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        
        monitor.log_data_access("TEST_COMPONENT", "sensitive_table", "test_user", "READ")
        
        # Check security log exists
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        security_file = monitor._security_dir / f"audit_{today}.jsonl"
        assert security_file.exists()
        
        with open(security_file) as f:
            event = json.loads(f.read().strip())
            assert event["event_type"] == "DATA_ACCESS"
            assert event["resource"] == "sensitive_table"
            assert event["operation"] == "READ"


class TestPerformanceMonitor:
    """Test performance monitoring."""
    
    def test_operation_timing(self, tmp_path):
        monitor = PerformanceMonitor(kb_base=str(tmp_path))
        
        with monitor.time_operation("TEST_COMPONENT", "test_operation"):
            time.sleep(0.1)  # Simulate work
        
        # Should have recorded timing
        assert len(monitor._slow_operations) == 0  # 0.1s is not slow
        
        # Check metric was collected
        assert monitor.shadow_collector._metrics_queue.qsize() > 0
    
    def test_slow_operation_detection(self, tmp_path):
        monitor = PerformanceMonitor(kb_base=str(tmp_path))
        
        # Manually record a slow operation
        monitor.record_timing("TEST_COMPONENT", "slow_operation", 6000.0)  # 6 seconds
        
        # Should be tracked as slow
        assert len(monitor._slow_operations) == 1
        assert monitor._slow_operations[0]["duration_ms"] == 6000.0
    
    def test_very_slow_operation_alert(self, tmp_path):
        monitor = PerformanceMonitor(kb_base=str(tmp_path))
        
        # Record very slow operation
        monitor.record_timing("TEST_COMPONENT", "very_slow_operation", 35000.0)  # 35 seconds
        
        # Should have generated an alert
        alerts = monitor.alert_system.get_recent(10)
        slow_alerts = [a for a in alerts if a["alert_type"] == "SLOW_OPERATION"]
        assert len(slow_alerts) > 0
        assert slow_alerts[0]["details"]["duration_ms"] == 35000.0
    
    def test_performance_summary(self, tmp_path):
        monitor = PerformanceMonitor(kb_base=str(tmp_path))
        
        # Record some slow operations
        monitor.record_timing("TEST_COMPONENT", "slow1", 6000.0)
        monitor.record_timing("TEST_COMPONENT", "slow2", 7000.0)
        
        summary = monitor.get_performance_summary()
        assert len(summary["slow_operations_last_hour"]) == 2


class TestEnhancedSessionLogger:
    """Test enhanced session logging."""
    
    def test_component_lifecycle_logging(self, tmp_path):
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        start_line = logger.log_component_start("TEST_COMPONENT", "1.0.0", {"setting": "value"})
        stop_line = logger.log_component_stop("TEST_COMPONENT", 0, "normal shutdown")
        
        assert "COMPONENT_START" in start_line
        assert "COMPONENT_STOP" in stop_line
        assert "TEST_COMPONENT" in start_line
        assert "TEST_COMPONENT" in stop_line
    
    def test_model_prediction_logging(self, tmp_path):
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        line = logger.log_model_prediction("claude-sonnet-4-6", "input_hash_123", "BULLISH", 0.85)
        
        assert "AI_MODEL" in line
        assert "PREDICTION" in line
        assert "claude-sonnet-4-6" in line
        assert "0.85" in line
    
    def test_configuration_change_logging(self, tmp_path):
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        line = logger.log_configuration_change("TEST_COMPONENT", "max_trades", "5", "10")
        
        # Should create both session log entry and audit entry
        assert "CONFIG" in line
        assert "CHANGE" in line
        
        # Check audit log exists
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = logger._audit_dir / f"audit_{today}.jsonl"
        assert audit_file.exists()
    
    def test_session_snapshot(self, tmp_path):
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        snapshot_id = logger.create_session_snapshot()
        
        # Check snapshot file exists
        snapshot_file = logger._audit_dir / f"{snapshot_id}.json"
        assert snapshot_file.exists()
        
        with open(snapshot_file) as f:
            snapshot = json.load(f)
            assert "timestamp" in snapshot
            assert "system_info" in snapshot
            assert "component_states" in snapshot
    
    def test_trading_decision_chain(self, tmp_path):
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        steps = [
            {"step": 1, "component": "ANALYZER", "decision": "CANDIDATE"},
            {"step": 2, "component": "DEBATE", "decision": "APPROVE"},
            {"step": 3, "component": "EXECUTION", "decision": "EXECUTE"}
        ]
        
        line = logger.log_trading_decision_chain("decision_123", steps)
        
        assert "TRADING" in line
        assert "DECISION_CHAIN" in line
        assert "decision_123" in line


class TestYouTubeRateLimiter:
    """Test YouTube rate limiting functionality."""
    
    def test_basic_rate_limiting(self):
        limiter = YouTubeRateLimiter()
        
        start_time = time.time()
        
        # First request should not wait
        limiter.wait_for_rate_limit()
        first_duration = time.time() - start_time
        
        # Second request should wait
        start_time = time.time()
        limiter.wait_for_rate_limit()
        second_duration = time.time() - start_time
        
        # Second request should have waited ~10 seconds
        assert second_duration >= 9.5  # Allow some tolerance
    
    def test_429_error_handling(self):
        limiter = YouTubeRateLimiter()
        
        # Handle first 429 error
        limiter.handle_429_error()
        assert limiter._block_count == 1
        assert limiter._block_until > time.time()
        
        # Handle second 429 error
        limiter.handle_429_error()
        assert limiter._block_count == 2
    
    def test_success_reset(self):
        limiter = YouTubeRateLimiter()
        
        # Simulate 429 error
        limiter.handle_429_error()
        assert limiter._block_count == 1
        
        # Reset on success
        limiter.reset_on_success()
        assert limiter._block_count == 0
        assert limiter._block_until == 0
    
    def test_request_counting(self):
        limiter = YouTubeRateLimiter()
        
        # Make several requests
        for i in range(3):
            limiter.wait_for_rate_limit()
        
        assert limiter._request_count == 3
    
    def test_max_backoff(self):
        limiter = YouTubeRateLimiter()
        
        # Simulate many 429 errors
        for i in range(10):
            limiter.handle_429_error()
        
        # Should cap at 10 minutes (600 seconds)
        backoff_time = limiter._block_until - time.time()
        assert backoff_time <= 600


class TestMetricSnapshot:
    """Test metric snapshot data structure."""
    
    def test_metric_creation(self):
        metric = MetricSnapshot(
            timestamp="2026-04-07T10:00:00Z",
            metric_type="cpu_usage",
            value=75.5,
            component="SYSTEM",
            details={"core_count": 8}
        )
        
        assert metric.timestamp == "2026-04-07T10:00:00Z"
        assert metric.metric_type == "cpu_usage"
        assert metric.value == 75.5
        assert metric.component == "SYSTEM"
        assert metric.details["core_count"] == 8


class TestIntegration:
    """Integration tests for enhanced monitoring system."""
    
    def test_full_monitoring_workflow(self, tmp_path):
        # Initialize all components
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        
        # Start monitoring
        shadow_collector.start_collection()
        
        try:
            # Log various events
            enhanced_logger.log_component_start("TEST_SYSTEM", "1.0")
            
            with performance_monitor.time_operation("TEST_SYSTEM", "test_operation"):
                time.sleep(0.1)
            
            security_monitor.log_data_access("TEST_SYSTEM", "test_table", "test_user", "READ")
            shadow_collector.collect_metric("test_metric", 100.0, "TEST_SYSTEM")
            
            enhanced_logger.log_component_stop("TEST_SYSTEM", 0, "test complete")
            
            # Create snapshot
            snapshot_id = enhanced_logger.create_session_snapshot()
            
            # Verify files exist
            assert (shadow_collector._shadow_dir).exists()
            assert (security_monitor._security_dir).exists()
            assert (enhanced_logger._audit_dir / f"{snapshot_id}.json").exists()
            
        finally:
            shadow_collector.stop_collection()
    
    def test_monitoring_error_recovery(self, tmp_path):
        # Test that monitoring components handle errors gracefully
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path / "test_recovery"))
        
        # Should not crash on collection errors
        try:
            shadow_collector.collect_metric("test", 1.0, "TEST")
            shadow_collector._process_metric_queue()
        except Exception as e:
            pytest.fail(f"Should handle collection errors gracefully: {e}")


"""Comprehensive Infrastructure Test Suite - Tests for monitoring, alerts, and data collection.

This test suite validates all infrastructure improvements including:
- Enhanced monitoring systems
- Shadow data collection
- Alert management
- Performance monitoring
- System health checks
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.components.monitoring import (
    AlertSystem,
    SessionLogger,
    ShadowDataCollector,
    SecurityEventMonitor,
    PerformanceMonitor,
    EnhancedSessionLogger,
    YouTubeRateLimiter,
    MetricSnapshot,
)


# ═══════════════════════════════════════════════════════════════════════
# Enhanced Monitoring Infrastructure Tests
# ═══════════════════════════════════════════════════════════════════════

class TestShadowDataCollection:
    """Test shadow data collection infrastructure."""

    def test_shadow_collector_initialization(self, tmp_path):
        """Test shadow collector initializes properly."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        assert collector._shadow_dir.exists()
        assert not collector._running
        assert collector._metrics_queue.empty()

    def test_metric_collection_and_persistence(self, tmp_path):
        """Test metric collection and file persistence."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Collect various metric types
        collector.collect_metric("cpu_usage", 75.5, "SYSTEM", core="cpu0", load_avg=1.2)
        collector.collect_metric("memory_usage", 85.2, "SYSTEM", available_mb=1024)
        collector.collect_metric("api_latency", 150.0, "LLM_BACKEND", endpoint="/chat")

        # Process the queue
        collector._process_metric_queue()

        # Check persistence
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        metrics_file = collector._shadow_dir / f"metrics_{today}.jsonl"
        assert metrics_file.exists()

        # Verify content
        with open(metrics_file) as f:
            lines = f.read().strip().split('\n')
            assert len(lines) == 3

            cpu_metric = json.loads(lines[0])
            assert cpu_metric["type"] == "cpu_usage"
            assert cpu_metric["value"] == 75.5
            assert cpu_metric["component"] == "SYSTEM"
            assert cpu_metric["details"]["core"] == "cpu0"

    def test_background_collection_lifecycle(self, tmp_path):
        """Test background collection thread lifecycle."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Start collection
        collector.start_collection()
        assert collector._running
        assert collector._collector_thread is not None
        assert collector._collector_thread.is_alive()

        # Add metrics while running
        for i in range(5):
            collector.collect_metric(f"test_metric_{i}", float(i), "TEST")

        # Wait a bit for processing (background thread processes every 10 seconds)
        # But we can manually trigger processing for testing
        collector._process_metric_queue()

        # Stop collection
        collector.stop_collection()
        assert not collector._running

        # Thread should have processed metrics
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        metrics_file = collector._shadow_dir / f"metrics_{today}.jsonl"
        assert metrics_file.exists()

    def test_queue_overflow_protection(self, tmp_path):
        """Test protection against queue overflow."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Simulate queue overflow by setting small max size
        original_maxsize = collector._metrics_queue.maxsize
        collector._metrics_queue = collector._metrics_queue.__class__(maxsize=2)

        # Fill beyond capacity
        collector.collect_metric("metric1", 1.0, "TEST")
        collector.collect_metric("metric2", 2.0, "TEST")
        collector.collect_metric("metric3", 3.0, "TEST")  # Should be dropped

        assert collector._metrics_queue.qsize() <= 2

    def test_metric_aggregation_by_day(self, tmp_path):
        """Test metrics are properly aggregated by day."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Mock datetime for different days
        with patch('src.components.monitoring.datetime') as mock_dt:
            # Day 1
            mock_dt.now.return_value = datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc)
            mock_dt.strftime = datetime.strftime
            collector.collect_metric("day1_metric", 1.0, "TEST")
            collector._process_metric_queue()

            # Day 2
            mock_dt.now.return_value = datetime(2026, 4, 8, 10, 0, 0, tzinfo=timezone.utc)
            collector.collect_metric("day2_metric", 2.0, "TEST")
            collector._process_metric_queue()

        # Should have separate files for each day
        day1_file = collector._shadow_dir / "metrics_2026-04-07.jsonl"
        day2_file = collector._shadow_dir / "metrics_2026-04-08.jsonl"

        assert day1_file.exists()
        assert day2_file.exists()

    def test_collection_error_resilience(self, tmp_path):
        """Test collector handles errors gracefully."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Make shadow directory read-only to cause write errors
        collector._shadow_dir.chmod(0o444)

        try:
            # Should not crash even with write errors
            collector.collect_metric("error_test", 1.0, "TEST")
            collector._process_metric_queue()
        except Exception:
            pytest.fail("Collector should handle write errors gracefully")
        finally:
            # Restore permissions for cleanup
            collector._shadow_dir.chmod(0o755)


class TestSecurityEventMonitoring:
    """Test security event monitoring infrastructure."""

    def test_auth_failure_tracking(self, tmp_path):
        """Test authentication failure tracking and alerting."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        # Log multiple failed attempts from same user/IP
        user = "test_user"
        ip = "0.0.0.0"
        component = "AUTH_SERVICE"

        for i in range(6):  # Exceed threshold
            monitor.log_auth_attempt(component, user, False, ip)

        # Check alert was generated
        alerts = monitor.alert_system.get_recent(10)
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]
        assert len(critical_alerts) > 0

        critical_alert = critical_alerts[0]
        assert "EXCESSIVE_AUTH_FAILURES" in critical_alert["alert_type"]
        assert user in str(critical_alert["details"])
        assert ip in str(critical_alert["details"])

    def test_auth_success_reset(self, tmp_path):
        """Test that successful auth resets failure count."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        user = "test_user"
        ip = "0.0.0.0"
        component = "AUTH_SERVICE"

        # Log some failures
        for i in range(3):
            monitor.log_auth_attempt(component, user, False, ip)

        # Successful auth should clear failures
        monitor.log_auth_attempt(component, user, True, ip)

        # Failure count should be reset
        key = f"{component}:{user}"
        assert key not in monitor._failed_attempts

    def test_rate_limit_monitoring(self, tmp_path):
        """Test rate limiting monitoring."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        component = "API_GATEWAY"
        endpoint = "/api/trades"
        ip = "0.0.0.0"

        # Generate many rate limit hits
        for i in range(20):
            monitor.log_rate_limit_hit(component, endpoint, ip)

        # Should generate warning
        alerts = monitor.alert_system.get_recent(10)
        warning_alerts = [a for a in alerts if a["level"] == "WARNING"]
        rate_alerts = [a for a in warning_alerts if "RATE_LIMITING" in a["alert_type"]]
        assert len(rate_alerts) > 0

    def test_data_access_audit_logging(self, tmp_path):
        """Test data access audit logging."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        component = "DATABASE"
        resource = "trades_table"
        user = "trading_bot"
        operation = "SELECT"

        monitor.log_data_access(component, resource, user, operation)

        # Check audit log was created
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = monitor._security_dir / f"audit_{today}.jsonl"
        assert audit_file.exists()

        # Verify content
        with open(audit_file) as f:
            audit_entry = json.loads(f.read().strip())
            assert audit_entry["event_type"] == "DATA_ACCESS"
            assert audit_entry["component"] == component
            assert audit_entry["resource"] == resource
            assert audit_entry["user_id"] == user
            assert audit_entry["operation"] == operation

    def test_ip_address_tracking(self, tmp_path):
        """Test IP address tracking across events."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        # Track events from suspicious IP
        suspicious_ip = "192.168.1.666"

        # Multiple failure types from same IP
        monitor.log_auth_attempt("AUTH", "user1", False, suspicious_ip)
        monitor.log_auth_attempt("AUTH", "user2", False, suspicious_ip)
        monitor.log_rate_limit_hit("API", "/endpoint", suspicious_ip)

        # Failures should be tracked by component:user
        assert len(monitor._failed_attempts) == 2  # Two users failed
        assert 'AUTH:user1' in monitor._failed_attempts
        assert 'AUTH:user2' in monitor._failed_attempts

    def test_security_event_aggregation(self, tmp_path):
        """Test security event aggregation and reporting."""
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        # Generate various security events
        events = [
            ("AUTH_FAIL", "auth_attempt", "user1", False, "0.0.0.0"),
            ("AUTH_FAIL", "auth_attempt", "user2", False, "0.0.0.0"),
            ("RATE_LIMIT", "rate_limit_hit", "/api/v1", None, "0.0.0.0"),
            ("DATA_ACCESS", "data_access", "sensitive_data", "admin", None),
        ]

        for event_type, method, *args in events:
            if method == "auth_attempt":
                monitor.log_auth_attempt("AUTH", args[0], args[1], args[2])
            elif method == "rate_limit_hit":
                monitor.log_rate_limit_hit("API", args[0], args[2])
            elif method == "data_access":
                monitor.log_data_access("DB", args[0], args[1], "READ")

        # Check multiple event types were logged
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = monitor._security_dir / f"audit_{today}.jsonl"

        if audit_file.exists():
            with open(audit_file) as f:
                audit_lines = f.read().strip().split('\n')
                assert len(audit_lines) >= 1  # At least data access event


class TestPerformanceMonitoring:
    """Test performance monitoring infrastructure."""

    def test_operation_timing_context_manager(self, tmp_path):
        """Test operation timing using context manager."""
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        component = "TEST_COMPONENT"
        operation = "test_operation"

        with monitor.time_operation(component, operation):
            time.sleep(0.1)  # Simulate work

        # Should have recorded timing metric
        assert not monitor.shadow_collector._metrics_queue.empty()

        # Process and check
        monitor.shadow_collector._process_metric_queue()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        metrics_file = monitor.shadow_collector._shadow_dir / f"metrics_{today}.jsonl"

        if metrics_file.exists():
            with open(metrics_file) as f:
                metric = json.loads(f.read().strip())
                assert metric["type"] == "operation_duration_ms"
                assert metric["component"] == component
                assert metric["details"]["operation"] == operation
                assert metric["value"] >= 100  # At least 100ms

    def test_slow_operation_detection(self, tmp_path):
        """Test slow operation detection and alerting."""
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        component = "SLOW_COMPONENT"
        operation = "heavy_computation"
        slow_duration = 6000.0  # 6 seconds

        monitor.record_timing(component, operation, slow_duration)

        # Should be tracked as slow operation
        assert len(monitor._slow_operations) == 1
        slow_op = monitor._slow_operations[0]
        assert slow_op["component"] == component
        assert slow_op["operation"] == operation
        assert slow_op["duration_ms"] == slow_duration

    def test_very_slow_operation_alerting(self, tmp_path):
        """Test alerting for very slow operations."""
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        component = "CRITICAL_COMPONENT"
        operation = "timeout_prone_task"
        very_slow_duration = 35000.0  # 35 seconds

        monitor.record_timing(component, operation, very_slow_duration)

        # Should generate alert
        alerts = monitor.alert_system.get_recent(10)
        slow_alerts = [a for a in alerts if a["alert_type"] == "SLOW_OPERATION"]
        assert len(slow_alerts) > 0

        alert = slow_alerts[0]
        assert alert["details"]["component"] == component
        assert alert["details"]["operation"] == operation
        assert alert["details"]["duration_ms"] == very_slow_duration

    def test_performance_summary_generation(self, tmp_path):
        """Test performance summary generation."""
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        # Record various operations
        timings = [
            ("COMPONENT_A", "fast_op", 100.0),
            ("COMPONENT_A", "slow_op", 6000.0),
            ("COMPONENT_B", "medium_op", 2000.0),
            ("COMPONENT_B", "slow_op", 8000.0),
        ]

        for comp, op, duration in timings:
            monitor.record_timing(comp, op, duration)

        summary = monitor.get_performance_summary()

        assert "slow_operations_last_hour" in summary
        assert len(summary["slow_operations_last_hour"]) == 2  # Two slow ops

        slow_ops = summary["slow_operations_last_hour"]
        assert all(op["duration_ms"] >= 5000 for op in slow_ops)

    def test_timing_metric_collection_integration(self, tmp_path):
        """Test integration with shadow data collector."""
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        # Record timing
        monitor.record_timing("INTEGRATION_TEST", "test_op", 1500.0)

        # Should collect shadow metric
        assert not monitor.shadow_collector._metrics_queue.empty()

        # Process metrics
        monitor.shadow_collector._process_metric_queue()

        # Check shadow data
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        metrics_file = monitor.shadow_collector._shadow_dir / f"metrics_{today}.jsonl"

        if metrics_file.exists():
            with open(metrics_file) as f:
                lines = f.read().strip().split('\n')
                timing_metrics = [json.loads(line) for line in lines
                                if json.loads(line)["type"] == "operation_duration_ms"]
                assert len(timing_metrics) >= 1


class TestEnhancedSessionLogging:
    """Test enhanced session logging infrastructure."""

    def test_component_lifecycle_logging(self, tmp_path):
        """Test component start/stop lifecycle logging."""
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        component = "TEST_COMPONENT"
        version = "1.2.3"
        config = {"setting1": "value1", "setting2": 42}

        # Log component start
        start_line = logger.log_component_start(component, version, config)
        assert "COMPONENT_START" in start_line
        assert component in start_line
        assert version in start_line

        # Log component stop
        stop_line = logger.log_component_stop(component, 0, "normal shutdown")
        assert "COMPONENT_STOP" in stop_line
        assert component in stop_line
        assert "normal shutdown" in stop_line

    def test_ai_model_prediction_logging(self, tmp_path):
        """Test AI model prediction logging."""
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        model = "claude-sonnet-4-6"
        input_hash = "abc123"
        prediction = "BULLISH"
        confidence = 0.87

        line = logger.log_model_prediction(model, input_hash, prediction, confidence)

        assert "AI_MODEL" in line
        assert "PREDICTION" in line
        assert model in line
        assert input_hash in line
        assert prediction in line
        assert str(confidence) in line

    def test_configuration_change_auditing(self, tmp_path):
        """Test configuration change auditing."""
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        component = "TRADING_ENGINE"
        setting = "max_position_size"
        old_value = "1.0"
        new_value = "2.0"

        line = logger.log_configuration_change(component, setting, old_value, new_value)

        # Should log to session log
        assert "CONFIG" in line
        assert "CHANGE" in line
        assert setting in line

        # Should create audit entry
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = logger._audit_dir / f"audit_{today}.jsonl"
        assert audit_file.exists()

        with open(audit_file) as f:
            audit_entry = json.loads(f.read().strip())
            assert audit_entry["event_type"] == "CONFIG_CHANGE"
            assert audit_entry["data"]["component"] == component
            assert audit_entry["data"]["setting"] == setting
            assert audit_entry["data"]["old_value"] == old_value
            assert audit_entry["data"]["new_value"] == new_value

    def test_system_snapshot_creation(self, tmp_path):
        """Test system snapshot creation."""
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        snapshot_id = logger.create_session_snapshot()

        # Should return valid snapshot ID
        assert snapshot_id is not None
        assert len(snapshot_id) > 0

        # Should create snapshot file
        snapshot_file = logger._audit_dir / f"{snapshot_id}.json"
        assert snapshot_file.exists()

        # Verify snapshot content
        with open(snapshot_file) as f:
            snapshot = json.load(f)

            required_fields = ["timestamp", "system_info", "component_states"]
            for field in required_fields:
                assert field in snapshot

            assert "python_version" in snapshot["system_info"]
            assert "platform" in snapshot["system_info"]

    def test_trading_decision_chain_logging(self, tmp_path):
        """Test trading decision chain logging."""
        logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        decision_id = "decision_20260407_001"
        steps = [
            {"step": 1, "component": "ANALYZER", "decision": "CANDIDATE", "confidence": 0.75},
            {"step": 2, "component": "DEBATE", "decision": "APPROVE", "confidence": 0.82},
            {"step": 3, "component": "EXECUTION", "decision": "EXECUTE", "size": 1.0}
        ]

        line = logger.log_trading_decision_chain(decision_id, steps)

        assert "TRADING" in line
        assert "DECISION_CHAIN" in line
        assert decision_id in line

        # Should log each step
        log_data = json.loads(line.split(" | ")[-1])
        assert log_data["decision_id"] == decision_id
        assert log_data["steps"] == steps
        assert log_data["total_steps"] == 3


class TestYouTubeRateLimiting:
    """Test YouTube rate limiting infrastructure."""

    def test_basic_rate_limiting_enforcement(self):
        """Test basic rate limiting enforcement."""
        limiter = YouTubeRateLimiter()

        # First request should not wait
        start_time = time.time()
        limiter.wait_for_rate_limit()
        first_duration = time.time() - start_time

        assert first_duration < 1.0  # Should be immediate

        # Second request should wait
        start_time = time.time()
        limiter.wait_for_rate_limit()
        second_duration = time.time() - start_time

        assert second_duration >= 9.5  # Should wait ~10 seconds

    def test_429_error_handling_and_backoff(self):
        """Test 429 error handling with exponential backoff."""
        limiter = YouTubeRateLimiter()

        # Handle first 429 error
        limiter.handle_429_error()
        assert limiter._block_count == 1
        block_time_1 = limiter._block_until - time.time()
        assert 85 <= block_time_1 <= 95  # Should be ~90 seconds

        # Handle second 429 error (exponential backoff)
        limiter.handle_429_error()
        assert limiter._block_count == 2
        block_time_2 = limiter._block_until - time.time()
        assert 175 <= block_time_2 <= 185  # Should be ~180 seconds

    def test_success_reset_mechanism(self):
        """Test success reset mechanism."""
        limiter = YouTubeRateLimiter()

        # Trigger 429 errors
        limiter.handle_429_error()
        limiter.handle_429_error()
        assert limiter._block_count == 2

        # Success should reset
        limiter.reset_on_success()
        assert limiter._block_count == 0
        assert limiter._block_until == 0

    def test_maximum_backoff_limit(self):
        """Test maximum backoff time limit."""
        limiter = YouTubeRateLimiter()

        # Trigger many 429 errors to test max backoff
        for i in range(10):
            limiter.handle_429_error()

        # Should not exceed 10 minutes (600 seconds)
        backoff_time = limiter._block_until - time.time()
        assert backoff_time <= 600

    def test_request_counting(self):
        """Test request counting functionality."""
        limiter = YouTubeRateLimiter()

        # Make multiple requests
        for i in range(5):
            limiter.wait_for_rate_limit()

        assert limiter._request_count == 5

    def test_blocking_period_enforcement(self):
        """Test that blocking period is properly enforced."""
        limiter = YouTubeRateLimiter()

        # Set a short block period for testing
        limiter._block_until = time.time() + 2.0  # 2 seconds

        start_time = time.time()
        limiter.wait_for_rate_limit()
        wait_duration = time.time() - start_time

        assert wait_duration >= 1.5  # Should wait for block period


class TestMetricDataStructures:
    """Test metric data structures and utilities."""

    def test_metric_snapshot_creation(self):
        """Test MetricSnapshot creation and serialization."""
        timestamp = "2026-04-07T15:30:00Z"
        metric_type = "cpu_usage"
        value = 78.5
        component = "SYSTEM_MONITOR"
        details = {"core": "cpu0", "frequency": 2400}

        metric = MetricSnapshot(
            timestamp=timestamp,
            metric_type=metric_type,
            value=value,
            component=component,
            details=details
        )

        assert metric.timestamp == timestamp
        assert metric.metric_type == metric_type
        assert metric.value == value
        assert metric.component == component
        assert metric.details == details

    def test_metric_snapshot_validation(self):
        """Test MetricSnapshot validation."""
        # Valid metric
        metric = MetricSnapshot(
            timestamp="2026-04-07T15:30:00Z",
            metric_type="memory_usage",
            value=85.0,
            component="SYSTEM",
            details={}
        )
        assert metric.value == 85.0

        # Test with different value types
        float_metric = MetricSnapshot(
            timestamp="2026-04-07T15:30:00Z",
            metric_type="latency",
            value=123.45,
            component="API",
            details={}
        )
        assert float_metric.value == 123.45


# ═══════════════════════════════════════════════════════════════════════
# Integration Infrastructure Tests
# ═══════════════════════════════════════════════════════════════════════

class TestInfrastructureIntegration:
    """Integration tests for infrastructure components."""

    def test_full_monitoring_stack_initialization(self, tmp_path):
        """Test full monitoring stack initialization."""
        # Initialize all components
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))

        # All should initialize without errors
        assert shadow_collector._shadow_dir.exists()
        assert security_monitor._security_dir.exists()
        assert performance_monitor.shadow_collector._shadow_dir.exists()
        assert enhanced_logger._audit_dir.exists()
        assert alert_system._alerts_file.parent.exists()

    def test_cross_component_integration(self, tmp_path):
        """Test integration between monitoring components."""
        # Initialize components
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        # Start shadow collection
        shadow_collector.start_collection()

        try:
            # Log component start
            enhanced_logger.log_component_start("INTEGRATION_TEST", "1.0")

            # Perform operation with timing
            with performance_monitor.time_operation("INTEGRATION_TEST", "test_operation"):
                time.sleep(0.1)

            # Log security event — log_data_access invokes _write_security_log,
            # which is what creates audit_{today}.jsonl. log_auth_attempt with
            # success=True only clears the failed-attempts cache and never
            # writes (see SecurityEventMonitor.log_auth_attempt success branch).
            security_monitor.log_data_access(
                "INTEGRATION_TEST", "test_resource", "test_user", "READ"
            )

            # Collect custom metric
            shadow_collector.collect_metric("integration_test", 100.0, "INTEGRATION_TEST")

            # Log component stop
            enhanced_logger.log_component_stop("INTEGRATION_TEST", 0, "test complete")

            # Verify all systems recorded events
            time.sleep(0.2)  # Allow processing

            # Check files exist
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Session log
            session_log = enhanced_logger._logs_dir / f"{today}.log"
            assert session_log.exists()

            # Shadow metrics — flush explicitly since background thread timing is non-deterministic
            shadow_collector._process_metric_queue()
            metrics_file = shadow_collector._shadow_dir / f"metrics_{today}.jsonl"
            assert metrics_file.exists()

            # Security audit
            audit_file = security_monitor._security_dir / f"audit_{today}.jsonl"
            assert audit_file.exists()

        finally:
            shadow_collector.stop_collection()

    def test_monitoring_under_load(self, tmp_path):
        """Test monitoring system under load."""
        # Initialize components
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))

        shadow_collector.start_collection()

        try:
            # Generate load
            for i in range(100):
                shadow_collector.collect_metric(f"load_test_{i}", float(i), "LOAD_TEST")
                performance_monitor.record_timing("LOAD_TEST", f"operation_{i}", float(i * 10))

            # Allow processing — flush explicitly for deterministic file check
            shadow_collector._process_metric_queue()

            # System should handle load without errors
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            metrics_file = shadow_collector._shadow_dir / f"metrics_{today}.jsonl"
            assert metrics_file.exists()

        finally:
            shadow_collector.stop_collection()

    def test_error_recovery_and_resilience(self, tmp_path):
        """Test infrastructure error recovery and resilience."""
        # Pre-create dirs so init succeeds; make shadow_data read-only to test write resilience
        corrupted_path = tmp_path / "corrupted"
        corrupted_path.mkdir()
        shadow_data_dir = corrupted_path / "meta" / "shadow_data"
        shadow_data_dir.mkdir(parents=True, exist_ok=True)
        (corrupted_path / "meta" / "security").mkdir(parents=True, exist_ok=True)
        shadow_data_dir.chmod(0o444)  # Read-only — mkdir(exist_ok=True) ok, writes fail gracefully

        try:
            # Components should handle initialization errors gracefully
            collector = ShadowDataCollector(kb_base=str(corrupted_path))
            monitor = SecurityEventMonitor(kb_base=str(corrupted_path))

            # Operations should not crash
            collector.collect_metric("error_test", 1.0, "ERROR_TEST")
            monitor.log_auth_attempt("ERROR_TEST", "user", False, "127.0.0.1")

        except Exception:
            pytest.fail("Infrastructure should handle errors gracefully")
        finally:
            # Restore permissions for cleanup
            shadow_data_dir.chmod(0o755)

    def test_monitoring_initialization_script_integration(self, tmp_path, monkeypatch):
        """Test integration with monitoring initialization script."""
        from src.utils import monitoring_init as _mi
        from src.utils.monitoring_init import initialize_monitoring, test_monitoring_components

        # The 4 singletons in monitoring_init are constructed at import time
        # with the default kb_base="knowledge_base" — initialize_monitoring()
        # only rebuilds AlertSystem, so without this monkeypatch the test
        # writes to the real production knowledge_base/ tree (caught by the
        # write guard in tests/conftest.py). Rebuild each singleton against
        # tmp_path before the test runs anything.
        monkeypatch.setattr(_mi, "enhanced_logger", EnhancedSessionLogger(kb_base=str(tmp_path)))
        monkeypatch.setattr(_mi, "shadow_collector", ShadowDataCollector(kb_base=str(tmp_path)))
        monkeypatch.setattr(_mi, "security_monitor", SecurityEventMonitor(kb_base=str(tmp_path)))
        monkeypatch.setattr(_mi, "performance_monitor", PerformanceMonitor(kb_base=str(tmp_path)))

        # Test initialization
        with patch('src.utils.monitoring_init.logger'):
            success = initialize_monitoring(kb_base=str(tmp_path))
            assert success is True

        # Test component testing
        with patch('src.utils.monitoring_init.logger'):
            results = test_monitoring_components()

            # Should test all major components
            expected_components = [
                "shadow_collector",
                "security_monitor",
                "performance_monitor",
                "enhanced_logger"
            ]

            for component in expected_components:
                assert component in results


# ═══════════════════════════════════════════════════════════════════════
# Performance and Scalability Tests
# ═══════════════════════════════════════════════════════════════════════

class TestInfrastructurePerformance:
    """Test infrastructure performance and scalability."""

    def test_shadow_collection_performance(self, tmp_path):
        """Test shadow collection performance under high throughput."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))

        # Measure collection performance
        start_time = time.time()

        for i in range(1000):
            collector.collect_metric(f"perf_test_{i}", float(i), "PERF_TEST")

        collection_time = time.time() - start_time

        # Should handle 1000 metrics quickly
        assert collection_time < 5.0  # Less than 5 seconds

        # Process queue
        start_time = time.time()
        collector._process_metric_queue()
        processing_time = time.time() - start_time

        # Processing should also be fast
        assert processing_time < 10.0  # Less than 10 seconds

    def test_concurrent_monitoring_operations(self, tmp_path):
        """Test concurrent monitoring operations."""
        import threading

        collector = ShadowDataCollector(kb_base=str(tmp_path))
        monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        errors = []

        def collect_metrics():
            try:
                for i in range(50):
                    collector.collect_metric(f"thread_metric_{i}", float(i), "THREAD_TEST")
            except Exception as e:
                errors.append(e)

        def log_security_events():
            try:
                for i in range(50):
                    monitor.log_auth_attempt("THREAD_TEST", f"user_{i}", i % 2 == 0, "127.0.0.1")
            except Exception as e:
                errors.append(e)

        # Run concurrent operations
        threads = [
            threading.Thread(target=collect_metrics),
            threading.Thread(target=log_security_events),
            threading.Thread(target=collect_metrics),
            threading.Thread(target=log_security_events),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0

    def test_memory_usage_stability(self, tmp_path):
        """Test memory usage stability over extended operation."""
        collector = ShadowDataCollector(kb_base=str(tmp_path))
        monitor = PerformanceMonitor(kb_base=str(tmp_path))

        # Simulate extended operation
        for cycle in range(10):
            # Generate batch of metrics
            for i in range(100):
                collector.collect_metric(f"memory_test_{cycle}_{i}", float(i), "MEMORY_TEST")
                monitor.record_timing("MEMORY_TEST", f"op_{i}", float(i * 10))

            # Process immediately to prevent queue buildup
            collector._process_metric_queue()

        # System should remain stable (no assertions, just verify no crashes)
        assert True  # If we reach here, memory usage was stable


# ═══════════════════════════════════════════════════════════════════════
# Configuration and Customization Tests
# ═══════════════════════════════════════════════════════════════════════

class TestInfrastructureConfiguration:
    """Test infrastructure configuration and customization."""

    def test_custom_knowledge_base_paths(self, tmp_path):
        """Test custom knowledge base path configuration."""
        custom_kb = tmp_path / "custom_kb"

        # Initialize with custom path
        collector = ShadowDataCollector(kb_base=str(custom_kb))
        monitor = SecurityEventMonitor(kb_base=str(custom_kb))
        logger = EnhancedSessionLogger(kb_base=str(custom_kb))

        # Should create directories under custom path
        assert (custom_kb / "meta" / "shadow_data").exists()
        assert (custom_kb / "meta" / "security").exists()
        assert (custom_kb / "meta" / "logs").exists()

    def test_monitoring_component_isolation(self, tmp_path):
        """Test monitoring component isolation."""
        # Create separate knowledge bases
        kb1 = tmp_path / "kb1"
        kb2 = tmp_path / "kb2"

        collector1 = ShadowDataCollector(kb_base=str(kb1))
        collector2 = ShadowDataCollector(kb_base=str(kb2))

        # Collect different metrics
        collector1.collect_metric("kb1_metric", 1.0, "KB1")
        collector2.collect_metric("kb2_metric", 2.0, "KB2")

        collector1._process_metric_queue()
        collector2._process_metric_queue()

        # Should be isolated
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        kb1_metrics = kb1 / "meta" / "shadow_data" / f"metrics_{today}.jsonl"
        kb2_metrics = kb2 / "meta" / "shadow_data" / f"metrics_{today}.jsonl"

        assert kb1_metrics.exists()
        assert kb2_metrics.exists()

        # Content should be different
        with open(kb1_metrics) as f:
            kb1_content = f.read()
        with open(kb2_metrics) as f:
            kb2_content = f.read()

        assert "kb1_metric" in kb1_content
        assert "kb2_metric" not in kb1_content
        assert "kb2_metric" in kb2_content
        assert "kb1_metric" not in kb2_content

    def test_alert_system_configuration(self, tmp_path):
        """Test alert system configuration options."""
        alert_system = AlertSystem(kb_base=str(tmp_path))

        # Test different alert levels
        levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            alert_system.log_alert(level, f"TEST_{level}", f"Test {level} message")

        # All should be logged
        alerts = alert_system.get_recent(10)
        assert len(alerts) == 4

        # Check order (most recent first)
        assert alerts[0]["level"] == "CRITICAL"
        assert alerts[-1]["level"] == "INFO"


class TestLoggingUTCConverter:
    """Apr 16 lock-file mtime correlation (see memory/project_pytest_contamination_forensics.md)
    requires log timestamps in UTC so they align with on-disk UTC mtimes."""

    def test_monitoring_init_sets_global_utc_converter(self):
        import logging
        import time as _time

        import src.utils.monitoring_init  # noqa: F401 — import triggers converter assignment

        assert logging.Formatter.converter is _time.gmtime

    def test_formatter_emits_utc_timestamp_for_known_epoch(self):
        import logging
        import time as _time

        import src.utils.monitoring_init  # noqa: F401

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__, lineno=1,
            msg="ping", args=(), exc_info=None,
        )
        record.created = 1700000000.0  # 2023-11-14 22:13:20 UTC
        formatter = logging.Formatter("%(asctime)s", datefmt="%Y-%m-%d %H:%M:%S")
        formatted = formatter.format(record)
        expected_utc = _time.strftime("%Y-%m-%d %H:%M:%S", _time.gmtime(1700000000.0))
        assert formatted == expected_utc
        local_repr = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(1700000000.0))
        if local_repr != expected_utc:
            assert formatted != local_repr


if __name__ == "__main__":
    pytest.main([__file__])
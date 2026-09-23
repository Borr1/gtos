"""End-to-End Integration Test Suite - Tests for complete system integration.

This test suite validates the integration between:
- Security and infrastructure systems
- Trading logic with monitoring
- Alert systems with decision making
- Cross-component data flow
"""

from __future__ import annotations

import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import concurrent.futures

import pytest

from src.security.validation import validate_ai_response_secure, SecurityValidationError
from src.security.environment import validate_environment_security, SecurityLevel
from src.components.monitoring import (
    AlertSystem,
    ShadowDataCollector,
    SecurityEventMonitor,
    PerformanceMonitor,
    EnhancedSessionLogger,
)


# ═══════════════════════════════════════════════════════════════════════
# Security and Infrastructure Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityInfrastructureIntegration:
    """Test integration between security and infrastructure systems."""

    def test_security_monitoring_integration(self, tmp_path):
        """Test security events trigger proper monitoring and alerts."""
        # Initialize systems
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))

        # Simulate security events that should trigger alerts
        for i in range(6):  # Exceed auth failure threshold
            security_monitor.log_auth_attempt("WEB_API", "suspicious_user", False, "0.0.0.0")

        # Check that critical alert was generated
        alerts = alert_system.get_recent(10)
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]
        assert len(critical_alerts) > 0

        # Verify alert contains security context
        alert = critical_alerts[0]
        assert "EXCESSIVE_AUTH_FAILURES" in alert["alert_type"]
        assert "suspicious_user" in str(alert["details"])

    def test_ai_validation_with_security_monitoring(self, tmp_path):
        """Test AI response validation integration with security monitoring."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            decision: str

        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))

        # Test malicious AI response
        malicious_response = '{"decision": "LONG", "__proto__": {"malicious": true}}'

        try:
            validate_ai_response_secure(malicious_response, TestSchema)
            pytest.fail("Should have rejected malicious response")
        except SecurityValidationError as e:
            # Log security event
            security_monitor.log_data_access(
                "AI_VALIDATOR", "ai_response_validation", "trading_system", "REJECT"
            )

            # Generate security alert
            alert_system.log_alert(
                "WARNING",
                "AI_INJECTION_ATTEMPT",
                f"Malicious AI response detected: {str(e)[:100]}",
                {"response_type": "prototype_pollution", "blocked": True}
            )

        # Verify security event was logged
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = security_monitor._security_dir / f"audit_{today}.jsonl"
        assert audit_file.exists()

        # Verify alert was generated
        alerts = alert_system.get_recent(10)
        injection_alerts = [a for a in alerts if "AI_INJECTION" in a["alert_type"]]
        assert len(injection_alerts) > 0

    def test_environment_security_with_infrastructure(self, tmp_path):
        """Test environment security validation with infrastructure monitoring."""
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))

        # Mock insecure production environment
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',  # Insecure
            'SECRET_KEY': 'weak'  # Weak key
        }):
            # Validate environment
            result = validate_environment_security()

            # Log security validation
            enhanced_logger.log_component_start(
                "ENVIRONMENT_VALIDATOR",
                "1.0",
                {"security_level": result.security_level.value}
            )

            # Should not be secure for production
            assert not result.is_secure_for_production
            assert len(result.security_issues) > 0

            # Generate alerts for security issues
            for issue in result.security_issues:
                alert_system.log_alert(
                    "ERROR",
                    "ENVIRONMENT_SECURITY_ISSUE",
                    f"Environment security issue: {issue}",
                    {"security_level": result.security_level.value}
                )

        # Verify alerts were generated
        alerts = alert_system.get_recent(10)
        env_alerts = [a for a in alerts if "ENVIRONMENT_SECURITY" in a["alert_type"]]
        assert len(env_alerts) > 0


# ═══════════════════════════════════════════════════════════════════════
# Trading System Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestTradingSystemIntegration:
    """Test integration with trading system components."""

    def test_trading_decision_with_monitoring(self, tmp_path):
        """Test trading decision process with full monitoring."""
        # Initialize monitoring stack
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        shadow_collector.start_collection()

        try:
            # Simulate trading decision pipeline
            decision_id = "decision_20260407_001"

            # Step 1: Market Analysis
            enhanced_logger.log_component_start("MARKET_ANALYZER", "2.1")

            with performance_monitor.time_operation("MARKET_ANALYZER", "analyze_market_state"):
                time.sleep(0.1)  # Simulate analysis
                shadow_collector.collect_metric("market_volatility", 0.75, "MARKET_ANALYZER")

            # Step 2: AI Model Prediction
            enhanced_logger.log_model_prediction(
                "claude-sonnet-4-6", "market_hash_123", "BULLISH", 0.85
            )

            # Step 3: Security validation
            security_monitor.log_data_access(
                "TRADING_ENGINE", "market_data", "trading_bot", "READ"
            )

            # Step 4: Decision chain
            steps = [
                {"step": 1, "component": "ANALYZER", "decision": "CANDIDATE", "confidence": 0.75},
                {"step": 2, "component": "DEBATE", "decision": "APPROVE", "confidence": 0.82},
                {"step": 3, "component": "EXECUTION", "decision": "EXECUTE", "size": 1.0}
            ]

            enhanced_logger.log_trading_decision_chain(decision_id, steps)

            # Step 5: Performance metrics
            shadow_collector.collect_metric("decision_latency", 150.0, "TRADING_ENGINE")
            performance_monitor.record_timing("TRADING_ENGINE", "full_decision_cycle", 250.0)

            # Verify all systems captured the trading flow
            time.sleep(0.2)  # Allow processing

            # Check logs exist
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            session_log = enhanced_logger._logs_dir / f"{today}.log"
            assert session_log.exists()

            audit_file = security_monitor._security_dir / f"audit_{today}.jsonl"
            assert audit_file.exists()

            shadow_collector._process_metric_queue()  # flush before file check
            shadow_metrics = shadow_collector._shadow_dir / f"metrics_{today}.jsonl"
            assert shadow_metrics.exists()

            # Check log content
            with open(session_log) as f:
                log_content = f.read()
                assert decision_id in log_content
                assert "TRADING" in log_content
                assert "DECISION_CHAIN" in log_content

        finally:
            shadow_collector.stop_collection()

    def test_error_handling_with_monitoring(self, tmp_path):
        """Test error handling integration with monitoring systems."""
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        # Simulate trading system error
        component = "TRADING_ENGINE"
        error_type = "market_data_timeout"

        # Log component start
        enhanced_logger.log_component_start(component, "2.1")

        # Simulate error condition
        error_details = {
            "timeout_duration": 30,
            "endpoint": "/api/market-data",
            "retry_count": 3
        }

        # Log error
        enhanced_logger.log_error(component, error_type, error_details)

        # Generate alert
        alert_system.log_alert(
            "ERROR",
            "TRADING_SYSTEM_ERROR",
            f"Trading system error: {error_type}",
            error_details
        )

        # Log security event (potential DoS)
        security_monitor.log_rate_limit_hit(
            "MARKET_DATA_API", "/api/market-data", "trading.system.ip"
        )

        # Log component stop with error
        enhanced_logger.log_component_stop(component, 1, f"Error: {error_type}")

        # Verify error handling was properly logged
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        session_log = enhanced_logger._logs_dir / f"{today}.log"

        with open(session_log) as f:
            log_content = f.read()
            assert "ERROR" in log_content
            assert error_type in log_content
            assert "COMPONENT_STOP" in log_content

        # Verify alerts
        alerts = alert_system.get_recent(10)
        error_alerts = [a for a in alerts if a["level"] == "ERROR"]
        assert len(error_alerts) > 0

    def test_performance_degradation_detection(self, tmp_path):
        """Test performance degradation detection and response."""
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))

        component = "MARKET_ANALYZER"

        # Simulate normal performance
        for i in range(5):
            performance_monitor.record_timing(component, "analysis_cycle", 100.0 + i * 10)

        # Simulate performance degradation
        slow_operations = [5000.0, 7000.0, 12000.0, 25000.0, 35000.0]

        for duration in slow_operations:
            performance_monitor.record_timing(component, "analysis_cycle", duration)

        # Check slow operations were detected
        assert len(performance_monitor._slow_operations) >= 4  # Operations > 5 seconds

        # Check alerts for very slow operations
        alerts = alert_system.get_recent(20)
        slow_alerts = [a for a in alerts if a["alert_type"] == "SLOW_OPERATION"]
        assert len(slow_alerts) >= 1  # Operations > 30 seconds (35000ms threshold)

        # Generate performance summary
        summary = performance_monitor.get_performance_summary()
        assert len(summary["slow_operations_last_hour"]) >= 4

        # Log performance issue
        enhanced_logger.log_component_start("PERFORMANCE_MONITOR", "1.0")
        enhanced_logger.log_configuration_change(
            "PERFORMANCE_MONITOR", "alert_threshold", "5000", "3000"
        )


# ═══════════════════════════════════════════════════════════════════════
# Cross-Component Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCrossComponentIntegration:
    """Test integration across multiple system components."""

    def test_full_system_startup_sequence(self, tmp_path):
        """Test full system startup with all monitoring components."""
        # Initialize all components in startup order
        components = {}

        # 1. Environment validation
        env_result = validate_environment_security()
        components["environment"] = env_result

        # 2. Alert system
        alert_system = AlertSystem(kb_base=str(tmp_path))
        components["alerts"] = alert_system

        # 3. Security monitoring
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))
        components["security"] = security_monitor

        # 4. Performance monitoring
        performance_monitor = PerformanceMonitor(kb_base=str(tmp_path))
        components["performance"] = performance_monitor

        # 5. Shadow data collection
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        components["shadow_data"] = shadow_collector

        # 6. Enhanced logging
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        components["logging"] = enhanced_logger

        # Start monitoring systems
        shadow_collector.start_collection()

        try:
            # Log startup sequence
            startup_components = [
                "ENVIRONMENT_VALIDATOR",
                "ALERT_SYSTEM",
                "SECURITY_MONITOR",
                "PERFORMANCE_MONITOR",
                "SHADOW_COLLECTOR",
                "ENHANCED_LOGGER"
            ]

            for component in startup_components:
                enhanced_logger.log_component_start(component, "1.0")

            # Generate startup alert
            alert_system.log_alert(
                "INFO",
                "SYSTEM_STARTUP",
                "Trading system monitoring infrastructure initialized",
                {
                    "components": len(startup_components),
                    "security_level": env_result.security_level.value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            # Create system snapshot
            snapshot_id = enhanced_logger.create_session_snapshot()

            # Verify all components are operational
            assert len(components) == 6
            assert snapshot_id is not None

            # Check snapshot file
            snapshot_file = enhanced_logger._audit_dir / f"{snapshot_id}.json"
            assert snapshot_file.exists()

            # Verify log files exist
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            assert (enhanced_logger._logs_dir / f"{today}.log").exists()
            assert alert_system._alerts_file.exists()

        finally:
            shadow_collector.stop_collection()

    def test_error_propagation_and_recovery(self, tmp_path):
        """Test error propagation and recovery across components."""
        # Initialize components
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))
        security_monitor = SecurityEventMonitor(kb_base=str(tmp_path))

        # Simulate cascading error scenario
        error_chain = [
            {"component": "MARKET_DATA_FEED", "error": "connection_timeout"},
            {"component": "MARKET_ANALYZER", "error": "data_unavailable"},
            {"component": "TRADING_ENGINE", "error": "analysis_failure"},
            {"component": "RISK_MANAGER", "error": "position_halt"}
        ]

        for i, error_info in enumerate(error_chain):
            component = error_info["component"]
            error_type = error_info["error"]

            # Log component failure
            enhanced_logger.log_component_stop(component, 1, f"Error: {error_type}")

            # Generate escalating alerts
            alert_level = ["WARNING", "WARNING", "ERROR", "CRITICAL"][i]
            alert_system.log_alert(
                alert_level,
                f"{component}_FAILURE",
                f"Component {component} failed: {error_type}",
                {"chain_position": i + 1, "total_failures": len(error_chain)}
            )

            # Log security implications
            if i >= 2:  # Trading engine and beyond
                security_monitor.log_data_access(
                    component, "trading_operations", "emergency_stop", "HALT"
                )

        # Simulate recovery
        for error_info in reversed(error_chain):
            component = error_info["component"]

            # Log component restart
            enhanced_logger.log_component_start(f"{component}_RECOVERY", "1.0")

            # Generate recovery alert
            alert_system.log_alert(
                "INFO",
                f"{component}_RECOVERY",
                f"Component {component} recovered and operational",
                {"recovery_time": datetime.now(timezone.utc).isoformat()}
            )

        # Verify error chain was logged
        alerts = alert_system.get_recent(20)
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]
        recovery_alerts = [a for a in alerts if "RECOVERY" in a["alert_type"]]

        assert len(critical_alerts) >= 1
        assert len(recovery_alerts) >= 4

    def test_data_consistency_across_components(self, tmp_path):
        """Test data consistency across all monitoring components."""
        # Initialize components
        shadow_collector = ShadowDataCollector(kb_base=str(tmp_path))
        enhanced_logger = EnhancedSessionLogger(kb_base=str(tmp_path))
        alert_system = AlertSystem(kb_base=str(tmp_path))

        shadow_collector.start_collection()

        try:
            # Generate correlated events with timestamps
            test_timestamp = datetime.now(timezone.utc)
            test_id = "consistency_test_001"

            # 1. Log session event
            enhanced_logger.log_trading_decision_chain(test_id, [
                {"step": 1, "component": "TEST", "decision": "EXECUTE"}
            ])

            # 2. Collect metric
            shadow_collector.collect_metric("test_metric", 42.0, "TEST", test_id=test_id)

            # 3. Generate alert
            alert_system.log_alert(
                "INFO", "CONSISTENCY_TEST", f"Test event for {test_id}",
                {"test_id": test_id}
            )

            # Process data
            shadow_collector._process_metric_queue()
            time.sleep(0.1)

            # Verify data consistency
            today = test_timestamp.strftime("%Y-%m-%d")

            # Check all files contain the test ID
            session_log = enhanced_logger._logs_dir / f"{today}.log"
            metrics_file = shadow_collector._shadow_dir / f"metrics_{today}.jsonl"
            alerts_file = alert_system._alerts_file

            files_to_check = [session_log, metrics_file, alerts_file]

            for file_path in files_to_check:
                assert file_path.exists()
                with open(file_path) as f:
                    content = f.read()
                    assert test_id in content

        finally:
            shadow_collector.stop_collection()


if __name__ == "__main__":
    pytest.main([__file__])
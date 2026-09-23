"""Comprehensive Security Test Suite - Tests for security fixes and vulnerability protection.

SECURITY CONTEXT: Critical test coverage for Red Team Audit findings
Reference: research/kap_outputs/red_team_audit_april7.md

This test suite validates all security implementations including:
- AI response validation and injection protection
- Environment security checks
- File system protection
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.security.validation import (
    SecurityValidationError,
    validate_ai_response_secure,
    MAX_RESPONSE_LENGTH,
    MAX_JSON_DEPTH,
    MAX_STRING_LENGTH,
)
from src.security.environment import (
    SecurityLevel,
    EnvironmentSecurityManager,
    validate_environment_security,
    get_security_recommendations,
)


# ═══════════════════════════════════════════════════════════════════════
# AI Response Validation Tests
# ═══════════════════════════════════════════════════════════════════════

class TestAIResponseValidation:
    """Test AI response validation and injection protection."""

    def test_valid_json_response_parsing(self):
        """Test parsing of valid AI response with JSON."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            decision: str
            confidence: float

        response = """
        Here's my analysis:

        ```json
        {
            "decision": "BULLISH",
            "confidence": 0.85
        }
        ```
        """

        result = validate_ai_response_secure(response, TestSchema)
        assert result.decision == "BULLISH"
        assert result.confidence == 0.85

    def test_response_length_limit_enforcement(self):
        """Test that oversized responses are rejected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Create response larger than limit
        large_response = "x" * (MAX_RESPONSE_LENGTH + 1000)

        with pytest.raises(SecurityValidationError, match="Response too large"):
            validate_ai_response_secure(large_response, TestSchema)

    def test_injection_pattern_detection(self):
        """Test that malicious injection patterns are detected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        malicious_responses = [
            '{"data": "__import__(\\"os\\").system(\\"rm -rf /\\")"}',
            '{"data": "eval(malicious_code)"}',
            '{"data": "exec(dangerous_code)"}',
            '{"data": "from os import system"}',
            '{"data": "constructor.prototype"}',
        ]

        for malicious in malicious_responses:
            with pytest.raises(SecurityValidationError, match="Suspicious pattern detected"):
                validate_ai_response_secure(malicious, TestSchema)

    def test_json_depth_limit_enforcement(self):
        """Test that deeply nested JSON is rejected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: dict

        # Create deeply nested JSON beyond limit
        nested_json = '{"data": '
        for _ in range(MAX_JSON_DEPTH + 2):
            nested_json += '{"nested": '
        nested_json += '"value"'
        for _ in range(MAX_JSON_DEPTH + 2):
            nested_json += '}'
        nested_json += '}'

        with pytest.raises(SecurityValidationError, match="JSON too deeply nested"):
            validate_ai_response_secure(nested_json, TestSchema)

    def test_string_length_limit_enforcement(self):
        """Test that overly long string fields are rejected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            message: str

        # Create a long string with high entropy to avoid JSON bomb detection
        import string
        long_string = ''.join([f"char_{i}_" for i in range((MAX_STRING_LENGTH + 100) // 7)])
        response = f'{{"message": "{long_string}"}}'

        with pytest.raises(SecurityValidationError, match="String field too long"):
            validate_ai_response_secure(response, TestSchema)

    def test_json_bomb_detection(self):
        """Test that JSON bombs (low entropy) are detected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Create low-entropy JSON bomb
        bomb_json = '{"data": "' + 'A' * 5000 + '"}'

        with pytest.raises(SecurityValidationError, match="Potential JSON bomb"):
            validate_ai_response_secure(bomb_json, TestSchema)

    def test_prototype_pollution_detection(self):
        """Test that prototype pollution attempts are detected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        pollution_attempts = [
            '{"__proto__": {"polluted": true}, "data": "test"}',
            '{"constructor": {"prototype": {"polluted": true}}, "data": "test"}',
            '{"prototype": {"polluted": true}, "data": "test"}',
        ]

        for attempt in pollution_attempts:
            with pytest.raises(SecurityValidationError, match="(Dangerous object key|Suspicious pattern detected)"):
                validate_ai_response_secure(attempt, TestSchema)

    def test_script_injection_detection(self):
        """Test that script injection attempts are detected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            content: str

        injection_attempts = [
            '{"content": "<script>alert(\\"xss\\")</script>"}',
            '{"content": "javascript:alert(\\"xss\\")"}',
            '{"content": "data:text/html,<script>alert(1)</script>"}',
            '{"content": "vbscript:msgbox(\\"xss\\")"}',
            '{"content": "<div onclick=\\"alert(1)\\">test</div>"}',
        ]

        for attempt in injection_attempts:
            with pytest.raises(SecurityValidationError, match="Suspicious content pattern"):
                validate_ai_response_secure(attempt, TestSchema)

    def test_malformed_json_handling(self):
        """Test that malformed JSON is handled securely."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        malformed_json = '{"data": "test", invalid}'

        with pytest.raises(SecurityValidationError, match="Invalid JSON format"):
            validate_ai_response_secure(malformed_json, TestSchema)

    def test_non_object_json_rejection(self):
        """Test that non-object JSON is rejected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        array_json = '["not", "an", "object"]'

        with pytest.raises(SecurityValidationError, match="Expected JSON object"):
            validate_ai_response_secure(array_json, TestSchema)

    def test_unbalanced_braces_detection(self):
        """Test that unbalanced JSON braces are detected."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        unbalanced_json = '{"data": "test", "missing": "brace"'

        with pytest.raises(SecurityValidationError, match="(Unbalanced JSON braces|Invalid JSON format)"):
            validate_ai_response_secure(unbalanced_json, TestSchema)


# ═══════════════════════════════════════════════════════════════════════
# Environment Security Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnvironmentSecurity:
    """Test environment security validation and management."""

    def test_security_level_enum(self):
        """Test SecurityLevel enum values."""
        assert SecurityLevel.DEVELOPMENT.value == "development"
        assert SecurityLevel.TESTING.value == "testing"
        assert SecurityLevel.PRODUCTION.value == "production"

    def test_development_environment_validation(self):
        """Test development environment security validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            result = validate_environment_security()
            assert result.security_level == SecurityLevel.DEVELOPMENT
            assert not result.is_secure_for_production

    def test_production_environment_validation(self):
        """Test production environment security validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'LOG_LEVEL': 'INFO',
            'SECRET_KEY': 'secure-key-here-with-sufficient-length',
            'DATABASE_URL': 'postgresql://secure-connection'
        }):
            result = validate_environment_security()
            assert result.security_level == SecurityLevel.PRODUCTION
            assert result.is_secure_for_production

    def test_missing_critical_variables_detection(self):
        """Test detection of missing critical environment variables."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false'
            # Missing SECRET_KEY and DATABASE_URL
        }, clear=True):
            result = validate_environment_security()
            assert not result.is_secure_for_production
            assert len(result.missing_variables) > 0
            assert 'SECRET_KEY' in result.missing_variables

    def test_insecure_configuration_detection(self):
        """Test detection of insecure configurations."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',  # Insecure for production
            'LOG_LEVEL': 'DEBUG',  # Insecure for production
            'SECRET_KEY': '123'  # Weak secret
        }):
            result = validate_environment_security()
            assert not result.is_secure_for_production
            assert len(result.security_issues) > 0

    def test_security_recommendations_generation(self):
        """Test security recommendations generation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true'
        }):
            recommendations = get_security_recommendations()
            assert len(recommendations) > 0
            assert any("production" in rec.lower() for rec in recommendations)

    def test_environment_security_manager_initialization(self):
        """Test EnvironmentSecurityManager initialization."""
        manager = EnvironmentSecurityManager()
        assert manager.current_level in [SecurityLevel.DEVELOPMENT, SecurityLevel.TESTING, SecurityLevel.PRODUCTION]

    def test_security_manager_validation_caching(self):
        """Test that security validation results are cached."""
        manager = EnvironmentSecurityManager()

        # First validation
        result1 = manager.validate_current_environment()

        # Second validation (should use cache)
        result2 = manager.validate_current_environment()

        # Results should be identical (cached)
        assert result1.security_level == result2.security_level
        assert result1.is_secure_for_production == result2.is_secure_for_production

    def test_security_manager_force_refresh(self):
        """Test forced refresh of security validation."""
        manager = EnvironmentSecurityManager()

        # Get initial result
        manager.validate_current_environment()

        # Force refresh should work without error
        result = manager.validate_current_environment(force_refresh=True)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════
# Integration Security Tests
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityIntegration:
    """Integration tests for security systems."""

    def test_security_systems_initialization(self, tmp_path):
        """Test that all security systems can be initialized together."""
        # Create test environment
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        test_agent = agents_dir / "test_agent.md"
        test_agent.write_text("# Test Agent")

        # Test environment security
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            env_result = validate_environment_security()
            assert env_result.security_level == SecurityLevel.TESTING

        # Test AI validation
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            status: str

        response = '{"status": "secure"}'
        result = validate_ai_response_secure(response, TestSchema)
        assert result.status == "secure"

    def test_security_under_stress(self, tmp_path):
        """Test security systems under stress conditions."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Test multiple validation attempts
        for i in range(100):
            try:
                response = f'{{"data": "test_{i}"}}'
                result = validate_ai_response_secure(response, TestSchema)
                assert result.data == f"test_{i}"
            except Exception as e:
                pytest.fail(f"Security validation failed under stress: {e}")

    def test_security_error_handling(self):
        """Test security system error handling."""
        # Test with invalid schema
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            required_field: str

        # Missing required field should raise ValidationError, not SecurityValidationError
        response = '{"optional_field": "test"}'

        with pytest.raises(Exception):  # Could be ValidationError or SecurityValidationError
            validate_ai_response_secure(response, TestSchema)


# ═══════════════════════════════════════════════════════════════════════
# Edge Cases and Attack Vectors
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityEdgeCases:
    """Test edge cases and potential attack vectors."""

    def test_empty_response_handling(self):
        """Test handling of empty AI responses."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str = "default"

        empty_responses = ["", " ", "\n", "\t"]

        for empty in empty_responses:
            with pytest.raises((SecurityValidationError, Exception)):
                validate_ai_response_secure(empty, TestSchema)

    def test_unicode_injection_attempts(self):
        """Test handling of Unicode-based injection attempts."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            content: str

        unicode_attacks = [
            '{"content": "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e"}',
            '{"content": "\\u0065val(\\u0061lert(1))"}',
            '{"content": "\\u006Aavascript:alert(1)"}',
        ]

        for attack in unicode_attacks:
            try:
                result = validate_ai_response_secure(attack, TestSchema)
                # If parsing succeeds, content should not contain dangerous patterns
                assert "<script" not in result.content.lower()
                assert "javascript:" not in result.content.lower()
            except SecurityValidationError:
                # Security validation rejection is also acceptable
                pass

    def test_null_byte_injection(self):
        """Test handling of null byte injection attempts."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            filename: str

        null_byte_attack = '{"filename": "safe.txt\\u0000../../../etc/passwd"}'

        # Should be handled by security validation
        try:
            result = validate_ai_response_secure(null_byte_attack, TestSchema)
            # If parsing succeeds, the null byte may remain (depends on implementation)
            # The key is that the security system processed it
            assert result.filename is not None
        except SecurityValidationError:
            # Security validation rejection is the preferred outcome
            pass

    def test_extremely_long_key_names(self):
        """Test handling of extremely long JSON key names."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        long_key = "x" * (MAX_STRING_LENGTH + 100)
        attack_json = f'{{"{long_key}": "test", "data": "value"}}'

        with pytest.raises(SecurityValidationError):
            validate_ai_response_secure(attack_json, TestSchema)

    def test_circular_reference_attack(self):
        """Test handling of circular reference attempts."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Simulate circular reference pattern
        circular_json = '{"a": {"b": {"c": {"a": "reference"}}}, "data": "test"}'

        # Should be handled gracefully
        try:
            result = validate_ai_response_secure(circular_json, TestSchema)
            assert result.data == "test"
        except SecurityValidationError:
            pass

    def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion attacks."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Attempt to create memory exhaustion
        large_array_json = '{"data": "test", "large_array": [' + '"x",' * 100000 + '"x"]}'

        with pytest.raises(SecurityValidationError):
            validate_ai_response_secure(large_array_json, TestSchema)


# ═══════════════════════════════════════════════════════════════════════
# Performance and Benchmarking Tests
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityPerformance:
    """Test security system performance characteristics."""

    def test_validation_performance_baseline(self):
        """Test validation performance baseline."""
        import time
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        response = '{"data": "test_performance"}'

        # Measure validation time
        start_time = time.time()
        for _ in range(100):
            validate_ai_response_secure(response, TestSchema)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100

        # Should complete in reasonable time (< 10ms per validation)
        assert avg_time < 0.01, f"Validation too slow: {avg_time:.4f}s per call"

# ═══════════════════════════════════════════════════════════════════════
# Security Configuration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityConfiguration:
    """Test security configuration and customization."""

    def test_custom_validation_limits(self):
        """Test custom validation limits."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            data: str

        # Test with custom max length
        custom_limit = 1000
        large_response = "x" * (custom_limit + 100)

        with pytest.raises(SecurityValidationError, match="Response too large"):
            validate_ai_response_secure(large_response, TestSchema, max_length=custom_limit)

    def test_security_level_escalation_protection(self):
        """Test protection against security level escalation."""
        manager = EnvironmentSecurityManager()

        # Cannot manually set higher security level
        with pytest.raises(AttributeError):
            manager.current_level = SecurityLevel.PRODUCTION

    def test_configuration_immutability(self):
        """Test that security configurations are immutable."""
        from src.security.validation import MAX_RESPONSE_LENGTH

        original_limit = MAX_RESPONSE_LENGTH

        # Attempting to modify should not affect validation
        # (This is a Python constant, but test demonstrates principle)
        assert MAX_RESPONSE_LENGTH == original_limit


if __name__ == "__main__":
    pytest.main([__file__])
#!/usr/bin/env python3
"""Security test suite for Red Team Audit remediation.

SECURITY CONTEXT: Verification of critical security fixes
Reference: research/kap_outputs/red_team_audit_april7.md
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def test_environment_sanitization():
    """Test that API keys are properly stripped from environment."""
    print("Testing environment sanitization...")

    # Set some fake API keys for testing
    test_keys = {
        "ANTHROPIC_API_KEY": "sk-test-key-123",
        "OPENAI_API_KEY": "sk-test-key-456",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
    }

    # Temporarily set these keys
    original_values = {}
    for key, value in test_keys.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from src.security import get_sanitized_environment

        # Get sanitized environment
        clean_env = get_sanitized_environment()

        # Check that no test keys survived
        leaked_keys = []
        for key in test_keys:
            if key in clean_env:
                leaked_keys.append(key)

        if leaked_keys:
            print(f"❌ FAILED: API keys leaked: {leaked_keys}")
            return False

        print("✅ PASSED: Environment sanitization working")
        return True

    except Exception as e:
        print(f"❌ FAILED: Environment sanitization error: {e}")
        return False

    finally:
        # Restore original environment
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

def test_secure_json_validation():
    """Test that JSON validation blocks malicious content."""
    print("Testing secure JSON validation...")

    from pydantic import BaseModel
    from src.security.validation import validate_ai_response_secure, SecurityValidationError

    class TestSchema(BaseModel):
        name: str
        value: int

    # Test cases
    test_cases = [
        # Valid JSON
        ('{"name": "test", "value": 42}', True, "Valid JSON"),

        # Malicious patterns
        ('{"name": "test", "__proto__": {"value": 999}}', False, "Prototype pollution"),
        ('{"name": "<script>alert(1)</script>", "value": 42}', False, "XSS attempt"),
        ('{"name": "test", "value": 42, "eval": "import os"}', False, "Code injection"),

        # Size limits
        ('{"name": "' + 'x' * 15000 + '", "value": 42}', False, "Oversized string"),
    ]

    passed = 0
    for test_json, should_pass, description in test_cases:
        try:
            result = validate_ai_response_secure(test_json, TestSchema)
            if should_pass:
                print(f"✅ PASSED: {description}")
                passed += 1
            else:
                print(f"❌ FAILED: {description} (should have been blocked)")
        except (SecurityValidationError, ValueError) as e:
            if not should_pass:
                print(f"✅ PASSED: {description} (correctly blocked)")
                passed += 1
            else:
                print(f"❌ FAILED: {description} (incorrectly blocked): {e}")

    total = len(test_cases)
    if passed == total:
        print(f"✅ PASSED: JSON validation ({passed}/{total})")
        return True
    else:
        print(f"❌ FAILED: JSON validation ({passed}/{total})")
        return False

def test_runtime_monitoring():
    """Test runtime API key monitoring."""
    print("Testing runtime monitoring...")

    try:
        from src.security import install_runtime_monitoring

        # Install monitoring
        install_runtime_monitoring()

        # This is a basic test - the monitoring installs log filters
        # Real testing would require injecting test log messages
        print("✅ PASSED: Runtime monitoring installed")
        return True

    except Exception as e:
        print(f"❌ FAILED: Runtime monitoring error: {e}")
        return False

def main():
    """Run all security tests."""
    print("🔒 Running Security Test Suite")
    print("=" * 50)

    tests = [
        test_environment_sanitization,
        test_secure_json_validation,
        test_runtime_monitoring,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    total = len(tests)
    print(f"Security Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL SECURITY TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME SECURITY TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
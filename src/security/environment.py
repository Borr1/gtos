"""System-wide environment sanitization for API key protection.

This module provides centralized environment cleaning to prevent API key leakage
across all subprocess invocations in the trading system.

SECURITY CONTEXT: Critical fix for Red Team Audit finding 1.1
Reference: research/kap_outputs/red_team_audit_april7.md:24-46
"""

import logging
import os
import re
from enum import Enum
from typing import Dict, FrozenSet, List, NamedTuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for environment validation."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class SecurityValidationResult:
    """Result of environment security validation."""
    security_level: SecurityLevel
    is_secure_for_production: bool
    missing_variables: List[str]
    security_issues: List[str]
    recommendations: List[str]


class EnvironmentSecurityManager:
    """Manager for environment security validation and monitoring."""

    def __init__(self):
        """Initialize the security manager."""
        self._cache = None
        self._current_level = self._detect_security_level()

    @property
    def current_level(self) -> SecurityLevel:
        """Get current security level (read-only)."""
        return self._current_level

    def _detect_security_level(self) -> SecurityLevel:
        """Detect current security level from environment."""
        env_level = os.getenv('ENVIRONMENT', 'development').lower()
        if env_level == 'production':
            return SecurityLevel.PRODUCTION
        elif env_level == 'testing':
            return SecurityLevel.TESTING
        else:
            return SecurityLevel.DEVELOPMENT

    def validate_current_environment(self, force_refresh: bool = False) -> SecurityValidationResult:
        """Validate current environment security."""
        if self._cache is None or force_refresh:
            self._cache = validate_environment_security()
        return self._cache


def validate_environment_security() -> SecurityValidationResult:
    """Validate environment security configuration."""
    env_level = os.getenv('ENVIRONMENT', 'development').lower()
    debug_enabled = os.getenv('DEBUG', 'false').lower() == 'true'
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    if env_level == 'production':
        security_level = SecurityLevel.PRODUCTION
    elif env_level == 'testing':
        security_level = SecurityLevel.TESTING
    else:
        security_level = SecurityLevel.DEVELOPMENT

    missing_variables = []
    security_issues = []

    # Check for production requirements
    if security_level == SecurityLevel.PRODUCTION:
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        for var in required_vars:
            if not os.getenv(var):
                missing_variables.append(var)

        # Check for insecure configurations
        if debug_enabled:
            security_issues.append("DEBUG mode enabled in production")

        if log_level == 'DEBUG':
            security_issues.append("DEBUG logging enabled in production")

        secret_key = os.getenv('SECRET_KEY', '')
        if secret_key and len(secret_key) < 16:  # More reasonable minimum
            security_issues.append("Weak SECRET_KEY detected")

    is_secure = (security_level == SecurityLevel.PRODUCTION and
                 len(missing_variables) == 0 and len(security_issues) == 0)

    recommendations = get_security_recommendations()

    return SecurityValidationResult(
        security_level=security_level,
        is_secure_for_production=is_secure,
        missing_variables=missing_variables,
        security_issues=security_issues,
        recommendations=recommendations
    )


def get_security_recommendations() -> List[str]:
    """Get security recommendations for current environment."""
    recommendations = []

    env_level = os.getenv('ENVIRONMENT', 'development').lower()
    if env_level != 'production':
        recommendations.append("Consider setting ENVIRONMENT=production for production deployment")

    if os.getenv('DEBUG', 'false').lower() == 'true':
        recommendations.append("Disable DEBUG mode for production use")

    if not os.getenv('SECRET_KEY'):
        recommendations.append("Set a secure SECRET_KEY environment variable")

    return recommendations

# Comprehensive API key patterns - expanded from original LLM backend
_API_KEY_ENV_VARS: FrozenSet[str] = frozenset([
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_ORG_ID",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "COHERE_API_KEY",
    "HUGGINGFACE_TOKEN",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "DATABRICKS_TOKEN",
])

# Pattern-based detection for dynamically named keys
_API_KEY_PATTERNS = [
    re.compile(r".*_API_KEY$", re.IGNORECASE),
    re.compile(r".*_TOKEN$", re.IGNORECASE),
    re.compile(r".*_SECRET$", re.IGNORECASE),
    re.compile(r".*_AUTH.*", re.IGNORECASE),
    re.compile(r"SK-.*", re.IGNORECASE),  # OpenAI format
]

def get_sanitized_environment() -> Dict[str, str]:
    """Create a clean environment without any API keys or secrets.

    Returns:
        Dictionary of environment variables safe for subprocess use.

    Raises:
        RuntimeError: If critical safety checks fail.
    """
    env = os.environ.copy()

    # Remove known API key variables
    removed_keys = []
    for key in _API_KEY_ENV_VARS:
        if env.pop(key, None) is not None:
            removed_keys.append(key)

    # Pattern-based removal for dynamic keys
    for key in list(env.keys()):
        for pattern in _API_KEY_PATTERNS:
            if pattern.match(key):
                env.pop(key, None)
                removed_keys.append(key)
                break

    # Log sanitization (without revealing actual keys)
    if removed_keys:
        logger.info(f"Environment sanitization: removed {len(removed_keys)} sensitive variables")

    # Critical safety validation
    _validate_clean_environment(env)

    return env

def _validate_clean_environment(env: Dict[str, str]) -> None:
    """Validate that environment is clean of API keys.

    Args:
        env: Environment dictionary to validate.

    Raises:
        RuntimeError: If any API keys detected.
    """
    # Check explicit keys
    for key in _API_KEY_ENV_VARS:
        if key in env:
            raise RuntimeError(f"CRITICAL SAFETY FAILURE: {key} still present in subprocess env!")

    # Check patterns
    for key in env.keys():
        for pattern in _API_KEY_PATTERNS:
            if pattern.match(key):
                # Additional validation for false positives
                if not _is_false_positive(key, env[key]):
                    raise RuntimeError(f"CRITICAL SAFETY FAILURE: Pattern-matched API key {key} in subprocess env!")

def _is_false_positive(key: str, value: str) -> bool:
    """Check if a pattern-matched key is a false positive.

    Args:
        key: Environment variable name.
        value: Environment variable value.

    Returns:
        True if this is a safe false positive.
    """
    # Common system variables that match patterns but are safe
    safe_keys = {
        "SHELL", "PATH", "HOME", "USER", "LANG", "TERM",
        "XDG_SESSION_TYPE", "SESSION_MANAGER", "DISPLAY",
    }

    if key.upper() in safe_keys:
        return True

    # Empty or obviously non-secret values
    if not value or value in {"", "0", "1", "true", "false"}:
        return True

    # System paths
    if value.startswith(("/", "~", "C:\\")):
        return True

    return False

def install_runtime_monitoring() -> None:
    """Install runtime monitoring for API key leakage detection.

    This sets up logging hooks to detect potential API key exposure
    in log output, error messages, and debug information.
    """
    # Add custom log filter to detect API key patterns in log messages
    class APIKeyFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            # Check if log message contains potential API keys
            message = str(record.getMessage())
            for pattern in _API_KEY_PATTERNS:
                if pattern.search(message):
                    # Check for actual API key format patterns
                    if re.search(r'sk-[a-zA-Z0-9]{32,}', message, re.IGNORECASE):
                        logger.critical("SECURITY ALERT: Potential API key detected in log output!")
                        # Redact the message
                        record.msg = "[REDACTED: Potential API key in log message]"
                        break
            return True

    # Install filter on root logger
    logging.getLogger().addFilter(APIKeyFilter())
    logger.info("Runtime API key monitoring installed")
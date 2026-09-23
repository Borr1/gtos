"""Security module for trading system protection.

SECURITY CONTEXT: Emergency security patches for Red Team Audit findings
Reference: research/kap_outputs/red_team_audit_april7.md
"""

from .environment import get_sanitized_environment, install_runtime_monitoring
from .validation import SecurityValidationError, validate_ai_response_secure

__all__ = [
    "get_sanitized_environment",
    "install_runtime_monitoring",
    "SecurityValidationError",
    "validate_ai_response_secure",
]
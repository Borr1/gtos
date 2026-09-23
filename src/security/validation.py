"""Secure validation for AI response parsing with injection protection.

SECURITY CONTEXT: Critical fix for Red Team Audit finding 1.2
Reference: research/kap_outputs/red_team_audit_april7.md:47-68
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Security limits for AI response processing
MAX_RESPONSE_LENGTH = 100_000  # 100KB limit
MAX_JSON_DEPTH = 10  # Prevent deeply nested objects
MAX_STRING_LENGTH = 10_000  # Individual string field limit

class SecurityValidationError(Exception):
    """Raised when security validation fails."""
    pass

def validate_ai_response_secure(
    response_text: str,
    expected_schema: type[BaseModel],
    max_length: Optional[int] = None
) -> BaseModel:
    """Securely validate and parse AI response with injection protection.

    Args:
        response_text: Raw AI response text.
        expected_schema: Pydantic model class for validation.
        max_length: Custom max length override.

    Returns:
        Validated pydantic model instance.

    Raises:
        SecurityValidationError: If security checks fail.
        ValidationError: If schema validation fails.
    """
    # Security check 1: Response length limit
    max_len = max_length or MAX_RESPONSE_LENGTH
    if len(response_text) > max_len:
        raise SecurityValidationError(
            f"Response too large: {len(response_text)} bytes > {max_len} limit"
        )

    # Security check 2: Extract and validate JSON structure
    try:
        json_text = _extract_json_secure(response_text)
    except SecurityValidationError:
        raise
    except Exception as e:
        raise SecurityValidationError(f"JSON extraction failed: {e}")

    # Security check 3: Parse with strict limits
    try:
        raw_data = _parse_json_secure(json_text)
    except SecurityValidationError:
        raise
    except Exception as e:
        raise SecurityValidationError(f"JSON parsing failed: {e}")

    # Security check 4: Content validation (order matters for error messages)
    try:
        _validate_content_security(raw_data)
    except SecurityValidationError:
        raise

    # Schema validation
    try:
        return expected_schema.model_validate(raw_data)
    except ValidationError as e:
        logger.warning(f"Schema validation failed: {e}")
        raise

def _extract_json_secure(text: str) -> str:
    """Extract JSON from AI response with security checks.

    Args:
        text: Raw AI response text.

    Returns:
        Extracted JSON string.

    Raises:
        SecurityValidationError: If extraction fails security checks.
    """
    text = text.strip()

    # Security: Check for obvious injection attempts
    suspicious_patterns = [
        r'__[a-zA-Z_]+__',  # Python dunder methods
        r'eval\s*\(',       # eval() calls
        r'exec\s*\(',       # exec() calls
        r'import\s+',       # import statements
        r'from\s+\w+\s+import',  # from ... import
        r'\.prototype\.',   # JavaScript prototype pollution
        r'constructor',     # Constructor access
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise SecurityValidationError(f"Suspicious pattern detected: {pattern}")

    # Try exact match first (fences at start/end)
    pattern = r"^```(?:json|yaml)?\s*\n?(.*?)```\s*$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try with preamble — find ```json anywhere in the text
    pattern2 = r"```(?:json|yaml)?\s*\n?(.*?)```"
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        return match2.group(1).strip()

    # Try to find raw JSON object with strict validation
    brace_start = text.find("{")
    brace_end = text.rfind("}")

    if brace_start >= 0 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1]

        # Security: Basic structure validation
        open_braces = candidate.count("{")
        close_braces = candidate.count("}")

        if open_braces != close_braces:
            raise SecurityValidationError("Unbalanced JSON braces detected")

        if open_braces > MAX_JSON_DEPTH:
            raise SecurityValidationError(f"JSON too deeply nested: {open_braces} levels")

        return candidate

    # Last resort: treat entire text as potential JSON
    return text

def _parse_json_secure(json_text: str) -> Dict[str, Any]:
    """Parse JSON with security limits and validation.

    Args:
        json_text: JSON string to parse.

    Returns:
        Parsed dictionary.

    Raises:
        SecurityValidationError: If parsing fails security checks.
    """
    # Security: Additional length check after extraction
    if len(json_text) > MAX_RESPONSE_LENGTH:
        raise SecurityValidationError(f"Extracted JSON too large: {len(json_text)} bytes")

    # Security: Check for JSON bombs (excessive repetition)
    unique_chars = len(set(json_text))
    if len(json_text) > 1000 and unique_chars < 20:
        raise SecurityValidationError("Potential JSON bomb detected (low entropy)")

    try:
        # Use strict JSON parsing
        data = json.loads(json_text, strict=True)
    except json.JSONDecodeError as e:
        raise SecurityValidationError(f"Invalid JSON format: {e}")

    if not isinstance(data, dict):
        raise SecurityValidationError(f"Expected JSON object, got {type(data)}")

    return data

def _validate_content_security(data: Dict[str, Any]) -> None:
    """Validate parsed data for security issues.

    Args:
        data: Parsed JSON data.

    Raises:
        SecurityValidationError: If security issues detected.
    """
    # Check in order of priority for better error messages
    _check_suspicious_content(data)  # Check dangerous content first
    _check_string_lengths(data)      # Then check string lengths
    _check_object_depth(data, 0)     # Finally check depth

def _check_object_depth(obj: Any, depth: int) -> None:
    """Check object nesting depth recursively."""
    if depth > MAX_JSON_DEPTH:
        raise SecurityValidationError(f"Object nesting too deep: {depth} levels")

    if isinstance(obj, dict):
        for value in obj.values():
            _check_object_depth(value, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _check_object_depth(item, depth + 1)

def _check_string_lengths(obj: Any) -> None:
    """Check string field lengths recursively."""
    if isinstance(obj, str):
        if len(obj) > MAX_STRING_LENGTH:
            raise SecurityValidationError(f"String field too long: {len(obj)} chars")
    elif isinstance(obj, dict):
        # Check both keys and values
        for key, value in obj.items():
            if isinstance(key, str) and len(key) > MAX_STRING_LENGTH:
                raise SecurityValidationError(f"String field too long: {len(key)} chars")
            _check_string_lengths(value)
    elif isinstance(obj, list):
        for item in obj:
            _check_string_lengths(item)

def _check_suspicious_content(obj: Any) -> None:
    """Check for suspicious content patterns."""
    if isinstance(obj, str):
        # Check for script injection patterns - literal strings
        suspicious_literals = [
            '<script',
            'javascript:',
            'data:text/html',
            'vbscript:',
        ]

        lower_obj = obj.lower()
        for pattern in suspicious_literals:
            if pattern in lower_obj:
                raise SecurityValidationError(f"Suspicious content pattern: {pattern}")

        # Check for HTML event handlers using regex
        import re
        event_handler_pattern = re.compile(r'on[a-z]+=', re.IGNORECASE)
        if event_handler_pattern.search(obj):
            raise SecurityValidationError(f"Suspicious content pattern: HTML event handler")

    elif isinstance(obj, dict):
        # Check for prototype pollution attempts
        dangerous_keys = ['__proto__', 'constructor', 'prototype']
        for key in dangerous_keys:
            if key in obj:
                raise SecurityValidationError(f"Dangerous object key: {key}")

        for value in obj.values():
            _check_suspicious_content(value)
    elif isinstance(obj, list):
        for item in obj:
            _check_suspicious_content(item)
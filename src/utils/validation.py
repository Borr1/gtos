"""Validation utilities for data schemas and AI response parsing.

SECURITY UPDATE: Enhanced with secure AI response validation.
See src.security.validation for new secure parsing functions.
"""

import json
import re
from typing import Any

from pydantic import ValidationError

# Import secure validation functions
from src.security.validation import validate_ai_response_secure, SecurityValidationError


def validate_json_schema(data: dict, model_class: type) -> tuple[bool, Any]:
    """Validate data against a pydantic model class.

    Args:
        data: Dictionary to validate.
        model_class: A pydantic BaseModel subclass to validate against.

    Returns:
        Tuple of (is_valid, parsed_model_or_error_string).
    """
    try:
        parsed = model_class.model_validate(data)
        return True, parsed
    except ValidationError as e:
        return False, str(e)


def _balanced_json_object_at(text: str, start: int) -> str | None:
    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]

    return None


def _first_valid_json_object(text: str) -> str | None:
    for start, char in enumerate(text):
        if char != "{":
            continue
        candidate = _balanced_json_object_at(text, start)
        if not candidate:
            continue
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return candidate
    return None


def strip_json_fences(text: str) -> str:
    """Strip markdown code fences and preamble from AI responses before JSON parsing.

    DEPRECATED: Use src.security.validation.validate_ai_response_secure() for new code.
    This function remains for backward compatibility but lacks security validation.

    Handles:
      - ```json ... ``` at the start of text
      - Preamble text before ```json ... ``` (CLI mode often adds prose first)
      - ``` ... ``` without language tag
      - Plain JSON with no fences
      - A valid first JSON object followed by trailing prose or another object
    """
    text = text.strip()

    # Try exact match first (fences at start/end)
    pattern = r"^```(?:json|yaml)?\s*\n?(.*?)```\s*$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        fenced = match.group(1).strip()
        return _first_valid_json_object(fenced) or fenced

    # Try with preamble — find ```json anywhere in the text
    pattern2 = r"```(?:json|yaml)?\s*\n?(.*?)```"
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        fenced = match2.group(1).strip()
        return _first_valid_json_object(fenced) or fenced

    candidate = _first_valid_json_object(text)
    if candidate:
        return candidate

    # Try to find raw JSON object (starts with { and ends with })
    # This handles cases where there's preamble but no fences
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1]
        # Quick sanity check — does it look like JSON?
        if candidate.count("{") > 0 and candidate.count("}") > 0:
            return candidate

    return text

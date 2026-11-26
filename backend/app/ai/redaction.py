"""PII detection and secure redaction for documents.

Detects common personally identifiable information (emails, phones, national IDs,
credit-card-like patterns) and redacts them with a reversible placeholder.
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

_PATTERNS: list[tuple[str, str, str]] = [
    ("email", r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]"),
    (
        "phone",
        r"(\+\d{1,3}[\s\-])?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}",
        "[PHONE_REDACTED]",
    ),
    (
        "iranian_national_id",
        r"\b\d{10}\b",
        "[NATIONAL_ID_REDACTED]",
    ),
    (
        "credit_card",
        r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        "[CARD_REDACTED]",
    ),
]


def detect_pii(text: str) -> list[dict]:
    """Return list of PII matches with type, value, start, end."""
    matches: list[dict] = []
    for label, pattern, _ in _PATTERNS:
        for m in re.finditer(pattern, text):
            matches.append(
                {
                    "type": label,
                    "value": m.group(0),
                    "start": m.start(),
                    "end": m.end(),
                }
            )
    # Sort by start position, then deduplicate overlapping matches
    matches.sort(key=lambda x: x["start"])
    deduped: list[dict] = []
    last_end = -1
    for m in matches:
        if m["start"] >= last_end:
            deduped.append(m)
            last_end = m["end"]
    return deduped


def redact(text: str) -> tuple[str, list[dict]]:
    """Return (redacted_text, list_of_redactions)."""
    matches = detect_pii(text)
    # Apply redactions from end to start to preserve positions
    result = text
    for m in sorted(matches, key=lambda x: x["start"], reverse=True):
        label = m["type"]
        placeholder = next(p for lbl, _, p in _PATTERNS if lbl == label)
        result = result[: m["start"]] + placeholder + result[m["end"] :]
    return result, matches

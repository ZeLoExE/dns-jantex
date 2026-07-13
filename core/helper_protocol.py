"""Strict protocol shared by the UI and the elevated DNS helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .validation import normalize_ipv4

ALLOWED_OPERATIONS = frozenset({"set", "reset", "flush"})
ALLOWED_REQUEST_KEYS = frozenset({"operation", "primary", "secondary", "flush_after"})


@dataclass(frozen=True)
class DNSRequest:
    operation: str
    primary: str = ""
    secondary: str = ""
    flush_after: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "primary": self.primary,
            "secondary": self.secondary,
            "flush_after": self.flush_after,
        }


def validate_request(payload: Any) -> DNSRequest:
    """Parse an untrusted helper request into a strict allow-listed command."""
    if not isinstance(payload, dict):
        raise ValueError("Request must be a JSON object")
    unknown = set(payload) - ALLOWED_REQUEST_KEYS
    if unknown:
        raise ValueError(f"Unknown request fields: {', '.join(sorted(unknown))}")

    operation = payload.get("operation")
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("Unsupported DNS operation")

    flush_after = payload.get("flush_after", False)
    if not isinstance(flush_after, bool):
        raise ValueError("flush_after must be a boolean")

    if operation == "set":
        primary = normalize_ipv4(payload.get("primary", ""))
        secondary = normalize_ipv4(payload.get("secondary", ""), required=False)
    else:
        primary = ""
        secondary = ""
        flush_after = False

    return DNSRequest(operation, primary, secondary, flush_after)

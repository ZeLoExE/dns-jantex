"""Shared validation for privileged and unprivileged code paths."""

from __future__ import annotations

import ipaddress


def normalize_ipv4(value: str, *, required: bool = True) -> str:
    """Return canonical IPv4 text or raise ValueError.

    IPv6 is deliberately rejected in v3.0.4 until adapter application and UI
    support can be tested end-to-end.
    """
    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError("IPv4 address is required")
        return ""
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError as exc:
        raise ValueError(f"Invalid IPv4 address: {value}") from exc
    return str(address)


def is_valid_ipv4(value: str) -> bool:
    try:
        normalize_ipv4(value)
        return True
    except ValueError:
        return False

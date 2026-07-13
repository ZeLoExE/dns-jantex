"""Custom DNS Manager - save/load/edit custom DNS entries."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Optional

from .paths import data_dir
from .storage import atomic_write_json, load_json
from .validation import normalize_ipv4


@dataclass
class CustomDNSEntry:
    """A custom IPv4 DNS entry."""

    name: str
    primary: str
    secondary: str
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]


CUSTOM_DNS_FILE = data_dir() / "custom_dns.json"


def load_custom_dns() -> list[CustomDNSEntry]:
    data = load_json(CUSTOM_DNS_FILE, [])
    if not isinstance(data, list):
        return []

    entries: list[CustomDNSEntry] = []
    for item in data:
        try:
            if not isinstance(item, dict):
                continue
            entry = CustomDNSEntry(**item)
            entry.primary = normalize_ipv4(entry.primary)
            entry.secondary = normalize_ipv4(entry.secondary, required=False)
            entries.append(entry)
        except (TypeError, ValueError):
            continue
    return entries


def save_custom_dns(entries: list[CustomDNSEntry]) -> None:
    atomic_write_json(CUSTOM_DNS_FILE, [asdict(entry) for entry in entries])


def add_custom_dns(name: str, primary: str, secondary: str) -> CustomDNSEntry:
    name = name.strip()
    if not name:
        raise ValueError("DNS name is required")
    entry = CustomDNSEntry(
        name=name,
        primary=normalize_ipv4(primary),
        secondary=normalize_ipv4(secondary, required=False),
    )
    entries = load_custom_dns()
    entries.append(entry)
    save_custom_dns(entries)
    return entry


def update_custom_dns(entry_id: str, name: str, primary: str, secondary: str) -> bool:
    name = name.strip()
    if not name:
        raise ValueError("DNS name is required")
    primary = normalize_ipv4(primary)
    secondary = normalize_ipv4(secondary, required=False)

    entries = load_custom_dns()
    for index, entry in enumerate(entries):
        if entry.id == entry_id:
            entries[index] = CustomDNSEntry(name, primary, secondary, id=entry_id)
            save_custom_dns(entries)
            return True
    return False


def remove_custom_dns(entry_id: str) -> bool:
    entries = load_custom_dns()
    filtered = [entry for entry in entries if entry.id != entry_id]
    if len(filtered) == len(entries):
        return False
    save_custom_dns(filtered)
    return True


def get_custom_dns_by_id(entry_id: str) -> Optional[CustomDNSEntry]:
    return next((entry for entry in load_custom_dns() if entry.id == entry_id), None)

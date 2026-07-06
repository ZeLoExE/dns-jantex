"""Custom DNS Manager - save/load/edit custom DNS entries."""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class CustomDNSEntry:
    """A custom DNS entry."""
    name: str
    primary: str
    secondary: str
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"{self.name}_{self.primary}".replace(" ", "_").lower()


# Storage path — writable location next to the executable (not inside _MEIPASS)
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(_APP_DIR, "config")
CUSTOM_DNS_FILE = os.path.join(DATA_DIR, "custom_dns.json")


def _ensure_dir():
    """Ensure config directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_custom_dns() -> list[CustomDNSEntry]:
    """Load custom DNS entries from file."""
    _ensure_dir()
    if not os.path.exists(CUSTOM_DNS_FILE):
        return []

    try:
        with open(CUSTOM_DNS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [CustomDNSEntry(**item) for item in data]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def save_custom_dns(entries: list[CustomDNSEntry]):
    """Save custom DNS entries to file."""
    _ensure_dir()
    data = [asdict(e) for e in entries]
    with open(CUSTOM_DNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_custom_dns(name: str, primary: str, secondary: str) -> CustomDNSEntry:
    """Add a new custom DNS entry."""
    entries = load_custom_dns()
    entry = CustomDNSEntry(name=name, primary=primary, secondary=secondary)
    entries.append(entry)
    save_custom_dns(entries)
    return entry


def update_custom_dns(entry_id: str, name: str, primary: str, secondary: str) -> bool:
    """Update an existing custom DNS entry."""
    entries = load_custom_dns()
    for i, e in enumerate(entries):
        if e.id == entry_id:
            entries[i] = CustomDNSEntry(name=name, primary=primary, secondary=secondary, id=entry_id)
            save_custom_dns(entries)
            return True
    return False


def remove_custom_dns(entry_id: str) -> bool:
    """Remove a custom DNS entry."""
    entries = load_custom_dns()
    original_count = len(entries)
    entries = [e for e in entries if e.id != entry_id]
    if len(entries) < original_count:
        save_custom_dns(entries)
        return True
    return False


def get_custom_dns_by_id(entry_id: str) -> Optional[CustomDNSEntry]:
    """Get a custom DNS entry by ID."""
    for e in load_custom_dns():
        if e.id == entry_id:
            return e
    return None

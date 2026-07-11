"""Network Profiles — save/load/edit DNS profiles linked to specific networks."""

import json
import os
import sys
import uuid
from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class NetworkProfile:
    """A DNS profile linked to a specific network."""
    id: str = ""
    name: str = ""
    icon: str = "🌐"
    network_id: str = ""
    network_type: str = "wifi"  # "wifi" or "ethernet"
    dns_provider: str = ""  # provider name from DNS_PROVIDERS, or "custom"
    primary_dns: str = ""
    secondary_dns: str = ""
    enabled: bool = True
    last_applied: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


# Storage path — writable location next to the executable (same as custom_dns.py)
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(_APP_DIR, "config")
PROFILES_FILE = os.path.join(DATA_DIR, "network_profiles.json")


def _ensure_dir():
    """Ensure config directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_profiles() -> list[NetworkProfile]:
    """Load network profiles from file."""
    _ensure_dir()
    if not os.path.exists(PROFILES_FILE):
        return []

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [NetworkProfile(**item) for item in data]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def save_profiles(profiles: list[NetworkProfile]):
    """Save network profiles to file."""
    _ensure_dir()
    data = [asdict(p) for p in profiles]
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_profile(name: str, icon: str, network_id: str, network_type: str,
                dns_provider: str, primary_dns: str, secondary_dns: str,
                enabled: bool = True) -> NetworkProfile:
    """Add a new network profile."""
    profiles = load_profiles()
    profile = NetworkProfile(
        name=name, icon=icon, network_id=network_id, network_type=network_type,
        dns_provider=dns_provider, primary_dns=primary_dns, secondary_dns=secondary_dns,
        enabled=enabled,
    )
    profiles.append(profile)
    save_profiles(profiles)
    return profile


def update_profile(profile_id: str, name: str, icon: str, network_id: str,
                   network_type: str, dns_provider: str, primary_dns: str,
                   secondary_dns: str, enabled: bool) -> bool:
    """Update an existing network profile."""
    profiles = load_profiles()
    for i, p in enumerate(profiles):
        if p.id == profile_id:
            profiles[i] = NetworkProfile(
                id=profile_id, name=name, icon=icon, network_id=network_id,
                network_type=network_type, dns_provider=dns_provider,
                primary_dns=primary_dns, secondary_dns=secondary_dns,
                enabled=enabled, last_applied=p.last_applied,
            )
            save_profiles(profiles)
            return True
    return False


def remove_profile(profile_id: str) -> bool:
    """Remove a network profile."""
    profiles = load_profiles()
    original_count = len(profiles)
    profiles = [p for p in profiles if p.id != profile_id]
    if len(profiles) < original_count:
        save_profiles(profiles)
        return True
    return False


def get_profile_by_id(profile_id: str) -> Optional[NetworkProfile]:
    """Get a network profile by ID."""
    for p in load_profiles():
        if p.id == profile_id:
            return p
    return None


def match_profile_for_network(network_id: str, network_type: str) -> Optional[NetworkProfile]:
    """Find the first enabled profile matching the given network."""
    for p in load_profiles():
        if p.enabled and p.network_id == network_id and p.network_type == network_type:
            return p
    return None

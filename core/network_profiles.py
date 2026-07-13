"""Network Profiles — persistent DNS profiles linked to networks."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Optional

from .paths import data_dir
from .storage import atomic_write_json, load_json
from .validation import normalize_ipv4


@dataclass
class NetworkProfile:
    id: str = ""
    name: str = ""
    icon: str = "🌐"
    network_id: str = ""
    network_type: str = "wifi"
    dns_provider: str = ""
    primary_dns: str = ""
    secondary_dns: str = ""
    enabled: bool = True
    last_applied: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]


PROFILES_FILE = data_dir() / "network_profiles.json"


def _validated_profile(item: dict) -> NetworkProfile:
    profile = NetworkProfile(**item)
    profile.name = profile.name.strip()
    profile.network_id = profile.network_id.strip()
    if not profile.name or not profile.network_id:
        raise ValueError("Profile name and network ID are required")
    if profile.network_type not in {"wifi", "ethernet"}:
        raise ValueError("Invalid network type")
    profile.primary_dns = normalize_ipv4(profile.primary_dns)
    profile.secondary_dns = normalize_ipv4(profile.secondary_dns, required=False)
    return profile


def load_profiles() -> list[NetworkProfile]:
    data = load_json(PROFILES_FILE, [])
    if not isinstance(data, list):
        return []
    profiles: list[NetworkProfile] = []
    for item in data:
        try:
            if isinstance(item, dict):
                profiles.append(_validated_profile(item))
        except (TypeError, ValueError):
            continue
    return profiles


def save_profiles(profiles: list[NetworkProfile]) -> None:
    atomic_write_json(PROFILES_FILE, [asdict(profile) for profile in profiles])


def add_profile(name: str, icon: str, network_id: str, network_type: str,
                dns_provider: str, primary_dns: str, secondary_dns: str,
                enabled: bool = True) -> NetworkProfile:
    profile = _validated_profile({
        "name": name,
        "icon": icon,
        "network_id": network_id,
        "network_type": network_type,
        "dns_provider": dns_provider,
        "primary_dns": primary_dns,
        "secondary_dns": secondary_dns,
        "enabled": enabled,
    })
    profiles = load_profiles()
    profiles.append(profile)
    save_profiles(profiles)
    return profile


def update_profile(profile_id: str, name: str, icon: str, network_id: str,
                   network_type: str, dns_provider: str, primary_dns: str,
                   secondary_dns: str, enabled: bool) -> bool:
    profiles = load_profiles()
    for index, previous in enumerate(profiles):
        if previous.id == profile_id:
            profiles[index] = _validated_profile({
                "id": profile_id,
                "name": name,
                "icon": icon,
                "network_id": network_id,
                "network_type": network_type,
                "dns_provider": dns_provider,
                "primary_dns": primary_dns,
                "secondary_dns": secondary_dns,
                "enabled": enabled,
                "last_applied": previous.last_applied,
            })
            save_profiles(profiles)
            return True
    return False


def remove_profile(profile_id: str) -> bool:
    profiles = load_profiles()
    filtered = [profile for profile in profiles if profile.id != profile_id]
    if len(filtered) == len(profiles):
        return False
    save_profiles(filtered)
    return True


def get_profile_by_id(profile_id: str) -> Optional[NetworkProfile]:
    return next((profile for profile in load_profiles() if profile.id == profile_id), None)


def match_profile_for_network(network_id: str, network_type: str) -> Optional[NetworkProfile]:
    return next((
        profile for profile in load_profiles()
        if profile.enabled
        and profile.network_id == network_id
        and profile.network_type == network_type
    ), None)

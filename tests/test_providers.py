import ipaddress
import json
from pathlib import Path

from core.dns_providers import DNS_PROVIDERS

ROOT = Path(__file__).resolve().parents[1]


def test_provider_dataset_is_unique_and_valid():
    names = set()
    keys = set()
    pairs = set()
    for provider in DNS_PROVIDERS:
        assert provider.name not in names
        assert provider.name_key not in keys
        pair = (provider.primary, provider.secondary)
        assert pair not in pairs, f"duplicate DNS pair: {pair}"
        assert ipaddress.IPv4Address(provider.primary)
        if provider.secondary:
            assert ipaddress.IPv4Address(provider.secondary)
            assert provider.primary != provider.secondary
        names.add(provider.name)
        keys.add(provider.name_key)
        pairs.add(pair)


def test_all_provider_names_have_english_and_persian_translations():
    en = json.loads((ROOT / "translations" / "en.json").read_text(encoding="utf-8"))
    fa = json.loads((ROOT / "translations" / "fa.json").read_text(encoding="utf-8"))
    for provider in DNS_PROVIDERS:
        assert provider.name_key in en
        assert provider.name_key in fa
        assert en[provider.name_key].strip()
        assert fa[provider.name_key].strip()

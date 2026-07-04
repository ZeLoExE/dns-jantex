from dataclasses import dataclass, field


@dataclass
class DNSProvider:
    """Represents a DNS provider with its servers."""
    name: str
    name_key: str  # Translation key
    primary: str
    secondary: str
    is_custom: bool = False
    category: str = "international"  # "iran" or "international"
    tags: list[str] = field(default_factory=list)  # "gaming", "adblock", "family", "privacy", "security", "anti-sanction"


# Predefined DNS providers — comprehensive global list
DNS_PROVIDERS = [
    # Iranian DNS Providers (anti-sanction, bypass filtering)
    DNSProvider("Shecan", "provider_shecan", "178.22.122.100", "185.51.200.2", category="iran", tags=["anti-sanction"]),
    DNSProvider("Hamrahe Aval", "provider_hamrahe", "78.157.42.100", "78.157.42.101", category="iran", tags=["anti-sanction"]),
    DNSProvider("Alisha", "provider_alisha", "31.14.117.18", "87.107.166.226", category="iran", tags=["anti-sanction"]),
    DNSProvider("Electro", "provider_electro", "78.157.42.104", "78.157.42.106", category="iran", tags=["anti-sanction"]),
    DNSProvider("Begzar", "provider_begzar", "185.55.226.26", "185.55.225.25", category="iran", tags=["anti-sanction"]),
    DNSProvider("Radar", "provider_radar", "10.10.10.4", "10.10.10.4", category="iran", tags=["anti-sanction"]),
    DNSProvider("403 Online", "provider_403online", "10.10.10.10", "10.10.10.20", category="iran", tags=["anti-sanction"]),

    # Google
    DNSProvider("Google", "provider_google", "8.8.8.8", "8.8.4.4", tags=["gaming"]),
    DNSProvider("Google Family", "provider_google_family", "8.8.8.9", "8.8.4.9", tags=["family"]),

    # Cloudflare
    DNSProvider("Cloudflare", "provider_cloudflare", "1.1.1.1", "1.0.0.1", tags=["gaming", "privacy"]),
    DNSProvider("Cloudflare Family", "provider_cloudflare_family", "1.1.1.3", "1.0.0.3", tags=["family"]),
    DNSProvider("Cloudflare Malware", "provider_cloudflare_malware", "1.1.1.2", "1.0.0.2", tags=["security"]),

    # Quad9
    DNSProvider("Quad9", "provider_quad9", "9.9.9.9", "149.112.112.112", tags=["security"]),
    DNSProvider("Quad9 Secured", "provider_quad9_secured", "9.9.9.10", "149.112.112.10", tags=["security"]),
    DNSProvider("Quad9 Unsecured", "provider_quad9_unsecured", "9.9.9.11", "149.112.112.11", tags=["gaming"]),

    # OpenDNS
    DNSProvider("OpenDNS", "provider_opendns", "208.67.222.222", "208.67.220.220", tags=["security"]),
    DNSProvider("OpenDNS Family", "provider_opendns_family", "208.67.222.123", "208.67.220.123", tags=["family"]),

    # AdGuard
    DNSProvider("AdGuard", "provider_adguard", "94.140.14.14", "94.140.15.15", tags=["adblock"]),
    DNSProvider("AdGuard Family", "provider_adguard_family", "94.140.14.15", "94.140.15.16", tags=["adblock", "family"]),

    # NordVPN
    DNSProvider("NordVPN", "provider_nordvpn", "103.86.96.100", "103.86.99.100", tags=["privacy"]),

    # Comodo Secure
    DNSProvider("Comodo Secure", "provider_comodo", "8.26.56.26", "8.20.247.20", tags=["security"]),

    # Level3
    DNSProvider("Level3", "provider_level3", "4.2.2.1", "4.2.2.2", tags=["gaming"]),

    # CleanBrowsing
    DNSProvider("CleanBrowsing", "provider_cleanbrowsing", "185.228.168.9", "185.228.169.9", tags=["security"]),
    DNSProvider("CleanBrowsing Family", "provider_cleanbrowsing_family", "185.228.168.168", "185.228.169.168", tags=["family"]),
    DNSProvider("CleanBrowsing Adult", "provider_cleanbrowsing_adult", "185.228.168.10", "185.228.169.10", tags=["family"]),

    # Yandex
    DNSProvider("Yandex", "provider_yandex", "77.88.8.8", "77.88.8.1", tags=[]),
    DNSProvider("Yandex Safe", "provider_yandex_safe", "77.88.8.7", "77.88.8.3", tags=["security"]),

    # Verisign
    DNSProvider("Verisign", "provider_verisign", "64.6.64.6", "64.6.65.6", tags=["privacy"]),

    # SafeDNS
    DNSProvider("SafeDNS", "provider_safedns", "195.46.39.39", "195.46.39.40", tags=["family", "security"]),

    #alternate DNS
    DNSProvider("Alternate DNS", "provider_alternate", "76.76.19.19", "76.223.122.155", tags=["adblock"]),

    # Hurricane Electric
    DNSProvider("Hurricane Electric", "provider_hurricane", "74.82.42.42", "", tags=["privacy"]),

    # IBM Quad9
    DNSProvider("IBM Quad9", "provider_ibm_quad9", "9.9.9.9", "149.112.112.112", tags=["security"]),

    # DNSWatch
    DNSProvider("DNSWatch", "provider_dnswatch", "185.121.177.177", "169.239.202.202", tags=["privacy"]),

    # Mullvad
    DNSProvider("Mullvad", "provider_mullvad", "194.242.2.2", "194.242.2.3", tags=["privacy"]),

    # NextDNS
    DNSProvider("NextDNS", "provider_nextdns", "45.90.28.0", "45.90.30.0", tags=["adblock", "security"]),

    # UncensoredDNS
    DNSProvider("UncensoredDNS", "provider_uncensored", "91.239.100.100", "89.233.43.71", tags=["privacy"]),

    # HE DNS
    DNSProvider("HE DNS", "provider_he_dns", "74.82.42.42", "", tags=["privacy"]),

    # Cisco Umbrella
    DNSProvider("Cisco Umbrella", "provider_cisco", "208.67.222.222", "208.67.220.220", tags=["security"]),

    # Turkish ISPs
    DNSProvider("Turk Telekom", "provider_turk_telekom", "195.175.254.1", "195.175.254.2", tags=[]),
    DNSProvider("Turkcell", "provider_turkcell", "212.156.70.6", "212.156.70.14", tags=[]),

    # Russian
    DNSProvider("RU Safe", "provider_rusafe", "195.46.39.39", "195.46.39.40", tags=["security"]),
    DNSProvider("DNSlytics", "provider_dnslytics", "77.88.8.8", "77.88.8.1", tags=[]),

    # Chinese
    DNSProvider("Alibaba DNS", "provider_alibaba", "223.5.5.5", "223.6.6.6", tags=["gaming"]),
    DNSProvider("Tencent DNS", "provider_tencent", "119.29.29.29", "119.28.28.28", tags=["gaming"]),
    DNSProvider("Baidu DNS", "provider_baidu", "180.76.76.76", "", tags=[]),
    DNSProvider("CNNIC", "provider_cnnic", "1.2.4.8", "101.226.4.6", tags=[]),

    # Indian
    DNSProvider("Jio DNS", "provider_jio", "101.2.2.2", "101.2.3.3", tags=[]),

    # Australian
    DNSProvider("Australia GOV", "provider_australia", "139.130.4.5", "", tags=[]),

    # Brazilian
    DNSProvider("NIC.BR", "provider_nic_br", "200.160.0.8", "200.160.2.3", tags=[]),
]


def get_provider_by_name(name: str) -> DNSProvider | None:
    """Get a DNS provider by its name."""
    for provider in DNS_PROVIDERS:
        if provider.name == name:
            return provider
    return None


def get_provider_by_index(index: int) -> DNSProvider | None:
    """Get a DNS provider by its index in the list."""
    if 0 <= index < len(DNS_PROVIDERS):
        return DNS_PROVIDERS[index]
    return None

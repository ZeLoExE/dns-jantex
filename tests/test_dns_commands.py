from core.dns_manager import DNSManager
from core.powershell import PowerShellExecutor


def _capture_command(monkeypatch, alias="Ethernet'; Write-Output injected; #"):
    commands = []
    monkeypatch.setattr(
        DNSManager,
        "_get_iface",
        classmethod(lambda cls, adapter_name=None: (alias, None)),
    )
    monkeypatch.setattr(
        PowerShellExecutor,
        "execute",
        staticmethod(lambda command, timeout=30: (commands.append(command) or True, "")),
    )
    return commands


def test_set_dns_quotes_adapter_and_does_not_flush_when_disabled(monkeypatch):
    commands = _capture_command(monkeypatch)
    success, _ = DNSManager.set_dns("1.1.1.1", "1.0.0.1", flush_cache=False)
    assert success
    assert len(commands) == 1
    assert "-InterfaceAlias 'Ethernet''; Write-Output injected; #'" in commands[0]
    assert "Clear-DnsClientCache" not in commands[0]


def test_set_dns_flushes_exactly_once_when_enabled(monkeypatch):
    commands = _capture_command(monkeypatch, alias="Wi-Fi")
    success, _ = DNSManager.set_dns("8.8.8.8", flush_cache=True)
    assert success
    assert commands[0].count("Clear-DnsClientCache") == 1

from core.network_adapter import AdapterInfo, NetworkAdapterDetector


def test_active_adapter_uses_windows_route_metric(monkeypatch):
    adapters = [
        AdapterInfo("Wi-Fi", "Up", "192.168.1.10", ["1.1.1.1"], True, 50, True),
        AdapterInfo("Ethernet", "Up", "10.0.0.10", ["8.8.8.8"], True, 10, False),
    ]
    monkeypatch.setattr(NetworkAdapterDetector, "get_all_adapters", staticmethod(lambda: adapters))
    assert NetworkAdapterDetector.get_active_adapter().name == "Ethernet"


def test_network_profile_type_follows_active_adapter(monkeypatch):
    ethernet = AdapterInfo("Ethernet", "Up", "10.0.0.10", [], True, 10, False)
    monkeypatch.setattr(NetworkAdapterDetector, "get_active_adapter", staticmethod(lambda: ethernet))
    monkeypatch.setattr(NetworkAdapterDetector, "get_current_wifi_ssid", staticmethod(lambda: "Idle Wi-Fi"))
    assert NetworkAdapterDetector.get_current_network_id() == ("Ethernet", "ethernet")

    wifi = AdapterInfo("Wi-Fi", "Up", "192.168.1.10", [], True, 5, True)
    monkeypatch.setattr(NetworkAdapterDetector, "get_active_adapter", staticmethod(lambda: wifi))
    monkeypatch.setattr(NetworkAdapterDetector, "get_current_wifi_ssid", staticmethod(lambda: "Home"))
    assert NetworkAdapterDetector.get_current_network_id() == ("Home", "wifi")

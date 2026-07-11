"""Network Monitor — background thread that detects network changes and matches profiles."""

import logging
from PySide6.QtCore import QThread, Signal
from core.network_adapter import NetworkAdapterDetector
from core.network_profiles import match_profile_for_network

logger = logging.getLogger(__name__)


class NetworkMonitor(QThread):
    """Periodically checks the current network and matches it against saved profiles.

    Emits:
        network_changed: (network_id, network_type) when the network changes
        profile_matched: (NetworkProfile) when a profile matches the current network
    """

    network_changed = Signal(str, str)   # network_id, network_type
    profile_matched = Signal(object)     # NetworkProfile

    def __init__(self, interval_ms: int = 5000, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self._running = True
        self._last_network_id = None
        self._last_network_type = None

    def run(self):
        while self._running:
            self.msleep(self.interval_ms)
            if not self._running:
                break
            try:
                self._check_network()
            except Exception as e:
                logger.warning("NetworkMonitor check failed: %s", e)

    def _check_network(self):
        network_id, network_type = NetworkAdapterDetector.get_current_network_id()

        if not network_id:
            return

        # Detect change
        if network_id != self._last_network_id or network_type != self._last_network_type:
            self._last_network_id = network_id
            self._last_network_type = network_type
            self.network_changed.emit(network_id, network_type)

            # Try to match a profile
            profile = match_profile_for_network(network_id, network_type)
            if profile:
                self.profile_matched.emit(profile)

    def stop(self):
        self._running = False
        self.wait(2000)

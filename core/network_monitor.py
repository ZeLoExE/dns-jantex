"""Background network-change monitor with cooperative cancellation."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from core.network_adapter import NetworkAdapterDetector
from core.network_profiles import match_profile_for_network

logger = logging.getLogger(__name__)


class NetworkMonitor(QThread):
    network_changed = Signal(str, str)
    profile_matched = Signal(object)

    def __init__(self, interval_ms: int = 5000, parent=None):
        super().__init__(parent)
        self.interval_ms = max(250, interval_ms)
        self._last_network_id = None
        self._last_network_type = None

    def run(self):
        # Check immediately, then use short sleeps so shutdown never waits for the
        # full polling interval.
        while not self.isInterruptionRequested():
            try:
                self._check_network()
            except Exception as exc:
                logger.warning("NetworkMonitor check failed: %s", exc)
            remaining = self.interval_ms
            while remaining > 0 and not self.isInterruptionRequested():
                step = min(remaining, 100)
                self.msleep(step)
                remaining -= step

    def _check_network(self):
        network_id, network_type = NetworkAdapterDetector.get_current_network_id()
        if not network_id:
            self._last_network_id = None
            self._last_network_type = None
            return
        if network_id == self._last_network_id and network_type == self._last_network_type:
            return

        self._last_network_id = network_id
        self._last_network_type = network_type
        self.network_changed.emit(network_id, network_type)
        profile = match_profile_for_network(network_id, network_type)
        if profile:
            self.profile_matched.emit(profile)

    def stop(self):
        self.requestInterruption()
        return self.wait(3000)

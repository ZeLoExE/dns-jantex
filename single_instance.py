"""Single-instance enforcement for Windows applications.

Uses a named mutex to detect if another instance is already running,
and a named pipe to send activation requests to the existing instance.
This works even when the window is hidden (minimized to system tray).
"""

import ctypes
import ctypes.wintypes
import json
import sys
import threading
import time

# Windows API constants
ERROR_ALREADY_EXISTS = 183
ERROR_PIPE_CONNECTED = 535
ERROR_BROKEN_PIPE = 109
SW_RESTORE = 9
SW_SHOW = 5
PIPE_ACCESS_DUPLEX = 0x00000003
PIPE_TYPE_BYTE = 0x00000000
PIPE_READMODE_BYTE = 0x00000000
PIPE_WAIT = 0x00000000
PIPE_UNLIMITED_INSTANCES = 255
BUFFER_SIZE = 4096
INVALID_HANDLE_VALUE = -1

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class SingleInstance:
    """Ensures only one instance of the application runs at a time."""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self._mutex_handle = None
        self._pipe_handle = None
        self._pipe_thread = None
        self._activation_callback = None
        self._lock = threading.Lock()
        self._running = False

    def try_lock(self) -> bool:
        """Try to acquire the single-instance mutex.

        Returns True if this is the first instance (lock acquired).
        Returns False if another instance is already running.
        """
        with self._lock:
            if self._mutex_handle is not None:
                return True

            mutex_name = f"Global\\{self.app_name}_SingleInstance_Mutex"
            self._mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)

            if not self._mutex_handle:
                return True

            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None
                self._send_activation()
                return False

            return True

    def start_listening(self, activation_callback):
        """Start listening for activation requests from other instances.

        Args:
            activation_callback: Called on a background thread when another
                                 instance requests activation.
        """
        self._activation_callback = activation_callback
        self._start_pipe_server()

    def _start_pipe_server(self):
        """Start a named pipe server to listen for activation requests."""
        pipe_name = f"\\\\.\\pipe\\{self.app_name}_Activation_Pipe"

        self._pipe_handle = kernel32.CreateNamedPipeW(
            pipe_name,
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            PIPE_UNLIMITED_INSTANCES,
            BUFFER_SIZE,
            BUFFER_SIZE,
            0,
            None,
        )

        if not self._pipe_handle or self._pipe_handle == INVALID_HANDLE_VALUE:
            self._pipe_handle = None
            return

        self._running = True
        self._pipe_thread = threading.Thread(
            target=self._pipe_server_loop, daemon=True
        )
        self._pipe_thread.start()

    def _pipe_server_loop(self):
        """Background thread that listens for activation requests."""
        while self._running:
            connected = kernel32.ConnectNamedPipe(self._pipe_handle, None)

            if not connected:
                error = kernel32.GetLastError()
                if error == ERROR_PIPE_CONNECTED:
                    pass
                elif error == ERROR_BROKEN_PIPE:
                    kernel32.DisconnectNamedPipe(self._pipe_handle)
                    continue
                else:
                    time.sleep(0.05)
                    continue

            buffer = ctypes.create_string_buffer(BUFFER_SIZE)
            bytes_read = ctypes.wintypes.DWORD()

            success = kernel32.ReadFile(
                self._pipe_handle,
                buffer,
                BUFFER_SIZE - 1,
                ctypes.byref(bytes_read),
                None,
            )

            if success and bytes_read.value > 0:
                try:
                    data = json.loads(buffer.value.decode("utf-8"))
                    if data.get("action") == "activate" and self._activation_callback:
                        self._activation_callback()
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            kernel32.DisconnectNamedPipe(self._pipe_handle)

    def _send_activation(self):
        """Send an activation request to the existing instance via named pipe."""
        pipe_name = f"\\\\.\\pipe\\{self.app_name}_Activation_Pipe"

        for _attempt in range(30):
            handle = kernel32.CreateFileW(
                pipe_name,
                0x40000000,  # GENERIC_WRITE
                0,
                None,
                3,  # OPEN_EXISTING
                0,
                None,
            )

            if handle and handle != INVALID_HANDLE_VALUE:
                message = json.dumps({"action": "activate"}).encode("utf-8")
                bytes_written = ctypes.wintypes.DWORD()

                kernel32.WriteFile(
                    handle,
                    message,
                    len(message),
                    ctypes.byref(bytes_written),
                    None,
                )

                kernel32.CloseHandle(handle)
                return

            time.sleep(0.03)

    def release(self):
        """Release resources (called on application exit)."""
        with self._lock:
            self._running = False

            if self._pipe_handle:
                kernel32.CloseHandle(self._pipe_handle)
                self._pipe_handle = None

            if self._mutex_handle:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None

    def __del__(self):
        self.release()

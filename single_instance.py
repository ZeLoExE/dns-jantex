"""Single-instance enforcement for Windows applications.

Uses a named mutex to detect if another instance is already running,
and a named pipe to send activation requests to the existing instance.
This works even when the window is hidden (minimized to system tray).
"""

import ctypes
import ctypes.wintypes
import json
import os
import sys
import tempfile
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


def _activate_existing_window():
    """Find and restore the existing application window using native API."""
    # Try common window titles
    titles = ["DNS Jantex", "DNS Changer"]
    for title in titles:
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            # Show window if hidden
            user32.ShowWindow(hwnd, SW_SHOW)
            # Restore if minimized
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            # Force foreground
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.SetFocus(hwnd)
            return True
    return False


class SingleInstance:
    """Ensures only one instance of the application runs at a time.

    Uses a named mutex for detection and a named pipe for activation messaging.
    """

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

            # Create a named mutex (global, accessible across sessions if admin)
            mutex_name = f"Global\\{self.app_name}_SingleInstance_Mutex"
            self._mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)

            if not self._mutex_handle:
                # Mutex creation failed — allow startup anyway
                return True

            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                # Another instance already holds the mutex — send activation
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None
                self._send_activation()
                return False

            return True

    def start_listening(self, activation_callback):
        """Start listening for activation requests from other instances.

        Call this after the main window is created.

        Args:
            activation_callback: Function to call when activation is requested.
                                 Will be called on a background thread.
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
            None
        )

        if not self._pipe_handle or self._pipe_handle == INVALID_HANDLE_VALUE:
            self._pipe_handle = None
            return

        self._running = True
        self._pipe_thread = threading.Thread(target=self._pipe_server_loop, daemon=True)
        self._pipe_thread.start()

    def _pipe_server_loop(self):
        """Background thread that listens for activation requests."""
        while self._running:
            # Wait for a client to connect
            connected = kernel32.ConnectNamedPipe(self._pipe_handle, None)

            if not connected:
                error = kernel32.GetLastError()
                if error == ERROR_PIPE_CONNECTED:
                    pass  # Client connected before ConnectNamedPipe, proceed
                elif error == ERROR_BROKEN_PIPE:
                    kernel32.DisconnectNamedPipe(self._pipe_handle)
                    continue
                else:
                    time.sleep(0.05)
                    continue

            # Read the activation request
            buffer = ctypes.create_string_buffer(BUFFER_SIZE)
            bytes_read = ctypes.wintypes.DWORD()

            success = kernel32.ReadFile(
                self._pipe_handle,
                buffer,
                BUFFER_SIZE - 1,
                ctypes.byref(bytes_read),
                None
            )

            if success and bytes_read.value > 0:
                try:
                    data = json.loads(buffer.value.decode("utf-8"))
                    if data.get("action") == "activate":
                        if self._activation_callback:
                            self._activation_callback()
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            # Disconnect for next connection
            kernel32.DisconnectNamedPipe(self._pipe_handle)

    def _send_activation(self):
        """Send an activation request to the existing instance via named pipe."""
        pipe_name = f"\\\\.\\pipe\\{self.app_name}_Activation_Pipe"

        # Try to connect to the pipe (with retries for timing)
        for attempt in range(30):
            handle = kernel32.CreateFileW(
                pipe_name,
                0x40000000,  # GENERIC_WRITE
                0,
                None,
                3,  # OPEN_EXISTING
                0,
                None
            )

            if handle and handle != INVALID_HANDLE_VALUE:
                # Send activation request
                message = json.dumps({"action": "activate"}).encode("utf-8")
                bytes_written = ctypes.wintypes.DWORD()

                success = kernel32.WriteFile(
                    handle,
                    message,
                    len(message),
                    ctypes.byref(bytes_written),
                    None
                )

                kernel32.CloseHandle(handle)

                if success:
                    # Also try direct window activation as fallback
                    time.sleep(0.1)
                    _activate_existing_window()
                return

            # Pipe not ready yet, wait and retry
            time.sleep(0.03)

        # Fallback: try direct window activation even if pipe failed
        _activate_existing_window()

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

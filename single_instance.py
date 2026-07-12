"""Single-instance enforcement for Windows applications.

Uses a named mutex to detect if another instance is already running.
If found, signals the existing instance to restore its window and exits.
"""

import ctypes
import ctypes.wintypes
import sys
import threading

# Windows API constants
ERROR_ALREADY_EXISTS = 183
HWND_BROADCAST = 0xFFFF
SW_RESTORE = 9
SW_SHOW = 5

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class SingleInstance:
    """Ensures only one instance of the application runs at a time.

    Usage:
        si = SingleInstance("MyAppName")
        if not si.try_lock():
            # Another instance is already running — exit
            sys.exit(0)

        # ... run application ...

        # On exit, release the lock (optional, handled by destructor)
        si.release()
    """

    def __init__(self, app_name: str):
        self.app_name = app_name
        self._mutex_handle = None
        self._lock = threading.Lock()

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
                # Another instance already holds the mutex
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None
                return False

            return True

    def release(self):
        """Release the mutex (called on application exit)."""
        with self._lock:
            if self._mutex_handle:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None

    def __del__(self):
        self.release()

    @staticmethod
    def find_and_restore_window(class_name: str = None, window_titles: list[str] = None) -> bool:
        """Find an existing application window and bring it to the foreground.

        Args:
            class_name: Window class name to search for (optional).
            window_titles: List of possible window titles to search for.

        Returns True if a window was found and activated.
        """
        if not window_titles:
            window_titles = []

        # Try each title until we find a match
        for title in window_titles:
            hwnd = user32.FindWindowW(class_name, title)
            if hwnd:
                # Restore if minimized
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, SW_RESTORE)

                # Bring to foreground
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)

                return True

        return False

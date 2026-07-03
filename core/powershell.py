import subprocess
import sys
import ctypes
import json
import re
from typing import Optional


class PowerShellExecutor:
    """Executes PowerShell commands and returns results."""

    @staticmethod
    def is_admin() -> bool:
        """Check if the application is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def request_admin():
        """Request UAC elevation to run as administrator."""
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception:
            sys.exit(1)

    @staticmethod
    def execute(command: str, timeout: int = 30) -> tuple[bool, str]:
        """
        Execute a PowerShell command and return success status and output.

        Args:
            command: PowerShell command to execute
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            full_command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", command
            ]

            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            output = result.stdout.strip()
            error = result.stderr.strip()

            # PowerShell sometimes returns 0 but has errors in stderr
            if error and "FullyQualifiedErrorId" in error:
                return False, error

            if result.returncode == 0:
                return True, output
            else:
                return False, error or output

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "PowerShell not found"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def execute_json(command: str, timeout: int = 30) -> tuple[bool, Optional[object]]:
        """
        Execute a PowerShell command that returns JSON output.

        Args:
            command: PowerShell command that outputs JSON
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (success: bool, data: dict/list/str or None)
        """
        success, output = PowerShellExecutor.execute(command, timeout)
        if not success or not output:
            return success, output if not success else None

        try:
            cleaned = output.strip()

            # Try JSON parse
            if cleaned.startswith(("[", "{")):
                data = json.loads(cleaned)
                return True, data

            # PowerShell @{key=value} format - convert to dict
            if cleaned.startswith("@{"):
                return True, PowerShellExecutor._parse_ps_hashtable(cleaned)

            # Plain text output (like a single value)
            return True, cleaned

        except json.JSONDecodeError:
            # Try to parse PowerShell objects
            if cleaned.startswith("@{"):
                return True, PowerShellExecutor._parse_ps_hashtable(cleaned)
            return True, cleaned

    @staticmethod
    def _parse_ps_hashtable(text: str) -> dict:
        """Parse a PowerShell @{key=value} hashtable string."""
        result = {}
        # Remove @{ and }
        inner = text.strip().lstrip("@{").rstrip("}")
        if not inner:
            return result

        # Split by "; " or "};"
        for part in re.split(r';\s*', inner):
            part = part.strip()
            if "=" in part:
                key, _, value = part.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value

        return result

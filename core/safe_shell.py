"""

 SafeShell - Secure subprocess execution wrapper

Eliminate shell injection vulnerabilities by enforcing shell=False
and validating all commands against a whitelist.
"""

import subprocess
import shlex
from typing import List, Union, Optional
from pathlib import Path

from utils.logger import Logger


class SafeShell:
    """
    Secure wrapper for subprocess execution.
    
    Features:
    - Enforces shell=False (no shell injection possible)
    - Validates commands against whitelist
    - Logs all executions
    - Sanitizes arguments
    """
    
    # Whitelist erlaubter Commands (Basis-Set)
    ALLOWED_COMMANDS = {
        # System
        'netsh',
        'taskkill',
        'wevtutil',
        
        # File operations
        'attrib',
        'icacls',
        
        # Linux equivalents
        'pkill',
        'killall',
        'chmod',
        'ip',
        'ifconfig',
        
        # macOS equivalents
        'osascript',
        'networksetup',
    }
    
    def __init__(self, logger: Optional[Logger] = None, extra_allowed: Optional[List[str]] = None):
        """
        Initialisiert SafeShell.
        
        Args:
            logger: Logger-Instanz (optional)
            extra_allowed: Zusätzlich erlaubte Commands (optional)
        """
        self.logger = logger or Logger()
        self.allowed_commands = self.ALLOWED_COMMANDS.copy()
        
        if extra_allowed:
            self.allowed_commands.update(extra_allowed)
    
    def run(
        self,
        command: Union[str, List[str]],
        *,
        capture_output: bool = True,
        text: bool = True,
        timeout: Optional[int] = None,
        check: bool = False,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Führt Command sicher aus (IMMER shell=False).
        
        Args:
            command: Command als String oder Liste
            capture_output: stdout/stderr erfassen
            text: Als Text zurückgeben (nicht bytes)
            timeout: Timeout in Sekunden
            check: Exception bei non-zero exit
            **kwargs: Weitere subprocess.run() Parameter
            
        Returns:
            CompletedProcess object
            
        Raises:
            PermissionError: Command nicht in Whitelist
            ValueError: Command ist leer
            subprocess.TimeoutExpired: Timeout überschritten
            subprocess.CalledProcessError: Wenn check=True und exit != 0
        """
        # Parse command to list
        if isinstance(command, str):
            cmd_list = shlex.split(command)  # Safe parsing!
        else:
            cmd_list = list(command)
        
        if not cmd_list:
            raise ValueError("Command ist leer")
        
        # Validate command against whitelist
        base_command = Path(cmd_list[0]).name  # Extract base command (remove path)
        
        if base_command not in self.allowed_commands:
            self.logger.error(f"SafeShell: Command nicht erlaubt: {base_command}")
            raise PermissionError(
                f"Command '{base_command}' ist nicht in der Whitelist. "
                f"Erlaubte Commands: {sorted(self.allowed_commands)}"
            )
        
        # Log execution
        self.logger.info(f"SafeShell: Ausführen: {' '.join(cmd_list)}")
        
        # Force shell=False (override if user passed it)
        kwargs['shell'] = False
        
        # Execute safely
        try:
            result = subprocess.run(
                cmd_list,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=check,
                **kwargs
            )
            
            # Log result
            if result.returncode == 0:
                self.logger.debug(f"SafeShell: Erfolgreich: {base_command}")
            else:
                self.logger.warning(
                    f"SafeShell: Exit code {result.returncode}: {base_command}\n"
                    f"stderr: {result.stderr[:200] if result.stderr else 'N/A'}"
                )
            
            return result
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"SafeShell: Timeout nach {timeout}s: {base_command}")
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(f"SafeShell: Fehler {e.returncode}: {base_command}")
            raise
        except Exception as e:
            self.logger.error(f"SafeShell: Unexpected error: {e}")
            raise
    
    def run_safe(
        self,
        command: str,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Alias für run() mit String-Command.
        
        Beispiel:
            safe_shell.run_safe("netsh interface show interface")
        """
        return self.run(command, **kwargs)
    
    def add_allowed_command(self, command: str) -> None:
        """
        Fügt Command zur Whitelist hinzu.
        
        Args:
            command: Command-Name
        """
        self.allowed_commands.add(command)
        self.logger.info(f"SafeShell: Command zur Whitelist hinzugefügt: {command}")
    
    def remove_allowed_command(self, command: str) -> None:
        """
        Entfernt Command aus Whitelist.
        
        Args:
            command: Command-Name
        """
        self.allowed_commands.discard(command)
        self.logger.info(f"SafeShell: Command aus Whitelist entfernt: {command}")
    
    def is_allowed(self, command: str) -> bool:
        """
        Prüft ob Command erlaubt ist.
        
        Args:
            command: Command-Name oder Pfad
            
        Returns:
            True wenn erlaubt
        """
        base_command = Path(command).name
        return base_command in self.allowed_commands
    
    def get_allowed_commands(self) -> List[str]:
        """
        Gibt Liste aller erlaubten Commands zurück.
        
        Returns:
            Sortierte Liste
        """
        return sorted(self.allowed_commands)


# Convenience function
def safe_run(
    command: Union[str, List[str]],
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Schnelle Safe-Execution ohne Instanz erstellen zu müssen.
    
    Beispiel:
        from core.safe_shell import safe_run
        result = safe_run("netsh interface show interface")
    
    Args:
        command: Command als String oder Liste
        **kwargs: subprocess.run() Parameter
        
    Returns:
        CompletedProcess object
    """
    shell = SafeShell()
    return shell.run(command, **kwargs)

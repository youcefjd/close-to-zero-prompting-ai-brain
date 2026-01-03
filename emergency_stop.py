"""Emergency Stop: Break-glass mechanism for halting agent execution.

This module provides a way to gracefully stop agent execution without
killing the process, allowing for safe shutdown and cleanup.
"""

import signal
import threading
import sys
from typing import Optional
from pathlib import Path
import json
from datetime import datetime


class EmergencyStop:
    """Singleton emergency stop mechanism for agent execution."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._stop_flag = threading.Event()
        self._reason = None
        self._stop_file = Path(".emergency_stop")
        self._original_handlers = {}
        self._setup_signal_handlers()
        self._check_stop_file()
        self._initialized = True
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for SIGINT and SIGTERM."""
        def signal_handler(sig, frame):
            signal_name = signal.Signals(sig).name
            print(f"\n⚠️  EMERGENCY STOP ACTIVATED ({signal_name})")
            self.stop(reason=f"Signal received: {signal_name}")
            sys.exit(130 if sig == signal.SIGINT else 143)
        
        # Save original handlers
        self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, signal_handler)
        self._original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, signal_handler)
    
    def _check_stop_file(self):
        """Check for stop file (created by CLI command)."""
        if self._stop_file.exists():
            try:
                with open(self._stop_file, 'r') as f:
                    data = json.load(f)
                    self._reason = data.get("reason", "Stop file detected")
                    self._stop_flag.set()
                    print(f"⚠️  EMERGENCY STOP ACTIVATED: {self._reason}")
            except Exception as e:
                print(f"Warning: Could not read stop file: {e}")
    
    def stop(self, reason: Optional[str] = None):
        """Activate emergency stop.
        
        Args:
            reason: Optional reason for stopping
        """
        self._reason = reason or "Emergency stop activated"
        self._stop_flag.set()
        
        # Create stop file for persistence across process restarts
        try:
            with open(self._stop_file, 'w') as f:
                json.dump({
                    "stopped": True,
                    "reason": self._reason,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write stop file: {e}")
    
    def reset(self):
        """Reset emergency stop (clear flag and stop file)."""
        self._stop_flag.clear()
        self._reason = None
        
        # Remove stop file
        if self._stop_file.exists():
            try:
                self._stop_file.unlink()
            except Exception as e:
                print(f"Warning: Could not remove stop file: {e}")
    
    def is_stopped(self) -> bool:
        """Check if emergency stop is activated.
        
        Returns:
            True if stopped, False otherwise
        """
        # Check both flag and file
        if self._stop_file.exists():
            if not self._stop_flag.is_set():
                # File exists but flag not set - sync them
                self._check_stop_file()
        
        return self._stop_flag.is_set()
    
    def get_reason(self) -> Optional[str]:
        """Get reason for emergency stop.
        
        Returns:
            Reason string or None if not stopped
        """
        return self._reason
    
    def check_and_raise(self):
        """Check if stopped and raise exception if so.
        
        Raises:
            EmergencyStopException: If emergency stop is activated
        """
        if self.is_stopped():
            raise EmergencyStopException(self._reason or "Emergency stop activated")


class EmergencyStopException(Exception):
    """Exception raised when emergency stop is activated."""
    
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Emergency stop: {reason}")


# Global instance getter
def get_emergency_stop() -> EmergencyStop:
    """Get global emergency stop instance."""
    return EmergencyStop()


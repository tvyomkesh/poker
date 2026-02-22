"""Action logging utility for the poker game."""

from typing import List, Callable, Optional
from datetime import datetime


class ActionLogger:
    """Logs game actions and provides them for display."""

    def __init__(self, max_entries: int = 100,
                 on_log: Optional[Callable[[str], None]] = None):
        """
        Initialize the action logger.

        Args:
            max_entries: Maximum log entries to keep
            on_log: Callback function when new entry is logged
        """
        self.entries: List[str] = []
        self.max_entries = max_entries
        self.on_log = on_log

    def log(self, message: str):
        """
        Log a new action.

        Args:
            message: The message to log
        """
        self.entries.append(message)

        # Trim old entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        # Callback
        if self.on_log:
            self.on_log(message)

    def get_recent(self, count: int = 5) -> List[str]:
        """
        Get the most recent log entries.

        Args:
            count: Number of entries to return

        Returns:
            List of recent log messages
        """
        return self.entries[-count:]

    def clear(self):
        """Clear all log entries."""
        self.entries = []

    def __len__(self) -> int:
        """Number of log entries."""
        return len(self.entries)

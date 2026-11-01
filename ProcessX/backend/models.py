"""Plain data objects shared by every scheduling module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Process:
    """One process to be scheduled.

    All times are whole numbers of "time units".
    ``priority``: a SMALLER number means a HIGHER priority (1 is the most urgent).
    """

    id: str
    arrival_time: int
    burst_time: int
    priority: int = 1

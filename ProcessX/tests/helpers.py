"""Shared helpers for the ProcessX tests (works with unittest and pytest)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models import Process                      # noqa: E402
from backend.utils.metrics import compute_metrics       # noqa: E402

# The dataset from the project brief: (id, arrival, burst, priority)
SAMPLE = [
    Process("P1", 0, 5, 2),
    Process("P2", 1, 3, 1),
    Process("P3", 2, 8, 3),
    Process("P4", 3, 2, 2),
]


def procs(*rows):
    """procs(("A", 0, 5, 1), ...) -> list of Process"""
    return [Process(*row) for row in rows]


def blocks(segments):
    """Gantt segments -> [(label, start, end)] with 'IDLE' for idle blocks."""
    return [(s["process_id"] or "IDLE", s["start"], s["end"]) for s in segments]


def analyse(processes, segments):
    """Return (per-process dict keyed by id, summary dict)."""
    result = compute_metrics(processes, segments)
    return {row["id"]: row for row in result["processes"]}, result["summary"]

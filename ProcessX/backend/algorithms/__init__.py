"""Registry of all scheduling algorithms.

Every algorithm lives in its own module and exposes ``schedule(processes, ...)``
which returns a list of Gantt segments (including IDLE segments).
"""

from . import fcfs, priority, round_robin, sjf, srtf

# Order matters: it is the order used on the comparison screen.
ALGORITHMS = {
    "FCFS": {
        "name": "First Come First Serve",
        "preemptive": False,
        "uses_quantum": False,
        "schedule": fcfs.schedule,
    },
    "SJF": {
        "name": "Shortest Job First (Non-Preemptive)",
        "preemptive": False,
        "uses_quantum": False,
        "schedule": sjf.schedule,
    },
    "SRTF": {
        "name": "Shortest Remaining Time First (Preemptive)",
        "preemptive": True,
        "uses_quantum": False,
        "schedule": srtf.schedule,
    },
    "RR": {
        "name": "Round Robin",
        "preemptive": True,
        "uses_quantum": True,
        "schedule": round_robin.schedule,
    },
    "PRIORITY": {
        "name": "Priority Scheduling (Non-Preemptive)",
        "preemptive": False,
        "uses_quantum": False,
        "schedule": priority.schedule,
    },
}

__all__ = ["ALGORITHMS", "fcfs", "sjf", "srtf", "round_robin", "priority"]

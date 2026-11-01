"""Glue between the REST API and the algorithm modules."""

from backend.algorithms import ALGORITHMS
from backend.utils.metrics import compute_metrics

# Metrics where a LOWER total is better. (CPU utilization is reported but is not
# ranked: every algorithm here is work-conserving, so it is identical.)
_RANKED = (
    ("avg_waiting_time", "total_waiting_time"),
    ("avg_turnaround_time", "total_turnaround_time"),
    ("avg_response_time", "total_response_time"),
)


def simulate(processes, algorithm, time_quantum=None):
    """Run one algorithm and return schedule + metrics as a JSON-ready dict."""
    info = ALGORITHMS[algorithm]
    if info["uses_quantum"]:
        segments = info["schedule"](processes, time_quantum)
    else:
        segments = info["schedule"](processes)
    result = compute_metrics(processes, segments)
    return {
        "algorithm": algorithm,
        "algorithm_name": info["name"],
        "preemptive": info["preemptive"],
        "time_quantum": time_quantum if info["uses_quantum"] else None,
        "processes": result["processes"],
        "gantt": segments,
        "metrics": result["summary"],
    }


def compare_all(processes, time_quantum):
    """Run every algorithm on the same process set and find the best per metric."""
    results = [simulate(processes, key, time_quantum) for key in ALGORITHMS]

    best = {}
    for avg_key, total_key in _RANKED:
        lowest = min(r["metrics"][total_key] for r in results)
        winners = [r["algorithm"] for r in results if r["metrics"][total_key] == lowest]
        value = next(r["metrics"][avg_key] for r in results if r["algorithm"] == winners[0])
        best[avg_key] = {"algorithms": winners, "value": value}

    return {
        "time_quantum": time_quantum,
        "process_count": len(processes),
        "results": results,
        "best": best,
    }

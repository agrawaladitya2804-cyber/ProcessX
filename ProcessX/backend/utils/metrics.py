"""Performance metrics, computed from the Gantt segments an algorithm produced.

Definitions (AT = arrival time, BT = burst time):
    Completion Time (CT)  = time at which the process finishes its last burst
    Turnaround Time (TAT) = CT - AT
    Waiting Time (WT)     = TAT - BT
    Response Time (RT)    = (first time on the CPU) - AT

    Total Execution Time  = end of the last segment (the timeline starts at 0)
    CPU Busy Time         = sum of all burst times
    CPU Idle Time         = Total Execution Time - CPU Busy Time
    CPU Utilization (%)   = CPU Busy Time / Total Execution Time * 100

Because every number is derived from the SAME segment list that is drawn in the
Gantt chart, the table and the chart can never disagree with each other.
"""


class SchedulingError(RuntimeError):
    """Raised if an algorithm returns an impossible schedule (a bug safeguard)."""


def verify_schedule(processes, segments):
    """Sanity-check a schedule. Raises SchedulingError if it is impossible."""
    if not segments:
        raise SchedulingError("Schedule is empty")
    cursor = 0
    executed = {p.id: 0 for p in processes}
    arrival = {p.id: p.arrival_time for p in processes}
    for seg in segments:
        if seg["start"] != cursor or seg["end"] <= seg["start"]:
            raise SchedulingError(f"Gantt chart is not contiguous at time {cursor}")
        cursor = seg["end"]
        pid = seg["process_id"]
        if pid is None:
            continue
        if pid not in executed:
            raise SchedulingError(f"Unknown process {pid} in schedule")
        if seg["start"] < arrival[pid]:
            raise SchedulingError(f"{pid} ran before it arrived")
        executed[pid] += seg["end"] - seg["start"]
    for p in processes:
        if executed[p.id] != p.burst_time:
            raise SchedulingError(
                f"{p.id} received {executed[p.id]} units of CPU but needs {p.burst_time}"
            )


def compute_metrics(processes, segments):
    """Return ``{"processes": [...per process...], "summary": {...}}``."""
    verify_schedule(processes, segments)

    first_start, completion = {}, {}
    for seg in segments:
        pid = seg["process_id"]
        if pid is None:
            continue
        first_start.setdefault(pid, seg["start"])
        completion[pid] = seg["end"]

    rows = []
    for p in processes:                      # keep the user's input order
        ct = completion[p.id]
        tat = ct - p.arrival_time
        wt = tat - p.burst_time
        rt = first_start[p.id] - p.arrival_time
        rows.append({
            "id": p.id,
            "arrival_time": p.arrival_time,
            "burst_time": p.burst_time,
            "priority": p.priority,
            "start_time": first_start[p.id],
            "completion_time": ct,
            "turnaround_time": tat,
            "waiting_time": wt,
            "response_time": rt,
        })

    n = len(rows)
    total_wt = sum(r["waiting_time"] for r in rows)
    total_tat = sum(r["turnaround_time"] for r in rows)
    total_rt = sum(r["response_time"] for r in rows)
    total_time = segments[-1]["end"]
    busy = sum(p.burst_time for p in processes)

    summary = {
        "total_processes": n,
        "avg_waiting_time": round(total_wt / n, 2),
        "avg_turnaround_time": round(total_tat / n, 2),
        "avg_response_time": round(total_rt / n, 2),
        "cpu_utilization": round(busy / total_time * 100, 2),
        "total_execution_time": total_time,
        "cpu_busy_time": busy,
        "cpu_idle_time": total_time - busy,
        # Exact integer totals (used for tie-free "best algorithm" comparison).
        "total_waiting_time": total_wt,
        "total_turnaround_time": total_tat,
        "total_response_time": total_rt,
    }
    return {"processes": rows, "summary": summary}

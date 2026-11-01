"""Shortest Job First (SJF) - NON-preemptive.

Rule: whenever the CPU becomes free, pick the arrived process with the smallest
burst time and let it run to completion.
Tie-break (consistent): smaller burst -> earlier arrival -> earlier input order.
"""

from backend.utils.gantt import GanttBuilder


def schedule(processes):
    n = len(processes)
    done = [False] * n
    gantt = GanttBuilder()
    time = 0
    finished = 0
    while finished < n:
        ready = [i for i in range(n) if not done[i] and processes[i].arrival_time <= time]
        if not ready:
            # CPU idle: jump to the next arrival (the gap is recorded as IDLE)
            time = min(processes[i].arrival_time for i in range(n) if not done[i])
            continue
        i = min(ready, key=lambda k: (processes[k].burst_time, processes[k].arrival_time, k))
        p = processes[i]
        gantt.add(p.id, time, time + p.burst_time)
        time += p.burst_time
        done[i] = True
        finished += 1
    return gantt.segments

"""Shortest Remaining Time First (SRTF) - PREEMPTIVE version of SJF.

Rule: at every moment the CPU runs the arrived process with the least remaining
burst time. A newly arrived process with a shorter remaining time preempts the
running one.

Implementation note: the only event that can cause a preemption is a new
arrival, so the loop runs the chosen process until it finishes OR the next
process arrives, then decides again. This is exactly equivalent to deciding at
every single time unit, but faster.
Tie-break (consistent): smaller remaining time -> earlier arrival -> input order.
"""

from backend.utils.gantt import GanttBuilder


def schedule(processes):
    n = len(processes)
    remaining = [p.burst_time for p in processes]
    gantt = GanttBuilder()
    time = 0
    finished = 0
    while finished < n:
        ready = [i for i in range(n) if remaining[i] > 0 and processes[i].arrival_time <= time]
        future = [processes[i].arrival_time for i in range(n)
                  if remaining[i] > 0 and processes[i].arrival_time > time]
        if not ready:
            time = min(future)           # idle until the next arrival
            continue
        i = min(ready, key=lambda k: (remaining[k], processes[k].arrival_time, k))
        run_until = time + remaining[i]
        if future:
            run_until = min(run_until, min(future))   # a new arrival may preempt
        gantt.add(processes[i].id, time, run_until)
        remaining[i] -= run_until - time
        time = run_until
        if remaining[i] == 0:
            finished += 1
    return gantt.segments

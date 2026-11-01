"""Priority Scheduling - NON-preemptive.

PRIORITY CONVENTION: a SMALLER priority number means a HIGHER priority
(priority 1 is the most urgent). This is the convention used by most OS
textbooks and it is shown in the user interface.

Rule: whenever the CPU becomes free, pick the arrived process with the highest
priority (smallest number) and let it run to completion.
Tie-break (consistent): smaller priority number -> earlier arrival -> input order.
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
            time = min(processes[i].arrival_time for i in range(n) if not done[i])
            continue
        i = min(ready, key=lambda k: (processes[k].priority, processes[k].arrival_time, k))
        p = processes[i]
        gantt.add(p.id, time, time + p.burst_time)
        time += p.burst_time
        done[i] = True
        finished += 1
    return gantt.segments

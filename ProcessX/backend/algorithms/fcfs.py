"""First Come First Serve (FCFS) - non-preemptive.

Rule: processes run strictly in order of arrival. If two processes arrive at the
same time, the one entered first (input order) runs first.
"""

from backend.utils.gantt import GanttBuilder


def schedule(processes):
    order = sorted(range(len(processes)), key=lambda i: (processes[i].arrival_time, i))
    gantt = GanttBuilder()
    time = 0
    for i in order:
        p = processes[i]
        start = max(time, p.arrival_time)      # wait (idle) if it has not arrived yet
        time = start + p.burst_time
        gantt.add(p.id, start, time)
    return gantt.segments

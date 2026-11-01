"""Round Robin (RR) - preemptive, time-sliced.

Rules
* A FIFO ready queue is used. The process at the front runs for at most
  ``time_quantum`` units.
* If it still has work left it goes to the BACK of the queue.
* Standard textbook convention for simultaneous events: processes that arrive
  during a slice - or exactly when the slice ends - are placed in the queue
  BEFORE the pre-empted process is put back.
* Processes with the same arrival time enter the queue in input order.
* If a process runs two slices in a row (queue was otherwise empty) the two
  slices are shown as one continuous Gantt block.
"""

from collections import deque

from backend.utils.gantt import GanttBuilder


def schedule(processes, time_quantum):
    if isinstance(time_quantum, bool) or not isinstance(time_quantum, int) or time_quantum < 1:
        raise ValueError("time_quantum must be a whole number >= 1")

    n = len(processes)
    arrival_order = sorted(range(n), key=lambda i: (processes[i].arrival_time, i))
    remaining = [p.burst_time for p in processes]
    queue = deque()
    gantt = GanttBuilder()
    next_arrival = 0          # index into arrival_order
    time = 0
    finished = 0

    def admit_arrivals(up_to):
        nonlocal next_arrival
        while next_arrival < n and processes[arrival_order[next_arrival]].arrival_time <= up_to:
            queue.append(arrival_order[next_arrival])
            next_arrival += 1

    while finished < n:
        admit_arrivals(time)
        if not queue:
            # Nobody is ready: CPU idles until the next process arrives.
            time = processes[arrival_order[next_arrival]].arrival_time
            continue
        i = queue.popleft()
        run = min(time_quantum, remaining[i])
        gantt.add(processes[i].id, time, time + run)
        time += run
        remaining[i] -= run
        admit_arrivals(time)              # newcomers go in BEFORE the pre-empted process
        if remaining[i] > 0:
            queue.append(i)
        else:
            finished += 1
    return gantt.segments

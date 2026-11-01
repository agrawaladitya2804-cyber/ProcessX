# ProcessX - Viva Questions and Answers

### Q1. What is the difference between preemptive and non-preemptive scheduling?
**Non-preemptive**: once a process gets the CPU it keeps it until it finishes (FCFS, SJF, Priority in ProcessX).
**Preemptive**: the OS can take the CPU away, for example when a time slice ends or a shorter job arrives (SRTF, Round Robin).

### Q2. Define turnaround, waiting and response time.
* Turnaround time = completion time - arrival time.
* Waiting time = turnaround time - burst time (time spent in the ready queue).
* Response time = first time on the CPU - arrival time.

For non-preemptive algorithms, waiting time and response time are equal. For preemptive ones the response time can be much smaller.

### Q3. What is the convoy effect?
In FCFS a long job at the front makes all short jobs behind it wait. In the sample data, FCFS gives P4 (burst 2) a waiting time of 13.

### Q4. Why does SJF/SRTF give a low average waiting time?
Running short jobs first lets many processes finish quickly, so fewer processes wait behind long ones. For the sample data: FCFS 5.75, SJF 4.00, SRTF 3.50. The drawback is that burst times must be known in advance and long jobs can starve.

### Q5. What is starvation and how is it solved?
Starvation is indefinite waiting, for example a low-priority (or long) process that is always overtaken by new arrivals. The standard fix is **aging**: gradually raise the priority of processes that have waited a long time.

### Q6. How does the time quantum affect Round Robin?
* Very large quantum: Round Robin behaves like FCFS.
* Very small quantum: response time is good, but real systems waste time on context switches.
* In ProcessX, compare quantum 1, 2 and 5 on the same data to see the effect.

### Q7. In Priority scheduling, does 1 mean high or low priority?
It depends on the convention. ProcessX uses the common textbook convention: a **smaller number means higher priority**.

### Q8. How is CPU utilization calculated?
Busy time / total execution time x 100. If the CPU waits for the first process to arrive, that waiting is idle time and utilization drops below 100%.

### Q9. How do you break ties in ProcessX?
Shorter burst (or higher priority) first, then earlier arrival, then the order in which the processes were entered. Round Robin queues processes that arrive at the same time in input order.

### Q10. Where are the calculations done?
All in Python (`backend/algorithms` and `backend/utils/metrics.py`). JavaScript only sends the input and draws the results.

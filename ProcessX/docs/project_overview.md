# Project Overview - ProcessX 2.0

## Objective
ProcessX shows, step by step, how an operating system decides which process gets the CPU.
It is built for teaching: you enter processes, choose an algorithm and see the Gantt chart
and the performance numbers.

## Key features
1. **Process input** - add, remove and clear processes with arrival time, burst time and
   priority. Inputs are validated in the browser and again on the server.
2. **Five scheduling algorithms** (each in its own Python module):
   - First Come First Serve (FCFS)
   - Shortest Job First, non-preemptive (SJF)
   - Shortest Remaining Time First, preemptive (SRTF)
   - Round Robin with a configurable time quantum (RR)
   - Priority scheduling, non-preemptive (smaller number = higher priority)
3. **Gantt chart** - coloured blocks per process, start/end times, idle periods, and
   preemptive algorithms show a process in several blocks.
4. **Metrics** - completion, turnaround, waiting and response time per process, plus averages,
   CPU utilization, total execution time and idle time.
5. **Compare all algorithms** - the same process set run through all five algorithms with
   tables and Chart.js bar charts.

## Architecture
```
Browser (HTML/CSS/JS)  --JSON-->  Flask REST API (app.py)  -->  backend/algorithms/*.py
                       <--JSON--                            -->  backend/utils/metrics.py
```
The browser only draws. Every scheduling decision and every number comes from Python.

## What changed from ProcessX 1.0
* The C++ engine (CMake / MinGW / `httplib.h`) was replaced by Python + Flask.
* SRTF was added (version 1.0 had four algorithms).
* Response time and idle time are now calculated.
* The dark theme was replaced with a light dashboard.
* Automated tests were added.

"""Independent cross-check.

A second, deliberately naive simulator decides "who runs?" for EVERY single time
unit (no jumping ahead, no merging). Its result must match each real algorithm
on thousands of random process sets, and the schedules must obey basic laws.
"""

import random
import unittest
from collections import deque

from helpers import procs
from backend.algorithms import ALGORITHMS
from backend.utils.metrics import compute_metrics
from backend.simulator import simulate


def compress(timeline):
    """[pid|None per unit] -> [(label, start, end)] with adjacent equal units merged."""
    out = []
    for t, pid in enumerate(timeline):
        label = pid if pid is not None else "IDLE"
        if out and out[-1][0] == label:
            out[-1] = (label, out[-1][1], t + 1)
        else:
            out.append((label, t, t + 1))
    return out


def reference_tick(processes, algo):
    """Unit-by-unit simulation of FCFS / SJF / SRTF / PRIORITY."""
    keys = {
        "FCFS": lambda i, rem: (processes[i].arrival_time, i),
        "SJF": lambda i, rem: (processes[i].burst_time, processes[i].arrival_time, i),
        "PRIORITY": lambda i, rem: (processes[i].priority, processes[i].arrival_time, i),
        "SRTF": lambda i, rem: (rem[i], processes[i].arrival_time, i),
    }
    key = keys[algo]
    n = len(processes)
    rem = [p.burst_time for p in processes]
    running, timeline, t = None, [], 0
    while any(rem):
        ready = [i for i in range(n) if rem[i] > 0 and processes[i].arrival_time <= t]
        if algo == "SRTF" or running is None or rem[running] == 0:
            running = min(ready, key=lambda i: key(i, rem)) if ready else None
        timeline.append(processes[running].id if running is not None else None)
        if running is not None:
            rem[running] -= 1
        t += 1
    return compress(timeline)


def reference_rr(processes, quantum):
    n = len(processes)
    rem = [p.burst_time for p in processes]
    admitted = [False] * n
    queue, running, used, t, timeline = deque(), None, 0, 0, []

    def admit(now):
        for i in sorted(range(n), key=lambda k: (processes[k].arrival_time, k)):
            if not admitted[i] and processes[i].arrival_time <= now:
                admitted[i] = True
                queue.append(i)

    while any(rem):
        if running is None:
            admit(t)
            if queue:
                running, used = queue.popleft(), 0
        if running is None:
            timeline.append(None)
            t += 1
            continue
        timeline.append(processes[running].id)
        rem[running] -= 1
        used += 1
        t += 1
        admit(t)
        if rem[running] == 0:
            running = None
        elif used == quantum:
            queue.append(running)
            running = None
    return compress(timeline)


def random_processes(rng):
    n = rng.randint(1, 8)
    return procs(*[(f"P{i + 1}", rng.randint(0, 14), rng.randint(1, 9), rng.randint(1, 4))
                   for i in range(n)])


def as_blocks(segments):
    return [(s["process_id"] or "IDLE", s["start"], s["end"]) for s in segments]


class CrossCheckTests(unittest.TestCase):
    CASES = 1500

    def test_non_round_robin_algorithms_match_reference(self):
        rng = random.Random(2024)
        for _ in range(self.CASES):
            p = random_processes(rng)
            for algo in ("FCFS", "SJF", "SRTF", "PRIORITY"):
                actual = as_blocks(ALGORITHMS[algo]["schedule"](p))
                self.assertEqual(actual, reference_tick(p, algo), f"{algo}: {p}")

    def test_round_robin_matches_reference(self):
        rng = random.Random(7)
        for _ in range(self.CASES):
            p, q = random_processes(rng), rng.randint(1, 5)
            actual = as_blocks(ALGORITHMS["RR"]["schedule"](p, q))
            self.assertEqual(actual, reference_rr(p, q), f"RR q={q}: {p}")

    def test_laws_that_must_hold_for_every_result(self):
        rng = random.Random(99)
        for _ in range(400):
            p = random_processes(rng)
            makespans = set()
            for algo in ALGORITHMS:
                out = simulate(p, algo, rng.randint(1, 5))
                m = out["metrics"]
                makespans.add(m["total_execution_time"])
                self.assertEqual(m["cpu_busy_time"], sum(x.burst_time for x in p))
                for row in out["processes"]:
                    self.assertEqual(row["turnaround_time"], row["completion_time"] - row["arrival_time"])
                    self.assertEqual(row["waiting_time"], row["turnaround_time"] - row["burst_time"])
                    self.assertGreaterEqual(row["waiting_time"], 0)
                    self.assertLessEqual(row["response_time"], row["waiting_time"])
                    self.assertGreaterEqual(row["response_time"], 0)
                self.assertTrue(0 < m["cpu_utilization"] <= 100)
            # All five algorithms never idle while work is available -> same finish time.
            self.assertEqual(len(makespans), 1, p)

    def test_no_infinite_loop_on_extreme_input(self):
        p = procs(("A", 10000, 1000, 1), ("B", 0, 1000, 1))
        for algo in ALGORITHMS:
            out = simulate(p, algo, 1)
            self.assertEqual(out["metrics"]["total_execution_time"], 11000)


if __name__ == "__main__":
    unittest.main()

import unittest

from helpers import SAMPLE, analyse, blocks, procs
from backend.algorithms import priority


class PriorityTests(unittest.TestCase):
    def test_single_process(self):
        self.assertEqual(blocks(priority.schedule(procs(("P1", 0, 2, 7)))), [("P1", 0, 2)])

    def test_sample_dataset_hand_verified(self):
        seg = priority.schedule(SAMPLE)
        # At t=5: P2 (priority 1) < P4 (priority 2) < P3 (priority 3)
        self.assertEqual(blocks(seg), [("P1", 0, 5), ("P2", 5, 8), ("P4", 8, 10), ("P3", 10, 18)])
        rows, s = analyse(SAMPLE, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3", "P4")], [5, 8, 18, 10])
        self.assertEqual([rows[i]["turnaround_time"] for i in ("P1", "P2", "P3", "P4")], [5, 7, 16, 7])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3", "P4")], [0, 4, 8, 5])
        self.assertEqual(s["avg_waiting_time"], 4.25)      # 17 / 4
        self.assertEqual(s["avg_turnaround_time"], 8.75)   # 35 / 4

    def test_smaller_number_means_higher_priority(self):
        p = procs(("low", 0, 1, 3), ("high", 0, 1, 1), ("mid", 0, 1, 2))
        self.assertEqual([b[0] for b in blocks(priority.schedule(p))], ["high", "mid", "low"])

    def test_is_non_preemptive(self):
        p = procs(("P1", 0, 10, 5), ("P2", 1, 1, 1))
        self.assertEqual(blocks(priority.schedule(p)), [("P1", 0, 10), ("P2", 10, 11)])

    def test_tie_same_priority_same_arrival_uses_input_order(self):
        p = procs(("P1", 0, 2, 5), ("P2", 1, 3, 2), ("P3", 1, 1, 2))
        self.assertEqual(blocks(priority.schedule(p)), [("P1", 0, 2), ("P2", 2, 5), ("P3", 5, 6)])

    def test_tie_same_priority_prefers_earlier_arrival(self):
        p = procs(("F", 0, 3, 9), ("B", 2, 1, 2), ("A", 1, 1, 2))
        self.assertEqual(blocks(priority.schedule(p)), [("F", 0, 3), ("A", 3, 4), ("B", 4, 5)])

    def test_all_equal_priorities_degenerates_to_fcfs(self):
        p = procs(("A", 0, 2, 1), ("B", 1, 2, 1), ("C", 2, 2, 1))
        self.assertEqual([b[0] for b in blocks(priority.schedule(p))], ["A", "B", "C"])

    def test_idle_time(self):
        p = procs(("P1", 4, 2, 1))
        seg = priority.schedule(p)
        self.assertEqual(blocks(seg), [("IDLE", 0, 4), ("P1", 4, 6)])
        _, s = analyse(p, seg)
        self.assertEqual(s["cpu_utilization"], 33.33)


if __name__ == "__main__":
    unittest.main()

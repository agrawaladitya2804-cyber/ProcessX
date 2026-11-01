import unittest

from helpers import SAMPLE, analyse, blocks, procs
from backend.algorithms import sjf


class SJFTests(unittest.TestCase):
    def test_single_process(self):
        self.assertEqual(blocks(sjf.schedule(procs(("P1", 0, 3, 1)))), [("P1", 0, 3)])

    def test_sample_dataset_hand_verified(self):
        seg = sjf.schedule(SAMPLE)
        # P1 runs alone first; at t=5 the shortest of {P2:3, P3:8, P4:2} is P4.
        self.assertEqual(blocks(seg), [("P1", 0, 5), ("P4", 5, 7), ("P2", 7, 10), ("P3", 10, 18)])
        rows, s = analyse(SAMPLE, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3", "P4")], [5, 10, 18, 7])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3", "P4")], [0, 6, 8, 2])
        self.assertEqual(s["avg_waiting_time"], 4.0)       # 16 / 4
        self.assertEqual(s["avg_turnaround_time"], 8.5)    # 34 / 4

    def test_is_non_preemptive(self):
        p = procs(("long", 0, 10, 1), ("tiny", 1, 1, 1))
        self.assertEqual(blocks(sjf.schedule(p)), [("long", 0, 10), ("tiny", 10, 11)])

    def test_tie_on_burst_prefers_earlier_arrival(self):
        p = procs(("F", 0, 4, 1), ("late", 2, 3, 1), ("early", 1, 3, 1))
        self.assertEqual(blocks(sjf.schedule(p)), [("F", 0, 4), ("early", 4, 7), ("late", 7, 10)])

    def test_tie_on_burst_and_arrival_prefers_input_order(self):
        p = procs(("F", 0, 3, 1), ("B", 1, 2, 1), ("A", 1, 2, 1))
        self.assertEqual(blocks(sjf.schedule(p)), [("F", 0, 3), ("B", 3, 5), ("A", 5, 7)])

    def test_all_same_arrival(self):
        p = procs(("A", 0, 6, 1), ("B", 0, 2, 1), ("C", 0, 4, 1))
        self.assertEqual(blocks(sjf.schedule(p)), [("B", 0, 2), ("C", 2, 6), ("A", 6, 12)])

    def test_idle_gap(self):
        p = procs(("P1", 0, 2, 1), ("P2", 6, 1, 1))
        seg = sjf.schedule(p)
        self.assertEqual(blocks(seg), [("P1", 0, 2), ("IDLE", 2, 6), ("P2", 6, 7)])
        _, s = analyse(p, seg)
        self.assertEqual(s["cpu_idle_time"], 4)


if __name__ == "__main__":
    unittest.main()

import unittest

from helpers import SAMPLE, analyse, blocks, procs
from backend.algorithms import srtf


class SRTFTests(unittest.TestCase):
    def test_single_process(self):
        self.assertEqual(blocks(srtf.schedule(procs(("P1", 0, 7, 1)))), [("P1", 0, 7)])

    def test_sample_dataset_hand_verified(self):
        seg = srtf.schedule(SAMPLE)
        self.assertEqual(blocks(seg), [("P1", 0, 1), ("P2", 1, 4), ("P4", 4, 6),
                                       ("P1", 6, 10), ("P3", 10, 18)])
        rows, s = analyse(SAMPLE, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3", "P4")], [10, 4, 18, 6])
        self.assertEqual([rows[i]["turnaround_time"] for i in ("P1", "P2", "P3", "P4")], [10, 3, 16, 3])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3", "P4")], [5, 0, 8, 1])
        self.assertEqual([rows[i]["response_time"] for i in ("P1", "P2", "P3", "P4")], [0, 0, 8, 1])
        self.assertEqual(s["avg_waiting_time"], 3.5)       # 14 / 4
        self.assertEqual(s["avg_turnaround_time"], 8.0)    # 32 / 4
        self.assertEqual(s["avg_response_time"], 2.25)     # 9 / 4

    def test_preemption_and_process_appearing_multiple_times(self):
        p = procs(("P1", 0, 8, 1), ("P2", 1, 4, 1), ("P3", 2, 1, 1))
        seg = srtf.schedule(p)
        self.assertEqual(blocks(seg), [("P1", 0, 1), ("P2", 1, 2), ("P3", 2, 3),
                                       ("P2", 3, 6), ("P1", 6, 13)])
        rows, s = analyse(p, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3")], [13, 6, 3])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3")], [5, 1, 0])
        self.assertEqual(s["avg_waiting_time"], 2.0)

    def test_equal_remaining_time_does_not_preempt(self):
        # At t=1: P1 has 3 left, P2 needs 3 -> tie, earlier arrival (P1) keeps the CPU.
        p = procs(("P1", 0, 4, 1), ("P2", 1, 3, 1))
        self.assertEqual(blocks(srtf.schedule(p)), [("P1", 0, 4), ("P2", 4, 7)])

    def test_longer_arrival_does_not_preempt(self):
        p = procs(("P1", 0, 3, 1), ("P2", 1, 9, 1))
        self.assertEqual(blocks(srtf.schedule(p)), [("P1", 0, 3), ("P2", 3, 12)])

    def test_same_arrival_time(self):
        p = procs(("A", 0, 3, 1), ("B", 0, 1, 1), ("C", 0, 2, 1))
        self.assertEqual(blocks(srtf.schedule(p)), [("B", 0, 1), ("C", 1, 3), ("A", 3, 6)])

    def test_idle_time_handled(self):
        p = procs(("P1", 3, 2, 1), ("P2", 10, 1, 1))
        seg = srtf.schedule(p)
        self.assertEqual(blocks(seg), [("IDLE", 0, 3), ("P1", 3, 5), ("IDLE", 5, 10), ("P2", 10, 11)])
        _, s = analyse(p, seg)
        self.assertEqual((s["total_execution_time"], s["cpu_idle_time"]), (11, 8))


if __name__ == "__main__":
    unittest.main()

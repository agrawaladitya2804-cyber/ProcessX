import unittest

from helpers import SAMPLE, analyse, blocks, procs
from backend.algorithms import fcfs


class FCFSTests(unittest.TestCase):
    def test_single_process(self):
        p = procs(("P1", 0, 4, 1))
        seg = fcfs.schedule(p)
        self.assertEqual(blocks(seg), [("P1", 0, 4)])
        rows, s = analyse(p, seg)
        self.assertEqual((rows["P1"]["completion_time"], rows["P1"]["waiting_time"]), (4, 0))
        self.assertEqual(s["cpu_utilization"], 100.0)

    def test_sample_dataset_hand_verified(self):
        seg = fcfs.schedule(SAMPLE)
        self.assertEqual(blocks(seg), [("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 16), ("P4", 16, 18)])
        rows, s = analyse(SAMPLE, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3", "P4")], [5, 8, 16, 18])
        self.assertEqual([rows[i]["turnaround_time"] for i in ("P1", "P2", "P3", "P4")], [5, 7, 14, 15])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3", "P4")], [0, 4, 6, 13])
        self.assertEqual(s["avg_waiting_time"], 5.75)      # 23 / 4
        self.assertEqual(s["avg_turnaround_time"], 10.25)  # 41 / 4
        self.assertEqual(s["avg_response_time"], 5.75)     # non-preemptive: RT == WT

    def test_same_arrival_uses_input_order(self):
        p = procs(("B", 0, 2, 1), ("A", 0, 3, 1))
        self.assertEqual(blocks(fcfs.schedule(p)), [("B", 0, 2), ("A", 2, 5)])

    def test_unsorted_input_is_ordered_by_arrival(self):
        p = procs(("late", 4, 1, 1), ("early", 0, 2, 1))
        self.assertEqual(blocks(fcfs.schedule(p)),
                         [("early", 0, 2), ("IDLE", 2, 4), ("late", 4, 5)])

    def test_idle_time_at_start_and_between(self):
        p = procs(("P1", 2, 3, 1), ("P2", 10, 2, 1))
        seg = fcfs.schedule(p)
        self.assertEqual(blocks(seg), [("IDLE", 0, 2), ("P1", 2, 5), ("IDLE", 5, 10), ("P2", 10, 12)])
        rows, s = analyse(p, seg)
        self.assertEqual(s["total_execution_time"], 12)
        self.assertEqual(s["cpu_idle_time"], 7)
        self.assertEqual(s["cpu_utilization"], 41.67)      # 5 / 12
        self.assertEqual(rows["P2"]["waiting_time"], 0)

    def test_idle_segments_are_flagged(self):
        seg = fcfs.schedule(procs(("P1", 3, 1, 1)))
        self.assertTrue(seg[0]["idle"] and seg[0]["process_id"] is None)
        self.assertFalse(seg[1]["idle"])


if __name__ == "__main__":
    unittest.main()

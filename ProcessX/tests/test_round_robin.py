import unittest

from helpers import SAMPLE, analyse, blocks, procs
from backend.algorithms import fcfs, round_robin


class RoundRobinTests(unittest.TestCase):
    def test_single_process_slices_are_merged(self):
        seg = round_robin.schedule(procs(("P1", 0, 5, 1)), 2)
        self.assertEqual(blocks(seg), [("P1", 0, 5)])

    def test_sample_dataset_hand_verified(self):
        seg = round_robin.schedule(SAMPLE, 2)
        self.assertEqual(blocks(seg), [
            ("P1", 0, 2), ("P2", 2, 4), ("P3", 4, 6), ("P1", 6, 8), ("P4", 8, 10),
            ("P2", 10, 11), ("P3", 11, 13), ("P1", 13, 14), ("P3", 14, 18)])
        rows, s = analyse(SAMPLE, seg)
        self.assertEqual([rows[i]["completion_time"] for i in ("P1", "P2", "P3", "P4")], [14, 11, 18, 10])
        self.assertEqual([rows[i]["turnaround_time"] for i in ("P1", "P2", "P3", "P4")], [14, 10, 16, 7])
        self.assertEqual([rows[i]["waiting_time"] for i in ("P1", "P2", "P3", "P4")], [9, 7, 8, 5])
        self.assertEqual([rows[i]["response_time"] for i in ("P1", "P2", "P3", "P4")], [0, 1, 2, 5])
        self.assertEqual(s["avg_waiting_time"], 7.25)      # 29 / 4
        self.assertEqual(s["avg_turnaround_time"], 11.75)  # 47 / 4
        self.assertEqual(s["avg_response_time"], 2.0)      # 8 / 4

    def test_queue_rotation(self):
        p = procs(("A", 0, 5, 1), ("B", 0, 3, 1), ("C", 0, 1, 1))
        seg = round_robin.schedule(p, 2)
        self.assertEqual(blocks(seg), [("A", 0, 2), ("B", 2, 4), ("C", 4, 5),
                                       ("A", 5, 7), ("B", 7, 8), ("A", 8, 9)])
        rows, _ = analyse(p, seg)
        self.assertEqual([rows[i]["completion_time"] for i in "ABC"], [9, 8, 5])
        self.assertEqual([rows[i]["waiting_time"] for i in "ABC"], [4, 5, 4])
        self.assertEqual([rows[i]["response_time"] for i in "ABC"], [0, 2, 4])

    def test_arrival_at_slice_end_enters_queue_before_preempted_process(self):
        p = procs(("A", 0, 4, 1), ("B", 2, 2, 1))
        self.assertEqual(blocks(round_robin.schedule(p, 2)),
                         [("A", 0, 2), ("B", 2, 4), ("A", 4, 6)])

    def test_arrival_during_slice_enters_queue_before_preempted_process(self):
        p = procs(("A", 0, 4, 1), ("B", 1, 1, 1))
        self.assertEqual(blocks(round_robin.schedule(p, 2)),
                         [("A", 0, 2), ("B", 2, 3), ("A", 3, 5)])

    def test_large_quantum_behaves_like_fcfs(self):
        rr = blocks(round_robin.schedule(SAMPLE, 100))
        self.assertEqual(rr, blocks(fcfs.schedule(SAMPLE)))

    def test_quantum_one(self):
        p = procs(("A", 0, 2, 1), ("B", 0, 2, 1))
        self.assertEqual(blocks(round_robin.schedule(p, 1)),
                         [("A", 0, 1), ("B", 1, 2), ("A", 2, 3), ("B", 3, 4)])

    def test_idle_time_at_start_and_middle(self):
        p = procs(("P1", 3, 2, 1), ("P2", 8, 2, 1))
        seg = round_robin.schedule(p, 2)
        self.assertEqual(blocks(seg), [("IDLE", 0, 3), ("P1", 3, 5), ("IDLE", 5, 8), ("P2", 8, 10)])
        _, s = analyse(p, seg)
        self.assertEqual((s["cpu_idle_time"], s["cpu_utilization"]), (6, 40.0))

    def test_same_arrival_enter_queue_in_input_order(self):
        p = procs(("Z", 0, 1, 1), ("Y", 0, 1, 1))
        self.assertEqual(blocks(round_robin.schedule(p, 5)), [("Z", 0, 1), ("Y", 1, 2)])

    def test_invalid_quantum_rejected(self):
        for bad in (0, -1, 1.5, "2", None, True):
            with self.assertRaises(ValueError, msg=repr(bad)):
                round_robin.schedule(SAMPLE, bad)


if __name__ == "__main__":
    unittest.main()

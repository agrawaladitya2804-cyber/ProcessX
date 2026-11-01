import unittest

from helpers import SAMPLE, procs
from backend.utils.metrics import SchedulingError, compute_metrics, verify_schedule
from backend.utils.validation import (ValidationError, parse_algorithm, parse_processes,
                                      parse_time_quantum)


def seg(pid, start, end):
    return {"process_id": pid, "start": start, "end": end, "idle": pid is None}


class MetricsTests(unittest.TestCase):
    def test_formulas_on_a_tiny_example(self):
        p = procs(("A", 1, 3, 1))
        out = compute_metrics(p, [seg(None, 0, 1), seg("A", 1, 4)])
        row = out["processes"][0]
        self.assertEqual(row["completion_time"], 4)
        self.assertEqual(row["turnaround_time"], 3)   # CT - AT = 4 - 1
        self.assertEqual(row["waiting_time"], 0)      # TAT - BT = 3 - 3
        self.assertEqual(row["response_time"], 0)     # start 1 - AT 1
        s = out["summary"]
        self.assertEqual((s["total_execution_time"], s["cpu_busy_time"], s["cpu_idle_time"]), (4, 3, 1))
        self.assertEqual(s["cpu_utilization"], 75.0)

    def test_results_keep_input_order(self):
        out = compute_metrics(procs(("Z", 0, 1, 1), ("A", 1, 1, 1)),
                              [seg("Z", 0, 1), seg("A", 1, 2)])
        self.assertEqual([r["id"] for r in out["processes"]], ["Z", "A"])

    def test_verify_rejects_impossible_schedules(self):
        p = procs(("A", 2, 3, 1))
        with self.assertRaises(SchedulingError):                 # runs before arrival
            verify_schedule(p, [seg("A", 0, 3)])
        with self.assertRaises(SchedulingError):                 # too little CPU time
            verify_schedule(p, [seg(None, 0, 2), seg("A", 2, 4)])
        with self.assertRaises(SchedulingError):                 # gap in the timeline
            verify_schedule(p, [seg(None, 0, 1), seg("A", 2, 5)])
        with self.assertRaises(SchedulingError):                 # empty schedule
            verify_schedule(p, [])


class ValidationTests(unittest.TestCase):
    def good(self, **over):
        row = {"id": "P1", "arrival_time": 0, "burst_time": 3, "priority": 1}
        row.update(over)
        return row

    def errors_for(self, raw):
        with self.assertRaises(ValidationError) as ctx:
            parse_processes(raw)
        return ctx.exception.errors

    def test_valid_input_is_parsed(self):
        out = parse_processes([self.good(), self.good(id="P2", arrival_time="4", burst_time=2.0)])
        self.assertEqual((out[1].arrival_time, out[1].burst_time), (4, 2))

    def test_priority_is_optional(self):
        row = self.good()
        del row["priority"]
        self.assertEqual(parse_processes([row])[0].priority, 1)

    def test_zero_and_negative_burst(self):
        for bad in (0, -3):
            self.assertIn("Burst time must be greater than 0", " ".join(self.errors_for([self.good(burst_time=bad)])))

    def test_negative_arrival(self):
        self.assertIn("cannot be negative", " ".join(self.errors_for([self.good(arrival_time=-1)])))

    def test_invalid_priority(self):
        for bad in (0, -2, "abc", 1.5, True):
            self.errors_for([self.good(priority=bad)])

    def test_non_numeric_and_fractional_values(self):
        for bad in ("x", "", None, 2.5, [1], True):
            self.errors_for([self.good(burst_time=bad)])
            self.errors_for([self.good(arrival_time=bad)])

    def test_duplicate_ids_are_rejected_case_insensitively(self):
        errs = self.errors_for([self.good(id="P1"), self.good(id="p1")])
        self.assertTrue(any("duplicate" in e for e in errs))

    def test_bad_ids(self):
        for bad in ("", "  ", "has space", "way-too-long-id", None, 5, "a/b"):
            self.errors_for([self.good(id=bad)])

    def test_missing_fields_and_wrong_shapes(self):
        self.errors_for([{"id": "P1"}])
        self.errors_for(["not an object"])
        self.errors_for([])
        self.errors_for(None)
        self.errors_for("P1")

    def test_all_problems_are_reported_together(self):
        errs = self.errors_for([self.good(burst_time=0), self.good(id="P2", arrival_time=-1)])
        self.assertEqual(len(errs), 2)

    def test_too_many_processes(self):
        many = [self.good(id=f"P{i}") for i in range(51)]
        self.errors_for(many)

    def test_algorithm_and_quantum_parsing(self):
        self.assertEqual(parse_algorithm(" rr "), "RR")
        with self.assertRaises(ValidationError):
            parse_algorithm("LOTTERY")
        with self.assertRaises(ValidationError):
            parse_algorithm(None)
        self.assertEqual(parse_time_quantum(None), 2)
        self.assertEqual(parse_time_quantum("3"), 3)
        for bad in (0, -1, 1.5, "abc"):
            with self.assertRaises(ValidationError):
                parse_time_quantum(bad)
        with self.assertRaises(ValidationError):
            parse_time_quantum(None, required=True)


if __name__ == "__main__":
    unittest.main()

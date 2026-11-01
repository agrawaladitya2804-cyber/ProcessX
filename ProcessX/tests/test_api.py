import json
import unittest

from helpers import ROOT  # noqa: F401  (adds project root to sys.path)
from app import create_app

SAMPLE_JSON = [
    {"id": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
    {"id": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1},
    {"id": "P3", "arrival_time": 2, "burst_time": 8, "priority": 3},
    {"id": "P4", "arrival_time": 3, "burst_time": 2, "priority": 2},
]
EXPECTED_AVG_WT = {"FCFS": 5.75, "SJF": 4.0, "SRTF": 3.5, "RR": 7.25, "PRIORITY": 4.25}
EXPECTED_AVG_TAT = {"FCFS": 10.25, "SJF": 8.5, "SRTF": 8.0, "RR": 11.75, "PRIORITY": 8.75}


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app().test_client()

    def post(self, path, payload):
        return self.client.post(path, json=payload)

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_frontend_is_served(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertIn(b"ProcessX", self.client.get("/").data)
        self.assertEqual(self.client.get("/css/style.css").status_code, 200)
        self.assertEqual(self.client.get("/js/app.js").status_code, 200)

    def test_simulate_every_algorithm_matches_hand_calculation(self):
        for algo in EXPECTED_AVG_WT:
            r = self.post("/api/simulate", {"algorithm": algo, "processes": SAMPLE_JSON, "time_quantum": 2})
            self.assertEqual(r.status_code, 200, algo)
            data = r.get_json()
            self.assertEqual(data["metrics"]["avg_waiting_time"], EXPECTED_AVG_WT[algo], algo)
            self.assertEqual(data["metrics"]["avg_turnaround_time"], EXPECTED_AVG_TAT[algo], algo)
            self.assertEqual(data["gantt"][-1]["end"], 18)
            self.assertEqual([p["id"] for p in data["processes"]], ["P1", "P2", "P3", "P4"])

    def test_simulate_response_shape(self):
        data = self.post("/api/simulate", {"algorithm": "rr", "processes": SAMPLE_JSON, "time_quantum": 2}).get_json()
        self.assertEqual(data["algorithm"], "RR")
        self.assertEqual(data["time_quantum"], 2)
        for key in ("avg_waiting_time", "avg_turnaround_time", "avg_response_time", "cpu_utilization",
                    "total_execution_time", "cpu_idle_time"):
            self.assertIn(key, data["metrics"])
        for key in ("id", "arrival_time", "burst_time", "completion_time", "turnaround_time",
                    "waiting_time", "response_time"):
            self.assertIn(key, data["processes"][0])
        self.assertEqual(set(data["gantt"][0]), {"process_id", "start", "end", "idle"})

    def test_idle_period_is_returned(self):
        procs = [{"id": "A", "arrival_time": 3, "burst_time": 2, "priority": 1}]
        data = self.post("/api/simulate", {"algorithm": "FCFS", "processes": procs}).get_json()
        self.assertEqual(data["gantt"][0], {"process_id": None, "start": 0, "end": 3, "idle": True})
        self.assertEqual(data["metrics"]["cpu_idle_time"], 3)

    def test_quantum_ignored_for_other_algorithms(self):
        data = self.post("/api/simulate", {"algorithm": "FCFS", "processes": SAMPLE_JSON, "time_quantum": "junk"}).get_json()
        self.assertIsNone(data["time_quantum"])

    def test_compare_all(self):
        r = self.post("/api/compare", {"processes": SAMPLE_JSON, "time_quantum": 2})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual([x["algorithm"] for x in data["results"]], ["FCFS", "SJF", "SRTF", "RR", "PRIORITY"])
        self.assertEqual(data["time_quantum"], 2)
        self.assertEqual(data["best"]["avg_waiting_time"], {"algorithms": ["SRTF"], "value": 3.5})
        self.assertEqual(data["best"]["avg_turnaround_time"], {"algorithms": ["SRTF"], "value": 8.0})
        self.assertEqual(data["best"]["avg_response_time"], {"algorithms": ["RR"], "value": 2.0})

    def test_compare_defaults_quantum_to_two(self):
        data = self.post("/api/compare", {"processes": SAMPLE_JSON}).get_json()
        self.assertEqual(data["time_quantum"], 2)

    def test_compare_reports_ties(self):
        one = [{"id": "A", "arrival_time": 0, "burst_time": 4, "priority": 1}]
        best = self.post("/api/compare", {"processes": one, "time_quantum": 2}).get_json()["best"]
        self.assertEqual(len(best["avg_waiting_time"]["algorithms"]), 5)

    # ---- error handling -------------------------------------------------
    def assert_400(self, response, fragment):
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertIn("error", body)
        self.assertIn(fragment, " ".join(body["details"]))

    def test_invalid_json_body(self):
        r = self.client.post("/api/simulate", data="not json", content_type="application/json")
        self.assert_400(r, "JSON object")
        self.assert_400(self.client.post("/api/simulate", data="[]", content_type="application/json"), "JSON object")

    def test_unknown_algorithm(self):
        self.assert_400(self.post("/api/simulate", {"algorithm": "XYZ", "processes": SAMPLE_JSON}), "Unknown algorithm")

    def test_empty_process_list(self):
        self.assert_400(self.post("/api/simulate", {"algorithm": "FCFS", "processes": []}), "at least one process")

    def test_zero_and_negative_values(self):
        bad = [{"id": "A", "arrival_time": -1, "burst_time": 0, "priority": 0}]
        r = self.post("/api/simulate", {"algorithm": "FCFS", "processes": bad})
        self.assertEqual(r.status_code, 400)
        details = " ".join(r.get_json()["details"])
        self.assertIn("negative", details)
        self.assertIn("greater than 0", details)
        self.assertIn("Priority", details)

    def test_duplicate_ids(self):
        dup = SAMPLE_JSON[:1] * 2
        self.assert_400(self.post("/api/simulate", {"algorithm": "FCFS", "processes": dup}), "duplicate")

    def test_round_robin_needs_valid_quantum(self):
        self.assert_400(self.post("/api/simulate", {"algorithm": "RR", "processes": SAMPLE_JSON}), "quantum")
        for bad in (0, -2, 1.5, "x"):
            r = self.post("/api/simulate", {"algorithm": "RR", "processes": SAMPLE_JSON, "time_quantum": bad})
            self.assertEqual(r.status_code, 400, bad)
        self.assertEqual(self.post("/api/compare", {"processes": SAMPLE_JSON, "time_quantum": 0}).status_code, 400)

    def test_unknown_api_route_returns_json_404(self):
        r = self.client.get("/api/nope")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())

    def test_wrong_method_returns_json_405(self):
        r = self.client.get("/api/simulate")
        self.assertEqual(r.status_code, 405)
        self.assertIn("error", json.loads(r.data))


if __name__ == "__main__":
    unittest.main()

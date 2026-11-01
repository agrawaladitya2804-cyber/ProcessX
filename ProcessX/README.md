# ProcessX 2.0 - CPU Scheduling Visualizer

ProcessX is an educational web app that shows how an operating system schedules processes on the CPU.
You enter processes, pick an algorithm, and ProcessX draws the **Gantt chart** and calculates waiting,
turnaround and response times. It can also **compare all five algorithms** side by side.

* **Backend:** Python 3 + Flask (all scheduling maths happens here)
* **Frontend:** HTML, CSS and plain JavaScript (drawing only) + Chart.js for comparison charts
* **No C++, CMake, GCC, MinGW or Visual Studio needed. No database needed.**

Algorithms: FCFS, SJF (non-preemptive), SRTF (preemptive), Round Robin, Priority (non-preemptive).

---

## 1. Quick start on Windows (easiest)

1. Install **Python 3.9 or newer** from <https://www.python.org/downloads/>.
   In the installer, tick **"Add python.exe to PATH"**.
2. Unzip the project and **double-click `run.bat`**.

`run.bat` does everything for you: it checks Python, creates a `venv` folder the first time, installs
Flask (internet needed once), starts the app and opens <http://127.0.0.1:5000> in your browser.
Keep the black window open while you use the app. Press **Ctrl+C** in it to stop.

### Opening and running it in Visual Studio Code

1. Start VS Code, choose **File > Open Folder...** and select the `ProcessX` folder.
2. Open a terminal: **Terminal > New Terminal**.
3. Type this and press Enter:

   ```
   .\run.bat
   ```

   (In PowerShell the `.\` in front is required.)
4. The browser opens by itself. If it does not, go to <http://127.0.0.1:5000>.

Optional: press **Ctrl+Shift+B** in VS Code to run the "Run ProcessX" task, or **Ctrl+Shift+P > Python: Select Interpreter**
and pick the one inside `venv`.

---

## 2. Manual start (without run.bat)

In a terminal opened inside the `ProcessX` folder:

**Command Prompt (cmd)**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**PowerShell**
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
If PowerShell says scripts are disabled, skip the activate line and use `venv\Scripts\python.exe app.py`
(after `venv\Scripts\python.exe -m pip install -r requirements.txt`).

**macOS / Linux**
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>. To use another port, set the `PORT` environment variable first
(for example `set PORT=5050` in cmd).

---

## 3. Using the app

1. **Add processes** - fill in Process ID, Arrival time, Burst time and Priority, then press *Add Process*.
   Leave the ID blank (or use the suggested one) to get automatic IDs P1, P2, ...
   Or press **Load Sample Data** to load the demo set.
2. **Remove** - tick one or more rows and press *Remove Process*. *Clear All* empties the table.
3. **Pick an algorithm.** For Round Robin a *Time quantum* box appears.
4. Press **Run Simulation**. You get the Gantt chart, four metric cards and the per-process results table.
5. Press **Compare All Algorithms** (Compare section) to run the same processes through all five algorithms
   (Round Robin quantum defaults to **2** and is shown on screen). The best value per metric is marked.
   "Best" only means best for *that* process set, not best in general.

Validation: arrival time must be 0 or more, burst time must be greater than 0, priority must be a positive
whole number, and process IDs must be unique.

---

## 4. Running the automated tests

```
venv\Scripts\python.exe -m unittest discover -s tests -v
```
(or just `python -m unittest discover -s tests -v` if the virtual environment is active).

The tests use Python's built-in `unittest`, so nothing extra has to be installed. They cover single and multiple
processes, equal and different arrival times, idle time, preemption, Round Robin queue rotation, priority ties,
invalid input, zero/negative values, the REST API, and a cross-check against an independent unit-by-unit simulator.

---

## 5. REST API

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/health` | Backend status |
| POST | `/api/simulate` | Run one algorithm |
| POST | `/api/compare` | Run all five algorithms on the same processes |

`POST /api/simulate` body:
```json
{
  "algorithm": "RR",
  "time_quantum": 2,
  "processes": [
    {"id": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
    {"id": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1}
  ]
}
```
`algorithm` is one of `FCFS`, `SJF`, `SRTF`, `RR`, `PRIORITY`. `time_quantum` is only needed for `RR`.
`priority` is optional (defaults to 1).

The response contains `processes` (CT, TAT, WT, RT for each), `gantt` (list of segments, idle ones have
`"idle": true` and `"process_id": null`) and `metrics` (averages, CPU utilization, total execution time, idle time).

`POST /api/compare` body: `{"processes": [...], "time_quantum": 2}` (quantum defaults to 2). The response
holds one full result per algorithm plus a `best` object listing the winner(s) for each metric.

Errors are JSON with HTTP status 400, for example:
```json
{"error": "Invalid input.", "details": ["Process #1 (P1): Burst time must be greater than 0."]}
```

Try it in PowerShell:
```
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

---

## 6. Project structure

```
ProcessX/
├── app.py                  Flask app: routes and error handling
├── requirements.txt        Python packages (Flask)
├── run.bat                 One-click launcher for Windows
├── README.md
├── backend/
│   ├── models.py           Process data class
│   ├── simulator.py        Runs one/all algorithms, picks the best per metric
│   ├── algorithms/         fcfs.py, sjf.py, srtf.py, round_robin.py, priority.py
│   └── utils/
│       ├── gantt.py        Builds the CPU timeline and fills idle gaps
│       ├── metrics.py      CT, TAT, WT, RT, averages, utilization + self-check
│       └── validation.py   Input validation
├── frontend/
│   ├── index.html          The single-page dashboard
│   ├── css/style.css       Light theme
│   └── js/app.js           UI logic and drawing
├── tests/                  unittest test files
└── docs/                   Project overview and viva questions
```

---

## 7. Rules and conventions used by the algorithms

* **Formulas:** TAT = CT - AT, WT = TAT - BT, RT = first CPU start - AT.
  CPU utilization = busy time / total execution time x 100. The timeline starts at time 0,
  so waiting for the first arrival counts as idle time.
* **Priority:** a **smaller number means higher priority** (1 is the most urgent).
* **Ties** (SJF, SRTF, Priority): shorter burst / shorter remaining time / higher priority first, then earlier
  arrival, then the order the processes were entered. FCFS uses arrival time, then entry order.
* **SRTF:** a new arrival preempts only if its burst is strictly shorter than the running process's remaining time.
* **Round Robin:** FIFO ready queue. Processes that arrive during a slice, or exactly when it ends,
  join the queue *before* the preempted process returns to the back. If a process runs two slices in a row,
  they are drawn as one block.

### Verified example (sample data)

| Process | Arrival | Burst | Priority |
|---|---|---|---|
| P1 | 0 | 5 | 2 |
| P2 | 1 | 3 | 1 |
| P3 | 2 | 8 | 3 |
| P4 | 3 | 2 | 2 |

| Algorithm | Gantt order | Avg WT | Avg TAT | Avg RT |
|---|---|---|---|---|
| FCFS | P1 P2 P3 P4 | 5.75 | 10.25 | 5.75 |
| SJF | P1 P4 P2 P3 | 4.00 | 8.50 | 4.00 |
| SRTF | P1 P2 P4 P1 P3 | 3.50 | 8.00 | 2.25 |
| Round Robin (q=2) | P1 P2 P3 P1 P4 P2 P3 P1 P3 | 7.25 | 11.75 | 2.00 |
| Priority | P1 P2 P4 P3 | 4.25 | 8.75 | 4.25 |

These were calculated by hand and are asserted in the automated tests.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `Python 3 was not found` | Install Python from python.org and tick "Add python.exe to PATH", then run `run.bat` again. |
| Pip cannot install Flask | The first run needs internet. Connect and run `run.bat` again. |
| "Backend not reachable" badge at the top | Open the app through <http://127.0.0.1:5000> after starting it with `run.bat`. Do not open `index.html` by double-clicking it. |
| "Address already in use" | Another program uses port 5000. Close it, or set `PORT=5050` and start again. |
| Charts look like simple bars | Chart.js could not be downloaded (no internet). The numbers are still correct. For an offline copy see `frontend/js/vendor/README.txt`. |

---

## 9. Note for users of ProcessX 1.0

The old `backend/tests/test_cases.txt` listed expected averages that do not match the correct results
(for example it gave FCFS an average waiting time of 6.25; the correct value for that data set is 5.75).
ProcessX 2.0 replaces them with hand-verified values that are checked by automated tests.

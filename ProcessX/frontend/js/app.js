/* ProcessX 2.0 – frontend controller.
   This file only handles the user interface and drawing.
   Every scheduling calculation is done by the Python backend (/api/simulate, /api/compare). */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ data */
  var SAMPLE = [
    { id: 'P1', arrival_time: 0, burst_time: 5, priority: 2 },
    { id: 'P2', arrival_time: 1, burst_time: 3, priority: 1 },
    { id: 'P3', arrival_time: 2, burst_time: 8, priority: 3 },
    { id: 'P4', arrival_time: 3, burst_time: 2, priority: 2 }
  ];
  var LIMITS = { processes: 50, arrival: 10000, burst: 1000, priority: 1000, quantum: 1000 };
  var SHORT_NAMES = { FCFS: 'FCFS', SJF: 'SJF', SRTF: 'SRTF', RR: 'Round Robin', PRIORITY: 'Priority' };

  // Soft fill / border pairs. Process colours follow the order processes were entered.
  var PALETTE = [
    ['#DBEAFE', '#93C5FD'], ['#DCFCE7', '#86EFAC'], ['#FEF3C7', '#FCD34D'], ['#FCE7F3', '#F9A8D4'],
    ['#EDE9FE', '#C4B5FD'], ['#CCFBF1', '#5EEAD4'], ['#FFE4E6', '#FDA4AF'], ['#E0F2FE', '#7DD3FC'],
    ['#ECFCCB', '#BEF264'], ['#FFEDD5', '#FDBA74']
  ];

  var state = {
    processes: [],
    selected: {},          // id -> true
    algorithm: 'FCFS',
    result: null,
    charts: []
  };

  /* --------------------------------------------------------------- helpers */
  function $(id) { return document.getElementById(id); }

  function make(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function two(n) { return Number(n).toFixed(2); }

  function colorFor(index) {
    if (index < PALETTE.length) return PALETTE[index];
    var hue = (index * 137.5) % 360;
    return ['hsl(' + hue + ', 80%, 90%)', 'hsl(' + hue + ', 60%, 70%)'];
  }

  function colorMap(rows) {
    var map = {};
    rows.forEach(function (r, i) { map[r.id] = colorFor(i); });
    return map;
  }

  function setError(fieldId, message) {
    var span = $('err-' + fieldId);
    span.textContent = message || '';
    var input = fieldId === 'id' ? $('in-id') : fieldId === 'at' ? $('in-at') :
      fieldId === 'bt' ? $('in-bt') : fieldId === 'pr' ? $('in-pr') :
      fieldId === 'quantum' ? $('in-quantum') : $('compare-quantum');
    if (input && input.parentElement) input.parentElement.classList.toggle('has-error', !!message);
  }

  function showAlert(node, messages) {
    node.textContent = '';
    if (!messages || !messages.length) { node.hidden = true; return; }
    if (messages.length === 1) {
      node.textContent = messages[0];
    } else {
      var ul = make('ul');
      messages.forEach(function (m) { ul.appendChild(make('li', null, m)); });
      node.appendChild(ul);
    }
    node.hidden = false;
  }

  /* ------------------------------------------------------- backend calling */
  function api(path, options) {
    return fetch(path, options).then(function (res) {
      return res.json().catch(function () { return null; }).then(function (data) {
        if (!res.ok) {
          var err = new Error((data && data.error) || ('Request failed (' + res.status + ')'));
          err.details = (data && data.details) || [];
          throw err;
        }
        return data;
      });
    }, function () {
      var err = new Error('Cannot reach the ProcessX backend.');
      err.details = ['Start the app with run.bat (or "python app.py") and open http://127.0.0.1:5000 in your browser.'];
      throw err;
    });
  }

  function post(path, body) {
    return api(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }

  function errorMessages(err) {
    return err.details && err.details.length ? err.details : [err.message];
  }

  function checkBackend() {
    var box = $('backend-status');
    api('/api/health').then(function () {
      box.className = 'status is-ok';
      box.title = 'Python backend is running';
      $('backend-status-text').textContent = 'Backend connected';
    }, function () {
      box.className = 'status is-bad';
      box.title = 'Start the app with run.bat or "python app.py", then open http://127.0.0.1:5000';
      $('backend-status-text').textContent = 'Backend not reachable';
    });
  }

  /* -------------------------------------------------- input validation (UI) */
  // Mirrors the server rules so mistakes are caught instantly; the server re-validates everything.
  function checkWholeNumber(text, label, min, max, minMessage) {
    var t = text.trim();
    if (t === '') return { error: label + ' is required.' };
    if (!/^[+-]?\d+$/.test(t)) return { error: label + ' must be a whole number.' };
    var n = parseInt(t, 10);
    if (n < min) return { error: minMessage };
    if (n > max) return { error: label + ' cannot be greater than ' + max + '.' };
    return { value: n };
  }

  function validateProcess(raw) {
    var errors = {}, out = {};
    var id = raw.id.trim();
    if (!id) {
      errors.id = 'Enter a process ID.';
    } else if (!/^[A-Za-z0-9_-]{1,10}$/.test(id)) {
      errors.id = 'Use 1–10 letters, digits, "-" or "_".';
    } else if (state.processes.some(function (p) { return p.id.toLowerCase() === id.toLowerCase(); })) {
      errors.id = 'ID "' + id + '" already exists.';
    } else {
      out.id = id;
    }
    var at = checkWholeNumber(raw.at, 'Arrival time', 0, LIMITS.arrival, 'Arrival time cannot be negative.');
    var bt = checkWholeNumber(raw.bt, 'Burst time', 1, LIMITS.burst, 'Burst time must be greater than 0.');
    var pr = checkWholeNumber(raw.pr, 'Priority', 1, LIMITS.priority, 'Priority must be a positive whole number (1 or higher).');
    if (at.error) errors.at = at.error; else out.arrival_time = at.value;
    if (bt.error) errors.bt = bt.error; else out.burst_time = bt.value;
    if (pr.error) errors.pr = pr.error; else out.priority = pr.value;
    return { errors: errors, value: out };
  }

  function nextId() {
    var used = {}, max = 0;
    state.processes.forEach(function (p) {
      used[p.id.toLowerCase()] = true;
      var m = /^P(\d+)$/i.exec(p.id);
      if (m) max = Math.max(max, parseInt(m[1], 10));
    });
    var n = Math.max(max, state.processes.length) + 1;
    while (used['p' + n]) n++;
    return 'P' + n;
  }

  /* ----------------------------------------------------- process table (UI) */
  function selectedIds() { return Object.keys(state.selected).filter(function (k) { return state.selected[k]; }); }

  function renderProcesses() {
    var body = $('process-body');
    body.textContent = '';
    if (!state.processes.length) {
      var tr = make('tr', 'empty-row');
      var td = make('td', null, 'No processes yet. Add one above or load the sample data.');
      td.colSpan = 5;
      tr.appendChild(td);
      body.appendChild(tr);
    }
    state.processes.forEach(function (p, i) {
      var row = make('tr', state.selected[p.id] ? 'is-selected' : '');
      var cell = make('td', 'col-check');
      var box = make('input');
      box.type = 'checkbox';
      box.checked = !!state.selected[p.id];
      box.setAttribute('aria-label', 'Select ' + p.id);
      box.addEventListener('change', function () {
        if (box.checked) state.selected[p.id] = true; else delete state.selected[p.id];
        renderProcesses();
      });
      cell.appendChild(box);
      row.appendChild(cell);

      var idCell = make('td', 'pid');
      var dot = make('span', 'pid-dot');
      var c = colorFor(i);
      dot.style.background = c[0];
      dot.style.borderColor = c[1];
      idCell.appendChild(dot);
      idCell.appendChild(document.createTextNode(p.id));
      row.appendChild(idCell);
      row.appendChild(make('td', null, p.arrival_time));
      row.appendChild(make('td', null, p.burst_time));
      row.appendChild(make('td', null, p.priority));
      body.appendChild(row);
    });

    var count = selectedIds().length;
    var all = $('select-all');
    all.checked = state.processes.length > 0 && count === state.processes.length;
    all.indeterminate = count > 0 && count < state.processes.length;
    $('remove-btn').disabled = count === 0;
    $('remove-btn').textContent = count > 1 ? 'Remove ' + count + ' Processes' : 'Remove Process';

    var n = state.processes.length;
    $('stat-total').textContent = n;
    $('stat-total-hint').textContent = n === 0 ? 'Add a process or load the sample data' :
      n + (n === 1 ? ' process is ready to simulate' : ' processes are ready to simulate');
  }

  function resetOverviewResults() {
    [['wt', 'Run a simulation to see this'], ['tat', 'Run a simulation to see this'], ['util', 'Run a simulation to see this']]
      .forEach(function (pair) {
        var v = $('stat-' + pair[0]);
        v.textContent = '—';
        v.classList.add('is-placeholder');
        $('stat-' + pair[0] + '-hint').textContent = pair[1];
      });
  }

  // Called whenever the process list changes: old results would no longer match.
  function invalidateResults() {
    var had = !!state.result || !$('compare-output').hidden;
    state.result = null;
    $('results').hidden = true;
    $('compare-output').hidden = true;
    $('compare-empty').hidden = false;
    destroyCharts();
    resetOverviewResults();
    return had;
  }

  function resetForm() {
    $('in-id').value = nextId();
    $('in-at').value = '0';
    $('in-bt').value = '';
    $('in-pr').value = '1';
    ['id', 'at', 'bt', 'pr'].forEach(function (f) { setError(f, ''); });
    showAlert($('form-error'), null);
  }

  function addProcess(event) {
    event.preventDefault();
    showAlert($('form-error'), null);
    if (state.processes.length >= LIMITS.processes) {
      showAlert($('form-error'), ['You can add at most ' + LIMITS.processes + ' processes.']);
      return;
    }
    var idText = $('in-id').value.trim() || nextId();     // blank ID -> automatic ID
    $('in-id').value = idText;
    var result = validateProcess({ id: idText, at: $('in-at').value, bt: $('in-bt').value, pr: $('in-pr').value });
    ['id', 'at', 'bt', 'pr'].forEach(function (f) { setError(f, result.errors[f]); });
    var firstBad = ['id', 'at', 'bt', 'pr'].filter(function (f) { return result.errors[f]; })[0];
    if (firstBad) {
      $({ id: 'in-id', at: 'in-at', bt: 'in-bt', pr: 'in-pr' }[firstBad]).focus();
      return;
    }
    state.processes.push(result.value);
    invalidateResults();
    renderProcesses();
    resetForm();
    $('in-bt').focus();
  }

  function removeSelected() {
    var ids = selectedIds();
    if (!ids.length) return;
    state.processes = state.processes.filter(function (p) { return ids.indexOf(p.id) === -1; });
    state.selected = {};
    invalidateResults();
    renderProcesses();
    resetForm();
  }

  function clearAll() {
    state.processes = [];
    state.selected = {};
    invalidateResults();
    renderProcesses();
    resetForm();
    showAlert($('run-error'), null);
  }

  function loadSample() {
    state.processes = SAMPLE.map(function (p) { return Object.assign({}, p); });
    state.selected = {};
    invalidateResults();
    renderProcesses();
    resetForm();
    showAlert($('run-error'), null);
  }

  /* ---------------------------------------------------- algorithm selection */
  function selectAlgorithm(value) {
    state.algorithm = value;
    Array.prototype.forEach.call(document.querySelectorAll('.algo-option'), function (label) {
      label.classList.toggle('selected', label.querySelector('input').value === value);
    });
    $('quantum-row').hidden = value !== 'RR';
    setError('quantum', '');
  }

  /* --------------------------------------------------------- run simulation */
  function runSimulation() {
    showAlert($('run-error'), null);
    setError('quantum', '');
    if (!state.processes.length) {
      showAlert($('run-error'), ['Add at least one process (or load the sample data) before running a simulation.']);
      return;
    }
    var payload = { algorithm: state.algorithm, processes: state.processes };
    if (state.algorithm === 'RR') {
      var q = checkWholeNumber($('in-quantum').value, 'Time quantum', 1, LIMITS.quantum, 'Time quantum must be greater than 0.');
      if (q.error) { setError('quantum', q.error); $('in-quantum').focus(); return; }
      payload.time_quantum = q.value;
    }
    var btn = $('run-btn');
    btn.disabled = true;
    btn.textContent = 'Running…';
    post('/api/simulate', payload).then(function (data) {
      state.result = data;
      renderResults(data);
      $('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }).catch(function (err) {
      showAlert($('run-error'), errorMessages(err));
    }).then(function () {
      btn.disabled = false;
      btn.textContent = 'Run Simulation';
    });
  }

  function renderResults(data) {
    var m = data.metrics;
    $('results').hidden = false;
    $('results-title').textContent = 'Results: ' + data.algorithm_name;
    $('results-sub').textContent = data.time_quantum ? 'Time quantum = ' + data.time_quantum : '';
    $('results-sub').hidden = !data.time_quantum;

    // overview cards (top of page)
    var short = SHORT_NAMES[data.algorithm] || data.algorithm;
    [['wt', two(m.avg_waiting_time)], ['tat', two(m.avg_turnaround_time)], ['util', two(m.cpu_utilization) + '%']]
      .forEach(function (pair) {
        var v = $('stat-' + pair[0]);
        v.textContent = pair[1];
        v.classList.remove('is-placeholder');
      });
    $('stat-wt-hint').textContent = short + ', in time units';
    $('stat-tat-hint').textContent = short + ', in time units';
    $('stat-util-hint').textContent = m.cpu_idle_time > 0 ? m.cpu_idle_time + ' idle time units' : 'CPU was never idle';

    // metric cards
    $('m-wt').textContent = two(m.avg_waiting_time);
    $('m-tat').textContent = two(m.avg_turnaround_time);
    $('m-rt').textContent = two(m.avg_response_time);
    $('m-util').textContent = two(m.cpu_utilization) + '%';
    $('m-util-hint').textContent = m.cpu_busy_time + ' busy of ' + m.total_execution_time + ' time units';

    // chips above the Gantt chart
    var chips = $('gantt-chips');
    chips.textContent = '';
    [['Total execution time', m.total_execution_time, ''], ['CPU busy', m.cpu_busy_time, ''],
     ['CPU idle', m.cpu_idle_time, m.cpu_idle_time > 0 ? 'is-warn' : '']].forEach(function (c) {
      var chip = make('span', 'chip ' + c[2]);
      chip.appendChild(make('b', null, c[1]));
      chip.appendChild(document.createTextNode(c[0]));
      chips.appendChild(chip);
    });

    renderGantt(data);
    renderResultsTable(data);
  }

  /* -------------------------------------------------------------- Gantt chart */
  function renderGantt(data) {
    var segments = data.gantt;
    var colors = colorMap(data.processes);
    var total = segments[segments.length - 1].end;
    var holder = $('gantt');
    holder.textContent = '';

    var available = $('gantt-scroll').clientWidth - 44;
    var digits = String(total).length;
    var minUnit = Math.max(34, digits * 9 + 8);          // keep time labels readable
    var unit = Math.max(minUnit, Math.min(64, Math.floor(available / total)));
    holder.style.width = (total * unit) + 'px';

    var boundaries = {};
    segments.forEach(function (seg) {
      boundaries[seg.start] = true;
      boundaries[seg.end] = true;
      var block = make('div', 'gantt-block' + (seg.idle ? ' idle' : ''));
      block.style.left = (seg.start * unit + 1) + 'px';
      block.style.width = Math.max(2, (seg.end - seg.start) * unit - 2) + 'px';
      var label = seg.idle ? 'Idle' : seg.process_id;
      block.title = (seg.idle ? 'CPU idle' : seg.process_id) + ': ' + seg.start + ' to ' + seg.end +
        ' (' + (seg.end - seg.start) + ' time unit' + (seg.end - seg.start === 1 ? '' : 's') + ')';
      if (!seg.idle) {
        var c = colors[seg.process_id];
        block.style.background = c[0];
        block.style.borderColor = c[1];
      }
      if ((seg.end - seg.start) * unit >= (seg.idle ? 40 : 26)) block.textContent = label;
      holder.appendChild(block);
    });

    Object.keys(boundaries).forEach(function (t) {
      var tick = make('span', 'gantt-tick', t);
      tick.style.left = (Number(t) * unit) + 'px';
      holder.appendChild(tick);
    });

    var legend = $('gantt-legend');
    legend.textContent = '';
    data.processes.forEach(function (p) {
      var item = make('span', 'legend-item');
      var sw = make('span', 'swatch');
      sw.style.background = colors[p.id][0];
      sw.style.borderColor = colors[p.id][1];
      item.appendChild(sw);
      item.appendChild(document.createTextNode(p.id));
      legend.appendChild(item);
    });
    if (data.metrics.cpu_idle_time > 0) {
      var idle = make('span', 'legend-item');
      idle.appendChild(make('span', 'swatch idle'));
      idle.appendChild(document.createTextNode('Idle (no process ready)'));
      legend.appendChild(idle);
    }
  }

  /* ----------------------------------------------------------- results table */
  function renderResultsTable(data) {
    var body = $('results-body');
    body.textContent = '';
    data.processes.forEach(function (p) {
      var tr = make('tr');
      [p.id, p.arrival_time, p.burst_time, p.completion_time, p.turnaround_time, p.waiting_time, p.response_time]
        .forEach(function (v, i) { tr.appendChild(make('td', i === 0 ? 'pid' : null, v)); });
      body.appendChild(tr);
    });
    var foot = $('results-foot');
    foot.textContent = '';
    var tr = make('tr');
    var label = make('td', null, 'Average');
    label.colSpan = 4;
    label.style.textAlign = 'left';
    tr.appendChild(label);
    tr.appendChild(make('td', null, two(data.metrics.avg_turnaround_time)));
    tr.appendChild(make('td', null, two(data.metrics.avg_waiting_time)));
    tr.appendChild(make('td', null, two(data.metrics.avg_response_time)));
    foot.appendChild(tr);
  }

  /* ------------------------------------------------------------------ compare */
  function runCompare() {
    showAlert($('compare-error'), null);
    setError('compare-quantum', '');
    if (!state.processes.length) {
      showAlert($('compare-error'), ['Add at least one process (or load the sample data) before comparing.']);
      return;
    }
    var q = checkWholeNumber($('compare-quantum').value, 'Time quantum', 1, LIMITS.quantum, 'Time quantum must be greater than 0.');
    if (q.error) { setError('compare-quantum', q.error); return; }
    var btn = $('compare-btn');
    btn.disabled = true;
    btn.textContent = 'Comparing…';
    post('/api/compare', { processes: state.processes, time_quantum: q.value }).then(function (data) {
      renderCompare(data);
    }).catch(function (err) {
      showAlert($('compare-error'), errorMessages(err));
    }).then(function () {
      btn.disabled = false;
      btn.textContent = 'Compare All Algorithms';
    });
  }

  var METRICS = [
    { key: 'avg_waiting_time', chart: 'wt', title: 'Average waiting time' },
    { key: 'avg_turnaround_time', chart: 'tat', title: 'Average turnaround time' },
    { key: 'avg_response_time', chart: 'rt', title: 'Average response time' }
  ];

  function renderCompare(data) {
    $('compare-empty').hidden = true;
    $('compare-output').hidden = false;

    var chips = $('compare-chips');
    chips.textContent = '';
    [['Round Robin time quantum', data.time_quantum, 'is-info'], ['Processes compared', data.process_count, '']]
      .forEach(function (c) {
        var chip = make('span', 'chip ' + c[2]);
        chip.appendChild(make('b', null, c[1]));
        chip.appendChild(document.createTextNode(c[0]));
        chips.appendChild(chip);
      });

    var total = data.results.length;
    var winners = {};   // metric key -> list of algorithm codes (empty if everyone ties)
    var ties = [];
    METRICS.forEach(function (mt) {
      var best = data.best[mt.key].algorithms;
      if (best.length === total) { winners[mt.key] = []; ties.push(mt.title.toLowerCase()); }
      else winners[mt.key] = best;
    });

    var body = $('compare-body');
    body.textContent = '';
    data.results.forEach(function (r) {
      var tr = make('tr');
      var name = make('td', 'algo-cell');
      name.appendChild(make('strong', null, r.algorithm));
      name.appendChild(make('small', null, r.algorithm === 'RR' ? 'Round Robin (quantum ' + data.time_quantum + ')' :
        r.algorithm_name.replace(/ \(.*\)$/, '')));
      tr.appendChild(name);
      METRICS.forEach(function (mt) {
        var td = make('td', null, two(r.metrics[mt.key]));
        if (winners[mt.key].indexOf(r.algorithm) !== -1) {
          td.className = 'is-best';
          td.appendChild(make('span', 'badge-best', 'Best'));
        }
        tr.appendChild(td);
      });
      tr.appendChild(make('td', null, two(r.metrics.cpu_utilization) + '%'));
      tr.appendChild(make('td', null, r.metrics.total_execution_time));
      body.appendChild(tr);
    });

    var note = 'Best means the lowest value for this particular set of processes. It does not make an algorithm better in general: ' +
      'results change with arrival times, burst lengths and the time quantum.';
    if (ties.length) note += ' All algorithms tie on ' + ties.join(', ') + ' for this input.';
    $('compare-note').textContent = note;

    destroyCharts();
    METRICS.forEach(function (mt) {
      drawBarChart(mt, data, winners[mt.key]);
    });
  }

  /* ------------------------------------------------------------------- charts */
  function destroyCharts() {
    state.charts.forEach(function (c) { c.destroy(); });
    state.charts = [];
  }

  var valueLabels = {
    id: 'valueLabels',
    afterDatasetsDraw: function (chart) {
      var ctx = chart.ctx;
      ctx.save();
      ctx.font = '600 12px Inter, "Segoe UI", system-ui, sans-serif';
      ctx.fillStyle = '#172033';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      chart.getDatasetMeta(0).data.forEach(function (bar, i) {
        ctx.fillText(two(chart.data.datasets[0].data[i]), bar.x, bar.y - 4);
      });
      ctx.restore();
    }
  };

  function drawBarChart(metric, data, bestList) {
    var box = $('chart-box-' + metric.chart);
    var labels = data.results.map(function (r) { return r.algorithm === 'PRIORITY' ? 'Priority' : r.algorithm; });
    var values = data.results.map(function (r) { return r.metrics[metric.key]; });
    var isBest = data.results.map(function (r) { return bestList.indexOf(r.algorithm) !== -1; });

    if (typeof window.Chart === 'undefined') {       // Chart.js missing (e.g. offline): simple CSS bars
      box.textContent = '';
      var max = Math.max.apply(null, values.concat([1]));
      values.forEach(function (v, i) {
        var row = make('div', 'bar-row');
        row.appendChild(make('span', null, labels[i]));
        var track = make('div', 'bar-track');
        var fill = make('div', 'bar-fill' + (isBest[i] ? ' is-best' : ''));
        fill.style.width = (v / max * 100) + '%';
        track.appendChild(fill);
        row.appendChild(track);
        row.appendChild(make('span', 'bar-value', two(v)));
        box.appendChild(row);
      });
      return;
    }

    box.textContent = '';
    var canvas = make('canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Bar chart of ' + metric.title.toLowerCase() + ' per algorithm');
    box.appendChild(canvas);
    var chart = new window.Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: metric.title,
          data: values,
          backgroundColor: isBest.map(function (b) { return b ? '#16A34A' : '#2563EB'; }),
          borderRadius: 6,
          maxBarThickness: 44
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (ctx) { return metric.title + ': ' + two(ctx.parsed.y); } } }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748B' } },
          y: { beginAtZero: true, grace: '15%', grid: { color: '#E5E7EB' }, ticks: { color: '#64748B' },
               title: { display: true, text: 'time units', color: '#64748B' } }
        }
      },
      plugins: [valueLabels]
    });
    state.charts.push(chart);
  }

  /* -------------------------------------------------------------------- setup */
  function init() {
    $('process-form').addEventListener('submit', addProcess);
    $('remove-btn').addEventListener('click', removeSelected);
    $('clear-btn').addEventListener('click', clearAll);
    $('sample-btn').addEventListener('click', loadSample);
    $('run-btn').addEventListener('click', runSimulation);
    $('compare-btn').addEventListener('click', runCompare);
    $('select-all').addEventListener('change', function (e) {
      state.selected = {};
      if (e.target.checked) state.processes.forEach(function (p) { state.selected[p.id] = true; });
      renderProcesses();
    });
    Array.prototype.forEach.call(document.querySelectorAll('input[name="algorithm"]'), function (radio) {
      radio.addEventListener('change', function () { selectAlgorithm(radio.value); });
    });
    ['in-id', 'in-at', 'in-bt', 'in-pr'].forEach(function (id) {
      $(id).addEventListener('input', function () {
        var key = { 'in-id': 'id', 'in-at': 'at', 'in-bt': 'bt', 'in-pr': 'pr' }[id];
        setError(key, '');
      });
    });
    $('in-quantum').addEventListener('input', function () { setError('quantum', ''); });
    $('compare-quantum').addEventListener('input', function () { setError('compare-quantum', ''); });

    var resizeTimer = null;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () { if (state.result) renderGantt(state.result); }, 150);
    });

    selectAlgorithm('FCFS');
    renderProcesses();
    resetForm();
    checkBackend();
  }

  init();
})();

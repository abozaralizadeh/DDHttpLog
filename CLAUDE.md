# CLAUDE.md

Guidance for Claude Code (and humans) working in this repo. [README.md](README.md) is the
user-facing page.

## What this is

A small Python 3 console app (originally called HttpLogMonitoring) that reads an HTTP access log
in CSV form and prints, to stdout: statistics for every 10-second window (total calls, the most
hit section, non-200 responses grouped by request) and a high-traffic alert when the average over
the last 2 minutes reaches 10 hits per second, followed by "Alert recovered" when it drops below.
Standard library only: no dependencies, no requirements file, no packaging.

## Commands

Run everything from the repo root (the test uses relative paths).

```bash
python http_log_monitoring.py LOG_FILE.csv            # run on the sample log
TZ=Europe/Rome python tests.py                        # both tests (or: python -m unittest tests)
PYTHONDONTWRITEBYTECODE=1 TZ=Europe/Rome python tests.py   # same, without leaving __pycache__/
TZ=Europe/Rome python http_log_monitoring.py LOG_FILE.csv > results.txt   # regenerate the expected output
```

- `results.txt` was generated in UTC+1 (CET). Times are printed with `datetime.fromtimestamp`,
  i.e. in the local time zone, so in any other zone `test_command` fails on every timestamp line.
  `TZ=Europe/Rome` (or any CET zone) makes it pass; checked on Python 3.13.
- `test_command` shells out with `os.popen("python http_log_monitoring.py LOG_FILE.csv")`, so
  `python` on PATH must be Python 3.
- Only regenerate `results.txt` when an output change is intended; it is compared byte for byte.

## Layout

```
http_log_monitoring.py  entry point: reads the CSV in argv[1] row by row, feeds AnalyzeLogs
helpers.py              Statistics (counters for one window) and AnalyzeLogs (stats windows +
                        sliding alert window); config key constants
models.py               HttpLog: one CSV row; section = first path segment of the request
tests.py                unittest: end-to-end output vs results.txt, plus an alert/recover test
LOG_FILE.csv            sample input: header + 4,830 rows, timestamps partly out of order
results.txt             expected stdout for LOG_FILE.csv
```

## Configuration

No flags or environment variables. The defaults live in `AnalyzeLogs.__init__` (helpers.py) and
are passed as a dict keyed by the constants in helpers.py:

- `STATS_TIMESPAN` 10 s: length of a statistics window
- `ALERT_TIMESPAN` 120 s: length of the sliding alert window
- `TOLERANCE` 1 s: how late an out-of-order row may arrive before its window is printed
- `THRESHOLD` 10: average hits per second over the alert window that raises the alert

`AnalyzeLogs(config)` takes a replacement dict (all four keys required); the CLI does not expose it.

## Conventions / gotchas

- Input must have a header row (skipped unread) and exactly seven columns in this order:
  `remotehost, rfc931, authuser, date, request, status, bytes` (`HttpLog(*row)`). `date` is Unix
  seconds. All time logic uses these log timestamps, never the wall clock.
- `section` is the text between the first and second `/` of the request
  (`GET /api/user HTTP/1.0` gives `api`); a request with no `/` raises `IndexError`.
- `status` stays a string and anything other than `'200'` is listed under "Errors".
- Windows sit in a deque. A window is printed once a row arrives more than
  `STATS_TIMESPAN + TOLERANCE` seconds after its start. A row older than the oldest open window is
  left out of the statistics silently (it still counts toward the alert window), except before
  the second window exists (`first_iteration`), when it moves the first window's start back.
- Gaps in the log create empty windows, which print "The most hit section is None ...".
- There is no flush at end of input: windows still open when the file ends are never printed
  (with the sample log, 3 windows holding 21 of the 4,830 rows).
- The alert window counts rows, not distinct seconds: average = rows in the last
  `ALERT_TIMESPAN` seconds / `ALERT_TIMESPAN`. The alert and recovery messages print once per
  crossing (`alert_status`).
- Output wording and order are the test contract: statuses sorted as strings, requests by count
  descending. Any change to a `print` means regenerating `results.txt`.
- There is no `.gitignore`, so a stray `__pycache__/` shows up as untracked; delete it.

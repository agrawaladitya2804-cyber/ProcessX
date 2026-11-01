"""Input validation for the REST API (and for direct use of the algorithms).

Every problem found is collected, so the user sees ALL mistakes at once.
"""

import re

from backend.algorithms import ALGORITHMS
from backend.models import Process

MAX_PROCESSES = 50
MAX_ARRIVAL = 10_000
MAX_BURST = 1_000
MAX_PRIORITY = 1_000
MAX_QUANTUM = 1_000
DEFAULT_QUANTUM = 2

ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,10}$")
_INT_TEXT = re.compile(r"^[+-]?\d+$")


class ValidationError(ValueError):
    """Carries a list of human-readable problems in ``self.errors``."""

    def __init__(self, errors):
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__("; ".join(self.errors))


def to_int(value):
    """Convert ``value`` to int, or return None if it is not a whole number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str) and _INT_TEXT.match(value.strip()):
        return int(value.strip())
    return None


def _check_int(errors, label, raw, minimum, maximum, min_message):
    value = to_int(raw)
    if value is None:
        errors.append(f"{label} must be a whole number.")
        return None
    if value < minimum:
        errors.append(min_message)
        return None
    if value > maximum:
        errors.append(f"{label} cannot be greater than {maximum}.")
        return None
    return value


def parse_processes(raw):
    """Turn the JSON list sent by the browser into a list of ``Process``."""
    if not isinstance(raw, list) or len(raw) == 0:
        raise ValidationError("Add at least one process before running a simulation.")
    if len(raw) > MAX_PROCESSES:
        raise ValidationError(f"At most {MAX_PROCESSES} processes are supported.")

    errors, processes, seen = [], [], set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            errors.append(f"Process #{index}: must be an object with id, arrival_time and burst_time.")
            continue
        raw_id = item.get("id")
        pid = raw_id.strip() if isinstance(raw_id, str) else None
        tag = f"Process #{index}" + (f" ({pid})" if pid else "")
        before = len(errors)

        if not pid or not ID_PATTERN.match(pid):
            errors.append(f"{tag}: ID must be 1-10 characters (letters, digits, '-' or '_').")
        elif pid.lower() in seen:
            errors.append(f"{tag}: duplicate process ID '{pid}'.")
        else:
            seen.add(pid.lower())

        if "arrival_time" not in item:
            errors.append(f"{tag}: arrival_time is required.")
            at = None
        else:
            local = []
            at = _check_int(local, "Arrival time", item["arrival_time"], 0, MAX_ARRIVAL,
                            "Arrival time cannot be negative.")
            errors.extend(f"{tag}: {m}" for m in local)

        if "burst_time" not in item:
            errors.append(f"{tag}: burst_time is required.")
            bt = None
        else:
            local = []
            bt = _check_int(local, "Burst time", item["burst_time"], 1, MAX_BURST,
                            "Burst time must be greater than 0.")
            errors.extend(f"{tag}: {m}" for m in local)

        pr = 1   # priority is optional for the API; the UI always sends it
        if item.get("priority") is not None:
            local = []
            pr = _check_int(local, "Priority", item["priority"], 1, MAX_PRIORITY,
                            "Priority must be a positive whole number (1 or higher).")
            errors.extend(f"{tag}: {m}" for m in local)

        if len(errors) == before:
            processes.append(Process(pid, at, bt, pr))

    if errors:
        raise ValidationError(errors)
    return processes


def parse_algorithm(raw):
    key = raw.strip().upper() if isinstance(raw, str) else ""
    if key not in ALGORITHMS:
        raise ValidationError(
            "Unknown algorithm. Choose one of: " + ", ".join(ALGORITHMS) + "."
        )
    return key


def parse_time_quantum(raw, required=False):
    """Validate the Round Robin quantum. ``None`` means 'use the default'."""
    if raw is None or raw == "":
        if required:
            raise ValidationError("Time quantum is required for Round Robin.")
        return DEFAULT_QUANTUM
    errors = []
    value = _check_int(errors, "Time quantum", raw, 1, MAX_QUANTUM,
                       "Time quantum must be greater than 0.")
    if errors:
        raise ValidationError(errors)
    return value

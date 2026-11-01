"""A tiny helper that every algorithm uses to record what the CPU did.

The CPU timeline always starts at time 0. Whenever an algorithm asks the CPU to
start running something later than the end of the previous block, the gap is
recorded automatically as an IDLE segment. This means no algorithm can forget to
report idle time, and no algorithm can produce overlapping blocks.
"""


class GanttBuilder:
    def __init__(self):
        self.segments = []   # list of dicts, see _segment()
        self.cursor = 0      # end time of the last recorded segment

    @staticmethod
    def _segment(process_id, start, end):
        return {
            "process_id": process_id,   # None means the CPU was idle
            "start": start,
            "end": end,
            "idle": process_id is None,
        }

    def add(self, process_id, start, end):
        """Record that ``process_id`` ran on the CPU from ``start`` to ``end``."""
        if end <= start:
            raise ValueError(f"Empty or negative segment: {start}..{end}")
        if start < self.cursor:
            raise ValueError(
                f"Segment {start}..{end} overlaps the previous one (ends at {self.cursor})"
            )
        if start > self.cursor:  # CPU had nothing to run in between
            self.segments.append(self._segment(None, self.cursor, start))
        last = self.segments[-1] if self.segments else None
        if last and last["process_id"] == process_id and last["end"] == start:
            last["end"] = end    # same process continues: merge into one block
        else:
            self.segments.append(self._segment(process_id, start, end))
        self.cursor = end

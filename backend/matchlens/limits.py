"""Small, process-local demo work budget; not distributed production protection."""

import os
from collections import deque
from functools import lru_cache
from threading import Lock
from time import monotonic


class ModelBudget:
    def __init__(self, per_minute=6, total=50):
        self.per_minute, self.total = per_minute, total
        self.used = 0
        self.recent = deque()
        self.lock = Lock()

    def acquire(self, now=None):
        now = monotonic() if now is None else now
        with self.lock:
            while self.recent and now - self.recent[0] >= 60:
                self.recent.popleft()
            if self.used >= self.total or len(self.recent) >= self.per_minute:
                return False
            self.used += 1
            self.recent.append(now)
            return True


@lru_cache
def model_budget():
    return ModelBudget(
        per_minute=max(0, int(os.getenv("MATCHLENS_MODEL_REQUESTS_PER_MINUTE", "6"))),
        total=max(0, int(os.getenv("MATCHLENS_MODEL_REQUEST_LIMIT", "50"))),
    )

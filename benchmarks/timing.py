from time import perf_counter
from typing import Callable


class timing:
    t0: float
    elapsed: float

    def repeat(self, times: int, func: Callable, *args, **kwargs):
        for _ in range(times):
            func(*args, **kwargs)

    def __enter__(self):
        self.t0 = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = perf_counter() - self.t0

    def __str__(self):
        return f"{self.elapsed:.3f}s"

from time import perf_counter
from typing import Callable
from datetime import datetime


class timing:
    t0: float
    elapsed: float
    testing: str

    def __init__(self, logfile="logfile", header=f"{datetime.now()} benchmarks\n"):
        self.log = open(logfile, "a")
        self.header = header

    def repeat(self, times: int, func: Callable, *args, **kwargs):
        for _ in range(times):
            func(*args, **kwargs)

    def __enter__(self, testing="Elapsed: {}"):
        self.t0 = perf_counter()
        self.testing = testing
        self.log.write(self.header)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = perf_counter() - self.t0
        self.log.write(self.testing.format(self) + "\n\n")
        self.log.close()

    def __str__(self):
        return f"{self.elapsed:.3f}s"

# TODO: https://stackoverflow.com/a/10252925

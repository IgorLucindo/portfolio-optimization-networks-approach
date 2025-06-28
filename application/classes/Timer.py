import numpy as np
import time


class Timer:
    """
    Class for tracking running time and total runtime
    """
    def __init__(self, time_limit=float('inf')):
        self.timestamps = []
        self.runtimes = np.array([])
        self.runtimes_list = []
        self.runtimes_sum = []
        self.start_time = time.time()
        self.total_runtime = 0
        self.time_limit = time_limit


    def update(self):
        # Update instance runtimes
        self.runtimes = np.diff(self.timestamps)
        self.runtimes_list.append([round(float(t), 4) if t < self.time_limit else "TL" for t in self.runtimes])
        self.runtimes_sum.append(round(float(sum(self.runtimes)), 4))

        # Update total runtime
        self.total_runtime = time.time() - self.start_time


    def reset(self):
        self.timestamps = [time.time()]


    def mark(self):
        self.timestamps.append(time.time())
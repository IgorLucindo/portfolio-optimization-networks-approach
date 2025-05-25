import numpy as np
import time


class Timer:
    """
    Class for tracking running time and total runtime
    """
    def __init__(self):
        self.timestamps = []
        self.instance_runtimes = np.array([])
        self.start_time = time.time()
        self.total_runtime = 0


    def update(self):
        # Update instance runtimes
        self.instance_runtimes = np.diff(self.timestamps)

        # Update total runtime
        self.total_runtime = time.time() - self.start_time


    def reset(self):
        self.timestamps = [time.time()]


    def mark(self):
        self.timestamps.append(time.time())
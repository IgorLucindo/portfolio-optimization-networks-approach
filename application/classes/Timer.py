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
        self.instance_runtimes = [self.format_time(s) for s in self.instance_runtimes]

        # Update total runtime
        self.total_runtime = time.time() - self.start_time


    def reset(self):
        self.timestamps = [time.time()]


    def mark(self):
        self.timestamps.append(time.time())


    def format_time(self, total_seconds):
        """
        Format time in a readable way
        """
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = round(total_seconds % 60, 1)

        return (f"{hours}h " if hours else "") + (f"{minutes}min " if minutes else "") + f"{seconds}s"
import time

class SetTracker:
    def __init__(self, rest_threshold=10.0):
        self.rest_threshold = rest_threshold
        self.current_set = []
        self.last_rep_time = None
        self.sets = []

    def add_rep(self, rep_summary):
        now = time.time()

        if self.last_rep_time is not None:
            rest_time = now - self.last_rep_time

            if rest_time > self.rest_threshold:
                # end previous set
                self.sets.append(self.current_set)
                self.current_set = []

        self.current_set.append(rep_summary)
        self.last_rep_time = now

    def finalize(self):
        if self.current_set:
            self.sets.append(self.current_set)

    def get_sets(self):
        return self.sets
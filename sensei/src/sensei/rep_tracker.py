from sensei.src.sensei.faults.knee_callapse_fault import KneeCollapseFault


class RepTracker:
    def __init__(self):
        self.faults = [KneeCollapseFault()]
        self.is_active = False

    def reset(self):
        self.faults = [KneeCollapseFault()]

    def update(self, msg):
        for f in self.faults:
            f.check(msg)

    def get_summary(self):
        return {
            "faults": [f.result() for f in self.faults]
        }
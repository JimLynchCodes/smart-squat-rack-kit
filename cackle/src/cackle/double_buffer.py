class DoubleBufferState:
    def __init__(self):
        self.active = "a"

    def flip(self):
        self.active = "b" if self.active == "a" else "a"
        return self.active
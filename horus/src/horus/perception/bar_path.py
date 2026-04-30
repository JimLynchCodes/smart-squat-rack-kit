from horus.types import Point


class BarPathTracker:
    def __init__(self):
        self.prev_x: float | None = None

    def update(self, bar_pos: Point) -> float:
        x, _ = bar_pos

        if self.prev_x is None:
            self.prev_x = x
            return 0.0

        dx = x - self.prev_x
        self.prev_x = x
        return dx
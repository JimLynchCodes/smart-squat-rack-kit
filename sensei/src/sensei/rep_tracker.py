class RepTracker:
    """
    Stable Sensei RepTracker (contract-safe version)

    Guarantees (IMPORTANT):
    - last_score always exists
    - last_summary always exists
    - rep_finished is consumable event flag
    - no KeyErrors from missing state
    """

    def __init__(self, faults=None):

        # ---------------------------
        # EXTERNAL CONTRACT FIELDS
        # ---------------------------
        self.last_score = 0
        self.last_summary = {}
        self._rep_just_finished = False

        # ---------------------------
        # FAULTS
        # ---------------------------
        self.faults = faults or []

        # ---------------------------
        # STATE
        # ---------------------------
        self.reset()

    # =========================================================
    # PUBLIC FLAGS (SERVICE COMPAT)
    # =========================================================
    @property
    def rep_finished(self):
        """
        Legacy compatibility for service.py
        """
        return self._rep_just_finished

    def consume_rep_finished(self):
        """
        Preferred API (one-shot event)
        """
        if self._rep_just_finished:
            self._rep_just_finished = False
            return True
        return False

    # =========================================================
    # MAIN UPDATE
    # =========================================================
    def update(self, msg):

        if not msg:
            return

        metrics = msg.get("instant_metrics", {})
        bar = msg.get("bar", {})
        vel_y = bar.get("velocity_y", 0.0)

        # ---------------------------
        # COLLECT DATA
        # ---------------------------
        if self.rep_active:

            self.back_angles.append(metrics.get("back_angle", 0.0))
            self.knee_dists.append(metrics.get("knee_dist", 0.0))
            self.hip_positions.append(metrics.get("hip_y", 0.0))

            for f in self.faults:
                try:
                    r = f.check(msg)
                    if r:
                        self.fault_events.append(r)
                except:
                    pass

        self._update_state(msg, vel_y)

    # =========================================================
    # STATE MACHINE
    # =========================================================
    def _update_state(self, msg, vel_y):

        abs_vel = abs(vel_y)

        # ---------------------------
        # START REP
        # ---------------------------
        if vel_y > 0:

            if not self.rep_active:
                self.rep_active = True
                print("\n[sensei] Rep started")

            self.state = "DESCENT"

        # ---------------------------
        # ASCENT
        # ---------------------------
        elif vel_y < 0:
            self.state = "ASCENT"

        # ---------------------------
        # LOCKOUT → END REP
        # ---------------------------
        else:
            if self.rep_active:
                self._end_rep()

            self.state = "LOCKOUT"

    # =========================================================
    # END REP
    # =========================================================
    def _end_rep(self):

        summary = self.get_summary()
        score = self._score(summary)

        # 🔥 CONTRACT GUARANTEE FIELDS
        self.last_score = score
        self.last_summary = summary
        self._rep_just_finished = True

        print("\n[sensei] Rep complete")
        print(f"[sensei] Score: {score}/100")
        print(f"[sensei] Back Avg: {summary['back_avg']:.2f}°")
        print(f"[sensei] Back Max: {summary['back_max']:.2f}°")
        print(f"[sensei] Back Min: {summary['back_min']:.2f}°")

        self.reset()

    # =========================================================
    # SCORING
    # =========================================================
    def _score(self, s):

        score = 100

        if s["back_avg"] > 60:
            score -= 25
        elif s["back_avg"] > 45:
            score -= 10

        if s["knee_dist_avg"] < 0.05:
            score -= 15

        score -= len(self.fault_events) * 5

        return max(1, min(100, round(score, 1)))

    # =========================================================
    # SUMMARY
    # =========================================================
    def get_summary(self):

        return {
            "back_avg": self._avg(self.back_angles),
            "back_max": self._max(self.back_angles),
            "back_min": self._min(self.back_angles),

            "knee_dist_avg": self._avg(self.knee_dists),
            "hip_travel": self._travel(self.hip_positions),

            "faults": self.fault_events,
        }

    # =========================================================
    # RESET
    # =========================================================
    def reset(self):

        self.state = "LOCKOUT"
        self.rep_active = False

        self.back_angles = []
        self.knee_dists = []
        self.hip_positions = []
        self.fault_events = []

    # =========================================================
    # HELPERS
    # =========================================================
    def _avg(self, a):
        return sum(a) / len(a) if a else 0.0

    def _max(self, a):
        return max(a) if a else 0.0

    def _min(self, a):
        return min(a) if a else 0.0

    def _travel(self, a):
        return max(a) - min(a) if len(a) > 1 else 0.0
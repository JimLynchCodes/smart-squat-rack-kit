class WeightDistributionFault:
    name = "weight_distribution"

    def check(self, msg, state):
        hip_x = msg["hip_x"]
        left_ankle = msg["left_ankle_x"]
        right_ankle = msg["right_ankle_x"]

        center_base = (left_ankle + right_ankle) / 2

        offset = abs(hip_x - center_base)

        severity = min(1.0, offset / 100)

        return severity

    def result(self, severity):
        return {
            "fault": self.name,
            "severity": severity
        }
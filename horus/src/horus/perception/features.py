def compute_metrics(pose):
    hip = pose["hip"]
    knee = pose["knee"]

    return {
        "knee_angle_proxy": abs(knee[1] - hip[1]) * 100,
        "hip_height": hip[1]
    }
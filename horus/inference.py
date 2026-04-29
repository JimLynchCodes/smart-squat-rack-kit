def run_inference(front_frame, side_frame, frame_id: int):
    """
    Placeholder AI coach brain.
    This is where pose estimation + rep logic will live.
    """

    rep_count = frame_id // 30

    cue = "neutral"

    # fake logic for now
    if rep_count % 5 == 0:
        cue = "keep chest up"
    elif rep_count % 7 == 0:
        cue = "drive through heels"

    return {
        "frame_id": frame_id,
        "rep_count": rep_count,
        "cue": cue
    }
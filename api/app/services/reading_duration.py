def track_duration(item: dict) -> tuple[int, bool]:
    duration = item.get("duration_ms")
    if type(duration) is int and 0 < duration < 86_400_000:
        return duration, False
    estimate = item.get("estimated_duration_ms")
    if type(estimate) is not int or not 0 < estimate < 86_400_000:
        estimate = 300_000
    return estimate, True


def reading_summary(rows: list[dict], target: int) -> dict:
    durations = [track_duration(row["item"]) for row in rows]
    total = sum(duration for duration, _ in durations)
    return {
        "total_duration_ms": total,
        "tracks_count": len(rows),
        "duration_estimated": any(estimated for _, estimated in durations),
        "target_duration_ms": target,
        "target_met": total >= target,
        "shortfall_ms": max(0, target - total),
    }

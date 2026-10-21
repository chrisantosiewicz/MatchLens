"""Transparent event-only definitions; no tracking or causal inference."""

from math import hypot

from .models import Clock, Event, visible


def normalized(e: Event, point):
    return (point.x if e.attack_right else 105 - point.x, point.y)


def in_box(x, y):
    return x >= 88.5 and 13.84 <= y <= 54.16


def is_entry(e: Event) -> bool:
    return bool(
        e.start
        and e.end
        and e.event_type in {"pass", "carry"}
        and e.outcome == "complete"
        and not in_box(*normalized(e, e.start))
        and in_box(*normalized(e, e.end))
    )


def is_progressive(e: Event) -> bool:
    if e.event_type != "pass" or e.outcome != "complete" or not e.start or not e.end:
        return False
    sx, sy = normalized(e, e.start)
    ex, ey = normalized(e, e.end)
    return (
        not in_box(sx, sy) and hypot(105 - sx, 34 - sy) - hypot(105 - ex, 34 - ey) >= 10
    )


def player_stats(events: list[Event], player_id: str, viewer_clock: Clock) -> dict:
    actions = [
        e
        for e in visible(events, viewer_clock)
        if e.player_id == player_id and e.event_type not in {"substitution", "stoppage"}
    ]
    passes = [e for e in actions if e.event_type == "pass"]
    completed = sum(e.outcome == "complete" for e in passes)
    return {
        "actions": len(actions),
        "pass_attempts": len(passes),
        "completed_passes": completed,
        "pass_completion": round(100 * completed / len(passes), 1) if passes else None,
        "progressive_passes": sum(is_progressive(e) for e in actions),
        "shots": sum(e.event_type == "shot" for e in actions),
        "goals": sum(e.event_type == "shot" and e.outcome == "goal" for e in actions),
        "recoveries": sum(e.event_type == "recovery" for e in actions),
        "box_entries": sum(is_entry(e) for e in actions),
        "evidence_ids": [e.event_id for e in actions],
    }


def window_stats(events, duration_ms):
    if duration_ms <= 0:
        events = []
    entries = [e for e in events if is_entry(e)]
    routes = {"left": 0, "central": 0, "right": 0}
    for e in entries:
        # Flip both axes for attack-oriented lane labels after a direction switch.
        y = e.end.y if e.attack_right else 68 - e.end.y
        routes["right" if y < 68 / 3 else "left" if y > 136 / 3 else "central"] += 1
    return {
        "box_entries": len(entries),
        "routes": routes,
        "actions": sum(
            e.event_type not in {"stoppage", "substitution"} for e in events
        ),
        "duration_ms": duration_ms,
        "evidence_ids": [e.event_id for e in entries],
    }


def compare_windows(
    events: list[Event], anchor: Clock, viewer_clock: Clock, team_id: str
) -> dict:
    if (
        anchor.period != viewer_clock.period
        or anchor.elapsed_ms > viewer_clock.elapsed_ms
    ):
        raise ValueError(
            "Anchor must be in the viewer's current period and not in the future"
        )
    start = max(0, anchor.elapsed_ms - 600_000)
    end = min(viewer_clock.elapsed_ms, anchor.elapsed_ms + 600_000)
    allowed = [
        e
        for e in visible(events, viewer_clock)
        if e.period == anchor.period and e.team_id == team_id
    ]
    before = window_stats(
        [e for e in allowed if start <= e.elapsed_ms < anchor.elapsed_ms],
        anchor.elapsed_ms - start,
    )
    after = window_stats(
        [e for e in allowed if anchor.elapsed_ms <= e.elapsed_ms <= end],
        end - anchor.elapsed_ms,
    )
    return {
        "before": before,
        "after": after,
        "anchor": anchor.model_dump(),
        "provisional": end < anchor.elapsed_ms + 600_000
        or start != anchor.elapsed_ms - 600_000,
        "pattern_supported": before["box_entries"] >= 5 and after["box_entries"] >= 5,
        "team_id": team_id,
        "viewer_clock": viewer_clock.model_dump(),
    }

from collections import Counter

from .analytics import is_progressive
from .models import Clock, Event, Player, visible


def progressive_alerts(
    events: list[Event], players: list[Player], clock: Clock
) -> list[dict]:
    counts = Counter()
    roster = {p.id: p for p in players}
    alerts = []
    for event in sorted(
        visible(events, clock), key=lambda e: (e.period, e.elapsed_ms, e.sequence)
    ):
        if not event.player_id or not is_progressive(event):
            continue
        counts[event.player_id] += 1
        count = counts[event.player_id]
        if (
            event.period != clock.period
            or clock.elapsed_ms - event.elapsed_ms > 12000
            or count < 4
            or count % 4
        ):
            continue
        rank = 1 + sum(n > count for n in counts.values())
        if rank > 2 or event.player_id not in roster:
            continue
        others = sorted(
            [
                (pid, n)
                for pid, n in counts.items()
                if pid != event.player_id and pid in roster
            ],
            key=lambda x: (-x[1], x[0]),
        )
        runner = None
        if others:
            pid, n = others[0]
            runner = {
                "player_id": pid,
                "name": roster[pid].name,
                "count": n,
                "rank": 1 + sum(value > n for value in counts.values()),
            }
        alerts.append(
            {
                "id": f"progressive-{event.event_id}",
                "player_id": event.player_id,
                "name": roster[event.player_id].name,
                "number": roster[event.player_id].number,
                "count": count,
                "rank": rank,
                "runner_up": runner,
                "period": event.period,
                "elapsed_ms": event.elapsed_ms,
                "event_id": event.event_id,
            }
        )
    return alerts[-1:]

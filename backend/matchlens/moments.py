from .models import Clock, Event, visible


def key_moments(
    events: list[Event], player_id: str, viewer_clock: Clock, limit: int = 5
) -> list[dict]:
    allowed = visible(events, viewer_clock)
    possessions: dict[tuple, list[Event]] = {}
    for e in allowed:
        possessions.setdefault((e.period, e.possession_id), []).append(e)
    candidates = []
    for group in possessions.values():
        group.sort(key=lambda e: (e.elapsed_ms, e.sequence))
        own = [
            e
            for e in group
            if e.player_id == player_id
            and e.event_type not in {"stoppage", "substitution"}
        ]
        if not own:
            continue
        shots = [e for e in group if e.event_type == "shot"]
        own_shots = [e for e in shots if e.player_id == player_id]
        contributing_shots = [
            s
            for s in shots
            if any(
                e.team_id == s.team_id
                and (e.elapsed_ms, e.sequence) <= (s.elapsed_ms, s.sequence)
                for e in own
            )
        ]
        goal = next((e for e in own_shots if e.outcome == "goal"), None)
        recovery = next(
            (e for e in own if e.event_type in {"recovery", "tackle"}), None
        )
        if goal:
            rank, title, selected = 0, "Scored a goal", goal
        elif own_shots:
            rank, title, selected = 2, "Attempted a shot", own_shots[-1]
        elif contributing_shots:
            rank, title, selected = (
                1,
                "Involved in a shot-ending sequence",
                contributing_shots[-1],
            )
        elif recovery:
            rank, title, selected = 3, "Recorded a recovery or tackle", recovery
        else:
            continue
        sequence = [
            e
            for e in group
            if (e.elapsed_ms, e.sequence) <= (selected.elapsed_ms, selected.sequence)
        ]
        candidates.append(
            {
                "id": selected.event_id,
                "title": title,
                "rank": rank,
                "period": selected.period,
                "elapsed_ms": selected.elapsed_ms,
                "evidence_ids": [e.event_id for e in sequence],
                "sequence": [e.model_dump() for e in sequence],
                "explanation": "Selected from recorded match actions; off-ball contributions are not measured.",
            }
        )
    ordered = sorted(allowed, key=lambda e: (e.period, e.elapsed_ms, e.sequence))
    for i, loss in enumerate(ordered):
        if loss.player_id != player_id or loss.event_type != "turnover":
            continue
        following = []
        for e in ordered[i + 1 :]:
            if e.period != loss.period or e.elapsed_ms - loss.elapsed_ms > 20_000:
                break
            if e.team_id == loss.team_id and e.event_type == "recovery":
                break
            following.append(e)
            if e.event_type == "shot" and e.team_id != loss.team_id:
                seq = [loss] + following
                candidates.append(
                    {
                        "id": loss.event_id,
                        "title": "Turnover followed by an opposition shot",
                        "rank": 4,
                        "period": loss.period,
                        "elapsed_ms": loss.elapsed_ms,
                        "evidence_ids": [x.event_id for x in seq],
                        "sequence": [x.model_dump() for x in seq],
                        "explanation": "An opposition shot followed within 20 seconds; temporal association does not establish causation.",
                    }
                )
                break
    return sorted(
        candidates, key=lambda m: (m["rank"], -m["period"], -m["elapsed_ms"])
    )[: max(0, min(limit, 5))]

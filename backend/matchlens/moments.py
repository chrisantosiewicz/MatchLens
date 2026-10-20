from .models import Clock, Event, visible


def key_moments(events: list[Event], player_id: str, viewer_clock: Clock, limit: int = 5) -> list[dict]:
    allowed = visible(events, viewer_clock)
    possessions: dict[tuple, list[Event]] = {}
    for e in allowed:
        possessions.setdefault((e.period, e.possession_id), []).append(e)
    candidates = []
    for group in possessions.values():
        group.sort(key=lambda e: (e.elapsed_ms, e.sequence))
        own = [e for e in group if e.player_id == player_id and e.event_type not in {"stoppage", "substitution"}]
        if not own:
            continue
        shots = [e for e in group if e.event_type == "shot"]
        own_shots = [e for e in shots if e.player_id == player_id]
        goal = next((e for e in own_shots if e.outcome == "goal"), None)
        recovery = next((e for e in own if e.event_type in {"recovery", "tackle"}), None)
        if goal:
            rank, title, selected = 0, "Scored a goal", goal
        elif shots and any(e.team_id == shots[-1].team_id for e in own):
            rank, title, selected = 1, "Involved in a shot-ending sequence", shots[-1]
        elif own_shots:
            rank, title, selected = 2, "Attempted a shot", own_shots[-1]
        elif recovery:
            rank, title, selected = 3, "Recorded a recovery or tackle", recovery
        else:
            continue
        sequence = [e for e in group if e.elapsed_ms <= selected.elapsed_ms]
        candidates.append({"id": selected.event_id, "title": title, "rank": rank, "period": selected.period,
                           "elapsed_ms": selected.elapsed_ms, "evidence_ids": [e.event_id for e in sequence],
                           "sequence": [e.model_dump() for e in sequence],
                           "explanation": "Selected from recorded match actions; off-ball contributions are not measured."})
    return sorted(candidates, key=lambda m: (m["rank"], -m["period"], -m["elapsed_ms"]))[:min(limit, 5)]

from collections import Counter

from .analytics import player_stats
from .models import Clock, MatchFixture, visible
from .moments import key_moments


def minute(period: int, elapsed_ms: int) -> str:
    seconds = elapsed_ms // 1000
    return f"{(period - 1) * 45 + seconds // 60}:{seconds % 60:02d}"


def build_recap(
    match: MatchFixture, player_id: str, clock: Clock, language: str
) -> dict:
    player = next(p for p in match.players if p.id == player_id)
    events = sorted(
        visible(match.events, clock), key=lambda e: (e.period, e.elapsed_ms, e.sequence)
    )
    goals = [e for e in events if e.event_type == "shot" and e.outcome == "goal"]
    totals = Counter(e.team_id for e in goals)
    score = {team: totals[team] for team in match.teams}
    stats = player_stats(events, player_id, clock)
    moments = key_moments(events, player_id, clock, limit=None)
    evidence = list(stats["evidence_ids"])
    es = language == "es"
    selected = minute(clock.period, clock.elapsed_ms)
    parts = [
        f"En tu momento seleccionado: {selected}."
        if es
        else f"At your selected time: {selected}."
    ]
    if match.feed_completeness == "incomplete":
        parts.append(
            "Datos incompletos: los goles y acciones son solo los observados; la ausencia de un evento no demuestra que no ocurriera."
            if es
            else "Incomplete feed: goals and actions are observed only; a missing event does not prove it did not happen."
        )
    goal_context = None
    if goals:
        goal = goals[-1]
        sequence = [
            e
            for e in events
            if e.period == goal.period
            and e.possession_id == goal.possession_id
            and (e.elapsed_ms, e.sequence) <= (goal.elapsed_ms, goal.sequence)
        ]
        involved = any(
            e.team_id == goal.team_id
            and (
                e.player_id == player_id
                or (
                    e.event_type == "pass"
                    and e.outcome == "complete"
                    and e.recipient_id == player_id
                )
            )
            for e in sequence
        )
        scorer = next(
            (p.name for p in match.players if p.id == goal.player_id), "Unknown player"
        )
        goal_time = minute(goal.period, goal.elapsed_ms)
        parts.append(
            f"Último gol, {goal_time}: marcó {scorer}."
            if es
            else f"Latest goal, {goal_time}: {scorer} scored."
        )
        parts.append(
            (
                f"{player.name} participó en la secuencia registrada del gol."
                if involved
                else f"{player.name} no participó en la secuencia registrada del gol."
            )
            if es
            else (
                f"{player.name} was involved in the recorded goal sequence."
                if involved
                else f"{player.name} was not involved in the recorded goal sequence."
            )
        )
        evidence.extend(e.event_id for e in sequence)
        goal_context = {
            "event_id": goal.event_id,
            "minute": goal_time,
            "scorer": scorer,
            "player_involved": involved,
        }
    else:
        parts.append(
            "No hay goles registrados hasta este momento."
            if es
            else "No goals have been recorded by this time."
        )
    if es:
        parts.append(
            f"{player.name} completó {stats['completed_passes']} pases y registró {stats['shots']} tiros."
        )
        parts.append(
            f"Tiene {len(moments)} momentos clave registrados."
            if moments
            else "Todavía no tiene momentos clave registrados."
        )
        parts.append(
            f"Resumen: {stats['progressive_passes']} pases progresivos y {stats['recoveries']} recuperaciones en los eventos disponibles. El resumen no evalúa movimientos sin balón."
        )
    else:
        pass_word = "pass" if stats["completed_passes"] == 1 else "passes"
        shot_word = "shot" if stats["shots"] == 1 else "shots"
        parts.append(
            f"{player.name} completed {stats['completed_passes']} {pass_word} and recorded {stats['shots']} {shot_word}."
        )
        parts.append(
            f"He has {len(moments)} key recorded moments."
            if moments
            else "He has had no key recorded moments yet."
        )
        parts.append(
            f"Summary: {stats['progressive_passes']} progressive passes and {stats['recoveries']} recoveries in the available events. Off-ball contributions are not assessed."
        )
    position_frame_ids = []
    if match.position_frames:
        from .set_pieces import corner_context

        corners = corner_context(match, clock, language)["corners"]
        if corners:
            latest = corners[-1]
            parts.append(("Último córner: " if es else "Latest corner: ") + latest["text"])
            evidence.extend(latest["evidence_ids"])
            position_frame_ids = latest["position_frame_ids"]
    return {
        "text": " ".join(parts),
        "selected_time": selected,
        "score": score,
        "goal_context": goal_context,
        "moment_count": len(moments),
        "stats": stats,
        "evidence_ids": list(dict.fromkeys(evidence)),
        "generation_mode": "template",
        "position_frame_ids": position_frame_ids,
    }

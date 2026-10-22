"""Deterministic narrative evidence, never off-ball or causal inference."""

from .analytics import is_progressive
from .models import visible


def sequence_stories(match, player_id, clock, start_ms=0):
    if match.feed_completeness != "complete":
        return []
    player = next(p for p in match.players if p.id == player_id)
    names = {p.id: p.name for p in match.players}
    events = sorted(
        [
            e
            for e in visible(match.events, clock)
            if e.period == clock.period and e.elapsed_ms >= start_ms
        ],
        key=lambda e: (e.elapsed_ms, e.sequence),
    )
    groups = {}
    for e in events:
        groups.setdefault(e.possession_id, []).append(e)
    stories = []

    def add(kind, chain, action, terminal, meaning, meaning_es, limit, limit_es):
        def stamp(e):
            seconds = e.elapsed_ms // 1000
            return f"{(e.period - 1) * 45 + seconds // 60}:{seconds % 60:02}"

        stories.append(
            {
                "id": f"{kind}:{action.event_id}:{terminal.event_id}",
                "kind": kind,
                "player_name": player.name,
                "sequence_duration_seconds": (terminal.elapsed_ms - action.elapsed_ms)
                / 1000,
                "review_window_seconds": 20
                if kind == "turnover_then_opposition_shot"
                else 30,
                "action_clock": stamp(action),
                "outcome_clock": stamp(terminal),
                "player_action_progressive": is_progressive(action),
                "outcome": terminal.outcome
                if terminal.event_type == "shot"
                else terminal.event_type,
                "outcome_player": names.get(terminal.player_id, "opponent"),
                "meaning_en": meaning,
                "meaning_es": meaning_es,
                "limitation_en": limit,
                "limitation_es": limit_es,
                "evidence_ids": [e.event_id for e in chain],
                "sequence": [e.model_dump() for e in chain],
            }
        )

    for group in groups.values():
        for index, terminal in enumerate(group):
            if (
                terminal.event_type not in {"shot", "turnover"}
                or terminal.team_id != player.team_id
            ):
                continue
            prior = group[:index]
            own = [
                e
                for e in prior
                if e.player_id == player_id
                and e.event_type in {"pass", "carry"}
                and e.outcome == "complete"
            ]
            if not own or terminal.elapsed_ms - own[-1].elapsed_ms > 30000:
                continue
            action = own[-1]
            chain = group[group.index(action) : index + 1]
            # No credit across an opposing touch, failed pass, or an earlier terminal event.
            if any(
                e.team_id != player.team_id
                or e.event_type in {"turnover", "shot"}
                or (e.event_type == "pass" and e.outcome != "complete")
                for e in chain[:-1]
            ):
                continue
            if terminal.event_type == "shot" and terminal.player_id != player_id:
                add(
                    "shot_build_up",
                    chain,
                    action,
                    terminal,
                    "Recorded build-up involvement can be missed by headline progressive-pass totals; a connecting pass can belong to a shot-ending move without qualifying as progressive.",
                    "La participación registrada en la jugada puede quedar oculta en el total de pases progresivos: un pase de conexión puede formar parte de una secuencia con tiro sin ser progresivo.",
                    "Sequence involvement is not an assist, proof of chance quality, or proof that this pass caused the shot.",
                    "Participar en la secuencia no equivale a una asistencia ni demuestra calidad de ocasión o causalidad.",
                )
            elif terminal.event_type == "turnover" and is_progressive(action):
                add(
                    "progression_without_shot",
                    chain,
                    action,
                    terminal,
                    "Moving the ball closer to goal and producing a shot are different outcomes: this recorded progression ended in a turnover before a shot.",
                    "Acercar el balón a la portería y producir un tiro son resultados distintos: esta progresión terminó en una pérdida antes de un tiro.",
                    "This does not prove a poor pass or a poor decision; the feed does not explain defensive pressure or alternatives.",
                    "Esto no demuestra un mal pase ni una mala decisión; el flujo no describe presión defensiva ni alternativas.",
                )
    for index, loss in enumerate(events):
        if loss.player_id != player_id or loss.event_type != "turnover":
            continue
        chain = [loss]
        for e in events[index + 1 :]:
            if e.elapsed_ms - loss.elapsed_ms > 20000 or (
                e.team_id == player.team_id
                and (
                    e.event_type in {"recovery", "tackle", "shot"}
                    or (e.event_type in {"pass", "carry"} and e.outcome == "complete")
                )
            ):
                break
            chain.append(e)
            if e.event_type == "shot":
                if e.team_id != player.team_id:
                    add(
                        "turnover_then_opposition_shot",
                        chain,
                        loss,
                        e,
                        "An opposition attempt followed this turnover within 20 seconds, making this a useful sequence to review for transition risk.",
                        "Un tiro rival siguió a esta pérdida en menos de 20 segundos: es una secuencia útil para revisar el riesgo en transición.",
                        "Timing is not causation or sole responsibility; pressure, support and alternative decisions are unobserved.",
                        "El orden temporal no demuestra causalidad ni responsabilidad exclusiva; no se observan presión, apoyos ni alternativas.",
                    )
                break
    # One recent example of each kind; keep the model packet small and varied.
    selected = []
    for kind in (
        "shot_build_up",
        "progression_without_shot",
        "turnover_then_opposition_shot",
    ):
        options = [s for s in stories if s["kind"] == kind]
        if options:
            selected.append(options[-1])
    return selected


def render_story(story, language="en"):
    if language == "es":
        outcome = {
            "saved": "tiro parado",
            "wide": "tiro fuera",
            "goal": "gol",
            "turnover": "pérdida",
        }.get(story["outcome"], story["outcome"])
        return (
            f"A las {story['action_clock']}, {story['player_name']} participó en una secuencia registrada "
            f"que terminó a las {story['outcome_clock']} ({outcome}). "
            f"{story['meaning_es']} {story['limitation_es']}"
        )
    return (
        f"At {story['action_clock']}, {story['player_name']} contributed to a recorded sequence ending "
        f"at {story['outcome_clock']} ({story['outcome']}). "
        f"{story['meaning_en']} {story['limitation_en']}"
    )

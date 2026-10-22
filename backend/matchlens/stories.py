"""Deterministic narrative evidence, never off-ball or causal inference."""

from .analytics import is_entry, is_progressive
from .editorial import POLICY_VERSION, action_location
from .models import visible


def sequence_stories(match, player_id, clock, start_ms=0, include_all=False):
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
                "policy_version": POLICY_VERSION,
                "qualifying_outcome": "shot"
                if terminal.event_type == "shot"
                else "box entry"
                if any(is_entry(e) for e in chain)
                else terminal.event_type,
                "action_location": action_location(action),
                "pass_rank_before_shot": sum(
                    e.event_type == "pass" and e.outcome == "complete"
                    for e in chain[:-1]
                )
                if kind == "shot_build_up" and action.event_type == "pass"
                else None,
                "subsequent_on_ball_actions": sum(
                    e.event_type not in {"stoppage", "substitution"} for e in chain[1:]
                ),
                "intervening_on_ball_actions": sum(
                    e.event_type not in {"stoppage", "substitution"}
                    for e in chain[1:-1]
                ),
                "immediate_attempt": kind == "turnover_then_opposition_shot"
                and sum(
                    e.event_type not in {"stoppage", "substitution"}
                    for e in chain[1:-1]
                )
                <= 1,
                "loss_player": names.get(terminal.player_id)
                if terminal.event_type == "turnover"
                else None,
                "prohibited_inferences": [
                    "line break",
                    "tempo intent",
                    "defensive presence",
                    "nearby support",
                    "receiver control error",
                    "sole blame",
                    "causation",
                ],
                "player_name": player.name,
                "sequence_duration_seconds": (terminal.elapsed_ms - action.elapsed_ms)
                / 1000,
                "review_window_seconds": 20
                if kind
                in {"turnover_then_opposition_shot", "recovery_followed_by_attack"}
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
                if (
                    sum(
                        e.event_type == "pass" and e.outcome == "complete"
                        for e in chain[:-1]
                    )
                    > 3
                ):
                    continue
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
    for group in groups.values():
        for i, recovery in enumerate(group):
            if recovery.player_id != player_id or recovery.event_type != "recovery":
                continue
            chain = [recovery]
            first_entry = None
            terminal = None
            for e in group[i + 1 :]:
                if (
                    e.elapsed_ms - recovery.elapsed_ms > 20000
                    or e.team_id != player.team_id
                    or e.event_type == "substitution"
                ):
                    break
                if (
                    e.event_type not in {"stoppage", "substitution"}
                    and sum(
                        x.event_type not in {"stoppage", "substitution"}
                        for x in chain[1:]
                    )
                    >= 5
                ):
                    break
                chain.append(e)
                if is_entry(e) and first_entry is None:
                    first_entry = e
                if e.event_type in {"shot", "turnover", "stoppage"} or (
                    e.event_type == "pass" and e.outcome == "incomplete"
                ):
                    terminal = e
                    break
            if terminal is None:
                terminal = first_entry
            if terminal and (terminal.event_type == "shot" or first_entry):
                selected_chain = chain[: chain.index(terminal) + 1]
                add(
                    "recovery_followed_by_attack",
                    selected_chain,
                    recovery,
                    terminal,
                    "A recorded recovery was followed by a box entry or shot in the same possession, connecting ball recovery with an observable attacking outcome.",
                    "Una recuperación registrada fue seguida por una entrada al área o un tiro en la misma posesión: conecta la recuperación con un resultado ofensivo observable.",
                    "Followed by is sequence membership, not proof of creating a counterattack or beating pressure.",
                    "Seguido por describe la secuencia; no demuestra que creara un contraataque ni superara presión.",
                )
    for index, loss in enumerate(events):
        if loss.player_id != player_id or loss.event_type != "turnover":
            continue
        chain = [loss]
        for e in events[index + 1 :]:
            if (
                e.event_type in {"stoppage", "substitution"}
                or e.elapsed_ms - loss.elapsed_ms > 20000
                or (
                    e.team_id == player.team_id
                    and (
                        e.event_type in {"recovery", "tackle", "shot"}
                        or (
                            e.event_type in {"pass", "carry"}
                            and e.outcome == "complete"
                        )
                    )
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
    if include_all:
        return stories
    # One recent example of each kind; keep the model packet small and varied.
    selected = []
    for kind in (
        "shot_build_up",
        "progression_without_shot",
        "turnover_then_opposition_shot",
        "recovery_followed_by_attack",
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
    location = story.get("action_location", {})
    route = (
        f" from the {location['origin_zone']} to the {location['destination_zone']}"
        if location.get("destination_zone")
        else f" in the {location['origin_zone']}"
        if location.get("available")
        else ""
    )
    rank = story.get("pass_rank_before_shot")
    if story["kind"] == "shot_build_up" and rank:
        ordinal = {1: "last", 2: "second-last", 3: "third-last"}[rank]
        located_pass = (
            f"{location['distance_m']}m pass from {location['origin_half']} ({location['origin_zone']}) into the {location['destination_zone']}"
            if location.get("destination_zone")
            else "completed pass"
        )
        fact = (
            f"At {story['action_clock']}, {story['player_name']}'s {located_pass} was the {ordinal} completed pass "
            f"before {story['outcome_player']}'s shot at {story['outcome_clock']} ({story['outcome']})."
        )
        return fact + " " + story["meaning_en"] + " " + story["limitation_en"]
    if story["kind"] == "progression_without_shot":
        fact = (
            f"At {story['action_clock']}, {story['player_name']} completed a progressive pass{route}. "
            f"The recorded move ended with {story['loss_player'] or 'a teammate'}'s turnover at {story['outcome_clock']}, "
            f"after {story['intervening_on_ball_actions']} intervening on-ball actions."
        )
        return fact + " " + story["limitation_en"]
    if story["kind"] == "turnover_then_opposition_shot":
        return (
            f"{story['player_name']}'s recorded turnover at {story['action_clock']}{route} was followed by "
            f"an opposition shot at {story['outcome_clock']}, with {story['intervening_on_ball_actions']} intervening on-ball actions. "
            + story["limitation_en"]
        )
    if story["kind"] == "recovery_followed_by_attack":
        return (
            f"{story['player_name']}'s recovery at {story['action_clock']}{route} was followed by "
            f"{story['subsequent_on_ball_actions']} on-ball actions in a recorded {story['qualifying_outcome']} sequence ending at {story['outcome_clock']} ({story['outcome']}). "
            + story["limitation_en"]
        )
    return (
        f"At {story['action_clock']}, {story['player_name']} contributed to a recorded sequence ending "
        f"at {story['outcome_clock']} ({story['outcome']}). "
        f"{story['meaning_en']} {story['limitation_en']}"
    )

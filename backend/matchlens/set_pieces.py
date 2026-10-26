"""Fail-closed positional facts for synthetic corner sequences."""

from .analytics import in_box
from .corner_data import active_players
from .models import visible


def box_occupancy(positions, players, team_id, attack_right):
    inside = [
        players[p["player_id"]]
        for p in positions
        if in_box(
            round(p["point"]["x"] if attack_right else 105 - p["point"]["x"], 5),
            round(p["point"]["y"], 5),
        )
    ]
    return {
        "attackers": sum(p.team_id == team_id for p in inside),
        "defenders": sum(p.team_id != team_id for p in inside),
        "defending_goalkeepers": sum(
            p.team_id != team_id and p.position == "GK" for p in inside
        ),
    }


def stamp(event):
    seconds = event.elapsed_ms // 1000
    return f"{(event.period - 1) * 45 + seconds // 60}:{seconds % 60:02}"


def valid_phase_sequence(group, match, players):
    expected = ["setup", "delivery", "first_contact", "outcome"]
    if [e.set_piece.phase for e in group] != expected[: len(group)]:
        return False
    setup = group[0]
    for event in group:
        if event.period != setup.period:
            return False
        if event.set_piece.phase == "setup":
            if event.event_type != "stoppage":
                return False
            continue
        if event.player_id not in active_players(match, event.period, event.elapsed_ms):
            return False
        if (
            event.player_id not in players
            or players[event.player_id].team_id != event.team_id
        ):
            return False
        if event.set_piece.phase == "delivery":
            if (
                event.event_type != "pass"
                or event.team_id != setup.team_id
                or event.outcome not in {"complete", "incomplete"}
            ):
                return False
        elif event.set_piece.phase == "first_contact":
            if event.event_type not in {"touch", "recovery"} or event.outcome not in {
                "recorded",
                "complete",
            }:
                return False
        elif event.event_type == "shot":
            if event.outcome not in {"wide", "saved", "goal"}:
                return False
        elif event.event_type == "pass":
            if event.outcome not in {"complete", "incomplete"}:
                return False
            if event.outcome == "complete" and (
                event.recipient_id not in players
                or players[event.recipient_id].team_id != event.team_id
            ):
                return False
        else:
            return False
    return True


def corner_context(match, clock, language="en"):
    es = language == "es"
    events = sorted(
        visible(match.events, clock), key=lambda e: (e.period, e.elapsed_ms, e.sequence)
    )
    players = {p.id: p for p in match.players}
    groups = {}
    for e in events:
        if e.set_piece:
            groups.setdefault(e.set_piece.id, []).append(e)
    corners = []
    for sid, group in groups.items():
        setup = next((e for e in group if e.set_piece.phase == "setup"), None)
        if setup is None:
            continue
        delivery = next((e for e in group if e.set_piece.phase == "delivery"), None)
        contact = next((e for e in group if e.set_piece.phase == "first_contact"), None)
        outcome = next((e for e in group if e.set_piece.phase == "outcome"), None)
        shape_valid = valid_phase_sequence(group, match, players)
        if not shape_valid:
            delivery = contact = outcome = None
        phases = []
        anchors = {e.event_id: e for e in group}
        bundle_current = all(
            f.anchor_event_revision == anchors[f.anchor_event_id].revision
            for f in match.position_frames
            if f.anchor_event_id in anchors
        )
        for event in group:
            matches = [
                f
                for f in match.position_frames
                if f.anchor_event_id == event.event_id
                and (f.period, f.elapsed_ms) <= (clock.period, clock.elapsed_ms)
            ]
            frame = matches[0] if len(matches) == 1 else None
            ids = [p.player_id for p in frame.positions] if frame else []
            valid = bool(
                frame
                and shape_valid
                and bundle_current
                and match.feed_completeness == "complete"
                and frame.anchor_event_revision == event.revision
                and (frame.period, frame.elapsed_ms) == (event.period, event.elapsed_ms)
                and len(ids) == len(set(ids)) == 22
                and set(ids) == active_players(match, event.period, event.elapsed_ms)
            )
            positions = [p.model_dump() for p in frame.positions] if valid else []
            phases.append(
                {
                    "phase": event.set_piece.phase,
                    "period": event.period,
                    "elapsed_ms": event.elapsed_ms,
                    "available": valid,
                    "unavailable_reason": None
                    if valid
                    else "missing_or_stale_positional_evidence",
                    "frame_id": frame.frame_id if valid else None,
                    "frame_revision": frame.revision if valid else None,
                    "anchor_event_id": event.event_id,
                    "anchor_event_revision": event.revision,
                    "positions": positions,
                    "ball": frame.ball.model_dump() if valid else None,
                    "counts": box_occupancy(
                        positions, players, setup.team_id, setup.attack_right
                    )
                    if valid
                    else None,
                }
            )
        df = next(
            (f for f in phases if f["phase"] == "delivery" and f["available"]), None
        )
        sf = next((f for f in phases if f["phase"] == "setup" and f["available"]), None)
        entered = []
        if df and sf:
            before = {p["player_id"]: p["point"] for p in sf["positions"]}
            for p in df["positions"]:
                if players[p["player_id"]].team_id != setup.team_id:
                    continue
                b, a = before.get(p["player_id"]), p["point"]
                if b is None:
                    continue
                if not in_box(
                    b["x"] if setup.attack_right else 105 - b["x"], b["y"]
                ) and in_box(a["x"] if setup.attack_right else 105 - a["x"], a["y"]):
                    entered.append(p["player_id"])
        team = match.teams[setup.team_id]
        text = (
            f"{team}: córner a las {stamp(delivery or setup)}."
            if es
            else f"{team}: corner at {stamp(delivery or setup)}."
        )
        if df:
            c = df["counts"]
            keeper_label = (
                "goalkeeper" if c["defending_goalkeepers"] == 1 else "goalkeepers"
            )
            text += (
                f" {c['attackers']} atacantes y {c['defenders']} defensores en el área al sacar ({c['defending_goalkeepers']} porteros incluidos)."
                if es
                else f" {c['attackers']} attackers and {c['defenders']} defenders are in the box at delivery ({c['defending_goalkeepers']} {keeper_label} included)."
            )
            if entered:
                text += (
                    f" {len(entered)} atacantes pasan de fuera a dentro del área entre las dos instantáneas."
                    if es
                    else f" {len(entered)} attackers move from outside to inside the box between setup and delivery snapshots."
                )
        else:
            text += (
                " El recuento al sacar no está disponible todavía."
                if es
                else " Delivery occupancy is not available yet."
            )
        if contact and contact.player_id in players:
            name = players[contact.player_id].name
            text += (
                f" {name} realiza el primer contacto registrado."
                if es
                else f" {name} makes the recorded first contact."
            )
        if outcome:
            name = players[outcome.player_id].name
            if outcome.event_type == "shot":
                label = {"wide": "fuera", "saved": "parado", "goal": "gol"}.get(
                    outcome.outcome, outcome.outcome
                )
                text += (
                    f" {name} remata a las {stamp(outcome)}: {label}."
                    if es
                    else f" {name} shoots at {stamp(outcome)}: {outcome.outcome}."
                )
            elif outcome.outcome == "complete":
                recipient = players[outcome.recipient_id].name
                text += (
                    f" Después, {name} completa un pase a {recipient}."
                    if es
                    else f" Then {name} completes a pass to {recipient}."
                )
            else:
                text += (
                    f" El siguiente pase de {name} queda incompleto."
                    if es
                    else f" {name}'s follow-up pass is incomplete."
                )
        corners.append(
            {
                "id": sid,
                "team_id": setup.team_id,
                "attack_right": setup.attack_right,
                "period": setup.period,
                "elapsed_ms": setup.elapsed_ms,
                "delivery_clock": stamp(delivery) if delivery else None,
                "text": text,
                "frames": phases,
                "entered_box_ids": entered,
                "first_contact": {
                    "player_id": contact.player_id,
                    "event_id": contact.event_id,
                    "clock": stamp(contact),
                }
                if contact
                else None,
                "outcome": {
                    "event_id": outcome.event_id,
                    "event_type": outcome.event_type,
                    "outcome": outcome.outcome,
                    "clock": stamp(outcome),
                }
                if outcome
                else None,
                "events": [e.model_dump() for e in group],
                "evidence_ids": [e.event_id for e in group],
                "event_revisions": {e.event_id: e.revision for e in group},
                "position_frame_ids": [f["frame_id"] for f in phases if f["available"]],
                "limitation": "Posiciones simuladas en instantes concretos; no demuestran intención, presión, jugadores desmarcados ni creación de espacios."
                if es
                else "Simulated positions at discrete moments; they do not establish intent, pressure, unmarked options or space creation.",
            }
        )
    return {
        "available": bool(match.position_frames),
        "synthetic": True,
        "data_mode": "simulated_position_snapshots",
        "viewer_clock": clock.model_dump(),
        "generation_mode": "template",
        "corners": corners,
        "players": [p.model_dump() for p in match.players],
    }


def is_corner_question(question):
    return any(
        word in question.lower()
        for word in (
            "corner",
            "córner",
            "box occupancy",
            "in the box",
            "en el área",
            "en el area",
        )
    )


def corner_answer(match, request):
    from .models import Clock

    es = request["language"] == "es"
    context = corner_context(
        match,
        Clock(period=request["period"], elapsed_ms=request["elapsed_ms"]),
        request["language"],
    )
    corner = context["corners"][-1] if context["corners"] else None
    text = (
        corner["text"]
        if corner
        else (
            "No hay un córner observado con posiciones simuladas en este tiempo."
            if es
            else "No observed corner with simulated positions is available at this clock."
        )
    )
    if corner:
        delivery = next(
            (
                f
                for f in corner["frames"]
                if f["phase"] == "delivery" and f["available"]
            ),
            None,
        )
        if delivery:
            point = next(
                (
                    p["point"]
                    for p in delivery["positions"]
                    if p["player_id"] == request["player_id"]
                ),
                None,
            )
            inside = point is not None and in_box(
                point["x"] if corner["attack_right"] else 105 - point["x"], point["y"]
            )
            name = next(p.name for p in match.players if p.id == request["player_id"])
            text += (
                (
                    f" No hay posición de saque registrada para {name}."
                    if es
                    else f" No delivery position is recorded for {name}."
                )
                if point is None
                else f" {name} está {'dentro' if inside else 'fuera'} del área al sacar."
                if es
                else f" {name} is {'inside' if inside else 'outside'} the box at delivery."
            )
        text += " " + corner["limitation"]
    return {
        "text": text,
        "intent": "corner_context",
        "generation_mode": "template",
        "notice": "Deterministic synthetic positional context · no model call",
        "model_calls": 0,
        "evidence_ids": corner["evidence_ids"] if corner else [],
        "event_revisions": corner["event_revisions"] if corner else {},
        "position_frame_ids": corner["position_frame_ids"] if corner else [],
        "position_fact_support": corner["frames"] if corner else [],
        "language": request["language"],
        "viewer_clock": context["viewer_clock"],
    }

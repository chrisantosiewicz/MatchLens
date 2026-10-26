"""Explicit synthetic corner frames; these are never inferred from ball events."""

import random
from collections import Counter

from .models import Event, PlayerPosition, Point, PositionFrame, SetPiece

PHASES = ("setup", "delivery", "first_contact", "outcome")


def active_players(match, period, elapsed_ms):
    active = {p.id for p in match.players if p.starter}
    for e in sorted(match.events, key=lambda e: (e.period, e.elapsed_ms, e.sequence)):
        if (e.period, e.elapsed_ms) > (period, elapsed_ms):
            break
        if e.event_type == "substitution":
            active.discard(e.player_id)
            active.add(e.recipient_id)
    return active


def add_corner_scenarios(base, seed):
    rng = random.Random(seed + 23000)
    match_id = f"match-{seed}-corners"
    events = [
        e.model_copy(
            update={
                "match_id": match_id,
                "event_id": e.event_id.replace(base.id, match_id),
            }
        )
        for e in base.events
    ]
    frames = []
    roster = {p.id: p for p in base.players}
    for index, (period, block, team, defended) in enumerate(
        [(1, 40, "north", False), (2, 35, "harbor", True), (2, 38, "north", False)]
    ):
        start = block * 30000
        events = [
            e
            for e in events
            if not (e.period == period and e.possession_id == f"p{period}-{block}")
        ]
        active = active_players(base, period, start)
        own = [p for p in base.players if p.id in active and p.team_id == team]
        opponents = [p for p in base.players if p.id in active and p.team_id != team]
        taker = next(p for p in own if p.position == "W")
        receiver = next(p for p in own if p.number == 3)
        defender = next(p for p in opponents if p.number == 3)
        cleared_to = next(p for p in opponents if p.number == 2)
        right = (team == "north") == (period == 1)
        sid = f"{match_id}-corner-{index + 1}"
        own_box = {
            3: [(88, 26), (93, 25), (96, 25), (96, 25)],
            4: [(87, 40), (92, 42), (96, 44), (96, 44)],
            6: [(87, 34), (89.5, 35), (93, 36), (94, 36)],
            8: [(89, 49), (91, 49), (93, 48), (94, 48)],
            11: [(90, 30), (94, 32), (97, 34), (98, 34)],
        }
        def_box = {
            1: (103.5, 34),
            2: (95, 24),
            3: (96, 42),
            4: (92, 30),
            5: (94, 38),
            6: (90, 46),
            7: (89.5, 20),
            8: (97, 33),
        }
        # One seeded offset per player keeps paths coherent across sparse frames.
        jitter = {
            p.id: (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12))
            for p in own + opponents
        }

        def point(x, y, right=right):
            return Point(
                x=round(x if right else 105 - x, 2), y=round(y if right else 68 - y, 2)
            )

        phase_positions = []
        for phase_index in range(4):
            positions = []
            for p in own + opponents:
                if p.id == taker.id:
                    x, y = (104.6, 0.5)
                elif p.team_id == team:
                    x, y = (
                        own_box[p.number][phase_index]
                        if p.number in own_box
                        else (
                            (3, 34)
                            if p.position == "GK"
                            else (60 + p.number, 8 + 4 * p.number)
                        )
                    )
                else:
                    x, y = def_box.get(p.number, (75 + p.number / 2, 10 + 3 * p.number))
                    if defended and p.id == defender.id:
                        x, y = [(96, 42), (96, 34), (95, 24), (95, 24)][phase_index]
                    if defended and p.id == cleared_to.id and phase_index == 3:
                        x, y = (75, 16)
                dx, dy = jitter[p.id]
                positions.append(
                    PlayerPosition(player_id=p.id, point=point(x + dx, y + dy))
                )
            phase_positions.append(positions)
        contact_actor = defender if defended else receiver
        contact = next(
            p.point for p in phase_positions[2] if p.player_id == contact_actor.id
        )
        kick = point(105, 0.2)
        outcome_end = (
            next(p.point for p in phase_positions[3] if p.player_id == cleared_to.id)
            if defended
            else point(105, 34)
        )
        corner_events = [
            Event(
                match_id=match_id,
                event_id=sid + "-setup",
                period=period,
                elapsed_ms=start + 1000,
                team_id=team,
                event_type="stoppage",
                possession_id=sid,
                attack_right=right,
                set_piece=SetPiece(id=sid, phase="setup"),
            ),
            Event(
                match_id=match_id,
                event_id=sid + "-delivery",
                period=period,
                elapsed_ms=start + 4000,
                team_id=team,
                player_id=taker.id,
                recipient_id=None if defended else receiver.id,
                event_type="pass",
                outcome="incomplete" if defended else "complete",
                start=kick,
                end=contact,
                possession_id=sid,
                attack_right=right,
                set_piece=SetPiece(id=sid, phase="delivery"),
            ),
            Event(
                match_id=match_id,
                event_id=sid + "-contact",
                period=period,
                elapsed_ms=start + 7000,
                team_id=contact_actor.team_id,
                player_id=contact_actor.id,
                event_type="recovery" if defended else "touch",
                outcome="recorded",
                start=contact,
                possession_id=sid,
                attack_right=right if not defended else not right,
                set_piece=SetPiece(id=sid, phase="first_contact"),
            ),
            Event(
                match_id=match_id,
                event_id=sid + "-outcome",
                period=period,
                elapsed_ms=start + 11000,
                team_id=contact_actor.team_id,
                player_id=contact_actor.id,
                recipient_id=cleared_to.id if defended else None,
                event_type="pass" if defended else "shot",
                outcome="complete" if defended else rng.choice(["wide", "saved"]),
                start=contact,
                end=outcome_end,
                possession_id=sid,
                attack_right=right if not defended else not right,
                set_piece=SetPiece(id=sid, phase="outcome"),
            ),
        ]
        events.extend(corner_events)
        for phase_index, e in enumerate(corner_events):
            frames.append(
                PositionFrame(
                    frame_id=sid + "-frame-" + PHASES[phase_index],
                    period=period,
                    elapsed_ms=e.elapsed_ms,
                    anchor_event_id=e.event_id,
                    anchor_event_revision=e.revision,
                    ball=kick
                    if phase_index < 2
                    else contact
                    if phase_index == 2
                    else outcome_end,
                    positions=phase_positions[phase_index],
                )
            )
    events.sort(key=lambda e: (e.period, e.elapsed_ms, e.sequence))
    events = [e.model_copy(update={"sequence": i + 1}) for i, e in enumerate(events)]
    score = Counter(
        e.team_id for e in events if e.event_type == "shot" and e.outcome == "goal"
    )
    assert all(
        roster[e.player_id].position != "GK"
        for e in events
        if e.set_piece and e.event_type == "shot"
    )
    return base.model_copy(
        update={
            "id": match_id,
            "schema_version": "1.1",
            "events": events,
            "position_frames": frames,
            "final_score": dict(score),
        }
    )

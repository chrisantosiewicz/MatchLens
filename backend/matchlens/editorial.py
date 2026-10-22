"""Versioned editorial gates over event facts, not validated tactical benchmarks."""

from math import hypot

from .analytics import is_entry, is_progressive, normalized
from .models import visible

POLICY_VERSION = "location-editorial-v1"


def action_location(event):
    if event.start is None:
        return {"available": False}
    sx, sy = normalized(event, event.start)
    zone = lambda x: (
        "defensive third" if x < 35 else "middle third" if x < 70 else "attacking third"
    )
    result = {
        "available": True,
        "origin_zone": zone(sx),
        "origin_half": "own half" if sx < 52.5 else "opposition half",
    }
    if event.end is not None:
        ex, ey = normalized(event, event.end)
        gain = round(ex - sx, 2)
        result.update(
            {
                "destination_zone": zone(ex),
                "destination_half": "own half" if ex < 52.5 else "opposition half",
                "longitudinal_gain_m": gain,
                "distance_m": round(hypot(ex - sx, ey - sy), 2),
                "direction": "backward"
                if gain <= -5
                else "forward"
                if gain >= 5
                else "lateral",
                "own_half_to_final_third": sx < 52.5 and ex >= 70,
            }
        )
    return result


def passing_context(match, player_id, clock, start_ms):
    passes = [
        e
        for e in visible(match.events, clock)
        if e.period == clock.period
        and e.elapsed_ms >= start_ms
        and e.player_id == player_id
        and e.event_type == "pass"
    ]
    located = [e for e in passes if e.start and e.end]
    backward = [e for e in located if action_location(e)["direction"] == "backward"]
    completed = [e for e in passes if e.outcome == "complete"]
    backward_completed = [e for e in backward if e.outcome == "complete"]
    return {
        "scope": "selected interval",
        "window_minutes": (clock.elapsed_ms - start_ms) / 60000,
        "start_ms": start_ms,
        "end_ms": clock.elapsed_ms,
        "attempts": len(passes),
        "completed": len(completed),
        "located_attempts": len(located),
        "backward_attempts": len(backward),
        "backward_completed": len(backward_completed),
        "progressive_completed": sum(is_progressive(e) for e in passes),
        "recycling_eligible": match.feed_completeness == "complete"
        and len(backward_completed) >= 5
        and len(backward_completed) * 2 >= len(completed),
        "origin_zones": {
            z: sum(action_location(e)["origin_zone"] == z for e in backward_completed)
            for z in ("defensive third", "middle third", "attacking third")
        },
        "evidence_ids": [e.event_id for e in passes],
        "backward_evidence_ids": [e.event_id for e in backward_completed],
        "prohibited_inferences": [
            "tempo",
            "intentional possession management",
            "safe or correct decision",
            "defensive pressure",
            "receiver control error",
        ],
    }


def same_metric_contrast(
    pb, pa, tb, ta, before_min, after_min, player_before_min, player_after_min, complete
):
    br = pb / player_before_min if player_before_min else None
    ar = pa / player_after_min if player_after_min else None
    team_br = tb / before_min if before_min else None
    team_ar = ta / after_min if after_min else None
    enough = (
        complete
        and before_min == after_min == 10
        and player_before_min == player_after_min == 10
        and pb + pa >= 5
        and abs(pa - pb) >= 3
    )
    opposite = enough and (ar - br) * (team_ar - team_br) < 0
    return {
        "metric": "box_entries",
        "eligible": bool(opposite),
        "sample_gate_passed": bool(enough),
        "player_before_count": pb,
        "player_after_count": pa,
        "team_before_count": tb,
        "team_after_count": ta,
        "before_minutes": before_min,
        "after_minutes": after_min,
        "player_before_minutes": player_before_min,
        "player_after_minutes": player_after_min,
        "player_before_rate": round(br, 4) if br is not None else None,
        "player_after_rate": round(ar, 4) if ar is not None else None,
        "team_before_rate": round(team_br, 4) if team_br is not None else None,
        "team_after_rate": round(team_ar, 4) if team_ar is not None else None,
        "limitation": "Descriptive editorial gate, not statistical significance or substitution causation.",
        "reason": "opposite same-metric trends"
        if opposite
        else "no opposite direction"
        if enough
        else "insufficient comparable exposure/activity",
    }


def entry_possessions(match, team_id, clock):
    start = max(0, clock.elapsed_ms - 900000)
    allowed = sorted(
        [
            e
            for e in visible(match.events, clock)
            if e.period == clock.period and start <= e.elapsed_ms
        ],
        key=lambda e: (e.elapsed_ms, e.sequence),
    )
    groups = {}
    for e in allowed:
        groups.setdefault(e.possession_id, []).append(e)
    rows = []
    unfinished = 0
    for group in groups.values():
        if any(e.team_id != team_id for e in group):
            continue
        entries = [e for e in group if is_entry(e)]
        if not entries:
            continue
        first = entries[0]
        terminal = next(
            (
                e
                for e in group
                if (e.elapsed_ms, e.sequence) >= (first.elapsed_ms, first.sequence)
                and (
                    e.event_type in {"shot", "turnover", "stoppage"}
                    or (e.event_type == "pass" and e.outcome == "incomplete")
                )
            ),
            None,
        )
        if terminal is None:
            unfinished += 1
            continue
        chain = [
            e
            for e in group
            if (first.elapsed_ms, first.sequence)
            <= (e.elapsed_ms, e.sequence)
            <= (terminal.elapsed_ms, terminal.sequence)
        ]
        rows.append(
            {
                "possession_id": first.possession_id,
                "with_shot": terminal.event_type == "shot",
                "evidence_ids": [e.event_id for e in chain],
            }
        )
    shots = sum(row["with_shot"] for row in rows)
    return {
        "available": match.feed_completeness == "complete",
        "window_minutes": (clock.elapsed_ms - start) / 60000,
        "completed_entry_possessions": len(rows),
        "with_later_shot": shots,
        "unfinished_excluded": unfinished,
        "spotlight_eligible": match.feed_completeness == "complete"
        and len(rows) >= 8
        and shots <= 1,
        "possessions": rows,
        "evidence_ids": list(
            dict.fromkeys(i for row in rows for i in row["evidence_ids"])
        ),
        "limitation": "Counts completed recorded entry possessions, not chance or finishing quality; unfinished sequences excluded.",
    }


def game_state_context(match, team_id, clock):
    if match.feed_completeness != "complete":
        return {
            "available": False,
            "reason": "Observed feed may omit goals; game-state interpretation withheld.",
        }
    goals = [
        e
        for e in visible(match.events, clock)
        if e.event_type == "shot" and e.outcome == "goal"
    ]
    own = sum(e.team_id == team_id for e in goals)
    other = sum(e.team_id != team_id for e in goals)
    return {
        "available": True,
        "phase": "late"
        if (clock.period - 1) * 45 + clock.elapsed_ms / 60000 >= 75
        else "regular",
        "state": "leading" if own > other else "trailing" if own < other else "level",
        "score_for": own,
        "score_against": other,
        "evidence_ids": [e.event_id for e in goals],
        "limitation": "Score/clock prioritize facts; they do not establish intent to protect a lead, chase or settle.",
    }


def editorial_packet(
    match,
    player,
    clock,
    comparison,
    contributions_before,
    contributions_after,
    exposure,
    active_match_minutes,
    source_revision,
):
    from .analytics import player_stats

    packet = {
        "policy_version": POLICY_VERSION,
        "source_revision": source_revision,
        "coverage": match.feed_completeness,
        "position": player.position,
        "position_rule": "Use observed role-relevant contributions; position is not a ceiling on attacking impact.",
        "passing": passing_context(
            match, player.id, clock, max(0, clock.elapsed_ms - 600000)
        ),
        "box_access": entry_possessions(match, player.team_id, clock),
        "game_state": game_state_context(match, player.team_id, clock),
    }
    contrast = same_metric_contrast(
        contributions_before["box_entries"],
        contributions_after["box_entries"],
        comparison["before"]["box_entries"],
        comparison["after"]["box_entries"],
        comparison["before"]["duration_ms"] / 60000,
        comparison["after"]["duration_ms"] / 60000,
        exposure["before"],
        exposure["after"],
        match.feed_completeness == "complete",
    )
    contrast["evidence_ids"] = list(
        dict.fromkeys(
            contributions_before["evidence_ids"]
            + contributions_after["evidence_ids"]
            + comparison["before"]["evidence_ids"]
            + comparison["after"]["evidence_ids"]
        )
    )
    packet["player_team_contrast"] = contrast
    stats = player_stats(match.events, player.id, clock)
    packet["on_ball_involvement"] = {
        "scope": "match through selected clock",
        "active_minutes": active_match_minutes,
        "recorded_actions": stats["actions"],
        "eligible": match.feed_completeness == "complete"
        and active_match_minutes >= 15
        and stats["actions"] <= 3,
        "evidence_ids": stats["evidence_ids"],
        "limitation": "Limited recorded on-ball involvement, not total influence or off-ball value.",
    }
    substitutions = [
        e
        for e in visible(match.events, clock)
        if e.event_type == "substitution" and e.recipient_id == player.id
    ]
    replacement = next(
        (
            p
            for p in match.players
            if substitutions and p.id == substitutions[-1].player_id
        ),
        None,
    )
    packet["replacement"] = {
        "available": bool(substitutions),
        "has_before_baseline": exposure["before"] > 0,
        "replaced_player": replacement.name if replacement else None,
        "replaced_position": replacement.position if replacement else None,
        "same_listed_position": bool(
            replacement and replacement.position == player.position
        ),
        "evidence_ids": [e.event_id for e in substitutions],
        "limitation": "Roster positions describe listed roles, not tactical equivalence. Team before/after changes do not isolate a substitution effect.",
    }
    from .stories import sequence_stories

    followups = [
        s
        for s in sequence_stories(
            match, player.id, clock, max(0, clock.elapsed_ms - 600000), include_all=True
        )
        if s["kind"] == "progression_without_shot"
    ]
    immediate = [s for s in followups if s["intervening_on_ball_actions"] <= 1]
    packet["progression_loss_followups"] = {
        "window_minutes": min(10, clock.elapsed_ms / 60000),
        "recorded_sequences": len(followups),
        "immediate_sequences": len(immediate),
        "spotlight_eligible": match.feed_completeness == "complete"
        and len(immediate) >= 3,
        "evidence_ids": list(
            dict.fromkeys(i for s in immediate for i in s["evidence_ids"])
        ),
        "limitation": "Repeated observed outcomes, not proof of risk-taking intent, a bad pass or receiver control error.",
    }
    packet["prohibited_inferences"] = [
        "tempo management intent",
        "defensive line break",
        "receiver control error",
        "nearby supporting players",
        "defensive pressure",
        "sole blame",
        "position-based attacking ceiling",
        "substitution caused a change",
    ]
    return packet


def editorial_summary_sources(packet):
    if packet["coverage"] != "complete":
        return []
    if packet["passing"]["recycling_eligible"]:
        return packet["passing"]["evidence_ids"]
    if packet["on_ball_involvement"]["eligible"]:
        return packet["on_ball_involvement"]["evidence_ids"]
    if packet["player_team_contrast"]["eligible"]:
        return packet["player_team_contrast"]["evidence_ids"]
    return []


def editorial_summary(packet, player_name, language="en"):
    """Same gates/limitations for fan and analyst; detail is rendered separately."""
    if packet["coverage"] != "complete":
        return ""
    spanish = language == "es"
    passing = packet["passing"]
    low = packet["on_ball_involvement"]
    contrast = packet["player_team_contrast"]
    if passing["recycling_eligible"]:
        return (
            f"{player_name} completó {passing['backward_completed']} pases hacia atrás en el intervalo seleccionado: circulación registrada, sin demostrar intención de controlar el ritmo."
            if spanish
            else f"{player_name} completed {passing['backward_completed']} backward passes in the selected interval: recorded recycling of the ball, without establishing intent to manage tempo."
        )
    if low["eligible"]:
        return (
            f"Participación registrada con balón limitada: {low['recorded_actions']} acciones en {low['active_minutes']} minutos en el campo. No mide su valor sin balón."
            if spanish
            else f"Limited recorded on-ball involvement: {low['recorded_actions']} actions in {low['active_minutes']} active minutes. This does not measure off-ball value."
        )
    if contrast["eligible"]:
        return (
            "Las entradas al área del jugador y del equipo cambiaron en direcciones opuestas en dos ventanas completas de 10 minutos. Es una comparación descriptiva, no causal."
            if spanish
            else "Player and team box-entry rates moved in opposite directions across two complete 10-minute windows. This is a descriptive comparison, not a causal explanation."
        )
    return ""

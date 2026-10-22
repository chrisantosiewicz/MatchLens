"""Experimental single-call interpretation. Structural checks are not semantic proof."""

import re
from decimal import Decimal
from time import perf_counter

from .analytics import compare_windows, is_entry, is_progressive, player_stats
from .models import Clock, Event, visible
from .stories import sequence_stories


def active_minutes(match, player, period, start_ms, end_ms):
    offset = (period - 1) * 2700000
    low, high = offset + start_ms, offset + end_ms
    active_from = 0 if player.starter else None
    duration = 0
    for event in sorted(
        visible(match.events, Clock(period=period, elapsed_ms=end_ms)),
        key=lambda e: (e.period, e.elapsed_ms, e.sequence),
    ):
        if event.event_type != "substitution":
            continue
        time = (event.period - 1) * 2700000 + event.elapsed_ms
        if event.player_id == player.id and active_from is not None:
            duration += max(0, min(high, time) - max(low, active_from))
            active_from = None
        if event.recipient_id == player.id:
            active_from = time
    if active_from is not None:
        duration += max(0, high - max(low, active_from))
    return round(duration / 60000, 4)


def context_packet(match, player_id, clock, anchor_ms):
    player = next(p for p in match.players if p.id == player_id)
    events = visible(match.events, clock)
    anchor = Clock(period=clock.period, elapsed_ms=min(anchor_ms, clock.elapsed_ms))
    comparison = compare_windows(events, anchor, clock, player.team_id)
    # Only the relevant period/window and selected-player actions; no future facts.
    relevant = [
        e
        for e in events
        if e.period == clock.period
        and max(0, anchor.elapsed_ms - 600000) <= e.elapsed_ms
    ]
    packet = {
        "synthetic": True,
        "feed_completeness": match.feed_completeness,
        "viewer_clock": clock.model_dump(),
        "display_clock_minutes": (clock.period - 1) * 45 + clock.elapsed_ms / 60000,
        "anchor_clock_minutes": (clock.period - 1) * 45 + anchor.elapsed_ms / 60000,
        "window_bounds_minutes": {
            "before": [
                (clock.period - 1) * 45 + max(0, anchor.elapsed_ms - 600000) / 60000,
                (clock.period - 1) * 45 + anchor.elapsed_ms / 60000,
            ],
            "after": [
                (clock.period - 1) * 45 + anchor.elapsed_ms / 60000,
                (clock.period - 1) * 45
                + min(clock.elapsed_ms, anchor.elapsed_ms + 600000) / 60000,
            ],
        },
        "window_minutes": {
            "before": comparison["before"]["duration_ms"] / 60000,
            "after": comparison["after"]["duration_ms"] / 60000,
        },
        "subject_guide": {
            "comparison": f"TEAM {match.teams[player.team_id]}, NOT the selected player",
            "player_stats": f"PLAYER {player.name}, match totals",
            "contributions_before": f"PLAYER {player.name}, before window only",
            "contributions_after": f"PLAYER {player.name}, after window only",
        },
        "player": player.model_dump(),
        "player_stats": player_stats(events, player_id, clock),
        "comparison": comparison,
        "contributions_before": player_stats(
            [e for e in relevant if e.elapsed_ms < anchor.elapsed_ms], player_id, clock
        ),
        "contributions_after": player_stats(
            [
                e
                for e in relevant
                if anchor.elapsed_ms
                <= e.elapsed_ms
                <= min(anchor.elapsed_ms + 600000, clock.elapsed_ms)
            ]
            if clock.elapsed_ms > anchor.elapsed_ms
            else [],
            player_id,
            clock,
        ),
        "events": [
            e.model_dump()
            for e in relevant
            if e.player_id == player_id
            or e.event_id
            in comparison["before"]["evidence_ids"]
            + comparison["after"]["evidence_ids"]
        ],
        "limits": "Temporal association, not causation. Event-only: no tracking, defensive lines, pressure, off-ball movement or video inference. Unequal windows and sparse observations limit comparison. Five entries is an editorial gate, not significance. Synthetic heuristics are not calibrated football truth.",
    }

    bounds = {
        "before": (max(0, anchor.elapsed_ms - 600000), anchor.elapsed_ms),
        "after": (anchor.elapsed_ms, min(clock.elapsed_ms, anchor.elapsed_ms + 600000)),
    }
    packet["player_window_minutes"] = {
        key: active_minutes(match, player, clock.period, *window)
        for key, window in bounds.items()
    }
    packet["player_rates"] = {
        key: {
            f"{metric}_per_minute": round(
                packet[f"contributions_{key}"][metric] / minutes, 4
            )
            if minutes
            else None
            for metric in ("actions", "progressive_passes", "box_entries")
        }
        for key, minutes in packet["player_window_minutes"].items()
    }
    packet["rate_contract"] = {
        "basis": "per_minute"
        if comparison["entry_rate_change"] != "not_comparable"
        else "not_comparable",
        "team_entry_rate_change": comparison["entry_rate_change"],
        "before": comparison["before"]["box_entries_per_minute"],
        "after": comparison["after"]["box_entries_per_minute"],
    }
    packet["narrative_evidence"] = sequence_stories(
        match,
        player_id,
        Clock(
            period=clock.period,
            elapsed_ms=min(clock.elapsed_ms, anchor.elapsed_ms + 600000),
        ),
        max(0, anchor.elapsed_ms - 600000),
    )
    extra = {
        e["event_id"]: e
        for story in packet["narrative_evidence"]
        for e in story["sequence"]
    }
    packet["events"] = list(
        {e["event_id"]: e for e in packet["events"] + list(extra.values())}.values()
    )
    return packet


def calculated_numbers(context):
    """Use calculated metric values, never incidental digits in IDs or coordinates."""

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key != "evidence_ids":
                    yield from walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from walk(child)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            yield Decimal(str(value))

    return {
        value
        for story in context.get("narrative_evidence", [])
        for value in (
            Decimal(str(story["sequence_duration_seconds"])),
            Decimal(str(story["review_window_seconds"])),
        )
    } | set(
        walk(
            {
                key: context[key]
                for key in (
                    "player_stats",
                    "comparison",
                    "contributions_before",
                    "contributions_after",
                    "display_clock_minutes",
                    "anchor_clock_minutes",
                    "window_bounds_minutes",
                    "window_minutes",
                    "player_rates",
                    "player_window_minutes",
                    "rate_contract",
                )
            }
        )
    )


def interpretation_limit(request, context):
    return (
        "incomplete_feed"
        if context.get("feed_completeness") == "incomplete"
        else "zero_duration"
        if any(value <= 0 for value in context["window_minutes"].values())
        else "no_player_comparison_baseline"
        if any(value <= 0 for value in context["player_window_minutes"].values())
        else "no_recorded_passing"
        if "pass" in request.get("question", "").lower()
        and context["player_stats"]["pass_attempts"] == 0
        else None
    )


def comparison_fact_support(context):
    """Attach complete deterministic metric sources, separate from model citations."""
    events = [Event.model_validate(e) for e in context["events"]]
    player = context["player"]
    period = context["viewer_clock"]["period"]
    offset = (period - 1) * 45
    cards = []
    for window in ("before", "after"):
        bounds = context["window_bounds_minutes"][window]
        low, high = (round((minute - offset) * 60000) for minute in bounds)
        selected = [
            e
            for e in events
            if e.period == period
            and high > low
            and low <= e.elapsed_ms
            and (e.elapsed_ms < high if window == "before" else e.elapsed_ms <= high)
        ]
        groups = [
            (
                "team_box_entries",
                context["window_minutes"][window],
                [e for e in selected if e.team_id == player["team_id"] and is_entry(e)],
            ),
            (
                "player_progressive_passes",
                context["player_window_minutes"][window],
                [
                    e
                    for e in selected
                    if e.player_id == player["id"] and is_progressive(e)
                ],
            ),
            (
                "player_box_entries",
                context["player_window_minutes"][window],
                [e for e in selected if e.player_id == player["id"] and is_entry(e)],
            ),
        ]
        for metric, minutes, qualifying in groups:
            cards.append(
                {
                    "metric": metric,
                    "window": window,
                    "count": len(qualifying),
                    "minutes": minutes,
                    "rate": round(len(qualifying) / minutes, 4) if minutes else None,
                    "source_ids": [e.event_id for e in qualifying],
                    "period": period,
                    "start_ms": low,
                    "end_ms": high,
                    "end_inclusive": window == "after",
                }
            )
    return cards


def model_context(context):
    """Only relevant calculated facts; raw coordinates/action totals invite invalid inferences."""
    return {
        "synthetic": True,
        "player_name": context["player"]["name"],
        "viewer_clock_minutes": context["display_clock_minutes"],
        "window_bounds_minutes": context["window_bounds_minutes"],
        "window_minutes": context["window_minutes"],
        "player_window_minutes": context["player_window_minutes"],
        "rate_contract": context["rate_contract"],
        "player_progressive_passes": {
            window: {
                "count": context[f"contributions_{window}"]["progressive_passes"],
                "per_active_minute": context["player_rates"][window][
                    "progressive_passes_per_minute"
                ],
            }
            for window in ("before", "after")
        },
        "metric_sources": [e["event_id"] for e in context["events"]],
        "narrative_evidence": [
            {
                k: v
                for k, v in story.items()
                if k not in {"sequence", "meaning_es", "limitation_es"}
            }
            for story in context.get("narrative_evidence", [])
        ],
        "limits": context["limits"],
    }


def explain(
    request,
    context,
    provider,
    trusted_text,
    diagnostics=None,
    trusted_evidence_ids=None,
    trusted_narrative=None,
):
    start = perf_counter()
    fallback_ids = (
        trusted_evidence_ids
        if trusted_evidence_ids is not None
        else list(
            dict.fromkeys(
                context["player_stats"]["evidence_ids"]
                + [
                    i
                    for story in context.get("narrative_evidence", [])[:1]
                    for i in story["evidence_ids"]
                ]
            )
        )
    )

    def result(text, mode, status, ids):
        return {
            "text": text,
            "narrative_evidence": (
                trusted_narrative
                if trusted_narrative is not None
                else context.get("narrative_evidence", [])[:1]
            )
            if mode != "model"
            else [],
            "generation_mode": mode,
            "status": status,
            "evidence_ids": ids,
            "latency_ms": round((perf_counter() - start) * 1000, 2),
            "usage": getattr(provider, "last_usage", None),
            "validation": "structural_only; semantic support requires evaluation",
        }

    limited_reason = interpretation_limit(request, context)
    if limited_reason:
        return {
            **result(
                trusted_text,
                "template",
                "limited_input",
                fallback_ids,
            ),
            "limitation": limited_reason,
        }
    if provider is None:
        return result(
            trusted_text,
            "template",
            "template",
            fallback_ids,
        )
    output = None
    rejection = "provider_unavailable"
    try:
        output = provider.complete(
            "explainer", {"request": request, "context": model_context(context)}
        )
        if output.get("abstain") is True:
            text = (
                "Evidencia insuficiente para esa interpretación."
                if request.get("language") == "es"
                else "Insufficient evidence for that interpretation."
            )
            return result(text, "model", "abstain", [])
        text, ids = output["text"], output["evidence_ids"]
        allowed = {e["event_id"] for e in context["events"]}
        if not isinstance(text, str) or not text.strip() or len(text) > 1800:
            rejection = "invalid_narrative"
            raise ValueError(rejection)
        # Conservative scope filter, not a proof that remaining prose is supported.
        if re.search(
            r"\b(speed|velocity|sprints?|pressing|pressure|chaos|dominance|sparse)\b"
            r"|\bactions?\s+(?:rate|per minute)|\b(?:all|recorded|total)\s+actions\b"
            r"|attacking presence|retained control|defensive.line.break"
            r"|improved (?:passing|quality)|creates? (?:space|chances)",
            text,
            re.IGNORECASE,
        ):
            rejection = "unsupported_concept"
            raise ValueError(rejection)
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(i, str) or i not in allowed for i in ids)
        ):
            rejection = "unknown_evidence"
            raise ValueError(rejection)
        story_ids = output.get("story_ids", [])
        stories = {
            story["id"]: story for story in context.get("narrative_evidence", [])
        }
        if not isinstance(story_ids, list) or any(
            not isinstance(i, str) or i not in stories for i in story_ids
        ):
            rejection = "unknown_story"
            raise ValueError(rejection)
        if "story_ids" in output and stories and not story_ids:
            rejection = "missing_story"
            raise ValueError(rejection)
        selected_stories = [stories[i] for i in dict.fromkeys(story_ids)]
        if any(
            not set(story["evidence_ids"]) <= set(ids) for story in selected_stories
        ):
            rejection = "incomplete_story_evidence"
            raise ValueError(rejection)
        allowed_clocks = {
            story[key]
            for story in selected_stories
            for key in ("action_clock", "outcome_clock")
        }
        times = re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", text)
        if any(time not in allowed_clocks for time in times):
            rejection = "unknown_clock"
            raise ValueError(rejection)
        numeric_text = re.sub(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", "", text)
        # Exact numerical equivalence accepts 100 == 100.0; rounding is still rejected.
        numbers = calculated_numbers(context)
        if any(
            Decimal(n.replace(",", ".").replace("−", "-")) not in numbers
            for n in re.findall(r"(?<!\w)[+−-]?\d+(?:[.,]\d+)?", numeric_text)
        ):
            rejection = "unknown_number"
            raise ValueError(rejection)
        contract = context.get("rate_contract")
        if contract and (
            output.get("rate_basis") != contract["basis"]
            or output.get("team_entry_rate_change")
            != contract["team_entry_rate_change"]
        ):
            rejection = "invalid_rate_comparison"
            raise ValueError(rejection)
        support = comparison_fact_support(context)
        complete_ids = list(
            dict.fromkeys(
                ids + [event_id for card in support for event_id in card["source_ids"]]
            )
        )
        return {
            **result(text, "model", "experimental", complete_ids),
            "model_cited_event_ids": list(dict.fromkeys(ids)),
            "narrative_evidence": selected_stories,
            "fact_support": support,
            "metric_definition": "Recorded progression means completed passes moving the ball at least 10m closer to goal from outside the box. Frequency is not passing quality or causation.",
        }
    except (TimeoutError, RuntimeError, ValueError, KeyError, TypeError):
        if diagnostics is not None:
            diagnostics.append({"candidate": output, "rejection_reason": rejection})
        return {
            **result(
                trusted_text,
                "fallback",
                "fallback",
                fallback_ids,
            ),
            "rejection_reason": rejection,
        }

"""Experimental single-call interpretation. Structural checks are not semantic proof."""

import re
from decimal import Decimal
from time import perf_counter

from .analytics import compare_windows, player_stats
from .models import Clock, visible


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
    return {
        "synthetic": True,
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

    return set(
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
                )
            }
        )
    )


def explain(request, context, provider, trusted_text, diagnostics=None):
    start = perf_counter()

    def result(text, mode, status, ids):
        return {
            "text": text,
            "generation_mode": mode,
            "status": status,
            "evidence_ids": ids,
            "latency_ms": round((perf_counter() - start) * 1000, 2),
            "usage": getattr(provider, "last_usage", None),
            "validation": "structural_only; semantic support requires evaluation",
        }

    if provider is None:
        return result(
            trusted_text,
            "template",
            "template",
            context["player_stats"]["evidence_ids"],
        )
    output = None
    rejection = "provider_unavailable"
    try:
        output = provider.complete(
            "explainer", {"request": request, "context": context}
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
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(i, str) or i not in allowed for i in ids)
        ):
            rejection = "unknown_evidence"
            raise ValueError(rejection)
        # Exact numerical equivalence accepts 100 == 100.0; rounding is still rejected.
        numbers = calculated_numbers(context)
        if any(
            Decimal(n.replace(",", ".")) not in numbers
            for n in re.findall(r"\d+(?:[.,]\d+)?", text)
        ):
            rejection = "unknown_number"
            raise ValueError(rejection)
        return result(text, "model", "experimental", list(dict.fromkeys(ids)))
    except (TimeoutError, RuntimeError, ValueError, KeyError, TypeError):
        if diagnostics is not None:
            diagnostics.append({"candidate": output, "rejection_reason": rejection})
        return {
            **result(
                trusted_text,
                "fallback",
                "fallback",
                context["player_stats"]["evidence_ids"],
            ),
            "rejection_reason": rejection,
        }

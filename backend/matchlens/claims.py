"""Deterministic claim ledger. IDs link typed facts, rules and exact event revisions."""

import json
from hashlib import sha256

from .analytics import is_progressive
from .editorial import POLICY_VERSION, action_location
from .explainer import comparison_fact_support
from .models import Event
from .stories import render_story


def digest(value):
    return sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()[:32]


def stamp(event):
    seconds = event["elapsed_ms"] // 1000
    return f"{(event['period'] - 1) * 45 + seconds // 60}:{seconds % 60:02}"


def build_ledger(request, context, answer):
    source = answer["source_version"]
    if source != context["editorial_context"]["source_revision"]:
        raise ValueError("mixed_source_revision")
    clock = context["viewer_clock"]
    snapshot = digest(
        {
            "source_revision": source,
            "clock": clock,
            "player_id": context["player"]["id"],
            "anchor": request.get("anchor_ms"),
            "language": request.get("language", "en"),
            "depth": request.get("depth", "casual"),
            "question": request.get("question", ""),
            "policy": POLICY_VERSION,
        }
    )
    raw = context.get("audit_events", context["events"])
    events = {e["event_id"]: Event.model_validate(e).model_dump() for e in raw}
    if len(events) != len(raw):
        raise ValueError("duplicate_event_ids")
    if any(
        (e["period"], e["elapsed_ms"]) > (clock["period"], clock["elapsed_ms"])
        for e in events.values()
    ):
        raise ValueError("future_event")
    directory = context.get("player_directory", {})
    facts = []
    claims = []
    candidates = []
    seen = {}
    for story in answer.get("narrative_evidence", []) + context.get(
        "narrative_evidence", []
    ):
        if story["id"] in seen:
            if seen[story["id"]] != story:
                raise ValueError("conflicting_story_revision")
            continue
        seen[story["id"]] = story
        if context["feed_completeness"] != "complete":
            continue
        sequence = [Event.model_validate(e).model_dump() for e in story["sequence"]]
        if not sequence or [e["event_id"] for e in sequence] != story["evidence_ids"]:
            raise ValueError("invalid_story_sources")
        if any(events.get(e["event_id"]) != e for e in sequence):
            raise ValueError("story_source_mismatch")
        if sequence != sorted(
            sequence, key=lambda e: (e["period"], e["elapsed_ms"], e["sequence"])
        ):
            raise ValueError("unordered_sequence")
        first, last = sequence[0], sequence[-1]
        if (
            first["player_id"] != context["player"]["id"]
            or first["period"] != last["period"]
        ):
            raise ValueError("wrong_sequence_subject")
        if story["action_clock"] != stamp(first) or story["outcome_clock"] != stamp(
            last
        ):
            raise ValueError("wrong_story_clock")
        if story.get("policy_version", POLICY_VERSION) != POLICY_VERSION:
            raise ValueError("wrong_editorial_policy")
        if story.get("action_location") != action_location(Event.model_validate(first)):
            raise ValueError("wrong_geometry")
        if story["player_action_progressive"] != is_progressive(
            Event.model_validate(first)
        ):
            raise ValueError("wrong_progression_flag")
        if story["kind"] == "shot_build_up":
            rank = sum(
                e["event_type"] == "pass" and e["outcome"] == "complete"
                for e in sequence[:-1]
            )
            expected_rank = rank if first["event_type"] == "pass" else None
            if (
                last["event_type"] != "shot"
                or rank > 3
                or story["pass_rank_before_shot"] != expected_rank
            ):
                raise ValueError("wrong_shot_role")
        if (
            last["player_id"] in directory
            and story["outcome_player"] != directory[last["player_id"]]["name"]
        ):
            raise ValueError("wrong_outcome_actor")
        if request.get("question") and answer.get("intent") == "change":
            end = (
                context["window_bounds_minutes"]["after"][1]
                - (clock["period"] - 1) * 45
            ) * 60000
            if last["elapsed_ms"] > end:
                continue
        # A recovery story is not a passing explanation, even if it contains later passes.
        if answer.get("intent") == "passing" and first["event_type"] != "pass":
            continue
        scope = {
            "kind": "recorded_sequence",
            "period": first["period"],
            "start_ms": first["elapsed_ms"],
            "end_ms": last["elapsed_ms"],
            "viewer_clock": clock,
            "source_revision": source,
        }
        scope_id = digest(scope)
        base = f"story:{story['id']}"
        fact_ids = []
        for suffix, predicate, subject, value, ids in [
            (
                "geometry",
                "action_location",
                first["player_id"],
                story["action_location"],
                [first["event_id"]],
            ),
            (
                "role",
                "recorded_sequence_role",
                first["player_id"],
                {
                    "progressive_pass": story["player_action_progressive"],
                    "pass_rank_before_shot": story.get("pass_rank_before_shot"),
                    "intervening_on_ball_actions": story.get(
                        "intervening_on_ball_actions"
                    ),
                    "outcome_actor_id": last["player_id"],
                    "outcome_actor_name": story["outcome_player"],
                    "outcome": story["outcome"],
                },
                story["evidence_ids"],
            ),
        ]:
            fid = base + ":" + suffix
            fact_ids.append(fid)
            facts.append(
                {
                    "id": fid,
                    "subject_id": subject,
                    "predicate": predicate,
                    "value": value,
                    "scope_id": scope_id,
                    "scope": scope,
                    "evidence_ids": ids,
                    "event_revisions": {i: events[i]["revision"] for i in ids},
                    "eligible": True,
                    "definition_id": POLICY_VERSION + "/" + story["kind"],
                }
            )
        full = render_story(story, request.get("language", "en"))
        es = request.get("language") == "es"
        meaning = story["meaning_es" if es else "meaning_en"]
        limit = story["limitation_es" if es else "limitation_en"]
        if not full.endswith(limit):
            raise ValueError("missing_canonical_limitation")
        observation = full[: -len(limit)].strip()
        parts = []
        if meaning in observation:
            observed, _, tail = observation.partition(meaning)
            if tail.strip():
                raise ValueError("noncanonical_story_suffix")
            parts = [("observation", observed.strip()), ("interpretation", meaning)]
        else:
            parts = [("observation", observation)]
        parts.append(("limitation", limit))
        claim_ids = []
        for kind, text in parts:
            cid = base + ":" + kind
            claim_ids.append(cid)
            claims.append(
                {
                    "id": cid,
                    "kind": kind,
                    "text": text,
                    "subject_id": first["player_id"],
                    "fact_ids": fact_ids,
                    "evidence_ids": story["evidence_ids"]
                    if kind != "limitation"
                    else [],
                    "scope_id": scope_id,
                    "scope": scope,
                    "rule_id": POLICY_VERSION + "/" + story["kind"],
                    "support_type": "event_facts"
                    if kind == "observation"
                    else "editorial_rule_with_facts",
                    "checker_verdict": "not_run",
                }
            )
        candidates.append(
            {
                "id": base,
                "story_id": story["id"],
                "kind": story["kind"],
                "fact_ids": fact_ids,
                "claim_ids": claim_ids,
                "scope_id": scope_id,
                "scope": scope,
                "eligible": True,
                "language": request.get("language", "en"),
            }
        )
    aggregates = comparison_fact_support(context)
    return {
        "version": "claim-ledger-v1",
        "snapshot_id": snapshot,
        "source_revision": source,
        "viewer_clock": clock,
        "subject_id": context["player"]["id"],
        "coverage": context["feed_completeness"],
        "policy_version": POLICY_VERSION,
        "facts": facts,
        "claims": claims,
        "candidates": candidates,
        "events": list(events.values()),
        "aggregate_calculations": aggregates,
    }


def enrich_answer(request, context, answer, ledger=None, conclusion_id=None):
    ledger = ledger or build_ledger(request, context, answer)
    selected = next((c for c in ledger["candidates"] if c["id"] == conclusion_id), None)
    if selected is None:
        story_ids = {s["id"] for s in answer.get("narrative_evidence", [])}
        selected = next(
            (c for c in ledger["candidates"] if c["story_id"] in story_ids), None
        )
    if selected and conclusion_id is None:
        selected_cards = [
            c for c in ledger["claims"] if c["id"] in selected["claim_ids"]
        ]
        if not all(c["text"] in answer["text"] for c in selected_cards):
            selected = None
    claims = [
        c for c in ledger["claims"] if selected and c["id"] in selected["claim_ids"]
    ]
    primary = list(dict.fromkeys(i for c in claims for i in c["evidence_ids"]))
    related = list(
        dict.fromkeys(
            answer.get("evidence_ids", [])
            + [
                i
                for calc in ledger["aggregate_calculations"]
                for i in calc["source_ids"]
            ]
        )
    )
    aggregate = [i for i in related if i not in primary]
    evidence_ids = list(dict.fromkeys(primary + answer.get("evidence_ids", [])))
    event_ids = set(primary + aggregate)
    trail = {
        **ledger,
        "claims": claims,
        "facts": [
            f for f in ledger["facts"] if any(f["id"] in c["fact_ids"] for c in claims)
        ],
        "events": [e for e in ledger["events"] if e["event_id"] in event_ids],
        "primary_evidence_ids": primary,
        "aggregate_evidence_ids": aggregate,
        "selected_conclusion_id": selected["id"] if selected else None,
    }
    return {
        **answer,
        "evidence_ids": evidence_ids,
        "primary_evidence_ids": primary,
        "aggregate_evidence_ids": aggregate,
        "claims": claims,
        "evidence_trail": trail,
    }

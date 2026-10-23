"""Reproducible synthetic demonstrations and unfilled human review/study materials."""

import argparse
import json
import random
from pathlib import Path

from matchlens.analytics import is_entry, player_stats
from matchlens.api import Question, source_version, template_question
from matchlens.claims import build_ledger
from matchlens.explainer import context_packet
from matchlens.models import Clock
from matchlens.stories import render_story, sequence_stories
from matchlens.synthetic import generate_match

ROOT = Path(__file__).resolve().parents[1]
CLOCK = Clock(period=2, elapsed_ms=1500000)


def scripted_contrast(player):
    """Explicit authored variant, not a held-out benchmark or observed match."""
    match = generate_match(7, "shift")
    events = list(match.events)
    identifier = f"scripted-attribution-{player}"
    entries = [
        e
        for e in events
        if e.period == 2
        and e.team_id == "north"
        and is_entry(e)
        and 300000 <= e.elapsed_ms <= 1500000
    ]
    after = [e for e in entries if e.elapsed_ms >= 900000]
    selected_after = after[0].event_id
    for index, event in enumerate(events):
        if event not in entries:
            continue
        actor = (
            player
            if event.elapsed_ms < 900000 or event.event_id == selected_after
            else "north-7"
        )
        recipient = "north-10" if event.recipient_id == actor else event.recipient_id
        events[index] = event.model_copy(
            update={"player_id": actor, "recipient_id": recipient}
        )
        if (
            index
            and events[index - 1].possession_id == event.possession_id
            and events[index - 1].event_type == "pass"
            and events[index - 1].outcome == "complete"
        ):
            events[index - 1] = events[index - 1].model_copy(
                update={"recipient_id": actor}
            )
    events = [
        e.model_copy(update={"match_id": identifier, "event_id": f"{identifier}-{i}"})
        for i, e in enumerate(events)
    ]
    return match.model_copy(update={"id": identifier, "events": events})


def correction_replay():
    match = generate_match(7, "shift")
    request = Question(
        period=2,
        elapsed_ms=1500000,
        player_id="north-6",
        question="Why does his passing matter?",
    )
    before = template_question(match.id, request, match)
    old = before["evidence_trail"]["selected_conclusion_id"]
    target = before["primary_evidence_ids"][0]
    events = [
        e.model_copy(update={"outcome": "incomplete", "revision": e.revision + 1})
        if e.event_id == target
        else e
        for e in match.events
    ]
    corrected = match.model_copy(update={"events": events})
    after = template_question(match.id, request, corrected)
    ctx = context_packet(corrected, request.player_id, CLOCK, request.anchor_ms)
    ledger = build_ledger(request.model_dump(), ctx, after)
    return {
        "mode": "Recorded deterministic correction replay; not a live ingestion request.",
        "before_source": source_version(match),
        "after_source": source_version(corrected),
        "old_conclusion_id": old,
        "before": before,
        "after": after,
        "corrected_event": next(e.model_dump() for e in events if e.event_id == target),
        "after_candidate_ids": [c["id"] for c in ledger["candidates"]],
    }


def study_cases():
    cases = []
    for seed in (7, 5209):
        match = generate_match(seed, "shift")
        player = next(p for p in match.players if p.id == "north-6")
        stories = sequence_stories(match, player.id, CLOCK, 0, include_all=True)
        story = next(
            s
            for s in stories
            if s["kind"] == "shot_build_up"
            and not s["player_action_progressive"]
            and s["sequence"][0]["event_type"] == "pass"
        )
        stats = player_stats(match.events, player.id, CLOCK)
        cases.append(
            {
                "id": f"hidden-{seed}",
                "kind": "hidden",
                "title": "Who took part before the shot?",
                "disclosure": "Seeded synthetic event sequence; complete event feed, no tracking.",
                "facts": [
                    f"Viewer clock 70:00. {player.name}: {stats['completed_passes']} completed passes, {stats['progressive_passes']} progressive passes, {stats['shots']} shots.",
                    f"The selected pass is not progressive under the 10m-closer-to-goal definition. Recorded shot outcome: {story['outcome']}.",
                ],
                "events": story["sequence"],
                "explanation": render_story(story),
                "source": source_version(match),
                "questions": [
                    {
                        "id": "involvement",
                        "prompt": f"What can these records establish about {player.name}?",
                        "options": [
                            "Recorded involvement before this shot",
                            "Scored this goal",
                            "Created the chance alone",
                            "No recorded involvement",
                        ],
                        "correct": 0,
                    },
                    {
                        "id": "causation",
                        "prompt": "Does the sequence establish an assist or that this player caused the shot?",
                        "options": ["Yes", "No"],
                        "correct": 1,
                    },
                ],
            }
        )
    for player_id in ("north-6", "north-8"):
        match = scripted_contrast(player_id)
        player = next(p for p in match.players if p.id == player_id)
        ctx = context_packet(match, player_id, CLOCK, 900000)
        c = ctx["editorial_context"]["player_team_contrast"]
        assert c["eligible"]
        ids = set(c["evidence_ids"])
        explanation = f"Northbridge's box-entry rate rose from {c['team_before_rate']} to {c['team_after_rate']} per minute, while {player.name}'s fell from {c['player_before_rate']} to {c['player_after_rate']} per active minute. The team's increased activity does not establish an increase in this player's comparable on-ball contribution. These two 10-minute windows do not isolate a substitution effect or measure off-ball value."
        cases.append(
            {
                "id": f"attribution-{player_id}",
                "kind": "attribution",
                "title": "Does the team headline describe this player?",
                "disclosure": "Explicitly scripted synthetic variant to demonstrate opposite same-metric trends; not a held-out model test.",
                "facts": [
                    "Complete event coverage. Before 50:00–60:00; after 60:00–70:00. Player active for both complete 10-minute windows.",
                    f"Northbridge box entries: {c['team_before_count']} before, {c['team_after_count']} after. Rates: {c['team_before_rate']} and {c['team_after_rate']} per minute.",
                    f"{player.name} box entries: {c['player_before_count']} before, {c['player_after_count']} after. Rates: {c['player_before_rate']} and {c['player_after_rate']} per active minute.",
                    "A substitution is recorded at 60:00. These are descriptive observations, with no causal comparison group.",
                ],
                "events": [
                    e.model_dump()
                    for e in match.events
                    if e.event_id in ids and is_entry(e)
                ],
                "explanation": explanation,
                "source": source_version(match),
                "contrast": c,
                "questions": [
                    {
                        "id": "rates",
                        "prompt": "Which description matches the box-entry rates?",
                        "options": [
                            "Team rose; player rose",
                            "Team rose; player fell",
                            "Both fell",
                            "No comparable window",
                        ],
                        "correct": 1,
                    },
                    {
                        "id": "substitution",
                        "prompt": "Can the rate change be attributed to the substitution from these records alone?",
                        "options": ["Yes", "No"],
                        "correct": 1,
                    },
                ],
            }
        )
    for seed in (7, 5209):
        match = generate_match(seed, "sparse")
        stats = player_stats(match.events, "north-6", CLOCK)
        cases.append(
            {
                "id": f"withheld-{seed}",
                "kind": "withheld",
                "title": "What does a sparse feed let us conclude?",
                "disclosure": "Synthetic feed intentionally omits events; no tracking.",
                "facts": [
                    f"Viewer clock 70:00. Coverage: incomplete. Mateo Silva has {stats['actions']} observed actions and {stats['shots']} observed shots.",
                    "Unknown actions may be missing. The feed does not measure off-ball movement.",
                ],
                "events": [],
                "source": source_version(match),
                "explanation": "An overall impact conclusion is withheld. Sparse observations can describe recorded actions but cannot establish that Mateo had no involvement or no value. Missing events and off-ball contributions remain unknown.",
                "questions": [
                    {
                        "id": "absence",
                        "prompt": "Do the low observed counts establish no contribution?",
                        "options": ["Yes", "No"],
                        "correct": 1,
                    },
                    {
                        "id": "unknown",
                        "prompt": "Which statement is supported?",
                        "options": [
                            "The player was ineffective",
                            "Only recorded actions can be counted; total involvement remains unknown",
                            "The player stayed in one position",
                        ],
                        "correct": 1,
                    },
                ],
            }
        )
    names = {p.id: p.name for p in generate_match(7, "shift").players}
    for case in cases:
        case["events"] = [
            {**event, "actor_name": names.get(event["player_id"], event["player_id"])}
            for event in case["events"]
        ]
    return cases


def review_sources(case):
    ledger = case["ledger"]
    stats = case["context"]["player_stats"]
    ids = (
        {i for f in ledger["facts"] for i in f["evidence_ids"]}
        | {i for c in ledger["aggregate_calculations"] for i in c["source_ids"]}
        | set(stats["evidence_ids"])
    )
    return {
        "full_clock_stats": {
            **stats,
            "subject_id": ledger["subject_id"],
            "scope": "All recorded selected-player actions through viewer clock",
            "viewer_clock": ledger["viewer_clock"],
            "coverage": ledger["coverage"],
        },
        "metric_definitions": {
            "completed_passes": "Recorded pass events with outcome complete. Denominator is all pass attempts.",
            "progressive_passes": "Completed passes with start and end locations, starting outside the box, reducing Euclidean distance to goal centre by at least 10m. Attack direction is normalized.",
            "box_entries": "Completed passes/carries from outside to inside the penalty area; each qualifying event counted. Rates use the displayed team-window or player-active minutes.",
            "absence": "Zero is an observed count under the stated coverage; it does not establish no off-ball contribution.",
        },
        "events": [e for e in ledger["events"] if e["event_id"] in ids],
    }


def build(results_path, summary_path):
    data = json.loads(results_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    folder = ROOT / "frontend/public/review"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "study.json").write_text(
        json.dumps(
            {"version": "pilot-v1", "cases": study_cases()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    randomizer = random.Random(20261022)
    reviews = []
    key = []
    for number, (case_id, case) in enumerate(data["cases"].items(), 1):
        rows = [r for r in data["rows"] if r["case_id"] == case_id and r["eligible"]]
        if not rows:
            continue
        randomizer.shuffle(rows)
        options = []
        for index, row in enumerate(rows):
            option_id = f"R{number}-{chr(65 + index)}"
            answer = row["answer"]
            options.append(
                {
                    "id": option_id,
                    "text": answer["text"],
                    "claims": [
                        {k: v for k, v in claim.items() if k != "checker_verdict"}
                        for claim in answer.get("claims", [])
                    ],
                    "evidence_ids": answer.get("primary_evidence_ids", []),
                }
            )
            key.append(
                {
                    "case_id": f"R{number}",
                    "option_id": option_id,
                    "source_case": case_id,
                    "policy": row["policy"],
                    "generation_mode": answer["generation_mode"],
                }
            )
        ledger = case["ledger"]
        common = review_sources(case)
        reviews.append(
            {
                "id": f"R{number}",
                "question": case["request"]["question"],
                "player": case["context"]["player"],
                "clock": case["context"]["viewer_clock"],
                "options": options,
                "coverage": ledger["coverage"],
                "candidate_claims": ledger["claims"],
                "facts": ledger["facts"],
                **common,
                "aggregate_calculations": ledger["aggregate_calculations"],
            }
        )
    (folder / "blind.json").write_text(
        json.dumps(
            {"version": "label-blinded-v1", "cases": reviews},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (ROOT / "artifacts").mkdir(parents=True, exist_ok=True)
    (ROOT / "artifacts/review-unblinding.json").write_text(
        json.dumps(
            {
                "warning": "Keep this policy key from reviewers until they submit. Interface-label blinding, not secure or double blinding.",
                "key": key,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    selected = [r for r in data["rows"] if r["case_id"] == "5201-north-6"]
    (folder / "execution.json").write_text(
        json.dumps(
            {
                "disclosure": "Actual recorded Foundry executions, not fresh model calls from this page.",
                "manifest_sha256": data["manifest_sha256"],
                "source_hashes": data["source_hashes"],
                "comparison": selected,
                "checker_challenges": data["checker_challenges"],
                "summary": summary,
                "correction": correction_replay(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        "Built label-blinded review, six pilot situations and recorded execution. No human results created."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    build(args.results, args.summary)

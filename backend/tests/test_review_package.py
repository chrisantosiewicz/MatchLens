import runpy
from pathlib import Path


def package():
    return runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "scripts/build_review_package.py")
    )


def test_scripted_attribution_is_a_same_metric_event_backed_contrast():
    module = package()
    match = module["scripted_contrast"]("north-6")
    from matchlens.explainer import context_packet
    from matchlens.models import Clock

    context = context_packet(
        match, "north-6", Clock(period=2, elapsed_ms=1500000), 900000
    )
    contrast = context["editorial_context"]["player_team_contrast"]
    assert contrast["eligible"]
    assert contrast["player_before_count"] == 4 and contrast["player_after_count"] == 1
    assert contrast["team_before_count"] == 4 and contrast["team_after_count"] == 6


def test_recorded_correction_replay_retires_old_sequence_in_actual_engine():
    replay = package()["correction_replay"]()
    assert replay["before_source"] != replay["after_source"]
    assert replay["old_conclusion_id"] not in replay["after_candidate_ids"]
    assert replay["corrected_event"]["revision"] == 2


def test_study_cases_have_same_facts_for_both_conditions_and_no_results():
    cases = package()["study_cases"]()
    assert len(cases) == 6
    assert {c["kind"] for c in cases} == {"hidden", "attribution", "withheld"}
    assert all(
        c["facts"] and len(c["questions"]) == 2 and c["explanation"] for c in cases
    )
    assert not any("responses" in c or "participant" in c for c in cases)


def test_blinded_common_evidence_covers_full_clock_fallback_counts():
    from matchlens.api import Question, template_question
    from matchlens.claims import build_ledger
    from matchlens.explainer import context_packet
    from matchlens.models import Clock
    from matchlens.synthetic import generate_match

    match = generate_match(5209, "shift")
    request = Question(
        period=2,
        elapsed_ms=1500000,
        player_id="north-8",
        question="Why does this passing matter?",
    )
    context = context_packet(
        match,
        request.player_id,
        Clock(period=2, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    answer = template_question(match.id, request, match)
    ledger = build_ledger(request.model_dump(), context, answer)
    common = package()["review_sources"]({"context": context, "ledger": ledger})
    assert set(context["player_stats"]["evidence_ids"]) <= {
        e["event_id"] for e in common["events"]
    }
    assert (
        common["full_clock_stats"]["completed_passes"]
        == context["player_stats"]["completed_passes"]
    )
    assert common["metric_definitions"]["progressive_passes"]


def test_viewer_scoring_never_turns_QA_or_missing_people_into_user_evidence():
    module = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "scripts/score_viewer_study.py")
    )
    cases = package()["study_cases"]()
    empty = module["score"](cases, [])
    assert (
        empty["participants"] == 0 and empty["conditions"]["stats"]["accuracy"] is None
    )
    qa = {
        "kind": "study",
        "version": "pilot-v1",
        "code": "qa-only",
        "complete": True,
        "involved": "yes",
        "responses": [],
    }
    result = module["score"](cases, [qa])
    assert result["participants"] == 0 and len(result["excluded"]) == 1


def test_preexposed_viewers_are_not_counted_as_first_use_comprehension_evidence():
    module = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "scripts/score_viewer_study.py")
    )
    session = {
        "kind": "study",
        "version": "pilot-v1",
        "code": "exposed",
        "complete": True,
        "involved": "no",
        "prior_exposure": "yes",
        "responses": [],
    }
    result = module["score"](package()["study_cases"](), [session])
    assert result["participants"] == 0
    assert result["excluded"][0]["reason"] == "prior_exposure_or_unknown"


def test_review_rebuild_keeps_organizer_key_out_of_public_outputs(tmp_path):
    module = package()
    root = Path(__file__).resolve().parents[2]
    builder = module["build"]
    builder.__globals__["ROOT"] = tmp_path
    builder(
        root / "docs/evaluations/fair-canonical-v1.json",
        root / "docs/evaluations/fair-canonical-summary-v1.json",
    )
    assert (tmp_path / "artifacts/review-unblinding.json").is_file()
    assert not (tmp_path / "docs/review-unblinding.json").exists()
    assert not list((tmp_path / "frontend/public").rglob("*unblinding*"))

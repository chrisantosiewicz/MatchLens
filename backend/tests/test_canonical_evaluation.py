import runpy
from pathlib import Path

import pytest

evaluation = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/evaluate_canonical.py")
)


def test_checker_probes_have_good_controls_and_four_distinct_failure_classes():
    case = {
        "seed": 5201,
        "scenario": "shift",
        "request": {
            "period": 2,
            "elapsed_ms": 1500000,
            "player_id": "north-6",
            "question": "Why does this passing matter?",
        },
    }
    req, ctx, trusted = evaluation["load_case"](case)
    probes = evaluation["checker_cases"](req, ctx, trusted)
    assert len(probes) == 12
    assert sum(p["expected_accept"] for p in probes) == 4
    assert {p["kind"] for p in probes if not p["expected_accept"]} == {
        "wrong_scope",
        "overgeneralization",
        "omitted_limitation",
        "irrelevant_but_factual",
    }
    assert all(p["state"]["snapshot_id"] for p in probes)


def test_evaluation_enforces_call_cap_before_an_additional_paid_call():
    class Provider:
        last_usage = None

        def __init__(self):
            self.calls = 0

        def complete(self, role, state):
            self.calls += 1
            return {}

    provider = Provider()
    recorder = evaluation["Recorder"](provider, 1)
    recorder.complete("checker", {})
    with pytest.raises(RuntimeError, match="evaluation_call_limit"):
        recorder.complete("checker", {})
    assert provider.calls == 1


def test_frozen_evaluation_refuses_source_drift_and_overwrite(tmp_path):
    import json

    manifest = tmp_path / "manifest.json"
    output = tmp_path / "result.json"
    evaluation["freeze"](manifest)
    with pytest.raises(FileExistsError):
        evaluation["freeze"](manifest)
    specification = json.loads(manifest.read_text(encoding="utf-8"))
    specification["source_hashes"]["backend/matchlens/canonical.py"] = "stale"
    manifest.write_text(json.dumps(specification), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Frozen source changed"):
        evaluation["run"](manifest, output)
    assert not output.exists()

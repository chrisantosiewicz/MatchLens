from matchlens.evaluate import run_evaluation


def test_no_cloud_evaluation_records_skips_and_preserves_shared_cases():
    rows = run_evaluation()
    groups = {}
    for row in rows:
        groups.setdefault(row["case_id"], []).append(row)
        assert row["seed"] not in {7}
        assert row["factual_support"] is None
        assert row["cost_usd"] is None
    assert len(groups) >= 10
    for group in groups.values():
        assert {row["policy"] for row in group} == {"template", "single", "specialist"}
        assert len({row["question"] for row in group}) == 1
        assert (
            next(row for row in group if row["policy"] == "template")["status"]
            == "completed"
        )
        assert all(
            row["status"] == "skipped_no_live_provider"
            for row in group
            if row["policy"] != "template"
        )


def test_single_evaluation_uses_same_deterministic_count_routing_as_api():
    calls = []

    class Provider:
        def complete(self, role, state):
            calls.append(state["request"]["question"])
            return {"abstain": True}

    rows = run_evaluation(Provider(), policies=("single",))
    assert len(calls) == 6
    counts = [
        r
        for r in rows
        if "shots" in r["question"]
        or "tiros" in r["question"]
        or "completó" in r["question"]
    ]
    assert len(counts) == 6
    assert all(r["answer"]["generation_mode"] == "template" for r in counts)

from matchlens.workflow import run_workflow


class Scripted:
    def __init__(self, bad=False, reject=False):
        self.bad, self.reject = bad, reject

    def complete(self, role, state):
        if role == "analyst":
            return {"tool": "player_stats"}
        if role == "reviewer":
            return {
                "verdict": "revise" if self.reject else "accept",
                "reason": "Check sample",
            }
        return {
            "text": "Completed 999 passes" if self.bad else state["facts"][0]["text"],
            "fact_ids": ["invented"] if self.bad else [state["facts"][0]["id"]],
        }


def tool():
    return [
        {
            "id": "passes",
            "text": "Completed 3 of 4 passes.",
            "evidence_ids": ["e1", "e2", "e3", "e4"],
        }
    ]


def test_specialists_use_tools_and_record_handoffs():
    result = run_workflow({"question": "Passing?"}, {"player_stats": tool}, Scripted())
    assert result["text"] == "Completed 3 of 4 passes."
    assert result["generation_mode"] == "model"
    assert result["evidence_ids"] == ["e1", "e2", "e3", "e4"]
    assert [s["role"] for s in result["trace"]] == [
        "analyst",
        "tool",
        "reviewer",
        "producer",
        "validator",
    ]


def test_unknown_facts_and_changed_numbers_cannot_publish():
    result = run_workflow(
        {"question": "Passing?"}, {"player_stats": tool}, Scripted(bad=True)
    )
    assert result["generation_mode"] == "template"
    assert "999" not in result["text"]
    assert result["status"] == "fallback"


def test_revisions_are_bounded_and_timeout_has_factual_fallback():
    result = run_workflow(
        {"question": "Passing?"}, {"player_stats": tool}, Scripted(reject=True)
    )
    assert sum(t["role"] == "analyst" for t in result["trace"]) == 2
    assert result["status"] == "abstain"

    class Timeout:
        def complete(self, role, state):
            raise TimeoutError()

    result = run_workflow({}, {"player_stats": tool}, Timeout())
    assert result["generation_mode"] == "template"
    assert "Completed 3" in result["text"]


def test_no_provider_is_explicit_template_mode():
    assert (
        run_workflow({}, {"player_stats": tool}, None)["generation_mode"] == "template"
    )


def test_unavailable_tool_is_rejected_without_execution():
    class Malicious(Scripted):
        def complete(self, role, state):
            return {"tool": "arbitrary_sql"}

    result = run_workflow({}, {"player_stats": tool}, Malicious())
    assert result["generation_mode"] == "template"
    assert result["status"] == "fallback"


def test_wrong_tool_then_timeout_returns_requested_answer():
    class WrongThenTimeout:
        def complete(self, role, state):
            if role == "analyst":
                return {"tool": "season"}
            raise TimeoutError()

    wrong = lambda: [{"id": "season", "text": "Season baseline.", "evidence_ids": []}]
    answer = run_workflow(
        {}, {"requested_answer": tool, "season": wrong}, WrongThenTimeout()
    )
    assert answer["text"] == "Completed 3 of 4 passes."
    assert answer["evidence_ids"] == ["e1", "e2", "e3", "e4"]

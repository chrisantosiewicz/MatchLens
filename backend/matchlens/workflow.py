"""Bounded role orchestration. Not a claim of evaluated multi-agent superiority.

Models choose tools and compose approved factual sentences. Numerical calculations
and publication checks are code. Free-form model prose is deliberately withheld
until a richer claim parser is evaluated against a real Foundry deployment.
"""

from collections.abc import Callable
from typing import Protocol


class ModelProvider(Protocol):
    def complete(self, role: str, state: dict) -> dict: ...


def run_workflow(
    request: dict, tools: dict[str, Callable], provider: ModelProvider | None
) -> dict:
    trace: list[dict] = []
    facts: list[dict] = []

    def result(text, mode="template", status="fallback", chosen=None):
        selected = chosen if chosen is not None else facts
        ids = list(dict.fromkeys(e for f in selected for e in f["evidence_ids"]))
        return {
            "text": text,
            "generation_mode": mode,
            "status": status,
            "evidence_ids": ids,
            "trace": trace,
            "facts": selected,
        }

    def fallback():
        nonlocal facts
        if not facts and tools:
            facts = next(iter(tools.values()))()
        return result(
            " ".join(f["text"] for f in facts) or "Insufficient recorded evidence."
        )

    if provider is None:
        return fallback()
    state = {
        "request": request,
        "available_tools": list(tools),
        "facts": [],
        "feedback": None,
    }
    try:
        for attempt in range(2):
            calls = attempt + 1
            plan = provider.complete("analyst", state)
            trace.append(
                {"role": "analyst", "attempt": attempt + 1, "tool": plan.get("tool")}
            )
            name = plan.get("tool")
            if name not in tools or calls >= 8:
                raise ValueError("Unavailable tool or tool budget exhausted")
            facts = tools[name]()
            if any(
                not f.get("id")
                or not f.get("text")
                or not isinstance(f.get("evidence_ids"), list)
                for f in facts
            ):
                raise ValueError("Invalid fact contract")
            state["facts"] = facts
            trace.append({"role": "tool", "tool": name, "fact_count": len(facts)})
            review = provider.complete("reviewer", state)
            trace.append({"role": "reviewer", "verdict": review.get("verdict")})
            verdict = review.get("verdict")
            if verdict == "abstain":
                return result(
                    "Insufficient evidence for the requested interpretation.",
                    status="abstain",
                    chosen=[],
                )
            if verdict == "accept":
                break
            if verdict != "revise":
                raise ValueError("Invalid review verdict")
            state["feedback"] = str(review.get("reason", "Check evidence"))[:500]
        else:
            return result(
                "Insufficient evidence for the requested interpretation.",
                status="abstain",
                chosen=[],
            )
        output = provider.complete("producer", state)
        trace.append({"role": "producer"})
        lookup = {f["id"]: f for f in facts}
        selected_ids = output.get("fact_ids", [])
        if (
            not isinstance(selected_ids, list)
            or not selected_ids
            or len(set(selected_ids)) != len(selected_ids)
            or any(i not in lookup for i in selected_ids)
        ):
            raise ValueError("Unknown or invalid fact IDs")
        chosen = [lookup[i] for i in selected_ids]
        text = " ".join(f["text"] for f in chosen)
        # The model cannot smuggle unsupported facts in a different sentence.
        if output.get("text", text) != text:
            raise ValueError("Narrative differs from approved factual sentences")
        trace.append(
            {"role": "validator", "verdict": "accepted", "fact_ids": selected_ids}
        )
        return result(text, "model", "reviewed", chosen)
    except (TimeoutError, ValueError, KeyError, TypeError, RuntimeError):
        trace.append({"role": "validator", "verdict": "fallback"})
        return fallback()

import json
from contextlib import contextmanager
from types import SimpleNamespace

from matchlens.providers import FoundryProvider


def test_provider_reuses_client_requests_schema_and_records_all_usage():
    calls, lifecycle = [], []

    class Client:
        def with_options(self, **kwargs):
            return self

        @property
        def responses(self):
            return self

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                output_text=json.dumps(
                    {"abstain": True, "text": "", "evidence_ids": []}
                ),
                usage=SimpleNamespace(
                    model_dump=lambda: {"input_tokens": 12, "output_tokens": 3}
                ),
            )

    @contextmanager
    def factory(endpoint):
        lifecycle.append("open")
        yield Client()
        lifecycle.append("close")

    provider = FoundryProvider(
        "https://example.invalid/api/projects/test", "test", client_factory=factory
    )
    with provider:
        provider.complete("explainer", {})
        provider.complete("explainer", {})
        assert lifecycle == ["open"]
    assert lifecycle == ["open", "close"]
    assert calls[0]["text"]["format"]["type"] == "json_schema"
    assert calls[0]["text"]["format"]["strict"] is True
    assert sum(r["usage"]["input_tokens"] for r in provider.call_records) == 24

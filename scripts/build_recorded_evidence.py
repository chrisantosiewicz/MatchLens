"""Export auditable recorded results, checking source hashes and observed facts."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from matchlens.analytics import compare_windows, is_progressive, player_stats
from matchlens.explainer import model_context
from matchlens.models import Clock, visible
from matchlens.synthetic import generate_match
from package_judge import SECRET_TEXT


def export(trace_path, specification_path):
    root = Path(__file__).resolve().parents[1]
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    specification = json.loads(specification_path.read_text(encoding="utf-8"))
    assert (
        trace["manifest_sha256"]
        == hashlib.sha256(
            specification_path.read_text(encoding="utf-8").encode()
        ).hexdigest()
    )
    for name, expected in trace["source_hashes"].items():
        actual = hashlib.sha256(
            (root / name).read_text(encoding="utf-8").encode()
        ).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Cannot regenerate facts from changed source: {name}")
    target = root / "frontend/public/evidence"
    target.mkdir(parents=True, exist_ok=True)
    index = {
        "date": "2026-10-22",
        "model": "gpt-4.1-mini",
        "model_version": "2025-04-14",
        "manifest_sha256": trace["manifest_sha256"],
        "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        "live_generation": False,
        "independent_human_acceptance": False,
        "cases": [],
    }
    for case in specification["cases"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", case["id"]):
            raise ValueError("Invalid case filename")
        pair = {r["policy"]: r for r in trace["rows"] if r["case_id"] == case["id"]}
        assert set(pair) == {"template", "single"}
        assert all(
            row["status"] == "completed" and row["answer"] for row in pair.values()
        )
        context = pair["single"]["context"]
        assert context == pair["template"]["context"]
        match = generate_match(case["seed"], case["scenario"])
        clock = Clock(
            period=case["request"]["period"], elapsed_ms=case["request"]["elapsed_ms"]
        )
        events = visible(match.events, clock)
        assert (
            player_stats(events, case["request"]["player_id"], clock)
            == context["player_stats"]
        )
        anchor = case["request"]["anchor_ms"]
        support = []
        for window in ("before", "after"):
            selected = [
                e
                for e in events
                if e.period == clock.period
                and (
                    max(0, anchor - 600000) <= e.elapsed_ms < anchor
                    if window == "before"
                    else anchor
                    <= e.elapsed_ms
                    <= min(anchor + 600000, clock.elapsed_ms)
                    and clock.elapsed_ms > anchor
                )
            ]
            progressive_ids = [
                e.event_id
                for e in selected
                if e.player_id == context["player"]["id"] and is_progressive(e)
            ]
            assert (
                len(progressive_ids)
                == context[f"contributions_{window}"]["progressive_passes"]
            )
            support.extend(
                [
                    {
                        "label": f"Team box entries — {window}",
                        "count": context["comparison"][window]["box_entries"],
                        "minutes": context["window_minutes"][window],
                        "rate": context["rate_contract"][window],
                        "source_ids": context["comparison"][window]["evidence_ids"],
                    },
                    {
                        "label": f"Player progressive passes — {window}",
                        "count": len(progressive_ids),
                        "minutes": context["player_window_minutes"][window],
                        "rate": context["player_rates"][window][
                            "progressive_passes_per_minute"
                        ],
                        "source_ids": progressive_ids,
                    },
                ]
            )
        assert (
            compare_windows(
                events,
                Clock(period=clock.period, elapsed_ms=case["request"]["anchor_ms"]),
                clock,
                context["player"]["team_id"],
            )
            == context["comparison"]
        )
        payload = {
            "id": case["id"],
            "question": case["request"]["question"],
            "context": context,
            "reconstructed_model_input": {"request": pair["single"]["request"], "context": model_context(context)},
            "template": pair["template"],
            "single": pair["single"],
            "visible_events": [e.model_dump(mode="json") for e in events],
            "fact_support": support,
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ).encode()
        if SECRET_TEXT.search(encoded):
            raise ValueError("Credential-like content in export")
        filename = case["id"] + ".json"
        (target / filename).write_bytes(encoded)
        if pair['single']['answer'].get('generation_mode') == 'model' and 'default_case' not in index:
            index['default_case'] = filename
        index["cases"].append(
            {
                "id": case["id"],
                "question": case["request"]["question"],
                "player": context["player"]["name"],
                "file": filename,
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    (target / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(
        f"Exported {len(index['cases'])} paired cases; all selected-clock facts recomputed exactly."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    export(args.trace, args.manifest)

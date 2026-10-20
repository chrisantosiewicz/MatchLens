"""Local event-backed API. AI integration is deliberately explicit and deferred."""

from collections import Counter
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .analytics import compare_windows, player_stats
from .models import Clock, visible
from .moments import key_moments
from .profiles import profile
from .providers import configured_provider
from .synthetic import generate_match, generate_seasons
from .workflow import run_workflow

app = FastAPI(title="MatchLens", version="0.1.0")


@lru_cache
def fixtures():
    return {
        m.id: m for m in [generate_match(7, s) for s in ("shift", "null", "sparse")]
    }


@lru_cache
def seasons():
    return generate_seasons(7)


def match_or_404(match_id):
    if match_id not in fixtures():
        raise HTTPException(404, "Unknown match")
    return fixtures()[match_id]


def player_or_404(match, player_id):
    player = next((p for p in match.players if p.id == player_id), None)
    if player is None:
        raise HTTPException(404, "Unknown player")
    return player


def score_at(events):
    goals = Counter(
        e.team_id for e in events if e.event_type == "shot" and e.outcome == "goal"
    )
    return {"north": goals["north"], "harbor": goals["harbor"]}


def minutes_played(match, player_id, clock):
    player = player_or_404(match, player_id)
    end = (clock.period - 1) * 45 * 60_000 + clock.elapsed_ms
    start, stop = (0 if player.starter else None), end
    for e in visible(match.events, clock):
        if e.event_type != "substitution":
            continue
        time = (e.period - 1) * 45 * 60_000 + e.elapsed_ms
        if e.recipient_id == player_id:
            start = time
        if e.player_id == player_id:
            stop = time
    return round(max(0, stop - start) / 60_000, 1) if start is not None else 0


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "data_mode": "synthetic",
        "ai_mode": "template",
        "cloud_connected": False,
    }


@app.get("/api/matches")
def matches():
    return [
        {"id": m.id, "teams": m.teams, "label": label, "synthetic": True}
        for m, label in zip(
            fixtures().values(), ["Developing pattern", "Balanced match", "Sparse feed"]
        )
    ]


@app.get("/api/matches/{match_id}/state")
def state(
    match_id: str,
    period: int = Query(2, ge=1, le=2),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
):
    match = match_or_404(match_id)
    clock = Clock(period=period, elapsed_ms=elapsed_ms)
    events = visible(match.events, clock)
    return {
        "id": match.id,
        "teams": match.teams,
        "players": match.players,
        "clock": clock,
        "events": events,
        "score": score_at(events),
        "synthetic": True,
        "moments": [
            e
            for e in events
            if e.event_type == "substitution"
            or (e.event_type == "shot" and e.outcome == "goal")
        ],
    }


@app.get("/api/matches/{match_id}/players/{player_id}")
def player_detail(
    match_id: str,
    player_id: str,
    period: int = Query(2, ge=1, le=2),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
):
    match = match_or_404(match_id)
    player = player_or_404(match, player_id)
    clock = Clock(period=period, elapsed_ms=elapsed_ms)
    return {
        "player": player,
        "stats": player_stats(match.events, player_id, clock),
        "minutes_played": minutes_played(match, player_id, clock),
        "profile": profile(player_id, seasons()),
        "moments": key_moments(match.events, player_id, clock),
    }


@app.get("/api/matches/{match_id}/comparison")
def comparison(
    match_id: str,
    period: int = Query(2, ge=1, le=2),
    anchor_ms: int = Query(900_000, ge=0, le=2_700_000),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
    team_id: Literal["north", "harbor"] = "north",
):
    match = match_or_404(match_id)
    try:
        return compare_windows(
            match.events,
            Clock(period=period, elapsed_ms=anchor_ms),
            Clock(period=period, elapsed_ms=elapsed_ms),
            team_id,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


class Question(BaseModel):
    period: int = Field(ge=1, le=2)
    elapsed_ms: int = Field(ge=0, le=2_700_000)
    player_id: str
    question: str = Field(min_length=1, max_length=500)
    language: Literal["en", "es"] = "en"
    depth: Literal["casual", "analyst"] = "casual"
    anchor_ms: int = Field(default=900_000, ge=0, le=2_700_000)


def template_question(match_id: str, request: Question):
    match = match_or_404(match_id)
    player = player_or_404(match, request.player_id)
    clock = Clock(period=request.period, elapsed_ms=request.elapsed_ms)
    stats = player_stats(match.events, player.id, clock)
    q = request.question.lower()
    spanish = request.language == "es"
    evidence = stats["evidence_ids"]
    intent = "unsupported"
    if any(
        word in q
        for word in [
            "speed",
            "fast",
            "running",
            "off-ball",
            "shape",
            "velocidad",
            "corre",
        ]
    ):
        text = (
            "Este flujo de eventos no permite medir velocidad ni movimientos sin balón; se necesitan datos de tracking."
            if spanish
            else "This event feed cannot establish speed or off-ball movement; tracking data is required."
        )
        evidence = []
    elif any(
        word in q
        for word in ["usual", "season", "baseline", "normal", "temporada", "habitual"]
    ):
        intent = "season"
        baseline = profile(player.id, seasons())
        rates = {m["key"]: m["per90"] for m in baseline["metrics"]}
        minutes = minutes_played(match, player.id, clock)
        text = (
            f"{player.name}: {stats['progressive_passes']} pases progresivos en {minutes} minutos. Su referencia sintética es {rates['progressive_passes']} por 90 minutos. Una muestra de un partido no equivale a una temporada."
            if spanish
            else f"{player.name} has {stats['progressive_passes']} progressive passes in {minutes} minutes played. His synthetic season baseline is {rates['progressive_passes']} per 90. A single-match sample is not equivalent to a season."
        )
    elif any(
        word in q for word in ["changed", "since", "substitution", "cambio", "desde"]
    ):
        intent = "change"
        if request.anchor_ms > request.elapsed_ms:
            raise HTTPException(422, "Anchor is in the future")
        relevant = [e for e in match.events if e.period == clock.period]
        before = player_stats(
            [
                e
                for e in relevant
                if max(0, request.anchor_ms - 600000)
                <= e.elapsed_ms
                < request.anchor_ms
            ],
            player.id,
            clock,
        )
        after = player_stats(
            [
                e
                for e in relevant
                if request.anchor_ms
                <= e.elapsed_ms
                <= min(clock.elapsed_ms, request.anchor_ms + 600000)
            ],
            player.id,
            clock,
        )
        evidence = before["evidence_ids"] + after["evidence_ids"]
        text = (
            f"Acciones registradas: {before['actions']} antes y {after['actions']} después del momento seleccionado. La ventana posterior puede estar incompleta; no demuestra causalidad."
            if spanish
            else f"Recorded actions: {before['actions']} before and {after['actions']} after the selected moment. The after window may be incomplete; this does not establish causation."
        )
    elif any(word in q for word in ["pass", "passing", "pase", "pases"]):
        intent = "passing"
        text = (
            f"{player.name} completó {stats['completed_passes']} de {stats['pass_attempts']} pases, incluidos {stats['progressive_passes']} progresivos. Selecciona una acción en el campo para ver su destino."
            if spanish
            else f"{player.name} completed {stats['completed_passes']} of {stats['pass_attempts']} passes, including {stats['progressive_passes']} progressive passes. Select an action on the pitch to inspect its destination."
        )
    elif any(
        word in q
        for word in [
            "involved",
            "involvement",
            "moments",
            "contribution",
            "particip",
            "momentos",
        ]
    ):
        intent = "involvement"
        text = (
            f"{player.name} tiene {stats['actions']} acciones registradas, {stats['shots']} tiros y {stats['recoveries']} recuperaciones. Los momentos destacados muestran las secuencias que apoyan estos datos."
            if spanish
            else f"{player.name} has {stats['actions']} recorded actions, {stats['shots']} shots and {stats['recoveries']} recoveries. Key recorded moments show the sequences behind these counts."
        )
    else:
        text = (
            "Pregunta sobre participación, pases, cambios o su temporada sintética."
            if spanish
            else "Ask about involvement, passing, changes since a moment, or his synthetic season baseline."
        )
        evidence = []
    if request.depth == "analyst" and intent != "unsupported":
        text += (
            " Definición: un pase progresivo reduce al menos 10 m la distancia a la portería, desde fuera del área."
            if spanish
            else " Definition: a progressive pass reduces distance to goal by at least 10m, starting outside the box."
        )
    return {
        "text": text,
        "intent": intent,
        "evidence_ids": evidence,
        "generation_mode": "template",
        "language": request.language,
        "notice": "Deterministic explanation · Foundry not connected",
    }


@app.post("/api/matches/{match_id}/questions")
def question(match_id: str, request: Question):
    requested = template_question(match_id, request)

    def fact(answer, key):
        return [
            {"id": key, "text": answer["text"], "evidence_ids": answer["evidence_ids"]}
        ]

    tools = {"requested_answer": lambda: fact(requested, "requested")}
    if requested["intent"] != "unsupported":
        for name, text in {
            "player_stats": "How involved has he been?",
            "passing": "How is his passing?",
            "season_baseline": "Compare his usual season",
            "change": "What changed since the selected moment?",
        }.items():
            if name == "change" and request.anchor_ms > request.elapsed_ms:
                continue

            def call_tool(name=name, text=text):
                return fact(
                    template_question(
                        match_id, request.model_copy(update={"question": text})
                    ),
                    name,
                )

            tools[name] = call_tool
    try:
        provider = (
            configured_provider() if requested["intent"] != "unsupported" else None
        )
    except RuntimeError:
        provider = None
    result = run_workflow(request.model_dump(), tools, provider)
    return {
        **requested,
        **result,
        "notice": "Model-selected verified sentences"
        if result["generation_mode"] == "model"
        else "Deterministic template · live AI unavailable",
    }


@app.get("/api/matches/{match_id}/recap")
def recap(
    match_id: str,
    period: int = Query(2, ge=1, le=2),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
    language: Literal["en", "es"] = "en",
    player_id: str = "north-6",
):
    match = match_or_404(match_id)
    player = player_or_404(match, player_id)
    clock = Clock(period=period, elapsed_ms=elapsed_ms)
    events = visible(match.events, clock)
    score = score_at(events)
    stats = player_stats(events, player_id, clock)
    text = (
        f"Hasta este momento: Northbridge {score['north']}–{score['harbor']} Harbor. {player.name} completó {stats['completed_passes']} pases y registró {stats['shots']} tiros. Resumen limitado a tu reloj del partido."
        if language == "es"
        else f"At your match clock: Northbridge {score['north']}–{score['harbor']} Harbor. {player.name} completed {stats['completed_passes']} passes and recorded {stats['shots']} shots. This recap includes only events available at your clock."
    )
    return {
        "text": text,
        "score": score,
        "evidence_ids": stats["evidence_ids"],
        "generation_mode": "template",
    }

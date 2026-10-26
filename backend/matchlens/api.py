"""Local event-backed API. AI integration is deliberately explicit and deferred."""

import os
import secrets
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .alerts import progressive_alerts
from .analytics import compare_windows, player_stats
from .editorial import action_location, editorial_summary, editorial_summary_sources
from .explainer import context_packet, explain, interpretation_limit
from .limits import model_budget
from .models import Clock, Event, visible
from .moments import key_moments
from .profiles import profile
from .providers import configured_provider
from .store import EventStore
from .stories import render_story, sequence_stories
from .summaries import build_recap
from .synthetic import generate_match, generate_seasons
from .workflow import run_workflow

app = FastAPI(title="MatchLens", version="0.1.0")


@lru_cache
def fixtures():
    return {
        m.id: m
        for m in [generate_match(7, s) for s in ("shift", "null", "sparse", "corners")]
    }


@lru_cache
def seasons():
    return generate_seasons(7)


@lru_cache
def event_store():
    store = EventStore(os.getenv("MATCHLENS_EVENT_DB", ":memory:"))
    for match in fixtures().values():
        for event in match.events:
            store.upsert(event)
    return store


def match_or_404(match_id):
    if match_id not in fixtures():
        raise HTTPException(404, "Unknown match")
    return fixtures()[match_id].model_copy(
        update={"events": event_store().events_at(2, 3600000, match_id)}
    )


def source_version(match):
    revision_list = sorted((e.event_id, e.revision) for e in match.events)
    source = repr(revision_list)
    if match.position_frames:
        source += "|positions|" + "|".join(
            f.model_dump_json()
            for f in sorted(match.position_frames, key=lambda f: f.frame_id)
        )
    return sha256(source.encode()).hexdigest()[:24]


@app.post("/api/matches/{match_id}/events")
def ingest_event(
    match_id: str, event: Event, x_matchlens_token: str | None = Header(None)
):
    expected = os.getenv("MATCHLENS_INGEST_TOKEN", "")
    if (
        not expected
        or not x_matchlens_token
        or not secrets.compare_digest(expected, x_matchlens_token)
    ):
        raise HTTPException(401, "Ingestion requires an administrator token")
    match = match_or_404(match_id)
    if event.match_id != match_id or event.team_id not in match.teams:
        raise HTTPException(422, "Event match/team mismatch")
    roster = {p.id: p for p in match.players}
    for player_id in (event.player_id, event.recipient_id):
        if player_id and (
            player_id not in roster or roster[player_id].team_id != event.team_id
        ):
            raise HTTPException(422, "Unknown player or team mismatch")
    return event_store().upsert(event)


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
    mode = os.getenv("MATCHLENS_AI_MODE", "template")
    configured = bool(
        os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        and os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    )
    return {
        "status": "ok",
        "data_mode": "synthetic",
        "ai_mode": mode,
        "integration_status": (
            "configured_unverified" if configured else "missing_configuration"
        )
        if mode == "foundry"
        else "disabled",
        "cloud_connected": None if mode == "foundry" and configured else False,
    }


@app.get("/api/matches")
def matches():
    return [
        {"id": m.id, "teams": m.teams, "label": label, "synthetic": True}
        for m, label in zip(
            fixtures().values(),
            [
                "Developing pattern",
                "Balanced match",
                "Sparse feed",
                "Corners · simulated positions",
            ],
        )
    ]


@app.get("/api/matches/{match_id}/revision")
def revision(match_id: str):
    match = match_or_404(match_id)
    return {"id": match.id, "source_version": source_version(match)}


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
        "has_position_frames": bool(match.position_frames),
        "source_version": source_version(match),
        "teams": match.teams,
        "players": match.players,
        "clock": clock,
        "events": [
            {**e.model_dump(), "location_context": action_location(e)} for e in events
        ],
        "score": score_at(events),
        "feed_completeness": match.feed_completeness,
        "synthetic": True,
        "alerts": progressive_alerts(events, match.players, clock),
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
        "source_version": source_version(match),
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
        result = compare_windows(
            match.events,
            Clock(period=period, elapsed_ms=anchor_ms),
            Clock(period=period, elapsed_ms=elapsed_ms),
            team_id,
        )
        return {**result, "source_version": source_version(match)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/matches/{match_id}/set-pieces")
def set_pieces(
    match_id: str,
    period: int = Query(2, ge=1, le=2),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
    language: Literal["en", "es"] = "en",
):
    from .set_pieces import corner_context

    match = match_or_404(match_id)
    return {
        **corner_context(match, Clock(period=period, elapsed_ms=elapsed_ms), language),
        "source_version": source_version(match),
    }


class Question(BaseModel):
    period: int = Field(ge=1, le=2)
    elapsed_ms: int = Field(ge=0, le=2_700_000)
    player_id: str
    question: str = Field(min_length=1, max_length=500)
    language: Literal["en", "es"] = "en"
    depth: Literal["casual", "analyst"] = "casual"
    anchor_ms: int = Field(default=900_000, ge=0, le=2_700_000)


def template_question(match_id: str, request: Question, match=None):
    match = match if match is not None else match_or_404(match_id)
    player = player_or_404(match, request.player_id)
    clock = Clock(period=request.period, elapsed_ms=request.elapsed_ms)
    stats = player_stats(match.events, player.id, clock)
    q = request.question.lower()
    spanish = request.language == "es"
    evidence = stats["evidence_ids"]
    intent = "unsupported"
    from .guide import is_broad_question

    if is_broad_question(request.question):
        return {
            "text": f"¿Qué aspecto de {player.name} quieres explorar? Elige ataque, defensa o juego neutral."
            if spanish
            else f"What would you like to understand about {player.name}? Choose attacking, defending or neutral play.",
            "source_version": source_version(match),
            "intent": "clarify",
            "evidence_ids": [],
            "generation_mode": "template",
            "language": request.language,
            "notice": "Local clarification · choose an interest",
            "narrative_evidence": [],
            "editorial_context": None,
        }
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
    elif any(word in q for word in ["cause", "caused", "causar", "causaron", "provoc"]):
        text = (
            "Estos eventos no demuestran causalidad; una secuencia anterior al gol no prueba que lo causara."
            if spanish
            else "These events do not establish causation; an action preceding a goal does not prove it caused the goal."
        )
        evidence = []
    elif any(word in q for word in ["shot", "shoot", "tiro", "disparo"]):
        intent = "shooting"
        text = (
            f"{player.name}: {stats['shots']} tiros y {stats['goals']} goles hasta el tiempo seleccionado."
            if spanish
            else f"{player.name} has {stats['shots']} shots and {stats['goals']} goals at the selected time."
        )
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
                if clock.elapsed_ms > request.anchor_ms
                and request.anchor_ms
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
    elif any(word in q for word in ["defen", "recover", "tackle", "recuper"]):
        intent = "defending"
        defensive = [
            e
            for e in visible(match.events, clock)
            if e.player_id == player.id and e.event_type in {"recovery", "tackle"}
        ]
        recoveries = sum(e.event_type == "recovery" for e in defensive)
        tackles = len(defensive) - recoveries
        evidence = [e.event_id for e in defensive]
        text = (
            f"{player.name}: {recoveries} recuperaciones observadas y {tackles} entradas registradas. No mide coberturas, presión, éxito en entradas ni defensa sin balón."
            if spanish
            else f"{player.name} has {recoveries} observed recoveries and {tackles} recorded tackles at the selected time. These counts do not establish tackle success, pressure, cover or off-ball defending."
        )
    elif any(word in q for word in ["pass", "passing", "pase", "pases"]):
        intent = "passing"
        text = (
            f"{player.name} completó {stats['completed_passes']} de {stats['pass_attempts']} pases, incluidos {stats['progressive_passes']} progresivos. Selecciona una acción en el campo para ver su destino."
            if spanish
            else f"{player.name} completed {stats['completed_passes']} of {stats['pass_attempts']} passes, including {stats['progressive_passes']} progressive passes. Select an action on the pitch to inspect its destination."
        )
        if any(word in q for word in ("why", "por qué", "por que", "importa")):
            if stats["progressive_passes"]:
                text += (
                    " Estos pases acercaron el balón a la portería al menos 10 m desde fuera del área: registran progresión, no solo volumen de pases. Esto no demuestra calidad de ocasiones, superación de líneas defensivas ni causalidad."
                    if spanish
                    else " These passes moved the ball at least 10m closer to goal from outside the box: they record forward progression, beyond pass volume alone. This does not establish chance quality, defensive-line breaking or causation."
                )
            else:
                text += (
                    " No hay progresión registrada que cumpla nuestra definición; completar pases por sí solo no explica su impacto."
                    if spanish
                    else " No qualifying forward progression is recorded; pass completion alone does not establish impact."
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
    narrative = []
    editorial = None
    if intent in {"passing", "change", "involvement", "defending"}:
        start = (
            max(0, min(request.anchor_ms, clock.elapsed_ms) - 600000)
            if intent == "change"
            else max(0, clock.elapsed_ms - 600000)
        )
        story_clock = (
            Clock(
                period=clock.period,
                elapsed_ms=min(clock.elapsed_ms, request.anchor_ms + 600000),
            )
            if intent == "change"
            else clock
        )
        narrative = (
            sequence_stories(match, player.id, story_clock, start)
            if intent != "change" or clock.elapsed_ms > request.anchor_ms
            else []
        )
        if intent == "defending":
            narrative = [
                story
                for story in narrative
                if story["kind"]
                in {"recovery_followed_by_attack", "turnover_then_opposition_shot"}
            ]
        editorial = context_packet(match, player.id, clock, request.anchor_ms)[
            "editorial_context"
        ]
        summary = (
            ""
            if intent == "defending"
            or (intent == "change" and clock.elapsed_ms <= request.anchor_ms)
            else editorial_summary(editorial, player.name, request.language)
        )
        if summary:
            text = summary + " " + text
            evidence = list(
                dict.fromkeys(evidence + editorial_summary_sources(editorial))
            )
        if narrative:
            # A concrete sequence adds football meaning even when cloud generation is disabled.
            interpretive_story = intent in {"change", "involvement"} or any(
                word in q for word in ("why", "mean", "por qué", "por que", "importa")
            )
            if interpretive_story:
                text = render_story(narrative[0], request.language) + (
                    " " + text if request.depth == "analyst" else ""
                )
            evidence = list(dict.fromkeys(evidence + narrative[0]["evidence_ids"]))
    if request.depth == "analyst" and intent != "unsupported":
        text += (
            " Definición: un pase progresivo reduce al menos 10 m la distancia a la portería, desde fuera del área."
            if spanish
            else " Definition: a progressive pass reduces distance to goal by at least 10m, starting outside the box."
        )
    if match.feed_completeness == "incomplete":
        text += (
            " Datos incompletos: los recuentos incluyen solo los eventos observados."
            if spanish
            else " Incomplete feed: counts include observed events only."
        )
    answer = {
        "text": text,
        "source_version": source_version(match),
        "intent": intent,
        "evidence_ids": evidence,
        "generation_mode": "template",
        "language": request.language,
        "notice": "Deterministic event-backed answer",
        "narrative_evidence": narrative[:1],
        "editorial_context": editorial,
    }
    from .claims import enrich_answer

    packet = context_packet(
        match,
        request.player_id,
        Clock(period=request.period, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    return enrich_answer(request.model_dump(), packet, answer)


def interpretation_requested(request, requested):
    if request.language != "en":
        return False
    return requested["intent"] == "change" or any(
        word in request.question.lower()
        for word in ("why", "por qué", "por que", "importa")
    )


def compatible_trace(requested, result):
    # Legacy free-text workflows have no per-sentence contract; never attach template claims.
    if (
        result.get("generation_mode") == "model"
        or result.get("text", requested["text"]) != requested["text"]
    ):
        return {
            k: v
            for k, v in requested.items()
            if k
            not in {
                "claims",
                "evidence_trail",
                "primary_evidence_ids",
                "aggregate_evidence_ids",
            }
        }
    return requested


@app.post("/api/matches/{match_id}/questions")
def question(match_id: str, request: Question):
    match = match_or_404(match_id)
    from .set_pieces import corner_answer, is_corner_question

    if is_corner_question(request.question):
        player_or_404(match, request.player_id)
        return {
            **corner_answer(match, request.model_dump()),
            "source_version": source_version(match),
        }
    requested = template_question(match_id, request, match)
    interpretive = interpretation_requested(request, requested)
    if requested["intent"] == "clarify":
        return {**requested, "status": "clarification"}
    # The opt-in evidence chain preserves legacy evaluation policies unchanged.
    if os.getenv("MATCHLENS_AI_POLICY", "single") in {
        "evidence_chain",
        "canonical_single",
    }:
        from .claims import enrich_answer
        from .evidence_chain import run_evidence_chain

        packet = context_packet(
            match,
            request.player_id,
            Clock(period=request.period, elapsed_ms=request.elapsed_ms),
            request.anchor_ms,
        )
        if not interpretive or requested["intent"] == "unsupported":
            return {
                **enrich_answer(request.model_dump(), packet, requested),
                "status": "template",
            }
        try:
            provider = configured_provider()
        except RuntimeError:
            provider = None
        try:
            from .canonical import run_canonical

            runner = (
                run_canonical
                if os.getenv("MATCHLENS_AI_POLICY") == "canonical_single"
                else run_evidence_chain
            )
            result = runner(
                request.model_dump(),
                packet,
                requested,
                provider,
                acquire=model_budget().acquire,
            )
        finally:
            if hasattr(provider, "close"):
                provider.close()
        if source_version(match_or_404(match_id)) != requested["source_version"]:
            return {
                **template_question(match_id, request),
                "generation_mode": "fallback",
                "status": "source_changed",
                "notice": "Match corrected during analysis; refreshed local answer",
            }
        return {
            **result,
            "notice": "Experimental model-selected canonical explanation"
            if result["generation_mode"] == "model"
            else "Local evidence-backed explanation; inspect workflow status",
        }
    if os.getenv("MATCHLENS_AI_POLICY", "single") == "single" and not interpretive:
        return {
            **requested,
            "status": "abstain" if requested["intent"] == "unsupported" else "template",
            "notice": "Deterministic event-backed answer",
        }

    packet = None
    if (
        os.getenv("MATCHLENS_AI_POLICY", "single") == "single"
        and requested["intent"] != "unsupported"
    ):
        packet = context_packet(
            match,
            request.player_id,
            Clock(period=request.period, elapsed_ms=request.elapsed_ms),
            request.anchor_ms,
        )
        if interpretation_limit(request.model_dump(), packet):
            return {
                **requested,
                **explain(
                    request.model_dump(),
                    packet,
                    None,
                    requested["text"],
                    trusted_evidence_ids=requested["evidence_ids"],
                    trusted_narrative=requested["narrative_evidence"],
                ),
                "notice": "Deterministic explanation; input outside experimental interpretation scope",
            }

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
                        match_id, request.model_copy(update={"question": text}), match
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
    if provider is not None and not model_budget().acquire():
        if hasattr(provider, "close"):
            provider.close()
        return {
            **requested,
            "generation_mode": "fallback",
            "status": "budget_limited",
            "notice": "Local factual answer · demo model request budget reached",
        }
    if (
        os.getenv("MATCHLENS_AI_POLICY", "single") == "single"
        and requested["intent"] != "unsupported"
    ):
        assert packet is not None
        try:
            result = explain(
                request.model_dump(),
                packet,
                provider,
                requested["text"],
                trusted_evidence_ids=requested["evidence_ids"],
                trusted_narrative=requested["narrative_evidence"],
            )
        finally:
            if hasattr(provider, "close"):
                provider.close()
        return {
            **compatible_trace(requested, result),
            **result,
            "notice": (
                "Model declined interpretation; no factual conclusion"
                if result["status"] == "abstain"
                else "Experimental model interpretation; inspect supporting events"
                if result["generation_mode"] == "model"
                else "Deterministic explanation; input outside experimental interpretation scope"
                if result["status"] == "limited_input"
                else "Model unavailable or rejected; deterministic fallback"
                if result["generation_mode"] == "fallback"
                else "Deterministic event-backed explanation"
            ),
        }
    try:
        result = run_workflow(request.model_dump(), tools, provider)
    finally:
        if hasattr(provider, "close"):
            provider.close()
    return {
        **compatible_trace(requested, result),
        **result,
        "notice": "Model-selected verified sentences"
        if result["generation_mode"] == "model"
        else "Deterministic template · live AI unavailable",
    }


class GuideQuestion(Question):
    branch: Literal["attacking", "defending", "neutral"] = "neutral"
    seen_ids: list[str] = Field(default_factory=list, max_length=12)
    answer_conclusion_id: str | None = Field(default=None, max_length=500)
    expected_source_version: str | None = Field(default=None, max_length=128)


@app.post("/api/matches/{match_id}/guidance")
def guidance(match_id: str, request: GuideQuestion):
    from .guide import is_broad_question, run_guide

    match = match_or_404(match_id)
    player_or_404(match, request.player_id)
    expected = source_version(match)
    if request.expected_source_version and request.expected_source_version != expected:
        raise HTTPException(409, "Match evidence changed; request new guidance")
    packet = context_packet(
        match,
        request.player_id,
        Clock(period=request.period, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    try:
        provider = (
            None if is_broad_question(request.question) else configured_provider()
        )
    except RuntimeError:
        provider = None
    try:
        result = run_guide(
            match,
            request.model_dump(),
            packet,
            provider,
            acquire=model_budget().acquire,
        )
    finally:
        if hasattr(provider, "close"):
            provider.close()
    if source_version(match_or_404(match_id)) != expected:
        raise HTTPException(409, "Match corrected during guidance; refresh evidence")
    return result


@app.get("/api/matches/{match_id}/recap")
def recap(
    match_id: str,
    period: int = Query(2, ge=1, le=2),
    elapsed_ms: int = Query(1_200_000, ge=0, le=2_700_000),
    language: Literal["en", "es"] = "en",
    player_id: str = "north-6",
):
    match = match_or_404(match_id)
    player_or_404(match, player_id)
    clock = Clock(period=period, elapsed_ms=elapsed_ms)
    return {
        **build_recap(match, player_id, clock, language),
        "source_version": source_version(match),
    }


if os.getenv("MATCHLENS_FRONTEND_DIR"):
    from .serving import mount_frontend

    mount_frontend(app, os.environ["MATCHLENS_FRONTEND_DIR"])

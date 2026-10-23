"""Viewer-selected knowledge branches and one optional action-ranking agent."""

import re
import unicodedata
from time import perf_counter

from .claims import digest
from .editorial import passing_context
from .explainer import comparison_fact_support
from .models import Clock, visible
from .stories import render_story, sequence_stories

VERSION = "viewing-guide-v1"
BRANCHES = {"attacking", "defending", "neutral"}
FIFA_IN = "https://www.fifatrainingcentre.com/en/resources-tools/football-language/in-possession/index.php"
FIFA_OUT = "https://www.fifatrainingcentre.com/en/resources-tools/football-language/out-of-possession/index.php"
FA_PHASES = "https://learn.englandfootball.com/articles-and-resources/coaching/resources/2026/What-are-the-game-phases-in-football"


def normalized_question(text):
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def is_broad_question(text):
    q = normalized_question(text)
    return q in {
        "is he playing well",
        "is this player playing well",
        "how is he doing",
        "how is this player doing",
        "help me choose a question",
        "esta jugando bien",
        "como esta jugando",
        "ayudame a elegir una pregunta",
    } or bool(re.fullmatch(r"is .+ playing well", q))


def available_stories(match, request):
    return sequence_stories(
        match,
        request["player_id"],
        Clock(period=request["period"], elapsed_ms=request["elapsed_ms"]),
        max(0, request["elapsed_ms"] - 1200000),
        include_all=True,
    )


def build_catalog(match, request, context):
    branch = request.get("branch", "neutral")
    es = request.get("language") == "es"
    analyst = request.get("depth") == "analyst"
    if branch not in BRANCHES:
        raise ValueError("unknown_branch")
    clock = Clock(period=request["period"], elapsed_ms=request["elapsed_ms"])
    if clock.model_dump() != context["viewer_clock"]:
        raise ValueError("clock_mismatch")
    events = visible(match.events, clock)
    event_map = {e.event_id: e for e in events}
    source = context["editorial_context"]["source_revision"]
    player = context["player"]
    cards = []
    complete = (
        match.feed_completeness == "complete"
        and context["feed_completeness"] == "complete"
    )

    def add(id, kind, title, title_es, body, body_es, ids=(), **extra):
        ids = list(dict.fromkeys(ids))
        if any(i not in event_map for i in ids):
            raise ValueError("unavailable_action_source")
        cards.append(
            {
                "id": id,
                "kind": kind,
                "branch": branch,
                "title": title_es if es else title,
                "body": body_es if es else body,
                "subject_id": player["id"],
                "source_version": source,
                "viewer_clock": clock.model_dump(),
                "evidence_ids": ids,
                "event_revisions": {i: event_map[i].revision for i in ids},
                **extra,
            }
        )

    if branch == "attacking":
        definition = (
            "A completed pass starting outside the penalty area qualifies in MatchLens if its start/end coordinates reduce Euclidean distance to goal centre by at least 10m. This is our event metric, not a judgement of pass quality."
            if analyst
            else "In MatchLens, a completed progressive pass moves the ball at least 10m closer to goal from outside the box. Other passes can still appear in a useful recorded attack."
        )
        add(
            "concept_progression",
            "concept",
            "What counts as a progressive pass?",
            "¿Qué cuenta como pase progresivo?",
            definition,
            "En MatchLens, un pase completo desde fuera del área es progresivo si acerca el balón al centro de la portería al menos 10m. Otros pases también pueden participar en una jugada. No mide la calidad del pase.",
            definition_id="matchlens-progressive-pass-v1",
            references=[{"title": "Football language: in possession", "url": FIFA_IN}],
        )
        add(
            "ask_passing",
            "ask",
            "Explore this player’s passing",
            "Explorar sus pases",
            "Investigate recorded passing and a qualifying sequence, when one exists.",
            "Consulta los pases registrados y una secuencia válida, si existe.",
            question="¿Por qué importan sus pases?"
            if es
            else "Why does his passing matter?",
        )
    elif branch == "defending":
        add(
            "concept_defending",
            "concept",
            "What do recoveries and tackles tell us?",
            "¿Qué indican recuperaciones y entradas?",
            "They describe recorded on-ball actions. More recoveries or tackles do not by themselves establish better defending; positioning, pressure and cover are unobserved.",
            "Describen acciones registradas con balón. Más recuperaciones o entradas no demuestran por sí solas una mejor defensa; no se observan la presión, las coberturas ni la posición sin balón.",
            definition_id="recorded-defensive-actions-v1",
            references=[
                {"title": "Football language: out of possession", "url": FIFA_OUT}
            ],
        )
        defense = [
            e
            for e in events
            if e.player_id == player["id"] and e.event_type in {"recovery", "tackle"}
        ]
        recoveries = sum(e.event_type == "recovery" for e in defense)
        tackles = len(defense) - recoveries
        add(
            "defensive_counts",
            "facts",
            "Inspect recorded defensive actions",
            "Ver acciones defensivas registradas",
            f"{player['name']}: {recoveries} observed recoveries and {tackles} recorded tackles through this clock. These counts do not measure off-ball defending or tackle success.",
            f"{player['name']}: {recoveries} recuperaciones observadas y {tackles} entradas registradas hasta este tiempo. No mide defensa sin balón ni éxito de las entradas.",
            [e.event_id for e in defense],
            coverage=context["feed_completeness"],
        )
        add(
            "ask_defending",
            "ask",
            "Explore a defensive contribution",
            "Explorar su contribución defensiva",
            "Ask about recoveries, tackles and any qualifying follow-up sequence.",
            "Consulta recuperaciones, entradas y secuencias posteriores válidas.",
            question="¿Por qué importan sus recuperaciones registradas?"
            if es
            else "Why do his recorded recoveries matter?",
        )
    else:
        add(
            "concept_circulation",
            "concept",
            "Why pass sideways or backwards?",
            "¿Por qué pasar lateralmente o hacia atrás?",
            "Circulation can move the ball between teammates and reset an attack. A backward pass alone does not establish tempo management, safety or a good decision. Neutral is an exploration category here, not a detected tactical phase.",
            "La circulación permite mover el balón entre compañeros y reiniciar una jugada. Un pase hacia atrás no demuestra control del ritmo, seguridad ni una buena decisión. Neutral es una categoría de exploración, no una fase táctica detectada.",
            definition_id="circulation-limits-v1",
            references=[{"title": "Game phases", "url": FA_PHASES}],
        )
        p = passing_context(
            match, player["id"], clock, max(0, clock.elapsed_ms - 600000)
        )
        add(
            "circulation_counts",
            "facts",
            "Inspect circulation in the last ten minutes",
            "Ver circulación en los últimos diez minutos",
            f"{p['backward_completed']} observed completed backward passes in {p['window_minutes']} minutes; {p['located_attempts']} of {p['attempts']} pass attempts have both locations. Counts do not establish intent to control tempo.",
            f"{p['backward_completed']} pases completos hacia atrás observados en {p['window_minutes']} minutos; {p['located_attempts']} de {p['attempts']} intentos tienen ambas ubicaciones. No demuestra intención de controlar el ritmo.",
            p["evidence_ids"],
            coverage=context["feed_completeness"],
        )
        add(
            "ask_involvement",
            "ask",
            "Explore recorded involvement",
            "Explorar participación registrada",
            "Look at recorded actions and moments without inferring off-ball impact.",
            "Consulta acciones y momentos registrados sin inferir impacto sin balón.",
            question="¿Cómo ha participado?" if es else "How involved has he been?",
        )
    stories = available_stories(match, request) if complete else []
    wanted = (
        {"shot_build_up", "progression_without_shot", "recovery_followed_by_attack"}
        if branch == "attacking"
        else {"recovery_followed_by_attack", "turnover_then_opposition_shot"}
        if branch == "defending"
        else set()
    )
    stories = [s for s in stories if s["kind"] in wanted]
    anchor = request.get("answer_conclusion_id")
    stories.sort(
        key=lambda s: ("story:" + s["id"] != anchor, -s["sequence"][-1]["elapsed_ms"])
    )
    names = {p.id: p.name for p in match.players}
    seen = set(request.get("seen_ids", []))
    # Identity follows the story, not its rank or branch; seen stories cannot
    # occupy the two slots and make further eligible moves unreachable.
    stories = [s for s in stories if "sequence_" + digest(s["id"])[:20] not in seen]
    for story in stories[:2]:
        add(
            "sequence_" + digest(story["id"])[:20],
            "sequence",
            f"Explore the recorded move · {story['action_clock']}",
            f"Explorar la jugada · {story['action_clock']}",
            render_story(story),
            render_story(story, "es"),
            story["evidence_ids"],
            story_id=story["id"],
            sequence=[
                {**e, "actor_name": names.get(e["player_id"], e["player_id"])}
                for e in story["sequence"]
            ],
        )
    if (
        branch in {"attacking", "neutral"}
        and complete
        and all(m > 0 for m in context["window_minutes"].values())
        and all(m > 0 for m in context["player_window_minutes"].values())
    ):
        calculations = [
            f
            for f in comparison_fact_support(context)
            if f["metric"] in {"team_box_entries", "player_box_entries"}
        ]
        add(
            "compare_entries",
            "comparison",
            "Compare player and team box entries",
            "Comparar entradas al área de jugador y equipo",
            "Compare the same metric with its own window and active-minute denominators. These are descriptive counts, not a substitution effect, statistical significance or a measure of off-ball value.",
            "Compara la misma métrica con sus ventanas y minutos activos. Son recuentos descriptivos, no un efecto de la sustitución, significancia estadística ni valor sin balón.",
            [i for f in calculations for i in f["source_ids"]],
            calculations=calculations,
        )
    add(
        "evidence_limits",
        "concept",
        "What can this feed establish?",
        "¿Qué puede establecer este flujo?",
        (
            "Coverage is incomplete: count only observed actions. "
            if not complete
            else ""
        )
        + "Events do not measure defensive shape, pressure, off-ball movement or intent. An event sequence does not prove causation.",
        (
            "La cobertura es incompleta: solo se cuentan acciones observadas. "
            if not complete
            else ""
        )
        + "Los eventos no miden forma defensiva, presión, movimientos sin balón ni intención. Una secuencia no demuestra causalidad.",
        definition_id="event-feed-limits-v1",
    )
    # Declared local baseline: knowledge first for fan, inspectable sequence/comparison first for analyst.
    priority = (
        {"sequence": 0, "comparison": 1, "facts": 2, "ask": 3, "concept": 4}
        if analyst
        else {"concept": 0, "sequence": 1, "facts": 2, "ask": 3, "comparison": 4}
    )
    cards.sort(
        key=lambda c: (c["id"] == "evidence_limits" and complete, priority[c["kind"]])
    )
    seen = set(request.get("seen_ids", []))
    q = normalized_question(request.get("question", ""))
    return [
        c
        for c in cards
        if c["id"] not in seen
        and (c["kind"] != "ask" or normalized_question(c["question"]) != q)
    ]


def run_guide(match, request, context, provider=None, acquire=None):
    start = perf_counter()
    calls = 0
    reason = None
    mode = "template"
    clarification = is_broad_question(request["question"])
    try:
        catalog = build_catalog(match, request, context)
    except (ValueError, KeyError, TypeError):
        catalog = []
        reason = "invalid_context"
    source = context["editorial_context"]["source_revision"]
    snapshot = digest(
        {"version": VERSION, "request": request, "source": source, "catalog": catalog}
    )
    anchor = request.get("answer_conclusion_id")
    if anchor and anchor not in {
        "story:" + s["id"] for s in available_stories(match, request)
    }:
        reason = "unknown_answer_anchor"
        catalog = []
    if clarification:
        catalog = sorted(catalog, key=lambda c: c["kind"] != "ask")
    selected = catalog[:3]
    if provider is not None and catalog and not clarification and reason is None:
        try:
            if acquire is not None and not acquire():
                raise ValueError("budget_exhausted")
            calls += 1
            output = provider.complete(
                "viewing_guide",
                {
                    "snapshot_id": snapshot,
                    "request": request,
                    "coverage": context["feed_completeness"],
                    "player": context["player"],
                    "viewer_clock": context["viewer_clock"],
                    "source_revision": source,
                    "actions": catalog,
                    "instruction_boundary": "Rank only available action IDs. These branches are viewer interests, not inferred tactical phases.",
                },
            )
            if (
                not isinstance(output, dict)
                or set(output) != {"snapshot_id", "action_ids"}
                or output["snapshot_id"] != snapshot
            ):
                raise ValueError("invalid_guide_contract")
            ids = output["action_ids"]
            known = {c["id"]: c for c in catalog}
            if (
                not isinstance(ids, list)
                or not 1 <= len(ids) <= 3
                or len(set(ids)) != len(ids)
                or any(i not in known for i in ids)
            ):
                raise ValueError("invalid_guide_actions")
            selected = [known[i] for i in ids]
            mode = "model"
        except (RuntimeError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) else "guide_unavailable"
            mode = "fallback"
    return {
        "source_version": source,
        "snapshot_id": snapshot,
        "viewer_clock": context["viewer_clock"],
        "branch": request.get("branch", "neutral"),
        "cards": selected,
        "clarification": clarification,
        "generation_mode": mode,
        "model_calls": calls,
        "rejection_reason": reason,
        "latency_ms": round((perf_counter() - start) * 1000, 2),
        "notice": "Model-selected next steps"
        if mode == "model"
        else "Local next steps · model unavailable or rejected"
        if mode == "fallback"
        else "Local next steps · no model call",
    }

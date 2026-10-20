"""Seeded, fictional, event-only fixtures. Not calibrated to real competition data."""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from .models import Event, MatchFixture, Player, Point, SeasonRecord

LEAGUES = ["Albion Circuit", "Iberian Circuit", "Alpine Circuit", "Riviera Circuit", "Lowlands Circuit"]
POSITIONS = ["GK", "CB", "CB", "FB", "FB", "CM", "CM", "CM", "W", "W", "ST", "W", "CM"]
NAMES = ["Elias Vale", "Luca Moreno", "Jonas Berg", "Noah Costa", "Adam Laurent", "Mateo Silva", "Ibrahim Diallo", "Leon Fischer", "Rafael Cruz", "Kai Jensen", "Theo Marin", "Nico Vega", "Sami Morel"]


def squad() -> list[Player]:
    return [Player(id=f"{team}-{i+1}", name=name if team == "north" else NAMES[(i+5) % len(NAMES)] + " II",
                   team_id=team, number=i+1, position=pos, starter=i < 11)
            for team in ("north", "harbor") for i, (name, pos) in enumerate(zip(NAMES, POSITIONS))]


def generate_match(seed: int = 7, scenario: str = "shift") -> MatchFixture:
    if scenario not in {"shift", "null", "sparse"}:
        raise ValueError("scenario must be shift, null or sparse")
    rng = random.Random(seed)
    match_id = f"match-{seed}-{scenario}"
    players = squad()
    events: list[Event] = []
    score: Counter = Counter()
    active = {t: [p.id for p in players if p.team_id == t and p.starter] for t in ("north", "harbor")}

    def add(period, time, team, actor, kind, possession, start=None, end=None, recipient=None, outcome="recorded"):
        events.append(Event(match_id=match_id, event_id=f"{match_id}-e{len(events)+1}", sequence=len(events)+1,
                            period=period, elapsed_ms=time, team_id=team, player_id=actor,
                            recipient_id=recipient, event_type=kind, outcome=outcome,
                            possession_id=possession, start=start, end=end,
                            attack_right=(team == "north") == (period == 1)))

    for period in (1, 2):
        for k in range(90):
            base = k * 30_000
            if period == 2 and k == 30:
                add(period, base, "north", "north-9", "substitution", "sub-60", recipient="north-12")
                active["north"].remove("north-9")
                active["north"].append("north-12")
            if scenario == "sparse" and k % 6:
                continue
            team = "north" if k % 2 == 0 else "harbor"
            right = (team == "north") == (period == 1)
            pid = f"p{period}-{k}"
            pool = active[team][1:]
            actor = rng.choice(pool)
            # Twenty-second possessions start with a recorded recovery.
            x, y = rng.uniform(22, 40), rng.uniform(14, 54)

            def pt(a, b):
                return Point(x=round(a if right else 105-a, 2), y=round(b, 2))

            add(period, base+1000, team, actor, "recovery", pid, pt(x, y))
            for j in range(3):
                recipient = "north-6" if team == "north" and j == 0 else rng.choice([p for p in pool if p != actor])
                nx, ny = x + rng.uniform(9, 14), rng.uniform(15, 53)
                add(period, base+4000+j*3500, team, actor, "pass", pid, pt(x, y), pt(nx, ny), recipient, "complete")
                actor, x, y = recipient, nx, ny
            # Match rhythm changes through event probabilities, not labels sent to the analyst.
            shifted = scenario == "shift" and team == "north" and period == 2 and k >= 30
            enters = rng.random() < (0.88 if shifted else 0.48)
            if enters:
                lane = rng.uniform(14, 23) if shifted else rng.uniform(15, 53)
                recipient = "north-12" if shifted else rng.choice([p for p in pool if p != actor])
                add(period, base+16000, team, actor, "pass", pid, pt(x, y), pt(92, lane), recipient, "complete")
                actor, x, y = recipient, 92, lane
            elif rng.random() < 0.35:
                add(period, base+16000, team, actor, "pass", pid, pt(x, y), pt(min(x+12, 100), y), rng.choice(pool), "incomplete")
                continue
            # A shot terminates the possession, followed by a stoppage or next recovery.
            if enters or rng.random() < 0.18:
                outcome = rng.choices(["wide", "saved", "goal"], weights=[48, 48, 4])[0]
                add(period, base+22000, team, actor, "shot", pid, pt(x, y), pt(105, 34), outcome=outcome)
                if outcome == "goal":
                    score[team] += 1
                add(period, base+24000, team, None, "stoppage", pid)
            else:
                add(period, base+22000, team, actor, "turnover", pid, pt(x, y))
    return MatchFixture(id=match_id, teams={"north": "Northbridge FC", "harbor": "Harbor Athletic"},
                        players=players, events=events, final_score=dict(score))


def generate_seasons(seed: int = 7) -> list[SeasonRecord]:
    rng = random.Random(seed+1000)
    people = squad()
    for position in ("GK", "CB", "FB", "CM", "W", "ST"):
        for i in range(40):
            people.append(Player(id=f"peer-{position}-{i}", name=f"{NAMES[i % len(NAMES)]} {position}{i+1}",
                                 position=position, team_id="peer", number=i+1))
    records = []
    for i, p in enumerate(people):
        minutes = rng.randint(1000, 2600)
        rate = {"GK": 22, "CB": 55, "FB": 40, "CM": 52, "W": 27, "ST": 18}[p.position]
        factor = minutes/90
        records.append(SeasonRecord(player_id=p.id, name=p.name, position=p.position,
            league=LEAGUES[i % 5], minutes=minutes,
            completed_passes=int(factor*rate*rng.uniform(0.65, 1.35)),
            progressive_passes=int(factor*rng.uniform(2, 8)),
            shots=int(factor*rng.uniform(0.1 if p.position == "GK" else 0.6, 3.5)),
            recoveries=int(factor*rng.uniform(2, 9))))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for scenario in ("shift", "null", "sparse"):
        (args.output/f"{scenario}.json").write_text(generate_match(7, scenario).model_dump_json(indent=2), encoding="utf-8")
    (args.output/"seasons.json").write_text(json.dumps([s.model_dump() for s in generate_seasons()], indent=2), encoding="utf-8")
    (args.output/"manifest.json").write_text(json.dumps({"seed": 7, "synthetic": True, "scenarios": ["shift", "null", "sparse"]}), encoding="utf-8")


if __name__ == "__main__":
    main()

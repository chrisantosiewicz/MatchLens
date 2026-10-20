from .models import SeasonRecord

METRICS = {"completed_passes": "Completed passes", "progressive_passes": "Progressive passes", "shots": "Shots", "recoveries": "Recoveries"}


def percentile(value: float, peers: list[float]) -> float | None:
    if not peers:
        return None
    return round(100*(sum(p < value for p in peers)+0.5*sum(p == value for p in peers))/len(peers), 1)


def profile(player_id: str, seasons: list[SeasonRecord]) -> dict:
    player = next(s for s in seasons if s.player_id == player_id)
    cohort = [s for s in seasons if s.position == player.position and s.minutes >= 900]
    metrics = []
    for key, label in METRICS.items():
        value = getattr(player, key)*90/player.minutes if player.minutes else 0
        peers = [getattr(s, key)*90/s.minutes for s in cohort]
        metrics.append({"key": key, "label": label, "per90": round(value, 2),
                        "percentile": percentile(value, peers) if len(cohort) >= 30 and player.minutes >= 900 else None})
    return {"synthetic": True, "league": player.league, "minutes": player.minutes, "position": player.position,
            "cohort_size": len(cohort), "minimum_minutes": 900, "metrics": metrics,
            "cohort_label": "Five fictional European competitions · same position · 900+ minutes"}

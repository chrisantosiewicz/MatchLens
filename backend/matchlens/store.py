import sqlite3
from threading import RLock

from .models import Event


class EventStore:
    def __init__(self, path=":memory:"):
        self.lock = RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events (match_id TEXT,event_id TEXT,revision INTEGER,payload TEXT,PRIMARY KEY(match_id,event_id))"
        )
        self.db.commit()

    def upsert(self, event: Event) -> dict:
        with self.lock, self.db:
            previous = self.db.execute(
                "SELECT revision FROM events WHERE match_id=? AND event_id=?",
                (event.match_id, event.event_id),
            ).fetchone()
            if previous and previous[0] >= event.revision:
                return {"changed": False, "invalidated": []}
            self.db.execute(
                "INSERT OR REPLACE INTO events VALUES (?,?,?,?)",
                (
                    event.match_id,
                    event.event_id,
                    event.revision,
                    event.model_dump_json(),
                ),
            )
        return {"changed": True, "invalidated": [event.event_id] if previous else []}

    def events_at(
        self, period: int, elapsed_ms: int, match_id: str | None = None
    ) -> list[Event]:
        rows = self.db.execute(
            "SELECT payload FROM events" + (" WHERE match_id=?" if match_id else ""),
            (match_id,) if match_id else (),
        ).fetchall()
        events = [Event.model_validate_json(row[0]) for row in rows]
        return sorted(
            [e for e in events if (e.period, e.elapsed_ms) <= (period, elapsed_ms)],
            key=lambda e: (e.period, e.elapsed_ms, e.sequence),
        )

    def close(self):
        self.db.close()

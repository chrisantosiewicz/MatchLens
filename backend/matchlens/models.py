from typing import Literal

from pydantic import BaseModel, Field

Position = Literal["GK", "CB", "FB", "CM", "W", "ST"]


class Point(BaseModel):
    x: float = Field(ge=0, le=105)
    y: float = Field(ge=0, le=68)


class Player(BaseModel):
    id: str
    name: str
    team_id: str
    number: int
    position: Position
    starter: bool = True


class SetPiece(BaseModel):
    id: str
    kind: Literal["corner"] = "corner"
    phase: Literal["setup", "delivery", "first_contact", "outcome"]


class PlayerPosition(BaseModel):
    player_id: str
    point: Point


class PositionFrame(BaseModel):
    frame_id: str
    revision: int = Field(default=1, ge=1)
    simulated: Literal[True] = True
    period: int = Field(ge=1, le=2)
    elapsed_ms: int = Field(ge=0, le=3_600_000)
    anchor_event_id: str
    anchor_event_revision: int = Field(ge=1)
    ball: Point
    positions: list[PlayerPosition]


class Event(BaseModel):
    match_id: str = "demo"
    event_id: str
    revision: int = Field(default=1, ge=1)
    sequence: int = 0
    period: int = Field(ge=1, le=2)
    elapsed_ms: int = Field(ge=0, le=3_600_000)
    team_id: str
    player_id: str | None = None
    recipient_id: str | None = None
    event_type: Literal[
        "pass",
        "carry",
        "shot",
        "recovery",
        "tackle",
        "turnover",
        "substitution",
        "stoppage",
        "touch",
    ]
    outcome: Literal["complete", "incomplete", "goal", "saved", "wide", "recorded"] = (
        "recorded"
    )
    start: Point | None = None
    end: Point | None = None
    possession_id: str
    # Explicit metadata makes direction independent of receipt time and team name.
    attack_right: bool = True
    set_piece: SetPiece | None = None


class MatchFixture(BaseModel):
    schema_version: str = "1.0"
    id: str
    teams: dict[str, str]
    players: list[Player]
    events: list[Event]
    final_score: dict[str, int]
    feed_completeness: Literal["complete", "incomplete"] = "complete"
    position_frames: list[PositionFrame] = Field(default_factory=list)


class SeasonRecord(BaseModel):
    player_id: str
    name: str
    position: Position
    league: str
    minutes: int = Field(ge=0)
    completed_passes: int = Field(ge=0)
    progressive_passes: int = Field(ge=0)
    shots: int = Field(ge=0)
    recoveries: int = Field(ge=0)
    excludes_current_match: bool = True


class Clock(BaseModel):
    period: int = Field(ge=1, le=2)
    elapsed_ms: int = Field(ge=0, le=3_600_000)


def visible(events: list[Event], clock: Clock) -> list[Event]:
    return [
        e
        for e in events
        if (e.period, e.elapsed_ms) <= (clock.period, clock.elapsed_ms)
    ]

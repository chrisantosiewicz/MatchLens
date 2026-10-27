"""One revision identity for API facts and model context, including explicit positions."""

from hashlib import sha256


def source_version(match):
    source = repr(sorted((e.event_id, e.revision) for e in match.events))
    if match.position_frames:
        source += "|positions|" + "|".join(
            frame.model_dump_json()
            for frame in sorted(match.position_frames, key=lambda f: f.frame_id)
        )
    return sha256(source.encode()).hexdigest()[:24]

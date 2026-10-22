from concurrent.futures import ThreadPoolExecutor

from matchlens.store import EventStore
from matchlens.synthetic import generate_match


def test_concurrent_replay_reads_and_corrections_preserve_canonical_events():
    store = EventStore()
    events = generate_match().events[:60]
    for event in events:
        store.upsert(event)

    def read(_):
        for _ in range(12):
            snapshot = store.events_at(2, 2700000, events[0].match_id)
            assert len(snapshot) == 60
            assert len({e.event_id for e in snapshot}) == 60

    def correct(_):
        for revision in range(2, 26):
            store.upsert(events[0].model_copy(update={"revision": revision}))

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(read, i) for i in range(36)] + [pool.submit(correct, 0)]
        for future in futures:
            future.result()
    assert store.events_at(2, 2700000, events[0].match_id)[0].revision == 25
    store.close()

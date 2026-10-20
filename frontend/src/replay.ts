import type {Clock, MatchEvent} from './contracts';
export function visibleEvents(events: MatchEvent[], clock: Clock) {
  return events.filter(e => e.period < clock.period || (e.period === clock.period && e.elapsed_ms <= clock.elapsed_ms));
}
export function selectSequence(events: MatchEvent[], eventId: string, clock: Clock) {
  const selected = events.find(e=>e.event_id===eventId);
  return selected ? visibleEvents(events,clock).filter(e=>e.period===selected.period && e.possession_id===selected.possession_id) : [];
}

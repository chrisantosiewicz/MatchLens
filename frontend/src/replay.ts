import type {Clock, MatchEvent, Player} from './contracts';
export function visibleEvents(events: MatchEvent[], clock: Clock) {
  return events.filter(e => e.period < clock.period || (e.period === clock.period && e.elapsed_ms <= clock.elapsed_ms));
}
export function selectSequence(events: MatchEvent[], eventId: string, clock: Clock) {
  const selected = events.find(e=>e.event_id===eventId);
  return selected ? visibleEvents(events,clock).filter(e=>e.period===selected.period && e.possession_id===selected.possession_id) : [];
}

export function recentActions(events: MatchEvent[], clock: Clock, team='all', capacity=12) {
  return visibleEvents(events,clock)
    .filter(e=>e.period===clock.period && e.elapsed_ms>=clock.elapsed_ms-120000 && e.start && !['stoppage','substitution'].includes(e.event_type) && (team==='all'||e.team_id===team))
    .sort((a,b)=>a.elapsed_ms-b.elapsed_ms)
    .slice(-Math.max(1,capacity));
}

export function rosterAt(players:Player[],events:MatchEvent[],clock:Clock) {
  const active=new Set(players.filter(p=>p.starter).map(p=>p.id));
  for(const event of visibleEvents(events,clock))if(event.event_type==='substitution'){
    if(event.player_id)active.delete(event.player_id);
    if(event.recipient_id)active.add(event.recipient_id);
  }
  return players.filter(p=>active.has(p.id));
}

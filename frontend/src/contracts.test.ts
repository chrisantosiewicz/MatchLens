import {describe, it, expect} from 'vitest';
import {formatClock} from './contracts';
import {visibleEvents, selectSequence, recentActions, rosterAt} from './replay';
import type {MatchEvent} from './contracts';
import type {Player} from './contracts';

describe('viewer-safe replay', () => {
  const events = [{event_id:'a',period:1,elapsed_ms:100,possession_id:'p'}, {event_id:'b',period:2,elapsed_ms:100,possession_id:'p2'}, {event_id:'c',period:2,elapsed_ms:200,possession_id:'p2'}] as MatchEvent[];
  it('formats second-half time', () => expect(formatClock({period:2,elapsed_ms:900000})).toBe('60:00'));
  it('does not reveal future events when seeking', () => expect(visibleEvents(events,{period:2,elapsed_ms:100}).map(e=>e.event_id)).toEqual(['a','b']));
  it('bounds sequence by period and viewer clock', () => expect(selectSequence(events,'b',{period:2,elapsed_ms:100}).map(e=>e.event_id)).toEqual(['b']));
});

it('keeps both teams within two minutes and evicts the oldest beyond 12',()=>{
  const events = Array.from({length:20},(_,i)=>({event_id:String(i),period:2,elapsed_ms:i*5000,team_id:i%2?'harbor':'north',event_type:'pass',start:{x:30,y:20}})) as MatchEvent[];
  const result=recentActions(events,{period:2,elapsed_ms:95000});
  expect(result).toHaveLength(12);
  expect(result[0].event_id).toBe('8');
  expect(new Set(result.map(e=>e.team_id)).size).toBe(2);
  expect(recentActions(events,{period:2,elapsed_ms:220000})).toEqual([]);
  expect(recentActions(events,{period:2,elapsed_ms:95000},'north').every(e=>e.team_id==='north')).toBe(true);
});

it('preserves player identity until a substitution replaces the active jersey',()=>{
  const players=[{id:'out',number:9,starter:true},{id:'on',number:12,starter:false}] as Player[];
  const events=[{event_id:'sub',event_type:'substitution',player_id:'out',recipient_id:'on',period:2,elapsed_ms:1000}] as MatchEvent[];
  expect(rosterAt(players,events,{period:2,elapsed_ms:999}).map(p=>p.id)).toEqual(['out']);
  expect(rosterAt(players,events,{period:2,elapsed_ms:1000}).map(p=>p.id)).toEqual(['on']);
});

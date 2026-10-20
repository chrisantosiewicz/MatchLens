import {describe, it, expect} from 'vitest';
import {formatClock} from './contracts';
import {visibleEvents, selectSequence} from './replay';
import type {MatchEvent} from './contracts';

describe('viewer-safe replay', () => {
  const events = [{event_id:'a',period:1,elapsed_ms:100,possession_id:'p'}, {event_id:'b',period:2,elapsed_ms:100,possession_id:'p2'}, {event_id:'c',period:2,elapsed_ms:200,possession_id:'p2'}] as MatchEvent[];
  it('formats second-half time', () => expect(formatClock({period:2,elapsed_ms:900000})).toBe('60:00'));
  it('does not reveal future events when seeking', () => expect(visibleEvents(events,{period:2,elapsed_ms:100}).map(e=>e.event_id)).toEqual(['a','b']));
  it('bounds sequence by period and viewer clock', () => expect(selectSequence(events,'b',{period:2,elapsed_ms:100}).map(e=>e.event_id)).toEqual(['b']));
});

export type Clock = {period: number; elapsed_ms: number};
export type Player = {id: string; name: string; team_id: string; number: number; position: string; starter: boolean};
export type Point = {x: number; y: number};
export type MatchEvent = Clock & {event_id: string; player_id: string | null; recipient_id: string | null; team_id: string; event_type: string; outcome: string; start: Point | null; end: Point | null; possession_id: string; attack_right: boolean};
export type MatchInfo = {id: string; label: string; teams: Record<string,string>};
export type MilestoneAlert = Clock & {id:string;player_id:string;name:string;number:number;count:number;rank:number;runner_up:{player_id:string;name:string;count:number;rank:number}|null;event_id:string};
export type MatchState = {source_version?: string; id: string; teams: Record<string,string>; players: Player[]; events: MatchEvent[]; moments: MatchEvent[]; score: Record<string,number>; clock: Clock;alerts?:MilestoneAlert[]};
export type Stats = {actions: number; completed_passes: number; pass_attempts: number; pass_completion: number | null; progressive_passes: number; shots: number; goals: number; recoveries: number; box_entries: number; evidence_ids: string[]};
export type Moment = Clock & {id: string; rank: number; title: string; explanation: string; evidence_ids: string[]; sequence: MatchEvent[]};
export type ProfileMetric = {key: keyof Stats; label: string; per90: number; percentile: number | null};
export type PlayerDetail = {source_version?: string; player: Player; stats: Stats; minutes_played: number; moments: Moment[]; profile: {minutes: number; position: string; cohort_size: number; cohort_label: string; metrics: ProfileMetric[]}};
export type WindowStats = {box_entries_per_minute?: number|null; actions_per_minute?: number|null; box_entries: number; actions: number; duration_ms: number; routes: Record<string,number>; evidence_ids: string[]};
export type Comparison = {entry_rate_change?: 'increased'|'decreased'|'unchanged'|'not_comparable'; source_version?: string; before: WindowStats; after: WindowStats; provisional: boolean; pattern_supported: boolean};
export type Answer = {source_version?: string; notice?: string; text: string; intent?: string; generation_mode: string; evidence_ids: string[]};

export function formatClock(clock: Clock) {
  const seconds = Math.floor(clock.elapsed_ms / 1000);
  return `${(clock.period-1)*45+Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
}

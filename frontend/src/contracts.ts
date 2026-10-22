export type ActionLocation = {available:boolean;origin_zone?:string;destination_zone?:string;origin_half?:string;destination_half?:string;direction?:string;distance_m?:number;longitudinal_gain_m?:number;own_half_to_final_third?:boolean};
export type EditorialContext = {
 policy_version:string;coverage:string;source_revision:string;position:string;
 passing:{window_minutes:number;attempts:number;completed:number;located_attempts:number;backward_completed:number;recycling_eligible:boolean;origin_zones:Record<string,number>};
 player_team_contrast:{eligible:boolean;reason:string;player_before_count:number;player_after_count:number;team_before_count:number;team_after_count:number;before_minutes:number;after_minutes:number;player_before_minutes:number;player_after_minutes:number;player_before_rate:number|null;player_after_rate:number|null;team_before_rate:number|null;team_after_rate:number|null};
 box_access:{available:boolean;completed_entry_possessions:number;with_later_shot:number;unfinished_excluded:number;window_minutes:number;spotlight_eligible:boolean};
 game_state:{available:boolean;phase?:string;state?:string;score_for?:number;score_against?:number};
 replacement:{available:boolean;has_before_baseline:boolean;replaced_player:string|null;replaced_position:string|null;same_listed_position:boolean};
 on_ball_involvement:{eligible:boolean;recorded_actions:number;active_minutes:number};
 progression_loss_followups:{immediate_sequences:number;recorded_sequences:number;spotlight_eligible:boolean};
};
export type Clock = {period: number; elapsed_ms: number};
export type Player = {id: string; name: string; team_id: string; number: number; position: string; starter: boolean};
export type Point = {x: number; y: number};
export type MatchEvent = Clock & {location_context?:ActionLocation;event_id: string; player_id: string | null; recipient_id: string | null; team_id: string; event_type: string; outcome: string; start: Point | null; end: Point | null; possession_id: string; attack_right: boolean};
export type MatchInfo = {id: string; label: string; teams: Record<string,string>};
export type MilestoneAlert = Clock & {id:string;player_id:string;name:string;number:number;count:number;rank:number;runner_up:{player_id:string;name:string;count:number;rank:number}|null;event_id:string};
export type MatchState = {feed_completeness?: 'complete'|'incomplete'; source_version?: string; id: string; teams: Record<string,string>; players: Player[]; events: MatchEvent[]; moments: MatchEvent[]; score: Record<string,number>; clock: Clock;alerts?:MilestoneAlert[]};
export type Stats = {actions: number; completed_passes: number; pass_attempts: number; pass_completion: number | null; progressive_passes: number; shots: number; goals: number; recoveries: number; box_entries: number; evidence_ids: string[]};
export type Moment = Clock & {id: string; rank: number; title: string; explanation: string; evidence_ids: string[]; sequence: MatchEvent[]};
export type ProfileMetric = {key: keyof Stats; label: string; per90: number; percentile: number | null};
export type PlayerDetail = {source_version?: string; player: Player; stats: Stats; minutes_played: number; moments: Moment[]; profile: {minutes: number; position: string; cohort_size: number; cohort_label: string; metrics: ProfileMetric[]}};
export type WindowStats = {box_entries_per_minute?: number|null; actions_per_minute?: number|null; box_entries: number; actions: number; duration_ms: number; routes: Record<string,number>; evidence_ids: string[]};
export type Comparison = {entry_rate_change?: 'increased'|'decreased'|'unchanged'|'not_comparable'; source_version?: string; before: WindowStats; after: WindowStats; provisional: boolean; pattern_supported: boolean};
export type Answer = {editorial_context?:EditorialContext|null;narrative_evidence?:{id:string;kind:string;action_location?:ActionLocation;pass_rank_before_shot?:number|null;intervening_on_ball_actions?:number;action_clock:string;outcome_clock:string;meaning_en:string;meaning_es:string;limitation_en:string;limitation_es:string;evidence_ids:string[];sequence:MatchEvent[]}[];metric_definition?:string; model_cited_event_ids?:string[]; fact_support?:{metric:string;window:string;count:number;minutes:number;rate:number|null;source_ids:string[];period:number;start_ms:number;end_ms:number;end_inclusive:boolean}[]; source_version?: string; notice?: string; text: string; intent?: string; generation_mode: string; evidence_ids: string[]};

export function formatClock(clock: Clock) {
  const seconds = Math.floor(clock.elapsed_ms / 1000);
  return `${(clock.period-1)*45+Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
}

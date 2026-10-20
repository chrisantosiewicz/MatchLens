import type {MatchEvent, Player} from '../contracts';

export default function Pitch({events, players, selectedPlayer, onPlayer, onEvent, compact=false}: {
  events: MatchEvent[]; players: Player[]; selectedPlayer: string; onPlayer:(id:string)=>void; onEvent?:(event:MatchEvent)=>void; compact?:boolean;
}) {
  const actions = events.filter(e=>e.start && e.event_type!=='stoppage').slice(-30);
  return <div className={`pitch-wrap ${compact?'compact':''}`}>
    <svg className="pitch" viewBox="-5 -7 115 82" role="group" aria-label="Recorded football action map">
      <defs>
        <pattern id={compact?'grass-small':'grass'} width="21" height="68" patternUnits="userSpaceOnUse"><rect width="10.5" height="68" fill="#ffffff" opacity=".018"/></pattern>
        <marker id={compact?'arrow-small':'arrow'} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="#b8d581"/></marker>
      </defs>
      <rect x="0" y="0" width="105" height="68" fill="#132f29" rx=".5"/>
      <rect x="0" y="0" width="105" height="68" fill={`url(#${compact?'grass-small':'grass'})`}/>
      <g fill="none" stroke="#88a89c" strokeWidth=".24" opacity=".65">
        <rect width="105" height="68"/><path d="M52.5 0V68"/><circle cx="52.5" cy="34" r="9.15"/>
        <path d="M0 13.84H16.5V54.16H0 M105 13.84H88.5V54.16H105 M0 24.84H5.5V43.16H0 M105 24.84H99.5V43.16H105"/>
        <path d="M16.5 26.8 A9.15 9.15 0 0 1 16.5 41.2 M88.5 26.8 A9.15 9.15 0 0 0 88.5 41.2"/>
        <path d="M0 30H-2V38H0 M105 30H107V38H105"/><circle cx="52.5" cy="34" r=".5" fill="#88a89c"/>
      </g>
      {actions.map((e,i)=>e.end && <line key={`line-${e.event_id}`} x1={e.start!.x} y1={68-e.start!.y} x2={e.end.x} y2={68-e.end.y}
        stroke={e.player_id===selectedPlayer?'#c9f296':e.team_id==='north'?'#75bda5':'#e2aa8c'} strokeWidth={e.player_id===selectedPlayer?.65:.35}
        opacity={.24+i/actions.length*.48} strokeDasharray={e.outcome==='incomplete'?'1 1':undefined} markerEnd={`url(#${compact?'arrow-small':'arrow'})`}/>)}
      {actions.map((e,i)=>{
        const p = players.find(p=>p.id===e.player_id);
        return <g key={e.event_id} role="button" tabIndex={0} aria-label={`${p?.name??'Unknown player'} · ${e.event_type}`}
          onClick={()=>{if(e.player_id)onPlayer(e.player_id);onEvent?.(e);}}
          onKeyDown={k=>{if(k.key==='Enter'||k.key===' '){k.preventDefault();if(e.player_id)onPlayer(e.player_id);onEvent?.(e);}}} className="pitch-marker">
          <circle cx={e.start!.x} cy={68-e.start!.y} r={e.player_id===selectedPlayer?2:1.35} fill={e.player_id===selectedPlayer?'#c9f296':e.team_id==='north'?'#70baa4':'#d69b82'} stroke="#10211d" strokeWidth=".5" opacity={.55+i/actions.length*.45}/>
          {e.player_id===selectedPlayer && <text x={e.start!.x} y={68-e.start!.y+.7} fontSize="2" fill="#142416" textAnchor="middle" fontWeight="700">{p?.number}</text>}
        </g>;
      })}
      <text x="1" y="-2.5" fill="#83a998" fontSize="1.8" letterSpacing=".4">RECORDED ACTIONS · EVENT LOCATIONS</text>
      <text x="104" y="73" fill="#83a998" fontSize="1.8" textAnchor="end">SCHEMATIC VIEW / NO TRACKING</text>
    </svg>
  </div>;
}

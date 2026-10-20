import {useState} from 'react';
import {ArrowUpRight, X} from 'lucide-react';
import {formatClock} from '../contracts';
import {rosterAt} from '../replay';
import type {Clock,MatchEvent,MilestoneAlert,Player} from '../contracts';

function ordinal(n:number){const mod=n%100;return `${n}${mod>=11&&mod<=13?'th':({1:'st',2:'nd',3:'rd'}[n%10]??'th')}`;}

export default function SyntheticBroadcast({players,events,clock,selectedPlayer,onPlayer,alerts=[],compact=false}:{
  players:Player[];events:MatchEvent[];clock:Clock;selectedPlayer:string;onPlayer:(id:string)=>void;alerts?:MilestoneAlert[];compact?:boolean;
}){
  const [dismissed,setDismissed]=useState<string[]>([]);
  const active=rosterAt(players,events,clock);
  const positions:Record<string,[number,number]>={GK:[7,34],CB:[23,24],FB:[30,9],CM:[47,25],W:[70,13],ST:[82,34]};
  const latest=events.filter(e=>e.period===clock.period&&e.elapsed_ms<=clock.elapsed_ms&&e.start).slice(-1)[0];
  const alert=alerts.find(a=>!dismissed.includes(a.id)&&a.period===clock.period&&a.elapsed_ms<=clock.elapsed_ms&&clock.elapsed_ms-a.elapsed_ms<=12000);
  return <section className={`synthetic-broadcast panel ${compact?'is-compact':''}`} aria-label="Synthetic broadcast companion">
    {!compact&&<div className="broadcast-heading"><span><i className="live-dot"/>SYNTHETIC MATCH FEED</span><b>{formatClock(clock)}</b></div>}
    <svg viewBox="-5 -4 115 76" className="broadcast-scene" role="group" aria-label="Illustrative synthetic match scene">
      <defs><pattern id={compact?'video-grass-pip':'video-grass'} width="15" height="68" patternUnits="userSpaceOnUse"><rect width="7.5" height="68" fill="#a1c58e" opacity=".08"/></pattern></defs>
      <rect x="-5" y="-4" width="115" height="76" fill="#0f231b"/>
      <rect width="105" height="68" fill="#356248"/><rect width="105" height="68" fill={`url(#${compact?'video-grass-pip':'video-grass'})`}/>
      <g stroke="#e0e8cf" strokeWidth=".25" fill="none" opacity=".65"><rect width="105" height="68"/><path d="M52.5 0V68"/><circle cx="52.5" cy="34" r="9.15"/><path d="M0 13.84H16.5V54.16H0 M105 13.84H88.5V54.16H105 M0 24.84H5.5V43.16H0 M105 24.84H99.5V43.16H105"/></g>
      {active.map(p=>{
        const peers=active.filter(a=>a.team_id===p.team_id&&a.position===p.position);
        const offset=peers.findIndex(a=>a.id===p.id);
        const [baseX,baseY]=positions[p.position]??[50,34];
        const ownLast=events.filter(e=>e.period===clock.period&&e.elapsed_ms<=clock.elapsed_ms&&e.elapsed_ms>=clock.elapsed_ms-120000&&(e.player_id===p.id||e.recipient_id===p.id)&&e.start).slice(-1)[0];
        const right=(p.team_id==='north')===(clock.period===1);
        const point=ownLast?(ownLast.recipient_id===p.id?ownLast.end:ownLast.start):null;
        const x=point?.x??(right?baseX:105-baseX);
        const y=68-(point?.y??(peers.length>1?Math.min(59,baseY+offset*18):baseY));
        return <g key={p.id} role="button" tabIndex={0} aria-label={`${p.name}, number ${p.number}`} className="synthetic-player" onClick={()=>onPlayer(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onPlayer(p.id);}}}>
          <ellipse cx={x+.5} cy={y+1} rx="1.5" ry=".65" fill="#000" opacity=".3"/>
          {selectedPlayer===p.id&&<circle cx={x} cy={y} r="2.2" fill="none" stroke="#e4f9af" strokeWidth=".3"/>}
          <circle cx={x} cy={y} r="1.55" fill={p.team_id==='north'?'#d9f2a1':'#e7aa86'} stroke="#183625" strokeWidth=".25"/>
          <text x={x} y={y+.6} textAnchor="middle" fill="#192b22" fontSize="1.7" fontWeight="700">{p.number}</text>
        </g>;
      })}
      {latest&&<circle className="synthetic-ball" cx={(latest.end??latest.start)!.x} cy={68-(latest.end??latest.start)!.y} r=".65" fill="#fff" stroke="#172a21" strokeWidth=".2"/>}
    </svg>
    {alert&&!compact&&<div className="broadcast-alert"><button className="alert-main" onClick={()=>onPlayer(alert.player_id)}><span className="alert-kicker">PLAYER MILESTONE · {formatClock(alert)}</span><strong>{alert.name}’s {ordinal(alert.count)} progressive pass <ArrowUpRight size={15}/></strong>{alert.runner_up&&<small>{alert.runner_up.name} · {ordinal(alert.runner_up.rank)} in this match · {alert.runner_up.count} progressive passes</small>}<span className="alert-link">Explore player performance →</span></button><button className="alert-dismiss" aria-label="Dismiss milestone alert" onClick={()=>setDismissed(d=>[...d,alert.id])}><X size={13}/></button></div>}
    <div className="broadcast-caption">Illustrative synthetic scene · roster-linked identities, not video recognition</div>
  </section>;
}

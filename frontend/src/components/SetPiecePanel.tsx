import {useEffect,useRef,useState} from 'react';
import {api} from '../api';
import {formatClock} from '../contracts';
import type {Clock,CornerContext,PositionPhase} from '../contracts';

export default function SetPiecePanel({matchId,sourceVersion,clock,language,selectedPlayer,onPlayer}:{matchId:string;sourceVersion?:string;clock:Clock;language:string;selectedPlayer:string;onPlayer:(id:string)=>void}){
  const es=language==='es';
  const identity=JSON.stringify([matchId,sourceVersion,language]);
  const requestKey=JSON.stringify([identity,clock.period,clock.elapsed_ms]);
  const latest=useRef(requestKey);latest.current=requestKey;
  const [loaded,setLoaded]=useState<{identity:string;data:CornerContext}|null>(null);
  const [error,setError]=useState('');
  const [cornerId,setCornerId]=useState('');
  const [phase,setPhase]=useState<PositionPhase|'latest'>('latest');
  const [retry,setRetry]=useState(0);
  useEffect(()=>{
    let disposed=false;const controller=new AbortController();setError('');
    void api<CornerContext>(`/matches/${matchId}/set-pieces?period=${clock.period}&elapsed_ms=${clock.elapsed_ms}&language=${language}`,undefined,controller.signal).then(data=>{
      if(disposed||latest.current!==requestKey)return;
      if((sourceVersion&&data.source_version!==sourceVersion)||data.viewer_clock.period!==clock.period||data.viewer_clock.elapsed_ms!==clock.elapsed_ms){setLoaded(null);throw new Error('changed_source');}
      setLoaded({identity,data});
    }).catch(()=>{if(!disposed)setError(es?'No se pudieron actualizar las posiciones.':'Could not refresh positional evidence.');});
    return()=>{disposed=true;controller.abort();};
  },[matchId,sourceVersion,clock.period,clock.elapsed_ms,language,requestKey,identity,es,retry]);
  const data=loaded?.identity===identity&&(loaded.data.viewer_clock.period<clock.period||(loaded.data.viewer_clock.period===clock.period&&loaded.data.viewer_clock.elapsed_ms<=clock.elapsed_ms))?loaded.data:null;
  const corner=data?.corners.find(c=>c.id===cornerId)??data?.corners.at(-1);
  const frame=corner?.frames.find(f=>f.phase===phase)??corner?.frames.at(-1);
  const phases:Record<PositionPhase,string>=es?{setup:'Preparación',delivery:'Saque',first_contact:'Primer contacto',outcome:'Resultado'}:{setup:'Setup',delivery:'Delivery',first_contact:'First contact',outcome:'Outcome'};
  const players=new Map(data?.players.map(p=>[p.id,p])??[]);
  return <section className="panel set-piece-panel" aria-label={es?'Contexto posicional de córner':'Corner positional context'}>
    <div className="section-label">{es?'POSICIONES SIMULADAS · INSTANTÁNEAS':'SIMULATED POSITIONS · SNAPSHOTS'}</div>
    <h2>{es?'Quién ocupa el área':'Who occupies the box'}</h2>
    <p className="tiny muted">{es?'Todos los jugadores en instantes concretos. Vista separada de las ubicaciones de eventos; sin reconocimiento de vídeo.':'All players at discrete moments. Separate from ball-event locations; no video recognition.'}</p>
    {error&&<p role="alert">{error} <button onClick={()=>setRetry(n=>n+1)}>{es?'Reintentar':'Retry positions'}</button></p>}
    {!data&&<p role="status">{es?'Consultando evidencia posicional…':'Checking positional evidence…'}</p>}
    {data&&!corner&&<p>{es?'Todavía no hay córners observados en este tiempo.':'No observed corners at this clock yet.'}</p>}
    {data&&corner&&frame&&<>
      <label className="corner-picker">{es?'Córner observado':'Observed corner'} <select aria-label={es?'Córner observado':'Observed corner'} value={corner.id} onChange={e=>{setCornerId(e.target.value);setPhase('latest');}}>{data.corners.map(c=><option key={c.id} value={c.id}>{formatClock(c)} · {c.team_id==='north'?'Northbridge FC':'Harbor Athletic'}</option>)}</select></label>
      <div className="position-phases">{corner.frames.map(f=><button key={f.phase} aria-pressed={frame.phase===f.phase} onClick={()=>setPhase(f.phase)}>{phases[f.phase]}</button>)}</div>
      <p className="tiny muted">{es?'Instantánea':'Snapshot'} <strong>{formatClock(frame)}</strong> · {es?'evidencia hasta':'evidence through'} {formatClock(data.viewer_clock)} · {es?'Plantilla determinista':'Deterministic template'}</p>
      {frame.available&&frame.counts?<>
        <div className="occupancy-counts"><strong>{frame.counts.attackers} {es?'atacantes':'attackers'}</strong><span>{frame.counts.defenders} {es?'defensores':'defenders'} · {frame.counts.defending_goalkeepers} {es?'portero incluido':'goalkeeper included'}</span></div>
        <svg className="position-pitch" viewBox="-3 -3 111 74" role="group" aria-label={es?'Campo con posiciones simuladas':'Pitch with simulated positions'}>
          <rect x="0" y="0" width="105" height="68" fill="#163c31" stroke="#91b3a5" strokeWidth="0.3"/>
          <path d="M52.5 0V68 M0 13.84H16.5V54.16H0 M105 13.84H88.5V54.16H105 M0 24.84H5.5V43.16H0 M105 24.84H99.5V43.16H105" fill="none" stroke="#91b3a5" strokeWidth="0.3"/>
          <circle cx="52.5" cy="34" r="9.15" fill="none" stroke="#91b3a5" strokeWidth="0.3"/>
          <text x="52.5" y="4" textAnchor="middle" fill="#b4d4c6" fontSize="2">{corner.attack_right?'ATTACK →':'← ATTACK'}</text>
          {frame.positions.map(position=>{const p=players.get(position.player_id);if(!p)return null;return <g key={p.id} className="position-player" role="button" tabIndex={0} aria-label={`${p.name}, ${es?'número':'number'} ${p.number}, ${p.team_id}`} onClick={()=>onPlayer(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onPlayer(p.id);}}}>
            <circle cx={position.point.x} cy={position.point.y} r={p.id===selectedPlayer?2.25:1.8} fill={p.team_id===corner.team_id?'#d4f19a':'#91b8f8'} stroke={p.id===selectedPlayer?'#fff':'#0b2119'} strokeWidth={p.id===selectedPlayer?0.6:0.3}/>
            <text x={position.point.x} y={position.point.y+0.65} textAnchor="middle" fontSize="1.8" fill="#10231d" pointerEvents="none">{p.number}</text>
          </g>;})}
          {frame.ball&&<circle cx={frame.ball.x} cy={frame.ball.y} r="0.8" fill="white" stroke="black" strokeWidth="0.2"><title>{es?'Balón':'Ball'}</title></circle>}
        </svg>
        <p className="tiny muted"><span className="position-legend attacking"/> {es?'Equipo atacante':'Attacking team'} <span className="position-legend defending"/> {es?'Equipo defensor':'Defending team'} · {es?'Haz clic en un jugador para explorarlo.':'Click a player to explore.'}</p>
      </>:<p className="position-unavailable">{es?'Recuento no disponible: faltan posiciones completas o la evidencia cambió.':'Occupancy unavailable: complete positions are missing or the evidence changed.'}</p>}
      <p className="corner-narrative">{corner.text}</p>
      {!!corner.entered_box_ids.length&&<p className="tiny">{es?'De fuera a dentro entre preparación y saque':'Outside → inside between setup and delivery'}: {corner.entered_box_ids.map(id=>players.get(id)?.name??id).join(', ')}.</p>}
      <p className="tiny muted">{corner.limitation}</p>
      <details className="position-evidence"><summary>{es?'Inspeccionar fuentes posicionales':'Inspect positional sources'}</summary><p className="tiny">{frame.frame_id??'—'} · r{frame.frame_revision??'—'} · {frame.anchor_event_id} · r{frame.anchor_event_revision}</p><ol>{corner.events.map(e=><li key={e.event_id}>{formatClock(e)} · {players.get(e.player_id??'')?.name??(es?'Preparación':'Setup')} · {e.event_type} · {e.outcome}<small>{e.event_id} · r{corner.event_revisions[e.event_id]}</small></li>)}</ol></details>
    </>}
  </section>;
}

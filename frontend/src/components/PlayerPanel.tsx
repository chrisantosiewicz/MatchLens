import {ArrowUpRight, ChevronRight, CornerDownLeft, UserRound} from 'lucide-react';
import {useEffect, useRef, useState} from 'react';
import {api} from '../api';
import {formatClock} from '../contracts';
import type {Answer, Clock, Moment, PlayerDetail} from '../contracts';

export default function PlayerPanel({detail, clock, matchId, language, depth, anchor, onMoment, onInteract}: {
  detail: PlayerDetail | null; clock: Clock; matchId:string; language:string; depth:string; anchor:number; onMoment:(m:Moment)=>void; onInteract?:()=>void;
}) {
  const [tab,setTab] = useState('profile');
  const [question,setQuestion] = useState('');
  const [answer,setAnswer] = useState<Answer|null>(null);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [answerAt,setAnswerAt] = useState('');
  const active = useRef(0);
  const previousClock=useRef(clock);
  useEffect(()=>{
    const previous=previousClock.current;
    if(clock.period!==previous.period||clock.elapsed_ms<previous.elapsed_ms){active.current++;setAnswer(null);setBusy(false);}
    previousClock.current=clock;
  },[clock.period,clock.elapsed_ms]);
  useEffect(()=>{active.current++;setAnswer(null);setBusy(false);},[anchor,language,depth]);
  useEffect(()=>()=>{active.current++;},[]);
  const es = language==='es';
  async function ask(text=question) {
    if(!text.trim()||busy||!detail)return;
    onInteract?.();
    const request=++active.current;
    setBusy(true);setError('');setAnswer(null);
    try {const result=await api<Answer>(`/matches/${matchId}/questions`,{...clock,player_id:detail.player.id,question:text,language,depth,anchor_ms:anchor});if(request===active.current){setAnswer(result);setAnswerAt(formatClock(clock));}}
    catch(e){if(request===active.current)setError((e as Error).message);}finally{if(request===active.current)setBusy(false);}
  }
  if(!detail)return <aside className="panel loading-panel" aria-busy="true">{es?'Cargando perfil…':'Loading player profile…'}</aside>;
  const {player,stats,profile} = detail;
  return <aside className="player-panel panel" onFocusCapture={onInteract}>
    <div className="section-label"><span className="live-dot"/>{es?'JUGADOR SELECCIONADO':'PLAYER SPOTLIGHT'}<UserRound size={14}/></div>
    <div className="player-heading"><div className="shirt">{player.number}</div><div><span className="eyebrow">{player.team_id==='north'?'NORTHBRIDGE FC':'HARBOR ATHLETIC'} · {player.position}</span><h2>{player.name}</h2><p>{detail.minutes_played} {es?'minutos jugados':'minutes played'} <span>·</span> {es?'Datos sintéticos':'Synthetic data'}</p></div></div>
    <div className="player-stats"><div><b>{stats.completed_passes}<small>/{stats.pass_attempts}</small></b><span>{es?'Pases completos':'Passes completed'}</span></div><div><b>{stats.progressive_passes}</b><span>{es?'Progresivos':'Progressive passes'}</span></div><div><b>{stats.shots}</b><span>{es?'Tiros':'Shots'}</span></div></div>
    <div className="tabs" role="tablist" aria-label="Player details"><button role="tab" aria-selected={tab==='profile'} className={tab==='profile'?'active':''} onClick={()=>setTab('profile')}>{es?'Perfil y partido':'Profile & match'}</button><button role="tab" aria-selected={tab==='moments'} className={tab==='moments'?'active':''} onClick={()=>setTab('moments')}>{es?'Momentos clave':'Key moments'} <span>{detail.moments.length}</span></button></div>
    {tab==='profile'? <div className="profile-content">
      <div className="subheading"><h3>{es?'Su perfil de temporada':'His season profile'}</h3><span>PER 90</span></div>
      <p className="muted tiny">{es?'Percentiles sintéticos · Misma posición':'Synthetic percentiles · Same position'} · {profile.cohort_size} {es?'jugadores':'players'}</p>
      {profile.metrics.map(m=><div className="percentile" key={m.key}><div><span>{es?({completed_passes:'Pases completos',progressive_passes:'Pases progresivos',shots:'Tiros',recoveries:'Recuperaciones'}[m.key as string]??m.label):m.label}</span><b>{m.percentile===null?'—':Math.round(m.percentile)}<small> {es?'percentil':'pct'}</small></b></div><div className="bar"><i style={{width:`${m.percentile??0}%`}}/></div><div className="metric-baseline"><span>{m.per90} / 90 {es?'temporada':'season'}</span><span>{stats[m.key]} {es?'hoy':'today'}</span></div></div>)}
      <p className="cohort-note">{es?'Cinco competiciones ficticias · 900+ minutos de temporada. Hoy muestra recuentos; los percentiles describen la temporada sintética.':'Five fictional European competitions · 900+ season minutes. Today shows counts; percentiles describe the synthetic season.'}</p>
    </div>:<div className="moments-list">{detail.moments.length?detail.moments.map(m=><button className="moment-card" key={m.id} onClick={()=>onMoment(m)}><span className="moment-time">{formatClock(m)}</span><span><strong>{es?(({0:'Marcó un gol',1:'Participó en una secuencia con tiro',2:'Intentó un tiro',3:'Recuperación registrada',4:'Pérdida seguida de un tiro rival'}[m.rank]??m.title)):m.title}</strong><small>{m.evidence_ids.length} {es?'eventos de apoyo':'supporting events'} · {es?'Ver secuencia':'Explore sequence'}</small></span><ChevronRight size={15}/></button>):<p className="muted">{es?'Sin momentos registrados hasta ahora.':'No key recorded moments at this clock.'}</p>}<p className="cohort-note">{es?'Selección basada en eventos; no incluye movimientos sin balón.':'Selected from recorded events; off-ball contributions are not measured.'}</p></div>}
    <section className="ask-player"><div className="subheading"><h3>{es?'Pregunta sobre este jugador':'Ask about this player'}</h3><ArrowUpRight size={15}/></div><div className="suggestions">{(es?['¿Cómo ha participado?','¿Por qué importan sus pases?','¿Mejor que su temporada habitual?']:['How involved has he been?','Why does his passing matter?','Better than his usual season?']).map(q=><button key={q} onClick={()=>{setQuestion(q);void ask(q);}} disabled={busy}>{q}</button>)}</div>
      <form onSubmit={e=>{e.preventDefault();void ask();}}><input aria-label="Ask about selected player" value={question} onChange={e=>setQuestion(e.target.value)} placeholder={es?'Participación, pases, cambios…':'Involvement, passing, changes…'} maxLength={500}/><button aria-label="Send player question" disabled={busy||!question.trim()}><CornerDownLeft size={17}/></button></form>
      {busy&&<p className="tiny muted" role="status">{es?'Consultando eventos…':'Checking match events…'}</p>}
      {error&&<p role="alert" className="error-text">{error}</p>}
      {answer&&<div className="answer" aria-live="polite"><span>{es?'Respuesta a las':'Answer at'} {answerAt}</span><p>{answer.text}</p><span>{answer.evidence_ids.length} {answer.generation_mode==='model'?(es?'eventos · Interpretación del modelo; revisa la evidencia':'events · Model output; inspect evidence'):(es?'eventos · Explicación por plantilla':'events · Template explanation')}</span></div>}
      <p className="mode-note">{answer?.notice ?? (es?'Demo sintética · Respuestas locales disponibles':'Synthetic demo · Local answers available')}</p>
    </section>
  </aside>;
}

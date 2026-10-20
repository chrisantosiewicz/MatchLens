import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, ChevronDown, CircleHelp, Clock3, Crosshair, Globe2, Layers3, Maximize2, Pause, Play, Radio, RefreshCw, ShieldCheck, Sparkles, Target, Users} from 'lucide-react';
import {api} from './api';
import Pitch from './components/Pitch';
import PlayerPanel from './components/PlayerPanel';
import {formatClock} from './contracts';
import type {Answer, Comparison, MatchEvent, MatchInfo, MatchState, Moment, PlayerDetail} from './contracts';

export default function App() {
  const [matches,setMatches]=useState<MatchInfo[]>([]);
  const [matchId,setMatchId]=useState('');
  const [snapshot,setSnapshot]=useState<{key:string;state:MatchState;detail:PlayerDetail;comparison:Comparison}|null>(null);
  const [period,setPeriod]=useState(2);
  const [elapsed,setElapsed]=useState(1_500_000);
  const [anchor,setAnchor]=useState(900_000);
  const [player,setPlayer]=useState('north-6');
  const [team,setTeam]=useState('north');
  const [language,setLanguage]=useState('en');
  const [depth,setDepth]=useState('casual');
  const [playing,setPlaying]=useState(false);
  const [error,setError]=useState('');
  const [sequence,setSequence]=useState<MatchEvent[]|null>(null);
  const [recap,setRecap]=useState<Answer|null>(null);
  const [present,setPresent]=useState(false);
  const [retry,setRetry]=useState(0);
  const es=language==='es';
  const clock=useMemo(()=>({period,elapsed_ms:elapsed}),[period,elapsed]);
  const query=`period=${period}&elapsed_ms=${elapsed}`;
  const requestKey=`${matchId}/${query}/${player}/${anchor}/${team}`;
  const contextKey=`${requestKey}/${language}/${depth}`;
  const currentContext=useRef(contextKey);
  currentContext.current=contextKey;
  const state=snapshot?.key===requestKey?snapshot.state:null;
  const detail=snapshot?.key===requestKey?snapshot.detail:null;
  const comparison=snapshot?.key===requestKey?snapshot.comparison:null;
  const refreshMatches=useCallback(()=>{setError('');api<MatchInfo[]>('/matches').then(m=>{setMatches(m);setMatchId(m[0].id);}).catch(e=>setError(e.message));},[]);
  useEffect(refreshMatches,[refreshMatches]);
  useEffect(()=>{
    if(!matchId)return;
    const controller=new AbortController();
    setError('');
    Promise.all([
      api<MatchState>(`/matches/${matchId}/state?${query}`,undefined,controller.signal),
      api<PlayerDetail>(`/matches/${matchId}/players/${player}?${query}`,undefined,controller.signal),
      api<Comparison>(`/matches/${matchId}/comparison?${query}&anchor_ms=${Math.min(anchor,elapsed)}&team_id=${team}`,undefined,controller.signal)
    ]).then(([s,p,c])=>{if(!controller.signal.aborted)setSnapshot({key:requestKey,state:s,detail:p,comparison:c});}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});
    return ()=>controller.abort();
  },[matchId,query,player,anchor,elapsed,team,retry,requestKey]);
  useEffect(()=>{if(!playing)return;const id=setInterval(()=>setElapsed(t=>{if(t>=2700000){setPlaying(false);return 2700000;}return Math.min(t+10000,2700000);}),1000);return()=>clearInterval(id);},[playing]);
  useEffect(()=>{setSequence(null);setRecap(null);},[matchId,period,elapsed,player,language]);
  const selectedClock=formatClock({period,elapsed_ms:Math.min(anchor,elapsed)});
  const pitchEvents=(sequence??state?.events.filter(e=>e.period===period&&e.elapsed_ms>=Math.max(0,elapsed-180000)&&e.team_id===team)??[]).filter(e=>e.period<period||(e.period===period&&e.elapsed_ms<=elapsed));
  const otherPlayerName=state?.players.find(p=>p.id===player)?.name??'Player';
  const insight=useMemo(()=>{
    if(!comparison)return '';
    const b=comparison.before,a=comparison.after;
    if(!comparison.pattern_supported)return es?`Entradas al área: ${b.box_entries} antes, ${a.box_entries} después. La muestra es pequeña; aún no hay evidencia suficiente para describir un patrón.`:`Box entries: ${b.box_entries} before, ${a.box_entries} after. The sample is small; there isn't enough evidence yet to describe a pattern.`;
    return es?`Desde ${selectedClock}, las entradas al área pasaron de ${b.box_entries} a ${a.box_entries}. ${a.routes.right} de las ${a.box_entries} entradas posteriores fueron por la derecha.`:`Since ${selectedClock}, box entries went from ${b.box_entries} to ${a.box_entries}. ${a.routes.right} of ${a.box_entries} entries in the after window came down the right.`;
  },[comparison,es,selectedClock]);
  function choosePlayer(id:string){setPlayer(id);}
  function chooseMoment(m:Moment){setPlaying(false);setSequence(m.sequence);}
  async function createRecap(){const requested=contextKey;try{const result=await api<Answer>(`/matches/${matchId}/recap?${query}&language=${language}&player_id=${player}`);if(currentContext.current===requested)setRecap(result);}catch(e){if(currentContext.current===requested)setError((e as Error).message);}}
  if(present&&comparison)return <main className="presentation"><button className="ghost presentation-close" onClick={()=>setPresent(false)}>{es?'Volver al estudio':'Back to studio'}</button><div className="present-card"><div className="brand"><Crosshair/>MatchLens <span> / MATCH INSIGHT</span></div><h1>{insight}</h1><p>{selectedClock} → {formatClock(clock)} · {es?'Datos sintéticos · Explicación por plantilla':'Synthetic match data · Template explanation'}</p><div className="present-values"><span>{comparison.before.box_entries}<small>BEFORE</small></span><ArrowRight/><span>{comparison.after.box_entries}<small>AFTER</small></span></div></div></main>;
  return <div className="app-shell">
    <nav className="sidebar" aria-label="Main navigation"><a className="brand-mark" href="/" aria-label="MatchLens home"><Crosshair size={26}/></a><div className="nav-stack"><button className="nav-icon selected" aria-label="Match workspace"><Activity/></button><a className="nav-icon" href="#lineup" aria-label="Player lineup"><Users/></a><button className="nav-icon" aria-label="Generate recap" onClick={()=>void createRecap()} disabled={!state}><Layers3/></button></div><span className="side-word">MATCH INTELLIGENCE</span><button className="nav-icon help" aria-label="About synthetic data" onClick={()=>alert('All clubs, players, matches and season profiles are fictional. Pitch markers represent recorded events, not tracking positions. AI and cloud integration are not connected in this local prototype.')}><CircleHelp/></button></nav>
    <div className="main-shell"><header className="topbar"><div className="brand">MatchLens<span className="brand-divider"/> <span className="workspace-label">Live workspace</span></div><div className="top-right"><span className="status-pill"><i/>SYNTHETIC REPLAY</span><span className="avatar">ML</span></div></header>
      <main className="workspace"><div className="page-heading"><div><div className="eyebrow">THE STORY BEHIND THE SCORELINE</div><h1>{es?'Cada momento importa.':'Every moment matters.'}</h1><p>{es?'Ve qué cambió. Entiende quién participó.':'See what changed. Understand who made it happen.'}</p></div><div className="view-controls"><label><Globe2 size={14}/><select aria-label="Language" value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="es">Español</option></select></label><div className="segmented"><button className={depth==='casual'?'active':''} onClick={()=>setDepth('casual')}>{es?'Aficionado':'Fan'}</button><button className={depth==='analyst'?'active':''} onClick={()=>setDepth('analyst')}>{es?'Analista':'Analyst'}</button></div></div></div>
      {error&&<div role="alert" className="error-banner">{error}<button onClick={()=>{if(!matchId)refreshMatches();else setRetry(r=>r+1);}}>Retry</button></div>}
      <section className="matchbar panel"><div className="competition"><div className="eyebrow">MATCHDAY 08 · FICTIONAL LEAGUE</div><select aria-label="Synthetic match scenario" value={matchId} onChange={e=>{setMatchId(e.target.value);setPlaying(false);}}>{matches.map(m=><option key={m.id} value={m.id}>{m.label}</option>)}</select></div><div className="scoreboard"><span className="team-name">Northbridge <i className="crest north">N</i></span><b className="score">{state?.score.north??'–'}<span>:</span>{state?.score.harbor??'–'}</b><span className="team-name"><i className="crest harbor">H</i> Harbor Athletic</span></div><div className="match-clock"><span className="live-dot"/><b>{formatClock(clock)}</b><span>{period===1?'1ST':'2ND'} HALF</span></div></section>
      <div className="content-grid"><div className="analysis-column"><section className="panel analysis-panel"><div className="panel-heading"><div><div className="section-label"><Activity size={14}/>{es?'EL PUNTO DE INFLEXIÓN':'THE TURNING POINT'}</div><h2>{es?'Desde este momento':'Since this moment'}</h2></div><label className="team-select"><select aria-label="Team focus" value={team} onChange={e=>{setTeam(e.target.value);setPlayer(e.target.value+'-6');}}><option value="north">Northbridge FC</option><option value="harbor">Harbor Athletic</option></select><ChevronDown size={12}/></label></div>
        <div className="anchor-bar"><span className="anchor-icon"><Clock3 size={17}/></span><div><span className="tiny muted">{es?'MOMENTO SELECCIONADO':'SELECTED MOMENT'}</span><b>{selectedClock} <span>·</span> {period===2&&anchor===900000?(es?'Sustitución · Nico Vega entra':'Substitution · Nico Vega on'):(es?'Punto de comparación':'Comparison anchor')}</b></div><span className="window-tag">{comparison?.provisional?(es?'VENTANA PARCIAL':'PARTIAL WINDOW'):'10 MIN / 10 MIN'}</span></div>
        <div className="metric-grid">{[{label:es?'Entradas al área':'Box entries',before:comparison?.before.box_entries,after:comparison?.after.box_entries,icon:Target},{label:es?'Por la derecha':'Right-side entries',before:comparison?.before.routes.right,after:comparison?.after.routes.right,icon:ArrowUpRight},{label:es?'Acciones registradas':'Recorded actions',before:comparison?.before.actions,after:comparison?.after.actions,icon:BarChart3}].map(m=><div className="metric-card" key={m.label}><span><m.icon size={14}/>{m.label}</span><div className="metric-values"><b>{m.before??'—'}</b><ArrowRight size={15}/><strong>{m.after??'—'}</strong>{m.before!==undefined&&m.after!==undefined&&(m.after>=m.before?<ArrowUpRight size={15} className="positive"/>:<ArrowDownRight size={15} className="muted"/>)}</div><small>{es?'ANTES':'BEFORE'}<span>{es?'DESPUÉS':'AFTER'}</span></small></div>)}</div>
        <div className="pitch-heading"><div><span className="legend-dot"/>{sequence?(es?'Secuencia seleccionada':'Selected sequence'):(es?'Últimos 3 minutos':'Last 3 minutes')}<span className="muted"> · {sequence?otherPlayerName:(es?'Haz clic en un jugador':'Click a player to explore')}</span></div><button className="ghost" onClick={()=>sequence?setSequence(null):setPresent(true)} aria-label={sequence?'Clear selected sequence':'Open presentation preview'}>{sequence?<RefreshCw size={14}/>:<Maximize2 size={14}/>}</button></div>
        <Pitch events={pitchEvents} players={state?.players??[]} selectedPlayer={player} onPlayer={choosePlayer} onEvent={e=>{if(!sequence&&e.player_id)setPlayer(e.player_id);}}/>
        {depth==='analyst'&&comparison&&<div className="analyst-note">Windows: {(comparison.before.duration_ms/60000).toFixed(1)} min before / {(comparison.after.duration_ms/60000).toFixed(1)} min after. Box entry: completed pass or carry from outside into the penalty area. No causal inference.</div>}
        <div className="insight"><div className="insight-icon"><Sparkles size={18}/></div><div><div className="section-label">{es?'QUÉ NOS DICEN LOS DATOS':'WHAT THE EVENTS TELL US'}</div><p>{insight||'Loading match evidence…'}</p><span><ShieldCheck size={12}/>{es?'Cálculo determinista · No demuestra causalidad':'Deterministic calculation · Does not establish causation'}</span></div></div>
        <div className="panel-footer"><span>{comparison?(comparison.before.evidence_ids.length+comparison.after.evidence_ids.length):0} {es?'eventos de apoyo':'supporting entry events'}</span><button className="text-button" onClick={()=>{if(!state||!comparison)return;const ids=new Set([...comparison.before.evidence_ids,...comparison.after.evidence_ids]);setSequence(state.events.filter(e=>ids.has(e.event_id)));}}>{es?'Explorar evidencia':'Explore evidence'}<ArrowRight size={13}/></button></div>
      </section>
      <section className="panel timeline-panel"><div className="timeline-title"><div className="section-label"><Clock3 size={14}/>{es?'TU RELOJ DEL PARTIDO':'YOUR MATCH CLOCK'}</div><span className="tiny muted">{es?'Sin spoilers · Alineación manual':'Spoiler-safe · Manual alignment'}</span></div><div className="replay-controls"><button className="play-button" aria-label={playing?'Pause replay':'Play replay'} onClick={()=>setPlaying(!playing)}>{playing?<Pause size={17}/>:<Play size={17}/>}</button><select aria-label="Match period" value={period} onChange={e=>{setPeriod(Number(e.target.value));setElapsed(0);setAnchor(0);setPlaying(false);}}><option value="1">1st half</option><option value="2">2nd half</option></select><input aria-label="Match clock" type="range" min="0" max="2700000" step="10000" value={elapsed} onChange={e=>{setPlaying(false);setElapsed(Number(e.target.value));}}/><b>{formatClock(clock)}</b><span className="tiny muted">10×</span></div><div className="timeline-markers">{state?.moments.filter(e=>e.period===period).map(e=><button key={e.event_id} className={anchor===e.elapsed_ms?'active':''} onClick={()=>setAnchor(e.elapsed_ms)}>{formatClock(e)} {e.event_type==='substitution'?'↔':'⚽'}</button>)}<button onClick={()=>setAnchor(elapsed)}>{es?'Anclar aquí':'Set anchor here'} +</button></div></section>
      <section className="panel lineup-panel" id="lineup"><div className="subheading"><h3><Users size={15}/>{es?'Explora el equipo':'Explore the squad'}</h3><span>{es?'Selecciona cualquier jugador':'Select any player'}</span></div><div className="lineup">{state?.players.filter(p=>p.team_id===team).map(p=><button key={p.id} onClick={()=>setPlayer(p.id)} className={player===p.id?'active':''}><i>{p.number}</i><span>{p.name.split(' ').slice(0,2).join(' ')}<small>{p.position}{!p.starter?' · SUB':''}</small></span></button>)}</div></section>
      </div><PlayerPanel key={`${player}-${matchId}`} detail={detail} clock={clock} matchId={matchId} language={language} depth={depth} anchor={Math.min(anchor,elapsed)} onMoment={chooseMoment} onInteract={()=>setPlaying(false)}/></div>
      <section className="recap-strip panel"><div className="recap-icon"><Layers3 size={23}/></div><div><h3>{es?'Tu partido. Tu historia.':'Your match. Your story.'}</h3><p>{es?'Un resumen centrado en tu jugador y tu reloj del partido.':'A catch-up focused on your player, at your match clock.'}</p></div><button className="primary" disabled={!state} onClick={()=>void createRecap()}>{es?'Generar resumen':'Build my recap'}<ArrowRight size={15}/></button></section>
      {recap&&<section className="panel recap-result" aria-live="polite"><div className="section-label"><Layers3 size={15}/>{es?'RESUMEN PERSONALIZADO':'PERSONALIZED RECAP'}</div><p>{recap.text}</p><span className="tiny muted">{es?'Plantilla determinista · Solo datos sintéticos':'Deterministic template · Synthetic data only'}</span></section>}
      <footer className="workspace-footer"><span><Radio size={12}/>Local prototype · Synthetic events & season profiles</span><span>Foundry integration pending <span className="footer-divider">/</span> MatchLens © 2026</span></footer>
      </main>
    </div>
  </div>;
}

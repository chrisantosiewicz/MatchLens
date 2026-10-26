import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Activity, ArrowRight, ArrowUpRight, BarChart3, ChevronDown, CircleHelp, Clock3, Crosshair, Globe2, Layers3, Maximize2, Pause, Play, Radio, RefreshCw, ShieldCheck, Sparkles, Target, Users} from 'lucide-react';
import {api} from './api';
import Pitch from './components/Pitch';
import PlayerPanel from './components/PlayerPanel';
import SyntheticBroadcast from './components/SyntheticBroadcast';
import SetPiecePanel from './components/SetPiecePanel';
import {formatClock} from './contracts';
import {recentActions} from './replay';
import type {Answer, Comparison, MatchEvent, MatchInfo, MatchState, Moment, PlayerDetail} from './contracts';

export default function App() {
  const [matches,setMatches]=useState<MatchInfo[]>([]);
  const [matchId,setMatchId]=useState('');
  const [snapshot,setSnapshot]=useState<{key:string;matchId:string;period:number;elapsed:number;player:string;anchor:number;team:string;state:MatchState;detail:PlayerDetail;comparison:Comparison}|null>(null);
  const [period,setPeriod]=useState(2);
  const [elapsed,setElapsed]=useState(1_500_000);
  const [anchor,setAnchor]=useState(900_000);
  const [player,setPlayer]=useState('north-6');
  const [team,setTeam]=useState('north');
  const [actionTeam,setActionTeam]=useState('all');
  const [language,setLanguage]=useState('en');
  const [depth,setDepth]=useState('casual');
  const [playing,setPlaying]=useState(false);
  const [error,setError]=useState('');
  const [sequence,setSequence]=useState<MatchEvent[]|null>(null);
  const [storedRecap,setRecap]=useState<(Answer & {requestedClock:{period:number;elapsed_ms:number}})|null>(null);
  const [present,setPresent]=useState(false);
  const [view,setView]=useState<'watch'|'explore'>('explore');
  const [retry,setRetry]=useState(0);
  const [sourceVersion,setSourceVersion]=useState<string|undefined>();
  const knownSource=useRef<{matchId:string;version:string|undefined}|null>(null);
  const [correctionNotice,setCorrectionNotice]=useState(false);
  const [correctionCheckFailed,setCorrectionCheckFailed]=useState(false);
  const [narrativeRevision,setNarrativeRevision]=useState(0);
  const es=language==='es';
  const clock=useMemo(()=>({period,elapsed_ms:elapsed}),[period,elapsed]);
  const query=`period=${period}&elapsed_ms=${elapsed}`;
  const requestKey=`${matchId}/${query}/${player}/${anchor}/${team}`;
  const currentContext=useRef({matchId,player,language,depth,period,elapsed});
  currentContext.current={matchId,player,language,depth,period,elapsed};
  const recap=storedRecap&&storedRecap.requestedClock.period===period&&storedRecap.requestedClock.elapsed_ms<=elapsed?storedRecap:null;
  // Keep confirmed snapshots during forward play; never retain future facts on rewind.
  const safeSnapshot=snapshot?.matchId===matchId && snapshot.period===period && snapshot.elapsed<=elapsed;
  const state=safeSnapshot?snapshot.state:null;
  const detail=safeSnapshot&&snapshot.player===player?snapshot.detail:null;
  const comparison=safeSnapshot&&snapshot.anchor===anchor&&snapshot.team===team?snapshot.comparison:null;
  const updating=snapshot?.key!==requestKey;
  const refreshMatches=useCallback(()=>{setError('');api<MatchInfo[]>('/matches').then(m=>{setMatches(m);setMatchId(m[0].id);}).catch(e=>setError(e.message));},[]);
  useEffect(refreshMatches,[refreshMatches]);
  useEffect(()=>{
    if(!matchId)return;
    const controller=new AbortController();
    setError('');
    async function refresh(){
      // Retry once when a correction lands between reads; no background polling.
      for(let attempt=0;attempt<2;attempt++){
        const [s,p,c]=await Promise.all([
          api<MatchState>(`/matches/${matchId}/state?${query}`,undefined,controller.signal),
          api<PlayerDetail>(`/matches/${matchId}/players/${player}?${query}`,undefined,controller.signal),
          api<Comparison>(`/matches/${matchId}/comparison?${query}&anchor_ms=${Math.min(anchor,elapsed)}&team_id=${team}`,undefined,controller.signal)
        ]);
        if(controller.signal.aborted)return;
        const previous=knownSource.current;
        const changed=previous?.matchId===matchId&&previous.version!==s.source_version;
        const mixed=s.source_version!==p.source_version||s.source_version!==c.source_version;
        if(changed||mixed){setNarrativeRevision(n=>n+1);setSnapshot(null);setSequence(null);setRecap(null);setCorrectionNotice(true);}
        if(!previous||previous.matchId!==matchId||changed||mixed)knownSource.current={matchId,version:s.source_version};
        setSourceVersion(s.source_version);
        if(!mixed){setSnapshot({key:requestKey,matchId,period,elapsed,player,anchor,team,state:s,detail:p,comparison:c});return;}
      }
      throw new Error('Match events changed during loading. Retry to load consistent evidence.');
    }
    void refresh().catch(e=>{if(!controller.signal.aborted&&e.name!=='AbortError')setError(e.message);});
    return ()=>controller.abort();
  },[matchId,query,player,anchor,elapsed,team,retry,requestKey]);
  useEffect(()=>{
    if(!matchId||playing)return;
    let active=true;
    const controller=new AbortController();
    const timer=setInterval(()=>{
      if(document.visibilityState==='hidden'||!knownSource.current?.version)return;
      void api<{source_version:string}>(`/matches/${matchId}/revision`,undefined,controller.signal).then(revision=>{
        if(!active||knownSource.current?.matchId!==matchId||typeof revision.source_version!=='string')return;
        setCorrectionCheckFailed(false);
        if(revision.source_version===knownSource.current.version)return;
        knownSource.current={matchId,version:revision.source_version};
        setSourceVersion(revision.source_version);setNarrativeRevision(n=>n+1);setRecap(null);setSequence(null);setSnapshot(null);setCorrectionNotice(true);setRetry(n=>n+1);
      }).catch(()=>{if(active)setCorrectionCheckFailed(true);});
    },15000);
    return()=>{active=false;controller.abort();clearInterval(timer);};
  },[matchId,playing]);
  useEffect(()=>{if(!playing)return;const id=setInterval(()=>setElapsed(t=>{if(t>=2700000){setPlaying(false);return 2700000;}return Math.min(t+10000,2700000);}),1000);return()=>clearInterval(id);},[playing]);
  useEffect(()=>{setSequence(null);},[matchId,period,elapsed,player,language]);
  useEffect(()=>{setRecap(null);},[matchId,period,player,language,depth]);
  const effectiveAnchor=Math.min(anchor,elapsed);
  const selectedClock=formatClock({period,elapsed_ms:effectiveAnchor});
  const anchorEvent=state?.moments.find(e=>e.period===period&&e.elapsed_ms===effectiveAnchor&&e.elapsed_ms<=elapsed);
  const incomingPlayer=anchorEvent?.event_type==='substitution'?state?.players.find(p=>p.id===anchorEvent.recipient_id):undefined;
  const anchorLabel=incomingPlayer?(es?`Sustitución · ${incomingPlayer.name} entra`:`Substitution · ${incomingPlayer.name} on`):(es?'Punto de comparación':'Comparison anchor');
  const pitchEvents=(sequence??recentActions(state?.events??[],clock,actionTeam)).filter(e=>e.period<period||(e.period===period&&e.elapsed_ms<=elapsed));
  const otherPlayerName=state?.players.find(p=>p.id===player)?.name??'Player';
  const insight=useMemo(()=>{
    if(!comparison)return '';
    const b=comparison.before,a=comparison.after;
    const beforeMinutes=(b.duration_ms/60000).toFixed(1),afterMinutes=(a.duration_ms/60000).toFixed(1);
    const counts=es?`Entradas al área registradas: ${b.box_entries} en ${beforeMinutes} min antes; ${a.box_entries} en ${afterMinutes} min después.`:`Recorded box entries: ${b.box_entries} in ${beforeMinutes} min before; ${a.box_entries} in ${afterMinutes} min after.`;
    const rates=b.box_entries_per_minute!=null&&a.box_entries_per_minute!=null
      ?(es?` Frecuencia por minuto: ${b.box_entries_per_minute.toFixed(2)} antes y ${a.box_entries_per_minute.toFixed(2)} después.`:` Rate per minute: ${b.box_entries_per_minute.toFixed(2)} before and ${a.box_entries_per_minute.toFixed(2)} after.`)
      :(es?' Sin ventanas comparables para calcular frecuencias.':' Comparable window rates are unavailable.');
    const caveat=!comparison.pattern_supported
      ?(es?' La muestra es pequeña; aún no hay evidencia suficiente para describir un patrón.':' The sample is small; there is not enough evidence yet to describe a pattern.')
      :(es?' Asociación temporal; no demuestra causalidad.':' Temporal association; does not establish causation.');
    return counts+rates+caveat;

  },[comparison,es,selectedClock]);
  function choosePlayer(id:string){setPlayer(id);}
  function chooseMoment(m:Moment){setPlaying(false);setSequence(m.sequence);}
  async function createRecap(){
    const requested={...currentContext.current};
    const requestedSource=knownSource.current;
    const stillRelevant=()=>{const latest=currentContext.current;return knownSource.current===requestedSource&&latest.matchId===requested.matchId&&latest.player===requested.player&&latest.language===requested.language&&latest.depth===requested.depth&&latest.period===requested.period&&latest.elapsed>=requested.elapsed;};
    try{const result=await api<Answer>(`/matches/${matchId}/recap?${query}&language=${language}&player_id=${player}`);if(stillRelevant()&&result.source_version===requestedSource?.version)setRecap({...result,requestedClock:{period:requested.period,elapsed_ms:requested.elapsed}});}catch(e){if(stillRelevant())setError((e as Error).message);}
  }
  if(present&&comparison)return <main className="presentation"><button className="ghost presentation-close" onClick={()=>setPresent(false)}>{es?'Volver al estudio':'Back to studio'}</button><div className="present-card"><div className="brand"><Crosshair/>MatchLens <span> / MATCH INSIGHT</span></div><h1>{insight}</h1><p>{selectedClock} → {formatClock(clock)} · {es?'Datos sintéticos · Explicación por plantilla':'Synthetic match data · Template explanation'}</p><div className="present-values"><span>{comparison.before.box_entries}<small>BEFORE</small></span><ArrowRight/><span>{comparison.after.box_entries}<small>AFTER</small></span></div></div></main>;
  return <div className="app-shell">
    <nav className="sidebar" aria-label="Main navigation"><a className="brand-mark" href="/" aria-label="MatchLens home"><Crosshair size={26}/></a><div className="nav-stack"><button className="nav-icon selected" aria-label="Match workspace"><Activity/></button><a className="nav-icon" href="#lineup" aria-label="Player lineup"><Users/></a><button className="nav-icon" aria-label="Generate recap" onClick={()=>void createRecap()} disabled={!state}><Layers3/></button></div><span className="side-word">MATCH INTELLIGENCE</span><button className="nav-icon help" aria-label="About synthetic data" onClick={()=>alert('All clubs, players, matches and season profiles are fictional. Pitch markers represent recorded events, not tracking positions. Answer mode is labeled per response: template, experimental model interpretation, or fallback. Model outputs need evidence review; configuration alone does not verify connectivity.')}><CircleHelp/></button></nav>
    <div className="main-shell"><header className="topbar"><div className="brand">MatchLens<span className="brand-divider"/> <span className="workspace-label">Live workspace</span></div><div className="top-right"><span className="status-pill"><i/>SYNTHETIC REPLAY</span><span className="avatar">ML</span></div></header>
      <main className="workspace"><div className="page-heading"><div><div className="eyebrow">THE STORY BEHIND THE SCORELINE</div><h1>{es?'Cada momento importa.':'Every moment matters.'}</h1><p>{es?'Ve qué cambió. Entiende quién participó.':'See what changed. Understand who made it happen.'}</p></div><div className="view-controls"><div className="segmented" aria-label="Viewing layout"><button className={view==='watch'?'active':''} onClick={()=>setView('watch')}>Watch</button><button className={view==='explore'?'active':''} onClick={()=>setView('explore')}>Explore</button></div><label><Globe2 size={14}/><select aria-label="Language" value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="es">Español</option></select></label><div className="segmented"><button className={depth==='casual'?'active':''} onClick={()=>setDepth('casual')}>{es?'Aficionado':'Fan'}</button><button className={depth==='analyst'?'active':''} onClick={()=>setDepth('analyst')}>{es?'Analista':'Analyst'}</button></div></div></div>
      {error&&<div role="alert" className="error-banner">{error}<button onClick={()=>{if(!matchId)refreshMatches();else setRetry(r=>r+1);}}>Retry</button></div>}
      {correctionNotice&&<div role="status">{es?'Se corrigieron los eventos. Vuelve a generar respuestas y resúmenes.':'Match events were corrected. Generate answers and recaps again.'}</div>}
      <section className="matchbar panel"><div className="competition"><div className="eyebrow">MATCHDAY 08 · FICTIONAL LEAGUE</div><select aria-label="Synthetic match scenario" value={matchId} onChange={e=>{setMatchId(e.target.value);setPlaying(false);}}>{matches.map(m=><option key={m.id} value={m.id}>{m.label}</option>)}</select></div><div className="scoreboard"><span className="team-name">Northbridge <i className="crest north">N</i></span><div className="score-context"><b className="score">{state?.score.north??'–'}<span>:</span>{state?.score.harbor??'–'}</b><small>{state?.feed_completeness==='incomplete'?(es?'Goles observados en datos incompletos':'Observed goals in incomplete feed'):(es?'Goles registrados':'Recorded goals')}</small></div><span className="team-name"><i className="crest harbor">H</i> Harbor Athletic</span></div><div className="match-clock"><span className="live-dot"/><b>{formatClock(clock)}</b><span>{period===1?'1ST':'2ND'} HALF</span></div></section>
      <div className="content-grid"><div className="analysis-column">{view==='watch'&&<><SyntheticBroadcast players={state?.players??[]} events={state?.events??[]} clock={clock} selectedPlayer={player} alerts={state?.alerts??[]} onPlayer={id=>{setPlayer(id);setView('explore');}}/><section className="panel watch-tracker"><div className="subheading"><h3>Live action tracker</h3><label className="action-filter"><select aria-label="Watch action team filter" value={actionTeam} onChange={e=>setActionTeam(e.target.value)}><option value="all">Both teams</option><option value="north">Northbridge FC</option><option value="harbor">Harbor Athletic</option></select></label></div><Pitch compact events={recentActions(state?.events??[],clock,actionTeam)} players={state?.players??[]} selectedPlayer={player} onPlayer={id=>{setPlayer(id);setView('explore');}}/><p>Last 2 minutes · Up to 12 actions · Full match history retained</p></section></>}<section className="panel analysis-panel" style={{display:view==='watch'?'none':undefined}}><div className="panel-heading"><div><div className="section-label"><Activity size={14}/>{es?'EL PUNTO DE INFLEXIÓN':'THE TURNING POINT'}</div><h2>{es?'Desde este momento':'Since this moment'}</h2></div><label className="team-select"><select aria-label="Team focus" value={team} onChange={e=>{setTeam(e.target.value);setPlayer(e.target.value+'-6');}}><option value="north">Northbridge FC</option><option value="harbor">Harbor Athletic</option></select><ChevronDown size={12}/></label></div>
        <div className="anchor-bar"><span className="anchor-icon"><Clock3 size={17}/></span><div><span className="tiny muted">{es?'MOMENTO SELECCIONADO':'SELECTED MOMENT'}</span><b>{selectedClock} <span>·</span> {anchorLabel}</b></div><span className="window-tag">{comparison?.provisional?(es?'VENTANA PARCIAL':'PARTIAL WINDOW'):'10 MIN / 10 MIN'}</span></div>
        <div className="metric-grid">{[{label:es?'Entradas al área':'Box entries',before:comparison?.before.box_entries,after:comparison?.after.box_entries,icon:Target},{label:es?'Por la derecha':'Right-side entries',before:comparison?.before.routes.right,after:comparison?.after.routes.right,icon:ArrowUpRight},{label:es?'Acciones registradas':'Recorded actions',before:comparison?.before.actions,after:comparison?.after.actions,icon:BarChart3}].map(m=><div className="metric-card" key={m.label}><span><m.icon size={14}/>{m.label}</span><div className="metric-values"><b>{m.before??'—'}</b><ArrowRight size={15}/><strong>{m.after??'—'}</strong></div><small>{es?'ANTES':'BEFORE'} · {comparison?(comparison.before.duration_ms/60000).toFixed(1):'—'} min<span>{es?'DESPUÉS':'AFTER'} · {comparison?(comparison.after.duration_ms/60000).toFixed(1):'—'} min</span></small></div>)}</div>
        <div className="pitch-heading"><div><span className="legend-dot"/>{sequence?(es?'Secuencia seleccionada':'Selected sequence'):(es?'Últimos 2 minutos':'Last 2 minutes')}<span className="muted"> · {sequence?otherPlayerName:(es?'Haz clic en un jugador':'Click a player to explore')}</span></div><label className="action-filter"><select aria-label="Action map team filter" value={actionTeam} onChange={e=>{setActionTeam(e.target.value);setSequence(null);}}><option value="all">{es?'Ambos equipos':'Both teams'}</option><option value="north">Northbridge FC</option><option value="harbor">Harbor Athletic</option></select></label><button className="ghost" onClick={()=>sequence?setSequence(null):setPresent(true)} aria-label={sequence?'Clear selected sequence':'Open presentation preview'}>{sequence?<RefreshCw size={14}/>:<Maximize2 size={14}/>}</button></div>
        <Pitch events={pitchEvents} players={state?.players??[]} selectedPlayer={player} onPlayer={choosePlayer} onEvent={e=>{if(!sequence&&e.player_id)setPlayer(e.player_id);}}/>
        {depth==='analyst'&&comparison&&<div className="analyst-note">Windows: {(comparison.before.duration_ms/60000).toFixed(1)} min before / {(comparison.after.duration_ms/60000).toFixed(1)} min after. Box entry: completed pass or carry from outside into the penalty area. No causal inference.</div>}
        <div className="insight"><div className="insight-icon"><Sparkles size={18}/></div><div><div className="section-label">{es?'QUÉ NOS DICEN LOS DATOS':'WHAT THE EVENTS TELL US'}</div><p>{insight||'Loading match evidence…'}</p><span><ShieldCheck size={12}/>{es?'Cálculo determinista · No demuestra causalidad':'Deterministic calculation · Does not establish causation'}</span></div></div>
        <div className="panel-footer"><span>{sequence?`${pitchEvents.length} ${es?'eventos de evidencia':'evidence events'}`:`${pitchEvents.length}/12 ${es?'acciones recientes':'recent actions'}`} · {updating?(es?'Actualizando…':'Updating…'):(es?'Datos confirmados':'Confirmed events')}</span><button className="text-button" onClick={()=>{if(!state||!comparison)return;const ids=new Set([...comparison.before.evidence_ids,...comparison.after.evidence_ids]);setSequence(state.events.filter(e=>ids.has(e.event_id)));}}>{es?'Explorar evidencia':'Explore evidence'}<ArrowRight size={13}/></button></div>
      </section>
      {state?.has_position_frames&&<SetPiecePanel matchId={matchId} sourceVersion={sourceVersion} clock={clock} language={language} selectedPlayer={player} onPlayer={choosePlayer}/>}
      <section className="panel timeline-panel"><div className="timeline-title"><div className="section-label"><Clock3 size={14}/>{es?'TU RELOJ DEL PARTIDO':'YOUR MATCH CLOCK'}</div><span className="tiny muted">{es?'Sin spoilers · Alineación manual':'Spoiler-safe · Manual alignment'}</span></div><div className="replay-controls"><button className="play-button" aria-label={playing?'Pause replay':'Play replay'} onClick={()=>setPlaying(!playing)}>{playing?<Pause size={17}/>:<Play size={17}/>}</button><select aria-label="Match period" value={period} onChange={e=>{setPeriod(Number(e.target.value));setElapsed(0);setAnchor(0);setPlaying(false);}}><option value="1">1st half</option><option value="2">2nd half</option></select><input aria-label="Match clock" type="range" min="0" max="2700000" step="10000" value={elapsed} onChange={e=>{setPlaying(false);setElapsed(Number(e.target.value));}}/><b>{formatClock(clock)}</b><span className="tiny muted">10×</span></div>{!playing&&<p className="tiny muted" role="status">{correctionCheckFailed?(es?'No se pudieron comprobar correcciones; actualiza los eventos.':'Correction check unavailable; refresh events.'):(es?'En pausa: correcciones comprobadas cada 15 s mientras esta pestaña está visible.':'Paused: checking for corrections every 15s while this tab is visible.')}</p>}<div className="timeline-markers">{state?.moments.filter(e=>e.period===period).map(e=><button key={e.event_id} className={anchor===e.elapsed_ms?'active':''} onClick={()=>setAnchor(e.elapsed_ms)}>{formatClock(e)} {e.event_type==='substitution'?'↔':'⚽'}</button>)}<button aria-label="Refresh match events" onClick={()=>{setCorrectionCheckFailed(false);setRetry(n=>n+1);}}><RefreshCw size={12}/>{es?'Actualizar eventos':'Refresh events'}</button><button onClick={()=>setAnchor(elapsed)}>{es?'Anclar aquí':'Set anchor here'} +</button></div></section>
      <section className="panel lineup-panel" id="lineup"><div className="subheading"><h3><Users size={15}/>{es?'Explora el equipo':'Explore the squad'}</h3><span>{es?'Selecciona cualquier jugador':'Select any player'}</span></div><div className="lineup">{state?.players.filter(p=>p.team_id===team).map(p=><button key={p.id} onClick={()=>setPlayer(p.id)} className={player===p.id?'active':''}><i>{p.number}</i><span>{p.name.split(' ').slice(0,2).join(' ')}<small>{p.position}{!p.starter?' · SUB':''}</small></span></button>)}</div></section>
      </div><PlayerPanel key={`${player}-${matchId}-${narrativeRevision}`} detail={detail} sourceVersion={sourceVersion} clock={clock} matchId={matchId} language={language} depth={depth} anchor={anchor} evidenceEvents={state?.events??[]} evidencePlayers={state?.players??[]} onMoment={chooseMoment} onInteract={()=>{}}/></div>
      {view==='explore'&&<div className="video-pip"><button onClick={()=>setView('watch')}>← Back to Watch</button><SyntheticBroadcast compact players={state?.players??[]} events={state?.events??[]} clock={clock} selectedPlayer={player} onPlayer={setPlayer}/></div>}<section className="recap-strip panel"><div className="recap-icon"><Layers3 size={23}/></div><div><h3>{es?'Tu partido. Tu historia.':'Your match. Your story.'}</h3><p>{es?'Un resumen centrado en tu jugador y tu reloj del partido.':'A catch-up focused on your player, at your match clock.'}</p></div><button className="primary" disabled={!state} onClick={()=>void createRecap()}>{es?'Generar resumen':'Build my recap'}<ArrowRight size={15}/></button></section>
      {recap&&<section className="panel recap-result" aria-live="polite"><div className="section-label"><Layers3 size={15}/>{es?'RESUMEN PERSONALIZADO':'PERSONALIZED RECAP'}</div><p>{recap.text}</p><span className="tiny muted">{es?'Plantilla determinista · Solo datos sintéticos':'Deterministic template · Synthetic data only'}</span></section>}
      <footer className="workspace-footer"><span><Radio size={12}/>Prototype · Synthetic events & season profiles</span><span><a href="/evidence/index.html">{es?'Evidencia de IA grabada':'Recorded AI evidence'}</a> · <a href="/review/">{es?'Decisiones y evaluación':'Football decisions & review'}</a> · Answer mode labeled per response <span className="footer-divider">/</span> MatchLens © 2026</span></footer>
      </main>
    </div>
  </div>;
}

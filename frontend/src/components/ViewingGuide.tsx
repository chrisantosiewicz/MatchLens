import {useEffect,useRef,useState} from 'react';
import {api} from '../api';
import {formatClock} from '../contracts';
import type {Clock,GuideBranch,GuideCard,GuideResponse,Moment} from '../contracts';

type AnswerContext={question:string;clock:Clock;conclusionId?:string|null};
export default function ViewingGuide({matchId,playerId,sourceVersion,clock,language,depth,anchor,answerContext,onAsk,onMoment}:{
  matchId:string;playerId:string;sourceVersion?:string;clock:Clock;language:string;depth:string;anchor:number;answerContext?:AnswerContext|null;onAsk:(question:string,at:Clock)=>void;onMoment:(moment:Moment)=>void;
}){
  const es=language==='es';
  const [branch,setBranch]=useState<GuideBranch>('neutral');
  const [guide,setGuide]=useState<GuideResponse|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [opened,setOpened]=useState<string|null>(null);
  const [seen,setSeen]=useState<string[]>([]);
  const active=useRef(0);
  const key=JSON.stringify([matchId,playerId,sourceVersion,language,depth,anchor,answerContext]);
  const latest=useRef({key,clock});latest.current={key,clock};
  const previousClock=useRef(clock);
  function clear(){active.current++;setGuide(null);setBusy(false);setError('');setOpened(null);setSeen([]);}
  useEffect(()=>{clear();},[key]);
  useEffect(()=>{const previous=previousClock.current;if(clock.period!==previous.period||clock.elapsed_ms<previous.elapsed_ms)clear();previousClock.current=clock;},[clock.period,clock.elapsed_ms]);
  useEffect(()=>()=>{active.current++;},[]);
  async function load(selected=branch,fresh=false){
    const ticket=++active.current;const requestedKey=key;
    const at=fresh?clock:guide?.viewer_clock??answerContext?.clock??clock;
    const anchored=!fresh&&answerContext?.clock.period===at.period&&answerContext?.clock.elapsed_ms===at.elapsed_ms;
    setBranch(selected);setBusy(true);setError('');setOpened(null);setGuide(null);
    try{
      const result=await api<GuideResponse>(`/matches/${matchId}/guidance`,{...at,player_id:playerId,question:answerContext?.question??(es?'Ayúdame a elegir una pregunta':'Help me choose a question'),language,depth,anchor_ms:Math.min(anchor,at.elapsed_ms),branch:selected,seen_ids:fresh?[]:seen,answer_conclusion_id:anchored?answerContext?.conclusionId??null:null,expected_source_version:sourceVersion});
      if(ticket!==active.current||requestedKey!==latest.current.key)return;
      if((sourceVersion&&result.source_version!==sourceVersion)||result.branch!==selected||result.viewer_clock.period!==at.period||result.viewer_clock.elapsed_ms!==at.elapsed_ms){setError(es?'La evidencia cambió. Actualiza el partido.':'Evidence changed. Refresh the match.');return;}
      setGuide({...result,cards:result.cards.slice(0,3)});if(fresh)setSeen([]);
    }catch{if(ticket===active.current)setError(es?'No se pudo cargar la guía. Tu respuesta sigue disponible.':'Guidance could not load. Your answer is still available.');}
    finally{if(ticket===active.current)setBusy(false);}
  }
  function explore(card:GuideCard){
    setSeen(old=>[...new Set([...old,card.id])].slice(-12));
    if(card.kind==='ask'&&card.question){onAsk(card.question,card.viewer_clock);return;}
    setOpened(old=>old===card.id?null:card.id);
  }
  function showSequence(card:GuideCard){const first=card.sequence?.[0];if(!first||!card.sequence)return;onMoment({id:card.story_id??card.id,period:first.period,elapsed_ms:first.elapsed_ms,rank:1,title:card.title,explanation:card.body,evidence_ids:card.evidence_ids,sequence:card.sequence});}
  const oldClock=guide&&(guide.viewer_clock.period!==clock.period||guide.viewer_clock.elapsed_ms!==clock.elapsed_ms);
  return <section className="viewing-guide" aria-label={es?'Guía del espectador':'Viewing guide'}>
    <div className="subheading"><h3>{es?'Tu guía del partido':'Your viewing guide'}</h3></div>
    <p className="tiny muted">{es?'Elige qué quieres entender. Las ramas no son fases detectadas.':'Choose what you want to understand. Branches are not detected match phases.'}</p>
    <div className="guide-branches">{(['attacking','defending','neutral'] as GuideBranch[]).map(b=><button type="button" key={b} aria-pressed={branch===b} onClick={()=>void load(b)}>{es?({attacking:'Ataque',defending:'Defensa',neutral:'Neutral'}[b]):({attacking:'Attacking',defending:'Defending',neutral:'Neutral'}[b])}</button>)}</div>
    <button className="guide-request" type="button" disabled={busy} onClick={()=>void load()}>{busy?(es?'Buscando próximos pasos…':'Choosing next steps…'):(es?'Sugerir próximos pasos':'Suggest next steps')}</button>
    {error&&<p role="alert" className="error-text">{error}</p>}
    {guide&&<div aria-live="polite"><p className="tiny muted">{es?'Guía a las':'Guide at'} {formatClock(guide.viewer_clock)} · {guide.generation_mode==='model'?(es?'Próximos pasos elegidos por IA':'AI-selected next steps'):guide.generation_mode==='fallback'?(es?'Próximos pasos locales · IA no disponible':'Local next steps · AI unavailable'):(es?'Próximos pasos locales · sin llamada al modelo':'Local next steps · no model call')}</p>
      {guide.clarification&&<p className="tiny">{es?'No hay una única definición de jugar bien. Elige una pregunta concreta.':'Playing well can mean different things. Choose a specific question.'}</p>}
      {guide.cards.map(card=><article key={card.id} className="guide-card"><button type="button" aria-expanded={card.kind==='ask'?undefined:opened===card.id} onClick={()=>explore(card)}>{card.title}<span aria-hidden="true">{card.kind==='ask'?' →':opened===card.id?' −':' +'}</span></button>
        {opened===card.id&&<div><p>{card.body}</p>
          {card.sequence&&<><ol>{card.sequence.map(e=><li key={e.event_id}>{formatClock(e)} · {e.actor_name??e.player_id} · {e.event_type} / {e.outcome}</li>)}</ol><button type="button" className="text-button" onClick={()=>showSequence(card)}>{es?'Mostrar en el campo':'Show on the pitch'}</button></>}
          {card.calculations&&<div className="guide-table"><table><thead><tr><th>{es?'Métrica y ventana':'Metric / window'}</th><th>{es?'Recuento':'Count'}</th><th>Min</th><th>/ min</th></tr></thead><tbody>{card.calculations.map(c=><tr key={`${c.metric}-${c.window}`}><td>{c.metric==='team_box_entries'?(es?'Equipo':'Team'):(es?'Jugador':'Player')} · {c.window==='before'?(es?'antes':'before'):(es?'después':'after')}<small>{formatClock({period:c.period,elapsed_ms:c.start_ms})} → {formatClock({period:c.period,elapsed_ms:c.end_ms})}</small></td><td>{c.count}</td><td>{c.minutes}</td><td>{c.rate??'—'}</td></tr>)}</tbody></table></div>}
          {!!card.evidence_ids.length&&<details><summary>{es?'Eventos de apoyo':'Supporting events'} ({card.evidence_ids.length})</summary><p className="tiny muted">{card.evidence_ids.map(id=>`${id} · r${card.event_revisions[id]}`).join(', ')}</p></details>}
          {card.definition_id&&<small className="muted">{es?'Concepto de conocimiento, no conclusión del partido':'Knowledge concept, not a match conclusion'} · {card.definition_id}</small>}
          {card.references?.map(ref=><p key={ref.url} className="tiny"><a href={ref.url} target="_blank" rel="noreferrer">{ref.title}</a></p>)}
        </div>}
      </article>)}
      {!guide.cards.length&&<p className="tiny muted">{es?'No quedan sugerencias válidas para este contexto. Actualiza la pregunta o el tiempo.':'No further eligible suggestions for this context. Update the question or clock.'}</p>}
      {oldClock&&<p className="tiny muted">{es?'Las sugerencias permanecen en el tiempo indicado mientras continúa el partido.':'Suggestions remain at their displayed clock while the match continues.'} <button type="button" onClick={()=>void load(branch,true)}>{es?'Actualizar a':'Update to'} {formatClock(clock)}</button></p>}
    </div>}
  </section>;
}

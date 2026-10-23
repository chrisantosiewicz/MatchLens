import type {Answer} from '../contracts';
import {formatClock} from '../contracts';

export default function ClaimEvidence({answer,es}:{answer:Answer;es:boolean}) {
  const trail=answer.evidence_trail;
  if(!trail)return null;
  return <details className="answer-evidence"><summary>{es?'Evidencia de cada afirmación':'Sentence-by-sentence evidence'}</summary>
    <p className="tiny muted">{es?'Hechos calculados y reglas editoriales; la coincidencia entre modelos no demuestra veracidad.':'Calculated facts and editorial rules; model agreement does not prove truth.'}</p>
    {answer.workflow&&<><p>{answer.workflow.model_calls} {es?'llamadas al modelo':'model calls'} · {answer.workflow.rejection_reason??'—'}</p><ol>{answer.workflow.stages.map(stage=><li key={stage.role}>{stage.role}: {stage.status}{stage.latency_ms!==undefined?` · ${stage.latency_ms} ms`:''}</li>)}</ol></>}
    {answer.claims?.map(claim=><details key={claim.id}><summary>{claim.kind} · {claim.checker_verdict}</summary><p>{claim.text}</p><p>{claim.subject_id} · {formatClock({period:claim.scope.period,elapsed_ms:claim.scope.start_ms})} → {formatClock({period:claim.scope.period,elapsed_ms:claim.scope.end_ms})}</p><p className="tiny muted">{claim.rule_id}</p>{trail.facts.filter(f=>claim.fact_ids.includes(f.id)).map(fact=><div key={fact.id}><strong>{fact.predicate}</strong><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(fact.value,null,2)}</pre><small>{fact.evidence_ids.map(id=>`${id} · revision ${fact.event_revisions[id]}`).join(', ')}</small></div>)}</details>)}
    {!!answer.workflow?.counter_evidence?.length&&<details><summary>{es?'Evidencia que matiza la conclusión':'Qualifying counter-evidence'}</summary>{answer.workflow.counter_evidence.map(item=><div key={item.candidate.id}>{item.claims.map(claim=><p key={claim.id}>{claim.text} <small>{claim.evidence_ids.join(', ')}</small></p>)}</div>)}</details>}
    {!!trail.aggregate_calculations?.length&&<details><summary>{es?'Cálculos del contexto':'Context calculations'}</summary>{trail.aggregate_calculations.map(calc=><details key={`${calc.metric}-${calc.window}`}><summary>{calc.metric} · {calc.window}: {calc.count} / {calc.minutes} min = {calc.rate??'—'} / min</summary><p>{formatClock({period:calc.period,elapsed_ms:calc.start_ms})} → {formatClock({period:calc.period,elapsed_ms:calc.end_ms})}</p><small>{calc.source_ids.length?calc.source_ids.join(', '):'No qualifying recorded events.'}</small></details>)}</details>}
    {!!answer.aggregate_evidence_ids?.length&&<details><summary>{es?'Fuentes de estadísticas adicionales':'Additional aggregate-stat sources'} ({answer.aggregate_evidence_ids.length})</summary><p className="tiny muted">{es?'No son la secuencia principal.':'Separate from the primary sequence; these sources support aggregate context.'}</p><small>{answer.aggregate_evidence_ids.join(', ')}</small></details>}
    <p className="tiny muted">Snapshot: {trail.snapshot_id}<br/>Source: {trail.source_revision}</p>
  </details>;
}

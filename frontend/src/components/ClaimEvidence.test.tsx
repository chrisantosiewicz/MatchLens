import {cleanup,render,screen} from '@testing-library/react';
import {afterEach,expect,it} from 'vitest';
import ClaimEvidence from './ClaimEvidence';
import type {Answer} from '../contracts';

afterEach(cleanup);
it('separates aggregate sources and never labels a local trace as agent checked',()=>{
  const answer:Answer={text:'Recorded involvement.',generation_mode:'template',evidence_ids:['sequence','aggregate'],primary_evidence_ids:['sequence'],aggregate_evidence_ids:['aggregate'],claims:[],evidence_trail:{snapshot_id:'snapshot',source_revision:'revision',facts:[]},workflow:{model_calls:0,assurance:'Canonical facts',rejection_reason:null,stages:[{role:'checker',status:'not_run'}]}};
  render(<ClaimEvidence answer={answer} es={false}/>);
  expect(screen.getByText('0 model calls · —')).toBeTruthy();
  expect(screen.getByText('checker: not_run')).toBeTruthy();
  expect(screen.getByText('Additional aggregate-stat sources (1)')).toBeTruthy();
  expect(screen.queryByText('supported')).toBeNull();
});

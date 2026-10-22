import {render,screen,fireEvent,cleanup,act} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import PlayerPanel from './PlayerPanel';
import type {PlayerDetail} from '../contracts';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('distinguishes fallback output and exposes supporting recorded actions',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({text:'Trusted fallback.',evidence_ids:['support-1'],generation_mode:'fallback'})}));
  render(<PlayerPanel detail={detail} clock={{period:1,elapsed_ms:3000}} matchId="demo" language="en" depth="casual" anchor={0} onMoment={()=>{}}
    evidenceEvents={[{event_id:'support-1',period:1,elapsed_ms:1000,player_id:'north-6',recipient_id:null,team_id:'north',event_type:'pass',outcome:'complete',start:null,end:null,possession_id:'p1',attack_right:true}]}/>);
  fireEvent.click(screen.getByRole('button',{name:'How involved has he been?'}));
  expect(await screen.findByText(/Fallback explanation/)).toBeTruthy();
  expect(screen.getByText(/Inspect supporting events/)).toBeTruthy();
  expect(screen.getByText(/0:01.*Mateo Silva.*pass.*complete/)).toBeTruthy();
});
const detail: PlayerDetail = {player:{id:'north-6',name:'Mateo Silva',number:6,team_id:'north',position:'CM',starter:true},stats:{actions:5,completed_passes:1,pass_attempts:2,pass_completion:50,progressive_passes:0,shots:1,goals:0,recoveries:0,box_entries:0,evidence_ids:[]},minutes_played:20,profile:{cohort_size:40,metrics:[],minutes:1200,position:'CM',cohort_label:'Synthetic'},moments:[{id:'shot',rank:2,period:1,elapsed_ms:1000,title:'Attempted a shot',evidence_ids:['shot'],sequence:[],explanation:'Recorded shot'},{id:'loss',rank:4,period:1,elapsed_ms:2000,title:'Turnover followed by an opposition shot',evidence_ids:['loss','opp-shot'],sequence:[],explanation:'Temporal sequence'}]};
it('preserves shot and turnover meanings in Spanish moments',()=>{
  render(<PlayerPanel detail={detail} clock={{period:1,elapsed_ms:3000}} matchId="demo" language="es" depth="casual" anchor={0} onMoment={()=>{}}/>);
  fireEvent.click(screen.getByRole('tab',{name:'Momentos clave 2'}));
  expect(screen.getByText('Intentó un tiro')).toBeTruthy();
  expect(screen.getByText('Pérdida seguida de un tiro rival')).toBeTruthy();
  expect(screen.queryByText('Recuperación registrada')).toBeNull();
});
it('labels model-selected answers accurately',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({text:'One completed pass.',evidence_ids:['e1'],generation_mode:'model'})}));
  render(<PlayerPanel detail={detail} clock={{period:1,elapsed_ms:3000}} matchId="demo" language="en" depth="casual" anchor={0} onMoment={()=>{}}/>);
  fireEvent.click(screen.getByRole('button',{name:'How involved has he been?'}));
  expect(await screen.findByText(/Experimental model interpretation/)).toBeTruthy();
  expect(screen.queryByText(/Foundry not connected yet/)).toBeNull();
});

it('keeps a timestamped answer during forward playback and clears it on rewind',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({text:'One completed pass.',evidence_ids:['e1'],generation_mode:'template'})}));
  const props={detail,matchId:'demo',language:'en',depth:'casual',anchor:0,onMoment:()=>{}};
  const view=render(<PlayerPanel {...props} clock={{period:1,elapsed_ms:3000}}/>);
  fireEvent.click(screen.getByRole('button',{name:'How involved has he been?'}));
  await screen.findByText('One completed pass.');
  view.rerender(<PlayerPanel {...props} clock={{period:1,elapsed_ms:4000}}/>);
  expect(screen.getByText('One completed pass.')).toBeTruthy();
  expect(screen.getByText(/Answer at 0:03/)).toBeTruthy();
  view.rerender(<PlayerPanel {...props} clock={{period:1,elapsed_ms:1000}}/>);
  expect(screen.queryByText('One completed pass.')).toBeNull();
});

it('clears cached answers and rejects pending answers after an event correction',async()=>{
  let resolveAnswer!: (response:Response)=>void;
  const fetcher=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({source_version:'v1',text:'Cached old evidence',evidence_ids:['e1'],generation_mode:'template'})})
    .mockImplementationOnce(()=>new Promise<Response>(resolve=>{resolveAnswer=resolve;}));
  vi.stubGlobal('fetch',fetcher);
  const props={detail,matchId:'demo',language:'en',depth:'casual',anchor:0,onMoment:()=>{},clock:{period:1,elapsed_ms:3000}};
  const view=render(<PlayerPanel {...props} sourceVersion="v1"/>);
  fireEvent.click(screen.getByRole('button',{name:'How involved has he been?'}));
  await screen.findByText('Cached old evidence');
  view.rerender(<PlayerPanel {...props} sourceVersion="v2"/>);
  expect(screen.queryByText('Cached old evidence')).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'How involved has he been?'}));
  view.rerender(<PlayerPanel {...props} sourceVersion="v3"/>);
  await act(async()=>{resolveAnswer({ok:true,json:async()=>({source_version:'v2',text:'Delayed old evidence',evidence_ids:[],generation_mode:'template'})} as Response);});
  expect(screen.queryByText('Delayed old evidence')).toBeNull();
});

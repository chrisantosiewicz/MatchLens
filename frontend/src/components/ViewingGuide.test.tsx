import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import ViewingGuide from './ViewingGuide';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const props={matchId:'demo',playerId:'north-6',sourceVersion:'v1',clock:{period:2,elapsed_ms:1500000},language:'en',depth:'casual',anchor:900000,onAsk:vi.fn(),onMoment:vi.fn()};
const packet={source_version:'v1',snapshot_id:'s',viewer_clock:props.clock,branch:'attacking',generation_mode:'template',model_calls:0,notice:'Local next steps · no model call',clarification:false,cards:[{id:'concept_progression',kind:'concept',branch:'attacking',title:'Understand progression',body:'A completed pass can qualify under our definition.',evidence_ids:[],event_revisions:{},source_version:'v1',viewer_clock:props.clock,subject_id:'north-6'},{id:'ask_passing',kind:'ask',branch:'attacking',title:'Explore passing',body:'Look at recorded contributions.',question:'Why does his passing matter?',evidence_ids:[],event_revisions:{},source_version:'v1',viewer_clock:props.clock,subject_id:'north-6'}]};

it('loads only on request, offers three branches and opens knowledge locally',async()=>{
  const fetcher=vi.fn().mockResolvedValue({ok:true,json:async()=>packet});vi.stubGlobal('fetch',fetcher);
  render(<ViewingGuide {...props}/>);
  expect(fetcher).not.toHaveBeenCalled();
  expect(screen.getByRole('button',{name:'Defending'})).toBeTruthy();
  expect(screen.getByRole('button',{name:'Neutral'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Attacking'}));
  fireEvent.click(await screen.findByRole('button',{name:'Understand progression'}));
  expect(screen.getByText('A completed pass can qualify under our definition.')).toBeTruthy();
  expect(fetcher).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button',{name:'Explore passing'}));
  expect(props.onAsk).toHaveBeenCalledWith('Why does his passing matter?',props.clock);
});

it('withholds pending guidance after a source correction',async()=>{
  let resolve!: (r:unknown)=>void;
  vi.stubGlobal('fetch',vi.fn(()=>new Promise(r=>{resolve=r;})));
  const view=render(<ViewingGuide {...props}/>);
  fireEvent.click(screen.getByRole('button',{name:'Attacking'}));
  view.rerender(<ViewingGuide {...props} sourceVersion="v2"/>);
  await act(async()=>resolve({ok:true,json:async()=>packet}));
  expect(screen.queryByRole('button',{name:'Understand progression'})).toBeNull();
});

it('keeps an explicit snapshot during forward playback and clears on rewind',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>packet}));
  const view=render(<ViewingGuide {...props}/>);
  fireEvent.click(screen.getByRole('button',{name:'Attacking'}));
  await screen.findByRole('button',{name:'Understand progression'});
  view.rerender(<ViewingGuide {...props} clock={{period:2,elapsed_ms:1510000}}/>);
  expect(screen.getByText(/Guide at 70:00/)).toBeTruthy();
  expect(screen.getByRole('button',{name:/Update to 70:10/})).toBeTruthy();
  view.rerender(<ViewingGuide {...props} clock={{period:2,elapsed_ms:1400000}}/>);
  expect(screen.queryByRole('button',{name:'Understand progression'})).toBeNull();
});

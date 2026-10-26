import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import SetPiecePanel from './SetPiecePanel';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const props={matchId:'corners',sourceVersion:'v1',clock:{period:2,elapsed_ms:1500000},language:'en',selectedPlayer:'north-6',onPlayer:vi.fn()};
const frame={phase:'delivery',period:2,elapsed_ms:1204000,available:true,frame_id:'frame-1',frame_revision:1,anchor_event_id:'delivery',anchor_event_revision:1,counts:{attackers:5,defenders:8,defending_goalkeepers:1},positions:[{player_id:'north-6',point:{x:92,y:30}},{player_id:'harbor-1',point:{x:103,y:34}}],ball:{x:105,y:0}};
const packet={source_version:'v1',viewer_clock:props.clock,available:true,synthetic:true,generation_mode:'template',data_mode:'simulated_position_snapshots',players:[{id:'north-6',name:'Mateo Silva',number:6,team_id:'north',position:'CM',starter:true},{id:'harbor-1',name:'Keeper',number:1,team_id:'harbor',position:'GK',starter:true}],corners:[{id:'corner-1',team_id:'north',period:2,elapsed_ms:1201000,attack_right:true,text:'Five attackers occupy the box. Silva makes first contact.',limitation:'Simulated snapshots do not establish intent.',frames:[{...frame,phase:'setup',elapsed_ms:1201000,frame_id:'frame-0',counts:{...frame.counts,attackers:2}},frame],entered_box_ids:['north-6'],first_contact:null,outcome:null,events:[],evidence_ids:['delivery'],event_revisions:{delivery:1},position_frame_ids:['frame-0','frame-1']}]};

it('renders simulated synchronized counts, phases, player selection and sources',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>packet}));
  render(<SetPiecePanel {...props}/>);
  expect(await screen.findByText('5 attackers')).toBeTruthy();
  expect(screen.getByText(/8 defenders/)).toBeTruthy();
  expect(screen.getByText(/65:04/)).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:/Mateo Silva/}));
  expect(props.onPlayer).toHaveBeenCalledWith('north-6');
  fireEvent.click(screen.getByRole('button',{name:'Setup'}));
  expect(screen.getByText('2 attackers')).toBeTruthy();
  expect(screen.getByText(/frame-0/)).toBeTruthy();
});

it('withholds old or delayed positional evidence after rewind and source correction',async()=>{
  let resolve!: (r:unknown)=>void;
  const fetcher=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>packet}).mockImplementation(()=>new Promise(r=>{resolve=r;}));
  vi.stubGlobal('fetch',fetcher);
  const view=render(<SetPiecePanel {...props}/>);
  await screen.findByText('5 attackers');
  view.rerender(<SetPiecePanel {...props} clock={{period:2,elapsed_ms:1000000}}/>);
  expect(screen.queryByText('5 attackers')).toBeNull();
  view.rerender(<SetPiecePanel {...props} sourceVersion="v2"/>);
  await act(async()=>resolve({ok:true,json:async()=>packet}));
  expect(screen.queryByText('5 attackers')).toBeNull();
});

it('shows unavailable occupancy rather than zero or stale positions',async()=>{
  const unavailable={...packet,corners:[{...packet.corners[0],frames:[{...frame,available:false,counts:null,positions:[],ball:null,frame_id:null,unavailable_reason:'missing_or_stale_positional_evidence'}]}]};
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>unavailable}));
  render(<SetPiecePanel {...props}/>);
  expect(await screen.findByText(/Occupancy unavailable/)).toBeTruthy();
  expect(screen.queryByText('0 attackers')).toBeNull();
  expect(screen.queryByRole('button',{name:/Mateo Silva/})).toBeNull();
});

it('withdraws displayed positions when a refresh detects a different source before the parent updates',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce({ok:true,json:async()=>packet}).mockResolvedValueOnce({ok:true,json:async()=>({...packet,source_version:'v2',viewer_clock:{period:2,elapsed_ms:1510000}})}));
  const view=render(<SetPiecePanel {...props}/>);
  await screen.findByText('5 attackers');
  view.rerender(<SetPiecePanel {...props} clock={{period:2,elapsed_ms:1510000}}/>);
  await screen.findByRole('alert');
  expect(screen.queryByText('5 attackers')).toBeNull();
});

it('retains a clearly timestamped older snapshot when a forward refresh is offline',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce({ok:true,json:async()=>packet}).mockRejectedValueOnce(Error('offline')));
  const view=render(<SetPiecePanel {...props}/>);
  await screen.findByText('5 attackers');
  view.rerender(<SetPiecePanel {...props} clock={{period:2,elapsed_ms:1510000}}/>);
  await screen.findByRole('alert');
  expect(screen.getByText('5 attackers')).toBeTruthy();
  expect(screen.getByText(/evidence through.*70:00/)).toBeTruthy();
});

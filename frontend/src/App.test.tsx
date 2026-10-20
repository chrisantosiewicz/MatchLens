import {render, screen, fireEvent, waitFor, cleanup, act} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import App from './App';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('shows a recoverable API error rather than a blank screen', async()=>{
  vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('Offline')));
  render(<App/>);
  await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Offline'));
  expect(screen.getByText('MatchLens')).toBeTruthy();
  await act(async()=>{fireEvent.click(screen.getByRole('button',{name:/retry/i}));});
  await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2));
});

function localFetch(url: string) {
  const player = {id:'north-6',name:'Mateo Silva',team_id:'north',number:6,position:'CM',starter:true};
  const stats = {actions:4,completed_passes:3,pass_attempts:4,progressive_passes:1,shots:0,recoveries:0,goals:0,box_entries:0,evidence_ids:[]};
  const window = {box_entries:0,actions:0,duration_ms:600000,routes:{right:0},evidence_ids:[]};
  const data = url.endsWith('/matches') ? [{id:'demo',label:'Demo',teams:{north:'Northbridge',harbor:'Harbor'}}]
    : url.includes('/players/') ? {player,stats,minutes_played:70,moments:[],profile:{metrics:[],cohort_size:40}}
    : url.includes('/comparison?') ? {before:window,after:window,provisional:true,pattern_supported:false}
    : {id:'demo',players:[player],score:{north:2,harbor:0},events:[],moments:[]};
  return Promise.resolve({ok:true,json:async()=>data} as Response);
}

it('hides old match data immediately when seeking while replacement is pending', async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>url.includes('elapsed_ms=0')?new Promise(()=>{}):localFetch(url)));
  render(<App/>);
  await screen.findByRole('heading',{name:'Mateo Silva'});
  fireEvent.change(screen.getByRole('slider',{name:'Match clock'}),{target:{value:'0'}});
  expect(screen.queryByRole('heading',{name:'Mateo Silva'})).toBeNull();
});

it('discards a recap response from a later clock after rewind', async()=>{
  let resolveRecap!: (value:Response)=>void;
  vi.stubGlobal('fetch',vi.fn((url:string)=>url.includes('/recap?')?new Promise<Response>(r=>{resolveRecap=r;}):localFetch(url)));
  render(<App/>);
  await screen.findByRole('heading',{name:'Mateo Silva'});
  fireEvent.click(screen.getByRole('button',{name:'Build my recap'}));
  fireEvent.change(screen.getByRole('slider',{name:'Match clock'}),{target:{value:'0'}});
  await act(async()=>{resolveRecap({ok:true,json:async()=>({text:'Future winning goal',evidence_ids:[],generation_mode:'template'})} as Response);});
  expect(screen.queryByText('Future winning goal')).toBeNull();
});

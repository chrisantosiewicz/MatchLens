import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import PlayerPanel from './PlayerPanel';
import type {PlayerDetail} from '../contracts';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
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
  expect(await screen.findByText(/Model-selected verified facts/)).toBeTruthy();
  expect(screen.queryByText(/Foundry not connected yet/)).toBeNull();
});

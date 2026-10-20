import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import SyntheticBroadcast from './SyntheticBroadcast';
import type {Player} from '../contracts';
afterEach(cleanup);
it('opens the stable player entity from its numbered synthetic marker',()=>{
  const select=vi.fn();
  render(<SyntheticBroadcast players={[{id:'n12',name:'Nico Vega',team_id:'north',number:12,position:'W',starter:true} as Player]} events={[]} clock={{period:2,elapsed_ms:1000}} selectedPlayer="n12" onPlayer={select}/>);
  fireEvent.click(screen.getByRole('button',{name:'Nico Vega, number 12'}));
  expect(select).toHaveBeenCalledWith('n12');
  expect(screen.getByText(/not video recognition/i)).toBeTruthy();
});

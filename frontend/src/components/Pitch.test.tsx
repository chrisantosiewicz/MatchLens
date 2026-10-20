import {render, screen, fireEvent, cleanup} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import Pitch from './Pitch';
import type {MatchEvent, Player} from '../contracts';
afterEach(cleanup);
it('selects an action player through an accessible marker', () => {
  const select = vi.fn();
  const player = {id:'n-6', name:'Mateo Silva', number:6, team_id:'north'} as Player;
  const event = {event_id:'e1', player_id:'n-6', team_id:'north', event_type:'pass', start:{x:40,y:30}, end:{x:70,y:20}, attack_right:true} as MatchEvent;
  render(<Pitch events={[event]} players={[player]} selectedPlayer="n-6" onPlayer={select}/>);
  fireEvent.click(screen.getByRole('button',{name:/Mateo Silva/}));
  expect(select).toHaveBeenCalledWith('n-6');
});

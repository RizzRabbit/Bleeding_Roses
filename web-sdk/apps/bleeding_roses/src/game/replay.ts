import { stateBet } from 'state-shared';

import type { Bet } from './typesBookEvent';

let cache: Bet | null = null;

export const rememberReplay = () => {
	if (stateBet.betToResume) cache = stateBet.betToResume as Bet;
};

export const armReplay = () => {
	if (!cache && stateBet.betToResume) cache = stateBet.betToResume as Bet;
	if (!cache) return false;
	stateBet.betToResume = { ...cache, active: true, event: '0' };
	if (cache.mode) stateBet.activeBetModeKey = cache.mode;
	return true;
};

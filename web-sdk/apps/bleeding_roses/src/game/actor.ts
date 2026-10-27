import { stateBet } from 'state-shared';
import { checkIsMultipleRevealEvents } from 'utils-book';
import { createPrimaryMachines, createIntermediateMachines, createGameActor } from 'utils-xstate';

import { columnNames, dismissPresentation, stateGame } from './stateGame.svelte';
import { reelEngine } from './reels.svelte';
import { restorePersistent } from './betModes';
import { playBet, convertTorResumableBet } from './utils';
import type { Bet } from './typesBookEvent';

const primaryMachines = createPrimaryMachines<Bet>({
	onResumeGameActive: (betToResume) => convertTorResumableBet(betToResume),
	onResumeGameInactive: () => undefined,
	onNewGameStart: async () => {
		stateBet.winBookEventAmount = 0;
		if (stateGame.presentation) dismissPresentation();
		stateGame.glow = null;
		reelEngine.start(columnNames());
	},
	onNewGameError: () => {
		reelEngine.abort();
		restorePersistent();
	},
	onPlayGame: async (bet) => {
		try {
			await playBet(bet);
		} finally {
			restorePersistent();
		}
	},
	checkIsBonusGame: (bet) => checkIsMultipleRevealEvents({ bookEvents: bet.state }),
});

const intermediateMachines = createIntermediateMachines(primaryMachines);

export const gameActor = createGameActor(intermediateMachines);

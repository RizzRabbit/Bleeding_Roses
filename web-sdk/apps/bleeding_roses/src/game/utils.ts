import { stateBet } from 'state-shared';
import { createPlayBookUtils } from 'utils-book';

import { beginRound, bookEventHandlerMap } from './bookEventHandlerMap';
import type { Bet, BookEventOfType } from './typesBookEvent';

export const { playBookEvents } = createPlayBookUtils({ bookEventHandlerMap });

export const playBet = async (bet: Bet) => {
	beginRound();
	stateBet.winBookEventAmount = 0;
	await playBookEvents(bet.state);
};

const RESUME_TYPES = ['bonusTier', 'freeSpinTrigger', 'updateFreeSpin', 'setTotalWin', 'updateGlobalMult', 'stickyReel', 'wincap'];

export const convertTorResumableBet = (betToResume: Bet) => {
	const resumingIndex = Number(betToResume.event);
	const bookEventsBeforeResume = betToResume.state.filter((_, eventIndex) => eventIndex < resumingIndex);
	const bookEventsAfterResume = betToResume.state.filter((_, eventIndex) => eventIndex >= resumingIndex);
	const bookEventToCreateSnapshot: BookEventOfType<'createBonusSnapshot'> = {
		index: 0,
		type: 'createBonusSnapshot',
		bookEvents: bookEventsBeforeResume.filter((bookEvent) => RESUME_TYPES.includes(bookEvent.type)),
	};
	return { ...betToResume, state: [bookEventToCreateSnapshot, ...bookEventsAfterResume] };
};

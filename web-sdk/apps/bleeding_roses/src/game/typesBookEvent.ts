import type { BetType } from 'rgs-requests';

import type { GameType, Position, RawSymbol, Transformation } from './types';

type BookEventReveal = {
	index: number;
	type: 'reveal';
	board: RawSymbol[][];
	paddingPositions: number[];
	anticipation: number[];
	gameType: GameType;
};

type BookEventWinInfo = {
	index: number;
	type: 'winInfo';
	totalWin: number;
	wins: {
		symbol: string;
		kind: number;
		win: number;
		positions: Position[];
		meta?: {
			ways?: number;
			globalMult?: number;
			winWithoutMult?: number;
			reelMult?: number;
			reelMultipliers?: { reel: number; multiplier: number }[];
		};
	}[];
};

type BookEventSetWin = {
	index: number;
	type: 'setWin';
	amount: number;
	winLevel: number;
};

type BookEventSetTotalWin = {
	index: number;
	type: 'setTotalWin';
	amount: number;
};

type BookEventFinalWin = {
	index: number;
	type: 'finalWin';
	amount: number;
};

type BookEventFreeSpinTrigger = {
	index: number;
	type: 'freeSpinTrigger';
	totalFs: number;
	positions: Position[];
};

type BookEventFreeSpinRetrigger = {
	index: number;
	type: 'freeSpinRetrigger';
	totalFs: number;
	positions: Position[];
};

type BookEventUpdateFreeSpin = {
	index: number;
	type: 'updateFreeSpin';
	amount: number;
	total: number;
};

type BookEventFreeSpinEnd = {
	index: number;
	type: 'freeSpinEnd';
	amount: number;
	winLevel: number;
};

type BookEventEnterBonus = {
	index: number;
	type: 'enterBonus';
	reason: string;
};

type BookEventBonusTier = {
	index: number;
	type: 'bonusTier';
	tier: string;
	tierName: string;
	scatterCount: number;
	spins: number;
	boardBleed: boolean;
	sticky: boolean;
	globalMultiplier: boolean;
};

type BookEventRetrigger = {
	index: number;
	type: 'retrigger';
	tier: string;
	addedSpins: number;
	totalFs: number;
	scatterCount: number;
};

type BookEventFullBleed = {
	index: number;
	type: 'fullBleed';
	transformations: Transformation[];
};

type BookEventReelBleed = {
	index: number;
	type: 'reelBleed';
	reel: number;
	scope: string;
	multiplierApplied: boolean;
	multiplier: number;
	triggers: Position[];
	transformations: Transformation[];
};

type BookEventStickyBleed = {
	index: number;
	type: 'stickyBleed';
	stickyReels: number[];
	transformations: Transformation[];
};

type BookEventStickyReel = {
	index: number;
	type: 'stickyReel';
	newReels: number[];
	multipliers: number[];
	stickyReels: number[];
	stickyMultipliers: number[];
};

type BookEventUpdateGlobalMult = {
	index: number;
	type: 'updateGlobalMult';
	globalMult: number;
	increment: number;
	reel: number;
	heartReels: number[];
	reason: string;
};

type BookEventBoardAfterBleed = {
	index: number;
	type: 'boardAfterBleed';
	board: RawSymbol[][];
	reelMultipliers: number[];
	globalMult: number;
	tier: string | null;
	stickyReels: number[];
};

type BookEventWincap = {
	index: number;
	type: 'wincap';
	amount: number;
};

type BookEventCreateBonusSnapshot = {
	index: number;
	type: 'createBonusSnapshot';
	bookEvents: BookEvent[];
};

export type BookEvent =
	| BookEventReveal
	| BookEventWinInfo
	| BookEventSetWin
	| BookEventSetTotalWin
	| BookEventFinalWin
	| BookEventFreeSpinTrigger
	| BookEventFreeSpinRetrigger
	| BookEventUpdateFreeSpin
	| BookEventFreeSpinEnd
	| BookEventEnterBonus
	| BookEventBonusTier
	| BookEventRetrigger
	| BookEventFullBleed
	| BookEventReelBleed
	| BookEventStickyBleed
	| BookEventStickyReel
	| BookEventUpdateGlobalMult
	| BookEventBoardAfterBleed
	| BookEventWincap
	| BookEventCreateBonusSnapshot;

export type Bet = BetType<BookEvent>;
export type BookEventOfType<T> = Extract<BookEvent, { type: T }>;
export type BookEventContext = { bookEvents: BookEvent[] };

import { recordBookEvent, type BookEventHandlerMap } from 'utils-book';
import { stateBet } from 'state-shared';

import { applyVisible, animateCell, clearFeature, present, stateGame } from './stateGame.svelte';
import { reelEngine } from './reels.svelte';
import { hold, skipHolds, TEMPO } from './tempo';
import { tone } from './sound';
import { t } from './social';
import type { BookEvent, BookEventContext, BookEventOfType } from './typesBookEvent';
import type { Position } from './types';
import { winLevelMap, type WinLevel } from './winLevelMap';

const pending: Promise<void>[] = [];

/** Book units for 15000x. A round stops presenting once this cap is on screen. */
const CAP_AMOUNT = 1_500_000;
let maxWinShown = false;

export const beginRound = () => {
	maxWinShown = false;
};

const clampToCap = (amount: number) => (amount > CAP_AMOUNT ? CAP_AMOUNT : amount);

const queueMelt = (reel: number, row: number, to: string) => {
	const job = animateCell(reel, row, 'melt', to);
	pending.push(job);
	return job;
};

const flushMelts = async () => {
	const jobs = pending.splice(0, pending.length);
	await Promise.all(jobs);
};

const showWin = async (amount: number, winLevel: number, title: string, kind: 'win' | 'total') => {
	const level = winLevelMap[(winLevel as WinLevel) || 1] ?? winLevelMap[2];
	if (!amount && kind === 'win') return;
	if (level.type === 'max' || winLevel >= 10 || amount >= 1_500_000) {
		const { preloadWinSheets, releaseWinSheets } = await import('./winSheets');
		await preloadWinSheets();
		await present({
			kind,
			title: t('MAX WIN'),
			subtitle: t('15000x'),
			amount,
			winLevel: 10,
			duration: stateBet.isTurbo ? 900 : TEMPO.win.max,
		});
		await releaseWinSheets();
		return;
	}
	const duration =
		level.type === 'big'
			? TEMPO.win.big + (winLevel - 6) * 400
			: level.presentDuration || TEMPO.win.small;
	await present({
		kind,
		title: t(title || level.text || 'WIN'),
		subtitle: '',
		amount,
		winLevel,
		duration: stateBet.isTurbo ? Math.min(700, duration) : duration,
	});
};

const glowWins = async (positions: Position[]) => {
	const unique = positions.filter(
		(position, index) =>
			positions.findIndex((other) => other.reel === position.reel && other.row === position.row) === index,
	);
	if (!unique.length) return;
	const jobs = unique.map((position) => {
		const row = position.row - 1;
		if (row < 0 || row > 3) return Promise.resolve();
		return animateCell(position.reel, row, 'win');
	});
	let cursor = 0;
	const timer = setInterval(() => {
		const position = unique[cursor % unique.length];
		stateGame.glow = { reel: position.reel, row: position.row - 1 };
		cursor += 1;
	}, stateBet.isTurbo ? 120 : 420);
	stateGame.glow = { reel: unique[0].reel, row: unique[0].row - 1 };
	await Promise.all(jobs);
	clearInterval(timer);
	stateGame.glow = null;
};

export const bookEventHandlerMap: BookEventHandlerMap<BookEvent, BookEventContext> = {
	reveal: async (bookEvent: BookEventOfType<'reveal'>, { bookEvents }: BookEventContext) => {
		if (bookEvents.filter((event) => event.type === 'reveal').length > 1) recordBookEvent({ bookEvent });
		if (bookEvent.gameType === 'basegame') clearFeature();
		stateGame.gameType = bookEvent.gameType;
		const columns = bookEvent.board.map((reel) => reel.slice(1, 5).map((raw) => String(raw.name)));
		await reelEngine.stop(columns, bookEvent.anticipation ?? [0, 0, 0, 0, 0]);
		applyVisible(bookEvent.board);
		tone(180, 0.05, 'triangle', 0.02);
	},
	winInfo: async (bookEvent: BookEventOfType<'winInfo'>) => {
		await flushMelts();
		if (maxWinShown) {
			// A winInfo after MAX WIN does not add another celebration. The meter stays on the cap.
			stateBet.winBookEventAmount = CAP_AMOUNT;
			return;
		}
		const lineOverCap = bookEvent.wins.some((win) => win.win > CAP_AMOUNT) || bookEvent.totalWin > CAP_AMOUNT;
		const room = CAP_AMOUNT - stateBet.winBookEventAmount;
		const crosses = bookEvent.totalWin > room;
		const positions = bookEvent.wins.flatMap((win) => win.positions);
		tone(520, 0.18, 'triangle', 0.03);
		await glowWins(positions);
		if (lineOverCap || crosses) stateBet.winBookEventAmount = CAP_AMOUNT;
	},
	setWin: async (bookEvent: BookEventOfType<'setWin'>) => {
		if (maxWinShown) return;
		const room = CAP_AMOUNT - stateBet.winBookEventAmount;
		if (bookEvent.amount > room) return;
		const amount = clampToCap(bookEvent.amount);
		const level = winLevelMap[(bookEvent.winLevel as WinLevel) || 1];
		await showWin(amount, bookEvent.winLevel, level?.text ?? 'WIN', 'win');
	},
	setTotalWin: async (bookEvent: BookEventOfType<'setTotalWin'>) => {
		stateBet.winBookEventAmount = clampToCap(bookEvent.amount);
	},
	finalWin: async (bookEvent: BookEventOfType<'finalWin'>) => {
		stateBet.winBookEventAmount = bookEvent.amount;
	},
	freeSpinTrigger: async (bookEvent: BookEventOfType<'freeSpinTrigger'>) => {
		await glowWins(bookEvent.positions);
	},
	enterBonus: async () => {
		stateGame.gameType = 'freegame';
	},
	bonusTier: async (bookEvent: BookEventOfType<'bonusTier'>) => {
		stateGame.tierName = bookEvent.tierName;
		stateGame.freeSpin = { current: 0, total: bookEvent.spins };
		tone(220, 0.4, 'sine', 0.04);
		await present({
			kind: 'tier',
			title: t(bookEvent.tierName),
			subtitle: t(`${bookEvent.spins} free spins`),
			amount: null,
			winLevel: 5,
			duration: stateBet.isTurbo ? 700 : TEMPO.intro,
		});
	},
	updateFreeSpin: async (bookEvent: BookEventOfType<'updateFreeSpin'>) => {
		stateGame.freeSpin = { current: bookEvent.amount + 1, total: bookEvent.total };
	},
	freeSpinRetrigger: async (bookEvent: BookEventOfType<'freeSpinRetrigger'>) => {
		await glowWins(bookEvent.positions);
		if (stateGame.freeSpin) stateGame.freeSpin = { ...stateGame.freeSpin, total: bookEvent.totalFs };
	},
	retrigger: async (bookEvent: BookEventOfType<'retrigger'>) => {
		await present({
			kind: 'retrigger',
			title: t(`+${bookEvent.addedSpins} spins`),
			subtitle: t(bookEvent.tier),
			amount: null,
			winLevel: 4,
			duration: stateBet.isTurbo ? 500 : 1200,
		});
	},
	freeSpinEnd: async (bookEvent: BookEventOfType<'freeSpinEnd'>) => {
		// Bonus total only. The round total is finalWin, which is what the RGS pays.
		if (!maxWinShown) {
			await showWin(bookEvent.amount, bookEvent.winLevel, 'TOTAL WIN', 'total');
		}
		clearFeature();
		stateGame.gameType = 'basegame';
	},
	fullBleed: async (bookEvent: BookEventOfType<'fullBleed'>) => {
		tone(140, 0.3, 'sawtooth', 0.02);
		await Promise.all(bookEvent.transformations.map((item) => queueMelt(item.reel, item.row - 1, item.to)));
		await flushMelts();
	},
	reelBleed: async (bookEvent: BookEventOfType<'reelBleed'>) => {
		if (bookEvent.multiplier && bookEvent.multiplier > 1) {
			const next = stateGame.reelMultipliers.slice();
			next[bookEvent.reel] = bookEvent.multiplier;
			stateGame.reelMultipliers = next;
		}
		bookEvent.transformations.forEach((item) => {
			queueMelt(item.reel, item.row - 1, item.to);
		});
		await hold(stateBet.isTurbo ? TEMPO.bleed.turboStagger : TEMPO.bleed.stagger);
	},
	stickyBleed: async (bookEvent: BookEventOfType<'stickyBleed'>) => {
		bookEvent.transformations.forEach((item) => queueMelt(item.reel, item.row - 1, item.to));
		await hold(stateBet.isTurbo ? TEMPO.bleed.turboStagger : TEMPO.bleed.stagger);
	},
	stickyReel: async (bookEvent: BookEventOfType<'stickyReel'>) => {
		stateGame.stickyReels = bookEvent.stickyReels.slice();
		const next = stateGame.reelMultipliers.slice();
		bookEvent.stickyReels.forEach((reel, index) => {
			const mult = bookEvent.stickyMultipliers[index] ?? bookEvent.multipliers[index];
			if (mult) next[reel] = mult;
		});
		stateGame.reelMultipliers = next;
	},
	updateGlobalMult: async (bookEvent: BookEventOfType<'updateGlobalMult'>) => {
		stateGame.globalMult = bookEvent.globalMult;
		await hold(360);
	},
	boardAfterBleed: async (bookEvent: BookEventOfType<'boardAfterBleed'>) => {
		await flushMelts();
		applyVisible(bookEvent.board);
		stateGame.reelMultipliers = bookEvent.reelMultipliers.slice();
		stateGame.globalMult = bookEvent.globalMult || 1;
		stateGame.stickyReels = bookEvent.stickyReels?.slice() ?? [];
	},
	wincap: async (bookEvent: BookEventOfType<'wincap'>) => {
		maxWinShown = true;
		const amount = clampToCap(bookEvent.amount);
		stateBet.winBookEventAmount = amount;
		await showWin(amount, 10, 'MAX WIN', 'total');
	},
	createBonusSnapshot: async (bookEvent: BookEventOfType<'createBonusSnapshot'>) => {
		const find = <T extends BookEvent['type']>(type: T) =>
			[...bookEvent.bookEvents].reverse().find((event) => event.type === type) as
				| BookEventOfType<T>
				| undefined;
		const tier = find('bonusTier');
		const update = find('updateFreeSpin');
		const total = find('setTotalWin');
		const global = find('updateGlobalMult');
		const sticky = find('stickyReel');
		if (tier) {
			stateGame.tierName = tier.tierName;
			stateGame.gameType = 'freegame';
		}
		if (update) stateGame.freeSpin = { current: update.amount + 1, total: update.total };
		if (total) stateBet.winBookEventAmount = clampToCap(total.amount);
		if (global) stateGame.globalMult = global.globalMult;
		if (sticky) stateGame.stickyReels = sticky.stickyReels.slice();
		if (bookEvent.bookEvents.some((event) => event.type === 'wincap')) {
			maxWinShown = true;
			stateBet.winBookEventAmount = CAP_AMOUNT;
		}
	},
};

export const skipPresentation = () => skipHolds();

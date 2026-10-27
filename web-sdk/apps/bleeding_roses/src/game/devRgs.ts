import { registerDevRgs } from 'rgs-requests';

import { MODE_COST } from './betModes';
import type { BookEvent } from './typesBookEvent';

type SampleBook = {
	id: string;
	mode: string;
	criteria: string;
	payoutMultiplier: number;
	events: BookEvent[];
};

// base-wincap is lookup id 12 in lookUpTable_base.csv: mode base, simulation 11, criteria wincap, 15000x.
const ORDER: Record<string, string[]> = {
	base: ['base-win', 'base-best', 'base-bleeding', 'base-moon', 'base-harvest', 'base-zero', 'base-spin', 'base-wincap'],
	bloodlust: ['bloodlust-spin', 'bloodlust-bleeding'],
	super_ante_20: ['super-spin', 'super-harvest'],
	buy_bleeding: ['buy-bleeding'],
	buy_blood_moon: ['buy-moon'],
	buy_harvest: ['buy-harvest'],
	full_bleed: ['full-spin', 'full-best', 'full-zero'],
};

let books: SampleBook[] = [];
let cursor: Record<string, number> = {};
let balanceCents = 100_000;
let pendingCreditCents = 0;

const toApi = (cents: number) => cents * 10_000;

const levels = [0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.6, 2, 3, 4, 5, 10, 20, 50, 100];

const query = () => new URLSearchParams(window.location.search);

const pick = (mode: string) => {
	const forced = query().get('book');
	if (forced) return books.find((book) => book.id === forced) ?? books[0];
	const ids = ORDER[mode] ?? ORDER.base;
	const index = cursor[mode] ?? 0;
	cursor[mode] = index + 1;
	const id = ids[index % ids.length];
	return books.find((book) => book.id === id) ?? books[0];
};

export const installDevBooks = () => {
	if (!import.meta.env.DEV) return;
	registerDevRgs({
		authenticate: async () => {
			if (!books.length) {
				const url = new URL('./dev/sample-books.json', import.meta.url).href;
				const payload = (await (await fetch(url)).json()) as { books: SampleBook[] };
				books = payload.books;
			}
			const start = query().get('mode') || 'base';
			return {
				balance: { amount: toApi(balanceCents), currency: 'USD' },
				config: {
					gameID: 'bleeding_roses',
					minBet: 200_000,
					maxBet: 100_000_000,
					stepBet: 200_000,
					defaultBetLevel: 1_000_000,
					betLevels: levels.map((level) => Math.round(level * 1_000_000)),
					betModes: {},
					jurisdiction: {
						socialCasino: false,
						disabledFullscreen: false,
						disabledTurbo: false,
						disabledSuperTurbo: false,
						disabledAutoplay: false,
						disabledSlamstop: false,
						disabledSpacebar: false,
						disabledBuyFeature: false,
						displayNetPosition: false,
						displayRTP: true,
						displaySessionTimer: false,
						minimumRoundDuration: 0,
					},
				},
				round: {
					amount: 1_000_000,
					mode: start,
					active: false,
					payoutMultiplier: 0,
				},
			};
		},
		bet: async (options) => {
			const cost = MODE_COST[options.mode] ?? 1;
			const debit = Math.round(options.amount * cost * 100);
			if (debit > balanceCents) {
				return { error: 'ERR_IPB', message: 'Insufficient funds to place this bet.' };
			}
			balanceCents -= debit;
			const book = pick(options.mode);
			const credit = Math.round(options.amount * (book.payoutMultiplier / 100) * 100);
			pendingCreditCents = credit;
			if (credit === 0) pendingCreditCents = 0;
			return {
				balance: { amount: toApi(balanceCents), currency: options.currency || 'USD' },
				round: {
					betID: 1,
					amount: Math.round(options.amount * 1_000_000),
					payout: Math.round(options.amount * (book.payoutMultiplier / 100) * 1_000_000),
					payoutMultiplier: book.payoutMultiplier,
					active: false,
					state: book.events,
					mode: options.mode,
					event: '0',
					costMultiplier: cost,
				},
			};
		},
		endRound: async () => {
			balanceCents += pendingCreditCents;
			pendingCreditCents = 0;
			return { balance: { amount: toApi(balanceCents), currency: 'USD' } };
		},
		endEvent: async (options) => ({ event: `${options.eventIndex}` }),
	});
};

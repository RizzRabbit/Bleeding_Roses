import type { RawSymbol, SymbolState } from './types';

export const SYMBOL_SIZE = 180;
export const REEL_COUNT = 5;
export const VISIBLE_ROWS = 4;

export const INITIAL_SYMBOL_STATE: SymbolState = 'static';

/** Padded board: row 0 and row 5 are off-window. Visible rows match the target layout. */
/** Padded 6-high reels. Visible rows 1–4 match the v6 desktop mockup. */
export const INITIAL_BOARD: RawSymbol[][] = [
	[{ name: 'Q' }, { name: '10' }, { name: 'BWR' }, { name: 'BR' }, { name: 'WR' }, { name: 'J' }],
	[{ name: 'A' }, { name: 'J' }, { name: 'Q' }, { name: 'K' }, { name: 'A' }, { name: '10' }],
	[{ name: 'J' }, { name: 'Q' }, { name: 'RP' }, { name: 'RR' }, { name: 'BR' }, { name: 'K' }],
	[{ name: '10' }, { name: 'K' }, { name: 'K' }, { name: 'BBR' }, { name: 'WR' }, { name: 'Q' }],
	[{ name: 'K' }, { name: 'A' }, { name: 'BRR' }, { name: 'BH' }, { name: 'J' }, { name: 'A' }],
];

const CYCLE = ['10', 'J', 'Q', 'K', 'A', 'WR', 'RR', 'BR', 'BH', 'RP', 'Q', 'K', 'WR', 'A', 'J', '10'];

export const PADDING_BOARD: RawSymbol[][] = Array.from({ length: REEL_COUNT }, (_, reel) =>
	Array.from({ length: 24 }, (_, index) => ({ name: CYCLE[(index + reel * 3) % CYCLE.length] })),
);

const SPIN_SHARED = {
	reelPaddingMultiplierNormal: 1.15,
	reelPaddingMultiplierAnticipated: 1.4,
	reelSpinDelay: 160,
};

/** Calm reel travel. Speeds are pixels per millisecond. */
export const SPIN_OPTIONS_DEFAULT = {
	...SPIN_SHARED,
	reelPreSpinSpeed: 0.26,
	reelSpinSpeed: 0.58,
	reelSpinSpeedBeforeBounce: 0.2,
	reelBounceBackSpeed: 0.14,
	reelBounceSizeMulti: 0.1,
};

export const SPIN_OPTIONS_FAST = {
	...SPIN_SHARED,
	reelPreSpinSpeed: 1.6,
	reelSpinSpeed: 2.1,
	reelSpinSpeedBeforeBounce: 1.4,
	reelBounceBackSpeed: 0.9,
	reelBounceSizeMulti: 0.05,
	reelSpinDelay: 0,
	reelPaddingMultiplierNormal: 0.35,
	reelPaddingMultiplierAnticipated: 0.5,
};

export const BLOODY = new Set(['BWR', 'BRR', 'BBR']);
export const PLAIN_ROSES = new Set(['WR', 'RR', 'BR']);

export const STILL_FILES: Record<string, string> = {
	'10': '01_10.png',
	J: '02_J.png',
	Q: '03_Q.png',
	K: '04_K.png',
	A: '05_A.png',
	WR: '06_white_rose.png',
	RR: '07_red_rose.png',
	BR: '08_black_rose.png',
	BWR: '09_bloody_white_rose.png',
	BRR: '10_bloody_red_rose.png',
	BBR: '11_bloody_black_rose.png',
	BH: '12_bleeding_heart_wild.png',
	RP: '13_reaper_scatter.png',
};

export const CLIP_KEY: Record<string, string> = {
	WR: 'white_rose',
	RR: 'red_rose',
	BR: 'black_rose',
	BWR: 'white_rose',
	BRR: 'red_rose',
	BBR: 'black_rose',
	BH: 'bleeding_heart',
};

export const MAX_WIN_X = 15000;
export const RTP = 0.96;

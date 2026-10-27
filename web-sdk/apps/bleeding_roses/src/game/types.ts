export type SymbolName =
	| '10'
	| 'J'
	| 'Q'
	| 'K'
	| 'A'
	| 'WR'
	| 'RR'
	| 'BR'
	| 'BWR'
	| 'BRR'
	| 'BBR'
	| 'BH'
	| 'RP';

export type RawSymbol = {
	name: SymbolName | string;
	wild?: boolean;
	scatter?: boolean;
	multiplier?: number;
	bled?: boolean;
};

export type GameType = 'basegame' | 'freegame';

export const SYMBOL_STATES = ['static', 'spin', 'land', 'win', 'melt', 'idle'] as const;

export type SymbolState = (typeof SYMBOL_STATES)[number];

export type Position = {
	reel: number;
	row: number;
};

export type Transformation = Position & {
	from: string;
	to: string;
};

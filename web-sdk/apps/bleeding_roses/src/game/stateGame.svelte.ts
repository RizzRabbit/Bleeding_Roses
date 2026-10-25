import { BLOODY, INITIAL_BOARD } from './constants';
import type { RawSymbol } from './types';
import { shouldIdle } from './reels.svelte';

export type CellAnim = 'still' | 'idle' | 'melt' | 'win';

export type Cell = { name: string; anim: CellAnim; token: number };

export type Presentation = {
	kind: 'win' | 'tier' | 'retrigger' | 'total';
	title: string;
	subtitle: string;
	amount: number | null;
	winLevel: number;
	duration: number;
	resolve: () => void;
};

const visible = (board: RawSymbol[][]): Cell[][] =>
	board.map((reel) =>
		reel.slice(1, 5).map((raw) => ({
			name: String(raw.name),
			anim: (shouldIdle(String(raw.name)) ? 'idle' : 'still') as CellAnim,
			token: 0,
		})),
	);

const finishers = new Map<string, () => void>();

export const stateGame = $state({
	cells: visible(INITIAL_BOARD),
	gameType: 'basegame' as 'basegame' | 'freegame',
	reelMultipliers: [1, 1, 1, 1, 1],
	globalMult: 1,
	stickyReels: [] as number[],
	tierName: '',
	freeSpin: null as { current: number; total: number } | null,
	glow: null as { reel: number; row: number } | null,
	presentation: null as Presentation | null,
	panel: null as null | 'buy' | 'ante' | 'info' | 'auto' | 'confirm' | 'funds' | 'menu',
	infoTab: 'paytable' as 'paytable' | 'rules' | 'how',
	confirm: null as null | { title: string; body: string; mode: string; resolve: (ok: boolean) => void },
});

export const columnNames = () => stateGame.cells.map((reel) => reel.map((cell) => cell.name));

export const applyVisible = (board: RawSymbol[][]) => {
	board.forEach((reel, reelIndex) => {
		reel.slice(1, 5).forEach((raw, row) => {
			const cell = stateGame.cells[reelIndex][row];
			const name = String(raw.name);
			if (!cell) return;
			if (cell.name !== name || cell.anim === 'win' || cell.anim === 'melt') {
				cell.name = name;
				cell.anim = shouldIdle(name) ? 'idle' : 'still';
				cell.token += 1;
			} else if (shouldIdle(name) && cell.anim !== 'idle') {
				cell.anim = 'idle';
				cell.token += 1;
			}
		});
	});
};

export const clearFeature = () => {
	stateGame.reelMultipliers = [1, 1, 1, 1, 1];
	stateGame.globalMult = 1;
	stateGame.stickyReels = [];
	stateGame.tierName = '';
	stateGame.freeSpin = null;
	stateGame.glow = null;
	stateGame.gameType = 'basegame';
};

const keyOf = (reel: number, row: number, token: number) => `${reel}:${row}:${token}`;

export const animateCell = (reel: number, row: number, anim: CellAnim, nextName?: string) =>
	new Promise<void>((resolve) => {
		const cell = stateGame.cells[reel]?.[row];
		if (!cell) {
			resolve();
			return;
		}
		if (nextName && cell.name === nextName && anim === 'melt') {
			resolve();
			return;
		}
		cell.token += 1;
		const token = cell.token;
		finishers.set(keyOf(reel, row, token), () => {
			finishers.delete(keyOf(reel, row, token));
			if (nextName) cell.name = nextName;
			const name = cell.name;
			cell.anim = name === 'BH' || BLOODY.has(name) ? 'idle' : 'still';
			resolve();
		});
		cell.anim = anim;
	});

export const completeCell = (reel: number, row: number, token: number) => {
	finishers.get(keyOf(reel, row, token))?.();
};

export const present = (input: Omit<Presentation, 'resolve'>) =>
	new Promise<void>((resolve) => {
		stateGame.presentation = { ...input, resolve };
	});

export const dismissPresentation = () => {
	const current = stateGame.presentation;
	if (!current) return;
	stateGame.presentation = null;
	stateGame.glow = null;
	current.resolve();
};

export const askConfirm = (title: string, body: string, mode: string) =>
	new Promise<boolean>((resolve) => {
		stateGame.panel = 'confirm';
		stateGame.confirm = {
			title,
			body,
			mode,
			resolve: (ok) => {
				stateGame.confirm = null;
				stateGame.panel = null;
				resolve(ok);
			},
		};
	});

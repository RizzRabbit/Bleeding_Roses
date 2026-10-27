import { stateBet, stateMeta, type BetModeData } from 'state-shared';

import { t } from './social';

const blank = (
	mode: string,
	costMultiplier: number,
	type: BetModeData['type'],
	title: string,
	dialog: string,
): BetModeData => ({
	mode,
	costMultiplier,
	type,
	parent: '',
	children: '',
	maxWin: 15000,
	assets: { icon: '', volatility: '', button: '', dialogImage: '', dialogVolatility: '' },
	text: {
		title,
		dialog,
		button: title,
		tickerIdle: '',
		tickerSpin: '',
		description: dialog,
		betAmountLabel: title,
		bannerText: '',
	},
});

export const MODE_COST: Record<string, number> = {
	base: 1,
	bloodlust: 3,
	super_ante_20: 20,
	buy_bleeding: 100,
	buy_blood_moon: 300,
	buy_harvest: 600,
	full_bleed: 100,
};

export const ONE_SHOT = new Set(['buy_bleeding', 'buy_blood_moon', 'buy_harvest', 'full_bleed']);

export const playSession = { persistentMode: 'base' };

export const applyBetModes = () => {
	stateMeta.betModeMeta = {
		base: blank('base', 1, 'default', 'Base', 'Standard round.'),
		bloodlust: blank('bloodlust', 3, 'activate', 'Bloodlust', 'Ante. Each round is 3x the base play.'),
		super_ante_20: blank('super_ante_20', 20, 'activate', 'Super Ante', 'Ante. Each round is 20x the base play.'),
		buy_bleeding: blank('buy_bleeding', 100, 'buy', 'Bleeding Spins', 'Bonus. 100x the base play.'),
		buy_blood_moon: blank('buy_blood_moon', 300, 'buy', 'Blood Moon', 'Bonus. 300x the base play.'),
		buy_harvest: blank('buy_harvest', 600, 'buy', "Reaper's Harvest", 'Bonus. 600x the base play.'),
		full_bleed: blank('full_bleed', 100, 'buy', 'Full Bleed', 'Feature round. 100x the base play.'),
	};
	if (stateBet.activeBetModeKey === 'BASE') stateBet.activeBetModeKey = 'base';
};

export const modeCost = (mode = stateBet.activeBetModeKey) => MODE_COST[mode] ?? 1;

export const debitAmount = (mode = stateBet.activeBetModeKey) => stateBet.betAmount * modeCost(mode);

export const canAfford = (mode = stateBet.activeBetModeKey) =>
	stateBet.betAmount > 0 && debitAmount(mode) <= stateBet.balanceAmount + 1e-9;

export const restorePersistent = () => {
	if (ONE_SHOT.has(stateBet.activeBetModeKey)) stateBet.activeBetModeKey = playSession.persistentMode;
};

export const setPersistent = (mode: string) => {
	playSession.persistentMode = mode;
	stateBet.activeBetModeKey = mode;
};

export const priceLine = (mode: string) => t(`${modeCost(mode)}x`);

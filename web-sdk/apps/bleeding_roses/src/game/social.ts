import { stateConfig, stateUrlDerived } from 'state-shared';

/** Whole-word swaps from the Stake social-mode list. Longer phrases first. */
const PHRASES: [RegExp, string][] = [
	[/\bbonus buy\b/gi, 'Bonus'],
	[/\bbuy bonus\b/gi, 'Get Bonus'],
	[/\bwin feature\b/gi, 'play feature'],
	[/\bplace your bets\b/gi, 'come and play'],
	[/\btotal bet\b/gi, 'total play'],
	[/\bpaytable\b/gi, 'Win table'],
	[/\bpay table\b/gi, 'Win table'],
	[/\bpays out\b/gi, 'won'],
	[/\bpay out\b/gi, 'win'],
	[/\bpaid out\b/gi, 'win'],
	[/\bat the cost of\b/gi, 'for'],
	[/\bcost of\b/gi, 'can be played for'],
	[/\bbe awarded to player's accounts\b/gi, "appear in player's accounts"],
	[/\binsufficient funds\b/gi, 'insufficient balance'],
	[/\bfunds\b/gi, 'balance'],
	[/\bfund\b/gi, 'balance'],
	[/\bbetting\b/gi, 'playing'],
	[/\bbets\b/gi, 'plays'],
	[/\bbet\b/gi, 'play'],
	[/\bpays\b/gi, 'wins'],
	[/\bpaid\b/gi, 'won'],
	[/\bpay\b/gi, 'win'],
	[/\bbought\b/gi, 'instantly triggered'],
	[/\bpurchase\b/gi, 'play'],
	[/\bbuy\b/gi, 'play'],
	[/\bwager\b/gi, 'play'],
	[/\bstake\b/gi, 'play amount'],
	[/\bgamble\b/gi, 'play'],
	[/\bcurrency\b/gi, 'token'],
	[/\bcredit\b/gi, 'balance'],
	[/\bdeposit\b/gi, 'get coins'],
	[/\bwithdraw\b/gi, 'redeem'],
	[/\bcash\b/gi, 'coins'],
	[/\bmoney\b/gi, 'coins'],
	[/\brebet\b/gi, 'respin'],
];

export const isSocial = () =>
	stateUrlDerived.social() || Boolean(stateConfig.jurisdiction.socialCasino);

const matchCase = (source: string, replacement: string) => {
	if (source === source.toUpperCase()) return replacement.toUpperCase();
	if (source[0] === source[0]?.toUpperCase()) {
		return replacement.charAt(0).toUpperCase() + replacement.slice(1);
	}
	return replacement.charAt(0).toLowerCase() + replacement.slice(1);
};

export const t = (value: string) => {
	if (!isSocial() || !value) return value;
	let next = value;
	for (const [pattern, replacement] of PHRASES) {
		next = next.replace(pattern, (found) => matchCase(found, replacement));
	}
	return next;
};

export const modeLabel = (mode: string) => {
	const labels: Record<string, [string, string]> = {
		base: ['Base', 'Base'],
		bloodlust: ['Bloodlust', 'Bloodlust'],
		super_ante_20: ['Super Ante', 'Super Ante'],
		buy_bleeding: ['Bleeding Spins', 'Bleeding Spins'],
		buy_blood_moon: ['Blood Moon', 'Blood Moon'],
		buy_harvest: ["Reaper's Harvest", "Reaper's Harvest"],
		full_bleed: ['Full Bleed', 'Full Bleed'],
	};
	const pair = labels[mode] ?? [mode, mode];
	return t(isSocial() ? pair[1] : pair[0]);
};

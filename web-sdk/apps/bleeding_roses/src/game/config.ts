/** Published math. Prices and pays are multiples of the base bet. RTP is 96% on every mode. */
export const GAME = {
	providerName: 'Rizzin Games',
	gameName: 'Bleeding Roses',
	gameID: 'bleeding_roses',
	rtp: 0.96,
	volatility: 3,
	maxWin: 15000,
	ways: 1024,
};

export type PayRow = { symbol: string; label: string; three: number; four: number; five: number };

const rose = (label: string, symbol: string, three: number, four: number, five: number): PayRow => ({
	symbol,
	label,
	three,
	four,
	five,
});

export const PAYTABLE: PayRow[] = [
	rose('10', '10', 0.1, 0.2, 0.5),
	rose('J', 'J', 0.1, 0.2, 0.5),
	rose('Q', 'Q', 0.1, 0.3, 0.8),
	rose('K', 'K', 0.2, 0.4, 1),
	rose('A', 'A', 0.2, 0.5, 1.2),
	rose('White Rose', 'WR', 0.4, 0.8, 2),
	rose('Red Rose', 'RR', 0.5, 1.2, 3),
	rose('Black Rose', 'BR', 0.6, 1.6, 4),
	rose('Bloody White Rose', 'BWR', 1.2, 2.4, 6),
	rose('Bloody Red Rose', 'BRR', 1.5, 3.6, 9),
	rose('Bloody Black Rose', 'BBR', 1.8, 4.8, 12),
	rose('Bleeding Heart', 'BH', 1, 4, 15),
];

export const RULES: { title: string; body: string }[] = [
	{
		title: 'Ways',
		body: 'Bleeding Roses is a 5 reel, 4 row game with 1,024 ways. Matching symbols pay left to right. The Bleeding Heart is wild for every symbol except the Reaper.',
	},
	{
		title: 'Bleed',
		body: 'A Bleeding Heart on reels 2, 3 or 4 bleeds the roses. In the base game and on the Full Bleed spin, that reel is stamped 2x, 3x or 5x and the multiplier applies to ways that pass through it. Plain roses play their melt, then loop the bloody idle.',
	},
	{
		title: 'Bleeding Spins',
		body: '3 Reapers award 10 free spins. Every rose on the board bleeds. Reel multipliers are not stamped. 3 Reapers during the feature add 5 spins.',
	},
	{
		title: 'Blood Moon',
		body: '4 Reapers award 12 free spins. A reel locks bloody the first time a Bleeding Heart lands on it and keeps the 2x, 3x or 5x drawn for that lock. Roses that land on a locked reel bleed. 4 Reapers add 6 spins.',
	},
	{
		title: "Reaper's Harvest",
		body: '5 Reapers award 15 free spins. The whole board bleeds. A global multiplier starts at 1x and grows by 1 on every spin that bleeds, once per spin. 5 Reapers add 8 spins.',
	},
	{
		title: 'Ante, buys and Full Bleed',
		body: 'Bloodlust is an ante of 3x the base bet. Super Ante is 20x. Bonus Buy opens 4 features from 100x: Bleeding Spins at 100x, Blood Moon at 300x, Reaper\'s Harvest at 600x, and Full Bleed at 100x. Full Bleed turns every plain rose bloody before the ways are scored. All prices are multiples of the base bet.',
	},
	{
		title: 'Return and maximum win',
		body: 'Every mode returns RTP 96.00%. The maximum win is 15,000x the base bet on every mode. Antes and buys do not scale that cap. Volatility is 3 stars.',
	},
];

export const HOW_TO_PLAY: { control: string; text: string }[] = [
	{ control: 'Spin', text: 'Starts a round at the selected bet.' },
	{ control: '+ / −', text: 'Steps the bet through the allowed levels. The ends stop there.' },
	{ control: 'Autoplay', text: 'Opens a confirmation, then repeats the round for the chosen count.' },
	{ control: 'Turbo', text: 'Speeds up the reels and the win presentation.' },
	{ control: 'Bonus Buy', text: 'Opens 4 features from 100x: Bleeding Spins, Blood Moon, Reaper\'s Harvest and Full Bleed.' },
	{ control: 'Ante', text: 'Turns Bloodlust (3x) or Super Ante (20x) on for the following rounds. Each one asks you to confirm the cost.' },
	{ control: 'Full Bleed', text: 'A single feature round at 100x the base bet. Every plain rose bleeds before the ways are scored.' },
	{ control: 'Sound', text: 'Mutes or restores every tone, including feature rounds and big wins.' },
	{ control: 'Info', text: 'Opens the paytable, the rules and this guide.' },
	{ control: 'Menu', text: 'Opens sound and info.' },
	{ control: 'Space', text: 'Starts a bet. It does nothing while a panel is open, and it skips a spin that is already moving.' },
];

export const DISCLAIMER =
	'Malfunction voids all wins and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted rounds. The expected return is calculated over many plays. The game display is not representative of any physical device and is for illustrative purposes only. Winnings are settled according to the amount received from the Remote Game Server and not from events within the web browser. TM and © 2026 Engine.';

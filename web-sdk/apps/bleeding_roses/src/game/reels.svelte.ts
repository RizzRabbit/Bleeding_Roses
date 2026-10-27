import { BLOODY } from './constants';
import { spinPace, type SpinPace } from './tempo';

const FILL = ['10', 'J', 'Q', 'K', 'A', 'WR', 'RR', 'BR', 'Q', 'K', 'A', 'J'];

export type ReelView = {
	scroll: number;
	anticipating: boolean;
	symbols: string[];
};

const filler = (reel: number, index: number) => FILL[(index + reel * 3) & 15] ?? 'Q';

const accDist = (pace: SpinPace) => pace.cellsPerSec * (pace.accel / 1000) * 0.5;

const coastEnd = (elapsed: number, pace: SpinPace) => {
	const coast = Math.max(0, elapsed - pace.accel);
	return accDist(pace) + pace.cellsPerSec * (coast / 1000);
};

type Plan = {
	landAt: number;
	brakeAt: number;
	sBrake: number;
	dist: number;
	finalAt: number;
	overshoot: number;
	finals: string[];
	resolve: () => void;
};

const makeViews = (): ReelView[] =>
	Array.from({ length: 5 }, () => ({ scroll: 0, anticipating: false, symbols: [] }));

export const reelView = $state({
	active: false,
	startedAt: 0,
	reels: makeViews(),
});

let plans: (Plan | null)[] = [null, null, null, null, null];
let raf = 0;
let paceOverride: SpinPace | null = null;
let home: string[][] = [[], [], [], [], []];

const symbolFor = (reel: number, index: number, plan: Plan | null) => {
	if (plan && index >= plan.finalAt && index < plan.finalAt + 4) return plan.finals[index - plan.finalAt];
	if (index >= 0 && index < 4) return home[reel][index] ?? 'Q';
	return filler(reel, index);
};

const drawNames = (reel: number, scroll: number, plan: Plan | null) => {
	const base = Math.floor(scroll) - 2;
	const names: string[] = [];
	for (let i = 0; i < 10; i += 1) names.push(symbolFor(reel, base + i, plan));
	reelView.reels[reel].symbols = names;
	reelView.reels[reel].scroll = scroll - base;
};

const motion = (elapsed: number, plan: Plan | null, pace: SpinPace) => {
	if (!plan || elapsed < plan.brakeAt) {
		if (elapsed <= pace.accel) {
			const u = Math.max(0, elapsed) / pace.accel;
			return pace.cellsPerSec * (pace.accel / 1000) * (u ** 3 - u ** 4 / 2);
		}
		return coastEnd(Math.min(elapsed, plan ? plan.brakeAt : elapsed), pace);
	}
	const into = elapsed - plan.brakeAt;
	if (into < pace.brake) {
		const u = into / pace.brake;
		return plan.sBrake + plan.dist * (1 - (1 - u) ** pace.brakePower);
	}
	const u = Math.min(1, (into - pace.brake) / pace.settle);
	const peak = plan.finalAt + plan.overshoot;
	const rest = plan.finalAt;
	return rest + (peak - rest) * 0.5 * (1 + Math.cos(Math.PI * u));
};

const frame = (now: number) => {
	raf = 0;
	const pace = paceOverride ?? spinPace();
	const elapsed = now - reelView.startedAt;
	let live = false;
	reelView.reels.forEach((_, reel) => {
		const plan = plans[reel];
		if (plan && elapsed >= plan.landAt) {
			drawNames(reel, plan.finalAt, plan);
			reelView.reels[reel].anticipating = false;
			if (!plan.resolve) return;
			const resolve = plan.resolve;
			plan.resolve = () => {};
			plans[reel] = null;
			resolve();
			return;
		}
		live = true;
		const scroll = motion(elapsed, plan, pace);
		drawNames(reel, scroll, plan);
		if (plan && elapsed >= plan.brakeAt - 400) reelView.reels[reel].anticipating = false;
	});
	if (live) raf = requestAnimationFrame(frame);
	else reelView.active = plans.some(Boolean);
};

export const reelEngine = {
	start(current: string[][]) {
		cancelAnimationFrame(raf);
		paceOverride = null;
		plans = [null, null, null, null, null];
		reelView.startedAt = performance.now();
		reelView.active = true;
		home = current.map((column) => column.slice());
		current.forEach((_, reel) => {
			reelView.reels[reel].scroll = 0;
			reelView.reels[reel].anticipating = false;
			drawNames(reel, 0, null);
		});
		raf = requestAnimationFrame(frame);
	},
	stop(finals: string[][], anticipation: number[]) {
		const pace = spinPace();
		const origin = reelView.startedAt || performance.now();
		return Promise.all(
			finals.map(
				(column, reel) =>
					new Promise<void>((resolve) => {
						const extra = (anticipation[reel] || 0) > 0 ? pace.anticipation + (anticipation[reel] || 0) * 80 : 0;
						let landFromStart = pace.firstStop + reel * pace.gap + extra;
						const elapsed = performance.now() - origin;
						if (elapsed > landFromStart - pace.settle - pace.brake) {
							landFromStart = elapsed + pace.brake + pace.settle;
						}
						const brakeAt = landFromStart - pace.settle - pace.brake;
						const sBrake = coastEnd(Math.max(pace.accel, brakeAt), pace);
						const natural = (pace.cellsPerSec * pace.brake) / (pace.brakePower * 1000);
						const peak = sBrake + natural;
						const finalAt = Math.max(4, Math.round(peak - pace.overshootCells));
						const dist = finalAt + pace.overshootCells - sBrake;
						plans[reel] = {
							landAt: landFromStart,
							brakeAt,
							sBrake,
							dist,
							finalAt,
							overshoot: pace.overshootCells,
							finals: column,
							resolve,
						};
						reelView.reels[reel].anticipating = extra > 0;
						if (!raf) raf = requestAnimationFrame(frame);
					}),
			),
		).then(() => {
			reelView.active = false;
		});
	},
	hurry() {
		const pace = {
			...spinPace(),
			brake: Math.min(spinPace().brake, 200),
			settle: Math.min(spinPace().settle, 80),
			overshootCells: 0,
		};
		paceOverride = pace;
		const elapsed = performance.now() - reelView.startedAt;
		plans.forEach((plan, reel) => {
			if (!plan) return;
			if (elapsed >= plan.brakeAt) return;
			const landFromStart = elapsed + pace.brake + pace.settle + reel * 40;
			const brakeAt = elapsed;
			const sBrake = motion(elapsed, null, spinPace());
			const finalAt = Math.max(plan.finalAt, Math.ceil(sBrake + 2));
			plan.landAt = landFromStart;
			plan.brakeAt = brakeAt;
			plan.sBrake = sBrake;
			plan.finalAt = finalAt;
			plan.overshoot = 0;
			plan.dist = finalAt - sBrake;
			plan.finals = plan.finals;
			reelView.reels[reel].anticipating = false;
		});
	},
	abort() {
		cancelAnimationFrame(raf);
		raf = 0;
		paceOverride = null;
		plans.forEach((plan) => plan?.resolve?.());
		plans = [null, null, null, null, null];
		reelView.active = false;
	},
	symbolAt(reel: number, slot: number) {
		const names = reelView.reels[reel]?.symbols ?? [];
		return names[slot] ?? 'Q';
	},
};

export const shouldIdle = (name: string) => name === 'BH' || BLOODY.has(name);

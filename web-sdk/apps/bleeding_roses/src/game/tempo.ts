import { stateBet } from 'state-shared';

/**
 * Every board timing lives here.
 * Normal spin: last reel settled 2.72s after the press, stops 280ms apart,
 * soft brake, 0.05 cell overshoot, one cosine settle, no bounce.
 * Turbo and tap-to-skip use the fast column.
 */
export const TEMPO = {
	spin: {
		firstStop: 1600,
		gap: 280,
		accel: 300,
		cellsPerSec: 14.2857,
		brake: 844,
		settle: 380,
		overshootCells: 0.05,
		brakePower: 2.2,
		anticipation: 720,
	},
	turbo: {
		firstStop: 280,
		gap: 70,
		accel: 60,
		cellsPerSec: 44,
		brake: 180,
		settle: 90,
		overshootCells: 0,
		brakePower: 2,
		anticipation: 160,
	},
	win: {
		letter: 700,
		rose: 900,
		heartFrames: 90,
		fps: 30,
		small: 800,
		nice: 1200,
		great: 1500,
		big: 2800,
		super: 3200,
		mega: 3600,
		epic: 4200,
		max: 5200,
	},
	bleed: {
		stagger: 280,
		turboStagger: 70,
	},
	intro: 1600,
} as const;

export type SpinPace = {
	firstStop: number;
	gap: number;
	accel: number;
	cellsPerSec: number;
	brake: number;
	settle: number;
	overshootCells: number;
	brakePower: number;
	anticipation: number;
};

export const spinPace = (): SpinPace => (stateBet.isTurbo ? TEMPO.turbo : TEMPO.spin);

const holds = new Set<() => void>();

export const hold = (ms: number) =>
	new Promise<void>((resolve) => {
		const done = () => {
			clearTimeout(timer);
			holds.delete(done);
			resolve();
		};
		const timer = setTimeout(done, stateBet.isTurbo ? Math.round(ms * 0.35) : ms);
		holds.add(done);
	});

export const skipHolds = () => {
	[...holds].forEach((done) => done());
};

export const animSpeed = () => (stateBet.isTurbo ? 1 : TEMPO.win.fps / 60);

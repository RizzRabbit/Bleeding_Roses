/** v6 placements. Frame x/y/scale come from reel_frame.json at runtime. */
export type StageKind = 'desktop' | 'portrait' | 'square';

export type StagePlan = {
	kind: StageKind;
	width: number;
	height: number;
	logo: { cx: number; cy: number; width: number };
	plaques: { cx: number; cy: number; width: number }[];
	bar: { x: number; y: number; width: number; height: number };
	tools: 'top-right';
};

export const stageFor = (layoutType: string): StagePlan => {
	if (layoutType === 'portrait') {
		return {
			kind: 'portrait',
			width: 1080,
			height: 1920,
			logo: { cx: 540, cy: 410, width: 1020 },
			plaques: [
				{ cx: 280, cy: 610, width: 300 },
				{ cx: 800, cy: 610, width: 300 },
			],
			bar: { x: 130, y: 1733, width: 820, height: 150 },
			tools: 'top-right',
		};
	}
	if (layoutType === 'tablet') {
		return {
			kind: 'square',
			width: 1080,
			height: 1080,
			logo: { cx: 540, cy: 64, width: 640 },
			plaques: [
				{ cx: 180, cy: 980, width: 220 },
				{ cx: 420, cy: 980, width: 220 },
			],
			bar: { x: 80, y: 980, width: 0, height: 0 },
			tools: 'top-right',
		};
	}
	return {
		kind: 'desktop',
		width: 1920,
		height: 1080,
		logo: { cx: 960, cy: 72, width: 960 },
		plaques: [
			{ cx: 168, cy: 690, width: 250 },
			{ cx: 168, cy: 880, width: 250 },
		],
		bar: { x: 470, y: 904, width: 980, height: 150 },
		tools: 'top-right',
	};
};

export const mainSizesMap = {
	desktop: { width: 1920, height: 1080 },
	tablet: { width: 1080, height: 1080 },
	landscape: { width: 1920, height: 1080 },
	portrait: { width: 1080, height: 1920 },
};

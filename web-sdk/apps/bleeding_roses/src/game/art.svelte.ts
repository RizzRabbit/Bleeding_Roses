import * as PIXI from 'pixi.js';

import { STILL_FILES } from './constants';

export type FrameMeta = {
	window: { x: number; y: number; w: number; h: number };
	grid: { cols: number; rows: number; cell: number };
	mockup_1920: { cell: number; scale: number; frame_pos: [number, number]; window: { x: number; y: number; w: number; h: number } };
	mockup_portrait_1080: { cell: number; scale: number; frame_pos: [number, number]; window: { x: number; y: number; w: number; h: number } };
};

type SheetSpec = { frames: number; fps: number; sheets: string[] };
type Manifest = Record<string, Record<string, Record<string, SheetSpec>>>;

export type MemoryRow = { feature: string; name: string; bytes: number; scale: number };

const CLIP_BUDGET = 100 * 1024 * 1024;

export const artState = $state({
	ready: false,
	progress: 0,
	error: '',
	scale: 1,
	frame: null as PIXI.Texture | null,
	logo: null as PIXI.Texture | null,
	background: null as PIXI.Texture | null,
	frameMeta: null as FrameMeta | null,
	stills: {} as Record<string, PIXI.Texture>,
	memory: [] as MemoryRow[],
});

const clips = new Map<string, PIXI.Texture[]>();
let manifest: Manifest | null = null;

export const preferredScale = () => {
	if (typeof window === 'undefined') return 1;
	const query = new URLSearchParams(window.location.search).get('assetScale');
	if (query === '1' || query === '2') return Number(query);
	const desktop = window.innerWidth / Math.max(1, window.innerHeight) > 1.2 && window.innerWidth >= 900;
	const sharp = (window.devicePixelRatio || 1) >= 1.5;
	return desktop || sharp ? 2 : 1;
};

const note = (feature: string, name: string, bytes: number, scale: number) => {
	artState.memory = [...artState.memory.filter((row) => row.name !== name), { feature, name, bytes, scale }];
};

const bytesOf = (texture: PIXI.Texture) => {
	const w = texture.width || 0;
	const h = texture.height || 0;
	return Math.round(w * h * 4);
};

async function loadTexture(url: string) {
	const texture = (await PIXI.Assets.load(url)) as PIXI.Texture;
	return texture;
}

async function sheetMeta(file: string) {
	const response = await fetch(`/assets/atlas/${file}`);
	if (!response.ok) return null;
	const json = (await response.json()) as { meta?: { size?: { w: number; h: number } } };
	const w = json.meta?.size?.w ?? 0;
	const h = json.meta?.size?.h ?? 0;
	return { bytes: w * h * 4 };
}

async function loadSheetTextures(file: string) {
	const sheet = (await PIXI.Assets.load(`/assets/atlas/${file}`)) as PIXI.Spritesheet;
	const animations = sheet.animations ?? {};
	const key = Object.keys(animations)[0];
	const frames = key ? animations[key] : Object.values(sheet.textures);
	return frames ?? [];
}

export async function loadArt(portrait: boolean) {
	artState.scale = preferredScale();
	const baseFiles = [
		'/assets/scene/reel_frame.png',
		'/assets/scene/ui/logo.png',
		...Object.values(STILL_FILES).map((file) => `/assets/symbols/${file}`),
	];
	const bg = portrait
		? artState.scale === 2
			? '/assets/scene/bg_v6_portrait_1440.png'
			: '/assets/scene/bg_v6_portrait_1080.png'
		: artState.scale === 2
			? '/assets/scene/bg_v6_2560.png'
			: '/assets/scene/bg_v6_1920.png';
	let done = 0;
	const tick = () => {
		done += 1;
		artState.progress = done / (baseFiles.length + 2);
	};
	const [frame, logo, background, frameMeta] = await Promise.all([
		loadTexture('/assets/scene/reel_frame.png').then((texture) => {
			tick();
			return texture;
		}),
		loadTexture('/assets/scene/ui/logo.png').then((texture) => {
			tick();
			return texture;
		}),
		loadTexture(bg).then((texture) => {
			tick();
			return texture;
		}),
		fetch('/assets/scene/reel_frame.json').then((response) => response.json() as Promise<FrameMeta>),
	]);
	artState.frame = frame;
	artState.logo = logo;
	artState.background = background;
	artState.frameMeta = frameMeta;
	note('base', 'frame', bytesOf(frame), 1);
	note('base', 'logo', bytesOf(logo), 1);
	note('base', bg, bytesOf(background), artState.scale);
	const stills: Record<string, PIXI.Texture> = {};
	await Promise.all(
		Object.entries(STILL_FILES).map(async ([name, file]) => {
			const texture = await loadTexture(`/assets/symbols/${file}`);
			stills[name] = texture;
			note('base', `still:${name}`, bytesOf(texture), 1);
			tick();
		}),
	);
	artState.stills = stills;
	manifest = (await (await fetch('/assets/atlas/manifest.json')).json()) as Manifest;
	artState.ready = true;
	artState.progress = 1;
	if (import.meta.env.DEV) {
		(globalThis as { memorySummary?: typeof memorySummary }).memorySummary = memorySummary;
	}
}

const featureOf = (mode: string) => (mode === 'win' ? 'win' : mode === 'melt' ? 'melt' : 'idle');

export async function loadClip(symbolKey: string, mode: 'melt' | 'idle' | 'win') {
	const cacheKey = `${symbolKey}:${mode}:${artState.scale}`;
	const cached = clips.get(cacheKey) ?? clips.get(`${symbolKey}:${mode}:1`);
	if (cached) return cached;
	if (!manifest) return [];
	const entry = manifest[symbolKey]?.[mode];
	if (!entry) return [];
	let scale: 1 | 2 = artState.scale === 2 && entry['2'] ? 2 : 1;
	if (scale === 2 && entry['2']) {
		const sizes = await Promise.all(entry['2'].sheets.map((file) => sheetMeta(file)));
		const total = sizes.reduce((sum, row) => sum + (row?.bytes ?? 0), 0);
		if (!sizes.every(Boolean) || total > CLIP_BUDGET) scale = 1;
	}
	const spec = entry[String(scale) as '1' | '2'] ?? entry['1'];
	if (!spec) return [];
	const frames: PIXI.Texture[] = [];
	let bytes = 0;
	for (const file of spec.sheets) {
		const textures = await loadSheetTextures(file);
		frames.push(...textures);
		const meta = await sheetMeta(file);
		bytes += meta?.bytes ?? 0;
	}
	clips.set(`${symbolKey}:${mode}:${scale}`, frames);
	note(featureOf(mode), `${symbolKey}:${mode}@${scale}`, bytes, scale);
	return frames;
}

export function stillTexture(name: string) {
	return artState.stills[name] ?? PIXI.Texture.WHITE;
}

export function memorySummary() {
	const totals: Record<string, number> = {};
	for (const row of artState.memory) totals[row.feature] = (totals[row.feature] ?? 0) + row.bytes;
	return { scale: artState.scale, totals, rows: artState.memory };
}

export async function releaseFeature(feature: string) {
	const drop = artState.memory.filter((row) => row.feature === feature);
	for (const row of drop) {
		const [key] = row.name.split('@');
		const textures = clips.get(`${key}:${row.scale}`) ?? clips.get(key);
		textures?.forEach((texture) => {
			texture.destroy(true);
		});
		clips.delete(`${key}:${row.scale}`);
		clips.delete(key);
	}
	artState.memory = artState.memory.filter((row) => row.feature !== feature);
}

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
type AtlasMeta = {
	meta: { image: string; size: { w: number; h: number } };
	frames: Record<string, { frame: { x: number; y: number; w: number; h: number } }>;
};

export type MemoryRow = { feature: string; name: string; bytes: number; scale: number };

/**
 * Decoded size of the previous loader at 1x, measured from the atlas JSON:
 * four idle loops × two 2048×3072 sheets, thirteen 1024 stills, and the 1x scene.
 * Idle alone was 192 MiB. The base game is the scene plus whatever idle loops
 * are actually on screen.
 */
export const MEMORY_BEFORE_1X = {
	idle: 4 * 2 * 2048 * 3072 * 4,
	stills: 13 * 1024 * 1024 * 4,
	scene: 1182 * 1005 * 4 + 1892 * 267 * 4 + 1920 * 1080 * 4,
};

/** Keep one idle frame in four. Playback holds each frame so the 6s loop stays put. */
export const IDLE_FRAME_STRIDE = 4;

const CLIP_BUDGET = 100 * 1024 * 1024;
const STILL_EDGE = 512;

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
const idleBases = new Map<string, PIXI.Texture>();
const idleLoads = new Map<string, Promise<PIXI.Texture[]>>();
const idleRetains = new Map<string, number>();
let idleChain: Promise<unknown> = Promise.resolve();
let manifest: Manifest | null = null;

export const preferredScale = () => {
	if (typeof window === 'undefined') return 1;
	const query = new URLSearchParams(window.location.search).get('assetScale');
	if (query === '1' || query === '2') return Number(query);
	return (window.devicePixelRatio || 1) >= 1.5 ? 2 : 1;
};

const note = (feature: string, name: string, bytes: number, scale: number) => {
	artState.memory = [...artState.memory.filter((row) => row.name !== name), { feature, name, bytes, scale }];
};

const bytesOf = (texture: PIXI.Texture) => Math.round((texture.width || 0) * (texture.height || 0) * 4);

const queueIdle = <T>(job: () => Promise<T>) => {
	const run = idleChain.then(job, job);
	idleChain = run.then(
		() => undefined,
		() => undefined,
	);
	return run;
};

const loadImage = (url: string) =>
	new Promise<HTMLImageElement>((resolve, reject) => {
		const image = new Image();
		image.onload = () => resolve(image);
		image.onerror = () => reject(new Error(`Could not load ${url}`));
		image.src = url;
	});

async function loadTexture(url: string) {
	return (await PIXI.Assets.load(url)) as PIXI.Texture;
}

async function loadStill(url: string) {
	const image = await loadImage(url);
	const edge = Math.max(image.width, image.height);
	const scale = Math.min(1, STILL_EDGE / edge);
	const width = Math.max(1, Math.round(image.width * scale));
	const height = Math.max(1, Math.round(image.height * scale));
	const canvas = document.createElement('canvas');
	canvas.width = width;
	canvas.height = height;
	const context = canvas.getContext('2d');
	if (!context) return PIXI.Texture.WHITE;
	context.drawImage(image, 0, 0, width, height);
	const texture = PIXI.Texture.from(canvas);
	texture.source.autoGenerateMipmaps = false;
	texture.source.mipLevelCount = 1;
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

const dropClips = () => {
	idleBases.forEach((texture) => {
		if (!texture.destroyed) texture.destroy(true);
	});
	idleBases.clear();
	idleLoads.clear();
	idleRetains.clear();
	clips.clear();
	artState.memory = [];
};

export async function loadArt(portrait: boolean) {
	dropClips();
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
			const texture = await loadStill(`/assets/symbols/${file}`);
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

const idleKey = (symbolKey: string) => `${symbolKey}:idle:${artState.scale}`;

const releasePacked = (symbolKey: string, scale: number) => {
	const id = `${symbolKey}:idle:${scale}`;
	const base = idleBases.get(id);
	idleBases.delete(id);
	clips.delete(id);
	idleLoads.delete(id);
	if (base && !base.destroyed) base.destroy(true);
	artState.memory = artState.memory.filter((row) => row.name !== `${symbolKey}:idle@${scale}`);
};

async function decodeIdle(symbolKey: string, scale: 1 | 2) {
	if (!manifest) return { frames: [] as PIXI.Texture[], bytes: 0, base: null as PIXI.Texture | null };
	const entry = manifest[symbolKey]?.idle;
	const spec = (scale === 2 ? entry?.['2'] : entry?.['1']) ?? entry?.['1'];
	if (!spec) return { frames: [] as PIXI.Texture[], bytes: 0, base: null as PIXI.Texture | null };
	const sources: { canvas: HTMLCanvasElement; frames: AtlasMeta['frames'] }[] = [];
	let index = 0;
	const picked: { canvas: HTMLCanvasElement; x: number; y: number; w: number; h: number }[] = [];
	for (const file of spec.sheets) {
		const response = await fetch(`/assets/atlas/${file}`);
		const meta = (await response.json()) as AtlasMeta;
		const image = await loadImage(`/assets/atlas/${meta.meta.image}`);
		const frameSize = Object.values(meta.frames)[0]?.frame.w || image.width;
		const target = scale === 2 ? 384 : frameSize;
		const drawScale = target / frameSize;
		const canvas = document.createElement('canvas');
		canvas.width = Math.max(1, Math.round(meta.meta.size.w * drawScale));
		canvas.height = Math.max(1, Math.round(meta.meta.size.h * drawScale));
		const context = canvas.getContext('2d');
		if (!context) continue;
		context.imageSmoothingEnabled = true;
		context.imageSmoothingQuality = 'high';
		context.drawImage(image, 0, 0, canvas.width, canvas.height);
		sources.push({ canvas, frames: meta.frames });
		for (const name of Object.keys(meta.frames).sort()) {
			if (index % IDLE_FRAME_STRIDE === 0) {
				const frame = meta.frames[name].frame;
				picked.push({
					canvas,
					x: frame.x * drawScale,
					y: frame.y * drawScale,
					w: frame.w * drawScale,
					h: frame.h * drawScale,
				});
			}
			index += 1;
		}
	}
	if (!picked.length) return { frames: [] as PIXI.Texture[], bytes: 0, base: null as PIXI.Texture | null };
	const cell = Math.round(picked[0].w);
	const columns = 8;
	const rows = Math.ceil(picked.length / columns);
	const packed = document.createElement('canvas');
	packed.width = columns * cell;
	packed.height = rows * cell;
	const painter = packed.getContext('2d');
	if (!painter) return { frames: [] as PIXI.Texture[], bytes: 0, base: null as PIXI.Texture | null };
	picked.forEach((frame, frameIndex) => {
		const column = frameIndex % columns;
		const row = Math.floor(frameIndex / columns);
		painter.drawImage(frame.canvas, frame.x, frame.y, frame.w, frame.h, column * cell, row * cell, cell, cell);
	});
	sources.forEach((source) => {
		source.canvas.width = 0;
		source.canvas.height = 0;
	});
	const base = PIXI.Texture.from(packed);
	base.source.autoGenerateMipmaps = false;
	base.source.mipLevelCount = 1;
	const frames = picked.map((_, frameIndex) => {
		const column = frameIndex % columns;
		const row = Math.floor(frameIndex / columns);
		return new PIXI.Texture({
			source: base.source,
			frame: new PIXI.Rectangle(column * cell, row * cell, cell, cell),
		});
	});
	return { frames, bytes: packed.width * packed.height * 4, base };
}

async function loadIdle(symbolKey: string) {
	const scale = artState.scale === 2 ? 2 : 1;
	const id = idleKey(symbolKey);
	const pending = idleLoads.get(id);
	if (pending) return pending;
	const job = queueIdle(async () => {
		const decoded = await decodeIdle(symbolKey, scale);
		if ((idleRetains.get(id) ?? 0) <= 0) {
			if (decoded.base && !decoded.base.destroyed) decoded.base.destroy(true);
			idleLoads.delete(id);
			return [] as PIXI.Texture[];
		}
		if (decoded.base) idleBases.set(id, decoded.base);
		clips.set(id, decoded.frames);
		note('idle', `${symbolKey}:idle@${scale}`, decoded.bytes, scale);
		return decoded.frames;
	});
	idleLoads.set(id, job);
	return job;
}

export function retainIdle(symbolKey: string) {
	const id = idleKey(symbolKey);
	idleRetains.set(id, (idleRetains.get(id) ?? 0) + 1);
	return loadIdle(symbolKey);
}

export function releaseIdle(symbolKey: string) {
	const scale = artState.scale === 2 ? 2 : 1;
	const id = idleKey(symbolKey);
	const next = (idleRetains.get(id) ?? 0) - 1;
	if (next > 0) {
		idleRetains.set(id, next);
		return;
	}
	idleRetains.delete(id);
	if (idleBases.has(id)) releasePacked(symbolKey, scale);
}

export async function loadClip(symbolKey: string, mode: 'melt' | 'idle' | 'win') {
	if (mode === 'idle') return loadIdle(symbolKey);
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
	const decoded = Object.values(totals).reduce((sum, value) => sum + value, 0);
	return {
		scale: artState.scale,
		totals,
		decoded,
		before: MEMORY_BEFORE_1X,
		rows: artState.memory,
	};
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

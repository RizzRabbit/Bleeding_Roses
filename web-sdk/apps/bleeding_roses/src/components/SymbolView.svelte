<script lang="ts">
	import type * as PIXI from 'pixi.js';
	import { AnimatedSprite, BaseSprite, Graphics } from 'pixi-svelte';

	import { IDLE_FRAME_STRIDE, loadClip, releaseIdle, retainIdle, stillTexture } from '../game/art.svelte';
	import { BLOODY, CLIP_KEY } from '../game/constants';
	import { completeCell } from '../game/stateGame.svelte';
	import { animSpeed, TEMPO } from '../game/tempo';

	type Props = {
		name: string;
		anim: 'still' | 'idle' | 'melt' | 'win';
		token: number;
		reel: number;
		row: number;
		x: number;
		y: number;
		glow?: boolean;
	};

	const props: Props = $props();

	let textures = $state<PIXI.Texture[]>([]);

	const clipMode = (anim: Props['anim'], name: string): 'melt' | 'idle' | 'win' | null => {
		if (anim === 'melt') return 'melt';
		if (anim === 'idle') return 'idle';
		if (anim === 'win' && name === 'BH') return 'win';
		if (anim === 'win' && BLOODY.has(name)) return 'idle';
		return null;
	};

	$effect(() => {
		const anim = props.anim;
		const name = props.name;
		const token = props.token;
		const reel = props.reel;
		const row = props.row;
		let cancelled = false;
		let timer = 0;
		const finish = () => completeCell(reel, row, token);
		const mode = clipMode(anim, name);
		const key = CLIP_KEY[name];
		if (!mode || !key) {
			textures = [];
			if (anim === 'win') timer = window.setTimeout(finish, TEMPO.win.letter);
			return () => window.clearTimeout(timer);
		}
		const cap =
			anim === 'melt' ? 4500 : anim === 'win' ? (name === 'BH' ? 5000 : TEMPO.win.rose) : 0;
		if (cap) timer = window.setTimeout(finish, cap);
		const framesPromise = mode === 'idle' ? retainIdle(key) : loadClip(key, mode);
		framesPromise.then((frames) => {
			if (cancelled) return;
			if (!frames.length) {
				if (cap) finish();
				return;
			}
			textures = frames;
		});
		return () => {
			cancelled = true;
			window.clearTimeout(timer);
			if (mode === 'idle') releaseIdle(key);
		};
	});

	const still = $derived(stillTexture(props.name));
	const looping = $derived(
		props.anim === 'idle' || (props.anim === 'win' && props.name !== 'BH' && BLOODY.has(props.name)),
	);
	const shownWidth = $derived(textures[0]?.width || still.width || 180);
	const scale = $derived(180 / shownWidth);
	const playSpeed = $derived(looping ? animSpeed() / IDLE_FRAME_STRIDE : animSpeed());
</script>

{#if props.glow}
	<Graphics
		x={props.x}
		y={props.y}
		draw={(graphics) => {
			graphics.clear();
			graphics.roundRect(-84, -84, 168, 168, 8).stroke({ width: 3, color: 0x9a3040, alpha: 0.9 });
		}}
	/>
{/if}

{#if textures.length}
	<AnimatedSprite
		{textures}
		x={props.x}
		y={props.y}
		anchor={{ x: 0.5, y: 0.5 }}
		{scale}
		animationSpeed={playSpeed}
		loop={looping}
		play={true}
		onComplete={() => {
			if (props.anim === 'melt' || (props.anim === 'win' && props.name === 'BH')) {
				completeCell(props.reel, props.row, props.token);
			}
		}}
	/>
{:else}
	<BaseSprite texture={still} x={props.x} y={props.y} anchor={{ x: 0.5, y: 0.5 }} {scale} />
{/if}

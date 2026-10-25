<script lang="ts">
	import type * as PIXI from 'pixi.js';
	import { AnimatedSprite, BaseSprite } from 'pixi-svelte';

	import { stillTexture, loadClip } from '../game/art.svelte';
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
		loadClip(key, mode).then((frames) => {
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
		};
	});

	const scale = $derived(textures[0] ? 180 / textures[0].width : 180 / 1024);
	const still = $derived(stillTexture(props.name));
	const looping = $derived(
		props.anim === 'idle' || (props.anim === 'win' && props.name !== 'BH' && BLOODY.has(props.name)),
	);
</script>

{#if props.glow}
	<BaseSprite
		texture={textures[0] ?? still}
		x={props.x}
		y={props.y}
		anchor={{ x: 0.5, y: 0.5 }}
		scale={scale * 1.08}
		alpha={0.55}
		tint={0xffc1d4}
	/>
{/if}

{#if textures.length}
	<AnimatedSprite
		{textures}
		x={props.x}
		y={props.y}
		anchor={{ x: 0.5, y: 0.5 }}
		{scale}
		animationSpeed={animSpeed()}
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

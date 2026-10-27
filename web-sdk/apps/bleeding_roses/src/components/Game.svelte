<script lang="ts">
	import { onMount } from 'svelte';
	import EnableHotkey from 'components-shared/src/components/EnableHotkey.svelte';
	import { MainContainer } from 'components-layout';
	import { App, BaseSprite, Container } from 'pixi-svelte';

	import { artState, loadArt } from '../game/art.svelte';
	import { boot } from '../game/boot.svelte';
	import { getContext } from '../game/context';
	import Board from './Board.svelte';
	import EnableGameActor from './EnableGameActor.svelte';
	import Hud from './Hud.svelte';
	import ResumeBet from './ResumeBet.svelte';

	const context = getContext();
	const canvas = $derived.by(context.stateLayoutDerived.canvasSizes);
	const stage = $derived.by(context.stateLayoutDerived.layoutType);
	const cover = $derived.by(() => {
		const texture = artState.background;
		if (!texture) return 1;
		return Math.max(canvas.width / texture.width, canvas.height / texture.height);
	});
	const logo = $derived.by(() => {
		const texture = artState.logo;
		if (!texture) return null;
		const portrait = stage === 'portrait';
		const width = portrait ? 1020 : 960;
		const cx = portrait ? 540 : 960;
		const cy = portrait ? 410 : 72;
		return {
			texture,
			x: cx,
			y: cy,
			width,
			height: width * (texture.height / texture.width),
		};
	});

	$effect(() => {
		boot.progress = artState.progress;
	});

	onMount(() => {
		let portrait = context.stateLayoutDerived.layoutType() === 'portrait';
		let token = 0;
		const run = (nextPortrait: boolean) => {
			const id = ++token;
			boot.ready = false;
			artState.ready = false;
			loadArt(nextPortrait)
				.then(() => {
					if (id === token) boot.ready = true;
				})
				.catch((error: unknown) => {
					artState.error = error instanceof Error ? error.message : 'Art failed to load.';
					if (id === token) boot.ready = true;
				});
		};
		run(portrait);
		const timer = window.setInterval(() => {
			const next = context.stateLayoutDerived.layoutType() === 'portrait';
			if (next !== portrait) {
				portrait = next;
				run(next);
			}
		}, 500);
		return () => window.clearInterval(timer);
	});
</script>

<App>
	<EnableHotkey />
	<EnableGameActor />
	{#if artState.ready && artState.background}
		<ResumeBet />
		<Container>
			<BaseSprite
				texture={artState.background}
				x={canvas.width / 2}
				y={canvas.height / 2}
				anchor={{ x: 0.5, y: 0.5 }}
				scale={cover}
			/>
		</Container>
		<MainContainer>
			<Board />
			{#if logo}
				<BaseSprite
					texture={logo.texture}
					x={logo.x}
					y={logo.y}
					anchor={{ x: 0.5, y: 0.5 }}
					width={logo.width}
					height={logo.height}
				/>
			{/if}
		</MainContainer>
	{/if}
</App>

{#if artState.ready}
	<Hud />
{/if}

{#if artState.error}
	<p class="art-error">{artState.error}</p>
{/if}

<style>
	.art-error {
		position: fixed;
		left: 24px;
		right: 24px;
		bottom: 24px;
		z-index: 30;
		color: #f4e7ea;
		font-family: Cinzel, serif;
		text-align: center;
	}
</style>
